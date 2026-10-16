"""Local-only maintenance operations exposed by `sgokb system`."""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def system_status(repository, db_path: Path) -> dict:
    migrations = [
        row[0]
        for row in repository.db.execute("SELECT version FROM schema_migrations ORDER BY version")
    ]
    object_count = repository.db.execute("SELECT count(*) FROM objects").fetchone()[0]
    current_count = repository.db.execute(
        "SELECT count(*) FROM objects WHERE current_version_id IS NOT NULL"
    ).fetchone()[0]
    return {
        "database": str(db_path.resolve()),
        "schema_migrations": migrations,
        "source": repository.source_store.status(),
        "objects": {"count": object_count, "with_current_version": current_count},
    }


def integrity(repository) -> dict:
    sqlite_result = repository.db.execute("PRAGMA integrity_check").fetchall()
    foreign_keys = [dict(row) for row in repository.db.execute("PRAGMA foreign_key_check")]
    migrations = [
        row[0]
        for row in repository.db.execute("SELECT version FROM schema_migrations ORDER BY version")
    ]
    ok = [row[0] for row in sqlite_result] == ["ok"] and not foreign_keys
    return {
        "ok": ok,
        "sqlite_integrity": [row[0] for row in sqlite_result],
        "foreign_key_violations": foreign_keys,
        "schema_migrations": migrations,
    }


def index_status(repository) -> dict:
    rows = [
        dict(row)
        for row in repository.db.execute(
            """SELECT object_id,kind,target_version_id,status,revision,updated_at
               FROM object_derived_states ORDER BY object_id,kind"""
        )
    ]
    embedding_spaces = [
        dict(row)
        for row in repository.db.execute(
            """SELECT s.id,s.provider_key,s.model,s.model_revision,s.dimension,
                      count(e.representation_id) AS embedding_count
               FROM search_embedding_spaces s
               LEFT JOIN search_representation_embeddings e ON e.space_id=s.id
               GROUP BY s.id ORDER BY s.created_at,s.id"""
        )
    ]
    return {"derived_states": rows, "embedding_spaces": embedding_spaces}


def create_backup(repository, output: Path | None = None, root: Path = Path("backups")) -> dict:
    if output is None:
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = root / f"sgokb-{stamp}.sqlite"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Backup already exists: {output}")
    destination = sqlite3.connect(output)
    try:
        repository.db.backup(destination)
        check = destination.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise RuntimeError(f"Backup integrity check failed: {check}")
    finally:
        destination.close()
    return {"path": str(output), "byte_count": output.stat().st_size, "integrity": "ok"}


def backup_status(root: Path) -> dict:
    root = root.resolve()
    files = []
    if root.exists():
        for path in sorted(root.glob("*.sqlite"), reverse=True):
            files.append(
                {
                    "path": str(path),
                    "byte_count": path.stat().st_size,
                    "modified_at": datetime.fromtimestamp(
                        path.stat().st_mtime, timezone.utc
                    ).isoformat(),
                }
            )
    return {"root": str(root), "backups": files}


def restore_plan(backup: Path, target: Path) -> dict:
    backup = backup.resolve()
    target = target.resolve()
    if not backup.is_file():
        raise FileNotFoundError(f"Backup does not exist: {backup}")
    connection = sqlite3.connect(f"file:{backup.as_posix()}?mode=ro", uri=True)
    try:
        integrity_result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        try:
            migrations = [
                row[0]
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ]
        except sqlite3.Error:
            migrations = []
    finally:
        connection.close()
    return {
        "backup": str(backup),
        "target": str(target),
        "target_exists": target.exists(),
        "backup_integrity": integrity_result,
        "schema_migrations": migrations,
        "requires_overwrite_acknowledgement": target.exists(),
    }


def restore_apply(backup: Path, target: Path, *, acknowledge_overwrite: bool) -> dict:
    plan = restore_plan(backup, target)
    if plan["backup_integrity"] != "ok":
        raise RuntimeError("Backup integrity check failed")
    if plan["target_exists"] and not acknowledge_overwrite:
        raise PermissionError("Restore requires --acknowledge-overwrite for an existing target DB")
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.restore-{os.getpid()}.tmp")
    try:
        shutil.copy2(backup.resolve(), temporary)
        os.replace(temporary, target)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(target) + suffix)
            if sidecar.exists():
                sidecar.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"restored": True, **plan}
