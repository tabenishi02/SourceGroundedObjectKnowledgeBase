"""N07-R01 product-level re-acceptance and deterministic frozen-contract evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(Path(__file__).parent)]

from sgokb import composite_recovery as recovery  # noqa: E402
from sgokb.application import Application  # noqa: E402
from sgokb.application_read import KnowledgeReadApplication  # noqa: E402
from sgokb.exchange.result_import import load_immutable_result_artifact  # noqa: E402
from sgokb.repository import Repository  # noqa: E402
from sgokb.storage import PackageExchangeAuditRepository  # noqa: E402

CONTRACT = ROOT / "benchmark/n07-r01-composite-backup-restore-contract-v1.json"
NEGATIVES = [
    "missing_raw",
    "missing_result",
    "raw_hash",
    "result_hash",
    "manifest_traversal",
    "incomplete",
    "overlapping_targets",
    "overwrite_without_ack",
]


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return recovery._sha256(path)


def canonical_tables(db):
    result = {}
    for (name,) in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        quoted = '"' + name.replace('"', '""') + '"'
        cursor = db.execute("SELECT * FROM " + quoted)
        columns = [item[0] for item in cursor.description]
        rows = []
        for row in cursor:
            values = list(row)
            if name == "raw_artifacts":
                values[columns.index("storage_ref")] = "<relocated Raw reference>"
            rows.append(
                json.dumps(values, ensure_ascii=True, default=lambda value: {"bytes": value.hex()})
            )
        result[name] = hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()
    return result


def product_drill(fixture, directory):
    """All source and destructive targets must be newly-created disposable fixture paths."""
    directory = directory.resolve()
    repo = fixture["repo"]
    bundle, incoming = fixture["bundle"], fixture["incoming"]
    if not bundle.resolve().is_relative_to(directory) or not incoming.resolve().is_relative_to(
        directory
    ):
        raise ValueError("Fixture stores must belong to the disposable drill root")
    before = canonical_tables(repo.db)
    import_rows = [
        dict(row) for row in repo.db.execute("SELECT * FROM object_result_imports ORDER BY id")
    ]
    read_before = KnowledgeReadApplication(repo).get_object(fixture["object_id"])
    backup = directory / "complete-backups" / "generation-one"
    creation_started = datetime.now(timezone.utc)
    start = time.perf_counter()
    created = recovery.create_composite_backup(repo, incoming_root=incoming, output=backup)
    backup_seconds = time.perf_counter() - start
    verified = recovery.verify_composite_backup(backup)
    second = recovery.create_composite_backup(
        repo, incoming_root=incoming, root=directory / "complete-backups"
    )
    assert second["generation_id"] != created["generation_id"]
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    backup_files = {str(p.relative_to(backup)): sha(p) for p in backup.rglob("*") if p.is_file()}
    bundle.rename(bundle.with_name(bundle.name + ".quarantined"))
    incoming.rename(incoming.with_name(incoming.name + ".quarantined"))
    assert not bundle.exists() and not incoming.exists()
    db_target = directory / "alternate" / "canonical.sqlite"
    raw_root = directory / "alternate-raw"
    incoming_root = directory / "alternate-incoming"
    restore_started = datetime.now(timezone.utc)
    timer = time.perf_counter()
    restored_result = recovery.composite_restore_apply(
        backup, db_target=db_target, raw_root=raw_root, incoming_root=incoming_root
    )
    restore_copy_seconds = time.perf_counter() - timer
    restored = Repository(db_target)
    try:
        identities_equal = canonical_tables(restored.db) == before
        imports_equal = import_rows == [
            dict(row)
            for row in restored.db.execute("SELECT * FROM object_result_imports ORDER BY id")
        ]
        assert identities_equal and imports_equal
        assert restored.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not restored.db.execute("PRAGMA foreign_key_check").fetchall()
        refs = {
            Path(row[0]) for row in restored.db.execute("SELECT storage_ref FROM raw_artifacts")
        }
        assert refs and all(p.is_relative_to(raw_root.resolve()) and p.exists() for p in refs)
        assert next(iter(refs)).name == bundle.name
        processed = Application(restored).process_source_snapshot(fixture["snapshot_id"])
        assert processed["snapshot"] == fixture["snapshot_id"]
        receipt = PackageExchangeAuditRepository(restored.db).result_receipt(fixture["receipt_id"])
        parsed, digest, count = load_immutable_result_artifact(receipt, incoming_root)
        assert (
            digest == import_rows[0]["result_sha256"]
            and count == import_rows[0]["result_byte_count"]
        )
        assert parsed["target"]["object_id"] == fixture["object_id"]
        assert KnowledgeReadApplication(restored).get_object(fixture["object_id"]) == read_before
        lexical = KnowledgeReadApplication(restored).search_objects("Alice Example", mode="lexical")
        assert fixture["object_id"] in {hit.object_id for hit in lexical.results}
        metadata_path = Path(restored_result["recovery_metadata"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata == recovery._recovery_metadata()
        assert str(bundle.parent.resolve()) not in metadata_path.read_text(encoding="utf-8")
        assert str(incoming.resolve()) not in metadata_path.read_text(encoding="utf-8")
        canonical_rto = time.perf_counter() - timer
        rpo_hours = (datetime.now(timezone.utc) - creation_started).total_seconds() / 3600
    finally:
        restored.close()
    assert backup_files == {
        str(p.relative_to(backup)): sha(p) for p in backup.rglob("*") if p.is_file()
    }
    negative = {}
    for name in NEGATIVES:
        copied = directory / "negative" / name
        copied.parent.mkdir(exist_ok=True)
        shutil.copytree(backup, copied)
        raw_path = copied / manifest["raw"][0]["path"]
        result_path = copied / manifest["provenance"][0]["path"]
        try:
            if name == "missing_raw":
                raw_path.unlink()
            elif name == "missing_result":
                result_path.unlink()
            elif name in {"raw_hash", "result_hash"}:
                path = raw_path if name == "raw_hash" else result_path
                path.write_bytes(path.read_bytes() + b"corrupt")
            elif name == "manifest_traversal":
                changed = json.loads((copied / "manifest.json").read_text(encoding="utf-8"))
                changed["raw"][0]["path"] = "../escape.zip"
                write(copied / "manifest.json", changed)
            elif name == "incomplete":
                (copied / "manifest.json").unlink()
            elif name == "overlapping_targets":
                recovery.composite_restore_plan(
                    copied,
                    db_target=directory / "overlap/db.sqlite",
                    raw_root=directory / "overlap",
                    incoming_root=directory / "overlap-incoming",
                )
            else:
                recovery.composite_restore_apply(
                    copied, db_target=db_target, raw_root=raw_root, incoming_root=incoming_root
                )
            if name not in {"overlapping_targets", "overwrite_without_ack"}:
                recovery.verify_composite_backup(copied)
        except (ValueError, OSError, RuntimeError) as exc:
            negative[name] = {"status": "PASS", "exception_type": type(exc).__name__}
        else:
            negative[name] = {"status": "FAIL"}
    proof = {
        "backup_generation_id": created["generation_id"],
        "creation_started_utc": creation_started.isoformat(),
        "created_at": created["created_at"],
        "restore_started_utc": restore_started.isoformat(),
        "backup_seconds": backup_seconds,
        "restore_copy_seconds": restore_copy_seconds,
        "canonical_rto_seconds": canonical_rto,
        "complete_canonical_rpo_hours": rpo_hours,
        "rpo_daily_equivalent_generations": 2,
        "rpo_basis": "age since conservative backup start; two independently verified generations",
        "verification": verified,
        "canonical_sqlite": manifest["canonical"],
        "raw_bundles": len(manifest["raw"]),
        "original_results": len(manifest["provenance"]),
        "manifest_sha256": sha(backup / "manifest.json"),
        "recovery_metadata": manifest["recovery_metadata"],
        "source_stores_quarantined": True,
        "backup_unchanged": True,
        "raw_basename_preserved": True,
        "only_raw_storage_ref_relocated": identities_equal,
        "accepted_result_audit_unchanged": imports_equal,
        "negative_drills": negative,
        "product_proofs": {
            name: True
            for name in [
                "restored_canonical_read",
                "restored_raw_reprocessing",
                "restored_original_result_open",
                "sqlite_integrity",
                "sqlite_foreign_key_integrity",
                "provenance_identity_equal",
                "content_hashes_equal",
            ]
        },
        "minimum_lexical_retrieval": True,
        "recovery_metadata_verified": True,
    }
    write(directory / "formal-proof.json", proof)
    return proof


def evaluate(evidence):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    failed, blocked = [], []
    proof = evidence.get("proof", {})
    for name in contract["acceptance"]["required_product_proofs"]:
        value = proof.get("product_proofs", {}).get(name)
        (blocked if value is None else failed if value is not True else []).append(name)
    for key, maximum in [
        (
            "complete_canonical_rpo_hours",
            contract["acceptance"]["complete_canonical_rpo_max_hours"],
        ),
        ("canonical_rto_seconds", contract["acceptance"]["canonical_restore_rto_max_seconds"]),
    ]:
        value = proof.get(key)
        if value is None:
            blocked.append(key)
        elif (
            type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= maximum
        ):
            failed.append(key)
    for name in NEGATIVES:
        status = proof.get("negative_drills", {}).get(name, {}).get("status")
        if status != "PASS":
            (failed if status == "FAIL" else blocked).append(name)
    for name in [
        "source_stores_quarantined",
        "backup_unchanged",
        "raw_basename_preserved",
        "only_raw_storage_ref_relocated",
        "accepted_result_audit_unchanged",
        "minimum_lexical_retrieval",
        "recovery_metadata_verified",
    ]:
        value = proof.get(name)
        if value is not True:
            (blocked if value is None else failed).append(name)
    for name in ["preflight", "formal_tests", "derived_rebuild", "post_regression", "safety"]:
        status = evidence.get(name, {}).get("status")
        if status != "PASS":
            (failed if status == "FAIL" else blocked).append(name)
    return {
        "overall": "FAIL" if failed else "BLOCKED" if blocked else "PASS",
        "failures": sorted(set(failed)),
        "blocked": sorted(set(blocked)),
    }


def pytest_case(run, label, selectors):
    if label != "product-drill" or not run.resolve().is_relative_to(ROOT / ".local/n07-r01"):
        raise ValueError("Formal test targets must belong to the N07-R01 run")
    (run / label).mkdir(exist_ok=False)
    xml = run / (label + ".xml")
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *selectors,
        "--basetemp",
        str(run / label / "fixtures"),
        "--junitxml",
        str(xml),
    ]
    with (run / (label + ".log")).open("w", encoding="utf-8") as stream:
        rc = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT).returncode
    cases = list(ET.parse(xml).iter("testcase")) if xml.exists() else []
    errors = sum(c.find("error") is not None for c in cases)
    failed = sum(c.find("failure") is not None for c in cases)
    skipped = sum(c.find("skipped") is not None for c in cases)
    return {
        "status": "BLOCKED"
        if errors or skipped or not cases
        else "FAIL"
        if rc or failed
        else "PASS",
        "return_code": rc,
        "passed": len(cases) - errors - failed - skipped,
        "failed": failed,
        "setup_errors": errors,
        "skipped": skipped,
    }


def restored_derived_rebuild(run, db_path):
    """Rebuild actual restored fixture via existing APIs, not a separate synthetic DB."""
    if not db_path.resolve().is_relative_to(run.resolve()):
        raise ValueError("Derived rebuild target must belong to this formal run")
    from qdrant_client import QdrantClient

    from sgokb.application_generation import KnowledgeSearchGenerationApplication
    from sgokb.application_maintenance import DerivedSearchMaintenanceApplication
    from sgokb.rendering import MarkdownRenderService
    from sgokb.retrieval.embedding import default_sentence_transformer_provider
    from sgokb.retrieval.generation import route_generation_vector_index
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    repo = Repository(db_path)
    before = {
        k: v
        for k, v in canonical_tables(repo.db).items()
        if not k.startswith(("search_", "knowledge_search", "object_derived"))
    }
    client = QdrantClient(location=":memory:")
    start = time.perf_counter()
    try:
        provider = default_sentence_transformer_provider(
            cache_folder=os.environ["N07_MODEL_CACHE"], local_files_only=True
        )
        assert provider.device == "cuda"
        provider.batch_size = 1
        index = QdrantVectorIndexAdapter(client=client, wait_for_index=False)
        maintenance = DerivedSearchMaintenanceApplication(
            repo, embedding_provider=provider, vector_index=index
        )
        objects = repo.rows(
            "SELECT id,current_version_id FROM objects WHERE current_version_id IS NOT NULL"
        )
        for obj in objects:
            maintenance.sync_search_representation(obj["id"])
            maintenance.sync_embedding(obj["id"])
        for obj in objects:
            maintenance.sync_vector_index(obj["id"])
        generation = KnowledgeSearchGenerationApplication(
            repo, embedding_provider=provider, vector_index=index
        )
        active = repo.one(
            "SELECT g.* FROM knowledge_search_active_generation a "
            "JOIN knowledge_search_generations g ON g.id=a.active_generation_id"
        )
        assert active and active["contract_key"] == "n05d04r2-hierarchical-v2"
        generation_id = active["id"]
        generation.refresh_active_generation(generation_id)
        kinds = {
            row[0]
            for row in repo.db.execute(
                "SELECT m.target_kind FROM knowledge_search_generation_memberships gm "
                "JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id "
                "WHERE gm.generation_id=?",
                (generation_id,),
            )
        }
        membership_count = len(generation._generation_membership_rows(generation_id))
        binding = repo.one(
            "SELECT * FROM knowledge_search_generation_vector_indexes WHERE generation_id=?",
            (generation_id,),
        )
        assert binding and binding["point_count"] == membership_count
        assert kinds <= {"object_overview", "facet", "statement"} and "object_overall" not in kinds
        routed = route_generation_vector_index(repo, index)
        reader = KnowledgeReadApplication(repo, embedding_provider=provider, vector_index=routed)
        assert reader.search_objects("Alice Example", mode="semantic").results
        for obj in objects:
            MarkdownRenderService(repo).render_version(
                obj["current_version_id"], output_root=run / "rendered"
            )
        after = {
            k: v
            for k, v in canonical_tables(repo.db).items()
            if not k.startswith(("search_", "knowledge_search", "object_derived"))
        }
        assert before == after
        result = {
            "status": "PASS",
            "seconds_including_provider_load": time.perf_counter() - start,
            "generation_id": generation_id,
            "membership_count": membership_count,
            "point_count": binding["point_count"],
            "family": sorted(kinds),
            "object_overall_leakage": 0,
            "canonical_unchanged": True,
            "semantic_read": True,
            "render": True,
            "model": provider.space.model,
            "revision": provider.space.model_revision,
            "device": provider.device,
            "dimension": provider.space.dimension,
            "vector_backend": "real Qdrant in-memory, run-owned only",
        }
        write(run / "derived-proof.json", result)
    finally:
        repo.close()
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--preflight-proof", type=Path)
    parser.add_argument("--derived-proof", type=Path)
    args = parser.parse_args()
    run = args.run_root.resolve()
    if args.derived_proof is not None:
        if not run.is_relative_to(ROOT / ".local/n07-r01"):
            raise ValueError("Owned N07-R01 root required")
        restored_derived_rebuild(run, args.derived_proof)
        return
    if args.workspace is None or args.preflight_proof is None:
        raise ValueError("Workspace baseline and preflight proof required")
    if not run.is_relative_to(ROOT / ".local/n07-r01") or run.exists():
        raise ValueError("Unique fresh N07-R01 run root required")

    def git(*parts):
        return subprocess.check_output(["git", *parts], cwd=ROOT, encoding="utf-8").strip()

    if git("status", "--porcelain"):
        raise RuntimeError("Formal measurement requires a committed clean source")
    preflight = json.loads(args.preflight_proof.read_text(encoding="utf-8"))
    if preflight["tested_tree"] != git("rev-parse", "HEAD^{tree}") or any(
        preflight["return_codes"].values()
    ):
        raise RuntimeError("Fresh preflight must cover exact measured tree")
    run.mkdir(parents=True)
    from n07_failure_recovery import originals, reference_vector_snapshot
    from qdrant_client import QdrantClient

    baseline = originals(args.workspace)
    client = QdrantClient(url="http://localhost:6333", timeout=30)
    vectors = reference_vector_snapshot(args.workspace, client)
    counts = {
        c.name: client.count(c.name, exact=True).count for c in client.get_collections().collections
    }
    write(run / "original-before.json", baseline)
    write(run / "reference-before.json", {"vectors": vectors, "counts": counts})
    head = git("rev-parse", "HEAD")
    main_before = git("rev-parse", "main")
    evidence = {
        "run_id": run.name,
        "execution_head": head,
        "preflight": {"status": "PASS", **preflight},
    }

    def command(name, argv):
        with (run / (name + ".log")).open("w", encoding="utf-8") as stream:
            return subprocess.run(
                argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT
            ).returncode

    try:
        write(run / "status.json", {"stage": "formal_drill", "pid": os.getpid()})
        evidence["formal_tests"] = pytest_case(
            run, "product-drill", ["tests/test_n07_r01_composite_recovery.py"]
        )
        proofs = list((run / "product-drill").rglob("formal-proof.json"))
        if len(proofs) == 1:
            evidence["proof"] = json.loads(proofs[0].read_text(encoding="utf-8"))
        write(run / "evidence.json", evidence)
        write(run / "status.json", {"stage": "separate_derived_rebuild", "pid": os.getpid()})
        if len(proofs) != 1:
            raise RuntimeError("Exactly one complete product drill proof is required")
        restored_db = proofs[0].parent / "alternate/canonical.sqlite"
        rc = command(
            "derived",
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--run-root",
                str(run),
                "--derived-proof",
                str(restored_db),
            ],
        )
        if rc == 0 and (run / "derived-proof.json").is_file():
            evidence["derived_rebuild"] = json.loads(
                (run / "derived-proof.json").read_text(encoding="utf-8")
            )
        else:
            evidence["derived_rebuild"] = {"status": "BLOCKED", "return_code": rc}
    except Exception as exc:
        evidence["execution_error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        write(run / "status.json", {"stage": "post_run_regression", "pid": os.getpid()})
        commands = {
            "focused": [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_n07_r01_composite_recovery.py",
                "tests/test_n07_failure_recovery.py",
                "--basetemp",
                str(run / "post-focused"),
            ],
            "full": [sys.executable, "-m", "pytest", "-q", "--basetemp", str(run / "post-full")],
            "ruff": [sys.executable, "-m", "ruff", "check", "."],
            "diff": ["git", "diff", "--check"],
        }
        codes = {name: command("post-" + name, argv) for name, argv in commands.items()}
        evidence["post_regression"] = {
            "status": "PASS" if not any(codes.values()) else "FAIL",
            "return_codes": codes,
        }
        after = originals(args.workspace)
        after_vectors = reference_vector_snapshot(args.workspace, client)
        after_counts = {
            c.name: client.count(c.name, exact=True).count
            for c in client.get_collections().collections
        }
        client.close()
        write(run / "original-after.json", after)
        write(run / "reference-after.json", {"vectors": after_vectors, "counts": after_counts})
        import psutil

        ancestors = {process.pid for process in psutil.Process().parents()} | {os.getpid()}
        leftover = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            try:
                if (
                    process.pid not in ancestors
                    and str(run).lower() in " ".join(process.info["cmdline"] or []).lower()
                ):
                    leftover.append(process.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        write(run / "process-audit.json", {"remaining_pids": leftover})
        safety = {
            "no_run_owned_processes": not leftover,
            "local_main_unchanged": main_before == git("rev-parse", "main"),
            "original_assets": baseline == after,
            "reference_vectors": vectors == after_vectors,
            "reference_inventory": counts == after_counts,
            "head_unchanged": head == git("rev-parse", "HEAD"),
            "tracked_unchanged": not git("status", "--porcelain"),
        }
        evidence["safety"] = {
            "status": "PASS" if all(safety.values()) else "FAIL",
            "checks": safety,
        }
        write(run / "evidence.json", evidence)
        result = evaluate(evidence)
        write(run / "evaluation.json", result)
        write(
            run / "status.json",
            {
                "stage": "formal_finished_awaiting_review",
                "overall": result["overall"],
                "pid": os.getpid(),
                "execution_error": evidence.get("execution_error"),
            },
        )


if __name__ == "__main__":
    main()
