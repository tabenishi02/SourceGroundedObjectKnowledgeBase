"""Persistence helpers for Package v2 Raw membership and accepted Raw grounding."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping

from sgokb.domain.object import new_persistent_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class RawGroundingRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def record_package(self, manifest: Mapping[str, Any]) -> None:
        if manifest.get("schema_version") != "sgokb.object-evidence-package/2.0":
            return
        package_id = str(manifest["package_id"])
        raw = manifest["raw_grounding"]
        integrity = raw["integrity"]
        existing = self.db.execute(
            "SELECT grounding_set_sha256 FROM package_raw_grounding_metadata WHERE package_id=?",
            (package_id,),
        ).fetchone()
        if existing:
            if existing["grounding_set_sha256"] != integrity["grounding_set_sha256"]:
                raise ValueError("Package Raw audit already exists with different grounding set")
            return
        with self.db:
            self.db.execute(
                "INSERT INTO package_raw_grounding_metadata VALUES(?,?,?,?,?)",
                (
                    package_id,
                    str(manifest["binding"]["grounding_contract"]),
                    str(raw["resolution_contract"]),
                    str(integrity["grounding_set_sha256"]),
                    _now(),
                ),
            )
            for ordinal, item in enumerate(raw["artifacts"]):
                self.db.execute(
                    """INSERT INTO package_raw_artifacts
                       (package_id,ordinal,raw_artifact_id,source_id,snapshot_id,
                        artifact_kind,package_path,logical_path,media_type,charset,
                        byte_size,sha256)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        package_id,
                        ordinal,
                        item["raw_artifact_id"],
                        item["source_id"],
                        item["snapshot_id"],
                        item["artifact_kind"],
                        item["package_path"],
                        item.get("logical_path"),
                        item.get("media_type"),
                        item.get("charset"),
                        item["byte_size"],
                        item["sha256"],
                    ),
                )
            for ordinal, item in enumerate(raw["evidence_bindings"]):
                self.db.execute(
                    """INSERT INTO package_evidence_raw_bindings
                       (package_id,ordinal,evidence_id,source_id,snapshot_id,
                        normalization_run_id,raw_artifact_ids_json)
                       VALUES(?,?,?,?,?,?,?)""",
                    (
                        package_id,
                        ordinal,
                        item["evidence_id"],
                        item["source_id"],
                        item["snapshot_id"],
                        item["normalization_run_id"],
                        _json(item["raw_artifact_ids"]),
                    ),
                )

    def package_grounding(self, package_id: str) -> dict | None:
        metadata = self.db.execute(
            "SELECT * FROM package_raw_grounding_metadata WHERE package_id=?", (package_id,)
        ).fetchone()
        if not metadata:
            return None
        artifacts = tuple(
            dict(row)
            for row in self.db.execute(
                """SELECT * FROM package_raw_artifacts
                   WHERE package_id=? ORDER BY ordinal""",
                (package_id,),
            )
        )
        bindings = []
        for row in self.db.execute(
            """SELECT * FROM package_evidence_raw_bindings
               WHERE package_id=? ORDER BY ordinal""",
            (package_id,),
        ):
            item = dict(row)
            item["raw_artifact_ids"] = json.loads(item.pop("raw_artifact_ids_json"))
            bindings.append(item)
        return {
            "grounding_contract": metadata["grounding_contract"],
            "resolution_contract": metadata["resolution_contract"],
            "grounding_set_sha256": metadata["grounding_set_sha256"],
            "included_raw_artifact_ids": tuple(item["raw_artifact_id"] for item in artifacts),
            "artifacts": artifacts,
            "evidence_bindings": tuple(bindings),
        }

    def package_raw_artifact(self, package_id: str, raw_artifact_id: str) -> dict | None:
        row = self.db.execute(
            """SELECT * FROM package_raw_artifacts
               WHERE package_id=? AND raw_artifact_id=?""",
            (package_id, raw_artifact_id),
        ).fetchone()
        return dict(row) if row else None

    def link_raw_grounding(
        self,
        version_id: str,
        target_kind: str,
        target_id: str,
        package_id: str,
        reference: Mapping[str, Any],
        *,
        origin_ref: str,
    ) -> str:
        link_id = new_persistent_id()
        locator = reference.get("locator")
        self.db.execute(
            """INSERT INTO raw_grounding_links
               (id,version_id,target_kind,target_id,package_id,raw_artifact_id,
                role,locator_json,origin_kind,origin_ref,created_at)
               VALUES(?,?,?,?,?,?,?,?, 'result_import',?,?)""",
            (
                link_id,
                version_id,
                target_kind,
                target_id,
                package_id,
                reference["raw_artifact_id"],
                reference["role"],
                _json(locator) if locator is not None else None,
                origin_ref,
                _now(),
            ),
        )
        return link_id

    def links_for_version(self, version_id: str) -> tuple[dict, ...]:
        rows = self.db.execute(
            "SELECT * FROM raw_grounding_links WHERE version_id=? ORDER BY rowid",
            (version_id,),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["locator"] = (
                json.loads(item.pop("locator_json")) if item["locator_json"] is not None else None
            )
            result.append(item)
        return tuple(result)
