from sgokb.application import Application
from sgokb.repository import Repository


class SemanticFixtureEmbedder:
    model = "f03-semantic-fixture"
    revision = "1"
    configuration = "fixture"

    def embed(self, texts, *, query=False):
        if query:
            return [[1.0, 0.01] for _ in texts]
        return [
            [1.0, 0.01] if "frost sovereign" in text.casefold() else [0.01, 1.0] for text in texts
        ]


def _capture(app, make_bundle, *, url, html, timestamp="2026-01-01T00:00:00.000Z"):
    imported = app.import_source_path(make_bundle(url=url, html=html, timestamp=timestamp))
    processed = app.process_source_snapshot(imported["snapshot"])
    return imported, processed


def _channels(candidate):
    return {reason["channel"] for reason in candidate["reasons"]}


def test_object_evidence_retrieval_combines_signals_and_honors_excluded(tmp_path, make_bundle):
    repository = Repository(tmp_path / "f03-signals.sqlite")
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object(
            "架空太郎",
            "class:character",
            aliases=["氷の隊長"],
        )
        confirmed, _ = _capture(
            app,
            make_bundle,
            url="https://example.test/confirmed",
            html="<html><main><p>架空太郎は勇敢な人物である。</p></main></html>",
        )
        alias_source, _ = _capture(
            app,
            make_bundle,
            url="https://example.test/alias",
            html="<html><main><p>氷の隊長は仲間を守る。</p></main></html>",
        )
        excluded, excluded_run = _capture(
            app,
            make_bundle,
            url="https://example.test/excluded",
            html="<html><main><p>架空太郎についての除外対象記事。</p></main></html>",
        )
        repository.source_store.associate_object(
            confirmed["source"],
            object_id,
            "confirmed",
            subject_relationship="main_subject",
        )
        repository.source_store.associate_object(
            alias_source["source"],
            object_id,
            "candidate",
            subject_relationship="possible_subject",
        )
        repository.source_store.associate_object(excluded["source"], object_id, "excluded")

        result = app.retrieve_object_evidence(object_id, semantic=False)
        assert result["scope"] == "effective_snapshot_and_run"
        assert excluded["source"] in result["excluded_source_ids"]
        returned_ids = {item["evidence_id"] for item in result["candidates"]}
        assert not returned_ids.intersection(excluded_run["evidence_ids"])

        confirmed_candidates = [
            item for item in result["candidates"] if item["source_id"] == confirmed["source"]
        ]
        assert confirmed_candidates
        assert {"explicit_association", "name", "lexical"} <= _channels(confirmed_candidates[0])

        alias_candidates = [
            item for item in result["candidates"] if item["source_id"] == alias_source["source"]
        ]
        assert alias_candidates
        assert {"explicit_association", "alias", "lexical"} <= _channels(alias_candidates[0])
        assert repository.one("SELECT name FROM sqlite_master WHERE name='ai_runs'") is None
    finally:
        repository.close()


def test_retrieval_uses_effective_generation_but_manual_include_can_select_history(
    tmp_path, make_bundle
):
    repository = Repository(tmp_path / "f03-effective.sqlite")
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        first, first_run = _capture(
            app,
            make_bundle,
            url="https://example.test/history",
            html="<html><main><p>架空太郎の初期記録。</p></main></html>",
            timestamp="2026-01-01T00:00:00.000Z",
        )
        second, second_run = _capture(
            app,
            make_bundle,
            url="https://example.test/history",
            html="<html><main><p>SECOND GENERATION ONLY.</p></main></html>",
            timestamp="2026-01-02T00:00:00.000Z",
        )
        assert first["source"] == second["source"]
        assert second["effective"] is False
        assert second_run["effective"] is False
        repository.source_store.associate_object(first["source"], object_id, "confirmed")

        default = app.retrieve_object_evidence(object_id, semantic=False)
        default_ids = {item["evidence_id"] for item in default["candidates"]}
        assert default_ids.intersection(first_run["evidence_ids"])
        assert not default_ids.intersection(second_run["evidence_ids"])

        historical_id = second_run["evidence_ids"][0]
        included = app.retrieve_object_evidence(
            object_id,
            semantic=False,
            manual_include=[historical_id],
            manual_exclude=[first_run["evidence_ids"][0]],
        )
        selected = {item["evidence_id"]: item for item in included["candidates"]}
        assert historical_id in selected
        assert "manual" in _channels(selected[historical_id])
        assert first_run["evidence_ids"][0] not in selected
    finally:
        repository.close()


def test_semantic_channel_can_retrieve_without_name_alias_or_metadata_match(tmp_path, make_bundle):
    repository = Repository(tmp_path / "f03-semantic.sqlite")
    app = Application(repository, embedder=SemanticFixtureEmbedder())
    try:
        object_id = repository.object_store.create_object("Semantic Hero", "class:character")
        _, processed = _capture(
            app,
            make_bundle,
            url="https://example.test/semantic",
            html=(
                "<html><main><p>The frost sovereign commands winter and protects the north.</p>"
                "<p>Unrelated background material.</p></main></html>"
            ),
        )

        lexical_only = app.retrieve_object_evidence(object_id, semantic=False)
        assert lexical_only["candidate_count"] == 0

        semantic = app.retrieve_object_evidence(object_id, semantic=True, max_candidates=1)
        assert semantic["candidate_count"] == 1
        candidate = semantic["candidates"][0]
        assert candidate["evidence_id"] in processed["evidence_ids"]
        assert "frost sovereign" in candidate["content"].casefold()
        assert _channels(candidate) == {"semantic"}
    finally:
        repository.close()


def test_migration_009_backfills_existing_canonical_evidence(tmp_path):
    import sqlite3
    from pathlib import Path

    from sgokb.storage import SourceRepository

    path = tmp_path / "pre-f03.sqlite"
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
    migrations = Path("src/sgokb/migrations")
    for file in sorted(migrations.glob("*.sql")):
        version = int(file.name.split("_", 1)[0])
        if version > 8:
            continue
        db.executescript(
            "BEGIN;\n"
            + file.read_text(encoding="utf-8")
            + f"\nINSERT INTO schema_migrations VALUES({version});\nCOMMIT;"
        )

    store = SourceRepository(db)
    source_id = store.create_source("Backfill source")
    snapshot_id = store.create_snapshot(
        source_id,
        "2026-01-01T00:00:00Z",
        "fixture",
        title="Backfill Hero",
    )
    artifact_id = store.add_raw_artifact(
        snapshot_id,
        "rendered_dom",
        "fixture://raw",
        "a" * 64,
        1,
        logical_path="dom/main.html",
        media_type="text/html",
    )
    run_id = store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        [artifact_id],
    )
    evidence_id = store.add_evidence(
        run_id,
        "Backfill Hero appears in evidence created before Migration 009.",
        "normalized",
    )
    store.select_effective_snapshot(source_id, snapshot_id, reason="fixture")
    store.select_effective_run(snapshot_id, run_id, reason="fixture")
    db.close()

    repository = Repository(path)
    try:
        rows = repository.source_store.lexical_evidence_rows('"Backfill Hero"')
        assert [row["id"] for row in rows] == [evidence_id]
        assert repository.one("SELECT count(*) n FROM schema_migrations")["n"] == 17
    finally:
        repository.close()
