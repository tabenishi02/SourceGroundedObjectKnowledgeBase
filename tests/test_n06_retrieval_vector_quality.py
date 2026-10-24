"""N-06 frozen gates, namespace safety and R2-only evaluation contracts."""

from __future__ import annotations

import copy
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark/tools"))
import n06_retrieval_vector_quality as harness  # noqa: E402
from n06_evaluate_retrieval_vector_quality import evaluate, recall_at_10  # noqa: E402
from n06_studies import active_r2_vectors, exact_top_10  # noqa: E402

from sgokb.domain import EmbeddingSpaceSpec, VectorMatch, VectorSearchFilter  # noqa: E402
from sgokb.repository import Repository  # noqa: E402
from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter  # noqa: E402

CONTRACT = json.loads(
    (ROOT / "benchmark/n06-retrieval-vector-quality-contract-v1.json").read_text(encoding="utf-8")
)


class Provider:
    space = EmbeddingSpaceSpec(
        provider_key="unit",
        provider_version="1",
        model="unit",
        model_revision="1",
        dimension=3,
        native_dimension=3,
        preprocessing_key="unit",
        preprocessing_version="1",
    )

    def embed_documents(self, texts):
        return [[1.0, 0.1, 0.2] for _ in texts]

    embed_queries = embed_documents


def valid_evidence():
    gates = CONTRACT["synthetic_search"]["gates"].copy()
    real = CONTRACT["real_data"]["gates"].copy()
    cases = [{"exact_ids": list(range(10)), "ann_ids": list(range(10))} for _ in range(72)]
    stages = {s: {"status": "PASS"} for s in "ABCDEFGH"}
    stages["B"].update(
        gates=gates, contracts={"passed": 5, "total": 5}, similarity_passed=4, evidence_passed=6
    )
    stages["C"]["gates"] = real
    stages["D"]["direct_statement_search_enabled"] = True
    for model, value in CONTRACT["reranker"]["models"].items():
        stages["E"][model] = {"revision": value["revision"], "cases": [{}] * 22}
    stages["F"].update(
        indexed_points=100000,
        unfiltered={"cases": cases},
        filtered={"cases": copy.deepcopy(cases)},
        identity_violations=0,
        profile=CONTRACT["ann_100k"]["qdrant"],
        initial_build_seconds=1,
        full_rebuild_seconds=1,
        update_100_seconds=1,
    )
    stages["H"].update(
        safety={
            s: True
            for s in (
                "canonical_unchanged",
                "preserved_n03_unchanged",
                "reference_qdrant_unchanged",
                "head_unchanged",
                "tracked_unchanged",
                "r1_unchanged",
            )
        },
        regression={s: 0 for s in ("focused", "full", "ruff", "diff")},
    )
    return {"stages": stages}


def test_complete_evaluator_pass_is_deterministic():
    e = valid_evidence()
    before = copy.deepcopy(e)
    assert evaluate(e, CONTRACT) == evaluate(e, CONTRACT)
    assert evaluate(e, CONTRACT)["overall"] == "PASS"
    assert e == before


@pytest.mark.parametrize(
    "change", ["mean", "minimum", "indexed", "payload", "identity", "safety", "regression"]
)
def test_evaluator_rejects_valid_measured_gate_failure(change):
    e = valid_evidence()
    f = e["stages"]["F"]
    if change == "mean":
        for row in f["unfiltered"]["cases"]:
            row["ann_ids"][-1] = 100
    elif change == "minimum":
        f["filtered"]["cases"][0]["ann_ids"] = list(range(8)) + [100, 101]
    elif change == "indexed":
        f["indexed_points"] = 99999
    elif change == "payload":
        f["identity_violations"] = 1
    elif change == "identity":
        e["stages"]["C"]["gates"]["identity_rank1_required"] = False
    elif change == "safety":
        e["stages"]["H"]["safety"]["r1_unchanged"] = False
    else:
        e["stages"]["H"]["regression"]["full"] = 1
    assert evaluate(e, CONTRACT)["overall"] == "FAIL"


@pytest.mark.parametrize("change", ["missing", "blocked", "bad_reference", "nan"])
def test_incomplete_evidence_cannot_pass(change):
    e = valid_evidence()
    if change == "missing":
        del e["stages"]["E"]
    elif change == "blocked":
        e["stages"]["C"]["status"] = "BLOCKED"
    elif change == "bad_reference":
        e["stages"]["F"]["unfiltered"]["cases"][0]["exact_ids"] = [1] * 10
    else:
        e["stages"]["B"]["gates"]["hybrid_mrr"] = float("nan")
    assert evaluate(e, CONTRACT)["overall"] != "PASS"


def test_exact_recall_uses_ids_not_positions():
    assert recall_at_10(list(range(9, -1, -1)), list(range(10))) == 1
    assert recall_at_10(list(range(5, 15)), list(range(10))) == 0.5


def test_filtered_exact_reference_uses_same_partition():
    vectors = np.eye(24, dtype=np.float32)
    query = np.ones(24, dtype=np.float32)
    scopes = np.arange(24) % 2
    ids = exact_top_10(vectors, query, scopes, 1)
    assert len(ids) == 10 and all(scopes[i] == 1 for i in ids)


