"""Detached, resumable local speed measurements; never writes the CPC database."""

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import time
import uuid
from copy import deepcopy
from pathlib import Path

import httpx

from cpc.capture import quote_choices, resolve_quotes, validate_capture
from cpc.domain import digest, json_text

MODELS = [
    ("L01", "qwen/qwen3.8-27b", "Qwen3.8-27B", "Qwen3.8-27B-Q4_K_M.gguf"),
    ("L02", "openai/gpt-oss-20b", "GPT-OSS 20B", "gpt-oss-20b-MXFP4.gguf"),
    (
        "L03",
        "google/gemma-4-26b-a4b-qat",
        "Gemma 4 26B-A4B QAT",
        "gemma-4-26B-A4B-it-QAT-Q4_0.gguf",
    ),
    (
        "L04",
        "mistralai/mistral-small-3.2",
        "Mistral Small 3.2 24B",
        "Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf",
    ),
    (
        "L05",
        "mistralai/ministral-3-14b-reasoning",
        "Ministral 3 14B Reasoning",
        "Ministral-3-14B-Reasoning-2512-Q4_K_M.gguf",
    ),
    (
        "L06",
        "nvidia/nemotron-3-nano",
        "Nemotron 3 Nano 30B A3B",
        "NVIDIA-Nemotron-3-Nano-30B-A3B-Q3_K_L.gguf",
    ),
    ("L07", "meta/muse-glimmer", "Muse Glimmer", "Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf"),
    ("L08", "google/gemma-4-31b-qat", "Gemma 4 31B QAT", "gemma-4-31B-it-QAT-Q4_0.gguf"),
]


def inputs():
    sentence = (
        "架空の資料館は午前九時に開館する。入口には青い案内板がある。"
        "展示室は三つあり、第一展示室では古い時計を展示する。水曜日は休館する。"
    )
    source = (
        "架空太郎は資料館の案内係である。年齢は十七歳である。青い制服を着ている。"
        "毎朝九時に入口で来館者を迎える。古い時計の手入れが得意である。"
        "水曜日は資料館の休館日である。"
    )
    # Frozen synthetic text; no real captures or user data.
    evidence = [
        {
            "id": "speed-evidence-01",
            "content": (source * 10)[:480],
            "metadata": {"kinds": ["paragraph"]},
        }
    ]
    allowed = {e["id"]: e for e in evidence}
    schema = json.loads(Path("src/cpc/prompts/high_recall.schema.json").read_text(encoding="utf-8"))
    response_schema = deepcopy(schema)
    assessment = response_schema["properties"]["assessments"]
    assessment.update(minItems=1, maxItems=1)
    assessment["items"]["properties"]["evidence_id"]["enum"] = list(allowed)
    choices = quote_choices(allowed)
    fragment = response_schema["properties"]["fragments"]["items"]
    del fragment["properties"]["original_text"]
    fragment["required"].remove("original_text")
    fragment["required"].append("quote_id")
    fragment["properties"]["quote_id"] = {"type": "string", "enum": list(choices)}
    fragment["properties"]["evidence_ids"]["items"]["enum"] = list(allowed)
    payload = {
        "entity": {"name": "架空太郎", "type": "Character"},
        "page_context": {
            "source_type": "generic",
            "publisher_type": "unknown",
            "page_purpose": "character_profile",
        },
        "captured_at": "2026-01-01T00:00:00Z",
        "evidence": evidence,
        "target_evidence_ids": list(allowed),
        "neighbors": [],
        "mode": "single_pass",
        "focus": "all",
        "quote_choices": choices,
    }
    prompt = Path("src/cpc/prompts/high_recall.md").read_text(encoding="utf-8")
    prompt += "\nResponse JSON Schema (CPC instruction):\n" + json_text(response_schema)
    common = (
        "日本語で資料に基づく詳しい説明を番号付きで続けてください。"
        "各項目に資料中の具体的な情報を含め、合計四十項目以上を目指してください。"
        "資料にない事実は作らないでください。"
    )
    return [
        {"id": "S01", "prompt": common, "input": (sentence * 6)[:300], "budget": 1024},
        {"id": "S02", "prompt": common, "input": (sentence * 40)[:2000], "budget": 1024},
        {
            "id": "S03",
            "prompt": prompt,
            "input": json_text(payload),
            "budget": 8192,
            "payload": payload,
            "response_schema": response_schema,
            "canonical_schema": schema,
        },
    ]


