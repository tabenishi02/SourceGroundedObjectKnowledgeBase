"""Transport-neutral Object Knowledge reads for Phase J / J-01.

This module is part of the Retrieval Core. It may depend on canonical repositories
and SQLite-backed storage details; transport adapters must not import or call it
directly. Application read use cases are the public boundary for CLI/MCP clients.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable


class ObjectKnowledgeReader:
    """Resolve current or pinned accepted Object Knowledge into a stable read model."""

    def __init__(self, repository) -> None:
        self.repository = repository
        self.db = repository.db

    def get_object(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        facets: Iterable[str] | None = None,
        include_relations: bool = True,
        include_evidence_refs: bool = True,
    ) -> dict:
        object_record = self.repository.object_store.get_object(object_id)
        resolved_version_id = version_id or object_record.current_version_id
        if resolved_version_id is None:
            raise ValueError("Object has no current Knowledge Version")

        version = self.repository.version_store.version_by_id(resolved_version_id)
        if version.object_id != object_id:
            raise ValueError("Pinned Knowledge Version does not belong to the Object")
        if version.state.value != "accepted":
            raise ValueError("Object Knowledge reads require an accepted Version")

        requested_facets = self._normalize_facets(facets)
        allowed_facet_ids = self._facet_ids(requested_facets)
        evidence = self._evidence_by_target(resolved_version_id) if include_evidence_refs else {}
        metadata = self._result_metadata(resolved_version_id)

        primary_class = self._class_payload(version.classification.primary_class_id)
        additional_classes = [
            self._class_payload(class_id)
            for class_id in version.classification.additional_class_ids
        ]

        statement_rows = self._statement_rows(resolved_version_id)
        summary = []
        statements_by_facet: dict[str, list[dict]] = defaultdict(list)
        for row in statement_rows:
            statement = self._statement_payload(row, evidence)
            if row["facet_id"] is None:
                summary.append(statement)
            elif allowed_facet_ids is None or row["facet_id"] in allowed_facet_ids:
                statements_by_facet[row["facet_id"]].append(statement)

        facet_rows = self._facet_rows(resolved_version_id, allowed_facet_ids)
        facet_payloads = [
            {
                "facet_id": row["facet_id"],
                "key": row["facet_key"],
                "name": row["facet_name"],
                "status": row["status"],
                "statements": statements_by_facet.get(row["facet_id"], []),
            }
            for row in facet_rows
        ]

        attributes = [
            self._attribute_payload(row, evidence)
            for row in self._attribute_rows(resolved_version_id)
        ]
        relations = (
            [
                self._relation_payload(row, evidence, perspective_object_id=object_id)
                for row in self._relation_rows(resolved_version_id)
            ]
            if include_relations
            else []
        )

        warnings = []
        if metadata is None:
            warnings.append("result_metadata_unavailable")

        return {
            "object_id": object_record.object_id,
            "name": object_record.name,
            "aliases": [
                {
                    "value": alias.value,
                    "language": alias.language,
                    "kind": alias.kind,
                }
                for alias in object_record.aliases
            ],
            "object_status": object_record.status.value,
            "requested_version_id": version_id,
            "resolved_version_id": resolved_version_id,
            "is_current": resolved_version_id == object_record.current_version_id,
            "version_number": version.version_number,
            "primary_class": primary_class,
            "additional_classes": additional_classes,
            "scope": {
                "facets": None if requested_facets is None else list(requested_facets),
                "include_relations": include_relations,
                "include_evidence_refs": include_evidence_refs,
            },
            "knowledge": {
                "default_language": metadata["default_language"] if metadata else None,
                "result_status": metadata["result_status"] if metadata else None,
                "summary": summary,
                "facets": facet_payloads,
                "attributes": attributes,
                "relations": relations,
            },
            "warnings": warnings,
        }

    def get_relations(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        include_evidence_refs: bool = True,
    ) -> dict:
        """Read one-hop Relations for an Object.

        Without ``version_id`` this is a current Relation-graph traversal: a Registry
        Object may be queried even when it has no Knowledge Version of its own, and
        Relations owned by any endpoint's current accepted Version are returned.
        With ``version_id`` the read remains pinned to that Object's accepted Version.
        """

        object_record = self.repository.object_store.get_object(object_id)
        if version_id is not None:
            payload = self.get_object(
                object_id,
                version_id=version_id,
                facets=(),
                include_relations=True,
                include_evidence_refs=include_evidence_refs,
            )
            return {
                "object_id": payload["object_id"],
                "scope": "pinned_object_version",
                "requested_version_id": version_id,
                "object_current_version_id": object_record.current_version_id,
                "resolved_version_id": payload["resolved_version_id"],
                "is_current": payload["is_current"],
                "relations": payload["knowledge"]["relations"],
                "warnings": payload["warnings"],
            }

        rows = self._current_relation_rows(object_id)
        evidence_by_version: dict[str, dict[tuple[str, str], list[dict]]] = {}
        relations = []
        for row in rows:
            owner_version_id = row["version_id"]
            if include_evidence_refs:
                if owner_version_id not in evidence_by_version:
                    evidence_by_version[owner_version_id] = self._evidence_by_target(owner_version_id)
                evidence = evidence_by_version[owner_version_id]
            else:
                evidence = {}
            relations.append(
                self._relation_payload(row, evidence, perspective_object_id=object_id)
            )

        return {
            "object_id": object_record.object_id,
            "scope": "current_relation_graph",
            "requested_version_id": None,
            "object_current_version_id": object_record.current_version_id,
            "resolved_version_id": object_record.current_version_id,
            "is_current": True,
            "relations": relations,
            "warnings": [],
        }

    @staticmethod
    def _normalize_facets(facets: Iterable[str] | None) -> tuple[str, ...] | None:
        if facets is None:
            return None
        normalized = tuple(dict.fromkeys(value.strip() for value in facets if value.strip()))
        return normalized

    def _facet_ids(self, facets: tuple[str, ...] | None) -> set[str] | None:
        if facets is None:
            return None
        if not facets:
            return set()
        marks = ",".join("?" for _ in facets)
        rows = self.db.execute(
            f"SELECT id,key FROM facet_definitions WHERE key IN ({marks})",
            facets,
        ).fetchall()
        by_key = {row["key"]: row["id"] for row in rows}
        unknown = [key for key in facets if key not in by_key]
        if unknown:
            raise ValueError("Unknown Facet filter: " + ", ".join(unknown))
        return set(by_key.values())

    def _class_payload(self, class_id: str) -> dict:
        value = self.repository.object_store.class_by_id(class_id)
        if value is None:
            raise RuntimeError("Version classification references an unknown Class")
        return {"id": value.class_id, "key": value.key, "name": value.name}

    def _result_metadata(self, version_id: str) -> dict | None:
        row = self.db.execute(
            """SELECT m.default_language,i.result_status
               FROM object_version_result_metadata m
               JOIN object_result_imports i ON i.id=m.import_id
               WHERE m.version_id=?""",
            (version_id,),
        ).fetchone()
        return dict(row) if row else None

    def _statement_rows(self, version_id: str) -> list[dict]:
        rows = self.db.execute(
            """SELECT s.id,s.local_key,s.text,s.derivation_kind,s.language,s.facet_id,
                      f.key AS facet_key,s.temporal_scope_id,
                      ts.as_of,ts.valid_from,ts.valid_to,ts.context_object_id,ts.label,
                      a.kind AS attribution_kind,a.source_id AS attribution_source_id,
                      a.object_id AS attribution_object_id,a.label AS attribution_label
               FROM knowledge_statements s
               LEFT JOIN facet_definitions f ON f.id=s.facet_id
               LEFT JOIN temporal_scopes ts ON ts.id=s.temporal_scope_id
               LEFT JOIN knowledge_statement_attributions a ON a.statement_id=s.id
               WHERE s.version_id=?
               ORDER BY CASE WHEN s.facet_id IS NULL THEN 0 ELSE 1 END,
                        f.key,s.local_key,s.id""",
            (version_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _facet_rows(self, version_id: str, allowed_ids: set[str] | None) -> list[dict]:
        rows = self.db.execute(
            """SELECT vf.facet_id,f.key AS facet_key,f.name AS facet_name,vf.status
               FROM object_version_facets vf
               JOIN facet_definitions f ON f.id=vf.facet_id
               WHERE vf.version_id=? ORDER BY f.key,vf.facet_id""",
            (version_id,),
        ).fetchall()
        values = [dict(row) for row in rows]
        if allowed_ids is not None:
            values = [row for row in values if row["facet_id"] in allowed_ids]
        return values

    def _attribute_rows(self, version_id: str) -> list[dict]:
        rows = self.db.execute(
            """SELECT a.id,a.attribute_id,d.key AS attribute_key,d.name AS attribute_name,
                      d.value_type,a.ordinal,a.status,a.value_text,a.value_integer,a.value_real,
                      a.value_boolean,a.value_json,a.language,a.temporal_scope_id,
                      ts.as_of,ts.valid_from,ts.valid_to,ts.context_object_id,ts.label
               FROM object_version_attributes a
               JOIN attribute_definitions d ON d.id=a.attribute_id
               LEFT JOIN temporal_scopes ts ON ts.id=a.temporal_scope_id
               WHERE a.version_id=? ORDER BY d.key,a.ordinal,a.id""",
            (version_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _relation_rows(self, version_id: str) -> list[dict]:
        rows = self.db.execute(
            """SELECT r.id,r.version_id,r.subject_object_id,r.object_object_id,r.relation_type_id,
                      t.key AS relation_key,t.name AS relation_name,
                      subject.name AS subject_name,target.name AS object_name,
                      v.object_id AS owner_object_id,owner.name AS owner_name,
                      rs.temporal_scope_id,
                      ts.as_of,ts.valid_from,ts.valid_to,ts.context_object_id,ts.label
               FROM object_relations r
               JOIN relation_types t ON t.id=r.relation_type_id
               JOIN objects subject ON subject.id=r.subject_object_id
               JOIN objects target ON target.id=r.object_object_id
               JOIN object_versions v ON v.id=r.version_id
               JOIN objects owner ON owner.id=v.object_id
               LEFT JOIN relation_temporal_scopes rs ON rs.relation_id=r.id
               LEFT JOIN temporal_scopes ts ON ts.id=rs.temporal_scope_id
               WHERE r.version_id=?
               ORDER BY t.key,subject.name,target.name,r.id""",
            (version_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _current_relation_rows(self, object_id: str) -> list[dict]:
        rows = self.db.execute(
            """SELECT r.id,r.version_id,r.subject_object_id,r.object_object_id,r.relation_type_id,
                      t.key AS relation_key,t.name AS relation_name,
                      subject.name AS subject_name,target.name AS object_name,
                      v.object_id AS owner_object_id,owner.name AS owner_name,
                      rs.temporal_scope_id,
                      ts.as_of,ts.valid_from,ts.valid_to,ts.context_object_id,ts.label
               FROM object_relations r
               JOIN relation_types t ON t.id=r.relation_type_id
               JOIN objects subject ON subject.id=r.subject_object_id
               JOIN objects target ON target.id=r.object_object_id
               JOIN object_versions v ON v.id=r.version_id
               JOIN object_version_lifecycle lifecycle
                 ON lifecycle.version_id=v.id AND lifecycle.state='accepted'
               JOIN objects owner
                 ON owner.id=v.object_id AND owner.current_version_id=v.id
               LEFT JOIN relation_temporal_scopes rs ON rs.relation_id=r.id
               LEFT JOIN temporal_scopes ts ON ts.id=rs.temporal_scope_id
               WHERE r.subject_object_id=? OR r.object_object_id=?
               ORDER BY t.key,subject.name,target.name,r.id""",
            (object_id, object_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def _evidence_by_target(self, version_id: str) -> dict[tuple[str, str], list[dict]]:
        rows = self.db.execute(
            """SELECT l.target_kind,l.target_id,l.evidence_id,r.key AS role
               FROM evidence_links l
               JOIN evidence_roles r ON r.id=l.role_id
               WHERE l.version_id=?
               ORDER BY l.target_kind,l.target_id,l.evidence_id,r.key""",
            (version_id,),
        ).fetchall()
        grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in rows:
            grouped[(row["target_kind"], row["target_id"])].append(
                {"evidence_id": row["evidence_id"], "role": row["role"]}
            )
        return grouped

    @staticmethod
    def _temporal_payload(row: dict) -> dict | None:
        if row.get("temporal_scope_id") is None:
            return None
        return {
            "temporal_scope_id": row["temporal_scope_id"],
            "as_of": row.get("as_of"),
            "valid_from": row.get("valid_from"),
            "valid_to": row.get("valid_to"),
            "context_object_id": row.get("context_object_id"),
            "label": row.get("label"),
        }

    def _statement_payload(self, row: dict, evidence: dict) -> dict:
        attribution = None
        if row.get("attribution_kind") is not None:
            attribution = {
                "kind": row["attribution_kind"],
                "source_id": row.get("attribution_source_id"),
                "object_id": row.get("attribution_object_id"),
                "label": row.get("attribution_label"),
            }
        return {
            "statement_id": row["id"],
            "local_key": row["local_key"],
            "text": row["text"],
            "derivation_kind": row["derivation_kind"],
            "language": row["language"],
            "facet": row.get("facet_key"),
            "temporal_scope": self._temporal_payload(row),
            "attribution": attribution,
            "evidence": evidence.get(("statement", row["id"]), []),
        }

    @staticmethod
    def _attribute_value(row: dict):
        if row["status"] != "known":
            return None
        kind = row["value_type"]
        if kind in {"text", "date", "datetime", "identifier", "enum"}:
            return row["value_text"]
        if kind == "integer":
            return row["value_integer"]
        if kind == "real":
            return row["value_real"]
        if kind == "boolean":
            return bool(row["value_boolean"])
        if kind == "json":
            return json.loads(row["value_json"])
        raise RuntimeError(f"Unsupported Attribute value type: {kind}")

    def _attribute_payload(self, row: dict, evidence: dict) -> dict:
        return {
            "attribute_value_id": row["id"],
            "attribute_id": row["attribute_id"],
            "key": row["attribute_key"],
            "name": row["attribute_name"],
            "value_type": row["value_type"],
            "ordinal": row["ordinal"],
            "status": row["status"],
            "value": self._attribute_value(row),
            "language": row["language"],
            "temporal_scope": self._temporal_payload(row),
            "evidence": evidence.get(("attribute", row["id"]), []),
        }

    def _relation_payload(
        self,
        row: dict,
        evidence: dict,
        *,
        perspective_object_id: str | None = None,
    ) -> dict:
        perspective = None
        if perspective_object_id is not None:
            if (
                row["subject_object_id"] == perspective_object_id
                and row["object_object_id"] == perspective_object_id
            ):
                perspective = "self"
            elif row["subject_object_id"] == perspective_object_id:
                perspective = "outgoing"
            elif row["object_object_id"] == perspective_object_id:
                perspective = "incoming"

        return {
            "relation_id": row["id"],
            "relation_type_id": row["relation_type_id"],
            "relation_key": row["relation_key"],
            "relation_name": row["relation_name"],
            "subject_object_id": row["subject_object_id"],
            "subject_name": row["subject_name"],
            "object_object_id": row["object_object_id"],
            "object_name": row["object_name"],
            "perspective": perspective,
            "owner_object_id": row["owner_object_id"],
            "owner_name": row["owner_name"],
            "owner_version_id": row["version_id"],
            "temporal_scope": self._temporal_payload(row),
            "evidence": evidence.get(("relation", row["id"]), []),
        }
