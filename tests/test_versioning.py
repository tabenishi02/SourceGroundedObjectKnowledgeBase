import sqlite3
from pathlib import Path

import pytest

from sgokb.domain import (
    AttributeValueType,
    DerivationKind,
    DerivedState,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    StaleVersionError,
    VersionState,
)
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "versioning.sqlite")
    yield value
    value.close()


def _object(repo, name="Object", class_key="character"):
    class_id = repo.object_store.class_by_key(class_key).class_id
    return repo.object_store.create_object(name, class_id)


def _evidence(repo, suffix="a"):
    source = repo.source_store.create_source(f"Source {suffix}")
    locator = repo.source_store.add_locator(source, "url", f"https://example.test/{suffix}")
    snapshot = repo.source_store.create_snapshot(
        source,
        "2026-10-12T00:00:00Z",
        "web_capture",
        observed_locator_id=locator,
    )
    artifact = repo.source_store.add_raw_artifact(
        snapshot,
        "document",
        f"raw/{suffix}.txt",
        f"sha-{suffix}",
        10,
    )
    run = repo.source_store.create_normalization_run(snapshot, "text", "1", [artifact])
    return repo.source_store.add_evidence(
        run,
        f"Evidence {suffix}",
        EvidenceExtractionMode.VERBATIM,
    )


def _grounded_statement(repo, version_id, suffix="a"):
    evidence_id = _evidence(repo, suffix)
    statement_id = repo.semantic_store.add_statement(
        version_id,
        f"summary-{suffix}",
        f"Grounded statement {suffix}.",
        DerivationKind.DIRECT_STATEMENT,
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.STATEMENT,
        statement_id,
        evidence_id,
    )
    return statement_id, evidence_id


def test_candidate_captures_base_classification_and_acceptance_promotes_current(repo):
    object_id = _object(repo)
    fictional = repo.object_store.class_by_key("fictional_entity").class_id
    repo.object_store.add_additional_class(object_id, fictional)

    first = repo.version_store.begin_candidate(object_id, None, version_id="version-1")
    first_record = repo.version_store.version_by_id(first)
    assert first_record.state is VersionState.CANDIDATE
    assert first_record.base_version_id is None
    assert first_record.version_number == 1
    assert first_record.classification.primary_class_id == "class:character"
    assert first_record.classification.additional_class_ids == (fictional,)

    _grounded_statement(repo, first, "one")
    accepted = repo.version_store.accept_candidate(first)
    assert accepted.state is VersionState.ACCEPTED
    assert repo.version_store.current_version_id(object_id) == first

    second = repo.version_store.begin_candidate(object_id, first, version_id="version-2")
    second_record = repo.version_store.version_by_id(second)
    assert second_record.version_number == 2
    assert second_record.base_version_id == first


def test_current_pointer_rejects_unaccepted_candidate(repo):
    object_id = _object(repo)
    candidate = repo.version_store.begin_candidate(object_id, None)
    with pytest.raises(sqlite3.IntegrityError, match="be accepted"):
        with repo.db:
            repo.db.execute(
                "UPDATE objects SET current_version_id=? WHERE id=?", (candidate, object_id)
            )


def test_concurrent_candidate_becomes_stale_after_other_candidate_is_accepted(repo):
    object_id = _object(repo)
    first = repo.version_store.begin_candidate(object_id, None)
    _grounded_statement(repo, first, "first")
    repo.version_store.accept_candidate(first)

    candidate_a = repo.version_store.begin_candidate(object_id, first)
    candidate_b = repo.version_store.begin_candidate(object_id, first)
    _grounded_statement(repo, candidate_a, "a")
    _grounded_statement(repo, candidate_b, "b")
    repo.version_store.accept_candidate(candidate_a)

    with pytest.raises(StaleVersionError, match="no longer matches current"):
        repo.version_store.accept_candidate(candidate_b)
    assert repo.version_store.version_by_id(candidate_b).state is VersionState.CANDIDATE
    assert repo.version_store.current_version_id(object_id) == candidate_a


