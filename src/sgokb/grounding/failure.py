"""Bounded retry and terminal outcome policy for grounded generation."""

from __future__ import annotations

from typing import Any

GROUNDING_FAILURE_POLICY_VERSION = "sgokb.grounding-failure-policy.v1"
MAX_GENERATION_ATTEMPTS = 2
MAX_RETRIES = 1

TERMINAL_ACCEPTED = "ACCEPTED"
TERMINAL_INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
TERMINAL_REJECTED = "REJECTED"
TERMINAL_SYSTEM_FAILURE = "SYSTEM_FAILURE"
ACTION_RETRY = "RETRY"


class GroundingFailureController:
    """Apply G-06 retry/terminal semantics to one validation result."""

    contract_version = GROUNDING_FAILURE_POLICY_VERSION

    def decide(
        self,
        validation: dict[str, Any],
        *,
        attempt: int,
        materially_sufficient: bool | None = None,
    ) -> dict[str, Any]:
        if attempt not in {1, 2}:
            raise ValueError("grounded-generation attempt must be 1 or 2")

        verdict = validation.get("verdict")
        failures = list(validation.get("failures", []))

        if verdict == "PASS":
            if materially_sufficient is None:
                materially_sufficient = self._infer_material_sufficiency(validation)
            outcome = (
                TERMINAL_ACCEPTED
                if materially_sufficient
                else TERMINAL_INSUFFICIENT_CONTEXT
            )
            return self._decision(outcome, attempt, retry=False)

        if any(bool(item.get("system_failure")) for item in failures):
            return self._decision(TERMINAL_SYSTEM_FAILURE, attempt, retry=False)

        retryable = bool(failures) and all(bool(item.get("retryable")) for item in failures)
        if retryable and attempt == 1:
            return self._decision(ACTION_RETRY, attempt, retry=True)

        return self._decision(TERMINAL_REJECTED, attempt, retry=False)

    def build_retry_feedback(
        self,
        validation: dict[str, Any],
        *,
        previous_attempt: int = 1,
    ) -> dict[str, Any]:
        if previous_attempt != 1:
            raise ValueError("Only one retry is permitted; previous_attempt must be 1")

        failures = [
            item for item in validation.get("failures", []) if bool(item.get("retryable"))
        ]
        if not failures:
            raise ValueError("Validation result contains no retryable failure")

        failed_units = sorted(
            {item["unit_id"] for item in failures if item.get("unit_id") is not None}
        )
        feedback_failures = [
            {
                "failure_class": item.get("failure_class"),
                "failure_code": item.get("failure_code"),
                "unit_id": item.get("unit_id"),
                "support_refs": list(item.get("support_refs", [])),
            }
            for item in failures
        ]
        return {
            "retry_policy_version": self.contract_version,
            "attempt": 2,
            "previous_attempt": previous_attempt,
            "failed_units": failed_units,
            "failures": feedback_failures,
            "repair_directives": [
                "regenerate_the_entire_structured_output",
                "remove_or_rewrite_unsupported_material",
                "use_only_existing_grounding_refs",
                "preserve_context_fingerprint_purpose_model_and_generation_settings",
                "use_context_limit_if_context_is_insufficient",
            ],
        }

    @staticmethod
    def _infer_material_sufficiency(validation: dict[str, Any]) -> bool:
        output = validation.get("output") or {}
        material_roles = {"source_fact", "interpretation", "creative_addition"}
        return any(
            unit.get("semantic_role") in material_roles
            for block in output.get("blocks", [])
            for unit in block.get("units", [])
        )

    def _decision(self, outcome: str, attempt: int, *, retry: bool) -> dict[str, Any]:
        return {
            "failure_policy_version": self.contract_version,
            "attempt": attempt,
            "action": outcome,
            "retry": retry,
            "terminal": not retry,
            "max_generation_attempts": MAX_GENERATION_ATTEMPTS,
            "max_retries": MAX_RETRIES,
        }
