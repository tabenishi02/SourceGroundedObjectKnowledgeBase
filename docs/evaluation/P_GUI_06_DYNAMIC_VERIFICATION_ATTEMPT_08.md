# P-GUI-06 — Dynamic Verification Attempt 08

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Scope: post-From/To-removal automated verification refresh
- Result: **PASS**
- Current role: **Current automated verification authority**

## 1. Verification context

Attempt 08 verifies the reduced P-GUI-06 surface after the operator-directed removal of the experimental GUI From/To date-range filter.

The verified source state was pulled from `main` through:

```text
git pull --ff-only
Updating 89f2e7b..ac1a425
Fast-forward
```

The update included removal of the range-aware retrieval adapters and range-specific test modules while preserving the semantic-runtime crash remediation.

## 2. Focused GUI / P-GUI-06 gate

Executed:

```text
python -m pytest \
  tests/test_p_gui_03r_operator_boundary.py \
  tests/test_p_gui_04_optional_boundary.py \
  tests/test_p_gui_04_shell.py \
  tests/test_p_gui_05_domain_pages.py \
  tests/test_p_gui_05_object_class_selector.py \
  tests/test_p_gui_05_object_class_controls.py \
  tests/test_p_gui_05_source_recursive_zip_import.py \
  tests/test_p_gui_06_search_registry_version.py \
  tests/test_p_gui_06_search_filter_selectors.py \
  tests/test_p_gui_06_derivation_kind_selector.py \
  tests/test_p_gui_06_search_runtime_state.py \
  tests/test_p_gui_06_runtime_dependency.py
```

Measured result:

```text
collected 28 items
28 passed in 4.69s
```

Verdict:

```text
Focused P-GUI-06 regression = PASS
```

## 3. Static verification

Executed:

```text
python -m ruff check src tests
```

Measured result:

```text
All checks passed!
```

Verdict:

```text
Ruff = PASS
```

## 4. Full regression

Executed:

```text
python -m pytest
```

Measured result:

```text
collected 817 items
817 passed, 2 warnings in 203.62s (0:03:23)
```

The two warnings are the already-known local-Qdrant limitations:

1. local Qdrant payload indexes have no effect;
2. local mode performs exact brute-force search so `search_params` has no effect except `idf`.

Neither warning is a test failure or a new P-GUI-06 regression.

Verdict:

```text
Full regression = PASS
```

## 5. Verified post-removal surface

This run directly covers the amended Search implementation after From/To removal, including:

```text
GUI/operator boundary
GUI shell / semantic-native preload regression
P-GUI-05 domain regression
Search / Registry / Version GUI
Search selector behavior after From/To retirement
Derivation Kind selector
Search runtime-state reset
Semantic runtime dependency normalization
```

The removed range-only adapters and tests are intentionally absent from the current inventory.

## 6. Formal automated disposition

```text
focused regression = 28 / 28 PASS
Ruff               = PASS
full regression    = 817 / 817 PASS
warnings           = 2 known local-Qdrant warnings
```

Therefore:

```text
P-GUI-06 automated verification after From/To removal = PASS
```

This supersedes Attempt 07 as the current automated closure authority. Attempt 07 remains historical evidence for the pre-removal surface.

## 7. Remaining gate

Automated verification is complete. P-GUI-06 remains open only for interactive smoke covering the current reduced GUI surface:

```text
Search
  - From/To controls absent
  - remaining hard filters usable
  - Lexical Search usable
  - Semantic runtime ON remains crash-free
  - explicit degradation / failure display

Similarity
  - Object / Facet / Version selection
  - overall / facet-specific similarity

Registry / Version / Render
  - browse/detail
  - Proposal Accept/Reject separate from Apply
  - Version Show/Diff
  - Render preview/export
```

Current task status:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```
