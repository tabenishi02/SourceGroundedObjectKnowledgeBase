from __future__ import annotations

import copy
import hashlib

import pytest

from sgokb.application_grounding_v4 import GroundedGenerationV4Application
from sgokb.grounding.context import GroundedContextProjector
from sgokb.grounding.v4_contracts import (
    RETRY_FEEDBACK_VERSION,
    SYSTEM_CONTEXT_LIMIT_VERSION,
    V4ContractError,
    digest_object,
)
from sgokb.grounding.v4_pipeline import (
    ActiveAttemptLedger,
    MATERIAL_PASS,
    REQUIRED_PROVIDER_PROBE_CASES,
    TERMINAL_ACCEPTED,
)
from sgokb.grounding.v4_validation import (
    INTERPRETATION_CONTENT,
    SOURCE_FACT_CONTENT,
)


class FakeAtomicity:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}
        self.calls: list[str] = []

    def classify(self, *, claim_text: str) -> dict:
        self.calls.append(claim_text)
        return {"verdict": self.verdicts.get(claim_text, "ATOMIC"), "id": "fake-a"}


class FakeContentType:
    def __init__(self, verdicts: dict[str, str] | None = None) -> None:
        self.verdicts = verdicts or {}
        self.calls: list[str] = []

    def classify(self, *, claim_text: str) -> dict:
        self.calls.append(claim_text)
        default = SOURCE_FACT_CONTENT
        if claim_text.startswith("Interpretation:"):
            default = INTERPRETATION_CONTENT
        if claim_text.startswith("Creative:"):
            default = "CREATIVE_CONTENT"
        return {"verdict": self.verdicts.get(claim_text, default), "id": "fake-c"}


class FakeSupport:
    def __init__(self, verdict: str = "SUPPORTED") -> None:
        self.verdict = verdict

    def validate(self, *, claim_text: str, support_units: list[dict]) -> dict:
        return {"verdict": self.verdict, "support_count": len(support_units)}


class FakeDerivation:
    def __init__(self, verdict: str = "DERIVED_SUPPORTED") -> None:
        self.verdict = verdict

    def validate(
        self,
        *,
        conclusion_text: str,
        premise_texts: list[str],
        premise_metadata: list[dict],
        purpose: str,
    ) -> dict:
        return {
            "verdict": self.verdict,
            "premise_count": len(premise_texts),
            "purpose": purpose,
        }


def object_payload(object_id: str, name: str, statements: list[tuple[str, str]]) -> dict:
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
                for statement_id, text in statements
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


