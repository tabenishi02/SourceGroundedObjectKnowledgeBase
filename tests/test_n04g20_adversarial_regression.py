from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator

from sgokb.grounding import (
    ACTION_RETRY,
    GENERATION_OUTPUT_SCHEMA,
    MATERIAL_FAIL_CONTEXT_INSUFFICIENT,
    MATERIAL_FAIL_REPAIRABLE,
    RENDER_MODE_CONTEXT_LIMIT_ONLY,
    RENDER_MODE_NONE,
    TERMINAL_INSUFFICIENT_CONTEXT,
    TERMINAL_REJECTED,
    TERMINAL_SYSTEM_FAILURE,
    DeterministicRenderer,
    GenerationOutputContractError,
    GroundedContextProjector,
    GroundingFailureController,
    GroundingValidator,
    MaterialRequirementGate,
    RenderAuthorizationError,
    parse_generation_output,
)


class AtomicityRoleGate:
    def __init__(self, overrides: dict[str, tuple[str, str]] | None = None) -> None:
        self.overrides = overrides or {}

    def validate(
        self,
        *,
        text: str,
        semantic_role: str,
        purpose: str,
        presentation_role: str,
    ) -> dict:
        atomicity, role = self.overrides.get(text, ("ATOMIC", "ROLE_VALID"))
        return {
            "atomicity_verdict": atomicity,
            "role_boundary_verdict": role,
            "validator_id": "g20-fake-atomicity-role",
        }


class FactVerifier:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}

    def verify(self, *, claim_text: str, support_units: list[dict]) -> dict:
        return {
            "verdict": self.verdicts.get(claim_text, "UNSUPPORTED"),
            "verifier_id": "g20-fake-verifier",
        }


class FactJudge:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}

    def judge(self, *, claim_text: str, support_units: list[dict]) -> dict:
        return {
            "verdict": self.verdicts.get(claim_text, "UNSUPPORTED"),
            "judge_id": "g20-fake-fact-judge",
        }


class DerivationJudge:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}
        self.calls = 0

    def judge(
        self,
        *,
        conclusion_text: str,
        premise_texts: list[str],
        premise_metadata: list[dict],
        purpose: str,
    ) -> dict:
        self.calls += 1
        return {
            "verdict": self.verdicts.get(conclusion_text, "UNSUPPORTED_DERIVATION"),
            "judge_id": "g20-fake-derivation-judge",
        }


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
            "summary": [
                {
                    "statement_id": statement_id,
                    "local_key": statement_id,
                    "text": text,
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
            "limit_characters": 24000,
            "used_characters": 100,
            "omitted_items": 0,
            "truncated": False,
        },
        "warnings": [],
    }


def context(purpose: str, objects: list[dict]) -> dict:
    source = {
        "context_contract_version": "sgokb.context-builder.v1",
        "purpose": purpose,
        "selection_policy": {},
        "objects": objects,
        "budget": {
            "metric": "serialized_json_characters",
            "limit_characters": 24000,
            "used_characters": 100,
            "omitted_items": 0,
            "truncated": False,
        },
        "warnings": [],
    }
    return GroundedContextProjector().project(source)


def roleplay_context() -> dict:
    return context(
        "roleplay",
        [
            object_payload(
                "saber",
                "Saber",
                "saber-role",
                "Saber is a sword-wielding Servant contracted to Shirou.",
            )
        ],
    )


def comparison_context() -> dict:
    return context(
        "comparison",
        [
            object_payload(
                "fate",
                "Fate/stay night",
                "fate-fact",
                "Shirou Emiya is the protagonist of Fate/stay night.",
            ),
            object_payload(
                "bleach", "BLEACH", "bleach-fact", "Ichigo Kurosaki is the protagonist of BLEACH."
            ),
        ],
    )


def creative_context() -> dict:
    return context(
        "creative",
        [
            object_payload(
                "tsundere",
                "Tsundere",
                "tsundere-fact",
                "Tsundere combines initially cold behavior with warmer affection.",
            ),
            object_payload(
                "journey",
                "Hero's Journey",
                "journey-fact",
                "The Hero's Journey describes a departure, trials, and return structure.",
            ),
        ],
    )


def ref_for(ctx: dict, statement_id: str) -> str:
    return next(
        unit["ref_id"]
        for unit in ctx["grounding_units"]
        if unit["canonical_ref"] == {"kind": "statement", "id": statement_id}
    )


