# P-GUI-05 — Add Object Class Selector Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Improvement: Add Object Primary Class selector
- Status: **Implemented / Verification Refresh Pending**

## Request

Replace free-text Primary Class entry in `Add Object` with selection from the existing Object Class registry.

## Implementation

`src/sgokb/gui/views/object_page.py` now performs the following flow:

```text
Add Object
  -> enter canonical name
  -> registry.class.list through BackendCoordinator / OperatorSession
  -> keep active existing Classes
  -> show non-editable Primary Class dropdown
  -> select Class
  -> enter optional aliases
  -> object.add using the selected class_id
```

The selector label is presentation-only:

```text
<Class name> [<Class key>]
```

The canonical write target is the selected stable `class_id`, not the display text.

No View/Widget direct SQLite access was added. The lookup uses the existing public `registry.class.list` operation through the accepted GUI backend lane.

If no active Class exists, Object creation is stopped and an explicit status message is shown.

## Regression coverage

Added:

```text
tests/test_p_gui_05_object_class_selector.py
```

The test verifies that:

1. Add Object obtains Classes from the Registry operation path;
2. the Class input is non-editable selection, not free text;
3. `Character [character]` is available from the seeded registry;
4. selecting it creates the Object with canonical `primary_class_id = class:character`;
5. optional aliases are preserved.

## Verification disposition

The previous P-GUI-05 automated PASS was measured before this code change. Therefore it is retained as historical evidence but is not sufficient to close the amended implementation.

Required refresh:

```powershell
python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py `
  tests/test_p_gui_05_object_class_selector.py

python -m ruff check src tests
python -m pytest
```

Until those gates pass again:

```text
P-GUI-05 = Automated Verification Refresh Pending / Functional Smoke Pending
```
