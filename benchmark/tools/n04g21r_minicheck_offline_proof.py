from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_REVISION = "b58b9fa69acbd1015ec970fa65dd752413a053d2"
EXPECTED_MODEL_REVISION = "74c8919647e61ed0f71bc177d94f10930f090068"
MODEL_REPOSITORY = "lytang/MiniCheck-RoBERTa-Large"
THRESHOLD = 0.50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--nltk-data", type=Path, required=True)
    parser.add_argument("--g21v-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def git_output(source_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_dir), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def verify_source(source_dir: Path) -> dict[str, Any]:
    revision = git_output(source_dir, "rev-parse", "HEAD")
    if revision != EXPECTED_SOURCE_REVISION:
        raise RuntimeError(
            f"MiniCheck source revision mismatch: {revision} != {EXPECTED_SOURCE_REVISION}"
        )
    status = git_output(source_dir, "status", "--porcelain")
    if status:
        raise RuntimeError("MiniCheck source checkout is not clean")
    return {"revision": revision, "clean": True}


def model_cache_root(cache_dir: Path) -> Path:
    return cache_dir / "models--lytang--MiniCheck-RoBERTa-Large"


def verify_model_cache(cache_dir: Path) -> dict[str, Any]:
    root = model_cache_root(cache_dir)
    ref_path = root / "refs" / "main"
    snapshot_path = root / "snapshots" / EXPECTED_MODEL_REVISION
    if not ref_path.is_file():
        raise RuntimeError(f"missing Hugging Face main ref: {ref_path}")
    resolved = ref_path.read_text(encoding="utf-8").strip()
    if resolved != EXPECTED_MODEL_REVISION:
        raise RuntimeError(
            f"MiniCheck model main ref mismatch: {resolved} != {EXPECTED_MODEL_REVISION}"
        )
    if not snapshot_path.is_dir():
        raise RuntimeError(f"missing pinned model snapshot: {snapshot_path}")
    files = sorted(
        str(path.relative_to(snapshot_path))
        for path in snapshot_path.rglob("*")
        if path.is_file()
    )
    if not files:
        raise RuntimeError("pinned model snapshot contains no files")
    return {
        "repository": MODEL_REPOSITORY,
        "resolved_main_revision": resolved,
        "snapshot_path": str(snapshot_path),
        "snapshot_files": files,
    }


def enable_offline_mode(nltk_data: Path) -> dict[str, str]:
    values = {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "NLTK_DATA": str(nltk_data),
    }
    os.environ.update(values)
    return values


class NetworkBlocked(RuntimeError):
    pass


def install_socket_block() -> dict[str, int]:
    attempts = {"socket_connect": 0, "create_connection": 0}
    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def blocked_connect(self: socket.socket, address: object) -> None:  # noqa: ARG001
        attempts["socket_connect"] += 1
        raise NetworkBlocked(f"network disabled during G-21R proof: {address!r}")

    def blocked_create_connection(*args: object, **kwargs: object) -> socket.socket:
        attempts["create_connection"] += 1
        raise NetworkBlocked("network disabled during G-21R proof")

    socket.socket.connect = blocked_connect  # type: ignore[method-assign]
    socket.create_connection = blocked_create_connection  # type: ignore[assignment]
    attempts["_original_connect_id"] = id(original_connect)
    attempts["_original_create_connection_id"] = id(original_create_connection)
    return attempts


def verify_nltk(nltk_data: Path) -> dict[str, str]:
    if not nltk_data.is_dir():
        raise RuntimeError(f"NLTK_DATA directory is missing: {nltk_data}")
    import nltk

    nltk.data.path[:] = [str(nltk_data)]
    resources = {}
    for name, locator in (
        ("punkt", "tokenizers/punkt"),
        ("punkt_tab", "tokenizers/punkt_tab"),
    ):
        try:
            path = nltk.data.find(locator)
        except LookupError as exc:
            raise RuntimeError(f"missing local NLTK resource: {name}") from exc
        resources[name] = str(path)
    return resources


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    required_negative = [
        item for item in cases if item["required"] and item["expected"] == "UNSUPPORTED"
    ]
    required_positive = [
        item for item in cases if item["required"] and item["expected"] == "SUPPORTED"
    ]
    all_positive = [item for item in cases if item["expected"] == "SUPPORTED"]
    all_negative = [item for item in cases if item["expected"] == "UNSUPPORTED"]
    false_positive_ids = [
        item["case_id"] for item in required_negative if item["verdict"] == "SUPPORTED"
    ]
    positive_ids = [
        item["case_id"] for item in required_positive if item["verdict"] == "SUPPORTED"
    ]
    return {
        "required_negative_false_positive_count": len(false_positive_ids),
        "required_negative_false_positive_ids": false_positive_ids,
        "required_positive_supported_count": len(positive_ids),
        "required_positive_count": len(required_positive),
        "required_positive_supported_ids": positive_ids,
        "positive_recall": sum(item["verdict"] == "SUPPORTED" for item in all_positive)
        / len(all_positive),
        "negative_specificity": sum(
            item["verdict"] == "UNSUPPORTED" for item in all_negative
        )
        / len(all_negative),
    }


def compare_with_g21v(cases: list[dict[str, Any]], g21v: dict[str, Any]) -> dict[str, Any]:
    previous = {item["case_id"]: item for item in g21v["cases"]}
    rows = []
    for item in cases:
        old = previous[item["case_id"]]
        rows.append(
            {
                "case_id": item["case_id"],
                "verdict_equal": item["verdict"] == old["verdict"],
                "probability_delta": item["support_probability"]
                - old["support_probability"],
            }
        )
    return {
        "all_verdicts_equal": all(row["verdict_equal"] for row in rows),
        "max_abs_probability_delta": max(
            abs(row["probability_delta"]) for row in rows
        ),
        "cases": rows,
    }


def main() -> int:
    args = parse_args()
    corpus = load_json(args.corpus)
    if not isinstance(corpus.get("cases"), list) or not corpus["cases"]:
        raise ValueError("benchmark corpus must contain cases")

    source_identity = verify_source(args.source_dir)
    model_identity = verify_model_cache(args.cache_dir)
    offline_env = enable_offline_mode(args.nltk_data)
    network_attempts = install_socket_block()
    nltk_resources = verify_nltk(args.nltk_data)

    sys.path.insert(0, str(args.source_dir))
    import torch
    from minicheck.minicheck import MiniCheck

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for Reference Workstation G-21R proof")

    started = time.perf_counter()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    scorer = MiniCheck(model_name="roberta-large", cache_dir=str(args.cache_dir))
    docs = [item["document"] for item in corpus["cases"]]
    claims = [item["claim"] for item in corpus["cases"]]
    pred_labels, raw_probs, used_chunks, chunk_probs = scorer.score(
        docs=docs, claims=claims
    )
    elapsed = time.perf_counter() - started

    scored = []
    for source, label, probability, chunks, probabilities in zip(
        corpus["cases"], pred_labels, raw_probs, used_chunks, chunk_probs
    ):
        probability_value = float(probability)
        scored.append(
            {
                **source,
                "verdict": "SUPPORTED"
                if probability_value >= THRESHOLD
                else "UNSUPPORTED",
                "model_pred_label": int(label),
                "support_probability": probability_value,
                "used_chunks": list(chunks),
                "support_prob_per_chunk": [float(value) for value in probabilities],
            }
        )

    metrics = summarize(scored)
    gate_pass = (
        metrics["required_negative_false_positive_count"] == 0
        and metrics["required_positive_supported_count"]
        == metrics["required_positive_count"]
        and network_attempts["socket_connect"] == 0
        and network_attempts["create_connection"] == 0
    )

    g21v = load_json(args.g21v_result)
    comparison = compare_with_g21v(scored, g21v)
    report = {
        "task": "N-04G-21R",
        "status": "PASS" if gate_pass else "FAIL",
        "formal_network_policy": "offline/local-files-only",
        "offline_environment": offline_env,
        "network_attempts": {
            "socket_connect": network_attempts["socket_connect"],
            "create_connection": network_attempts["create_connection"],
        },
        "source_identity": source_identity,
        "model_identity": model_identity,
        "nltk_resources": nltk_resources,
        "threshold": THRESHOLD,
        "metrics": metrics,
        "comparison_with_g21v": comparison,
        "cases": scored,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                name: package_version(name)
                for name in (
                    "minicheck",
                    "nltk",
                    "torch",
                    "transformers",
                    "huggingface_hub",
                    "tokenizers",
                    "accelerate",
                )
            },
            "cuda": {
                "device_name": torch.cuda.get_device_name(0),
                "device_capability": list(torch.cuda.get_device_capability(0)),
                "torch_cuda_build": torch.version.cuda,
            },
            "elapsed_seconds": elapsed,
            "peak_vram_mib": torch.cuda.max_memory_allocated(0) / (1024 * 1024),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if gate_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
