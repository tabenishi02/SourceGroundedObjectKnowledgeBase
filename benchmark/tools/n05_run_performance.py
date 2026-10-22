"""Run the frozen N-05 contract with isolated canonical workflows and local Harrier/Qdrant."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import traceback
import urllib.request
from pathlib import Path

from n05_performance_workflow import prepare_fixture, read, run_sample, write

ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(sys.executable)
TARGETS = {
    "standard": dict(
        source_count=10,
        candidate_evidence_count=500,
        package_evidence_count=120,
        knowledge_statement_count=300,
    ),
    "large": dict(
        source_count=40,
        candidate_evidence_count=2000,
        package_evidence_count=350,
        knowledge_statement_count=1200,
    ),
}
CHECKS = {
    "evaluator": [str(PYTHON), "-m", "pytest", "-q", "tests/test_n05_performance_evaluator.py"],
    "full": [str(PYTHON), "-m", "pytest", "-q"],
    "ruff": [str(PYTHON), "-m", "ruff", "check", "."],
    "diff": ["git", "diff", "--check"],
}


def sample_prefix(run_id, sample_id):
    """Bound native Windows Qdrant paths while retaining sample/run isolation."""
    return "n05" + hashlib.sha256(f"{run_id}:{sample_id}".encode()).hexdigest()[:12]


def capture(arguments):
    return subprocess.check_output(arguments, cwd=ROOT, text=True, encoding="utf-8").strip()


def command(arguments, log):
    with log.open("w", encoding="utf-8") as stream:
        return subprocess.run(
            arguments, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT
        ).returncode


def checks(root, phase):
    results = {}
    for name, arguments in CHECKS.items():
        results[name] = {
            "command": arguments,
            "return_code": command(arguments, root / f"{phase}-{name}.log"),
        }
        write(root / f"{phase}.json", results)
    return all(item["return_code"] == 0 for item in results.values())


def canonical_state():
    """Read-only deterministic full-table fingerprints; never copy private row values to logs."""
    result = {}
    for relative in (".local/sgokb.sqlite", ".local/n03/sgokb-n03.sqlite"):
        path = ROOT / relative
        if not path.exists():
            result[relative] = {"exists": False}
            continue
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            connection.execute("BEGIN")
            tables = {}
            names = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            for (name,) in names:
                quoted = '"' + name.replace('"', '""') + '"'
                rows = connection.execute(f"SELECT * FROM {quoted}").fetchall()
                digests = sorted(hashlib.sha256(repr(row).encode()).hexdigest() for row in rows)
                tables[name] = {
                    "count": len(rows),
                    "sha256": hashlib.sha256("\n".join(digests).encode()).hexdigest(),
                }
            result[relative] = {"exists": True, "tables": tables}
        finally:
            connection.close()
    return result


def configure_offline():
    for key, value in {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "SGOKB_MODEL_LOCAL_ONLY": "1",
        "CUDA_VISIBLE_DEVICES": "0",
        "SGOKB_MODEL_CACHE": ".local/models",
        "PYTHONUTF8": "1",
    }.items():
        os.environ[key] = value


def provider():
    from sgokb.retrieval.embedding import default_sentence_transformer_provider

    value = default_sentence_transformer_provider(
        cache_folder=".local/models", local_files_only=True
    )
    # Fixed before measurement: avoid padding the full Object alongside many short Statements.
    value.batch_size = 1
    if value.device != "cuda":
        raise RuntimeError(
            "Accepted Reference Workstation GPU runtime unavailable; no CPU fallback"
        )
    return value


def worker(root, profile, condition, index):
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    fixture = root / "fixture" / profile
    warm = provider() if condition == "warm" else None
    if warm is not None:
        warm.embed_documents(["N05 neutral runtime initialization."])
    import torch

    identity = warm.space if warm is not None else None
    write(
        root / f"{profile}-{condition}-{index:02d}-runtime.json",
        {
            "torch_version": torch.__version__,
            "torch_cuda_build": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
            "gpu_vram_bytes": torch.cuda.get_device_properties(0).total_memory,
            "preloaded_embedding_space": identity,
        },
    )
    indexes = range(1, 21) if condition == "warm" else [index]
    for number in indexes:
        sample_id = f"{profile}-{condition}-{number:02d}"
        sample = root / profile / f"{condition}-{number:02d}"
        prefix = sample_prefix(root.name, sample_id)

        def vector_factory(space, namespace=prefix):
            return QdrantVectorIndexAdapter(
                url="http://localhost:6333",
                grpc_port=6334,
                prefer_grpc=True,
                collection_prefix=namespace,
            )

        result = run_sample(
            fixture, sample, sample_id, provider, vector_factory, warm_provider=warm
        )
        write(
            sample / "runtime.json",
            {
                "qdrant_collection_prefix": prefix,
                "embedding_batch_size": 1,
                "model_preloaded": warm is not None,
                "application_automatic_retries": 0,
            },
        )
        write(root / "progress.json", {"last_sample": sample_id, "status": result["status"]})
    return 0


def environment(root):
    from sgokb.retrieval.embedding import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_REVISION

    script = (
        "$o=Get-CimInstance Win32_OperatingSystem; $c=Get-CimInstance Win32_Processor; "
        "@{os=$o.Caption; build=$o.BuildNumber; cpu=$c.Name; "
        "ram_gib=[math]::Round($o.TotalVisibleMemorySize/1MB,2)} | ConvertTo-Json -Compress"
    )
    import json

    hardware = json.loads(capture(["powershell", "-NoProfile", "-Command", script]))
    with urllib.request.urlopen("http://localhost:6333/", timeout=10) as response:
        qdrant = json.load(response)
    with urllib.request.urlopen("http://localhost:6333/collections", timeout=10) as response:
        collections = json.load(response)
    prefixes = [
        sample_prefix(root.name, f"{profile}-{condition}-{number:02d}")
        for profile in TARGETS
        for condition, count in (("cold", 3), ("warm", 20))
        for number in range(1, count + 1)
    ]
    prefix = "n05 + 12 hex SHA-256(run_id:sample_id); 15 characters per sample"
    if any(
        any(item["name"].startswith(p + "_") for p in prefixes)
        for item in collections["result"]["collections"]
    ):
        raise RuntimeError("Run-specific Qdrant namespace already exists")
    return {
        **hardware,
        "git_head": capture(["git", "rev-parse", "HEAD"]),
        "origin_main": capture(["git", "rev-parse", "origin/main"]),
        "branch": capture(["git", "branch", "--show-current"]),
        "git_status": capture(["git", "status", "--porcelain"]),
        "gpu": capture(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader",
            ]
        ),
        "python": platform.python_version(),
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "embedding_revision": DEFAULT_EMBEDDING_REVISION,
        "embedding_batch_size": 1,
        "qdrant_version": qdrant["version"],
        "qdrant_transport": "gRPC localhost:6334",
        "collection_prefix": prefix,
        "planned_collection_prefixes": prefixes,
        "model_cache_mode": "local-files-only; offline",
        "volume": ROOT.anchor,
        "free_bytes": shutil.disk_usage(ROOT).free,
        "packages": {
            name: importlib.metadata.version(name)
            for name in (
                "torch",
                "transformers",
                "sentence-transformers",
                "qdrant-client",
                "pytest",
                "ruff",
            )
        },
        "cold_policy": "fresh Python process/model per sample; OS disk cache not flushed",
        "warm_policy": "one persistent preloaded model per profile; neutral warmup outside timing",
        "sample_policy": "fixed 3 cold + 20 warm per profile; no retries/replacement",
        "package_build": "default nonsemantic Evidence retrieval; no optional semantic reranking",
        "derived_sync": "real Harrier; new sample-specific Qdrant namespace; incremental only",
    }


def execute(root):
    root.mkdir(parents=True, exist_ok=False)
    write(root / "status.json", {"stage": "mandatory_preflight"})
    if not checks(root, "preflight"):
        write(root / "status.json", {"stage": "BLOCKED_preflight"})
        return 2
    env = environment(root)
    write(root / "environment.json", env)
    if env["git_status"] or env["branch"] != "main" or env["git_head"] != env["origin_main"]:
        raise RuntimeError("Formal start requires clean main == origin/main")
    before = canonical_state()
    write(root / "canonical-before.json", before)
    evidence = read(ROOT / "benchmark/n05-performance-evidence-template-v1.json")
    evidence.update(run_id=root.name, environment=env)
    try:
        for profile, target in TARGETS.items():
            prepare_fixture(root / "fixture" / profile, profile, target)
            for condition, indexes in (("cold", range(1, 4)), ("warm", [1])):
                for index in indexes:
                    write(
                        root / "status.json",
                        {
                            "stage": "measuring",
                            "profile": profile,
                            "condition": condition,
                            "worker_index": index,
                        },
                    )
                    rc = command(
                        [
                            str(PYTHON),
                            str(Path(__file__).resolve()),
                            "--run-root",
                            str(root),
                            "--worker",
                            "--profile",
                            profile,
                            "--condition",
                            condition,
                            "--index",
                            str(index),
                        ],
                        root / f"{profile}-{condition}-{index:02d}-worker.log",
                    )
                    records = [
                        read(p) for p in sorted((root / profile).glob(f"{condition}-*/sample.json"))
                    ]
                    evidence["profiles"][profile][f"{condition}_samples"] = records
                    write(root / "performance-evidence.json", evidence)
                    if rc:
                        raise RuntimeError(f"Worker exited {rc}; no samples replaced")
    except BaseException:
        write(root / "measurement-error.json", {"traceback": traceback.format_exc()})
    finally:
        write(root / "performance-evidence.json", evidence)
        evaluator_rc = command(
            [
                str(PYTHON),
                "benchmark/tools/n05_evaluate_performance.py",
                "--evidence",
                str(root / "performance-evidence.json"),
                "--output",
                str(root / "performance-evaluation.json"),
            ],
            root / "evaluator.log",
        )
        after = canonical_state()
        write(root / "canonical-after.json", after)
        regression = checks(root, "post-run")
        invariant = before == after
        tracked = capture(["git", "status", "--porcelain"]) == env["git_status"]
        same_head = capture(["git", "rev-parse", "HEAD"]) == env["git_head"]
        write(
            root / "safety.json",
            {
                "canonical_unchanged": invariant,
                "tracked_unchanged": tracked,
                "head_unchanged": same_head,
            },
        )
        write(
            root / "status.json",
            {
                "stage": "measurement_and_regressions_finished_awaiting_review"
                if regression and invariant and tracked and same_head
                else "BLOCKED_post_run",
                "evaluator_return_code": evaluator_rc,
                "regression_pass": regression,
            },
        )
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--profile", choices=TARGETS)
    parser.add_argument("--condition", choices=("cold", "warm"))
    parser.add_argument("--index", type=int, default=1)
    args = parser.parse_args()
    os.chdir(ROOT)
    configure_offline()
    root = args.run_root.resolve()
    if not root.is_relative_to(ROOT / ".local" / "n05"):
        raise ValueError("Run root must be beneath .local/n05")
    if args.worker:
        return worker(root, args.profile, args.condition, args.index)
    if root.exists():
        raise FileExistsError("Existing attempt evidence must never be overwritten")
    try:
        return execute(root)
    except BaseException:
        write(root / "runner-error.json", {"traceback": traceback.format_exc()})
        write(root / "status.json", {"stage": "BLOCKED_runner"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