def grounded_context(purpose: str = "comparison") -> dict:
    objects = [
        object_payload(
            "object-a",
            "Work A",
            [
                ("statement-a1", "Work A emphasizes conflict."),
                ("statement-a2", "Work A follows one protagonist."),
            ],
        ),
        object_payload(
            "object-b",
            "Work B",
            [("statement-b1", "Work B emphasizes cooperation.")],
        ),
    ]
    source = {
        "context_contract_version": "sgokb.context-builder.v1",
        "purpose": purpose,
        "selection_policy": {
            "facet_source": "purpose_profile",
            "facet_priority": ["overall"],
            "include_summary": True,
            "include_attributes": True,
            "include_relations": True,
            "include_evidence_refs": True,
            "budget_metric": "serialized_json_characters",
            "budget_strategy": "equal_share_per_object",
            "partial_statement_truncation": False,
        },
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


def ref_for_text(context: dict, text: str) -> str:
    return next(
        unit["ref_id"]
        for unit in context["grounding_units"]
        if unit.get("content", {}).get("text") == text
    )


def app(
    *,
    atomicity: FakeAtomicity | None = None,
    content: FakeContentType | None = None,
    support: FakeSupport | None = None,
    derivation: FakeDerivation | None = None,
) -> GroundedGenerationV4Application:
    return GroundedGenerationV4Application(
        atomicity_classifier=atomicity or FakeAtomicity(),
        content_type_classifier=content or FakeContentType(),
        source_fact_support=support or FakeSupport(),
        interpretation_derivation=derivation or FakeDerivation(),
    )


def certified_fixture(purpose: str = "comparison") -> tuple:
    context = grounded_context(purpose)
    application = app()
    request = application.build_stage1_request(
        user_task="Use the supplied facts.",
        grounded_context=context,
        request_id="R-test",
        attempt_id="S1A-test",
        max_candidates=4,
    )
    ref_a = ref_for_text(context, "Work A emphasizes conflict.")
    ref_b = ref_for_text(context, "Work B emphasizes cooperation.")
    _parsed, candidates = application.parse_stage1(
        {
            "candidates": [
                {"claim_text": "Work A emphasizes conflict.", "support_refs": [ref_a]},
                {"claim_text": "Work B emphasizes cooperation.", "support_refs": [ref_b]},
            ]
        },
        request=request,
    )
    records = application.validate_stage1(candidates, grounded_context=context)
    certified, decisions = application.certify_stage1(candidates, records, request=request)
    assert all(item["certified"] for item in decisions)
    return application, context, request, candidates, records, certified


def test_schema_valid_non_atomic_text_still_routes_to_residual_atomicity() -> None:
    context = grounded_context()
    claim = "Work A emphasizes conflict and Work B emphasizes cooperation."
    atomicity = FakeAtomicity({claim: "NON_ATOMIC"})
    content = FakeContentType()
    application = app(atomicity=atomicity, content=content)
    request = application.build_stage1_request(
        user_task="Compare.",
        grounded_context=context,
        request_id="R-non-atomic",
        attempt_id="S1A-1",
    )
    ref_a = ref_for_text(context, "Work A emphasizes conflict.")
    _parsed, candidates = application.parse_stage1(
        {"candidates": [{"claim_text": claim, "support_refs": [ref_a]}]},
        request=request,
    )
    record = application.validate_stage1(candidates, grounded_context=context)[0]
    assert record["verdict"] == "FAIL"
    assert "V2_ATOMICITY_NON_ATOMIC" in record["failure_codes"]
    assert atomicity.calls == [claim]
    assert content.calls == []


def test_model_cannot_forge_role_or_validation_status() -> None:
    context = grounded_context()
    application = app()
    request = application.build_stage1_request(
        user_task="Compare.",
        grounded_context=context,
        request_id="R-forge",
        attempt_id="S1A-1",
    )
    ref_a = ref_for_text(context, "Work A emphasizes conflict.")
    with pytest.raises(V4ContractError):
        application.parse_stage1(
            {
                "candidates": [
                    {
                        "claim_text": "Work A emphasizes conflict.",
                        "support_refs": [ref_a],
                        "semantic_role": "source_fact",
                        "validation_status": "PASS",
                    }
                ]
            },
            request=request,
        )


def test_stage1_rejects_unknown_and_duplicate_support_refs() -> None:
    context = grounded_context()
    application = app()
    request = application.build_stage1_request(
        user_task="Compare.",
        grounded_context=context,
        request_id="R-refs",
        attempt_id="S1A-1",
    )
    with pytest.raises(V4ContractError):
        application.parse_stage1(
            {"candidates": [{"claim_text": "x", "support_refs": ["K999"]}]},
            request=request,
        )

    ref_a = ref_for_text(context, "Work A emphasizes conflict.")
    with pytest.raises(V4ContractError) as error:
        application.parse_stage1(
            {
                "candidates": [
                    {
                        "claim_text": "Work A emphasizes conflict.",
                        "support_refs": [ref_a, ref_a],
                    }
                ]
            },
            request=request,
        )
    assert error.value.code == "DUPLICATE_REFERENCE_ID"


def test_certification_exact_copy_and_cannot_rescue_v2_failure() -> None:
    application, _context, request, candidates, records, certified = certified_fixture()
    fact = certified["facts"][0]
    assert fact["claim_text"] == candidates[0]["payload"]["claim_text"]
    assert fact["support_refs"] == candidates[0]["payload"]["support_refs"]
    assert fact["source_candidate_digest"] == candidates[0]["candidate_digest"]

    failed = copy.deepcopy(records[0])
    failed["v2_aggregate_result"] = "FAIL"
    failed["validation_record_digest"] = digest_object(
        {key: value for key, value in failed.items() if key != "validation_record_digest"}
    )
    failed_content, decisions = application.certify_stage1(
        [candidates[0]],
        [failed],
        request=request,
    )
    assert failed_content["facts"] == []
    assert decisions[0]["reason_code"] == "NOT_CERTIFIED_V2_FAILURE"


def test_certification_rejects_tampered_validation_record() -> None:
    application, _context, request, candidates, records, _certified = certified_fixture()
    tampered = copy.deepcopy(records[0])
    tampered["verdict"] = "FAIL"
    content, decisions = application.certify_stage1(
        [candidates[0]],
        [tampered],
        request=request,
    )
    assert content["facts"] == []
    assert decisions[0]["reason_code"] == "NOT_CERTIFIED_BINDING_MISMATCH"


def test_stage2_main_is_id_only_and_factual_paraphrase_is_rejected() -> None:
    application, _context, _request, _candidates, _records, certified = certified_fixture()
    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present the comparison.",
        stage2_request_id="S2R-main",
        attempt_id="S2A-1",
    )
    with pytest.raises(V4ContractError):
        application.parse_stage2(
            {
                "blocks": [
                    {
                        "block_kind": "main",
                        "certified_fact_ids": ["CF1"],
                        "claim_text": "Work A is centered on conflict.",
                    }
                ]
            },
            request=request2,
        )


