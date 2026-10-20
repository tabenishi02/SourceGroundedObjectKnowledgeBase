from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "benchmark" / "tools" / "n04g23ar_preflight.py"
SELECTOR = ROOT / "benchmark" / "tools" / "n04g23ar_compare_candidates.py"
MANIFEST = ROOT / "benchmark" / "n04g23ar-judge-candidates-v1.json"
PARAPHRASE = ROOT / "benchmark" / "n04g23ar-split-paraphrase-profile-v1.json"
G23A_PROFILES = ROOT / "benchmark" / "n04g23a-atomicity-role-prompt-profiles-v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_g23ar_preflight_passes_against_tracked_inputs() -> None:
    payload = _load_module("n04g23ar_preflight", PREFLIGHT).run(ROOT)
    assert payload["status"] == "PASS"
    assert payload["case_count"] == 47
    assert payload["required_count"] == 41
    assert payload["optional_count"] == 6
    assert payload["primary_profile"] == "split-v1"
    assert payload["secondary_profile"] == "split-paraphrase-a"


def test_candidate_pool_is_fixed_and_cross_family() -> None:
    manifest = _load(MANIFEST)
    candidates = manifest["candidates"]
    assert [candidate["candidate_id"] for candidate in candidates] == [
        "qwen35-9b-q6k",
        "ministral3-8b-q6k",
        "gemma4-12b-q6k",
        "mistral32-24b-q4km",
    ]
    assert len({candidate["family"] for candidate in candidates}) == 4
    assert all(candidate["lm_studio_alias"] for candidate in candidates)
    assert all(candidate["required_quantization"] in {"Q6_K", "Q4_K_M"} for candidate in candidates)


def test_primary_gate_cannot_relax_fail_closed_counts() -> None:
    manifest = _load(MANIFEST)
    primary = manifest["primary_gate"]
    for key in (
        "critical_atomicity_false_pass_cases",
        "critical_role_false_pass_cases",
        "required_atomicity_false_reject_cases",
        "required_role_false_reject_cases",
        "required_repeatability_failure_cases",
    ):
        assert primary[key] == 0
    assert "INDETERMINATE" in primary["rule"]
    assert "false reject" in primary["rule"]


def test_secondary_gate_requires_exact_required_stability() -> None:
    manifest = _load(MANIFEST)
    secondary = manifest["secondary_gate"]
    assert secondary["applies_to"] == "primary-gate pass candidates only"
    assert secondary["same_safety_and_required_valid_gates"] is True
    assert secondary["required_exact_vs_paraphrase_atomicity_agreement"].startswith("100%")
    assert secondary["required_exact_vs_paraphrase_role_agreement"].startswith("100%")
    assert secondary["required_exact_vs_paraphrase_joint_agreement"].startswith("100%")
    assert secondary["required_repeatability_failure_cases"] == 0


def test_paraphrase_profile_is_pre_registered_split_and_semantically_separate() -> None:
    paraphrase = _load(PARAPHRASE)
    g23a = _load(G23A_PROFILES)
    para = paraphrase["profiles"][0]
    split = next(profile for profile in g23a["profiles"] if profile["profile_id"] == "split-v1")
    assert paraphrase["status"] == "frozen_for_execution"
    assert para["profile_id"] == "split-paraphrase-a"
    assert para["mode"] == "split"
    assert para["atomicity"]["system_prompt"] != split["atomicity"]["system_prompt"]
    assert para["role"]["system_prompt"] != split["role"]["system_prompt"]
    assert (
        para["atomicity"]["response_format"]["json_schema"]["schema"]["properties"]
        ["atomicity_verdict"]["enum"]
        == split["atomicity"]["response_format"]["json_schema"]["schema"]["properties"]
        ["atomicity_verdict"]["enum"]
    )
    assert (
        para["role"]["response_format"]["json_schema"]["schema"]["properties"]
        ["role_boundary_verdict"]["enum"]
        == split["role"]["response_format"]["json_schema"]["schema"]["properties"]
        ["role_boundary_verdict"]["enum"]
    )


def test_selector_gate_pass_requires_every_failure_list_empty() -> None:
    selector = _load_module("n04g23ar_selector", SELECTOR)
    base = {
        "metrics": {
            "critical_atomicity_false_pass_cases": [],
            "critical_role_false_pass_cases": [],
            "required_atomicity_false_reject_cases": [],
            "required_role_false_reject_cases": [],
            "required_repeatability_failure_cases": [],
        }
    }
    assert selector._gate_pass(base) is True
    for key in tuple(base["metrics"]):
        failed = json.loads(json.dumps(base))
        failed["metrics"][key] = ["x"]
        assert selector._gate_pass(failed) is False


def test_selector_requires_123_of_123_required_prompt_stability() -> None:
    selector = _load_module("n04g23ar_selector_stability", SELECTOR)
    primary_cases = []
    secondary_cases = []
    for index in range(41):
        repeats = [
            {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"}
            for _ in range(3)
        ]
        primary_cases.append({"case_id": f"c{index}", "required": True, "repeats": repeats})
        secondary_cases.append(
            {"case_id": f"c{index}", "required": True, "repeats": json.loads(json.dumps(repeats))}
        )
    stability = selector._required_agreement(
        {"cases": primary_cases}, {"cases": secondary_cases}
    )
    assert stability["total_required_repeat_pairs"] == 123
    assert stability["atomicity_identical"] == 123
    assert stability["role_identical"] == 123
    assert stability["joint_identical"] == 123
    assert stability["pass"] is True
    secondary_cases[0]["repeats"][0]["role_boundary_verdict"] = "INDETERMINATE"
    stability = selector._required_agreement(
        {"cases": primary_cases}, {"cases": secondary_cases}
    )
    assert stability["joint_identical"] == 122
    assert stability["pass"] is False


def test_preflight_exposes_no_semantic_override_cli() -> None:
    source = PREFLIGHT.read_text(encoding="utf-8")
    for forbidden in (
        "--corpus",
        "--profiles",
        "--profile-id",
        "--candidate",
        "--model",
        "--threshold",
        "--repeats",
    ):
        assert forbidden not in source
