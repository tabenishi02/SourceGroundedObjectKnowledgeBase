"""Read-only canonical projection for Phase H / H-03 Markdown rendering."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from typing import Any


class MarkdownRenderReadRepository:
    """Build a presentation model for one immutable accepted Object Version."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def build_model(self, version_id: str) -> dict[str, Any]:
        version = self.db.execute(
            """SELECT v.id,v.object_id,v.version_number,v.created_at,
                      l.base_version_id,l.state,l.accepted_at,
                      c.primary_class_id,o.name,o.current_version_id
               FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id
               JOIN object_version_classification_snapshots c ON c.version_id=v.id
               JOIN objects o ON o.id=v.object_id
               WHERE v.id=?""",
            (version_id,),
        ).fetchone()
        if not version:
            raise ValueError("Unknown Object Knowledge Version ID")
        if version["state"] != "accepted":
            raise ValueError("Markdown rendering requires an accepted Object Version")

        object_id = version["object_id"]
        additional_ids = [
            row["class_id"]
            for row in self.db.execute(
                """SELECT class_id FROM object_version_additional_class_snapshots
                   WHERE version_id=? ORDER BY class_id""",
                (version_id,),
            )
        ]
        class_ids = [version["primary_class_id"], *additional_ids]
        class_rows = {
            row["id"]: dict(row)
            for row in self.db.execute(
                "SELECT id,key,name,description FROM object_classes WHERE id IN ({})".format(
                    ",".join("?" for _ in class_ids)
                ),
                class_ids,
            )
        }

        aliases = [
            {
                "value": row["value"],
                "language": row["language"],
                "kind": row["kind"],
            }
            for row in self.db.execute(
                """SELECT value,language,kind FROM object_aliases
                   WHERE object_id=? ORDER BY rowid""",
                (object_id,),
            )
        ]

        scopes = {
            row["id"]: {
                key: row[key]
                for key in ("as_of", "valid_from", "valid_to", "context_object_id", "label")
                if row[key] is not None
            }
            for row in self.db.execute(
                "SELECT * FROM temporal_scopes WHERE version_id=? ORDER BY rowid",
                (version_id,),
            )
        }
        context_ids = {
            scope["context_object_id"] for scope in scopes.values() if "context_object_id" in scope
        }
        context_names = self._object_names(context_ids)
        for scope in scopes.values():
            context_id = scope.get("context_object_id")
            if context_id:
                scope["context_object_name"] = context_names.get(context_id, context_id)

        links: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        evidence_ids: set[str] = set()
        for row in self.db.execute(
            """SELECT l.target_kind,l.target_id,l.evidence_id,r.key AS role
               FROM evidence_links l
               JOIN evidence_roles r ON r.id=l.role_id
               WHERE l.version_id=? ORDER BY l.rowid""",
            (version_id,),
        ):
            item = {"evidence_id": row["evidence_id"], "role": row["role"]}
            links[(row["target_kind"], row["target_id"])].append(item)
            evidence_ids.add(row["evidence_id"])

        attributions: dict[str, dict[str, str]] = {}
        source_ids: set[str] = set()
        attribution_object_ids: set[str] = set()
        for row in self.db.execute(
            """SELECT a.* FROM knowledge_statement_attributions a
               JOIN knowledge_statements s ON s.id=a.statement_id
               WHERE s.version_id=? ORDER BY a.rowid""",
            (version_id,),
        ):
            item = {"kind": row["kind"]}
            for key in ("source_id", "object_id", "label"):
                if row[key] is not None:
                    item[key] = row[key]
            if row["source_id"]:
                source_ids.add(row["source_id"])
            if row["object_id"]:
                attribution_object_ids.add(row["object_id"])
            attributions[row["statement_id"]] = item

        source_names = self._source_names(source_ids)
        attribution_object_names = self._object_names(attribution_object_ids)
        for item in attributions.values():
            if item.get("source_id"):
                item["display_name"] = source_names.get(item["source_id"], item["source_id"])
            elif item.get("object_id"):
                item["display_name"] = attribution_object_names.get(
                    item["object_id"], item["object_id"]
                )
            elif item.get("label"):
                item["display_name"] = item["label"]

        facet_rows = self.db.execute(
            """SELECT vf.facet_id,vf.status,f.key,f.name,f.description
               FROM object_version_facets vf
               JOIN facet_definitions f ON f.id=vf.facet_id
               WHERE vf.version_id=? ORDER BY f.key,vf.facet_id""",
            (version_id,),
        ).fetchall()
        facets = [
            {
                "facet_id": row["facet_id"],
                "key": row["key"],
                "name": row["name"],
                "description": row["description"],
                "status": row["status"],
                "statements": [],
            }
            for row in facet_rows
        ]
        facet_by_id = {item["facet_id"]: item for item in facets}

        summary: list[dict[str, Any]] = []
        for row in self.db.execute(
            "SELECT * FROM knowledge_statements WHERE version_id=? ORDER BY rowid",
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
            if row["id"] in attributions:
                statement["attribution"] = attributions[row["id"]]
            if row["facet_id"] is None:
                summary.append(statement)
            else:
                facet = facet_by_id.get(row["facet_id"])
                if facet is None:
                    raise ValueError("Version Statement references an unmaterialized Facet")
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

        relation_rows = self.db.execute(
            """SELECT r.*,t.key AS relation_key,t.name AS relation_name,
                      s.temporal_scope_id
               FROM object_relations r
               JOIN relation_types t ON t.id=r.relation_type_id
               LEFT JOIN relation_temporal_scopes s ON s.relation_id=r.id
               WHERE r.version_id=? ORDER BY t.key,r.object_object_id,r.id""",
            (version_id,),
        ).fetchall()
        relation_object_ids = {row["subject_object_id"] for row in relation_rows} | {
            row["object_object_id"] for row in relation_rows
        }
        relation_names = self._object_names(relation_object_ids)
        relations = [
            {
                "relation_id": row["id"],
                "subject_object_id": row["subject_object_id"],
                "subject_name": relation_names.get(
                    row["subject_object_id"], row["subject_object_id"]
                ),
                "relation_type_id": row["relation_type_id"],
                "relation_key": row["relation_key"],
                "relation_name": row["relation_name"],
                "object_object_id": row["object_object_id"],
                "object_name": relation_names.get(row["object_object_id"], row["object_object_id"]),
                "temporal_scope": scopes.get(row["temporal_scope_id"]),
                "evidence": links.get(("relation", row["id"]), []),
            }
            for row in relation_rows
        ]

        metadata = self.db.execute(
            "SELECT * FROM object_version_result_metadata WHERE version_id=?",
            (version_id,),
        ).fetchone()
        review = {
            "result_status": "legacy_or_manual",
            "conflicts": [],
            "gaps": [],
            "unresolved_references": [],
            "registry_proposals": [],
            "class_extensions": [],
        }
        generation: dict[str, Any] = {}
        provenance: dict[str, Any] = {}
        default_language = None
        if metadata:
            default_language = metadata["default_language"]
            generation = json.loads(metadata["generation_json"])
            review.update(
                {
                    "conflicts": json.loads(metadata["conflicts_json"]),
                    "gaps": json.loads(metadata["gaps_json"]),
                    "unresolved_references": json.loads(metadata["unresolved_references_json"]),
                    "registry_proposals": json.loads(metadata["registry_proposals_json"]),
                    "class_extensions": json.loads(metadata["class_extensions_json"]),
                }
            )
            imported = self.db.execute(
                "SELECT * FROM object_result_imports WHERE id=?",
                (metadata["import_id"],),
            ).fetchone()
            if imported:
                review["result_status"] = imported["result_status"]
                provenance = {
                    "import_id": imported["id"],
                    "receipt_id": imported["receipt_id"],
                    "package_id": imported["package_id"],
                    "manifest_sha256": imported["manifest_sha256"],
                    "result_sha256": imported["result_sha256"],
                    "review_acknowledged": bool(imported["review_acknowledged"]),
                    "imported_at": imported["imported_at"],
                }

        self._collect_review_evidence(review, evidence_ids)
        evidence = self._evidence_contexts(evidence_ids)

        primary = class_rows.get(version["primary_class_id"])
        if primary is None:
            raise ValueError("Version Primary Class is missing from Class Registry")
        additional = [class_rows[class_id] for class_id in additional_ids if class_id in class_rows]

        return {
            "schema_version": "sgokb.markdown-render-model/1.0",
            "canonical": True,
            "object": {
                "object_id": object_id,
                "name": version["name"],
                "aliases": aliases,
            },
            "version": {
                "version_id": version_id,
                "version_number": version["version_number"],
                "base_version_id": version["base_version_id"],
                "created_at": version["created_at"],
                "accepted_at": version["accepted_at"],
                "is_current": version["current_version_id"] == version_id,
                "classification": {
                    "primary": self._class_projection(primary),
                    "additional": [self._class_projection(item) for item in additional],
                },
            },
            "knowledge": {
                "default_language": default_language,
                "summary_statements": summary,
                "facets": facets,
                "attributes": attributes,
                "relations": relations,
            },
            "generation": generation,
            "review": review,
            "provenance": provenance,
            "evidence": evidence,
        }

    def _object_names(self, object_ids: set[str]) -> dict[str, str]:
        if not object_ids:
            return {}
        placeholders = ",".join("?" for _ in object_ids)
        return {
            row["id"]: row["name"]
            for row in self.db.execute(
                f"SELECT id,name FROM objects WHERE id IN ({placeholders})",
                tuple(sorted(object_ids)),
            )
        }

    def _source_names(self, source_ids: set[str]) -> dict[str, str]:
        if not source_ids:
            return {}
        placeholders = ",".join("?" for _ in source_ids)
        return {
            row["id"]: row["label"] or row["id"]
            for row in self.db.execute(
                f"SELECT id,label FROM source_records WHERE id IN ({placeholders})",
                tuple(sorted(source_ids)),
            )
        }

    def _evidence_contexts(self, evidence_ids: set[str]) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        result = []
        for evidence_id in sorted(evidence_ids):
            row = self.db.execute(
                """SELECT e.*,s.label AS source_label,ss.title AS snapshot_title
                   FROM evidence_records e
                   JOIN source_records s ON s.id=e.source_id
                   JOIN source_snapshots ss ON ss.id=e.snapshot_id
                   WHERE e.id=?""",
                (evidence_id,),
            ).fetchone()
            if not row:
                continue
            locators = [
                {
                    "kind": item["kind"],
                    "value": item["value"],
                    "preferred": bool(item["is_preferred"]),
                }
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
            result.append(
                {
                    "evidence_id": evidence_id,
                    "source_id": row["source_id"],
                    "source_label": row["source_label"] or row["source_id"],
                    "snapshot_id": row["snapshot_id"],
                    "snapshot_title": row["snapshot_title"],
                    "run_id": row["run_id"],
                    "language": row["language"],
                    "content": row["content"],
                    "locators": locators,
                    "locations": locations,
                }
            )
        return result

    @staticmethod
    def _collect_review_evidence(review: dict[str, Any], evidence_ids: set[str]) -> None:
        for key in (
            "conflicts",
            "gaps",
            "unresolved_references",
            "registry_proposals",
            "class_extensions",
        ):
            for item in review.get(key, []):
                for reference in item.get("evidence", []):
                    evidence_id = reference.get("evidence_id")
                    if evidence_id:
                        evidence_ids.add(str(evidence_id))

    @staticmethod
    def _class_projection(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "class_id": row["id"],
            "key": row["key"],
            "name": row["name"],
            "description": row["description"],
        }

    @staticmethod
    def _attribute_value(row: sqlite3.Row) -> Any:
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
