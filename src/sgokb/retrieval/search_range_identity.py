"""Registry-identity boundary for range-aware Object Search.

Knowledge validity is a Statement-scoped hard filter. Registry lexical identity
(Object name / alias) is canonical identity discovery and must remain available
independently of Statement temporal eligibility. Knowledge lexical/semantic
channels continue to apply the range to Statement representations.
"""

from __future__ import annotations

from sgokb.domain import ObjectSearchFilters

from .search_range import RangeAwareHybridObjectSearch as _BaseRangeAwareHybridObjectSearch


class RangeAwareHybridObjectSearch(_BaseRangeAwareHybridObjectSearch):
    """Keep canonical Registry identity independent of From/To-only filtering."""

    def _canonical_range_pairs(
        self,
        rows: list[dict],
        filters: ObjectSearchFilters,
        validity: tuple[str | None, str | None],
    ) -> set[tuple[str, str]]:
        # Facet / Derivation / Temporal Scope are Statement-specific constraints.
        # When any of them is requested, Registry identity may only represent an
        # Object/Version that has a matching canonical Statement under the range.
        if any(
            value is not None
            for value in (
                filters.facet,
                filters.derivation_kind,
                filters.temporal_scope_id,
            )
        ):
            return super()._canonical_range_pairs(rows, filters, validity)

        # knowledge_valid_at / GUI From-To alone constrains Statement channels,
        # not canonical Object identity. This follows the frozen R2 Search contract:
        # Registry name/alias discovery is possible even without Knowledge.
        return {
            (str(row["object_id"]), str(row["version_id"]))
            for row in rows
            if isinstance(row.get("version_id"), str) and row["version_id"]
        }
