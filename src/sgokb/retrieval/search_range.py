"""Range-aware extension for canonical R2 Object Search.

The public CLI historically exposes one ``valid_at`` value. P-GUI-06 needs an
optional From/To range without changing that transport contract. A range is
encoded in the existing value as ``YYYY-MM-DD..YYYY-MM-DD``; either endpoint may
be omitted. Plain values keep the historical point-in-time semantics unchanged.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import date

from sgokb.domain import (
    ObjectSearchFilters,
    SearchRepresentationKind,
    VectorRange,
    VectorSearchFilter,
)

from .hybrid_search import HybridObjectSearch as _PhaseIHybridObjectSearch
from .hybrid_search import _normalize
from .hybrid_search_r2 import HybridObjectSearch as _R2HybridObjectSearch

_RANGE_SEPARATOR = ".."


def _date_ordinal(value: str) -> int:
    try:
        return date.fromisoformat(value[:10]).toordinal()
    except ValueError as exc:
        raise ValueError(f"Temporal boundary must start with an ISO date: {value!r}") from exc


def _validity_range(value: str | None) -> tuple[str | None, str | None] | None:
    if value is None or _RANGE_SEPARATOR not in value:
        return None
    if value.count(_RANGE_SEPARATOR) != 1:
        raise ValueError("Knowledge validity range must contain one '..' separator")
    raw_from, raw_to = (part.strip() for part in value.split(_RANGE_SEPARATOR, 1))
    if not raw_from and not raw_to:
        raise ValueError("Knowledge validity range requires From or To")
    valid_from = raw_from[:10] if raw_from else None
    valid_to = raw_to[:10] if raw_to else None
    from_ordinal = _date_ordinal(valid_from) if valid_from else None
    to_ordinal = _date_ordinal(valid_to) if valid_to else None
    if from_ordinal is not None and to_ordinal is not None and from_ordinal > to_ordinal:
        raise ValueError("Knowledge validity From must not be after To")
    return valid_from, valid_to


def encode_validity_range(valid_from: str | None, valid_to: str | None) -> str | None:
    """Encode GUI From/To values into the backwards-compatible ``valid_at`` slot."""

    left = (valid_from or "").strip()
    right = (valid_to or "").strip()
    if not left and not right:
        return None
    _date_ordinal(left) if left else None
    _date_ordinal(right) if right else None
    if left and right and _date_ordinal(left) > _date_ordinal(right):
        raise ValueError("Knowledge validity From must not be after To")
    return f"{left}{_RANGE_SEPARATOR}{right}"


def _temporal_overlap_sql(
    validity: tuple[str | None, str | None],
) -> tuple[str, list[object]]:
    """Return canonical Statement temporal-overlap SQL and bound parameters."""

    valid_from, valid_to = validity
    interval_terms: list[str] = []
    point_terms: list[str] = []
    interval_params: list[object] = []
    point_params: list[object] = []
    if valid_from is not None:
        interval_terms.append("(ts.valid_to IS NULL OR date(ts.valid_to)>=date(?))")
        interval_params.append(valid_from)
        point_terms.append("date(ts.as_of)>=date(?)")
        point_params.append(valid_from)
    if valid_to is not None:
        interval_terms.append("(ts.valid_from IS NULL OR date(ts.valid_from)<=date(?))")
        interval_params.append(valid_to)
        point_terms.append("date(ts.as_of)<=date(?)")
        point_params.append(valid_to)

    interval_sql = " AND ".join(interval_terms) or "1=1"
    point_sql = " AND ".join(point_terms) or "1=1"
    sql = (
        "(s.temporal_scope_id IS NULL OR EXISTS ("
        " SELECT 1 FROM temporal_scopes ts"
        " WHERE ts.id=s.temporal_scope_id AND ("
        "   ((ts.valid_from IS NOT NULL OR ts.valid_to IS NOT NULL) AND "
        + interval_sql
        + ") OR "
        "   (ts.valid_from IS NULL AND ts.valid_to IS NULL"
        "     AND (ts.as_of IS NULL OR ("
        + point_sql
        + ")))"
        " )"
        "))"
    )
    return sql, [*interval_params, *point_params]


class RangeAwareHybridObjectSearch(_R2HybridObjectSearch):
    """R2 Hybrid Search with an optional temporal-overlap range filter."""

    @staticmethod
    def _without_range(filters: ObjectSearchFilters) -> ObjectSearchFilters:
        return replace(filters, knowledge_valid_at=None)

    def _validate_filters(self, filters: ObjectSearchFilters) -> None:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is None:
            super()._validate_filters(filters)
            return
        super()._validate_filters(self._without_range(filters))

    def _representation_kinds(self, filters: ObjectSearchFilters) -> tuple[str, ...]:
        if _validity_range(filters.knowledge_valid_at) is not None:
            return (SearchRepresentationKind.STATEMENT.value,)
        return super()._representation_kinds(filters)

    def _scope_conditions(
        self,
        filters: ObjectSearchFilters,
        *,
        kinds,
    ) -> tuple[list[str], list[object]]:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is None:
            return _PhaseIHybridObjectSearch._scope_conditions(self, filters, kinds=kinds)

        clauses, params = _PhaseIHybridObjectSearch._scope_conditions(
            self,
            self._without_range(filters),
            kinds=kinds,
        )
        temporal_sql, temporal_params = _temporal_overlap_sql(validity)
        clauses.append(temporal_sql)
        params.extend(temporal_params)
        return clauses, params

    @staticmethod
    def _vector_filters(
        filters: ObjectSearchFilters,
        kind: SearchRepresentationKind,
    ) -> VectorSearchFilter:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is None:
            return _PhaseIHybridObjectSearch._vector_filters(filters, kind)
        base = _PhaseIHybridObjectSearch._vector_filters(
            replace(filters, knowledge_valid_at=None),
            kind,
        )
        valid_from, valid_to = validity
        ranges = list(base.ranges)
        if valid_from is not None:
            ranges.append(VectorRange("valid_to_ordinal", gte=_date_ordinal(valid_from)))
        if valid_to is not None:
            ranges.append(VectorRange("valid_from_ordinal", lte=_date_ordinal(valid_to)))
        return VectorSearchFilter(
            matches=base.matches,
            excludes=base.excludes,
            ranges=tuple(ranges),
        )

    def _canonical_range_pairs(
        self,
        rows: list[dict],
        filters: ObjectSearchFilters,
        validity: tuple[str | None, str | None],
    ) -> set[tuple[str, str]]:
        """Resolve range-eligible Registry candidates from canonical accepted Knowledge.

        Registry name/alias identity is canonical data and must not disappear merely
        because the active derived Search generation lags a newly accepted current
        Version. Knowledge lexical/semantic channels remain generation-scoped elsewhere.
        """

        version_ids = tuple(
            dict.fromkeys(
                str(row["version_id"])
                for row in rows
                if isinstance(row.get("version_id"), str) and row["version_id"]
            )
        )
        if not version_ids:
            return set()

        marks = ",".join("?" for _ in version_ids)
        clauses = [f"s.version_id IN ({marks})", "l.state='accepted'"]
        params: list[object] = list(version_ids)
        if filters.facet is not None:
            clauses.append("f.key=?")
            params.append(filters.facet)
        if filters.derivation_kind is not None:
            clauses.append("s.derivation_kind=?")
            params.append(filters.derivation_kind)
        if filters.temporal_scope_id is not None:
            clauses.append("s.temporal_scope_id=?")
            params.append(filters.temporal_scope_id)
        temporal_sql, temporal_params = _temporal_overlap_sql(validity)
        clauses.append(temporal_sql)
        params.extend(temporal_params)

        sql = (
            "SELECT DISTINCT v.object_id,s.version_id "
            "FROM knowledge_statements s "
            "JOIN object_versions v ON v.id=s.version_id "
            "JOIN object_version_lifecycle l ON l.version_id=s.version_id "
            "LEFT JOIN facet_definitions f ON f.id=s.facet_id "
            "WHERE "
            + " AND ".join(clauses)
        )
        return {
            (str(row["object_id"]), str(row["version_id"]))
            for row in self.db.execute(sql, params)
        }

    def _registry_rows(self, filters: ObjectSearchFilters) -> list[dict]:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is None:
            return super()._registry_rows(filters)

        rows = super()._registry_rows(self._without_range(filters))
        if not rows:
            return rows
        allowed = self._canonical_range_pairs(rows, filters, validity)
        return [
            row
            for row in rows
            if isinstance(row.get("version_id"), str)
            and (str(row["object_id"]), str(row["version_id"])) in allowed
        ]

    def _knowledge_lexical_hits(
        self,
        query: str,
        filters: ObjectSearchFilters,
        limit: int,
    ) -> list[dict]:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is None:
            return super()._knowledge_lexical_hits(query, filters, limit)

        generation = self._current_generation()
        if generation.generation_id is None:
            return _PhaseIHybridObjectSearch._knowledge_lexical_hits(
                self,
                query,
                filters,
                limit,
            )

        kinds = self._representation_kinds(filters)
        clauses, params = self._scope_conditions(filters, kinds=kinds)
        clauses.append("gm.generation_id=?")
        params.append(generation.generation_id)
        base = """SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                         m.target_kind,m.facet_id,m.statement_id,r.content,
                         f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                         o.name AS object_name
                  FROM search_representations r
                  JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
                  JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
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
                     JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
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

    def _vector_filters_for_generation(
        self,
        filters: ObjectSearchFilters,
        kind: SearchRepresentationKind,
    ) -> VectorSearchFilter:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is None:
            return super()._vector_filters_for_generation(filters, kind)

        base = super()._vector_filters_for_generation(self._without_range(filters), kind)
        valid_from, valid_to = validity
        ranges = list(base.ranges)
        if valid_from is not None:
            ranges.append(VectorRange("valid_to_ordinal", gte=_date_ordinal(valid_from)))
        if valid_to is not None:
            ranges.append(VectorRange("valid_from_ordinal", lte=_date_ordinal(valid_to)))
        return VectorSearchFilter(
            matches=base.matches,
            excludes=base.excludes,
            ranges=tuple(ranges),
        )
