"""Paired downstream integration on private copies of the accepted capture results."""

import argparse
import os
import re
import sqlite3
import time
from pathlib import Path

from run_efficiency_capture_comparison import checksum, read, source_fingerprint, write

from cpc.application import Application
from cpc.claims import build_claims
from cpc.domain import SearchFilter, digest, json_text
from cpc.final import CATEGORIES, LABELS
from cpc.providers import CompatibleEmbedder
from cpc.repository import Repository
from cpc.views import build_view


def run(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = args.source.resolve()
    if out == source or source in out.parents:
        raise ValueError("Output must be separate from extraction source")
    plan = read(source / "plan.json")
    if read(source / "status.json")["status"] != "completed":
        raise ValueError("Completed extraction comparison required")
    entities = sorted({case["entity_id"] for case in plan["cases"]})
    manifest = read(Path("benchmark/sample-v1.json"))
    queries = [c for c in manifest["cases"] if c["task"] == "retrieval"]
    state_path = out / "status.json"
    state = read(state_path) if state_path.exists() else {"completed": []}
    if state_path.exists() and not args.resume:
        raise ValueError("Existing output requires --resume")
    state.update(status="running", pid=os.getpid(), current="prepare")
    write(state_path, state)
    fingerprints = {
        s: source_fingerprint(source / s / "captures.sqlite") for s in ("before", "after")
    }
    raw = {c["raw_path"]: (c["raw_sha256"], c["raw_mtime_ns"]) for c in plan["cases"]}
    frozen = {"sources": fingerprints, "queries": queries, "revision": args.revision}
    if (out / "conditions.json").exists():
        if read(out / "conditions.json") != frozen:
            raise ValueError("Resume conditions changed")
    else:
        write(out / "conditions.json", frozen)

    def phase(key, operation):
        target = out / (key.replace("/", "-") + ".json")
        if key in state["completed"]:
            return read(target)
        state["current"] = key
        write(state_path, state)
        start = time.perf_counter()
        result = operation()
        result["seconds"] = time.perf_counter() - start
        write(target, result)
        state["completed"].append(key)
        write(state_path, state)
        return result

    try:
        for side in ("before", "after"):
            directory = out / side
            directory.mkdir(exist_ok=True)
            target = directory / "captures.sqlite"
            if not target.exists():
                original = sqlite3.connect(
                    (source / side / "captures.sqlite").as_uri() + "?mode=ro", uri=True
                )
                copy = sqlite3.connect(target)
                try:
                    original.backup(copy)
                finally:
                    original.close()
                    copy.close()
            repo = Repository(target)
            try:
                app = Application(repo)
                rows = {e: repo.related_fragments(e) for e in entities}
                expected = sum(
                    read(source / side / f"{c['id']}-result.json")["result"]["fragments"]
                    for c in plan["cases"]
                )
                assert sum(map(len, rows.values())) == expected, "Unexpected active fragment set"
                input_hash = digest(json_text(rows))

                def derived():
                    results = []
                    for index, entity in enumerate(entities):
                        claims = build_claims(repo, entity)["claims"]
                        ids = {r["id"] for r in rows[entity]}
                        by_id = {r["id"]: r for r in rows[entity]}
                        assert {f for c in claims for f in c["fragment_ids"]} == ids
                        for claim in claims:
                            for fragment in claim["fragment_ids"]:

                                def normalized(text):
                                    return re.sub(r"\s+", "", text).rstrip("。．.!！")

                                assert normalized(claim["text"]) == normalized(
                                    by_id[fragment]["content"]
                                )
                                assert claim["facet"] == by_id[fragment]["facet"]
                                for key in (
                                    "subject",
                                    "epistemic_type",
                                    "asserted_by",
                                    "temporal_context",
                                    "evidence_strength",
                                    "conflict_group",
                                ):
                                    assert claim[key] == by_id[fragment]["metadata"].get(key)
                        write(directory / f"entity-{index}-claims.json", {"claims": claims})
                        views = []
                        for mode in ("short", "standard", "detailed", "context"):
                            view = build_view(repo, entity, mode=mode, context_tokens=65536)
                            selected = set(view["structured"]["selected_claim_ids"])
                            omitted = {v["claim_id"] for v in view["omission_manifest"]["omitted"]}
                            assert not selected & omitted and selected | omitted == {
                                c["id"] for c in claims
                            }
                            assert view["output_tokens"] <= view["configuration"]["budget"]
                            (directory / f"entity-{index}-{mode}.md").write_text(
                                view["markdown"], encoding="utf-8"
                            )
                            write(
                                directory / f"entity-{index}-{mode}-omitted.json",
                                view["omission_manifest"],
                            )
                            views.append(
                                {
                                    "mode": mode,
                                    "selected": len(selected),
                                    "omitted": len(omitted),
                                    "budget_units": view["output_tokens"],
                                    "counter": view["configuration"]["counter"],
                                }
                            )
                        start = time.perf_counter()
                        final = app.build_document(entity, use_llm=False)
                        rep = final["structured"]
                        groups = [c for key in LABELS for c in rep[key]]
                        assert {f for c in groups for f in c["fragment_ids"]} == ids
                        assert final["citations"] == len(ids)
                        assert len(groups) == final["clusters"]
                        for category in LABELS:
                            for cluster in rep[category]:
                                assert (
                                    CATEGORIES.get(cluster["epistemic_type"], "unknown") == category
                                )
                                for fragment in cluster["fragment_ids"]:
                                    for key in (
                                        "epistemic_type",
                                        "asserted_by",
                                        "evidence_strength",
                                        "temporal_context",
                                        "conflict_group",
                                    ):
                                        assert cluster[key] == by_id[fragment]["metadata"].get(key)
                        for fragment in ids:
                            provenance = repo.provenance("fragment", fragment)
                            assert provenance["evidence"] and all(
                                e["evidence_id"] for e in provenance["evidence"]
                            )
                        (directory / f"entity-{index}-final.md").write_text(
                            final["markdown"], encoding="utf-8"
                        )
                        write(directory / f"entity-{index}-final.json", rep)
                        results.append(
                            {
                                "entity_index": index,
                                "fragments": len(ids),
                                "claims": len(claims),
                                "views": views,
                                "final_clusters": final["clusters"],
                                "final_characters": len(final["markdown"]),
                                "final_seconds": time.perf_counter() - start,
                            }
                        )
                    return {"entities": results, "coverage_and_attributes_preserved": True}

                phase(side + "/derived", derived)
                if args.derived_only:
                    assert (
                        digest(json_text({e: repo.related_fragments(e) for e in entities}))
                        == input_hash
                    )
                    assert repo.one("PRAGMA integrity_check")["integrity_check"] == "ok"
                    assert not repo.rows("PRAGMA foreign_key_check")
                    continue
                app.embedder = CompatibleEmbedder(
                    "http://127.0.0.1:1234/v1",
                    "cpc-downstream-nomic",
                    args.revision,
                    timeout=180,
                    document_prefix="search_document: ",
                    query_prefix="search_query: ",
                    max_chars=600,
                )
                phase(side + "/embedding", lambda: app.embed(incremental=True))

                def cached():
                    result = app.embed(incremental=True)
                    assert result["inferred"] == 0 and result["reused"] == result["embedded"]
                    return result

                phase(side + "/embedding-cache", cached)

                def retrieval():
                    results = []
                    for case in queries:
                        found = app.search(
                            case["query"],
                            SearchFilter(entity=case["entity_id"]),
                            case["k"],
                            case["mode"],
                        )
                        assert found and len(found) <= case["k"]
                        for result in found:
                            assert repo.provenance(result["kind"], result["target_id"])["evidence"]
                        results.append(
                            {
                                "case": case["id"],
                                "count": len(found),
                                "results": found,
                                "semantic_metrics": None,
                                "reason": "human_gold_missing",
                            }
                        )
                    return {"cases": results}

                phase(side + "/retrieval", retrieval)
                assert (
                    digest(json_text({e: repo.related_fragments(e) for e in entities}))
                    == input_hash
                )
                assert repo.one("PRAGMA integrity_check")["integrity_check"] == "ok"
                assert not repo.rows("PRAGMA foreign_key_check")
            finally:
                repo.close()
        assert all(
            source_fingerprint(source / s / "captures.sqlite") == fingerprints[s]
            for s in fingerprints
        )
        assert all(
            checksum(Path(path)) == value[0] and Path(path).stat().st_mtime_ns == value[1]
            for path, value in raw.items()
        )
        summary = {
            "status": "derived_completed" if args.derived_only else "completed",
            "source_db_unchanged": True,
            "raw_unchanged": True,
            "fragments_unchanged": True,
            "integrity": "ok",
            "foreign_key_errors": 0,
            "semantic_quality": "human_gold_missing",
            "llm_ordering": False,
            "completed": state["completed"],
        }
        write(out / "result.json", summary)
        lines = [
            "Fragment downstream comparison",
            "Same downstream implementation; accepted before/after extraction inputs.",
            "Semantic gold unavailable. Final generation is extractive, without LLM ordering.",
            "side | fragments | claims | final clusters | final characters | derived seconds",
        ]
        for side in ("before", "after"):
            derived = read(out / (side + "-derived.json"))
            entities = derived["entities"]
            lines.append(
                f"{side} | {sum(e['fragments'] for e in entities)} | "
                f"{sum(e['claims'] for e in entities)} | "
                f"{sum(e['final_clusters'] for e in entities)} | "
                f"{sum(e['final_characters'] for e in entities)} | {derived['seconds']:.2f}"
            )
            if not args.derived_only:
                embedding = read(out / (side + "-embedding.json"))
                cached = read(out / (side + "-embedding-cache.json"))
                retrieval = read(out / (side + "-retrieval.json"))
                lines.append(
                    f"{side}: embedding {embedding['seconds']:.2f}s / "
                    f"{embedding['embedded']} items; cache {cached['seconds']:.2f}s / "
                    f"{cached['inferred']} inferred; retrieval {retrieval['seconds']:.2f}s / "
                    f"{len(retrieval['cases'])} cases."
                )
        lines.append("Integrity and input immutability checks passed. " + summary["status"])
        (out / "comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        state.update(status=summary["status"], current=None)
        write(state_path, state)
    except Exception as error:
        state.update(status="failed", error=str(error), error_type=type(error).__name__)
        write(state_path, state)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("sample/efficiency-capture-comparison-v2")
    )
    parser.add_argument("--out", type=Path, default=Path("sample/fragment-downstream"))
    parser.add_argument("--revision", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--derived-only", action="store_true")
    run(parser.parse_args())
