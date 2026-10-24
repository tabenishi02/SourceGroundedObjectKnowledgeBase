"""Evaluation-only Statement reranking and isolated fixed-profile 100k ANN."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from n06_evaluate_retrieval_vector_quality import recall_at_10
from n06_retrieval_vector_quality import grouped_objects, namespace

from sgokb.retrieval import aggregate_metric_rows, latency_summary, ranked_retrieval_metrics


def reranker_study(cases, contract, cache, run):
    import numpy as np
    import torch
    from sentence_transformers import CrossEncoder

    output = {"status": "PASS", "adoption_recommendation": "remain optional"}
    for key, spec in contract["reranker"]["models"].items():
        maximum = 1024 if key == "bge" else 4096
        model = CrossEncoder(
            spec["model"],
            revision=spec["revision"],
            device="cuda",
            max_length=maximum,
            cache_folder=str(cache),
            local_files_only=True,
            model_kwargs={"dtype": torch.bfloat16, "attn_implementation": "sdpa"},
        )
        actual_revision = getattr(model.model.config, "_commit_hash", None)
        if actual_revision is not None and actual_revision != spec["revision"]:
            raise RuntimeError("Reranker loaded an unexpected revision")
        model.predict([("neutral", "neutral")], batch_size=1, show_progress_bar=False)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        rows = []
        statements = []
        objects = []
        lats = []
        recall = []
        for case in cases:
            candidates = case["candidates"]
            pairs = [(case["query"], c["text"]) for c in candidates]
            lengths = model.tokenizer(pairs, truncation=False, padding=False)["input_ids"]
            if any(len(ids) > maximum for ids in lengths):
                raise RuntimeError("BLOCKED_RERANK_INPUT_EXCEEDS_FIXED_LENGTH")
            torch.cuda.synchronize()
            started = time.perf_counter()
            scores = np.asarray(
                model.predict(pairs, batch_size=32, show_progress_bar=False)
            ).reshape(-1)
            torch.cuda.synchronize()
            lats.append(time.perf_counter() - started)
            if len(scores) != len(candidates) or not np.isfinite(scores).all():
                raise RuntimeError("Invalid reranker scores")
            order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))
            ranked = [candidates[i] for i in order]
            ids = [c["statement_id"] for c in ranked]
            rel = case["statement_relevance"]
            sm = ranked_retrieval_metrics(ids, rel)
            grouped = grouped_objects(ranked)
            om = ranked_retrieval_metrics(grouped, case["object_relevance"])
            statements.append(sm)
            objects.append(om)
            recall.append(len({c["statement_id"] for c in candidates} & set(rel)) / len(rel))
            rows.append(
                {
                    "id": case["id"],
                    "candidate_count": len(candidates),
                    "statement_ids": ids,
                    "object_ids": grouped,
                    "scores": [float(scores[i]) for i in order],
                    "statement_metrics": sm,
                    "object_metrics": om,
                }
            )
        output[key] = {
            **spec,
            "candidate_recall_at_50": statistics.fmean(recall),
            "statement_quality": aggregate_metric_rows(statements),
            "object_quality": aggregate_metric_rows(objects),
            "latency": latency_summary(lats),
            "cases": rows,
            "peak_allocated": torch.cuda.max_memory_allocated(),
            "peak_reserved": torch.cuda.max_memory_reserved(),
        }
        (run / ("reranker-" + key + ".json")).write_text(
            json.dumps(output[key], indent=2),
            encoding="utf-8",
        )
        del model
    return output


def active_r2_vectors(repo, provider):
    import numpy as np

    row = repo.one(
        "SELECT g.* FROM knowledge_search_active_generation a "
        "JOIN knowledge_search_generations g ON g.id=a.active_generation_id"
    )
    if row is None or (row["contract_key"], row["contract_version"], row["state"]) != (
        "n05d04r2-hierarchical-v2",
        2,
        "ready",
    ):
        raise RuntimeError("ANN source is not active R2")
    records = repo.rows(
        "SELECT DISTINCT r.id,r.kind FROM search_representations r "
        "JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id "
        "JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id "
        "WHERE gm.generation_id=? ORDER BY r.id",
        (row["id"],),
    )
    if not records or any(
        r["kind"] not in {"object_overview", "facet", "statement"} for r in records
    ):
        raise RuntimeError("Invalid active-R2 fixture source vectors")
    ids = [r["id"] for r in records]
    vectors = {
        r["representation_id"]: r["vector"]
        for r in repo.embedding_store.embedding_rows(provider.space.space_id, ids)
    }
    if set(vectors) != set(ids):
        raise RuntimeError("Incomplete source embeddings")
    return np.asarray([vectors[i] for i in ids], dtype=np.float32), row["id"], ids


def exact_top_10(vectors, query, scopes, scope=None):
    import numpy as np

    ids = np.arange(len(vectors)) if scope is None else np.flatnonzero(scopes == scope)
    scores = vectors[ids] @ query
    order = np.argpartition(-scores, 9)[:10]
    order = order[np.argsort(-scores[order], kind="stable")]
    return ids[order].astype(int).tolist()


def ann_study(repo, index, provider, gold, contract, run):
    import numpy as np
    from qdrant_client import QdrantClient, models

    spec = contract["ann_100k"]
    base, generation_id, source_ids = active_r2_vectors(repo, provider)
    n, dim = spec["points"], spec["dimension"]
    rng = np.random.default_rng(20261014)
    selected = rng.integers(0, len(base), size=(n, 3), dtype=np.int32)
    weights = rng.uniform(0.15, 1.0, size=(n, 3)).astype(np.float32)
    weights /= weights.sum(axis=1, keepdims=True)
    vectors = sum(base[selected[:, i]] * weights[:, i, None] for i in range(3))
    vectors += rng.normal(0, spec["noise_sigma"], vectors.shape).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    scopes = (np.arange(n) % spec["hard_filter_partitions"]).astype(np.int32)
    queries = provider.embed_queries([q["query"] for q in gold["search_queries"]])
    assert len(queries) == spec["queries"]
    client = QdrantClient(
        url="http://localhost:6333", grpc_port=6334, prefer_grpc=True, timeout=180
    )
    collection = namespace(run.name, "ann") + "_100k"
    if client.collection_exists(collection):
        raise FileExistsError("Never reuse another benchmark namespace")
    profile = spec["qdrant"]

    def payload(i):
        return {
            "scope": int(scopes[i]),
            "generation_id": generation_id,
            "space_id": provider.space.space_id,
            "fixture_id": int(i),
        }

    def wait_ready():
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            info = client.get_collection(collection)
            if (
                info.points_count == n
                and info.indexed_vectors_count == n
                and "green" in str(info.status).lower()
            ):
                return info
            time.sleep(0.5)
        raise RuntimeError("Qdrant did not complete fixed-profile indexing")

    def build():
        started = time.perf_counter()
        client.create_collection(
            collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            hnsw_config=models.HnswConfigDiff(m=16, ef_construct=128, full_scan_threshold=10),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=0, default_segment_number=2
            ),
        )
        for field, schema in [
            ("scope", models.PayloadSchemaType.INTEGER),
            ("generation_id", models.PayloadSchemaType.KEYWORD),
            ("space_id", models.PayloadSchemaType.KEYWORD),
        ]:
            client.create_payload_index(collection, field, field_schema=schema, wait=True)
        client.upload_collection(
            collection,
            vectors=vectors,
            ids=range(n),
            payload=(payload(i) for i in range(n)),
            batch_size=512,
            parallel=1,
            wait=True,
        )
        client.update_collection(
            collection, optimizers_config=models.OptimizersConfigDiff(indexing_threshold=1000)
        )
        info = wait_ready()
        return time.perf_counter() - started, info

    try:
        initial, info = build()
        output = {
            "status": "PASS",
            "profile": profile,
            "indexed_points": info.indexed_vectors_count,
            "source_generation_id": generation_id,
            "source_representation_ids": source_ids,
            "namespace": collection,
            "initial_build_seconds": initial,
            "unfiltered": {"cases": []},
            "filtered": {"cases": []},
        }
        (run / "ann-partial.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
        for mode in ("unfiltered", "filtered"):
            for repeat in range(3):
                for i, query in enumerate(queries):
                    scope = i % 8 if mode == "filtered" else None
                    q = np.asarray(query, dtype=np.float32)
                    t = time.perf_counter()
                    exact = exact_top_10(vectors, q, scopes, scope)
                    exact_seconds = time.perf_counter() - t
                    must = [
                        models.FieldCondition(
                            key="generation_id", match=models.MatchValue(value=generation_id)
                        ),
                        models.FieldCondition(
                            key="space_id", match=models.MatchValue(value=provider.space.space_id)
                        ),
                    ]
                    if scope is not None:
                        must.append(
                            models.FieldCondition(key="scope", match=models.MatchValue(value=scope))
                        )
                    t = time.perf_counter()
                    hits = client.query_points(
                        collection,
                        query=query,
                        query_filter=models.Filter(must=must),
                        search_params=models.SearchParams(hnsw_ef=768, exact=False),
                        limit=10,
                        with_payload=True,
                    ).points
                    seconds = time.perf_counter() - t
                    ids = [int(h.id) for h in hits]
                    assert all(h.payload == payload(int(h.id)) for h in hits)
                    assert scope is None or all(scopes[x] == scope for x in ids)
                    output[mode]["cases"].append(
                        {
                            "query": gold["search_queries"][i]["id"],
                            "repeat": repeat,
                            "scope": scope,
                            "exact_ids": exact,
                            "ann_ids": ids,
                            "recall_at_10": recall_at_10(ids, exact),
                            "exact_seconds": exact_seconds,
                            "ann_seconds": seconds,
                        }
                    )
            rows = output[mode]["cases"]
            output[mode].update(
                mean_recall_at_10=statistics.fmean(r["recall_at_10"] for r in rows),
                min_recall_at_10=min(r["recall_at_10"] for r in rows),
                exact_latency=latency_summary([r["exact_seconds"] for r in rows]),
                ann_latency=latency_summary([r["ann_seconds"] for r in rows]),
            )

        (run / "ann-partial.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

        def points(values):
            return [
                models.PointStruct(id=i, vector=values[i].tolist(), payload=payload(i))
                for i in range(100)
            ]

        modified = vectors[:100] + rng.normal(0, 0.001, (100, dim)).astype(np.float32)
        modified /= np.linalg.norm(modified, axis=1, keepdims=True)
        t = time.perf_counter()
        client.upsert(collection, points=points(modified), wait=True)
        output["update_100_seconds"] = time.perf_counter() - t
        client.upsert(collection, points=points(vectors[:100]), wait=True)
        # Rebuild only this successful run-owned namespace; retain any failed collection.
        client.delete_collection(collection)
        output["full_rebuild_seconds"], info = build()
        seen = set()
        offset = None
        while True:
            records, offset = client.scroll(collection, limit=512, offset=offset, with_payload=True)
            for record in records:
                i = int(record.id)
                if i in seen or record.payload != payload(i):
                    raise RuntimeError("ANN payload/generation identity violation")
                seen.add(i)
            if offset is None:
                break
        if seen != set(range(n)):
            raise RuntimeError("ANN fixture identity mismatch")
        output["identity_violations"] = 0
        storage = Path(r"C:\Qdrant\SGOKB\storage\collections") / collection
        output["index_disk_bytes"] = sum(
            p.stat().st_size for p in storage.rglob("*") if p.is_file()
        )
        import psutil

        output["qdrant_working_set"] = [
            p.memory_info().rss
            for p in psutil.process_iter(["name"])
            if p.info["name"].lower() == "qdrant.exe"
        ]
        output["indexed_points"] = info.indexed_vectors_count
        return output
    finally:
        client.close()
