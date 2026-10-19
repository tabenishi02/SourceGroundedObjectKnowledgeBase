from __future__ import annotations

import copy
import json

import pytest

from sgokb.application_grounding import GroundedGenerationApplication
from sgokb.grounding import (
    ACTION_RETRY,
    MATERIAL_FAIL_CONTEXT_INSUFFICIENT,
    MATERIAL_FAIL_REPAIRABLE,
    MATERIAL_PASS,
    RENDER_MODE_CONTEXT_LIMIT_ONLY,
    RENDER_MODE_NORMAL,
    TERMINAL_ACCEPTED,
    TERMINAL_INSUFFICIENT_CONTEXT,
    TERMINAL_REJECTED,
    DeterministicRenderer,
    GenerationOutputContractError,
    GroundedContextProjector,
    GroundedGenerationRequestBuilder,
    GroundingEvidenceLogger,
    GroundingFailureController,
    GroundingValidator,
    MaterialRequirementGate,
    RenderAuthorizationError,
    generation_output_schema_hash,
    output_digest,
    parse_generation_output,
)


class FakeAtomicityRoleValidator:
    def __init__(self, overrides: dict[str, tuple[str, str]] | None = None) -> None:
        self.overrides = overrides or {}

    def validate(self, *, text: str, semantic_role: str, purpose: str, presentation_role: str) -> dict:
        atomicity, role = self.overrides.get(text, ("ATOMIC", "ROLE_VALID"))
        return {"atomicity_verdict": atomicity, "role_boundary_verdict": role, "validator_id": "fake-atomicity-role"}


class FakeFactVerifier:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}

    def verify(self, *, claim_text: str, support_units: list[dict]) -> dict:
        return {"verdict": self.verdicts.get(claim_text, "UNSUPPORTED"), "verifier_id": "fake-fact-checker", "score": 0.5}


class FakeFactJudge:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}

    def judge(self, *, claim_text: str, support_units: list[dict]) -> dict:
        return {"verdict": self.verdicts.get(claim_text, "UNSUPPORTED"), "judge_id": "fake-source-fact-judge"}


class FakeDerivationJudge:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}
        self.calls = 0

    def judge(self, *, conclusion_text: str, premise_texts: list[str], premise_metadata: list[dict], purpose: str) -> dict:
        self.calls += 1
        return {"verdict": self.verdicts.get(conclusion_text, "UNSUPPORTED_DERIVATION"), "judge_id": "fake-derivation-judge"}


def object_payload(object_id: str, name: str, statement_id: str, text: str) -> dict:
    return {
        "object_id": object_id,
        "name": name,
        "aliases": [],
        "object_status": "active",
        "requested_version_id": None,
        "resolved_version_id": f"version-{object_id}",
        "is_current": True,
        "primary_class": None,
        "additional_classes": [],
        "context_scope": {},
        "knowledge": {
            "default_language": "en",
            "result_status": "accepted",
            "summary": [{"statement_id": statement_id, "local_key": statement_id, "text": text, "derivation_kind": "direct", "language": "en", "facet": None, "temporal_scope": None, "attribution": None, "evidence": []}],
            "facets": [],
            "attributes": [],
            "relations": [],
        },
        "omitted": {},
        "budget": {"limit_characters": 12000, "used_characters": 100, "omitted_items": 0, "truncated": False},
        "warnings": [],
    }


def context_builder_output(*, purpose: str = "roleplay", objects: list[dict] | None = None) -> dict:
    if objects is None:
        objects = [object_payload("object-saber", "Saber", "statement-contract", "Saber is contracted to Shirou.")]
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
        "objects": objects,
        "budget": {"metric": "serialized_json_characters", "limit_characters": 12000, "used_characters": 100, "omitted_items": 0, "truncated": False},
        "warnings": [],
    }


def projected_context(*, purpose: str = "roleplay", objects: list[dict] | None = None) -> dict:
    return GroundedContextProjector().project(context_builder_output(purpose=purpose, objects=objects))


def comparison_context() -> dict:
    return projected_context(purpose="comparison", objects=[
        object_payload("object-a", "Work A", "statement-a", "Work A emphasizes conflict."),
        object_payload("object-b", "Work B", "statement-b", "Work B emphasizes cooperation."),
    ])


def creative_context() -> dict:
    return projected_context(purpose="creative", objects=[
        object_payload("concept-tsundere", "Tsundere", "statement-tsundere", "Tsundere combines initially cold behavior with warmer affection."),
        object_payload("concept-journey", "Hero's Journey", "statement-journey", "The Hero's Journey describes a departure, trials, and return structure."),
    ])


