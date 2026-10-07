"""Detached paired extraction of real captures using frozen before/after source trees."""

import argparse
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BEFORE, AFTER = "94f7e9c", "e95d06e"
RUNTIME_KEYS = ("model", "engine", "context", "kv", "cvec", "spec", "mtp_max", "lookup")


def write(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def accepted(report):
    return (
        report["result"]["status"] == "complete"
        and report["raw_unchanged"]
        and report["integrity"] == "ok"
        and not report["foreign_key_errors"]
    )


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_fingerprint(source):
    return {
        p.name: [checksum(p), p.stat().st_mtime_ns]
        for p in (source, Path(str(source) + "-wal"))
        if p.exists()
    }


def runtime():
    with httpx.Client(base_url="http://127.0.0.1:8080", timeout=10) as client:
        status = client.get("/v1/status")
        status.raise_for_status()
        engine = client.get("/metrics")
        engine.raise_for_status()
        if not status.json()["loaded"] or status.json()["activity"]["in_flight"]:
            raise ValueError("Strata must be loaded and idle; resume later")
        return {k: engine.json()["engine"].get(k) for k in RUNTIME_KEYS}


def prepare(source, out, after_commit=AFTER, reuse_before=None):
    if (out / "plan.json").exists():
        raise ValueError("Existing comparison requires --resume")
    out.mkdir(parents=True, exist_ok=True)
    manifest = read(ROOT / "benchmark/sample-v1.json")
    cases = [c for c in manifest["cases"] if c["task"] == "fragment"]
    frozen = runtime()
    fingerprint = source_fingerprint(source)
    original = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
    original.row_factory = sqlite3.Row
    try:
        for case in cases:
            snapshot = original.execute(
                "SELECT * FROM snapshots WHERE id=?", (case["snapshot_id"],)
            ).fetchone()
            raw = Path(snapshot["raw_path"])
            if checksum(raw) != case["raw_sha256"]:
                raise ValueError("Raw Capture differs from the frozen manifest")
            case["raw_path"], case["raw_mtime_ns"] = str(raw.resolve()), raw.stat().st_mtime_ns
            case["normalized_run"] = snapshot["active_run"]
        old_plan = read(reuse_before / "plan.json") if reuse_before else None
        if old_plan:
            fields = ("id", "snapshot_id", "entity_id", "raw_sha256", "normalized_run")
            if (
                old_plan["before"] != BEFORE
                or old_plan["runtime"] != frozen
                or old_plan["batch_size"] != manifest["fragment_batch_size"]
                or old_plan["output_tokens"] != 8192
                or [[c[k] for k in fields] for c in old_plan["cases"]]
                != [[c[k] for k in fields] for c in cases]
            ):
                raise ValueError("Existing control conditions differ; control reuse refused")
        for name, commit in (("before", BEFORE), ("after", after_commit)):
            destination = out / name
            destination.mkdir(exist_ok=True)
            archive = subprocess.check_output(
                ["git", "archive", "--format=zip", commit, "src"], cwd=ROOT
            )
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                for item in bundle.infolist():
                    resolved = (destination / item.filename).resolve()
                    if destination.resolve() not in resolved.parents:
                        raise ValueError("Archive path escaped comparison directory")
                    bundle.extract(item, destination)
            copy = sqlite3.connect(destination / "captures.sqlite")
            try:
                if name == "before" and reuse_before:
                    prior = sqlite3.connect(
                        (reuse_before / "before/captures.sqlite").resolve().as_uri() + "?mode=ro",
                        uri=True,
                    )
                    try:
                        prior.backup(copy)
                    finally:
                        prior.close()
                    for file in (reuse_before / "before").glob("fragment-*.json"):
                        shutil.copy2(file, destination / file.name)
                else:
                    original.backup(copy)
            finally:
                copy.close()
    finally:
        original.close()
    if source_fingerprint(source) != fingerprint:
        raise ValueError("Source DB changed while making comparison backups")
    plan = {
        "before": BEFORE,
        "after": after_commit,
        "reused_control": str(reuse_before.resolve()) if reuse_before else None,
        "runtime": frozen,
        "cases": cases,
        "source": str(source.resolve()),
        "source_fingerprint": fingerprint,
        "batch_size": manifest["fragment_batch_size"],
        "output_tokens": 8192,
        "conditions": {
            "before": {},
            "after": {
                "transport": "compact-keys-v1",
                "dedup_quotes": True,
                "window_checkpoint": True,
            },
        },
        "semantic_quality": "human_gold_missing",
    }
    write(out / "plan.json", plan)


def fragment_signatures(rows):
    result = {}
    for row in rows:
        metadata = row["metadata"]
        value = {
            k: v for k, v in metadata.items() if k not in {"ai_run", "extraction_job", "context_id"}
        }
        key = json.dumps([row["facet"], row["content"], value], ensure_ascii=False, sort_keys=True)
        result[key] = result.get(key, 0) + 1
    return result


def worker(out, name, case_id):
    # This process imports only the archived version selected by its PYTHONPATH.
    from cpc.application import Application
    from cpc.providers import StrataLLM
    from cpc.repository import Repository

    plan = read(out / "plan.json")
    case = next(c for c in plan["cases"] if c["id"] == case_id)
    directory = out / name
    progress_path = directory / f"{case_id}-progress.json"
    progress = read(progress_path) if progress_path.exists() else {}
    repo = Repository(directory / "captures.sqlite")
    start = time.perf_counter()
    elapsed = progress.get("seconds", 0)
    progress.setdefault(
        "first_ai_rowid", repo.one("SELECT coalesce(max(rowid),0) AS n FROM ai_runs")["n"]
    )
    try:
        if runtime() != plan["runtime"]:
            raise ValueError("Runtime changed; use a new comparison")
        provider = StrataLLM(
            "http://127.0.0.1:8080/v1",
            plan["runtime"]["model"],
            revision="shared-runtime-frozen",
            max_tokens=plan["output_tokens"],
            timeout=600,
        )
        provider.configuration["runtime_metadata"] = plan["runtime"]
        complete = provider.complete

        def checked(prompt, payload, *, schema=None):
            job = repo.one(
                "SELECT id FROM extraction_jobs WHERE snapshot_id=? AND entity_id=? "
                "ORDER BY rowid DESC LIMIT 1",
                (case["snapshot_id"], case["entity_id"]),
            )
            progress.update(job_id=job["id"], seconds=elapsed + time.perf_counter() - start)
            write(progress_path, progress)
            if runtime() != plan["runtime"]:
                raise ValueError("Runtime changed or shared server became busy")
            return complete(prompt, payload, schema=schema)

        provider.complete = checked
        app = Application(repo, provider)
        if repo.snapshot(case["snapshot_id"])["active_run"] != case["normalized_run"]:
            raise ValueError("Normalized Evidence generation changed")
        result = app.capture_fragments(
            case["snapshot_id"],
            case["entity_id"],
            batch_size=plan["batch_size"],
            resume=progress.get("job_id"),
            **plan["conditions"][name],
        )
        ai = repo.rows(
            "SELECT a.status,o.observations FROM ai_runs a "
            "LEFT JOIN ai_observations o ON o.ai_run=a.id WHERE a.rowid>?",
            (progress["first_ai_rowid"],),
        )
        observations = [json.loads(r["observations"] or "{}") for r in ai]
        rows = [
            r
            for r in repo.related_fragments(case["entity_id"])
            if r["metadata"].get("extraction_job") == result["job_id"]
        ]
        write(directory / f"{case_id}-fragments.json", rows)
        report = {
            "case": case_id,
            "variant": name,
            "result": result,
            "seconds": elapsed + time.perf_counter() - start,
            "calls": len(ai),
            "failed_attempts": sum(r["status"] != "success" for r in ai),
            "usage": {
                k: sum(o.get("usage", {}).get(k, 0) for o in observations)
                for k in ("prompt_tokens", "completion_tokens")
            },
            "cached_prompt_tokens": sum(
                o.get("usage", {}).get("prompt_tokens_details", {}).get("cached_tokens", 0)
                for o in observations
            ),
            "raw_unchanged": checksum(Path(case["raw_path"])) == case["raw_sha256"]
            and Path(case["raw_path"]).stat().st_mtime_ns == case["raw_mtime_ns"],
            "integrity": repo.one("PRAGMA integrity_check")["integrity_check"],
            "foreign_key_errors": len(repo.rows("PRAGMA foreign_key_check")),
        }
        write(directory / f"{case_id}-result.json", report)
        progress["seconds"] = report["seconds"]
        write(progress_path, progress)
        return 0 if accepted(report) else 1
    finally:
        repo.close()


def compare(out, plan):
    comparisons = []
    lines = [
        "実Capture 再抽出比較（同一Strata、変更前／変更後）",
        "意味品質gold未付与。完全一致の減少はRecall低下の証明ではない。",
        "Case | 前(秒) | 後(秒) | 短縮率 | Fragment前→後 | 完全一致（重複込み）",
    ]
    for case in plan["cases"]:
        paths = [out / v / f"{case['id']}-result.json" for v in ("before", "after")]
        if not all(p.exists() for p in paths):
            continue
        before, after = [read(p) for p in paths]
        if not all(accepted(r) for r in (before, after)):
            continue
        old, new = [
            fragment_signatures(read(out / v / f"{case['id']}-fragments.json"))
            for v in ("before", "after")
        ]
        common = sum(min(n, new.get(k, 0)) for k, n in old.items())
        record = {
            "case": case["id"],
            "before": before,
            "after": after,
            "exact_common": common,
            "removed_or_changed": sum(old.values()) - common,
            "added_or_changed": sum(new.values()) - common,
            "time_reduction_percent": 100 * (1 - after["seconds"] / before["seconds"]),
        }
        comparisons.append(record)
        lines.append(
            f"{case['id']} | {before['seconds']:.1f} | {after['seconds']:.1f} | "
            f"{record['time_reduction_percent']:.1f}% | "
            f"{sum(old.values())}→{sum(new.values())} | {common}"
        )
        write(
            out / f"{case['id']}-content-diff.json",
            {
                "before_only_or_changed": [json.loads(k) for k in old if k not in new],
                "after_only_or_changed": [json.loads(k) for k in new if k not in old],
                "multiplicity_changes": [
                    {"claim": json.loads(k), "before": n, "after": new[k]}
                    for k, n in old.items()
                    if k in new and n != new[k]
                ],
            },
        )
    write(out / "comparison.json", {"cases": comparisons, "semantic_quality": "human_gold_missing"})
    (out / "comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args):
    out = args.out.resolve()
    if not args.resume:
        prepare(args.source, out, args.after_commit, args.reuse_before)
    plan = read(out / "plan.json")
    if args.prepare_only:
        return 0
    status = {"status": "running", "pid": os.getpid(), "completed": [], "current": None}
    try:
        for index, case in enumerate(plan["cases"]):
            # Alternate order and record cache usage; retain the shared server's cache.
            for name in ("before", "after") if index % 2 == 0 else ("after", "before"):
                result_path = out / name / f"{case['id']}-result.json"
                if result_path.exists() and accepted(read(result_path)):
                    status["completed"].append(f"{name}/{case['id']}")
                    continue
                status["current"] = f"{name}/{case['id']}"
                write(out / "status.json", status)
                env = {
                    **os.environ,
                    "PYTHONPATH": str(out / name / "src"),
                    "PYTHONIOENCODING": "utf-8",
                }
                with (out / "worker.log").open("a", encoding="utf-8") as log:
                    process = subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--out",
                            str(out),
                            "--worker",
                            name,
                            "--case",
                            case["id"],
                        ],
                        cwd=ROOT,
                        env=env,
                        stdout=log,
                        stderr=log,
                    )
                if process.returncode:
                    raise ValueError(
                        f"Worker failed: {status['current']}; inspect worker.log and resume"
                    )
                status["completed"].append(status["current"])
            compare(out, plan)
        status.update(
            status="completed",
            current=None,
            source_db_unchanged=source_fingerprint(Path(plan["source"]))
            == plan["source_fingerprint"],
        )
        if not status["source_db_unchanged"]:
            raise ValueError("Original source DB changed during comparison")
    except Exception as exc:
        status.update(status="failed", error=str(exc))
    finally:
        write(out / "status.json", status)
    return 0 if status["status"] == "completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(".local/upgrade.sqlite"))
    parser.add_argument("--out", type=Path, default=Path("sample/efficiency-capture-comparison"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--worker", choices=["before", "after"])
    parser.add_argument("--case")
    parser.add_argument("--after-commit", default=AFTER)
    parser.add_argument("--reuse-before", type=Path)
    args = parser.parse_args()
    raise SystemExit(
        worker(args.out.resolve(), args.worker, args.case) if args.worker else run(args)
    )
