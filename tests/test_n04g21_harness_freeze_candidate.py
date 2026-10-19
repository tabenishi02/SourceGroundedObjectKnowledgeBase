from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sgokb.grounding.output import generation_output_schema_hash

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "benchmark" / "n04-ai-use-cases-v3.json"
MATERIAL = ROOT / "benchmark" / "n04-v3-material-profiles-v1.json"
VERIFIER = ROOT / "benchmark" / "n04-v3-source-fact-verifier-profile-v1.json"
HARNESS = ROOT / "benchmark" / "n04-v3-formal-harness-v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(payload: dict) -> str:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _logical_payload(document: dict) -> dict:
    return {
        key: value
        for key, value in document.items()
        if key not in {"hash", "status", "design_freeze"}
    }


def test_g21_candidate_file_identities_and_schema_hash_are_bound():
    harness = _load(HARNESS)
    material = _load(MATERIAL)
    verifier = _load(VERIFIER)

    assert harness["acceptance_spec"]["sha256"] == _file_sha256(ACCEPTANCE)
    assert harness["material_profiles"]["file_sha256"] == _file_sha256(MATERIAL)
    assert harness["source_fact_verifier_profile"]["file_sha256"] == _file_sha256(VERIFIER)
    assert harness["material_profiles"]["canonical_payload_sha256"] == _canonical_sha256(
        _logical_payload(material)
    )
    assert harness["source_fact_verifier_profile"]["canonical_payload_sha256"] == (
        _canonical_sha256(_logical_payload(verifier))
    )
    assert harness["lm_studio"]["structured_output"]["provider_schema_sha256"] == (
        generation_output_schema_hash()
    )


def test_g21_candidate_keeps_g18_contracts_and_stable_case_objects():
    acceptance = _load(ACCEPTANCE)
    profiles = _load(MATERIAL)["profiles"]

    assert acceptance["contract_versions"] == {
        "context_builder": "sgokb.context-builder.v1",
        "grounded_context": "sgokb.grounded-context.v1",
        "generation_output": "sgokb.grounded-generation-output.v2",
        "validation": "sgokb.grounding-validation.v2",
        "material_requirement": "sgokb.material-requirement.v1",
        "failure_policy": "sgokb.grounding-failure-policy.v2",
    }
    assert profiles["n04-v3-case-1-roleplay"]["required_source_objects"] == [
        "326a97cf-47aa-4760-a7f1-07bfe639fcf0"
    ]
    assert profiles["n04-v3-case-1-roleplay"]["minimum_supported_source_fact_units"] == 2
    assert profiles["n04-v3-case-2-comparison"]["required_source_objects"] == [
        "d5824d33-7008-4121-9cfe-1f95a19667fd",
        "57db855c-574a-4b38-b474-421c165894f1",
    ]
    assert profiles["n04-v3-case-2-comparison"]["require_cross_source_interpretation"]
    assert profiles["n04-v3-case-3-creative"]["required_source_objects"] == [
        "8c83f986-f491-41a8-8645-9f71dd5874b9",
        "fee32007-0f92-449a-ba21-4ec2f78d1cd4",
    ]
    assert profiles["n04-v3-case-3-creative"]["minimum_creative_addition_units"] == 1


def test_g21_candidate_pins_generator_judges_and_verifier_without_gate_relaxation():
    harness = _load(HARNESS)
    verifier = _load(VERIFIER)

    assert harness["generator"]["identifier"] == "sgokb-n04-mistral32"
    assert harness["generator"]["quantization"] == "Q4_K_M"
    assert harness["bounded_semantic_model"]["identifier"] == "sgokb-n04-phi4"
    assert harness["bounded_semantic_model"]["quantization"] == "Q4_K_S"
    assert verifier["specialized_verifier"]["source_repository_revision"] == (
        "b58b9fa69acbd1015ec970fa65dd752413a053d2"
    )
    assert verifier["specialized_verifier"]["model_repository_revision"] == (
        "74c8919647e61ed0f71bc177d94f10930f090068"
    )
    assert verifier["specialized_verifier"]["supported_threshold"] == 0.5
    assert verifier["specialized_verifier"]["threshold_operator"] == ">="
    assert verifier["screening_evidence"]["required_negative_false_positive_count"] == 0
    assert verifier["screening_evidence"]["required_positive_supported_count"] == 2
    assert verifier["screening_evidence"]["reference_workstation_reproduction"] == (
        verifier["status"] == "frozen"
    )
    assert harness["retry_terminal"]["max_retries"] == 1
    assert harness["retry_terminal"]["formal_case_pass_terminal"] == "ACCEPTED"
    assert not harness["retry_terminal"]["insufficient_context_formal_case_pass"]
    assert harness["overall_pass"]["unsupported_rendered_material_claims"] == 0


def test_g21_candidate_is_not_falsely_marked_frozen_before_local_verification():
    harness = _load(HARNESS)
    acceptance = _load(ACCEPTANCE)
    material = _load(MATERIAL)
    verifier = _load(VERIFIER)

    statuses = {document["status"] for document in (harness, acceptance, material, verifier)}
    assert len(statuses) == 1
    assert harness["preflight"]["formal_run_must_not_start_until_all_pass"]
    if harness["status"] == "freeze_candidate_pending_reference_workstation_verification":
        assert len(harness["unresolved_before_freeze"]) == 3
        assert not verifier["screening_evidence"]["reference_workstation_reproduction"]
        return

    assert statuses == {"frozen"}
    assert harness["unresolved_before_freeze"] == []
    assert verifier["screening_evidence"]["reference_workstation_reproduction"]
    proof_ref = verifier["screening_evidence"]["reference_workstation_result"]
    proof_path = ROOT / proof_ref["path"]
    assert _file_sha256(proof_path) == proof_ref["sha256"]
    proof = _load(proof_path)
    assert proof["status"] == "PASS"
    assert proof["source_identity"] == {
        "revision": verifier["specialized_verifier"]["source_repository_revision"],
        "clean": True,
    }
    assert proof["model_identity"]["resolved_main_revision"] == (
        verifier["specialized_verifier"]["model_repository_revision"]
    )
    assert proof["network_attempts"] == {"socket_connect": 0, "create_connection": 0}
    assert proof["threshold"] == 0.5
    assert proof["metrics"]["required_negative_false_positive_count"] == 0
    assert proof["metrics"]["required_positive_supported_count"] == 2
    assert proof["metrics"]["required_positive_count"] == 2
    assert proof["comparison_with_g21v"]["all_verdicts_equal"]
    runtime_lock = harness["reference_workstation"]["local_runtime_lock"]
    assert runtime_lock["standard_sgokb_venv_unchanged"]
    assert runtime_lock["verifier_packages"] == proof["runtime"]["packages"]
    assert runtime_lock["verifier_cuda"] == proof["runtime"]["cuda"]
