"""I-07 formal reranker comparison on the frozen Search quality gold."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sgokb.domain import ObjectSearchFilters, SearchRepresentationKind  # noqa: E402
from sgokb.repository import Repository  # noqa: E402
from sgokb.retrieval import (  # noqa: E402
    ExactVectorIndexAdapter,
    HybridObjectSearch,
    KnowledgeVectorIndexBuilder,
    default_sentence_transformer_provider,
    ranked_retrieval_metrics,
)

MODELS = {
    "bge": {
        "model": "BAAI/bge-reranker-v2-m3",
        "revision": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
        "max_length": 1024,
        "batch": 32,
    },
    "zerank2": {
        "model": "zeroentropy/zerank-2-reranker",
        "revision": "5eae30d5ee3c6b2df2ef6d723bde45172d761c4c",
        "max_length": 4096,
        "batch": 32,
    },
}


def aggregate(rows):
    if not rows:
        return {}
    return {key: statistics.fmean(float(row[key]) for row in rows) for key in rows[0]}


def resolve_statement_ref(repo, ref):
    head, local_key = ref.rsplit(":", 1)
    object_id, version_ref = head.split("@", 1)
    if version_ref == "current":
        version_id = repo.db.execute(
            "SELECT current_version_id FROM objects WHERE id=?", (object_id,)
        ).fetchone()["current_version_id"]
    else:
        # fixture IDs are ver:<short-object-id>:vN
        short = object_id.split(":", 1)[1]
        version_id = f"ver:{short}:{version_ref}"
    row = repo.db.execute(
        "SELECT id FROM knowledge_statements WHERE version_id=? AND local_key=?",
        (version_id, local_key),
    ).fetchone()
    if not row:
        raise ValueError(f"Unknown statement gold ref: {ref}")
    return row["id"]


def object_overall_text(repo, object_id, version_id):
    row = repo.db.execute(
        """SELECT r.content FROM knowledge_search_representation_memberships m
           JOIN search_representations r ON r.id=m.representation_id
           WHERE m.object_id=? AND m.version_id=? AND m.target_kind='object_overall'""",
        (object_id, version_id),
    ).fetchone()
    return row["content"] if row else None


def prepare_cases(repo, gold, provider, index, hybrid):
    rep_text = {
        row["id"]: row["content"]
        for row in repo.rows("SELECT id,content FROM search_representations")
    }
    cases = []
    for case in gold["search_queries"]:
        if not case.get("statement_refs"):
            continue
        filters = ObjectSearchFilters(**case.get("filters", {}))
        qvec = provider.embed_queries([case["query"]])[0]
        vf = hybrid._vector_filters(filters, SearchRepresentationKind.STATEMENT)
        hits = index.search(provider.space, qvec, limit=50, filters=vf)
        statement_candidates = []
        for hit in hits:
            statement_candidates.append(
                {
                    "statement_id": hit.metadata.get("statement_id"),
                    "object_id": hit.metadata.get("object_id"),
                    "version_id": hit.metadata.get("version_id"),
                    "text": rep_text[str(hit.metadata.get("representation_id"))],
                }
            )
        relevant_statements = {
            resolve_statement_ref(repo, ref): 3 for ref in case["statement_refs"]
        }
        hybrid_response = hybrid.search(case["query"], filters=filters, limit=20, mode="hybrid")
        object_candidates = []
        for result in hybrid_response.results:
            text = object_overall_text(repo, result.object_id, result.version_id)
            if text:
                object_candidates.append(
                    {"object_id": result.object_id, "version_id": result.version_id, "text": text}
                )
        cases.append(
            {
                "id": case["id"],
                "query": case["query"],
                "object_relevance": case["relevance"],
                "statement_relevance": relevant_statements,
                "statement_candidates": statement_candidates,
                "object_candidates": object_candidates,
            }
        )
    return cases


def evaluate_model(spec, cases):
    torch.cuda.empty_cache()
    model = CrossEncoder(
        spec["model"],
        revision=spec["revision"],
        device="cuda",
        max_length=spec["max_length"],
        model_kwargs={"dtype": torch.bfloat16, "attn_implementation": "sdpa"},
    )
    # warm
    model.predict([("warmup", "warmup")], batch_size=1, show_progress_bar=False)
    torch.cuda.reset_peak_memory_stats()
    statement_rows = []
    grouped_rows = []
    object_rows = []
    lats = []
    object_lats = []
    candidate_recall = []
    case_results = []
    for case in cases:
        candidates = case["statement_candidates"]
        relevance = case["statement_relevance"]
        candidate_recall.append(float(any(c["statement_id"] in relevance for c in candidates)))
        t0 = time.perf_counter()
        scores = np.asarray(
            model.predict(
                [(case["query"], c["text"]) for c in candidates],
                batch_size=spec["batch"],
                show_progress_bar=False,
            )
        ).reshape(-1)
        lats.append(time.perf_counter() - t0)
        order = np.argsort(-scores)
        ranked_statements = [candidates[i]["statement_id"] for i in order]
        statement_metric = ranked_retrieval_metrics(ranked_statements, relevance)
        statement_rows.append(statement_metric)
        grouped = []
        for i in order:
            oid = candidates[i]["object_id"]
            if oid not in grouped:
                grouped.append(oid)
        grouped_metric = ranked_retrieval_metrics(grouped, case["object_relevance"])
        grouped_rows.append(grouped_metric)

        oc = case["object_candidates"]
        t0 = time.perf_counter()
        oscores = np.asarray(
            model.predict(
                [(case["query"], c["text"]) for c in oc],
                batch_size=spec["batch"],
                show_progress_bar=False,
            )
        ).reshape(-1)
        object_lats.append(time.perf_counter() - t0)
        oorder = np.argsort(-oscores)
        ranked_objects = [oc[i]["object_id"] for i in oorder]
        object_metric = ranked_retrieval_metrics(ranked_objects, case["object_relevance"])
        object_rows.append(object_metric)
        case_results.append(
            {
                "id": case["id"],
                "statement": statement_metric,
                "statement_to_object": grouped_metric,
                "object_rerank": object_metric,
            }
        )
    result = {
        "model": spec["model"],
        "revision": spec["revision"],
        "candidate_recall@50": statistics.fmean(candidate_recall),
        "statement_quality": aggregate(statement_rows),
        "statement_to_object_quality": aggregate(grouped_rows),
        "object_level_quality": aggregate(object_rows),
        "statement_rerank_p50_ms": statistics.median(lats) * 1000,
        "object_rerank_p50_ms": statistics.median(object_lats) * 1000,
        "peak_allocated_gb": torch.cuda.max_memory_allocated() / 1024**3,
        "cases": case_results,
    }
    del model
    torch.cuda.empty_cache()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=ROOT / ".local/i07-search-gold.sqlite")
    ap.add_argument("--fixture", type=Path, default=ROOT / "benchmark/search-quality-gold-v1.json")
    ap.add_argument("--output", type=Path, default=ROOT / ".local/i07-reranker-result.json")
    ap.add_argument("--cache", type=Path, default=ROOT / ".local/hf-2026/hub")
    args = ap.parse_args()
    gold = json.loads(args.fixture.read_text(encoding="utf-8"))
    repo = Repository(args.db)
    try:
        provider = default_sentence_transformer_provider(
            cache_folder=str(args.cache), local_files_only=True
        )
        index = ExactVectorIndexAdapter()
        points = KnowledgeVectorIndexBuilder(repo, index).points(provider.space)
        index.rebuild(provider.space, points)
        hybrid = HybridObjectSearch(repo, embedding_provider=provider, vector_index=index)
        cases = prepare_cases(repo, gold, provider, index, hybrid)
        results = {key: evaluate_model(spec, cases) for key, spec in MODELS.items()}
        out = {
            "schema_version": "sgokb.search-reranker-benchmark/1.0",
            "dataset_id": gold["dataset_id"],
            "cases": len(cases),
            "results": results,
        }
        args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {k: {x: y for x, y in v.items() if x != "cases"} for k, v in results.items()},
                ensure_ascii=False,
                indent=2,
            )
        )
        print("saved", args.output)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
