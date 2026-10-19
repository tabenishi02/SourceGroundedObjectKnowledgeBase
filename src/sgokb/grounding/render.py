"""Terminal-bound deterministic renderer for N-04 v3 grounded generation."""

from __future__ import annotations

from typing import Any

from .failure import (
    RENDER_MODE_CONTEXT_LIMIT_ONLY,
    RENDER_MODE_NORMAL,
    TERMINAL_ACCEPTED,
    TERMINAL_INSUFFICIENT_CONTEXT,
)
from .material_gate import MATERIAL_FAIL_CONTEXT_INSUFFICIENT, MATERIAL_PASS
from .output import is_context_limit_output, output_binding


class RenderAuthorizationError(ValueError):
    failure_class = "RENDER_AUTHORIZATION_DENIED"

    def __init__(self, message: str, *, failure_code: str) -> None:
        super().__init__(message)
        self.failure_code = failure_code


class DeterministicRenderer:
    _HEADINGS = {
        "interpretation": "Interpretation",
        "creative": "Creative addition",
    }
    _CONTEXT_LIMIT_MESSAGE = (
        "Context limit\n"
        "The supplied context does not contain enough grounded material "
        "to satisfy this request safely."
    )

    def render(
        self,
        output: dict[str, Any],
        validation: dict[str, Any],
        material_result: dict[str, Any],
        terminal_decision: dict[str, Any],
    ) -> str:
        self._verify_binding(output, validation, material_result, terminal_decision)
        action = terminal_decision.get("action")
        render_mode = terminal_decision.get("render_mode")
        if action == TERMINAL_ACCEPTED and render_mode == RENDER_MODE_NORMAL:
            return self._render_normal(output, validation, material_result)
        if (
            action == TERMINAL_INSUFFICIENT_CONTEXT
            and render_mode == RENDER_MODE_CONTEXT_LIMIT_ONLY
        ):
            return self._render_context_limit(output, validation, material_result)
        raise RenderAuthorizationError(
            "Terminal decision does not authorize grounded rendering",
            failure_code="terminal_outcome_not_renderable",
        )

    @staticmethod
    def _verify_binding(
        output: dict[str, Any],
        validation: dict[str, Any],
        material_result: dict[str, Any],
        terminal_decision: dict[str, Any],
    ) -> None:
        validation_binding = validation.get("binding")
        if not isinstance(validation_binding, dict):
            raise RenderAuthorizationError(
                "Validation result has no output identity binding",
                failure_code="missing_validation_binding",
            )
        try:
            expected = output_binding(output, attempt=validation_binding.get("attempt"))
        except (TypeError, ValueError):
            raise RenderAuthorizationError(
                "Invalid render candidate attempt binding",
                failure_code="output_decision_binding_mismatch",
            ) from None
        if (
            validation_binding != expected
            or material_result.get("binding") != expected
            or terminal_decision.get("binding") != expected
        ):
            raise RenderAuthorizationError(
                "Output, validation, material, and terminal identities do not match",
                failure_code="output_decision_binding_mismatch",
            )

    def _render_normal(
        self, output: dict[str, Any], validation: dict[str, Any], material_result: dict[str, Any]
    ) -> str:
        if validation.get("verdict") != "PASS":
            raise RenderAuthorizationError(
                "NORMAL render requires Grounding PASS", failure_code="grounding_not_pass"
            )
        if material_result.get("verdict") != MATERIAL_PASS:
            raise RenderAuthorizationError(
                "NORMAL render requires Material PASS", failure_code="material_not_pass"
            )
        if is_context_limit_output(output):
            raise RenderAuthorizationError(
                "Context-limit output cannot use NORMAL render mode",
                failure_code="context_limit_normal_render_forbidden",
            )
        if validation.get("output") != output:
            raise RenderAuthorizationError(
                "Renderer output does not equal the validated output envelope",
                failure_code="validated_output_mismatch",
            )
        result_by_id = {
            item["unit_id"]: item
            for item in validation.get("unit_results", [])
            if isinstance(item, dict) and isinstance(item.get("unit_id"), str)
        }
        rendered_blocks: list[str] = []
        for block in output.get("blocks", []):
            role = block["presentation_role"]
            texts: list[str] = []
            for unit in block["units"]:
                result = result_by_id.get(unit["unit_id"])
                expected_disposition = {
                    "source_fact": "supported",
                    "interpretation": "derived_supported",
                    "creative_addition": "not_applicable",
                }[unit["semantic_role"]]
                if result is None or result.get("grounding_disposition") != expected_disposition:
                    raise RenderAuthorizationError(
                        "Every rendered unit must have the required successful disposition",
                        failure_code="unit_not_render_authorized",
                    )
                texts.append(unit["text"].strip())
            body = " ".join(texts).strip()
            if role == "main":
                rendered_blocks.append(body)
            else:
                heading = self._HEADINGS.get(role)
                if heading is None:
                    raise RenderAuthorizationError(
                        f"Unsupported presentation role for NORMAL render: {role}",
                        failure_code="unsupported_render_role",
                    )
                rendered_blocks.append(f"{heading}\n{body}")
        return "\n\n".join(rendered_blocks).strip()

    def _render_context_limit(
        self, output: dict[str, Any], validation: dict[str, Any], material_result: dict[str, Any]
    ) -> str:
        if validation.get("verdict") != "PASS":
            raise RenderAuthorizationError(
                "Context-limit render requires Grounding PASS", failure_code="grounding_not_pass"
            )
        if material_result.get("verdict") != MATERIAL_FAIL_CONTEXT_INSUFFICIENT:
            raise RenderAuthorizationError(
                "Context-limit render requires confirmed Context insufficiency",
                failure_code="context_limit_not_justified",
            )
        if not is_context_limit_output(output):
            raise RenderAuthorizationError(
                "CONTEXT_LIMIT_ONLY render requires exclusive context-limit shape",
                failure_code="context_limit_shape_violation",
            )
        return self._CONTEXT_LIMIT_MESSAGE
