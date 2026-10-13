"""Multi-representation Hybrid Object Search and Object aggregation for I-04."""

from __future__ import annotations

import sqlite3
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Sequence

from sgokb.domain import (
    EmbeddingSpaceSpec,
    ObjectSearchChannel,
    ObjectSearchFilters,
    ObjectSearchMatch,
    ObjectSearchMode,
    ObjectSearchResponse,
    ObjectSearchResult,
    SearchRepresentationKind,
    VectorIndexAdapter,
    VectorIndexPoint,
    VectorMatch,
    VectorRange,
    VectorSearchFilter,
)

RRF_K = 60
DEFAULT_CANDIDATE_LIMIT = 100
MAX_MATCH_DETAILS = 8
_CHANNEL_CONTRIBUTION_CAPS = {
    ObjectSearchChannel.KNOWLEDGE_LEXICAL: 3,
    ObjectSearchChannel.SEMANTIC_OBJECT: 1,
    ObjectSearchChannel.SEMANTIC_FACET: 2,
    ObjectSearchChannel.SEMANTIC_STATEMENT: 3,
}
_DATE_MIN_ORDINAL = date.min.toordinal()
_DATE_MAX_ORDINAL = date.max.toordinal()


@dataclass(slots=True)
class _Candidate:
    object_id: str
    name: str
    primary_class: str
    version_id: str | None
    exact_tier: int = 0
    exact_identity: str | None = None
    channel_matches: dict[ObjectSearchChannel, list[ObjectSearchMatch]] = field(
        default_factory=lambda: defaultdict(list)
    )
    channel_ranks: dict[ObjectSearchChannel, int] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str | None]:
        return self.object_id, self.version_id


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


def _snippet(value: str, limit: int = 280) -> str:
    clean = " ".join(value.split())
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip() + "…"


def _iso_ordinal(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10]).toordinal()
    except ValueError as exc:
        raise ValueError(f"Temporal boundary must start with an ISO date: {value!r}") from exc


def _temporal_bounds(row: sqlite3.Row | dict | None) -> tuple[int, int]:
    if row is None:
        return _DATE_MIN_ORDINAL, _DATE_MAX_ORDINAL
    valid_from = _iso_ordinal(row["valid_from"])
    valid_to = _iso_ordinal(row["valid_to"])
    if valid_from is not None or valid_to is not None:
        return valid_from or _DATE_MIN_ORDINAL, valid_to or _DATE_MAX_ORDINAL
    as_of = _iso_ordinal(row["as_of"])
    if as_of is not None:
        return as_of, as_of
    return _DATE_MIN_ORDINAL, _DATE_MAX_ORDINAL


