"""N07-R01 focused product tests for complete-canonical composite recovery."""

from __future__ import annotations

import json
import sqlite3
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


def _complete_fixture(tmp_path, make_bundle, *, r2=False):
    repo = Repository(tmp_path / "active" / "canonical.sqlite")
    bundle = make_bundle()
    app = Application(repo)
    imported = app.import_source_path(bundle)
    app.process_source_snapshot(imported["snapshot"])
    if r2:
        from qdrant_client import QdrantClient

        from sgokb.application_generation import KnowledgeSearchGenerationApplication
        from sgokb.retrieval.embedding import frozen_harrier_space
        from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

        client = QdrantClient(location=":memory:")
        try:
            KnowledgeSearchGenerationApplication(
                repo,
                embedding_space=frozen_harrier_space(),
                vector_index=QdrantVectorIndexAdapter(client=client, wait_for_index=False),
            ).bootstrap_empty_r2()
        finally:
            client.close()

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
        canonical = sqlite3.connect(
            (backup / "canonical/canonical.sqlite").resolve().as_uri() + "?mode=ro&immutable=1",
            uri=True,
        )
        try:
            assert (
                canonical.execute(
                    "SELECT count(*) FROM raw_artifacts WHERE logical_path='late-live-only'"
                ).fetchone()[0]
                == 0
            )
        finally:
            canonical.close()
        assert (
            repo.one("SELECT count(*) n FROM raw_artifacts WHERE logical_path='late-live-only'")[
                "n"
            ]
            == 1
        )
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
        assert restored_raw.name == fixture["bundle"].name
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
        restored = Repository(legacy_restore)
        try:
            assert restored.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            restored.close()
    finally:
        repo.close()


@pytest.fixture
def complete_case(tmp_path, make_bundle):
    fixture = _complete_fixture(tmp_path, make_bundle)
    backup = tmp_path / "generations" / "complete"
    composite_recovery.create_composite_backup(
        fixture["repo"], incoming_root=fixture["incoming"], output=backup
    )
    fixture["backup"] = backup
    try:
        yield fixture
    finally:
        fixture["repo"].close()


@pytest.mark.parametrize(
    "value",
    [
        "../result.json",
        "/absolute/result.json",
        "x/../result.json",
        "x\\result.json",
        "x//result.json",
        "./result.json",
        "x/./result.json",
        "C:/result.json",
        "x:stream/result.json",
        "NUL/result.json",
        "x./result.json",
    ],
)
def test_unsafe_result_paths_rejected(tmp_path, value):
    with pytest.raises(ValueError):
        composite_recovery._safe_result_source(tmp_path, value)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_raw",
        "missing_result",
        "raw_hash",
        "result_hash",
        "manifest_traversal",
        "incomplete",
        "extra",
        "metadata_fields",
    ],
)
def test_negative_generation_drills(complete_case, fault):
    backup = complete_case["backup"]
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    raw = backup / manifest["raw"][0]["path"]
    result = backup / manifest["provenance"][0]["path"]
    if fault == "missing_raw":
        raw.unlink()
    elif fault == "missing_result":
        result.unlink()
    elif fault in {"raw_hash", "result_hash"}:
        path = raw if fault == "raw_hash" else result
        path.write_bytes(path.read_bytes() + b"tampered")
    elif fault == "manifest_traversal":
        manifest["raw"][0]["path"] = "../outside.webcapture.zip"
        composite_recovery._write_json(backup / "manifest.json", manifest)
    elif fault == "incomplete":
        (backup / "manifest.json").unlink()
    elif fault == "extra":
        (backup / "undeclared").write_bytes(b"unexpected")
    else:
        metadata = backup / "metadata/recovery.json"
        data = json.loads(metadata.read_text(encoding="utf-8"))
        data["unapproved_extra"] = "not allowed"
        composite_recovery._write_json(metadata, data)
        manifest["recovery_metadata"].update(composite_recovery._file_identity(metadata))
        composite_recovery._write_json(backup / "manifest.json", manifest)
    with pytest.raises((OSError, ValueError, RuntimeError)):
        composite_recovery.verify_composite_backup(backup)


