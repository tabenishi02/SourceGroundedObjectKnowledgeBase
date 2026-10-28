# P-GUI-05 — Dynamic Verification Attempt 05

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Scope: recursive Source folder ZIP import amendment
- Verdict: **FAIL / TEST DEFECT CONFIRMED / REMEDIATION APPLIED / RE-VERIFICATION PENDING**

## Measured result

User-executed focused verification after the recursive ZIP import amendment:

```text
focused GUI regression = 11 / 12 PASS
Ruff                   = All checks passed!
full regression         = not run after focused failure
```

Only failure:

```text
tests/test_p_gui_05_source_recursive_zip_import.py
```

Observed symptom:

```text
expected SourcePage.snapshot_model.rowCount() == 2
actual                                         == 0
```

## Root cause

The regression fixture copied valid Web Capture Bundles to arbitrary filenames:

```text
first.zip
SECOND.ZIP
```

`WebCaptureImporter` intentionally validates that a bundle filename matches the manifest-derived canonical name:

```text
<captured_at compact form>_<capture_id>.webcapture.zip
```

Therefore both test bundles were correctly rejected by the existing importer contract. The recursive folder scan itself had discovered the ZIPs; the test had accidentally converted valid bundles into invalid inputs before asserting canonical import.

## Disposition

```text
recursive directory traversal defect = not demonstrated
product filename validation defect   = no
regression fixture defect            = yes
```

The existing filename validation is retained because it is a pre-existing integrity/safety invariant and was not part of the requested change.

## Remediation

The regression now:

- preserves canonical Web Capture bundle filenames;
- places one valid bundle directly under the chosen folder;
- places another valid bundle in a deeper nested directory;
- includes an invalid ordinary `.zip` to prove that the scan targets all ZIP files;
- verifies that the invalid ZIP is reported as a per-target partial failure without blocking the valid imports;
- verifies canonical Snapshots and Raw Artifact storage references for the valid bundles.

The interactive review also identified ambiguous UI text for effective Snapshot/Run selection. The prompt was changed from generic `Reason (required)` to explicit audit-purpose wording.

## Re-verification gate

```powershell
git pull --ff-only

python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py `
  tests/test_p_gui_05_object_class_selector.py `
  tests/test_p_gui_05_object_class_controls.py `
  tests/test_p_gui_05_source_recursive_zip_import.py

python -m ruff check src tests
```

If focused + Ruff pass:

```powershell
python -m pytest
```

Until then:

```text
P-GUI-05 = Automated Verification Refresh Pending / Visual Smoke PASS / Functional Smoke Pending
```
