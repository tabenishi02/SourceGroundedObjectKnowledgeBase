"""Application facade for the G-23F frozen SGOKB grounded-generation v4 pipeline."""

from __future__ import annotations

from typing import Any

from .grounding.v4_contracts import (
    Stage1RequestBuilder,
    Stage2RequestBuilder,
    build_stage2_candidate_envelopes,
    parse_stage1_output,
    parse_stage2_output,
)
from .grounding.v4_pipeline import (
    ActiveAttemptLedger,
    V4DeterministicRenderer,
    V4EvidenceManifest,
    V4MaterialRequirementGate,
    V4ProviderCapabilityProbe,
    V4RetryController,
    build_system_context_limit,
    terminal_from_material,
)
from .grounding.v4_validation import (
    InterpretationDerivationValidatorAdapter,
    ResidualAtomicityClassifierAdapter,
    ResidualContentTypeClassifierAdapter,
    SourceFactSupportValidatorAdapter,
    V4PropositionValidator,
    build_validated_presentation_plan,
    certify_stage1_attempt,
)


class GroundedGenerationV4Application:
    """Thin v4 composition facade.

    Concrete V2-R-A / V2-R-C classifier selection is intentionally injected and
    remains a G-25A responsibility. Missing adapters fail closed in validation.
    """

    def __init__(
        self,
        *,
        atomicity_classifier: ResidualAtomicityClassifierAdapter | None = None,
        content_type_classifier: ResidualContentTypeClassifierAdapter | None = None,
        source_fact_support: SourceFactSupportValidatorAdapter | None = None,
        interpretation_derivation: InterpretationDerivationValidatorAdapter | None = None,
    ) -> None:
        self.stage1_requests = Stage1RequestBuilder()
        self.stage2_requests = Stage2RequestBuilder()
        self.validator = V4PropositionValidator(
            atomicity_classifier=atomicity_classifier,
            content_type_classifier=content_type_classifier,
            source_fact_support=source_fact_support,
            interpretation_derivation=interpretation_derivation,
        )
        self.material_gate = V4MaterialRequirementGate()
        self.retry = V4RetryController()
        self.attempts = ActiveAttemptLedger()
        self.renderer = V4DeterministicRenderer()
        self.evidence = V4EvidenceManifest()
        self.provider_probe = V4ProviderCapabilityProbe()

    def build_stage1_request(self, **kwargs: Any) -> dict[str, Any]:
        request = self.stage1_requests.build(**kwargs)
        self.attempts.activate("stage1", int(request["attempt"]))
        return request

    def build_stage1_retry(
        self,
        previous_request: dict[str, Any],
        *,
        retry_feedback: dict[str, Any],
        attempt_id: str | None = None,
    ) -> dict[str, Any]:
        self.attempts.authorize_retry("stage1", previous_attempt=1)
        request = self.stage1_requests.build_retry(
            previous_request,
            retry_feedback=retry_feedback,
            attempt_id=attempt_id,
        )
        self.attempts.activate("stage1", 2)
        return request

    def parse_stage1(
        self,
        raw_output: str | bytes | dict[str, Any],
        *,
        request: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        return parse_stage1_output(raw_output, request=request)

    def validate_stage1(
        self,
        candidates: list[dict[str, Any]],
        *,
        grounded_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        records = []
        for index, candidate in enumerate(candidates):
            records.append(
                self.validator.validate_stage1_candidate(
                    candidate,
                    grounded_context=grounded_context,
                    validation_record_id=(
                        f"VR-S1-A{candidate['attempt']}-C{index + 1}"
                    ),
                )
            )
        return records

    def certify_stage1(
        self,
        candidates: list[dict[str, Any]],
        validation_records: list[dict[str, Any]],
        *,
        request: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        self.attempts.assert_active("stage1", int(request["attempt"]))
        return certify_stage1_attempt(
            candidates,
            validation_records,
            request=request,
        )

    def build_stage2_request(self, **kwargs: Any) -> dict[str, Any]:
        certified_content = kwargs["certified_content"]
        if "stage1" in self.attempts.active_attempts:
            self.attempts.assert_active(
                "stage1",
                int(certified_content["active_stage1_attempt"]),
            )
        request = self.stage2_requests.build(**kwargs)
        self.attempts.activate("stage2", int(request["attempt"]))
        return request

    def build_stage2_retry(
        self,
        previous_request: dict[str, Any],
        *,
        certified_content: dict[str, Any],
        retry_feedback: dict[str, Any],
        attempt_id: str | None = None,
    ) -> dict[str, Any]:
        self.attempts.authorize_retry("stage2", previous_attempt=1)
        request = self.stage2_requests.build_retry(
            previous_request,
            certified_content=certified_content,
            retry_feedback=retry_feedback,
            attempt_id=attempt_id,
        )
        self.attempts.activate("stage2", 2)
        return request

    def parse_stage2(
        self,
        raw_output: str | bytes | dict[str, Any],
        *,
        request: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        parsed = parse_stage2_output(raw_output, request=request)
        candidates = build_stage2_candidate_envelopes(parsed, request=request)
        return parsed, candidates

    def validate_stage2(
        self,
        candidates: list[dict[str, Any]],
        *,
        certified_content: dict[str, Any],
    ) -> list[dict[str, Any]]:
        records = []
        for index, candidate in enumerate(candidates):
            records.append(
                self.validator.validate_stage2_candidate(
                    candidate,
                    certified_content=certified_content,
                    validation_record_id=(
                        f"VR-S2-A{candidate['attempt']}-C{index + 1}"
                    ),
                )
            )
        return records

    def build_validated_plan(
        self,
        parsed_stage2: dict[str, Any],
        *,
        request: dict[str, Any],
        certified_content: dict[str, Any],
        candidate_envelopes: list[dict[str, Any]],
        validation_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.attempts.assert_active("stage2", int(request["attempt"]))
        return build_validated_presentation_plan(
            parsed_stage2,
            request=request,
            certified_content=certified_content,
            candidate_envelopes=candidate_envelopes,
            validation_records=validation_records,
        )

    def evaluate_stage1_readiness(self, **kwargs: Any) -> dict[str, Any]:
        return self.material_gate.evaluate_stage1_readiness(**kwargs)

    def evaluate_final_material(self, **kwargs: Any) -> dict[str, Any]:
        return self.material_gate.evaluate_final(**kwargs)

    def build_system_context_limit(self, **kwargs: Any) -> dict[str, Any]:
        return build_system_context_limit(**kwargs)

    def terminal_from_material(
        self,
        material_result: dict[str, Any],
        *,
        validation_pass: bool,
        system_failure: bool = False,
    ) -> dict[str, Any]:
        return terminal_from_material(
            material_result,
            validation_pass=validation_pass,
            system_failure=system_failure,
        )
