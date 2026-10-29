# P-GUI-06 — Dynamic Verification Attempt 05

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Scope: statement-less range identity remediation + GUI runtime-state remediation + real Qdrant R2 range-semantic coverage
- Verdict: **PASS / CURRENT AUTOMATED AUTHORITY / INTERACTIVE SMOKE PENDING**

## Operator execution

The operator pulled through commit `3ac868cb353bb7aa727ee19bbde1d20f5292666f` and ran the requested focused pytest set, Ruff, and full pytest regression on Windows with Python 3.10.6 / pytest 9.1.1.

Measured focused result:

```text
collected 31 items
31 passed, 2 warnings
```

Ruff:

```text
All checks passed!
```

Full regression:

```text
collected 826 items
826 passed, 2 warnings
```

The two warnings are the existing local-Qdrant limitations:

1. local Qdrant payload indexes have no effect except supported text indexes;
2. local mode performs exact brute-force search, so `search_params` has no effect except `idf`.

They are warnings, not test failures.

## Remediation coverage proven by this attempt

The focused gate includes the new regressions added after interactive reproduction:

```text
tests/test_search_validity_range_identity.py       5 PASS
tests/test_p_gui_06_search_runtime_state.py         1 PASS
tests/test_search_validity_range_qdrant_r2.py      1 PASS
```

The passing coverage proves:

- From/To alone does not remove Registry Object identity for an accepted Version with zero Knowledge Statements;
- Statement-specific Facet filtering still rejects a Statement-less Version;
- Search GUI clears prior results/degradation state before a new request and presents the current failure state instead of stale presentation;
- an actual in-memory Qdrant backend, routed through an R2 generation cutover, executes a From/To semantic Statement query successfully;
- prior range overlap, stale-generation, selector, and Derivation Kind regressions remain passing.

## Historical context

Attempt 04 was the previous automated authority:

```text
focused = 24 / 24 PASS
Ruff    = PASS
full    = 819 / 819 PASS
```

Interactive testing after Attempt 04 exposed a second range false-negative condition and a stale GUI runtime-state display. Those issues triggered the remediation now verified by Attempt 05.

Attempt 03 remains historical failure evidence for test-fixture / Ruff defects and is not overwritten.

## Current disposition

```text
implementation                         = Complete
desk audit                             = Complete
operation wiring                       = 14 / 14
statement-less range identity fix      = PASS
GUI runtime-state reset/failure display= PASS
real Qdrant R2 range-semantic path     = PASS
focused automated regression           = 31 / 31 PASS
Ruff                                    = PASS
full regression                         = 826 / 826 PASS
interactive smoke                       = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

Attempt 05 is the current automated authority. P-GUI-06 becomes `Complete / Accepted` only after interactive smoke confirms the repaired Search behavior and the remaining Search / Similarity / Registry / Version / Render surface.