def test_valid_manifest_in_staging_directory_rejected(complete_case):
    import shutil

    backup = complete_case["backup"]
    stage = backup.with_name(".candidate.staging-owned")
    shutil.copytree(backup, stage)
    with pytest.raises(ValueError, match="Staging"):
        composite_recovery.verify_composite_backup(stage)


def test_verify_and_plan_preserve_backup_bytes(complete_case, tmp_path):
    import hashlib

    backup = complete_case["backup"]

    def fingerprint():
        return {
            p.relative_to(backup).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in backup.rglob("*")
            if p.is_file()
        }

    before = fingerprint()
    composite_recovery.verify_composite_backup(backup)
    composite_recovery.composite_restore_plan(
        backup,
        db_target=tmp_path / "restored.sqlite",
        raw_root=tmp_path / "raw",
        incoming_root=tmp_path / "incoming-alt",
    )
    assert fingerprint() == before


@pytest.mark.parametrize("boundary", ["stage_copy", "raw", "incoming", "metadata", "database"])
@pytest.mark.parametrize("empty_roots_exist", [False, True])
def test_restore_failure_preserves_existing_target(
    complete_case, tmp_path, monkeypatch, boundary, empty_roots_exist
):
    import errno

    db = tmp_path / "target" / "canonical.sqlite"
    repo = Repository(db)
    repo.object_store.create_object("Preserve me", "class:character")
    repo.close()
    old_db = db.read_bytes()
    metadata = db.with_name(db.name + ".recovery.json")
    metadata.write_bytes(b"old metadata")
    raw = tmp_path / "alternate-raw"
    incoming = tmp_path / "alternate-incoming"
    if empty_roots_exist:
        raw.mkdir()
        incoming.mkdir()
    original_replace = composite_recovery.os.replace
    original_copy = composite_recovery.shutil.copy2
    fired = False
    target = {"raw": raw, "incoming": incoming, "metadata": metadata, "database": db}

    def replace(source, destination):
        nonlocal fired
        if not fired and boundary != "stage_copy" and Path(destination) == target[boundary]:
            fired = True
            raise OSError(errno.EIO, "controlled publication fault")
        return original_replace(source, destination)

    def copy(source, destination, *args, **kwargs):
        nonlocal fired
        if not fired and boundary == "stage_copy":
            fired = True
            Path(destination).write_bytes(b"partial")
            raise OSError(errno.ENOSPC, "controlled partial copy")
        return original_copy(source, destination, *args, **kwargs)

    monkeypatch.setattr(composite_recovery.os, "replace", replace)
    monkeypatch.setattr(composite_recovery.shutil, "copy2", copy)
    with pytest.raises(OSError, match="controlled"):
        composite_recovery.composite_restore_apply(
            complete_case["backup"],
            db_target=db,
            raw_root=raw,
            incoming_root=incoming,
            acknowledge_overwrite=True,
        )
    assert fired
    assert db.read_bytes() == old_db
    assert metadata.read_bytes() == b"old metadata"
    for root in (raw, incoming):
        assert root.exists() == empty_roots_exist
        if root.exists():
            assert list(root.iterdir()) == []
    assert not list(tmp_path.rglob("*.restore-*.tmp"))
    assert not list(tmp_path.rglob("*.rollback-*.tmp"))


def test_nonempty_external_and_live_sqlite_targets_fail_closed(complete_case, tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "keep").write_bytes(b"old")
    with pytest.raises(RuntimeError, match="empty"):
        composite_recovery.composite_restore_apply(
            complete_case["backup"],
            db_target=tmp_path / "target.sqlite",
            raw_root=raw,
            incoming_root=tmp_path / "unused-incoming",
            acknowledge_overwrite=True,
        )
    assert (raw / "keep").read_bytes() == b"old"
    (raw / "keep").unlink()
    repo = Repository(tmp_path / "target.sqlite")
    repo.object_store.create_object("Live writer", "class:character")
    try:
        with pytest.raises(RuntimeError, match="offline"):
            composite_recovery.composite_restore_apply(
                complete_case["backup"],
                db_target=tmp_path / "target.sqlite",
                raw_root=raw,
                incoming_root=tmp_path / "unused-incoming",
                acknowledge_overwrite=True,
            )
    finally:
        repo.close()


