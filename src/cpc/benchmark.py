"""Versioned local-only experiments. Automatic metrics never masquerade as semantic gold."""

import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from .domain import SearchFilter, digest, json_text
from .transport import KEYS


def require_local(provider):
    if provider is None:
        return
    url = getattr(provider, "base_url", None)
    if url and urlsplit(url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Benchmarks require a loopback local AI provider")


def retrieval_metrics(ids, relevance, k=10):
    if relevance is None:
        return {"recall_at_k": None, "mrr": None, "ndcg_at_k": None, "reason": "gold_missing"}
    relevant = {i for i, score in relevance.items() if score > 0}
    if not relevant:
        return {"recall_at_k": None, "mrr": None, "ndcg_at_k": None, "reason": "no_relevant_gold"}
    top = ids[:k]
    dcg = sum((2 ** relevance.get(i, 0) - 1) / math.log2(rank + 2) for rank, i in enumerate(top))
    ideal = sum(
        (2**score - 1) / math.log2(rank + 2)
        for rank, score in enumerate(sorted(relevance.values(), reverse=True)[:k])
    )
    return {
        "recall_at_k": len(set(top) & relevant) / len(relevant),
        "mrr": next((1 / (r + 1) for r, i in enumerate(ids) if i in relevant), 0),
        "ndcg_at_k": dcg / ideal if ideal else None,
    }


def judgement_metrics(labels):
    """Only consume explicitly supplied human/judge labels; preserve the judging channel."""
    if labels.get("channel") not in {"human", "llm_judge"}:
        raise ValueError("Semantic labels must declare human or llm_judge")
    items = labels.get("fragments", [])
    n = len(items)
    supported = [i for i in items if i["supported"]]
    gold = set(labels.get("gold_claim_ids", []))
    covered = {g for i in supported for g in i.get("matched_gold_claim_ids", [])}
    final = labels.get("final", {})
    return {
        "channel": labels["channel"],
        "annotated_fragments": n,
        "fragment_precision": len(supported) / n if n else None,
        "fragment_recall": len(covered & gold) / len(gold) if gold else None,
        "unsupported_rate": 1 - len(supported) / n if n else None,
        "epistemic_accuracy": sum(i["epistemic_correct"] for i in items) / n if n else None,
        "atomicity": sum(i["atomic"] for i in items) / n if n else None,
        "final": {
            key: final.get(key)
            for key in (
                "information_coverage",
                "unsupported_rate",
                "epistemic_separation",
                "structure",
                "redundancy",
                "conflict_retention",
                "citation_correctness",
            )
        },
    }


def run_benchmark(
    app, manifest_path, phase="all", strategy="single_pass", resume=None, on_start=None
):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not manifest.get("benchmark_version") or not manifest.get("cases"):
        raise ValueError("Versioned benchmark cases required")
    selected = {
        **manifest,
        "cases": [c for c in manifest["cases"] if phase == "all" or c["task"] == phase],
    }
    if not selected["cases"] or len({c["id"] for c in selected["cases"]}) != len(selected["cases"]):
        raise ValueError("Nonempty unique benchmark cases required")
    require_local(app.llm)
    require_local(app.embedder)
    extraction_options = manifest.get("extraction_options", {})
    if set(extraction_options) - {
        "transport",
        "dedup_quotes",
        "window_checkpoint",
        "packer",
        "token_counter",
        "material_tokens",
        "context_tokens",
        "output_tokens",
        "safety_margin",
    }:
        raise ValueError("Unknown extraction comparison option")
    schema_hashes, prompt_hashes = {}, {}
    for name in ("high_recall", "final_order"):
        prompt, _ = app.prompt(name)
        prompt_hashes[name] = digest(prompt)
        schema_hashes[name] = digest((app.prompt_dir / (name + ".schema.json")).read_bytes())
    config = {
        "transport_map_hash": digest(json_text(KEYS)),
        "extraction_options": extraction_options,
        "dataset_version": manifest["benchmark_version"],
        "phase": phase,
        "strategy": strategy,
        "llm": {
            "model": getattr(app.llm, "model", None),
            "revision": getattr(app.llm, "revision", None),
            "configuration": getattr(app.llm, "configuration", {}),
        },
        "embedding": {
            "model": getattr(app.embedder, "model", None),
            "revision": getattr(app.embedder, "revision", None),
            "configuration": getattr(app.embedder, "configuration", None),
        },
        "reranker": getattr(app.reranker, "version", "rrf60-literal-v1"),
        "prompt_hashes": prompt_hashes,
        "schema_hashes": schema_hashes,
    }
    repo = app.repository
    if resume:
        run = repo.one("SELECT * FROM benchmark_runs WHERE id=?", (resume,))
        if (
            not run
            or run["manifest_hash"] != digest(json_text(selected))
            or json.loads(run["configuration"]) != config
        ):
            raise ValueError("Benchmark resume conditions differ")
        run_id = resume
    else:
        run_id = repo.start_benchmark(selected, config)
    if on_start:
        on_start(run_id)
    checkpoints = {
        c["case_id"]: c
        for c in repo.rows("SELECT * FROM benchmark_cases WHERE run_id=?", (run_id,))
    }
    refreshed_embeddings = False
    for case in selected["cases"]:
        checkpoint = checkpoints[case["id"]]
        if checkpoint["status"] == "success":
            continue
        try:
            snapshot = repo.snapshot(case["snapshot_id"]) if case.get("snapshot_id") else None
            if snapshot and case.get("raw_sha256") != snapshot["raw_sha256"]:
                raise ValueError("Benchmark raw dataset hash differs")
            if case["task"] == "fragment":
                previous = json.loads(checkpoint["result"]) if checkpoint["result"] else {}
                result = app.capture_fragments(
                    snapshot["id"],
                    case["entity_id"],
                    strategy=strategy,
                    resume=previous.get("job_id"),
                    batch_size=manifest.get("fragment_batch_size", 4),
                    **extraction_options,
                )
                result["input_set"] = {
                    "normalized_run": snapshot["active_run"],
                    "evidence_hash": digest(
                        json_text(
                            [(e["id"], e["content_hash"]) for e in repo.evidence(snapshot["id"])]
                        )
                    ),
                }
                result["semantic_metrics"] = {
                    key: None
                    for key in (
                        "recall",
                        "precision",
                        "unsupported_rate",
                        "epistemic_accuracy",
                        "atomicity",
                    )
                }
                result["semantic_metrics"]["reason"] = "human_gold_missing"
                repo.benchmark_case(
                    run_id,
                    case["id"],
                    result,
                    error="IncompleteExtraction" if result["status"] != "complete" else None,
                )
            elif case["task"] == "retrieval":
                if phase == "all" and not refreshed_embeddings:
                    app.embed()
                    refreshed_embeddings = True
                mode = case.get("mode", "hybrid")
                found = app.search(
                    case["query"], SearchFilter(entity=case["entity_id"]), case.get("k", 10), mode
                )
                ids = [r["target_id"] for r in found]
                repo.benchmark_case(
                    run_id,
                    case["id"],
                    {
                        "ids": ids,
                        "mode": mode,
                        "metrics": retrieval_metrics(ids, case.get("relevance"), case.get("k", 10)),
                    },
                )
            elif case["task"] == "final":
                result = app.build_document(case["entity_id"], use_llm=case.get("llm_order", False))
                rep = result["structured"]
                repo.benchmark_case(
                    run_id,
                    case["id"],
                    {
                        "document_id": result["document_id"],
                        "characters": len(result["markdown"]),
                        "sections": result["markdown"].count("\n## "),
                        "citations": result["citations"],
                        "clusters": result["clusters"],
                        "conflicts": len(rep["conflicts"]),
                        "information_types": {
                            k: len(rep[k])
                            for k in (
                                "facts",
                                "source_interpretations",
                                "derived_interpretations",
                                "public_perception",
                            )
                        },
                        "semantic_metrics": {
                            "reason": "human_gold_missing",
                            **{
                                k: None
                                for k in (
                                    "information_coverage",
                                    "unsupported_rate",
                                    "structure",
                                    "redundancy",
                                    "epistemic_separation",
                                    "conflict_retention",
                                    "citation_correctness",
                                )
                            },
                        },
                    },
                )
            else:
                raise ValueError("Unknown benchmark task")
        except Exception as error:
            repo.benchmark_case(run_id, case["id"], error=type(error).__name__)
    return repo.finish_benchmark(run_id)
