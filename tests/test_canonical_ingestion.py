import json

import pytest

from sgokb.application import Application
from sgokb.repository import Repository


def _app(tmp_path):
    repository = Repository(tmp_path / "canonical-ingestion.sqlite")
    return Application(repository), repository


def _document(url, *, canonical_url=None):
    return {
        "url": url,
        "canonical_url": canonical_url,
        "title": "Test Subject",
        "language": "ja",
        "content_type": "text/html",
    }


def test_canonical_capture_to_evidence_preserves_full_provenance(tmp_path, make_bundle):
    app, repository = _app(tmp_path)
    try:
        url = "https://example.test/hero"
        canonical_url = "https://example.test/canonical-hero"
        warning = {"code": "FRAME_PARTIAL", "component": "frames"}
        path = make_bundle(
            url=url,
            warnings=[warning],
            extra={
                "metadata/document.json": json.dumps(
                    _document(url, canonical_url=canonical_url), ensure_ascii=False
                ).encode()
            },
        )

        imported = app.import_source_path(path)
        source_id, snapshot_id = imported["source"], imported["snapshot"]
        assert imported["duplicate"] is False
        assert imported["effective"] is True
        assert imported["raw_artifacts"] == 9
        assert repository.one("SELECT name FROM sqlite_master WHERE name='sources'") is None
        assert repository.one("SELECT name FROM sqlite_master WHERE name='snapshots'") is None

        locators = {(item.kind, item.value) for item in repository.source_store.locators(source_id)}
        assert locators == {("url", url), ("canonical_url", canonical_url)}
        snapshot = repository.source_store.snapshot_by_id(snapshot_id)
        assert snapshot.snapshot_id == path.stem.split("_")[-1].replace(".webcapture", "")
        assert snapshot.completeness.value == "partial"
        stored_snapshot = repository.one(
            "SELECT * FROM source_snapshots WHERE id=?", (snapshot_id,)
        )
        assert json.loads(stored_snapshot["warnings_json"]) == [warning]
        assert repository.source_store.snapshot_metadata(snapshot_id)["bundle_sha256"]

        artifacts = repository.source_store.raw_artifacts(snapshot_id)
        assert {item["logical_path"] for item in artifacts} == {
            "manifest.json",
            "dom/main.html",
            "metadata/document.json",
            "metadata/html-metadata.json",
            "metadata/structured-data.json",
            "metadata/frames.json",
            "metadata/shadow-dom.json",
            "metadata/resources.json",
            "checksums.json",
        }
        for item in artifacts:
            assert item["sha256"]
            assert item["bytes"] >= 0
            assert item["storage_ref"] == str(path.resolve())

        result = app.process_source_snapshot(snapshot_id)
        assert result["effective"] is True
        assert result["evidence"] > 0
        assert repository.one("SELECT name FROM sqlite_master WHERE name='normalized_runs'") is None
        assert repository.one("SELECT name FROM sqlite_master WHERE name='evidence'") is None

        provenance = repository.source_store.evidence_provenance(result["evidence_ids"][0])
        assert provenance.source.source_id == source_id
        assert provenance.snapshot.snapshot_id == snapshot_id
        assert provenance.evidence.run_id == result["run"]
        input_paths = {
            repository.one("SELECT logical_path FROM raw_artifacts WHERE id=?", (artifact_id,))[
                "logical_path"
            ]
            for artifact_id in provenance.raw_artifact_ids
        }
        assert input_paths == {"dom/main.html"}

        location_kinds = {
            row["kind"]
            for row in repository.rows(
                "SELECT kind FROM evidence_locations WHERE evidence_id=?",
                (result["evidence_ids"][0],),
            )
        }
        assert "dom_path" in location_kinds
        assert "block_order" in location_kinds

        classifications = repository.rows(
            "SELECT axis,value,origin_kind FROM source_classifications "
            "WHERE source_id=? ORDER BY axis,value",
            (source_id,),
        )
        assert {(item["axis"], item["value"], item["origin_kind"]) for item in classifications} >= {
            ("resource_type", "web_page", "deterministic"),
            ("site", "example.test", "deterministic"),
            ("document_genre", "generic_web", "deterministic"),
            ("media_type", "text/html", "captured"),
        }
        metadata = repository.rows(
            "SELECT key,origin_kind FROM source_metadata_values WHERE source_id=?",
            (source_id,),
        )
        assert ("canonical_url", "captured") in {
            (item["key"], item["origin_kind"]) for item in metadata
        }
        assert ("page_summary", "deterministic") in {
            (item["key"], item["origin_kind"]) for item in metadata
        }
    finally:
        repository.close()


