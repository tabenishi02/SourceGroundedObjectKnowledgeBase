"""v4 orchestration helpers: material gates, retry, terminal, evidence, and render."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .v4_contracts import (
    RETRY_FEEDBACK_VERSION,
    SYSTEM_CONTEXT_LIMIT_VERSION,
    V4_RUN_VERSION,
    VALIDATED_PLAN_VERSION,
    canonical_json_bytes,
    digest_object,
    sha256_bytes,
)

STAGE_READY = "READY"
STAGE_RETRYABLE = "RETRYABLE"
STAGE_IMPOSSIBLE = "IMPOSSIBLE"

MATERIAL_PASS = "PASS"
MATERIAL_FAIL_REPAIRABLE = "FAIL_REPAIRABLE"
MATERIAL_FAIL_CONTEXT_INSUFFICIENT = "FAIL_CONTEXT_INSUFFICIENT"

ACTION_RETRY = "RETRY"
TERMINAL_ACCEPTED = "ACCEPTED"
TERMINAL_INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
TERMINAL_REJECTED = "REJECTED"
TERMINAL_SYSTEM_FAILURE = "SYSTEM_FAILURE"

MAX_STAGE_ATTEMPTS = 2
MAX_STAGE_RETRIES = 1

REQUIRED_PROVIDER_PROBE_CASES = (
    "stage1_empty_candidates",
    "stage1_valid_candidate",
    "stage1_extra_property",
    "stage1_invalid_support_ref",
    "stage2_valid_main",
    "stage2_valid_interpretation",
    "stage2_creative_under_creative_purpose",
    "stage2_invalid_certified_fact_id",
    "application_rejects_duplicate_support_or_premise_ids",
    "application_rejects_duplicate_block_kind",
    "provider_incomplete_or_interrupted",
)


def _unit_map(grounded_context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(unit["ref_id"]): unit
        for unit in grounded_context.get("grounding_units", [])
        if isinstance(unit, dict) and isinstance(unit.get("ref_id"), str)
    }


def _fact_object_ids(
    fact: dict[str, Any],
    *,
    grounded_context: dict[str, Any],
) -> set[str]:
    units = _unit_map(grounded_context)
    result: set[str] = set()
    for ref in fact.get("support_refs", []):
        unit = units.get(str(ref))
        if unit and isinstance(unit.get("object_id"), str):
            result.add(str(unit["object_id"]))
    return result


class V4MaterialRequirementGate:
    """Evaluate frozen v3-style material profiles against v4 artifacts."""

    def evaluate_stage1_readiness(
        self,
        *,
        certified_content: dict[str, Any],
        grounded_context: dict[str, Any],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        facts = list(certified_content.get("facts", []))
        required_objects = [
            str(value) for value in profile.get("required_source_objects", [])
        ]
        minimum_total = int(
            profile.get("minimum_supported_source_fact_units", 0) or 0
        )
        minimum_per_object = int(
            profile.get("minimum_source_fact_per_object", 0) or 0
        )

        covered_counts = {object_id: 0 for object_id in required_objects}
        for fact in facts:
            for object_id in _fact_object_ids(
                fact,
                grounded_context=grounded_context,
            ):
                if object_id in covered_counts:
                    covered_counts[object_id] += 1

        missing_codes: list[str] = []
        if len(facts) < minimum_total:
            missing_codes.append("minimum_supported_source_fact_units")
        for object_id, count in covered_counts.items():
            if count < minimum_per_object:
                missing_codes.append(f"minimum_source_fact_per_object:{object_id}")

        if not missing_codes:
            verdict = STAGE_READY
        elif self._context_can_satisfy(
            grounded_context=grounded_context,
            profile=profile,
        ):
            verdict = STAGE_RETRYABLE
        else:
            verdict = STAGE_IMPOSSIBLE

        result = {
            "verdict": verdict,
            "profile_id": profile.get("profile_id"),
            "profile_hash": profile.get("profile_hash"),
            "certified_fact_count": len(facts),
            "covered_source_object_counts": covered_counts,
            "missing_requirement_codes": missing_codes,
        }
        result["result_digest"] = digest_object(result)
        return result

    def evaluate_final(
        self,
        *,
        validated_plan: dict[str, Any],
        certified_content: dict[str, Any],
        grounded_context: dict[str, Any],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        fact_map = {
            str(fact["certified_fact_id"]): fact
            for fact in certified_content.get("facts", [])
        }
        main_ids: list[str] = []
        interpretations: list[dict[str, Any]] = []
        creative: list[dict[str, Any]] = []
        for block in validated_plan.get("blocks", []):
            if block.get("block_kind") == "main":
                main_ids.extend(
                    str(item["certified_fact_id"])
                    for item in block.get("items", [])
                )
            elif block.get("block_kind") == "interpretation":
                interpretations.extend(block.get("items", []))
            elif block.get("block_kind") == "creative":
                creative.extend(block.get("items", []))

        required_objects = [
            str(value) for value in profile.get("required_source_objects", [])
        ]
        covered_counts = {object_id: 0 for object_id in required_objects}
        for fact_id in main_ids:
            fact = fact_map[fact_id]
            for object_id in _fact_object_ids(
                fact,
                grounded_context=grounded_context,
            ):
                if object_id in covered_counts:
                    covered_counts[object_id] += 1

        missing: list[str] = []
        minimum_total = int(
            profile.get("minimum_supported_source_fact_units", 0) or 0
        )
        if len(main_ids) < minimum_total:
            missing.append("minimum_supported_source_fact_units")
        minimum_per_object = int(
            profile.get("minimum_source_fact_per_object", 0) or 0
        )
        for object_id, count in covered_counts.items():
            if count < minimum_per_object:
                missing.append(f"minimum_source_fact_per_object:{object_id}")

        minimum_interpretations = int(
            profile.get("minimum_interpretation_units", 0) or 0
        )
        if len(interpretations) < minimum_interpretations:
            missing.append("minimum_interpretation_units")

        minimum_creative = int(
            profile.get("minimum_creative_addition_units", 0) or 0
        )
        if len(creative) < minimum_creative:
            missing.append("minimum_creative_addition_units")

        if profile.get("require_cross_source_interpretation"):
            if not self._has_cross_source_interpretation(
                interpretations,
                fact_map=fact_map,
                grounded_context=grounded_context,
                required_objects=set(required_objects),
            ):
                missing.append("require_cross_source_interpretation")

        if not missing:
            verdict = MATERIAL_PASS
        elif self._context_can_satisfy(
            grounded_context=grounded_context,
            profile=profile,
        ):
            verdict = MATERIAL_FAIL_REPAIRABLE
        else:
            verdict = MATERIAL_FAIL_CONTEXT_INSUFFICIENT

        result = {
            "verdict": verdict,
            "profile_id": profile.get("profile_id"),
            "profile_hash": profile.get("profile_hash"),
            "main_certified_fact_ids": main_ids,
            "interpretation_count": len(interpretations),
            "creative_count": len(creative),
            "covered_source_object_counts": covered_counts,
            "missing_requirement_codes": missing,
        }
        result["result_digest"] = digest_object(result)
        return result

    @staticmethod
    def _context_can_satisfy(
        *,
        grounded_context: dict[str, Any],
        profile: dict[str, Any],
    ) -> bool:
        required_objects = [
            str(value) for value in profile.get("required_source_objects", [])
        ]
        units = list(grounded_context.get("grounding_units", []))
        by_object = {
            object_id: [
                unit
                for unit in units
                if isinstance(unit, dict)
                and unit.get("object_id") == object_id
            ]
            for object_id in required_objects
        }
        minimum_total = int(
            profile.get("minimum_supported_source_fact_units", 0) or 0
        )
        minimum_per_object = int(
            profile.get("minimum_source_fact_per_object", 0) or 0
        )
        if minimum_total and len(units) < minimum_total:
            return False
        if minimum_per_object and any(
            len(by_object[object_id]) < minimum_per_object
            for object_id in required_objects
        ):
            return False
        if any(not by_object[object_id] for object_id in required_objects):
            return False
        return True

    @staticmethod
    def _has_cross_source_interpretation(
        interpretations: list[dict[str, Any]],
        *,
        fact_map: dict[str, dict[str, Any]],
        grounded_context: dict[str, Any],
        required_objects: set[str],
    ) -> bool:
        if not required_objects:
            return bool(interpretations)
        for item in interpretations:
            premise_objects: set[str] = set()
            for fact_id in item.get("premise_fact_ids", []):
                fact = fact_map.get(str(fact_id))
                if fact is not None:
                    premise_objects |= _fact_object_ids(
                        fact,
                        grounded_context=grounded_context,
                    )
            if required_objects.issubset(premise_objects):
                return True
        return False


@dataclass
class ActiveAttemptLedger:
    """Track active stage attempts without fallback or cross-attempt merge."""

    active_attempts: dict[str, int] = field(default_factory=dict)
    retry_authorized: set[str] = field(default_factory=set)

    def activate(self, stage: str, attempt: int) -> None:
        if stage not in {"stage1", "stage2"}:
            raise ValueError("stage must be stage1 or stage2")
        if attempt not in {1, 2}:
            raise ValueError("attempt must be 1 or 2")
        if stage == "stage1" and "stage2" in self.active_attempts:
            raise ValueError("Stage 2 has started; Stage 1 backtracking is forbidden")
        current = self.active_attempts.get(stage)
        if current == 2 and attempt == 1:
            raise ValueError("attempt 1 fallback is forbidden after attempt 2 activation")
        if attempt == 2 and stage not in self.retry_authorized:
            raise ValueError("attempt 2 requires explicit retry authorization")
        self.active_attempts[stage] = attempt

    def authorize_retry(self, stage: str, *, previous_attempt: int) -> None:
        if previous_attempt != 1:
            raise ValueError("only one retry is permitted")
        if stage not in {"stage1", "stage2"}:
            raise ValueError("stage must be stage1 or stage2")
        if stage == "stage1" and "stage2" in self.active_attempts:
            raise ValueError("Stage 2 has started; Stage 1 backtracking is forbidden")
        self.retry_authorized.add(stage)

    def assert_active(self, stage: str, attempt: int) -> None:
        if self.active_attempts.get(stage) != attempt:
            raise ValueError(f"{stage} attempt {attempt} is not the active attempt")


class V4RetryController:
    """Fail-closed stage-local retry / terminal policy."""

    max_attempts = MAX_STAGE_ATTEMPTS
    max_retries = MAX_STAGE_RETRIES

    def decide(
        self,
        *,
        stage: str,
        attempt: int,
        retryable: bool,
        impossible: bool = False,
        system_failure: bool = False,
    ) -> dict[str, Any]:
        if stage not in {"stage1", "stage2"}:
            raise ValueError("stage must be stage1 or stage2")
        if attempt not in {1, 2}:
            raise ValueError("attempt must be 1 or 2")
        if system_failure:
            action = TERMINAL_SYSTEM_FAILURE
        elif impossible:
            action = TERMINAL_INSUFFICIENT_CONTEXT
        elif retryable and attempt == 1:
            action = ACTION_RETRY
        else:
            action = TERMINAL_REJECTED
        return {
            "stage": stage,
            "attempt": attempt,
            "action": action,
            "retry": action == ACTION_RETRY,
            "terminal": action != ACTION_RETRY,
            "max_attempts": self.max_attempts,
            "max_retries": self.max_retries,
        }

    def build_retry_feedback(
        self,
        *,
        stage: str,
        previous_attempt_id: str,
        previous_output_digest: str,
        failures: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if stage not in {"stage1", "stage2"}:
            raise ValueError("stage must be stage1 or stage2")
        if not failures:
            raise ValueError("retry feedback requires at least one failure")
        normalized: list[dict[str, Any]] = []
        for item in failures:
            normalized.append(
                {
                    "failure_scope": item.get("failure_scope"),
                    "failure_code": item.get("failure_code"),
                    "json_path": item.get("json_path"),
                    "proposition_id": item.get("proposition_id"),
                    "claim_text": item.get("claim_text"),
                    "support_refs": list(item.get("support_refs", [])),
                    "premise_fact_ids": list(item.get("premise_fact_ids", [])),
                    "expected_rule": item.get("expected_rule"),
                    "repair_directive": item.get("repair_directive"),
                }
            )
        feedback = {
            "retry_contract_version": RETRY_FEEDBACK_VERSION,
            "stage": stage,
            "previous_attempt": 1,
            "next_attempt": 2,
            "previous_attempt_id": previous_attempt_id,
            "previous_output_digest": previous_output_digest,
            "failures": normalized,
        }
        feedback["retry_feedback_digest"] = digest_object(feedback)
        return feedback


def build_system_context_limit(
    *,
    context_limit_id: str,
    stage_at_detection: str,
    request_id: str,
    context_fingerprint: str,
    profile: dict[str, Any],
    missing_requirement_codes: list[str],
    authoritative_input_digest: str,
) -> dict[str, Any]:
    artifact = {
        "contract_version": SYSTEM_CONTEXT_LIMIT_VERSION,
        "context_limit_id": context_limit_id,
        "reason_code": "material_requirements_not_satisfied",
        "stage_at_detection": stage_at_detection,
        "request_id": request_id,
        "context_fingerprint": context_fingerprint,
        "material_profile_id": profile.get("profile_id"),
        "material_profile_hash": profile.get("profile_hash"),
        "missing_requirement_codes": list(missing_requirement_codes),
        "authoritative_input_digest": authoritative_input_digest,
    }
    artifact["context_limit_digest"] = digest_object(artifact)
    return artifact


def terminal_from_material(
    material_result: dict[str, Any],
    *,
    validation_pass: bool,
    system_failure: bool = False,
) -> dict[str, Any]:
    if system_failure:
        outcome = TERMINAL_SYSTEM_FAILURE
    elif not validation_pass:
        outcome = TERMINAL_REJECTED
    elif material_result.get("verdict") == MATERIAL_PASS:
        outcome = TERMINAL_ACCEPTED
    elif material_result.get("verdict") == MATERIAL_FAIL_CONTEXT_INSUFFICIENT:
        outcome = TERMINAL_INSUFFICIENT_CONTEXT
    else:
        outcome = TERMINAL_REJECTED
    decision = {
        "outcome": outcome,
        "render_authorized": outcome == TERMINAL_ACCEPTED,
        "context_limit_render_authorized": outcome
        == TERMINAL_INSUFFICIENT_CONTEXT,
        "material_result_digest": material_result.get("result_digest"),
    }
    decision["terminal_decision_digest"] = digest_object(decision)
    return decision


class V4DeterministicRenderer:
    """Render only validated plans or a system context-limit artifact."""

    def render_accepted(
        self,
        *,
        validated_plan: dict[str, Any],
        terminal_decision: dict[str, Any],
    ) -> str:
        if (
            validated_plan.get("validated_presentation_plan_contract_version")
            != VALIDATED_PLAN_VERSION
        ):
            raise ValueError("renderer requires sgokb.validated-presentation-plan.v1")
        if terminal_decision.get("outcome") != TERMINAL_ACCEPTED:
            raise ValueError("normal render requires ACCEPTED terminal")
        sections: list[str] = []
        for block in validated_plan.get("blocks", []):
            kind = block["block_kind"]
            lines = [str(item["claim_text"]) for item in block.get("items", [])]
            if not lines:
                continue
            heading = {
                "main": "Facts",
                "interpretation": "Interpretation",
                "creative": "Creative addition",
            }[kind]
            body = "\n".join(f"- {line}" for line in lines)
            sections.append(f"{heading}:\n{body}")
        return "\n\n".join(sections)

    def render_context_limit(
        self,
        *,
        context_limit: dict[str, Any],
        terminal_decision: dict[str, Any],
    ) -> str:
        if context_limit.get("contract_version") != SYSTEM_CONTEXT_LIMIT_VERSION:
            raise ValueError("invalid system context-limit artifact")
        if terminal_decision.get("outcome") != TERMINAL_INSUFFICIENT_CONTEXT:
            raise ValueError("context-limit render requires INSUFFICIENT_CONTEXT")
        return (
            "The supplied grounded context is insufficient to satisfy the required material."
        )


class V4EvidenceManifest:
    """Build a manifest whose artifact hashes bind persisted exact bytes."""

    def build(
        self,
        *,
        run_id: str,
        code_identity: dict[str, Any],
        artifacts: dict[str, bytes | str | dict[str, Any] | list[Any]],
        lineage: dict[str, Any],
    ) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        for name in sorted(artifacts):
            value = artifacts[name]
            if isinstance(value, bytes):
                payload = value
            elif isinstance(value, str):
                payload = value.encode("utf-8")
            else:
                payload = canonical_json_bytes(value)
            entries.append(
                {
                    "name": name,
                    "sha256": sha256_bytes(payload),
                    "size_bytes": len(payload),
                }
            )
        manifest = {
            "run_contract_version": V4_RUN_VERSION,
            "run_id": run_id,
            "code_identity": dict(code_identity),
            "lineage": dict(lineage),
            "artifacts": entries,
        }
        manifest["manifest_digest"] = digest_object(manifest)
        return manifest


class V4ProviderCapabilityProbe:
    """Record provider behavior without making it a safety authority."""

    def run(
        self,
        *,
        cases: list[dict[str, Any]],
        provider_runner: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for case in cases:
            response = provider_runner(case)
            results.append(
                {
                    "case_id": case["case_id"],
                    "expected": case.get("expected"),
                    "provider_status": response.get("status"),
                    "stop_reason": response.get("stop_reason"),
                    "raw_output_digest": sha256_bytes(
                        str(response.get("raw_output", "")).encode("utf-8")
                    ),
                }
            )
        report = {"cases": results}
        report["probe_digest"] = digest_object(report)
        return report
