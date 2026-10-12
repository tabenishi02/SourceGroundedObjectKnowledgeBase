"""Persistence operations for the Phase E canonical Object registry.

This module intentionally stops at E-01 boundaries. Knowledge content, version
promotion, Evidence grounding, and Result import are implemented by later tasks.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable

from sgokb.domain.object import (
    AssignmentPolicy,
    LifecycleStatus,
    ObjectAliasRecord,
    ObjectClassRecord,
    ObjectRecord,
    RelationTypeRecord,
    new_persistent_id,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class ObjectRepository:
    """Canonical Object registry persistence backed by an existing SQLite connection."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    @staticmethod
    def _class_record(row: sqlite3.Row | dict) -> ObjectClassRecord:
        return ObjectClassRecord(
            class_id=row["id"],
            key=row["key"],
            name=row["name"],
            description=row["description"],
            assignment_policy=AssignmentPolicy(row["assignment_policy"]),
            status=LifecycleStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def class_by_id(self, class_id: str) -> ObjectClassRecord | None:
        row = self.db.execute("SELECT * FROM object_classes WHERE id=?", (class_id,)).fetchone()
        return self._class_record(row) if row else None

    def class_by_key(self, key: str) -> ObjectClassRecord | None:
        row = self.db.execute("SELECT * FROM object_classes WHERE key=?", (key,)).fetchone()
        return self._class_record(row) if row else None

    def classes(self) -> list[ObjectClassRecord]:
        rows = self.db.execute("SELECT * FROM object_classes ORDER BY key").fetchall()
        return [self._class_record(row) for row in rows]

    def ancestor_class_ids(self, class_id: str) -> tuple[str, ...]:
        rows = self.db.execute(
            """WITH RECURSIVE ancestors(id) AS (
                   SELECT parent_class_id FROM object_class_parents WHERE child_class_id=?
                   UNION
                   SELECT p.parent_class_id
                   FROM object_class_parents p JOIN ancestors a ON p.child_class_id=a.id
               )
               SELECT id FROM ancestors ORDER BY id""",
            (class_id,),
        ).fetchall()
        return tuple(row["id"] for row in rows)

    def create_object(
        self,
        name: str,
        primary_class_id: str,
        aliases: Iterable[str] = (),
        *,
        object_id: str | None = None,
    ) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Object name is required")
        object_id = object_id or new_persistent_id()
        timestamp = _now()
        unique_aliases = tuple(dict.fromkeys(a.strip() for a in aliases if a.strip()))
        with self.db:
            self.db.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?,?,?)",
                (object_id, name, primary_class_id, "active", None, timestamp, timestamp),
            )
            for alias in unique_aliases:
                self._insert_alias(object_id, alias, None, "alias", timestamp)
            self._event(
                object_id,
                "object_created",
                {"name": name, "primary_class_id": primary_class_id},
                timestamp,
            )
        return object_id

    def get_object(self, object_id: str) -> ObjectRecord:
        row = self.db.execute("SELECT * FROM objects WHERE id=?", (object_id,)).fetchone()
        if not row:
            raise ValueError("Unknown object ID")
        aliases = tuple(
            ObjectAliasRecord(
                alias_id=item["id"],
                value=item["value"],
                language=item["language"],
                kind=item["kind"],
            )
            for item in self.db.execute(
                "SELECT * FROM object_aliases WHERE object_id=? ORDER BY rowid", (object_id,)
            )
        )
        additional = tuple(
            item["class_id"]
            for item in self.db.execute(
                "SELECT class_id FROM object_additional_classes "
                "WHERE object_id=? ORDER BY class_id",
                (object_id,),
            )
        )
        return ObjectRecord(
            object_id=row["id"],
            name=row["name"],
            primary_class_id=row["primary_class_id"],
            status=LifecycleStatus(row["status"]),
            current_version_id=row["current_version_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            aliases=aliases,
            additional_class_ids=additional,
        )

    def list_objects(self) -> list[ObjectRecord]:
        ids = [row["id"] for row in self.db.execute("SELECT id FROM objects ORDER BY name,id")]
        return [self.get_object(object_id) for object_id in ids]

    def rename_object(self, object_id: str, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Object name is required")
        current = self.get_object(object_id)
        if current.name == name:
            return
        timestamp = _now()
        with self.db:
            self.db.execute(
                "UPDATE objects SET name=?,updated_at=? WHERE id=?",
                (name, timestamp, object_id),
            )
            self._event(
                object_id,
                "name_changed",
                {"before": current.name, "after": name},
                timestamp,
            )

    def set_status(self, object_id: str, status: LifecycleStatus | str) -> None:
        status = LifecycleStatus(status)
        current = self.get_object(object_id)
        if current.status == status:
            return
        timestamp = _now()
        with self.db:
            self.db.execute(
                "UPDATE objects SET status=?,updated_at=? WHERE id=?",
                (status.value, timestamp, object_id),
            )
            self._event(
                object_id,
                "status_changed",
                {"before": current.status.value, "after": status.value},
                timestamp,
            )

    def set_primary_class(self, object_id: str, class_id: str) -> None:
        current = self.get_object(object_id)
        if current.primary_class_id == class_id:
            return
        timestamp = _now()
        with self.db:
            self.db.execute(
                "UPDATE objects SET primary_class_id=?,updated_at=? WHERE id=?",
                (class_id, timestamp, object_id),
            )
            self._event(
                object_id,
                "primary_class_changed",
                {"before": current.primary_class_id, "after": class_id},
                timestamp,
            )

    def add_additional_class(self, object_id: str, class_id: str) -> None:
        timestamp = _now()
        with self.db:
            self.db.execute(
                "INSERT INTO object_additional_classes VALUES(?,?,?)",
                (object_id, class_id, timestamp),
            )
            self.db.execute("UPDATE objects SET updated_at=? WHERE id=?", (timestamp, object_id))
            self._event(object_id, "additional_class_added", {"class_id": class_id}, timestamp)

    def remove_additional_class(self, object_id: str, class_id: str) -> None:
        timestamp = _now()
        with self.db:
            cursor = self.db.execute(
                "DELETE FROM object_additional_classes WHERE object_id=? AND class_id=?",
                (object_id, class_id),
            )
            if cursor.rowcount == 0:
                return
            self.db.execute("UPDATE objects SET updated_at=? WHERE id=?", (timestamp, object_id))
            self._event(object_id, "additional_class_removed", {"class_id": class_id}, timestamp)

    def add_alias(
        self,
        object_id: str,
        value: str,
        *,
        language: str | None = None,
        kind: str = "alias",
    ) -> str:
        value = value.strip()
        kind = kind.strip()
        if not value or not kind:
            raise ValueError("Alias value and kind are required")
        timestamp = _now()
        alias_id = new_persistent_id()
        with self.db:
            self._insert_alias(object_id, value, language, kind, timestamp, alias_id=alias_id)
            self.db.execute("UPDATE objects SET updated_at=? WHERE id=?", (timestamp, object_id))
            self._event(
                object_id,
                "alias_added",
                {"alias_id": alias_id, "value": value, "language": language, "kind": kind},
                timestamp,
            )
        return alias_id

    def stage_class_proposal(
        self,
        proposed_key: str,
        display_name: str,
        rationale: str,
        *,
        description: str = "",
        payload: dict | None = None,
    ) -> str:
        proposed_key = proposed_key.strip()
        display_name = display_name.strip()
        rationale = rationale.strip()
        if not proposed_key or not display_name or not rationale:
            raise ValueError("Class proposal key, display name, and rationale are required")
        proposal_id = new_persistent_id()
        with self.db:
            self.db.execute(
                """INSERT INTO object_class_proposals
                   (id,proposed_key,display_name,description,rationale,payload,status,
                    resolved_class_id,created_at,reviewed_at)
                   VALUES(?,?,?,?,?,?,?,NULL,?,NULL)""",
                (
                    proposal_id,
                    proposed_key,
                    display_name,
                    description,
                    rationale,
                    _json(payload or {}),
                    "pending",
                    _now(),
                ),
            )
        return proposal_id

    def register_relation_type(
        self,
        key: str,
        name: str,
        *,
        description: str = "",
        relation_type_id: str | None = None,
    ) -> str:
        key = key.strip()
        name = name.strip()
        if not key or not name:
            raise ValueError("Relation type key and name are required")
        relation_type_id = relation_type_id or f"relation:{key}"
        timestamp = _now()
        with self.db:
            self.db.execute(
                "INSERT INTO relation_types VALUES(?,?,?,?,?,?,?)",
                (
                    relation_type_id,
                    key,
                    name,
                    description,
                    "active",
                    timestamp,
                    timestamp,
                ),
            )
        return relation_type_id

    def registry_events(self, object_id: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM object_registry_events WHERE object_id=? ORDER BY created_at,rowid",
            (object_id,),
        ).fetchall()
        return [dict(row, payload=json.loads(row["payload"])) for row in rows]

    def _insert_alias(
        self,
        object_id: str,
        value: str,
        language: str | None,
        kind: str,
        timestamp: str,
        *,
        alias_id: str | None = None,
    ) -> str:
        alias_id = alias_id or new_persistent_id()
        self.db.execute(
            "INSERT INTO object_aliases VALUES(?,?,?,?,?,?)",
            (alias_id, object_id, value, language, kind, timestamp),
        )
        return alias_id

    def _event(self, object_id: str, event_type: str, payload: dict, timestamp: str) -> None:
        self.db.execute(
            "INSERT INTO object_registry_events VALUES(?,?,?,?,?)",
            (new_persistent_id(), object_id, event_type, _json(payload), timestamp),
        )

    def relation_type_by_key(self, key: str) -> RelationTypeRecord | None:
        row = self.db.execute("SELECT * FROM relation_types WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        return RelationTypeRecord(
            relation_type_id=row["id"],
            key=row["key"],
            name=row["name"],
            description=row["description"],
            status=LifecycleStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
