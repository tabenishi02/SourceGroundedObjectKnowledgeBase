"""Hybrid grounding validation for structured grounded-generation output."""

from __future__ import annotations

import re
from typing import Any, Protocol

from .context import GroundedContextProjector
from .output import GenerationOutputContractError, parse_generation_output

GROUNDING_VALIDATION_CONTRACT_VERSION = "sgokb.grounding-validation.v1"


class SemanticValidatorAdapter(Protocol):
    """Bounded semantic judge over only the claim and supplied K units.

    The implementation may return the G-05 minimum verdicts plus ``role_valid``
    for non-factual semantic-role boundary checks.
    """

    def validate(
        self,
        *,
        text: str,
        semantic_role: str,
        support_units: list[dict[str, Any]],
        purpose: str,
        presentation_role: str,
    ) -> str: ...


def _normalize_text(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[\s.,;:!?]+$", "", value)
    return value


def _support_texts(unit: dict[str, Any]) -> list[str]:
    content = unit.get("content", {})
    values: list[str] = []
    if unit.get("source_kind") == "statement" and isinstance(content.get("text"), str):
        values.append(content["text"])
    elif unit.get("source_kind") == "object_field":
        value = content.get("value")
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, dict):
            for key in ("value", "name", "key"):
                item = value.get(key)
                if isinstance(item, str):
                    values.append(item)
    elif unit.get("source_kind") == "attribute":
        value = content.get("value")
        if isinstance(value, (str, int, float, bool)):
            values.append(str(value))
    elif unit.get("source_kind") == "relation":
        for key in ("relation_name", "relation_key", "object_name"):
            item = content.get(key)
            if isinstance(item, str):
                values.append(item)
    return values


def _failure(
    stage: str,
    failure_class: str,
    failure_code: str,
    *,
    unit_id: str | None = None,
    support_refs: list[str] | None = None,
    retryable: bool,
    system_failure: bool = False,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "failure_class": failure_class,
        "failure_code": failure_code,
        "unit_id": unit_id,
        "support_refs": list(support_refs or []),
        "retryable": retryable,
        "system_failure": system_failure,
    }


