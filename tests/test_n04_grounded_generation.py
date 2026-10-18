from __future__ import annotations

import copy
import json

import pytest

from sgokb.application_grounding import GroundedGenerationApplication
from sgokb.grounding import (
    ACTION_RETRY,
    TERMINAL_ACCEPTED,
    TERMINAL_INSUFFICIENT_CONTEXT,
    TERMINAL_REJECTED,
    TERMINAL_SYSTEM_FAILURE,
    DeterministicRenderer,
    GenerationOutputContractError,
    GroundedContextProjector,
    GroundedGenerationRequestBuilder,
    GroundingEvidenceLogger,
    GroundingFailureController,
    GroundingValidator,
    parse_generation_output,
)


class FakeSemanticValidator:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}

    def validate(
        self,
        *,
        text: str,
        semantic_role: str,
        support_units: list[dict],
        purpose: str,
        presentation_role: str,
    ) -> str:
        if text in self.verdicts:
            return self.verdicts[text]
        if semantic_role in {"creative_addition", "context_limit", "stylistic_expression"}:
            return "role_valid"
        return "unsupported"


class ExplodingSemanticValidator:
    def validate(self, **kwargs) -> str:
        raise RuntimeError("validator unavailable")


def context_builder_output(
    *,
    purpose: str = "roleplay",
    resolved_version_id: str = "version-current",
    is_current: bool = True,
) -> dict:
    return {
        "context_contract_version": "sgokb.context-builder.v1",
        "purpose": purpose,
        "selection_policy": {
            "facet_source": "purpose_profile",
            "facet_priority": ["overall", "relationships"],
            "include_summary": True,
            "include_attributes": True,
            "include_relations": purpose != "comparison",
            "include_evidence_refs": purpose == "comparison",
            "budget_metric": "serialized_json_characters",
            "budget_strategy": "equal_share_per_object",
            "partial_statement_truncation": False,
        },
        "objects": [
            {
                "object_id": "object-saber",
                "name": "Saber",
                "aliases": [],
                "object_status": "active",
                "requested_version_id": None,
                "resolved_version_id": resolved_version_id,
                "is_current": is_current,
                "primary_class": None,
                "additional_classes": [],
                "context_scope": {},
                "knowledge": {
                    "default_language": "en",
                    "result_status": "accepted",
                    "summary": [
                        {
                            "statement_id": "statement-contract",
                            "local_key": "contract",
                            "text": "Saber is contracted to Shirou.",
                            "derivation_kind": "direct",
                            "language": "en",
                            "facet": None,
                            "temporal_scope": None,
                            "attribution": None,
                            "evidence": [],
                        }
                    ],
                    "facets": [],
                    "attributes": [],
                    "relations": [],
                },
                "omitted": {},
                "budget": {
                    "limit_characters": 12000,
                    "used_characters": 100,
                    "omitted_items": 0,
                    "truncated": False,
                },
                "warnings": [],
            }
        ],
        "budget": {
            "metric": "serialized_json_characters",
            "limit_characters": 12000,
            "used_characters": 100,
            "omitted_items": 0,
            "truncated": False,
        },
        "warnings": [],
    }


def projected_context(**kwargs) -> dict:
    return GroundedContextProjector().project(context_builder_output(**kwargs))


def statement_ref(context: dict) -> str:
    return next(
        unit["ref_id"]
        for unit in context["grounding_units"]
        if unit["canonical_ref"] == {"kind": "statement", "id": "statement-contract"}
    )


def output_envelope(context: dict, blocks: list[dict], *, purpose: str | None = None) -> dict:
    return {
        "contract_version": "sgokb.grounded-generation-output.v1",
        "context_fingerprint": context["context_fingerprint"],
        "purpose": purpose or context["purpose"],
        "blocks": blocks,
    }


def source_fact_block(context: dict, *, text: str = "Saber is contracted to Shirou.") -> dict:
    return {
        "block_id": "B1",
        "presentation_role": "main",
        "label": None,
        "units": [
            {
                "unit_id": "U1",
                "semantic_role": "source_fact",
                "text": text,
                "support_refs": [statement_ref(context)],
            }
        ],
    }


def test_grounded_context_projection_is_deterministic_and_non_mutating():
    source = context_builder_output()
    before = copy.deepcopy(source)

    first = GroundedContextProjector().project(source)
    second = GroundedContextProjector().project(source)

    assert source == before
    assert first == second
    assert GroundedContextProjector.verify(first)
    assert first["context_fingerprint"] == second["context_fingerprint"]
    assert [unit["ref_id"] for unit in first["grounding_units"]] == ["K1", "K2"]
    assert first["grounding_units"][1]["canonical_ref"] == {
        "kind": "statement",
        "id": "statement-contract",
    }


