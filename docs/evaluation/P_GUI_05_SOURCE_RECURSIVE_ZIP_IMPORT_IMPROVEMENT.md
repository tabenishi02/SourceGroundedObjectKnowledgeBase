# P-GUI-05 — Source Recursive ZIP Import Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Improvement: recursive folder ZIP import from the Sources tab
- Status: **Implemented / Verification Refresh Pending**

## Request

Add a Sources-tab import mode that accepts a folder and attempts every ZIP file below that folder recursively.

## Implementation

### GUI

`src/sgokb/gui/views/source_page.py` exposes:

```text
Import Capture...   -> existing single-file ZIP import
Import Folder...    -> choose a directory for recursive ZIP import
```

`Import Folder...` uses `QFileDialog.getExistingDirectory()` and passes the selected directory to the existing `source.import` operator path.

Directory drag/drop continues to call the same `source.import` operation and therefore receives the same recursive ZIP behavior.

### Application boundary

`src/sgokb/application_source.py` resolves directory import targets as:

```text
selected directory
  -> recursive traversal
  -> regular files whose suffix case-folds to `.zip`
  -> deterministic sorted target list
  -> attempt each through Application.import_source_path()
```

The directory scan therefore targets all ZIP files, rather than pre-filtering only names matching `*.webcapture.zip`.

This does **not** weaken Web Capture validation. `WebCaptureImporter` still requires a valid Web Capture Bundle, including the canonical filename derived from `captured_at` and `capture_id`. An arbitrary ZIP, renamed capture, or otherwise invalid ZIP is attempted and reported as a per-target failure; it is not imported canonically.

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

The corrected regression exercises the actual folder dialog path and verifies that:

1. a valid canonically named Web Capture ZIP directly under the selected folder is imported;
2. another valid canonically named Web Capture ZIP in a deeper subdirectory is imported;
3. a non-ZIP file is ignored;
4. an arbitrary invalid `.zip` is still discovered and reported as a partial per-target failure;
5. both valid captures become canonical Snapshots;
6. Raw Artifact `storage_ref` values point to the recursively discovered valid ZIP files.

## Verification attempt 01

Initial focused verification produced:

```text
focused = 11 / 12 PASS
Ruff    = PASS
```

The failing test had renamed otherwise valid Web Capture Bundles to `first.zip` and `SECOND.ZIP`. That violated the pre-existing importer invariant that the bundle filename must match `captured_at + capture_id + .webcapture.zip`.

Disposition:

```text
product recursive scan defect = not demonstrated
test fixture defect           = confirmed
existing importer safety rule = retained
```

The regression fixture was corrected to preserve canonical bundle filenames while placing them at different recursive depths. An additional invalid ordinary ZIP remains in the fixture so the test still proves that all ZIP files are targeted by the folder scan.

## Effective selection prompt clarification

During the same interactive review, the previous prompt:

```text
Reason (required):
```

was found ambiguous. The GUI now states the purpose explicitly:

```text
Reason for choosing this Snapshot as effective (required):
Reason for choosing this normalization run as effective (required):
```

The value remains free-text audit/provenance context explaining why the operator chose that Snapshot or normalization run as the effective one.

## Verification refresh

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
```

If those pass, run:

```powershell
python -m pytest
```

Until the refreshed gates pass:

```text
P-GUI-05 = Automated Verification Refresh Pending / Visual Smoke PASS / Functional Smoke Pending
```