def test_symlink_is_checked_before_resolve(complete_case, monkeypatch):
    backup = complete_case["backup"]
    original = Path.is_symlink

    def linked(path):
        return path == backup or original(path)

    monkeypatch.setattr(Path, "is_symlink", linked)
    with pytest.raises(ValueError, match="symlink"):
        composite_recovery.verify_composite_backup(backup)


def test_composite_cli_create_verify_plan_apply(complete_case, tmp_path, capsys):
    from sgokb.cli.main import main

    db = tmp_path / "active/canonical.sqlite"
    backup = tmp_path / "cli-generation"
    assert (
        main(
            [
                "--db",
                str(db),
                "system",
                "backup",
                "composite",
                "create",
                "--incoming-root",
                str(complete_case["incoming"]),
                "--output",
                str(backup),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["data"]["verification"]["ok"]
    unused = tmp_path / "must-not-open.sqlite"
    assert main(["--db", str(unused), "system", "backup", "composite", "verify", str(backup)]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["ok"]
    options = [
        str(backup),
        "--db-target",
        str(tmp_path / "cli-restored.sqlite"),
        "--raw-root",
        str(tmp_path / "cli-raw"),
        "--incoming-root",
        str(tmp_path / "cli-incoming"),
    ]
    assert main(["--db", str(unused), "system", "restore", "composite", "plan", *options]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["verification"]["ok"]
    assert not unused.exists() and not (tmp_path / "cli-restored.sqlite").exists()
    assert main(["--db", str(unused), "system", "restore", "composite", "apply", *options]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["restored"]
    assert not unused.exists()
    assert main(["system", "restore", "composite", "apply", *options]) != 0
    capsys.readouterr()


def test_formal_product_drill(tmp_path, make_bundle):
    from benchmark.tools.n07_r01_reacceptance import product_drill

    fixture = _complete_fixture(tmp_path, make_bundle, r2=True)
    try:
        proof = product_drill(fixture, tmp_path)
        assert all(proof["product_proofs"].values())
        assert all(case["status"] == "PASS" for case in proof["negative_drills"].values())
        assert proof["complete_canonical_rpo_hours"] <= 24
        assert proof["canonical_rto_seconds"] <= 14400
    finally:
        fixture["repo"].close()


def test_formal_evaluator_rejects_missing_or_failed_recovery():
    from benchmark.tools.n07_r01_reacceptance import evaluate

    assert evaluate({})["overall"] == "BLOCKED"
    failed = {"proof": {"canonical_rto_seconds": 14400.001}}
    assert evaluate(failed)["overall"] == "FAIL"
    assert "canonical_rto_seconds" in evaluate(failed)["failures"]


def test_formal_evaluator_pass_and_exact_boundaries():
    from benchmark.tools.n07_r01_reacceptance import CONTRACT, NEGATIVES, evaluate

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    proof = {
        "product_proofs": {
            name: True for name in contract["acceptance"]["required_product_proofs"]
        },
        "complete_canonical_rpo_hours": 24.0,
        "canonical_rto_seconds": 14400.0,
        "negative_drills": {name: {"status": "PASS"} for name in NEGATIVES},
    }
    for name in [
        "source_stores_quarantined",
        "backup_unchanged",
        "raw_basename_preserved",
        "only_raw_storage_ref_relocated",
        "accepted_result_audit_unchanged",
        "minimum_lexical_retrieval",
        "recovery_metadata_verified",
    ]:
        proof[name] = True
    evidence = {
        "proof": proof,
        **{
            name: {"status": "PASS"}
            for name in [
                "preflight",
                "formal_tests",
                "derived_rebuild",
                "post_regression",
                "safety",
            ]
        },
    }
    assert evaluate(evidence)["overall"] == "PASS"
    for value in [24.00001, float("nan"), float("inf"), True]:
        proof["complete_canonical_rpo_hours"] = value
        assert evaluate(evidence)["overall"] == "FAIL"


def test_nonexistent_generation_verification_does_not_create_files(tmp_path):
    target = tmp_path / "absent"
    with pytest.raises(ValueError):
        composite_recovery.verify_composite_backup(target)
    assert not target.exists()
