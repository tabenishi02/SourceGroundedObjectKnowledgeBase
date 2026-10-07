import copy
import json

import pytest
from test_upgrade import GroundedLLM, grounded

from cpc.budget import TokenCounter, calibrate_packer, packed_windows
from cpc.claims import build_claims, derive_claims
from cpc.domain import json_text
from cpc.errors import OutputBudgetExceeded
from cpc.experiments import claim_experiment, compression_experiment, hierarchy
from cpc.transport import KEYS, compact_schema, decode, rename
from cpc.views import build_view


class CompactLLM(GroundedLLM):
    def complete(self, prompt, payload, *, schema=None):
        compact = "f" in schema.get("properties", {})
        if compact:
            schema = {"properties": {"fragments": {"items": {"required": ["quote_id"]}}}}
        result = json.loads(super().complete(prompt, payload, schema=schema))
        return json_text(rename(result, KEYS) if compact else result)


def test_compact_quote_dedup_keeps_canonical_storage(core):
    app, repo, snapshot, entity = grounded(core)
    app.llm = CompactLLM()
    before = copy.deepcopy(repo.evidence(snapshot))
    result = app.capture_fragments(snapshot, entity, transport="compact-keys-v1", dedup_quotes=True)
    assert result["status"] == "complete"
    assert repo.evidence(snapshot) == before
    for _, payload in app.llm.calls:
        assert all(set(c) == {"evidence_id"} for c in payload["quote_choices"].values())
    fragments = repo.related_fragments(entity)
    assert fragments and all(f["metadata"]["original_text"] for f in fragments)
    assert all("quote_id" not in f["metadata"] for f in fragments)
    assert not repo.rows("PRAGMA foreign_key_check")


def test_window_input_does_not_leak_unsliced_metadata_body(core):
    app, repo, snapshot, entity = grounded(core)
    before = copy.deepcopy(repo.evidence(snapshot))
    assert any("content" in json.loads(e["metadata"]) for e in before)
    result = app.capture_fragments(snapshot, entity, window_checkpoint=True)
    assert result["status"] == "complete"
    for _, payload in app.llm.calls:
        for row in payload["evidence"] + payload["neighbors"]:
            assert "content" not in row["metadata"]
    assert repo.evidence(snapshot) == before


def test_assessment_retry_identifies_evidence_and_required_null(core):
    app, repo, snapshot, entity = grounded(core)

    class Contradictory(GroundedLLM):
        def complete(self, prompt, payload, *, schema=None):
            response = json.loads(super().complete(prompt, payload, schema=schema))
            feedback = payload.get("validation_error", "")
            cited = {e for f in response["fragments"] for e in f["evidence_ids"]}
            for assessment in response["assessments"]:
                if assessment["evidence_id"] in cited and not feedback:
                    assessment["discard_reason"] = "metadata_only"
            if feedback:
                assert any(e in feedback for e in cited)
                assert "null" in feedback and "Do not discard" in feedback
            return json_text(response)

    app.llm = Contradictory()
    result = app.capture_fragments(snapshot, entity)
    assert result["status"] == "complete"
    assert any(p.get("validation_error") for _, p in app.llm.calls)
    assert not repo.rows("PRAGMA foreign_key_check")


def test_compact_roundtrip_rejects_unknown_and_preserves_null():
    canonical = {
        "type": "object",
        "properties": {"subject": {"type": ["string", "null"]}},
        "required": ["subject"],
        "additionalProperties": False,
    }
    schema = compact_schema(canonical)
    assert decode({"s": None}, schema) == {"subject": None}
    with pytest.raises(ValueError):
        decode({"s": None, "invented": True}, schema)
    with pytest.raises(ValueError):
        rename({"subject": "a", "s": "b"}, KEYS)


def test_window_resume_skips_successful_siblings(core, make_bundle):
    app, repo, _, entity = grounded(core)
    snapshot = app.import_path(make_bundle(html="<main><p>" + "A" * 950 + "</p></main>"))[
        "snapshot"
    ]
    app.process(snapshot)

    class Failing(GroundedLLM):
        def complete(self, prompt, payload, *, schema=None):
            if len(self.calls) == 1 and not self.fail:
                raise RuntimeError("middle window failure")
            return super().complete(prompt, payload, schema=schema)

    app.llm = Failing()
    failed = app.capture_fragments(snapshot, entity, window_checkpoint=True)
    assert failed["status"] == "incomplete"
    assert repo.rows("SELECT * FROM extraction_windows")
    app.llm = GroundedLLM()
    resumed = app.capture_fragments(
        snapshot, entity, window_checkpoint=True, resume=failed["job_id"]
    )
    assert resumed["status"] == "complete"
    assert len(app.llm.calls) == 2
    assert not repo.rows("PRAGMA foreign_key_check")


