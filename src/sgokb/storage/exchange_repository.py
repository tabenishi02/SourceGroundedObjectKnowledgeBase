"""Persistence for Phase G Package exchange and Result receipt audit metadata."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Mapping

from sgokb.domain.object import new_persistent_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class PackageExchangeAuditRepository:
    """Append-safe audit metadata for Package staging/export and Result receipt."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def record_staged(
        self,
        manifest: Mapping[str, object],
        staged_path: str,
        preflight: Mapping[str, object],
    ) -> None:
        package_id = str(manifest["package_id"])
        manifest_sha256 = str(manifest["integrity"]["manifest_sha256"])
        existing = self.db.execute(
            "SELECT manifest_sha256 FROM package_exchange_records WHERE package_id=?",
            (package_id,),
        ).fetchone()
        if existing and existing["manifest_sha256"] != manifest_sha256:
            raise ValueError("Package ID already exists with a different manifest hash")

        evidence_ids = list(manifest["evidence"]["included_evidence_ids"])
        values = (
            package_id,
            str(manifest["schema_version"]),
            manifest_sha256,
            str(manifest["target"]["object_id"]),
            manifest["binding"].get("base_version_id"),
            str(manifest["created_at"]),
            str(manifest["extracted_at"]),
            _json(evidence_ids),
            staged_path,
            str(preflight["disposition"]),
            _json(dict(preflight)),
            _now(),
        )
        with self.db:
            if existing:
                self.db.execute(
                    """UPDATE package_exchange_records
                       SET staged_path=?,preflight_disposition=?,preflight_json=?,staged_at=?
                       WHERE package_id=?""",
                    (
                        staged_path,
                        str(preflight["disposition"]),
                        _json(dict(preflight)),
                        _now(),
                        package_id,
                    ),
                )
            else:
                self.db.execute(
                    "INSERT INTO package_exchange_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )

    def record_export(
        self,
        package_id: str,
        manifest_sha256: str,
        destination_root: str,
        exported_path: str,
        *,
        acknowledged_review: bool,
        already_present: bool,
    ) -> str:
        row = self.db.execute(
            "SELECT manifest_sha256 FROM package_exchange_records WHERE package_id=?",
            (package_id,),
        ).fetchone()
        if not row:
            raise ValueError("Package must be staged/audited before export")
        if row["manifest_sha256"] != manifest_sha256:
            raise ValueError("Export manifest hash does not match staged audit record")
        event_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO package_export_events VALUES(?,?,?,?,?,?,?,?)",
                (
                    event_id,
                    package_id,
                    destination_root,
                    exported_path,
                    manifest_sha256,
                    int(acknowledged_review),
                    int(already_present),
                    _now(),
                ),
            )
        return event_id

    def package_record(self, package_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT * FROM package_exchange_records WHERE package_id=?", (package_id,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["included_evidence_ids"] = json.loads(result.pop("included_evidence_ids_json"))
        result["preflight"] = json.loads(result.pop("preflight_json"))
        return result

    def export_events(self, package_id: str) -> tuple[dict, ...]:
        rows = self.db.execute(
            "SELECT * FROM package_export_events WHERE package_id=? ORDER BY rowid",
            (package_id,),
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def result_receipt_by_hash(self, package_id: str, result_sha256: str) -> dict | None:
        row = self.db.execute(
            """SELECT * FROM package_result_receipts
               WHERE package_id=? AND result_sha256=?""",
            (package_id, result_sha256),
        ).fetchone()
        return self._receipt(row) if row else None

    def record_result_receipt(
        self,
        package_id: str,
        result_sha256: str,
        byte_count: int,
        storage_ref: str,
        intake_state: str,
        intake_findings: list[str] | tuple[str, ...],
        *,
        parsed_schema_version: str | None = None,
        parsed_result_status: str | None = None,
        parsed_target_object_id: str | None = None,
        parsed_binding_package_id: str | None = None,
        parsed_manifest_sha256: str | None = None,
        parsed_base_version_id: str | None = None,
    ) -> str:
        if self.package_record(package_id) is None:
            raise ValueError("Result receipt requires a staged/audited Package")
        if intake_state not in {"ready_for_validation", "needs_review"}:
            raise ValueError("Invalid Result intake state")
        existing = self.result_receipt_by_hash(package_id, result_sha256)
        if existing:
            return str(existing["id"])

        receipt_id = new_persistent_id()
        timestamp = _now()
        with self.db:
            self.db.execute(
                """INSERT INTO package_result_receipts
                   (id,package_id,result_sha256,byte_count,storage_ref,intake_state,
                    intake_findings_json,parsed_schema_version,parsed_result_status,
                    parsed_target_object_id,parsed_binding_package_id,
                    parsed_manifest_sha256,parsed_base_version_id,validation_state,
                    validation_requested_at,received_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)""",
                (
                    receipt_id,
                    package_id,
                    result_sha256,
                    byte_count,
                    storage_ref,
                    intake_state,
                    _json(list(intake_findings)),
                    parsed_schema_version,
                    parsed_result_status,
                    parsed_target_object_id,
                    parsed_binding_package_id,
                    parsed_manifest_sha256,
                    parsed_base_version_id,
                    timestamp,
                    timestamp,
                ),
            )
        return receipt_id

    def result_receipt(self, receipt_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT * FROM package_result_receipts WHERE id=?", (receipt_id,)
        ).fetchone()
        return self._receipt(row) if row else None

    def result_receipts(self, package_id: str | None = None) -> tuple[dict, ...]:
        if package_id is None:
            rows = self.db.execute(
                "SELECT * FROM package_result_receipts ORDER BY received_at,id"
            ).fetchall()
        else:
            rows = self.db.execute(
                """SELECT * FROM package_result_receipts
                   WHERE package_id=? ORDER BY received_at,id""",
                (package_id,),
            ).fetchall()
        return tuple(self._receipt(row) for row in rows)

    def pending_result_receipts(self) -> tuple[dict, ...]:
        rows = self.db.execute(
            """SELECT * FROM package_result_receipts
               WHERE validation_state='pending'
               ORDER BY validation_requested_at,id"""
        ).fetchall()
        return tuple(self._receipt(row) for row in rows)

    @staticmethod
    def _receipt(row: sqlite3.Row | dict) -> dict:
        result = dict(row)
        result["intake_findings"] = json.loads(result.pop("intake_findings_json"))
        return result
