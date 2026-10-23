"""Run N05D-04R2 Search-quality acceptance on the frozen Phase-I gold.

This harness deliberately keeps the Harrier OSS v1 0.6B embedding space fixed,
materializes the R2 representation family into an isolated synthetic generation,
and reuses the accepted Phase-I gold/evaluators. It does not run R2-09 formal
performance acceptance and it never mutates the reference production database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_search_quality_gold import (  # noqa: E402
    evaluate_contracts,
    evaluate_evidence,
    evaluate_search,
    evaluate_similarity,
    load_gold,
    populate_repository,
)
from sgokb.application_generation import (  # noqa: E402
    KnowledgeSearchGenerationApplication,
    R2_CONTRACT_KEY,
)
from sgokb.domain import SearchRepresentationKind  # noqa: E402
from sgokb.repository import Repository  # noqa: E402
from sgokb.retrieval import (  # noqa: E402
    ExactVectorIndexAdapter,
    HybridObjectSearch,
    KnowledgeVectorIndexBuilder,
    SearchRepresentationBuilder,
    default_sentence_transformer_provider,
)

GENERATION_ID = "search-generation:r2:search-quality-gold-v1"
EPSILON = 1e-12


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_contract(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        value.get("schema_version") != "sgokb.n05d04r2-search-quality-acceptance/1.0"
        or value.get("status") != "frozen"
    ):
        raise ValueError("Frozen sgokb.n05d04r2-search-quality-acceptance/1.0 required")
    return value


def _clean_db(path: Path) -> None:
    if path.exists():
        path.unlink()
    for suffix in ("-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        if candidate.exists():
            candidate.unlink()


def materialize_r2_generation(repo: Repository) -> dict:
    builder = SearchRepresentationBuilder(repo)
    version_ids = [
        row["version_id"]
        for row in repo.rows(
            """SELECT version_id FROM object_version_lifecycle
               WHERE state='accepted' ORDER BY version_id"""
        )
    ]
    for version_id in version_ids:
        builder.materialize_version_r2(version_id)

    app = KnowledgeSearchGenerationApplication(repo)
    source_digest = app.source_catalog_digest()
    now = _now()
    repo.db.execute(
        """INSERT INTO knowledge_search_generations(
               id,contract_key,contract_version,state,source_catalog_digest,created_at
           ) VALUES(?,?,?,?,?,?)""",
        (GENERATION_ID, R2_CONTRACT_KEY, 2, "building", source_digest, now),
    )
    repo.db.execute(
        """INSERT INTO knowledge_search_generation_memberships(
               generation_id,membership_id,created_at
           )
           SELECT ?,m.id,?
           FROM knowledge_search_representation_memberships m
           JOIN object_version_lifecycle l ON l.version_id=m.version_id
           WHERE l.state='accepted'
             AND m.target_kind IN ('object_overview','facet','statement')
           ORDER BY m.id""",
        (GENERATION_ID, now),
    )
    membership_count = app._validate_generation_shape(GENERATION_ID, R2_CONTRACT_KEY)
    membership_digest = app.membership_digest(GENERATION_ID)
    repo.db.execute(
        """UPDATE knowledge_search_generations
           SET state='ready',membership_digest=?,ready_at=?
           WHERE id=?""",
        (membership_digest, now, GENERATION_ID),
    )
    repo.db.execute("DELETE FROM knowledge_search_active_generation WHERE scope='knowledge'")
    repo.db.execute(
        """INSERT INTO knowledge_search_active_generation(
               scope,active_generation_id,activation_revision,activated_at
           ) VALUES('knowledge',?,?,?)""",
        (GENERATION_ID, 1, now),
    )
    repo.db.commit()

    kind_rows = repo.rows(
        """SELECT m.target_kind,count(*) AS count
           FROM knowledge_search_generation_memberships gm
           JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id
           WHERE gm.generation_id=?
           GROUP BY m.target_kind ORDER BY m.target_kind""",
        (GENERATION_ID,),
    )
    return {
        "generation_id": GENERATION_ID,
        "contract_key": R2_CONTRACT_KEY,
        "source_catalog_digest": source_digest,
        "membership_digest": membership_digest,
        "membership_count": membership_count,
        "representation_counts": {row["target_kind"]: row["count"] for row in kind_rows},
    }


def embed_r2_generation(repo: Repository, provider) -> int:
    rows = repo.rows(
        """SELECT DISTINCT r.id,r.content
           FROM search_representations r
           JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
           JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
           WHERE gm.generation_id=?
           ORDER BY r.id""",
        (GENERATION_ID,),
    )
    vectors = provider.embed_documents([row["content"] for row in rows])
    if len(vectors) != len(rows):
        raise RuntimeError("Embedding provider returned an unexpected vector count")
    for row, vector in zip(rows, vectors):
        repo.embedding_store.save_representation_embedding(provider.space, row["id"], vector)
    return len(rows)


def _metric(result: dict, path: tuple[str, ...]) -> float:
    value = result
    for key in path:
        value = value[key]
    return float(value)


def evaluate_baseline_gates(result: dict, contract: dict) -> dict:
    baseline = contract["phase_i_observed_baseline"]
    strict = [
        (
            "exact_lookup_accuracy",
            float(result["search"]["exact_lookup_accuracy"]),
            float(baseline["exact_lookup_accuracy"]),
        ),
        (
            "hybrid.mrr",
            _metric(result, ("search", "modes", "hybrid", "quality", "mrr")),
            float(baseline["hybrid"]["mrr"]),
        ),
        (
            "hybrid.recall@10",
            _metric(result, ("search", "modes", "hybrid", "quality", "recall@10")),
            float(baseline["hybrid"]["recall@10"]),
        ),
        (
            "hybrid.ndcg@10",
            _metric(result, ("search", "modes", "hybrid", "quality", "ndcg@10")),
            float(baseline["hybrid"]["ndcg@10"]),
        ),
        (
            "statement_semantic.mrr",
            _metric(result, ("search", "statement_semantic", "quality", "mrr")),
            float(baseline["statement_semantic"]["mrr"]),
        ),
        (
            "statement_semantic.recall@10",
            _metric(result, ("search", "statement_semantic", "quality", "recall@10")),
            float(baseline["statement_semantic"]["recall@10"]),
        ),
        (
            "facet_similarity.mrr",
            _metric(result, ("similarity", "facet_quality", "mrr")),
            float(baseline["similarity_facet"]["mrr"]),
        ),
        (
            "facet_similarity.recall@10",
            _metric(result, ("similarity", "facet_quality", "recall@10")),
            float(baseline["similarity_facet"]["recall@10"]),
        ),
        (
            "facet_similarity.ndcg@10",
            _metric(result, ("similarity", "facet_quality", "ndcg@10")),
            float(baseline["similarity_facet"]["ndcg@10"]),
        ),
    ]
    for channel, key in (
        ("lexical_association", "evidence_lexical_association"),
        ("semantic", "evidence_semantic"),
    ):
        for metric in ("mrr", "recall@10", "ndcg@10"):
            strict.append(
                (
                    f"evidence.{channel}.{metric}",
                    _metric(result, ("evidence_search", channel, "quality", metric)),
                    float(baseline[key][metric]),
                )
            )

    strict_rows = [
        {
            "metric": name,
            "actual": actual,
            "baseline": expected,
            "delta": actual - expected,
            "passed": actual + EPSILON >= expected,
        }
        for name, actual, expected in strict
    ]
    contract_passed = (
        result["contracts"]["passed"] == baseline["contract_cases"]["passed"]
        and result["contracts"]["total"] == baseline["contract_cases"]["total"]
    )

    review = [
        (
            "semantic.mrr",
            _metric(result, ("search", "modes", "semantic", "quality", "mrr")),
            float(baseline["semantic"]["mrr"]),
        ),
        (
            "semantic.recall@1",
            _metric(result, ("search", "modes", "semantic", "quality", "recall@1")),
            float(baseline["semantic"]["recall@1"]),
        ),
        (
            "semantic.recall@10",
            _metric(result, ("search", "modes", "semantic", "quality", "recall@10")),
            float(baseline["semantic"]["recall@10"]),
        ),
        (
            "semantic.ndcg@10",
            _metric(result, ("search", "modes", "semantic", "quality", "ndcg@10")),
            float(baseline["semantic"]["ndcg@10"]),
        ),
        (
            "hybrid.recall@1",
            _metric(result, ("search", "modes", "hybrid", "quality", "recall@1")),
            float(baseline["hybrid"]["recall@1"]),
        ),
        (
            "statement_semantic.recall@1",
            _metric(result, ("search", "statement_semantic", "quality", "recall@1")),
            float(baseline["statement_semantic"]["recall@1"]),
        ),
        (
            "statement_semantic.ndcg@10",
            _metric(result, ("search", "statement_semantic", "quality", "ndcg@10")),
            float(baseline["statement_semantic"]["ndcg@10"]),
        ),
        (
            "overall_similarity.mrr",
            _metric(result, ("similarity", "overall_quality", "mrr")),
            float(baseline["similarity_overall"]["mrr"]),
        ),
        (
            "overall_similarity.recall@1",
            _metric(result, ("similarity", "overall_quality", "recall@1")),
            float(baseline["similarity_overall"]["recall@1"]),
        ),
        (
            "overall_similarity.recall@10",
            _metric(result, ("similarity", "overall_quality", "recall@10")),
            float(baseline["similarity_overall"]["recall@10"]),
        ),
        (
            "overall_similarity.ndcg@10",
            _metric(result, ("similarity", "overall_quality", "ndcg@10")),
            float(baseline["similarity_overall"]["ndcg@10"]),
        ),
    ]
    review_rows = [
        {
            "metric": name,
            "actual": actual,
            "baseline": expected,
            "delta": actual - expected,
            "requires_review": actual + EPSILON < expected,
        }
        for name, actual, expected in review
    ]
    return {
        "strict_non_regression": strict_rows,
        "contracts": {
            "actual": {
                "passed": result["contracts"]["passed"],
                "total": result["contracts"]["total"],
            },
            "baseline": baseline["contract_cases"],
            "passed": contract_passed,
        },
        "review_on_negative_delta": review_rows,
        "strict_passed": contract_passed and all(row["passed"] for row in strict_rows),
        "requires_explanation": any(row["requires_review"] for row in review_rows),
    }


def structural_audit(repo: Repository, points, generation: dict, search: dict) -> dict:
    membership_kinds = set(generation["representation_counts"])
    vector_kinds = {str(point.metadata.get("kind")) for point in points}
    vector_generations = {str(point.metadata.get("generation_id")) for point in points}
    duplicate_result_cases = []
    for case in search["cases"]:
        for mode, row in case["modes"].items():
            ids = row["ids"]
            if len(ids) != len(set(ids)):
                duplicate_result_cases.append(f"{case['id']}:{mode}")
    allowed = {"object_overview", "facet", "statement"}
    return {
        "active_generation_contract": generation["contract_key"],
        "membership_kinds": sorted(membership_kinds),
        "vector_kinds": sorted(vector_kinds),
        "vector_generation_ids": sorted(vector_generations),
        "object_overall_leakage": "object_overall" in membership_kinds
        or "object_overall" in vector_kinds,
        "allowed_family_only": membership_kinds <= allowed and vector_kinds <= allowed,
        "single_generation_payload": vector_generations == {GENERATION_ID},
        "one_object_one_result": not duplicate_result_cases,
        "duplicate_result_cases": duplicate_result_cases,
    }


def torch_resource_snapshot() -> dict:
    try:
        import torch
    except ImportError:
        return {"cuda_available": False, "torch_available": False}
    output = {"torch_available": True, "cuda_available": bool(torch.cuda.is_available())}
    if torch.cuda.is_available():
        output.update(
            {
                "device": torch.cuda.get_device_name(0),
                "max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                "max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "benchmark/search-quality-gold-v1.json",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "benchmark/n05d04r2-search-quality-acceptance-v1.json",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT / ".local/n05d04r2-search-quality.sqlite",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".local/n05d04r2-search-quality-result.json",
    )
    parser.add_argument("--cache", type=Path, default=ROOT / ".local/hf-2026/hub")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    gold = load_gold(args.fixture)
    contract = load_contract(args.contract)
    _clean_db(args.db)
    repo = Repository(args.db)
    started = time.perf_counter()
    try:
        refs = populate_repository(repo, gold)
        generation = materialize_r2_generation(repo)
        provider = default_sentence_transformer_provider(
            cache_folder=str(args.cache), local_files_only=args.local_files_only
        )
        fixed = contract["fixed_runtime"]
        if provider.space.model != fixed["embedding_model"]:
            raise RuntimeError(
                f"R2-08 requires {fixed['embedding_model']}; got {provider.space.model}"
            )
        if provider.space.model_revision != fixed["embedding_revision"]:
            raise RuntimeError("R2-08 embedding revision differs from frozen contract")
        if provider.space.dimension != fixed["embedding_dimension"]:
            raise RuntimeError("R2-08 embedding dimension differs from frozen contract")

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
        except ImportError:
            pass

        representation_count = embed_r2_generation(repo, provider)
        builder = KnowledgeVectorIndexBuilder(
            repo,
            ExactVectorIndexAdapter(),
            generation_id=GENERATION_ID,
        )
        points = builder.points(provider.space)
        full_index = ExactVectorIndexAdapter()
        full_meta = full_index.rebuild(provider.space, points)
        no_statement_index = ExactVectorIndexAdapter()
        no_statement_points = [
            point
            for point in points
            if point.metadata.get("kind") != SearchRepresentationKind.STATEMENT.value
        ]
        no_statement_index.rebuild(provider.space, no_statement_points)
        engine = HybridObjectSearch(repo, embedding_provider=provider, vector_index=full_index)
        no_statement_engine = HybridObjectSearch(
            repo,
            embedding_provider=provider,
            vector_index=no_statement_index,
        )

        search = evaluate_search(gold, engine, no_statement_engine, provider, full_index, refs)
        contracts = evaluate_contracts(gold, engine)
        similarity = evaluate_similarity(gold, repo, provider, full_index)
        evidence = evaluate_evidence(gold, repo, provider)
        result = {
            "schema_version": "sgokb.n05d04r2-search-quality-result/1.0",
            "contract_id": contract["contract_id"],
            "dataset_id": gold["dataset_id"],
            "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
            "contract_sha256": hashlib.sha256(args.contract.read_bytes()).hexdigest(),
            "embedding_space": provider.space.configuration_payload,
            "generation": generation,
            "canonical": {
                "objects": len(gold["objects"]),
                "accepted_versions": sum(len(item["versions"]) for item in gold["objects"]),
                "r2_search_representations": representation_count,
                "r2_vector_points": full_meta.points_count,
            },
            "search": search,
            "contracts": contracts,
            "similarity": similarity,
            "evidence_search": evidence,
        }
        result["structural_audit"] = structural_audit(repo, points, generation, search)
        result["baseline_evaluation"] = evaluate_baseline_gates(result, contract)
        result["resource_observation"] = torch_resource_snapshot()
        result["benchmark_seconds"] = time.perf_counter() - started

        structure = result["structural_audit"]
        baseline = result["baseline_evaluation"]
        automatic_pass = (
            baseline["strict_passed"]
            and not structure["object_overall_leakage"]
            and structure["allowed_family_only"]
            and structure["single_generation_payload"]
            and structure["one_object_one_result"]
        )
        result["automatic_verdict"] = "PASS" if automatic_pass else "FAIL"
        result["manual_review_required"] = baseline["requires_explanation"]
        result["final_r2_08_verdict"] = "PENDING_CONTRACT_TESTS_AND_REVIEW"

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    "automatic_verdict": result["automatic_verdict"],
                    "manual_review_required": result["manual_review_required"],
                    "canonical": result["canonical"],
                    "generation": result["generation"],
                    "structural_audit": result["structural_audit"],
                    "baseline_evaluation": result["baseline_evaluation"],
                    "resource_observation": result["resource_observation"],
                    "benchmark_seconds": result["benchmark_seconds"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print("saved", args.output)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
