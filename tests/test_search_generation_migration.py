import sqlite3

import pytest

from sgokb.repository import Repository
from sgokb.retrieval import SearchRepresentationBuilder


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "search-generation.sqlite")
    yield value
    value.close()


def _accepted_empty_version(repo):
    object_id = repo.object_store.create_object(
        "R2 Migration Subject",
        repo.object_store.class_by_key("character").class_id,
        object_id="object-r2-migration",
    )
    version_id = repo.version_store.begin_candidate(
        object_id,
        None,
        version_id="version-r2-migration",
    )
    repo.version_store.accept_candidate(version_id)
    return object_id, version_id


def test_migration_018_installs_coexistence_and_generation_schema(repo):
    assert repo.one("SELECT version FROM schema_migrations WHERE version=18") == {"version": 18}

    tables = {
        row["name"]
        for row in repo.rows("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {
        "knowledge_search_generations",
        "knowledge_search_generation_memberships",
        "knowledge_search_active_generation",
        "knowledge_search_generation_switches",
        "knowledge_search_generation_vector_indexes",
    } <= tables

    legacy = repo.one(
        "SELECT id,contract_key,contract_version,state FROM knowledge_search_generations "
        "WHERE id='search-generation:phase-i-v1'"
    )
    assert legacy == {
        "id": "search-generation:phase-i-v1",
        "contract_key": "phase-i-search-v1",
        "contract_version": 1,
        "state": "building",
    }
    assert repo.rows("PRAGMA foreign_key_check") == []


def test_migration_018_rejects_unknown_representation_kind(repo):
    with pytest.raises(sqlite3.IntegrityError):
        with repo.db:
            repo.db.execute(
                """INSERT INTO search_representations
                   (id,kind,builder_key,builder_version,content,content_hash,created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    "invalid-kind",
                    "unknown_kind",
                    "sgokb-canonical-search",
                    "1",
                    "content",
                    "0" * 64,
                    "2026-10-23T00:00:00Z",
                ),
            )


def test_overview_fts_and_generation_kind_guards(repo):
    object_id, version_id = _accepted_empty_version(repo)
    builder = SearchRepresentationBuilder(repo)

    builder.materialize_version_r2(version_id)
    overview = repo.one(
        """SELECT m.id AS membership_id,m.representation_id,r.kind,r.builder_version
           FROM knowledge_search_representation_memberships m
           JOIN search_representations r ON r.id=m.representation_id
           WHERE m.object_id=? AND m.version_id=? AND m.target_kind='object_overview'""",
        (object_id, version_id),
    )
    assert overview["kind"] == "object_overview"
    assert overview["builder_version"] == "2"
    assert repo.one(
        "SELECT representation_id FROM search_representation_fts WHERE representation_id=?",
        (overview["representation_id"],),
    ) == {"representation_id": overview["representation_id"]}

    with pytest.raises(sqlite3.IntegrityError, match="incompatible"):
        with repo.db:
            repo.db.execute(
                """INSERT INTO knowledge_search_generation_memberships
                   (generation_id,membership_id,created_at) VALUES(?,?,?)""",
                (
                    "search-generation:phase-i-v1",
                    overview["membership_id"],
                    "2026-10-23T00:00:00Z",
                ),
            )

    with repo.db:
        repo.db.execute(
            """INSERT INTO knowledge_search_generations
               (id,contract_key,contract_version,state,created_at)
               VALUES(?,?,?,?,?)""",
            (
                "search-generation:r2-test",
                "n05d04r2-hierarchical-v2",
                2,
                "building",
                "2026-10-23T00:00:00Z",
            ),
        )
        repo.db.execute(
            """INSERT INTO knowledge_search_generation_memberships
               (generation_id,membership_id,created_at) VALUES(?,?,?)""",
            (
                "search-generation:r2-test",
                overview["membership_id"],
                "2026-10-23T00:00:00Z",
            ),
        )

    builder.materialize_version(version_id)
    overall = repo.one(
        """SELECT m.id AS membership_id
           FROM knowledge_search_representation_memberships m
           WHERE m.object_id=? AND m.version_id=? AND m.target_kind='object_overall'""",
        (object_id, version_id),
    )
    with pytest.raises(sqlite3.IntegrityError, match="incompatible"):
        with repo.db:
            repo.db.execute(
                """INSERT INTO knowledge_search_generation_memberships
                   (generation_id,membership_id,created_at) VALUES(?,?,?)""",
                (
                    "search-generation:r2-test",
                    overall["membership_id"],
                    "2026-10-23T00:00:00Z",
                ),
            )
