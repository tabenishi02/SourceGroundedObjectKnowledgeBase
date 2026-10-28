# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-28

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

### GUI baseline

- PySide6 / Qt for Python + Qt Widgets
- public `sgokb` CLIとsemantic parityを持つDesktop GUI
- CLI / GUIはApplication / Service層を共有
- GUIはCLI subprocess wrapperをprimary business boundaryにしない
- backendは専用QThread上のQObject worker
- Repositoryはoperationごとにworker thread内で生成・破棄
- Windows distribution baselineは`pyside6-deploy` / Nuitka standalone directory
- PySide6 / Qt LGPL complianceをRelease gateへ含める

### RAW Grounding

- Evidence retrieval / selectionは維持する
- external AIへ送るsemantic materialはEvidence再構成MarkdownからRaw Artifactへ変更する
- Package / Result / Validation / Review / Import / ProvenanceをRaw-grounded modelへ再設計する

### Runtime

- Windowsログイン後にQdrantを自動利用可能にする
- QdrantはGUI processのlifecycle ownerにせずCLI / GUI / MCPから共有する
- Docker / Compose + pinned Qdrant + named volume + localhost binding + restart policyをinitial baseline候補とする

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01 | **Complete / Accepted** | GUI requirements / compatibility contract |
| GUI | P-GUI-02 | **Complete / Accepted** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | **Complete / Accepted** | Transport-neutral Application boundary audit / refactor plan |
| GUI | P-GUI-03R | **Next / Not Started** | Shared Application/operator boundary refactor implementation |
| GUI | P-GUI-04 | **Blocked by P-GUI-03R for backend wiring** | GUI shell / Workspace / navigation |
| GUI | P-GUI-05 | Not Started | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | Not Started | Search / Similarity / Registry / Version GUI |
| GUI | P-GUI-07 | Not Started | Progress / error / safety / audit UX |
| GUI | P-GUI-08 | Blocked by P-RAW | Package / Result GUI |
| GUI | P-GUI-09 | Not Started | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01..06 | Not Started | Raw-grounded exchange redesign / implementation / acceptance |
| Runtime | P-RUNTIME-01..06 | Not Started | Windows Qdrant auto-start / health / GUI integration |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## P-GUI-01 completion

P-GUI-01 fixed GUI semantic compatibility and mapped current public CLI capability:

```text
public CLI operations = 67
assigned GUI capability = 67 / 67
unassigned = 0
```

Authority:

- `docs/requirements/GUI_REQUIREMENTS.md`
- `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`

## P-GUI-02 completion

P-GUI-02 fixed the Desktop technical baseline:

```text
Framework            = PySide6
UI                    = Qt Widgets
Backend              = QObject worker on dedicated QThread
DB                    = Repository per operation in worker thread
Operation concurrency = serialized per Workspace initially
Packaging             = pyside6-deploy / Nuitka
Mode                  = standalone directory / portable ZIP
Onefile               = not baseline
Static Qt linking     = prohibited
```

Authority:

- `docs/evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`
- `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`
- `docs/operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`

Public OSS publication remains blocked until SGOKB itself receives an explicit project-level license Decision/root `LICENSE`; private development is unaffected.

## P-GUI-03 completion

P-GUI-03 audited the implementation boundary for all 67 public operations.

Result:

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
--------------------------------
Total                      67
```

Interpretation:

- 25 operations already have a suitable Application boundary.
- 26 have reusable lower-level services but CLI-owned orchestration/audit/target/batch behavior must be extracted.
- 15 still depend on CLI/direct Repository logic that needs a transport-neutral Application facade.
- `mcp serve` is the sole transport-specific public operation and remains outside normal synchronous OperatorSession dispatch.

Accepted target:

```text
CLI parser/renderer ─┐
GUI BackendWorker ───┼─> OperatorSession
                     │      ├─ shared OperationRequest
                     │      ├─ OperationOutcome / OperationFailure
                     │      ├─ RuntimeFactory
                     │      └─ domain Application facades
MCP read adapter ────┘
```

P-GUI-03 authority:

- `docs/evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`
- `docs/reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`
- `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`

The audit found that proceeding directly to broad P-GUI-04 backend wiring would require duplication or CLI coupling. Therefore `P-GUI-03R` is inserted as a required P0 implementation remediation.

## P-GUI-03R gate

`P-GUI-03R` implements the accepted design without intended public CLI semantic change.

Required slices:

```text
R1 shared operation/error contracts
R2 shared runtime factory
R3 Source/Object/Registry boundaries
R4 Evidence/Version/Render boundaries
R5 Package/Result boundaries
R6 System/Recovery boundary
R7 Operator dispatcher/session
R8 CLI cutover
R9 regression / semantic-equivalence acceptance
```

P-GUI-04 may perform presentation-only preparation in isolation, but canonical operation wiring is blocked until P-GUI-03R passes.

## Sequencing

```text
P-GUI-01 Complete
        ↓
P-GUI-02 Complete
        ↓
P-GUI-03 Complete
        ↓
P-GUI-03R Next
        ↓
P-GUI-04 GUI shell / Workspace / navigation
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

Phase P is still in development. Current implemented system semantics remain governed by:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- release `v1.1.0`

P-GUI-01..03 documents are accepted future GUI/refactor contracts and must not be represented as already implemented runtime capability.

## Next

```text
P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation
```
