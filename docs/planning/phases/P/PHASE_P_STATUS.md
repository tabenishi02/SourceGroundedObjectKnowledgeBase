# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)

## Accepted modernization direction

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01 | **Complete / Accepted** | GUI requirements / compatibility contract |
| GUI | P-GUI-02 | **Complete / Accepted** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | **Complete / Accepted** | Transport-neutral Application boundary audit / refactor plan |
| GUI | P-GUI-03R | **Complete / Accepted** | Shared Application/operator boundary refactor; R9 regression PASS |
| GUI | P-GUI-04 | **Complete / Accepted** | GUI shell / Workspace / navigation foundation |
| GUI | P-GUI-05 | **Complete / Accepted** | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | **Complete / Accepted** | Search / Similarity / Registry / Version GUI; Attempt 09 + interactive PASS |
| GUI | P-GUI-07 | **Implementation Complete / Automated Verification Pending / Interactive Smoke Pending** | Progress / error / safety / audit UX implemented |
| GUI | P-GUI-08 | Blocked by P-RAW | Package / Result GUI |
| GUI | P-GUI-09 | Not Started | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01..06 | Not Started | Raw-grounded exchange redesign / implementation / acceptance |
| Runtime | P-RUNTIME-01..06 | Not Started | Windows Qdrant auto-start / health / GUI integration |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## GUI baseline

```text
Framework             = PySide6 / Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation in worker thread
Backend concurrency   = serialized per Workspace initially
Windows deployment    = pyside6-deploy / Nuitka standalone directory
Qt linking            = dynamic / separate shared libraries
```

GUI is not a CLI subprocess wrapper. Qdrant remains an independent shared runtime.

## P-GUI-01..06 accepted baseline

```text
P-GUI-01..03R = Complete / Accepted
P-GUI-04      = Complete / Accepted
P-GUI-05      = Complete / Accepted
P-GUI-06      = Complete / Accepted
```

P-GUI-06 final evidence:

```text
focused regression = 29 / 29 PASS
Ruff               = PASS
full regression    = 818 / 818 PASS
warnings           = 2 known local-Qdrant warnings
interactive smoke  = PASS in accepted scope
```

Final authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`
- `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`

## P-GUI-07 current implementation

P-GUI-07 adds desktop operation safety and observability without changing canonical Application semantics.

Implemented:

```text
indeterminate progress for queued/running work
operation identity + READ/DERIVED/WRITE/EXTERNAL/MAINTENANCE class
explicit cancellation availability
partial / blocked outcome visibility
normalized error category/code visibility
warning / degradation / error center
high-impact WRITE + EXTERNAL + MAINTENANCE confirmation boundary
form-only Undo / Redo
no canonical rollback through GUI Undo
Equivalent CLI command display
session-local operation history / audit surface
```

Current operations remain non-cancellable after dispatch because no cooperative cancellation contract exists. P-GUI-07 does not use `QThread.terminate()` or forced process termination.

Operation Center history is presentation-only session state; canonical Object events, provenance and audit records remain owned by existing Application/Repository contracts.

Safety behavior follows the accepted P-GUI-01 contract: an explicit commit action can be sufficient for ordinary WRITE, while high-impact WRITE, EXTERNAL and MAINTENANCE mutation receive stronger confirmation.

Current authority:

- Design: `docs/design/P_GUI_OPERATION_SAFETY_AUDIT_UX.md`
- Implementation: `docs/evaluation/P_GUI_07_PROGRESS_ERROR_SAFETY_AUDIT_UX_IMPLEMENTATION.md`

## P-GUI-07 verification gate

Because shared `worker.py`, `OperationPage`, and `MainWindow` changed, the refreshed gate covers P-GUI-03R through P-GUI-07.

Expected inventory, assuming no unrelated test changes:

```text
focused GUI gate ~= 34 tests
full regression   ~= 823 tests
```

These counts are expectations only until measured locally.

## Sequencing

```text
P-GUI-01 Complete / Accepted
        ↓
P-GUI-02 Complete / Accepted
        ↓
P-GUI-03 / 03R Complete / Accepted
        ↓
P-GUI-04 Complete / Accepted
        ↓
P-GUI-05 Complete / Accepted
        ↓
P-GUI-06 Complete / Accepted
        ↓
P-GUI-07 Implementation Complete   <- CURRENT
        ↓ focused + Ruff + full regression PASS
P-GUI-07 Interactive Smoke
        ↓ PASS
P-GUI-07 Complete / Accepted
```

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-06 are accepted development baselines. P-GUI-07 implementation is complete but is not accepted until refreshed automated and interactive verification pass.

## Next

```text
1. run P-GUI-07 focused GUI regression + Ruff
2. run full regression
3. run Operation Center / progress / confirmation / Undo interactive smoke
4. if all PASS, close P-GUI-07 as Complete / Accepted
```
