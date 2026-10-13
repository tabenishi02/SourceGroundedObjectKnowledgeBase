"""I-07 ANN backend benchmark using vectors derived from the frozen Search gold."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sgokb.repository import Repository  # noqa: E402
from sgokb.retrieval import default_sentence_transformer_provider  # noqa: E402


def directory_bytes(path: Path) -> int:
    return (
        sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        if path.exists()
        else 0
    )


def latency_summary(values):
    ordered = sorted(values)
    return {
        "p50_ms": statistics.median(ordered),
        "p95_ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))],
        "mean_ms": statistics.fmean(ordered),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / ".local/i07-search-gold.sqlite")
    parser.add_argument(
        "--fixture", type=Path, default=ROOT / "benchmark/search-quality-gold-v1.json"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / ".local/i07-vector-backend-result.json"
    )
    parser.add_argument("--cache", type=Path, default=ROOT / ".local/hf-2026/hub")
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--url", default="http://localhost:6337")
    parser.add_argument("--grpc-port", type=int, default=6338)
    parser.add_argument("--storage", type=Path, default=Path(r"C:\sgokb-qdrant-i07\storage"))
    parser.add_argument("--hnsw-ef", type=int, default=768)
    args = parser.parse_args()

    try:
        from qdrant_client import QdrantClient, models
        from qdrant_client import __version__ as client_version
    except ImportError:
        from importlib.metadata import version

        from qdrant_client import QdrantClient, models

        client_version = version("qdrant-client")

    gold = json.loads(args.fixture.read_text(encoding="utf-8"))
    repo = Repository(args.db)
    try:
        spaces = repo.embedding_store.db.execute(
            "SELECT id FROM search_embedding_spaces ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        if not spaces:
            raise RuntimeError("Run run_search_quality_gold.py first")
        space_id = spaces["id"]
        rows = repo.embedding_store.embedding_rows(space_id)
        base = np.asarray([row["vector"] for row in rows], dtype=np.float32)
    finally:
        repo.close()
    provider = default_sentence_transformer_provider(
        cache_folder=str(args.cache), local_files_only=True
    )
    if provider.space.space_id != space_id:
        raise RuntimeError("Gold DB Embedding Space differs from frozen provider")
    queries = np.asarray(
        provider.embed_queries([item["query"] for item in gold["search_queries"]]), dtype=np.float32
    )
    n, dim = args.count, base.shape[1]
    rng = np.random.default_rng(20261014)
    # 100k exact-ID ANN fixture: mix three real gold directions instead of creating
    # hundreds of near-identical clones of every source vector.
    mix_idx = rng.integers(0, len(base), size=(n, 3), dtype=np.int32)
    weights = rng.uniform(0.15, 1.0, size=(n, 3)).astype(np.float32)
    weights /= weights.sum(axis=1, keepdims=True)
    vectors = (
        base[mix_idx[:, 0]] * weights[:, 0, None]
        + base[mix_idx[:, 1]] * weights[:, 1, None]
        + base[mix_idx[:, 2]] * weights[:, 2, None]
    ).astype(np.float32, copy=False)
    vectors += rng.normal(0.0, 0.005, size=vectors.shape).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    scopes = (np.arange(n) % 8).astype(np.int32)
    query_scopes = np.arange(len(queries), dtype=np.int32) % 8
    k = 10

    def exact_topk(query, scope=None):
        ids = np.arange(n) if scope is None else np.flatnonzero(scopes == scope)
        scores = vectors @ query if scope is None else vectors[ids] @ query
        selected = np.argpartition(-scores, k - 1)[:k]
        selected = selected[np.argsort(-scores[selected], kind="stable")]
        return ids[selected].astype(int).tolist()

    exact_refs = []
    exact_filtered_refs = []
    exact_lats = []
    exact_filtered_lats = []
    for query, scope in zip(queries, query_scopes):
        t0 = time.perf_counter()
        exact_refs.append(exact_topk(query))
        exact_lats.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        exact_filtered_refs.append(exact_topk(query, int(scope)))
        exact_filtered_lats.append((time.perf_counter() - t0) * 1000)

    client = QdrantClient(url=args.url, grpc_port=args.grpc_port, prefer_grpc=True, timeout=180)
    collection = "sgokb_i07_gold_100k"

    def wait_ready():
        last = None
        for _ in range(360):
            last = client.get_collection(collection)
            points = int(last.points_count or 0)
            indexed = int(last.indexed_vectors_count or 0)
            if points >= n and indexed >= n and "green" in str(last.status).lower():
                return last
            time.sleep(0.5)
        raise RuntimeError(f"Qdrant did not finish indexing: {last}")

    def build():
        if client.collection_exists(collection):
            client.delete_collection(collection)
        started = time.perf_counter()
        client.create_collection(
            collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            hnsw_config=models.HnswConfigDiff(
                m=16, ef_construct=128, full_scan_threshold=10, on_disk=False
            ),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=0, default_segment_number=2
            ),
        )
        client.create_payload_index(
            collection, field_name="scope", field_schema=models.PayloadSchemaType.INTEGER, wait=True
        )
        create = time.perf_counter() - started
        t0 = time.perf_counter()
        client.upload_collection(
            collection,
            vectors=vectors,
            payload=({"scope": int(x)} for x in scopes),
            ids=range(n),
            batch_size=512,
            parallel=1,
            wait=True,
        )
        upload = time.perf_counter() - t0
        client.update_collection(
            collection, optimizers_config=models.OptimizersConfigDiff(indexing_threshold=1000)
        )
        t0 = time.perf_counter()
        info = wait_ready()
        index = time.perf_counter() - t0
        return {
            "create_seconds": create,
            "upload_seconds": upload,
            "index_seconds": index,
            "total_seconds": create + upload + index,
        }, info

    build1, info = build()

    def filt(scope):
        if scope is None:
            return None
        return models.Filter(
            must=[models.FieldCondition(key="scope", match=models.MatchValue(value=int(scope)))]
        )

    def qsearch(query, scope, exact=False):
        response = client.query_points(
            collection,
            query=query,
            query_filter=filt(scope),
            search_params=models.SearchParams(hnsw_ef=args.hnsw_ef, exact=exact),
            limit=k,
            with_payload=False,
            with_vectors=False,
        )
        return [int(point.id) for point in response.points]

    def recall(found, expected):
        return len(set(found[:k]) & set(expected[:k])) / k

    ann_lats = []
    ann_recall = []
    ann_filter_lats = []
    ann_filter_recall = []
    for _ in range(3):
        for i, (query, scope) in enumerate(zip(queries, query_scopes)):
            t0 = time.perf_counter()
            found = qsearch(query, None)
            ann_lats.append((time.perf_counter() - t0) * 1000)
            ann_recall.append(recall(found, exact_refs[i]))
            t0 = time.perf_counter()
            found = qsearch(query, int(scope))
            ann_filter_lats.append((time.perf_counter() - t0) * 1000)
            ann_filter_recall.append(recall(found, exact_filtered_refs[i]))

    updated = vectors[:100] + rng.normal(0, 0.001, size=(100, dim)).astype(np.float32)
    updated /= np.linalg.norm(updated, axis=1, keepdims=True)
    update_points = [
        models.PointStruct(id=int(i), vector=updated[i].tolist(), payload={"scope": int(scopes[i])})
        for i in range(100)
    ]
    t0 = time.perf_counter()
    client.upsert(collection, points=update_points, wait=True)
    update_seconds = time.perf_counter() - t0
    restore = [
        models.PointStruct(id=int(i), vector=vectors[i].tolist(), payload={"scope": int(scopes[i])})
        for i in range(100)
    ]
    client.upsert(collection, points=restore, wait=True)

    build2, info2 = build()
    result = {
        "schema_version": "sgokb.vector-backend-benchmark/1.0",
        "fixture": {
            "base_gold_vectors": len(base),
            "scaled_points": n,
            "dimension": dim,
            "queries": len(queries),
            "filter_partitions": 8,
            "generation": "3-way weighted mixture of frozen gold vectors + Gaussian noise",
            "noise_sigma": 0.005,
        },
        "exact": {
            "unfiltered": latency_summary(exact_lats),
            "filtered": latency_summary(exact_filtered_lats),
            "reference": "NumPy Float32 cosine",
        },
        "qdrant": {
            "server_version": "1.19.2",
            "client_version": str(client_version),
            "profile": {
                "m": 16,
                "ef_construct": 128,
                "hnsw_ef": args.hnsw_ef,
                "full_scan_threshold": 10,
            },
            "build": build1,
            "full_rebuild": build2,
            "unfiltered": {
                **latency_summary(ann_lats),
                "mean_recall@10": statistics.fmean(ann_recall),
                "min_recall@10": min(ann_recall),
            },
            "filtered": {
                **latency_summary(ann_filter_lats),
                "mean_recall@10": statistics.fmean(ann_filter_recall),
                "min_recall@10": min(ann_filter_recall),
            },
            "incremental_update_100_seconds": update_seconds,
            "points_count": int(info2.points_count or 0),
            "indexed_vectors_count": int(info2.indexed_vectors_count or 0),
            "disk_bytes": directory_bytes(args.storage),
        },
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("saved", args.output)


if __name__ == "__main__":
    main()
