import sqlite3

import pytest

from sgokb.domain import AssignmentPolicy, LifecycleStatus
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "object-schema.sqlite")
    yield value
    value.close()


def _class_id(repo, key):
    return repo.object_store.class_by_key(key).class_id


def test_initial_class_registry_seed_is_complete_and_deterministic(repo):
    classes = repo.object_store.classes()
    assert len(classes) == 62
    assert repo.object_store.class_by_key("character").class_id == "class:character"
    character = repo.object_store.class_by_key("character")
    assert character.assignment_policy is AssignmentPolicy.PRIMARY_ELIGIBLE
    assert repo.object_store.class_by_key("agent").assignment_policy is AssignmentPolicy.STRUCTURAL
    fictional = repo.object_store.class_by_key("fictional_entity")
    assert fictional.assignment_policy is AssignmentPolicy.ADDITIONAL_ONLY

    ancestors = set(repo.object_store.ancestor_class_ids("class:character"))
    assert {"class:agent", "class:fictional_entity", "class:object_class"} <= ancestors


def test_object_identity_does_not_depend_on_name(repo):
    character = _class_id(repo, "character")
    first = repo.object_store.create_object("Alice", character)
    second = repo.object_store.create_object("Alice", character)

    assert first != second
    assert repo.object_store.get_object(first).name == "Alice"
    assert repo.object_store.get_object(second).name == "Alice"


def test_primary_and_additional_class_constraints(repo):
    character = _class_id(repo, "character")
    agent = _class_id(repo, "agent")
    fictional = _class_id(repo, "fictional_entity")
    object_id = repo.object_store.create_object("Example", character)

    with pytest.raises(sqlite3.IntegrityError, match="primary class"):
        repo.object_store.create_object("Invalid", agent)
    with pytest.raises(sqlite3.IntegrityError, match="additional class"):
        repo.object_store.add_additional_class(object_id, agent)
    with pytest.raises(sqlite3.IntegrityError, match="cannot equal primary"):
        repo.object_store.add_additional_class(object_id, character)

    repo.object_store.add_additional_class(object_id, fictional)
    assert repo.object_store.get_object(object_id).additional_class_ids == (fictional,)


def test_class_hierarchy_rejects_cycles(repo):
    with pytest.raises(sqlite3.IntegrityError, match="class hierarchy cycle"):
        with repo.db:
            repo.db.execute(
                "INSERT INTO object_class_parents VALUES(?,?,?)",
                ("class:agent", "class:character", "2026-10-12T00:00:00Z"),
            )


def test_current_version_must_belong_to_same_object(repo):
    character = _class_id(repo, "character")
    first = repo.object_store.create_object("First", character)
    second = repo.object_store.create_object("Second", character)
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_versions VALUES(?,?,?,?)",
            ("version-1", first, 1, "2026-10-12T00:00:00Z"),
        )

    with pytest.raises(sqlite3.IntegrityError, match="current version must belong"):
        with repo.db:
            repo.db.execute(
                "UPDATE objects SET current_version_id=? WHERE id=?",
                ("version-1", second),
            )

    with repo.db:
        repo.db.execute(
            "UPDATE objects SET current_version_id=? WHERE id=?",
            ("version-1", first),
        )
    assert repo.object_store.get_object(first).current_version_id == "version-1"


def test_registry_metadata_changes_are_audited(repo):
    character = _class_id(repo, "character")
    person = _class_id(repo, "person")
    organization = _class_id(repo, "organization")
    object_id = repo.object_store.create_object("Before", character, aliases=("Alias A",))

    repo.object_store.rename_object(object_id, "After")
    repo.object_store.add_alias(object_id, "Alias B", language="en", kind="translated_name")
    repo.object_store.add_additional_class(object_id, organization)
    repo.object_store.set_primary_class(object_id, person)
    repo.object_store.set_status(object_id, LifecycleStatus.ARCHIVED)

    current = repo.object_store.get_object(object_id)
    assert current.object_id == object_id
    assert current.name == "After"
    assert current.primary_class_id == person
    assert current.status is LifecycleStatus.ARCHIVED
    assert organization in current.additional_class_ids
    assert [alias.value for alias in current.aliases] == ["Alias A", "Alias B"]

    event_types = [event["event_type"] for event in repo.object_store.registry_events(object_id)]
    assert event_types == [
        "object_created",
        "name_changed",
        "alias_added",
        "additional_class_added",
        "primary_class_changed",
        "status_changed",
    ]


