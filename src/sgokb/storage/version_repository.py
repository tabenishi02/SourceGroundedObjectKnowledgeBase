"""Object Knowledge Version lifecycle persistence for Phase E / E-04."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from sgokb.domain.object import new_persistent_id
from sgokb.domain.version import (
    DerivedState,
    DerivedStateRecord,
    ObjectVersionRecord,
    StaleVersionError,
    VersionClassificationSnapshot,
    VersionState,
)

DEFAULT_DERIVED_KINDS = (
    "search_representation",
    "embedding",
    "vector_index",
    "rendering",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class VersionRepository:
    """Transactional lifecycle and current-pointer operations for Object Versions."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def _require_idle_transaction(self) -> None:
        if self.db.in_transaction:
            raise RuntimeError("Version lifecycle operation requires an outer-transaction boundary")

    def _record(self, row: sqlite3.Row | dict) -> ObjectVersionRecord:
        additional = tuple(
            item["class_id"]
            for item in self.db.execute(
                """SELECT class_id FROM object_version_additional_class_snapshots
                   WHERE version_id=? ORDER BY class_id""",
                (row["id"],),
            )
        )
        classification = self.db.execute(
            "SELECT primary_class_id FROM object_version_classification_snapshots "
            "WHERE version_id=?",
            (row["id"],),
        ).fetchone()
        if not classification:
            raise ValueError("Version is missing its classification snapshot")
        return ObjectVersionRecord(
            version_id=row["id"],
            object_id=row["object_id"],
            version_number=row["version_number"],
            base_version_id=row["base_version_id"],
            state=VersionState(row["state"]),
            snapshot_kind=row["snapshot_kind"],
            created_at=row["created_at"],
            accepted_at=row["accepted_at"],
            abandoned_at=row["abandoned_at"],
            classification=VersionClassificationSnapshot(
                primary_class_id=classification["primary_class_id"],
                additional_class_ids=additional,
            ),
        )

    def version_by_id(self, version_id: str) -> ObjectVersionRecord:
        row = self.db.execute(
            """SELECT v.*,l.base_version_id,l.state,l.snapshot_kind,l.accepted_at,l.abandoned_at
               FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id
               WHERE v.id=?""",
            (version_id,),
        ).fetchone()
        if not row:
            raise ValueError("Unknown Object Knowledge Version ID")
        return self._record(row)

    def versions_for_object(self, object_id: str) -> tuple[ObjectVersionRecord, ...]:
        rows = self.db.execute(
            """SELECT v.*,l.base_version_id,l.state,l.snapshot_kind,l.accepted_at,l.abandoned_at
               FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id
               WHERE v.object_id=? ORDER BY v.version_number""",
            (object_id,),
        ).fetchall()
        return tuple(self._record(row) for row in rows)

    def current_version_id(self, object_id: str) -> str | None:
        row = self.db.execute(
            "SELECT current_version_id FROM objects WHERE id=?", (object_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown Object ID")
        return row["current_version_id"]

    def begin_candidate(
        self,
        object_id: str,
        base_version_id: str | None,
        *,
        version_id: str | None = None,
    ) -> str:
        """Create a full-snapshot candidate iff the expected base is still current."""

        self._require_idle_transaction()
        version_id = version_id or new_persistent_id()
        timestamp = _now()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            current = self.current_version_id(object_id)
            if current != base_version_id:
                raise StaleVersionError(
                    f"Expected base {base_version_id!r}, but current version is {current!r}"
                )
            row = self.db.execute(
                "SELECT coalesce(max(version_number),0)+1 AS next "
                "FROM object_versions WHERE object_id=?",
                (object_id,),
            ).fetchone()
            self.db.execute(
                "INSERT INTO object_versions VALUES(?,?,?,?)",
                (version_id, object_id, row["next"], timestamp),
            )
            self._event(
                version_id,
                "candidate_created",
                {"base_version_id": base_version_id, "snapshot_kind": "full"},
                timestamp,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return version_id

    def abandon_candidate(self, version_id: str, *, reason: str | None = None) -> None:
        self._require_idle_transaction()
        timestamp = _now()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                """SELECT l.state FROM object_version_lifecycle l WHERE l.version_id=?""",
                (version_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown Object Knowledge Version ID")
            if row["state"] != VersionState.CANDIDATE.value:
                raise ValueError("Only candidate Versions may be abandoned")
            self.db.execute(
                """UPDATE object_version_lifecycle
                   SET state='abandoned',abandoned_at=? WHERE version_id=?""",
                (timestamp, version_id),
            )
            self._event(version_id, "candidate_abandoned", {"reason": reason}, timestamp)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def accept_candidate(
        self,
        version_id: str,
        *,
        derived_kinds: tuple[str, ...] = DEFAULT_DERIVED_KINDS,
    ) -> ObjectVersionRecord:
        """Atomically accept a candidate and promote it to current.

        Derived artifacts are not generated in this transaction. Only their mutable
        synchronization state is advanced to a new pending revision.
        """

        self._require_idle_transaction()
        timestamp = _now()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                """SELECT v.object_id,l.state,l.base_version_id
                   FROM object_versions v
                   JOIN object_version_lifecycle l ON l.version_id=v.id
                   WHERE v.id=?""",
                (version_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown Object Knowledge Version ID")
            if row["state"] != VersionState.CANDIDATE.value:
                raise ValueError("Only candidate Versions may be accepted")
            current = self.current_version_id(row["object_id"])
            if current != row["base_version_id"]:
                raise StaleVersionError(
                    "Candidate base "
                    f"{row['base_version_id']!r} no longer matches current {current!r}"
                )
            current_class = self.db.execute(
                "SELECT primary_class_id FROM objects WHERE id=?", (row["object_id"],)
            ).fetchone()["primary_class_id"]
            snapshot_class = self.db.execute(
                "SELECT primary_class_id FROM object_version_classification_snapshots "
            "WHERE version_id=?",
                (version_id,),
            ).fetchone()
            if not snapshot_class or snapshot_class["primary_class_id"] != current_class:
                raise StaleVersionError("Candidate classification snapshot is stale")
            current_additional = {
                item["class_id"]
                for item in self.db.execute(
                    "SELECT class_id FROM object_additional_classes WHERE object_id=?",
                    (row["object_id"],),
                )
            }
            snapshot_additional = {
                item["class_id"]
                for item in self.db.execute(
                    "SELECT class_id FROM object_version_additional_class_snapshots "
                    "WHERE version_id=?",
                    (version_id,),
                )
            }
            if current_additional != snapshot_additional:
                raise StaleVersionError("Candidate classification snapshot is stale")

            self.db.execute(
                """UPDATE object_version_lifecycle
                   SET state='accepted',accepted_at=? WHERE version_id=?""",
                (timestamp, version_id),
            )
            self.db.execute(
                "UPDATE objects SET current_version_id=?,updated_at=? WHERE id=?",
                (version_id, timestamp, row["object_id"]),
            )
            self._queue_derived(row["object_id"], version_id, derived_kinds, timestamp)
            self._event(
                version_id,
                "accepted_and_promoted",
                {"previous_current_version_id": current},
                timestamp,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.version_by_id(version_id)

    def rollback_current(
        self,
        object_id: str,
        target_version_id: str,
        *,
        derived_kinds: tuple[str, ...] = DEFAULT_DERIVED_KINDS,
    ) -> ObjectVersionRecord:
        """Point current Knowledge at an older accepted immutable Version."""

        self._require_idle_transaction()
        timestamp = _now()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            target = self.db.execute(
                """SELECT v.id,v.object_id,l.state
                   FROM object_versions v
                   JOIN object_version_lifecycle l ON l.version_id=v.id
                   WHERE v.id=?""",
                (target_version_id,),
            ).fetchone()
            if not target or target["object_id"] != object_id:
                raise ValueError("Rollback target must belong to the Object")
            if target["state"] != VersionState.ACCEPTED.value:
                raise ValueError("Rollback target must be an accepted Version")
            previous = self.current_version_id(object_id)
            if previous == target_version_id:
                self.db.commit()
                return self.version_by_id(target_version_id)
            self.db.execute(
                "UPDATE objects SET current_version_id=?,updated_at=? WHERE id=?",
                (target_version_id, timestamp, object_id),
            )
            self._queue_derived(object_id, target_version_id, derived_kinds, timestamp)
            self._event(
                target_version_id,
                "rollback_promoted",
                {"previous_current_version_id": previous},
                timestamp,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.version_by_id(target_version_id)

    def derived_states(self, object_id: str) -> tuple[DerivedStateRecord, ...]:
        rows = self.db.execute(
            "SELECT * FROM object_derived_states WHERE object_id=? ORDER BY kind", (object_id,)
        ).fetchall()
        return tuple(
            DerivedStateRecord(
                object_id=row["object_id"],
                kind=row["kind"],
                target_version_id=row["target_version_id"],
                status=DerivedState(row["status"]),
                revision=row["revision"],
                last_error=row["last_error"],
                updated_at=row["updated_at"],
            )
            for row in rows
        )

    def mark_derived_state(
        self,
        object_id: str,
        kind: str,
        revision: int,
        status: DerivedState | str,
        *,
        error: str | None = None,
    ) -> bool:
        status = DerivedState(status)
        if status is DerivedState.READY and error is not None:
            raise ValueError("ready derived state cannot carry an error")
        timestamp = _now()
        with self.db:
            cursor = self.db.execute(
                """UPDATE object_derived_states
                   SET status=?,last_error=?,updated_at=?
                   WHERE object_id=? AND kind=? AND revision=?""",
                (status.value, error, timestamp, object_id, kind, revision),
            )
        return cursor.rowcount == 1

    def _queue_derived(
        self, object_id: str, target_version_id: str, kinds: tuple[str, ...], timestamp: str
    ) -> None:
        for kind in dict.fromkeys(k.strip() for k in kinds if k.strip()):
            self.db.execute(
                """INSERT INTO object_derived_states
                   (object_id,kind,target_version_id,status,revision,last_error,updated_at)
                   VALUES(?,?,?,'pending',1,NULL,?)
                   ON CONFLICT(object_id,kind) DO UPDATE SET
                     target_version_id=excluded.target_version_id,
                     status='pending',
                     revision=object_derived_states.revision+1,
                     last_error=NULL,
                     updated_at=excluded.updated_at""",
                (object_id, kind, target_version_id, timestamp),
            )

    def _event(self, version_id: str, event_type: str, payload: object, timestamp: str) -> None:
        self.db.execute(
            "INSERT INTO object_version_events VALUES(?,?,?,?,?)",
            (new_persistent_id(), version_id, event_type, _json(payload), timestamp),
        )
