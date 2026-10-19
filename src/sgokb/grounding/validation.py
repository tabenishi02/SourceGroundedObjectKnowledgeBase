"""Grounding validation v2 for N-04 post-G12 grounded generation."""

from __future__ import annotations

import re
from typing import Any

from .context import GroundedContextProjector
from .output import GenerationOutputContractError, output_binding, parse_generation_output
from .verifiers import (
    AtomicityRoleValidatorAdapter,
    InterpretationDerivationJudgeAdapter,
    SourceFactJudgeAdapter,
    SourceFactVerifierAdapter,
    normalize_adapter_result,
)

GROUNDING_VALIDATION_CONTRACT_VERSION = "sgokb.grounding-validation.v2"


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


def _failure(stage: str, failure_class: str, failure_code: str, *, unit_id: str | None = None, support_refs: list[str] | None = None, premise_unit_ids: list[str] | None = None, retryable: bool, system_failure: bool = False, **details: Any) -> dict[str, Any]:
    return {
        "stage": stage,
        "failure_class": failure_class,
        "failure_code": failure_code,
        "unit_id": unit_id,
        "support_refs": list(support_refs or []),
        "premise_unit_ids": list(premise_unit_ids or []),
        "retryable": retryable,
        "system_failure": system_failure,
        **details,
    }


