# P-GUI-06 — Dynamic Verification Attempt 04

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Scope: Derivation Kind selector + Knowledge validity range false-negative remediation after Attempt 03 fixture/lint cleanup
- Verdict: **PASS / AUTOMATED VERIFICATION COMPLETE / INTERACTIVE SMOKE PENDING**

## Operator execution

The operator pulled through commit `9a33f33300560977088d91f64bd3e167e718cd83` and executed the requested focused pytest set, Ruff, and full regression on Windows using Python 3.10.6 / pytest 9.1.1.

## Focused verification

Measured result:

```text
collected 24 items
24 passed in 4.26s
```

The focused set includes:

```text
tests/test_p_gui_04_optional_boundary.py
tests/test_p_gui_04_shell.py
tests/test_p_gui_05_domain_pages.py
tests/test_p_gui_05_object_class_selector.py
tests/test_p_gui_05_object_class_controls.py
tests/test_p_gui_05_source_recursive_zip_import.py
tests/test_p_gui_06_search_registry_version.py
tests/test_p_gui_06_search_filter_selectors.py
tests/test_p_gui_06_derivation_kind_selector.py
tests/test_search_validity_range.py
```

This directly certifies:

- fixed-value Derivation Kind selector behavior;
- Search selector population and argument construction;
- bounded and one-sided Knowledge validity ranges;
- the stale-active-generation false-negative remediation;
- the GUI end-to-end path for range Search;
- preservation of active-generation isolation for derived Knowledge channels.

## Static verification

Measured Ruff result:

```text
All checks passed!
```

The Attempt 03 E402 / I001 defects are therefore closed.

## Full regression

Measured result:

```text
collected 819 items
819 passed, 2 warnings in 228.62s (0:03:48)
```

The two warnings are the known local-Qdrant limitations:

1. local Qdrant payload indexes do not affect local-mode filtering except supported text-index behavior;
2. local mode performs exact brute-force search, so `search_params` does not affect ordinary ANN behavior except `idf`.

These are existing warnings and are not test failures.

## Attempt history

```text
Attempt 01 = PASS, pre-selector/range implementation
Attempt 02 = PASS, selector/range baseline
Attempt 03 = FAIL, test fixture transaction + Ruff defects; product assertion not reached
Attempt 04 = PASS, post-remediation current authority
```

Attempt 03 remains historical failure evidence and is not overwritten.

## Current disposition

```text
implementation                  = Complete
desk audit                      = Complete
operation wiring                = 14 / 14
Derivation Kind selector        = PASS
validity-range remediation      = PASS
focused regression              = 24 / 24 PASS
Ruff                            = PASS
full regression                 = 819 / 819 PASS
known local-Qdrant warnings     = 2
interactive smoke               = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

P-GUI-06 becomes `Complete / Accepted` only after interactive GUI smoke acceptance is measured PASS.
