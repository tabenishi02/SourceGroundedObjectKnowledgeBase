"""Read models used to build Object Evidence Packages from canonical storage."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict


class PackageBuildReadRepository:
    """Storage-layer read model for Package generation.

    This class keeps Package serialization SQL out of the exchange/application layers.
    It never mutates canonical Knowledge.
    """

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def current_grounding_evidence_ids(self, version_id: str | None) -> tuple[str, ...]:
        if version_id is None:
            return ()
        rows = self.db.execute(
            """SELECT evidence_id FROM evidence_links
               WHERE version_id=? ORDER BY rowid""",
            (version_id,),
        ).fetchall()
        return tuple(dict.fromkeys(row["evidence_id"] for row in rows))

    def active_attribute_definitions(self) -> tuple[dict, ...]:
        rows = self.db.execute(
            """SELECT id,key,name,description,value_type
               FROM attribute_definitions WHERE status='active' ORDER BY key,id"""
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def active_relation_types(self) -> tuple[dict, ...]:
        rows = self.db.execute(
            """SELECT id,key,name,description
               FROM relation_types WHERE status='active' ORDER BY key,id"""
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def current_object_snapshot(self, object_id: str) -> dict | None:
        object_row = self.db.execute(
            "SELECT id,current_version_id FROM objects WHERE id=?", (object_id,)
        ).fetchone()
        if not object_row:
            raise ValueError("Unknown Object ID")
        version_id = object_row["current_version_id"]
        if version_id is None:
            return None

        version = self.db.execute(
            """SELECT v.id,v.version_number,v.created_at,l.state,c.primary_class_id
               FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id
               JOIN object_version_classification_snapshots c ON c.version_id=v.id
               WHERE v.id=? AND v.object_id=?""",
            (version_id, object_id),
        ).fetchone()
        if not version:
            raise ValueError("Current Object Version is missing")
        if version["state"] != "accepted":
            raise ValueError("Current Object Version must be accepted")

        additional = [
            row["class_id"]
            for row in self.db.execute(
                """SELECT class_id FROM object_version_additional_class_snapshots
                   WHERE version_id=? ORDER BY class_id""",
                (version_id,),
            )
        ]

        scopes = {
            row["id"]: self._temporal_scope(dict(row))
            for row in self.db.execute(
                "SELECT * FROM temporal_scopes WHERE version_id=? ORDER BY rowid", (version_id,)
            )
        }

        links: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in self.db.execute(
            """SELECT l.target_kind,l.target_id,l.evidence_id,r.key AS role
               FROM evidence_links l
               JOIN evidence_roles r ON r.id=l.role_id
               WHERE l.version_id=? ORDER BY l.rowid""",
            (version_id,),
        ):
            links[(row["target_kind"], row["target_id"])].append(
                {"evidence_id": row["evidence_id"], "role": row["role"]}
            )

        facet_rows = self.db.execute(
            """SELECT vf.facet_id,vf.status,f.key,f.name
               FROM object_version_facets vf
               JOIN facet_definitions f ON f.id=vf.facet_id
               WHERE vf.version_id=? ORDER BY f.key,vf.facet_id""",
            (version_id,),
        ).fetchall()
        facet_map = {
            row["facet_id"]: {
                "facet_id": row["facet_id"],
                "key": row["key"],
                "name": row["name"],
                "status": row["status"],
                "statements": [],
            }
            for row in facet_rows
        }

        summary_statements: list[dict] = []
        for row in self.db.execute(
            """SELECT * FROM knowledge_statements
               WHERE version_id=? ORDER BY rowid""",
            (version_id,),
        ):
            statement = {
                "statement_id": row["id"],
                "local_key": row["local_key"],
                "text": row["text"],
                "derivation_kind": row["derivation_kind"],
                "language": row["language"],
                "temporal_scope": scopes.get(row["temporal_scope_id"]),
                "evidence": links.get(("statement", row["id"]), []),
            }
            if row["facet_id"] is None:
                summary_statements.append(statement)
            else:
                facet = facet_map.get(row["facet_id"])
                if facet is None:
                    raise ValueError("Statement references Facet outside current Version Facets")
                facet["statements"].append(statement)

        attributes = []
        for row in self.db.execute(
            """SELECT a.*,d.key,d.name,d.value_type
               FROM object_version_attributes a
               JOIN attribute_definitions d ON d.id=a.attribute_id
               WHERE a.version_id=? ORDER BY d.key,a.ordinal,a.id""",
            (version_id,),
        ):
            attributes.append(
                {
                    "attribute_value_id": row["id"],
                    "attribute_id": row["attribute_id"],
                    "key": row["key"],
                    "name": row["name"],
                    "ordinal": row["ordinal"],
                    "status": row["status"],
                    "value_type": row["value_type"],
                    "value": self._attribute_value(row),
                    "language": row["language"],
                    "temporal_scope": scopes.get(row["temporal_scope_id"]),
                    "evidence": links.get(("attribute", row["id"]), []),
                }
            )

        relations = []
        for row in self.db.execute(
            """SELECT r.*,t.key AS relation_key,t.name AS relation_name,
                      s.temporal_scope_id
               FROM object_relations r
               JOIN relation_types t ON t.id=r.relation_type_id
               LEFT JOIN relation_temporal_scopes s ON s.relation_id=r.id
               WHERE r.version_id=? ORDER BY t.key,r.object_object_id,r.id""",
            (version_id,),
        ):
            relations.append(
                {
                    "relation_id": row["id"],
                    "subject_object_id": row["subject_object_id"],
                    "relation_type_id": row["relation_type_id"],
                    "relation_key": row["relation_key"],
                    "relation_name": row["relation_name"],
                    "object_object_id": row["object_object_id"],
                    "temporal_scope": scopes.get(row["temporal_scope_id"]),
                    "evidence": links.get(("relation", row["id"]), []),
                }
            )

        return {
            "object_id": object_id,
            "version_id": version_id,
            "version_number": version["version_number"],
            "version_created_at": version["created_at"],
            "classification": {
                "primary_class_id": version["primary_class_id"],
                "additional_class_ids": additional,
            },
            "knowledge": {
                "summary_statements": summary_statements,
                "facets": list(facet_map.values()),
                "attributes": attributes,
                "relations": relations,
            },
        }

    @staticmethod
    def _temporal_scope(row: dict) -> dict:
        return {
            key: row[key]
            for key in ("as_of", "valid_from", "valid_to", "context_object_id", "label")
            if row.get(key) is not None
        }

    @staticmethod
    def _attribute_value(row: sqlite3.Row):
        if row["status"] != "known":
            return None
        value_type = row["value_type"]
        if value_type in {"text", "date", "datetime", "identifier", "enum"}:
            return row["value_text"]
        if value_type == "integer":
            return row["value_integer"]
        if value_type == "real":
            return row["value_real"]
        if value_type == "boolean":
            return bool(row["value_boolean"])
        if value_type == "json":
            return json.loads(row["value_json"])
        raise ValueError(f"Unsupported attribute value type: {value_type}")