def test_grounded_context_version_binding_prevents_silent_cross_version_identity():
    current = projected_context(resolved_version_id="version-current", is_current=True)
    historical = projected_context(resolved_version_id="version-historical", is_current=False)

    assert current["context_fingerprint"] != historical["context_fingerprint"]
    assert {unit["resolved_version_id"] for unit in current["grounding_units"]} == {
        "version-current"
    }
    assert {unit["resolved_version_id"] for unit in historical["grounding_units"]} == {
        "version-historical"
    }
    assert current["objects"][0]["is_current"] is True
    assert historical["objects"][0]["is_current"] is False


def test_parse_generation_output_accepts_valid_envelope_and_rejects_free_prose():
    context = projected_context()
    payload = output_envelope(context, [source_fact_block(context)])

    assert parse_generation_output(json.dumps(payload)) == payload
    with pytest.raises(GenerationOutputContractError) as exc_info:
        parse_generation_output("Here is the answer: {}")
    assert exc_info.value.failure_code == "malformed_json"


def test_parse_generation_output_rejects_duplicate_unit_ids():
    context = projected_context(purpose="comparison")
    ref = statement_ref(context)
    payload = output_envelope(
        context,
        [
            {
                "block_id": "B1",
                "presentation_role": "main",
                "label": None,
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "source_fact",
                        "text": "Saber is contracted to Shirou.",
                        "support_refs": [ref],
                    }
                ],
            },
            {
                "block_id": "B2",
                "presentation_role": "interpretation",
                "label": "Interpretation",
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "interpretation",
                        "text": "This suggests a relationship-centered comparison.",
                        "support_refs": [ref],
                    }
                ],
            },
        ],
    )

    with pytest.raises(GenerationOutputContractError) as exc_info:
        parse_generation_output(payload)
    assert exc_info.value.failure_code == "duplicate_unit_id"


def test_request_builder_binds_valid_context_and_frozen_output_contract():
    context = projected_context()
    request = GroundedGenerationRequestBuilder().build(
        user_task="Answer as Saber.",
        grounded_context=context,
    )
    prompt = GroundedGenerationRequestBuilder().to_prompt_text(request)

    assert request["grounded_context"] == context
    assert request["output_contract"]["contract_version"] == (
        "sgokb.grounded-generation-output.v1"
    )
    assert request["output_contract"]["json_schema"]["additionalProperties"] is False
    assert "Do not use external knowledge as factual support." in prompt
    assert context["context_fingerprint"] in prompt


def test_exact_supported_source_fact_passes_without_semantic_validator():
    context = projected_context()
    output = output_envelope(context, [source_fact_block(context)])

    validation = GroundingValidator().validate(context, output)

    assert validation["verdict"] == "PASS"
    assert validation["failures"] == []
    assert validation["unit_results"] == [
        {
            "unit_id": "U1",
            "semantic_role": "source_fact",
            "grounding_disposition": "supported",
            "validation_stage": "V3",
        }
    ]


def test_unsupported_source_fact_fails_even_with_valid_reference():
    context = projected_context()
    text = "Saber secretly protects Shirou throughout the Holy Grail War."
    output = output_envelope(context, [source_fact_block(context, text=text)])
    validator = GroundingValidator(FakeSemanticValidator({text: "unsupported"}))

    validation = validator.validate(context, output)

    assert validation["verdict"] == "FAIL"
    assert validation["failures"][0]["failure_class"] == "UNSUPPORTED_CLAIM"
    assert validation["failures"][0]["retryable"] is True


def test_contradictory_source_fact_is_classified_separately():
    context = projected_context()
    text = "Saber is not contracted to Shirou."
    output = output_envelope(context, [source_fact_block(context, text=text)])
    validator = GroundingValidator(FakeSemanticValidator({text: "contradictory"}))

    validation = validator.validate(context, output)

    assert validation["verdict"] == "FAIL"
    assert validation["unit_results"][0]["grounding_disposition"] == "contradictory"
    assert validation["failures"][0]["failure_class"] == "CONTRADICTORY_CLAIM"


def test_interpretation_requires_visible_separation_and_semantic_derivation():
    context = projected_context(purpose="comparison")
    ref = statement_ref(context)
    interpretation = "The available material supports a relationship-focused comparison."
    output = output_envelope(
        context,
        [
            source_fact_block(context),
            {
                "block_id": "B2",
                "presentation_role": "interpretation",
                "label": "Interpretation",
                "units": [
                    {
                        "unit_id": "U2",
                        "semantic_role": "interpretation",
                        "text": interpretation,
                        "support_refs": [ref],
                    }
                ],
            },
        ],
    )
    validator = GroundingValidator(
        FakeSemanticValidator({interpretation: "reasonable_derivation"})
    )

    validation = validator.validate(context, output)

    assert validation["verdict"] == "PASS"
    result = next(item for item in validation["unit_results"] if item["unit_id"] == "U2")
    assert result["grounding_disposition"] == "derived_supported"
    assert result["validation_stage"] == "V4"


