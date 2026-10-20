"""Pre-V2 reference-integrity gate for the frozen v4 pipeline."""

from __future__ import annotations

from typing import Any

from .v4_contracts import VALIDATION_RECORD_VERSION, digest_object


def validate_stage1_reference_integrity(
    candidate: dict[str, Any],
    *,
    grounded_context: dict[str, Any],
) -> dict[str, Any]:
    unit_ids = {
        str(unit["ref_id"])
        for unit in grounded_context.get("grounding_units", [])
        if isinstance(unit, dict) and isinstance(unit.get("ref_id"), str)
    }
    payload = candidate.get("payload")
    refs = payload.get("support_refs") if isinstance(payload, dict) else None
    failures: list[str] = []

    if candidate.get("context_fingerprint") != grounded_context.get("context_fingerprint"):
        failures.append("CONTEXT_FINGERPRINT_BINDING_FAILURE")
    if candidate.get("purpose") != grounded_context.get("purpose"):
        failures.append("PURPOSE_BINDING_FAILURE")
    if not isinstance(refs, list) or not refs:
        failures.append("SOURCE_FACT_SUPPORT_REFS_REQUIRED")
        refs = []
    if len(refs) != len(set(refs)):
        failures.append("DUPLICATE_REFERENCE_ID")
    unknown = [ref for ref in refs if ref not in unit_ids]
    if unknown:
        failures.append("REFERENCE_ALLOWLIST_VIOLATION")

    return {
        "result": "PASS" if not failures else "FAIL",
        "failure_codes": failures,
        "support_refs": list(refs),
        "unknown_support_refs": unknown,
    }


def reference_failure_record(
    candidate: dict[str, Any],
    *,
    validation_record_id: str,
    reference_result: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "validation_contract_version": VALIDATION_RECORD_VERSION,
        "validation_record_id": validation_record_id,
        "source_proposition_id": candidate.get("proposition_id"),
        "source_candidate_digest": candidate.get("candidate_digest"),
        "context_fingerprint": candidate.get("context_fingerprint"),
        "path_provenance": candidate.get("path_provenance"),
        "normalized_role": "source_fact",
        "reference_integrity_result": "FAIL",
        "v2_aggregate_result": "NOT_RUN",
        "source_support_aggregate_result": "NOT_RUN",
        "component_evidence": [
            {
                "component": "REFERENCE_INTEGRITY",
                "result": "FAIL",
                "evidence": dict(reference_result),
            }
        ],
        "failure_codes": list(reference_result["failure_codes"]),
        "verdict": "FAIL",
    }
    record["validation_record_digest"] = digest_object(record)
    return record


def bind_reference_pass(
    record: dict[str, Any],
    *,
    reference_result: dict[str, Any],
) -> dict[str, Any]:
    updated = {
        key: value
        for key, value in record.items()
        if key != "validation_record_digest"
    }
    updated["reference_integrity_result"] = "PASS"
    updated["component_evidence"] = [
        {
            "component": "REFERENCE_INTEGRITY",
            "result": "PASS",
            "evidence": dict(reference_result),
        },
        *list(updated.get("component_evidence", [])),
    ]
    updated["validation_record_digest"] = digest_object(updated)
    return updated
