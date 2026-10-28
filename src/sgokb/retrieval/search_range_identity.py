"""Registry-identity completion for range-aware Object Search.

A Knowledge validity range constrains temporal Knowledge. An accepted Version with
no Knowledge Statements has no statement-level temporal restriction, so a range
must not make its canonical Object name/alias identity disappear. Statement-
specific filters still require a matching Statement.
"""

from __future__ import annotations

from sgokb.domain import ObjectSearchFilters

from .search_range import RangeAwareHybridObjectSearch as _BaseRangeAwareHybridObjectSearch


class RangeAwareHybridObjectSearch(_BaseRangeAwareHybridObjectSearch):
    """Keep statement-less accepted Versions identity-visible under From/To."""

    def _canonical_range_pairs(
        self,
        rows: list[dict],
        filters: ObjectSearchFilters,
        validity: tuple[str | None, str | None],
    ) -> set[tuple[str, str]]:
        allowed = super()._canonical_range_pairs(rows, filters, validity)

        # Facet / Derivation / Temporal Scope are Statement-specific constraints.
        # A Version without Statements cannot satisfy those filters.
        if any(
            value is not None
            for value in (
                filters.facet,
                filters.derivation_kind,
                filters.temporal_scope_id,
            )
        ):
            return allowed

        version_ids = tuple(
            dict.fromkeys(
                str(row["version_id"])
                for row in rows
                if isinstance(row.get("version_id"), str) and row["version_id"]
            )
        )
        if not version_ids:
            return allowed

        marks = ",".join("?" for _ in version_ids)
        sql = f"""SELECT v.object_id,v.id AS version_id
                  FROM object_versions v
                  JOIN object_version_lifecycle l ON l.version_id=v.id
                  WHERE v.id IN ({marks}) AND l.state='accepted'
                    AND NOT EXISTS (
                      SELECT 1 FROM knowledge_statements s WHERE s.version_id=v.id
                    )"""
        allowed.update(
            (str(row["object_id"]), str(row["version_id"]))
            for row in self.db.execute(sql, version_ids)
        )
        return allowed
