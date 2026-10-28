# P-GUI-06 — Search Filter Selector / Knowledge Validity Range Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Implemented / Automated Verification Refresh Pending / Interactive Smoke Pending**
- Baseline automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

## Request

Improve Search / Similarity input ergonomics so operators do not need to remember Registry keys or persistent IDs where the system can offer known choices.

Requested changes implemented in this amendment:

- Search Hard Filters `Primary Class`, `Additional Class`, `Ancestor Class`, `Facet`, `Version ID`, and `Temporal Scope ID` use selector controls.
- Similarity `Facet` and `Version` use selector controls scoped to the selected Object.
- `Knowledge valid at` is replaced in the GUI by `Knowledge valid From` and `Knowledge valid To`.
- The validity range supports both bounded and one-sided ranges.

The user message also contained an unfinished bullet beginning `Registryタブの`. No requirement was inferred from that incomplete fragment, so this amendment makes no Registry-page change from it.

## Selector sources

The GUI keeps the accepted application/operator boundary and does not query SQLite directly.

### Class selectors

Search loads Classes through:

```text
registry.class.list
```

The UI submits the stable Class `key`, matching the existing Search filter contract.

### Facet / Version / Temporal Scope selectors

The current public operator inventory has no standalone Facet-list, Version-list, or Temporal-Scope-list operation. Rather than adding GUI SQL or expanding the public operation count only for presentation lookup, the GUI composes existing read operations:

```text
object.list
    -> each Object current_version_id
    -> version.show(current accepted Version)
    -> Facet keys / Temporal Scope IDs / Version metadata
```

Consequences:

- automatically listed Version candidates are current accepted Versions known from `object.list`;
- automatically listed Facets and Temporal Scopes come from loaded current accepted Knowledge;
- Facet / Version / Temporal Scope combo boxes remain editable so an operator may enter a known historical accepted Version ID, historical Facet key, or historical Temporal Scope ID that is not in the automatically loaded current set;
- Similarity Facet / Version options are narrowed to the selected Object.

This preserves the existing 67-operation boundary and keeps lookup composition above Repository storage.

## Knowledge validity range

The historical Search contract exposes one `valid_at` string. Existing single-date callers remain valid.

For GUI range requests, `valid_at` now also accepts the following backward-compatible encoded forms:

```text
YYYY-MM-DD..YYYY-MM-DD   bounded range
YYYY-MM-DD..             open-ended From
..YYYY-MM-DD             open-ended To
```

Plain historical values without `..` keep the original point-in-time semantics.

Range semantics are temporal overlap:

```text
Knowledge interval overlaps requested [From, To]
```

For interval temporal scopes this means:

```text
knowledge.valid_to   >= requested From   (when From exists)
knowledge.valid_from <= requested To     (when To exists)
```

`as_of` scopes are treated as point intervals. Statements without a Temporal Scope remain eligible, preserving the previous `valid_at` behavior for timeless Knowledge.

The GUI rejects an invalid ISO date and rejects `From > To` before submitting Search.

## Retrieval integration

Added:

```text
src/sgokb/retrieval/search_range.py
```

`sgokb.retrieval.HybridObjectSearch` now routes through the range-aware R2 adapter. The adapter delegates unchanged for ordinary point-in-time requests and adds range handling only when `knowledge_valid_at` contains the range separator.

Both lexical SQL filtering and semantic Vector filtering use the same overlap intent. Generation-aware R2 filtering remains in force.

## GUI implementation

Updated:

```text
src/sgokb/gui/views/search_page.py
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
```

Similarity now uses Object-scoped dropdowns for the existing `Facet` and `Version` inputs. The Similarity operation itself is not expanded with new Class or Temporal-Scope semantics; its existing contract remains Object / Facet / source Version / cross-Class / archived scope.

## Regression coverage

Added:

```text
tests/test_p_gui_06_search_filter_selectors.py
tests/test_search_validity_range.py
```

Coverage includes:

- Registry Class candidates in all three Class selectors;
- Facet / current Version / Temporal Scope candidates discovered from accepted Knowledge;
- Object-scoped Similarity Facet / Version candidates;
- GUI construction of a bounded `From..To` request;
- invalid reversed range blocked before submit;
- bounded, open-From, and open-To temporal-overlap retrieval semantics;
- timeless Statement eligibility under range filtering.

## Verification state

The previous P-GUI-06 automated PASS was measured before this amendment:

```text
focused regression = 16 / 16 PASS
Ruff               = PASS
full pytest         = 811 / 811 PASS
```

That result remains historical evidence for the pre-amendment baseline, but does not certify the selector/range code added here.

Current disposition:

```text
implementation                = Complete
desk audit                    = Complete
automated verification refresh = Pending
interactive smoke             = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
