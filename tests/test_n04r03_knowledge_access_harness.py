from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "benchmark" / "tools" / "n04r03_harness_preflight.py"
CASES = ROOT / "benchmark" / "n04-knowledge-access-cases-v1.json"
HARNESS = ROOT / "benchmark" / "n04-knowledge-access-formal-harness-v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location("n04r03_harness_preflight", PREFLIGHT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_n04r03_preflight_passes() -> None:
    module = _load_preflight_module()
    report = module.evaluate(ROOT)
    assert report["preflight"] == "PASS", report["failed_checks"]


def test_n04r03_three_cases_stop_at_consumer_boundary() -> None:
    cases = _load(CASES)
    assert cases["formal_boundary"] == "external_consumer_boundary"
    assert [item["case_id"] for item in cases["cases"]] == [
        "n04-roleplay-saber",
        "n04-similar-work-comparison",
        "n04-concept-combination-creative",
    ]
    assert [
        (item.get("build_context") or item.get("build_context_template"))["purpose"]
        for item in cases["cases"]
    ] == ["roleplay", "comparison", "creative"]
    assert all("generation" not in item for item in cases["cases"])


def test_n04r03_comparison_candidate_must_come_from_similarity() -> None:
    comparison = _load(CASES)["cases"][1]
    assert comparison["tool_sequence"] == ["find_similar_objects", "build_context"]
    assert comparison["build_context_template"]["object_ids"] == [
        "d5824d33-7008-4121-9cfe-1f95a19667fd",
        "<retrieved_current_work_candidate_id>",
    ]
    assert comparison["expected_dataset_candidate_id_observation_only"] == (
        "57db855c-574a-4b38-b474-421c165894f1"
    )


def test_n04r03_only_sgokb_responsibility_gates_are_formal() -> None:
    harness = _load(HARNESS)
    assert set(harness["case_gates"]) == {
        "public_boundary",
        "canonical_scope",
        "retrieval_integration",
        "context_contract",
        "traceability",
        "budget_contract",
    }
    assert set(harness["global_gates"]) == {
        "canonical_invariance",
        "integrity",
        "regression",
    }
    assert harness["formal_boundary"]["consumer_inference_or_generation_is_gating"] is False
    assert harness["result_policy"]["allowed_states"] == ["PASS", "FAIL", "BLOCKED"]


def test_n04r03_reference_consumer_is_explicitly_non_gating() -> None:
    harness = _load(HARNESS)
    assert harness["non_gating"]["reference_consumer_demonstration"] is True
    assert harness["non_gating"]["consumer_output_quality"] is True
    assert harness["non_gating"]["consumer_grounding"] is True
    assert harness["evidence_contract"][
        "consumer_demonstration_must_not_affect_formal_verdict"
    ] is True


def test_n04r03_old_harnesses_are_historical_only() -> None:
    harness = _load(HARNESS)
    assert harness["historical_harnesses_are_current_authority"] is False
    assert harness["historical_harnesses"] == [
        "benchmark/n04-v2-formal-harness-v1.json",
        "benchmark/n04-v3-formal-harness-v1.json",
    ]


def test_n04r03_preflight_has_no_grounded_generation_dependency() -> None:
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert "sgokb.grounding" not in source
    assert "generation_output_schema_hash" not in source
    assert "MiniCheck" not in source
    assert "Phi-4" not in source
    assert "Mistral" not in source