def statement_ref(context: dict, statement_id: str) -> str:
    return next(unit["ref_id"] for unit in context["grounding_units"] if unit["canonical_ref"] == {"kind": "statement", "id": statement_id})


def output_envelope(context: dict, blocks: list[dict]) -> dict:
    return {"contract_version": "sgokb.grounded-generation-output.v2", "context_fingerprint": context["context_fingerprint"], "purpose": context["purpose"], "blocks": blocks}


def source_fact_block(*units: dict) -> dict:
    return {"block_id": "B1", "presentation_role": "main", "units": list(units)}


def source_fact(unit_id: str, text: str, ref: str) -> dict:
    return {"unit_id": unit_id, "semantic_role": "source_fact", "text": text, "support_refs": [ref]}


def interpretation_block(unit_id: str, text: str, premise_unit_ids: list[str]) -> dict:
    return {"block_id": "B2", "presentation_role": "interpretation", "units": [{"unit_id": unit_id, "semantic_role": "interpretation", "text": text, "premise_unit_ids": premise_unit_ids}]}


def creative_block(unit_id: str, text: str) -> dict:
    return {"block_id": "B3", "presentation_role": "creative", "units": [{"unit_id": unit_id, "semantic_role": "creative_addition", "text": text}]}


def context_limit_block() -> dict:
    return {"block_id": "B1", "presentation_role": "context_limit", "units": [{"unit_id": "U1", "semantic_role": "context_limit", "limit_code": "material_requirements_not_satisfied"}]}


def validator(*, atomicity: FakeAtomicityRoleValidator | None = None, fact_verifier: FakeFactVerifier | None = None, fact_judge: FakeFactJudge | None = None, derivation: FakeDerivationJudge | None = None) -> GroundingValidator:
    return GroundingValidator(atomicity_role_validator=atomicity or FakeAtomicityRoleValidator(), source_fact_verifier=fact_verifier, source_fact_judge=fact_judge, interpretation_judge=derivation)


def roleplay_profile(minimum: int = 2) -> dict:
    return {"profile_id": "n04-v3-case-1-roleplay", "profile_version": "1", "required_source_object_ids": ["object-saber"], "minimum_supported_source_fact_units": minimum, "minimum_source_fact_per_object": 1, "minimum_interpretation_units": 0, "require_cross_source_interpretation": False, "minimum_creative_addition_units": 0}


def comparison_profile() -> dict:
    return {"profile_id": "n04-v3-case-2-comparison", "profile_version": "1", "required_source_object_ids": ["object-a", "object-b"], "minimum_supported_source_fact_units": 0, "minimum_source_fact_per_object": 1, "minimum_interpretation_units": 1, "require_cross_source_interpretation": True, "minimum_creative_addition_units": 0}


def creative_profile() -> dict:
    return {"profile_id": "n04-v3-case-3-creative", "profile_version": "1", "required_source_object_ids": ["concept-tsundere", "concept-journey"], "minimum_supported_source_fact_units": 0, "minimum_source_fact_per_object": 1, "minimum_interpretation_units": 0, "require_cross_source_interpretation": False, "minimum_creative_addition_units": 1}


def test_grounded_context_projection_is_deterministic_and_non_mutating():
    source = context_builder_output()
    before = copy.deepcopy(source)
    first = GroundedContextProjector().project(source)
    second = GroundedContextProjector().project(source)
    assert source == before
    assert first == second
    assert GroundedContextProjector.verify(first)
    assert [unit["ref_id"] for unit in first["grounding_units"]] == ["K1", "K2"]


def test_output_v2_accepts_valid_shape_and_rejects_model_label():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    payload = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    assert parse_generation_output(json.dumps(payload)) == payload
    invalid = copy.deepcopy(payload)
    invalid["blocks"][0]["label"] = "Untrusted label"
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(invalid)


def test_output_v2_rejects_stylistic_expression_and_mixed_context_limit():
    context = projected_context()
    invalid_style = output_envelope(context, [{"block_id": "B1", "presentation_role": "main", "units": [{"unit_id": "U1", "semantic_role": "stylistic_expression", "text": "Very well."}]}])
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(invalid_style)
    ref = statement_ref(context, "statement-contract")
    mixed = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref)), {"block_id": "B2", "presentation_role": "context_limit", "units": [{"unit_id": "U2", "semantic_role": "context_limit", "limit_code": "material_requirements_not_satisfied"}]}])
    with pytest.raises(GenerationOutputContractError) as exc_info:
        parse_generation_output(mixed)
    assert exc_info.value.failure_code == "context_limit_mixed_output"


