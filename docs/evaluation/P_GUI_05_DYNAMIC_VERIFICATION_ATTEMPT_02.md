# P-GUI-05 — Dynamic Verification Attempt 02

Updated: 2026-10-29

- Task: `P-GUI-05 — Object / Source / Evidence / Association GUI`
- Result: **Automated Verification PASS / Interactive Smoke Pending**
- Baseline: `main` after the P-GUI-05 remediation and exact Ruff import-order fixes

## 1. Focused GUI regression

Command:

```powershell
python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py
```

Result:

```text
9 passed
```

This confirms the P-GUI-04 shell/optional-boundary regression plus P-GUI-05 Object / Source / Evidence / Association acceptance coverage.

## 2. Ruff

Command:

```powershell
python -m ruff check src tests
```

Result:

```text
All checks passed!
```

The three remaining I001 findings from the prior attempt were resolved by applying Ruff's exact import ordering (`QTableView` before `QTabWidget`) in the Evidence, Object, and Source pages.

## 3. Full regression

Command:

```powershell
python -m pytest
```

Result:

```text
804 passed, 2 warnings
```

The two warnings are the previously known local-Qdrant warnings:

1. local Qdrant payload indexes have no effect except supported text-index cases;
2. local Qdrant performs exact/brute-force search, so `search_params` has no effect except `idf`.

No test failures or errors remain.

## 4. Remediation verification

The Attempt 01 functional failure was the Source Raw Artifact DTO exposing canonical storage field `bytes` while the GUI contract expected `byte_count`.

The remediation normalizes the shared Application/operator DTO:

```text
canonical storage raw_artifacts.bytes
        ↓
SourceOperatorApplication
        ↓
raw_artifacts[].byte_count
        ↓
Source GUI
```

The canonical schema and migration contract were not changed.

Attempt 02 focused regression passing 9/9 confirms the remediation.

## 5. Automated acceptance verdict

```text
focused GUI regression = 9 / 9 PASS
Ruff                   = PASS
full regression         = 804 / 804 PASS
known warnings          = 2 local-Qdrant warnings
Automated gate          = PASS
```

P-GUI-05 is not yet `Complete / Accepted` because the task includes an interactive GUI smoke gate. The remaining acceptance work is limited to exercising the Object / Source / Evidence / Association pages in the running `sgokb-gui` application against a real Workspace and confirming expected visible behavior and canonical persistence.

Final current verdict:

```text
P-GUI-05 = Automated Verification PASS / Interactive Smoke Pending
```
