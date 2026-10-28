# P-GUI-05 — Source Recursive ZIP Import Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Improvement: recursive folder ZIP import from the Sources tab
- Status: **Implemented / Verification Refresh Pending**

## Request

Add a Sources-tab import mode that accepts a folder and imports every ZIP file below that folder recursively.

## Implementation

### GUI

`src/sgokb/gui/views/source_page.py` now exposes:

```text
Import Capture...   -> existing single-file ZIP import
Import Folder...    -> choose a directory for recursive ZIP import
```

`Import Folder...` uses `QFileDialog.getExistingDirectory()` and passes the selected directory to the existing `source.import` operator path.

Directory drag/drop continues to call the same `source.import` operation and therefore receives the same recursive ZIP behavior.

### Application boundary

`src/sgokb/application_source.py` now resolves directory import targets as:

```text
selected directory
  -> recursive traversal
  -> regular files whose suffix case-folds to `.zip`
  -> deterministic sorted target list
  -> import each through Application.import_source_path()
```

This includes ordinary `.zip` names and uppercase/mixed-case ZIP suffixes. It is no longer restricted to `*.webcapture.zip` filenames.

Single-file behavior remains unchanged: an explicitly supplied file is attempted directly.

Batch semantics remain unchanged:

- every discovered ZIP is attempted;
- one invalid ZIP does not stop later targets;
- per-target errors are returned in the batch result;
- the operator outcome is partial when any target fails.

No GUI direct SQL or Repository access was introduced.

## Regression coverage

Added:

```text
tests/test_p_gui_05_source_recursive_zip_import.py
```

The regression exercises the actual folder dialog path and verifies that:

1. a ZIP directly under the selected folder is imported;
2. a `.ZIP` in a deeper subdirectory is imported;
3. non-ZIP files are ignored;
4. both captures become canonical Snapshots;
5. Raw Artifact `storage_ref` values point to the discovered ZIP files.

## Verification refresh

The previous P-GUI-05 automated PASS was measured before this amendment. Therefore a refreshed automated gate is required.

Run:

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
python -m pytest
```

Until these gates pass:

```text
P-GUI-05 = Automated Verification Refresh Pending / Visual Smoke PASS / Functional Smoke Pending
```
