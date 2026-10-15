"""L-05 canonical bootstrap and non-destructive Prototype rejection contracts."""

import sqlite3

import pytest

from sgokb.repository import Repository

CANONICAL_TABLES = {
    "objects",
    "object_versions",
    "source_records",
    "source_locators",
    "source_snapshots",
    "raw_artifacts",
    "normalization_runs",
    "evidence_records",
    "search_representations",
    "search_embedding_spaces",
    "search_representation_embeddings",
}
PROTOTYPE_TABLES = {
    "sources",
    "snapshots",
    "artifacts",
    "normalized_runs",
    "evidence",
    "entities",
    "entity_relations",
    "entity_evidence",
    "ai_runs",
    "fragment_runs",
    "fragments",
    "fragment_evidence",
    "search_items",
    "search_fts",
    "embedding_spaces",
    "embeddings",
    "documents",
    "page_contexts",
    "extraction_jobs",
    "extraction_batches",
    "evidence_assessments",
    "entity_candidates",
    "structured_documents",
    "ai_observations",
    "benchmark_runs",
    "benchmark_cases",
}


def test_fresh_canonical_database_and_reopen(tmp_path):
    path = tmp_path / "canonical.sqlite"
    for _ in range(2):
        repo = Repository(path)
        try:
            assert [
                r["version"]
                for r in repo.rows("SELECT version FROM schema_migrations ORDER BY version")
            ] == list(range(3, 17))
            tables = {
                r["name"] for r in repo.rows("SELECT name FROM sqlite_master WHERE type='table'")
            }
            assert CANONICAL_TABLES <= tables
            assert not PROTOTYPE_TABLES & tables
            assert repo.one("PRAGMA integrity_check")["integrity_check"] == "ok"
            assert not repo.rows("PRAGMA foreign_key_check")
            assert repo.source_store.status()["sources"] == 0
        finally:
            repo.close()


@pytest.mark.parametrize("versions", [(1,), (2,), (1, 2), (2, 3)])
def test_prototype_database_rejected_without_upgrade_drop_or_writes(tmp_path, versions):
    path = tmp_path / "prototype.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
        db.executemany("INSERT INTO schema_migrations VALUES(?)", [(v,) for v in versions])
        db.execute("CREATE TABLE retained_sentinel(id TEXT PRIMARY KEY, content BLOB)")
        db.execute("INSERT INTO retained_sentinel VALUES('stable-id', X'0001FF')")
    db.close()
    before = path.read_bytes()
    with pytest.raises(ValueError, match="Prototype DB rejected"):
        Repository(path)
    assert path.read_bytes() == before
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall() == [
            (v,) for v in versions
        ]
        assert db.execute("SELECT * FROM retained_sentinel").fetchall() == [
            ("stable-id", b"\x00\x01\xff")
        ]
        assert db.execute("SELECT name FROM sqlite_master WHERE name='objects'").fetchone() is None
    db.close()
    path.unlink()
