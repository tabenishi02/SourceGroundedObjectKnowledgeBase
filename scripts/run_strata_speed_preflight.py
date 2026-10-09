"""Resumable S01/S02/S03 speed trial on the existing, shared Strata server."""

import argparse
import csv
import json
import os
import statistics
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx
from run_speed_preflight import inputs, response_record, write_atomic

from sgokb.domain import digest, json_text


def request_body(condition):
    # Native LM Studio sends this exact input string too. Schema is in S03's prompt.
    return {
        "model": "qwen3.8-flash-next-iq3_s",
        "messages": [
            {"role": "system", "content": condition["prompt"]},
            {"role": "user", "content": condition["input"]},
        ],
        "temperature": 0,
        "max_tokens": condition["budget"],
        "chat_template_kwargs": {"enable_thinking": False},
    }


def measure(body, elapsed, condition):
    usage = body.get("usage", {})
    choice = body["choices"][0]
    row = response_record(
        {
            "output": [{"type": "message", "content": choice["message"].get("content") or ""}],
            "stats": {
                "input_tokens": usage.get("prompt_tokens"),
                "total_output_tokens": usage.get("completion_tokens"),
                "reasoning_output_tokens": usage.get("completion_tokens_details", {}).get(
                    "reasoning_tokens"
                ),
                "tokens_per_second": body.get("timings", {}).get("predicted_per_second"),
                # Non-streaming prompt_ms is not time to first token.
                "time_to_first_token_seconds": None,
            },
        },
        elapsed,
        condition,
        "template-disable-thinking",
    )
    row["finish_reason"] = choice.get("finish_reason")
    row["timings"] = body.get("timings", {})
    if choice.get("finish_reason") == "length":
        row.update(status="budget_reached", cpc_valid=False if condition["id"] == "S03" else None)
    return row