class GroundingValidator:
    contract_version = GROUNDING_VALIDATION_CONTRACT_VERSION

    def __init__(self, *, atomicity_role_validator: AtomicityRoleValidatorAdapter | None = None, source_fact_verifier: SourceFactVerifierAdapter | None = None, source_fact_judge: SourceFactJudgeAdapter | None = None, interpretation_judge: InterpretationDerivationJudgeAdapter | None = None) -> None:
        self.atomicity_role_validator = atomicity_role_validator
        self.source_fact_verifier = source_fact_verifier
        self.source_fact_judge = source_fact_judge
        self.interpretation_judge = interpretation_judge

    def validate(self, grounded_context: dict[str, Any], raw_output: str | dict[str, Any], *, attempt: int = 1) -> dict[str, Any]:
        if attempt not in {1, 2}:
            raise ValueError("grounded-generation attempt must be 1 or 2")
        failures: list[dict[str, Any]] = []
        unit_results: list[dict[str, Any]] = []

        try:
            output = parse_generation_output(raw_output)
        except GenerationOutputContractError as exc:
            failures.append(_failure("V0", "VALIDATION_CONTRACT_ERROR", exc.failure_code, retryable=True, json_path=exc.json_path, block_id=exc.block_id, failure_detail=exc.failure_detail, expected_rule=exc.expected_rule))
            return self._result("FAIL", None, attempt, unit_results, failures)

        if not GroundedContextProjector.verify(grounded_context):
            failures.append(_failure("V1", "REFERENCE_INTEGRITY_ERROR", "grounded_context_fingerprint_invalid", retryable=False, system_failure=True))
            return self._result("INDETERMINATE", output, attempt, unit_results, failures)
        if output["context_fingerprint"] != grounded_context["context_fingerprint"]:
            failures.append(_failure("V1", "REFERENCE_INTEGRITY_ERROR", "output_context_fingerprint_mismatch", retryable=True))
        if output["purpose"] != grounded_context.get("purpose"):
            failures.append(_failure("V1", "VALIDATION_CONTRACT_ERROR", "purpose_mismatch", retryable=True))

        support_by_ref = {unit["ref_id"]: unit for unit in grounded_context.get("grounding_units", []) if isinstance(unit, dict) and isinstance(unit.get("ref_id"), str)}
        for ref_id, source in support_by_ref.items():
            canonical_ref = source.get("canonical_ref")
            if not isinstance(canonical_ref, dict) or not canonical_ref.get("kind"):
                failures.append(_failure("V1", "REFERENCE_INTEGRITY_ERROR", "broken_canonical_mapping", support_refs=[ref_id], retryable=False, system_failure=True))

        unit_map: dict[str, tuple[dict[str, Any], str]] = {}
        for block in output["blocks"]:
            for unit in block["units"]:
                unit_map[unit["unit_id"]] = (unit, block["presentation_role"])
                if unit["semantic_role"] == "source_fact":
                    unknown_refs = [ref for ref in unit["support_refs"] if ref not in support_by_ref]
                    if unknown_refs:
                        failures.append(_failure("V1", "REFERENCE_INTEGRITY_ERROR", "unknown_grounding_reference", unit_id=unit["unit_id"], support_refs=unknown_refs, retryable=True))
        if any(item["system_failure"] for item in failures):
            return self._result("INDETERMINATE", output, attempt, unit_results, failures)

        v2_ok: set[str] = set()
        for block in output["blocks"]:
            presentation_role = block["presentation_role"]
            for unit in block["units"]:
                unit_id = unit["unit_id"]
                role = unit["semantic_role"]
                if role == "context_limit":
                    unit_results.append({"unit_id": unit_id, "semantic_role": role, "atomicity_verdict": "NOT_APPLICABLE", "role_boundary_verdict": "ROLE_VALID", "grounding_disposition": "not_applicable", "validation_stage": "V2", "limit_code": unit["limit_code"]})
                    v2_ok.add(unit_id)
                    continue
                if role == "creative_addition" and output["purpose"] != "creative":
                    failures.append(_failure("V2", "CREATIVE_SCOPE_VIOLATION", "creative_addition_not_allowed_for_purpose", unit_id=unit_id, retryable=True))
                    unit_results.append(self._failed_gate_result(unit_id, role, atomicity="INDETERMINATE", role_boundary="ROLE_VIOLATION"))
                    continue
                gate = self._atomicity_role_gate(unit, purpose=output["purpose"], presentation_role=presentation_role)
                atomicity = gate["atomicity_verdict"]
                role_boundary = gate["role_boundary_verdict"]
                if atomicity == "NON_ATOMIC":
                    failures.append(_failure("V2", "ATOMICITY_VIOLATION", "non_atomic_material_unit", unit_id=unit_id, retryable=True))
                elif atomicity == "INDETERMINATE":
                    failures.append(_failure("V2", "ATOMICITY_INDETERMINATE", "atomicity_indeterminate", unit_id=unit_id, retryable=True))
                if role_boundary == "ROLE_VIOLATION":
                    failures.append(_failure("V2", "ROLE_BOUNDARY_VIOLATION", "semantic_role_boundary_violation", unit_id=unit_id, retryable=True))
                elif role_boundary == "INDETERMINATE":
                    failures.append(_failure("V2", "ROLE_BOUNDARY_INDETERMINATE", "role_boundary_indeterminate", unit_id=unit_id, retryable=True))
                if gate.get("unavailable"):
                    failures.append(_failure("V2", "VALIDATOR_UNAVAILABLE", "atomicity_role_validator_unavailable", unit_id=unit_id, retryable=False, system_failure=True))
                if atomicity == "ATOMIC" and role_boundary == "ROLE_VALID":
                    v2_ok.add(unit_id)
                else:
                    unit_results.append(self._failed_gate_result(unit_id, role, atomicity=atomicity, role_boundary=role_boundary, gate_metadata=gate.get("metadata")))
        if any(item["system_failure"] for item in failures):
            return self._result("INDETERMINATE", output, attempt, unit_results, failures)

        result_by_id = {item["unit_id"]: item for item in unit_results}
        for unit_id, (unit, _) in unit_map.items():
            if unit["semantic_role"] != "source_fact" or unit_id not in v2_ok:
                continue
            refs = unit["support_refs"]
            if any(ref not in support_by_ref for ref in refs):
                result = self._unsupported_result(unit_id, "source_fact", "V1")
                unit_results.append(result)
                result_by_id[unit_id] = result
                continue
            support_units = [support_by_ref[ref] for ref in refs]
            if self._deterministic_support(unit, support_units) == "supported":
                result = {"unit_id": unit_id, "semantic_role": "source_fact", "atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID", "grounding_disposition": "supported", "validation_stage": "V3", "support_refs": list(refs), "source_object_ids": sorted({support.get("object_id") for support in support_units if isinstance(support.get("object_id"), str)}), "deterministic_verdict": "deterministic_supported"}
                unit_results.append(result)
                result_by_id[unit_id] = result
                continue
            result, new_failures = self._validate_source_fact_semantically(unit, support_units=support_units)
            failures.extend(new_failures)
            unit_results.append(result)
            result_by_id[unit_id] = result
        if any(item["system_failure"] for item in failures):
            return self._result("INDETERMINATE", output, attempt, unit_results, failures)

        for unit_id, (unit, _) in unit_map.items():
            if unit["semantic_role"] == "creative_addition" and unit_id in v2_ok and unit_id not in result_by_id:
                result = {"unit_id": unit_id, "semantic_role": "creative_addition", "atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID", "grounding_disposition": "not_applicable", "validation_stage": "V2"}
                unit_results.append(result)
                result_by_id[unit_id] = result

        for unit_id, (unit, _) in unit_map.items():
            if unit["semantic_role"] != "interpretation" or unit_id not in v2_ok:
                continue
            premise_ids = list(unit["premise_unit_ids"])
            premise_units: list[dict[str, Any]] = []
            premise_metadata: list[dict[str, Any]] = []
            premise_failure = False
            for premise_id in premise_ids:
                premise_entry = unit_map.get(premise_id)
                premise_result = result_by_id.get(premise_id)
                if premise_id == unit_id or premise_entry is None or premise_entry[0].get("semantic_role") != "source_fact" or premise_result is None or premise_result.get("grounding_disposition") != "supported":
                    premise_failure = True
                    break
                premise_unit = premise_entry[0]
                premise_units.append(premise_unit)
                premise_metadata.append({"unit_id": premise_id, "support_refs": list(premise_unit.get("support_refs", [])), "source_object_ids": list(premise_result.get("source_object_ids", []))})
            if premise_failure:
                failures.append(_failure("V4I", "PREMISE_INTEGRITY_ERROR", "invalid_or_unsupported_premise", unit_id=unit_id, premise_unit_ids=premise_ids, retryable=True))
                result = {"unit_id": unit_id, "semantic_role": "interpretation", "atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID", "grounding_disposition": "unsupported", "validation_stage": "V4I", "premise_unit_ids": premise_ids}
                unit_results.append(result)
                result_by_id[unit_id] = result
                continue
            result, new_failures = self._validate_interpretation(unit, premise_units=premise_units, premise_metadata=premise_metadata, purpose=output["purpose"])
            failures.extend(new_failures)
            unit_results.append(result)
            result_by_id[unit_id] = result

        all_unit_ids = set(unit_map)
        successful_unit_ids = {item["unit_id"] for item in unit_results if item.get("grounding_disposition") in {"supported", "derived_supported", "not_applicable"}}
        if not failures and successful_unit_ids == all_unit_ids:
            verdict = "PASS"
        elif any(item["system_failure"] for item in failures):
            verdict = "INDETERMINATE"
        elif any(item["failure_class"] in {"ATOMICITY_INDETERMINATE", "ROLE_BOUNDARY_INDETERMINATE", "VERIFIER_INDETERMINATE", "VERIFIER_DISAGREEMENT", "DERIVATION_INDETERMINATE"} for item in failures):
            verdict = "INDETERMINATE"
        else:
            verdict = "FAIL"
        return self._result(verdict, output, attempt, unit_results, failures)

    def _atomicity_role_gate(self, unit: dict[str, Any], *, purpose: str, presentation_role: str) -> dict[str, Any]:
        if self.atomicity_role_validator is None:
            return {"atomicity_verdict": "INDETERMINATE", "role_boundary_verdict": "INDETERMINATE", "unavailable": True}
        try:
            raw = self.atomicity_role_validator.validate(text=unit["text"], semantic_role=unit["semantic_role"], purpose=purpose, presentation_role=presentation_role)
        except Exception:
            return {"atomicity_verdict": "INDETERMINATE", "role_boundary_verdict": "INDETERMINATE", "unavailable": True}
        if not isinstance(raw, dict):
            return {"atomicity_verdict": "INDETERMINATE", "role_boundary_verdict": "INDETERMINATE", "metadata": {"raw_result_type": type(raw).__name__}}
        atomicity = str(raw.get("atomicity_verdict", "INDETERMINATE")).upper()
        role_boundary = str(raw.get("role_boundary_verdict", "INDETERMINATE")).upper()
        if atomicity not in {"ATOMIC", "NON_ATOMIC", "INDETERMINATE"}:
            atomicity = "INDETERMINATE"
        if role_boundary not in {"ROLE_VALID", "ROLE_VIOLATION", "INDETERMINATE"}:
            role_boundary = "INDETERMINATE"
        metadata = {key: value for key, value in raw.items() if key not in {"atomicity_verdict", "role_boundary_verdict"}}
        return {"atomicity_verdict": atomicity, "role_boundary_verdict": role_boundary, "metadata": metadata}

    @staticmethod
    def _deterministic_support(output_unit: dict[str, Any], support_units: list[dict[str, Any]]) -> str:
        claim = _normalize_text(output_unit["text"])
        for support in support_units:
            for candidate in _support_texts(support):
                if claim == _normalize_text(candidate):
                    return "supported"
        return "unresolved"

    def _validate_source_fact_semantically(self, unit: dict[str, Any], *, support_units: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        unit_id = unit["unit_id"]
        refs = list(unit["support_refs"])
        base = {"unit_id": unit_id, "semantic_role": "source_fact", "atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID", "validation_stage": "V4F", "support_refs": refs, "source_object_ids": sorted({support.get("object_id") for support in support_units if isinstance(support.get("object_id"), str)}), "deterministic_verdict": "unresolved"}
        if self.source_fact_verifier is None:
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4F", "VALIDATOR_UNAVAILABLE", "source_fact_verifier_unavailable", unit_id=unit_id, support_refs=refs, retryable=False, system_failure=True)]
        try:
            specialized = normalize_adapter_result(self.source_fact_verifier.verify(claim_text=unit["text"], support_units=support_units), allowed_verdicts={"SUPPORTED_CANDIDATE", "UNSUPPORTED", "CONTRADICTORY", "INDETERMINATE", "UNAVAILABLE"})
        except Exception:
            specialized = {"verdict": "UNAVAILABLE"}
        base["specialized_verifier"] = specialized
        verdict = specialized["verdict"]
        if verdict == "UNAVAILABLE":
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4F", "VALIDATOR_UNAVAILABLE", "source_fact_verifier_unavailable", unit_id=unit_id, support_refs=refs, retryable=False, system_failure=True)]
        if verdict == "UNSUPPORTED":
            return {**base, "grounding_disposition": "unsupported"}, [_failure("V4F", "UNSUPPORTED_CLAIM", "specialized_verifier_unsupported", unit_id=unit_id, support_refs=refs, retryable=True)]
        if verdict == "CONTRADICTORY":
            return {**base, "grounding_disposition": "contradictory"}, [_failure("V4F", "CONTRADICTORY_CLAIM", "specialized_verifier_contradictory", unit_id=unit_id, support_refs=refs, retryable=True)]
        if verdict == "INDETERMINATE":
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4F", "VERIFIER_INDETERMINATE", "specialized_verifier_indeterminate", unit_id=unit_id, support_refs=refs, retryable=True)]
        if self.source_fact_judge is None:
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4F", "VALIDATOR_UNAVAILABLE", "source_fact_llm_judge_unavailable", unit_id=unit_id, support_refs=refs, retryable=False, system_failure=True)]
        try:
            judge = normalize_adapter_result(self.source_fact_judge.judge(claim_text=unit["text"], support_units=support_units), allowed_verdicts={"ENTAILED", "UNSUPPORTED", "CONTRADICTORY", "INDETERMINATE", "UNAVAILABLE"})
        except Exception:
            judge = {"verdict": "UNAVAILABLE"}
        base["source_fact_judge"] = judge
        judge_verdict = judge["verdict"]
        if judge_verdict == "ENTAILED":
            return {**base, "grounding_disposition": "supported"}, []
        if judge_verdict == "UNAVAILABLE":
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4F", "VALIDATOR_UNAVAILABLE", "source_fact_llm_judge_unavailable", unit_id=unit_id, support_refs=refs, retryable=False, system_failure=True)]
        return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4F", "VERIFIER_DISAGREEMENT", "source_fact_verifier_disagreement", unit_id=unit_id, support_refs=refs, retryable=True, specialized_verdict=verdict, judge_verdict=judge_verdict)]

    def _validate_interpretation(self, unit: dict[str, Any], *, premise_units: list[dict[str, Any]], premise_metadata: list[dict[str, Any]], purpose: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        unit_id = unit["unit_id"]
        premise_ids = list(unit["premise_unit_ids"])
        base = {"unit_id": unit_id, "semantic_role": "interpretation", "atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID", "validation_stage": "V4I", "premise_unit_ids": premise_ids, "premise_object_ids": sorted({object_id for metadata in premise_metadata for object_id in metadata.get("source_object_ids", [])}), "premise_support_refs": sorted({ref for metadata in premise_metadata for ref in metadata.get("support_refs", [])})}
        if self.interpretation_judge is None:
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4I", "VALIDATOR_UNAVAILABLE", "interpretation_derivation_judge_unavailable", unit_id=unit_id, premise_unit_ids=premise_ids, retryable=False, system_failure=True)]
        try:
            judge = normalize_adapter_result(self.interpretation_judge.judge(conclusion_text=unit["text"], premise_texts=[item["text"] for item in premise_units], premise_metadata=premise_metadata, purpose=purpose), allowed_verdicts={"REASONABLE_DERIVATION", "UNSUPPORTED_DERIVATION", "CONTRADICTORY", "INDETERMINATE", "UNAVAILABLE"})
        except Exception:
            judge = {"verdict": "UNAVAILABLE"}
        base["derivation_judge"] = judge
        verdict = judge["verdict"]
        if verdict == "REASONABLE_DERIVATION":
            return {**base, "grounding_disposition": "derived_supported"}, []
        if verdict == "UNAVAILABLE":
            return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4I", "VALIDATOR_UNAVAILABLE", "interpretation_derivation_judge_unavailable", unit_id=unit_id, premise_unit_ids=premise_ids, retryable=False, system_failure=True)]
        if verdict == "UNSUPPORTED_DERIVATION":
            return {**base, "grounding_disposition": "unsupported"}, [_failure("V4I", "UNSUPPORTED_DERIVATION", "interpretation_not_derived_from_premises", unit_id=unit_id, premise_unit_ids=premise_ids, retryable=True)]
        if verdict == "CONTRADICTORY":
            return {**base, "grounding_disposition": "contradictory"}, [_failure("V4I", "DERIVATION_CONTRADICTORY", "interpretation_contradicts_premises", unit_id=unit_id, premise_unit_ids=premise_ids, retryable=True)]
        return {**base, "grounding_disposition": "indeterminate"}, [_failure("V4I", "DERIVATION_INDETERMINATE", "interpretation_derivation_indeterminate", unit_id=unit_id, premise_unit_ids=premise_ids, retryable=True)]

    @staticmethod
    def _failed_gate_result(unit_id: str, role: str, *, atomicity: str, role_boundary: str, gate_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        result = {"unit_id": unit_id, "semantic_role": role, "atomicity_verdict": atomicity, "role_boundary_verdict": role_boundary, "grounding_disposition": "unsupported", "validation_stage": "V2"}
        if gate_metadata:
            result["atomicity_role_metadata"] = gate_metadata
        return result

    @staticmethod
    def _unsupported_result(unit_id: str, role: str, stage: str) -> dict[str, Any]:
        return {"unit_id": unit_id, "semantic_role": role, "atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID", "grounding_disposition": "unsupported", "validation_stage": stage}

    def _result(self, verdict: str, output: dict[str, Any] | None, attempt: int, unit_results: list[dict[str, Any]], failures: list[dict[str, Any]]) -> dict[str, Any]:
        return {"validation_contract_version": self.contract_version, "verdict": verdict, "output": output, "binding": output_binding(output, attempt=attempt) if output is not None else None, "unit_results": unit_results, "failures": failures}
