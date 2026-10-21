"""Read-only three-repeat selection of all locked development classifiers.

There is no final-confirmation path or threshold-fitting command in this runner.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

from n04g25a_development_metrics import model_inputs, predict_labels
from n04g25a_select_development import evaluate, select
from n04g25a_train_development import (
    MANIFEST,
    ROOT,
    read,
    seed_everything,
    sha,
    transformer_load,
    transformer_predict,
    write,
)

FREEZE = ROOT / "benchmark/n04g25a-development-policy-lock-v1.json"


def verify_freeze(frozen, manifest, root=ROOT, artifacts=True):
    if frozen["status"] != "all_checkpoint_policies_locked_before_selection":
        raise ValueError("Every checkpoint/policy must be frozen before selection")
    if (
        not frozen["standard_venv_unchanged"]
        or frozen["selection_started"]
        or frozen["confirmation_started"]
    ):
        raise ValueError("Invalid pre-selection boundary")
    expected = {(c["candidate_id"], t) for c in manifest["candidates"] for t in manifest["tasks"]}
    actual = [(j["candidate_id"], j["task"]) for j in frozen["locks"]]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Complete unique locks required for the frozen candidate pool")
    for lock in frozen["locks"]:
        candidate = next(
            c for c in manifest["candidates"] if c["candidate_id"] == lock["candidate_id"]
        )
        classes = (
            list(manifest["class_definitions"][lock["task"]])
            if candidate["family"] == "cross_encoder_zero_shot"
            else manifest["tasks"][lock["task"]]["supervised_classes"]
        )
        if (
            lock["classes"] != classes
            or lock["fit_partition"] != "validation"
            or lock["status"] != "checkpoint_policy_locked"
        ):
            raise ValueError("Class map/policy provenance mismatch")
        if (
            lock["policy"]["min_confidence"] not in manifest["abstention"]["min_confidence_grid"]
            or lock["policy"]["min_margin"] not in manifest["abstention"]["min_margin_grid"]
        ):
            raise ValueError("Undeclared abstention policy")
        if lock["selection_started"] or lock["confirmation_started"]:
            raise ValueError("Training lock crossed selection/confirmation boundary")
        if not lock["artifacts"]:
            raise ValueError("Checkpoint artifact hashes required")
        if artifacts:
            path = root / lock["raw_lock_path"]
            if sha(path) != lock["raw_lock_sha256"]:
                raise ValueError("Raw training lock changed")
            raw = read(path)
            if any(lock.get(k) != value for k, value in raw.items()):
                raise ValueError("Committed policy differs from raw validation-only lock")
            checkpoint = (root / lock["checkpoint"]).resolve()
            work_area = (root / ".local/n04-v4/g25a").resolve()
            runtime_area = (root / ".local/n04-v4/g25a/runtime").resolve()
            if not (
                checkpoint.is_relative_to(work_area) or checkpoint.is_relative_to(runtime_area)
            ):
                raise ValueError("Checkpoint is outside isolated runtime")
            for name, expected_artifact in lock["artifacts"].items():
                path = checkpoint / name
                if (
                    path.stat().st_size != expected_artifact["bytes"]
                    or sha(path) != expected_artifact["sha256"]
                ):
                    raise ValueError("Checkpoint artifact changed")
    return True


def verify_inputs():
    frozen, manifest = read(FREEZE), read(MANIFEST)
    if sha(MANIFEST) != frozen["candidate_manifest_sha256"]:
        raise ValueError("Candidate manifest changed after policy freeze")
    inputs = frozen["training_input_lock"]
    for name, digest in inputs["development_files"].items():
        if sha(ROOT / "benchmark" / name) != digest:
            raise ValueError("Development corpus/manifest changed")
    if sha(ROOT / "benchmark/n04g25a-split-manifest-v1.json") != inputs["split_manifest_sha256"]:
        raise ValueError("Development split changed")
    if (
        sha(Path(__file__).with_name("n04g25a_train_development.py")) != inputs["runner_sha256"]
        or sha(Path(__file__).with_name("n04g25a_development_metrics.py"))
        != inputs["metrics_sha256"]
    ):
        raise ValueError("Training/metrics implementation changed")
    verify_freeze(frozen, manifest)
    return frozen, manifest


def selection_rows(task):
    if task not in {"atomicity", "content_type"}:
        raise ValueError("Only declared development tasks permitted")
    suffix = task.replace("_", "-")
    path = ROOT / f"benchmark/n04g25a-{suffix}-development-v1.jsonl"
    return [
        r
        for line in path.read_text(encoding="utf-8").splitlines()
        if (r := json.loads(line))["split"] == "selection"
    ]


def child(candidate_id, task, output):
    import torch

    frozen, manifest = verify_inputs()
    candidate = next(c for c in manifest["candidates"] if c["candidate_id"] == candidate_id)
    lock = next(
        j for j in frozen["locks"] if j["candidate_id"] == candidate_id and j["task"] == task
    )
    seed_everything(manifest["seed"])
    torch.cuda.init()
    torch.cuda.set_device(0)
    if "RTX 4090" not in torch.cuda.get_device_name(0):
        raise RuntimeError("Reference GPU identity mismatch")
    path = ROOT / lock["checkpoint"]
    if candidate["family"] == "setfit":
        from setfit import SetFitModel

        model = SetFitModel.from_pretrained(str(path), local_files_only=True, device="cuda:0")
        if list(model.model_head.classes_) != list(range(len(lock["classes"]))):
            raise ValueError("SetFit class map changed")
        model.model_body.eval()

        def infer(texts):
            return model.predict_proba(
                texts, batch_size=8, as_numpy=True, show_progress_bar=False
            ).tolist()
    else:
        model, tokenizer = transformer_load(candidate, path, lock["classes"])
        definitions = (
            manifest["class_definitions"][task]
            if candidate["family"] == "cross_encoder_zero_shot"
            else None
        )

        def infer(texts):
            return transformer_predict(
                model, tokenizer, texts, manifest["common_training"]["max_length"], definitions
            )

    infer(["The neutral marker has one stated property."])
    torch.cuda.synchronize(0)
    torch.cuda.reset_peak_memory_stats(0)
    rows = selection_rows(task)
    predictions, latencies = [], []
    start = time.perf_counter()
    for repeat in range(1, 4):
        probabilities, batch_timings = [], []
        for offset in range(0, len(rows), 8):
            batch = rows[offset : offset + 8]
            torch.cuda.synchronize(0)
            before = time.perf_counter()
            probabilities.extend(infer(model_inputs(batch)))
            torch.cuda.synchronize(0)
            elapsed = time.perf_counter() - before
            latencies.extend([elapsed / len(batch)] * len(batch))
            batch_timings.append({"offset": offset, "rows": len(batch), "elapsed_seconds": elapsed})
        labels = predict_labels(probabilities, lock["classes"], lock["policy"])
        predictions.append(labels)
        write(
            output / f"repeat-{repeat}.json",
            {
                "case_ids": [r["case_id"] for r in rows],
                "classes": lock["classes"],
                "probabilities": probabilities,
                "labels": labels,
                "batch_timings": batch_timings,
            },
        )
    result = evaluate(
        task,
        rows,
        predictions,
        manifest["tasks"][task]["output_classes"],
        latencies,
        torch.cuda.max_memory_allocated(0),
        sum(a["bytes"] for a in lock["artifacts"].values()),
    )
    write(
        output / "result.json",
        {
            "status": "completed",
            "candidate_id": candidate_id,
            "task": task,
            "rows": len(rows),
            "repeats": 3,
            "classes": lock["classes"],
            "policy": lock["policy"],
            "checkpoint": lock["checkpoint"],
            "elapsed_seconds": time.perf_counter() - start,
            "measurement": manifest["selection_measurement"],
            **result,
        },
    )


def standard_venv_identity():
    executable = ROOT / ".venv/Scripts/python.exe"
    return {
        "executable_sha256": sha(executable),
        "pip_freeze": subprocess.check_output([str(executable), "-m", "pip", "freeze"], text=True),
    }


def orchestrate(output):
    if output.exists():
        raise ValueError("New run directory required; evidence cannot be overwritten")
    frozen, manifest = verify_inputs()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("Selection requires clean committed inputs")
    output.mkdir(parents=True)
    before = standard_venv_identity()
    runtime = manifest["runtime_identity"]
    import importlib.metadata

    for package, expected in runtime["packages"].items():
        if importlib.metadata.version(package) != expected:
            raise ValueError("Runtime package changed: " + package)
    import torch

    if torch.version.cuda != runtime["cuda_build"]:
        raise ValueError("PyTorch CUDA build changed")
    write(
        output / "runtime-lock.json",
        {
            "python": sys.version,
            "packages": {p: importlib.metadata.version(p) for p in runtime["packages"]},
            "cuda_build": torch.version.cuda,
            "devices": [
                {
                    "name": torch.cuda.get_device_name(i),
                    "vram_bytes": torch.cuda.get_device_properties(i).total_memory,
                }
                for i in range(torch.cuda.device_count())
            ],
            "pip_freeze": subprocess.check_output(
                [sys.executable, "-m", "pip", "freeze"], text=True
            ),
        },
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    write(
        output / "input-lock.json",
        {
            "selection_input_head": head,
            "training_input_head": frozen["training_input_lock"]["benchmark_input_head"],
            "policy_lock_sha256": sha(FREEZE),
            "candidate_manifest_sha256": sha(MANIFEST),
            "runner_sha256": sha(Path(__file__)),
            "selector_sha256": sha(Path(__file__).with_name("n04g25a_select_development.py")),
            "confirmation_started": False,
        },
    )
    results = []
    for candidate in manifest["candidates"]:
        for task in manifest["tasks"]:
            job = output / candidate["candidate_id"] / task
            job.mkdir(parents=True)
            write(
                output / "status.json",
                {
                    "stage": "selection_running",
                    "candidate_id": candidate["candidate_id"],
                    "task": task,
                    "confirmation_started": False,
                },
            )
            with (
                (job / "stdout.log").open("w", encoding="utf-8") as stdout,
                (job / "stderr.log").open("w", encoding="utf-8") as stderr,
            ):
                code = subprocess.call(
                    [
                        sys.executable,
                        str(Path(__file__)),
                        "--child",
                        candidate["candidate_id"],
                        "--task",
                        task,
                        "--output",
                        str(job),
                    ],
                    cwd=ROOT,
                    stdout=stdout,
                    stderr=stderr,
                )
            results.append(
                read(job / "result.json")
                if code == 0
                else {
                    "status": "execution_failed",
                    "candidate_id": candidate["candidate_id"],
                    "task": task,
                    "exit_code": code,
                }
            )
            write(output / "results.json", results)
    verify_inputs()
    unchanged = before == standard_venv_identity()
    complete = all(r["status"] == "completed" for r in results)
    outcome = (
        select(results, [c["candidate_id"] for c in manifest["candidates"]])
        if complete and unchanged
        else {"outcome": "BLOCKED_execution", "confirmation_started": False}
    )
    write(
        output / "comparison.json",
        {**outcome, "standard_venv_unchanged": unchanged, "results": results},
    )
    write(
        output / "status.json",
        {
            "stage": "selection_finished_awaiting_review"
            if complete and unchanged
            else "BLOCKED_selection",
            **outcome,
            "standard_venv_unchanged": unchanged,
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--child")
    parser.add_argument("--task", choices=["atomicity", "content_type"])
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to((ROOT / ".local/n04-v4/g25a").resolve()):
        raise ValueError("Evidence must stay inside ignored G-25A work area")
    for name in (
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
        "PYTHONNOUSERSITE",
    ):
        os.environ[name] = "1"
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    try:
        if args.child:
            child(args.child, args.task, args.output)
        else:
            orchestrate(args.output)
    except Exception:
        args.output.mkdir(parents=True, exist_ok=True)
        write(
            args.output / "execution-error.json",
            {"traceback": traceback.format_exc(), "confirmation_started": False},
        )
        raise


if __name__ == "__main__":
    main()
