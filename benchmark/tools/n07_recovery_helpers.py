"""Read-only observations and strict ownership checks for N-07 fault targets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def owned_path(root: Path, target: Path) -> Path:
    root, target = root.resolve(), target.resolve()
    if root == target or not target.is_relative_to(root):
        raise ValueError("Destructive target must be strictly inside the unique run root")
    if ".local" not in root.parts or "n07" not in root.parts:
        raise ValueError("N-07 run root required")
    return target


def database_digest(connection) -> str:
    tables = sorted(
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    )
    state = {}
    for name in tables:
        quoted = '"' + name.replace('"', '""') + '"'
        rows = [list(row) for row in connection.execute("SELECT * FROM " + quoted)]
        encoded = [
            json.dumps(row, default=lambda x: {"bytes": x.hex()}, ensure_ascii=True, sort_keys=True)
            for row in rows
        ]
        state[name] = sorted(encoded)
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def recovery_inventory(repository) -> dict:
    raw = [
        dict(row)
        for row in repository.db.execute(
            "SELECT id,storage_ref,logical_path,sha256,bytes FROM raw_artifacts ORDER BY id"
        )
    ]
    results = [
        dict(row)
        for row in repository.db.execute(
            "SELECT id,result_storage_ref,result_sha256 FROM object_result_imports ORDER BY id"
        )
    ]
    return {
        "canonical_sqlite": {"required": True, "product_backup_covers": True},
        "raw_artifact_store": {
            "required": bool(raw),
            "artifacts": raw,
            "product_backup_covers": False,
        },
        "external_canonical_or_provenance_manifests_if_any": {
            "required": bool(results),
            "imported_results": results,
            "capture_manifests": "members of the externally referenced capture bundle",
            "product_backup_covers": False,
        },
        "recovery_configuration_metadata_without_plaintext_secrets": {
            "required": True,
            "items": ["Raw store resolution", "Result incoming root"],
            "product_backup_covers": False,
        },
        "rebuildable_derived": ["search representation", "embedding", "vector index", "render"],
    }
