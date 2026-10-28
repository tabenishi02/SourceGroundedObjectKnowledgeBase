# P-GUI-05 — Add Object Class Selector Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Improvement: Add Object Primary Class selector
- Status: **Implemented / Automated Verification PASS / Functional Smoke Pending**

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

## Verification result

After the improvement, the automated gate was rerun from the repository root.

Measured result:

```text
focused P-GUI-04 + P-GUI-05 + Class selector = 10 / 10 PASS
ruff                                             = All checks passed!
full pytest                                      = 805 / 805 PASS
known warnings                                   = 2 local-Qdrant warnings
```

The new selector test is included in both the focused run and the 805-test full regression. No new warning or regression was introduced.

Verification authority:

```text
docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_03.md
```

Current disposition:

```text
P-GUI-05 = Automated Verification PASS / Visual Smoke PASS / Functional Smoke Pending
```

The improvement is therefore accepted at the automated level. P-GUI-05 remains open only because the interactive functional smoke has not yet been completed.
