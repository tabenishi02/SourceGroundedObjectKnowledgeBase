# P-GUI-06 — Range Identity / Runtime-State Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Remediation Implemented / Automated Verification Refresh Pending / Interactive Smoke Pending**
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

The lexical failure proves the From/To false negative is independent of Qdrant or the semantic runtime.

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

The canonical `HybridObjectSearch` export now layers this completion over the existing range-aware R2 implementation.

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

Every submitted Search now clears the previous result model, detail pane, and runtime-state display before the new result is accepted. The runtime label shows the current running mode.

If the Search operation fails before a Search response is produced, the Search runtime-state area now displays the current normalized failure instead of retaining the previous Search/degradation text.

This is particularly important for semantic-runtime startup/Qdrant failures, where the prior GUI could leave an old `semantic:RuntimeError` or old results visible while only the generic operation-status label changed.

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

## Verification state

The previous measured result was:

```text
focused regression = 24 / 24 PASS
Ruff               = PASS
full regression    = 819 / 819 PASS
known warnings     = 2 local-Qdrant warnings
```

That result predates this remediation and is historical evidence only.

Current disposition:

```text
interactive reproduction evidence = Accepted
second range false-negative cause  = Identified
product remediation                = Implemented
GUI stale-state remediation        = Implemented
Qdrant range-semantic coverage     = Added
automated verification refresh     = Pending
interactive smoke                  = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