def test_output_digest_is_canonical_and_content_sensitive():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    payload = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    reordered = {"blocks": payload["blocks"], "purpose": payload["purpose"], "context_fingerprint": payload["context_fingerprint"], "contract_version": payload["contract_version"]}
    changed = copy.deepcopy(payload)
    changed["blocks"][0]["units"][0]["text"] = "Changed"
    assert output_digest(payload) == output_digest(reordered)
    assert output_digest(payload) != output_digest(changed)


def test_request_builder_exposes_v2_schema_hash_and_requirement_profile():
    context = projected_context()
    request = GroundedGenerationRequestBuilder().build(user_task="Answer as Saber.", grounded_context=context)
    assert request["output_contract"]["contract_version"] == "sgokb.grounded-generation-output.v2"
    assert request["output_contract"]["json_schema_hash"] == generation_output_schema_hash()
    assert request["requirement_profile"]["profile_id"] == "sgokb-generic-roleplay"
    assert "stylistic_expression" not in request["output_contract"]["allowed_semantic_roles"]


def test_exact_source_fact_passes_v3_after_atomicity_role_gate():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    validation = validator().validate(context, output)
    assert validation["verdict"] == "PASS"
    assert validation["unit_results"][0]["validation_stage"] == "V3"
    assert validation["unit_results"][0]["grounding_disposition"] == "supported"


def test_missing_atomicity_role_validator_is_fail_closed():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    validation = GroundingValidator().validate(context, output)
    assert validation["verdict"] == "INDETERMINATE"
    assert any(item["failure_class"] == "VALIDATOR_UNAVAILABLE" for item in validation["failures"])


def test_non_atomic_unit_never_reaches_support_pass():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    text = "Saber is contracted to Shirou and secretly protects him in every war."
    output = output_envelope(context, [source_fact_block(source_fact("U1", text, ref))])
    validation = validator(atomicity=FakeAtomicityRoleValidator({text: ("NON_ATOMIC", "ROLE_VALID")})).validate(context, output)
    assert validation["verdict"] == "FAIL"
    assert validation["failures"][0]["failure_class"] == "ATOMICITY_VIOLATION"


def test_unresolved_source_fact_specialized_negative_fails():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    text = "Saber protects Shirou throughout the Holy Grail War."
    output = output_envelope(context, [source_fact_block(source_fact("U1", text, ref))])
    validation = validator(fact_verifier=FakeFactVerifier({text: "UNSUPPORTED"})).validate(context, output)
    assert validation["verdict"] == "FAIL"
    assert validation["failures"][0]["failure_class"] == "UNSUPPORTED_CLAIM"


def test_unresolved_source_fact_requires_specialized_and_independent_agreement():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    text = "Saber has a contract with Shirou."
    output = output_envelope(context, [source_fact_block(source_fact("U1", text, ref))])
    accepted = validator(fact_verifier=FakeFactVerifier({text: "SUPPORTED_CANDIDATE"}), fact_judge=FakeFactJudge({text: "ENTAILED"})).validate(context, output)
    assert accepted["verdict"] == "PASS"
    disagreed = validator(fact_verifier=FakeFactVerifier({text: "SUPPORTED_CANDIDATE"}), fact_judge=FakeFactJudge({text: "UNSUPPORTED"})).validate(context, output)
    assert disagreed["verdict"] == "INDETERMINATE"
    assert disagreed["failures"][0]["failure_class"] == "VERIFIER_DISAGREEMENT"


def test_interpretation_references_validated_source_fact_units_not_k_refs():
    context = comparison_context()
    ref_a = statement_ref(context, "statement-a")
    ref_b = statement_ref(context, "statement-b")
    conclusion = "The works differ in the emphasis described by the supplied facts."
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Work A emphasizes conflict.", ref_a), source_fact("U2", "Work B emphasizes cooperation.", ref_b)), interpretation_block("U3", conclusion, ["U1", "U2"])])
    validation = validator(derivation=FakeDerivationJudge({conclusion: "REASONABLE_DERIVATION"})).validate(context, output)
    assert validation["verdict"] == "PASS"
    result = next(item for item in validation["unit_results"] if item["unit_id"] == "U3")
    assert result["grounding_disposition"] == "derived_supported"
    assert result["premise_unit_ids"] == ["U1", "U2"]


