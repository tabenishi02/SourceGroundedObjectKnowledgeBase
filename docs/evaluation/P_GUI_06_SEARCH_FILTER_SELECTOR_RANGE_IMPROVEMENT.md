# P-GUI-06 — Search Filter Selector / Knowledge Validity Range Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Implemented / Automated Verification PASS / Interactive Smoke Pending**
- Current automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`
- Historical authorities: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`, `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_02.md`, `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_03.md`

## Request

Improve Search / Similarity input ergonomics so operators do not need to remember Registry keys or persistent IDs where the system can offer known choices.

Implemented changes:

- Search Hard Filters `Primary Class`, `Additional Class`, `Ancestor Class`, `Facet`, `Version ID`, and `Temporal Scope ID` use selector controls.
- Similarity `Facet` and `Version` use selector controls scoped to the selected Object.
- `Knowledge valid at` is replaced in the GUI by `Knowledge valid From` and `Knowledge valid To`.
- The validity range supports bounded and one-sided ranges.
- `Derivation kind` uses a fixed-value non-editable selector through the follow-up amendment.

The user message also contained an unfinished bullet beginning `Registryタブの`. No requirement was inferred from that incomplete fragment, so no Registry-page change was made from it.

## Selector sources

The GUI keeps the accepted application/operator boundary and does not query SQLite directly.

### Class selectors

Search loads Classes through:

```text
registry.class.list
```

The UI submits the stable Class `key`, matching the existing Search filter contract.

### Facet / Version / Temporal Scope selectors

The public operator inventory has no standalone Facet-list, Version-list, or Temporal-Scope-list operation. Rather than adding GUI SQL, the GUI composes existing reads:

```text
object.list
    -> each Object current_version_id
    -> version.show(current accepted Version)
    -> Facet keys / Temporal Scope IDs / Version metadata
```

Consequences:

- automatically listed Version candidates are current accepted Versions known from `object.list`;
- automatically listed Facets and Temporal Scopes come from loaded current accepted Knowledge;
- Facet / Version / Temporal Scope combo boxes remain editable so a known historical value may be entered;
- Similarity Facet / Version options are narrowed to the selected Object.

This preserves the existing public operation boundary and keeps lookup composition above Repository storage.

## Knowledge validity range

The historical Search contract exposes one `valid_at` string. Existing single-date callers remain valid.

For GUI range requests, `valid_at` also accepts:

```text
YYYY-MM-DD..YYYY-MM-DD   bounded range
YYYY-MM-DD..             open-ended From
..YYYY-MM-DD             open-ended To
```

Plain values without `..` retain historical point-in-time semantics.

Range semantics are temporal overlap:

```text
Knowledge interval overlaps requested [From, To]
```

For interval temporal scopes:

```text
knowledge.valid_to   >= requested From   (when From exists)
knowledge.valid_from <= requested To     (when To exists)
```

`as_of` scopes are treated as point intervals. Statements without a Temporal Scope remain eligible, preserving previous behavior for timeless Knowledge.

The GUI rejects invalid ISO dates and rejects `From > To` before submitting Search.

## Retrieval integration

Added:

```text
src/sgokb/retrieval/search_range.py
```

`sgokb.retrieval.HybridObjectSearch` routes through the range-aware R2 adapter. The adapter delegates unchanged for ordinary point-in-time requests and adds range handling only when `knowledge_valid_at` contains the range separator.

A later false-negative remediation corrected Registry identity eligibility when the active derived R2 generation lags a newer accepted current Version:

```text
Registry identity range eligibility
    -> canonical accepted Knowledge

Knowledge lexical / semantic channels
    -> active R2 generation
```

This preserves canonical Object discoverability without bypassing generation isolation for derived Knowledge channels. See `P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`.

## GUI implementation

Updated:

```text
src/sgokb/gui/views/search_page.py
src/sgokb/gui/views/search_page_derivation.py
```

Search Hard Filters now use:

```text
Primary Class       non-editable Registry dropdown
Additional Class    non-editable Registry dropdown
Ancestor Class      non-editable Registry dropdown
Facet               dropdown + editable historical fallback
Version ID          dropdown + editable historical fallback
Temporal Scope ID   dropdown + editable historical fallback
Knowledge valid     From / To date fields
Derivation kind     non-editable fixed-value dropdown
```

Similarity uses Object-scoped dropdowns for the existing `Facet` and `Version` inputs. The Similarity operation itself is not expanded with new Class or Temporal-Scope semantics; its existing contract remains Object / Facet / source Version / cross-Class / archived scope.

## Regression coverage

Coverage includes:

```text
tests/test_p_gui_06_search_filter_selectors.py
tests/test_p_gui_06_derivation_kind_selector.py
tests/test_search_validity_range.py
```

It verifies:

- Registry Class candidates in all three Class selectors;
- Facet / current Version / Temporal Scope candidates discovered from accepted Knowledge;
- Object-scoped Similarity Facet / Version candidates;
- fixed Derivation Kind candidates and submission behavior;
- GUI construction of a bounded `From..To` request;
- invalid reversed range blocked before submit;
- lexical and semantic temporal-overlap retrieval;
- bounded, open-From, and open-To range semantics;
- timeless Statement eligibility;
- stale-active-generation false-negative remediation;
- GUI end-to-end Search through BackendCoordinator / OperatorSession;
- preservation of active-generation isolation for derived Knowledge channels.

## Automated verification

Current post-remediation result from Attempt 04:

```text
focused regression = 24 / 24 PASS
Ruff               = All checks passed!
full pytest         = 819 / 819 PASS
known warnings      = 2 local-Qdrant warnings
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

The two warnings are the existing local-Qdrant limitations and are not failures.

## Current disposition

```text
implementation         = Complete
desk audit             = Complete
automated verification = PASS
interactive smoke      = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```
