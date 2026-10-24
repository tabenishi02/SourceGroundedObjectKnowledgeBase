"""N07-R01 complete canonical composite backup and restore.

The legacy SQLite-only backup API in :mod:`sgokb.system_ops` intentionally keeps
its existing semantics.  This module adds an explicit complete-canonical
boundary: SQLite + Raw Web Capture bundles + accepted immutable Result inputs +
non-secret recovery metadata.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import uuid
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .ingestion import WebCaptureImporter

COMPOSITE_BACKUP_SCHEMA = "sgokb.composite-backup.v1"
RECOVERY_METADATA_SCHEMA = "sgokb.composite-recovery-metadata.v1"
CANONICAL_REL = "canonical/canonical.sqlite"
RECOVERY_REL = "metadata/recovery.json"
MANIFEST_NAME = "manifest.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_identity(path: Path) -> dict[str, object]:
    return {"sha256": _sha256(path), "bytes": path.stat().st_size}


def _safe_posix_relative(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Composite path must be a non-empty POSIX relative path")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("Composite path contains empty, dot or parent segment")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("Composite path must not be absolute or contain traversal")
    if any(":" in part for part in path.parts):
        raise ValueError("Composite path contains an unsafe path segment")
    for part in path.parts:
        base = part.split(".")[0].upper()
        if (
            "\x00" in part
            or part.endswith((".", " "))
            or base
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)],
            }
        ):
            raise ValueError("Composite path contains an unsafe Windows segment")
    return path


def _no_links(path: Path) -> Path:
    """Check lexical path components before resolve can hide links/junctions."""
    path = path.absolute()
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("Composite paths must not traverse symlinks")
        if component.exists() and getattr(component.lstat(), "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        ):
            raise ValueError("Composite paths must not traverse reparse points")
    return path.resolve()


def _safe_segment(value: str, label: str) -> str:
    if (
        not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or ":" in value
        or "\x00" in value
    ):
        raise ValueError(f"Unsafe {label}")
    return value


def _package_path(root: Path, relative: str) -> Path:
    rel = _safe_posix_relative(relative)
    root = _no_links(root)
    target = _no_links(root / Path(*rel.parts))
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Composite path escapes backup root") from exc
    return target


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular non-symlink file")
    return path


def _sqlite_connection(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    connection = (
        sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        if readonly
        else sqlite3.connect(path)
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _sqlite_integrity(path: Path) -> dict[str, object]:
    connection = _sqlite_connection(path, readonly=True)
    try:
        integrity_rows = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        foreign_keys = [list(row) for row in connection.execute("PRAGMA foreign_key_check")]
    finally:
        connection.close()
    if integrity_rows != ["ok"] or foreign_keys:
        raise RuntimeError("Composite SQLite snapshot failed integrity checks")
    return {"integrity_check": integrity_rows, "foreign_key_violations": foreign_keys}


def _create_sqlite_snapshot(repository, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    target = sqlite3.connect(destination)
    try:
        repository.db.backup(target)
        target.execute("PRAGMA journal_mode=DELETE")
    finally:
        target.close()
    _sqlite_integrity(destination)


def _snapshot_raw_inventory(connection: sqlite3.Connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """SELECT a.id,a.snapshot_id,a.artifact_kind,a.logical_path,a.storage_ref,
                  a.media_type,a.sha256,a.bytes,s.metadata_json
           FROM raw_artifacts a
           JOIN source_snapshots s ON s.id=a.snapshot_id
           ORDER BY a.snapshot_id,a.id"""
    ).fetchall()
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[str(row["snapshot_id"])].append(row)

    result: list[dict[str, object]] = []
    importer = WebCaptureImporter()
    for snapshot_id, members in sorted(grouped.items()):
        refs = {str(row["storage_ref"]) for row in members}
        if len(refs) != 1:
            raise ValueError(f"Raw Snapshot {snapshot_id} has multiple physical storage refs")
        source = _regular_file(_no_links(Path(next(iter(refs)))), "Raw Web Capture bundle")
        bundle = importer.read(source)
        if str(bundle.manifest.get("capture_id")) != snapshot_id:
            raise ValueError("Raw Web Capture capture_id does not match canonical Snapshot")
        metadata = json.loads(str(members[0]["metadata_json"]))
        expected_bundle_sha = metadata.get("bundle_sha256")
        if not isinstance(expected_bundle_sha, str) or bundle.sha256 != expected_bundle_sha:
            raise ValueError("Raw Web Capture physical SHA-256 does not match Snapshot metadata")
        for row in members:
            logical_path = row["logical_path"]
            if not isinstance(logical_path, str) or logical_path not in bundle.artifacts:
                raise ValueError("Canonical Raw logical artifact is missing from physical bundle")
            raw = bundle.artifacts[logical_path]
            if len(raw) != int(row["bytes"]):
                raise ValueError("Canonical Raw logical artifact byte count drift")
            if hashlib.sha256(raw).hexdigest() != str(row["sha256"]):
                raise ValueError("Canonical Raw logical artifact SHA-256 drift")
        result.append(
            {
                "snapshot_id": snapshot_id,
                "source": source,
                "basename": source.name,
                "sha256": bundle.sha256,
                "bytes": source.stat().st_size,
                "logical_artifact_count": len(members),
            }
        )
    return result


def _safe_result_source(incoming_root: Path, storage_ref: str) -> Path:
    rel = _safe_posix_relative(storage_ref)
    if rel.name != "result.json":
        raise ValueError("Accepted Result storage reference must end in result.json")
    root = _no_links(incoming_root)
    source = _no_links(root / Path(*rel.parts))
    try:
        source.relative_to(root)
    except ValueError as exc:
        raise ValueError("Accepted Result storage reference escapes incoming root") from exc
    return _regular_file(source, "Accepted immutable Result")


def _snapshot_result_inventory(
    connection: sqlite3.Connection, incoming_root: Path
) -> list[dict[str, object]]:
    rows = connection.execute(
        """SELECT i.id AS import_id,i.receipt_id,i.result_storage_ref,i.result_sha256,
                  i.result_byte_count,r.storage_ref AS receipt_storage_ref,
                  r.result_sha256 AS receipt_sha256,r.byte_count AS receipt_byte_count
           FROM object_result_imports i
           JOIN package_result_receipts r ON r.id=i.receipt_id
           ORDER BY i.id"""
    ).fetchall()
    seen_refs: dict[str, tuple[str, int]] = {}
    result: list[dict[str, object]] = []
    for row in rows:
        storage_ref = str(row["result_storage_ref"])
        if storage_ref != str(row["receipt_storage_ref"]):
            raise ValueError("Accepted Result import and receipt storage refs disagree")
        sha256 = str(row["result_sha256"])
        byte_count = int(row["result_byte_count"])
        if sha256 != str(row["receipt_sha256"]) or byte_count != int(row["receipt_byte_count"]):
            raise ValueError("Accepted Result import and receipt identities disagree")
        source = _safe_result_source(incoming_root, storage_ref)
        raw = source.read_bytes()
        if len(raw) != byte_count or hashlib.sha256(raw).hexdigest() != sha256:
            raise ValueError("Accepted immutable Result bytes no longer match canonical audit")
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Accepted immutable Result is no longer valid UTF-8 JSON") from exc
        if not isinstance(parsed, Mapping):
            raise ValueError("Accepted immutable Result top level must be a JSON object")
        previous = seen_refs.get(storage_ref)
        identity = (sha256, byte_count)
        if previous is not None and previous != identity:
            raise ValueError("One Result storage ref resolves to conflicting canonical identities")
        seen_refs[storage_ref] = identity
        result.append(
            {
                "import_id": str(row["import_id"]),
                "receipt_id": str(row["receipt_id"]),
                "storage_ref": storage_ref,
                "source": source,
                "sha256": sha256,
                "bytes": byte_count,
            }
        )
    return result


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _recovery_metadata() -> dict[str, object]:
    return {
        "schema": RECOVERY_METADATA_SCHEMA,
        "raw_relocation_strategy": "rewrite raw_artifacts.storage_ref by snapshot_id",
        "result_relative_root_strategy": "preserve accepted incoming-root-relative storage_ref",
        "rebuildable_derived_classification": [
            "search_representation",
            "embedding",
            "vector_index",
            "render",
        ],
        "plaintext_secrets_included": False,
        "original_absolute_roots_included": False,
    }


def _default_generation(root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / f"composite-{stamp}-{uuid.uuid4().hex[:12]}"


def create_composite_backup(
    repository,
    *,
    incoming_root: str | Path,
    output: str | Path | None = None,
    root: str | Path = Path("backups"),
) -> dict[str, object]:
    """Create one complete-canonical backup generation from a SQLite consistency point."""

    output_path = Path(output) if output is not None else _default_generation(Path(root))
    output_path = _no_links(output_path)
    if output_path.exists():
        raise FileExistsError(f"Composite backup target already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stage = output_path.parent / f".{output_path.name}.staging-{uuid.uuid4().hex}"
    if stage.exists():
        raise FileExistsError(f"Composite staging path already exists: {stage}")

    try:
        stage.mkdir()
        canonical = stage / Path(*PurePosixPath(CANONICAL_REL).parts)
        _create_sqlite_snapshot(repository, canonical)

        snapshot = _sqlite_connection(canonical, readonly=True)
        try:
            raw_inventory = _snapshot_raw_inventory(snapshot)
            result_inventory = _snapshot_result_inventory(snapshot, Path(incoming_root))
        finally:
            snapshot.close()

        raw_entries: list[dict[str, object]] = []
        for item in raw_inventory:
            snapshot_id = _safe_segment(str(item["snapshot_id"]), "Raw Snapshot ID")
            basename = _safe_segment(str(item["basename"]), "Raw bundle basename")
            relative = PurePosixPath("raw") / snapshot_id / basename
            destination = stage / Path(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(item["source"]), destination)
            identity = _file_identity(destination)
            if identity["sha256"] != item["sha256"] or identity["bytes"] != item["bytes"]:
                raise ValueError("Raw Web Capture copy integrity verification failed")
            # The importer validates member checksums and the timestamp/UUID filename contract.
            WebCaptureImporter().read(destination)
            raw_entries.append(
                {
                    "snapshot_id": item["snapshot_id"],
                    "path": relative.as_posix(),
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "logical_artifact_count": item["logical_artifact_count"],
                }
            )

        result_entries: list[dict[str, object]] = []
        copied_results: dict[str, tuple[str, int]] = {}
        for item in result_inventory:
            storage_ref = _safe_posix_relative(str(item["storage_ref"]))
            relative = PurePosixPath("provenance") / storage_ref
            identity_tuple = (str(item["sha256"]), int(item["bytes"]))
            existing = copied_results.get(storage_ref.as_posix())
            if existing is None:
                destination = stage / Path(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(item["source"]), destination)
                identity = _file_identity(destination)
                if (identity["sha256"], identity["bytes"]) != identity_tuple:
                    raise ValueError("Accepted Result copy integrity verification failed")
                copied_results[storage_ref.as_posix()] = identity_tuple
            elif existing != identity_tuple:
                raise ValueError("Conflicting accepted Result identities share one storage ref")
            result_entries.append(
                {
                    "import_id": item["import_id"],
                    "receipt_id": item["receipt_id"],
                    "storage_ref": storage_ref.as_posix(),
                    "path": relative.as_posix(),
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                }
            )

        recovery = stage / Path(*PurePosixPath(RECOVERY_REL).parts)
        _write_json(recovery, _recovery_metadata())
        manifest = {
            "schema": COMPOSITE_BACKUP_SCHEMA,
            "generation_id": str(uuid.uuid4()),
            "created_at": _now(),
            "consistency_model": "sqlite_online_backup_then_inventory_from_snapshot",
            "canonical": {
                "path": CANONICAL_REL,
                **_file_identity(canonical),
            },
            "raw": raw_entries,
            "provenance": result_entries,
            "recovery_metadata": {
                "path": RECOVERY_REL,
                **_file_identity(recovery),
            },
        }
        _write_json(stage / MANIFEST_NAME, manifest)
        _verify_composite_backup(stage)
        os.replace(stage, output_path)
        verified = verify_composite_backup(output_path)
        return {
            "created": True,
            "path": str(output_path),
            "generation_id": manifest["generation_id"],
            "created_at": manifest["created_at"],
            "raw_bundles": len(raw_entries),
            "original_results": len(result_entries),
            "verification": verified,
        }
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _load_manifest(root: Path) -> dict[str, object]:
    manifest_path = _regular_file(root / MANIFEST_NAME, "Composite manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Composite manifest is not valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != COMPOSITE_BACKUP_SCHEMA:
        raise ValueError("Unsupported composite backup schema")
    expected = {
        "schema",
        "generation_id",
        "created_at",
        "consistency_model",
        "canonical",
        "raw",
        "provenance",
        "recovery_metadata",
    }
    if set(manifest) != expected:
        raise ValueError("Composite manifest has missing or unexpected fields")
    try:
        uuid.UUID(manifest["generation_id"])
        created = datetime.fromisoformat(manifest["created_at"])
        if created.utcoffset() is None:
            raise ValueError("Composite creation timestamp must have timezone")
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Composite manifest generation/time identity is invalid") from exc
    if manifest["consistency_model"] != "sqlite_online_backup_then_inventory_from_snapshot":
        raise ValueError("Unsupported composite consistency model")
    return manifest


def _verify_declared_file(root: Path, entry: Mapping[str, object], label: str) -> Path:
    relative = str(entry.get("path", ""))
    path = _regular_file(_package_path(root, relative), label)
    identity = _file_identity(path)
    if identity["sha256"] != entry.get("sha256") or identity["bytes"] != entry.get("bytes"):
        raise ValueError(f"{label} hash or byte count mismatch")
    return path


def _verify_snapshot_closure(
    canonical: Path,
    root: Path,
    manifest: Mapping[str, object],
) -> dict[str, int]:
    connection = _sqlite_connection(canonical, readonly=True)
    try:
        raw_rows = connection.execute(
            """SELECT a.id,a.snapshot_id,a.logical_path,a.sha256,a.bytes,
                      a.storage_ref,s.metadata_json
               FROM raw_artifacts a JOIN source_snapshots s ON s.id=a.snapshot_id
               ORDER BY a.snapshot_id,a.id"""
        ).fetchall()
        result_rows = connection.execute(
            """SELECT id,receipt_id,result_storage_ref,result_sha256,result_byte_count
               FROM object_result_imports ORDER BY id"""
        ).fetchall()
        # Re-check receipt/import identity using packaged bytes, never original roots.
        _snapshot_result_inventory(connection, root / "provenance")
    finally:
        connection.close()

    raw_manifest = manifest.get("raw")
    provenance_manifest = manifest.get("provenance")
    if not isinstance(raw_manifest, list) or not isinstance(provenance_manifest, list):
        raise ValueError("Composite manifest dependency collections are invalid")

    raw_by_snapshot: dict[str, Mapping[str, object]] = {}
    for entry in raw_manifest:
        if not isinstance(entry, Mapping):
            raise ValueError("Composite Raw manifest entry is invalid")
        snapshot_id = str(entry.get("snapshot_id", ""))
        if snapshot_id in raw_by_snapshot:
            raise ValueError("Composite Raw manifest duplicates one Snapshot")
        raw_by_snapshot[snapshot_id] = entry

    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in raw_rows:
        grouped[str(row["snapshot_id"])].append(row)
    if set(raw_by_snapshot) != set(grouped):
        raise ValueError("Composite Raw manifest does not close SQLite Snapshot dependencies")

    importer = WebCaptureImporter()
    for snapshot_id, members in grouped.items():
        entry = raw_by_snapshot[snapshot_id]
        relative = _safe_posix_relative(str(entry.get("path", "")))
        if len(relative.parts) != 3 or relative.parts[:2] != ("raw", snapshot_id):
            raise ValueError("Composite Raw path must preserve Snapshot/basename layout")
        if len({row["storage_ref"] for row in members}) != 1:
            raise ValueError("Canonical Snapshot has multiple Raw storage refs")
        if entry.get("logical_artifact_count") != len(members):
            raise ValueError("Composite logical artifact count differs from canonical Snapshot")
        packaged = _verify_declared_file(root, entry, "Composite Raw bundle")
        bundle = importer.read(packaged)
        metadata = json.loads(str(members[0]["metadata_json"]))
        if (
            bundle.sha256 != metadata.get("bundle_sha256")
            or bundle.manifest.get("capture_id") != snapshot_id
        ):
            raise ValueError("Composite Raw bundle identity does not match SQLite Snapshot")
        for row in members:
            logical = str(row["logical_path"])
            if logical not in bundle.artifacts:
                raise ValueError("Composite Raw bundle misses canonical logical artifact")
            raw = bundle.artifacts[logical]
            if len(raw) != int(row["bytes"]) or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise ValueError("Composite Raw logical artifact does not match SQLite identity")

    result_by_import: dict[str, Mapping[str, object]] = {}
    for entry in provenance_manifest:
        if not isinstance(entry, Mapping):
            raise ValueError("Composite provenance manifest entry is invalid")
        import_id = str(entry.get("import_id", ""))
        if import_id in result_by_import:
            raise ValueError("Composite provenance manifest duplicates one import")
        result_by_import[import_id] = entry
    expected_imports = {str(row["id"]) for row in result_rows}
    if set(result_by_import) != expected_imports:
        raise ValueError("Composite provenance does not close accepted Result dependencies")
    for row in result_rows:
        entry = result_by_import[str(row["id"])]
        storage_ref = _safe_posix_relative(str(row["result_storage_ref"])).as_posix()
        if entry.get("path") != "provenance/" + storage_ref:
            raise ValueError("Composite Result path must preserve incoming relative ref")
        if entry.get("receipt_id") != row["receipt_id"] or entry.get("storage_ref") != storage_ref:
            raise ValueError("Composite provenance identity does not match SQLite import audit")
        if (
            entry.get("sha256") != row["result_sha256"]
            or entry.get("bytes") != row["result_byte_count"]
        ):
            raise ValueError(
                "Composite provenance content identity does not match SQLite import audit"
            )
        packaged = _verify_declared_file(root, entry, "Composite accepted Result")
        if packaged.name != "result.json":
            raise ValueError("Composite accepted Result filename is invalid")
        try:
            parsed = json.loads(packaged.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Composite accepted Result is not valid UTF-8 JSON") from exc
        if not isinstance(parsed, Mapping):
            raise ValueError("Composite accepted Result top level must be a JSON object")

    return {"raw_bundles": len(grouped), "original_results": len(result_rows)}


def verify_composite_backup(backup: str | Path) -> dict[str, object]:
    """Verify a finalized generation without mutating it or recovery targets."""
    root = _no_links(Path(backup))
    if root.name.startswith(".") and ".staging-" in root.name:
        raise ValueError("Staging directories are not accepted composite generations")
    return _verify_composite_backup(root)


def _verify_composite_backup(backup: str | Path) -> dict[str, object]:
    root = _no_links(Path(backup))
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Composite backup must be a regular directory")
    manifest = _load_manifest(root)

    canonical_entry = manifest.get("canonical")
    recovery_entry = manifest.get("recovery_metadata")
    if not isinstance(canonical_entry, Mapping) or not isinstance(recovery_entry, Mapping):
        raise ValueError("Composite manifest is missing required top-level artifacts")
    if canonical_entry.get("path") != CANONICAL_REL or recovery_entry.get("path") != RECOVERY_REL:
        raise ValueError("Composite required artifact paths do not match the frozen contract")
    canonical = _verify_declared_file(root, canonical_entry, "Composite canonical SQLite")
    sqlite_report = _sqlite_integrity(canonical)
    recovery = _verify_declared_file(root, recovery_entry, "Composite recovery metadata")
    try:
        recovery_data = json.loads(recovery.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Composite recovery metadata is not valid UTF-8 JSON") from exc
    if (
        not isinstance(recovery_data, dict)
        or recovery_data.get("schema") != RECOVERY_METADATA_SCHEMA
    ):
        raise ValueError("Composite recovery metadata schema is invalid")
    if recovery_data.get("plaintext_secrets_included") is not False:
        raise ValueError("Composite recovery metadata cannot claim plaintext-secret inclusion")
    if recovery_data.get("original_absolute_roots_included") is not False:
        raise ValueError("Composite recovery metadata cannot include original absolute roots")

    if recovery_data != _recovery_metadata():
        raise ValueError("Composite recovery metadata contains unexpected fields or semantics")
    closure = _verify_snapshot_closure(canonical, root, manifest)

    declared = {MANIFEST_NAME, str(canonical_entry["path"]), str(recovery_entry["path"])}
    for collection in ("raw", "provenance"):
        entries = manifest.get(collection)
        if not isinstance(entries, list):
            raise ValueError(f"Composite manifest {collection} collection is invalid")
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise ValueError("Composite manifest entry is invalid")
            relative = _safe_posix_relative(str(entry.get("path", ""))).as_posix()
            if relative in declared:
                raise ValueError("Composite manifest contains duplicate packaged paths")
            declared.add(relative)

    actual: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Composite backup must not contain symlinks")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != declared:
        raise ValueError("Composite backup contains missing or undeclared files")

    return {
        "ok": True,
        "schema": COMPOSITE_BACKUP_SCHEMA,
        "generation_id": manifest.get("generation_id"),
        "created_at": manifest.get("created_at"),
        "canonical_sha256": canonical_entry.get("sha256"),
        "raw_bundles": closure["raw_bundles"],
        "original_results": closure["original_results"],
        "sqlite": sqlite_report,
    }


def _paths_overlap(first: Path, second: Path) -> bool:
    first = first.resolve()
    second = second.resolve()
    if first == second:
        return True
    return first in second.parents or second in first.parents


def _restore_targets(
    db_target: str | Path,
    raw_root: str | Path,
    incoming_root: str | Path,
) -> tuple[Path, Path, Path, Path]:
    db = _no_links(Path(db_target))
    raw = _no_links(Path(raw_root))
    incoming = _no_links(Path(incoming_root))
    metadata = _no_links(db.with_name(db.name + ".recovery.json"))
    paths = [db, raw, incoming, metadata]
    for index, first in enumerate(paths):
        for second in paths[index + 1 :]:
            if _paths_overlap(first, second):
                raise ValueError("Composite restore targets must not overlap")
    return db, raw, incoming, metadata


def composite_restore_plan(
    backup: str | Path,
    *,
    db_target: str | Path,
    raw_root: str | Path,
    incoming_root: str | Path,
) -> dict[str, object]:
    """Return a read-only, verified restore plan."""

    root = _no_links(Path(backup))
    verification = verify_composite_backup(root)
    db, raw, incoming, metadata = _restore_targets(db_target, raw_root, incoming_root)
    for target in (db, raw, incoming, metadata):
        if _paths_overlap(root, target):
            raise ValueError("Composite backup and restore targets must not overlap")
    return {
        "backup": str(root),
        "verification": verification,
        "targets": {
            "canonical_database": str(db),
            "raw_root": str(raw),
            "incoming_root": str(incoming),
            "recovery_metadata": str(metadata),
        },
        "existing": {
            "canonical_database": db.exists(),
            "raw_root": raw.exists(),
            "incoming_root": incoming.exists(),
            "recovery_metadata": metadata.exists(),
        },
        "raw_relocation": "raw_artifacts.storage_ref only",
        "result_relocation": "preserve incoming-root-relative storage_ref",
        "database_published_last": True,
    }


def _prepare_external_target(path: Path, acknowledge_overwrite: bool) -> None:
    if not path.exists():
        return
    if not acknowledge_overwrite:
        raise PermissionError(f"Restore target exists; explicit acknowledgement required: {path}")
    if path.is_symlink():
        raise ValueError("Composite restore will not replace a symlink target")
    if path.is_file() or any(path.iterdir()):
        raise RuntimeError(
            "N07-R01 initial restore contract only replaces absent or empty external roots"
        )


def _restore_stage_paths(db_target, raw_root, incoming_root, metadata_target):
    token = uuid.uuid4().hex
    return tuple(
        path.parent / f".{path.name}.restore-{token}.tmp"
        for path in (db_target, raw_root, incoming_root, metadata_target)
    )


def _stage_restore(
    backup: Path,
    manifest: Mapping[str, object],
    db_target: Path,
    raw_root: Path,
    incoming_root: Path,
    metadata_target: Path,
    stages: tuple[Path, Path, Path, Path],
) -> tuple[Path, Path, Path, Path]:
    db_stage, raw_stage, incoming_stage, metadata_stage = stages
    for stage in (db_stage, raw_stage, incoming_stage, metadata_stage):
        if stage.exists():
            raise FileExistsError(f"Restore staging target already exists: {stage}")
    db_target.parent.mkdir(parents=True, exist_ok=True)
    raw_root.parent.mkdir(parents=True, exist_ok=True)
    incoming_root.parent.mkdir(parents=True, exist_ok=True)
    metadata_target.parent.mkdir(parents=True, exist_ok=True)
    raw_stage.mkdir()
    incoming_stage.mkdir()

    canonical_entry = manifest["canonical"]
    recovery_entry = manifest["recovery_metadata"]
    assert isinstance(canonical_entry, Mapping)
    assert isinstance(recovery_entry, Mapping)
    shutil.copy2(_package_path(backup, str(canonical_entry["path"])), db_stage)
    shutil.copy2(_package_path(backup, str(recovery_entry["path"])), metadata_stage)

    raw_entries = manifest["raw"]
    assert isinstance(raw_entries, list)
    for entry in raw_entries:
        assert isinstance(entry, Mapping)
        source = _package_path(backup, str(entry["path"]))
        relative = _safe_posix_relative(str(entry["path"]))
        if not relative.parts or relative.parts[0] != "raw":
            raise ValueError("Composite Raw package path is outside raw prefix")
        destination = raw_stage / Path(*relative.parts[1:])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if _file_identity(destination) != {"sha256": entry["sha256"], "bytes": entry["bytes"]}:
            raise ValueError("Staged restored Raw bundle failed integrity verification")
        WebCaptureImporter().read(destination)

    provenance_entries = manifest["provenance"]
    assert isinstance(provenance_entries, list)
    copied: set[str] = set()
    for entry in provenance_entries:
        assert isinstance(entry, Mapping)
        storage_ref = _safe_posix_relative(str(entry["storage_ref"]))
        relative = _safe_posix_relative(str(entry["path"]))
        expected = PurePosixPath("provenance") / storage_ref
        if relative != expected:
            raise ValueError("Composite provenance packaged path does not preserve storage ref")
        if storage_ref.as_posix() in copied:
            continue
        destination = incoming_stage / Path(*storage_ref.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_package_path(backup, relative.as_posix()), destination)
        if _file_identity(destination) != {"sha256": entry["sha256"], "bytes": entry["bytes"]}:
            raise ValueError("Staged restored Result failed integrity verification")
        copied.add(storage_ref.as_posix())

    connection = _sqlite_connection(db_stage)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for entry in raw_entries:
            assert isinstance(entry, Mapping)
            snapshot_id = str(entry["snapshot_id"])
            relative = _safe_posix_relative(str(entry["path"]))
            final_path = raw_root / Path(*relative.parts[1:])
            cursor = connection.execute(
                "UPDATE raw_artifacts SET storage_ref=? WHERE snapshot_id=?",
                (str(final_path), snapshot_id),
            )
            if cursor.rowcount <= 0:
                raise ValueError("Composite Raw relocation refers to unknown Snapshot")
        connection.commit()
        connection.execute("PRAGMA journal_mode=DELETE")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    _sqlite_integrity(db_stage)

    # Validate staged external bytes against the staged DB while allowing its Raw refs
    # to already contain their final post-publication locations.
    check = _sqlite_connection(db_stage)
    try:
        rows = check.execute(
            "SELECT DISTINCT snapshot_id,storage_ref FROM raw_artifacts ORDER BY snapshot_id"
        ).fetchall()
        for row in rows:
            expected_final = Path(str(row["storage_ref"]))
            try:
                relative = expected_final.relative_to(raw_root)
            except ValueError as exc:
                raise ValueError("Relocated Raw storage ref escapes target Raw root") from exc
            WebCaptureImporter().read(raw_stage / relative)
        results = check.execute(
            "SELECT result_storage_ref,result_sha256,result_byte_count FROM object_result_imports"
        ).fetchall()
        for row in results:
            ref = _safe_posix_relative(str(row["result_storage_ref"]))
            path = _regular_file(incoming_stage / Path(*ref.parts), "Staged restored Result")
            identity = _file_identity(path)
            if (
                identity["sha256"] != row["result_sha256"]
                or identity["bytes"] != row["result_byte_count"]
            ):
                raise ValueError("Staged restored Result does not match accepted import audit")
    finally:
        check.close()

    return db_stage, raw_stage, incoming_stage, metadata_stage


def composite_restore_apply(
    backup: str | Path,
    *,
    db_target: str | Path,
    raw_root: str | Path,
    incoming_root: str | Path,
    acknowledge_overwrite: bool = False,
) -> dict[str, object]:
    """Restore a verified composite generation; publish the database last as completion marker."""

    plan = composite_restore_plan(
        backup,
        db_target=db_target,
        raw_root=raw_root,
        incoming_root=incoming_root,
    )
    root = Path(str(plan["backup"]))
    db, raw, incoming, metadata = _restore_targets(db_target, raw_root, incoming_root)
    if db.exists() and not acknowledge_overwrite:
        raise PermissionError("Database restore target exists; explicit acknowledgement required")
    if db.exists() and (db.is_symlink() or not db.is_file()):
        raise ValueError("Database restore target must be a regular file")
    if metadata.exists() and not acknowledge_overwrite:
        raise PermissionError("Recovery metadata target exists; explicit acknowledgement required")
    if metadata.exists() and (metadata.is_symlink() or not metadata.is_file()):
        raise ValueError("Recovery metadata target must be a regular file")
    _prepare_external_target(raw, acknowledge_overwrite)
    _prepare_external_target(incoming, acknowledge_overwrite)

    if any(Path(str(db) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise RuntimeError("Composite restore requires an offline target without SQLite sidecars")
    manifest = _load_manifest(root)
    stages = _restore_stage_paths(db, raw, incoming, metadata)
    published_external = []
    existing_empty = [path for path in (raw, incoming) if path.exists()]
    metadata_rollback = metadata.with_name(f".{metadata.name}.rollback-{uuid.uuid4().hex}.tmp")
    database_published = False
    try:
        _stage_restore(root, manifest, db, raw, incoming, metadata, stages)
        db_stage, raw_stage, incoming_stage, metadata_stage = stages
        if metadata.exists():
            shutil.copy2(metadata, metadata_rollback)
        for path in existing_empty:
            path.rmdir()
        os.replace(raw_stage, raw)
        published_external.append(raw)
        os.replace(incoming_stage, incoming)
        published_external.append(incoming)
        os.replace(metadata_stage, metadata)
        published_external.append(metadata)
        # All validations precede this final atomic completion marker.
        os.replace(db_stage, db)
        database_published = True
        return {
            "restored": True,
            "backup": str(root),
            "canonical_database": str(db),
            "raw_root": str(raw),
            "incoming_root": str(incoming),
            "recovery_metadata": str(metadata),
            "database_published_last": True,
            "sqlite": {"integrity_check": ["ok"], "foreign_key_violations": []},
            "verification": plan["verification"],
        }
    finally:
        if not database_published:
            for target in reversed(published_external):
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink(missing_ok=True)
            if metadata_rollback.exists() and metadata in published_external:
                os.replace(metadata_rollback, metadata)
            for path in existing_empty:
                path.mkdir(exist_ok=True)
        for stage in stages:
            if stage.is_dir():
                shutil.rmtree(stage)
            else:
                stage.unlink(missing_ok=True)
        metadata_rollback.unlink(missing_ok=True)