def test_capture_retry_is_idempotent_and_changed_raw_is_rejected(tmp_path, make_bundle):
    app, repository = _app(tmp_path)
    try:
        path = make_bundle()
        first = app.import_source_path(path)
        second = app.import_source_path(path)
        assert second == {
            "source": first["source"],
            "snapshot": first["snapshot"],
            "duplicate": True,
            "effective": True,
        }
        assert repository.one("SELECT count(*) n FROM source_snapshots")["n"] == 1
        assert repository.one("SELECT count(*) n FROM raw_artifacts")["n"] == 9

        make_bundle(
            capture_id=first["snapshot"],
            html="<html><main><p>changed raw content</p></main></html>",
        )
        with pytest.raises(ValueError, match="different raw bytes"):
            app.import_source_path(path)
    finally:
        repository.close()


def test_locator_resolution_rejects_ambiguity_but_explicit_source_wins(tmp_path, make_bundle):
    app, repository = _app(tmp_path)
    try:
        url = "https://example.test/shared"
        first = repository.source_store.create_source("First")
        second = repository.source_store.create_source("Second")
        repository.source_store.add_locator(first, "url", url)
        repository.source_store.add_locator(second, "url", url)
        path = make_bundle(url=url)

        with pytest.raises(ValueError, match="Ambiguous Source resolution"):
            app.import_source_path(path)
        imported = app.import_source_path(path, source_id=first)
        assert imported["source"] == first
        assert repository.source_store.snapshot_by_id(imported["snapshot"]).source_id == first
    finally:
        repository.close()


def test_effective_snapshot_and_run_require_explicit_replacement(tmp_path, make_bundle):
    app, repository = _app(tmp_path)
    try:
        url = "https://example.test/history"
        first_path = make_bundle(url=url, timestamp="2026-01-01T00:00:00.000Z")
        second_path = make_bundle(url=url, timestamp="2026-01-02T00:00:00.000Z")
        first = app.import_source_path(first_path)
        second = app.import_source_path(second_path)
        assert first["source"] == second["source"]
        assert first["effective"] is True
        assert second["effective"] is False
        assert (
            repository.source_store.effective_snapshot(first["source"]).snapshot_id
            == first["snapshot"]
        )

        first_run = app.process_source_snapshot(first["snapshot"])
        replacement_run = app.process_source_snapshot(first["snapshot"])
        assert first_run["effective"] is True
        assert replacement_run["effective"] is False
        assert repository.source_store.effective_run(first["snapshot"])["id"] == first_run["run"]

        with pytest.raises(ValueError, match="Invalid chunk size"):
            app.process_source_snapshot(first["snapshot"], size=10)
        statuses = [
            row["status"]
            for row in repository.rows(
                "SELECT status FROM normalization_runs WHERE snapshot_id=? ORDER BY rowid",
                (first["snapshot"],),
            )
        ]
        assert statuses == ["complete", "complete", "failed"]
        assert repository.source_store.effective_run(first["snapshot"])["id"] == first_run["run"]

        second_run = app.process_source_snapshot(second["snapshot"])
        assert second_run["effective"] is False
        repository.source_store.select_effective_snapshot(
            first["source"], second["snapshot"], reason="operator_reviewed_new_capture"
        )
        repository.source_store.select_effective_run(
            second["snapshot"], second_run["run"], reason="operator_reviewed_normalization"
        )
        assert (
            repository.source_store.effective_snapshot(first["source"]).snapshot_id
            == second["snapshot"]
        )
        assert repository.source_store.effective_run(second["snapshot"])["id"] == second_run["run"]
        assert repository.one("SELECT count(*) n FROM source_snapshots")["n"] == 2
        assert repository.one("SELECT count(*) n FROM normalization_runs")["n"] == 4
        assert (
            repository.one("SELECT count(*) n FROM evidence_records")["n"] > first_run["evidence"]
        )
    finally:
        repository.close()