def response_record(body, elapsed, condition):
    stats = body.get("stats", {})
    output = body.get("output", [])
    content = "\n".join(item.get("content", "") for item in output if item.get("type") == "message")
    tokens = stats.get("total_output_tokens")
    budget = tokens is not None and tokens >= condition["budget"]
    state = "budget_reached" if budget else "completed"
    validity = None
    error = None
    if not content.strip():
        state, error = "empty_response", "No message content"
    elif any(item.get("type") not in {"message", "reasoning"} for item in output):
        state, error = "unexpected_output", "Non-message output"
    elif condition["id"] == "S03":
        validity = False
        if not budget:
            try:
                raw = content.strip()
                if raw.startswith("```") and raw.endswith("```"):
                    raw = "\n".join(raw.splitlines()[1:-1])
                payload = condition["payload"]
                parsed = resolve_quotes(
                    json.loads(raw), payload["quote_choices"], condition["response_schema"]
                )
                validate_capture(
                    parsed,
                    payload["target_evidence_ids"],
                    {e["id"]: e for e in payload["evidence"]},
                    condition["canonical_schema"],
                )
                validity = True
            except (ValueError, KeyError) as exc:
                state, error = "contract_failure", str(exc)
    reasoning = stats.get("reasoning_output_tokens")
    if reasoning is not None and reasoning > 0:
        state, error = "reasoning_mismatch", "Reasoning tokens generated with reasoning off"
    return {
        "status": state,
        "error": error,
        "total_seconds": elapsed,
        "tokens_per_second": stats.get("tokens_per_second"),
        "ttft_seconds": stats.get("time_to_first_token_seconds"),
        "output_tokens": tokens,
        "input_tokens": stats.get("input_tokens"),
        "reasoning_tokens": reasoning,
        "characters": len(content),
        "characters_per_second": len(content) / elapsed if elapsed else None,
        "end_to_end_tokens_per_second": tokens / elapsed
        if tokens is not None and elapsed
        else None,
        "cpc_valid": validity,
    }


