# P-GUI-06 — Dynamic Verification Attempt 03

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Scope: Derivation Kind selector + Knowledge validity range false-negative remediation
- Verdict: **FAIL / TEST FIXTURE + STATIC-LINT DEFECTS CONFIRMED / REMEDIATION APPLIED / RE-VERIFICATION PENDING**

## Operator execution

The operator pulled through commit `c6b24198562e88030bbb15e4501f046100bb7986` and ran the requested focused pytest set plus Ruff.

Measured focused result:

```text
collected 24 items
19 passed
5 failed
```

All five failures occurred while constructing the stale-generation regression fixture, before the product range assertions ran:

```text
RuntimeError: Version lifecycle operation requires an outer-transaction boundary
```

The failing sequence was:

```text
accept V1
_activate_r2_generation(...)
    -> direct SQL leaves Repository transaction active
begin V2 candidate
    -> VersionRepository._require_idle_transaction()
    -> RuntimeError
```

Therefore Attempt 03 does **not** demonstrate a product-code failure in the validity-range remediation. The regression fixture violated the Version lifecycle transaction boundary.

## Fixture remediation

Updated:

```text
tests/test_search_validity_range.py
tests/test_p_gui_06_search_filter_selectors.py
```

Both stale-generation fixtures now explicitly commit immediately after `_activate_r2_generation(...)` and before beginning the V2 lifecycle. This preserves the intended scenario while respecting the repository transaction contract.

## Ruff result

Measured Ruff result:

```text
Found 7 errors
```

Six errors were `E402` in `src/sgokb/gui/views/__init__.py`. The Derivation Kind amendment intentionally patches the base `search_page.SearchPage` symbol before importing `MainWindow`, because `MainWindow` imports that module symbol while it is defined. Those late imports are now documented and marked with targeted `# noqa: E402` annotations.

One error was `I001` in `tests/test_search_validity_range.py`, caused by the sibling-test fixture import block. The file now explicitly documents that fixture-import ordering with a targeted file-level `I001` exemption rather than altering runtime behavior.

## Product remediation status

The product change in:

```text
src/sgokb/retrieval/search_range.py
```

remains unchanged by this Attempt 03 cleanup. The intended root-cause remediation is still:

```text
Registry name/alias identity range eligibility
    -> canonical accepted Knowledge

Knowledge lexical / semantic channels
    -> active R2 Search generation
```

This prevents current canonical Objects from disappearing solely because the active derived generation lags the latest accepted Version, while preserving generation isolation for derived Knowledge channels.

## Current disposition

```text
validity-range root cause       = Confirmed
product remediation             = Implemented
Attempt 03 focused pytest       = FAIL before product assertion
Attempt 03 Ruff                 = FAIL
fixture transaction defect      = Remediated
Ruff E402 / I001 defects        = Remediated
re-verification                 = Pending
interactive smoke               = Pending
```

Therefore the current task state remains:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```

Attempt 03 is historical failure evidence and must not be overwritten by a later PASS attempt.