def test_unsupported_premise_blocks_derivation_judge():
    context = comparison_context()
    ref_a = statement_ref(context, "statement-a")
    ref_b = statement_ref(context, "statement-b")
    bad_text = "Work B is a destiny-driven epic."
    conclusion = "Both works are destiny-driven."
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Work A emphasizes conflict.", ref_a), source_fact("U2", bad_text, ref_b)), interpretation_block("U3", conclusion, ["U1", "U2"])])
    derivation = FakeDerivationJudge({conclusion: "REASONABLE_DERIVATION"})
    validation = validator(fact_verifier=FakeFactVerifier({bad_text: "UNSUPPORTED"}), derivation=derivation).validate(context, output)
    assert validation["verdict"] == "FAIL"
    assert any(item["failure_class"] == "PREMISE_INTEGRITY_ERROR" for item in validation["failures"])
    assert derivation.calls == 0


def test_creative_addition_uses_role_gate_but_no_source_support_refs():
    context = creative_context()
    ref_a = statement_ref(context, "statement-tsundere")
    ref_b = statement_ref(context, "statement-journey")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Tsundere combines initially cold behavior with warmer affection.", ref_a), source_fact("U2", "The Hero's Journey describes a departure, trials, and return structure.", ref_b)), creative_block("U3", "A guarded knight gradually learns to trust companions.")])
    validation = validator().validate(context, output)
    assert validation["verdict"] == "PASS"
    creative = next(item for item in validation["unit_results"] if item["unit_id"] == "U3")
    assert creative["grounding_disposition"] == "not_applicable"


def test_roleplay_material_minimum_is_separate_from_grounding_pass():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    validation = validator().validate(context, output)
    material = MaterialRequirementGate().evaluate(context, validation, requirement_profile=roleplay_profile())
    decision = GroundingFailureController().decide(validation, material, attempt=1)
    assert validation["verdict"] == "PASS"
    assert material["verdict"] == MATERIAL_FAIL_REPAIRABLE
    assert decision["action"] == ACTION_RETRY


def test_comparison_requires_both_sources_and_cross_source_interpretation():
    context = comparison_context()
    ref_a = statement_ref(context, "statement-a")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Work A emphasizes conflict.", ref_a))])
    validation = validator().validate(context, output)
    material = MaterialRequirementGate().evaluate(context, validation, requirement_profile=comparison_profile())
    assert material["verdict"] == MATERIAL_FAIL_REPAIRABLE
    assert "object-b" in material["missing_source_object_ids"]


def test_comparison_full_flow_accepts_and_renders_only_validated_text():
    context = comparison_context()
    ref_a = statement_ref(context, "statement-a")
    ref_b = statement_ref(context, "statement-b")
    conclusion = "The supplied facts describe different thematic emphases."
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Work A emphasizes conflict.", ref_a), source_fact("U2", "Work B emphasizes cooperation.", ref_b)), interpretation_block("U3", conclusion, ["U1", "U2"])])
    validation = validator(derivation=FakeDerivationJudge({conclusion: "REASONABLE_DERIVATION"})).validate(context, output)
    material = MaterialRequirementGate().evaluate(context, validation, requirement_profile=comparison_profile())
    decision = GroundingFailureController().decide(validation, material, attempt=1)
    rendered = DeterministicRenderer().render(output, validation, material, decision)
    assert material["verdict"] == MATERIAL_PASS
    assert decision["action"] == TERMINAL_ACCEPTED
    assert decision["render_mode"] == RENDER_MODE_NORMAL
    assert rendered == "Work A emphasizes conflict. Work B emphasizes cooperation.\n\nInterpretation\nThe supplied facts describe different thematic emphases."


def test_creative_material_requires_both_concepts_and_creative_addition():
    context = creative_context()
    ref_a = statement_ref(context, "statement-tsundere")
    ref_b = statement_ref(context, "statement-journey")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Tsundere combines initially cold behavior with warmer affection.", ref_a), source_fact("U2", "The Hero's Journey describes a departure, trials, and return structure.", ref_b)), creative_block("U3", "A guarded knight leaves home and returns more open to others.")])
    validation = validator().validate(context, output)
    material = MaterialRequirementGate().evaluate(context, validation, requirement_profile=creative_profile())
    assert material["verdict"] == MATERIAL_PASS