def test_interpretation_in_main_block_is_separation_violation():
    context = projected_context(purpose="comparison")
    ref = statement_ref(context)
    output = output_envelope(
        context,
        [
            {
                "block_id": "B1",
                "presentation_role": "main",
                "label": None,
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "interpretation",
                        "text": "This suggests a comparison.",
                        "support_refs": [ref],
                    }
                ],
            }
        ],
    )

    validation = GroundingValidator(FakeSemanticValidator()).validate(context, output)

    assert validation["verdict"] == "FAIL"
    assert validation["failures"][0]["failure_class"] == "SEPARATION_VIOLATION"


def test_creative_addition_passes_only_in_visible_creative_scope():
    context = projected_context(purpose="creative")
    output = output_envelope(
        context,
        [
            source_fact_block(context),
            {
                "block_id": "B2",
                "presentation_role": "creative",
                "label": "Creative addition",
                "units": [
                    {
                        "unit_id": "U2",
                        "semantic_role": "creative_addition",
                        "text": "A new knight begins a journey of self-discovery.",
                        "support_refs": [],
                    }
                ],
            },
        ],
    )

    validation = GroundingValidator(FakeSemanticValidator()).validate(context, output)

    assert validation["verdict"] == "PASS"
    creative = next(item for item in validation["unit_results"] if item["unit_id"] == "U2")
    assert creative["grounding_disposition"] == "not_applicable"


def test_creative_addition_in_main_block_is_scope_violation():
    context = projected_context(purpose="creative")
    output = output_envelope(
        context,
        [
            {
                "block_id": "B1",
                "presentation_role": "main",
                "label": None,
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "creative_addition",
                        "text": "A new knight appears.",
                        "support_refs": [],
                    }
                ],
            }
        ],
    )

    validation = GroundingValidator(FakeSemanticValidator()).validate(context, output)

    assert validation["verdict"] == "FAIL"
    assert validation["failures"][0]["failure_class"] == "CREATIVE_SCOPE_VIOLATION"


def test_context_limit_passes_validation_but_maps_to_insufficient_context():
    context = projected_context()
    output = output_envelope(
        context,
        [
            {
                "block_id": "B1",
                "presentation_role": "context_limit",
                "label": "Context limit",
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "context_limit",
                        "text": "The supplied context does not contain enough personality detail.",
                        "support_refs": [],
                    }
                ],
            }
        ],
    )
    validation = GroundingValidator(FakeSemanticValidator()).validate(context, output)

    decision = GroundingFailureController().decide(validation, attempt=1)

    assert validation["verdict"] == "PASS"
    assert decision["action"] == TERMINAL_INSUFFICIENT_CONTEXT
    assert decision["terminal"] is True


def test_semantic_validator_unavailable_is_fail_closed_system_failure():
    context = projected_context(purpose="creative")
    output = output_envelope(
        context,
        [
            {
                "block_id": "B1",
                "presentation_role": "creative",
                "label": "Creative addition",
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "creative_addition",
                        "text": "A new knight appears.",
                        "support_refs": [],
                    }
                ],
            }
        ],
    )
    validation = GroundingValidator(ExplodingSemanticValidator()).validate(context, output)
    decision = GroundingFailureController().decide(validation, attempt=1)

    assert validation["verdict"] == "INDETERMINATE"
    assert validation["failures"][0]["failure_class"] == "VALIDATOR_UNAVAILABLE"
    assert validation["failures"][0]["system_failure"] is True
    assert decision["action"] == TERMINAL_SYSTEM_FAILURE


def test_unknown_reference_is_retryable_and_never_passes_by_reference_presence_alone():
    context = projected_context()
    output = output_envelope(
        context,
        [
            {
                "block_id": "B1",
                "presentation_role": "main",
                "label": None,
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "source_fact",
                        "text": "Saber is contracted to Shirou.",
                        "support_refs": ["K999"],
                    }
                ],
            }
        ],
    )

    validation = GroundingValidator(FakeSemanticValidator()).validate(context, output)

    assert validation["verdict"] == "FAIL"
    assert validation["failures"][0]["failure_class"] == "REFERENCE_INTEGRITY_ERROR"
    assert validation["failures"][0]["failure_code"] == "unknown_grounding_reference"


