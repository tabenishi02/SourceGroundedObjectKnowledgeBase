"""Train/validate frozen G-25A candidates offline. Selection is a separate stage.

Only the two development corpora are accepted. Raw checkpoints stay under .local.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import traceback
from pathlib import Path

from n04g25a_development_metrics import fit_policy, model_inputs

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "benchmark/n04g25a-candidate-manifest-v1.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path):
    with path.open("rb") as stream:
        return (
            hashlib.file_digest(stream, "sha256").hexdigest()
            if hasattr(hashlib, "file_digest")
            else _digest(stream)
        )


def _digest(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def tree(path):
    return {
        str(p.relative_to(path)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
        for p in sorted(path.rglob("*"))
        if p.is_file()
    }


def rows_for(task, partition):
    if task not in {"atomicity", "content_type"} or partition not in {"train", "validation"}:
        raise ValueError("Training runner accepts train/validation development inputs only")
    suffix = task.replace("_", "-")
    path = ROOT / f"benchmark/n04g25a-{suffix}-development-v1.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return [row for row in rows if row["split"] == partition]


def seed_everything(seed):
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.set_num_threads(4)


def transformer_load(candidate, path, classes):
    import torch
    from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

    config = AutoConfig.from_pretrained(path, local_files_only=True)
    if candidate["family"] == "sequence_classifier":
        config.num_labels = len(classes)
        config.id2label = dict(enumerate(classes))
        config.label2id = {label: i for i, label in enumerate(classes)}
    if candidate["family"] == "cross_encoder_zero_shot":
        matches = [int(k) for k, v in config.id2label.items() if str(v).lower() == "entailment"]
        if len(matches) != 1:
            raise ValueError("Exact NLI config has no unambiguous entailment mapping")
    tokenizer = AutoTokenizer.from_pretrained(
        path, local_files_only=True, use_fast=config.model_type != "deberta-v2"
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        path,
        config=config,
        local_files_only=True,
        attn_implementation="eager",
        torch_dtype=torch.float32,
    ).to("cuda:0")
    return model, tokenizer


def transformer_predict(model, tokenizer, texts, max_length, definitions=None):
    import torch

    model.eval()
    vectors = []
    with torch.no_grad():
        for offset in range(0, len(texts), 8):
            batch = texts[offset : offset + 8]
            if definitions:
                premises = [text for text in batch for _ in definitions]
                hypotheses = list(definitions.values()) * len(batch)
                tokens = tokenizer(
                    premises,
                    hypotheses,
                    truncation=True,
                    padding=True,
                    max_length=max_length,
                    return_tensors="pt",
                ).to("cuda:0")
                logits = model(**tokens).logits.softmax(-1)
                entailment = next(
                    int(k)
                    for k, v in model.config.id2label.items()
                    if str(v).lower() == "entailment"
                )
                scores = logits[:, entailment].reshape(len(batch), len(definitions))
                scores = scores / scores.sum(-1, keepdim=True)
            else:
                tokens = tokenizer(
                    batch, truncation=True, padding=True, max_length=max_length, return_tensors="pt"
                ).to("cuda:0")
                scores = model(**tokens).logits.softmax(-1)
            vectors.extend(scores.cpu().tolist())
    return vectors


def train_transformer(candidate, task, manifest, out, train, validation, classes):
    import torch

    config = manifest["common_training"]
    model, tokenizer = transformer_load(candidate, ROOT / candidate["local_path"], classes)
    if candidate["family"] == "cross_encoder_zero_shot":
        definitions = manifest["class_definitions"][task]
        probabilities = transformer_predict(
            model, tokenizer, model_inputs(validation), config["max_length"], definitions
        )
        return probabilities, {
            "checkpoint": candidate["local_path"],
            "epoch": None,
            "entailment_mapping": model.config.id2label,
        }
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"]
    )
    train = [r for r in train if r["training_target"]]
    targets = {label: i for i, label in enumerate(classes)}
    validation_supervised = [r for r in validation if r["training_target"]]
    best_loss, best_epoch = float("inf"), None
    history = []
    checkpoint = out / "checkpoint"
    for epoch in range(1, config["epochs"] + 1):
        model.train()
        order = torch.randperm(len(train)).tolist()
        losses = []
        for offset in range(0, len(order), config["per_device_batch_size"]):
            batch = [train[i] for i in order[offset : offset + config["per_device_batch_size"]]]
            tokens = tokenizer(
                model_inputs(batch),
                truncation=True,
                padding=True,
                max_length=config["max_length"],
                return_tensors="pt",
            ).to("cuda:0")
            labels = torch.tensor([targets[r["label"]] for r in batch], device="cuda:0")
            optimizer.zero_grad(set_to_none=True)
            loss = model(**tokens, labels=labels).loss
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        probs = transformer_predict(
            model, tokenizer, model_inputs(validation_supervised), config["max_length"]
        )
        import math

        val_loss = sum(
            -math.log(max(p[targets[r["label"]]], 1e-30))
            for p, r in zip(probs, validation_supervised)
        ) / len(probs)
        history.append(
            {
                "epoch": epoch,
                "train_loss": sum(losses) / len(losses),
                "validation_cross_entropy": val_loss,
            }
        )
        write(out / "epochs.json", history)
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch
            model.save_pretrained(checkpoint, safe_serialization=True)
            tokenizer.save_pretrained(checkpoint)
    del optimizer, model
    gc.collect()
    torch.cuda.empty_cache()
    model, tokenizer = transformer_load(candidate, checkpoint, classes)
    probabilities = transformer_predict(
        model, tokenizer, model_inputs(validation), config["max_length"]
    )
    return probabilities, {
        "checkpoint": checkpoint.relative_to(ROOT).as_posix(),
        "epoch": best_epoch,
        "validation_cross_entropy": best_loss,
        "epochs": history,
    }


def train_setfit(candidate, manifest, out, train, validation, classes):
    from datasets import Dataset
    from setfit import SetFitModel, Trainer, TrainingArguments

    sample = []
    rng = random.Random(manifest["seed"])
    for label in classes:
        eligible = [r for r in train if r["training_target"] and r["label"] == label]
        sample.extend(rng.sample(eligible, candidate["few_shot_per_class"]))
    model = SetFitModel.from_pretrained(
        str(ROOT / candidate["local_path"]),
        local_files_only=True,
        use_differentiable_head=False,
        head_params=candidate["head_params"],
        device="cuda:0",
    )
    model.model_body.max_seq_length = manifest["common_training"]["max_length"]
    args = TrainingArguments(
        output_dir=str(out / "setfit-training"),
        batch_size=candidate["body_batch_size"],
        num_epochs=candidate["body_epochs"],
        num_iterations=candidate["num_iterations"],
        seed=manifest["seed"],
        max_length=manifest["common_training"]["max_length"],
        report_to="none",
        save_strategy="no",
        show_progress_bar=False,
    )
    dataset = Dataset.from_dict(
        {"text": model_inputs(sample), "label": [classes.index(r["label"]) for r in sample]}
    )
    Trainer(model=model, args=args, train_dataset=dataset).train()
    checkpoint = out / "checkpoint"
    model.save_pretrained(checkpoint)
    # Head probability columns must follow the frozen numeric class map.
    if list(model.model_head.classes_) != list(range(len(classes))):
        raise ValueError("SetFit head class mapping mismatch")
    probabilities = model.predict_proba(
        model_inputs(validation), as_numpy=True, show_progress_bar=False
    ).tolist()
    return probabilities, {
        "checkpoint": checkpoint.relative_to(ROOT).as_posix(),
        "sample_case_ids": [r["case_id"] for r in sample],
        "head_classes": model.model_head.classes_.tolist(),
    }


def child(candidate_id, task, out):
    import torch

    manifest = read(MANIFEST)
    candidate = next(c for c in manifest["candidates"] if c["candidate_id"] == candidate_id)
    seed_everything(manifest["seed"])
    torch.cuda.init()
    torch.cuda.set_device(0)
    if "RTX 4090" not in torch.cuda.get_device_name(0):
        raise RuntimeError("Frozen Reference Workstation GPU identity mismatch")
    torch.cuda.reset_peak_memory_stats(0)
    classes = manifest["tasks"][task]["supervised_classes"]
    if candidate["family"] == "cross_encoder_zero_shot":
        classes = list(manifest["class_definitions"][task])
    train, validation = rows_for(task, "train"), rows_for(task, "validation")
    start = time.perf_counter()
    if candidate["family"] == "setfit":
        probabilities, checkpoint = train_setfit(
            candidate, manifest, out, train, validation, classes
        )
    else:
        probabilities, checkpoint = train_transformer(
            candidate, task, manifest, out, train, validation, classes
        )
    policy = fit_policy(task, validation, probabilities, classes, manifest)
    write(
        out / "validation-probabilities.json",
        {
            "case_ids": [r["case_id"] for r in validation],
            "classes": classes,
            "probabilities": probabilities,
        },
    )
    checkpoint_path = ROOT / checkpoint["checkpoint"]
    checkpoint["artifacts"] = tree(checkpoint_path)
    result = {
        "status": "checkpoint_policy_locked",
        "candidate_id": candidate_id,
        "task": task,
        "classes": classes,
        **policy,
        **checkpoint,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_allocated_vram_bytes": torch.cuda.max_memory_allocated(0),
        "selection_started": False,
        "confirmation_started": False,
    }
    write(out / "lock.json", result)


def orchestrate(out):
    if out.exists():
        raise ValueError("New run directory required; evidence cannot be overwritten")
    out.mkdir(parents=True)
    manifest = read(MANIFEST)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("Training requires clean committed inputs")
    write(
        out / "input-lock.json",
        {
            "benchmark_input_head": head,
            "candidate_manifest_sha256": sha(MANIFEST),
            "development_files": {
                p.name: sha(p)
                for p in sorted((ROOT / "benchmark").glob("n04g25a-*development*.json*"))
            },
            "split_manifest_sha256": sha(ROOT / "benchmark/n04g25a-split-manifest-v1.json"),
            "runner_sha256": sha(Path(__file__)),
            "metrics_sha256": sha(Path(__file__).with_name("n04g25a_development_metrics.py")),
            "confirmation_started": False,
        },
    )
    standard_python = ROOT / ".venv/Scripts/python.exe"
    baseline = subprocess.check_output([str(standard_python), "-m", "pip", "freeze"], text=True)
    write(
        out / "standard-venv-before.json",
        {"pip_freeze": baseline, "executable_sha256": sha(standard_python)},
    )
    for c in manifest["candidates"]:
        for name, expected in c["downloaded_artifact_identity"].items():
            p = ROOT / c["local_path"] / name
            if p.stat().st_size != expected["bytes"] or sha(p) != expected["sha256"]:
                raise ValueError(f"Artifact identity mismatch: {c['candidate_id']}/{name}")
    write(
        out / "runtime-packages.json",
        {
            "python": sys.version,
            "pip_freeze": subprocess.check_output(
                [sys.executable, "-m", "pip", "freeze"], text=True
            ),
        },
    )
    jobs = []
    for candidate in manifest["candidates"]:
        for task in manifest["tasks"]:
            job = out / candidate["candidate_id"] / task
            job.mkdir(parents=True)
            write(
                out / "status.json",
                {
                    "stage": "training_validation_only",
                    "candidate_id": candidate["candidate_id"],
                    "task": task,
                    "selection_started": False,
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
            jobs.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "task": task,
                    "exit_code": code,
                    "lock": str((job / "lock.json").relative_to(ROOT)).replace("\\", "/")
                    if code == 0
                    else None,
                }
            )
            write(out / "jobs.json", jobs)
    after = subprocess.check_output([str(standard_python), "-m", "pip", "freeze"], text=True)
    unchanged = (
        baseline == after
        and sha(standard_python) == read(out / "standard-venv-before.json")["executable_sha256"]
    )
    write(out / "standard-venv-after.json", {"unchanged": unchanged, "pip_freeze": after})
    stage = (
        "all_checkpoint_policies_locked_awaiting_review"
        if unchanged and all(j["exit_code"] == 0 for j in jobs)
        else "BLOCKED_training_requires_review"
    )
    write(
        out / "policy-freeze.json",
        {
            "stage": stage,
            "jobs": jobs,
            "lock_hashes": {j["lock"]: sha(ROOT / j["lock"]) for j in jobs if j["lock"]},
            "standard_venv_unchanged": unchanged,
            "selection_started": False,
            "confirmation_started": False,
        },
    )
    write(out / "status.json", read(out / "policy-freeze.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--child")
    parser.add_argument("--task", choices=["atomicity", "content_type"])
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to((ROOT / ".local/n04-v4/g25a").resolve()):
        raise ValueError("Run evidence must stay inside the ignored G-25A work area")
    for key in (
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
        "PYTHONNOUSERSITE",
    ):
        os.environ[key] = "1"
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
