import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "speed_preflight", Path("scripts/run_speed_preflight.py")
)
speed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speed)


def test_speed_budget_is_measurable_but_not_cpc_complete():
    conditions = speed.inputs()
    body = {
        "stats": {"total_output_tokens": 1024, "tokens_per_second": 50},
        "output": [{"type": "message", "content": "Test"}],
    }
    row = speed.response_record(body, 25, conditions[0])
    assert row["status"] == "budget_reached" and row["tokens_per_second"] == 50
    assert row["cpc_valid"] is None
    body["stats"]["total_output_tokens"] = 8192
    row = speed.response_record(body, 170, conditions[2])
    assert row["status"] == "budget_reached" and row["cpc_valid"] is False


def test_speed_keeps_metrics_for_invalid_cpc_and_rejects_reasoning():
    condition = speed.inputs()[2]
    body = {
        "stats": {"total_output_tokens": 20, "tokens_per_second": 50},
        "output": [{"type": "message", "content": "Not JSON"}],
    }
    row = speed.response_record(body, 1, condition)
    assert row["status"] == "contract_failure" and row["cpc_valid"] is False
    assert row["tokens_per_second"] == 50
    body["stats"]["reasoning_output_tokens"] = 10
    assert speed.response_record(body, 1, condition)["status"] == "reasoning_mismatch"


def test_unknown_server_speed_is_not_invented():
    row = speed.response_record(
        {"output": [{"type": "message", "content": "Test"}]}, 1, speed.inputs()[0]
    )
    assert row["tokens_per_second"] is None
    assert row["end_to_end_tokens_per_second"] is None


def test_frozen_inputs_have_expected_lengths_and_cpc_quote_mapping():
    conditions = speed.inputs()
    assert [len(c["input"]) for c in conditions[:2]] == [300, 2000]
    payload = conditions[2]["payload"]
    assert len(payload["evidence"][0]["content"]) == 480
    assert (
        next(iter(payload["quote_choices"].values()))["text"] == payload["evidence"][0]["content"]
    )