def write_atomic(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def summarize(state, output):
    rows = state["trials"]
    columns = [
        "model_id",
        "model",
        "condition",
        "trial",
        "warmup",
        "final_check",
        "status",
        "tokens_per_second",
        "ttft_seconds",
        "total_seconds",
        "output_tokens",
        "input_tokens",
        "reasoning_tokens",
        "characters",
        "characters_per_second",
        "cpc_valid",
        "error",
    ]
    with (output / "速度比較.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "LLM出力速度の予備試験",
        f"run: {state['run_id']} / 状態: {state['status']}",
        "速度と品質は別評価。予算到達は回答完了を意味しません。",
        "生成tokens/sはAPIの値。TTFTはエンジン側。総時間はclient計測。",
        "条件: context16384 / temperature0 / reasoning off / sequential",
        "GPU offload、CPU配置、cache、runtime version、ピーク使用量が不明な場合はunknown。",
        "未取得値は推測しません。異なるtokenizer/量子化による構成差を含みます。",
        "Ministralは保存済みのReasoning版を使用し、通常版とは区別します。",
        "",
    ]
    for model in state["models"]:
        lines.append(
            f"{model['id']} {model['name']} / {model['status']} / "
            f"{model.get('quantization', 'unknown')}"
        )
        if model.get("error"):
            lines.append("  理由: " + model["error"])
        for condition in ("S01", "S02", "S03"):
            selected = [
                r
                for r in rows
                if r["model_id"] == model["id"]
                and r["condition"] == condition
                and not r["warmup"]
                and not r.get("final_check")
            ]
            valid = [
                r
                for r in selected
                if r["status"] in {"completed", "budget_reached", "contract_failure"}
            ]

            def value(key):
                values = [r[key] for r in valid if isinstance(r.get(key), (int, float))]
                return (
                    f"{statistics.median(values):.2f} [{min(values):.2f}〜{max(values):.2f}]"
                    if values
                    else "未測定"
                )

            lines.append(
                f"  {condition}: 測定{len(selected)}/3、"
                f"生成tokens/s {value('tokens_per_second')}、TTFT秒 {value('ttft_seconds')}、"
                f"総時間秒 {value('total_seconds')}、文字/秒 {value('characters_per_second')}"
            )
            lines.append(
                "    状態: "
                + ", ".join(r["status"] for r in selected)
                + (
                    f" / CPC適合 {sum(r.get('cpc_valid') is True for r in selected)}"
                    f"/{len(selected)}"
                    if condition == "S03"
                    else ""
                )
            )
        lines.append("")
    lines += [
        "中央値[最小〜最大]。ウォームアップ・最後のQwen確認はCSVで別表示。",
        "3回は予備測定。速度順位だけで本試験の品質順位を決めません。",
        "生応答・設定・statsは同じフォルダ内。CPCの既存DBは変更していません。",
    ]
    baseline = [
        r
        for r in rows
        if r["model_id"] == "L01"
        and r["condition"] == "S03"
        and not r["warmup"]
        and not r.get("final_check")
        and r.get("cpc_valid") is True
        and r.get("tokens_per_second")
        and r.get("output_tokens")
        and r.get("ttft_seconds") is not None
    ]
    if baseline:
        tokens = statistics.median(r["output_tokens"] for r in baseline)
        base_time = statistics.median(
            r["ttft_seconds"] for r in baseline
        ) + tokens / statistics.median(r["tokens_per_second"] for r in baseline)
        lines += [
            "",
            "本試験8Captureの時間概算（Qwen実測5.11時間を基準。品質・出力量・再試行差は未反映）:",
        ]
        for model in state["models"]:
            measured = [
                r
                for r in rows
                if r["model_id"] == model["id"]
                and r["condition"] == "S03"
                and not r["warmup"]
                and not r.get("final_check")
                and r.get("cpc_valid") is True
                and r.get("tokens_per_second")
                and r.get("ttft_seconds") is not None
            ]
            if not measured:
                lines.append(model["name"] + ": CPC適合測定が不足、推定不可")
                continue
            estimate = (
                5.11
                * (
                    statistics.median(r["ttft_seconds"] for r in measured)
                    + tokens / statistics.median(r["tokens_per_second"] for r in measured)
                )
                / base_time
            )
            lines.append(
                f"{model['name']}: 約{estimate:.1f}時間（有効{len(measured)}/3回、"
                "単発測定からの概算）"
            )
    (output / "速度比較.txt").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("sample/モデル比較/予備速度試験"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    status_path = output / "status.json"
    if status_path.exists() and not args.resume:
        raise ValueError("Output already exists; use --resume or a new --out")
    state = (
        json.loads(status_path.read_text(encoding="utf-8"))
        if args.resume
        else {
            "run_id": str(uuid.uuid4()),
            "models": [
                {"id": mid, "key": key, "name": name, "filename": filename, "status": "pending"}
                for mid, key, name, filename in MODELS
            ],
            "trials": [],
        }
    )
    if state.get("status") == "completed":
        return
    state.update(pid=os.getpid(), status="running")
    lms = str(Path.home() / ".lmstudio/bin/lms.exe")
    conditions = inputs()
    condition_hash = digest(json_text(conditions))
    if state.get("input_hash", condition_hash) != condition_hash:
        raise ValueError("Resume input conditions changed")
    state["input_hash"] = condition_hash
    state["environment"] = {
        "runtime_version": None,
        "gpu_offload": "auto/unknown",
        "cache": "unknown",
        "peak_vram": None,
        "peak_ram": None,
    }
    write_atomic(output / "inputs.json", conditions)

    def cli(*arguments, timeout=30):
        return subprocess.run(
            [lms, *arguments],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=True,
        ).stdout

    def save():
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_atomic(status_path, state)
        summarize(state, output)

    def measure(model, identifier, condition, trial, final=False):
        name = f"{model['id']}-{condition['id']}-{'final' if final else trial}"
        existing = next((r for r in state["trials"] if r["record_id"] == name), None)
        if existing:
            return existing["status"]
        row = {
            "record_id": name,
            "model_id": model["id"],
            "model": model["key"],
            "condition": condition["id"],
            "trial": trial,
            "warmup": trial == 0 and not final,
            "final_check": final,
        }
        state["current"] = name
        save()
        start = time.perf_counter()
        try:
            active = json.loads(cli("ps", "--json"))
            if any(m.get("identifier") != identifier for m in active):
                raise RuntimeError(
                    "Other model loaded during speed test; stopping without unloading it"
                )
            with httpx.Client(timeout=180) as client:
                start = time.perf_counter()
                response = client.post(
                    "http://127.0.0.1:1234/api/v1/chat",
                    json={
                        "model": identifier,
                        "system_prompt": condition["prompt"],
                        "input": condition["input"],
                        "temperature": 0,
                        "reasoning": "off",
                        "max_output_tokens": condition["budget"],
                        "store": False,
                        "integrations": [],
                    },
                )
                elapsed = time.perf_counter() - start
                raw = {"http_status": response.status_code, "body": response.text}
                write_atomic(output / (name + "-response.json"), raw)
                response.raise_for_status()
                row.update(response_record(response.json(), elapsed, condition))
        except httpx.TimeoutException:
            row.update(
                status="timeout",
                total_seconds=time.perf_counter() - start,
                error="180 second HTTP timeout",
            )
        except httpx.HTTPError as error:
            row.update(
                status="api_error",
                total_seconds=time.perf_counter() - start,
                error=type(error).__name__,
            )
        except ValueError as error:
            row.update(
                status="api_error",
                total_seconds=time.perf_counter() - start,
                error=type(error).__name__,
            )
        state["trials"].append(row)
        save()
        return row["status"]

    identifier = None
    try:
        save()
        active = json.loads(cli("ps", "--json"))
        if active:
            raise RuntimeError("Models already loaded; do not interfere with another session")
        inventory = json.loads(cli("ls", "--json"))
        write_atomic(output / "inventory.json", inventory)
        settings = json.loads((Path.home() / ".lmstudio/settings.json").read_text(encoding="utf-8"))
        folder = Path(settings["downloadsFolder"])
        for model in state["models"]:
            if model["status"] in {"completed", "not_available", "load_failed"}:
                continue
            available = next((m for m in inventory if m["modelKey"] == model["key"]), None)
            if not available:
                model.update(
                    status="not_available", error="Requested model not found in local inventory"
                )
                save()
                continue
            model["quantization"] = available.get("quantization", {}).get("name", "unknown")
            paths = list(folder.rglob(model["filename"]))
            if len(paths) == 1:
                state["current"] = model["id"] + " hash"
                save()
                h = hashlib.sha256()
                with paths[0].open("rb") as file:
                    for chunk in iter(lambda: file.read(8 * 1024 * 1024), b""):
                        h.update(chunk)
                model["sha256"] = h.hexdigest()
            model["revision"] = None
            model["status"] = "loading"
            state["current"] = model["id"] + " load"
            save()
            identifier = f"cpc-speed-{state['run_id'][:8]}-{model['id']}"
            start = time.perf_counter()
            try:
                log = cli(
                    "load",
                    model["key"],
                    "--identifier",
                    identifier,
                    "--context-length",
                    "16384",
                    "--ttl",
                    "600",
                    "-y",
                    timeout=600,
                )
                (output / (model["id"] + "-load.txt")).write_text(log, encoding="utf-8")
                model["load_seconds"] = time.perf_counter() - start
            except (subprocess.SubprocessError, OSError) as error:
                model.update(status="load_failed", error=type(error).__name__)
                (output / (model["id"] + "-load-error.txt")).write_text(
                    str(getattr(error, "stderr", None) or error), encoding="utf-8"
                )
                save()
                # A load timeout may leave the engine loading; do not start another model.
                if isinstance(error, subprocess.TimeoutExpired):
                    raise
                if any(m.get("identifier") == identifier for m in json.loads(cli("ps", "--json"))):
                    cli("unload", identifier)
                identifier = None
                continue
            model["status"] = "measuring"
            save()
            for condition in conditions:
                failures = 0
                for trial in range(4):
                    result = measure(model, identifier, condition, trial)
                    if result in {"timeout", "api_error"}:
                        failures += 1
                    elif result is not None:
                        failures = 0
                    if failures >= 2:
                        break
            cli("unload", identifier)
            identifier = None
            model["status"] = "completed"
            save()
        # End-of-run Qwen check is separate from the three-trial summaries.
        qwen = state["models"][0]
        if qwen["status"] == "completed":
            identifier = f"cpc-speed-{state['run_id'][:8]}-check"
            cli(
                "load",
                qwen["key"],
                "--identifier",
                identifier,
                "--context-length",
                "16384",
                "--ttl",
                "600",
                "-y",
                timeout=600,
            )
            for condition in conditions:
                measure(qwen, identifier, condition, 1, final=True)
            cli("unload", identifier)
            identifier = None
        state["status"] = "completed"
        state["current"] = None
        save()
    except Exception as error:
        state.update(status="failed", error=str(error))
        save()
        raise
    finally:
        if identifier:
            try:
                cli("unload", identifier)
            except (subprocess.SubprocessError, OSError):
                pass


if __name__ == "__main__":
    main()