def test_context_limit_requires_independent_material_gate_justification():
    context = projected_context()
    output = output_envelope(context, [context_limit_block()])
    validation = GroundingValidator().validate(context, output)
    unjustified = MaterialRequirementGate().evaluate(context, validation, requirement_profile=roleplay_profile(minimum=1))
    first = GroundingFailureController().decide(validation, unjustified, attempt=1)
    assert unjustified["verdict"] == MATERIAL_FAIL_REPAIRABLE
    assert first["action"] == ACTION_RETRY
    justified = MaterialRequirementGate().evaluate(context, validation, requirement_profile=roleplay_profile(minimum=3))
    terminal = GroundingFailureController().decide(validation, justified, attempt=1)
    rendered = DeterministicRenderer().render(output, validation, justified, terminal)
    assert justified["verdict"] == MATERIAL_FAIL_CONTEXT_INSUFFICIENT
    assert terminal["action"] == TERMINAL_INSUFFICIENT_CONTEXT
    assert terminal["render_mode"] == RENDER_MODE_CONTEXT_LIMIT_ONLY
    assert rendered.startswith("Context limit\n")
    assert "Saber" not in rendered


def test_renderer_rejects_rejected_terminal_and_binding_mismatch():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    validation = validator().validate(context, output)
    material = MaterialRequirementGate().evaluate(context, validation)
    terminal = GroundingFailureController().decide(validation, material, attempt=1)
    rejected = copy.deepcopy(terminal)
    rejected["action"] = TERMINAL_REJECTED
    rejected["render_mode"] = "NONE"
    with pytest.raises(RenderAuthorizationError):
        DeterministicRenderer().render(output, validation, material, rejected)
    mismatched = copy.deepcopy(terminal)
    mismatched["binding"]["output_digest"] = "0" * 64
    with pytest.raises(RenderAuthorizationError) as exc_info:
        DeterministicRenderer().render(output, validation, material, mismatched)
    assert exc_info.value.failure_code == "output_decision_binding_mismatch"


def test_retry_feedback_contains_grounding_repair_context_only():
    context = projected_context()
    ref = statement_ref(context, "statement-contract")
    text = "Saber protects Shirou throughout the Holy Grail War."
    output = output_envelope(context, [source_fact_block(source_fact("U1", text, ref))])
    validation = validator(fact_verifier=FakeFactVerifier({text: "UNSUPPORTED"})).validate(context, output)
    controller = GroundingFailureController()
    decision = controller.decide(validation, None, attempt=1)
    feedback = controller.build_retry_feedback(validation)
    assert decision["action"] == ACTION_RETRY
    assert feedback["attempt"] == 2
    assert feedback["failed_units"] == ["U1"]
    assert "grounded_context" not in feedback
    assert "web" not in json.dumps(feedback).lower()


def test_evidence_logger_persists_v3_decision_artifacts(tmp_path):
    logger = GroundingEvidenceLogger(tmp_path)
    logger.write_attempt("case-roleplay", 1, request={"request": 1}, response={"response": 1}, validation={"verdict": "PASS"})
    material_path, terminal_path, rendered_path = logger.write_v3_decision("case-roleplay", 1, material_result={"verdict": "PASS"}, terminal_decision={"action": "ACCEPTED"}, rendered_output="Rendered")
    assert json.loads(material_path.read_text(encoding="utf-8")) == {"verdict": "PASS"}
    assert json.loads(terminal_path.read_text(encoding="utf-8")) == {"action": "ACCEPTED"}
    assert rendered_path is not None
    assert rendered_path.read_text(encoding="utf-8") == "Rendered\n"


def test_application_facade_wires_validation_material_terminal_and_render():
    app = GroundedGenerationApplication(atomicity_role_validator=FakeAtomicityRoleValidator())
    context = app.project_context(context_builder_output())
    request = app.build_request(user_task="Answer only from supplied context.", grounded_context=context)
    ref = statement_ref(context, "statement-contract")
    output = output_envelope(context, [source_fact_block(source_fact("U1", "Saber is contracted to Shirou.", ref))])
    validation = app.validate(context, output, attempt=1)
    material = app.evaluate_material(context, validation)
    decision = app.decide(validation, material, attempt=1)
    rendered = app.render(output, validation, material, decision)
    assert request["output_contract"]["contract_version"].endswith(".v2")
    assert validation["verdict"] == "PASS"
    assert material["verdict"] == MATERIAL_PASS
    assert decision["action"] == TERMINAL_ACCEPTED
    assert rendered == "Saber is contracted to Shirou."