def test_unknown_class_is_staged_without_mutating_registry(repo):
    before = len(repo.object_store.classes())
    proposal_id = repo.object_store.stage_class_proposal(
        "vehicle",
        "Vehicle",
        "A dedicated Class is required; Artifact would lose intended semantics.",
        payload={"requested_by": "test"},
    )

    assert len(repo.object_store.classes()) == before
    proposal = repo.one("SELECT * FROM object_class_proposals WHERE id=?", (proposal_id,))
    assert proposal["status"] == "pending"
    assert proposal["resolved_class_id"] is None
    assert repo.object_store.class_by_key("vehicle") is None


def test_relation_type_registry_is_separate_from_class_registry(repo):
    relation_id = repo.object_store.register_relation_type("appears_in", "appears in")
    assert relation_id == "relation:appears_in"
    relation_type = repo.object_store.relation_type_by_key("appears_in")
    assert relation_type.relation_type_id == relation_id
    assert repo.object_store.class_by_key("appears_in") is None


def test_relation_rows_are_scoped_to_knowledge_version(repo):
    character = _class_id(repo, "character")
    work = _class_id(repo, "work")
    subject = repo.object_store.create_object("Character A", character)
    target = repo.object_store.create_object("Work A", work)
    relation_type = repo.object_store.register_relation_type("appears_in", "appears in")
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_versions VALUES(?,?,?,?)",
            ("version-a", subject, 1, "2026-10-12T00:00:00Z"),
        )
        repo.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                "relation-a",
                "version-a",
                subject,
                relation_type,
                target,
                "2026-10-12T00:00:00Z",
            ),
        )

    row = repo.one("SELECT * FROM object_relations WHERE id='relation-a'")
    assert row["version_id"] == "version-a"
    assert row["subject_object_id"] == subject
    assert row["object_object_id"] == target


def test_assigned_class_cannot_be_made_invalid_in_place(repo):
    character = _class_id(repo, "character")
    repo.object_store.create_object("Assigned", character)

    with pytest.raises(sqlite3.IntegrityError, match="assigned as primary"):
        with repo.db:
            repo.db.execute(
                "UPDATE object_classes SET assignment_policy='structural' WHERE id=?",
                (character,),
            )
    with pytest.raises(sqlite3.IntegrityError, match="cannot archive class"):
        with repo.db:
            repo.db.execute("UPDATE object_classes SET status='archived' WHERE id=?", (character,))


def test_version_owner_is_immutable(repo):
    character = _class_id(repo, "character")
    first = repo.object_store.create_object("First", character)
    second = repo.object_store.create_object("Second", character)
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_versions VALUES(?,?,?,?)",
            ("version-owner", first, 1, "2026-10-12T00:00:00Z"),
        )

    with pytest.raises(sqlite3.IntegrityError, match="version owner is immutable"):
        with repo.db:
            repo.db.execute(
                "UPDATE object_versions SET object_id=? WHERE id='version-owner'",
                (second,),
            )


def test_relation_version_owner_must_be_an_endpoint(repo):
    character = _class_id(repo, "character")
    work = _class_id(repo, "work")
    owner = repo.object_store.create_object("Owner", character)
    subject = repo.object_store.create_object("Subject", character)
    target = repo.object_store.create_object("Target", work)
    relation_type = repo.object_store.register_relation_type("related_to", "related to")
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_versions VALUES(?,?,?,?)",
            ("owner-version", owner, 1, "2026-10-12T00:00:00Z"),
        )

    with pytest.raises(sqlite3.IntegrityError, match="version owner must participate"):
        with repo.db:
            repo.db.execute(
                "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
                (
                    "bad-relation",
                    "owner-version",
                    subject,
                    relation_type,
                    target,
                    "2026-10-12T00:00:00Z",
                ),
            )