def test_split_plan_resume_does_not_retry_parent(core, make_bundle):
    app, repo, _, entity = grounded(core)
    snapshot = app.import_path(make_bundle(html="<main><p>" + "A" * 480 + "</p></main>"))[
        "snapshot"
    ]
    app.process(snapshot)

    class Dense(GroundedLLM):
        stop = True

        def complete(self, prompt, payload, *, schema=None):
            length = sum(len(e["content"]) for e in payload["evidence"])
            if length > 240:
                raise OutputBudgetExceeded("dense")
            if self.stop and len(self.calls) == 1:
                raise RuntimeError("child failure")
            return super().complete(prompt, payload, schema=schema)

    app.llm = Dense()
    failed = app.capture_fragments(snapshot, entity, window_checkpoint=True)
    assert failed["status"] == "incomplete" and repo.rows("SELECT * FROM window_splits")
    app.llm.stop = False
    before = len(app.llm.calls)
    resumed = app.capture_fragments(
        snapshot, entity, window_checkpoint=True, resume=failed["job_id"]
    )
    assert resumed["status"] == "complete" and len(app.llm.calls) - before == 2


def test_token_spans_cover_unicode_and_keep_identity():
    counter = TokenCounter()
    text = "ABCあ。😀" * 60
    windows = list(packed_windows([{"id": "e", "content": text, "metadata": {}}], counter, 100))
    covered = set()
    for window in windows:
        for row in window:
            assert row["id"] == "e" and counter.count(row["content"]) <= 100
            assert row["content"] == text[row["span_start"] : row["span_end"]]
            covered.update(range(row["span_start"], row["span_end"]))
    assert covered == set(range(len(text)))


def test_claims_and_views_are_derived_and_budgeted(core):
    app, repo, snapshot, entity = grounded(core)
    app.capture_fragments(snapshot, entity)
    rows = copy.deepcopy(repo.related_fragments(entity))
    claims = build_claims(repo, entity)
    assert claims == build_claims(repo, entity)
    provenance = repo.provenance("claim", claims["claims"][0]["id"])
    assert provenance["supports"] and provenance["supports"][0]["evidence"]
    assert repo.related_fragments(entity) == rows
    assert repo.rows("SELECT * FROM claim_support")
    view = build_view(repo, entity, budget=4000)
    counter = TokenCounter()
    assert counter.count(view["markdown"]) <= 4000
    assert counter.count(json_text(view["structured"])) <= 4000
    assert view["document_id"] and repo.document(view["document_id"])
    assert repo.related_fragments(entity) == rows
    with pytest.raises(ValueError, match="cannot fit"):
        build_view(repo, entity, budget=1)
    changed = copy.deepcopy(rows[0])
    changed["id"] = "different-subject"
    changed["metadata"]["subject"] = "other"
    assert len(derive_claims(entity, [rows[0], changed])) == 2


def test_incremental_embeddings_reuse_and_invalidate_configuration(core):
    app, repo, *_ = core
    original = app.embedder.embed
    calls = []

    def counted(texts, **kwargs):
        calls.append(len(texts))
        return original(texts, **kwargs)

    app.embedder.embed = counted
    first = app.embed(incremental=True)
    assert first["inferred"] > 0
    calls.clear()
    second = app.embed(incremental=True)
    assert second["inferred"] == 0 and second["reused"] == second["embedded"] and not calls
    app.embedder.configuration += " "
    third = app.embed(incremental=True)
    assert third["inferred"] > 0 and calls
    assert not repo.rows("PRAGMA foreign_key_check")


def test_token_packing_uses_full_material_without_rechunking(core, make_bundle, monkeypatch):
    import cpc.capture as capture

    class ExactCounter:
        configuration = {"kind": "unit-test-codepoints", "exact": True}

        def __init__(self, *args):
            pass

        def count(self, text):
            return len(text)

        def request_tokens(self, prompt, payload):
            return len(prompt + json_text(payload))

    monkeypatch.setattr(capture, "TokenCounter", ExactCounter)
    app, repo, _, entity = grounded(core)
    snapshot = app.import_path(make_bundle(html="<main><p>" + "A" * 900 + "</p></main>"))[
        "snapshot"
    ]
    app.process(snapshot)
    before = copy.deepcopy(repo.evidence(snapshot))
    result = app.capture_fragments(
        snapshot,
        entity,
        window_checkpoint=True,
        packer="token",
        material_tokens=1000,
        context_tokens=65536,
    )
    assert result["status"] == "complete" and len(app.llm.calls) == 1
    assert len(app.llm.calls[0][1]["evidence"][0]["content"]) == 900
    assert repo.evidence(snapshot) == before


