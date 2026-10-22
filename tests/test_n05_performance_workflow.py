"""Canonical-path tests for the isolated N-05 runner, without real model inference."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from sgokb.domain import EmbeddingSpaceSpec
from sgokb.repository import Repository
from sgokb.retrieval import ExactVectorIndexAdapter

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "n05_workflow", ROOT / "benchmark/tools/n05_performance_workflow.py"
)
WORK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORK)


class UnitProvider:
    def __init__(self):
        self.space = EmbeddingSpaceSpec(
            provider_key="n05-unit",
            provider_version="1",
            model="unit-only",
            model_revision="1",
            dimension=3,
            native_dimension=3,
            preprocessing_key="sgokb-search-representation",
            preprocessing_version="2",
            query_instruction="",
            document_instruction="",
            normalize_embeddings=True,
            max_sequence_length=32768,
            overflow_policy="reject",
            output_dtype="float32",
            provider_configuration="{}",
        )

    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for text in texts]


def target():
    return {
        "source_count": 2,
        "candidate_evidence_count": 8,
        "package_evidence_count": 3,
        "knowledge_statement_count": 9,
    }


def test_fixture_is_fresh_and_canonical_samples_do_not_carry_versions_or_embeddings(tmp_path):
    fixture = tmp_path / "fixture"
    WORK.prepare_fixture(fixture, "unit", target())
    seed_hash = WORK.sha(fixture / "starting.sqlite")
    for number in range(2):
        sample = tmp_path / f"sample-{number}"
        result = WORK.run_sample(
            fixture, sample, f"unit-{number}", UnitProvider, lambda space: ExactVectorIndexAdapter()
        )
        assert result["status"] == "PASS", (
            WORK.read(sample / "execution-error.json") if result["status"] != "PASS" else result
        )
        assert result["actual_workload"] == target()
        assert result["retry_count"] == 0
        assert list(result["segments"]) == list(WORK.SEGMENTS)
        assert result["total_seconds"] == sum(result["segments"].values())
        assert all(event["end_ns"] >= event["start_ns"] for event in result["segment_events"])
        assert WORK.read(sample / "result-validation.json")["is_valid"] is True
        assert WORK.read(sample / "diff-review.json")["blocked"] is False
        assert (
            WORK.read(sample / "derived-incremental-sync.json")["vector_index"][
                "written_point_count"
            ]
            == 13
        )
        assert WORK.read(sample / "render.json")["byte_count"] > 0
        repo = Repository(sample / "sgokb.sqlite")
        try:
            assert repo.one("SELECT count(*) AS n FROM object_versions")["n"] == 1
            assert repo.one("SELECT count(*) AS n FROM knowledge_statements")["n"] == 9
        finally:
            repo.close()
    assert WORK.sha(fixture / "starting.sqlite") == seed_hash


def test_prebuilt_result_statements_are_exact_explicit_readings_from_selected_evidence(tmp_path):
    fixture = tmp_path / "fixture"
    WORK.prepare_fixture(fixture, "unit", target())
    sample = tmp_path / "sample"
    result = WORK.run_sample(
        fixture, sample, "unit", UnitProvider, lambda space: ExactVectorIndexAdapter()
    )
    assert result["status"] == "PASS"
    payload = WORK.read(sample / "external-result/result.json")
    statements = payload["knowledge"]["summary"] + [
        s for f in payload["knowledge"]["facets"] for s in f["statements"]
    ]
    facts = WORK.read(fixture / "evidence-facts.json")
    assert len(statements) == 9
    assert len({s["local_key"] for s in statements}) == 9
    for statement in statements:
        assert statement["text"] in facts[statement["evidence"][0]["evidence_id"]]
    assert payload["generation"]["generator_kind"] == "tool"


def test_failed_workflow_keeps_evidence_and_does_not_invent_unexecuted_timings(tmp_path):
    fixture = tmp_path / "fixture"
    WORK.prepare_fixture(fixture, "unit", target())
    sample = tmp_path / "failed"

    def unavailable():
        raise RuntimeError("unit runtime unavailable")

    result = WORK.run_sample(
        fixture, sample, "failed", unavailable, lambda space: ExactVectorIndexAdapter()
    )
    assert result["status"] == "FAIL"
    assert result["retry_count"] == 0
    assert "derived_incremental_sync" in result["segments"]
    assert "render" not in result["segments"]
    assert WORK.read(sample / "execution-error.json")["unexecuted_segments"] == ["render"]
    assert WORK.read(sample / "sample.json")["status"] == "FAIL"
    with pytest.raises(FileExistsError):
        WORK.run_sample(
            fixture, sample, "failed", UnitProvider, lambda space: ExactVectorIndexAdapter()
        )


def test_segment_clock_retains_failed_attempt_wall_time_without_retry_or_replacement():
    clock = WORK.SegmentClock()

    def fail():
        raise ValueError("unit failure")

    with pytest.raises(ValueError):
        clock.measure("package_build", fail)
    assert clock.events[0]["status"] == "FAIL"
    assert clock.seconds["package_build"] >= 0
    with pytest.raises(ValueError, match="repeated"):
        clock.measure("package_build", lambda: None)


def test_native_qdrant_namespaces_are_short_stable_and_sample_specific(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "benchmark/tools"))
    runner_spec = importlib.util.spec_from_file_location(
        "n05_runner", ROOT / "benchmark/tools/n05_run_performance.py"
    )
    runner = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(runner)
    names = [
        runner.sample_prefix("run-a", f"{profile}-{condition}-{number:02d}")
        for profile in ("standard", "large")
        for condition, count in (("cold", 3), ("warm", 20))
        for number in range(1, count + 1)
    ]
    assert len(names) == len(set(names)) == 46
    assert all(len(name) == 15 for name in names)
    assert names[0] == runner.sample_prefix("run-a", "standard-cold-01")
    assert names[0] != runner.sample_prefix("run-b", "standard-cold-01")
