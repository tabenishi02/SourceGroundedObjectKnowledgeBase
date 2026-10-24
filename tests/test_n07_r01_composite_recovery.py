"""N07-R01 focused product tests for complete-canonical composite recovery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_object_version_import import _import, _validate
from test_result_validation import _valid_result

from sgokb import composite_recovery, system_ops
from sgokb.application import Application
from sgokb.exchange import ObjectEvidencePackageBuilder, PackageTransferService
from sgokb.exchange.result_import import load_immutable_result_artifact
from sgokb.repository import Repository
from sgokb.storage import PackageExchangeAuditRepository


def _complete_fixture(tmp_path, make_bundle):
    repo = Repository(tmp_path / "active" / "canonical.sqlite")
    bundle = make_bundle()
    app = Application(repo)
    imported = app.import_source_path(bundle)
    app.process_source_snapshot(imported["snapshot"])

    object_id = repo.object_store.create_object("Alice Example", "class:character")
    repo.source_store.associate_object(
        imported["source"],
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    built = ObjectEvidencePackageBuilder(repo).build(
        object_id,
        build_root=tmp_path / "build",
        semantic=False,
    )
    transfer = PackageTransferService()
    staged = transfer.stage_from_directory(built.path, tmp_path / "staging")
    manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
    audit = PackageExchangeAuditRepository(repo.db)
    audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
    exported = transfer.export(staged.path, tmp_path / "export")
    audit.record_export(
        exported.package_id,
        exported.manifest_sha256,
        exported.destination_root,
        exported.path,
        acknowledged_review=False,
        already_present=False,
    )
    receipt, incoming, _ = _validate(
        repo,
        audit,
        manifest,
        tmp_path,
        _valid_result(repo, manifest),
    )
    imported_version = _import(repo, audit, receipt, incoming)
    return {
        "repo": repo,
        "bundle": Path(bundle),
        "snapshot_id": imported["snapshot"],
        "object_id": object_id,
        "audit": audit,
        "receipt_id": receipt.receipt_id,
        "incoming": Path(incoming),
        "version_id": imported_version.version_id,
    }


def test_composite_generation_contains_complete_dependency_classes(tmp_path, make_bundle):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    try:
        backup = tmp_path / "backups" / "complete"
        created = composite_recovery.create_composite_backup(
            repo,
            incoming_root=fixture["incoming"],
            output=backup,
        )
        verified = composite_recovery.verify_composite_backup(backup)
        assert created["verification"]["ok"] is True
        assert verified["ok"] is True
        assert verified["raw_bundles"] == 1
        assert verified["original_results"] == 1

        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["canonical"]["path"] == "canonical/canonical.sqlite"
        assert manifest["raw"][0]["path"].endswith(fixture["bundle"].name)
        assert manifest["provenance"][0]["path"].endswith("result.json")
        assert manifest["recovery_metadata"]["path"] == "metadata/recovery.json"
    finally:
        repo.close()


def test_dependency_inventory_is_bound_to_sqlite_snapshot(tmp_path, make_bundle, monkeypatch):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    original = composite_recovery._create_sqlite_snapshot

    def snapshot_then_mutate(repository, destination):
        original(repository, destination)
        repository.source_store.add_raw_artifact(
            fixture["snapshot_id"],
            "late_live_only_artifact",
            str(fixture["bundle"]),
            "0" * 64,
            0,
            logical_path="late-live-only",
        )

    monkeypatch.setattr(composite_recovery, "_create_sqlite_snapshot", snapshot_then_mutate)
    try:
        backup = tmp_path / "backups" / "snapshot-bound"
        composite_recovery.create_composite_backup(
            repo,
            incoming_root=fixture["incoming"],
            output=backup,
        )
        canonical = Repository(backup / "canonical" / "canonical.sqlite")
        try:
            assert canonical.one(
                "SELECT count(*) n FROM raw_artifacts WHERE logical_path='late-live-only'"
            )["n"] == 0
        finally:
            canonical.close()
        assert repo.one(
            "SELECT count(*) n FROM raw_artifacts WHERE logical_path='late-live-only'"
        )["n"] == 1
        assert composite_recovery.verify_composite_backup(backup)["ok"] is True
    finally:
        repo.close()


def test_missing_raw_or_result_fails_closed_without_final_generation(tmp_path, make_bundle):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    try:
        raw_backup = tmp_path / "backups" / "missing-raw"
        quarantined_raw = fixture["bundle"].with_suffix(".quarantined")
        fixture["bundle"].rename(quarantined_raw)
        with pytest.raises((OSError, ValueError)):
            composite_recovery.create_composite_backup(
                repo,
                incoming_root=fixture["incoming"],
                output=raw_backup,
            )
        assert not raw_backup.exists()
        quarantined_raw.rename(fixture["bundle"])

        row = fixture["audit"].result_receipt(fixture["receipt_id"])
        result_path = fixture["incoming"] / row["storage_ref"]
        quarantined_result = result_path.with_suffix(".quarantined")
        result_path.rename(quarantined_result)
        result_backup = tmp_path / "backups" / "missing-result"
        with pytest.raises((OSError, ValueError)):
            composite_recovery.create_composite_backup(
                repo,
                incoming_root=fixture["incoming"],
                output=result_backup,
            )
        assert not result_backup.exists()
    finally:
        repo.close()


def test_tampered_generation_is_rejected(tmp_path, make_bundle):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    try:
        backup = tmp_path / "backups" / "tamper"
        composite_recovery.create_composite_backup(
            repo,
            incoming_root=fixture["incoming"],
            output=backup,
        )
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        raw = backup / Path(*manifest["raw"][0]["path"].split("/"))
        raw.write_bytes(raw.read_bytes() + b"tamper")
        with pytest.raises(ValueError):
            composite_recovery.verify_composite_backup(backup)
    finally:
        repo.close()


def test_restore_to_alternate_roots_relocates_raw_and_preserves_result_ref(tmp_path, make_bundle):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    backup = tmp_path / "backups" / "restore"
    try:
        composite_recovery.create_composite_backup(
            repo,
            incoming_root=fixture["incoming"],
            output=backup,
        )
        original_result_ref = repo.one(
            "SELECT result_storage_ref FROM object_result_imports WHERE version_id=?",
            (fixture["version_id"],),
        )["result_storage_ref"]
    finally:
        repo.close()

    # Prove the restored system does not depend on the original external stores.
    quarantined_raw = fixture["bundle"].with_suffix(".quarantined")
    fixture["bundle"].rename(quarantined_raw)
    quarantined_incoming = fixture["incoming"].with_name("incoming.quarantined")
    fixture["incoming"].rename(quarantined_incoming)

    db_target = tmp_path / "restored" / "canonical.sqlite"
    raw_root = tmp_path / "restored-raw"
    incoming_root = tmp_path / "restored-incoming"
    result = composite_recovery.composite_restore_apply(
        backup,
        db_target=db_target,
        raw_root=raw_root,
        incoming_root=incoming_root,
    )
    assert result["restored"] is True

    restored = Repository(db_target)
    try:
        refs = {
            Path(row["storage_ref"])
            for row in restored.db.execute(
                "SELECT DISTINCT storage_ref FROM raw_artifacts WHERE snapshot_id=?",
                (fixture["snapshot_id"],),
            )
        }
        assert len(refs) == 1
        restored_raw = next(iter(refs))
        assert restored_raw.is_relative_to(raw_root.resolve())
        assert restored_raw.name == quarantined_raw.name.replace(".quarantined", "")
        assert restored_raw.exists()

        # Existing product code must be able to reopen and reprocess restored Raw bytes.
        processed = Application(restored).process_source_snapshot(fixture["snapshot_id"])
        assert processed["snapshot"] == fixture["snapshot_id"]

        restored_ref = restored.one(
            "SELECT result_storage_ref FROM object_result_imports WHERE version_id=?",
            (fixture["version_id"],),
        )["result_storage_ref"]
        assert restored_ref == original_result_ref
        audit = PackageExchangeAuditRepository(restored.db)
        receipt = audit.result_receipt(fixture["receipt_id"])
        parsed, digest, byte_count = load_immutable_result_artifact(receipt, incoming_root)
        assert parsed["target"]["object_id"] == fixture["object_id"]
        assert digest == receipt["result_sha256"]
        assert byte_count == receipt["byte_count"]
    finally:
        restored.close()


def test_restore_plan_is_read_only_and_overlap_is_rejected(tmp_path, make_bundle):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    try:
        backup = tmp_path / "backups" / "plan"
        composite_recovery.create_composite_backup(
            repo,
            incoming_root=fixture["incoming"],
            output=backup,
        )
        db = tmp_path / "restore" / "canonical.sqlite"
        raw = tmp_path / "restore-raw"
        incoming = tmp_path / "restore-incoming"
        plan = composite_recovery.composite_restore_plan(
            backup,
            db_target=db,
            raw_root=raw,
            incoming_root=incoming,
        )
        assert plan["verification"]["ok"] is True
        assert not db.exists() and not raw.exists() and not incoming.exists()
        with pytest.raises(ValueError, match="overlap"):
            composite_recovery.composite_restore_plan(
                backup,
                db_target=tmp_path / "same" / "canonical.sqlite",
                raw_root=tmp_path / "same",
                incoming_root=tmp_path / "elsewhere",
            )
    finally:
        repo.close()


def test_recovery_metadata_omits_original_absolute_roots_and_legacy_backup_still_works(
    tmp_path, make_bundle
):
    fixture = _complete_fixture(tmp_path, make_bundle)
    repo = fixture["repo"]
    try:
        backup = tmp_path / "backups" / "metadata"
        composite_recovery.create_composite_backup(
            repo,
            incoming_root=fixture["incoming"],
            output=backup,
        )
        text = (backup / "metadata" / "recovery.json").read_text(encoding="utf-8")
        assert str(fixture["bundle"].parent.resolve()) not in text
        assert str(fixture["incoming"].resolve()) not in text
        metadata = json.loads(text)
        assert metadata["plaintext_secrets_included"] is False
        assert metadata["original_absolute_roots_included"] is False

        legacy = tmp_path / "legacy" / "canonical.sqlite"
        system_ops.create_backup(repo, legacy)
        legacy_restore = tmp_path / "legacy-restored.sqlite"
        system_ops.restore_apply(legacy, legacy_restore, acknowledge_overwrite=False)
        assert Repository(legacy_restore).db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        repo.close()
