"""Persistence for E-02 semantic facets and versioned knowledge content."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable

from sgokb.domain.knowledge import (
    AttributeDefinitionRecord,
    AttributeStatus,
    AttributeValueType,
    DerivationKind,
    FacetDefinitionRecord,
    FacetStatus,
    SearchRepresentationKind,
    SearchRepresentationRecord,
)
from sgokb.domain.object import new_persistent_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SemanticRepository:
    """Version-scoped semantic knowledge persistence for the canonical Object model."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    @staticmethod
    def _facet_record(row: sqlite3.Row | dict) -> FacetDefinitionRecord:
        return FacetDefinitionRecord(
            facet_id=row["id"],
            key=row["key"],
            name=row["name"],
            description=row["description"],
            is_common=bool(row["is_common"]),
            status=row["status"],
        )

    def facet_by_key(self, key: str) -> FacetDefinitionRecord | None:
        row = self.db.execute("SELECT * FROM facet_definitions WHERE key=?", (key,)).fetchone()
        return self._facet_record(row) if row else None

    def facets_for_classes(self, class_ids: Iterable[str]) -> tuple[FacetDefinitionRecord, ...]:
        result: dict[str, FacetDefinitionRecord] = {}
        for row in self.db.execute(
            "SELECT * FROM facet_definitions WHERE status='active' AND is_common=1 ORDER BY key"
        ):
            record = self._facet_record(row)
            result[record.facet_id] = record

        for class_id in dict.fromkeys(class_ids):
            rows = self.db.execute(
                """WITH RECURSIVE lineage(id,depth) AS (
                       SELECT ?,0
                       UNION
                       SELECT p.parent_class_id,lineage.depth+1
                       FROM object_class_parents p
                       JOIN lineage ON p.child_class_id=lineage.id
                   )
                   SELECT f.*,p.position,lineage.depth,p.inherit_to_descendants
                   FROM lineage
                   JOIN class_facet_profiles p ON p.class_id=lineage.id
                   JOIN facet_definitions f ON f.id=p.facet_id
                   WHERE f.status='active'
                     AND (lineage.depth=0 OR p.inherit_to_descendants=1)
                   ORDER BY p.position,f.key""",
                (class_id,),
            ).fetchall()
            for row in rows:
                record = self._facet_record(row)
                result.setdefault(record.facet_id, record)
        return tuple(result.values())

    def set_version_facet(
        self, version_id: str, facet_id: str, status: FacetStatus | str = FacetStatus.CONTENT
    ) -> None:
        status = FacetStatus(status)
        row = self.db.execute(
            "SELECT 1 FROM object_version_facets WHERE version_id=? AND facet_id=?",
            (version_id, facet_id),
        ).fetchone()
        with self.db:
            if row:
                self.db.execute(
                    "UPDATE object_version_facets SET status=? WHERE version_id=? AND facet_id=?",
                    (status.value, version_id, facet_id),
                )
            else:
                self.db.execute(
                    "INSERT INTO object_version_facets VALUES(?,?,?,?)",
                    (version_id, facet_id, status.value, _now()),
                )

    def create_temporal_scope(
        self,
        version_id: str,
        *,
        as_of: str | None = None,
        valid_from: str | None = None,
        valid_to: str | None = None,
        context_object_id: str | None = None,
        label: str | None = None,
    ) -> str:
        if not any((as_of, valid_from, valid_to, context_object_id, label)):
            raise ValueError("Temporal scope requires at least one boundary or context")
        scope_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO temporal_scopes VALUES(?,?,?,?,?,?,?,?)",
                (
                    scope_id,
                    version_id,
                    as_of,
                    valid_from,
                    valid_to,
                    context_object_id,
                    label,
                    _now(),
                ),
            )
        return scope_id

    def add_statement(
        self,
        version_id: str,
        local_key: str,
        text: str,
        derivation_kind: DerivationKind | str,
        *,
        facet_id: str | None = None,
        language: str | None = None,
        temporal_scope_id: str | None = None,
    ) -> str:
        local_key, text = local_key.strip(), text.strip()
        if not local_key or not text:
            raise ValueError("Statement local_key and text are required")
        statement_id = new_persistent_id()
        derivation_kind = DerivationKind(derivation_kind)
        with self.db:
            self.db.execute(
                "INSERT INTO knowledge_statements VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    statement_id,
                    version_id,
                    facet_id,
                    local_key,
                    text,
                    derivation_kind.value,
                    language,
                    temporal_scope_id,
                    _now(),
                ),
            )
        return statement_id

    @staticmethod
    def _attribute_record(row: sqlite3.Row | dict) -> AttributeDefinitionRecord:
        return AttributeDefinitionRecord(
            attribute_id=row["id"],
            key=row["key"],
            name=row["name"],
            description=row["description"],
            value_type=AttributeValueType(row["value_type"]),
            status=row["status"],
        )

    def attribute_by_key(self, key: str) -> AttributeDefinitionRecord | None:
        row = self.db.execute("SELECT * FROM attribute_definitions WHERE key=?", (key,)).fetchone()
        return self._attribute_record(row) if row else None

    def register_attribute_definition(
        self,
        key: str,
        name: str,
        value_type: AttributeValueType | str,
        *,
        description: str = "",
        attribute_id: str | None = None,
    ) -> str:
        key, name = key.strip(), name.strip()
        if not key or not name:
            raise ValueError("Attribute key and name are required")
        value_type = AttributeValueType(value_type)
        attribute_id = attribute_id or f"attribute:{key}"
        timestamp = _now()
        with self.db:
            self.db.execute(
                "INSERT INTO attribute_definitions VALUES(?,?,?,?,?,?,?,?)",
                (
                    attribute_id,
                    key,
                    name,
                    description,
                    value_type.value,
                    "active",
                    timestamp,
                    timestamp,
                ),
            )
        return attribute_id

    def add_attribute(
        self,
        version_id: str,
        attribute_key: str,
        value: object | None = None,
        *,
        ordinal: int = 0,
        status: AttributeStatus | str = AttributeStatus.KNOWN,
        language: str | None = None,
        temporal_scope_id: str | None = None,
    ) -> str:
        definition = self.attribute_by_key(attribute_key)
        if definition is None:
            raise ValueError("Unknown attribute key")
        status = AttributeStatus(status)
        columns: dict[str, object | None] = {
            "value_text": None,
            "value_integer": None,
            "value_real": None,
            "value_boolean": None,
            "value_json": None,
        }
        if status is AttributeStatus.KNOWN:
            value_type = definition.value_type
            if value_type in {
                AttributeValueType.TEXT,
                AttributeValueType.DATE,
                AttributeValueType.DATETIME,
                AttributeValueType.IDENTIFIER,
                AttributeValueType.ENUM,
            }:
                if not isinstance(value, str):
                    raise TypeError(f"{value_type.value} attribute requires str")
                columns["value_text"] = value
            elif value_type is AttributeValueType.INTEGER:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise TypeError("integer attribute requires int")
                columns["value_integer"] = value
            elif value_type is AttributeValueType.REAL:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise TypeError("real attribute requires int or float")
                columns["value_real"] = float(value)
            elif value_type is AttributeValueType.BOOLEAN:
                if not isinstance(value, bool):
                    raise TypeError("boolean attribute requires bool")
                columns["value_boolean"] = int(value)
            elif value_type is AttributeValueType.JSON:
                columns["value_json"] = json.dumps(
                    value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
        elif value is not None:
            raise ValueError("Non-known attribute status cannot carry a value")

        attribute_value_id = new_persistent_id()
        with self.db:
            self.db.execute(
                """INSERT INTO object_version_attributes
                   (id,version_id,attribute_id,ordinal,status,value_text,value_integer,
                    value_real,value_boolean,value_json,language,temporal_scope_id,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    attribute_value_id,
                    version_id,
                    definition.attribute_id,
                    ordinal,
                    status.value,
                    columns["value_text"],
                    columns["value_integer"],
                    columns["value_real"],
                    columns["value_boolean"],
                    columns["value_json"],
                    language,
                    temporal_scope_id,
                    _now(),
                ),
            )
        return attribute_value_id

    def set_relation_temporal_scope(self, relation_id: str, temporal_scope_id: str) -> None:
        with self.db:
            self.db.execute(
                """INSERT INTO relation_temporal_scopes(relation_id,temporal_scope_id,created_at)
                   VALUES(?,?,?)
                   ON CONFLICT(relation_id) DO UPDATE SET
                       temporal_scope_id=excluded.temporal_scope_id""",
                (relation_id, temporal_scope_id, _now()),
            )

    def get_or_create_search_representation(
        self,
        kind: SearchRepresentationKind | str,
        builder_key: str,
        builder_version: str,
        content: str,
    ) -> str:
        kind = SearchRepresentationKind(kind)
        builder_key = builder_key.strip()
        builder_version = builder_version.strip()
        if not builder_key or not builder_version:
            raise ValueError("Representation builder key and version are required")
        content_hash = _digest(content)
        row = self.db.execute(
            """SELECT id FROM search_representations
               WHERE kind=? AND builder_key=? AND builder_version=? AND content_hash=?""",
            (kind.value, builder_key, builder_version, content_hash),
        ).fetchone()
        if row:
            return row["id"]
        representation_id = new_persistent_id()
        with self.db:
            self.db.execute(
                "INSERT INTO search_representations VALUES(?,?,?,?,?,?,?)",
                (
                    representation_id,
                    kind.value,
                    builder_key,
                    builder_version,
                    content,
                    content_hash,
                    _now(),
                ),
            )
        return representation_id

    def search_representation(self, representation_id: str) -> SearchRepresentationRecord:
        row = self.db.execute(
            "SELECT * FROM search_representations WHERE id=?", (representation_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown search representation ID")
        return SearchRepresentationRecord(
            representation_id=row["id"],
            kind=SearchRepresentationKind(row["kind"]),
            builder_key=row["builder_key"],
            builder_version=row["builder_version"],
            content=row["content"],
            content_hash=row["content_hash"],
        )

    def link_knowledge_search_representation(
        self,
        object_id: str,
        version_id: str,
        representation_id: str,
        target_kind: SearchRepresentationKind | str,
        *,
        facet_id: str | None = None,
        statement_id: str | None = None,
    ) -> str:
        target_kind = SearchRepresentationKind(target_kind)
        if target_kind is SearchRepresentationKind.EVIDENCE:
            raise ValueError("Evidence uses a separate search representation membership family")
        existing = self.db.execute(
            """SELECT id FROM knowledge_search_representation_memberships
               WHERE object_id=? AND version_id=? AND representation_id=? AND target_kind=?
                 AND facet_id IS ? AND statement_id IS ?""",
            (
                object_id,
                version_id,
                representation_id,
                target_kind.value,
                facet_id,
                statement_id,
            ),
        ).fetchone()
        if existing:
            return existing["id"]
        membership_id = new_persistent_id()
        with self.db:
            self.db.execute(
                """INSERT INTO knowledge_search_representation_memberships
                   (id,representation_id,object_id,version_id,target_kind,facet_id,statement_id,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (
                    membership_id,
                    representation_id,
                    object_id,
                    version_id,
                    target_kind.value,
                    facet_id,
                    statement_id,
                    _now(),
                ),
            )
        return membership_id

    def link_evidence_search_representation(self, representation_id: str, evidence_id: str) -> str:
        evidence = self.db.execute(
            "SELECT source_id,snapshot_id,run_id FROM evidence_records WHERE id=?",
            (evidence_id,),
        ).fetchone()
        if not evidence:
            raise ValueError("Unknown evidence ID")
        existing = self.db.execute(
            """SELECT id FROM evidence_search_representation_memberships
               WHERE representation_id=? AND evidence_id=?""",
            (representation_id, evidence_id),
        ).fetchone()
        if existing:
            return existing["id"]
        membership_id = new_persistent_id()
        with self.db:
            self.db.execute(
                """INSERT INTO evidence_search_representation_memberships
                   (id,representation_id,evidence_id,source_id,snapshot_id,run_id,created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    membership_id,
                    representation_id,
                    evidence_id,
                    evidence["source_id"],
                    evidence["snapshot_id"],
                    evidence["run_id"],
                    _now(),
                ),
            )
        return membership_id

    def link_search_representation(
        self,
        version_id: str,
        representation_id: str,
        target_kind: SearchRepresentationKind | str,
        target_ref: str,
    ) -> str:
        """Compatibility wrapper for the pre-I-01 Knowledge membership API."""

        target_kind = SearchRepresentationKind(target_kind)
        if target_kind is SearchRepresentationKind.EVIDENCE:
            raise ValueError("Evidence memberships are not version-scoped")
        version = self.db.execute(
            "SELECT object_id FROM object_versions WHERE id=?", (version_id,)
        ).fetchone()
        if not version:
            raise ValueError("Unknown Object Knowledge Version ID")
        facet_id = None
        statement_id = None
        if target_kind is SearchRepresentationKind.OBJECT_OVERALL:
            if target_ref != version["object_id"]:
                raise ValueError("Object representation target must own version")
        elif target_kind is SearchRepresentationKind.FACET:
            facet_id = target_ref
        elif target_kind is SearchRepresentationKind.STATEMENT:
            statement_id = target_ref
            statement = self.db.execute(
                "SELECT facet_id FROM knowledge_statements WHERE id=? AND version_id=?",
                (statement_id, version_id),
            ).fetchone()
            facet_id = statement["facet_id"] if statement else None
        return self.link_knowledge_search_representation(
            version["object_id"],
            version_id,
            representation_id,
            target_kind,
            facet_id=facet_id,
            statement_id=statement_id,
        )

    def knowledge_search_memberships(
        self,
        *,
        object_id: str | None = None,
        version_id: str | None = None,
        current_only: bool = False,
    ) -> tuple[dict, ...]:
        clauses: list[str] = []
        parameters: list[str] = []
        if object_id is not None:
            clauses.append("m.object_id=?")
            parameters.append(object_id)
        if version_id is not None:
            clauses.append("m.version_id=?")
            parameters.append(version_id)
        if current_only:
            clauses.append("o.status='active' AND o.current_version_id=m.version_id")
        clauses.append("l.state='accepted'")
        sql = """SELECT m.* FROM knowledge_search_representation_memberships m
                 JOIN objects o ON o.id=m.object_id
                 JOIN object_version_lifecycle l ON l.version_id=m.version_id"""
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY m.object_id,m.version_id,m.target_kind,m.facet_id,m.statement_id,m.id"
        return tuple(dict(row) for row in self.db.execute(sql, parameters))

    def evidence_search_memberships(self, *, evidence_id: str | None = None) -> tuple[dict, ...]:
        if evidence_id is None:
            rows = self.db.execute(
                "SELECT * FROM evidence_search_representation_memberships ORDER BY evidence_id,id"
            ).fetchall()
        else:
            rows = self.db.execute(
                """SELECT * FROM evidence_search_representation_memberships
                   WHERE evidence_id=? ORDER BY id""",
                (evidence_id,),
            ).fetchall()
        return tuple(dict(row) for row in rows)
