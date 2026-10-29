import hashlib
import json
from pathlib import Path

import pytest

from sgokb.application_exchange import PackageExchangeApplication, ResultExchangeApplication
from sgokb.application_version import VersionReadApplication
from sgokb.exchange.package_manifest_v2 import validate_package_manifest_v2
from sgokb.repository import Repository


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _setup(repository, tmp_path, *, two_evidence=False):
    object_id = repository.object_store.create_object(
        "Alice Raw",
        "class:character",
        object_id="object-praw05-alice",
    )
    source_id = repository.source_store.create_source(
        "Alice Raw source",
        source_id="source-praw05-alice",
    )
    locator = repository.source_store.ensure_locator(
        source_id,
        "url",
        "https://example.test/alice-raw",
    )
    snapshot_id = "snapshot-praw05-alice"
    repository.source_store.create_snapshot(
        source_id,
        "2026-10-29T16:00:00Z",
        "test_fixture",
        observed_locator_id=locator,
        title="Alice Raw source",
        snapshot_id=snapshot_id,
    )
    raw = b"<html><body>Alice Raw is a fictional character.</body></html>"
    raw_path = tmp_path / "alice-raw.html"
    raw_path.write_bytes(raw)
    artifact_id = repository.source_store.add_raw_artifact(
        snapshot_id,
        "rendered_dom",
        str(raw_path),
        _sha256(raw),
        len(raw),
        media_type="text/html",
        artifact_id="raw-praw05-alice",
    )
    run_id = "run-praw05-alice"
    repository.source_store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        [artifact_id],
        run_id=run_id,
    )
    evidence_ids = []
    for index in range(2 if two_evidence else 1):
        evidence_id = f"evidence-praw05-alice-{index + 1}"
        repository.source_store.add_evidence(
            run_id,
            f"Alice Raw fixture Evidence {index + 1}.",
            "normalized",
            evidence_id=evidence_id,
        )
        evidence_ids.append(evidence_id)
    repository.source_store.select_effective_snapshot(
        source_id,
        snapshot_id,
        reason="P-RAW-05 fixture",
    )
    repository.source_store.select_effective_run(
        snapshot_id,
        run_id,
        reason="P-RAW-05 fixture",
    )
    repository.source_store.associate_object(
        source_id,
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    return object_id, source_id, artifact_id, tuple(evidence_ids), raw


def _build_stage_export(repository, tmp_path, object_id, *, include_evidence=()):
    packages = PackageExchangeApplication(repository)
    built = packages.build(
        object_id,
        package_version="v2",
        build_root=tmp_path / "build",
        include_evidence=include_evidence,
    )
    manifest = json.loads(Path(built.path, "manifest.json").read_text(encoding="utf-8"))
    staged = packages.stage(built.path, staging_root=tmp_path / "staging")
    packages.export(staged.path, destination=tmp_path / "export")
    return packages, built, manifest, staged


def _valid_result(repository, manifest, *, locator=None):
    target = manifest["target"]
    raw_id = manifest["raw_grounding"]["included_raw_artifact_ids"][0]
    facets = repository.semantic_store.facets_for_classes(
        (target["primary_class_id"], *target["additional_class_ids"])
    )
    grounding = {"raw_artifact_id": raw_id, "role": "supports"}
    if locator is not None:
        grounding["locator"] = locator
    return {
        "schema_version": "sgokb.object-result/2.0",
        "result_status": "complete",
        "target": {
            "object_id": target["object_id"],
            "primary_class_id": target["primary_class_id"],
            "additional_class_ids": target["additional_class_ids"],
        },
        "binding": {
            "package_id": manifest["package_id"],
            "package_schema_version": manifest["schema_version"],
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "package_created_at": manifest["created_at"],
            "base_version_id": manifest["binding"]["base_version_id"],
            "grounding_contract": manifest["binding"]["grounding_contract"],
            "grounding_set_sha256": manifest["raw_grounding"]["integrity"][
                "grounding_set_sha256"
            ],
        },
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
            "generator_kind": "interactive_ai",
            "application": "ChatGPT",
            "generated_at": "2026-10-29T16:05:00Z",
        },
        "knowledge": {
            "default_language": "ja",
            "summary": [
                {
                    "local_key": "summary-1",
                    "text": "Alice Rawは架空のキャラクターである。",
                    "derivation_kind": "direct_statement",
                    "grounding": [grounding],
                }
            ],
            "facets": [
                {"facet_id": facet.facet_id, "status": "not_analyzed", "statements": []}
                for facet in facets
            ],
            "attributes": [],
            "relations": [],
        },
        "conflicts": [],
        "gaps": [],
        "unresolved_references": [],
        "registry_proposals": [],
        "class_extensions": [],
    }


def _receive(repository, tmp_path, manifest, result):
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    results = ResultExchangeApplication(repository)
    receipt = results.receive(
        result_path,
        package_id=manifest["package_id"],
        incoming_root=tmp_path / "incoming",
    )
    return results, receipt


