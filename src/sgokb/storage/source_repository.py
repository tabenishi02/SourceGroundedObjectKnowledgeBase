"""Canonical Source / Evidence persistence for Phase E / E-03."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable

from sgokb.domain.object import new_persistent_id
from sgokb.domain.source import (
    AssociationStatus,
    EvidenceExtractionMode,
    EvidenceLinkRecord,
    EvidenceProvenance,
    EvidenceRecord,
    EvidenceRole,
    EvidenceTargetKind,
    LocatorStatus,
    MetadataOrigin,
    NormalizationStatus,
    SnapshotCompleteness,
    SourceLocatorRecord,
    SourceRecord,
    SourceSnapshotRecord,
    SourceStatus,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SourceRepository:
    """Persistence for canonical Source identity, Evidence, and provenance links."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    @staticmethod
    def _source_record(row: sqlite3.Row | dict) -> SourceRecord:
        return SourceRecord(
            source_id=row["id"],
            label=row["label"],
            status=SourceStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _locator_record(row: sqlite3.Row | dict) -> SourceLocatorRecord:
        return SourceLocatorRecord(
            locator_id=row["id"],
            source_id=row["source_id"],
            kind=row["kind"],
            value=row["value"],
            is_preferred=bool(row["is_preferred"]),
            status=LocatorStatus(row["status"]),
        )

    @staticmethod
    def _snapshot_record(row: sqlite3.Row | dict) -> SourceSnapshotRecord:
        return SourceSnapshotRecord(
            snapshot_id=row["id"],
            source_id=row["source_id"],
            observed_locator_id=row["observed_locator_id"],
            captured_at=row["captured_at"],
            imported_at=row["imported_at"],
            capture_method=row["capture_method"],
            completeness=SnapshotCompleteness(row["completeness"]),
            title=row["title"],
        )

    @staticmethod
    def _evidence_record(row: sqlite3.Row | dict) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=row["id"],
            run_id=row["run_id"],
            snapshot_id=row["snapshot_id"],
            source_id=row["source_id"],
            ordinal=row["ordinal"],
            content=row["content"],
            content_hash=row["content_hash"],
            extraction_mode=EvidenceExtractionMode(row["extraction_mode"]),
            language=row["language"],
        )

    def create_source(self, label: str | None = None, *, source_id: str | None = None) -> str:
        source_id = source_id or new_persistent_id()
        timestamp = _now()
        with self.db:
            self.db.execute(
                "INSERT INTO source_records VALUES(?,?,?,?,?)",
                (
                    source_id,
                    label.strip() if label else None,
                    SourceStatus.ACTIVE.value,
                    timestamp,
                    timestamp,
                ),
            )
        return source_id

    def source_by_id(self, source_id: str) -> SourceRecord:
        row = self.db.execute("SELECT * FROM source_records WHERE id=?", (source_id,)).fetchone()
        if not row:
            raise ValueError("Unknown source ID")
        return self._source_record(row)

    def sources_by_locator(self, kind: str, value: str) -> tuple[SourceRecord, ...]:
        rows = self.db.execute(
            """SELECT DISTINCT s.* FROM source_records s
               JOIN source_locators l ON l.source_id=s.id
               WHERE l.kind=? AND l.value=? AND l.status='active' AND s.status='active'
               ORDER BY s.id""",
            (kind.strip(), value.strip()),
        ).fetchall()
        return tuple(self._source_record(row) for row in rows)

    def add_locator(
        self,
        source_id: str,
        kind: str,
        value: str,
        *,
        preferred: bool = False,
        locator_id: str | None = None,
    ) -> str:
        kind, value = kind.strip(), value.strip()
        if not kind or not value:
            raise ValueError("Locator kind and value are required")
        locator_id = locator_id or new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO source_locators VALUES(?,?,?,?,?,?,?,NULL)",
                (
                    locator_id,
                    source_id,
                    kind,
                    value,
                    int(preferred),
                    LocatorStatus.ACTIVE.value,
                    _now(),
                ),
            )
        return locator_id

    def locators(self, source_id: str) -> tuple[SourceLocatorRecord, ...]:
        rows = self.db.execute(
            "SELECT * FROM source_locators WHERE source_id=? ORDER BY rowid", (source_id,)
        ).fetchall()
        return tuple(self._locator_record(row) for row in rows)

    def ensure_locator(
        self, source_id: str, kind: str, value: str, *, preferred: bool = False
    ) -> str:
        row = self.db.execute(
            """SELECT id FROM source_locators
               WHERE source_id=? AND kind=? AND value=? AND status='active'
               ORDER BY rowid LIMIT 1""",
            (source_id, kind.strip(), value.strip()),
        ).fetchone()
        if row:
            return row["id"]
        return self.add_locator(source_id, kind, value, preferred=preferred)

    def create_snapshot(
        self,
        source_id: str,
        captured_at: str,
        capture_method: str,
        *,
        observed_locator_id: str | None = None,
        imported_at: str | None = None,
        capture_tool: str | None = None,
        capture_version: str | None = None,
        completeness: SnapshotCompleteness | str = SnapshotCompleteness.COMPLETE,
        title: str | None = None,
        manifest: object | None = None,
        metadata: object | None = None,
        warnings: object | None = None,
        snapshot_id: str | None = None,
    ) -> str:
        capture_method = capture_method.strip()
        if not capture_method:
            raise ValueError("Capture method is required")
        completeness = SnapshotCompleteness(completeness)
        snapshot_id = snapshot_id or new_persistent_id()
        timestamp = _now()
        with self.db:
            self.db.execute(
                """INSERT INTO source_snapshots
                   (id,source_id,observed_locator_id,captured_at,imported_at,capture_method,
                    capture_tool,capture_version,completeness,title,manifest_json,metadata_json,
                    warnings_json,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    snapshot_id,
                    source_id,
                    observed_locator_id,
                    captured_at,
                    imported_at or timestamp,
                    capture_method,
                    capture_tool,
                    capture_version,
                    completeness.value,
                    title,
                    _json(manifest or {}),
                    _json(metadata or {}),
                    _json(warnings or []),
                    timestamp,
                ),
            )
        return snapshot_id

    def snapshot_by_id(self, snapshot_id: str) -> SourceSnapshotRecord:
        row = self.db.execute(
            "SELECT * FROM source_snapshots WHERE id=?", (snapshot_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown source snapshot ID")
        return self._snapshot_record(row)

    def find_snapshot_by_id(self, snapshot_id: str) -> SourceSnapshotRecord | None:
        row = self.db.execute(
            "SELECT * FROM source_snapshots WHERE id=?", (snapshot_id,)
        ).fetchone()
        return self._snapshot_record(row) if row else None

    def snapshots(self) -> tuple[SourceSnapshotRecord, ...]:
        rows = self.db.execute("SELECT * FROM source_snapshots ORDER BY captured_at,id").fetchall()
        return tuple(self._snapshot_record(row) for row in rows)

    def status(self) -> dict[str, int]:
        tables = {
            "sources": "source_records",
            "snapshots": "source_snapshots",
            "raw_artifacts": "raw_artifacts",
            "normalization_runs": "normalization_runs",
            "evidence": "evidence_records",
            "selection_events": "source_selection_events",
        }
        return {
            name: self.db.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            for name, table in tables.items()
        }

    def snapshot_metadata(self, snapshot_id: str) -> dict:
        row = self.db.execute(
            "SELECT metadata_json FROM source_snapshots WHERE id=?", (snapshot_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown source snapshot ID")
        return json.loads(row["metadata_json"])

    def add_classification(
        self,
        source_id: str,
        axis: str,
        value: str,
        origin: MetadataOrigin | str,
        *,
        snapshot_id: str | None = None,
    ) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Classification value is required")
        classification_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO source_classifications VALUES(?,?,?,?,?,?,?)",
                (
                    classification_id,
                    source_id,
                    axis,
                    value,
                    MetadataOrigin(origin).value,
                    snapshot_id,
                    _now(),
                ),
            )
        return classification_id

    def add_metadata(
        self,
        source_id: str,
        key: str,
        value: object,
        origin: MetadataOrigin | str,
        *,
        snapshot_id: str | None = None,
    ) -> str:
        key = key.strip()
        if not key:
            raise ValueError("Metadata key is required")
        metadata_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO source_metadata_values VALUES(?,?,?,?,?,?,?)",
                (
                    metadata_id,
                    source_id,
                    key,
                    _json(value),
                    MetadataOrigin(origin).value,
                    snapshot_id,
                    _now(),
                ),
            )
        return metadata_id

    def observe_classification(
        self,
        source_id: str,
        axis: str,
        value: str,
        origin: MetadataOrigin | str,
        *,
        snapshot_id: str | None = None,
    ) -> str:
        normalized_origin = MetadataOrigin(origin).value
        row = self.db.execute(
            """SELECT id FROM source_classifications
               WHERE source_id=? AND axis=? AND value=? AND origin_kind=?
                 AND snapshot_id IS ?
               ORDER BY rowid LIMIT 1""",
            (source_id, axis, value.strip(), normalized_origin, snapshot_id),
        ).fetchone()
        if row:
            return row["id"]
        return self.add_classification(
            source_id, axis, value, normalized_origin, snapshot_id=snapshot_id
        )

    def observe_metadata(
        self,
        source_id: str,
        key: str,
        value: object,
        origin: MetadataOrigin | str,
        *,
        snapshot_id: str | None = None,
    ) -> str:
        normalized_origin = MetadataOrigin(origin).value
        encoded = _json(value)
        row = self.db.execute(
            """SELECT id FROM source_metadata_values
               WHERE source_id=? AND key=? AND value_json=? AND origin_kind=?
                 AND snapshot_id IS ?
               ORDER BY rowid LIMIT 1""",
            (source_id, key.strip(), encoded, normalized_origin, snapshot_id),
        ).fetchone()
        if row:
            return row["id"]
        return self.add_metadata(source_id, key, value, normalized_origin, snapshot_id=snapshot_id)

    def add_raw_artifact(
        self,
        snapshot_id: str,
        artifact_kind: str,
        storage_ref: str,
        sha256: str,
        byte_count: int,
        *,
        logical_path: str | None = None,
        media_type: str | None = None,
        artifact_id: str | None = None,
    ) -> str:
        artifact_id = artifact_id or new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO raw_artifacts VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    artifact_id,
                    snapshot_id,
                    artifact_kind,
                    logical_path,
                    storage_ref,
                    media_type,
                    sha256,
                    byte_count,
                    _now(),
                ),
            )
        return artifact_id

    def raw_artifacts(self, snapshot_id: str) -> tuple[dict, ...]:
        rows = self.db.execute(
            "SELECT * FROM raw_artifacts WHERE snapshot_id=? ORDER BY rowid", (snapshot_id,)
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def create_normalization_run(
        self,
        snapshot_id: str,
        extractor_key: str,
        extractor_version: str,
        artifact_ids: Iterable[str],
        *,
        configuration: object | None = None,
        output: object | None = None,
        status: NormalizationStatus | str = NormalizationStatus.COMPLETE,
        run_id: str | None = None,
    ) -> str:
        artifact_ids = tuple(dict.fromkeys(artifact_ids))
        if not artifact_ids:
            raise ValueError("Normalization run requires at least one Raw Artifact")
        run_id = run_id or new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO normalization_runs VALUES(?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    snapshot_id,
                    extractor_key.strip(),
                    extractor_version.strip(),
                    _json(configuration or {}),
                    _json(output or {}),
                    NormalizationStatus(status).value,
                    _now(),
                ),
            )
            self.db.executemany(
                "INSERT INTO normalization_run_artifacts VALUES(?,?,'input')",
                [(run_id, artifact_id) for artifact_id in artifact_ids],
            )
        return run_id

    def add_evidence(
        self,
        run_id: str,
        content: str,
        extraction_mode: EvidenceExtractionMode | str,
        *,
        ordinal: int | None = None,
        language: str | None = None,
        metadata: object | None = None,
        evidence_id: str | None = None,
    ) -> str:
        if not content:
            raise ValueError("Evidence content is required")
        parent = self.db.execute(
            """SELECT n.snapshot_id,s.source_id FROM normalization_runs n
               JOIN source_snapshots s ON s.id=n.snapshot_id WHERE n.id=?""",
            (run_id,),
        ).fetchone()
        if not parent:
            raise ValueError("Unknown normalization run ID")
        if ordinal is None:
            row = self.db.execute(
                "SELECT coalesce(max(ordinal),-1)+1 AS next FROM evidence_records WHERE run_id=?",
                (run_id,),
            ).fetchone()
            ordinal = row["next"]
        evidence_id = evidence_id or new_persistent_id()
        with self.db:
            self.db.execute(
                """INSERT INTO evidence_records
                   (id,run_id,snapshot_id,source_id,ordinal,content,content_hash,
                    extraction_mode,language,metadata_json,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    evidence_id,
                    run_id,
                    parent["snapshot_id"],
                    parent["source_id"],
                    ordinal,
                    content,
                    _digest(content),
                    EvidenceExtractionMode(extraction_mode).value,
                    language,
                    _json(metadata or {}),
                    _now(),
                ),
            )
        return evidence_id

    def evidence_by_id(self, evidence_id: str) -> EvidenceRecord:
        row = self.db.execute(
            "SELECT * FROM evidence_records WHERE id=?", (evidence_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown evidence ID")
        return self._evidence_record(row)

    def add_evidence_location(
        self, evidence_id: str, kind: str, value: object, *, ordinal: int = 0
    ) -> str:
        location_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO evidence_locations VALUES(?,?,?,?,?,?)",
                (location_id, evidence_id, ordinal, kind, _json(value), _now()),
            )
        return location_id

    def normalization_run(self, run_id: str) -> dict:
        row = self.db.execute("SELECT * FROM normalization_runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            raise ValueError("Unknown normalization run ID")
        return dict(row)

    def select_effective_snapshot(
        self,
        source_id: str,
        snapshot_id: str,
        *,
        origin_kind: str = "manual",
        reason: str,
    ) -> str:
        self.source_by_id(source_id)
        snapshot = self.snapshot_by_id(snapshot_id)
        if snapshot.source_id != source_id:
            raise ValueError("Effective snapshot must belong to source")
        if snapshot.completeness is SnapshotCompleteness.FAILED:
            raise ValueError("Failed snapshot cannot be effective")
        selection_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO source_selection_events VALUES(?,?,?,?,?,?,?,?)",
                (
                    selection_id,
                    source_id,
                    "snapshot",
                    snapshot_id,
                    None,
                    origin_kind,
                    reason.strip(),
                    _now(),
                ),
            )
        return selection_id

    def effective_snapshot(self, source_id: str) -> SourceSnapshotRecord | None:
        row = self.db.execute(
            """SELECT s.* FROM source_selection_events e
               JOIN source_snapshots s ON s.id=e.snapshot_id
               WHERE e.source_id=? AND e.selection_kind='snapshot'
               ORDER BY e.rowid DESC LIMIT 1""",
            (source_id,),
        ).fetchone()
        return self._snapshot_record(row) if row else None

    def select_effective_run(
        self,
        snapshot_id: str,
        run_id: str,
        *,
        origin_kind: str = "manual",
        reason: str,
    ) -> str:
        snapshot = self.snapshot_by_id(snapshot_id)
        run = self.normalization_run(run_id)
        if run["snapshot_id"] != snapshot_id:
            raise ValueError("Effective run must belong to snapshot")
        if run["status"] == NormalizationStatus.FAILED.value:
            raise ValueError("Failed normalization run cannot be effective")
        selection_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO source_selection_events VALUES(?,?,?,?,?,?,?,?)",
                (
                    selection_id,
                    snapshot.source_id,
                    "run",
                    snapshot_id,
                    run_id,
                    origin_kind,
                    reason.strip(),
                    _now(),
                ),
            )
        return selection_id

    def effective_run(self, snapshot_id: str) -> dict | None:
        row = self.db.execute(
            """SELECT n.* FROM source_selection_events e
               JOIN normalization_runs n ON n.id=e.run_id
               WHERE e.snapshot_id=? AND e.selection_kind='run'
               ORDER BY e.rowid DESC LIMIT 1""",
            (snapshot_id,),
        ).fetchone()
        return dict(row) if row else None

    def associate_object(
        self,
        source_id: str,
        object_id: str,
        status: AssociationStatus | str,
        *,
        subject_relationship: str | None = None,
        origin_kind: str = "manual",
        note: str | None = None,
    ) -> None:
        status = AssociationStatus(status)
        timestamp = _now()
        with self.db:
            self.db.execute(
                """INSERT INTO source_object_associations
                   VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(source_id,object_id) DO UPDATE SET
                     status=excluded.status,
                     subject_relationship=excluded.subject_relationship,
                     origin_kind=excluded.origin_kind,
                     note=excluded.note,
                     updated_at=excluded.updated_at""",
                (
                    source_id,
                    object_id,
                    status.value,
                    subject_relationship,
                    origin_kind,
                    note,
                    timestamp,
                    timestamp,
                ),
            )

    def relate_sources(
        self,
        subject_source_id: str,
        relation_key: str,
        object_source_id: str,
        *,
        origin_kind: str = "manual",
        note: str | None = None,
    ) -> str:
        relation_type = self.db.execute(
            "SELECT id FROM source_relation_types WHERE key=? AND status='active'", (relation_key,)
        ).fetchone()
        if not relation_type:
            raise ValueError("Unknown or inactive Source relation type")
        relation_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO source_relations VALUES(?,?,?,?,?,?,?)",
                (
                    relation_id,
                    subject_source_id,
                    relation_type["id"],
                    object_source_id,
                    origin_kind,
                    note,
                    _now(),
                ),
            )
        return relation_id

    def link_evidence(
        self,
        version_id: str,
        target_kind: EvidenceTargetKind | str,
        target_id: str,
        evidence_id: str,
        role: EvidenceRole | str = EvidenceRole.SUPPORTS,
        *,
        origin_kind: str = "result_import",
        origin_ref: str | None = None,
    ) -> str:
        target_kind = EvidenceTargetKind(target_kind)
        role = EvidenceRole(role)
        role_row = self.db.execute(
            "SELECT id FROM evidence_roles WHERE key=? AND status='active'", (role.value,)
        ).fetchone()
        if not role_row:
            raise ValueError("Unknown or inactive Evidence role")
        link_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO evidence_links VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    link_id,
                    version_id,
                    target_kind.value,
                    target_id,
                    evidence_id,
                    role_row["id"],
                    origin_kind,
                    origin_ref,
                    _now(),
                ),
            )
        return link_id

    def evidence_provenance(self, evidence_id: str) -> EvidenceProvenance:
        evidence = self.evidence_by_id(evidence_id)
        snapshot = self.snapshot_by_id(evidence.snapshot_id)
        source = self.source_by_id(evidence.source_id)
        artifact_ids = tuple(
            row["artifact_id"]
            for row in self.db.execute(
                """SELECT artifact_id FROM normalization_run_artifacts
                   WHERE run_id=? ORDER BY artifact_id""",
                (evidence.run_id,),
            )
        )
        if not artifact_ids:
            raise ValueError("Evidence provenance has no Raw Artifact")
        return EvidenceProvenance(evidence, snapshot, source, artifact_ids)

    def validate_source_references(self, source_ids: Iterable[str]) -> tuple[str, ...]:
        requested = tuple(dict.fromkeys(source_ids))
        for source_id in requested:
            self.source_by_id(source_id)
        return requested

    def validate_evidence_references(
        self,
        evidence_ids: Iterable[str],
        *,
        package_evidence_ids: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        requested = tuple(dict.fromkeys(evidence_ids))
        if not requested:
            raise ValueError("At least one Evidence reference is required")
        package = set(package_evidence_ids) if package_evidence_ids is not None else None
        for evidence_id in requested:
            if package is not None and evidence_id not in package:
                raise ValueError(f"Evidence {evidence_id} is outside the input Package")
            self.evidence_provenance(evidence_id)
        return requested

    def evidence_links_for_target(
        self, version_id: str, target_kind: EvidenceTargetKind | str, target_id: str
    ) -> tuple[EvidenceLinkRecord, ...]:
        target_kind = EvidenceTargetKind(target_kind)
        rows = self.db.execute(
            """SELECT l.*,r.key AS role_key FROM evidence_links l
               JOIN evidence_roles r ON r.id=l.role_id
               WHERE l.version_id=? AND l.target_kind=? AND l.target_id=?
               ORDER BY l.rowid""",
            (version_id, target_kind.value, target_id),
        ).fetchall()
        return tuple(
            EvidenceLinkRecord(
                link_id=row["id"],
                version_id=row["version_id"],
                target_kind=EvidenceTargetKind(row["target_kind"]),
                target_id=row["target_id"],
                evidence_id=row["evidence_id"],
                role=EvidenceRole(row["role_key"]),
                origin_kind=row["origin_kind"],
                origin_ref=row["origin_ref"],
            )
            for row in rows
        )

    def associations_for_object(self, object_id: str) -> tuple[dict, ...]:
        rows = self.db.execute(
            """SELECT source_id,object_id,status,subject_relationship,origin_kind,note
               FROM source_object_associations
               WHERE object_id=? ORDER BY source_id""",
            (object_id,),
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def effective_evidence_rows(self, source_ids: Iterable[str] | None = None) -> tuple[dict, ...]:
        source_ids = tuple(dict.fromkeys(source_ids or ()))
        where = ""
        parameters: list[str] = []
        if source_ids:
            placeholders = ",".join("?" for _ in source_ids)
            where = f" AND er.source_id IN ({placeholders})"
            parameters.extend(source_ids)
        rows = self.db.execute(
            """WITH latest_snapshot AS (
                   SELECT e.source_id,e.snapshot_id
                   FROM source_selection_events e
                   JOIN (
                     SELECT source_id,max(rowid) AS rid
                     FROM source_selection_events
                     WHERE selection_kind='snapshot'
                     GROUP BY source_id
                   ) x ON x.rid=e.rowid
               ), latest_run AS (
                   SELECT e.snapshot_id,e.run_id
                   FROM source_selection_events e
                   JOIN (
                     SELECT snapshot_id,max(rowid) AS rid
                     FROM source_selection_events
                     WHERE selection_kind='run'
                     GROUP BY snapshot_id
                   ) x ON x.rid=e.rowid
               )
               SELECT er.* FROM evidence_records er
               JOIN latest_snapshot s
                 ON s.source_id=er.source_id AND s.snapshot_id=er.snapshot_id
               JOIN latest_run r
                 ON r.snapshot_id=er.snapshot_id AND r.run_id=er.run_id
               WHERE 1=1"""
            + where
            + " ORDER BY er.source_id,er.snapshot_id,er.ordinal,er.id",
            parameters,
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def lexical_evidence_rows(
        self,
        query: str,
        *,
        source_ids: Iterable[str] | None = None,
        limit: int = 200,
    ) -> tuple[dict, ...]:
        query = query.strip()
        if not query:
            return ()
        if not 1 <= limit <= 5000:
            raise ValueError("Evidence lexical limit must be 1..5000")
        source_ids = tuple(dict.fromkeys(source_ids or ()))
        source_filter = ""
        parameters: list[object] = [query]
        if source_ids:
            placeholders = ",".join("?" for _ in source_ids)
            source_filter = f" AND er.source_id IN ({placeholders})"
            parameters.extend(source_ids)
        parameters.append(limit)
        rows = self.db.execute(
            """WITH latest_snapshot AS (
                   SELECT e.source_id,e.snapshot_id
                   FROM source_selection_events e
                   JOIN (
                     SELECT source_id,max(rowid) AS rid
                     FROM source_selection_events
                     WHERE selection_kind='snapshot'
                     GROUP BY source_id
                   ) x ON x.rid=e.rowid
               ), latest_run AS (
                   SELECT e.snapshot_id,e.run_id
                   FROM source_selection_events e
                   JOIN (
                     SELECT snapshot_id,max(rowid) AS rid
                     FROM source_selection_events
                     WHERE selection_kind='run'
                     GROUP BY snapshot_id
                   ) x ON x.rid=e.rowid
               )
               SELECT er.*,bm25(evidence_retrieval_fts) AS lexical_rank_score
               FROM evidence_retrieval_fts
               JOIN evidence_records er ON er.rowid=evidence_retrieval_fts.rowid
               JOIN latest_snapshot s
                 ON s.source_id=er.source_id AND s.snapshot_id=er.snapshot_id
               JOIN latest_run r
                 ON r.snapshot_id=er.snapshot_id AND r.run_id=er.run_id
               WHERE evidence_retrieval_fts MATCH ?"""
            + source_filter
            + " ORDER BY lexical_rank_score,er.id LIMIT ?",
            parameters,
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def metadata_matching_sources(self, terms: Iterable[str]) -> dict[str, tuple[str, ...]]:
        normalized = tuple(dict.fromkeys(term.strip().casefold() for term in terms if term.strip()))
        if not normalized:
            return {}
        rows = self.db.execute(
            """WITH latest_snapshot AS (
                 SELECT e.source_id,e.snapshot_id
                 FROM source_selection_events e
                 JOIN (
                   SELECT source_id,max(rowid) AS rid
                   FROM source_selection_events
                   WHERE selection_kind='snapshot'
                   GROUP BY source_id
                 ) x ON x.rid=e.rowid
               )
               SELECT source_id,kind,value FROM (
                 SELECT id AS source_id,'source_label' AS kind,coalesce(label,'') AS value
                 FROM source_records WHERE status='active'
                 UNION ALL
                 SELECT source_id,'locator:' || kind,value
                 FROM source_locators WHERE status='active'
                 UNION ALL
                 SELECT c.source_id,'classification:' || c.axis,c.value
                 FROM source_classifications c
                 LEFT JOIN latest_snapshot s ON s.source_id=c.source_id
                 WHERE c.snapshot_id IS NULL OR c.snapshot_id=s.snapshot_id
                 UNION ALL
                 SELECT m.source_id,'metadata:' || m.key,m.value_json
                 FROM source_metadata_values m
                 LEFT JOIN latest_snapshot s ON s.source_id=m.source_id
                 WHERE m.snapshot_id IS NULL OR m.snapshot_id=s.snapshot_id
                 UNION ALL
                 SELECT ss.source_id,'snapshot_title',coalesce(ss.title,'')
                 FROM source_snapshots ss
                 JOIN latest_snapshot s
                   ON s.source_id=ss.source_id AND s.snapshot_id=ss.id
               )
               ORDER BY source_id,kind,value"""
        ).fetchall()
        matches: dict[str, list[str]] = {}
        for row in rows:
            value = row["value"].casefold()
            hit = next((term for term in normalized if term in value), None)
            if hit is not None:
                matches.setdefault(row["source_id"], []).append(f"{row['kind']}:{hit}")
        return {key: tuple(dict.fromkeys(values)) for key, values in matches.items()}

    def evidence_context(self, evidence_id: str) -> dict:
        row = self.db.execute(
            """SELECT er.*,ss.title AS snapshot_title,sr.label AS source_label
               FROM evidence_records er
               JOIN source_snapshots ss ON ss.id=er.snapshot_id
               JOIN source_records sr ON sr.id=er.source_id
               WHERE er.id=?""",
            (evidence_id,),
        ).fetchone()
        if not row:
            raise ValueError("Unknown evidence ID")
        locators = [
            {"kind": item["kind"], "value": item["value"], "preferred": bool(item["is_preferred"])}
            for item in self.db.execute(
                """SELECT kind,value,is_preferred FROM source_locators
                   WHERE source_id=? AND status='active'
                   ORDER BY is_preferred DESC,rowid""",
                (row["source_id"],),
            )
        ]
        locations = [
            {
                "kind": item["kind"],
                "value": json.loads(item["value_json"]),
                "ordinal": item["ordinal"],
            }
            for item in self.db.execute(
                """SELECT kind,value_json,ordinal FROM evidence_locations
                   WHERE evidence_id=? ORDER BY ordinal,rowid""",
                (evidence_id,),
            )
        ]
        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        result["locators"] = locators
        result["locations"] = locations
        return result
