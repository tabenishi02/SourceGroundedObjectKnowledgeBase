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
| GUI | P-GUI-04 | **Complete / Accepted** | GUI shell / Workspace / navigation foundation |
| GUI | P-GUI-05 | **Automated Verification PASS / Interactive Smoke Pending** | Object / Source / Evidence / Association GUI |
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

## P-GUI-04 accepted implementation

P-GUI-04 is **Complete / Accepted**.

Final acceptance evidence:

```text
sgokb-gui entrypoint                     PASS
focused pytest                           5 / 5 PASS
full pytest                              800 / 800 PASS
ruff                                     All checks passed!
GUI normal startup                       PASS
11 navigation destinations               PASS
Create Workspace                         PASS
Dashboard Workspace/status display       PASS
Open Workspace                           PASS
Recent Workspaces persisted after restart PASS
GUI close / DB release                    PASS
same DB readable from CLI                 PASS
```

Acceptance authority:

- `docs/evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md`

## P-GUI-05 implementation state

P-GUI-05 implementation is complete and the automated verification gate has passed. Interactive GUI smoke remains before formal closure.

The four P-GUI-04 placeholders are now real operator pages:

```text
Objects
Sources
Evidence
Associations
```

The P-GUI-05 operation inventory is fully wired:

```text
Object       12 / 12
Source        6 / 6
Evidence      5 / 5
Association   4 / 4
------------------
Total        27 / 27
```

Implemented behavior includes:

- stable `object_id` targeting for Object writes;
- Object registry/current Knowledge detail, aliases, events, read-only relations and Class operations;
- Source import by file dialog and drag/drop;
- Source processing and effective Snapshot/Run selection with interactive reason;
- Raw Artifact / normalization metadata inspection;
- Evidence candidates, bounded selection, detail/provenance and Evidence Search;
- Evidence manual include/exclude by mouse and `Ctrl+I` / `Ctrl+E` / `Ctrl+0`;
- selected/token/byte/omitted budget usage display;
- Association list/suggest/set/clear with status, subject relationship and note;
- shared request correlation and failure semantics through `OperationPage`;
- stable backend busy state across chained mutation -> refresh operations.

`source.snapshots` was extended backward-compatibly with Raw/Run inspection metadata rather than adding a GUI-only direct-storage path. The Application/operator DTO normalizes canonical `raw_artifacts.bytes` to presentation-neutral `byte_count`. Public operation count remains unchanged.

Automated acceptance coverage was added in:

```text
tests/test_p_gui_05_domain_pages.py
```

Automated verification evidence:

```text
focused GUI regression = 9 / 9 PASS
Ruff                   = All checks passed!
full regression         = 804 / 804 PASS
known warnings          = 2 local-Qdrant warnings
```

Verification authority:

- `docs/evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`
- `docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_02.md`

Current verdict:

```text
P-GUI-05 = Automated Verification PASS / Interactive Smoke Pending
```

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
P-GUI-04 Complete / Accepted
        ↓
P-GUI-05 Automated Verification PASS / Interactive Smoke Pending   <- CURRENT
        ↓ interactive smoke PASS
P-GUI-05 Complete / Accepted
        ↓
P-GUI-06 / 07 core GUI
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

P-GUI-03R and P-GUI-04 are accepted development baselines. P-GUI-05 is implemented and automated-verified development code pending interactive acceptance. None of these tasks alone advance the formal released version.

## Next

```text
P-GUI-05 — interactive GUI smoke acceptance
```