def test_multi_pass_checkpoint_preserves_successful_focus(core):
    app, repo, snapshot, entity = grounded(core)

    class PassFailure(GroundedLLM):
        stop = True

        def complete(self, prompt, payload, *, schema=None):
            if self.stop and payload["focus"] == "interpretations_and_perception":
                raise RuntimeError("second pass failure")
            return super().complete(prompt, payload, schema=schema)

    app.llm = PassFailure()
    failed = app.capture_fragments(
        snapshot, entity, window_checkpoint=True, strategy="high_recall_multi_pass"
    )
    assert failed["status"] == "incomplete"
    before = len(app.llm.calls)
    app.llm.stop = False
    resumed = app.capture_fragments(
        snapshot,
        entity,
        window_checkpoint=True,
        strategy="high_recall_multi_pass",
        resume=failed["job_id"],
    )
    assert resumed["status"] == "complete" and len(app.llm.calls) == 2 * before
    assert all(p["focus"] == "interpretations_and_perception" for _, p in app.llm.calls[before:])


def test_embedding_failure_does_not_replace_existing_vectors(core):
    app, repo, *_ = core
    app.embed(incremental=True)
    before = repo.rows("SELECT * FROM embeddings ORDER BY item_id")
    original = app.embedder.embed
    app.embedder.revision = "new-revision"
    calls = []

    def failure(texts, **kwargs):
        calls.append(True)
        if len(calls) > 1:
            raise RuntimeError("mid-generation failure")
        return original(texts, **kwargs)

    app.embedder.embed = failure
    with pytest.raises(RuntimeError):
        app.embed(batch_size=1, incremental=True)
    assert repo.rows("SELECT * FROM embeddings ORDER BY item_id") == before


def test_experiments_never_promote_semantic_merges(core):
    app, repo, snapshot, entity = grounded(core)
    app.capture_fragments(snapshot, entity)
    before = copy.deepcopy(repo.related_fragments(entity))
    result = claim_experiment(app, entity, max_pairs=1)
    assert len(result["relations"]) <= 1 and result["promoted_semantic_merges"] == 0
    assert result["semantic_quality"] == "human_gold_missing"
    assert repo.document(result["document_id"])
    result_rows = build_claims(repo, entity)["claims"]
    ids = [i for group in hierarchy(result_rows)["facets"] for i in group["claim_ids"]]
    assert set(ids) == {c["id"] for c in result_rows}
    compressed = compression_experiment(repo, entity, 12000)
    assert [v["ratio"] for v in compressed["variants"]] == [1, 2, 3, 5]
    assert repo.related_fragments(entity) == before
    with pytest.raises(ValueError, match="limits"):
        claim_experiment(app, entity, max_pairs=100)


def test_context_view_requires_consumer_budget(core):
    app, repo, snapshot, entity = grounded(core)
    app.capture_fragments(snapshot, entity)
    with pytest.raises(ValueError, match="must be specified"):
        build_view(repo, entity, mode="context")
    with pytest.raises(ValueError, match="exceeds"):
        build_view(repo, entity, mode="context", context_tokens=1000)
    result = build_view(repo, entity, mode="context", context_tokens=16384)
    assert result["configuration"]["budget"] == 12000
    assert result["output_tokens"] <= 12000


def test_existing_02_migration_preserves_entities(tmp_path):
    import sqlite3
    from pathlib import Path

    from cpc.repository import Repository

    path = tmp_path / "old-02.sqlite"
    db = sqlite3.connect(path)
    for name in ("001_initial.sql", "002_knowledge_capture.sql"):
        db.executescript((Path("src/cpc/migrations") / name).read_text(encoding="utf-8"))
    db.executescript(
        "CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY);"
        "INSERT INTO schema_migrations VALUES(1),(2);"
    )
    db.execute(
        "INSERT INTO entities VALUES(?,?,?,?,?)", ("old", "Character", "old-name", "[]", "2020")
    )
    db.commit()
    db.close()
    repo = Repository(path)
    assert repo.entity("old")["name"] == "old-name"
    assert repo.one("PRAGMA integrity_check")["integrity_check"] == "ok"
    assert not repo.rows("PRAGMA foreign_key_check")
    repo.close()


