"""Opt-in local integration: preserve baseline, resume jobs, export aggregate diagnostics."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from sgokb.application import Application
from sgokb.benchmark import run_benchmark
from sgokb.providers import embedder_from_env, llm_from_env
from sgokb.repository import Repository


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path(".local/upgrade.sqlite"))
    parser.add_argument("--baseline", type=Path, default=Path(".local/evaluation.sqlite"))
    parser.add_argument("--manifest", type=Path, default=Path("benchmark/sample-v1.json"))
    parser.add_argument(
        "--phase", choices=["prepare", "fragment", "retrieval", "final", "all"], default="all"
    )
    parser.add_argument("--strategy", default="single_pass")
    parser.add_argument("--resume")
    parser.add_argument("--report", type=Path, default=Path(".local/upgrade-evaluation.json"))
    args = parser.parse_args()
    if args.db.resolve() == args.baseline.resolve():
        raise ValueError("Upgrade evaluation must use a separate DB from the baseline")
    if not args.db.exists():
        args.db.parent.mkdir(parents=True, exist_ok=True)
        source = sqlite3.connect(args.baseline.resolve().as_uri() + "?mode=ro", uri=True)
        target = sqlite3.connect(args.db)
        source.backup(target)
        target.close()
        source.close()
    repo = Repository(args.db)
    raw_before = {
        s["id"]: (s["raw_sha256"], Path(s["raw_path"]).stat().st_mtime_ns) for s in repo.snapshots()
    }
    report = {"phase": args.phase, "db": str(args.db)}

    def checkpoint(run_id):
        report["run_id"] = run_id
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"run_id": run_id}), flush=True)

    try:
        app = Application(repo)
        if args.phase in {"prepare", "all"}:
            processed = []
            for snapshot in repo.snapshots():
                config = repo.one(
                    "SELECT configuration FROM normalized_runs WHERE id=?",
                    (snapshot["active_run"],),
                )
                extractor = app.registry.select(snapshot["site"])
                if (
                    config
                    and json.loads(config["configuration"]).get("extractor_version")
                    == extractor.version
                ):
                    continue
                processed.append(app.process(snapshot["id"]))
            report["processed"] = processed
            print(json.dumps({"processed": len(processed)}), flush=True)
        if args.phase != "prepare":
            app.llm = llm_from_env("fragment")
            if args.phase in {"retrieval", "all"}:
                app.embedder = embedder_from_env()
                report["embedding"] = app.embed()
            report["benchmark"] = run_benchmark(
                app, args.manifest, args.phase, args.strategy, args.resume, checkpoint
            )
        report["raw_unchanged"] = all(
            raw_before[s["id"]]
            == (
                hashlib.sha256(Path(s["raw_path"]).read_bytes()).hexdigest(),
                Path(s["raw_path"]).stat().st_mtime_ns,
            )
            for s in repo.snapshots()
        )
        report["integrity"] = repo.one("PRAGMA integrity_check")
        report["foreign_key_errors"] = repo.rows("PRAGMA foreign_key_check")
        report["status"] = repo.status()
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    k: report[k]
                    for k in ("raw_unchanged", "integrity", "foreign_key_errors", "status")
                }
            ),
            flush=True,
        )
        return 0 if args.phase == "prepare" or report["benchmark"]["status"] == "complete" else 1
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit(main())
