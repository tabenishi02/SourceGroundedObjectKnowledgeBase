"""Application-level facade for the frozen N-04 grounded-generation contract.

This facade owns SGOKB contract composition only. It deliberately does not load
or call a generator/validator model; model runtime/orchestration remains a
consumer responsibility under N-04G-01/G-07.
"""

from __future__ import annotations

from typing import Any

from .grounding import (
    DeterministicRenderer,
    GroundedContextProjector,
    GroundedGenerationRequestBuilder,
    GroundingFailureController,
    GroundingValidator,
    SemanticValidatorAdapter,
    parse_generation_output,
)


class GroundedGenerationApplication:
    """Compose the SGOKB-owned pieces of the frozen grounded-generation flow."""

    def __init__(self, semantic_validator: SemanticValidatorAdapter | None = None) -> None:
        self.projector = GroundedContextProjector()
        self.request_builder = GroundedGenerationRequestBuilder()
        self.validator = GroundingValidator(semantic_validator)
        self.failure_controller = GroundingFailureController()
        self.renderer = DeterministicRenderer()

    def project_context(self, context_builder_output: dict[str, Any]) -> dict[str, Any]:
        return self.projector.project(context_builder_output)

    def build_request(
        self,
        *,
        user_task: str,
        grounded_context: dict[str, Any],
        retry_feedback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.request_builder.build(
            user_task=user_task,
            grounded_context=grounded_context,
            retry_feedback=retry_feedback,
        )

    def request_prompt_text(self, request: dict[str, Any]) -> str:
        return self.request_builder.to_prompt_text(request)

    @staticmethod
    def parse_output(raw_output: str | dict[str, Any]) -> dict[str, Any]:
        return parse_generation_output(raw_output)

    def validate(
        self,
        grounded_context: dict[str, Any],
        raw_output: str | dict[str, Any],
    ) -> dict[str, Any]:
        return self.validator.validate(grounded_context, raw_output)

    def decide(
        self,
        validation: dict[str, Any],
        *,
        attempt: int,
        materially_sufficient: bool | None = None,
    ) -> dict[str, Any]:
        return self.failure_controller.decide(
            validation,
            attempt=attempt,
            materially_sufficient=materially_sufficient,
        )

    def build_retry_feedback(
        self,
        validation: dict[str, Any],
        *,
        previous_attempt: int = 1,
    ) -> dict[str, Any]:
        return self.failure_controller.build_retry_feedback(
            validation,
            previous_attempt=previous_attempt,
        )

    def render(
        self,
        output: dict[str, Any],
        validation: dict[str, Any],
    ) -> str:
        return self.renderer.render(output, validation)
