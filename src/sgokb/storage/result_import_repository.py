"""Atomic persistence for Phase H / H-02 Object Result imports."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

from sgokb.domain.object import new_persistent_id
from sgokb.domain.version import StaleVersionError

from .semantic_repository import SemanticRepository
from .version_repository import DEFAULT_DERIVED_KINDS, VersionRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _evidence_ids(result: Mapping[str, Any]) -> set[str]:
    identifiers: set[str] = set()
    knowledge = result.get("knowledge", {})
    items = list(knowledge.get("summary", []))
    for facet in knowledge.get("facets", []):
        items.extend(facet.get("statements", []))
    items.extend(knowledge.get("attributes", []))
    items.extend(knowledge.get("relations", []))
    for collection in ("conflicts", "gaps", "unresolved_references", "registry_proposals"):
        items.extend(result.get(collection, []))
    for item in items:
        for ref in item.get("evidence", []):
            identifiers.add(str(ref["evidence_id"]))
    return identifiers


class ResultImportRepository:
    """Import one validated full Object Result as one atomic accepted Version."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.version_store = VersionRepository(db)
        self.semantic_store = SemanticRepository(db)

    def import_by_receipt(self, receipt_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT * FROM object_result_imports WHERE receipt_id=?", (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def import_result(
        self,
        receipt_id: str,
        result: Mapping[str, Any],
        *,
        artifact_sha256: str,
        artifact_byte_count: int,
        review_acknowledged: bool,
        failure_hook: Callable[[str], None] | None = None,
    ) -> dict:
        if self.db.in_transaction:
            raise RuntimeError("Object Result import requires an outer-transaction boundary")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.import_by_receipt(receipt_id)
            if existing is not None:
                self.db.commit()
                return dict(existing, duplicate=True)

            receipt = self._receipt(receipt_id)
            package = self._package(str(receipt["package_id"]))
            self._validate_import_preconditions(
                receipt,
                package,
                result,
                artifact_sha256=artifact_sha256,
                artifact_byte_count=artifact_byte_count,
                review_acknowledged=review_acknowledged,
            )

            timestamp = _now()
            object_id = str(result["target"]["object_id"])
            base_version_id = result["binding"].get("base_version_id")
            version_id = self.version_store.create_candidate_in_transaction(
                object_id,
                base_version_id,
                timestamp=timestamp,
            )
            if failure_hook:
                failure_hook("candidate_created")

            import_id = new_persistent_id()
            self.db.execute(
                """INSERT INTO object_result_imports
                   (id,receipt_id,package_id,manifest_sha256,result_sha256,result_byte_count,
                    result_storage_ref,object_id,base_version_id,version_id,result_status,
                    validation_completed_at,validation_findings_json,review_acknowledged,imported_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    import_id,
                    receipt_id,
                    receipt["package_id"],
                    package["manifest_sha256"],
                    receipt["result_sha256"],
                    receipt["byte_count"],
                    receipt["storage_ref"],
                    object_id,
                    base_version_id,
                    version_id,
                    result["result_status"],
                    receipt["validation_completed_at"],
                    receipt["validation_findings_json"],
                    int(review_acknowledged),
                    timestamp,
                ),
            )
            self._insert_result_metadata(version_id, import_id, result, timestamp)
            self._insert_knowledge(version_id, import_id, result, timestamp)
            if failure_hook:
                failure_hook("knowledge_written")

            self.version_store.accept_candidate_in_transaction(
                version_id,
                derived_kinds=DEFAULT_DERIVED_KINDS,
                timestamp=timestamp,
            )
            if failure_hook:
                failure_hook("accepted")
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        imported = self.import_by_receipt(receipt_id)
        if imported is None:
            raise RuntimeError("Committed Object Result import cannot be reloaded")
        return dict(imported, duplicate=False)

    def _receipt(self, receipt_id: str) -> sqlite3.Row:
        row = self.db.execute(
            "SELECT * FROM package_result_receipts WHERE id=?", (receipt_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown Result receipt ID")
        if row["validation_state"] != "valid":
            raise ValueError("Object Result import requires a valid H-01 receipt")
        return row

    def _package(self, package_id: str) -> sqlite3.Row:
        row = self.db.execute(
            "SELECT * FROM package_exchange_records WHERE package_id=?", (package_id,)
        ).fetchone()
        if not row:
            raise ValueError("Result receipt Package audit record is missing")
        return row

    def _validate_import_preconditions(
        self,
        receipt: sqlite3.Row,
        package: sqlite3.Row,
        result: Mapping[str, Any],
        *,
        artifact_sha256: str,
        artifact_byte_count: int,
        review_acknowledged: bool,
    ) -> None:
        if (
            artifact_sha256 != receipt["result_sha256"]
            or artifact_byte_count != receipt["byte_count"]
        ):
            raise ValueError("Immutable Result artifact no longer matches its receipt audit")

        findings = json.loads(receipt["validation_findings_json"])
        review_required = receipt["intake_state"] == "needs_review" or any(
            item.get("severity") == "review" for item in findings
        )
        review_required = review_required or result.get("result_status") != "complete"
        if review_required and not review_acknowledged:
            raise ValueError("Object Result import requires explicit review acknowledgement")

        target = result["target"]
        binding = result["binding"]
        if target["object_id"] != package["object_id"]:
            raise ValueError("Result target does not match Package audit record")
        if binding["package_id"] != package["package_id"]:
            raise ValueError("Result Package ID does not match Package audit record")
        if binding["package_schema_version"] != package["schema_version"]:
            raise ValueError("Result Package schema version is stale")
        if binding["manifest_sha256"] != package["manifest_sha256"]:
            raise ValueError("Result Package manifest hash does not match audit record")
        if binding["package_created_at"] != package["package_created_at"]:
            raise ValueError("Result Package creation time does not match audit record")
        if binding.get("base_version_id") != package["base_version_id"]:
            raise ValueError("Result base Version does not match Package audit record")

        object_row = self.db.execute(
            "SELECT * FROM objects WHERE id=?", (target["object_id"],)
        ).fetchone()
        if not object_row or object_row["status"] != "active":
            raise ValueError("Result target Object must exist and be active")
        if object_row["current_version_id"] != binding.get("base_version_id"):
            raise StaleVersionError("Result base Version is no longer current")
        if object_row["primary_class_id"] != target["primary_class_id"]:
            raise StaleVersionError("Result Primary Class is no longer current")
        current_additional = {
            row["class_id"]
            for row in self.db.execute(
                "SELECT class_id FROM object_additional_classes WHERE object_id=?",
                (target["object_id"],),
            )
        }
        if current_additional != set(target["additional_class_ids"]):
            raise StaleVersionError("Result Additional Classes are no longer current")

        classes = (target["primary_class_id"], *target["additional_class_ids"])
        expected_facets = {
            item.facet_id for item in self.semantic_store.facets_for_classes(classes)
        }
        actual_facets = {item["facet_id"] for item in result["knowledge"]["facets"]}
        if expected_facets != actual_facets:
            raise StaleVersionError("Result Facet contract changed after validation")

        package_evidence = set(json.loads(package["included_evidence_ids_json"]))
        referenced_evidence = _evidence_ids(result)
        if not referenced_evidence.issubset(package_evidence):
            raise ValueError("Result references Evidence outside its audited Package")
        if referenced_evidence:
            placeholders = ",".join("?" for _ in referenced_evidence)
            rows = self.db.execute(
                f"SELECT id FROM evidence_records WHERE id IN ({placeholders})",
                tuple(referenced_evidence),
            ).fetchall()
            if {row["id"] for row in rows} != referenced_evidence:
                raise ValueError("Result references unknown canonical Evidence")

        if binding.get("base_version_id") is not None:
            base = self.db.execute(
                """SELECT v.object_id,l.state FROM object_versions v
                   JOIN object_version_lifecycle l ON l.version_id=v.id WHERE v.id=?""",
                (binding["base_version_id"],),
            ).fetchone()
            if not base or base["object_id"] != target["object_id"] or base["state"] != "accepted":
                raise StaleVersionError(
                    "Result base Version is not an accepted Version of the target"
                )

    def _insert_result_metadata(
        self,
        version_id: str,
        import_id: str,
        result: Mapping[str, Any],
        timestamp: str,
    ) -> None:
        self.db.execute(
            """INSERT INTO object_version_result_metadata
               (version_id,import_id,default_language,generation_json,conflicts_json,gaps_json,
                unresolved_references_json,registry_proposals_json,class_extensions_json,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                version_id,
                import_id,
                result["knowledge"]["default_language"],
                _json(result["generation"]),
                _json(result["conflicts"]),
                _json(result["gaps"]),
                _json(result["unresolved_references"]),
                _json(result["registry_proposals"]),
                _json(result["class_extensions"]),
                timestamp,
            ),
        )

    def _insert_knowledge(
        self,
        version_id: str,
        import_id: str,
        result: Mapping[str, Any],
        timestamp: str,
    ) -> None:
        knowledge = result["knowledge"]
        for facet in knowledge["facets"]:
            self.db.execute(
                "INSERT INTO object_version_facets VALUES(?,?,?,?)",
                (version_id, facet["facet_id"], facet["status"], timestamp),
            )

        role_ids = {
            row["key"]: row["id"]
            for row in self.db.execute("SELECT id,key FROM evidence_roles WHERE status='active'")
        }
        for statement in knowledge["summary"]:
            self._insert_statement(version_id, import_id, statement, None, role_ids, timestamp)
        for facet in knowledge["facets"]:
            for statement in facet["statements"]:
                self._insert_statement(
                    version_id,
                    import_id,
                    statement,
                    facet["facet_id"],
                    role_ids,
                    timestamp,
                )

        ordinals: defaultdict[str, int] = defaultdict(int)
        definitions = {
            row["id"]: row
            for row in self.db.execute(
                "SELECT id,value_type FROM attribute_definitions WHERE status='active'"
            )
        }
        for attribute in knowledge["attributes"]:
            definition = definitions.get(attribute["attribute_id"])
            if definition is None:
                raise ValueError(f"Attribute is no longer active: {attribute['attribute_id']}")
            ordinal = ordinals[attribute["attribute_id"]]
            ordinals[attribute["attribute_id"]] += 1
            self._insert_attribute(
                version_id,
                import_id,
                attribute,
                definition["value_type"],
                ordinal,
                role_ids,
                timestamp,
            )

        active_relations = {
            row["id"]
            for row in self.db.execute("SELECT id FROM relation_types WHERE status='active'")
        }
        for relation in knowledge["relations"]:
            if relation["relation_type_id"] not in active_relations:
                raise ValueError(
                    f"Relation Type is no longer active: {relation['relation_type_id']}"
                )
            self._insert_relation(version_id, import_id, relation, role_ids, timestamp)

    def _insert_temporal_scope(
        self, version_id: str, scope: Mapping[str, Any] | None, timestamp: str
    ) -> str | None:
        if not scope:
            return None
        scope_id = new_persistent_id()
        self.db.execute(
            "INSERT INTO temporal_scopes VALUES(?,?,?,?,?,?,?,?)",
            (
                scope_id,
                version_id,
                scope.get("as_of"),
                scope.get("valid_from"),
                scope.get("valid_to"),
                scope.get("context_object_id"),
                scope.get("label"),
                timestamp,
            ),
        )
        return scope_id

    def _insert_statement(
        self,
        version_id: str,
        import_id: str,
        statement: Mapping[str, Any],
        facet_id: str | None,
        role_ids: Mapping[str, str],
        timestamp: str,
    ) -> None:
        statement_id = new_persistent_id()
        temporal_scope_id = self._insert_temporal_scope(
            version_id, statement.get("temporal_scope"), timestamp
        )
        self.db.execute(
            "INSERT INTO knowledge_statements VALUES(?,?,?,?,?,?,?,?,?)",
            (
                statement_id,
                version_id,
                facet_id,
                statement["local_key"],
                statement["text"],
                statement["derivation_kind"],
                statement.get("language"),
                temporal_scope_id,
                timestamp,
            ),
        )
        attribution = statement.get("attribution")
        if attribution:
            self.db.execute(
                """INSERT INTO knowledge_statement_attributions
                   (statement_id,kind,source_id,object_id,label,created_at)
                   VALUES(?,?,?,?,?,?)""",
                (
                    statement_id,
                    attribution["kind"],
                    attribution.get("source_id"),
                    attribution.get("object_id"),
                    attribution.get("label"),
                    timestamp,
                ),
            )
        self._insert_evidence_links(
            version_id,
            "statement",
            statement_id,
            statement["evidence"],
            role_ids,
            import_id,
            timestamp,
        )

    def _insert_attribute(
        self,
        version_id: str,
        import_id: str,
        attribute: Mapping[str, Any],
        value_type: str,
        ordinal: int,
        role_ids: Mapping[str, str],
        timestamp: str,
    ) -> None:
        value_columns: dict[str, object | None] = {
            "value_text": None,
            "value_integer": None,
            "value_real": None,
            "value_boolean": None,
            "value_json": None,
        }
        if attribute["status"] == "known":
            value = attribute["value"]
            if value_type in {"text", "date", "datetime", "identifier", "enum"}:
                value_columns["value_text"] = value
            elif value_type == "integer":
                value_columns["value_integer"] = value
            elif value_type == "real":
                value_columns["value_real"] = float(value)
            elif value_type == "boolean":
                value_columns["value_boolean"] = int(value)
            elif value_type == "json":
                value_columns["value_json"] = _json(value)
            else:
                raise ValueError(f"Unsupported Attribute value type: {value_type}")

        attribute_value_id = new_persistent_id()
        temporal_scope_id = self._insert_temporal_scope(
            version_id, attribute.get("temporal_scope"), timestamp
        )
        self.db.execute(
            """INSERT INTO object_version_attributes
               (id,version_id,attribute_id,ordinal,status,value_text,value_integer,value_real,
                value_boolean,value_json,language,temporal_scope_id,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                attribute_value_id,
                version_id,
                attribute["attribute_id"],
                ordinal,
                attribute["status"],
                value_columns["value_text"],
                value_columns["value_integer"],
                value_columns["value_real"],
                value_columns["value_boolean"],
                value_columns["value_json"],
                attribute.get("language"),
                temporal_scope_id,
                timestamp,
            ),
        )
        self._insert_evidence_links(
            version_id,
            "attribute",
            attribute_value_id,
            attribute["evidence"],
            role_ids,
            import_id,
            timestamp,
        )

    def _insert_relation(
        self,
        version_id: str,
        import_id: str,
        relation: Mapping[str, Any],
        role_ids: Mapping[str, str],
        timestamp: str,
    ) -> None:
        relation_id = new_persistent_id()
        self.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                relation_id,
                version_id,
                relation["subject_object_id"],
                relation["relation_type_id"],
                relation["object_object_id"],
                timestamp,
            ),
        )
        temporal_scope_id = self._insert_temporal_scope(
            version_id, relation.get("temporal_scope"), timestamp
        )
        if temporal_scope_id:
            self.db.execute(
                "INSERT INTO relation_temporal_scopes VALUES(?,?,?)",
                (relation_id, temporal_scope_id, timestamp),
            )
        self._insert_evidence_links(
            version_id,
            "relation",
            relation_id,
            relation["evidence"],
            role_ids,
            import_id,
            timestamp,
        )

    def _insert_evidence_links(
        self,
        version_id: str,
        target_kind: str,
        target_id: str,
        references: list[Mapping[str, Any]],
        role_ids: Mapping[str, str],
        import_id: str,
        timestamp: str,
    ) -> None:
        for reference in references:
            role_id = role_ids.get(reference["role"])
            if role_id is None:
                raise ValueError(f"Evidence role is no longer active: {reference['role']}")
            self.db.execute(
                """INSERT INTO evidence_links
                   (id,version_id,target_kind,target_id,evidence_id,role_id,origin_kind,origin_ref,created_at)
                   VALUES(?,?,?,?,?,?, 'result_import',?,?)""",
                (
                    new_persistent_id(),
                    version_id,
                    target_kind,
                    target_id,
                    reference["evidence_id"],
                    role_id,
                    import_id,
                    timestamp,
                ),
            )