class GroundingValidator:
    """Run G-05 V0..V5 with optional bounded semantic validation."""

    contract_version = GROUNDING_VALIDATION_CONTRACT_VERSION

    def __init__(self, semantic_validator: SemanticValidatorAdapter | None = None) -> None:
        self.semantic_validator = semantic_validator

    def validate(
        self,
        grounded_context: dict[str, Any],
        raw_output: str | dict[str, Any],
    ) -> dict[str, Any]:
        failures: list[dict[str, Any]] = []
        unit_results: list[dict[str, Any]] = []

        # V0 — Contract / Parse
        try:
            output = parse_generation_output(raw_output)
        except GenerationOutputContractError as exc:
            failures.append(
                _failure(
                    "V0",
                    "VALIDATION_CONTRACT_ERROR",
                    exc.failure_code,
                    retryable=True,
                )
            )
            return self._result("FAIL", None, unit_results, failures)

        # V1 — Grounded Context integrity and reference namespace
        if not GroundedContextProjector.verify(grounded_context):
            failures.append(
                _failure(
                    "V1",
                    "REFERENCE_INTEGRITY_ERROR",
                    "grounded_context_fingerprint_invalid",
                    retryable=False,
                    system_failure=True,
                )
            )
            return self._result("INDETERMINATE", output, unit_results, failures)

        expected_fingerprint = grounded_context["context_fingerprint"]
        if output["context_fingerprint"] != expected_fingerprint:
            failures.append(
                _failure(
                    "V1",
                    "REFERENCE_INTEGRITY_ERROR",
                    "output_context_fingerprint_mismatch",
                    retryable=True,
                )
            )

        if output["purpose"] != grounded_context.get("purpose"):
            failures.append(
                _failure(
                    "V1",
                    "VALIDATION_CONTRACT_ERROR",
                    "purpose_mismatch",
                    retryable=True,
                )
            )

        support_by_ref = {
            unit["ref_id"]: unit for unit in grounded_context.get("grounding_units", [])
        }
        for ref_id, source in support_by_ref.items():
            canonical_ref = source.get("canonical_ref")
            if not isinstance(canonical_ref, dict) or not canonical_ref.get("kind"):
                failures.append(
                    _failure(
                        "V1",
                        "REFERENCE_INTEGRITY_ERROR",
                        "broken_canonical_mapping",
                        support_refs=[ref_id],
                        retryable=False,
                        system_failure=True,
                    )
                )

        if any(item["system_failure"] for item in failures):
            return self._result("INDETERMINATE", output, unit_results, failures)

        # V2/V3/V4 — unit policy, deterministic support and bounded semantics
        for block in output["blocks"]:
            presentation_role = block["presentation_role"]
            for unit in block["units"]:
                role = unit["semantic_role"]
                unit_id = unit["unit_id"]
                refs = unit["support_refs"]
                before = len(failures)

                unknown_refs = [ref for ref in refs if ref not in support_by_ref]
                if unknown_refs:
                    failures.append(
                        _failure(
                            "V1",
                            "REFERENCE_INTEGRITY_ERROR",
                            "unknown_grounding_reference",
                            unit_id=unit_id,
                            support_refs=unknown_refs,
                            retryable=True,
                        )
                    )

                self._validate_policy(
                    failures,
                    unit_id=unit_id,
                    role=role,
                    refs=refs,
                    presentation_role=presentation_role,
                    purpose=output["purpose"],
                )

                if len(failures) > before:
                    unit_results.append(
                        {
                            "unit_id": unit_id,
                            "semantic_role": role,
                            "grounding_disposition": "unsupported",
                            "validation_stage": "V2",
                        }
                    )
                    continue

                support_units = [support_by_ref[ref] for ref in refs]
                if role == "source_fact":
                    deterministic = self._deterministic_support(unit, support_units)
                    if deterministic == "supported":
                        unit_results.append(
                            {
                                "unit_id": unit_id,
                                "semantic_role": role,
                                "grounding_disposition": "supported",
                                "validation_stage": "V3",
                            }
                        )
                        continue

                semantic = self._semantic_support(
                    unit,
                    support_units=support_units,
                    purpose=output["purpose"],
                    presentation_role=presentation_role,
                )

                if role == "source_fact" and semantic == "entailed":
                    unit_results.append(
                        {
                            "unit_id": unit_id,
                            "semantic_role": role,
                            "grounding_disposition": "supported",
                            "validation_stage": "V4",
                        }
                    )
                    continue
                if role == "interpretation" and semantic in {
                    "reasonable_derivation",
                    "entailed",
                }:
                    unit_results.append(
                        {
                            "unit_id": unit_id,
                            "semantic_role": role,
                            "grounding_disposition": "derived_supported",
                            "validation_stage": "V4",
                        }
                    )
                    continue
                if role in {
                    "creative_addition",
                    "context_limit",
                    "stylistic_expression",
                } and semantic == "role_valid":
                    unit_results.append(
                        {
                            "unit_id": unit_id,
                            "semantic_role": role,
                            "grounding_disposition": "not_applicable",
                            "validation_stage": "V4",
                        }
                    )
                    continue

                disposition = "unsupported"
                failure_class = "UNSUPPORTED_CLAIM"
                failure_code = "claim_not_supported_by_refs"
                retryable = True
                system_failure = False
                aggregate_hint = "FAIL"
                if semantic == "contradictory":
                    disposition = "contradictory"
                    failure_class = "CONTRADICTORY_CLAIM"
                    failure_code = "claim_contradicts_refs"
                elif semantic == "role_mismatch":
                    failure_class = (
                        "CREATIVE_SCOPE_VIOLATION"
                        if role == "creative_addition"
                        else "ROLE_MISMATCH"
                    )
                    failure_code = "semantic_role_mismatch"
                elif semantic in {"indeterminate", "validator_unavailable"}:
                    failure_class = (
                        "VALIDATOR_UNAVAILABLE"
                        if semantic == "validator_unavailable"
                        else "SEMANTIC_INDETERMINATE"
                    )
                    failure_code = semantic
                    retryable = semantic == "indeterminate"
                    system_failure = semantic == "validator_unavailable"
                    aggregate_hint = "INDETERMINATE"

                failures.append(
                    _failure(
                        "V4",
                        failure_class,
                        failure_code,
                        unit_id=unit_id,
                        support_refs=refs,
                        retryable=retryable,
                        system_failure=system_failure,
                    )
                )
                unit_results.append(
                    {
                        "unit_id": unit_id,
                        "semantic_role": role,
                        "grounding_disposition": disposition,
                        "validation_stage": "V4",
                        "aggregate_hint": aggregate_hint,
                    }
                )

        # V5 — Aggregate verdict
        if not failures:
            verdict = "PASS"
        elif any(item["system_failure"] for item in failures) or any(
            item["failure_class"] == "SEMANTIC_INDETERMINATE" for item in failures
        ):
            verdict = "INDETERMINATE"
        else:
            verdict = "FAIL"
        return self._result(verdict, output, unit_results, failures)

    @staticmethod
    def _validate_policy(
        failures: list[dict[str, Any]],
        *,
        unit_id: str,
        role: str,
        refs: list[str],
        presentation_role: str,
        purpose: str,
    ) -> None:
        if role in {"source_fact", "interpretation"} and not refs:
            failures.append(
                _failure(
                    "V2",
                    "MISSING_REQUIRED_SUPPORT",
                    "support_refs_required",
                    unit_id=unit_id,
                    retryable=True,
                )
            )
        if role in {"creative_addition", "context_limit", "stylistic_expression"} and refs:
            failures.append(
                _failure(
                    "V2",
                    "ROLE_MISMATCH",
                    "support_refs_for_non_supported_role",
                    unit_id=unit_id,
                    support_refs=refs,
                    retryable=True,
                )
            )

        expected_block = {
            "source_fact": "main",
            "stylistic_expression": "main",
            "interpretation": "interpretation",
            "creative_addition": "creative",
            "context_limit": "context_limit",
        }[role]
        if presentation_role != expected_block:
            failure_class = (
                "SEPARATION_VIOLATION"
                if role == "interpretation"
                else "CREATIVE_SCOPE_VIOLATION"
                if role == "creative_addition"
                else "ROLE_MISMATCH"
            )
            failures.append(
                _failure(
                    "V2",
                    failure_class,
                    "presentation_scope_mismatch",
                    unit_id=unit_id,
                    retryable=True,
                )
            )

        if purpose in {"roleplay", "comparison"} and role == "creative_addition":
            failures.append(
                _failure(
                    "V2",
                    "CREATIVE_SCOPE_VIOLATION",
                    "creative_addition_not_allowed_for_purpose",
                    unit_id=unit_id,
                    retryable=True,
                )
            )

    @staticmethod
    def _deterministic_support(
        output_unit: dict[str, Any],
        support_units: list[dict[str, Any]],
    ) -> str:
        claim = _normalize_text(output_unit["text"])
        for support in support_units:
            for candidate in _support_texts(support):
                if claim == _normalize_text(candidate):
                    return "supported"
        return "unresolved"

    def _semantic_support(
        self,
        output_unit: dict[str, Any],
        *,
        support_units: list[dict[str, Any]],
        purpose: str,
        presentation_role: str,
    ) -> str:
        if self.semantic_validator is None:
            return "validator_unavailable"
        try:
            verdict = self.semantic_validator.validate(
                text=output_unit["text"],
                semantic_role=output_unit["semantic_role"],
                support_units=support_units,
                purpose=purpose,
                presentation_role=presentation_role,
            )
        except Exception:  # Runtime boundary: record unavailability, do not hide it.
            return "validator_unavailable"
        allowed = {
            "entailed",
            "reasonable_derivation",
            "role_valid",
            "unsupported",
            "contradictory",
            "role_mismatch",
            "indeterminate",
        }
        return verdict if verdict in allowed else "indeterminate"

    def _result(
        self,
        verdict: str,
        output: dict[str, Any] | None,
        unit_results: list[dict[str, Any]],
        failures: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "validation_contract_version": self.contract_version,
            "verdict": verdict,
            "output": output,
            "unit_results": unit_results,
            "failures": failures,
        }