def test_stage2_interpretation_requires_active_certified_fact_id() -> None:
    application, _context, _request, _candidates, _records, certified = certified_fixture()
    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present the comparison.",
        stage2_request_id="S2R-premise",
        attempt_id="S2A-1",
    )
    with pytest.raises(V4ContractError):
        application.parse_stage2(
            {
                "blocks": [
                    {
                        "block_kind": "interpretation",
                        "candidates": [
                            {
                                "claim_text": "Interpretation: both works contrast approaches.",
                                "premise_fact_ids": ["CF999"],
                            }
                        ],
                    }
                ]
            },
            request=request2,
        )


def test_creative_block_is_denied_outside_creative_purpose() -> None:
    application, _context, _request, _candidates, _records, certified = certified_fixture()
    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present the comparison.",
        stage2_request_id="S2R-creative-deny",
        attempt_id="S2A-1",
    )
    with pytest.raises(V4ContractError):
        application.parse_stage2(
            {
                "blocks": [
                    {
                        "block_kind": "creative",
                        "candidates": [{"claim_text": "Creative: invent a new event."}],
                    }
                ]
            },
            request=request2,
        )


def test_stage2_duplicate_block_kind_and_duplicate_ids_fail_application_validation() -> None:
    application, _context, _request, _candidates, _records, certified = certified_fixture()
    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present.",
        stage2_request_id="S2R-duplicates",
        attempt_id="S2A-1",
    )
    with pytest.raises(V4ContractError) as duplicate_block:
        application.parse_stage2(
            {
                "blocks": [
                    {"block_kind": "main", "certified_fact_ids": ["CF1"]},
                    {"block_kind": "main", "certified_fact_ids": ["CF2"]},
                ]
            },
            request=request2,
        )
    assert duplicate_block.value.code == "PRESENTATION_DUPLICATE_BLOCK_KIND"

    with pytest.raises(V4ContractError) as duplicate_id:
        application.parse_stage2(
            {
                "blocks": [
                    {"block_kind": "main", "certified_fact_ids": ["CF1", "CF1"]}
                ]
            },
            request=request2,
        )
    assert duplicate_id.value.code == "DUPLICATE_REFERENCE_ID"


