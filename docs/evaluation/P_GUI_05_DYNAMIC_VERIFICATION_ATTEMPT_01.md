# P-GUI-05 — Dynamic Verification Attempt 01

Updated: 2026-10-29

- Task: `P-GUI-05 — Object / Source / Evidence / Association GUI`
- Baseline under test: `c1d50c1d85390e0fae21a08eb81a1447ab93f90c`
- Disposition: **FAIL / Remediation Applied / Re-verification Pending**

## 1. Commands executed

```powershell
git pull --ff-only

python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py

python -m pytest
python -m ruff check src tests
```

## 2. Dynamic result

Focused GUI regression:

```text
9 collected
8 passed
1 failed
```

Full repository regression:

```text
804 collected
803 passed
1 failed
2 warnings
```

The two warnings were the existing local-Qdrant capability warnings.

The only pytest failure was:

```text
test_source_page_import_process_selection_and_raw_inspection
```

The P-GUI-05 test and Source page expected the transport-facing Raw Artifact size field `byte_count`, while `SourceOperatorApplication.snapshots()` was passing through the canonical SQLite row field `bytes` unchanged.

Canonical storage remains:

```text
raw_artifacts.bytes
```

The GUI/Application DTO contract is now normalized to:

```text
raw_artifacts[].byte_count
```

This keeps presentation code independent from canonical storage column names. No migration or canonical schema change was made.

## 3. Ruff result

Attempt 01 reported 8 lint findings:

```text
I001  evidence_page.py import block
F401  evidence_page.py unused QWidget
E501  evidence_page.py long selected_count line
I001  object_page.py import block
F401  object_page.py unused QWidget
I001  source_page.py import block
F401  source_page.py unused QWidget
E501  test_p_gui_05_domain_pages.py long assertion
```

Remediation applied:

- removed the three unused `QWidget` imports;
- wrapped the Evidence selection count expression;
- wrapped the long Association assertion;
- preserved all operation semantics and GUI behavior.

## 4. Remediation commits

Remediation was applied directly to `main` after Attempt 01. The resulting remediation range changes only:

```text
src/sgokb/application_source.py
src/sgokb/gui/views/object_page.py
src/sgokb/gui/views/source_page.py
src/sgokb/gui/views/evidence_page.py
tests/test_p_gui_05_domain_pages.py
```

No public operation IDs, database migrations, package/result contracts, or released v1.1.0 semantics were changed.

## 5. Required re-verification

Run focused GUI regression and Ruff first:

```powershell
git pull --ff-only

python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py

python -m ruff check src tests
```

If both pass, run the full repository regression:

```powershell
python -m pytest
```

P-GUI-05 remains **Implemented / Dynamic Verification Pending** until the re-verification passes.
