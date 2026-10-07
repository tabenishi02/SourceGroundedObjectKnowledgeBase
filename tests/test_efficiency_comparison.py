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


def test_control_reuse_requires_matching_conditions(tmp_path, monkeypatch):
    import io
    import sqlite3
    import zipfile

    root = tmp_path / "repo"
    (root / "benchmark").mkdir(parents=True)
    raw = root / "capture.zip"
    raw.write_bytes(b"synthetic capture")
    source = root / "source.sqlite"
    db = sqlite3.connect(source)
    db.execute("CREATE TABLE snapshots(id TEXT,raw_path TEXT,active_run TEXT)")
    db.execute("INSERT INTO snapshots VALUES(?,?,?)", ("snapshot", str(raw), "normalized"))
    db.commit()
    db.close()
    case = {
        "id": "fragment-01",
        "task": "fragment",
        "snapshot_id": "snapshot",
        "entity_id": "entity",
        "raw_sha256": comparison.checksum(raw),
    }
    comparison.write(
        root / "benchmark/sample-v1.json",
        {
            "cases": [case],
            "fragment_batch_size": 1,
        },
    )
    old = tmp_path / "old"
    (old / "before").mkdir(parents=True)
    prior = sqlite3.connect(old / "before/captures.sqlite")
    prior.execute("CREATE TABLE marker(value TEXT)")
    prior.execute("INSERT INTO marker VALUES('preserved control')")
    prior.commit()
    prior.close()
    comparison.write(old / "before/fragment-01-result.json", {"saved": True})
    comparison.write(
        old / "plan.json",
        {
            "before": comparison.BEFORE,
            "runtime": {"model": "test"},
            "batch_size": 1,
            "output_tokens": 8192,
            "cases": [{**case, "normalized_run": "normalized"}],
        },
    )
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("src/cpc/test.txt", "source")
    monkeypatch.setattr(comparison, "ROOT", root)
    monkeypatch.setattr(comparison, "runtime", lambda: {"model": "test"})
    monkeypatch.setattr(comparison.subprocess, "check_output", lambda *a, **k: archive.getvalue())
    out = tmp_path / "new"
    comparison.prepare(source, out, "fixed-commit", old)
    assert comparison.read(out / "plan.json")["after"] == "fixed-commit"
    check = sqlite3.connect(out / "before/captures.sqlite")
    assert check.execute("SELECT value FROM marker").fetchone()[0] == "preserved control"
    check.close()
    assert comparison.read(out / "before/fragment-01-result.json")["saved"]
    monkeypatch.setattr(comparison, "runtime", lambda: {"model": "different"})
    with pytest.raises(ValueError, match="control conditions differ"):
        comparison.prepare(source, tmp_path / "rejected", "fixed-commit", old)
