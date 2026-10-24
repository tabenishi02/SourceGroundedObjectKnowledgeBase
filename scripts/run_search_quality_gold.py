"""Build the frozen I-07 canonical search gold and evaluate retrieval quality."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sgokb.domain import (  # noqa: E402
    AssociationStatus,
    DerivationKind,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
    ObjectSearchFilters,
    ObjectSearchMode,
    SearchRepresentationKind,
)
from sgokb.repository import Repository  # noqa: E402
from sgokb.retrieval import (  # noqa: E402
    ExactVectorIndexAdapter,
    HybridObjectSearch,
    KnowledgeVectorIndexBuilder,
    ObjectEvidenceRetriever,
    ObjectSimilaritySearch,
    SearchRepresentationBuilder,
    aggregate_metric_rows,
    default_sentence_transformer_provider,
    latency_summary,
    ranked_retrieval_metrics,
)


def load_gold(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != "sgokb.search-gold/1.0" or value.get("status") != "frozen":
        raise ValueError("Frozen sgokb.search-gold/1.0 fixture required")
    return value


def class_id(repo: Repository, key: str) -> str:
    return repo.object_store.class_by_key(key).class_id


def facet_id(repo: Repository, key: str) -> str:
    return repo.semantic_store.facet_by_key(key).facet_id


def make_source_evidence(
    repo: Repository, source_id: str, evidence_id: str, title: str, content: str
):
    store = repo.source_store
    store.create_source(f"Gold source: {title}", source_id=source_id)
    locator = store.add_locator(
        source_id, "url", f"https://gold.invalid/{source_id}", preferred=True
    )
    snapshot_id = f"snap:{source_id}"
    store.create_snapshot(
        source_id,
        "2026-10-14T00:00:00Z",
        "synthetic_gold",
        observed_locator_id=locator,
        title=title,
        snapshot_id=snapshot_id,
    )
    raw = content.encode("utf-8")
    artifact_id = store.add_raw_artifact(
        snapshot_id,
        "text",
        f"memory://{source_id}",
        hashlib.sha256(raw).hexdigest(),
        len(raw),
        media_type="text/plain",
        artifact_id=f"raw:{source_id}",
    )
    run_id = store.create_normalization_run(
        snapshot_id,
        "synthetic-gold",
        "1",
        [artifact_id],
        run_id=f"run:{source_id}",
    )
    store.add_evidence(
        run_id,
        content,
        EvidenceExtractionMode.NORMALIZED,
        language="ja",
        evidence_id=evidence_id,
    )
    store.select_effective_snapshot(source_id, snapshot_id, reason="I-07 synthetic gold")
    store.select_effective_run(snapshot_id, run_id, reason="I-07 synthetic gold")
    return evidence_id


def populate_repository(
    repo: Repository, gold: dict, *, builder_factory=SearchRepresentationBuilder
) -> dict:
    statement_refs: dict[str, str] = {}
    current_versions: dict[str, str] = {}
    evidence_by_object: dict[str, list[str]] = {}
    builder = builder_factory(repo)

    for item in gold["objects"]:
        oid = item["id"]
        repo.object_store.create_object(
            item["name"],
            class_id(repo, item["primary_class"]),
            item.get("aliases", ()),
            object_id=oid,
        )
        for key in item.get("additional_classes", ()):
            repo.object_store.add_additional_class(oid, class_id(repo, key))
        previous = None
        for version_number, version in enumerate(item["versions"], start=1):
            version_id = repo.version_store.begin_candidate(oid, previous, version_id=version["id"])
            evidence_text = (
                item["name"] + "\n" + "\n".join(s["text"] for s in version["statements"])
            )
            evidence_id = make_source_evidence(
                repo,
                version["source_id"],
                version["evidence_id"],
                f"{item['name']} version {version_number}",
                evidence_text,
            )
            repo.source_store.associate_object(
                version["source_id"],
                oid,
                AssociationStatus.CONFIRMED,
                subject_relationship="primary_subject",
            )
            evidence_by_object.setdefault(oid, []).append(evidence_id)
            local_refs = []
            for statement_number, statement in enumerate(version["statements"]):
                fkey = statement["facet"]
                fid = facet_id(repo, fkey)
                repo.semantic_store.set_version_facet(version_id, fid, FacetStatus.CONTENT)
                temporal_scope_id = None
                if statement.get("temporal"):
                    temporal_scope_id = repo.semantic_store.create_temporal_scope(
                        version_id, **statement["temporal"]
                    )
                local_key = statement.get("key") or f"s{statement_number}"
                sid = repo.semantic_store.add_statement(
                    version_id,
                    local_key,
                    statement["text"],
                    statement.get("derivation", DerivationKind.DIRECT_STATEMENT),
                    facet_id=fid,
                    language="ja",
                    temporal_scope_id=temporal_scope_id,
                )
                repo.source_store.link_evidence(
                    version_id, EvidenceTargetKind.STATEMENT, sid, evidence_id
                )
                local_refs.append((local_key, sid))
            repo.version_store.accept_candidate(version_id)
            builder.materialize_version(version_id)
            ref_version = (
                "current" if version_number == len(item["versions"]) else f"v{version_number}"
            )
            for local_key, sid in local_refs:
                statement_refs[f"{oid}@{ref_version}:{local_key}"] = sid
            previous = version_id
        current_versions[oid] = previous
        # Historical sources should not pollute current Evidence Search.
        for historical in item["versions"][:-1]:
            repo.source_store.associate_object(
                historical["source_id"],
                oid,
                AssociationStatus.EXCLUDED,
                note="historical gold source",
            )

    for noise in gold.get("noise_sources", ()):
        make_source_evidence(
            repo,
            noise["source_id"],
            noise["evidence_id"],
            noise["source_id"],
            noise["content"],
        )
    return {
        "statement_refs": statement_refs,
        "current_versions": current_versions,
        "evidence_by_object": evidence_by_object,
    }


def embed_representations(repo: Repository, provider) -> int:
    rows = repo.rows(
        """SELECT DISTINCT r.id,r.content
           FROM search_representations r
           JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
           ORDER BY r.id"""
    )
    vectors = provider.embed_documents([row["content"] for row in rows])
    for row, vector in zip(rows, vectors):
        repo.embedding_store.save_representation_embedding(provider.space, row["id"], vector)
    return len(rows)


def filters_from(value: dict | None) -> ObjectSearchFilters:
    return ObjectSearchFilters(**(value or {}))


def result_ids(response) -> list[str]:
    return [result.object_id for result in response.results]


def evaluate_search(gold, engine, no_statement_engine, provider, full_index, refs):
    modes = (ObjectSearchMode.LEXICAL, ObjectSearchMode.SEMANTIC, ObjectSearchMode.HYBRID)
    mode_rows = {mode.value: [] for mode in modes}
    mode_latencies = {mode.value: [] for mode in modes}
    case_rows = []
    statement_rows = []
    statement_latencies = []
    no_statement_rows = []
    full_statement_query_rows = []
    exact_lookup_ok = 0
    exact_lookup_total = 0

    for case in gold["search_queries"]:
        filters = filters_from(case.get("filters"))
        row = {"id": case["id"], "category": case["category"], "modes": {}}
        for mode in modes:
            started = time.perf_counter()
            response = engine.search(case["query"], filters=filters, limit=10, mode=mode)
            elapsed = time.perf_counter() - started
            metrics = ranked_retrieval_metrics(result_ids(response), case["relevance"])
            mode_rows[mode.value].append(metrics)
            mode_latencies[mode.value].append(elapsed)
            row["modes"][mode.value] = {
                "ids": result_ids(response),
                "metrics": metrics,
                "degraded": list(response.degraded_channels),
            }
            if mode is ObjectSearchMode.LEXICAL and case["category"] in {
                "exact_name",
                "exact_alias",
            }:
                exact_lookup_total += 1
                exact_lookup_ok += int(
                    bool(response.results) and response.results[0].object_id in case["relevance"]
                )

        if case.get("statement_refs"):
            query_vector = provider.embed_queries([case["query"]])[0]
            vf = engine._vector_filters(filters, SearchRepresentationKind.STATEMENT)
            started = time.perf_counter()
            hits = full_index.search(provider.space, query_vector, limit=10, filters=vf)
            statement_latencies.append(time.perf_counter() - started)
            ranked_statements = [str(hit.metadata.get("statement_id")) for hit in hits]
            relevance = {refs["statement_refs"][ref]: 3 for ref in case["statement_refs"]}
            sm = ranked_retrieval_metrics(ranked_statements, relevance)
            statement_rows.append(sm)
            row["statement_semantic"] = {"ids": ranked_statements, "metrics": sm}

            full_response = engine.search(case["query"], filters=filters, limit=10, mode="hybrid")
            nost_response = no_statement_engine.search(
                case["query"], filters=filters, limit=10, mode="hybrid"
            )
            full_statement_query_rows.append(
                ranked_retrieval_metrics(result_ids(full_response), case["relevance"])
            )
            no_statement_rows.append(
                ranked_retrieval_metrics(result_ids(nost_response), case["relevance"])
            )
        case_rows.append(row)

    return {
        "modes": {
            mode.value: {
                "quality": aggregate_metric_rows(mode_rows[mode.value]),
                "latency": latency_summary(mode_latencies[mode.value]),
            }
            for mode in modes
        },
        "statement_semantic": {
            "quality": aggregate_metric_rows(statement_rows),
            "latency": latency_summary(statement_latencies),
            "cases": len(statement_rows),
        },
        "statement_embedding_ablation": {
            "with_statement": aggregate_metric_rows(full_statement_query_rows),
            "without_statement": aggregate_metric_rows(no_statement_rows),
            "cases": len(no_statement_rows),
        },
        "exact_lookup_accuracy": exact_lookup_ok / exact_lookup_total
        if exact_lookup_total
        else None,
        "cases": case_rows,
    }


def evaluate_contracts(gold, engine):
    output = []
    for case in gold["contract_cases"]:
        response = engine.search(
            case["query"],
            filters=filters_from(case.get("filters")),
            limit=10,
            mode=case["mode"],
        )
        ids = result_ids(response)
        passed = all(x in ids for x in case.get("expected_present", ())) and all(
            x not in ids for x in case.get("expected_absent", ())
        )
        if case.get("expected_version") and case.get("expected_present"):
            wanted = case["expected_present"][0]
            selected = next((r for r in response.results if r.object_id == wanted), None)
            passed = (
                passed and selected is not None and selected.version_id == case["expected_version"]
            )
        if case.get("expected_match_facets"):
            allowed = set(case["expected_match_facets"])
            for result in response.results:
                if result.object_id in case.get("expected_present", ()):
                    passed = passed and set(result.matched_facets).issubset(allowed)
        output.append({"id": case["id"], "passed": bool(passed), "ids": ids})
    return {"passed": sum(row["passed"] for row in output), "total": len(output), "cases": output}


def evaluate_similarity(gold, repo, provider, index):
    engine = ObjectSimilaritySearch(repo, space=provider.space, vector_index=index)
    rows = []
    cases = []
    for case in gold["similarity_cases"]:
        response = engine.find_similar_objects(
            case["source_object_id"], facet=case.get("facet"), limit=10
        )
        ids = [item.object_id for item in response.results]
        metric = ranked_retrieval_metrics(ids, case["relevance"])
        rows.append(metric)
        cases.append({"id": case["id"], "ids": ids, "metrics": metric})
    overall_rows = [
        metric for metric, case in zip(rows, gold["similarity_cases"]) if not case.get("facet")
    ]
    facet_rows = [
        metric for metric, case in zip(rows, gold["similarity_cases"]) if case.get("facet")
    ]
    return {
        "judgement_channel": "human_authored_synthetic_gold",
        "quality": aggregate_metric_rows(rows),
        "overall_quality": aggregate_metric_rows(overall_rows),
        "facet_quality": aggregate_metric_rows(facet_rows),
        "cases": cases,
    }


def evaluate_evidence(gold, repo, provider):
    output = {}
    for semantic in (False, True):
        retriever = ObjectEvidenceRetriever(repo, embedder=provider if semantic else None)
        rows = []
        cases = []
        for case in gold["evidence_cases"]:
            response = retriever.retrieve(case["object_id"], semantic=semantic, max_candidates=20)
            ids = [item.evidence_id for item in response["candidates"]]
            metric = ranked_retrieval_metrics(ids, case["relevance"])
            rows.append(metric)
            cases.append({"id": case["id"], "ids": ids, "metrics": metric})
        output["semantic" if semantic else "lexical_association"] = {
            "quality": aggregate_metric_rows(rows),
            "cases": cases,
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture", type=Path, default=ROOT / "benchmark/search-quality-gold-v1.json"
    )
    parser.add_argument("--db", type=Path, default=ROOT / ".local/i07-search-gold.sqlite")
    parser.add_argument("--output", type=Path, default=ROOT / ".local/i07-search-gold-result.json")
    parser.add_argument("--cache", type=Path, default=ROOT / ".local/hf-2026/hub")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    gold = load_gold(args.fixture)
    if args.db.exists():
        args.db.unlink()
    for suffix in ("-wal", "-shm"):
        candidate = Path(str(args.db) + suffix)
        if candidate.exists():
            candidate.unlink()
    repo = Repository(args.db)
    try:
        refs = populate_repository(repo, gold)
        provider = default_sentence_transformer_provider(
            cache_folder=str(args.cache), local_files_only=args.local_files_only
        )
        representation_count = embed_representations(repo, provider)
        builder = KnowledgeVectorIndexBuilder(repo, ExactVectorIndexAdapter())
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
            repo, embedding_provider=provider, vector_index=no_statement_index
        )

        started = time.perf_counter()
        search = evaluate_search(gold, engine, no_statement_engine, provider, full_index, refs)
        contracts = evaluate_contracts(gold, engine)
        similarity = evaluate_similarity(gold, repo, provider, full_index)
        evidence = evaluate_evidence(gold, repo, provider)
        total_seconds = time.perf_counter() - started
        result = {
            "schema_version": "sgokb.search-gold-result/1.0",
            "dataset_id": gold["dataset_id"],
            "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
            "embedding_space": provider.space.configuration_payload,
            "canonical": {
                "objects": len(gold["objects"]),
                "accepted_versions": sum(len(item["versions"]) for item in gold["objects"]),
                "search_representations": representation_count,
                "vector_points": full_meta.points_count,
            },
            "search": search,
            "contracts": contracts,
            "similarity": similarity,
            "evidence_search": evidence,
            "benchmark_seconds": total_seconds,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = {
            "canonical": result["canonical"],
            "modes": search["modes"],
            "statement_semantic": search["statement_semantic"],
            "statement_embedding_ablation": search["statement_embedding_ablation"],
            "exact_lookup_accuracy": search["exact_lookup_accuracy"],
            "contracts": {"passed": contracts["passed"], "total": contracts["total"]},
            "similarity": similarity["quality"],
            "evidence": {k: v["quality"] for k, v in evidence.items()},
            "seconds": total_seconds,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("saved", args.output)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
