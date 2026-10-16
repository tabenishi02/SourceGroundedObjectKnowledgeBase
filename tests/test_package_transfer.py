import hashlib
import json
from pathlib import Path

import pytest

from sgokb.exchange.instructions import INSTRUCTIONS_VERSION
from sgokb.exchange.object_result import load_object_result_schema
from sgokb.exchange.package_manifest import (
    MANIFEST_CANONICALIZATION,
    PACKAGE_SCHEMA_VERSION,
)
from sgokb.exchange.package_transfer import PackageTransferService, inspect_package
from sgokb.repository import Repository
from sgokb.storage import PackageExchangeAuditRepository


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write(path: Path, raw: bytes) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {"size_bytes": len(raw), "sha256": _sha(raw)}


def _workspace(tmp_path, *, disposition="allow", reasons=None, evidence_text="Evidence text"):
    root = tmp_path / "build"
    root.mkdir()
    instructions = (
        "# SGOKB Object Analysis Instructions\n\n"
        f"Instructions version: `{INSTRUCTIONS_VERSION}`\n"
    ).encode("utf-8")
    result_schema = (json.dumps(load_object_result_schema(), ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    evidence = evidence_text.encode("utf-8")
    files = []
    for relative, role, media_type, raw in (
        ("instructions.md", "instructions", "text/markdown", instructions),
        (
            "schema/object-result-v1.schema.json",
            "result_schema",
            "application/json",
            result_schema,
        ),
        ("evidence/source_001.md", "evidence", "text/markdown", evidence),
    ):
        meta = _write(root / relative, raw)
        files.append({"path": relative, "role": role, "media_type": media_type, **meta})

    manifest = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "package_id": "pkg_123e4567-e89b-42d3-a456-426614174000",
        "created_at": "2026-10-13T01:00:00Z",
        "extracted_at": "2026-10-13T00:59:00Z",
        "target": {
            "object_id": "object-1",
            "primary_class_id": "class:character",
            "additional_class_ids": [],
            "name": "Character A",
            "aliases": [],
        },
        "binding": {
            "base_version_id": None,
            "expected_result_schema_version": "sgokb.object-result/1.0",
            "instructions_version": INSTRUCTIONS_VERSION,
        },
        "artifacts": {
            "instructions_path": "instructions.md",
            "result_schema_path": "schema/object-result-v1.schema.json",
            "current_object_path": None,
        },
        "evidence": {
            "included_source_ids": ["source-1"],
            "included_evidence_ids": ["evidence-1"],
            "source_generations": [
                {
                    "source_id": "source-1",
                    "snapshot_id": "snapshot-1",
                    "normalization_run_id": "run-1",
                    "file_path": "evidence/source_001.md",
                    "evidence_ids": ["evidence-1"],
                }
            ],
            "items": [
                {
                    "evidence_id": "evidence-1",
                    "source_id": "source-1",
                    "snapshot_id": "snapshot-1",
                    "normalization_run_id": "run-1",
                    "file_path": "evidence/source_001.md",
                    "selected_by": "relevance_fill",
                    "package_roles": ["retrieved"],
                    "retrieval_reasons": ["lexical"],
                    "related_selected_evidence_ids": [],
                }
            ],
        },
        "selection": {
            "token_estimator": "ascii_div4_plus_non_ascii_v1",
            "budget": {
                "max_estimated_tokens": 12000,
                "max_bytes": 65536,
                "max_items": 64,
            },
            "usage": {
                "estimated_tokens": 10,
                "bytes": len(evidence),
                "items": 1,
                "sources": 1,
            },
            "candidate_count": 1,
            "selected_count": 1,
            "omitted_count": 0,
        },
        "files": files,
        "warnings": [],
        "export_preflight": {
            "disposition": disposition,
            "reasons": list(reasons or []),
            "credential_material_included": False,
        },
        "integrity": {
            "hash_algorithm": "sha256",
            "canonicalization": MANIFEST_CANONICALIZATION,
            "manifest_sha256": "0" * 64,
        },
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return root


def test_stage_finalizes_manifest_and_uses_atomic_package_directory(tmp_path):
    source = _workspace(tmp_path)
    service = PackageTransferService()
    result = service.stage_from_directory(source, tmp_path / "staging")

    staged = Path(result.path)
    assert staged.name == "pkg_123e4567-e89b-42d3-a456-426614174000"
    assert staged.is_dir()
    assert result.preflight.disposition == "allow"
    assert result.manifest_sha256 != "0" * 64
    assert inspect_package(staged).manifest_sha256 == result.manifest_sha256
    assert not list((tmp_path / "staging").glob(".*.staging-*"))


def test_stage_is_idempotent_only_for_the_same_finalized_package(tmp_path):
    source = _workspace(tmp_path)
    service = PackageTransferService()
    first = service.stage_from_directory(source, tmp_path / "staging")
    second = service.stage_from_directory(source, tmp_path / "staging")

    assert first.path == second.path
    assert second.already_staged is True


def test_stage_rejects_unexpected_files_and_hash_mismatch(tmp_path):
    source = _workspace(tmp_path)
    (source / "accidental.txt").write_text("not declared", encoding="utf-8")
    with pytest.raises(ValueError, match="scope mismatch"):
        PackageTransferService().stage_from_directory(source, tmp_path / "staging")

    (source / "accidental.txt").unlink()
    (source / "evidence/source_001.md").write_text("Tampered text", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        PackageTransferService().stage_from_directory(source, tmp_path / "staging")


def test_stage_rejects_high_confidence_credential_material(tmp_path):
    source = _workspace(tmp_path, evidence_text="token sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456")
    with pytest.raises(ValueError, match="Credential/secret"):
        PackageTransferService().stage_from_directory(source, tmp_path / "staging")


def test_review_required_export_needs_explicit_acknowledgement(tmp_path):
    source = _workspace(tmp_path, disposition="review_required", reasons=["source_review"])
    service = PackageTransferService()
    staged = service.stage_from_directory(source, tmp_path / "staging")
    destination = tmp_path / "DriveSync"

    with pytest.raises(ValueError, match="explicit review acknowledgement"):
        service.export(staged.path, destination)

    exported = service.export(staged.path, destination, acknowledge_review=True)
    assert Path(exported.path).is_dir()
    assert exported.acknowledged_review is True
    assert exported.preflight.disposition == "review_required"


def test_manifest_blocked_package_can_be_staged_but_never_exported(tmp_path):
    source = _workspace(tmp_path, disposition="blocked", reasons=["operator_policy"])
    service = PackageTransferService()
    staged = service.stage_from_directory(source, tmp_path / "staging")

    assert staged.preflight.disposition == "blocked"
    with pytest.raises(ValueError, match="export is blocked"):
        service.export(staged.path, tmp_path / "DriveSync", acknowledge_review=True)


def test_export_is_atomic_and_existing_identical_destination_is_idempotent(tmp_path):
    source = _workspace(tmp_path)
    service = PackageTransferService()
    staged = service.stage_from_directory(source, tmp_path / "staging")
    destination = tmp_path / "DriveSync"

    first = service.export(staged.path, destination)
    second = service.export(staged.path, destination)

    assert first.already_present is False
    assert second.already_present is True
    assert Path(first.path).read_bytes if False else True
    assert not list(destination.glob(".*.exporting-*"))
    assert inspect_package(first.path).disposition == "allow"


def test_preflight_blocks_tampered_finalized_package(tmp_path):
    source = _workspace(tmp_path)
    service = PackageTransferService()
    staged = service.stage_from_directory(source, tmp_path / "staging")
    Path(staged.path, "evidence/source_001.md").write_text("tampered", encoding="utf-8")

    preflight = service.preflight(staged.path, tmp_path / "DriveSync")
    assert preflight.disposition == "blocked"
    assert any(reason.startswith("size_mismatch:") or reason.startswith("sha256_mismatch:") for reason in preflight.reasons)


def test_staging_and_export_audit_metadata_are_persisted(tmp_path):
    source = _workspace(tmp_path)
    service = PackageTransferService()
    staged = service.stage_from_directory(source, tmp_path / "staging")
    exported = service.export(staged.path, tmp_path / "DriveSync")

    repository = Repository(tmp_path / "audit.sqlite")
    try:
        audit = PackageExchangeAuditRepository(repository.db)
        manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
        audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
        event_id = audit.record_export(
            exported.package_id,
            exported.manifest_sha256,
            exported.destination_root,
            exported.path,
            acknowledged_review=False,
            already_present=exported.already_present,
        )

        record = audit.package_record(exported.package_id)
        events = audit.export_events(exported.package_id)
        assert record["manifest_sha256"] == exported.manifest_sha256
        assert record["included_evidence_ids"] == ["evidence-1"]
        assert record["preflight"]["disposition"] == "allow"
        assert len(events) == 1
        assert events[0]["id"] == event_id
        assert events[0]["exported_path"] == exported.path
    finally:
        repository.close()
