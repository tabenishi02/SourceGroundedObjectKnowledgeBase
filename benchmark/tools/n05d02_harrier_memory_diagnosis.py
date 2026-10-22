"""N05D-02 offline, fresh-process Harrier diagnostics; never change provider behavior."""

from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
MODEL = "microsoft/harrier-oss-v1-0.6b"
REVISION = "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee"
SOURCE = ROOT / ".local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite"
TARGETS = (2048, 4096, 8192, 12288, 16384)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def offline():
    os.environ.update(
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", CUDA_VISIBLE_DEVICES="0", PYTHONUTF8="1"
    )


def prefixes(text, count):
    """Largest complete-line prefix <= target; do not assume token-count monotonicity."""
    candidates = {target: ("", 0) for target in TARGETS}
    prefix = ""
    for line in text.splitlines(keepends=True):
        prefix += line
        tokens = count(prefix)
        for target in TARGETS:
            if tokens <= target:
                candidates[target] = (prefix, tokens)
    if any(not value[0] for value in candidates.values()):
        raise ValueError("No complete-line prefix fits a required target")
    return candidates


def verdict(trials, complete_curve, source_unchanged=True, driver_errors=False):
    if not source_unchanged:
        return "BLOCKED"
    if any(t.get("resource_failure") for t in trials) or driver_errors:
        return "NOT_VIABLE_REQUIRES_DESIGN_REMEDIATION"
    full = [t for t in trials if t.get("full")]
    if complete_curve and len(full) == 3 and all(t.get("status") == "PASS" for t in trials):
        return "VIABLE_FOR_FORMAL_RERUN"
    return "BLOCKED"


class Pdh:
    """English PDH paths work regardless of the Windows display language."""

    class Value(ct.Structure):
        _fields_ = [("status", ct.c_ulong), ("number", ct.c_double)]

    def __init__(self):
        self.dll = ct.WinDLL("pdh")
        self.query = ct.c_void_p()
        self.check(self.dll.PdhOpenQueryW(None, 0, ct.byref(self.query)))
        self.counters = {}
        paths = {
            "dedicated": r"\GPU Process Memory(*)\Dedicated Usage",
            "shared": r"\GPU Process Memory(*)\Shared Usage",
            "system_available": r"\Memory\Available Bytes",
            "system_committed": r"\Memory\Committed Bytes",
            "system_commit_limit": r"\Memory\Commit Limit",
        }
        for key, path in paths.items():
            counter = ct.c_void_p()
            self.check(
                self.dll.PdhAddEnglishCounterW(self.query, ct.c_wchar_p(path), 0, ct.byref(counter))
            )
            self.counters[key] = counter
        self.collect()

    @staticmethod
    def check(code):
        if code:
            raise OSError(f"PDH error 0x{code & 0xFFFFFFFF:08x}")

    def collect(self):
        self.check(self.dll.PdhCollectQueryData(self.query))

    def array(self, counter):
        class Item(ct.Structure):
            _fields_ = [("name", ct.c_wchar_p), ("value", Pdh.Value)]

        size, count = ct.c_ulong(), ct.c_ulong()
        code = self.dll.PdhGetFormattedCounterArrayW(
            counter, 0x200, ct.byref(size), ct.byref(count), None
        )
        if code & 0xFFFFFFFF != 0x800007D2:
            self.check(code)
        buffer = ct.create_string_buffer(size.value)
        self.check(
            self.dll.PdhGetFormattedCounterArrayW(
                counter, 0x200, ct.byref(size), ct.byref(count), buffer
            )
        )
        items = ct.cast(buffer, ct.POINTER(Item))
        return [
            {
                "instance": items[i].name,
                "value": items[i].value.number,
                "status": items[i].value.status,
            }
            for i in range(count.value)
        ]

    def sample(self, pid):
        self.collect()
        result = {}
        for name, counter in self.counters.items():
            if name in ("shared", "dedicated"):
                values = [x for x in self.array(counter) if x["instance"].startswith(f"pid_{pid}_")]
                valid = [x for x in values if x["status"] in (0, 1)]
                result[name] = sum(x["value"] for x in valid) if valid else None
                result[name + "_instances"] = values
            else:
                value = self.Value()
                self.check(
                    self.dll.PdhGetFormattedCounterValue(counter, 0x200, None, ct.byref(value))
                )
                if value.status not in (0, 1):
                    raise OSError(f"Invalid PDH status {value.status}")
                result[name] = value.number
        return result

    def close(self):
        self.dll.PdhCloseQuery(self.query)


