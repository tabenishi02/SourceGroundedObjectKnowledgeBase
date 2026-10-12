import json
import sqlite3
from pathlib import Path

import pytest
from test_result_validation import _build_and_stage, _receive, _valid_result

from sgokb.exchange import (
    ObjectEvidencePackageBuilder,
    ObjectVersionImportService,
    PackageTransferService,
)
from sgokb.repository import Repository


def _validate(repository, audit, manifest, tmp_path, result):
    service, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)
    report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
    assert report.validation_state == "valid"
    return receipt, incoming, report


def _import(repository, audit, receipt, incoming, *, acknowledge_review=False, failure_hook=None):
    return ObjectVersionImportService(
        repository,
        audit,
        failure_hook=failure_hook,
    ).import_receipt(
        receipt.receipt_id,
        incoming_root=incoming,
        acknowledge_review=acknowledge_review,
    )


def test_valid_result_imports_full_knowledge_and_promotes_atomically(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        repository.semantic_store.register_attribute_definition(
            "test_power", "Test Power", "integer", attribute_id="attribute:test_power"
        )
        repository.object_store.register_relation_type(
            "knows", "knows", relation_type_id="relation:knows"
        )
        relation_target = repository.object_store.create_object(
            "Bob Example", "class:character", object_id="object-h02-bob"
        )
        audit, manifest, object_id, source_id, evidence_id, _ = _build_and_stage(
            repository, tmp_path
        )
        result = _valid_result(repository, manifest)
        result["knowledge"]["summary"][0]["temporal_scope"] = {"as_of": "2026-10-13"}
        facet = result["knowledge"]["facets"][0]
        facet["status"] = "content"
        facet["statements"] = [
            {
                "local_key": "facet-view-1",
                "text": "Source attributes a view to Alice.",
                "derivation_kind": "reported_view",
                "attribution": {"kind": "source", "source_id": source_id},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        result["knowledge"]["attributes"] = [
            {
                "local_key": "power-1",
                "attribute_id": "attribute:test_power",
                "status": "known",
                "value": 7,
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        result["knowledge"]["relations"] = [
            {
                "local_key": "knows-1",
                "subject_object_id": object_id,
                "relation_type_id": "relation:knows",
                "object_object_id": relation_target,
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)

        imported = _import(repository, audit, receipt, incoming)

        assert imported.duplicate is False
        assert repository.version_store.current_version_id(object_id) == imported.version_id
        version = repository.version_store.version_by_id(imported.version_id)
        assert version.state.value == "accepted"
        assert version.base_version_id is None
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 1
        assert repository.one("SELECT count(*) n FROM knowledge_statements")["n"] == 2
        assert repository.one("SELECT count(*) n FROM object_version_attributes")["n"] == 1
        assert repository.one("SELECT count(*) n FROM object_relations")["n"] == 1
        assert repository.one("SELECT count(*) n FROM evidence_links")["n"] == 4
        attribution = repository.one("SELECT * FROM knowledge_statement_attributions")
        assert attribution["kind"] == "source"
        assert attribution["source_id"] == source_id
        metadata = repository.one(
            "SELECT * FROM object_version_result_metadata WHERE version_id=?",
            (imported.version_id,),
        )
        assert metadata["default_language"] == "ja"
        assert json.loads(metadata["registry_proposals_json"]) == []
        audit_row = repository.one(
            "SELECT * FROM object_result_imports WHERE id=?", (imported.import_id,)
        )
        assert audit_row["receipt_id"] == receipt.receipt_id
        assert audit_row["package_id"] == manifest["package_id"]
        assert audit_row["result_sha256"] == receipt.result_sha256
        receipt_row = audit.result_receipt(receipt.receipt_id)
        assert audit_row["result_storage_ref"] == receipt_row["storage_ref"]
        assert audit_row["validation_completed_at"] == receipt_row["validation_completed_at"]
        assert (
            json.loads(audit_row["validation_findings_json"]) == receipt_row["validation_findings"]
        )
        states = repository.version_store.derived_states(object_id)
        assert {state.kind for state in states} == {
            "search_representation",
            "embedding",
            "vector_index",
            "rendering",
        }
        assert {state.status.value for state in states} == {"pending"}

        snapshot = repository.version_store.current_version_id(object_id)
        assert snapshot == imported.version_id
        current = repository.one(
            "SELECT count(*) n FROM object_version_lifecycle WHERE state='candidate'"
        )
        assert current["n"] == 0

        package = ObjectEvidencePackageBuilder(repository).build(
            object_id, build_root=tmp_path / "post-import-build", semantic=False
        )
        current_object = json.loads(
            Path(package.path, "current_object.json").read_text(encoding="utf-8")
        )
        assert current_object["knowledge"]["default_language"] == "ja"
        reported = [
            item
            for facet_item in current_object["knowledge"]["facets"]
            for item in facet_item["statements"]
            if item["derivation_kind"] == "reported_view"
        ]
        assert reported[0]["attribution"] == {"kind": "source", "source_id": source_id}
    finally:
        repository.close()


def test_import_requires_successful_h01_validation(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        _, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)

        with pytest.raises(ValueError, match="H-01"):
            _import(repository, audit, receipt, incoming)

        assert repository.version_store.current_version_id(object_id) is None
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 0
    finally:
        repository.close()


def test_review_required_result_needs_ack_and_does_not_apply_registry_proposal(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["result_status"] = "partial"
        result["gaps"] = [
            {
                "local_key": "gap-1",
                "kind": "not_analyzed",
                "description": "Some scope was not analyzed.",
                "evidence": [],
            }
        ]
        result["registry_proposals"] = [
            {
                "local_key": "proposal-1",
                "proposal_kind": "object_alias",
                "rationale": "Evidence suggests an alias.",
                "payload": {"value": "Alicia Example"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        receipt, incoming, report = _validate(repository, audit, manifest, tmp_path, result)
        assert any(item.severity == "review" for item in report.findings)

        with pytest.raises(ValueError, match="review acknowledgement"):
            _import(repository, audit, receipt, incoming)
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 0

        imported = _import(repository, audit, receipt, incoming, acknowledge_review=True)
        assert imported.review_acknowledged is True
        aliases = repository.rows(
            "SELECT value FROM object_aliases WHERE object_id=?", (object_id,)
        )
        assert "Alicia Example" not in {row["value"] for row in aliases}
        metadata = repository.one(
            "SELECT registry_proposals_json,gaps_json FROM object_version_result_metadata "
            "WHERE version_id=?",
            (imported.version_id,),
        )
        assert json.loads(metadata["registry_proposals_json"])[0]["payload"]["value"] == (
            "Alicia Example"
        )
        assert json.loads(metadata["gaps_json"])[0]["kind"] == "not_analyzed"
    finally:
        repository.close()


def test_stale_after_validation_is_blocked_without_partial_candidate(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)

        intervening = repository.version_store.begin_candidate(object_id, None)
        repository.version_store.accept_candidate(intervening)

        with pytest.raises(ValueError, match="no longer current"):
            _import(repository, audit, receipt, incoming)

        assert repository.version_store.current_version_id(object_id) == intervening
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 1
        assert repository.one("SELECT count(*) n FROM object_result_imports")["n"] == 0
        assert (
            repository.one(
                "SELECT count(*) n FROM object_version_lifecycle WHERE state='candidate'"
            )["n"]
            == 0
        )
    finally:
        repository.close()


def test_duplicate_import_returns_existing_version_without_second_commit(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)

        first = _import(repository, audit, receipt, incoming)
        second = _import(repository, audit, receipt, incoming)

        assert first.version_id == second.version_id
        assert second.duplicate is True
        assert repository.version_store.current_version_id(object_id) == first.version_id
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 1
        assert repository.one("SELECT count(*) n FROM object_result_imports")["n"] == 1
    finally:
        repository.close()


def test_import_failure_rolls_back_candidate_content_and_audit_then_retry_succeeds(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)

        def fail(step):
            if step == "accepted":
                raise RuntimeError("synthetic import interruption")

        with pytest.raises(RuntimeError, match="synthetic"):
            _import(repository, audit, receipt, incoming, failure_hook=fail)

        assert repository.version_store.current_version_id(object_id) is None
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 0
        assert repository.one("SELECT count(*) n FROM object_result_imports")["n"] == 0
        assert repository.one("SELECT count(*) n FROM knowledge_statements")["n"] == 0

        retried = _import(repository, audit, receipt, incoming)
        assert retried.duplicate is False
        assert repository.version_store.current_version_id(object_id) == retried.version_id
    finally:
        repository.close()


def test_import_rechecks_immutable_result_artifact_hash(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)
        receipt_row = audit.result_receipt(receipt.receipt_id)
        Path(incoming, receipt_row["storage_ref"]).write_text("{}\n", encoding="utf-8")

        with pytest.raises(ValueError, match="byte count|SHA-256"):
            _import(repository, audit, receipt, incoming)

        assert repository.version_store.current_version_id(object_id) is None
        assert repository.one("SELECT count(*) n FROM object_versions")["n"] == 0
    finally:
        repository.close()


def test_second_import_preserves_previous_accepted_version(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest1, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result1 = _valid_result(repository, manifest1)
        receipt1, incoming1, _ = _validate(repository, audit, manifest1, tmp_path, result1)
        first = _import(repository, audit, receipt1, incoming1)

        built2 = ObjectEvidencePackageBuilder(repository).build(
            object_id, build_root=tmp_path / "build2", semantic=False
        )
        transfer = PackageTransferService()
        staged2 = transfer.stage_from_directory(built2.path, tmp_path / "staging2")
        manifest2 = json.loads(Path(staged2.path, "manifest.json").read_text(encoding="utf-8"))
        audit.record_staged(manifest2, staged2.path, staged2.preflight.to_dict())
        exported2 = transfer.export(staged2.path, tmp_path / "DriveSync2")
        audit.record_export(
            exported2.package_id,
            exported2.manifest_sha256,
            exported2.destination_root,
            exported2.path,
            acknowledged_review=False,
            already_present=exported2.already_present,
        )
        result2 = _valid_result(repository, manifest2)
        result2["knowledge"]["summary"][0]["text"] = "Updated grounded summary."
        receipt2, incoming2, _ = _validate(repository, audit, manifest2, tmp_path, result2)
        second = _import(repository, audit, receipt2, incoming2)

        assert second.version_id != first.version_id
        assert second.base_version_id == first.version_id
        assert repository.version_store.current_version_id(object_id) == second.version_id
        versions = repository.version_store.versions_for_object(object_id)
        assert len(versions) == 2
        assert [item.state.value for item in versions] == ["accepted", "accepted"]
        old_statement = repository.one(
            "SELECT text FROM knowledge_statements WHERE version_id=?", (first.version_id,)
        )
        assert old_statement["text"] == "Alice Exampleについての根拠付き要約。"
        new_statement = repository.one(
            "SELECT text FROM knowledge_statements WHERE version_id=?", (second.version_id,)
        )
        assert new_statement["text"] == "Updated grounded summary."
    finally:
        repository.close()


def test_db_blocks_accepting_reported_view_without_attribution(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, _, object_id, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        version_id = repository.version_store.begin_candidate(object_id, None)
        facet_id = repository.semantic_store.facets_for_classes(("class:character",))[0].facet_id
        role_id = repository.one(
            "SELECT id FROM evidence_roles WHERE key='supports' AND status='active'"
        )["id"]
        with repository.db:
            repository.db.execute(
                "INSERT INTO object_version_facets VALUES(?,?,?,?)",
                (version_id, facet_id, "content", "2026-10-13T04:00:00Z"),
            )
            repository.db.execute(
                """INSERT INTO knowledge_statements
                   (id,version_id,facet_id,local_key,text,derivation_kind,language,
                    temporal_scope_id,created_at)
                   VALUES(?,?,?,?,?,'reported_view',NULL,NULL,?)""",
                (
                    "statement-without-attribution",
                    version_id,
                    facet_id,
                    "reported-view-1",
                    "A reported view without attribution.",
                    "2026-10-13T04:00:00Z",
                ),
            )
            repository.db.execute(
                """INSERT INTO evidence_links
                   (id,version_id,target_kind,target_id,evidence_id,role_id,origin_kind,
                    origin_ref,created_at)
                   VALUES(?,?,?,?,?,?,'manual',NULL,?)""",
                (
                    "evidence-link-without-attribution",
                    version_id,
                    "statement",
                    "statement-without-attribution",
                    evidence_id,
                    role_id,
                    "2026-10-13T04:00:00Z",
                ),
            )

        with pytest.raises(sqlite3.IntegrityError, match="attribution"):
            repository.version_store.accept_candidate(version_id)

        assert repository.version_store.current_version_id(object_id) is None
        assert repository.version_store.version_by_id(version_id).state.value == "candidate"
    finally:
        repository.close()
