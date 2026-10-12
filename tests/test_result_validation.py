import json
from pathlib import Path

from sgokb.exchange import (
    ObjectEvidencePackageBuilder,
    PackageTransferService,
    ResultReceiptService,
    ResultValidationService,
)
from sgokb.repository import Repository
from sgokb.storage import PackageExchangeAuditRepository


def _add_evidence(repository, source_id, suffix, content):
    store = repository.source_store
    locator = store.ensure_locator(source_id, "url", f"https://example.test/{suffix}")
    snapshot_id = f"snapshot-h01-{suffix}"
    store.create_snapshot(
        source_id,
        "2026-10-13T02:00:00Z",
        "test_fixture",
        observed_locator_id=locator,
        snapshot_id=snapshot_id,
    )
    artifact_id = store.add_raw_artifact(
        snapshot_id,
        "rendered_dom",
        f"fixture/{suffix}.html",
        "a" * 64,
        1,
    )
    run_id = f"run-h01-{suffix}"
    store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        [artifact_id],
        run_id=run_id,
    )
    evidence_id = f"evidence-h01-{suffix}"
    store.add_evidence(
        run_id,
        content,
        "normalized",
        evidence_id=evidence_id,
    )
    store.select_effective_snapshot(source_id, snapshot_id, reason="fixture")
    store.select_effective_run(snapshot_id, run_id, reason="fixture")
    return evidence_id, run_id