def test_classification_change_makes_candidate_stale_without_invalidating_old_versions(repo):
    object_id = _object(repo)
    candidate = repo.version_store.begin_candidate(object_id, None)
    _grounded_statement(repo, candidate, "class")

    person = repo.object_store.class_by_key("person").class_id
    repo.object_store.set_primary_class(object_id, person)
    with pytest.raises(StaleVersionError, match="classification snapshot"):
        repo.version_store.accept_candidate(candidate)

    assert (
        repo.version_store.version_by_id(candidate).classification.primary_class_id
        == "class:character"
    )
    assert repo.object_store.get_object(object_id).primary_class_id == person


def test_acceptance_requires_grounding_for_canonical_knowledge(repo):
    object_id = _object(repo)
    candidate = repo.version_store.begin_candidate(object_id, None)
    repo.semantic_store.add_statement(
        candidate,
        "ungrounded",
        "This has no Evidence Link.",
        DerivationKind.SYNTHESIS,
    )
    with pytest.raises(sqlite3.IntegrityError, match="statement requires evidence"):
        repo.version_store.accept_candidate(candidate)
    assert repo.version_store.current_version_id(object_id) is None

    object_id_2 = _object(repo, "Object 2")
    candidate_2 = repo.version_store.begin_candidate(object_id_2, None)
    repo.semantic_store.register_attribute_definition(
        "e04_known", "E04 known", AttributeValueType.TEXT
    )
    repo.semantic_store.add_attribute(candidate_2, "e04_known", "value")
    with pytest.raises(sqlite3.IntegrityError, match="known attribute requires evidence"):
        repo.version_store.accept_candidate(candidate_2)


def test_content_facet_must_have_statement_before_acceptance(repo):
    object_id = _object(repo)
    candidate = repo.version_store.begin_candidate(object_id, None)
    personality = repo.semantic_store.facet_by_key("personality").facet_id
    repo.semantic_store.set_version_facet(candidate, personality)
    with pytest.raises(sqlite3.IntegrityError, match="content facet requires statement"):
        repo.version_store.accept_candidate(candidate)


def test_accepted_version_content_and_grounding_are_immutable(repo):
    object_id = _object(repo)
    candidate = repo.version_store.begin_candidate(object_id, None)
    statement_id, evidence_id = _grounded_statement(repo, candidate, "immutable")
    repo.version_store.accept_candidate(candidate)

    with pytest.raises(sqlite3.IntegrityError, match="terminal version content is immutable"):
        with repo.db:
            repo.db.execute(
                "UPDATE knowledge_statements SET text='changed' WHERE id=?", (statement_id,)
            )
    with pytest.raises(sqlite3.IntegrityError, match="terminal version content is immutable"):
        repo.semantic_store.add_statement(
            candidate,
            "late",
            "Late mutation.",
            DerivationKind.DIRECT_STATEMENT,
        )
    link_id = repo.one(
        "SELECT id FROM evidence_links WHERE version_id=? AND target_id=?",
        (candidate, statement_id),
    )["id"]
    with pytest.raises(sqlite3.IntegrityError, match="terminal version content is immutable"):
        with repo.db:
            repo.db.execute("DELETE FROM evidence_links WHERE id=?", (link_id,))
    assert repo.source_store.evidence_by_id(evidence_id).content == "Evidence immutable"
    assert repo.version_store.current_version_id(object_id) == candidate


def test_rollback_moves_only_current_pointer_and_new_version_can_branch_from_old_base(repo):
    object_id = _object(repo)
    versions = []
    base = None
    for index in range(1, 4):
        version = repo.version_store.begin_candidate(object_id, base, version_id=f"version-{index}")
        _grounded_statement(repo, version, f"v{index}")
        repo.version_store.accept_candidate(version)
        versions.append(version)
        base = version

    repo.version_store.rollback_current(object_id, versions[0])
    assert repo.version_store.current_version_id(object_id) == versions[0]
    assert all(
        repo.version_store.version_by_id(version).state is VersionState.ACCEPTED
        for version in versions
    )

    branched = repo.version_store.begin_candidate(object_id, versions[0], version_id="version-4")
    record = repo.version_store.version_by_id(branched)
    assert record.version_number == 4
    assert record.base_version_id == versions[0]


