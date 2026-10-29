import sqlite3
from pathlib import Path

import pytest

from sgokb.domain import EmbeddingSpaceSpec, EvidenceExtractionMode
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

    tables = {row["name"] for row in repo.rows("SELECT name FROM sqlite_master WHERE type='table'")}
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


@pytest.fixture
def populated_pre018_database(tmp_path):
    class Pre018Repository(Repository):
        def migrate(self):
            self.db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
            self.db.commit()
            migrations = Path(__file__).resolve().parents[1] / "src/sgokb/migrations"
            for file in sorted(migrations.glob("*.sql")):
                version = int(file.name.split("_")[0])
                if 3 <= version <= 17:
                    self.db.executescript(
                        "BEGIN;\n"
                        + file.read_text(encoding="utf-8")
                        + f"\nINSERT INTO schema_migrations VALUES({version});\nCOMMIT;"
                    )

    path = tmp_path / "populated-pre018.sqlite"
    legacy = Pre018Repository(path)
    try:
        _, version_id = _accepted_empty_version(legacy)
        source_id = legacy.source_store.create_source("Preservation source")
        locator_id = legacy.source_store.add_locator(
            source_id, "url", "https://example.test/preservation", preferred=True
        )
        snapshot_id = legacy.source_store.create_snapshot(
            source_id, "2026-10-23T00:00:00Z", "test", observed_locator_id=locator_id
        )
        artifact_id = legacy.source_store.add_raw_artifact(
            snapshot_id, "html", "memory://preservation", "a" * 64, 10
        )
        run_id = legacy.source_store.create_normalization_run(
            snapshot_id, "fixture", "1", [artifact_id]
        )
        evidence_id = legacy.source_store.add_evidence(
            run_id, "Preservation witness.", EvidenceExtractionMode.NORMALIZED, language="en"
        )
        builder = SearchRepresentationBuilder(legacy)
        representations = (
            *builder.materialize_version(version_id),
            builder.materialize_evidence(evidence_id),
        )
        space = EmbeddingSpaceSpec(
            provider_key="migration-fixture",
            provider_version="1",
            model="fixture",
            model_revision="1",
            dimension=2,
            native_dimension=2,
            preprocessing_key="migration-preservation",
            preprocessing_version="1",
        )
        for representation_id in representations:
            legacy.embedding_store.save_representation_embedding(
                space, representation_id, [0.6, 0.8]
            )
        tables = (
            "search_representations",
            "knowledge_search_representation_memberships",
            "evidence_search_representation_memberships",
            "search_representation_embeddings",
            "search_embedding_spaces",
            "objects",
            "object_versions",
        )
        before = {
            table: [tuple(row) for row in legacy.db.execute(f"SELECT * FROM {table} ORDER BY 1")]
            for table in tables
        }
        assert all(before.values())
        assert legacy.one("SELECT max(version) AS n FROM schema_migrations")["n"] == 17
        assert (
            "object_overview"
            not in legacy.one("SELECT sql FROM sqlite_master WHERE name='search_representations'")[
                "sql"
            ]
        )
        assert legacy.rows("PRAGMA foreign_key_check") == []
        assert legacy.one("PRAGMA integrity_check") == {"integrity_check": "ok"}
    finally:
        legacy.close()
    return path, before, space


def test_pre018_populated_migration_preserves_ids_content_vectors_and_fts(
    populated_pre018_database,
):
    path, before, space = populated_pre018_database
    migrated = Repository(path)
    try:
        assert [
            x["version"]
            for x in migrated.rows("SELECT version FROM schema_migrations ORDER BY version")
        ] == list(range(3, 20))
        for table, rows in before.items():
            assert [
                tuple(row) for row in migrated.db.execute(f"SELECT * FROM {table} ORDER BY 1")
            ] == rows, table
        assert migrated.rows("PRAGMA foreign_key_check") == []
        assert migrated.one("PRAGMA integrity_check") == {"integrity_check": "ok"}
        fts = migrated.rows(
            "SELECT representation_id,kind,content FROM search_representation_fts "
            "ORDER BY representation_id"
        )
        expected = migrated.rows(
            "SELECT id AS representation_id,kind,content FROM search_representations ORDER BY id"
        )
        assert fts == expected
        assert (
            len(
                migrated.rows(
                    "SELECT representation_id FROM search_representation_fts "
                    "WHERE search_representation_fts MATCH 'Preservation'"
                )
            )
            == 1
        )
        migrated.db.execute(
            "INSERT INTO search_representation_fts(search_representation_fts) "
            "VALUES('integrity-check')"
        )
        migrated.db.commit()
        assert {
            x["membership_id"]
            for x in migrated.rows(
                "SELECT membership_id FROM knowledge_search_generation_memberships "
                "WHERE generation_id='search-generation:phase-i-v1'"
            )
        } == {row[0] for row in before["knowledge_search_representation_memberships"]}
        for row in before["search_representation_embeddings"]:
            assert migrated.embedding_store.representation_embedding(
                space.space_id, row[1]
            ) == pytest.approx([0.6, 0.8])
        assert (
            migrated.one(
                "SELECT count(*) AS n FROM search_representations WHERE kind='object_overview'"
            )["n"]
            == 0
        )
    finally:
        migrated.close()
