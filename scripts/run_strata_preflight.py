"""CPC contract trial against an already running Strata server; no server changes."""

import argparse
import json
import statistics
from pathlib import Path
from urllib.parse import urlparse

import httpx
from run_speed_preflight import inputs, write_atomic

from sgokb.capture import resolve_quotes, validate_capture
from sgokb.domain import digest, json_text
from sgokb.providers import StrataLLM


def validate_result(content, condition):
    raw = content.strip()
    if raw.startswith("```") and raw.endswith("```"):
        raw = "\n".join(raw.splitlines()[1:-1])
    payload = condition["payload"]
    result = resolve_quotes(json.loads(raw), payload["quote_choices"], condition["response_schema"])
    validate_capture(
        result,
        payload["target_evidence_ids"],
        {e["id"]: e for e in payload["evidence"]},
        condition["canonical_schema"],
    )
    return result


def run(base_url, out, trials):
    if urlparse(base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Local loopback server required")
    if (out / "status.json").exists():
        raise ValueError("Results already exist; select a new --out directory")
    out.mkdir(parents=True, exist_ok=True)
    condition = next(c for c in inputs() if c["id"] == "S03")
    write_atomic(out / "input.json", condition)
    report = {
        "status": "running",
        "candidate": "L09",
        "condition": "S03",
        "input_hash": digest(json_text(condition)),
        "trials_requested": trials,
        "records": [],
    }
    write_atomic(out / "status.json", report)
    try:
        with httpx.Client(base_url=base_url.rstrip("/"), timeout=10) as client:
            snapshots = {}
            for path in ("/health", "/v1/models", "/v1/status", "/metrics"):
                response = client.get(path)
                response.raise_for_status()
                body = response.json()
                snapshots[path] = (
                    {k: body.get(k) for k in ("engine", "live", "hardware_static")}
                    if path == "/metrics"
                    else body
                )
            if not snapshots["/health"].get("loaded"):
                raise ValueError("Strata model is not loaded")
            model = snapshots["/v1/models"]["data"][0]["id"]
            if model != "qwen3.8-flash-next-iq3_s":
                raise ValueError("L09 requires qwen3.8-flash-next-iq3_s")
            report["model"] = model
            # Keep runtime configuration, without other clients' request history.
            write_atomic(out / "runtime.json", snapshots)
            provider = StrataLLM(
                base_url.rstrip("/") + "/v1", model, max_tokens=condition["budget"], timeout=180
            )
            provider.configuration["runtime_metadata"] = {
                "runtime": "Strata",
                "runtime_version": snapshots["/v1/status"]["engine"],
                "context_length": snapshots["/v1/status"]["context"]["native"],
                "control_vector": snapshots["/metrics"]["engine"].get("cvec"),
                "quantization": "IQ3_S",
                "model_revision": "unknown",
            }
            for index in range(trials + 1):
                response = client.get("/v1/status")
                response.raise_for_status()
                status = response.json()
                if status.get("activity", {}).get("in_flight", 0):
                    raise ValueError("Shared server is busy; retry at an idle time")
                record = {"trial": index, "warmup": index == 0}
                try:
                    content = provider.complete(
                        condition["prompt"],
                        condition["payload"],
                        schema=condition["response_schema"],
                    )
                    (out / f"output-{index}.txt").write_text(content, encoding="utf-8")
                    result = validate_result(content, condition)
                    write_atomic(out / f"fragments-{index}.json", result)
                    record.update(
                        status="completed", cpc_valid=True, fragments=len(result["fragments"])
                    )
                except (ValueError, httpx.HTTPError) as exc:
                    record.update(status="failed", cpc_valid=False, error=str(exc))
                record["observation"] = provider.last_observation
                report["records"].append(record)
                write_atomic(out / "status.json", report)
            measured = report["records"][1:]
            report["status"] = (
                "completed" if all(r["cpc_valid"] for r in report["records"]) else "failed"
            )
            durations = [
                r["observation"]["duration_seconds"]
                for r in measured
                if "duration_seconds" in r["observation"]
            ]
            report["median_seconds"] = statistics.median(durations) if durations else None
            speeds = [r["observation"].get("engine_tokens_per_second") for r in measured]
            report["median_decode_tokens_per_second"] = (
                statistics.median(speeds)
                if all(isinstance(s, (int, float)) for s in speeds)
                else None
            )
    except Exception as exc:
        report.update(status="failed", error=str(exc))
    finally:
        write_atomic(out / "status.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--out", type=Path, default=Path(".local/strata-preflight"))
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("--trials must be positive")
    raise SystemExit(run(args.base_url, args.out, args.trials))
