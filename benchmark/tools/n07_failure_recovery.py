"""N-07 formal fault execution. All mutations are confined to fresh run-owned fixtures."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(Path(__file__).parent)]

from n06_retrieval_vector_quality import reference_vector_snapshot  # noqa: E402
from n07_evaluate_failure_recovery import CONTRACT, evaluate  # noqa: E402
from n07_recovery_helpers import database_digest, owned_path  # noqa: E402

R1 = [
    "benchmark/tools/n05_resource_preflight.py",
    "benchmark/tools/n05d04r1_sdpa_vram_diagnosis.py",
    "tests/test_n05d04r1_sdpa_vram_diagnosis.py",
]
N07 = "tests/test_n07_failure_recovery.py::"


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def originals(workspace):
    result = {"databases": {}, "r1": {}, "raw_files": {}}
    for relative in [".local/sgokb.sqlite", ".local/n03/sgokb-n03.sqlite"]:
        path = workspace / relative
        if not path.is_file():
            result["databases"][relative] = {"exists": False}
            continue
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            result["databases"][relative] = {
                "exists": True,
                "sha256": sha(path),
                "tables_digest": database_digest(db),
            }
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='raw_artifacts'").fetchone():
                for (ref,) in db.execute("SELECT DISTINCT storage_ref FROM raw_artifacts"):
                    raw = Path(ref)
                    if not raw.is_absolute():
                        raw = workspace / raw
                    result["raw_files"][str(raw)] = sha(raw) if raw.is_file() else None
        finally:
            db.close()
    for relative in R1:
        path = workspace / relative
        result["r1"][relative] = sha(path) if path.is_file() else None
    return result


def pytest_case(run, label, selectors, *, real_provider=False):
    owned_path(run, run / label)
    env = dict(os.environ)
    if real_provider:
        env["N07_REAL_PROVIDER"] = "1"
    else:
        env.pop("N07_REAL_PROVIDER", None)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *selectors,
        "--basetemp",
        str(run / label / "fixtures"),
        "--junitxml",
        str(run / (label + ".xml")),
    ]
    start = time.perf_counter()
    with (run / (label + ".log")).open("w", encoding="utf-8") as log:
        rc = subprocess.run(
            command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600
        ).returncode
    xml = run / (label + ".xml")
    cases = list(ET.parse(xml).iter("testcase")) if xml.is_file() else []
    skipped = sum(c.find("skipped") is not None for c in cases)
    failed = sum(c.find("failure") is not None or c.find("error") is not None for c in cases)
    return {
        "status": "PASS"
        if rc == 0 and cases and not skipped and not failed
        else "BLOCKED"
        if not cases or skipped
        else "FAIL",
        "return_code": rc,
        "passed": len(cases) - failed - skipped,
        "failed": failed,
        "skipped": skipped,
        "seconds": time.perf_counter() - start,
        "selectors": selectors,
        "junit": xml.name,
        "log": label + ".log",
    }


def selections(contract):
    stages = contract["stages"]
    result = {}
    for n, name in enumerate(stages["B_exchange_input"], 1):
        result[name] = [N07 + f"test_exchange_faults[B{n:02}]"]
    for name, checkpoint in zip(
        stages["C_transaction"][:3], ["candidate_created", "knowledge_written", "accepted"]
    ):
        result[name] = [N07 + f"test_import_checkpoint_rolls_back[{checkpoint}]"]
    result[stages["C_transaction"][3]] = [N07 + "test_controlled_child_termination"]
    for name, boundary in zip(stages["D_io"], ["package", "restore", "export"]):
        result[name] = [N07 + f"test_os_file_faults[{boundary}]"]
    result.update(
        dict(
            zip(
                stages["E_derived"],
                [
                    [
                        "tests/test_n04p03_embedding_sync.py::"
                        "test_provider_failure_marks_embedding_failed_and_preserves_canonical_knowledge"
                    ],
                    [
                        N07 + "test_qdrant_unreachable_is_explicit",
                        "tests/test_hybrid_search_r2.py::"
                        "test_r2_hybrid_degrades_runtime_failure_but_semantic_raises",
                    ],
                    [
                        "tests/test_n04p04_vector_index_sync.py::"
                        "test_vector_backend_failure_marks_failed_and_preserves_canonical_knowledge"
                    ],
                    [
                        "tests/test_n04p03_embedding_sync.py::"
                        "test_embedding_sync_requires_ready_search_representation_without_calling_provider"
                    ],
                    [
                        "tests/test_n04p05_derived_cli.py::"
                        "test_semantic_sync_is_ordered_idempotent_and_status_read_only"
                    ],
                ],
            )
        )
    )
    prefix = "tests/test_generation_lifecycle_r2.py::"
    result.update(
        dict(
            zip(
                stages["F_generation"],
                [
                    [prefix + "test_candidate_build_failure_preserves_active_generation"],
                    [prefix + "test_cutover_rejects_not_ready_generation_without_pointer_change"],
                    [prefix + "test_smoke_failure_recovers_previous_pointer_and_audit"],
                    [
                        prefix
                        + "test_interrupted_build_recovery_marks_only_non_active_builds_failed"
                    ],
                    [
                        "tests/test_generation_lifecycle_qdrant_r2.py::"
                        "test_qdrant_generation_cutover_rollback_and_recutover"
                    ],
                    [prefix + "test_bootstrap_candidate_cutover_rollback_and_recutover"],
                ],
            )
        )
    )
    result.update(
        dict(
            zip(
                stages["G_corruption"],
                [
                    [N07 + "test_exchange_faults[B06]"],
                    [N07 + "test_exchange_faults[B10]"],
                    [N07 + "test_provenance_foreign_key_corruption_detected"],
                    [N07 + "test_recovery_inventory_and_raw_loss"],
                ],
            )
        )
    )
    result.update(
        dict(
            zip(
                stages["H_outage"],
                [
                    [N07 + "test_process_local_network_denial_preserves_read"],
                    [
                        "tests/test_embedding_space.py::"
                        "test_sentence_transformer_loads_all_components_from_pinned_offline_cache"
                    ],
                    [
                        "tests/test_n04p03_embedding_sync.py::"
                        "test_embedding_sync_without_provider_leaves_pending_unattempted"
                    ],
                    [N07 + "test_mcp_stop_direct_read_restart"],
                    [N07 + "test_mcp_stop_direct_read_restart"],
                ],
            )
        )
    )
    for name in stages["I_backup_restore"]:
        result[name] = [N07 + "test_backup_ack_corrupt_and_replacement"]
    for name in [
        "sqlite_online_backup_integrity",
        "separate_backup_destination",
        "restored_canonical_digest_equal",
        "restored_integrity_and_fk_clean",
        "raw_provenance_present_and_verified",
        "minimum_read_and_lexical_recovery",
        "rpo_24h_capability",
        "rto_4h_measured",
    ]:
        result[name] = [N07 + "test_recovery_inventory_and_raw_loss"]
    result["temporary_restore_replacement"] = [N07 + "test_os_file_faults[restore]"]
    result["r2_derived_rebuild_after_restore"] = [N07 + "test_restored_db_r2_rebuild"]
    return result


def provider_probe(run):
    import torch

    from sgokb.retrieval.embedding import default_sentence_transformer_provider

    attempts = []

    def denied(*args, **kwargs):
        attempts.append("socket.connect")
        raise OSError("N07 process-local offline boundary")

    with patch.object(socket.socket, "connect", denied):
        provider = default_sentence_transformer_provider(
            cache_folder=os.environ["N07_MODEL_CACHE"], local_files_only=True
        )
        assert provider.device == "cuda"
        assert provider.space.model == "microsoft/harrier-oss-v1-0.6b"
        assert provider.space.model_revision == "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee"
        assert provider.space.dimension == 1024
        assert provider.space.normalize_embeddings
        assert provider.space.overflow_policy == "reject"
        vectors = provider.embed_queries(["local recovery probe"])
        assert len(vectors[0]) == 1024
        assert torch.isfinite(torch.tensor(vectors)).all()
    result = {
        "status": "PASS" if not attempts else "FAIL",
        "socket_attempts": len(attempts),
        "model": provider.space.model,
        "revision": provider.space.model_revision,
        "device": provider.device,
        "dimension": len(vectors[0]),
        "local_files_only": True,
        "no_cpu_or_cloud_fallback": True,
    }
    write(run / "offline-provider.json", result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--preflight-proof", type=Path)
    parser.add_argument("--provider-proof", action="store_true")
    args = parser.parse_args()
    run = args.run_root.resolve()
    owned_path(ROOT / ".local/n07", run)
    if args.provider_proof:
        provider_probe(run)
        return
    if run.exists():
        raise FileExistsError("Never resume or overwrite formal evidence")
    if git("status", "--porcelain"):
        raise RuntimeError("Formal source must be committed and clean")
    proof = json.loads(args.preflight_proof.read_text(encoding="utf-8"))
    if proof["tested_tree"] != git("rev-parse", "HEAD^{tree}") or not all(
        value == 0 for value in proof["return_codes"].values()
    ):
        raise RuntimeError("Fresh preflight must cover exact measured source tree")
    run.mkdir(parents=True)
    head = git("rev-parse", "HEAD")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    e = {
        "run_id": run.name,
        "execution_head": head,
        "baseline_head": proof["baseline_head"],
        "preflight": {"status": "PASS", **proof},
        "cases": {},
        "gates": {},
    }
    write(run / "status.json", {"stage": "A_baseline", "pid": os.getpid()})
    from qdrant_client import QdrantClient

    client = QdrantClient(url="http://localhost:6333", timeout=30)
    before = originals(args.workspace)
    if not before["databases"][".local/n03/sgokb-n03.sqlite"]["exists"]:
        raise RuntimeError("Required preserved N03 source unavailable")
    vectors_before = reference_vector_snapshot(args.workspace, client)
    inventory_before = {
        c.name: client.count(c.name, exact=True).count for c in client.get_collections().collections
    }
    write(run / "original-before.json", before)
    write(
        run / "qdrant-before.json",
        {"reference_vectors": vectors_before, "collections": inventory_before},
    )
    e["environment"] = {
        "python": platform.python_version(),
        "os": platform.platform(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in [
                "pytest",
                "ruff",
                "torch",
                "transformers",
                "sentence-transformers",
                "qdrant-client",
                "mcp",
            ]
        },
        "free_bytes": shutil.disk_usage(run).free,
    }
    tests = selections(contract)
    try:
        for stage, names in contract["stages"].items():
            for name in names:
                write(run / "status.json", {"stage": stage, "case": name, "pid": os.getpid()})
                label = name
                result = pytest_case(
                    run,
                    label,
                    tests[name],
                    real_provider=name == "r2_derived_rebuild_after_restore",
                )
                e["cases"][name] = result
                observations = []
                for path in sorted((run / label).rglob("*-observation.json")):
                    observations.append(
                        {
                            "path": str(path.relative_to(run)),
                            "data": json.loads(path.read_text(encoding="utf-8")),
                        }
                    )
                result["observations"] = observations
                if (
                    name
                    in {
                        "raw_provenance_present_and_verified",
                        "rpo_24h_capability",
                        "rto_4h_measured",
                    }
                    and result["status"] == "PASS"
                ):
                    coverage = [o["data"] for o in observations if "coverage_verdict" in o["data"]]
                    if not coverage:
                        result["status"] = "BLOCKED"
                    elif any(o["coverage_verdict"] == "FAIL" for o in coverage):
                        result["status"] = "FAIL"
                        result["reason"] = (
                            "Product SQLite backup omits required Raw/Result/config; "
                            "complete-canonical RPO/RTO not achievable from backup"
                        )
                if name == "cached_local_provider_offline_no_cloud_fallback":
                    command = [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--provider-proof",
                        "--run-root",
                        str(run),
                    ]
                    with (run / "offline-provider.log").open("w", encoding="utf-8") as log:
                        rc = subprocess.run(
                            command, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, timeout=180
                        ).returncode
                    if rc or not (run / "offline-provider.json").exists():
                        result["status"] = "BLOCKED"
                    else:
                        result["live_provider"] = json.loads(
                            (run / "offline-provider.json").read_text(encoding="utf-8")
                        )
                        if result["live_provider"]["status"] != "PASS":
                            result["status"] = "FAIL"
                write(run / "evidence.json", e)
                if result["status"] == "BLOCKED":
                    raise RuntimeError("Missing/unjudgeable case evidence: " + name)
    except Exception as exc:
        e["execution_error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        write(run / "status.json", {"stage": "J_post_regression", "pid": os.getpid()})
        return_codes = {}
        commands = {
            "focused": [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_n07_failure_recovery.py",
                "--basetemp",
                str(run / "post-focused-fixtures"),
            ],
            "full": [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--basetemp",
                str(run / "post-full-fixtures"),
            ],
            "ruff": [sys.executable, "-m", "ruff", "check", "."],
            "diff": ["git", "diff", "--check"],
        }
        for name, command in commands.items():
            with (run / ("post-" + name + ".log")).open("w", encoding="utf-8") as log:
                return_codes[name] = subprocess.run(
                    command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT
                ).returncode
        after = originals(args.workspace)
        vectors_after = reference_vector_snapshot(args.workspace, client)
        inventory_after = {
            c.name: client.count(c.name, exact=True).count
            for c in client.get_collections().collections
        }
        write(run / "original-after.json", after)
        write(
            run / "qdrant-after.json",
            {"reference_vectors": vectors_after, "collections": inventory_after},
        )
        client.close()
        import psutil

        leftover = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            try:
                command_line = " ".join(process.info["cmdline"] or [])
                if process.pid != os.getpid() and str(run).lower() in command_line.lower():
                    leftover.append(process.pid)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        write(run / "run-owned-process-audit.json", {"remaining_pids": leftover})
        checks = {
            "no_run_owned_processes": not leftover,
            "original_assets": before == after,
            "reference_vectors": vectors_before == vectors_after,
            "reference_inventory": inventory_before == inventory_after,
            "head": head == git("rev-parse", "HEAD"),
            "tracked": git("status", "--porcelain") == "",
        }
        e["safety"] = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
        e["post_regression"] = {
            "status": "PASS" if not any(return_codes.values()) else "FAIL",
            "return_codes": return_codes,
        }

        # Gates derive only from complete measured case groups, never optimistic defaults.
        def case_pass(name):
            return e["cases"].get(name, {}).get("status") == "PASS"

        groups = {
            "mandatory_invalid_inputs_rejected_fraction": (
                contract["stages"]["B_exchange_input"],
                1.0,
            ),
            "partial_accepted_versions_after_transaction_fault": (
                contract["stages"]["C_transaction"][:3],
                0,
            ),
            "successful_import_rows_after_transaction_rollback": (
                contract["stages"]["C_transaction"][:3],
                0,
            ),
            "finalized_partial_file_artifacts": (contract["stages"]["D_io"], 0),
            "silent_provider_cloud_cpu_backend_fallbacks": (contract["stages"]["H_outage"][:3], 0),
            "failed_generation_transition_active_pointer_changes": (
                contract["stages"]["F_generation"][:4],
                0,
            ),
            "canonical_corruption_from_derived_failure": (contract["stages"]["E_derived"], 0),
            "mandatory_corruption_detection_fraction": (contract["stages"]["G_corruption"], 1.0),
            "restored_canonical_digest_equal": (["restored_canonical_digest_equal"], True),
            "restored_integrity_ok": (["restored_integrity_and_fk_clean"], True),
            "restored_foreign_key_violations": (["restored_integrity_and_fk_clean"], 0),
            "minimum_restored_local_read": (["minimum_read_and_lexical_recovery"], True),
            "minimum_restored_lexical_retrieval": (["minimum_read_and_lexical_recovery"], True),
            "post_restore_r2_rebuild_audit": (["r2_derived_rebuild_after_restore"], True),
        }
        for name, (names, success) in groups.items():
            if all(case_pass(n) for n in names):
                e["gates"][name] = success
        e["gates"]["original_reference_asset_mutations"] = 0 if all(checks.values()) else 1
        raw_case = e["cases"].get("raw_provenance_present_and_verified", {})
        if raw_case.get("status") in {"PASS", "FAIL"}:
            e["gates"]["raw_provenance_restore_verification"] = raw_case["status"] == "PASS"
        # Complete canonical RPO/RTO are deliberately null when required Raw is not restored.
        e["gates"]["rpo_hours_max"] = None
        e["gates"]["rto_hours_max"] = None
        write(run / "evidence.json", e)
        verdict = evaluate(e, contract)
        write(run / "evaluation.json", verdict)
        write(
            run / "status.json",
            {
                "stage": "formal_finished_awaiting_review",
                "overall": verdict["overall"],
                "pid": os.getpid(),
                "execution_error": e.get("execution_error"),
            },
        )


if __name__ == "__main__":
    main()