def capture(args):
    return subprocess.check_output(
        args, cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    ).strip()


def prepare(root):
    from transformers import AutoTokenizer

    from sgokb.repository import Repository
    from sgokb.retrieval.search_representation import SearchRepresentationBuilder

    source_hash = sha(SOURCE)
    connection = sqlite3.connect(SOURCE.resolve().as_uri() + "?mode=ro", uri=True)
    copy = sqlite3.connect(root / "input.sqlite")
    try:
        connection.backup(copy)
    finally:
        copy.close()
        connection.close()
    repository = Repository(root / "input.sqlite")
    try:
        row = repository.db.execute(
            "SELECT current_version_id FROM objects WHERE id=?", ("object-n05-large",)
        ).fetchone()
        if not row or not row[0]:
            raise ValueError("Authoritative current Version unavailable")
        version = row[0]
        built = SearchRepresentationBuilder(repository).build_object_overall(version)
    finally:
        repository.close()
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, revision=REVISION, cache_dir=str(ROOT / ".local/models"), local_files_only=True
    )

    def count(text):
        return len(tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"])

    text = built.content
    full_tokens = count(text)
    if full_tokens > 32768:
        raise ValueError("Authoritative full representation exceeds frozen maximum")
    (root / "full.txt").write_text(text, encoding="utf-8")
    points = []
    for target, (prefix, actual) in prefixes(text, count).items():
        filename = f"prefix-{target}.txt"
        (root / filename).write_text(prefix, encoding="utf-8")
        points.append(
            {
                "name": str(target),
                "file": filename,
                "requested_tokens": target,
                "actual_tokens": actual,
                "full": False,
            }
        )
    points.append(
        {
            "name": "full-1",
            "file": "full.txt",
            "requested_tokens": full_tokens,
            "actual_tokens": full_tokens,
            "full": True,
        }
    )
    manifest = {
        "source_db": str(SOURCE.relative_to(ROOT)),
        "source_db_sha256": source_hash,
        "object_id": "object-n05-large",
        "version_id": version,
        "representation_sha256": built.content_hash,
        "characters": len(text),
        "lines": len(text.splitlines()),
        "exact_tokens": full_tokens,
        "points": points,
    }
    assert sha(SOURCE) == source_hash
    write(root / "input-manifest.json", manifest)
    return manifest


def verify_preprocessed_input(provider, text, expected_tokens):
    """Validate the installed encode preprocessing path without changing inference."""
    encoder = provider._encoder
    if encoder.default_prompt_name is not None or provider.document_instruction:
        raise ValueError("Unexpected document prompt; input identity must be investigated")
    features = encoder.preprocess([text])
    ids = features["input_ids"]
    raw = encoder.tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"]
    if list(ids.shape) != [1, expected_tokens] or ids[0].tolist() != raw:
        raise ValueError("Preprocessed token IDs differ; truncation/input change detected")
    return {
        "shape": list(ids.shape),
        "raw_token_ids_equal": True,
        "default_prompt_name": encoder.default_prompt_name,
        "verification": "encode preprocessing; CPU tokenization is not CPU inference",
    }


def trial(directory):
    import psutil
    import torch

    from sgokb.retrieval.embedding import default_sentence_transformer_provider

    request = json.loads((directory / "request.json").read_text())
    text = (directory.parent / request["file"]).read_text(encoding="utf-8")
    result = {
        **request,
        "pid": os.getpid(),
        "status": "BLOCKED",
        "resource_failure": False,
        "input_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    write(directory / "worker.json", result)
    monitor = Pdh()
    samples, monitor_errors = [], []
    stop = threading.Event()
    phase = {"value": "model_load"}

    def observe():
        process = psutil.Process()
        next_smi = 0
        with (directory / "memory-samples.jsonl").open("w", encoding="utf-8") as stream:
            while not stop.is_set():
                try:
                    sample = {
                        "monotonic": time.perf_counter(),
                        "timestamp": datetime.now().astimezone().isoformat(),
                        "phase": phase["value"],
                        **monitor.sample(os.getpid()),
                    }
                    memory = process.memory_info()
                    sample.update(working_set=memory.rss, private_memory=memory.private)
                    if time.monotonic() >= next_smi:
                        sample["nvidia_smi"] = capture(
                            [
                                "nvidia-smi",
                                "-i",
                                "0",
                                "--query-gpu=memory.used,memory.total,utilization.gpu",
                                "--format=csv,noheader,nounits",
                            ]
                        )
                        next_smi = time.monotonic() + 5
                    samples.append(sample)
                    stream.write(json.dumps(sample) + "\n")
                    stream.flush()
                except Exception as exc:
                    monitor_errors.append(repr(exc))
                stop.wait(0.25)

    thread = threading.Thread(target=observe, daemon=True)
    thread.start()
    started = None
    try:
        provider = default_sentence_transformer_provider(
            cache_folder=str(ROOT / ".local/models"), local_files_only=True
        )
        provider.batch_size = 1
        model = provider._encoder[0].auto_model
        config = model.config
        actual = len(
            provider._encoder.tokenizer(text, add_special_tokens=True, truncation=False)[
                "input_ids"
            ]
        )
        assert actual == request["actual_tokens"] and provider.device == "cuda"
        assert provider.space.model_revision == REVISION and provider.max_sequence_length == 32768
        assert provider.dtype == "bfloat16" and provider.overflow_policy == "reject"
        assert next(model.parameters()).dtype == torch.bfloat16
        result["runtime"] = {
            "model": MODEL,
            "revision": provider.revision,
            "device": provider.device,
            "dtype": str(next(model.parameters()).dtype),
            "batch_size": provider.batch_size,
            "max_sequence_length": provider.max_sequence_length,
            "overflow_policy": provider.overflow_policy,
            "versions": {
                p: importlib.metadata.version(p)
                for p in ("torch", "transformers", "sentence-transformers", "tokenizers")
            },
            "cuda_build": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(),
            "total_vram": torch.cuda.get_device_properties(0).total_memory,
            "config": {
                k: getattr(config, k, None)
                for k in (
                    "_commit_hash",
                    "_attn_implementation",
                    "model_type",
                    "num_hidden_layers",
                    "hidden_size",
                    "num_attention_heads",
                    "num_key_value_heads",
                    "head_dim",
                    "max_position_embeddings",
                    "use_cache",
                )
            },
            "attention_modules": sorted(
                {
                    type(m).__name__
                    for m in model.modules()
                    if "attention" in type(m).__name__.lower()
                }
            ),
            "sdpa_enabled": {
                "flash": torch.backends.cuda.flash_sdp_enabled(),
                "memory_efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
                "math": torch.backends.cuda.math_sdp_enabled(),
            },
            "warmup": "none; identical policy for all fresh workers",
        }

        result["preprocessed_input"] = verify_preprocessed_input(provider, text, actual)
        write(directory / "runtime.json", result["runtime"])
        torch.cuda.synchronize()
        result.update(
            baseline_allocated=torch.cuda.memory_allocated(),
            baseline_reserved=torch.cuda.memory_reserved(),
            mem_get_info_before=list(torch.cuda.mem_get_info()),
        )
        torch.cuda.reset_peak_memory_stats()
        phase["value"] = "embedding"
        started = time.perf_counter()
        vector = provider.embed_documents([text])[0]
        torch.cuda.synchronize()
        result["embedding_seconds"] = time.perf_counter() - started
        phase["value"] = "after_embedding"
        result.update(
            peak_allocated=torch.cuda.max_memory_allocated(),
            peak_reserved=torch.cuda.max_memory_reserved(),
            mem_get_info_after=list(torch.cuda.mem_get_info()),
            dimension=len(vector),
            finite=all(math.isfinite(x) for x in vector),
            vector_norm=math.sqrt(sum(x * x for x in vector)),
        )
        assert (
            result["dimension"] == 1024
            and result["finite"]
            and abs(result["vector_norm"] - 1) < 0.01
        )
        result["status"] = "PASS"
    except Exception as exc:
        result.update(
            status="FAIL",
            exception={
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
            resource_failure=isinstance(exc, torch.cuda.OutOfMemoryError),
        )
        if started is not None:
            result["embedding_seconds"] = time.perf_counter() - started
            result.update(
                peak_allocated=torch.cuda.max_memory_allocated(),
                peak_reserved=torch.cuda.max_memory_reserved(),
            )
    finally:
        stop.set()
        thread.join()
        monitor.close()
        measured = [s for s in samples if s["phase"] == "embedding"]
        result["monitor_errors"] = monitor_errors
        result["embedding_sample_count"] = len(measured)
        for key in (
            "dedicated",
            "shared",
            "working_set",
            "private_memory",
            "system_committed",
            "system_commit_limit",
        ):
            values = [s[key] for s in measured if s.get(key) is not None]
            result["peak_" + key] = max(values) if values else None
        available = [s["system_available"] for s in measured]
        result["min_system_available"] = min(available) if available else None
        if (
            not measured
            or any(result.get("peak_" + k) is None for k in ("shared", "dedicated"))
            or monitor_errors
        ):
            result["status"] = "BLOCKED"
        write(directory / "result.json", result)
    return result


def run(root):
    root.mkdir(parents=True, exist_ok=False)

    def state(stage, **extra):
        write(root / "execution-status.json", {"stage": stage, "pid": os.getpid(), **extra})

    trials = []
    try:
        state("preparing_input_and_instrumentation")
        write(
            root / "environment.json",
            {
                "head": capture(["git", "rev-parse", "HEAD"]),
                "git_status": capture(["git", "status", "--short"]),
                "python": sys.version,
                "os": platform.platform(),
                "gpu": capture(
                    [
                        "nvidia-smi",
                        "--query-gpu=index,name,uuid,driver_version,memory.total,memory.used",
                        "--format=csv",
                    ]
                ),
                "gpu_processes": capture(
                    [
                        "nvidia-smi",
                        "-i",
                        "0",
                        "--query-compute-apps=pid,process_name,used_memory",
                        "--format=csv",
                    ]
                ),
            },
        )
        # A substantial baseline allocation invalidates isolation; never kill another workload.
        used = float(
            capture(
                [
                    "nvidia-smi",
                    "-i",
                    "0",
                    "--query-gpu=memory.used",
                    "--format=csv,noheader,nounits",
                ]
            )
        )
        if used > 2048:
            raise RuntimeError("GPU baseline exceeds 2 GiB; competing-workload review required")
        monitor = Pdh()
        write(root / "instrumentation-probe.json", monitor.sample(os.getpid()))
        monitor.close()
        manifest = prepare(root)
        points = list(manifest["points"])
        index = 0
        while index < len(points):
            point = points[index]
            directory = root / point["name"]
            directory.mkdir()
            write(directory / "request.json", point)
            state("measuring_" + point["name"])
            with (
                (directory / "stdout.log").open("w") as out,
                (directory / "stderr.log").open("w") as err,
            ):
                code = subprocess.run(
                    [sys.executable, __file__, "--trial", str(directory)],
                    stdout=out,
                    stderr=err,
                    cwd=ROOT,
                ).returncode
            if not (directory / "result.json").exists():
                result = {
                    **point,
                    "status": "BLOCKED",
                    "return_code": code,
                    "exception": "Worker exited without measurements; retain logs for diagnosis",
                }
            else:
                result = json.loads((directory / "result.json").read_text())
                result["return_code"] = code
                if code != 0:
                    result["status"] = "BLOCKED"
            trials.append(result)
            write(root / "trials.json", trials)
            if result["status"] != "PASS":
                break
            if point["name"] == "full-1":
                points += [{**point, "name": f"full-{i}"} for i in (2, 3)]
            index += 1
        unchanged = sha(SOURCE) == manifest["source_db_sha256"]
        # Driver/display reset events during this exact run are evidence, not inferred from OOM.
        start = datetime.fromtimestamp((root / "environment.json").stat().st_mtime).isoformat()
        script = (
            "$ErrorActionPreference='Stop'; @(Get-WinEvent -FilterHashtable "
            "@{LogName='System'; StartTime=[datetime]'"
            + start
            + "'} -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 4101 -or "
            "($_.ProviderName -eq 'nvlddmkm' -and $_.Id -eq 153) } | "
            "Select-Object TimeCreated,Id,ProviderName,Message) | ConvertTo-Json -Depth 4"
        )
        events = capture(["powershell.exe", "-NoProfile", "-Command", script])
        (root / "driver-events.json").write_text(events or "[]", encoding="utf-8")
        decision = verdict(
            trials, len(trials) == 8, unchanged, bool(events.strip() and events.strip() != "[]")
        )
        write(
            root / "summary.json",
            {
                "verdict": decision,
                "source_unchanged": unchanged,
                "trials": trials,
                "input": manifest,
            },
        )
        state("diagnosis_finished_awaiting_review", verdict=decision)
    except Exception as exc:
        write(
            root / "execution-error.json",
            {"exception": repr(exc), "traceback": traceback.format_exc()},
        )
        state("BLOCKED_diagnosis", error=repr(exc))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--trial", type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    offline()
    if args.trial:
        trial(args.trial)
    elif args.run_root:
        run(args.run_root)
    else:
        parser.error("--run-root or --trial is required")


if __name__ == "__main__":
    main()
