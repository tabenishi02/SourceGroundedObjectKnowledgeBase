# P-GUI-06 — Knowledge Validity Range False-Negative Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Remediation Verified / Automated Verification PASS / Interactive Smoke Pending**
- Current automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

## Observed symptom

In the Search tab, setting `Knowledge valid From` and/or `Knowledge valid To` could produce zero results for an Object that was found without the range filter. The operation still completed with `success`, and changing the range values did not restore the expected Object.

## Root cause

The range-aware R2 Search adapter used the active derived Search generation not only for Knowledge lexical/semantic channels, but also to re-qualify Registry identity candidates when a validity range was present.

The problematic sequence was:

```text
Object current accepted Version advances from V1 to V2
        ↓
active Search generation still contains V1 memberships
        ↓
Search by Object name without From/To
        -> Registry identity can return current V2
        ↓
add From/To
        -> range-specific Registry eligibility joins active generation memberships
        -> active generation contains V1, while Object current_version_id is V2
        -> no qualifying pair
        -> Object disappears even when V2 has timeless/range-valid Knowledge
```

The false negative therefore depended on the presence of the range filter, not on the actual From/To values. This matches the observed behavior.

## Intended boundary

Registry name / alias identity is canonical data. It must not disappear merely because a derived Search generation temporarily lags a newly accepted current Version.

At the same time, R2 generation isolation for derived Knowledge channels must remain intact:

```text
Registry identity eligibility under From/To
    -> canonical accepted Knowledge

Knowledge lexical / semantic matches
    -> active Search generation only
```

This keeps exact/registry identity discoverable without silently injecting unlinked Knowledge representations into the active generation.

## Remediation

Updated:

```text
src/sgokb/retrieval/search_range.py
```

Range-specific Registry eligibility now:

1. starts from the normal canonical Registry candidate rows;
2. resolves their current/pinned accepted Version IDs;
3. evaluates Facet / Derivation Kind / Temporal Scope / From-To overlap against canonical `knowledge_statements` and `temporal_scopes`;
4. does **not** require `knowledge_search_generation_memberships` for Registry identity eligibility.

The temporal overlap expression was also centralized so canonical SQL range checks and generation-scoped lexical SQL use the same From/To semantics.

Knowledge lexical and semantic retrieval remain active-generation scoped. No cloud fallback, silent generation bypass, or direct GUI SQL path was introduced.

## Regression coverage

Updated:

```text
tests/test_search_validity_range.py
tests/test_p_gui_06_search_filter_selectors.py
```

The regression creates the exact lag condition:

```text
accept V1
activate R2 generation containing V1
commit generation setup
accept V2 as current after generation activation
search with From/To
```

The explicit transaction boundary is required because Version lifecycle operations reject an already-active outer transaction.

The core regression verifies multiple unrelated ranges, including bounded and one-sided values. Because the V2 Statement is timeless, the Object identity remains eligible for every requested range.

The GUI regression runs the real path:

```text
SearchPage
  -> BackendCoordinator
  -> OperatorSession(search)
  -> RangeAwareHybridObjectSearch
```

and verifies that the current V2 Object is returned with `search: success` despite the active generation still pointing at V1.

A companion assertion preserves R2 isolation: searching for V2-only Knowledge text does not make that text available through the older active generation.

## Verification history

Attempt 03 exposed two verification-harness defects before the product assertions ran:

```text
focused = 19 passed / 5 failed
Ruff    = 7 errors
```

Those failures were caused by missing fixture transaction boundaries and static import-order issues, not by the product range assertion. They were remediated and preserved as historical evidence in `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_03.md`.

Attempt 04 then measured the current implementation:

```text
focused regression = 24 / 24 PASS
Ruff               = All checks passed!
full pytest         = 819 / 819 PASS
known warnings      = 2 local-Qdrant warnings
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

## Current disposition

```text
root cause                 = Confirmed
remediation                = Implemented
core regression            = PASS
GUI end-to-end regression  = PASS
automated verification     = PASS
interactive smoke          = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```
