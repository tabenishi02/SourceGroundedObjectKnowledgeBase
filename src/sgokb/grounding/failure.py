"""Bounded retry and terminal outcome policy v2 for grounded generation."""

from __future__ import annotations

from typing import Any

from .material_gate import (
    MATERIAL_FAIL_CONTEXT_INSUFFICIENT,
    MATERIAL_FAIL_REPAIRABLE,
    MATERIAL_INDETERMINATE,
    MATERIAL_PASS,
)
from .output import is_context_limit_output

GROUNDING_FAILURE_POLICY_VERSION = "sgokb.grounding-failure-policy.v2"
MAX_GENERATION_ATTEMPTS = 2
MAX_RETRIES = 1

TERMINAL_ACCEPTED = "ACCEPTED"
TERMINAL_INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
TERMINAL_REJECTED = "REJECTED"
TERMINAL_SYSTEM_FAILURE = "SYSTEM_FAILURE"
ACTION_RETRY = "RETRY"

RENDER_MODE_NORMAL = "NORMAL"
RENDER_MODE_CONTEXT_LIMIT_ONLY = "CONTEXT_LIMIT_ONLY"
RENDER_MODE_NONE = "NONE"


class GroundingFailureController:
    """Compose grounding + material results into retry or terminal outcome."""

    contract_version = GROUNDING_FAILURE_POLICY_VERSION

    def decide(
        self,
        validation: dict[str, Any],
        material_result: dict[str, Any] | None,
        *,
        attempt: int,
    ) -> dict[str, Any]:
        if attempt not in {1, 2}:
            raise ValueError("grounded-generation attempt must be 1 or 2")

        validation_binding = validation.get("binding")
        if isinstance(validation_binding, dict) and validation_binding.get("attempt") != attempt:
            return self._decision(
                TERMINAL_SYSTEM_FAILURE,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="validation_attempt_binding_mismatch",
            )

        validation_failures = list(validation.get("failures", []))
        if any(bool(item.get("system_failure")) for item in validation_failures):
            return self._decision(
                TERMINAL_SYSTEM_FAILURE,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="validation_system_failure",
            )

        if validation.get("verdict") != "PASS":
            retryable = bool(validation_failures) and all(
                bool(item.get("retryable")) for item in validation_failures
            )
            if retryable and attempt == 1:
                return self._decision(
                    ACTION_RETRY,
                    attempt,
                    binding=validation_binding,
                    retry=True,
                    render_mode=RENDER_MODE_NONE,
                    failure_code="grounding_retryable_failure",
                )
            return self._decision(
                TERMINAL_REJECTED,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="grounding_not_certified",
            )

        if not isinstance(material_result, dict):
            return self._decision(
                TERMINAL_SYSTEM_FAILURE,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="material_result_missing",
            )

        material_binding = material_result.get("binding")
        if validation_binding != material_binding:
            return self._decision(
                TERMINAL_SYSTEM_FAILURE,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="output_decision_binding_mismatch",
            )

        material_failures = list(material_result.get("failures", []))
        if any(bool(item.get("system_failure")) for item in material_failures):
            return self._decision(
                TERMINAL_SYSTEM_FAILURE,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="material_gate_system_failure",
            )

        material_verdict = material_result.get("verdict")
        output = validation.get("output") or {}

        if material_verdict == MATERIAL_PASS:
            return self._decision(
                TERMINAL_ACCEPTED,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NORMAL,
                profile_id=material_result.get("profile_id"),
                profile_hash=material_result.get("profile_hash"),
            )

        if material_verdict == MATERIAL_FAIL_CONTEXT_INSUFFICIENT:
            if is_context_limit_output(output):
                return self._decision(
                    TERMINAL_INSUFFICIENT_CONTEXT,
                    attempt,
                    binding=validation_binding,
                    retry=False,
                    render_mode=RENDER_MODE_CONTEXT_LIMIT_ONLY,
                    profile_id=material_result.get("profile_id"),
                    profile_hash=material_result.get("profile_hash"),
                )
            if attempt == 1:
                return self._decision(
                    ACTION_RETRY,
                    attempt,
                    binding=validation_binding,
                    retry=True,
                    render_mode=RENDER_MODE_NONE,
                    failure_code="regenerate_as_context_limit_only",
                    profile_id=material_result.get("profile_id"),
                    profile_hash=material_result.get("profile_hash"),
                )
            return self._decision(
                TERMINAL_REJECTED,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="context_insufficient_but_no_safe_limit_output",
                profile_id=material_result.get("profile_id"),
                profile_hash=material_result.get("profile_hash"),
            )

        if material_verdict == MATERIAL_FAIL_REPAIRABLE:
            if attempt == 1:
                return self._decision(
                    ACTION_RETRY,
                    attempt,
                    binding=validation_binding,
                    retry=True,
                    render_mode=RENDER_MODE_NONE,
                    failure_code="material_requirement_repairable",
                    profile_id=material_result.get("profile_id"),
                    profile_hash=material_result.get("profile_hash"),
                )
            return self._decision(
                TERMINAL_REJECTED,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="material_requirement_exhausted",
                profile_id=material_result.get("profile_id"),
                profile_hash=material_result.get("profile_hash"),
            )

        if material_verdict == MATERIAL_INDETERMINATE:
            return self._decision(
                TERMINAL_SYSTEM_FAILURE,
                attempt,
                binding=validation_binding,
                retry=False,
                render_mode=RENDER_MODE_NONE,
                failure_code="material_requirement_indeterminate",
                profile_id=material_result.get("profile_id"),
                profile_hash=material_result.get("profile_hash"),
            )

        return self._decision(
            TERMINAL_SYSTEM_FAILURE,
            attempt,
            binding=validation_binding,
            retry=False,
            render_mode=RENDER_MODE_NONE,
            failure_code="unknown_material_verdict",
        )

    def build_retry_feedback(
        self,
        validation: dict[str, Any],
        material_result: dict[str, Any] | None = None,
        *,
        previous_attempt: int = 1,
    ) -> dict[str, Any]:
        if previous_attempt != 1:
            raise ValueError("Only one retry is permitted; previous_attempt must be 1")

        failures: list[dict[str, Any]] = []
        for source, items in (
            ("grounding", validation.get("failures", [])),
            ("material", (material_result or {}).get("failures", [])),
        ):
            for item in items:
                failures.append(
                    {
                        "source": source,
                        "failure_class": item.get("failure_class"),
                        "failure_code": item.get("failure_code"),
                        "unit_id": item.get("unit_id"),
                        "support_refs": list(item.get("support_refs", [])),
                        "premise_unit_ids": list(item.get("premise_unit_ids", [])),
                        "json_path": item.get("json_path"),
                        "expected_rule": item.get("expected_rule"),
                        "object_id": item.get("object_id"),
                    }
                )

        if not failures:
            raise ValueError("No grounding/material failure is available for retry feedback")

        failed_units = sorted(
            {item["unit_id"] for item in failures if isinstance(item.get("unit_id"), str)}
        )
        feedback: dict[str, Any] = {
            "retry_policy_version": self.contract_version,
            "attempt": 2,
            "previous_attempt": previous_attempt,
            "failed_units": failed_units,
            "failures": failures,
            "repair_directives": [
                "regenerate_the_entire_structured_output",
                "preserve_grounded_context_fingerprint_purpose_model_and_settings",
                "use_only_existing_grounding_refs",
                "keep_each_material_text_unit_atomic",
                "respect_role_specific_block_and_unit_shapes",
                "remove_or_rewrite_unsupported_material",
                "use_premise_unit_ids_only_for_validated_source_fact_premises",
            ],
        }

        if isinstance(material_result, dict):
            feedback["material_requirement"] = {
                "profile_id": material_result.get("profile_id"),
                "profile_hash": material_result.get("profile_hash"),
                "covered_source_object_ids": list(
                    material_result.get("covered_source_object_ids", [])
                ),
                "missing_source_object_ids": list(
                    material_result.get("missing_source_object_ids", [])
                ),
                "verdict": material_result.get("verdict"),
            }
            if material_result.get("verdict") == MATERIAL_FAIL_CONTEXT_INSUFFICIENT:
                feedback["repair_directives"].append(
                    "return_exclusive_context_limit_shape_when_required_material_is_absent"
                )
        return feedback

    def _decision(
        self,
        action: str,
        attempt: int,
        *,
        binding: dict[str, Any] | None,
        retry: bool,
        render_mode: str,
        failure_code: str | None = None,
        profile_id: str | None = None,
        profile_hash: str | None = None,
    ) -> dict[str, Any]:
        return {
            "failure_policy_version": self.contract_version,
            "attempt": attempt,
            "action": action,
            "retry": retry,
            "terminal": not retry,
            "render_mode": render_mode,
            "binding": dict(binding) if isinstance(binding, dict) else None,
            "failure_code": failure_code,
            "profile_id": profile_id,
            "profile_hash": profile_hash,
            "max_generation_attempts": MAX_GENERATION_ATTEMPTS,
            "max_retries": MAX_RETRIES,
        }
