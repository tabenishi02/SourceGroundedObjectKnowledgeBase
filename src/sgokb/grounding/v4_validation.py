"""Validation, certification, and presentation-plan assembly for SGOKB v4."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .v4_contracts import (
    CERTIFIED_CONTENT_VERSION,
    PATH_CERTIFIED_FACT,
    PATH_ROLE_MAP,
    PATH_STAGE1_FACT,
    PATH_STAGE2_CREATIVE,
    PATH_STAGE2_INTERPRETATION,
    ROLE_CREATIVE,
    ROLE_INTERPRETATION,
    ROLE_SOURCE_FACT,
    STRUCTURED_PROPOSITION_VERSION,
    VALIDATED_PLAN_VERSION,
    VALIDATION_RECORD_VERSION,
    digest_object,
)

ATOMIC = "ATOMIC"
NON_ATOMIC = "NON_ATOMIC"
AMBIGUOUS = "AMBIGUOUS"

SOURCE_FACT_CONTENT = "SOURCE_FACT_CONTENT"
INTERPRETATION_CONTENT = "INTERPRETATION_CONTENT"
CREATIVE_CONTENT = "CREATIVE_CONTENT"
CONTEXT_LIMIT_CONTENT = "CONTEXT_LIMIT_CONTENT"
MIXED_CONTENT = "MIXED_CONTENT"

EXPECTED_CONTENT_TYPE = {
    ROLE_SOURCE_FACT: SOURCE_FACT_CONTENT,
    ROLE_INTERPRETATION: INTERPRETATION_CONTENT,
    ROLE_CREATIVE: CREATIVE_CONTENT,
}


@runtime_checkable
class ResidualAtomicityClassifierAdapter(Protocol):
    """Narrow V2-R-A classifier. It must classify atomicity only."""

    def classify(self, *, claim_text: str) -> dict[str, Any] | str: ...


@runtime_checkable
class ResidualContentTypeClassifierAdapter(Protocol):
    """Narrow V2-R-C content-only classifier.

    Expected role is deliberately not part of this interface.
    """

    def classify(self, *, claim_text: str) -> dict[str, Any] | str: ...


@runtime_checkable
class SourceFactSupportValidatorAdapter(Protocol):
    """V3/V4F integration boundary for one atomic source-fact candidate."""

    def validate(
        self,
        *,
        claim_text: str,
        support_units: list[dict[str, Any]],
    ) -> dict[str, Any] | str: ...


@runtime_checkable
class InterpretationDerivationValidatorAdapter(Protocol):
    """V4I boundary: conclusion derivation from Certified Fact premises only."""

    def validate(
        self,
        *,
        conclusion_text: str,
        premise_texts: list[str],
        premise_metadata: list[dict[str, Any]],
        purpose: str,
    ) -> dict[str, Any] | str: ...


def _normalize_verdict(
    result: dict[str, Any] | str,
    *,
    allowed: set[str],
    unavailable_verdict: str,
) -> dict[str, Any]:
    if isinstance(result, str):
        payload: dict[str, Any] = {"verdict": result}
    elif isinstance(result, dict):
        payload = dict(result)
    else:
        return {"verdict": unavailable_verdict, "raw_result_type": type(result).__name__}
    verdict = payload.get("verdict")
    if verdict not in allowed:
        payload["raw_verdict"] = verdict
        payload["verdict"] = unavailable_verdict
    return payload


def _candidate_digest_valid(candidate: dict[str, Any]) -> bool:
    expected = candidate.get("candidate_digest")
    if not isinstance(expected, str):
        return False
    payload = {key: value for key, value in candidate.items() if key != "candidate_digest"}
    return expected == digest_object(payload)


def _grounding_unit_map(grounded_context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(unit["ref_id"]): unit
        for unit in grounded_context.get("grounding_units", [])
        if isinstance(unit, dict) and isinstance(unit.get("ref_id"), str)
    }


def _component(
    name: str,
    result: str,
    *,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "component": name,
        "result": result,
        "evidence": dict(evidence or {}),
    }


class V4PropositionValidator:
    """Validate model-authored v4 propositions with frozen responsibility order."""

    def __init__(
        self,
        *,
        atomicity_classifier: ResidualAtomicityClassifierAdapter | None,
        content_type_classifier: ResidualContentTypeClassifierAdapter | None,
        source_fact_support: SourceFactSupportValidatorAdapter | None = None,
        interpretation_derivation: InterpretationDerivationValidatorAdapter | None = None,
    ) -> None:
        self.atomicity_classifier = atomicity_classifier
        self.content_type_classifier = content_type_classifier
        self.source_fact_support = source_fact_support
        self.interpretation_derivation = interpretation_derivation

    def validate_stage1_candidate(
        self,
        candidate: dict[str, Any],
        *,
        grounded_context: dict[str, Any],
        validation_record_id: str,
    ) -> dict[str, Any]:
        return self._validate(
            candidate,
            expected_path=PATH_STAGE1_FACT,
            expected_role=ROLE_SOURCE_FACT,
            grounded_context=grounded_context,
            certified_fact_map=None,
            validation_record_id=validation_record_id,
        )

    def validate_stage2_candidate(
        self,
        candidate: dict[str, Any],
        *,
        certified_content: dict[str, Any],
        validation_record_id: str,
    ) -> dict[str, Any]:
        path = candidate.get("path_provenance")
        if path == PATH_STAGE2_INTERPRETATION:
            role = ROLE_INTERPRETATION
        elif path == PATH_STAGE2_CREATIVE:
            role = ROLE_CREATIVE
        else:
            return self._record(
                validation_record_id=validation_record_id,
                candidate=candidate,
                normalized_role=None,
                components=[_component("V2-P", "FAIL")],
                verdict="FAIL",
                failure_codes=["UNKNOWN_PATH_PROVENANCE"],
            )
        fact_map = {
            str(fact["certified_fact_id"]): fact
            for fact in certified_content.get("facts", [])
            if isinstance(fact, dict) and isinstance(fact.get("certified_fact_id"), str)
        }
        return self._validate(
            candidate,
            expected_path=path,
            expected_role=role,
            grounded_context=None,
            certified_fact_map=fact_map,
            validation_record_id=validation_record_id,
        )

    def _validate(
        self,
        candidate: dict[str, Any],
        *,
        expected_path: str,
        expected_role: str,
        grounded_context: dict[str, Any] | None,
        certified_fact_map: dict[str, dict[str, Any]] | None,
        validation_record_id: str,
    ) -> dict[str, Any]:
        components: list[dict[str, Any]] = []
        failures: list[str] = []

        structural_ok = (
            candidate.get("candidate_contract_version") == STRUCTURED_PROPOSITION_VERSION
            and candidate.get("path_provenance") == expected_path
            and candidate.get("stage") in {"stage1", "stage2"}
            and isinstance(candidate.get("proposition_id"), str)
            and _candidate_digest_valid(candidate)
            and isinstance(candidate.get("payload"), dict)
            and isinstance(candidate.get("payload", {}).get("claim_text"), str)
            and bool(candidate.get("payload", {}).get("claim_text"))
        )
        components.append(_component("V2-S", "PASS" if structural_ok else "FAIL"))
        if not structural_ok:
            failures.append("V2_STRUCTURAL_FAILURE")
            return self._record(
                validation_record_id=validation_record_id,
                candidate=candidate,
                normalized_role=expected_role,
                components=components,
                verdict="FAIL",
                failure_codes=failures,
            )

        normalized_role = PATH_ROLE_MAP.get(candidate["path_provenance"])
        provenance_ok = normalized_role == expected_role
        components.append(
            _component(
                "V2-P",
                "PASS" if provenance_ok else "FAIL",
                evidence={"normalized_role": normalized_role, "path": expected_path},
            )
        )
        if not provenance_ok:
            failures.append("V2_PROVENANCE_FAILURE")
            return self._record(
                validation_record_id=validation_record_id,
                candidate=candidate,
                normalized_role=normalized_role,
                components=components,
                verdict="FAIL",
                failure_codes=failures,
            )

        deterministic_ok, deterministic_evidence, deterministic_failures = self._v2_d(
            candidate,
            expected_role=expected_role,
            grounded_context=grounded_context,
            certified_fact_map=certified_fact_map,
        )
        components.append(
            _component(
                "V2-D",
                "PASS" if deterministic_ok else "FAIL",
                evidence=deterministic_evidence,
            )
        )
        if not deterministic_ok:
            failures.extend(deterministic_failures)
            return self._record(
                validation_record_id=validation_record_id,
                candidate=candidate,
                normalized_role=normalized_role,
                components=components,
                verdict="FAIL",
                failure_codes=failures,
            )

        claim_text = candidate["payload"]["claim_text"]
        if self.atomicity_classifier is None:
            atomicity = {"verdict": "UNAVAILABLE"}
        else:
            atomicity = _normalize_verdict(
                self.atomicity_classifier.classify(claim_text=claim_text),
                allowed={ATOMIC, NON_ATOMIC, AMBIGUOUS, "UNAVAILABLE"},
                unavailable_verdict="UNAVAILABLE",
            )
        atomicity_pass = atomicity["verdict"] == ATOMIC
        components.append(
            _component("V2-R-A", "PASS" if atomicity_pass else "FAIL", evidence=atomicity)
        )
        if not atomicity_pass:
            failures.append(f"V2_ATOMICITY_{atomicity['verdict']}")
            return self._record(
                validation_record_id=validation_record_id,
                candidate=candidate,
                normalized_role=normalized_role,
                components=components,
                verdict="FAIL",
                failure_codes=failures,
            )

        if self.content_type_classifier is None:
            content_type = {"verdict": "UNAVAILABLE"}
        else:
            content_type = _normalize_verdict(
                self.content_type_classifier.classify(claim_text=claim_text),
                allowed={
                    SOURCE_FACT_CONTENT,
                    INTERPRETATION_CONTENT,
                    CREATIVE_CONTENT,
                    CONTEXT_LIMIT_CONTENT,
                    MIXED_CONTENT,
                    AMBIGUOUS,
                    "UNAVAILABLE",
                },
                unavailable_verdict="UNAVAILABLE",
            )
        expected_type = EXPECTED_CONTENT_TYPE[expected_role]
        content_pass = content_type["verdict"] == expected_type
        components.append(
            _component(
                "V2-R-C",
                "PASS" if content_pass else "FAIL",
                evidence={"expected": expected_type, **content_type},
            )
        )
        if not content_pass:
            failures.append(f"V2_CONTENT_TYPE_{content_type['verdict']}")
            return self._record(
                validation_record_id=validation_record_id,
                candidate=candidate,
                normalized_role=normalized_role,
                components=components,
                verdict="FAIL",
                failure_codes=failures,
            )

        if expected_role == ROLE_SOURCE_FACT:
            return self._validate_source_support(
                candidate,
                grounded_context=grounded_context or {},
                validation_record_id=validation_record_id,
                normalized_role=normalized_role,
                components=components,
                failures=failures,
            )
        if expected_role == ROLE_INTERPRETATION:
            return self._validate_interpretation(
                candidate,
                certified_fact_map=certified_fact_map or {},
                validation_record_id=validation_record_id,
                normalized_role=normalized_role,
                components=components,
                failures=failures,
            )

        return self._record(
            validation_record_id=validation_record_id,
            candidate=candidate,
            normalized_role=normalized_role,
            components=components,
            verdict="PASS",
            failure_codes=failures,
            source_support_aggregate_result="NOT_APPLICABLE",
        )

    def _v2_d(
        self,
        candidate: dict[str, Any],
        *,
        expected_role: str,
        grounded_context: dict[str, Any] | None,
        certified_fact_map: dict[str, dict[str, Any]] | None,
    ) -> tuple[bool, dict[str, Any], list[str]]:
        payload = candidate["payload"]
        purpose = candidate.get("purpose")
        failures: list[str] = []
        evidence: dict[str, Any] = {"purpose": purpose}

        if expected_role == ROLE_SOURCE_FACT:
            refs = payload.get("support_refs")
            if not isinstance(refs, list) or not refs:
                failures.append("SOURCE_FACT_SUPPORT_REFS_REQUIRED")
            if "premise_fact_ids" in payload:
                failures.append("SOURCE_FACT_PREMISE_BINDING_FORBIDDEN")
            unit_map = _grounding_unit_map(grounded_context or {})
            if isinstance(refs, list):
                if len(refs) != len(set(refs)):
                    failures.append("DUPLICATE_REFERENCE_ID")
                unknown = [ref for ref in refs if ref not in unit_map]
                if unknown:
                    failures.append("REFERENCE_ALLOWLIST_VIOLATION")
                    evidence["unknown_support_refs"] = unknown
            evidence["support_refs"] = list(refs or [])

        elif expected_role == ROLE_INTERPRETATION:
            premises = payload.get("premise_fact_ids")
            if not isinstance(premises, list) or not premises:
                failures.append("INTERPRETATION_PREMISES_REQUIRED")
            if "support_refs" in payload:
                failures.append("INTERPRETATION_SUPPORT_REFS_FORBIDDEN")
            if isinstance(premises, list):
                if len(premises) != len(set(premises)):
                    failures.append("DUPLICATE_REFERENCE_ID")
                unknown = [value for value in premises if value not in (certified_fact_map or {})]
                if unknown:
                    failures.append("CERTIFIED_FACT_BINDING_FAILURE")
                    evidence["unknown_premise_fact_ids"] = unknown
            evidence["premise_fact_ids"] = list(premises or [])

        elif expected_role == ROLE_CREATIVE:
            if purpose != "creative":
                failures.append("CREATIVE_PURPOSE_VIOLATION")
            if "support_refs" in payload:
                failures.append("CREATIVE_SUPPORT_REFS_FORBIDDEN")
            if "premise_fact_ids" in payload:
                failures.append("CREATIVE_PREMISE_BINDING_FORBIDDEN")

        return not failures, evidence, failures

    def _validate_source_support(
        self,
        candidate: dict[str, Any],
        *,
        grounded_context: dict[str, Any],
        validation_record_id: str,
        normalized_role: str | None,
        components: list[dict[str, Any]],
        failures: list[str],
    ) -> dict[str, Any]:
        unit_map = _grounding_unit_map(grounded_context)
        support_refs = candidate["payload"]["support_refs"]
        support_units = [unit_map[ref] for ref in support_refs]
        if self.source_fact_support is None:
            support = {"verdict": "UNAVAILABLE"}
        else:
            support = _normalize_verdict(
                self.source_fact_support.validate(
                    claim_text=candidate["payload"]["claim_text"],
                    support_units=support_units,
                ),
                allowed={
                    "SUPPORTED",
                    "UNSUPPORTED",
                    "CONTRADICTORY",
                    "INDETERMINATE",
                    "UNAVAILABLE",
                },
                unavailable_verdict="UNAVAILABLE",
            )
        support_pass = support["verdict"] == "SUPPORTED"
        components.append(
            _component("V3/V4F", "PASS" if support_pass else "FAIL", evidence=support)
        )
        if not support_pass:
            failures.append(f"SOURCE_SUPPORT_{support['verdict']}")
        return self._record(
            validation_record_id=validation_record_id,
            candidate=candidate,
            normalized_role=normalized_role,
            components=components,
            verdict="PASS" if support_pass else "FAIL",
            failure_codes=failures,
            source_support_aggregate_result="PASS" if support_pass else support["verdict"],
        )

    def _validate_interpretation(
        self,
        candidate: dict[str, Any],
        *,
        certified_fact_map: dict[str, dict[str, Any]],
        validation_record_id: str,
        normalized_role: str | None,
        components: list[dict[str, Any]],
        failures: list[str],
    ) -> dict[str, Any]:
        premises = candidate["payload"]["premise_fact_ids"]
        premise_facts = [certified_fact_map[value] for value in premises]
        if self.interpretation_derivation is None:
            derivation = {"verdict": "UNAVAILABLE"}
        else:
            derivation = _normalize_verdict(
                self.interpretation_derivation.validate(
                    conclusion_text=candidate["payload"]["claim_text"],
                    premise_texts=[fact["claim_text"] for fact in premise_facts],
                    premise_metadata=[
                        {
                            "certified_fact_id": fact["certified_fact_id"],
                            "source_proposition_id": fact["source_proposition_id"],
                        }
                        for fact in premise_facts
                    ],
                    purpose=str(candidate["purpose"]),
                ),
                allowed={
                    "DERIVED_SUPPORTED",
                    "REASONABLE_DERIVATION",
                    "UNSUPPORTED",
                    "CONTRADICTORY",
                    "INDETERMINATE",
                    "UNAVAILABLE",
                },
                unavailable_verdict="UNAVAILABLE",
            )
        derivation_pass = derivation["verdict"] in {"DERIVED_SUPPORTED", "REASONABLE_DERIVATION"}
        components.append(
            _component("V4I", "PASS" if derivation_pass else "FAIL", evidence=derivation)
        )
        if not derivation_pass:
            failures.append(f"INTERPRETATION_DERIVATION_{derivation['verdict']}")
        return self._record(
            validation_record_id=validation_record_id,
            candidate=candidate,
            normalized_role=normalized_role,
            components=components,
            verdict="PASS" if derivation_pass else "FAIL",
            failure_codes=failures,
            source_support_aggregate_result="NOT_APPLICABLE",
        )

    @staticmethod
    def _record(
        *,
        validation_record_id: str,
        candidate: dict[str, Any],
        normalized_role: str | None,
        components: list[dict[str, Any]],
        verdict: str,
        failure_codes: list[str],
        source_support_aggregate_result: str | None = None,
    ) -> dict[str, Any]:
        v2_components = [
            component for component in components if component["component"].startswith("V2")
        ]
        v2_pass = bool(v2_components) and all(
            component["result"] == "PASS" for component in v2_components
        )
        record = {
            "validation_contract_version": VALIDATION_RECORD_VERSION,
            "validation_record_id": validation_record_id,
            "source_proposition_id": candidate.get("proposition_id"),
            "source_candidate_digest": candidate.get("candidate_digest"),
            "context_fingerprint": candidate.get("context_fingerprint"),
            "path_provenance": candidate.get("path_provenance"),
            "normalized_role": normalized_role,
            "reference_integrity_result": next(
                (
                    component["result"]
                    for component in components
                    if component["component"] == "V2-D"
                ),
                "NOT_RUN",
            ),
            "v2_aggregate_result": "PASS" if v2_pass else "FAIL",
            "source_support_aggregate_result": (
                source_support_aggregate_result
                if source_support_aggregate_result is not None
                else "NOT_APPLICABLE"
            ),
            "component_evidence": components,
            "failure_codes": list(failure_codes),
            "verdict": verdict,
        }
        record["validation_record_digest"] = digest_object(record)
        return record


def certify_stage1_attempt(
    candidates: list[dict[str, Any]],
    validation_records: list[dict[str, Any]],
    *,
    request: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Certify eligible candidates from one active Stage 1 attempt only."""
    by_proposition = {
        str(record.get("source_proposition_id")): record for record in validation_records
    }
    facts: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    exact_seen: dict[tuple[str, tuple[str, ...]], str] = {}

    for candidate in candidates:
        proposition_id = str(candidate["proposition_id"])
        record = by_proposition.get(proposition_id)
        reason: str | None = None
        if record is None:
            reason = "NOT_CERTIFIED_BINDING_MISMATCH"
        elif record.get("source_candidate_digest") != candidate.get("candidate_digest"):
            reason = "NOT_CERTIFIED_BINDING_MISMATCH"
        elif record.get("v2_aggregate_result") != "PASS":
            reason = "NOT_CERTIFIED_V2_FAILURE"
        elif record.get("source_support_aggregate_result") != "PASS":
            if record.get("source_support_aggregate_result") in {
                "INDETERMINATE",
                "UNAVAILABLE",
            }:
                reason = "NOT_CERTIFIED_INDETERMINATE"
            else:
                reason = "NOT_CERTIFIED_SUPPORT_FAILURE"
        elif record.get("verdict") != "PASS":
            reason = "NOT_CERTIFIED_VALIDATION_FAILURE"

        key = (
            candidate["payload"]["claim_text"],
            tuple(candidate["payload"]["support_refs"]),
        )
        if reason is None and key in exact_seen:
            reason = "NOT_CERTIFIED_EXACT_DUPLICATE"

        if reason is not None:
            decisions.append(
                {
                    "source_proposition_id": proposition_id,
                    "certified": False,
                    "reason_code": reason,
                    "duplicate_of": exact_seen.get(key),
                }
            )
            continue

        certified_fact_id = f"CF{len(facts) + 1}"
        fact = {
            "certified_fact_id": certified_fact_id,
            "source_proposition_id": proposition_id,
            "source_candidate_digest": candidate["candidate_digest"],
            "claim_text": candidate["payload"]["claim_text"],
            "support_refs": list(candidate["payload"]["support_refs"]),
            "validation_record_id": record["validation_record_id"],
            "validation_record_digest": record["validation_record_digest"],
            "request_id": request["request_id"],
            "context_fingerprint": request["context_fingerprint"],
            "purpose": request["purpose"],
            "source_attempt": candidate["attempt"],
            "source_candidate_index": candidate["candidate_index"],
        }
        fact["certified_fact_digest"] = digest_object(fact)
        facts.append(fact)
        exact_seen[key] = certified_fact_id
        decisions.append(
            {
                "source_proposition_id": proposition_id,
                "certified": True,
                "certified_fact_id": certified_fact_id,
            }
        )

    content_seed = {
        "certified_content_contract_version": CERTIFIED_CONTENT_VERSION,
        "request_id": request["request_id"],
        "context_fingerprint": request["context_fingerprint"],
        "purpose": request["purpose"],
        "active_stage1_attempt": request["attempt"],
        "facts": facts,
    }
    seed_digest = digest_object(content_seed)
    content = {
        **content_seed,
        "certified_content_id": f"CC-{seed_digest[:16]}",
    }
    content["certified_content_digest"] = digest_object(content)
    return content, decisions


