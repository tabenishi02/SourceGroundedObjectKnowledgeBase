# P-GUI-07 — Progress / Error / Safety / Audit UX Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-07 [P0] Progress / error / safety / audit UX`
- Status: **Complete / Accepted**
- Dependency baseline: `P-GUI-06 = Complete / Accepted`
- Design: `docs/design/P_GUI_OPERATION_SAFETY_AUDIT_UX.md`
- Automated authority: `docs/evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- Interactive authority: `docs/evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`

## 1. Implemented scope

P-GUI-07 adds a shared desktop safety/observability layer around the existing transport-neutral operation boundary.

Implemented:

- indeterminate progress for queued/running backend work;
- operation identity + safety class in the status bar;
- explicit current cancellation availability;
- `partial` / `blocked` outcome visibility;
- normalized failure category/code visibility;
- persistent-in-session warning/degradation/error center;
- WRITE / EXTERNAL / MAINTENANCE safety classification;
- stronger confirmation for high-impact WRITE and all EXTERNAL / mutation MAINTENANCE operations;
- form-only Undo/Redo boundary;
- explicit prohibition on treating canonical rollback as GUI Undo;
- Equivalent CLI command display;
- session-local GUI operation history/audit surface.

## 2. Operation Center

A bottom dock named `Operation Center` is available from `View -> Operation Center` and the Home page.

Operations tab:

```text
Time | Operation | Safety | State | Cancellation
```

Selected operation details include:

- request ID;
- Workspace path;
- safety class;
- cancellation availability;
- safety note;
- Equivalent CLI command;
- explicit statement that the history is session-local, not canonical audit data.

Warnings / Errors tab stores warning/degradation, partial/blocked, and normalized failure messages.

The dock automatically opens for warnings, degraded channels, partial/blocked outcomes, and failures.

## 3. Progress / cancellation

The current Application/operator boundary does not expose fractional progress for all operations, so the GUI uses an indeterminate progress bar instead of fabricated percentages.

Current operations have no cooperative cancellation contract. Therefore they are labeled `Cancellation: Unavailable` after dispatch. P-GUI-07 does not introduce `QThread.terminate()` or forced process termination.

## 4. Error / partial semantics

Existing transport-neutral semantics are preserved:

```text
success / partial / blocked
input / not_found / blocked / runtime / io / integrity / internal
```

Page status continues to show `[category/code]` for failures. MainWindow also exposes the normalized error in the global warning area, while Operation Center retains the session event.

## 5. Confirmation semantics

The accepted P-GUI-01 contract remains authoritative.

- READ: no destructive confirmation.
- DERIVED: target/progress visibility; no canonical-undo implication.
- WRITE: explicit commit action is the baseline confirmation; high-impact WRITE receives an additional modal gate.
- EXTERNAL: additional modal confirmation.
- MAINTENANCE mutation: additional modal confirmation.

Registry Proposal Apply keeps its existing dedicated confirmation and is not double-confirmed by the common gate.

## 6. Undo / redo

`Edit -> Undo form edit` and `Redo form edit` target only the currently focused editable widget.

They do not submit inverse operations and do not modify accepted Version history, Registry state, imported Results, or maintenance state.

## 7. Equivalent CLI

`src/sgokb/gui/operation_ux.py` renders public CLI syntax from the same operation ID / argument shape used by `OperatorSession`.

The GUI still invokes `OperatorSession` directly; Equivalent CLI is display-only.

## 8. Backend lifecycle extension

`BackendCoordinator` now emits presentation-only lifecycle signals:

```text
operation_submitted(request_id, request)
operation_started(request_id, request)
operation_warning(request_id, message)
operation_finished(request_id, outcome)
operation_failed(request_id, failure)
```

The worker emits `started` at actual execution entry, so queued and running states remain distinguishable.

## 9. Automated coverage added

New file:

```text
tests/test_p_gui_07_operation_safety_audit.py
```

Coverage includes:

- READ / WRITE / EXTERNAL / MAINTENANCE classification;
- strong confirmation boundary;
- Equivalent CLI rendering;
- cancellation metadata;
- Operation Center success lifecycle;
- warning / partial / error capture;
- MainWindow progress surface;
- form-only Undo behavior.

## 10. Automated verification

Final measured authority:

```text
focused GUI gate = 34 / 34 PASS
Ruff             = PASS
full regression  = 823 / 823 PASS
warnings         = 2 known local-Qdrant warnings
```

Authority:

- `docs/evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

The two warnings are the existing local-Qdrant limitations and are not P-GUI-07 regressions.

Earlier failed focused attempts were isolated to the new headless Undo test and one Ruff line-length issue; neither represented an Application/Repository behavior defect. The final passing test isolates the focused-form Undo contract from Qt offscreen focus acquisition behavior.

## 11. Interactive smoke

Final interactive authority:

- `docs/evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`

The operator completed the defined interactive smoke and reported no problem in the exercised scope. This closes the manual gate for Operation Center / progress / confirmation / Undo and representative existing GUI workflow usability.

## 12. Final disposition

```text
implementation          = Complete
automated verification  = PASS
interactive smoke       = PASS
```

Therefore:

```text
P-GUI-07 = Complete / Accepted
```

The next executable priority task is `P-RAW-01 — Current Evidence Package / Result impact survey` because `P-GUI-08` is blocked by completion of the P-RAW workstream and `P-GUI-09` depends on `P-RUNTIME-03`.