def test_derived_state_is_separate_failure_domain_and_uses_revision_token(repo):
    object_id = _object(repo)
    first = repo.version_store.begin_candidate(object_id, None)
    _grounded_statement(repo, first, "derived-1")
    repo.version_store.accept_candidate(first)
    states = {state.kind: state for state in repo.version_store.derived_states(object_id)}
    search = states["search_representation"]
    assert search.status is DerivedState.PENDING and search.revision == 1
    assert repo.version_store.mark_derived_state(
        object_id, search.kind, search.revision, DerivedState.READY
    )

    second = repo.version_store.begin_candidate(object_id, first)
    _grounded_statement(repo, second, "derived-2")
    repo.version_store.accept_candidate(second)
    current = {state.kind: state for state in repo.version_store.derived_states(object_id)}[
        "search_representation"
    ]
    assert current.target_version_id == second
    assert current.status is DerivedState.PENDING and current.revision == 2
    assert not repo.version_store.mark_derived_state(object_id, current.kind, 1, DerivedState.READY)
    assert repo.version_store.mark_derived_state(
        object_id, current.kind, 2, DerivedState.FAILED, error="controlled failure"
    )
    assert repo.version_store.current_version_id(object_id) == second
    failed = {state.kind: state for state in repo.version_store.derived_states(object_id)}[
        "search_representation"
    ]
    assert failed.status is DerivedState.FAILED
    assert failed.last_error == "controlled failure"


def test_abandoned_candidate_is_terminal_and_never_current(repo):
    object_id = _object(repo)
    candidate = repo.version_store.begin_candidate(object_id, None)
    repo.version_store.abandon_candidate(candidate, reason="review rejected")
    assert repo.version_store.version_by_id(candidate).state is VersionState.ABANDONED
    assert repo.version_store.current_version_id(object_id) is None
    with pytest.raises(ValueError, match="Only candidate Versions"):
        repo.version_store.accept_candidate(candidate)
    with pytest.raises(sqlite3.IntegrityError, match="terminal version content is immutable"):
        repo.semantic_store.add_statement(
            candidate,
            "late",
            "Cannot mutate abandoned candidate.",
            DerivationKind.DIRECT_STATEMENT,
        )


def test_pre_e04_versions_are_backfilled_as_accepted_on_upgrade(tmp_path):
    path = tmp_path / "pre-e04.sqlite"
    db = sqlite3.connect(path)
    migrations = Path("src/sgokb/migrations")
    db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
    for version in range(1, 7):
        file = next(migrations.glob(f"{version:03d}_*.sql"))
        db.executescript(file.read_text(encoding="utf-8"))
        db.execute("INSERT INTO schema_migrations VALUES(?)", (version,))
    db.execute(
        "INSERT INTO objects VALUES(?,?,?,?,?,?,?)",
        (
            "legacy-object",
            "Legacy Object",
            "class:character",
            "active",
            None,
            "2026-10-12T00:00:00Z",
            "2026-10-12T00:00:00Z",
        ),
    )
    db.execute(
        "INSERT INTO object_versions VALUES(?,?,?,?)",
        ("legacy-version", "legacy-object", 1, "2026-10-12T00:00:00Z"),
    )
    db.execute("UPDATE objects SET current_version_id='legacy-version' WHERE id='legacy-object'")
    db.commit()
    db.close()

    upgraded = Repository(path)
    record = upgraded.version_store.version_by_id("legacy-version")
    assert record.state is VersionState.ACCEPTED
    assert record.accepted_at == "2026-10-12T00:00:00Z"
    assert record.classification.primary_class_id == "class:character"
    assert upgraded.version_store.current_version_id("legacy-object") == "legacy-version"
    assert upgraded.one("SELECT count(*) n FROM schema_migrations")["n"] == 16
    assert upgraded.one("PRAGMA integrity_check")["integrity_check"] == "ok"
    assert not upgraded.rows("PRAGMA foreign_key_check")
    upgraded.close()
