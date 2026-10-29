# P-GUI-07 — Operation Safety / Audit UX Design

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-07 [P0] Progress / error / safety / audit UX`
- Status: **Implemented / Verification Pending**
- Safety authority: `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- Capability authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`

## 1. Purpose

P-GUI-07 adds desktop-only operator safety and observability without changing canonical Application semantics.

```text
Qt Page
  -> presentation safety gate
  -> GuiOperationRequest
  -> BackendCoordinator
       -> submitted / started lifecycle signals
       -> serialized BackendWorker
       -> OperatorSession
  -> warning / outcome / failure signals
  -> Page status + MainWindow status + Operation Center
```

No GUI SQL write path and no CLI subprocess path are introduced.

## 2. Progress contract

The current backend executes synchronous operations serially on one dedicated QThread. It does not expose trustworthy fractional progress for every operation.

Therefore the P-GUI-07 baseline is:

```text
queued/running operation -> indeterminate progress indicator
running identity         -> operation_id + safety class
cancellation state       -> explicit available/unavailable label
completion               -> success / partial / blocked / normalized failure
```

The GUI must not invent percentage progress when the Application layer has not supplied it.

## 3. Cancellation contract

Current public OperatorSession operations do not implement cooperative cancellation.

Therefore:

```text
current public operations after dispatch = non-cancellable
QThread.terminate()                       = prohibited
forced thread/process kill                = not a GUI cancellation mechanism
```

P-GUI-07 adds the metadata/UI distinction now, but marks current operations `Cancellation: Unavailable`.

A future operation may become cancellable only after its Application contract defines a safe cooperative cancellation point and cleanup semantics.

## 4. Outcome / error semantics

P-GUI-07 preserves the shared transport-neutral meaning rather than flattening states into generic UI errors.

```text
OperationOutcome.state
  success
  partial
  blocked

OperationFailure.category
  input
  not_found
  blocked
  runtime
  io
  integrity
  internal
```

Page status keeps the category/code for normalized failures.

`partial` and `blocked` outcomes are surfaced explicitly and direct the operator to the Operation Center.

## 5. Warning / degradation center

The Operation Center has two session-local views:

```text
Operations
  time
  operation
  safety class
  lifecycle state
  cancellation availability
  selected-request detail
  Equivalent CLI command

Warnings / Errors
  time
  operation
  kind
  message
```

Warnings include retrieval degradation messages emitted through `OperationOutcome.warnings`.

The center automatically becomes visible for warning/degradation, partial/blocked outcomes, and failures.

This is not a replacement for canonical provenance or Object event history. It is presentation-only session history.

## 6. Safety classification and confirmation

P-GUI-07 reuses the accepted P-GUI-01 side-effect model:

```text
READ
DERIVED
WRITE
EXTERNAL
MAINTENANCE
```

The mapping lives in `src/sgokb/gui/operation_ux.py` and is presentation metadata only.

### READ

- no destructive confirmation;
- warning/degradation remains visible.

### DERIVED

- progress / target scope visible;
- no claim that derived rebuild is canonical rollback.

### WRITE

The P-GUI-01 rule is retained: **not every WRITE needs a second modal dialog**.

Explicit Add / Rename / Apply / Import buttons are commit actions. Additional modal confirmation is reserved for higher-impact cases such as:

- effective Snapshot selection;
- effective Run selection;
- Object status transition including archive;
- association clear;
- Result force/validation/import class operations.

Registry Proposal Apply retains its existing dedicated impact confirmation rather than receiving two consecutive modal dialogs.

### EXTERNAL

External egress receives an additional common confirmation. Destination/artifact-specific preflight and acknowledgement remain the responsibility of P-GUI-08.

### MAINTENANCE

Maintenance mutation receives an additional common confirmation. Restore plan/apply separation and overwrite acknowledgement remain mandatory in P-GUI-09.

## 7. Undo / redo boundary

GUI Undo/Redo is intentionally limited to the currently focused editable widget **before submission**.

```text
allowed
  QLineEdit / QTextEdit local edit undo/redo before operation submission

not allowed
  reverse object rename after submission
  reverse Registry Apply
  reverse Result Import
  select an older Knowledge Version and call it GUI Undo
  map canonical rollback to Ctrl+Z
```

The Home page and Edit menu explicitly state this boundary.

Canonical history remains explicit domain/version/recovery behavior.

## 8. Equivalent CLI command

Each submitted GUI request is rendered as an equivalent public CLI invocation using the authoritative CLI parser shape.

Example:

```text
sgokb --db C:\data\sgokb.sqlite object rename --object object-1 --to 'New Name'
```

The command is displayed for audit/understanding only. The GUI does not execute it as a subprocess.

## 9. Session audit boundary

Operation Center history is intentionally in-memory for the GUI session.

It records presentation facts such as queued/running/success/partial/failure, warning text, safety class, and Equivalent CLI.

It does not create a second canonical audit database. Canonical mutation/event/provenance records remain owned by their existing Repository/Application contracts.

## 10. Implementation files

```text
src/sgokb/gui/operation_ux.py
src/sgokb/gui/worker.py
src/sgokb/gui/views/operation_page.py
src/sgokb/gui/views/operation_center.py
src/sgokb/gui/views/main_window.py
```

Regression coverage:

```text
tests/test_p_gui_07_operation_safety_audit.py
```

## 11. P-GUI-08 / P-GUI-09 reuse

P-GUI-08 should reuse the same EXTERNAL / WRITE safety metadata for Package Export and Result Import.

P-GUI-09 should reuse the same MAINTENANCE surface for backup / restore / derived / index operations, while retaining plan/apply and overwrite acknowledgement rules.