def test_package_v2_contains_exact_raw_bytes_and_deduplicates_by_artifact_id(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, _, artifact_id, evidence_ids, raw = _setup(
            repository,
            tmp_path,
            two_evidence=True,
        )
        _, built, manifest, _ = _build_stage_export(
            repository,
            tmp_path,
            object_id,
            include_evidence=evidence_ids,
        )

        assert built.raw_artifact_count == 1
        assert validate_package_manifest_v2(manifest) == ()
        assert manifest["schema_version"] == "sgokb.object-evidence-package/2.0"
        assert manifest["evidence"]["included_evidence_ids"] == list(evidence_ids)
        assert manifest["raw_grounding"]["included_raw_artifact_ids"] == [artifact_id]
        assert [item["evidence_id"] for item in manifest["raw_grounding"]["evidence_bindings"]] == list(
            evidence_ids
        )
        raw_path = Path(built.path) / "raw" / "artifact_0001" / "payload"
        assert raw_path.read_bytes() == raw
        assert not (Path(built.path) / "evidence").exists()
    finally:
        repository.close()


def test_result_v2_validates_reviews_imports_and_persists_only_raw_grounding(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, _, artifact_id, _, _ = _setup(repository, tmp_path)
        _, _, manifest, _ = _build_stage_export(repository, tmp_path, object_id)
        result = _valid_result(
            repository,
            manifest,
            locator={"kind": "text_quote", "exact": "Alice Raw"},
        )
        results, receipt = _receive(repository, tmp_path, manifest, result)

        report = results.validate(receipt.receipt_id, incoming_root=tmp_path / "incoming")
        assert report.validation_state == "valid"
        review = results.review(receipt.receipt_id, incoming_root=tmp_path / "incoming")
        assert not review.blocked
        imported = results.import_result(
            receipt.receipt_id,
            incoming_root=tmp_path / "incoming",
            acknowledge_review=review.requires_review,
        )

        assert repository.version_store.current_version_id(object_id) == imported.version_id
        assert repository.one(
            "SELECT count(*) AS n FROM evidence_links WHERE version_id=?",
            (imported.version_id,),
        )["n"] == 0
        raw_links = repository.all(
            "SELECT raw_artifact_id,role,locator_json FROM raw_grounding_links WHERE version_id=?",
            (imported.version_id,),
        )
        assert len(raw_links) == 1
        assert raw_links[0]["raw_artifact_id"] == artifact_id
        assert raw_links[0]["role"] == "supports"
        assert json.loads(raw_links[0]["locator_json"])["exact"] == "Alice Raw"

        shown = VersionReadApplication(repository).show(imported.version_id)
        assert shown["grounding_kind"] == "raw"
        assert shown["knowledge"]["summary"][0]["evidence"] == []
        assert shown["knowledge"]["summary"][0]["grounding"][0][
            "raw_artifact_id"
        ] == artifact_id
    finally:
        repository.close()


def test_result_v2_rejects_raw_outside_package_and_invalid_locator(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, _, _, _, raw = _setup(repository, tmp_path)
        _, _, manifest, _ = _build_stage_export(repository, tmp_path, object_id)

        other_source = repository.source_store.create_source(
            "Other Raw",
            source_id="source-praw05-other",
        )
        other_snapshot = "snapshot-praw05-other"
        repository.source_store.create_snapshot(
            other_source,
            "2026-10-29T16:10:00Z",
            "test_fixture",
            snapshot_id=other_snapshot,
        )
        other_path = tmp_path / "other.html"
        other_path.write_bytes(raw)
        other_raw_id = repository.source_store.add_raw_artifact(
            other_snapshot,
            "rendered_dom",
            str(other_path),
            _sha256(raw),
            len(raw),
            media_type="text/html",
            artifact_id="raw-praw05-other",
        )

        outside = _valid_result(repository, manifest)
        outside["knowledge"]["summary"][0]["grounding"][0][
            "raw_artifact_id"
        ] = other_raw_id
        results, receipt = _receive(repository, tmp_path, manifest, outside)
        report = results.validate(receipt.receipt_id, incoming_root=tmp_path / "incoming")
        assert report.validation_state == "invalid"
        assert "raw_artifact_outside_package" in {item.code for item in report.findings}

        invalid_locator = _valid_result(
            repository,
            manifest,
            locator={"kind": "byte_range", "start": 0, "end": len(raw) + 1},
        )
        results, receipt = _receive(repository, tmp_path, manifest, invalid_locator)
        report = results.validate(receipt.receipt_id, incoming_root=tmp_path / "incoming")
        assert report.validation_state == "invalid"
        assert "raw_locator_invalid" in {item.code for item in report.findings}
    finally:
        repository.close()


def test_v2_update_recovers_selection_lineage_and_blocks_legacy_v1_downgrade(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, _, _, evidence_ids, _ = _setup(repository, tmp_path)
        packages, _, manifest, _ = _build_stage_export(repository, tmp_path, object_id)
        result = _valid_result(repository, manifest)
        results, receipt = _receive(repository, tmp_path, manifest, result)
        assert results.validate(
            receipt.receipt_id,
            incoming_root=tmp_path / "incoming",
        ).validation_state == "valid"
        imported = results.import_result(
            receipt.receipt_id,
            incoming_root=tmp_path / "incoming",
        )

        updated = packages.build(
            object_id,
            package_version="v2",
            build_root=tmp_path / "update-build",
        )
        update_manifest = json.loads(
            Path(updated.path, "manifest.json").read_text(encoding="utf-8")
        )
        assert update_manifest["binding"]["base_version_id"] == imported.version_id
        assert evidence_ids[0] in update_manifest["evidence"]["included_evidence_ids"]
        selected = next(
            item
            for item in update_manifest["evidence"]["items"]
            if item["evidence_id"] == evidence_ids[0]
        )
        assert "carry_forward" in selected["package_roles"]
        current = json.loads(
            Path(updated.path, "current_object.json").read_text(encoding="utf-8")
        )
        assert current["grounding_kind"] == "raw"
        assert current["knowledge"]["summary_statements"][0]["evidence"] == []
        assert current["knowledge"]["summary_statements"][0]["grounding"]

        with pytest.raises(ValueError, match="Legacy Package v1 build is blocked"):
            packages.build(
                object_id,
                package_version="v1",
                build_root=tmp_path / "legacy-build",
            )
    finally:
        repository.close()
