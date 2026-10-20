from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "benchmark" / "n04g23a-atomicity-role-gold-seed-v1.json"
PROFILES = ROOT / "benchmark" / "n04g23a-atomicity-role-prompt-profiles-v1.json"
RUNNER = ROOT / "benchmark" / "tools" / "n04g23a_atomicity_role_benchmark.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_runner():
    spec = importlib.util.spec_from_file_location("n04g23a_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gold_seed_is_explicitly_pending_exact_g22_import() -> None:
    corpus = _load(CORPUS)
    assert corpus["status"] == "seed_pending_g22_exact_import"
    required = corpus["required_g22_import"]
    assert required["require_exact_text"] is True
    assert required["require_all_material_units_from_both_attempts"] is True
    assert "20261020T030904+0900" in required["source_evidence_root"]
    assert required["instruction"].startswith("Import exact G-22 material unit text")


def test_gold_seed_has_balanced_atomicity_and_role_boundaries() -> None:
    corpus = _load(CORPUS)
    cases = corpus["cases"]
    assert len(cases) >= 20
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids))

    atomicity = {case["gold"]["atomicity"] for case in cases}
    roles = {case["gold"]["role_boundary"] for case in cases}
    assert atomicity == {"ATOMIC", "NON_ATOMIC"}
    assert roles == {"ROLE_VALID", "ROLE_VIOLATION"}
    assert all(case["required"] is True for case in cases)
    assert any(case["origin"] == "g20_reuse" for case in cases)
    assert any(case["origin"] == "synthetic" for case in cases)


def test_gold_seed_separates_support_from_role_validity() -> None:
    corpus = _load(CORPUS)
    by_id = {case["case_id"]: case for case in corpus["cases"]}
    unsupported = by_id["unsupported-source-fact-still-role-valid"]
    negated = by_id["negated-source-fact-still-role-valid"]
    for case in (unsupported, negated):
        assert case["gold"] == {
            "atomicity": "ATOMIC",
            "role_boundary": "ROLE_VALID",
        }


def test_prompt_profiles_preserve_exact_replay_boundary() -> None:
    profiles = _load(PROFILES)
    by_id = {profile["profile_id"]: profile for profile in profiles["profiles"]}
    exact = by_id["g22-exact-joint"]
    assert exact["status"] == "requires_exact_local_evidence_import"
    assert exact["system_prompt"] is None
    assert exact["user_prompt_template"] is None
    assert exact["response_format"] is None
    assert by_id["clarified-joint-v1"]["status"] == "ready"
    assert by_id["split-v1"]["status"] == "ready"


def test_clarified_role_prompt_does_not_confuse_support_with_role() -> None:
    profiles = _load(PROFILES)
    clarified = next(
        profile for profile in profiles["profiles"] if profile["profile_id"] == "clarified-joint-v1"
    )
    system_prompt = clarified["system_prompt"]
    assert "Do not judge factual truth, source support" in system_prompt
    assert "it may still be unsupported or false" in system_prompt
    split = next(profile for profile in profiles["profiles"] if profile["profile_id"] == "split-v1")
    assert "Do not judge atomicity" in split["role"]["system_prompt"]
    assert "Do not judge truth, source support, semantic role" in split["atomicity"]["system_prompt"]


def test_runner_score_fail_closed_metrics() -> None:
    runner = _load_runner()
    case_results = [
        {
            "case_id": "valid",
            "required": True,
            "critical_for_safety": False,
            "gold": {"atomicity": "ATOMIC", "role_boundary": "ROLE_VALID"},
            "repeats": [
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
            ],
        },
        {
            "case_id": "unsafe",
            "required": True,
            "critical_for_safety": True,
            "gold": {"atomicity": "NON_ATOMIC", "role_boundary": "ROLE_VIOLATION"},
            "repeats": [
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
            ],
        },
    ]
    metrics = runner._score(case_results)
    assert metrics["critical_atomicity_false_pass_cases"] == ["unsafe"]
    assert metrics["critical_role_false_pass_cases"] == ["unsafe"]
    assert metrics["gates"]["safety_gate"] is False
    assert metrics["gates"]["candidate_viable"] is False


def test_runner_refuses_unprepared_exact_profile() -> None:
    profiles = _load(PROFILES)
    exact = next(profile for profile in profiles["profiles"] if profile["profile_id"] == "g22-exact-joint")
    assert exact["status"] != "ready"
    source = RUNNER.read_text(encoding="utf-8")
    assert "is not ready" in source
    assert "Import exact evidence before running this profile" in source
