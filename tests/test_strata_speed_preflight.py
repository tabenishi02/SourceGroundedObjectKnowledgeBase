import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
spec = importlib.util.spec_from_file_location(
    "strata_speed", Path("scripts/run_strata_speed_preflight.py")
)
speed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speed)


def response(content, finish="stop", tokens=20):
    return {
        "usage": {"prompt_tokens": 100, "completion_tokens": tokens},
        "timings": {"predicted_per_second": 50, "prompt_ms": 900},
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
    }


def test_same_speed_inputs_without_added_server_schema():
    for condition in speed.inputs():
        body = speed.request_body(condition)
        assert body["messages"][1]["content"] == condition["input"]
        assert body["messages"][0]["content"] == condition["prompt"]
        assert body["max_tokens"] == condition["budget"]
        assert "response_format" not in body


def test_decode_speed_is_separate_from_total_and_unknown_ttft():
    row = speed.measure(response("a" * 100), 10, speed.inputs()[0])
    assert row["tokens_per_second"] == 50
    assert row["end_to_end_tokens_per_second"] == 2
    assert row["characters_per_second"] == 10
    assert row["ttft_seconds"] is None
    assert row["reasoning_tokens"] is None


def test_budget_is_measurable_but_not_cpc_success():
    row = speed.measure(response("{}", "length", 8192), 10, speed.inputs()[2])
    assert row["status"] == "budget_reached" and row["cpc_valid"] is False
    assert row["tokens_per_second"] == 50


def test_cpc_contract_validation_is_retained():
    condition = speed.inputs()[2]
    result = {
        "assessments": [{"evidence_id": "speed-evidence-01", "discard_reason": "unrelated"}],
        "fragments": [],
        "entity_candidates": [],
    }
    assert speed.measure(response(json.dumps(result)), 10, condition)["cpc_valid"] is True
    result["assessments"][0]["evidence_id"] = "unknown"
    row = speed.measure(response(json.dumps(result)), 10, condition)
    assert row["status"] == "contract_failure" and row["cpc_valid"] is False
