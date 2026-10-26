from test_result_validation import _build_and_stage, _receive, _valid_result

from sgokb.application_read import KnowledgeReadApplication
from sgokb.exchange import ObjectVersionImportService
from sgokb.repository import Repository


def _import_grounded_relation(repo, tmp_path):
    repo.object_store.register_relation_type(
        "protagonist_of_work",
        "作品の主人公",
        relation_type_id="relation:protagonist_of_work",
    )
    target = repo.object_store.create_object("Target Work", "class:work")
    audit, manifest, subject, _, evidence_id, _ = _build_and_stage(repo, tmp_path)
    result = _valid_result(repo, manifest)
    result["knowledge"]["relations"] = [
        {
            "local_key": "relation.protagonist_of_work",
            "subject_object_id": subject,
            "relation_type_id": "relation:protagonist_of_work",
            "object_object_id": target,
            "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
        }
    ]

    service, receipt, incoming = _receive(repo, audit, manifest, tmp_path, result)
    report = service.validate_receipt(receipt.receipt_id, incoming_root=incoming)
    assert report.validation_state == "valid"
    imported = ObjectVersionImportService(repo, audit).import_receipt(
        receipt.receipt_id,
        incoming_root=incoming,
    )
    return subject, target, evidence_id, imported.version_id


def test_current_relation_graph_is_visible_from_both_endpoints_without_target_version(tmp_path):
    repo = Repository(tmp_path / "k03-relation-traversal.sqlite")
    try:
        subject, target, evidence_id, version_1 = _import_grounded_relation(repo, tmp_path)
        app = KnowledgeReadApplication(repo)

        outgoing = app.get_object_relations(subject)
        incoming = app.get_object_relations(target)

        assert outgoing["scope"] == "current_relation_graph"
        assert outgoing["object_current_version_id"] == version_1
        assert outgoing["resolved_version_id"] == version_1
        assert outgoing["is_current"] is True
        assert len(outgoing["relations"]) == 1
        assert outgoing["relations"][0]["perspective"] == "outgoing"

        assert incoming["scope"] == "current_relation_graph"
        assert incoming["object_current_version_id"] is None
        assert incoming["resolved_version_id"] is None
        assert incoming["is_current"] is True
        assert len(incoming["relations"]) == 1

        relation = incoming["relations"][0]
        assert relation["perspective"] == "incoming"
        assert relation["subject_object_id"] == subject
        assert relation["object_object_id"] == target
        assert relation["relation_type_id"] == "relation:protagonist_of_work"
        assert relation["owner_object_id"] == subject
        assert relation["owner_version_id"] == version_1
        assert relation["evidence"] == [{"evidence_id": evidence_id, "role": "supports"}]
    finally:
        repo.close()


def test_current_relation_graph_excludes_relation_from_noncurrent_historical_version(tmp_path):
    repo = Repository(tmp_path / "k03-relation-history.sqlite")
    try:
        subject, target, _, version_1 = _import_grounded_relation(repo, tmp_path)

        version_2 = repo.version_store.begin_candidate(
            subject,
            version_1,
            version_id="version:k03:subject:v2",
        )
        repo.version_store.accept_candidate(version_2)

        app = KnowledgeReadApplication(repo)
        current_from_target = app.get_object_relations(target)
        pinned_from_subject = app.get_object_relations(subject, version_id=version_1)

        assert current_from_target["relations"] == []
        assert current_from_target["scope"] == "current_relation_graph"

        assert pinned_from_subject["scope"] == "pinned_object_version"
        assert pinned_from_subject["resolved_version_id"] == version_1
        assert pinned_from_subject["is_current"] is False
        assert len(pinned_from_subject["relations"]) == 1
        assert pinned_from_subject["relations"][0]["subject_object_id"] == subject
        assert pinned_from_subject["relations"][0]["object_object_id"] == target
    finally:
        repo.close()
