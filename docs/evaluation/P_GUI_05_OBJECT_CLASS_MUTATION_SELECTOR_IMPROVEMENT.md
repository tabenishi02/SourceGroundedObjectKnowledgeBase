# P-GUI-05 — Object Class Mutation Selector Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Improvement: Object Class mutation selectors
- Status: **Implemented / Verification Refresh PASS**

## Request

Replace free-text Class entry for the existing Object mutation controls with registry-backed non-editable selectors:

1. `Set Primary Class`: select from every existing Object Class.
2. `Add Class`: select from every existing Object Class except the selected Object's current Primary Class.
3. `Remove Class`: enable only when the selected Object has one or more Additional Classes, and select only from those assigned Additional Classes.

## Implementation

Implemented in:

```text
src/sgokb/gui/views/object_page.py
```

All Class lists are loaded through the accepted shared operator path:

```text
ObjectPage
  -> BackendCoordinator / BackendWorker
  -> OperatorSession
  -> registry.class.list
  -> RegistryOperatorApplication
```

No GUI direct SQL or Repository access was added.

### Set Primary Class

The dialog loads all registry Classes and displays them through a non-editable dropdown. The selected stable `class_id` is passed to `object.class.set-primary`.

Inactive/non-active Classes are not hidden from this control because the requested contract is every existing Class. A non-active status is appended to the display label when applicable.

### Add Class

The dialog loads all registry Classes and removes only the selected Object's current `primary_class_id` from the candidate set. The selected stable `class_id` is passed to `object.class.add`.

This intentionally follows the requested boundary literally: all Classes except the current Primary Class remain candidates.

### Remove Class

`Remove Class` is disabled when the selected Object's `additional_class_ids` is empty.

When Additional Classes exist, the dialog loads registry labels but restricts the candidate set to those exact assigned `additional_class_ids`. The selected stable `class_id` is passed to `object.class.remove`.

Selection changes and mutation refreshes recompute the button enabled state from the current Object row.

## Stable-target behavior

All three dialogs capture the selected `object_id` before asynchronous Class lookup. Class mutation writes therefore remain stable-ID targeted and do not resolve the Object again by mutable display name.

## Regression coverage

Added:

```text
tests/test_p_gui_05_object_class_controls.py
```

The regression verifies:

- `Set Primary Class` exposes the full registry Class set;
- the selector is non-editable;
- selecting a Class changes the canonical `primary_class_id`;
- `Add Class` exposes exactly all registry Classes except the current Primary Class;
- the selected Additional Class is written canonically;
- `Remove Class` is disabled when no Additional Class exists;
- after an Additional Class exists the button becomes enabled;
- `Remove Class` exposes only the selected Object's assigned Additional Classes;
- removing a Class updates canonical state and recomputes button enabled state.

## Verification refresh

The amended implementation was verified after the change.

Measured result:

```text
focused GUI regression = 11 / 11 PASS
Ruff                   = All checks passed!
full regression         = 806 / 806 PASS
known warnings          = 2 local-Qdrant warnings
```

Verification authority:

```text
docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_04.md
```

Therefore this amendment is accepted for the P-GUI-05 automated gate.

Current P-GUI-05 state remains:

```text
P-GUI-05 = Automated Verification PASS / Visual Smoke PASS / Functional Smoke Pending
```
