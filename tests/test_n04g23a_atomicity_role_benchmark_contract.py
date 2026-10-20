from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

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
    assert exact["status"] == "ready"
    assert exact["system_prompt"]
    assert exact["user_prompt_template"]
    assert exact["response_format"]["json_schema"]["strict"] is True
    provenance = exact["exact_profile_provenance"]
    assert provenance["source_g22_run_id"] == "20261020T030904+0900"
    assert provenance["verified_render_count"] == 19
    assert provenance["mismatch_count"] == 0
    assert len(provenance["verified_requests"]) == provenance["verified_render_count"]
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
    assert (
        "Do not judge truth, source support, semantic role" in split["atomicity"]["system_prompt"]
    )


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


def test_runner_refuses_unprepared_exact_profile(tmp_path, monkeypatch) -> None:
    profiles = _load(PROFILES)
    exact = profiles["profiles"][0]
    exact["status"] = "requires_exact_local_evidence_import"
    unprepared = tmp_path / "profiles.json"
    unprepared.write_text(json.dumps(profiles), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            str(RUNNER),
            "--corpus",
            str(CORPUS),
            "--profiles",
            str(unprepared),
            "--profile-id",
            "g22-exact-joint",
            "--output",
            str(tmp_path / "result.json"),
        ],
    )
    with pytest.raises(RuntimeError, match="Import exact evidence before running this profile"):
        _load_runner().main()
    assert not (tmp_path / "result.json").exists()


def test_final_corpus_covers_every_g22_unit_and_excludes_ambiguous_required_gold() -> None:
    final = _load(ROOT / "benchmark" / "n04g23a-atomicity-role-gold-v1.json")
    assert final["status"] == "frozen_for_execution"
    assert final["source_g22_run_id"] == "20261020T030904+0900"
    assert len(final["cases"]) == 47
    imported = [c for c in final["cases"] if c["origin"] == "g22_exact"]
    assert len(imported) == 27
    assert len({c["case_id"] for c in final["cases"]}) == 47
    counts = {}
    for case in imported:
        key = (case["g22_case_id"], case["g22_attempt"])
        counts[key] = counts.get(key, 0) + 1
    assert sorted(counts.values()) == [3, 3, 5, 5, 5, 6]
    for case in final["cases"]:
        if case["required"]:
            assert case["gold_confidence"] == "high"
            assert "INDETERMINATE" not in case["gold"].values()
    assert final["cases"][:20] == [{**c, "gold_confidence": "high"} for c in _load(CORPUS)["cases"]]


def test_exact_template_preserves_json_quoting_and_unicode() -> None:
    runner = _load_runner()
    exact = _load(PROFILES)["profiles"][0]
    case = {
        "text": '日本語 "quoted"\nline',
        "semantic_role": "source_fact",
        "purpose": "comparison",
        "presentation_role": "main",
    }
    rendered = runner._substitute(exact["user_prompt_template"], case)
    assert rendered == json.dumps(case, ensure_ascii=False, sort_keys=True)
    assert json.loads(rendered) == case
