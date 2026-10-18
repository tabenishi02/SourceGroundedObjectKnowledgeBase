import sqlite3

import pytest

from sgokb.domain import EvidenceExtractionMode, EvidenceTargetKind
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "n01-domain-contracts.sqlite")
    yield value
    value.close()


def _object(repo, name, class_key):
    class_id = repo.object_store.class_by_key(class_key).class_id
    return repo.object_store.create_object(name, class_id)


def _candidate_relation(repo):
    subject = _object(repo, "Subject", "character")
    target = _object(repo, "Target", "work")
    candidate = repo.version_store.begin_candidate(subject, None, version_id="version-n01-relation")
    relation_type = repo.object_store.register_relation_type("n01_related_to", "N-01 related to")
    relation_id = "relation-n01"
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                relation_id,
                candidate,
                subject,
                relation_type,
                target,
                "2026-10-16T00:00:00Z",
            ),
        )
    return subject, target, candidate, relation_id


def _evidence(repo):
    source = repo.source_store.create_source("N-01 relation source")
    locator = repo.source_store.add_locator(source, "url", "https://example.test/n01-relation")
    snapshot = repo.source_store.create_snapshot(
        source,
        "2026-10-16T00:00:00Z",
        "web_capture",
        observed_locator_id=locator,
    )
    artifact = repo.source_store.add_raw_artifact(
        snapshot,
        "document",
        "raw/n01-relation.txt",
        "sha-n01-relation",
        10,
    )
    run = repo.source_store.create_normalization_run(snapshot, "text", "1", [artifact])
    return repo.source_store.add_evidence(
        run,
        "Grounding evidence for the N-01 relation.",
        EvidenceExtractionMode.VERBATIM,
    )


def test_relation_requires_evidence_before_candidate_can_be_accepted(repo):
    _, _, candidate, relation_id = _candidate_relation(repo)

    with pytest.raises(sqlite3.IntegrityError, match="accepted relation requires evidence"):
        repo.version_store.accept_candidate(candidate)

    object_id = repo.version_store.version_by_id(candidate).object_id
    assert repo.version_store.current_version_id(object_id) is None
    row = repo.one("SELECT id FROM object_relations WHERE id=?", (relation_id,))
    assert row["id"] == relation_id


def test_accepted_relation_and_grounding_are_immutable(repo):
    subject, target, candidate, relation_id = _candidate_relation(repo)
    evidence_id = _evidence(repo)
    repo.source_store.link_evidence(
        candidate,
        EvidenceTargetKind.RELATION,
        relation_id,
        evidence_id,
    )
    repo.version_store.accept_candidate(candidate)

    replacement_target = _object(repo, "Replacement Target", "work")
    with pytest.raises(sqlite3.IntegrityError, match="terminal version content is immutable"):
        with repo.db:
            repo.db.execute(
                "UPDATE object_relations SET object_object_id=? WHERE id=?",
                (replacement_target, relation_id),
            )

    with pytest.raises(sqlite3.IntegrityError, match="terminal version content is immutable"):
        with repo.db:
            repo.db.execute("DELETE FROM object_relations WHERE id=?", (relation_id,))

    row = repo.one("SELECT * FROM object_relations WHERE id=?", (relation_id,))
    assert row["subject_object_id"] == subject
    assert row["object_object_id"] == target
    assert repo.version_store.current_version_id(subject) == candidate
