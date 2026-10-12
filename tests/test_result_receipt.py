import json
from pathlib import Path

import pytest

from sgokb.exchange.result_receipt import ResultReceiptService
from sgokb.repository import Repository
from sgokb.storage import PackageExchangeAuditRepository


PACKAGE_ID = "pkg_123e4567-e89b-42d3-a456-426614174000"
MANIFEST_HASH = "a" * 64


def _package(tmp_path, *, exported=True):
    repository = Repository(tmp_path / "sgokb.sqlite")
    audit = PackageExchangeAuditRepository(repository.db)
    staged = tmp_path / "staging" / PACKAGE_ID
    staged.mkdir(parents=True)
    manifest = {
        "schema_version": "sgokb.object-evidence-package/1.0",
        "package_id": PACKAGE_ID,
        "created_at": "2026-10-13T01:00:00Z",
        "extracted_at": "2026-10-13T00:59:00Z",
        "target": {
            "object_id": "object-1",
            "primary_class_id": "class:character",
            "additional_class_ids": ["class:fictional_entity"],
        },
        "binding": {
            "base_version_id": None,
            "expected_result_schema_version": "sgokb.object-result/1.0",
            "instructions_version": "sgokb.object-analysis/1.0",
        },
        "evidence": {"included_evidence_ids": ["evidence-1"]},
        "integrity": {"manifest_sha256": MANIFEST_HASH},
    }
    (staged / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    audit.record_staged(manifest, str(staged), {"disposition": "allow"})
    if exported:
        audit.record_export(
            PACKAGE_ID,
            MANIFEST_HASH,
            str(tmp_path / "DriveSync"),
            str(tmp_path / "DriveSync" / PACKAGE_ID),
            acknowledged_review=False,
            already_present=False,
        )
    return repository, audit, manifest


def _result(manifest, **overrides):
    value = {
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
    for key, replacement in overrides.items():
        value[key] = replacement
    return value


def _write_result(path: Path, value) -> bytes:
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def test_detect_lists_manual_drop_without_modifying_it(tmp_path):
    repository, audit, manifest = _package(tmp_path)
    try:
        incoming = tmp_path / "incoming"
        path = incoming / "drop" / PACKAGE_ID / "result.json"
        _write_result(path, _result(manifest))

        detected = ResultReceiptService(audit).detect(incoming)
        assert len(detected) == 1
        assert detected[0].package_hint == PACKAGE_ID
        assert detected[0].package_known is True
        assert detected[0].already_received is False
        assert path.is_file()
        assert audit.result_receipts(PACKAGE_ID) == ()
    finally:
        repository.close()


def test_receive_preserves_exact_bytes_and_requests_validation(tmp_path):
    repository, audit, manifest = _package(tmp_path)
    try:
        source = tmp_path / "result.json"
        raw = _write_result(source, _result(manifest))
        receipt = ResultReceiptService(audit).receive(
            source, PACKAGE_ID, tmp_path / "incoming"
        )

        assert receipt.intake_state == "ready_for_validation"
        assert receipt.validation_state == "pending"
        assert receipt.intake_findings == ()
        assert Path(receipt.path).read_bytes() == raw
        stored = audit.result_receipt(receipt.receipt_id)
        assert stored["result_sha256"] == receipt.result_sha256
        assert stored["validation_state"] == "pending"
        assert stored["storage_ref"].endswith(f"/{receipt.receipt_id}/result.json")
        assert repository.one("SELECT count(*) AS n FROM object_versions")["n"] == 0
    finally:
        repository.close()


def test_receive_keeps_malformed_json_for_h01_instead_of_importing_it(tmp_path):
    repository, audit, _ = _package(tmp_path)
    try:
        source = tmp_path / "result.json"
        source.write_text("{not json", encoding="utf-8")
        receipt = ResultReceiptService(audit).receive(
            source, PACKAGE_ID, tmp_path / "incoming"
        )

        assert receipt.intake_state == "needs_review"
        assert "invalid_json" in receipt.intake_findings
        assert receipt.validation_state == "pending"
        assert Path(receipt.path).read_text(encoding="utf-8") == "{not json"
    finally:
        repository.close()


def test_binding_mismatch_is_routing_finding_not_authoritative_validation(tmp_path):
    repository, audit, manifest = _package(tmp_path)
    try:
        value = _result(manifest)
        value["binding"]["manifest_sha256"] = "b" * 64
        source = tmp_path / "result.json"
        _write_result(source, value)
        receipt = ResultReceiptService(audit).receive(
            source, PACKAGE_ID, tmp_path / "incoming"
        )

        assert receipt.intake_state == "needs_review"
        assert "routing_mismatch:manifest_sha256" in receipt.intake_findings
        assert receipt.validation_state == "pending"
    finally:
        repository.close()


def test_missing_export_audit_is_visible_but_result_is_preserved(tmp_path):
    repository, audit, manifest = _package(tmp_path, exported=False)
    try:
        source = tmp_path / "result.json"
        _write_result(source, _result(manifest))
        receipt = ResultReceiptService(audit).receive(
            source, PACKAGE_ID, tmp_path / "incoming"
        )

        assert receipt.intake_state == "needs_review"
        assert "package_has_no_export_audit" in receipt.intake_findings
        assert Path(receipt.path).is_file()
    finally:
        repository.close()


def test_same_package_and_same_bytes_are_idempotent(tmp_path):
    repository, audit, manifest = _package(tmp_path)
    try:
        source = tmp_path / "result.json"
        _write_result(source, _result(manifest))
        service = ResultReceiptService(audit)
        first = service.receive(source, PACKAGE_ID, tmp_path / "incoming")
        second = service.receive(source, PACKAGE_ID, tmp_path / "incoming")

        assert second.already_received is True
        assert second.receipt_id == first.receipt_id
        assert len(audit.result_receipts(PACKAGE_ID)) == 1
    finally:
        repository.close()


def test_different_result_attempts_for_same_package_are_retained_separately(tmp_path):
    repository, audit, manifest = _package(tmp_path)
    try:
        source = tmp_path / "result.json"
        first_value = _result(manifest)
        _write_result(source, first_value)
        service = ResultReceiptService(audit)
        first = service.receive(source, PACKAGE_ID, tmp_path / "incoming")

        second_value = _result(manifest)
        second_value["result_status"] = "partial"
        _write_result(source, second_value)
        second = service.receive(source, PACKAGE_ID, tmp_path / "incoming")

        assert first.receipt_id != second.receipt_id
        assert first.result_sha256 != second.result_sha256
        assert Path(first.path).is_file()
        assert Path(second.path).is_file()
        assert len(audit.result_receipts(PACKAGE_ID)) == 2
    finally:
        repository.close()


def test_only_exact_result_json_is_standard_receipt_artifact(tmp_path):
    repository, audit, manifest = _package(tmp_path)
    try:
        source = tmp_path / "result.md"
        _write_result(source, _result(manifest))
        with pytest.raises(ValueError, match="named result.json"):
            ResultReceiptService(audit).receive(
                source, PACKAGE_ID, tmp_path / "incoming"
            )
    finally:
        repository.close()


def test_unknown_package_is_rejected_before_result_is_copied(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit = PackageExchangeAuditRepository(repository.db)
        source = tmp_path / "result.json"
        source.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match="Unknown Package ID"):
            ResultReceiptService(audit).receive(
                source, PACKAGE_ID, tmp_path / "incoming"
            )
        assert not (tmp_path / "incoming" / "received").exists()
    finally:
        repository.close()
