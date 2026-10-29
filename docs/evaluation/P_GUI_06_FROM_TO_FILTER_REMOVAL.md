# P-GUI-06 — From/To Date Filter Removal

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Decision: **Remove the experimental GUI From/To date filter**
- Status: **Implemented / Automated Verification Refresh Pending / Interactive Smoke Pending**

## Operator decision

Interactive verification established that the From/To control could be made operational without hiding Registry identity, but its effective semantics were not trustworthy for operator use: ranges that should have excluded Knowledge could still leave a visible Object result because Registry identity discovery and Statement temporal eligibility are intentionally different search channels.

Rather than continue adding special cases to an ambiguous control, the operator requested that the GUI From/To date-filtering feature be removed.

## Final scope

Removed from P-GUI-06:

```text
Search GUI
  - Knowledge valid From
  - Knowledge valid To
  - GUI construction of valid_at="FROM..TO"

Retrieval extension
  - RangeAwareHybridObjectSearch
  - range identity adapter
  - ".." range interpretation added specifically for P-GUI-06

Verification
  - range-specific lexical tests
  - range-specific identity tests
  - range-specific Qdrant/R2 tests
```

Preserved:

```text
existing CLI / operator single-point valid_at contract
Temporal Scope ID filter
Facet / Version / Class / Derivation Kind filters
Semantic runtime remediation and GUI main-thread native preload
R2 generation-scoped HybridObjectSearch
```

The removal is deliberately limited to the P-GUI-06 From/To range extension. It does not remove canonical temporal-scope data or the pre-existing single-point `knowledge_valid_at` capability used by non-GUI callers.

## Implementation

### GUI

The exported P-GUI-06 `SearchPage` no longer presents usable From/To controls. The compatibility widgets inherited from the original base page are hidden, cleared, disabled, and ignored by the amended `run_search()` implementation.

GUI Search requests therefore never emit the experimental range form:

```text
valid_at = "YYYY-MM-DD..YYYY-MM-DD"
```

### Retrieval

`sgokb.retrieval.HybridObjectSearch` now resolves directly to the canonical R2 implementation in:

```text
src/sgokb/retrieval/hybrid_search_r2.py
```

The P-GUI-06 range adapters were removed:

```text
src/sgokb/retrieval/search_range.py
src/sgokb/retrieval/search_range_identity.py
```

### Tests

Range-only tests were removed. Current GUI selector coverage asserts that the retired controls are inert and that no `valid_at` argument is emitted even if a value is assigned programmatically to the compatibility widgets.

Semantic runtime dependency coverage remains in:

```text
tests/test_p_gui_06_runtime_dependency.py
```

The GUI main-thread native preload regression remains in `tests/test_p_gui_04_shell.py`.

## Historical evidence

The following documents remain historical records of the experimental range work and its interactive failures; they are not current behavior authority:

- `P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`
- `P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`
- `P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md`
- `P_GUI_06_RANGE_CONTRACT_SEMANTIC_RUNTIME_DEPENDENCY_REMEDIATION.md`
- `P_GUI_06_INTERACTIVE_ATTEMPT_07_FAILURE_AND_REMEDIATION.md`

Attempt 07 automated PASS also predates this removal and is historical until the reduced surface is re-verified.

## Current disposition

```text
From/To GUI controls              = Removed from operator surface
GUI range argument construction   = Removed
range retrieval adapters          = Removed
range-specific tests              = Removed
single-point valid_at contract     = Preserved
semantic runtime crash remediation= Preserved
automated verification refresh    = Pending
interactive smoke                 = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