def _setup_object(repository):
    object_id = repository.object_store.create_object(
        "Alice Example",
        "class:character",
        object_id="object-h01-alice",
    )
    source_id = repository.source_store.create_source("Alice source", source_id="source-h01-alice")
    evidence_id, run_id = _add_evidence(
        repository,
        source_id,
        "main",
        "Alice Example is a fictional character used for H-01 validation tests.",
    )
    repository.source_store.associate_object(
        source_id,
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    return object_id, source_id, evidence_id, run_id


def _valid_result(repository, manifest):
    target = manifest["target"]
    evidence_id = manifest["evidence"]["included_evidence_ids"][0]
    facets = repository.semantic_store.facets_for_classes(
        (target["primary_class_id"], *target["additional_class_ids"])
    )
    return {
        "schema_version": manifest["binding"]["expected_result_schema_version"],
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
        },
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
            "generator_kind": "interactive_ai",
            "application": "ChatGPT",
            "generated_at": "2026-10-13T02:05:00Z",
        },
        "knowledge": {
            "default_language": "ja",
            "summary": [
                {
                    "local_key": "summary-1",
                    "text": "Alice Exampleについての根拠付き要約。",
                    "derivation_kind": "direct_statement",
                    "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
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


def _build_and_stage(repository, tmp_path):
    object_id, source_id, evidence_id, run_id = _setup_object(repository)
    built = ObjectEvidencePackageBuilder(repository).build(
        object_id,
        build_root=tmp_path / "build",
        semantic=False,
    )
    transfer = PackageTransferService()
    staged = transfer.stage_from_directory(built.path, tmp_path / "staging")
    manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
    audit = PackageExchangeAuditRepository(repository.db)
    audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
    exported = transfer.export(staged.path, tmp_path / "DriveSync")
    audit.record_export(
        exported.package_id,
        exported.manifest_sha256,
        exported.destination_root,
        exported.path,
        acknowledged_review=False,
        already_present=exported.already_present,
    )
    return audit, manifest, object_id, source_id, evidence_id, run_id


def _receive(repository, audit, manifest, tmp_path, result):
    path = tmp_path / "result.json"
    if isinstance(result, bytes):
        path.write_bytes(result)
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    incoming = tmp_path / "incoming"
    receipt = ResultReceiptService(audit).receive(path, manifest["package_id"], incoming)
    service = ResultValidationService(repository, audit)
    return service, receipt, incoming


def _codes(report):
    return {finding.code for finding in report.findings}


def _stages(report):
    return {finding.stage for finding in report.findings}


def test_valid_receipt_reaches_valid_without_creating_knowledge_version(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)

        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "valid"
        assert report.findings == ()
        assert audit.result_receipt(receipt.receipt_id)["validation_state"] == "valid"
        assert repository.version_store.current_version_id(object_id) is None
        assert repository.one("SELECT count(*) AS n FROM object_versions")["n"] == 0
        assert service.validate_receipt(receipt.receipt_id, incoming_root=incoming) == report
    finally:
        repository.close()


def test_malformed_json_is_formally_invalid_at_artifact_syntax_layer(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        service, receipt, incoming = _receive(
            repository, audit, manifest, tmp_path, b"{not valid json"
        )
        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "invalid"
        assert "invalid_json" in _codes(report)
        assert _stages(report) == {"artifact_syntax"}
    finally:
        repository.close()


def test_static_schema_rejects_unknown_operation_field(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["execute"] = "do-not-run"
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)

        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
        assert report.validation_state == "invalid"
        assert _stages(report) == {"static_schema"}
        assert "schema" in _codes(report)
    finally:
        repository.close()


def test_package_binding_mismatch_is_invalid_not_rebound(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["binding"]["manifest_sha256"] = "b" * 64
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)

        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
        assert report.validation_state == "invalid"
        assert "manifest_sha256_mismatch" in _codes(report)
        assert "binding_precondition" in _stages(report)
    finally:
        repository.close()


def test_stale_base_version_blocks_validation(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        object_id, source_id, evidence_id, run_id = _setup_object(repository)
        first = repository.version_store.begin_candidate(object_id, None)
        repository.version_store.accept_candidate(first)

        built = ObjectEvidencePackageBuilder(repository).build(
            object_id, build_root=tmp_path / "build", semantic=False
        )
        transfer = PackageTransferService()
        staged = transfer.stage_from_directory(built.path, tmp_path / "staging")
        manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
        audit = PackageExchangeAuditRepository(repository.db)
        audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
        exported = transfer.export(staged.path, tmp_path / "DriveSync")
        audit.record_export(
            exported.package_id,
            exported.manifest_sha256,
            exported.destination_root,
            exported.path,
            acknowledged_review=False,
            already_present=False,
        )
        result = _valid_result(repository, manifest)
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)

        second = repository.version_store.begin_candidate(object_id, first)
        repository.version_store.accept_candidate(second)
        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "invalid"
        assert "stale_base_version" in _codes(report)
        assert repository.version_store.current_version_id(object_id) == second
    finally:
        repository.close()


def test_unknown_relation_endpoint_is_referential_error_not_invented_object(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        relation_type = repository.object_store.register_relation_type("knows_h01", "knows H-01")
        audit, manifest, object_id, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["knowledge"]["relations"] = [
            {
                "local_key": "relation-1",
                "subject_object_id": object_id,
                "relation_type_id": relation_type,
                "object_object_id": "object-does-not-exist",
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "invalid"
        assert "relation_object_missing" in _codes(report)
        assert "referential" in _stages(report)
        assert repository.one("SELECT 1 AS n FROM objects WHERE id='object-does-not-exist'") is None
    finally:
        repository.close()


def test_canonical_evidence_outside_package_is_grounding_error(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        other_source = repository.source_store.create_source("Other", source_id="source-h01-other")
        other_evidence, _ = _add_evidence(
            repository, other_source, "outside", "Canonical but not packaged Evidence."
        )
        result = _valid_result(repository, manifest)
        result["knowledge"]["summary"][0]["evidence"] = [
            {"evidence_id": other_evidence, "role": "supports"}
        ]
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "invalid"
        assert "evidence_outside_package" in _codes(report)
        assert "grounding_provenance" in _stages(report)
    finally:
        repository.close()


def test_broken_canonical_provenance_is_detected(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, evidence_id, run_id = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
        with repository.db:
            repository.db.execute(
                "DELETE FROM normalization_run_artifacts WHERE run_id=?", (run_id,)
            )

        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
        assert report.validation_state == "invalid"
        assert "evidence_provenance_invalid" in _codes(report)
        assert evidence_id in json.dumps(report.to_dict(), ensure_ascii=False)
    finally:
        repository.close()


def test_invalid_temporal_interval_is_domain_contract_error(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["knowledge"]["summary"][0]["temporal_scope"] = {
            "valid_from": "2026-10-14",
            "valid_to": "2026-10-13",
        }
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "invalid"
        assert "invalid_temporal_interval" in _codes(report)
        assert "domain_contract" in _stages(report)
    finally:
        repository.close()


def test_registry_proposal_can_validate_but_remains_review_required(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["registry_proposals"] = [
            {
                "local_key": "proposal-1",
                "proposal_kind": "object_alias",
                "rationale": "The source uses another stable alias.",
                "payload": {"value": "Alice Alt"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)

        assert report.validation_state == "valid"
        assert "registry_proposal_requires_review" in _codes(report)
        assert all(
            finding.severity == "review"
            for finding in report.findings
            if finding.code == "registry_proposal_requires_review"
        )
        assert repository.one("SELECT count(*) AS n FROM object_aliases")["n"] == 0
    finally:
        repository.close()


def test_received_artifact_hash_change_is_validation_error(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
        Path(receipt.path).write_text("{}\n", encoding="utf-8")

        report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
        assert report.validation_state == "error"
        assert {"receipt_byte_count_mismatch", "receipt_sha256_mismatch"}.intersection(
            _codes(report)
        )
    finally:
        repository.close()