def test_exact_counter_only_uses_loaded_model(monkeypatch):
    import sys
    from types import SimpleNamespace

    import httpx

    loaded = {"models": [{"key": "test-model", "loaded_instances": [{"id": "loaded-1"}]}]}
    monkeypatch.setattr(
        "cpc.budget.httpx.get",
        lambda *a, **k: httpx.Response(
            200, json=loaded, request=httpx.Request("GET", "http://localhost/models")
        ),
    )
    calls = []

    def get_model(identifier):
        calls.append(identifier)
        return SimpleNamespace(
            tokenize=lambda s: list(s),
            get_context_length=lambda: 16384,
            apply_prompt_template=lambda chat: json_text(chat),
        )

    monkeypatch.setitem(
        sys.modules,
        "lmstudio",
        SimpleNamespace(llm=get_model, Chat=SimpleNamespace(from_history=lambda history: history)),
    )
    counter = TokenCounter("lmstudio", "test-model")
    assert counter.count("ABC") == 3 and counter.configuration["exact"]
    assert counter.request_tokens("instruction", {"x": "data"}) > 3
    assert calls == ["loaded-1"]
    with pytest.raises(ValueError, match="already loaded"):
        TokenCounter("lmstudio", "unloaded-model")


def test_native_factory_defaults_to_prompt_only(monkeypatch):
    from cpc.providers import LMStudioLLM, llm_from_env

    monkeypatch.setenv("CPC_LLM_PROVIDER", "lmstudio")
    monkeypatch.setenv("CPC_LLM_MODEL", "unit-test")
    monkeypatch.delenv("CPC_LLM_STRUCTURED_MODE", raising=False)
    assert llm_from_env().configuration["structured_mode"] == "prompt_only"
    with pytest.raises(ValueError, match="compatible"):
        LMStudioLLM("http://localhost/v1", "unit-test", structured_mode="api_schema")


def test_claim_normalization_preserves_decimal_and_negation():
    rows = [
        {"id": str(i), "facet": "number", "content": text, "metadata": {}}
        for i, text in enumerate(("Value 1.2.", "Value 12.", "Not value 1.2.", "Value 1.2!"))
    ]
    claims = derive_claims("entity", rows)
    assert len(claims) == 3
    assert any(c["fragment_ids"] == ["0", "3"] for c in claims)


def test_experimental_judge_records_proposals_without_promotion(core):
    app, repo, snapshot, entity = grounded(core)
    app.capture_fragments(snapshot, entity)
    before = copy.deepcopy(repo.related_fragments(entity))

    class Judge(GroundedLLM):
        def complete(self, prompt, payload, *, schema=None):
            return json_text({"relation": "related"})

    app.llm = Judge()
    result = claim_experiment(app, entity, max_pairs=1, judge=True)
    assert result["relations"] and result["relations"][0]["status"] == "proposed"
    assert result["promoted_semantic_merges"] == 0
    assert repo.related_fragments(entity) == before


def test_packer_freezes_observed_output_ratio(core):
    repo = core[1]
    ai = repo.begin_ai(
        "high_recall_fragment",
        "model",
        "rev",
        "prompt",
        "v1",
        {
            "provider_configuration": {},
            "payload": {"evidence": [{"content": "ABC"}]},
            "response_schema": {"properties": {"fragments": {}}},
        },
    )
    repo.observe_ai(ai, {"usage": {"completion_tokens": 30}})
    repo.finish_ai(ai, "{}")
    counter = TokenCounter()
    counter.configuration["exact"] = True
    result = calibrate_packer(repo, counter, {}, "canonical", 2000, 3000, "model", "rev")
    assert result["material_target"] == 240 and result["sample_ai_runs"] == [ai]
    assert (
        calibrate_packer(repo, counter, {}, "canonical", 2000, 3000, "model", "other")[
            "material_target"
        ]
        == 2000
    )


def test_legacy_job_resume_preserves_original_options(core):
    app, repo, snapshot, entity = grounded(core)
    result = app.capture_fragments(snapshot, entity)
    job = repo.extraction_job(result["job_id"])
    added = {
        "transport",
        "transport_hash",
        "dedup_quotes",
        "window_checkpoint",
        "packer",
        "material_tokens",
        "context_tokens",
        "output_tokens",
        "safety_margin",
        "token_counter",
    }
    old = {k: v for k, v in job["configuration"].items() if k not in added}
    old["algorithm"] = "full-evidence-v4-adaptive-quote-selection"
    with repo.db:
        repo.db.execute(
            "UPDATE extraction_jobs SET configuration=? WHERE id=?",
            (json_text(old), result["job_id"]),
        )
    assert app.capture_fragments(snapshot, entity, resume=result["job_id"])["status"] == "complete"
    with pytest.raises(ValueError, match="original extraction"):
        app.capture_fragments(snapshot, entity, resume=result["job_id"], dedup_quotes=True)
