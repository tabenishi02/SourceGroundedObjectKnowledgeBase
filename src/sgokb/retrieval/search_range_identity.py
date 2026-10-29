"""Registry-identity boundary for range-aware Object Search.

Knowledge validity is a Statement-scoped hard filter. Registry lexical identity
(Object name / alias) is canonical identity discovery and must remain available
independently of Statement temporal eligibility. Knowledge lexical/semantic
channels continue to apply the range to Statement representations.
"""

from __future__ import annotations

from sgokb.domain import ObjectSearchFilters

from .search_range import RangeAwareHybridObjectSearch as _BaseRangeAwareHybridObjectSearch
from .search_range import _validity_range


class RangeAwareHybridObjectSearch(_BaseRangeAwareHybridObjectSearch):
    """Keep canonical Registry identity independent of From/To-only filtering."""

    @staticmethod
    def _has_statement_specific_filter(filters: ObjectSearchFilters) -> bool:
        return any(
            value is not None
            for value in (
                filters.facet,
                filters.derivation_kind,
                filters.temporal_scope_id,
            )
        )

    def _registry_rows(self, filters: ObjectSearchFilters) -> list[dict]:
        validity = _validity_range(filters.knowledge_valid_at)
        if validity is not None and not self._has_statement_specific_filter(filters):
            # From/To alone is a Statement-channel constraint. Do not re-qualify
            # canonical Object name/alias rows against Version or Statement state at
            # all. This intentionally preserves identity even for Objects that have
            # no current accepted Version yet.
            return super()._registry_rows(self._without_range(filters))
        return super()._registry_rows(filters)

    def _canonical_range_pairs(
        self,
        rows: list[dict],
        filters: ObjectSearchFilters,
        validity: tuple[str | None, str | None],
    ) -> set[tuple[str, str]]:
        # This hook is now reached only when a Statement-specific narrowing filter
        # accompanies the range. In that case a matching canonical Statement is
        # required, as defined by the existing range implementation.
        return super()._canonical_range_pairs(rows, filters, validity)
