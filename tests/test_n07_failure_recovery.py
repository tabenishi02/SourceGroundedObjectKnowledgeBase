"""N-07 product-boundary faults; only pytest-owned disposable assets are mutated."""

from __future__ import annotations

import errno
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from test_object_version_import import _import, _validate
from test_package_transfer import _workspace
from test_result_validation import _build_and_stage, _receive, _valid_result

from benchmark.tools.n07_evaluate_failure_recovery import CONTRACT, evaluate
from benchmark.tools.n07_recovery_helpers import (
    database_digest,
    owned_path,
    recovery_inventory,
)
from sgokb import system_ops
from sgokb.application import Application
from sgokb.application_read import KnowledgeReadApplication
from sgokb.exchange.package_transfer import PackageTransferService
from sgokb.exchange.result_import import load_immutable_result_artifact
from sgokb.repository import Repository


def observe(tmp_path, name, data):
    (tmp_path / (name + "-observation.json")).write_text(
        json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8"
    )


def assert_integrity(repo):
    assert system_ops.integrity(repo)["ok"]


@pytest.mark.parametrize("case", range(1, 12), ids=lambda n: f"B{n:02}")
def test_exchange_faults(tmp_path, case):
    repo = Repository(tmp_path / "exchange.sqlite")
    try:
        if case >= 8:
            source = _workspace(tmp_path)
            path = source / "evidence/source_001.md"
            original = path.read_bytes()
            if case == 8:
                path.unlink()
            elif case == 9:
                path.write_bytes(original + b"x")
            elif case == 10:
                path.write_bytes(b"X" * len(original))
            else:
                (source / "unexpected.txt").write_bytes(b"unexpected")
            before = database_digest(repo.db)
            with pytest.raises(ValueError) as exc:
                PackageTransferService().stage_from_directory(source, tmp_path / "staging")
            assert not list((tmp_path / "staging").glob("pkg_*"))
            assert database_digest(repo.db) == before
            if case == 11:
                (source / "unexpected.txt").unlink()
            path.write_bytes(original)
            assert (
                PackageTransferService()
                .stage_from_directory(source, tmp_path / "staging")
                .preflight.disposition
                == "allow"
            )
        else:
            audit, manifest, oid, *_ = _build_and_stage(repo, tmp_path)
            result = _valid_result(repo, manifest)
            if case == 1:
                result["execute"] = "invalid-schema-property"
            elif case == 2:
                result["binding"]["package_id"] = "pkg_00000000-0000-4000-8000-000000000000"
            elif case == 3:
                result["binding"]["manifest_sha256"] = "b" * 64
            elif case == 7:
                result = b'{"truncated":'
            service, receipt, incoming = _receive(repo, audit, manifest, tmp_path, result)
            if case in {5, 6}:
                assert (
                    service.validate_receipt(
                        receipt.receipt_id, incoming_root=incoming
                    ).validation_state
                    == "valid"
                )
                row = audit.result_receipt(receipt.receipt_id)
                path = incoming / row["storage_ref"]
                original = path.read_bytes()
                path.write_bytes(original + b"x" if case == 5 else b"X" * len(original))
            elif case == 4:
                version = repo.version_store.begin_candidate(oid, None)
                repo.version_store.accept_candidate(version)
            before = repo.version_store.current_version_id(oid)
            if case in {5, 6}:
                with pytest.raises(ValueError, match="byte count|SHA-256") as exc:
                    _import(repo, audit, receipt, incoming)
                path.write_bytes(original)
                assert load_immutable_result_artifact(row, incoming)
            else:
                report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
                assert report.validation_state == "invalid"
                with pytest.raises(ValueError) as exc:
                    _import(repo, audit, receipt, incoming)
            assert repo.version_store.current_version_id(oid) == before
            assert repo.one("SELECT count(*) n FROM object_result_imports")["n"] == 0
            # Retry original valid input against the unchanged current base.
            retry_root = tmp_path / "retry"
            retry_root.mkdir()
            if case in {5, 6}:
                assert _import(repo, audit, receipt, incoming).version_id
            elif case != 4:
                valid = _valid_result(repo, manifest)
                receipt2, incoming2, _ = _validate(repo, audit, manifest, retry_root, valid)
                assert _import(repo, audit, receipt2, incoming2).version_id
            else:
                # Stale original cannot become valid: a fresh Package must bind the new base.
                assert before is not None
        assert_integrity(repo)
        observe(tmp_path, "exchange", {"case": case, "rejection": str(exc.value), "status": "PASS"})
    finally:
        repo.close()