def test_stage2_whole_plan_invalidates_when_interpretation_fails() -> None:
    claim = "Interpretation: both works contrast approaches."
    application, _context, _request, _candidates, _records, certified = certified_fixture()
    application.validator.atomicity_classifier = FakeAtomicity({claim: "NON_ATOMIC"})
    application.validator.content_type_classifier = FakeContentType(
        {claim: INTERPRETATION_CONTENT}
    )
    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present.",
        stage2_request_id="S2R-whole-plan",
        attempt_id="S2A-1",
    )
    parsed, candidates2 = application.parse_stage2(
        {
            "blocks": [
                {"block_kind": "main", "certified_fact_ids": ["CF1"]},
                {
                    "block_kind": "interpretation",
                    "candidates": [
                        {
                            "claim_text": claim,
                            "premise_fact_ids": ["CF1", "CF2"],
                        }
                    ],
                },
            ]
        },
        request=request2,
    )
    records2 = application.validate_stage2(candidates2, certified_content=certified)
    assert records2[0]["verdict"] == "FAIL"
    with pytest.raises(ValueError):
        application.build_validated_plan(
            parsed,
            request=request2,
            certified_content=certified,
            candidate_envelopes=candidates2,
            validation_records=records2,
        )


def test_attempt_ledger_forbids_fallback_and_stage2_to_stage1_backtracking() -> None:
    ledger = ActiveAttemptLedger()
    ledger.activate("stage1", 1)
    ledger.authorize_retry("stage1", previous_attempt=1)
    ledger.activate("stage1", 2)
    with pytest.raises(ValueError):
        ledger.activate("stage1", 1)

    ledger.activate("stage2", 1)
    with pytest.raises(ValueError):
        ledger.authorize_retry("stage1", previous_attempt=1)
    with pytest.raises(ValueError):
        ledger.activate("stage1", 2)


def test_retry_builders_preserve_authoritative_inputs_and_schema() -> None:
    application, context, request1, _candidates, _records, certified = certified_fixture()
    feedback1 = application.retry.build_retry_feedback(
        stage="stage1",
        previous_attempt_id=request1["attempt_id"],
        previous_output_digest="output-1",
        failures=[
            {
                "failure_scope": "candidate",
                "failure_code": "V2_ATOMICITY_NON_ATOMIC",
                "repair_directive": "make each candidate atomic",
            }
        ],
    )
    retry1 = application.stage1_requests.build_retry(
        request1,
        retry_feedback=feedback1,
        attempt_id="S1A-2",
    )
    assert retry1["request_id"] == request1["request_id"]
    assert retry1["context_fingerprint"] == request1["context_fingerprint"]
    assert retry1["provider_schema_hash"] == request1["provider_schema_hash"]
    assert retry1["grounded_context"] == context

    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present.",
        stage2_request_id="S2R-retry",
        attempt_id="S2A-1",
    )
    feedback2 = application.retry.build_retry_feedback(
        stage="stage2",
        previous_attempt_id=request2["attempt_id"],
        previous_output_digest="output-2",
        failures=[
            {
                "failure_scope": "plan",
                "failure_code": "PRESENTATION_DUPLICATE_BLOCK_KIND",
                "repair_directive": "return at most one block per kind",
            }
        ],
    )
    retry2 = application.stage2_requests.build_retry(
        request2,
        certified_content=certified,
        retry_feedback=feedback2,
        attempt_id="S2A-2",
    )
    assert retry2["stage2_request_id"] == request2["stage2_request_id"]
    assert retry2["certified_content_digest"] == request2["certified_content_digest"]
    assert retry2["provider_schema_hash"] == request2["provider_schema_hash"]


