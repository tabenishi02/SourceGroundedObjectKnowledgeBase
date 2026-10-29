# P-GUI-06 — Range Identity / Runtime-State Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Remediation Verified / Automated Verification PASS / Interactive Smoke Pending**
- Current automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md`
- Previous automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

## Operator observations

Interactive testing reported:

```text
lexical, no From/To       -> results returned, no degradation
lexical, From/To          -> zero results, no degradation
hybrid, semantic OFF      -> results without range; semantic:RuntimeError degradation
hybrid, semantic OFF+range-> zero results; semantic:RuntimeError degradation
hybrid, semantic ON       -> previous Search presentation appeared to remain visible
```

The lexical failure proved the From/To false negative was independent of Qdrant or the semantic runtime.

## Root-cause refinement

The earlier stale-generation remediation correctly stopped Registry identity from depending on an out-of-date active derived generation. A second false-negative condition remained:

```text
range specified
  -> Registry identity candidate is re-qualified against canonical knowledge_statements
  -> accepted current Version has zero knowledge_statements
  -> no qualifying Statement pair exists
  -> Object name/alias identity disappears for every From/To value
```

A Version with no Statement-level temporal data has no Statement temporal restriction. From/To alone therefore must not make its canonical Object identity disappear.

Statement-specific filters remain strict. If `Facet`, `Derivation kind`, or `Temporal Scope` is also supplied, a Version with zero Statements cannot satisfy that filter and remains excluded.

## Product remediation

Added:

```text
src/sgokb/retrieval/search_range_identity.py
```

The canonical `HybridObjectSearch` export layers this completion over the existing range-aware R2 implementation.

Behavior:

```text
From/To only + accepted Version has matching/timeless Statement
    -> normal canonical Statement range eligibility

From/To only + accepted Version has zero Statements
    -> Version treated as having no Statement-level temporal restriction
    -> Registry name/alias identity remains eligible

From/To + Facet/Derivation/Temporal Scope + zero Statements
    -> not eligible
```

Knowledge lexical/semantic channels remain subject to their existing Statement and active-generation contracts.

## GUI stale-state remediation

Updated:

```text
src/sgokb/gui/views/search_page_derivation.py
```

Every submitted Search clears the previous result model, detail pane, and runtime-state display before the new result is accepted. The runtime label shows the current running mode.

If the Search operation fails before a Search response is produced, the Search runtime-state area displays the current normalized failure instead of retaining the previous Search/degradation text.

This is particularly important for semantic-runtime startup/Qdrant failures, where the prior GUI could leave old degradation text or old results visible while only the generic operation-status label changed.

## Regression additions

Added:

```text
tests/test_search_validity_range_identity.py
tests/test_p_gui_06_search_runtime_state.py
tests/test_search_validity_range_qdrant_r2.py
```

Coverage adds:

1. four bounded/one-sided From/To values over an accepted Version with zero Statements;
2. confirmation that Statement-specific Facet filtering still rejects a Statement-less Version;
3. Search GUI clearing of previous results/runtime state and current failure presentation;
4. real in-memory Qdrant + R2 generation cutover + semantic Statement range search.

The Qdrant test closes a previous verification gap: earlier range-semantic coverage used a fake Vector Index, while Qdrant R2 tests covered generation lifecycle but did not execute a From/To semantic query.

## Automated verification

Attempt 05 was executed on Windows with Python 3.10.6 / pytest 9.1.1 after this remediation.

Measured result:

```text
focused regression = 31 / 31 PASS
Ruff               = All checks passed!
full regression    = 826 / 826 PASS
known warnings     = 2 local-Qdrant warnings
```

Focused coverage includes:

```text
test_search_validity_range_identity.py   = 5 PASS
test_p_gui_06_search_runtime_state.py     = 1 PASS
test_search_validity_range_qdrant_r2.py  = 1 PASS
```

The Qdrant range-semantic regression passed with the real in-memory Qdrant adapter and R2 generation routing. The two warnings are the existing local-Qdrant payload-index and brute-force-search limitations and are not failures.

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md`

## Current disposition

```text
interactive reproduction evidence = Accepted
second range false-negative cause  = Confirmed
product remediation                = PASS
GUI stale-state remediation        = PASS
Qdrant range-semantic coverage     = PASS
automated verification             = PASS
interactive smoke                  = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```