@pytest.mark.parametrize("checkpoint", ["candidate_created", "knowledge_written", "accepted"])
def test_import_checkpoint_rolls_back(tmp_path, checkpoint):
    repo = Repository(tmp_path / "transaction.sqlite")
    try:
        audit, manifest, oid, *_ = _build_and_stage(repo, tmp_path)
        receipt, incoming, _ = _validate(
            repo, audit, manifest, tmp_path, _valid_result(repo, manifest)
        )
        before = database_digest(repo.db)

        def fail(label):
            if label == checkpoint:
                raise OSError(errno.EIO, "N07 controlled import interruption")

        with pytest.raises(OSError, match="N07"):
            _import(repo, audit, receipt, incoming, failure_hook=fail)
        assert database_digest(repo.db) == before
        assert repo.version_store.current_version_id(oid) is None
        assert repo.one("SELECT count(*) n FROM object_result_imports")["n"] == 0
        assert_integrity(repo)
        assert _import(repo, audit, receipt, incoming).version_id
        observe(tmp_path, "transaction", {"checkpoint": checkpoint, "rollback": True})
    finally:
        repo.close()


def test_controlled_child_termination(tmp_path):
    path = tmp_path / "crash.sqlite"
    repo = Repository(path)
    audit, manifest, _, *_ = _build_and_stage(repo, tmp_path)
    receipt, incoming, _ = _validate(repo, audit, manifest, tmp_path, _valid_result(repo, manifest))
    before = database_digest(repo.db)
    repo.close()
    code = """
import sys
from sgokb.repository import Repository
from sgokb.exchange.result_import import ObjectVersionImportService
repo=Repository(sys.argv[1])
def checkpoint(label):
    if label=='knowledge_written':
        print('N07_OWNED_CHECKPOINT',flush=True)
        sys.stdin.read()
ObjectVersionImportService(repo,failure_hook=checkpoint).import_receipt(
    sys.argv[2],incoming_root=sys.argv[3])
"""
    worker = subprocess.Popen(
        [sys.executable, "-c", code, str(path), receipt.receipt_id, str(incoming)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        # Only this explicitly created worker can be killed; timeout prevents guessing.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            line = pool.submit(worker.stdout.readline)
            try:
                checkpoint = line.result(timeout=30)
            except TimeoutError:
                worker.kill()
                worker.wait(timeout=15)
                pytest.fail("Owned worker did not reach deterministic checkpoint")
            assert checkpoint.strip() == "N07_OWNED_CHECKPOINT"
            worker.kill()
            worker.wait(timeout=15)
        repo = Repository(path)
        try:
            assert database_digest(repo.db) == before
            assert_integrity(repo)
        finally:
            repo.close()
        observe(
            tmp_path,
            "crash",
            {"pid": worker.pid, "exit": worker.returncode, "old_committed_state_restored": True},
        )
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=15)
        for stream in [worker.stdin, worker.stdout, worker.stderr]:
            stream.close()


@pytest.mark.parametrize("boundary", ["package", "restore", "export"])
def test_os_file_faults(tmp_path, boundary):
    service = PackageTransferService()
    source = _workspace(tmp_path)
    output = tmp_path / "output"
    error = OSError(errno.ENOSPC, "N07 injected disk-full at product boundary")

    def partial_copy(source, destination, *args, **kwargs):
        Path(destination).write_bytes(b"partial")
        raise error

    def partial_tree(source, destination, *args, **kwargs):
        Path(destination).mkdir()
        (Path(destination) / "partial").write_bytes(b"partial")
        raise error

    if boundary == "package":
        with patch("sgokb.exchange.package_transfer.shutil.copyfile", side_effect=partial_copy):
            with pytest.raises(OSError) as exc:
                service.stage_from_directory(source, output)
        assert not list(output.iterdir())
        assert service.stage_from_directory(source, output).preflight.disposition == "allow"
    elif boundary == "export":
        staged = service.stage_from_directory(source, tmp_path / "staging")
        with patch("sgokb.exchange.package_transfer.shutil.copytree", side_effect=partial_tree):
            with pytest.raises(OSError) as exc:
                service.export(staged.path, output)
        assert not list(output.glob("pkg_*"))
        assert service.export(staged.path, output).path
    else:
        repo = Repository(tmp_path / "source.sqlite")
        backup = tmp_path / "backup.sqlite"
        system_ops.create_backup(repo, backup)
        repo.close()
        output.write_bytes(b"old target")
        with patch("sgokb.system_ops.shutil.copy2", side_effect=partial_copy):
            with pytest.raises(OSError) as exc:
                system_ops.restore_apply(backup, output, acknowledge_overwrite=True)
        assert output.read_bytes() == b"old target"
        assert not list(tmp_path.glob(".*.restore-*.tmp"))
        system_ops.restore_apply(backup, output, acknowledge_overwrite=True)
    assert exc.value.errno == errno.ENOSPC
    observe(
        tmp_path, "io", {"boundary": boundary, "errno": exc.value.errno, "retry_succeeded": True}
    )


def test_backup_ack_corrupt_and_replacement(tmp_path):
    repo = Repository(tmp_path / "source.sqlite")
    backup = tmp_path / "backups" / "point.sqlite"
    system_ops.create_backup(repo, backup)
    before = database_digest(repo.db)
    repo.close()
    target = tmp_path / "target.sqlite"
    system_ops.restore_apply(backup, target, acknowledge_overwrite=False)
    with pytest.raises(PermissionError):
        system_ops.restore_apply(backup, target, acknowledge_overwrite=False)
    corrupt = tmp_path / "corrupt.sqlite"
    corrupt.write_bytes(b"not a sqlite database")
    with pytest.raises((sqlite3.DatabaseError, RuntimeError)):
        system_ops.restore_apply(corrupt, target, acknowledge_overwrite=True)
    restored = Repository(target)
    try:
        assert database_digest(restored.db) == before
        assert_integrity(restored)
    finally:
        restored.close()


def test_recovery_inventory_and_raw_loss(tmp_path, make_bundle):
    repo = Repository(tmp_path / "active" / "canonical.sqlite")
    bundle = make_bundle()
    app = Application(repo)
    imported = app.import_source_path(bundle)
    app.process_source_snapshot(imported["snapshot"])
    from sgokb.exchange import ObjectEvidencePackageBuilder
    from sgokb.storage import PackageExchangeAuditRepository

    oid = repo.object_store.create_object("Alice Example", "class:character")
    repo.source_store.associate_object(
        imported["source"], oid, "confirmed", subject_relationship="primary_subject"
    )
    built = ObjectEvidencePackageBuilder(repo).build(
        oid, build_root=tmp_path / "build", semantic=False
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
    receipt, incoming, _ = _validate(repo, audit, manifest, tmp_path, _valid_result(repo, manifest))
    _import(repo, audit, receipt, incoming)
    # The fixture contains both real physical capture and accepted immutable Result provenance.
    inventory = recovery_inventory(repo)
    assert inventory == recovery_inventory(repo)
    before = database_digest(repo.db)
    backup = tmp_path / "separate-backups" / "canonical.sqlite"
    start = time.perf_counter()
    system_ops.create_backup(repo, backup)
    backup_seconds = time.perf_counter() - start
    assert database_digest(repo.db) == before
    restore_start = time.perf_counter()
    target = tmp_path / "restored" / "canonical.sqlite"
    system_ops.restore_apply(backup, target, acknowledge_overwrite=False)
    restore_seconds = time.perf_counter() - restore_start
    restored = Repository(target)
    try:
        assert database_digest(restored.db) == before
        assert_integrity(restored)
        assert KnowledgeReadApplication(restored).get_object(oid)["object_id"] == oid
        read = KnowledgeReadApplication(restored).search_objects("Alice Example", mode="lexical")
        assert oid in {item.object_id for item in read.results}
        minimum_read_seconds = time.perf_counter() - restore_start
        # Quarantine disposable Raw bytes; never a reference input.
        # Verify every backup-point capture member exists and passes product checks before loss.
        assert app.importer.read(bundle)
        quarantined = bundle.with_suffix(".quarantined")
        bundle.rename(quarantined)
        with pytest.raises((OSError, ValueError)) as exc:
            Application(restored).process_source_snapshot(imported["snapshot"])
        assert system_ops.integrity(restored)[
            "ok"
        ]  # SQLite integrity cannot detect lost Raw bytes.
        outputs = [
            str(p.relative_to(backup.parent)) for p in backup.parent.rglob("*") if p.is_file()
        ]
        assert "canonical.sqlite" in outputs
        assert set(outputs) <= {"canonical.sqlite", "canonical.sqlite-wal", "canonical.sqlite-shm"}
        assert not bundle.exists()
        incoming.rename(incoming.with_name("incoming.quarantined"))
        row = audit.result_receipt(receipt.receipt_id)
        with pytest.raises(ValueError, match="missing"):
            load_immutable_result_artifact(row, incoming)
        assert recovery_inventory(restored) == inventory
        observe(
            tmp_path,
            "backup-coverage",
            {
                "inventory": inventory,
                "backup_files": outputs,
                "backup_seconds": backup_seconds,
                "restore_seconds": restore_seconds,
                "db_read_lexical_seconds": minimum_read_seconds,
                "restored_digest_equal": True,
                "sqlite_integrity_ok": True,
                "raw_reuse_error": str(exc.value),
                "raw_restored": False,
                "original_result_coverage": False,
                "configuration_coverage": False,
                "complete_canonical_rpo_hours": None,
                "complete_canonical_rto_seconds": None,
                "coverage_verdict": "FAIL",
            },
        )
    finally:
        restored.close()
        repo.close()


def test_provenance_foreign_key_corruption_detected(tmp_path):
    repo = Repository(tmp_path / "provenance.sqlite")
    _build_and_stage(repo, tmp_path)
    repo.db.execute("PRAGMA foreign_keys=OFF")
    row = dict(repo.db.execute("SELECT * FROM raw_artifacts LIMIT 1").fetchone())
    row["id"] = "corrupt-raw"
    row["snapshot_id"] = "missing-snapshot"
    columns = ",".join(row)
    placeholders = ",".join("?" for _ in row)
    repo.db.execute(
        f"INSERT INTO raw_artifacts({columns}) VALUES({placeholders})", tuple(row.values())
    )
    repo.db.commit()
    report = system_ops.integrity(repo)
    assert not report["ok"] and report["foreign_key_violations"]
    observe(tmp_path, "provenance", report)
    repo.close()


def test_qdrant_unreachable_is_explicit(tmp_path):
    from qdrant_client import QdrantClient

    # Reserve a run-owned localhost port with no listener; never interrupt reference Qdrant.
    with socket.socket() as owned:
        owned.bind(("127.0.0.1", 0))
        port = owned.getsockname()[1]
        client = QdrantClient(url=f"http://127.0.0.1:{port}", timeout=1, check_compatibility=False)
        try:
            with pytest.raises(Exception) as exc:
                client.get_collections()
            observe(
                tmp_path,
                "qdrant-outage",
                {"endpoint": f"localhost:{port}", "exception": type(exc.value).__name__},
            )
        finally:
            client.close()


@pytest.mark.parametrize("path", ["../outside.sqlite", ".", "../../n03/original.sqlite"])
def test_fault_target_guard(tmp_path, path):
    root = tmp_path / ".local" / "n07" / "unique"
    with pytest.raises(ValueError):
        owned_path(root, root / path)


def test_owned_target_and_digest_determinism(tmp_path):
    root = tmp_path / ".local" / "n07" / "unique"
    assert owned_path(root, root / "case/db.sqlite").is_relative_to(root)
    repo = Repository(tmp_path / "digest.sqlite")
    assert database_digest(repo.db) == database_digest(repo.db)
    repo.close()


def complete_evidence():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return {
        "cases": {
            name: {"status": "PASS"} for names in contract["stages"].values() for name in names
        },
        "gates": dict(contract["hard_gates"]),
        **{name: {"status": "PASS"} for name in ["preflight", "post_regression", "safety"]},
    }


def test_evaluator_capability_gap_is_fail():
    e = complete_evidence()
    e["cases"]["raw_provenance_present_and_verified"]["status"] = "FAIL"
    assert evaluate(e)["overall"] == "FAIL"
    assert evaluate({})["overall"] == "BLOCKED"
    assert evaluate(complete_evidence())["overall"] == "PASS"


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("rpo_hours_max", 24, "PASS"),
        ("rpo_hours_max", 24.00001, "FAIL"),
        ("rto_hours_max", 4, "PASS"),
        ("rto_hours_max", 4.00001, "FAIL"),
        ("raw_provenance_restore_verification", False, "FAIL"),
    ],
)
def test_evaluator_frozen_boundaries(key, value, expected):
    e = complete_evidence()
    e["gates"][key] = value
    assert evaluate(e)["overall"] == expected


