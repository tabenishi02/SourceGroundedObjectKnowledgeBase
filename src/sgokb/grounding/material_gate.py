"""Deterministic-first material/use-case completion gate for N-04 v3."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .output import is_context_limit_output, output_binding

MATERIAL_REQUIREMENT_CONTRACT_VERSION = "sgokb.material-requirement.v1"
MATERIAL_PASS = "PASS"
MATERIAL_FAIL_REPAIRABLE = "FAIL_REPAIRABLE"
MATERIAL_FAIL_CONTEXT_INSUFFICIENT = "FAIL_CONTEXT_INSUFFICIENT"
MATERIAL_INDETERMINATE = "INDETERMINATE"


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def default_requirement_profile(purpose: str, grounded_context: dict[str, Any]) -> dict[str, Any]:
    object_ids = [
        item["object_id"]
        for item in grounded_context.get("objects", [])
        if isinstance(item, dict) and isinstance(item.get("object_id"), str)
    ]
    base: dict[str, Any] = {
        "profile_id": f"sgokb-generic-{purpose}",
        "profile_version": "1",
        "required_source_object_ids": [],
        "minimum_supported_source_fact_units": 0,
        "minimum_source_fact_per_object": 0,
        "minimum_interpretation_units": 0,
        "require_cross_source_interpretation": False,
        "minimum_creative_addition_units": 0,
    }
    if purpose == "roleplay":
        base["minimum_supported_source_fact_units"] = 1
    elif purpose == "comparison":
        base["required_source_object_ids"] = object_ids
        base["minimum_source_fact_per_object"] = 1
        base["minimum_interpretation_units"] = 1
    elif purpose == "creative":
        base["required_source_object_ids"] = object_ids
        base["minimum_source_fact_per_object"] = 1
        base["minimum_creative_addition_units"] = 1
    return base


def _failure(failure_class: str, failure_code: str, *, retryable: bool, system_failure: bool = False, **details: Any) -> dict[str, Any]:
    return {
        "failure_class": failure_class,
        "failure_code": failure_code,
        "retryable": retryable,
        "system_failure": system_failure,
        **details,
    }


class MaterialRequirementGate:
    contract_version = MATERIAL_REQUIREMENT_CONTRACT_VERSION

    def evaluate(
        self,
        grounded_context: dict[str, Any],
        validation: dict[str, Any],
        *,
        requirement_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        output = validation.get("output")
        binding = validation.get("binding")
        if validation.get("verdict") != "PASS" or not isinstance(output, dict):
            return self._indeterminate(output, binding, requirement_profile, "material_gate_requires_grounding_pass", "Material gate requires a parsed Grounding PASS candidate.")
        if not isinstance(binding, dict):
            return self._indeterminate(output, binding, requirement_profile, "missing_validation_binding", "Validation result has no candidate identity binding.")
        expected_binding = output_binding(output, attempt=binding.get("attempt"))
        if binding != expected_binding:
            return self._indeterminate(output, binding, requirement_profile, "validation_binding_mismatch", "Validation binding does not match the parsed output candidate.")

        purpose = output.get("purpose")
        profile = dict(requirement_profile) if requirement_profile is not None else default_requirement_profile(str(purpose), grounded_context)
        profile_error = self._validate_profile(profile, grounded_context)
        if profile_error is not None:
            return {
                "requirement_contract_version": self.contract_version,
                "verdict": MATERIAL_INDETERMINATE,
                "purpose": purpose,
                "profile": profile,
                "profile_id": profile.get("profile_id"),
                "profile_hash": _canonical_hash(profile),
                "binding": dict(binding),
                "checks": [],
                "covered_source_object_ids": [],
                "missing_source_object_ids": [],
                "context_insufficient": False,
                "failures": [_failure("MATERIAL_REQUIREMENT_INDETERMINATE", "invalid_requirement_profile", retryable=False, system_failure=True, detail=profile_error)],
            }

        ref_to_object = {
            unit.get("ref_id"): unit.get("object_id")
            for unit in grounded_context.get("grounding_units", [])
            if isinstance(unit, dict)
        }
        available_by_object: dict[str, int] = {}
        for unit in grounded_context.get("grounding_units", []):
            if isinstance(unit, dict) and isinstance(unit.get("object_id"), str):
                oid = unit["object_id"]
                available_by_object[oid] = available_by_object.get(oid, 0) + 1

        output_units = {
            unit["unit_id"]: unit
            for block in output.get("blocks", [])
            for unit in block.get("units", [])
            if isinstance(unit, dict) and isinstance(unit.get("unit_id"), str)
        }
        result_by_id = {
            item["unit_id"]: item
            for item in validation.get("unit_results", [])
            if isinstance(item, dict) and isinstance(item.get("unit_id"), str)
        }
        supported_source_units = {
            uid: output_units[uid]
            for uid, result in result_by_id.items()
            if result.get("semantic_role") == "source_fact" and result.get("grounding_disposition") == "supported" and uid in output_units
        }
        derived_interpretations = {
            uid: output_units[uid]
            for uid, result in result_by_id.items()
            if result.get("semantic_role") == "interpretation" and result.get("grounding_disposition") == "derived_supported" and uid in output_units
        }
        creative_units = {
            uid: output_units[uid]
            for uid, result in result_by_id.items()
            if result.get("semantic_role") == "creative_addition" and result.get("grounding_disposition") == "not_applicable" and uid in output_units
        }

        source_objects_by_unit: dict[str, set[str]] = {}
        coverage_count: dict[str, int] = {}
        for uid, unit in supported_source_units.items():
            object_ids = {
                ref_to_object.get(ref)
                for ref in unit.get("support_refs", [])
                if isinstance(ref_to_object.get(ref), str)
            }
            source_objects_by_unit[uid] = {str(value) for value in object_ids}
            for object_id in source_objects_by_unit[uid]:
                coverage_count[object_id] = coverage_count.get(object_id, 0) + 1

        required_objects = list(profile["required_source_object_ids"])
        min_per_object = profile["minimum_source_fact_per_object"]
        minimum_total = profile["minimum_supported_source_fact_units"]
        minimum_interpretations = profile["minimum_interpretation_units"]
        minimum_creative = profile["minimum_creative_addition_units"]
        checks: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        context_insufficient = False

        total_ok = len(supported_source_units) >= minimum_total
        checks.append({"check": "minimum_supported_source_fact_units", "required": minimum_total, "actual": len(supported_source_units), "pass": total_ok})
        if not total_ok:
            context_capacity = sum(available_by_object.values())
            insufficient = context_capacity < minimum_total
            context_insufficient = context_insufficient or insufficient
            failures.append(_failure("MATERIAL_REQUIREMENT_MISSING", "minimum_supported_source_fact_units_missing", retryable=not insufficient, required=minimum_total, actual=len(supported_source_units), available_context_units=context_capacity))

        missing_objects: list[str] = []
        for object_id in required_objects:
            actual = coverage_count.get(object_id, 0)
            passed = actual >= min_per_object
            checks.append({"check": "source_object_coverage", "object_id": object_id, "required": min_per_object, "actual": actual, "pass": passed})
            if not passed:
                missing_objects.append(object_id)
                insufficient = available_by_object.get(object_id, 0) < min_per_object
                context_insufficient = context_insufficient or insufficient
                failure_class = "COMPARISON_COVERAGE_INCOMPLETE" if purpose == "comparison" else "CREATIVE_SOURCE_COVERAGE_INCOMPLETE" if purpose == "creative" else "SOURCE_COVERAGE_MISSING"
                failures.append(_failure(failure_class, "required_source_object_coverage_missing", retryable=not insufficient, object_id=object_id, required=min_per_object, actual=actual, available_context_units=available_by_object.get(object_id, 0)))

        interpretations_ok = len(derived_interpretations) >= minimum_interpretations
        checks.append({"check": "minimum_interpretation_units", "required": minimum_interpretations, "actual": len(derived_interpretations), "pass": interpretations_ok})
        if not interpretations_ok:
            failures.append(_failure("MATERIAL_REQUIREMENT_MISSING", "minimum_interpretation_units_missing", retryable=True, required=minimum_interpretations, actual=len(derived_interpretations)))

        if profile["require_cross_source_interpretation"]:
            cross_source_ok = False
            required_set = set(required_objects)
            for unit in derived_interpretations.values():
                premise_objects: set[str] = set()
                for premise_id in unit.get("premise_unit_ids", []):
                    premise_objects.update(source_objects_by_unit.get(premise_id, set()))
                if required_set and required_set.issubset(premise_objects):
                    cross_source_ok = True
                    break
            checks.append({"check": "cross_source_interpretation", "required_source_object_ids": required_objects, "pass": cross_source_ok})
            if not cross_source_ok:
                impossible = any(available_by_object.get(object_id, 0) < max(1, min_per_object) for object_id in required_objects)
                context_insufficient = context_insufficient or impossible
                failures.append(_failure("COMPARISON_COVERAGE_INCOMPLETE", "cross_source_interpretation_missing", retryable=not impossible, required_source_object_ids=required_objects))

        creative_ok = len(creative_units) >= minimum_creative
        checks.append({"check": "minimum_creative_addition_units", "required": minimum_creative, "actual": len(creative_units), "pass": creative_ok})
        if not creative_ok:
            failures.append(_failure("CREATIVE_ADDITION_MISSING", "minimum_creative_addition_units_missing", retryable=True, required=minimum_creative, actual=len(creative_units)))

        context_limit = is_context_limit_output(output)
        if context_limit:
            if context_insufficient:
                verdict = MATERIAL_FAIL_CONTEXT_INSUFFICIENT
            else:
                verdict = MATERIAL_FAIL_REPAIRABLE
                failures.append(_failure("CONTEXT_LIMIT_NOT_JUSTIFIED", "context_limit_not_justified", retryable=True))
        elif not failures:
            verdict = MATERIAL_PASS
        elif context_insufficient:
            verdict = MATERIAL_FAIL_CONTEXT_INSUFFICIENT
        else:
            verdict = MATERIAL_FAIL_REPAIRABLE

        covered = sorted(object_id for object_id in required_objects if coverage_count.get(object_id, 0) >= min_per_object)
        return {
            "requirement_contract_version": self.contract_version,
            "verdict": verdict,
            "purpose": purpose,
            "profile": profile,
            "profile_id": profile["profile_id"],
            "profile_hash": _canonical_hash(profile),
            "binding": dict(binding),
            "checks": checks,
            "covered_source_object_ids": covered,
            "missing_source_object_ids": sorted(missing_objects),
            "context_insufficient": context_insufficient,
            "failures": failures,
        }

    @staticmethod
    def _validate_profile(profile: dict[str, Any], grounded_context: dict[str, Any]) -> str | None:
        if not isinstance(profile.get("profile_id"), str) or not profile["profile_id"]:
            return "profile_id must be a non-empty string"
        if not isinstance(profile.get("profile_version"), str) or not profile["profile_version"]:
            return "profile_version must be a non-empty string"
        for field in ("minimum_supported_source_fact_units", "minimum_source_fact_per_object", "minimum_interpretation_units", "minimum_creative_addition_units"):
            value = profile.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                return f"{field} must be an integer >= 0"
        required = profile.get("required_source_object_ids")
        if not isinstance(required, list) or any(not isinstance(item, str) or not item for item in required) or len(set(required)) != len(required):
            return "required_source_object_ids must be a unique string list"
        if not isinstance(profile.get("require_cross_source_interpretation"), bool):
            return "require_cross_source_interpretation must be boolean"
        known = {item.get("object_id") for item in grounded_context.get("objects", []) if isinstance(item, dict)}
        unknown = [item for item in required if item not in known]
        if unknown:
            return f"required source objects are not present in Grounded Context: {unknown}"
        return None

    def _indeterminate(self, output: dict[str, Any] | None, binding: dict[str, Any] | None, requirement_profile: dict[str, Any] | None, failure_code: str, detail: str) -> dict[str, Any]:
        profile = dict(requirement_profile or {"profile_id": "unknown", "profile_version": "0"})
        return {
            "requirement_contract_version": self.contract_version,
            "verdict": MATERIAL_INDETERMINATE,
            "purpose": output.get("purpose") if isinstance(output, dict) else None,
            "profile": profile,
            "profile_id": profile.get("profile_id"),
            "profile_hash": _canonical_hash(profile),
            "binding": dict(binding) if isinstance(binding, dict) else None,
            "checks": [],
            "covered_source_object_ids": [],
            "missing_source_object_ids": [],
            "context_insufficient": False,
            "failures": [_failure("MATERIAL_REQUIREMENT_INDETERMINATE", failure_code, retryable=False, system_failure=True, detail=detail)],
        }
