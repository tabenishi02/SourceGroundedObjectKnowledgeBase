# P-GUI-06 — Dynamic Verification Attempt 02

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Amendment under verification: `P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`
- Execution platform: Windows / Python 3.10.6 / pytest 9.1.1
- Execution-source baseline: `d00635051a3ffdc11db3029cb94d502da4954061`
- Disposition: **PASS**

## 1. Purpose

Re-run the P-GUI-06 automated gate after the Search selector / Knowledge validity-range amendment changed production Search and GUI code after Attempt 01.

This attempt supersedes Attempt 01 as the current automated authority for P-GUI-06. Attempt 01 remains historical evidence for the pre-amendment implementation.

## 2. Focused regression

Executed:

```powershell
python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py `
  tests/test_p_gui_05_object_class_selector.py `
  tests/test_p_gui_05_object_class_controls.py `
  tests/test_p_gui_05_source_recursive_zip_import.py `
  tests/test_p_gui_06_search_registry_version.py `
  tests/test_p_gui_06_search_filter_selectors.py `
  tests/test_search_validity_range.py
```

Measured result:

```text
collected = 18
passed    = 18
failed    = 0
elapsed   = 8.38s
```

This includes both new amendment tests:

```text
tests/test_p_gui_06_search_filter_selectors.py
tests/test_search_validity_range.py
```

Focused disposition: **PASS**.

## 3. Ruff

Executed:

```powershell
python -m ruff check src tests
```

Measured result:

```text
All checks passed!
```

Ruff disposition: **PASS**.

## 4. Full regression

Executed:

```powershell
python -m pytest
```

Measured result:

```text
collected = 813
passed    = 813
failed    = 0
warnings  = 2
elapsed   = 268.35s (0:04:28)
```

The two warnings are the known local-Qdrant limitations:

1. payload indexes have no effect in local Qdrant except supported text-index behavior;
2. local mode performs exact brute-force search, so `search_params` has no effect except `idf`.

These warnings are unchanged environmental/runtime limitations and are not test failures.

Full-regression disposition: **PASS**.

## 5. Amendment coverage accepted by this run

The measured PASS covers the current P-GUI-06 implementation including:

- Registry-backed Primary / Additional / Ancestor Class selectors;
- Facet / Version / Temporal Scope selectors with historical editable fallback;
- Object-scoped Similarity Facet / Version selectors;
- bounded and one-sided `Knowledge valid From` / `Knowledge valid To` input;
- temporal-overlap range semantics for lexical and semantic Search paths;
- pre-cutover compatibility semantic filtering;
- rejection of invalid reversed ranges;
- timeless Statement eligibility;
- existing Search / Similarity / Registry / Version / Render regression surface.

## 6. Final automated verdict

```text
focused regression = 18 / 18 PASS
Ruff               = PASS
full pytest         = 813 / 813 PASS
warnings            = 2 known local-Qdrant warnings
```

Therefore:

```text
P-GUI-06 automated verification = PASS
```

The remaining P-GUI-06 gate is interactive GUI smoke acceptance.