def test_mcp_stop_direct_read_restart(tmp_path):
    import asyncio

    from mcp import Client, StdioServerParameters

    path = tmp_path / "mcp.sqlite"
    repo = Repository(path)
    oid = repo.object_store.create_object("N07 Local Object", "class:character")
    version = repo.version_store.begin_candidate(oid, None)
    repo.version_store.accept_candidate(version)
    before = database_digest(repo.db)
    repo.close()

    async def read_once():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "sgokb", "--db", str(path), "mcp", "serve"]
        )
        async with Client(params) as client:
            result = await client.call_tool("get_object", {"object_id": oid})
            assert not result.is_error
            assert result.structured_content["data"]["object_id"] == oid

    asyncio.run(read_once())  # Context exit shuts down only this run-owned server.
    repo = Repository(path)
    assert KnowledgeReadApplication(repo).get_object(oid)["object_id"] == oid
    repo.close()
    direct = subprocess.run(
        [sys.executable, "-m", "sgokb", "--db", str(path), "object", "show", "--object", oid],
        capture_output=True,
        text=True,
    )
    # The CLI help identifies a supported read command if spelling evolves; do not weaken success.
    assert direct.returncode == 0, direct.stderr
    asyncio.run(read_once())
    repo = Repository(path)
    assert database_digest(repo.db) == before
    repo.close()
    observe(tmp_path, "mcp", {"stop_direct_read_restart": True, "canonical_unchanged": True})


