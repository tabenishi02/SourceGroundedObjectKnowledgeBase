"""Small, resumable local support evaluation without re-extracting accepted Captures."""

import argparse
import os
import sqlite3
import time
from pathlib import Path

from run_efficiency_capture_comparison import read, runtime, source_fingerprint, write

from cpc.application import Application
from cpc.benchmark import require_local
from cpc.claims import build_claims
from cpc.domain import digest, json_text
from cpc.providers import llm_from_env
from cpc.quality import quality_metrics, speed_metrics
from cpc.reading import reading_final
from cpc.repository import Repository
from cpc.support import contract_hash, review_claim
from cpc.views import build_view


def run(args):
    source, out = args.source.resolve(), args.out.resolve()
    if out == source.parent or source.parent in out.parents:
        raise ValueError("Use a separate output directory")
    if not any(p in out.parents for p in (Path("sample").resolve(), Path(".local").resolve())):
        raise ValueError("Evaluation output must be private under sample/ or .local/")
    if args.limit < 1:
        raise ValueError("Invalid candidate limit")
    if args.labels and not args.live:
        raise ValueError("Reference labels require --live")
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / "status.json"
    if state_path.exists() and not args.resume:
        raise ValueError("Existing evaluation requires --resume")
    state = read(state_path) if state_path.exists() else {"completed": []}
    llm = llm_from_env("fragment") if args.live else None
    require_local(llm)
    conditions = {
        "source": source_fingerprint(source),
        "limit": args.limit,
        "contract": contract_hash(),
        "implementation_hash": digest(
            json_text(
                [
                    Path(__file__).read_text(encoding="utf-8"),
                    *[
                        (Path(__file__).resolve().parents[1] / "src/cpc" / name).read_text(
                            encoding="utf-8"
                        )
                        for name in (
                            "support.py",
                            "views.py",
                            "reading.py",
                            "providers.py",
                            "quality.py",
                        )
                    ],
                ]
            )
        ),
        "live": args.live,
        "provider": getattr(llm, "configuration", None),
        "model": getattr(llm, "model", None),
        "revision": getattr(llm, "revision", None),
        "runtime": runtime()
        if args.live and llm.configuration.get("adapter", "").startswith("strata")
        else None,
        "labels_hash": digest(args.labels.read_bytes()) if args.labels else None,
    }
    frozen = out / "conditions.json"
    if frozen.exists() and read(frozen) != conditions:
        raise ValueError("Resume inputs/runtime changed")
    write(frozen, conditions)
    state.update(status="running", pid=os.getpid())
    state["current"] = "prepare"
    write(state_path, state)
    db = out / "captures.sqlite"
    try:
        if not db.exists():
            wal = Path(str(source) + "-wal")
            if wal.exists() and wal.stat().st_size:
                raise ValueError("Source WAL is active; use a settled source snapshot")
            with sqlite3.connect(source.as_uri() + "?mode=ro&immutable=1", uri=True) as reader:
                with sqlite3.connect(db) as destination:
                    reader.backup(destination)
        repo = Repository(db)
    except Exception as error:
        state.update(status="failed", error=type(error).__name__)
        write(state_path, state)
        raise
    app = Application(repo, llm)
    before = digest(json_text([dict(r) for r in repo.rows("SELECT * FROM fragments ORDER BY id")]))
    baseline = out / "fragment-baseline.json"
    if baseline.exists():
        before = read(baseline)["hash"]
    else:
        write(baseline, {"hash": before})

    def phase(key, operation):
        target = out / (key + ".json")
        if key in state["completed"]:
            return read(target)
        state["current"] = key
        write(state_path, state)
        started = time.perf_counter()
        result = operation()
        write(target, {**result, "stage_seconds": time.perf_counter() - started})
        state["completed"].append(key)
        write(state_path, state)
        return result

    try:
        entities = [e for e in repo.entities() if repo.related_fragments(e["id"])]
        candidates = []
        for n, entity in enumerate(entities):
            views = {}
            for mode in ("short", "standard", "detailed"):
                view = phase(
                    f"entity-{n}-{mode}", lambda m=mode: build_view(repo, entity["id"], mode=m)
                )
                (out / f"entity-{n}-{mode}.md").write_text(view["markdown"], encoding="utf-8")
                views[mode] = view
            candidates.extend(views["short"]["structured"]["claims"])
            phase(f"entity-{n}-reading", lambda: reading_final(repo, entity["id"]))
            # These query examples have no gold until reference IDs are supplied.
            for q, query in enumerate(("性格 人物像", "所属 ユニット", "ジャンル 仕組み")):
                phase(
                    f"entity-{n}-query-{q}",
                    lambda query=query: build_view(
                        repo, entity["id"], query=query, mode="context", context_tokens=16384
                    ),
                )
        chosen = candidates[: args.limit]
        measurements = []
        if args.live:
            for n, claim in enumerate(chosen):
                phase(f"review-{n}", lambda c=claim: review_claim(app, c))
            if chosen:
                for n in range(4):

                    def measure():
                        start = time.perf_counter()
                        result = review_claim(app, chosen[0], use_cache=False)
                        preflight = (
                            repo.one("SELECT model FROM ai_runs WHERE id=?", (result["ai_run"],))[
                                "model"
                            ]
                            == "cpc-support-preflight"
                        )
                        return {
                            "phase": "warmup" if n == 0 else "warm",
                            "success": True,
                            "duration_seconds": time.perf_counter() - start,
                            "cached": result["cached"],
                            "preflight": preflight,
                            "verdict": result["verdict"],
                            "observation": getattr(llm, "last_observation", {}),
                        }

                    measurements.append(phase(f"speed-{n}", measure))
            for n, entity in enumerate(entities):
                phase(
                    f"entity-{n}-verified",
                    lambda: build_view(repo, entity["id"], supported_only=True),
                )
        quality = {"status": "gold_missing", "human_gold": False}
        if args.labels:
            cases = read(args.labels)
            all_claims = {
                c["id"]: c for e in entities for c in build_claims(repo, e["id"])["claims"]
            }
            for case in cases:
                claim = all_claims[case["claim_id"]]
                result = phase("label-" + claim["id"], lambda: review_claim(app, claim))
                case["actual"] = result["verdict"]
            quality = quality_metrics(cases)
        after = digest(
            json_text([dict(r) for r in repo.rows("SELECT * FROM fragments ORDER BY id")])
        )
        report = {
            "quality": quality,
            "speed": speed_metrics(measurements),
            "fragment_unchanged": before == after,
            "source_unchanged": source_fingerprint(source) == conditions["source"],
            "integrity": repo.one("PRAGMA integrity_check")["integrity_check"],
            "foreign_key_errors": [dict(r) for r in repo.rows("PRAGMA foreign_key_check")],
            "candidates": len(chosen),
            "retrieval_gold": "missing",
        }
        if (
            not report["fragment_unchanged"]
            or not report["source_unchanged"]
            or report["integrity"] != "ok"
            or report["foreign_key_errors"]
        ):
            raise ValueError("Preservation/integrity check failed")
        write(out / "report.json", report)
        state.update(status="completed", current=None)
    except Exception as error:
        state.update(status="failed", error=type(error).__name__, current=state.get("current"))
        raise
    finally:
        write(state_path, state)
        repo.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path("sample/fragment-downstream/after/captures.sqlite")
    )
    parser.add_argument("--out", type=Path, default=Path("sample/pipeline-improvement-evaluation"))
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--resume", action="store_true")
    run(parser.parse_args())
