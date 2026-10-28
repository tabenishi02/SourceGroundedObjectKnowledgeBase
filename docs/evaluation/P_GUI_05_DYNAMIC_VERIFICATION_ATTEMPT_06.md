# P-GUI-05 — Dynamic Verification Attempt 06

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Scope: recursive Sources-tab folder ZIP import amendment
- Result: **FAIL / Test Defect / Remediation Applied / Re-verification Pending**

## Executed gate

```powershell
python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py `
  tests/test_p_gui_05_object_class_selector.py `
  tests/test_p_gui_05_object_class_controls.py `
  tests/test_p_gui_05_source_recursive_zip_import.py

python -m ruff check src tests
```

Observed:

```text
focused pytest = 11 passed / 1 failed
Ruff           = All checks passed!
```

## Failure

The recursive Source import regression reached the post-import assertions with:

```text
page.snapshot_model.rowCount() == 2
```

so both valid Web Capture Bundles had been imported successfully from different recursive depths.

The only failing assertion attempted to find a raw Windows path string directly inside `operation_status.toolTip()`. The tooltip intentionally stores the batch result as JSON text. JSON escapes Windows backslashes, so a raw path such as:

```text
C:\path\to\bundle.zip
```

appears in the serialized JSON representation with escaped backslashes. Direct substring comparison therefore tested JSON rendering rather than batch-result semantics.

The logged tooltip also showed the invalid ZIP was correctly attempted and reported as:

```text
error  = BadZipFile
reason = File is not a zip file
```

## Disposition

This is a **test defect**, not a product-code defect.

The product behavior already demonstrated during Attempt 06 is:

1. recursive folder traversal reached the valid bundles;
2. both valid bundles imported into canonical Snapshots;
3. the invalid `.zip` was attempted;
4. its failure was retained in the partial batch result;
5. later/other valid targets were not suppressed.

## Remediation

Updated only:

```text
tests/test_p_gui_05_source_recursive_zip_import.py
```

The test now:

1. parses `operation_status.toolTip()` with `json.loads()`;
2. locates the batch item whose `input` equals the invalid ZIP path;
3. asserts `error == "BadZipFile"`;
4. asserts `reason == "File is not a zip file"`.

No product implementation code changed.

## Required re-verification

Re-run the same focused gate and Ruff. If both pass, run the full regression suite.

Until then:

```text
P-GUI-05 = Automated Verification Refresh Pending / Visual Smoke PASS / Functional Smoke Pending
```
