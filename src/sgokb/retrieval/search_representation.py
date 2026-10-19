"""Deterministic derived Search Representation builder for Phase I / I-01."""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass

from sgokb.domain import SearchRepresentationKind


@dataclass(frozen=True, slots=True)
class BuiltSearchRepresentation:
    kind: SearchRepresentationKind
    builder_key: str
    builder_version: str
    content: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


class SearchRepresentationBuilder:
    """Build searchable text from accepted canonical Knowledge or canonical Evidence.

    The builder performs no embedding, ranking, inference, or generative synthesis.
    Stable IDs and other coordination metadata stay in membership rows rather than
    being injected into semantic text.
    """

    BUILDER_KEY = "sgokb-canonical-search"
    BUILDER_VERSION = "1"

    def __init__(self, repository):
        self.repository = repository
        self.db = repository.db

    @staticmethod
    def _clean(value: object | None) -> str:
        if value is None:
            return ""
        return " ".join(unicodedata.normalize("NFC", str(value)).split())

    @classmethod
    def _append(cls, lines: list[str], label: str, value: object | None) -> None:
        cleaned = cls._clean(value)
        if cleaned:
            lines.append(f"{label}: {cleaned}")

    def _version_context(self, version_id: str) -> dict:
        row = self.db.execute(
            """SELECT v.id AS version_id,v.object_id,o.name AS object_name,
                      o.status AS object_status,
                      l.state,c.primary_class_id,oc.key AS class_key,oc.name AS class_name
               FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id
               JOIN objects o ON o.id=v.object_id
               JOIN object_version_classification_snapshots c ON c.version_id=v.id
               JOIN object_classes oc ON oc.id=c.primary_class_id
               WHERE v.id=?""",
            (version_id,),
        ).fetchone()
        if not row:
            raise ValueError("Unknown Object Knowledge Version ID")
        if row["state"] != "accepted":
            raise ValueError("Search Representations require an accepted Object Knowledge Version")
        return dict(row)

    def _facet_row(self, version_id: str, facet_id: str) -> dict | None:
        row = self.db.execute(
            """SELECT f.id AS facet_id,f.key,f.name,vf.status
               FROM object_version_facets vf
               JOIN facet_definitions f ON f.id=vf.facet_id
               WHERE vf.version_id=? AND vf.facet_id=?""",
            (version_id, facet_id),
        ).fetchone()
        if not row or row["status"] != "content":
            return None
        return dict(row)

    def _temporal_text(self, temporal_scope_id: str | None) -> str:
        if not temporal_scope_id:
            return ""
        row = self.db.execute(
            """SELECT t.*,o.name AS context_object_name
               FROM temporal_scopes t
               LEFT JOIN objects o ON o.id=t.context_object_id
               WHERE t.id=?""",
            (temporal_scope_id,),
        ).fetchone()
        if not row:
            return ""
        parts: list[str] = []
        if row["label"]:
            parts.append(self._clean(row["label"]))
        if row["as_of"]:
            parts.append(f"as_of={self._clean(row['as_of'])}")
        if row["valid_from"]:
            parts.append(f"from={self._clean(row['valid_from'])}")
        if row["valid_to"]:
            parts.append(f"to={self._clean(row['valid_to'])}")
        if row["context_object_name"]:
            parts.append(f"context={self._clean(row['context_object_name'])}")
        return "; ".join(parts)

    def _statement_line(self, row) -> str:
        prefix: list[str] = []
        temporal = self._temporal_text(row["temporal_scope_id"])
        if temporal:
            prefix.append(f"temporal={temporal}")
        if row["derivation_kind"] != "direct_statement":
            prefix.append(f"derivation={row['derivation_kind']}")
        text = self._clean(row["text"])
        return f"[{'; '.join(prefix)}] {text}" if prefix else text

    def _statement_rows(self, version_id: str, facet_id: str | None | object = ...) -> list:
        if facet_id is ...:
            return self.db.execute(
                """SELECT * FROM knowledge_statements
                   WHERE version_id=? ORDER BY local_key,id""",
                (version_id,),
            ).fetchall()
        if facet_id is None:
            return self.db.execute(
                """SELECT * FROM knowledge_statements
                   WHERE version_id=? AND facet_id IS NULL ORDER BY local_key,id""",
                (version_id,),
            ).fetchall()
        return self.db.execute(
            """SELECT * FROM knowledge_statements
               WHERE version_id=? AND facet_id=? ORDER BY local_key,id""",
            (version_id, facet_id),
        ).fetchall()

    def build_statement(self, statement_id: str) -> BuiltSearchRepresentation | None:
        statement = self.db.execute(
            "SELECT * FROM knowledge_statements WHERE id=?", (statement_id,)
        ).fetchone()
        if not statement:
            raise ValueError("Unknown Knowledge Statement ID")
        context = self._version_context(statement["version_id"])
        facet = None
        if statement["facet_id"] is not None:
            facet = self._facet_row(statement["version_id"], statement["facet_id"])
            if facet is None:
                return None

        lines: list[str] = []
        self._append(lines, "Object", context["object_name"])
        lines.append(
            f"Primary Class: {self._clean(context['class_key'])} "
            f"({self._clean(context['class_name'])})"
        )
        if facet is not None:
            lines.append(f"Facet: {self._clean(facet['name'])} ({self._clean(facet['key'])})")
        temporal = self._temporal_text(statement["temporal_scope_id"])
        self._append(lines, "Temporal Scope", temporal)
        if statement["derivation_kind"] != "direct_statement":
            self._append(lines, "Derivation", statement["derivation_kind"])
        self._append(lines, "Statement", statement["text"])
        return BuiltSearchRepresentation(
            SearchRepresentationKind.STATEMENT,
            self.BUILDER_KEY,
            self.BUILDER_VERSION,
            "\n".join(lines),
        )

    def build_facet(self, version_id: str, facet_id: str) -> BuiltSearchRepresentation | None:
        context = self._version_context(version_id)
        facet = self._facet_row(version_id, facet_id)
        if facet is None:
            return None
        rows = self._statement_rows(version_id, facet_id)
        if not rows:
            return None

        lines: list[str] = []
        self._append(lines, "Object", context["object_name"])
        lines.append(
            f"Primary Class: {self._clean(context['class_key'])} "
            f"({self._clean(context['class_name'])})"
        )
        lines.append(f"Facet: {self._clean(facet['name'])} ({self._clean(facet['key'])})")
        if rows:
            lines.append("Statements:")
            lines.extend(f"- {self._statement_line(row)}" for row in rows)
        if facet["key"] == "relationships":
            relations = self._relation_lines(version_id)
            if relations:
                lines.append("Relations:")
                lines.extend(relations)
        return BuiltSearchRepresentation(
            SearchRepresentationKind.FACET,
            self.BUILDER_KEY,
            self.BUILDER_VERSION,
            "\n".join(lines),
        )

    def _attribute_lines(self, version_id: str) -> list[str]:
        rows = self.db.execute(
            """SELECT a.*,d.key,d.name,d.value_type
               FROM object_version_attributes a
               JOIN attribute_definitions d ON d.id=a.attribute_id
               WHERE a.version_id=? AND a.status='known'
               ORDER BY d.key,a.ordinal,a.id""",
            (version_id,),
        ).fetchall()
        result: list[str] = []
        for row in rows:
            value = None
            for column in (
                "value_text",
                "value_integer",
                "value_real",
                "value_boolean",
                "value_json",
            ):
                if row[column] is not None:
                    value = row[column]
                    if column == "value_boolean":
                        value = "true" if bool(value) else "false"
                    break
            if value is not None:
                result.append(f"- {self._clean(row['name'])}: {self._clean(value)}")
        return result

    def _relation_lines(self, version_id: str) -> list[str]:
        rows = self.db.execute(
            """SELECT r.id,rt.key,rt.name,subject.name AS subject_name,
                      object.name AS object_name,ts.temporal_scope_id
               FROM object_relations r
               JOIN relation_types rt ON rt.id=r.relation_type_id
               JOIN objects subject ON subject.id=r.subject_object_id
               JOIN objects object ON object.id=r.object_object_id
               LEFT JOIN relation_temporal_scopes ts ON ts.relation_id=r.id
               WHERE r.version_id=?
               ORDER BY subject.name,rt.key,object.name,r.id""",
            (version_id,),
        ).fetchall()
        result: list[str] = []
        for row in rows:
            value = (
                f"{self._clean(row['subject_name'])} "
                f"{self._clean(row['name'])} {self._clean(row['object_name'])}"
            )
            temporal = self._temporal_text(row["temporal_scope_id"])
            if temporal:
                value += f" [temporal={temporal}]"
            result.append(f"- {value}")
        return result

    def build_object_overall(self, version_id: str) -> BuiltSearchRepresentation:
        context = self._version_context(version_id)
        aliases = [
            self._clean(row["value"])
            for row in self.db.execute(
                """SELECT value FROM object_aliases WHERE object_id=?
                   ORDER BY value COLLATE NOCASE,value,id""",
                (context["object_id"],),
            )
            if self._clean(row["value"])
        ]
        lines: list[str] = []
        self._append(lines, "Object", context["object_name"])
        if aliases:
            lines.append("Aliases: " + ", ".join(aliases))
        lines.append(
            f"Primary Class: {self._clean(context['class_key'])} "
            f"({self._clean(context['class_name'])})"
        )

        summaries = self._statement_rows(version_id, None)
        if summaries:
            lines.append("Summary Statements:")
            lines.extend(f"- {self._statement_line(row)}" for row in summaries)

        facets = self.db.execute(
            """SELECT f.id,f.key,f.name
               FROM object_version_facets vf
               JOIN facet_definitions f ON f.id=vf.facet_id
               WHERE vf.version_id=? AND vf.status='content'
               ORDER BY f.key,f.id""",
            (version_id,),
        ).fetchall()
        for facet in facets:
            statements = self._statement_rows(version_id, facet["id"])
            if not statements:
                continue
            lines.append(f"Facet {self._clean(facet['name'])} ({self._clean(facet['key'])}):")
            lines.extend(f"- {self._statement_line(row)}" for row in statements)

        attributes = self._attribute_lines(version_id)
        if attributes:
            lines.append("Attributes:")
            lines.extend(attributes)

        relations = self._relation_lines(version_id)
        if relations:
            lines.append("Relations:")
            lines.extend(relations)

        return BuiltSearchRepresentation(
            SearchRepresentationKind.OBJECT_OVERALL,
            self.BUILDER_KEY,
            self.BUILDER_VERSION,
            "\n".join(lines),
        )

    def build_evidence(self, evidence_id: str) -> BuiltSearchRepresentation:
        row = self.db.execute(
            """SELECT e.*,s.label AS source_label,n.title AS snapshot_title
               FROM evidence_records e
               JOIN source_records s ON s.id=e.source_id
               JOIN source_snapshots n ON n.id=e.snapshot_id
               WHERE e.id=?""",
            (evidence_id,),
        ).fetchone()
        if not row:
            raise ValueError("Unknown evidence ID")
        lines: list[str] = []
        self._append(lines, "Source", row["source_label"])
        self._append(lines, "Title", row["snapshot_title"])
        self._append(lines, "Language", row["language"])
        classifications = self.db.execute(
            """SELECT axis,value FROM source_classifications
               WHERE source_id=? AND (snapshot_id IS NULL OR snapshot_id=?)
               ORDER BY axis,value,id""",
            (row["source_id"], row["snapshot_id"]),
        ).fetchall()
        for item in classifications:
            lines.append(f"Source {self._clean(item['axis'])}: {self._clean(item['value'])}")
        self._append(lines, "Evidence", row["content"])
        return BuiltSearchRepresentation(
            SearchRepresentationKind.EVIDENCE,
            self.BUILDER_KEY,
            self.BUILDER_VERSION,
            "\n".join(lines),
        )

    def _persist(self, built: BuiltSearchRepresentation) -> str:
        return self.repository.semantic_store.get_or_create_search_representation(
            built.kind,
            built.builder_key,
            built.builder_version,
            built.content,
        )

    def materialize_version(self, version_id: str) -> tuple[str, ...]:
        context = self._version_context(version_id)
        stored: list[str] = []

        overall = self.build_object_overall(version_id)
        representation_id = self._persist(overall)
        self.repository.semantic_store.link_knowledge_search_representation(
            context["object_id"],
            version_id,
            representation_id,
            SearchRepresentationKind.OBJECT_OVERALL,
        )
        stored.append(representation_id)

        facets = self.db.execute(
            """SELECT facet_id FROM object_version_facets
               WHERE version_id=? AND status='content' ORDER BY facet_id""",
            (version_id,),
        ).fetchall()
        for facet in facets:
            built = self.build_facet(version_id, facet["facet_id"])
            if built is None:
                continue
            representation_id = self._persist(built)
            self.repository.semantic_store.link_knowledge_search_representation(
                context["object_id"],
                version_id,
                representation_id,
                SearchRepresentationKind.FACET,
                facet_id=facet["facet_id"],
            )
            stored.append(representation_id)

        for statement in self._statement_rows(version_id):
            built = self.build_statement(statement["id"])
            if built is None:
                continue
            representation_id = self._persist(built)
            self.repository.semantic_store.link_knowledge_search_representation(
                context["object_id"],
                version_id,
                representation_id,
                SearchRepresentationKind.STATEMENT,
                facet_id=statement["facet_id"],
                statement_id=statement["id"],
            )
            stored.append(representation_id)
        return tuple(stored)

    def materialize_evidence(self, evidence_id: str) -> str:
        representation_id = self._persist(self.build_evidence(evidence_id))
        self.repository.semantic_store.link_evidence_search_representation(
            representation_id, evidence_id
        )
        return representation_id