def summarize(state, baseline, out):
    rows = baseline["trials"] + state["trials"]
    columns = [
        "model_id",
        "model",
        "condition",
        "trial",
        "warmup",
        "final_check",
        "status",
        "tokens_per_second",
        "total_seconds",
        "characters_per_second",
        "output_tokens",
        "input_tokens",
        "reasoning_setting",
        "reasoning_tokens",
        "cpc_valid",
        "error",
    ]
    with (out / "速度比較.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "LLM出力速度の予備試験: 既存8モデルとStrataの比較",
        f"Strata run: {state['run_id']} / 状態: {state['status']}",
        f"既存8モデル run: {baseline['run_id']}（再実行せず保存済み測定を使用）",
        "同一固定入力・Prompt・temperature=0・出力上限・各条件warmup1回+測定3回。",
        "S01:300文字/1024token、S02:2000文字/1024token、S03:CPC抽出/8192token。",
        "LM Studio: Native API/context16384、Strata: 互換API/context65536/IQ3_S。",
        "Strata: enable_thinking=false、projection/engine/キャッシュ条件はruntime.json参照。",
        "S03は両runtimeともPrompt内Schema指定。Strata側response_format検証を追加しない。",
        "API生成tokens/sと総時間・本文文字/秒を併記。推論ありモデルは推論token込み。",
        "StrataのTTFTは未取得。reasoning token内訳がない場合は未取得。",
        "異なるruntime・context・量子化・tokenizerとキャッシュの構成比較。品質順位ではない。",
        "各値はwarmup/終了時確認を除く中央値。S01/S02の予算到達は速度測定として有効。",
        "",
        "モデル | S01 tokens/s | S02 tokens/s | S03 tokens/s | S03文字/秒 | S03総秒 | CPC適合",
    ]
    models = baseline["models"] + [{"id": "L09", "name": "Strata Qwen3.8-Flash-Next IQ3_S"}]
    for model in models:
        selected = [
            r
            for r in rows
            if r["model_id"] == model["id"] and not r["warmup"] and not r.get("final_check")
        ]

        def median(condition, key):
            values = [
                r[key]
                for r in selected
                if r["condition"] == condition
                and r["status"] in {"completed", "budget_reached", "contract_failure"}
                and isinstance(r.get(key), (int, float))
            ]
            return f"{statistics.median(values):.2f}" if values else "未取得"

        s03 = [r for r in selected if r["condition"] == "S03"]
        cells = [model["name"]] + [median(c, "tokens_per_second") for c in ("S01", "S02", "S03")]
        cells += [
            median("S03", "characters_per_second"),
            median("S03", "total_seconds"),
            f"{sum(r.get('cpc_valid') is True for r in s03)}/{len(s03)}",
        ]
        lines.append(" | ".join(cells))
    (out / "速度比較.txt").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def run(args):
    if urlparse(args.base_url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Loopback server required")
    conditions = inputs()
    condition_hash = digest(json_text(conditions))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    if baseline["status"] != "completed" or baseline["input_hash"] != condition_hash:
        raise ValueError("Baseline must be completed with identical input conditions")
    args.out.mkdir(parents=True, exist_ok=True)
    status_path = args.out / "status.json"
    if status_path.exists() and not args.resume:
        raise ValueError("Results exist; use --resume or a new --out")
    state = (
        json.loads(status_path.read_text(encoding="utf-8"))
        if args.resume
        else {
            "run_id": str(uuid.uuid4()),
            "input_hash": condition_hash,
            "trials": [],
            "runner_version": 1,
            "baseline_run": baseline["run_id"],
        }
    )
    if state["input_hash"] != condition_hash or state["baseline_run"] != baseline["run_id"]:
        raise ValueError("Resume conditions changed")
    if state.get("status") == "completed":
        return 0
    state.update(status="running", pid=os.getpid(), error=None)

    def save():
        write_atomic(status_path, state)
        summarize(state, baseline, args.out)

    save()
    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=180) as client:
            response = client.get("/v1/status", timeout=10)
            response.raise_for_status()
            runtime = response.json()
            response = client.get("/metrics", timeout=10)
            response.raise_for_status()
            engine = response.json()["engine"]
            configuration = {"status": runtime, "engine": engine}
            if not runtime["loaded"] or runtime["model"] != "qwen3.8-flash-next-iq3_s":
                raise ValueError("Required Strata model is not loaded")
            runtime_path = args.out / "runtime.json"
            if args.resume and runtime_path.exists():
                previous = json.loads(runtime_path.read_text(encoding="utf-8"))
                if any(
                    previous["engine"].get(k) != engine.get(k)
                    for k in ("model", "context", "engine", "cvec")
                ):
                    raise ValueError("Runtime configuration changed; use a new output directory")
            else:
                write_atomic(runtime_path, configuration)
            write_atomic(args.out / "inputs.json", conditions)
            for condition in conditions:
                for trial in range(4):
                    record_id = f"L09-{condition['id']}-{trial}"
                    if any(r["record_id"] == record_id for r in state["trials"]):
                        continue
                    response = client.get("/v1/status", timeout=10)
                    response.raise_for_status()
                    current = response.json()
                    if current["activity"]["in_flight"]:
                        raise ValueError("Shared server is busy; resume during idle time")
                    if (
                        current["engine"] != runtime["engine"]
                        or current["model"] != runtime["model"]
                    ):
                        raise ValueError("Shared server model or engine changed")
                    state["current"] = record_id
                    save()
                    row = {
                        "record_id": record_id,
                        "model_id": "L09",
                        "model": runtime["model"],
                        "condition": condition["id"],
                        "trial": trial,
                        "warmup": trial == 0,
                        "final_check": False,
                        "condition_variant": "Strata-template-off",
                    }
                    start = time.perf_counter()
                    try:
                        response = client.post("/v1/chat/completions", json=request_body(condition))
                        elapsed = time.perf_counter() - start
                        write_atomic(
                            args.out / f"{record_id}-response.json",
                            {"http_status": response.status_code, "body": response.text},
                        )
                        response.raise_for_status()
                        row.update(measure(response.json(), elapsed, condition))
                    except (httpx.HTTPError, ValueError, KeyError) as exc:
                        row.update(
                            status="api_error",
                            error=type(exc).__name__,
                            total_seconds=time.perf_counter() - start,
                        )
                    state["trials"].append(row)
                    save()
            state["status"] = (
                "failed"
                if any(r["status"] == "api_error" for r in state["trials"])
                else "completed"
            )
            state["current"] = None
    except Exception as exc:
        state.update(status="failed", error=str(exc))
    finally:
        save()
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--out", type=Path, default=Path("sample/strata-speed-preflight"))
    parser.add_argument(
        "--baseline", type=Path, default=Path("sample/speed-preflight-v2/status.json")
    )
    parser.add_argument("--resume", action="store_true")
    raise SystemExit(run(parser.parse_args()))
