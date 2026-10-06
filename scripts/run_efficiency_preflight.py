"""Detached, resumable real-provider comparison using frozen synthetic CPC material."""

import argparse
import json
import os
import sqlite3
import statistics
import time
from pathlib import Path

import httpx
from run_speed_preflight import inputs, write_atomic

from cpc.application import Application
from cpc.capture import HighRecallCapture
from cpc.domain import digest, json_text
from cpc.providers import StrataLLM
from cpc.repository import Repository

VARIANTS = [
    ("canonical", "canonical", False),
    ("quote-dedup", "canonical", True),
    ("compact", "compact-keys-v1", False),
    ("compact-dedup", "compact-keys-v1", True),
]


def summarize(out):
    state = json.loads((out / "status.json").read_text(encoding="utf-8"))
    if state["status"] != "completed" or len(state["records"]) != 16:
        raise ValueError("Comparison requires all 16 completed trials")
    db = sqlite3.connect(f"file:{(out / 'ledger.sqlite').as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    previous, trials = 0, []
    try:
        # Include every retry, not only the final successful response's observation.
        for record in state["records"]:
            last = db.execute(
                "SELECT rowid FROM ai_runs WHERE id=?", (record["ai_run"],)
            ).fetchone()[0]
            runs = db.execute(
                "SELECT a.output,a.status,o.observations FROM ai_runs a "
                "LEFT JOIN ai_observations o ON o.ai_run=a.id WHERE a.rowid>? AND a.rowid<=?",
                (previous, last),
            ).fetchall()
            previous = last
            observations = [json.loads(r["observations"] or "{}") for r in runs]
            trials.append(
                {
                    **record,
                    "calls": len(runs),
                    "failed_attempts": sum(r["status"] != "success" for r in runs),
                    "prompt_tokens": sum(
                        o.get("usage", {}).get("prompt_tokens", 0) for o in observations
                    ),
                    "completion_tokens": sum(
                        o.get("usage", {}).get("completion_tokens", 0) for o in observations
                    ),
                    "output_chars": sum(len(r["output"] or "") for r in runs),
                }
            )
    finally:
        db.close()
    results = []
    for name, _, _ in VARIANTS:
        measured = [r for r in trials if r["variant"] == name and not r["warmup"]]
        results.append(
            {
                "variant": name,
                **{
                    key: statistics.median(r[key] for r in measured)
                    for key in (
                        "total_seconds",
                        "prompt_tokens",
                        "completion_tokens",
                        "output_chars",
                    )
                },
                "seconds_range": [
                    min(r["total_seconds"] for r in measured),
                    max(r["total_seconds"] for r in measured),
                ],
                "calls": sum(r["calls"] for r in measured),
                "failed_attempts": sum(r["failed_attempts"] for r in measured),
                "valid_trials": sum(r["cpc_valid"] for r in measured),
            }
        )
    baseline = results[0]["total_seconds"]
    for result in results:
        result["time_reduction_percent"] = 100 * (1 - result["total_seconds"] / baseline)
    write_atomic(
        out / "comparison.json", {"runtime": state["runtime"], "results": results, "trials": trials}
    )
    lines = [
        "Knowledge Pipeline 効率化 比較試験",
        "固定合成資料 S03 / 同一 Strata runtime / 各条件 warmup 1回 + 本測定3回",
        "ウォームキャッシュ条件。品質gold未付与。実Captureの時間・品質を保証しない。",
        "秒数はCPC検証を含む総時間中央値。tokenは再試行を含むAPI使用量中央値。",
        "条件 | 総時間(秒) | 短縮率 | 入力token | 出力token | 本測定呼出数 | 失敗試行",
    ]
    for r in results:
        lines.append(
            f"{r['variant']} | {r['total_seconds']:.2f} | {r['time_reduction_percent']:.1f}% | "
            f"{r['prompt_tokens']:g} | {r['completion_tokens']:g} | "
            f"{r['calls']} | {r['failed_attempts']}"
        )
    lines.extend(
        [
            "",
            "全16回で引用・Schema検証成功、各6 Fragment。SQLite整合性正常。",
            f"Compact+引用重複削減の短縮: {results[-1]['time_reduction_percent']:.1f}%。"
            "計画目標20%の達否はこの実測値で判断する。",
        ]
    )
    (out / "comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results


def run(out, resume=False):
    out.mkdir(parents=True, exist_ok=True)
    path = out / "status.json"
    if path.exists() and not resume:
        raise ValueError("Choose a new output directory or --resume")
    condition = next(c for c in inputs() if c["id"] == "S03")
    frozen_hash = digest(json_text([condition, VARIANTS]))
    state = (
        json.loads(path.read_text(encoding="utf-8"))
        if resume
        else {
            "input_hash": frozen_hash,
            "records": [],
            "semantic_quality": "human_gold_missing",
        }
    )
    if state["input_hash"] != frozen_hash:
        raise ValueError("Resume input changed")
    if state.get("status") == "completed":
        return 0
    state.update(status="running", pid=os.getpid(), error=None)
    write_atomic(path, state)
    repo = Repository(out / "ledger.sqlite")
    try:
        with httpx.Client(base_url="http://127.0.0.1:8080", timeout=10) as client:
            response = client.get("/v1/status")
            response.raise_for_status()
            runtime = response.json()
            response = client.get("/metrics")
            response.raise_for_status()
            engine = response.json()["engine"]
            if not runtime["loaded"] or runtime["model"] != "qwen3.8-flash-next-iq3_s":
                raise ValueError("Required Strata model is not loaded")
            configuration = {
                k: engine.get(k)
                for k in (
                    "model",
                    "engine",
                    "context",
                    "cvec",
                    "spec",
                    "mtp_max",
                    "lookup",
                )
            }
            if resume and state.get("runtime") != configuration:
                raise ValueError("Runtime changed; use a new output directory")
            state["runtime"] = configuration
            write_atomic(out / "inputs.json", condition)
            provider = StrataLLM("http://127.0.0.1:8080/v1", runtime["model"], max_tokens=8192)
            provider.configuration["runtime_metadata"] = configuration
            app = Application(repo, provider)
            for name, transport, dedup in VARIANTS:
                for trial in range(4):
                    record_id = f"{name}-{trial}"
                    if any(r["id"] == record_id for r in state["records"]):
                        continue
                    response = client.get("/v1/status")
                    response.raise_for_status()
                    if response.json()["activity"]["in_flight"]:
                        raise ValueError("Shared server is busy; resume when idle")
                    state["current"] = record_id
                    write_atomic(path, state)
                    capture = HighRecallCapture(app)
                    capture.transport, capture.dedup_quotes = transport, dedup
                    payload = condition["payload"]
                    record = {
                        "id": record_id,
                        "variant": name,
                        "warmup": trial == 0,
                        "transport": transport,
                        "dedup_quotes": dedup,
                    }
                    start = time.perf_counter()
                    try:
                        result, _, ai_id = capture.extract_window(
                            payload,
                            {e["id"]: e for e in payload["evidence"]},
                            condition["canonical_schema"],
                            "single_pass",
                            6000,
                        )
                        write_atomic(out / f"{record_id}-fragments.json", result)
                        record.update(
                            status="completed",
                            fragments=len(result["fragments"]),
                            ai_run=ai_id,
                            cpc_valid=True,
                        )
                    except Exception as exc:
                        record.update(status="failed", cpc_valid=False, error=str(exc))
                    record.update(
                        total_seconds=time.perf_counter() - start,
                        observation=provider.last_observation,
                    )
                    state["records"].append(record)
                    write_atomic(path, state)
            state["status"] = (
                "completed" if all(r["cpc_valid"] for r in state["records"]) else "failed"
            )
            state["current"] = None
            state["integrity"] = repo.one("PRAGMA integrity_check")["integrity_check"]
            state["foreign_key_errors"] = len(repo.rows("PRAGMA foreign_key_check"))
    except Exception as exc:
        state.update(status="failed", error=str(exc))
    finally:
        write_atomic(path, state)
        repo.close()
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("sample/efficiency-preflight"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    if args.summarize:
        print(json.dumps(summarize(args.out), ensure_ascii=False, indent=2))
        raise SystemExit(0)
    raise SystemExit(run(args.out, args.resume))
