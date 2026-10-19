import json
from pathlib import Path

from sgokb.exchange import (
    ObjectEvidencePackageBuilder,
    PackageTransferService,
    ResultReceiptService,
    validate_package_manifest,
)
from sgokb.repository import Repository
from sgokb.storage import PackageExchangeAuditRepository


def _add_generation(repository, source_id, suffix, content):
    store = repository.source_store
    locator = store.ensure_locator(source_id, "url", f"https://example.test/{suffix}")
    snapshot_id = f"snapshot-{suffix}"
    store.create_snapshot(
        source_id,
        f"2026-10-13T00:0{suffix[-1] if suffix[-1].isdigit() else '0'}:00Z",
        "test_fixture",
        observed_locator_id=locator,
        title=f"Source {suffix}",
        snapshot_id=snapshot_id,
    )
    artifact_id = store.add_raw_artifact(
        snapshot_id,
        "rendered_dom",
        f"fixture/{suffix}.html",
        "a" * 64,
        1,
        logical_path="dom/main.html",
        media_type="text/html",
    )
    run_id = f"run-{suffix}"
    store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        [artifact_id],
        run_id=run_id,
    )
    evidence_id = f"evidence-{suffix}"
    store.add_evidence(
        run_id,
        content,
        "normalized",
        metadata={"section": ["Profile"], "start": 0, "kinds": ["paragraph"]},
        evidence_id=evidence_id,
    )
    store.add_evidence_location(
        evidence_id,
        "heading_path",
        {"headings": ["Profile"]},
    )
    store.select_effective_snapshot(
        source_id,
        snapshot_id,
        origin_kind="manual",
        reason="fixture",
    )
    store.select_effective_run(
        snapshot_id,
        run_id,
        origin_kind="manual",
        reason="fixture",
    )
    return snapshot_id, run_id, evidence_id


def _setup_initial(repository):
    object_id = repository.object_store.create_object(
        "Alice Example",
        "class:character",
        aliases=["Alice"],
        object_id="object-alice",
    )
    source_id = repository.source_store.create_source("Alice reference", source_id="source-alice")
    _, _, evidence_id = _add_generation(
        repository,
        source_id,
        "1",
        "Alice Example is a fictional character used for the Phase G fixture.",
    )
    repository.source_store.associate_object(
        source_id,
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    return object_id, source_id, evidence_id


def _routing_result(manifest):
    return {
        "schema_version": manifest["binding"]["expected_result_schema_version"],
        "result_status": "complete",
        "target": {
            "object_id": manifest["target"]["object_id"],
            "primary_class_id": manifest["target"]["primary_class_id"],
            "additional_class_ids": manifest["target"]["additional_class_ids"],
        },
        "binding": {
            "package_id": manifest["package_id"],
            "package_schema_version": manifest["schema_version"],
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "package_created_at": manifest["created_at"],
            "base_version_id": manifest["binding"]["base_version_id"],
        },
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
        },
    }


def test_phase_g_initial_object_round_trip_reaches_pending_validation_without_import(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, _, _ = _setup_initial(repository)
        builder = ObjectEvidencePackageBuilder(repository)
        built = builder.build(object_id, build_root=tmp_path / "build", semantic=False)
        workspace = Path(built.path)
        manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))

        assert validate_package_manifest(manifest) == ()
        assert manifest["binding"]["base_version_id"] is None
        assert manifest["artifacts"]["current_object_path"] is None
        assert (workspace / "instructions.md").is_file()
        assert list((workspace / "evidence").glob("source_*.md"))

        transfer = PackageTransferService()
        staged = transfer.stage_from_directory(workspace, tmp_path / "staging")
        audit = PackageExchangeAuditRepository(repository.db)
        staged_manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
        audit.record_staged(staged_manifest, staged.path, staged.preflight.to_dict())

        exported = transfer.export(staged.path, tmp_path / "DriveSync")
        audit.record_export(
            exported.package_id,
            exported.manifest_sha256,
            exported.destination_root,
            exported.path,
            acknowledged_review=False,
            already_present=exported.already_present,
        )

        returned = tmp_path / "result.json"
        returned.write_text(
            json.dumps(_routing_result(staged_manifest), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = ResultReceiptService(audit).receive(
            returned,
            built.package_id,
            tmp_path / "incoming",
        )

        assert receipt.intake_state == "ready_for_validation"
        assert receipt.validation_state == "pending"
        assert Path(receipt.path).is_file()
        assert repository.version_store.current_version_id(object_id) is None
        assert repository.one("SELECT count(*) AS n FROM object_versions")["n"] == 0
    finally:
        repository.close()


def test_update_package_serializes_current_object_and_protects_historical_grounding(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, source_id, old_evidence_id = _setup_initial(repository)
        version_id = repository.version_store.begin_candidate(object_id, None)
        repository.semantic_store.set_version_facet(version_id, "facet:overall", "content")
        statement_id = repository.semantic_store.add_statement(
            version_id,
            "summary-1",
            "Alice Example is the fixture character.",
            "direct_statement",
            facet_id="facet:overall",
            language="en",
        )
        repository.source_store.link_evidence(
            version_id,
            "statement",
            statement_id,
            old_evidence_id,
            "supports",
        )
        repository.version_store.accept_candidate(version_id)

        _add_generation(
            repository,
            source_id,
            "2",
            "Alice Example appears again in a newer effective Source generation.",
        )

        built = ObjectEvidencePackageBuilder(repository).build(
            object_id,
            build_root=tmp_path / "build",
            semantic=False,
        )
        root = Path(built.path)
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        current = json.loads((root / "current_object.json").read_text(encoding="utf-8"))

        assert built.base_version_id == version_id
        assert manifest["artifacts"]["current_object_path"] == "current_object.json"
        assert old_evidence_id in manifest["evidence"]["included_evidence_ids"]
        old_item = next(
            item for item in manifest["evidence"]["items"] if item["evidence_id"] == old_evidence_id
        )
        assert "carry_forward" in old_item["package_roles"]
        assert old_item["selected_by"] == "protected"
        assert current["version_id"] == version_id
        assert current["knowledge"]["facets"][0]["statements"][0]["evidence"] == [
            {"evidence_id": old_evidence_id, "role": "supports"}
        ]
        assert validate_package_manifest(manifest) == ()
    finally:
        repository.close()
