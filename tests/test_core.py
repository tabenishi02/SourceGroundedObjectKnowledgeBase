import hashlib
import json
import sqlite3

import pytest

from sgokb.cli import export_markdown, main
from sgokb.domain import SearchFilter, validate_fragments, validate_vectors
from sgokb.extraction import ExtractorRegistry, GenericExtractor, chunks
from sgokb.importer import WebCaptureImporter
from sgokb.search import merge_candidates


def test_import_dedup_sources_snapshots_and_raw_unchanged(core, make_bundle):
    app, repo, _, _, snapshot, _, path = core
    before = hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns
    assert app.import_path(path)["duplicate"]
    second = make_bundle(timestamp="2026-01-01T01:00:00.000Z")
    other = app.import_path(second)["snapshot"]
    assert other != snapshot
    assert repo.status()["sources"] == 1
    assert repo.status()["snapshots"] == 2
    assert before == (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)


@pytest.mark.parametrize("version", ["2.0", "0.9"])
def test_format_rejected_without_mutation(core, make_bundle, version):
    app, repo, *_ = core
    before = repo.status()
    with pytest.raises(ValueError, match="Unsupported"):
        app.import_path(make_bundle(version=version))
    assert repo.status() == before


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a.pop("dom/main.html"),
        lambda a: a.update({"dom/main.html": b"CORRUPT"}),
        lambda a: a.update({"../escape": b"BAD"}),
        lambda a: a.update({"checksums.json": b"{}"}),
    ],
)
def test_bundle_integrity(make_bundle, mutation):
    with pytest.raises(ValueError):
        WebCaptureImporter().read(make_bundle(mutate=mutation))


def test_same_id_different_content_rejected(core, make_bundle):
    app, repo, _, _, snapshot, _, _ = core
    old_run = repo.snapshot(snapshot)["active_run"]
    other = make_bundle(capture_id=snapshot, html="<html><body>changed</body></html>")
    with pytest.raises(ValueError, match="different raw bytes"):
        app.import_path(other)
    assert repo.snapshot(snapshot)["active_run"] == old_run
    with pytest.raises(ValueError, match="Raw changed"):
        app.process(snapshot)


def test_structural_extraction_and_utf8(core):
    _, repo, _, _, snapshot, _, _ = core
    evidence = repo.evidence(snapshot)
    content = "\n".join(e["content"] for e in evidence)
    assert "架空太郎" in content and "REMOVE" not in content and "SECRET" not in content
    kinds = {kind for e in evidence for kind in json.loads(e["metadata"])["kinds"]}
    assert {"heading", "paragraph", "table", "list", "quote", "post"} <= kinds
    assert "架空団 | 隊長" in content
    posts = [e for e in evidence if "post" in json.loads(e["metadata"])["kinds"]]
    assert len(posts) == 2
    meta = json.loads(posts[0]["metadata"])
    assert meta["blocks_metadata"][0]["links"] == ["#2"]
    assert meta["positions"][0].startswith("/html[0]/body")


def test_chunk_offsets_overlap_and_section():
    blocks = GenericExtractor().extract_html("<body><h2>Test</h2><p>" + "a" * 250 + "</p></body>")
    evidence = chunks(blocks, size=100, overlap=10)
    long = [e for e in evidence if e["kinds"] == ["paragraph"]]
    assert [e["start"] for e in long] == [0, 90, 180]
    assert all(e["section"] == ["Test"] for e in long)
    assert long[0]["content"][-10:] == long[1]["content"][:10]


@pytest.mark.parametrize(
    "output",
    [
        {},
        {"fragments": [{}]},
        {"fragments": [{"facet": "能力", "content": "claim", "evidence_ids": ["unknown"]}]},
    ],
)
def test_fragment_validation(output):
    with pytest.raises(ValueError):
        validate_fragments(output, {"known"})