class KnowledgeVectorIndexBuilder:
    """Materialize accepted Knowledge memberships into a replaceable Vector Index.

    Embeddings are deduplicated by Search Representation. Vector points are membership-
    scoped so current/history/Class/Facet filters never lose membership identity.
    """

    def __init__(self, repository, vector_index: VectorIndexAdapter):
        self.repository = repository
        self.db = repository.db
        self.vector_index = vector_index
        self._class_lineage_cache: dict[str, tuple[str, ...]] = {}

    def _class_lineage_keys(self, class_id: str) -> tuple[str, ...]:
        if class_id in self._class_lineage_cache:
            return self._class_lineage_cache[class_id]
        rows = self.db.execute(
            """WITH RECURSIVE lineage(id) AS (
                   SELECT ?
                   UNION
                   SELECT p.parent_class_id
                   FROM object_class_parents p JOIN lineage l ON p.child_class_id=l.id
               )
               SELECT c.key FROM lineage l JOIN object_classes c ON c.id=l.id ORDER BY c.key""",
            (class_id,),
        ).fetchall()
        value = tuple(row["key"] for row in rows)
        self._class_lineage_cache[class_id] = value
        return value

    def _membership_rows(self) -> list[dict]:
        rows = self.db.execute(
            """SELECT m.*,o.status AS object_status,o.current_version_id,
                      cs.primary_class_id,pc.key AS primary_class,
                      f.key AS facet,s.derivation_kind,s.temporal_scope_id,
                      ts.as_of,ts.valid_from,ts.valid_to
               FROM knowledge_search_representation_memberships m
               JOIN object_version_lifecycle l ON l.version_id=m.version_id
               JOIN objects o ON o.id=m.object_id
               JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
               JOIN object_classes pc ON pc.id=cs.primary_class_id
               LEFT JOIN facet_definitions f ON f.id=m.facet_id
               LEFT JOIN knowledge_statements s ON s.id=m.statement_id
               LEFT JOIN temporal_scopes ts ON ts.id=s.temporal_scope_id
               WHERE l.state='accepted'
               ORDER BY m.object_id,m.version_id,m.target_kind,m.facet_id,m.statement_id,m.id"""
        ).fetchall()
        return [dict(row) for row in rows]

    def _additional_classes_by_version(self) -> dict[str, tuple[dict, ...]]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        rows = self.db.execute(
            """SELECT a.version_id,c.id,c.key
               FROM object_version_additional_class_snapshots a
               JOIN object_classes c ON c.id=a.class_id
               ORDER BY a.version_id,c.key"""
        ).fetchall()
        for row in rows:
            grouped[row["version_id"]].append(dict(row))
        return {version_id: tuple(values) for version_id, values in grouped.items()}

    def _metadata_from_row(self, row: dict, additional_rows: tuple[dict, ...]) -> dict:
        class_ids = [row["primary_class_id"], *(item["id"] for item in additional_rows)]
        lineage = sorted(
            {key for class_id in class_ids for key in self._class_lineage_keys(class_id)}
        )
        metadata: dict[str, object] = {
            "membership_id": row["id"],
            "representation_id": row["representation_id"],
            "kind": row["target_kind"],
            "object_id": row["object_id"],
            "version_id": row["version_id"],
            "primary_class": row["primary_class"],
            "additional_classes": tuple(item["key"] for item in additional_rows),
            "ancestor_classes": tuple(lineage),
            "object_status": row["object_status"],
            "is_current": row["current_version_id"] == row["version_id"],
        }
        if row["facet_id"] is not None:
            metadata["facet_id"] = row["facet_id"]
            metadata["facet"] = row["facet"]
        if row["statement_id"] is not None:
            metadata["statement_id"] = row["statement_id"]
            metadata["derivation_kind"] = row["derivation_kind"]
            if row["temporal_scope_id"] is not None:
                metadata["temporal_scope_id"] = row["temporal_scope_id"]
            valid_from, valid_to = _temporal_bounds(row)
            metadata["valid_from_ordinal"] = valid_from
            metadata["valid_to_ordinal"] = valid_to
        return metadata

    def points(self, space: EmbeddingSpaceSpec) -> tuple[VectorIndexPoint, ...]:
        embeddings = {
            row["representation_id"]: row["vector"]
            for row in self.repository.embedding_store.embedding_rows(space.space_id)
        }
        memberships = self._membership_rows()
        missing = sorted(
            {
                row["representation_id"]
                for row in memberships
                if row["representation_id"] not in embeddings
            }
        )
        if missing:
            raise ValueError(
                "Vector Index rebuild requires embeddings for every accepted membership; "
                f"missing={len(missing)}"
            )
        additional = self._additional_classes_by_version()
        return tuple(
            VectorIndexPoint(
                point_id=row["id"],
                vector=tuple(embeddings[row["representation_id"]]),
                metadata=self._metadata_from_row(row, additional.get(row["version_id"], ())),
            )
            for row in memberships
        )

    def rebuild(self, space: EmbeddingSpaceSpec):
        points = self.points(space)
        metadata = self.vector_index.rebuild(space, points)
        for row in self.db.execute(
            """SELECT object_id,revision FROM object_derived_states
               WHERE kind='vector_index' AND status<>'ready'
                 AND target_version_id=(
                   SELECT current_version_id FROM objects WHERE id=object_derived_states.object_id
                 )"""
        ).fetchall():
            self.repository.version_store.mark_derived_state(
                row["object_id"], "vector_index", row["revision"], "ready"
            )
        return metadata