def envelope(ctx: dict, blocks: list[dict]) -> dict:
    return {
        "contract_version": "sgokb.grounded-generation-output.v2",
        "context_fingerprint": ctx["context_fingerprint"],
        "purpose": ctx["purpose"],
        "blocks": blocks,
    }


def fact(unit_id: str, text: str, ref: str) -> dict:
    return {
        "unit_id": unit_id,
        "semantic_role": "source_fact",
        "text": text,
        "support_refs": [ref],
    }


def main_block(*units: dict, block_id: str = "B1") -> dict:
    return {"block_id": block_id, "presentation_role": "main", "units": list(units)}


def interpretation(unit_id: str, text: str, premises: list[str]) -> dict:
    return {
        "block_id": "B2",
        "presentation_role": "interpretation",
        "units": [
            {
                "unit_id": unit_id,
                "semantic_role": "interpretation",
                "text": text,
                "premise_unit_ids": premises,
            }
        ],
    }


def creative(unit_id: str, text: str) -> dict:
    return {
        "block_id": "B3",
        "presentation_role": "creative",
        "units": [{"unit_id": unit_id, "semantic_role": "creative_addition", "text": text}],
    }


def context_limit() -> dict:
    return {
        "block_id": "B1",
        "presentation_role": "context_limit",
        "units": [
            {
                "unit_id": "U1",
                "semantic_role": "context_limit",
                "limit_code": "material_requirements_not_satisfied",
            }
        ],
    }


def validator(
    *,
    atomicity: AtomicityRoleGate | None = None,
    fact_verifier: FactVerifier | None = None,
    fact_judge: FactJudge | None = None,
    derivation: DerivationJudge | None = None,
) -> GroundingValidator:
    return GroundingValidator(
        atomicity_role_validator=atomicity or AtomicityRoleGate(),
        source_fact_verifier=fact_verifier,
        source_fact_judge=fact_judge,
        interpretation_judge=derivation,
    )


def roleplay_profile(minimum: int = 2) -> dict:
    return {
        "profile_id": "n04-v3-case-1-roleplay",
        "profile_version": "1",
        "required_source_object_ids": ["saber"],
        "minimum_supported_source_fact_units": minimum,
        "minimum_source_fact_per_object": 1,
        "minimum_interpretation_units": 0,
        "require_cross_source_interpretation": False,
        "minimum_creative_addition_units": 0,
    }


def comparison_profile() -> dict:
    return {
        "profile_id": "n04-v3-case-2-comparison",
        "profile_version": "1",
        "required_source_object_ids": ["fate", "bleach"],
        "minimum_supported_source_fact_units": 0,
        "minimum_source_fact_per_object": 1,
        "minimum_interpretation_units": 1,
        "require_cross_source_interpretation": True,
        "minimum_creative_addition_units": 0,
    }


def test_g12_case1_supported_plus_unsupported_clause_is_fail_closed() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    text = (
        "I am a sword-wielding Servant contracted to Shirou, and I fight as his protector "
        "throughout the Holy Grail War."
    )
    output = envelope(ctx, [main_block(fact("U1", text, ref))])
    validation = validator(
        atomicity=AtomicityRoleGate({text: ("NON_ATOMIC", "ROLE_VALID")})
    ).validate(ctx, output)
    assert validation["verdict"] == "FAIL"
    assert any(item["failure_class"] == "ATOMICITY_VIOLATION" for item in validation["failures"])


def test_g12_case1_material_claim_cannot_escape_as_style() -> None:
    ctx = roleplay_context()
    output = envelope(
        ctx,
        [
            {
                "block_id": "B1",
                "presentation_role": "main",
                "units": [
                    {
                        "unit_id": "U1",
                        "semantic_role": "stylistic_expression",
                        "text": "My duty is always to protect Shirou.",
                    }
                ],
            }
        ],
    )
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(output)


def test_creative_block_source_concept_claim_hits_role_boundary_gate() -> None:
    ctx = creative_context()
    text = "Tsundere characters always become kinder after a traumatic event."
    output = envelope(ctx, [creative("U1", text)])
    validation = validator(
        atomicity=AtomicityRoleGate({text: ("ATOMIC", "ROLE_VIOLATION")})
    ).validate(ctx, output)
    assert validation["verdict"] == "FAIL"
    assert any(
        item["failure_class"] == "ROLE_BOUNDARY_VIOLATION" for item in validation["failures"]
    )