def test_stage2_request_rejects_tampered_certified_content() -> None:
    application, _context, _request, _candidates, _records, certified = certified_fixture()
    tampered = copy.deepcopy(certified)
    tampered["facts"][0]["claim_text"] = "tampered"
    with pytest.raises(ValueError):
        application.build_stage2_request(
            certified_content=tampered,
            presentation_instruction="Present.",
        )


def test_system_context_limit_is_application_owned_only() -> None:
    application = app()
    context = grounded_context()
    artifact = application.build_system_context_limit(
        context_limit_id="CL1",
        stage_at_detection="stage1",
        request_id="R1",
        context_fingerprint=context["context_fingerprint"],
        profile={"profile_id": "p", "profile_hash": "h"},
        missing_requirement_codes=["minimum_supported_source_fact_units"],
        authoritative_input_digest="input-digest",
    )
    assert artifact["contract_version"] == SYSTEM_CONTEXT_LIMIT_VERSION
    assert "claim_text" not in artifact


def test_renderer_requires_validated_plan_and_accepted_terminal() -> None:
    application, context, _request, _candidates, _records, certified = certified_fixture()
    request2 = application.build_stage2_request(
        certified_content=certified,
        presentation_instruction="Present.",
        stage2_request_id="S2R-render",
        attempt_id="S2A-1",
    )
    parsed, candidates2 = application.parse_stage2(
        {"blocks": [{"block_kind": "main", "certified_fact_ids": ["CF1"]}]},
        request=request2,
    )
    plan = application.build_validated_plan(
        parsed,
        request=request2,
        certified_content=certified,
        candidate_envelopes=candidates2,
        validation_records=[],
    )
    profile = {
        "profile_id": "p",
        "profile_hash": "h",
        "required_source_objects": ["object-a"],
        "minimum_source_fact_per_object": 1,
    }
    material = application.evaluate_final_material(
        validated_plan=plan,
        certified_content=certified,
        grounded_context=context,
        profile=profile,
    )
    assert material["verdict"] == MATERIAL_PASS
    terminal = application.terminal_from_material(material, validation_pass=True)
    assert terminal["outcome"] == TERMINAL_ACCEPTED
    rendered = application.renderer.render_accepted(
        validated_plan=plan,
        terminal_decision=terminal,
    )
    assert "Work A emphasizes conflict." in rendered

    with pytest.raises(ValueError):
        application.renderer.render_accepted(
            validated_plan=parsed,
            terminal_decision=terminal,
        )


def test_evidence_manifest_hashes_exact_bytes_and_keeps_lineage() -> None:
    application = app()
    payload = b'{"x":1}\n'
    manifest = application.evidence.build(
        run_id="run-1",
        code_identity={"git_sha": "abc"},
        artifacts={"raw.json": payload},
        lineage={"stage1_attempt_id": "S1A-1"},
    )
    assert manifest["artifacts"][0]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert manifest["lineage"]["stage1_attempt_id"] == "S1A-1"


def test_required_provider_probe_matrix_is_explicit() -> None:
    assert set(REQUIRED_PROVIDER_PROBE_CASES) == {
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
    }


def test_retry_feedback_contract_does_not_create_replacement_claim() -> None:
    application = app()
    feedback = application.retry.build_retry_feedback(
        stage="stage1",
        previous_attempt_id="S1A-1",
        previous_output_digest="d",
        failures=[
            {
                "failure_scope": "candidate",
                "failure_code": "SOURCE_SUPPORT_UNSUPPORTED",
                "claim_text": "failed model text",
                "support_refs": ["K1"],
                "expected_rule": "use only supplied support",
                "repair_directive": "remove unsupported extra proposition",
            }
        ],
    )
    assert feedback["retry_contract_version"] == RETRY_FEEDBACK_VERSION
    assert feedback["failures"][0]["claim_text"] == "failed model text"
    assert "replacement_claim" not in feedback["failures"][0]
