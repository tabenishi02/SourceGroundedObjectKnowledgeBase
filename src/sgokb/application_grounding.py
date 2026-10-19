"""Application facade for the frozen post-G12 N-04 v3 grounded-generation contract.

The facade composes SGOKB-owned contracts and deterministic gates. It does not
load model runtimes; generator/verifier model execution remains orchestrator
responsibility.
"""

from __future__ import annotations

from typing import Any

from .grounding import (
    AtomicityRoleValidatorAdapter,
    DeterministicRenderer,
    GroundedContextProjector,
    GroundedGenerationRequestBuilder,
    GroundingFailureController,
    GroundingValidator,
    InterpretationDerivationJudgeAdapter,
    MaterialRequirementGate,
    SourceFactJudgeAdapter,
    SourceFactVerifierAdapter,
    parse_generation_output,
)


class GroundedGenerationApplication:
    """Compose the frozen output/validation/material/terminal/render pipeline."""

    def __init__(
        self,
        *,
        atomicity_role_validator: AtomicityRoleValidatorAdapter | None = None,
        source_fact_verifier: SourceFactVerifierAdapter | None = None,
        source_fact_judge: SourceFactJudgeAdapter | None = None,
        interpretation_judge: InterpretationDerivationJudgeAdapter | None = None,
    ) -> None:
        self.projector = GroundedContextProjector()
        self.request_builder = GroundedGenerationRequestBuilder()
        self.validator = GroundingValidator(
            atomicity_role_validator=atomicity_role_validator,
            source_fact_verifier=source_fact_verifier,
            source_fact_judge=source_fact_judge,
            interpretation_judge=interpretation_judge,
        )
        self.material_gate = MaterialRequirementGate()
        self.failure_controller = GroundingFailureController()
        self.renderer = DeterministicRenderer()

    def project_context(self, context_builder_output: dict[str, Any]) -> dict[str, Any]:
        return self.projector.project(context_builder_output)

    def build_request(
        self,
        *,
        user_task: str,
        grounded_context: dict[str, Any],
        requirement_profile: dict[str, Any] | None = None,
        retry_feedback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.request_builder.build(
            user_task=user_task,
            grounded_context=grounded_context,
            requirement_profile=requirement_profile,
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
        *,
        attempt: int = 1,
    ) -> dict[str, Any]:
        return self.validator.validate(grounded_context, raw_output, attempt=attempt)

    def evaluate_material(
        self,
        grounded_context: dict[str, Any],
        validation: dict[str, Any],
        *,
        requirement_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.material_gate.evaluate(
            grounded_context,
            validation,
            requirement_profile=requirement_profile,
        )

    def decide(
        self,
        validation: dict[str, Any],
        material_result: dict[str, Any] | None,
        *,
        attempt: int,
    ) -> dict[str, Any]:
        return self.failure_controller.decide(validation, material_result, attempt=attempt)

    def build_retry_feedback(
        self,
        validation: dict[str, Any],
        material_result: dict[str, Any] | None = None,
        *,
        previous_attempt: int = 1,
    ) -> dict[str, Any]:
        return self.failure_controller.build_retry_feedback(
            validation,
            material_result,
            previous_attempt=previous_attempt,
        )

    def render(
        self,
        output: dict[str, Any],
        validation: dict[str, Any],
        material_result: dict[str, Any],
        terminal_decision: dict[str, Any],
    ) -> str:
        return self.renderer.render(output, validation, material_result, terminal_decision)
