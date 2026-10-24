"""N-06 stage-ordered R2 retrieval evaluation; never modifies production search."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "benchmark/tools")]

from scripts import run_search_quality_gold as gold_helper  # noqa: E402
from sgokb.application_generation import KnowledgeSearchGenerationApplication  # noqa: E402
from sgokb.domain import ObjectSearchFilters, SearchRepresentationKind  # noqa: E402
from sgokb.repository import Repository  # noqa: E402
from sgokb.retrieval import (  # noqa: E402
    HybridObjectSearch,
    aggregate_metric_rows,
    latency_summary,
    ranked_retrieval_metrics,
)
from sgokb.retrieval.embedding import (  # noqa: E402
    default_sentence_transformer_provider,
    frozen_harrier_space,
)
from sgokb.retrieval.generation import (  # noqa: E402
    GenerationAwareSearchRepresentationBuilder,
    route_generation_vector_index,
)
from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter  # noqa: E402

CONTRACT_PATH = ROOT / "benchmark/n06-retrieval-vector-quality-contract-v1.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_n03(source, destination):
    if not source.is_file():
        raise RuntimeError("BLOCKED_N03_ASSET_UNAVAILABLE")
    if destination.exists():
        raise FileExistsError("Never overwrite an evaluation copy")
    before = sha(source)
    src = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
        assert dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        dst.close()
        src.close()
    if sha(source) != before:
        raise RuntimeError("Preserved N-03 changed during backup")
    return before


def namespace(run_id, purpose):
    if purpose not in {"gold", "real", "ann"}:
        raise ValueError("Unknown benchmark namespace purpose")
    return "n06" + hashlib.sha256((run_id + ":" + purpose).encode()).hexdigest()[:12]


class ObjectAblationIndex:
    """Object-only view; direct Statement searches keep using the underlying index."""

    def __init__(self, base):
        self.base = base
        self.backend_key = base.backend_key

    def search(self, space, vector, *, limit, filters=None):
        if filters is not None and any(
            match.field == "kind" and "statement" in match.values for match in filters.matches
        ):
            return ()
        return self.base.search(space, vector, limit=limit, filters=filters)


def grouped_objects(candidates):
    return list(dict.fromkeys(item["object_id"] for item in candidates))


def assert_r2(repo, index, space):
    generation = repo.one(
        "SELECT g.* FROM knowledge_search_active_generation a "
        "JOIN knowledge_search_generations g ON g.id=a.active_generation_id"
    )
    if generation is None or (
        generation["contract_key"],
        generation["contract_version"],
        generation["state"],
    ) != ("n05d04r2-hierarchical-v2", 2, "ready"):
        raise RuntimeError("Unsupported/missing active R2 generation")
    kinds = {
        r["target_kind"]
        for r in repo.rows(
            "SELECT DISTINCT m.target_kind FROM knowledge_search_generation_memberships gm "
            "JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id "
            "WHERE gm.generation_id=?",
            (generation["id"],),
        )
    }
    if not kinds.issubset({"object_overview", "facet", "statement"}):
        raise RuntimeError("Active generation family leakage")
    app = KnowledgeSearchGenerationApplication(repo, embedding_space=space, vector_index=index)
    app.refresh_active_generation(generation["id"])
    return {
        "generation_id": generation["id"],
        "kinds": sorted(kinds),
        "leakage": 0,
        "membership_count": len(app._generation_membership_rows(generation["id"])),
        "membership_digest": app.membership_digest(generation["id"]),
    }


def prepare_generation(repo, provider, prefix, gold=None):
    base = QdrantVectorIndexAdapter(
        url="http://localhost:6333",
        grpc_port=6334,
        prefer_grpc=True,
        collection_prefix=prefix,
        hnsw_m=16,
        ef_construct=128,
        search_ef=768,
        full_scan_threshold=10,
    )
    app = KnowledgeSearchGenerationApplication(repo, embedding_provider=provider, vector_index=base)
    refs = None
    if gold is not None:
        app.bootstrap_empty_r2()
        refs = gold_helper.populate_repository(
            repo,
            gold,
            builder_factory=GenerationAwareSearchRepresentationBuilder,
        )
    candidate = app.build_r2_candidate()
    app.cutover(candidate.generation_id)
    routed = route_generation_vector_index(repo, base)
    audit = assert_r2(repo, routed, provider.space)
    return routed, refs, audit


def statement_candidates(engine, index, provider, query, filters=None, limit=50):
    filters = filters or ObjectSearchFilters()
    vector = provider.embed_queries([query])[0]
    vf = engine._vector_filters_for_generation(filters, SearchRepresentationKind.STATEMENT)
    hits = index.search(provider.space, vector, limit=limit, filters=vf)
    output = []
    for hit in hits:
        sid = hit.metadata["statement_id"]
        row = engine.repository.one("SELECT text FROM knowledge_statements WHERE id=?", (sid,))
        output.append(
            {
                "statement_id": sid,
                "object_id": hit.metadata["object_id"],
                "version_id": hit.metadata["version_id"],
                "text": row["text"],
            }
        )
    return output


def evaluate_queries(queries, engine):
    rows = []
    metrics = {mode: [] for mode in ("lexical", "semantic", "hybrid")}
    lats = {mode: [] for mode in metrics}
    for case in queries:
        item = {"id": case["id"], "query": case["query"], "modes": {}}
        for mode in metrics:
            start = time.perf_counter()
            result = engine.search(
                case["query"],
                mode=mode,
                limit=10,
                filters=gold_helper.filters_from(case.get("filters")),
            )
            elapsed = time.perf_counter() - start
            if result.degraded_channels:
                raise RuntimeError("Retrieval degraded: " + str(result.degraded_channels))
            ids = gold_helper.result_ids(result)
            value = ranked_retrieval_metrics(ids, case["relevance"])
            item["modes"][mode] = {
                "ids": ids,
                "metrics": value,
                "versions": [r.version_id for r in result.results],
            }
            metrics[mode].append(value)
            lats[mode].append(elapsed)
        rows.append(item)
    return {
        "cases": rows,
        "modes": {
            m: {"quality": aggregate_metric_rows(metrics[m]), "latency": latency_summary(lats[m])}
            for m in metrics
        },
    }


def real_queries(manifest):
    cases = []
    for obj in manifest["objects"]:
        identities = {
            x["query"] for x in obj.get("lexical_smoke", []) if x.get("identity_required")
        }
        queries = list(
            dict.fromkeys(
                [
                    *obj["expected_search_queries"],
                    *[x["query"] for x in obj.get("lexical_smoke", [])],
                ]
            )
        )
        for number, query in enumerate(queries):
            cases.append(
                {
                    "id": obj["object_key"] + ":" + str(number),
                    "query": query,
                    "identity_required": query in identities,
                    "relevance": {obj["object_id"]: 3},
                }
            )
    return cases


def evaluate_ablation(queries, engine, ablated):
    full, reduced, cases = [], [], []
    for case in queries:
        filters = gold_helper.filters_from(case.get("filters"))
        a = gold_helper.result_ids(engine.search(case["query"], filters=filters, mode="semantic"))
        b = gold_helper.result_ids(ablated.search(case["query"], filters=filters, mode="semantic"))
        ma = ranked_retrieval_metrics(a, case["relevance"])
        mb = ranked_retrieval_metrics(b, case["relevance"])
        full.append(ma)
        reduced.append(mb)
        cases.append({"id": case["id"], "full_ids": a, "ablated_ids": b, "full": ma, "ablated": mb})
    return {
        "full": aggregate_metric_rows(full),
        "ablated": aggregate_metric_rows(reduced),
        "cases": cases,
    }


def command(run, name, args):
    with (run / (name + ".log")).open("w", encoding="utf-8") as log:
        return subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode


def reference_vector_snapshot(workspace, client):
    """Read-only full point fingerprints for persisted production/reference bindings."""
    names = set()
    for relative in (".local/sgokb.sqlite", ".local/n03/sgokb-n03.sqlite"):
        path = workspace / relative
        if not path.exists():
            continue
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE name=?",
                ("knowledge_search_generation_vector_indexes",),
            ).fetchone():
                names.update(
                    row[0]
                    for row in db.execute(
                        "SELECT namespace_key FROM knowledge_search_generation_vector_indexes "
                        "WHERE backend_key='qdrant'"
                    )
                )
        finally:
            db.close()
    result = {}
    for name in sorted(names):
        if not client.collection_exists(name):
            result[name] = {"exists": False}
            continue
        offset = None
        digests = []
        while True:
            records, offset = client.scroll(
                name, limit=256, offset=offset, with_payload=True, with_vectors=True
            )
            for record in records:
                data = json.dumps(
                    {"id": str(record.id), "payload": record.payload, "vector": record.vector},
                    sort_keys=True,
                )
                digests.append(hashlib.sha256(data.encode()).hexdigest())
            if offset is None:
                break
        result[name] = {
            "exists": True,
            "points": len(digests),
            "sha256": hashlib.sha256("\n".join(sorted(digests)).encode()).hexdigest(),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--reranker-cache", required=True, type=Path)
    args = parser.parse_args()
    run = args.run_root.resolve()
    if not run.is_relative_to(ROOT / ".local/n06") or run.exists():
        raise ValueError("New run must be beneath .local/n06")
    run.mkdir(parents=True)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", CUDA_VISIBLE_DEVICES="0")
    evidence = {"run_id": run.name, "stages": {}}
    contract = read(CONTRACT_PATH)

    def state(stage):
        write(run / "status.json", {"stage": stage, "pid": os.getpid()})
        write(run / "evidence.json", evidence)

    repos = []
    indexes = []
    preserved = args.workspace / ".local/n03/sgokb-n03.sqlite"
    import n05_run_performance as previous
    from n05_run_performance import canonical_state

    old_root = previous.ROOT
    previous.ROOT = args.workspace
    before = canonical_state()
    previous.ROOT = old_root
    write(run / "canonical-before.json", before)
    source_hash = sha(preserved) if preserved.exists() else None
    frozen_inputs = [
        CONTRACT_PATH,
        ROOT / "benchmark/search-quality-gold-v1.json",
        ROOT / "benchmark/n03-real-data-vertical-slice-v1.json",
        ROOT / "benchmark/n05d04r2-object-similarity-gold-v1.json",
        ROOT / "benchmark/n05d04r2-search-quality-acceptance-v1.json",
    ]
    write(run / "input-identity.json", {str(p.relative_to(ROOT)): sha(p) for p in frozen_inputs})
    assets = [
        "benchmark/tools/n05_resource_preflight.py",
        "benchmark/tools/n05d04r1_sdpa_vram_diagnosis.py",
        "tests/test_n05d04r1_sdpa_vram_diagnosis.py",
    ]
    asset_hashes = {p: sha(args.workspace / p) for p in assets if (args.workspace / p).exists()}
    write(run / "r1-before.json", asset_hashes)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if tracked:
        raise RuntimeError("Measurement requires a clean committed implementation")
    try:
        state("A_preflight")
        import torch
        from qdrant_client import QdrantClient

        gpu = subprocess.check_output(
            [
                "nvidia-smi",
                "-i",
                "0",
                "--query-gpu=name,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
        if not torch.cuda.is_available() or "4090" not in gpu or int(gpu.split(",")[1]) > 2048:
            raise RuntimeError("BLOCKED_GPU_RUNTIME_OR_COMPETING_WORKLOAD")
        if shutil.disk_usage(ROOT).free < 32 * 1024**3:
            raise RuntimeError("BLOCKED_DISK_HEADROOM")
        from n05_resource_preflight import _windows_memory

        evidence["host_memory"] = _windows_memory()
        write(run / "host-memory.json", evidence["host_memory"])
        client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)
        assert client.info().version == "1.19.2"
        production = {
            x.name: client.get_collection(x.name).points_count
            for x in client.get_collections().collections
        }
        write(run / "qdrant-before.json", production)
        reference_before = reference_vector_snapshot(args.workspace, client)
        write(run / "reference-vector-before.json", reference_before)
        evidence["stages"]["A"] = {
            "status": "PASS",
            "head": head,
            "free_bytes": shutil.disk_usage(ROOT).free,
            "gpu": gpu,
            "packages": {
                n: importlib.metadata.version(n)
                for n in ("torch", "transformers", "sentence-transformers", "qdrant-client")
            },
            "cuda": torch.version.cuda,
        }
        if not preserved.exists():
            raise RuntimeError("BLOCKED_N03_ASSET_UNAVAILABLE")
        provider = default_sentence_transformer_provider(
            cache_folder=str(args.cache), local_files_only=True
        )
        if provider.device != "cuda" or provider.space != frozen_harrier_space():
            raise RuntimeError("BLOCKED_EMBEDDING_IDENTITY")
        torch.cuda.reset_peak_memory_stats()
        state("B_synthetic")
        gold = gold_helper.load_gold(ROOT / "benchmark/search-quality-gold-v1.json")
        repo = Repository(run / "synthetic.sqlite")
        repos.append(repo)
        index, refs, audit = prepare_generation(repo, provider, namespace(run.name, "gold"), gold)
        indexes.append(index)
        engine = HybridObjectSearch(repo, embedding_provider=provider, vector_index=index)
        search = evaluate_queries(gold["search_queries"], engine)
        candidates = []
        statement_metrics = []
        for case in gold["search_queries"]:
            if not case.get("statement_refs"):
                continue
            cs = statement_candidates(
                engine,
                index,
                provider,
                case["query"],
                gold_helper.filters_from(case.get("filters")),
            )
            rel = {refs["statement_refs"][key]: 3 for key in case["statement_refs"]}
            statement_metrics.append(
                ranked_retrieval_metrics([c["statement_id"] for c in cs[:10]], rel)
            )
            candidates.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "candidates": cs,
                    "statement_relevance": rel,
                    "object_relevance": case["relevance"],
                }
            )
        write(run / "statement-candidates.json", candidates)
        contracts = gold_helper.evaluate_contracts(gold, engine)
        similarity = gold_helper.evaluate_similarity(gold, repo, provider, index)
        ev = gold_helper.evaluate_evidence(gold, repo, provider)
        mapping = read(ROOT / "benchmark/n05d04r2-object-similarity-gold-test-map-v1.json")
        r2cases = {}
        for key, names in mapping["cases"].items():
            rc = command(
                run,
                key,
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    *[mapping["test_file"] + "::" + name for name in names],
                ],
            )
            r2cases[key] = rc == 0
        identity_cases = [
            c for c in gold["search_queries"] if c["category"] in {"exact_name", "exact_alias"}
        ]
        identity = sum(
            bool(row["modes"]["lexical"]["ids"])
            and row["modes"]["lexical"]["ids"][0] in case["relevance"]
            for case, row in zip(gold["search_queries"], search["cases"])
            if case in identity_cases
        ) / len(identity_cases)
        from scripts.run_n05d04r2_search_quality_acceptance import evaluate_baseline_gates

        search["exact_lookup_accuracy"] = identity
        search["statement_semantic"] = {"quality": aggregate_metric_rows(statement_metrics)}
        baseline = evaluate_baseline_gates(
            {
                "search": search,
                "contracts": contracts,
                "similarity": similarity,
                "evidence_search": ev,
            },
            read(ROOT / "benchmark/n05d04r2-search-quality-acceptance-v1.json"),
        )
        accepted = read(ROOT / "benchmark/results/n05d04r2-r2-06-candidate-e-remediation.json")[
            "quality"
        ]["search"]
        accepted_cases = {row["id"]: row for row in accepted["cases"]}
        comparable_deltas = []
        for row in search["cases"]:
            for mode in ("lexical", "semantic", "hybrid"):
                for key, actual in row["modes"][mode]["metrics"].items():
                    previous_value = accepted_cases[row["id"]]["modes"][mode]["metrics"][key]
                    if actual + 1e-12 < previous_value:
                        comparable_deltas.append(
                            {
                                "id": row["id"],
                                "mode": mode,
                                "metric": key,
                                "before": previous_value,
                                "after": actual,
                                "classification": "unexplained",
                            }
                        )
        b = {
            "status": "PASS",
            "search": search,
            "contracts": contracts,
            "similarity": similarity,
            "evidence_search": ev,
            "generation": audit,
            "r2_similarity": r2cases,
            "statement_quality": aggregate_metric_rows(statement_metrics),
            "similarity_passed": sum(c["metrics"]["mrr"] == 1 for c in similarity["cases"]),
            "evidence_passed": sum(
                c["metrics"]["recall@10"] == 1 for v in ev.values() for c in v["cases"]
            ),
            "baseline_comparison": baseline,
            "accepted_r2_08_negative_deltas": comparable_deltas,
            "gates": {
                "exact_identity_accuracy": identity,
                "semantic_recall_at_10": search["modes"]["semantic"]["quality"]["recall@10"],
                "hybrid_recall_at_10": search["modes"]["hybrid"]["quality"]["recall@10"],
                "hybrid_mrr": search["modes"]["hybrid"]["quality"]["mrr"],
                "statement_recall_at_10": aggregate_metric_rows(statement_metrics)["recall@10"],
                "r2_similarity_cases_passed": sum(r2cases.values()),
                "r2_similarity_cases_total": len(r2cases),
                "unexplained_negative_comparable_deltas": len(comparable_deltas),
                "active_object_overall_leakage": audit["leakage"],
            },
        }
        evidence["stages"]["B"] = b
        state("C_real_data")
        copy_n03(preserved, run / "n03.sqlite")
        real_repo = Repository(run / "n03.sqlite")
        repos.append(real_repo)
        real_index, _, real_audit = prepare_generation(
            real_repo, provider, namespace(run.name, "real")
        )
        indexes.append(real_index)
        real_engine = HybridObjectSearch(
            real_repo, embedding_provider=provider, vector_index=real_index
        )
        queries = real_queries(read(ROOT / "benchmark/n03-real-data-vertical-slice-v1.json"))
        real = evaluate_queries(queries, real_engine)
        failures = []
        leakage = 0
        current = {
            r["id"]: r["current_version_id"]
            for r in real_repo.rows("SELECT id,current_version_id FROM objects")
        }
        for row in real["cases"]:
            for response in row["modes"].values():
                leakage += sum(
                    v != current[o] for o, v in zip(response["ids"], response["versions"])
                )
        for case, row in zip(queries, real["cases"]):
            for mode, result in row["modes"].items():
                if result["metrics"]["recall@10"] < 1:
                    failures.append(
                        {
                            "id": case["id"],
                            "mode": mode,
                            "classification": "lexical_wording_coverage_limitation"
                            if mode == "lexical"
                            else "supported_target_retrieval_miss",
                        }
                    )
        real["gates"] = {
            "identity_rank1_required": all(
                row["modes"]["hybrid"]["metrics"]["mrr"] == 1
                and row["modes"]["lexical"]["metrics"]["mrr"] == 1
                for case, row in zip(queries, real["cases"])
                if case["identity_required"]
            ),
            "semantic_supported_target_recall_at_10": real["modes"]["semantic"]["quality"][
                "recall@10"
            ],
            "hybrid_supported_target_recall_at_10": real["modes"]["hybrid"]["quality"]["recall@10"],
            "historical_or_generation_leakage": leakage,
        }
        real.update(status="PASS", failures=failures, generation=real_audit)
        evidence["stages"]["C"] = real
        state("D_statement_ablation")
        evidence["stages"]["D"] = {
            "status": "PASS",
            "direct_statement_search_enabled": True,
            "synthetic": evaluate_ablation(
                gold["search_queries"],
                engine,
                HybridObjectSearch(
                    repo, embedding_provider=provider, vector_index=ObjectAblationIndex(index)
                ),
            ),
            "real": evaluate_ablation(
                [q for q in queries if not q["identity_required"]],
                real_engine,
                HybridObjectSearch(
                    real_repo,
                    embedding_provider=provider,
                    vector_index=ObjectAblationIndex(real_index),
                ),
            ),
        }
        evidence["stages"]["D"]["direct_statement_synthetic_quality"] = b["statement_quality"]
        evidence["stages"]["D"]["real_direct_statement_hits"] = [
            {
                "id": q["id"],
                "hits": statement_candidates(
                    real_engine, real_index, provider, q["query"], limit=10
                ),
            }
            for q in queries
            if not q["identity_required"]
        ]
        evidence["stages"]["D"]["real_statement_judgement"] = (
            "No frozen per-query Statement relevance labels; raw rankings only"
        )
        evidence["resources"] = {
            "search_peak_allocated": torch.cuda.max_memory_allocated(),
            "search_peak_reserved": torch.cuda.max_memory_reserved(),
        }
        state("E_rerankers")
        from n06_studies import ann_study, reranker_study

        evidence["stages"]["E"] = reranker_study(candidates, contract, args.reranker_cache, run)
        state("F_ann_100k")
        evidence["stages"]["F"] = ann_study(repo, index, provider, gold, contract, run)
        state("G_evaluator")
        from n06_evaluate_retrieval_vector_quality import evaluate

        evidence["stages"]["G"] = {"status": "PASS"}
        write(run / "quality-evaluation.json", evaluate(evidence, contract, require_post_run=False))
    except Exception:
        evidence["blocker"] = traceback.format_exc()
        stage = read(run / "status.json")["stage"][0]
        evidence["stages"][stage] = {"status": "BLOCKED", "reason": evidence["blocker"]}
        state("BLOCKED_" + stage)
    finally:
        for index in indexes:
            index.base_vector_index._client.close()
        for repo in repos:
            repo.close()
        state_before_post = read(run / "status.json")["stage"]
        state("H_post_run")
        old_root = previous.ROOT
        previous.ROOT = args.workspace
        after = canonical_state()
        previous.ROOT = old_root
        write(run / "canonical-after.json", after)
        from qdrant_client import QdrantClient

        check_client = QdrantClient(url="http://localhost:6333", prefer_grpc=True)
        reference_unchanged = (
            all(
                check_client.get_collection(n).points_count == count
                for n, count in production.items()
            )
            if "production" in locals()
            else False
        )
        reference_after = reference_vector_snapshot(args.workspace, check_client)
        write(run / "reference-vector-after.json", reference_after)
        reference_unchanged = reference_unchanged and reference_after == reference_before
        check_client.close()
        regression = {}
        for name, args2 in [
            (
                "focused",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "tests/test_n06_retrieval_vector_quality.py",
                ],
            ),
            ("full", [sys.executable, "-m", "pytest", "-q"]),
            ("ruff", [sys.executable, "-m", "ruff", "check", "."]),
            ("diff", ["git", "diff", "--check"]),
        ]:
            regression[name] = command(run, "post-" + name, args2)
        evidence["stages"]["H"] = {
            "status": "PASS",
            "regression": regression,
            "safety": {
                "canonical_unchanged": before == after,
                "preserved_n03_unchanged": source_hash is not None
                and sha(preserved) == source_hash,
                "reference_qdrant_unchanged": reference_unchanged,
                "head_unchanged": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip()
                == head,
                "tracked_unchanged": subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                )
                == tracked,
                "r1_unchanged": asset_hashes == {p: sha(args.workspace / p) for p in asset_hashes},
            },
        }
        from n06_evaluate_retrieval_vector_quality import evaluate

        write(run / "evaluation.json", evaluate(evidence, contract))
        write(run / "evidence.json", evidence)
        write(
            run / "status.json",
            {
                "stage": "finished_awaiting_review",
                "previous_stage": state_before_post,
                "verdict": read(run / "evaluation.json")["overall"],
            },
        )


if __name__ == "__main__":
    main()
