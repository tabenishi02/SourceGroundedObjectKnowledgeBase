import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "benchmark" / "tools" / "n05_evaluate_performance.py"
CONTRACT_PATH = ROOT / "benchmark" / "n05-performance-contract-v1.json"

spec = importlib.util.spec_from_file_location("n05_evaluate_performance", TOOL_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _environment():
    return {
        "git_head": "a" * 40,
        "os": "Windows 11",
        "cpu": "Reference CPU",
        "ram_gib": 128,
        "gpu": "Reference GPU",
        "python": "3.10.6",
        "embedding_model": "example/model",
        "embedding_revision": "example-revision",
        "qdrant_version": "1.x",
        "qdrant_transport": "grpc",
        "collection_prefix": "sgokb_n05_test",
        "model_cache_mode": "local-only-warm",
    }


def _sample(sample_id, total, status="PASS", retry_count=0):
    segment = total / 8
    return {
        "sample_id": sample_id,
        "status": status,
        "total_seconds": total,
        "retry_count": retry_count,
        "segments": {
            "package_build": segment,
            "package_stage": segment,
            "package_preflight": segment,
            "result_validation": segment,
            "diff_review": segment,
            "result_import": segment,
            "derived_incremental_sync": segment,
            "render": segment,
        },
    }


def _profile(name, total):
    target = _contract()["profiles"][name]["reference_fixture_target"]
    return {
        "workload": dict(target),
        "cold_samples": [_sample(f"{name}-cold-{i}", total * 1.2) for i in range(3)],
        "warm_samples": [_sample(f"{name}-warm-{i}", total + i) for i in range(20)],
    }


def _evidence(standard_total=100, large_total=200):
    return {
        "schema_version": "sgokb.n05.performance-evidence.v1",
        "run_id": "test-run",
        "environment": _environment(),
        "profiles": {
            "standard": _profile("standard", standard_total),
            "large": _profile("large", large_total),
        },
    }


def test_nearest_rank_uses_one_based_ceiling():
    assert module.nearest_rank(list(range(1, 21)), 0.95) == 19
    assert module.nearest_rank(list(range(1, 21)), 0.50) == 10


def test_valid_profiles_pass():
    result = module.evaluate(_contract(), _evidence())
    assert result["overall"] == "PASS"
    assert result["profiles"]["standard"]["statistics"]["p95_seconds"] == 118
    assert result["profiles"]["large"]["statistics"]["p95_seconds"] == 218


def test_p95_above_target_fails():
    result = module.evaluate(_contract(), _evidence(standard_total=590))
    assert result["overall"] == "FAIL"
    assert result["profiles"]["standard"]["status"] == "FAIL"
    assert "exceeds target" in result["profiles"]["standard"]["reason"]


def test_formal_warm_failure_cannot_be_hidden_by_successes():
    evidence = _evidence()
    evidence["profiles"]["standard"]["warm_samples"][3] = _sample(
        "standard-warm-3", 10, status="FAIL", retry_count=1
    )
    result = module.evaluate(_contract(), evidence)
    assert result["overall"] == "FAIL"
    assert result["profiles"]["standard"]["statistics"]["warm_failure_count"] == 1
    assert result["profiles"]["standard"]["statistics"]["retry_count_total"] == 1


def test_insufficient_samples_are_blocked():
    evidence = _evidence()
    evidence["profiles"]["standard"]["warm_samples"] = evidence["profiles"]["standard"][
        "warm_samples"
    ][:19]
    result = module.evaluate(_contract(), evidence)
    assert result["overall"] == "BLOCKED"
    assert result["profiles"]["standard"]["status"] == "BLOCKED"


def test_out_of_envelope_workload_is_blocked():
    evidence = _evidence()
    evidence["profiles"]["large"]["workload"]["source_count"] = 19
    result = module.evaluate(_contract(), evidence)
    assert result["overall"] == "BLOCKED"
    assert result["profiles"]["large"]["status"] == "BLOCKED"


def test_missing_environment_metadata_is_blocked():
    evidence = _evidence()
    del evidence["environment"]["embedding_revision"]
    result = module.evaluate(_contract(), evidence)
    assert result["overall"] == "BLOCKED"
    assert "environment.embedding_revision is missing" in result["issues"]
