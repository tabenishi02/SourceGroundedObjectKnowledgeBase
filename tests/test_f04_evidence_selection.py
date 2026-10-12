import json
from dataclasses import asdict

import pytest

from sgokb.application import Application
from sgokb.repository import Repository
from sgokb.retrieval import (
    EvidenceBudget,
    EvidenceCandidate,
    EvidencePackageSelector,
    EvidenceSelectionReason,
    estimate_tokens,
)


def _candidate(evidence_id, source_id, content, *, start=0, score=10.0):
    return EvidenceCandidate(
        evidence_id=evidence_id,
        source_id=source_id,
        snapshot_id=f"snapshot:{source_id}",
        run_id=f"run:{source_id}",
        content=content,
        retrieval_score=score,
        reasons=(EvidenceSelectionReason("name", "fixture"),),
        context={
            "metadata": {
                "artifact": "dom/main.html",
                "positions": ["/html[0]/body[0]/main[0]/p[0]"],
                "section": ["Overview"],
                "kinds": ["paragraph"],
                "start": start,
            },
            "locations": [],
            "locators": [],
            "source_label": source_id,
            "snapshot_title": "Fixture",
        },
    )


def _retrieval(*candidates):
    return {
        "object_id": "object:fixture",
        "scope": "effective_snapshot_and_run",
        "candidates": list(candidates),
    }


def _payload_bytes(candidate):
    payload = json.dumps(
        asdict(candidate), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return len(payload.encode("utf-8"))


def _capture(app, make_bundle, *, url, html, size=1000, overlap=100):
    imported = app.import_source_path(make_bundle(url=url, html=html))
    processed = app.process_source_snapshot(imported["snapshot"], size=size, overlap=overlap)
    return imported, processed


def test_application_selection_prioritizes_source_diversity(tmp_path, make_bundle):
    repository = Repository(tmp_path / "f04-diversity.sqlite")
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        source_a, _ = _capture(
            app,
            make_bundle,
            url="https://example.test/a",
            html="<html><main><p>" + ("架空太郎の詳細記録。" * 40) + "</p></main></html>",
            size=100,
            overlap=20,
        )
        source_b, _ = _capture(
            app,
            make_bundle,
            url="https://example.test/b",
            html="<html><main><p>架空太郎について別のSourceが記録している。</p></main></html>",
        )
        repository.source_store.associate_object(source_a["source"], object_id, "confirmed")
        repository.source_store.associate_object(source_b["source"], object_id, "confirmed")

        result = app.select_object_evidence(
            object_id,
            semantic=False,
            max_items=2,
            max_estimated_tokens=100_000,
            max_bytes=1_000_000,
        )
        assert result["selected_count"] == 2
        assert result["usage"]["sources"] == 2
        assert {item["selected_by"] for item in result["selected"]} == {"source_diversity"}
        assert {item["candidate"]["source_id"] for item in result["selected"]} == {
            source_a["source"],
            source_b["source"],
        }
    finally:
        repository.close()


def test_duplicate_suppression_is_package_local_and_reasoned():
    first = _candidate("e1", "s1", "The same grounded statement.", score=30)
    duplicate = _candidate("e2", "s2", "The same grounded statement.", score=20)
    unique = _candidate("e3", "s3", "Independent additional evidence.", score=10)
    result = EvidencePackageSelector(
        EvidenceBudget(max_estimated_tokens=100_000, max_bytes=1_000_000, max_items=10)
    ).select(_retrieval(first, duplicate, unique))

    assert {item.candidate.evidence_id for item in result["selected"]} == {"e1", "e3"}
    omitted = {item.evidence_id: item for item in result["omitted"]}
    assert omitted["e2"].reason == "duplicate"
    assert "e1" in omitted["e2"].detail


def test_protected_manual_selection_is_honored_or_fails_explicitly():
    preferred = _candidate("e1", "s1", "Higher ranked candidate.", score=20)
    protected = _candidate("e2", "s2", "Operator required candidate.", score=1)
    result = EvidencePackageSelector(
        EvidenceBudget(max_estimated_tokens=100_000, max_bytes=1_000_000, max_items=1)
    ).select(_retrieval(preferred, protected), protected_evidence_ids=["e2"])
    assert [item.candidate.evidence_id for item in result["selected"]] == ["e2"]
    assert result["selected"][0].selected_by == "protected"
    assert any(
        item.evidence_id == "e1" and item.reason == "max_items" for item in result["omitted"]
    )

    with pytest.raises(ValueError, match="Protected Evidence exceeds Package budget"):
        EvidencePackageSelector(
            EvidenceBudget(max_estimated_tokens=1, max_bytes=1_000_000, max_items=10)
        ).select(_retrieval(protected), protected_evidence_ids=["e2"])


def test_byte_budget_is_hard_and_truncation_reason_is_recorded():
    first = _candidate("e1", "s1", "compact evidence", score=20)
    second = _candidate("e2", "s2", "another compact evidence", score=10)
    first_bytes = _payload_bytes(first)
    result = EvidencePackageSelector(
        EvidenceBudget(max_estimated_tokens=100_000, max_bytes=first_bytes, max_items=10)
    ).select(_retrieval(first, second))

    assert [item.candidate.evidence_id for item in result["selected"]] == ["e1"]
    assert result["usage"]["bytes"] <= first_bytes
    assert any(
        item.evidence_id == "e2" and item.reason == "byte_budget" for item in result["omitted"]
    )
    assert estimate_tokens("abcd日本") == 3


def test_adjacent_structural_chunks_are_grouped_but_not_silently_merged():
    first = _candidate("e1", "s1", "A" * 1000, start=0, score=20)
    adjacent = _candidate("e2", "s1", "B" * 1000, start=900, score=10)
    result = EvidencePackageSelector(
        EvidenceBudget(max_estimated_tokens=100_000, max_bytes=1_000_000, max_items=10)
    ).select(_retrieval(first, adjacent))

    assert [item.candidate.evidence_id for item in result["selected"]] == ["e1", "e2"]
    assert result["selected"][0].structure_group == result["selected"][1].structure_group
    assert result["selected"][1].related_selected_evidence_ids == ("e1",)