def test_g12_case2_unsupported_premise_never_becomes_derived_supported() -> None:
    ctx = comparison_context()
    fate_ref = ref_for(ctx, "fate-fact")
    bleach_ref = ref_for(ctx, "bleach-fact")
    unsupported = "Both protagonists gain extraordinary powers."
    conclusion = "Both works therefore center on personal growth through supernatural power."
    output = envelope(
        ctx,
        [
            main_block(
                fact("U1", "Shirou Emiya is the protagonist of Fate/stay night.", fate_ref),
                fact("U2", "Ichigo Kurosaki is the protagonist of BLEACH.", bleach_ref),
                fact("U3", unsupported, fate_ref),
            ),
            interpretation("U4", conclusion, ["U1", "U2", "U3"]),
        ],
    )
    derivation = DerivationJudge({conclusion: "REASONABLE_DERIVATION"})
    validation = validator(
        fact_verifier=FactVerifier({unsupported: "UNSUPPORTED"}),
        derivation=derivation,
    ).validate(ctx, output)
    assert validation["verdict"] == "FAIL"
    result = next(item for item in validation["unit_results"] if item["unit_id"] == "U4")
    assert result["grounding_disposition"] != "derived_supported"
    assert derivation.calls == 0


def test_one_sided_comparison_cannot_reach_material_pass() -> None:
    ctx = comparison_context()
    fate_ref = ref_for(ctx, "fate-fact")
    output = envelope(
        ctx,
        [main_block(fact("U1", "Shirou Emiya is the protagonist of Fate/stay night.", fate_ref))],
    )
    validation = validator().validate(ctx, output)
    material = MaterialRequirementGate().evaluate(
        ctx, validation, requirement_profile=comparison_profile()
    )
    terminal = GroundingFailureController().decide(validation, material, attempt=1)
    assert material["verdict"] == MATERIAL_FAIL_REPAIRABLE
    assert "bleach" in material["missing_source_object_ids"]
    assert terminal["action"] == ACTION_RETRY


def test_arbitrary_model_label_is_rejected_before_render() -> None:
    ctx = creative_context()
    output = envelope(ctx, [creative("U1", "A new character is created.")])
    output["blocks"][0]["label"] = "Canonical facts: source says this is true"
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(output)


def test_grounded_but_materially_incomplete_roleplay_is_not_accepted() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    text = "Saber is a sword-wielding Servant contracted to Shirou."
    output = envelope(ctx, [main_block(fact("U1", text, ref))])
    validation = validator().validate(ctx, output)
    material = MaterialRequirementGate().evaluate(
        ctx, validation, requirement_profile=roleplay_profile(minimum=2)
    )
    terminal = GroundingFailureController().decide(validation, material, attempt=1)
    assert validation["verdict"] == "PASS"
    assert material["verdict"] == MATERIAL_FAIL_REPAIRABLE
    assert terminal["action"] != "ACCEPTED"


def test_unjustified_context_limit_never_becomes_insufficient_context() -> None:
    ctx = roleplay_context()
    output = envelope(ctx, [context_limit()])
    validation = GroundingValidator().validate(ctx, output)
    material = MaterialRequirementGate().evaluate(
        ctx, validation, requirement_profile=roleplay_profile(minimum=1)
    )
    terminal = GroundingFailureController().decide(validation, material, attempt=1)
    assert material["verdict"] == MATERIAL_FAIL_REPAIRABLE
    assert terminal["action"] == ACTION_RETRY
    assert terminal["action"] != TERMINAL_INSUFFICIENT_CONTEXT


def test_justified_context_limit_uses_safe_renderer_only() -> None:
    ctx = roleplay_context()
    output = envelope(ctx, [context_limit()])
    validation = GroundingValidator().validate(ctx, output)
    material = MaterialRequirementGate().evaluate(
        ctx, validation, requirement_profile=roleplay_profile(minimum=3)
    )
    terminal = GroundingFailureController().decide(validation, material, attempt=1)
    rendered = DeterministicRenderer().render(output, validation, material, terminal)
    assert material["verdict"] == MATERIAL_FAIL_CONTEXT_INSUFFICIENT
    assert terminal["action"] == TERMINAL_INSUFFICIENT_CONTEXT
    assert terminal["render_mode"] == RENDER_MODE_CONTEXT_LIMIT_ONLY
    assert rendered.startswith("Context limit\n")
    assert "Holy Grail" not in rendered