def materialize_certified_facts(
    certified_content: dict[str, Any],
    fact_ids: list[str],
) -> list[dict[str, Any]]:
    fact_map = {
        str(fact["certified_fact_id"]): fact for fact in certified_content.get("facts", [])
    }
    if len(fact_ids) != len(set(fact_ids)):
        raise ValueError("duplicate Certified Fact ID in main block")
    materialized: list[dict[str, Any]] = []
    for fact_id in fact_ids:
        fact = fact_map.get(fact_id)
        if fact is None:
            raise ValueError(f"unknown Certified Fact ID: {fact_id}")
        materialized.append(
            {
                "path_provenance": PATH_CERTIFIED_FACT,
                "normalized_role": ROLE_SOURCE_FACT,
                "certified_fact_id": fact_id,
                "claim_text": fact["claim_text"],
                "source_proposition_id": fact["source_proposition_id"],
                "certified_fact_digest": fact["certified_fact_digest"],
            }
        )
    return materialized


def build_validated_presentation_plan(
    parsed_stage2: dict[str, Any],
    *,
    request: dict[str, Any],
    certified_content: dict[str, Any],
    candidate_envelopes: list[dict[str, Any]],
    validation_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a plan only when the entire Stage 2 attempt is valid."""
    by_proposition = {
        str(record.get("source_proposition_id")): record for record in validation_records
    }
    envelope_by_location = {
        (int(candidate["block_index"]), int(candidate["candidate_index"])): candidate
        for candidate in candidate_envelopes
    }
    blocks: list[dict[str, Any]] = []

    for block_index, block in enumerate(parsed_stage2["blocks"]):
        kind = block["block_kind"]
        if kind == "main":
            items = materialize_certified_facts(
                certified_content,
                list(block["certified_fact_ids"]),
            )
            blocks.append({"block_kind": "main", "items": items})
            continue

        validated_items: list[dict[str, Any]] = []
        for candidate_index, _payload in enumerate(block["candidates"]):
            candidate = envelope_by_location[(block_index, candidate_index)]
            record = by_proposition.get(candidate["proposition_id"])
            if record is None or record.get("verdict") != "PASS":
                raise ValueError("Stage 2 plan contains an unvalidated proposition")
            item = {
                "path_provenance": candidate["path_provenance"],
                "normalized_role": record["normalized_role"],
                "proposition_id": candidate["proposition_id"],
                "claim_text": candidate["payload"]["claim_text"],
                "candidate_digest": candidate["candidate_digest"],
                "validation_record_id": record["validation_record_id"],
                "validation_record_digest": record["validation_record_digest"],
            }
            if kind == "interpretation":
                item["premise_fact_ids"] = list(candidate["payload"]["premise_fact_ids"])
            validated_items.append(item)
        blocks.append({"block_kind": kind, "items": validated_items})

    plan = {
        "validated_presentation_plan_contract_version": VALIDATED_PLAN_VERSION,
        "plan_id": f"VP-{digest_object({'request': request['stage2_request_id'], 'a': request['attempt']})[:16]}",
        "stage2_request_id": request["stage2_request_id"],
        "certified_content_id": request["certified_content_id"],
        "certified_content_digest": request["certified_content_digest"],
        "context_fingerprint": request["context_fingerprint"],
        "purpose": request["purpose"],
        "attempt": request["attempt"],
        "blocks": blocks,
    }
    plan["validated_presentation_plan_digest"] = digest_object(plan)
    return plan