def test_tampered_grounded_context_is_non_retryable_system_failure():
    context = projected_context()
    context["grounding_units"][0]["content"]["value"] = "Tampered"
    output = {
        "contract_version": "sgokb.grounded-generation-output.v1",
        "context_fingerprint": context["context_fingerprint"],
        "purpose": "roleplay",
        "blocks": [source_fact_block(projected_context())],
    }

    validation = GroundingValidator(FakeSemanticValidator()).validate(context, output)
    decision = GroundingFailureController().decide(validation, attempt=1)

    assert validation["verdict"] == "INDETERMINATE"
    assert validation["failures"][0]["failure_code"] == "grounded_context_fingerprint_invalid"
    assert decision["action"] == TERMINAL_SYSTEM_FAILURE


def test_failure_controller_allows_one_retry_then_rejects_and_feedback_has_no_new_knowledge():
    context = projected_context()
    text = "Saber secretly protects Shirou throughout the Holy Grail War."
    output = output_envelope(context, [source_fact_block(context, text=text)])
    validation = GroundingValidator(FakeSemanticValidator({text: "unsupported"})).validate(
        context, output
    )
    controller = GroundingFailureController()

    first = controller.decide(validation, attempt=1)
    feedback = controller.build_retry_feedback(validation)
    second = controller.decide(validation, attempt=2)

    assert first["action"] == ACTION_RETRY
    assert first["retry"] is True
    assert feedback["attempt"] == 2
    assert feedback["previous_attempt"] == 1
    assert feedback["failed_units"] == ["U1"]
    assert "grounded_context" not in feedback
    assert "web" not in json.dumps(feedback).lower()
    assert second["action"] == TERMINAL_REJECTED
    assert second["retry"] is False


def test_deterministic_renderer_uses_exact_validated_unit_text_and_visible_labels():
    context = projected_context(purpose="comparison")
    ref = statement_ref(context)
    interpretation = "This is a bounded interpretation."
    output = output_envelope(
        context,
        [
            source_fact_block(context),
            {
                "block_id": "B2",
                "presentation_role": "interpretation",
                "label": "Interpretation",
                "units": [
                    {
                        "unit_id": "U2",
                        "semantic_role": "interpretation",
                        "text": interpretation,
                        "support_refs": [ref],
                    }
                ],
            },
        ],
    )
    validation = GroundingValidator(
        FakeSemanticValidator({interpretation: "reasonable_derivation"})
    ).validate(context, output)

    rendered = DeterministicRenderer().render(output, validation)

    assert rendered == (
        "Saber is contracted to Shirou.\n\n"
        "Interpretation\n"
        "This is a bounded interpretation."
    )
    assert "K" not in rendered
    assert "U1" not in rendered


def test_renderer_rejects_partial_salvage_or_unvalidated_output():
    context = projected_context()
    output = output_envelope(context, [source_fact_block(context)])
    validation = GroundingValidator().validate(context, output)
    incomplete_validation = copy.deepcopy(validation)
    incomplete_validation["unit_results"] = []

    with pytest.raises(ValueError, match="Every rendered unit"):
        DeterministicRenderer().render(output, incomplete_validation)

    failed_validation = copy.deepcopy(validation)
    failed_validation["verdict"] = "FAIL"
    with pytest.raises(ValueError, match="Only validation PASS"):
        DeterministicRenderer().render(output, failed_validation)


def test_evidence_logger_persists_attempt_artifacts(tmp_path):
    logger = GroundingEvidenceLogger(tmp_path)

    request_path, response_path, validation_path = logger.write_attempt(
        "case-roleplay",
        1,
        request={"request": 1},
        response={"response": 1},
        validation={"verdict": "PASS"},
    )

    assert json.loads(request_path.read_text(encoding="utf-8")) == {"request": 1}
    assert json.loads(response_path.read_text(encoding="utf-8")) == {"response": 1}
    assert json.loads(validation_path.read_text(encoding="utf-8")) == {"verdict": "PASS"}


def test_application_facade_runs_common_grounded_flow_without_model_runtime():
    app = GroundedGenerationApplication()
    source = context_builder_output()
    context = app.project_context(source)
    request = app.build_request(user_task="Answer only from context.", grounded_context=context)
    output = output_envelope(context, [source_fact_block(context)])

    validation = app.validate(context, output)
    decision = app.decide(validation, attempt=1)
    rendered = app.render(output, validation)

    assert request["purpose"] == "roleplay"
    assert validation["verdict"] == "PASS"
    assert decision["action"] == TERMINAL_ACCEPTED
    assert rendered == "Saber is contracted to Shirou."
