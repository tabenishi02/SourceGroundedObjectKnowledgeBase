import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "comparison", Path(__file__).parents[1] / "scripts/run_efficiency_capture_comparison.py"
)
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def row(job, statement="a"):
    return {
        "facet": "person",
        "content": statement,
        "metadata": {
            "subject": "person",
            "ai_run": "random",
            "extraction_job": job,
            "context_id": "context",
            "evidence_ids": ["evidence"],
        },
    }


def test_signatures_ignore_run_ids_but_keep_claim_context_and_multiplicity():
    assert comparison.fragment_signatures([row("old")]) == comparison.fragment_signatures(
        [row("new")]
    )
    counts = comparison.fragment_signatures([row("old"), row("old")])
    assert list(counts.values()) == [2]
    changed = row("new")
    changed["metadata"]["subject"] = "different"
    assert comparison.fragment_signatures([changed]) != comparison.fragment_signatures([row("old")])


def test_comparison_includes_duplicate_changes_and_usage(tmp_path):
    for name, seconds, rows in (
        ("before", 10, [row("old"), row("old")]),
        ("after", 8, [row("new"), row("new", "b")]),
    ):
        directory = tmp_path / name
        directory.mkdir()
        comparison.write(
            directory / "case-result.json",
            {
                "result": {"status": "complete"},
                "seconds": seconds,
                "usage": {"completion_tokens": 100},
                "raw_unchanged": True,
                "integrity": "ok",
                "foreign_key_errors": 0,
            },
        )
        comparison.write(directory / "case-fragments.json", rows)
    comparison.compare(tmp_path, {"cases": [{"id": "case"}]})
    result = json.loads((tmp_path / "comparison.json").read_text())
    case = result["cases"][0]
    assert case["time_reduction_percent"] == pytest.approx(20) and case["exact_common"] == 1
    assert case["removed_or_changed"] == 1 and case["added_or_changed"] == 1
    differences = comparison.read(tmp_path / "case-content-diff.json")
    assert differences["multiplicity_changes"][0]["before"] == 2


def test_failed_integrity_does_not_count_as_completed():
    report = {
        "result": {"status": "complete"},
        "raw_unchanged": True,
        "integrity": "ok",
        "foreign_key_errors": 0,
    }
    assert comparison.accepted(report)
    report["raw_unchanged"] = False
    assert not comparison.accepted(report)