def test_ablation_affects_only_object_view_and_leaves_direct_search():
    calls = []
    base = SimpleNamespace(backend_key="unit", search=lambda *a, **kw: calls.append(kw) or (1,))
    view = harness.ObjectAblationIndex(base)
    filters = VectorSearchFilter(matches=(VectorMatch("kind", ("statement",)),))
    assert view.search(None, [], limit=10, filters=filters) == ()
    assert not calls
    assert base.search(None, [], limit=10, filters=filters) == (1,)
    filters = VectorSearchFilter(matches=(VectorMatch("kind", ("facet",)),))
    assert view.search(None, [], limit=10, filters=filters) == (1,)


def test_statement_grouping_preserves_first_occurrence():
    assert harness.grouped_objects([{"object_id": x} for x in ["B", "A", "B", "C"]]) == [
        "B",
        "A",
        "C",
    ]


def test_n03_read_only_backup_never_mutates_preserved_file(tmp_path):
    source = tmp_path / "source.sqlite"
    db = sqlite3.connect(source)
    db.execute("CREATE TABLE canonical(value TEXT)")
    db.execute("INSERT INTO canonical VALUES ('preserved')")
    db.commit()
    db.close()
    before = source.read_bytes()
    destination = tmp_path / "copy.sqlite"
    harness.copy_n03(source, destination)
    db = sqlite3.connect(destination)
    db.execute("DELETE FROM canonical")
    db.commit()
    db.close()
    assert source.read_bytes() == before
    with pytest.raises(FileExistsError):
        harness.copy_n03(source, destination)
    with pytest.raises(RuntimeError, match="BLOCKED_N03_ASSET_UNAVAILABLE"):
        harness.copy_n03(tmp_path / "missing.sqlite", tmp_path / "new.sqlite")


def test_run_namespaces_are_isolated_and_do_not_accept_production_names():
    names = {
        harness.namespace(run, purpose) for run in ("a", "b") for purpose in ("gold", "real", "ann")
    }
    assert len(names) == 6 and all(n.startswith("n06") for n in names)
    with pytest.raises(ValueError):
        harness.namespace("a", "production")


def test_fresh_gold_is_active_r2_without_legacy_membership(tmp_path, monkeypatch):
    index = QdrantVectorIndexAdapter(client=QdrantClient(":memory:"), wait_for_index=False)
    monkeypatch.setattr(harness, "QdrantVectorIndexAdapter", lambda **kw: index)
    repo = Repository(tmp_path / "r2.sqlite")
    try:
        gold = harness.read(ROOT / "benchmark/search-quality-gold-v1.json")
        routed, refs, audit = harness.prepare_generation(repo, Provider(), "n06unit", gold)
        assert audit["leakage"] == 0
        # Direct Statement evaluation is a separate request, after Hybrid context reset.
        engine = harness.HybridObjectSearch(
            repo, embedding_provider=Provider(), vector_index=routed
        )
        engine.search(gold["objects"][0]["name"], mode="hybrid")
        hits = harness.statement_candidates(engine, routed, Provider(), "probe")
        assert hits and all(hit["statement_id"] for hit in hits)
        for hit in hits:
            assert (
                repo.one(
                    "SELECT 1 AS linked FROM knowledge_search_generation_memberships gm "
                    "JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id "
                    "WHERE gm.generation_id=? AND m.statement_id=?",
                    (audit["generation_id"], hit["statement_id"]),
                )["linked"]
                == 1
            )
        from dataclasses import replace

        real_search = routed.search

        def corrupted(*args, **kwargs):
            rows = real_search(*args, **kwargs)
            return (replace(rows[0], metadata={**rows[0].metadata, "generation_id": "wrong"}),)

        with monkeypatch.context() as context:
            context.setattr(routed, "search", corrupted)
            with pytest.raises(RuntimeError, match="generation payload mismatch"):
                harness.statement_candidates(engine, routed, Provider(), "probe")

        assert set(audit["kinds"]) == {"object_overview", "facet", "statement"}
        assert len(refs["current_versions"]) == len(gold["objects"])
        assert not repo.rows("SELECT * FROM search_representations WHERE kind='object_overall'")
        base, generation, ids = active_r2_vectors(repo, Provider())
        assert len(base) == len(ids) and generation == audit["generation_id"]
        assert all(
            point.metadata["generation_id"] == generation
            for point in __import__(
                "sgokb.retrieval", fromlist=["KnowledgeVectorMaintenanceBuilder"]
            )
            .KnowledgeVectorMaintenanceBuilder(repo, routed)
            .points(Provider.space)
        )
        with repo.db:
            repo.db.execute(
                "UPDATE knowledge_search_generations SET contract_key='wrong' WHERE id=?",
                (generation,),
            )
        with pytest.raises(RuntimeError, match="R2"):
            harness.assert_r2(repo, routed, Provider.space)
        with pytest.raises(RuntimeError, match="active R2"):
            active_r2_vectors(repo, Provider())
    finally:
        index._client.close()
        repo.close()


def test_reranker_source_has_no_legacy_object_path():
    source = (ROOT / "benchmark/tools/n06_studies.py").read_text(encoding="utf-8")
    assert "object_overall_text" not in source
    assert 'case["candidates"]' in source
    assert 'case["object_relevance"]' in source