def test_restored_db_r2_rebuild(tmp_path):
    from qdrant_client import QdrantClient
    from test_generation_lifecycle_qdrant_r2 import (
        FakeProvider,
        _accepted,
        _link_legacy,
        _save_legacy_embeddings,
        _space,
    )

    from sgokb.application_generation import KnowledgeSearchGenerationApplication
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    repo = Repository(tmp_path / "source.sqlite")
    _accepted(repo, "Recovery Alpha", "recovery-alpha")
    _accepted(repo, "Recovery Beta", "recovery-beta")
    if os.environ.get("N07_REAL_PROVIDER") == "1":
        from sgokb.retrieval.embedding import default_sentence_transformer_provider

        provider = default_sentence_transformer_provider(
            cache_folder=os.environ["N07_MODEL_CACHE"], local_files_only=True
        )
        assert provider.device == "cuda"
        provider.batch_size = 1
    else:
        provider = FakeProvider(_space())
    space = provider.space
    _link_legacy(repo)
    _save_legacy_embeddings(repo, provider)
    backup = tmp_path / "backups" / "canonical.sqlite"
    system_ops.create_backup(repo, backup)
    repo.close()
    target = tmp_path / "restored.sqlite"
    system_ops.restore_apply(backup, target, acknowledge_overwrite=False)
    restored = Repository(target)
    client = QdrantClient(location=":memory:")
    try:
        vector = QdrantVectorIndexAdapter(client=client, wait_for_index=False)
        app = KnowledgeSearchGenerationApplication(
            restored, embedding_provider=provider, vector_index=vector
        )
        from sgokb.application_generation import LEGACY_GENERATION_ID
        from sgokb.retrieval.vector_maintenance import KnowledgeVectorMaintenanceBuilder

        start = time.perf_counter()
        KnowledgeVectorMaintenanceBuilder(
            restored, vector, generation_id=LEGACY_GENERATION_ID
        ).rebuild(space)
        app.bootstrap_legacy()
        candidate = app.build_r2_candidate()
        app.cutover(candidate.generation_id)
        app.refresh_active_generation(candidate.generation_id)
        seconds = time.perf_counter() - start
        assert candidate.membership_count == candidate.point_count
        assert candidate.membership_count > 0
        assert_integrity(restored)
        observe(
            tmp_path,
            "rebuild",
            {
                "seconds": seconds,
                "generation_id": candidate.generation_id,
                "memberships": candidate.membership_count,
                "points": candidate.point_count,
                "runtime": "frozen Harrier CUDA"
                if os.environ.get("N07_REAL_PROVIDER")
                else "deterministic fixture",
                "note": "Small restore fixture; not reference-scale rebuild timing",
            },
        )
    finally:
        client.close()
        restored.close()