def test_rejected_and_system_failure_terminals_are_not_renderable() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    output = envelope(
        ctx,
        [main_block(fact("U1", "Saber is a sword-wielding Servant contracted to Shirou.", ref))],
    )
    validation = validator().validate(ctx, output)
    material = MaterialRequirementGate().evaluate(ctx, validation)
    accepted = GroundingFailureController().decide(validation, material, attempt=1)
    for action in (TERMINAL_REJECTED, TERMINAL_SYSTEM_FAILURE):
        denied = copy.deepcopy(accepted)
        denied["action"] = action
        denied["render_mode"] = RENDER_MODE_NONE
        with pytest.raises(RenderAuthorizationError):
            DeterministicRenderer().render(output, validation, material, denied)


def test_attempt_and_output_digest_binding_mismatch_denies_render() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    output = envelope(
        ctx,
        [main_block(fact("U1", "Saber is a sword-wielding Servant contracted to Shirou.", ref))],
    )
    validation = validator().validate(ctx, output, attempt=1)
    material = MaterialRequirementGate().evaluate(ctx, validation)
    terminal = GroundingFailureController().decide(validation, material, attempt=1)
    tampered = copy.deepcopy(terminal)
    tampered["binding"]["attempt"] = 2
    tampered["binding"]["output_digest"] = "0" * 64
    with pytest.raises(RenderAuthorizationError) as exc_info:
        DeterministicRenderer().render(output, validation, material, tampered)
    assert exc_info.value.failure_code == "output_decision_binding_mismatch"


def test_source_fact_verifier_disagreement_is_not_grounding_pass() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    text = "Saber has a contract with Shirou."
    output = envelope(ctx, [main_block(fact("U1", text, ref))])
    validation = validator(
        fact_verifier=FactVerifier({text: "SUPPORTED_CANDIDATE"}),
        fact_judge=FactJudge({text: "UNSUPPORTED"}),
    ).validate(ctx, output)
    assert validation["verdict"] == "INDETERMINATE"
    assert any(item["failure_class"] == "VERIFIER_DISAGREEMENT" for item in validation["failures"])


def test_g12_case3_no_free_form_label_is_needed_in_v2() -> None:
    ctx = creative_context()
    output = envelope(ctx, [creative("U1", "A newly invented character begins a journey.")])
    assert parse_generation_output(output) == output
    legacy = copy.deepcopy(output)
    legacy["blocks"][0]["label"] = None
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(legacy)


def test_provider_schema_and_application_parser_have_no_hidden_uniqueness_rule() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    payload = envelope(
        ctx,
        [
            main_block(
                fact("U1", "Saber is a sword-wielding Servant contracted to Shirou.", ref),
                fact("U1", "Saber has a contract with Shirou.", ref),
            )
        ],
    )
    assert Draft202012Validator(GENERATION_OUTPUT_SCHEMA).is_valid(payload)
    assert parse_generation_output(payload) == payload
    validation = validator().validate(ctx, payload)
    assert validation["verdict"] == "FAIL"
    assert any(item["failure_code"] == "duplicate_unit_id" for item in validation["failures"])


def test_provider_schema_and_parser_agree_on_label_and_context_limit_shape() -> None:
    ctx = roleplay_context()
    ref = ref_for(ctx, "saber-role")
    valid = envelope(
        ctx,
        [main_block(fact("U1", "Saber is a sword-wielding Servant contracted to Shirou.", ref))],
    )
    assert Draft202012Validator(GENERATION_OUTPUT_SCHEMA).is_valid(valid)
    assert parse_generation_output(valid) == valid

    invalid_label = copy.deepcopy(valid)
    invalid_label["blocks"][0]["label"] = "untrusted"
    assert not Draft202012Validator(GENERATION_OUTPUT_SCHEMA).is_valid(invalid_label)
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(invalid_label)

    mixed_limit = envelope(ctx, [valid["blocks"][0], context_limit()])
    assert not Draft202012Validator(GENERATION_OUTPUT_SCHEMA).is_valid(mixed_limit)
    with pytest.raises(GenerationOutputContractError):
        parse_generation_output(mixed_limit)