class HybridObjectSearch:
    """Canonical Object Search Core. Search scores never become Knowledge confidence."""

    def __init__(self, repository, *, embedding_provider=None, vector_index=None):
        self.repository = repository
        self.db = repository.db
        self.embedding_provider = embedding_provider
        self.vector_index = vector_index

    def _class_id(self, key: str) -> str:
        row = self.db.execute("SELECT id FROM object_classes WHERE key=?", (key,)).fetchone()
        if not row:
            raise ValueError(f"Unknown Class filter: {key}")
        return row["id"]

    def _facet_id(self, key: str) -> str:
        row = self.db.execute("SELECT id FROM facet_definitions WHERE key=?", (key,)).fetchone()
        if not row:
            raise ValueError(f"Unknown Facet filter: {key}")
        return row["id"]

    def _validate_filters(self, filters: ObjectSearchFilters) -> None:
        for key in (filters.primary_class, filters.additional_class, filters.ancestor_class):
            if key is not None:
                self._class_id(key)
        if filters.facet is not None:
            self._facet_id(filters.facet)
        if filters.derivation_kind is not None and filters.derivation_kind not in {
            "direct_statement",
            "synthesis",
            "interpretation",
            "reported_view",
        }:
            raise ValueError("Unknown derivation_kind filter")
        if filters.knowledge_valid_at is not None:
            _iso_ordinal(filters.knowledge_valid_at)
        if filters.temporal_scope_id is not None:
            row = self.db.execute(
                "SELECT 1 FROM temporal_scopes WHERE id=?", (filters.temporal_scope_id,)
            ).fetchone()
            if not row:
                raise ValueError("Unknown temporal_scope_id filter")
        if filters.version_id is not None:
            row = self.db.execute(
                """SELECT 1 FROM object_version_lifecycle
                   WHERE version_id=? AND state='accepted'""",
                (filters.version_id,),
            ).fetchone()
            if not row:
                raise ValueError("Historical version filter must identify an accepted Version")

    def _descendant_class_ids(self, key: str) -> tuple[str, ...]:
        class_id = self._class_id(key)
        rows = self.db.execute(
            """WITH RECURSIVE descendants(id) AS (
                   SELECT ?
                   UNION
                   SELECT p.child_class_id
                   FROM object_class_parents p JOIN descendants d ON p.parent_class_id=d.id
               ) SELECT id FROM descendants ORDER BY id""",
            (class_id,),
        ).fetchall()
        return tuple(row["id"] for row in rows)

    def _scope_conditions(
        self,
        filters: ObjectSearchFilters,
        *,
        kinds: Sequence[str],
    ) -> tuple[list[str], list[object]]:
        clauses = ["l.state='accepted'"]
        params: list[object] = []
        if filters.version_id is None:
            clauses.append("o.current_version_id=m.version_id")
        else:
            clauses.append("m.version_id=?")
            params.append(filters.version_id)
        if not filters.include_archived:
            clauses.append("o.status='active'")
        placeholders = ",".join("?" for _ in kinds)
        clauses.append(f"m.target_kind IN ({placeholders})")
        params.extend(kinds)
        if filters.primary_class is not None:
            clauses.append("pc.key=?")
            params.append(filters.primary_class)
        if filters.additional_class is not None:
            clauses.append(
                """EXISTS (
                     SELECT 1 FROM object_version_additional_class_snapshots ac
                     JOIN object_classes acc ON acc.id=ac.class_id
                     WHERE ac.version_id=m.version_id AND acc.key=?
                   )"""
            )
            params.append(filters.additional_class)
        if filters.ancestor_class is not None:
            descendants = self._descendant_class_ids(filters.ancestor_class)
            marks = ",".join("?" for _ in descendants)
            clauses.append(
                f"""(cs.primary_class_id IN ({marks}) OR EXISTS (
                       SELECT 1 FROM object_version_additional_class_snapshots ac
                       WHERE ac.version_id=m.version_id AND ac.class_id IN ({marks})
                     ))"""
            )
            params.extend(descendants)
            params.extend(descendants)
        if filters.facet is not None:
            clauses.append("f.key=?")
            params.append(filters.facet)
        if filters.derivation_kind is not None:
            clauses.append("s.derivation_kind=?")
            params.append(filters.derivation_kind)
        if filters.temporal_scope_id is not None:
            clauses.append("s.temporal_scope_id=?")
            params.append(filters.temporal_scope_id)
        if filters.knowledge_valid_at is not None:
            day = filters.knowledge_valid_at[:10]
            clauses.append(
                """(s.temporal_scope_id IS NULL OR EXISTS (
                     SELECT 1 FROM temporal_scopes ts
                     WHERE ts.id=s.temporal_scope_id AND (
                       ((ts.valid_from IS NOT NULL OR ts.valid_to IS NOT NULL)
                         AND (ts.valid_from IS NULL OR date(ts.valid_from)<=date(?))
                         AND (ts.valid_to IS NULL OR date(ts.valid_to)>=date(?)))
                       OR
                       (ts.valid_from IS NULL AND ts.valid_to IS NULL
                         AND (ts.as_of IS NULL OR date(ts.as_of)=date(?)))
                     )
                   ))"""
            )
            params.extend([day, day, day])
        return clauses, params

    @staticmethod
    def _representation_kinds(filters: ObjectSearchFilters) -> tuple[str, ...]:
        if filters.knowledge_valid_at is not None or filters.temporal_scope_id is not None:
            return (SearchRepresentationKind.STATEMENT.value,)
        if filters.derivation_kind is not None:
            return (SearchRepresentationKind.STATEMENT.value,)
        if filters.facet is not None:
            return (
                SearchRepresentationKind.FACET.value,
                SearchRepresentationKind.STATEMENT.value,
            )
        return (
            SearchRepresentationKind.OBJECT_OVERALL.value,
            SearchRepresentationKind.FACET.value,
            SearchRepresentationKind.STATEMENT.value,
        )

    def _registry_rows(self, filters: ObjectSearchFilters) -> list[dict]:
        if filters.version_id is not None:
            sql = """SELECT o.id AS object_id,o.name,o.status,v.id AS version_id,
                            pc.key AS primary_class
                     FROM object_versions v
                     JOIN object_version_lifecycle l ON l.version_id=v.id AND l.state='accepted'
                     JOIN objects o ON o.id=v.object_id
                     JOIN object_version_classification_snapshots cs ON cs.version_id=v.id
                     JOIN object_classes pc ON pc.id=cs.primary_class_id
                     WHERE v.id=?"""
            params: list[object] = [filters.version_id]
            if not filters.include_archived:
                sql += " AND o.status='active'"
            if filters.primary_class is not None:
                sql += " AND pc.key=?"
                params.append(filters.primary_class)
            if filters.additional_class is not None:
                sql += """ AND EXISTS (
                  SELECT 1 FROM object_version_additional_class_snapshots ac
                  JOIN object_classes c ON c.id=ac.class_id
                  WHERE ac.version_id=v.id AND c.key=?)"""
                params.append(filters.additional_class)
            if filters.ancestor_class is not None:
                descendants = self._descendant_class_ids(filters.ancestor_class)
                marks = ",".join("?" for _ in descendants)
                sql += f""" AND (cs.primary_class_id IN ({marks}) OR EXISTS (
                  SELECT 1 FROM object_version_additional_class_snapshots ac
                  WHERE ac.version_id=v.id AND ac.class_id IN ({marks})))"""
                params.extend(descendants)
                params.extend(descendants)
            rows = [dict(row) for row in self.db.execute(sql, params)]
        else:
            sql = """SELECT o.id AS object_id,o.name,o.status,o.current_version_id AS version_id,
                            pc.key AS primary_class
                     FROM objects o JOIN object_classes pc ON pc.id=o.primary_class_id WHERE 1=1"""
            params = []
            if not filters.include_archived:
                sql += " AND o.status='active'"
            if filters.primary_class is not None:
                sql += " AND pc.key=?"
                params.append(filters.primary_class)
            if filters.additional_class is not None:
                sql += """ AND EXISTS (
                  SELECT 1 FROM object_additional_classes ac
                  JOIN object_classes c ON c.id=ac.class_id
                  WHERE ac.object_id=o.id AND c.key=?)"""
                params.append(filters.additional_class)
            if filters.ancestor_class is not None:
                descendants = self._descendant_class_ids(filters.ancestor_class)
                marks = ",".join("?" for _ in descendants)
                sql += f""" AND (o.primary_class_id IN ({marks}) OR EXISTS (
                  SELECT 1 FROM object_additional_classes ac
                  WHERE ac.object_id=o.id AND ac.class_id IN ({marks})))"""
                params.extend(descendants)
                params.extend(descendants)
            rows = [dict(row) for row in self.db.execute(sql, params)]

        if any(
            value is not None
            for value in (
                filters.facet,
                filters.temporal_scope_id,
                filters.knowledge_valid_at,
                filters.derivation_kind,
            )
        ):
            kinds = self._representation_kinds(filters)
            clauses, scope_params = self._scope_conditions(filters, kinds=kinds)
            scope_sql = """SELECT DISTINCT m.object_id,m.version_id
                           FROM knowledge_search_representation_memberships m
                           JOIN object_version_lifecycle l ON l.version_id=m.version_id
                           JOIN objects o ON o.id=m.object_id
                           JOIN object_version_classification_snapshots cs
                             ON cs.version_id=m.version_id
                           JOIN object_classes pc ON pc.id=cs.primary_class_id
                           LEFT JOIN facet_definitions f ON f.id=m.facet_id
                           LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                           WHERE """ + " AND ".join(clauses)
            allowed = {
                (row["object_id"], row["version_id"])
                for row in self.db.execute(scope_sql, scope_params)
            }
            rows = [row for row in rows if (row["object_id"], row["version_id"]) in allowed]
        return rows

    def _registry_hits(
        self, query: str, filters: ObjectSearchFilters, limit: int
    ) -> list[tuple[dict, ObjectSearchMatch, int]]:
        normalized_query = _normalize(query)
        terms = normalized_query.split()
        results: list[tuple[tuple, dict, ObjectSearchMatch, int]] = []
        registry_rows = self._registry_rows(filters)
        aliases_by_object: dict[str, list[str]] = defaultdict(list)
        object_ids = tuple(dict.fromkeys(row["object_id"] for row in registry_rows))
        if object_ids:
            marks = ",".join("?" for _ in object_ids)
            alias_rows = self.db.execute(
                f"SELECT object_id,value FROM object_aliases "
                f"WHERE object_id IN ({marks}) ORDER BY object_id,value,id",
                object_ids,
            ).fetchall()
            for item in alias_rows:
                aliases_by_object[item["object_id"]].append(item["value"])
        for row in registry_rows:
            aliases = aliases_by_object[row["object_id"]]
            values = [(row["name"], True), *((value, False) for value in aliases)]
            best = None
            for value, is_name in values:
                normalized = _normalize(value)
                exact = normalized == normalized_query
                contains = bool(terms) and all(term in normalized for term in terms)
                if not exact and not contains:
                    continue
                if exact and is_name:
                    tier, quality, identity, channel = 2, 0, "name", ObjectSearchChannel.EXACT_NAME
                elif exact:
                    tier, quality, identity, channel = (
                        1,
                        1,
                        "alias",
                        ObjectSearchChannel.EXACT_ALIAS,
                    )
                else:
                    tier = 0
                    quality = 2 if normalized.startswith(normalized_query) else 3
                    identity = None
                    channel = ObjectSearchChannel.REGISTRY_LEXICAL
                candidate = (quality, len(normalized), 0 if is_name else 1, normalized)
                if best is None or candidate < best[0]:
                    match = ObjectSearchMatch(
                        channel=channel,
                        version_id=row["version_id"],
                        representation_id=None,
                        membership_id=None,
                        representation_kind=None,
                        facet=None,
                        statement_id=None,
                        snippet=value,
                        score=None,
                        score_type="identity_literal" if exact else "registry_literal",
                    )
                    best = (candidate, match, tier, identity)
            if best is not None:
                sort_key = (*best[0], row["object_id"])
                results.append((sort_key, row, best[1], best[2]))
        results.sort(key=lambda item: item[0])
        output = []
        for rank, (_, row, match, tier) in enumerate(results[:limit], start=1):
            output.append(
                (
                    row,
                    ObjectSearchMatch(
                        channel=match.channel,
                        version_id=match.version_id,
                        representation_id=None,
                        membership_id=None,
                        representation_kind=None,
                        facet=None,
                        statement_id=None,
                        snippet=match.snippet,
                        score=match.score,
                        score_type=match.score_type,
                        source_rank=rank,
                    ),
                    tier,
                )
            )
        return output

    def _knowledge_lexical_hits(
        self, query: str, filters: ObjectSearchFilters, limit: int
    ) -> list[dict]:
        kinds = self._representation_kinds(filters)
        clauses, params = self._scope_conditions(filters, kinds=kinds)
        base = """SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                         m.target_kind,m.facet_id,m.statement_id,r.content,
                         f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                         o.name AS object_name
                  FROM search_representations r
                  JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
                  JOIN object_version_lifecycle l ON l.version_id=m.version_id
                  JOIN objects o ON o.id=m.object_id
                  JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                  JOIN object_classes pc ON pc.id=cs.primary_class_id
                  LEFT JOIN facet_definitions f ON f.id=m.facet_id
                  LEFT JOIN knowledge_statements s ON s.id=m.statement_id"""
        terms = [term for term in _normalize(query).split() if term]
        if not terms:
            return []
        if all(len(term) >= 3 for term in terms):
            expression = " AND ".join('"' + term.replace('"', '""') + '"' for term in terms)
            sql = """SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                            m.target_kind,m.facet_id,m.statement_id,r.content,
                            f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                            o.name AS object_name,bm25(search_representation_fts) AS lexical_score
                     FROM search_representation_fts
                     JOIN search_representations r
                       ON r.id=search_representation_fts.representation_id
                     JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
                     JOIN object_version_lifecycle l ON l.version_id=m.version_id
                     JOIN objects o ON o.id=m.object_id
                     JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                     JOIN object_classes pc ON pc.id=cs.primary_class_id
                     LEFT JOIN facet_definitions f ON f.id=m.facet_id
                     LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                     WHERE search_representation_fts MATCH ? AND """ + " AND ".join(clauses)
            try:
                rows = self.db.execute(
                    sql + " ORDER BY lexical_score,m.id LIMIT ?",
                    [expression, *params, limit],
                ).fetchall()
                return [dict(row) for row in rows]
            except sqlite3.OperationalError:
                pass
        literal_clauses = ["instr(lower(r.content),lower(?))>0" for _ in terms]
        rows = self.db.execute(
            base
            + " WHERE "
            + " AND ".join([*clauses, *literal_clauses])
            + " ORDER BY m.id LIMIT ?",
            [*params, *terms, limit],
        ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["lexical_score"] = None
            output.append(item)
        return output

    @staticmethod
    def _vector_filters(
        filters: ObjectSearchFilters, kind: SearchRepresentationKind
    ) -> VectorSearchFilter:
        matches = [VectorMatch("kind", (kind.value,))]
        ranges: list[VectorRange] = []
        if filters.version_id is None:
            matches.append(VectorMatch("is_current", (True,)))
        else:
            matches.append(VectorMatch("version_id", (filters.version_id,)))
        if not filters.include_archived:
            matches.append(VectorMatch("object_status", ("active",)))
        if filters.primary_class is not None:
            matches.append(VectorMatch("primary_class", (filters.primary_class,)))
        if filters.additional_class is not None:
            matches.append(VectorMatch("additional_classes", (filters.additional_class,)))
        if filters.ancestor_class is not None:
            matches.append(VectorMatch("ancestor_classes", (filters.ancestor_class,)))
        if filters.facet is not None:
            matches.append(VectorMatch("facet", (filters.facet,)))
        if filters.derivation_kind is not None:
            matches.append(VectorMatch("derivation_kind", (filters.derivation_kind,)))
        if filters.temporal_scope_id is not None:
            matches.append(VectorMatch("temporal_scope_id", (filters.temporal_scope_id,)))
        if filters.knowledge_valid_at is not None:
            ordinal = _iso_ordinal(filters.knowledge_valid_at)
            ranges.extend(
                [
                    VectorRange("valid_from_ordinal", lte=ordinal),
                    VectorRange("valid_to_ordinal", gte=ordinal),
                ]
            )
        return VectorSearchFilter(matches=tuple(matches), ranges=tuple(ranges))

    def _semantic_hits(
        self, query: str, filters: ObjectSearchFilters, limit: int
    ) -> tuple[list[dict], tuple[str, ...]]:
        if self.embedding_provider is None or self.vector_index is None:
            raise RuntimeError(
                "Semantic search requires an EmbeddingProvider and VectorIndexAdapter"
            )
        space = self.embedding_provider.space
        query_vector = self.embedding_provider.embed_queries([query])[0]
        kind_channels = {
            SearchRepresentationKind.OBJECT_OVERALL: ObjectSearchChannel.SEMANTIC_OBJECT,
            SearchRepresentationKind.FACET: ObjectSearchChannel.SEMANTIC_FACET,
            SearchRepresentationKind.STATEMENT: ObjectSearchChannel.SEMANTIC_STATEMENT,
        }
        allowed_kinds = set(self._representation_kinds(filters))
        raw_hits = []
        for kind, channel in kind_channels.items():
            if kind.value not in allowed_kinds:
                continue
            for hit in self.vector_index.search(
                space,
                query_vector,
                limit=limit,
                filters=self._vector_filters(filters, kind),
            ):
                raw_hits.append((channel, hit))
        if not raw_hits:
            return [], ()
        membership_ids = tuple(dict.fromkeys(hit.point_id for _, hit in raw_hits))
        marks = ",".join("?" for _ in membership_ids)
        rows = self.db.execute(
            f"""SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                       m.target_kind,m.facet_id,m.statement_id,r.content,
                       f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                       o.name AS object_name
                FROM knowledge_search_representation_memberships m
                JOIN search_representations r ON r.id=m.representation_id
                JOIN object_version_lifecycle l ON l.version_id=m.version_id AND l.state='accepted'
                JOIN objects o ON o.id=m.object_id
                JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                JOIN object_classes pc ON pc.id=cs.primary_class_id
                LEFT JOIN facet_definitions f ON f.id=m.facet_id
                LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                WHERE m.id IN ({marks})""",
            membership_ids,
        ).fetchall()
        details = {row["membership_id"]: dict(row) for row in rows}
        output = []
        for channel, hit in raw_hits:
            detail = details.get(hit.point_id)
            if detail is None:
                continue
            # Defense in depth against an obsolete derived index after a current-pointer change.
            if filters.version_id is None:
                current = self.db.execute(
                    "SELECT status,current_version_id FROM objects WHERE id=?",
                    (detail["object_id"],),
                ).fetchone()
                if not current or current["current_version_id"] != detail["version_id"]:
                    continue
                if not filters.include_archived and current["status"] != "active":
                    continue
            detail["channel"] = channel
            detail["semantic_score"] = hit.score
            detail["source_rank"] = hit.rank
            output.append(detail)
        return output, ()

    @staticmethod
    def _representation_match(row: dict, channel: ObjectSearchChannel) -> ObjectSearchMatch:
        lexical = channel is ObjectSearchChannel.KNOWLEDGE_LEXICAL
        raw_score = row.get("lexical_score") if lexical else row.get("semantic_score")
        score_type = (
            "bm25"
            if lexical and raw_score is not None
            else ("literal_contains" if lexical else "cosine_similarity")
        )
        text = row.get("statement_text") or row["content"]
        return ObjectSearchMatch(
            channel=channel,
            version_id=row["version_id"],
            representation_id=row["representation_id"],
            membership_id=row["membership_id"],
            representation_kind=row["target_kind"],
            facet=row.get("facet"),
            statement_id=row.get("statement_id"),
            snippet=_snippet(text),
            score=None if raw_score is None else float(raw_score),
            score_type=score_type,
            source_rank=row.get("source_rank"),
        )

    @staticmethod
    def _aggregate_channel(
        rows: Iterable[tuple[tuple[str, str | None], ObjectSearchMatch]],
        channel: ObjectSearchChannel,
    ) -> tuple[
        dict[tuple[str, str | None], int], dict[tuple[str, str | None], list[ObjectSearchMatch]]
    ]:
        grouped: dict[tuple[str, str | None], list[ObjectSearchMatch]] = defaultdict(list)
        for key, match in rows:
            grouped[key].append(match)
        cap = _CHANNEL_CONTRIBUTION_CAPS.get(channel, 1)
        scored = []
        for key, matches in grouped.items():
            ordered = sorted(
                matches,
                key=lambda item: (
                    item.source_rank if item.source_rank is not None else 10**9,
                    item.membership_id or "",
                ),
            )
            contribution = sum(
                1.0 / (RRF_K + (item.source_rank or 10**6)) for item in ordered[:cap]
            )
            scored.append((key, contribution, ordered))
        scored.sort(key=lambda item: (-item[1], item[0][0], item[0][1] or ""))
        ranks = {key: rank for rank, (key, _, _) in enumerate(scored, start=1)}
        details = {key: ordered for key, _, ordered in scored}
        return ranks, details

    def search(
        self,
        query: str,
        *,
        filters: ObjectSearchFilters = ObjectSearchFilters(),
        limit: int = 10,
        mode: ObjectSearchMode | str = ObjectSearchMode.HYBRID,
        candidate_limit: int | None = None,
    ) -> ObjectSearchResponse:
        query = query.strip()
        if not query:
            raise ValueError("Search query must be non-empty")
        if not 1 <= limit <= 1000:
            raise ValueError("Search limit must be between 1 and 1000")
        mode = ObjectSearchMode(mode)
        self._validate_filters(filters)
        pool = candidate_limit or max(DEFAULT_CANDIDATE_LIMIT, min(1000, limit * 10))
        if not 1 <= pool <= 1000:
            raise ValueError("candidate_limit must be between 1 and 1000")

        candidates: dict[tuple[str, str | None], _Candidate] = {}
        channel_rows: dict[
            ObjectSearchChannel, list[tuple[tuple[str, str | None], ObjectSearchMatch]]
        ] = defaultdict(list)
        degraded: list[str] = []

        if mode in {ObjectSearchMode.LEXICAL, ObjectSearchMode.HYBRID}:
            registry = self._registry_hits(query, filters, pool)
            for row, match, tier in registry:
                key = row["object_id"], row["version_id"]
                candidate = candidates.setdefault(
                    key,
                    _Candidate(
                        object_id=row["object_id"],
                        name=row["name"],
                        primary_class=row["primary_class"],
                        version_id=row["version_id"],
                    ),
                )
                if tier > candidate.exact_tier:
                    candidate.exact_tier = tier
                    candidate.exact_identity = "name" if tier == 2 else "alias"
                candidate.channel_matches[match.channel].append(match)
                if match.channel is ObjectSearchChannel.REGISTRY_LEXICAL:
                    channel_rows[ObjectSearchChannel.REGISTRY_LEXICAL].append((key, match))
                else:
                    # Exact hits also participate in registry lexical fusion, while their tier
                    # independently guarantees identity priority over non-exact semantic hits.
                    lexical_match = ObjectSearchMatch(
                        channel=ObjectSearchChannel.REGISTRY_LEXICAL,
                        version_id=match.version_id,
                        representation_id=None,
                        membership_id=None,
                        representation_kind=None,
                        facet=None,
                        statement_id=None,
                        snippet=match.snippet,
                        score=None,
                        score_type="registry_literal",
                        source_rank=match.source_rank,
                    )
                    channel_rows[ObjectSearchChannel.REGISTRY_LEXICAL].append((key, lexical_match))
            for rank, row in enumerate(self._knowledge_lexical_hits(query, filters, pool), start=1):
                row["source_rank"] = rank
                key = row["object_id"], row["version_id"]
                candidates.setdefault(
                    key,
                    _Candidate(
                        object_id=row["object_id"],
                        name=row["object_name"],
                        primary_class=row["primary_class"],
                        version_id=row["version_id"],
                    ),
                )
                match = self._representation_match(row, ObjectSearchChannel.KNOWLEDGE_LEXICAL)
                channel_rows[ObjectSearchChannel.KNOWLEDGE_LEXICAL].append((key, match))

        if mode in {ObjectSearchMode.SEMANTIC, ObjectSearchMode.HYBRID}:
            try:
                semantic_rows, _ = self._semantic_hits(query, filters, pool)
                for row in semantic_rows:
                    channel = row["channel"]
                    key = row["object_id"], row["version_id"]
                    candidates.setdefault(
                        key,
                        _Candidate(
                            object_id=row["object_id"],
                            name=row["object_name"],
                            primary_class=row["primary_class"],
                            version_id=row["version_id"],
                        ),
                    )
                    match = self._representation_match(row, channel)
                    channel_rows[channel].append((key, match))
            except Exception as exc:
                if mode is ObjectSearchMode.SEMANTIC:
                    raise
                degraded.append(f"semantic:{type(exc).__name__}")

        for channel, rows in channel_rows.items():
            if channel is ObjectSearchChannel.REGISTRY_LEXICAL:
                grouped: dict[tuple[str, str | None], list[ObjectSearchMatch]] = defaultdict(list)
                for key, match in rows:
                    grouped[key].append(match)
                ordered_keys = sorted(
                    grouped,
                    key=lambda key: (
                        min(item.source_rank or 10**9 for item in grouped[key]),
                        key[0],
                        key[1] or "",
                    ),
                )
                ranks = {key: rank for rank, key in enumerate(ordered_keys, start=1)}
                details = grouped
            else:
                ranks, details = self._aggregate_channel(rows, channel)
            for key, rank in ranks.items():
                candidate = candidates[key]
                candidate.channel_ranks[channel] = rank
                candidate.channel_matches[channel].extend(details[key])

        scored = []
        for candidate in candidates.values():
            fused = sum(1.0 / (RRF_K + rank) for rank in candidate.channel_ranks.values())
            scored.append((candidate, fused))
        scored.sort(
            key=lambda item: (
                -item[0].exact_tier,
                -item[1],
                item[0].object_id,
                item[0].version_id or "",
            )
        )

        results = []
        for rank, (candidate, fused) in enumerate(scored[:limit], start=1):
            all_matches = [
                match for values in candidate.channel_matches.values() for match in values
            ]
            unique: dict[tuple, ObjectSearchMatch] = {}
            for match in all_matches:
                identity = (
                    match.channel,
                    match.membership_id,
                    match.representation_id,
                    match.snippet,
                )
                unique.setdefault(identity, match)
            matches = sorted(
                unique.values(),
                key=lambda item: (
                    item.source_rank if item.source_rank is not None else 10**9,
                    item.channel.value,
                    item.membership_id or "",
                ),
            )[:MAX_MATCH_DETAILS]
            channels = tuple(
                sorted({match.channel for match in matches}, key=lambda item: item.value)
            )
            facets = tuple(sorted({match.facet for match in all_matches if match.facet}))
            results.append(
                ObjectSearchResult(
                    object_id=candidate.object_id,
                    name=candidate.name,
                    primary_class=candidate.primary_class,
                    version_id=candidate.version_id,
                    rank=rank,
                    fused_score=fused,
                    score_type="rrf",
                    exact_identity=candidate.exact_identity,
                    channels=channels,
                    matched_facets=facets,
                    matches=tuple(matches),
                )
            )
        return ObjectSearchResponse(
            query=query,
            mode=mode,
            results=tuple(results),
            degraded_channels=tuple(degraded),
        )