def test_process_local_network_denial_preserves_read(tmp_path):
    repo = Repository(tmp_path / "offline.sqlite")
    oid = repo.object_store.create_object("N07 Offline Object", "class:character")
    version = repo.version_store.begin_candidate(oid, None)
    repo.version_store.accept_candidate(version)
    before = database_digest(repo.db)
    with patch("socket.socket.connect", side_effect=OSError(errno.ENETUNREACH, "N07 offline")):
        assert KnowledgeReadApplication(repo).get_object(oid)["object_id"] == oid
        assert KnowledgeReadApplication(repo).search_objects("N07 Offline Object", mode="lexical")
    assert database_digest(repo.db) == before
    repo.close()


def test_harness_maps_every_frozen_case():
    from benchmark.tools.n07_failure_recovery import selections

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    required = {case for cases in contract["stages"].values() for case in cases}
    mapped = selections(contract)
    assert set(mapped) == required
    assert all(mapped.values())


def test_supporting_kill_blocked_does_not_hide_mandatory_failure():
    evidence = complete_evidence()
    evidence["cases"]["controlled_process_termination_supporting_case"]["status"] = "BLOCKED"
    assert evaluate(evidence)["overall"] == "PASS"
    evidence["cases"]["failure_after_knowledge_written"]["status"] = "FAIL"
    assert evaluate(evidence)["overall"] == "FAIL"