def test_fragment_provenance_and_entity_relation(core):
    app, repo, _, _, snapshot, entity, path = core
    result = app.fragment(snapshot, entity)
    provenance = repo.provenance("fragment", result["fragment_ids"][0])
    evidence = provenance["evidence"][0]
    assert evidence["snapshot_id"] == snapshot
    assert evidence["raw_path"] == str(path.resolve())
    assert evidence["raw_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert evidence["metadata"]["artifact"] == "dom/main.html"
    work = repo.add_entity("Work", "架空作品")
    repo.relate(entity, "appears_in", work)
    assert len(repo.entities()) == 2


def test_fts_japanese_and_short_terms(core):
    app, _, _, _, _, _, _ = core
    assert app.search("架空太郎", mode="lexical")
    assert app.search("氷", mode="lexical")
    assert not app.search("不存在用語", mode="lexical")
    assert isinstance(app.search('" OR drop', mode="lexical"), list)


def test_semantic_synonym_and_model_isolation(core):
    app, repo, _, embedder, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    output = app.embed()
    assert output["dimension"] == 2
    assert not app.search("might", mode="lexical")
    results = app.search("might", mode="semantic")
    assert "strength" in results[0]["content"]
    assert {"evidence", "fragment"} <= {r["kind"] for r in app.search("strength", limit=50)}
    embedder.revision = "2"
    with pytest.raises(ValueError, match="No embeddings"):
        app.search("might", mode="semantic")
    app.embed()
    assert repo.status()["embedding_spaces"] == 2


def test_metadata_filter_before_limit(core):
    app, repo, _, _, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    app.embed()
    source = repo.snapshot(snapshot)["source_id"]
    for filters in [
        SearchFilter(entity=entity),
        SearchFilter(snapshot=snapshot),
        SearchFilter(source=source),
        SearchFilter(site="example.test"),
        SearchFilter(source_type="generic_web"),
        SearchFilter(facet="能力"),
    ]:
        assert app.search("power", filters, limit=1)
    assert not app.search("power", SearchFilter(site="unrelated.test"))
    assert not app.search("power", SearchFilter(entity=repo.add_entity("Character", "別人")))


def test_merge_dedup_and_channel_scores():
    row = {"kind": "evidence", "target_id": "x", "content": "text"}
    result = merge_candidates([dict(row, lexical_rank=1)], [dict(row, semantic_rank=2)])
    assert len(result) == 1
    assert result[0]["score"] == pytest.approx(1 / 61 + 1 / 62)
    assert result[0]["channels"] == ["lexical", "semantic"]


def test_final_document_grounding_and_provenance(core):
    app, repo, _, _, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    app.embed()
    result = app.generate(entity)
    doc = repo.document(result["document_id"])
    assert "[^c1]" in doc["markdown"] and "Snapshot" in doc["markdown"]
    citations = json.loads(doc["citations"])
    assert next(iter(citations.values()))["evidence"][0]["snapshot_id"] == snapshot
    ai = repo.one("SELECT * FROM ai_runs WHERE id=?", (doc["ai_run"],))
    assert ai["status"] == "success" and ai["model"] == "unit-test-double"
    assert "version:" in ai["prompt"] and json.loads(ai["input"])["payload"]["fragments"]


def test_invalid_ai_refs_preserve_previous_and_ledger(core):
    app, repo, llm, _, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    before = repo.status()["fragments"]
    llm.invalid = True
    with pytest.raises(ValueError):
        app.fragment(snapshot, entity)
    assert repo.status()["fragments"] == before
    ai = repo.one("SELECT * FROM ai_runs ORDER BY rowid DESC LIMIT 1")
    assert ai["status"] == "failed" and "invented" in ai["output"]


def test_final_failure_preserves_document(core):
    app, repo, llm, _, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    app.embed()
    original = app.generate(entity)["document_id"]
    llm.invalid = True
    with pytest.raises(ValueError):
        app.generate(entity)
    assert repo.status()["documents"] == 1
    assert repo.document(original)


def test_reprocess_retains_history_changes_active(core):
    app, repo, _, _, snapshot, entity, _ = core
    first = repo.snapshot(snapshot)["active_run"]
    app.fragment(snapshot, entity)
    first_evidence = repo.evidence(snapshot)[0]["id"]
    second = app.process(snapshot, size=150, overlap=20)["run"]
    assert first != second
    assert repo.status()["normalized_runs"] == 2
    assert repo.provenance("evidence", first_evidence)
    assert not any(r["kind"] == "fragment" for r in repo.candidates(SearchFilter()))
    app.fragment(snapshot, entity)
    assert any(r["kind"] == "fragment" for r in repo.candidates(SearchFilter()))


def test_processing_failure_preserves_active(core):
    app, repo, _, _, snapshot, _, _ = core
    before = repo.snapshot(snapshot)["active_run"]
    with pytest.raises(ValueError):
        app.process(snapshot, size=20, overlap=10)
    assert repo.snapshot(snapshot)["active_run"] == before


def test_transaction_rollback_on_fragment_save_failure(core):
    app, repo, _, _, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    before = repo.status()
    repo.db.execute(
        "CREATE TRIGGER reject_fragment BEFORE INSERT ON fragments "
        "BEGIN SELECT RAISE(ABORT,'simulated storage failure'); END"
    )
    with pytest.raises(sqlite3.IntegrityError):
        app.fragment(snapshot, entity)
    assert repo.status()["fragments"] == before["fragments"]
    assert repo.one("SELECT count(*) AS n FROM fragment_runs WHERE active=1")["n"] == 1


def test_empty_ai_result_does_not_replace_good_generation(core):
    app, repo, llm, _, snapshot, entity, _ = core
    app.fragment(snapshot, entity)
    llm.empty = True
    assert app.fragment(snapshot, entity)["fragments"] == 0
    assert repo.one("SELECT count(*) AS n FROM fragment_runs WHERE active=1")["n"] == 1


def test_embedding_failed_generation_atomic(core):
    app, repo, _, embedder, *_ = core
    app.embed()
    before = repo.status()["embeddings"]
    calls = []
    original = embedder.embed

    def fail(texts, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            raise RuntimeError("simulated embedding failure")
        return original(texts, **kwargs)

    embedder.embed = fail
    with pytest.raises(RuntimeError):
        app.embed(batch_size=1)
    assert repo.status()["embeddings"] == before


@pytest.mark.parametrize("vectors", [[], [[0, 0]], [[float("nan"), 1]], [[1, 2], [1]]])
def test_vector_validation(vectors):
    with pytest.raises(ValueError):
        validate_vectors(vectors, 1)


def test_cli_and_raw_export_guard(core, capsys):
    _, repo, _, _, _, _, path = core
    assert main(["--db", str(repo.db.execute("PRAGMA database_list").fetchone()[2]), "status"]) == 0
    assert json.loads(capsys.readouterr().out)["snapshots"] == 1
    with pytest.raises(ValueError, match="Raw"):
        export_markdown(path, "DO NOT WRITE", repo)


def test_auxiliary_frame_shadow_positions_and_default_isolation(core, make_bundle):
    app, repo, *_ = core
    frame = "dom/frames/frame-0001.html"
    extra = {
        frame: b"<body><p>Frame artificial fact.</p></body>",
        "metadata/frames.json": json.dumps(
            [{"frame_id": "frame-0001", "capture_status": "success", "file": frame}]
        ).encode(),
        "metadata/shadow-dom.json": json.dumps(
            [
                {
                    "frame_id": "main",
                    "host_path": "/html[0]/body[1]/x-test[0]",
                    "mode": "open",
                    "html": "<p>Shadow artificial fact.</p>",
                }
            ]
        ).encode(),
    }
    snapshot = app.import_path(make_bundle(extra=extra))["snapshot"]
    app.process(snapshot)
    assert not any("artificial fact" in e["content"] for e in repo.evidence(snapshot))
    app.process(snapshot, include_auxiliary=True)
    evidence = repo.evidence(snapshot)
    frames = [e for e in evidence if "Frame artificial" in e["content"]]
    shadows = [e for e in evidence if "Shadow artificial" in e["content"]]
    assert json.loads(frames[0]["metadata"])["artifact"] == frame
    assert json.loads(shadows[0]["metadata"])["artifact"] == "metadata/shadow-dom.json"
    assert "#shadow-root" in json.loads(shadows[0]["metadata"])["positions"][0]


def test_site_specific_roots():
    registry = ExtractorRegistry()
    html = (
        '<body><div>OUTSIDE UI</div><div id="mw-content-text">'
        '<div class="mw-parser-output"><h2>Topic</h2><p>Inside article</p></div></div></body>'
    )
    blocks = registry.select("ja.wikipedia.org").extract_html(html)
    assert "OUTSIDE" not in "\n".join(b.content for b in blocks)
    assert "Inside article" in "\n".join(b.content for b in blocks)
    assert registry.select("dic.pixiv.net").name == "pixiv-encyclopedia"
    assert registry.select("unknown.example").name == "generic"


def test_migration_reopen_preserves_data(core):
    from sgokb.repository import Repository

    _, repo, _, _, snapshot, *_ = core
    path = repo.db.execute("PRAGMA database_list").fetchone()[2]
    reopened = Repository(path)
    assert reopened.snapshot(snapshot)
    assert reopened.one("SELECT count(*) AS n FROM schema_migrations")["n"] == 4
    reopened.migrate()
    assert reopened.status()["sources"] == 1
    reopened.close()
