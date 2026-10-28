# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)
- P-GUI-03R amendment: [`P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)

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
| GUI | P-GUI-04 | **Automated Verification PASS / Interactive Smoke Pending** | GUI shell / Workspace / navigation foundation |
| GUI | P-GUI-05 | **Blocked by P-GUI-04 acceptance** | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | Not Started | Search / Similarity / Registry / Version GUI |
| GUI | P-GUI-07 | Not Started | Progress / error / safety / audit UX |
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

## P-GUI-01..03 accepted authority

P-GUI-01 fixed semantic parity for all 67 current public CLI operations:

```text
assigned = 67 / 67
unassigned = 0
```

Authority:

- `docs/requirements/GUI_REQUIREMENTS.md`
- `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`

P-GUI-02 fixed the PySide6/threading/packaging/license baseline:

- `docs/evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`
- `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`
- `docs/operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`

P-GUI-03 audited all 67 operations and accepted the target boundary:

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
```

```text
CLI parser/renderer ─┐
GUI BackendWorker ───┼─> OperatorSession
                     │      ├─ OperationRequest
                     │      ├─ OperationOutcome / OperationFailure
                     │      ├─ RuntimeFactory
                     │      └─ domain Application facades
MCP read adapter ────┘
```

Authority:

- `docs/evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`
- `docs/reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`
- `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`

## P-GUI-03R accepted implementation

All implementation and acceptance slices are complete:

```text
R1 shared operation/error contracts       Complete
R2 shared runtime factory                 Complete
R3 Source/Object/Registry boundaries      Complete
R4 Evidence/Version/Render boundaries     Complete
R5 Package/Result boundaries              Complete
R6 System/Recovery boundary               Complete
R7 Operator dispatcher/session            Complete
R8 CLI cutover                            Complete
R9 regression / semantic-equivalence      Complete / PASS
```

Current public boundary:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = 1 (mcp.serve)
```

Final R9 acceptance evidence:

```text
operator-boundary + M01 CLI = 18 / 18 PASS
M03 standard workflow       = 2 / 2 PASS
Phase N closure audit       = 11 / 11 PASS
full pytest                 = 795 / 795 PASS
ruff                        = All checks passed!
```

Final acceptance authority:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

## P-GUI-04 implementation and automated verification

The GUI foundation is implemented on `main`.

Implemented package surface:

```text
.[gui] = PySide6 bounded dependency
sgokb-gui entrypoint
src/sgokb/gui/
  bootstrap / main
  workspace state + QSettings
  GUI operation envelope
  BackendCoordinator / BackendWorker / BackendSession
  WorkspaceController
  QMainWindow shell / navigation
```

Accepted navigation is present as the 11-page shell:

```text
Home / Dashboard
Objects
Sources
Evidence
Associations
Search
Packages
Results
Registry
System
Settings
```

Workspace open/create is validated by executing `system.status` through `OperatorSession` on the backend QThread. Candidate failures do not replace the active Workspace. No GUI direct SQL or CLI-subprocess business path was introduced.

Automated acceptance result:

```text
sgokb-gui entrypoint = resolved
focused pytest       = 5 / 5 PASS
full pytest          = 800 / 800 PASS
ruff                 = All checks passed!
```

The full regression emitted only the existing two local-Qdrant capability warnings and no failures/errors.

Implementation / acceptance authority:

- `docs/evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md`

The only remaining P-GUI-04 acceptance gate is interactive GUI smoke. P-GUI-04 is therefore not yet `Complete / Accepted`.

## Sequencing

```text
P-GUI-01 Complete
        ↓
P-GUI-02 Complete
        ↓
P-GUI-03 Complete
        ↓
P-GUI-03R Complete / Accepted
        ↓
P-GUI-04 Automated Verification PASS / Interactive Smoke Pending   <- CURRENT
        ↓ interactive smoke PASS
P-GUI-04 Complete / Accepted
        ↓
P-GUI-05 / 06 / 07 core GUI
        ↓
P-RAW
        ↓
P-GUI-08 Package / Result GUI
        ↓
P-RUNTIME / P-GUI-09
        ↓
P-GUI-10 / P-CLOSE-01
```

## Current authority boundary

Phase P remains in development. Current released system semantics continue to be governed by:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- release `v1.1.0`

P-GUI-03R is an accepted development baseline. P-GUI-04 GUI code has passed automated verification but remains unaccepted until the interactive smoke gate passes.

## Next

```text
P-GUI-04 — interactive GUI smoke acceptance
```
