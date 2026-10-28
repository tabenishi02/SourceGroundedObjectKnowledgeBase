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
| GUI | P-GUI-03R | **Implemented / Dynamic Verification In Progress** | Shared Application/operator boundary refactor |
| GUI | P-GUI-04 | **Blocked by P-GUI-03R regression gate for backend wiring** | GUI shell / Workspace / navigation |
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
Framework             = PySide6
UI                     = Qt Widgets
Backend                = QObject worker on dedicated QThread
DB                     = Repository per operation in worker thread
Operation concurrency  = serialized per Workspace initially
Packaging              = pyside6-deploy / Nuitka
Mode                   = standalone directory / portable ZIP
Onefile                = not baseline
Static Qt linking      = prohibited
```

Authority:

- `docs/evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`
- `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`
- `docs/operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`

Public OSS publication remains blocked until SGOKB itself receives an explicit project-level license Decision/root `LICENSE`; private development is unaffected.

## P-GUI-03 completion

P-GUI-03 audited the implementation boundary for all 67 public operations.

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
--------------------------------
Total                      67
```

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

Authority:

- `docs/evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`
- `docs/reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`
- `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`

## P-GUI-03R implementation state

R1-R8 are implemented.

```text
R1 shared operation/error contracts       Implemented
R2 shared runtime factory                 Implemented
R3 Source/Object/Registry boundaries      Implemented
R4 Evidence/Version/Render boundaries     Implemented
R5 Package/Result boundaries              Implemented
R6 System/Recovery boundary               Implemented
R7 Operator dispatcher/session            Implemented
R8 CLI cutover                            Implemented
R9 regression / semantic-equivalence      In Progress
```

Current public boundary:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = 1 (mcp.serve)
```

The CLI synchronous path is now:

```text
argparse
  -> OperationRequest
  -> OperatorSession
  -> OperationOutcome / OperationFailure
  -> existing sgokb.cli/1.0 rendering / exit codes
```

Major implementation artifacts:

```text
src/sgokb/operation_contracts.py
src/sgokb/runtime.py
src/sgokb/application_source.py
src/sgokb/application_registry.py
src/sgokb/application_evidence.py
src/sgokb/application_version.py
src/sgokb/application_render.py
src/sgokb/application_exchange.py
src/sgokb/application_system.py
src/sgokb/application_operator.py
src/sgokb/cli/main.py
src/sgokb/cli/runtime.py
tests/test_p_gui_03r_operator_boundary.py
```

Implementation authority:

- `docs/evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`

## P-GUI-03R R9 Attempt 01

Operator execution on Windows/Python 3.10.6 produced:

```text
tests/test_p_gui_03r_operator_boundary.py + tests/test_m01_cli.py
→ PASS: 17 / 17

tests/test_m03_standard_workflow.py
→ NOT RUN: installed `sgokb` console script unavailable

full `python -m pytest`
→ NOT RUN: collection stopped because `qdrant_client` was unavailable

`python -m ruff check src tests`
→ findings detected; remediation applied after Attempt 01
```

Interpretation:

- the new shared boundary tests and existing M01 CLI contract tests passed together;
- M03 did not reach workflow execution and therefore did not demonstrate a semantic failure;
- full pytest did not reach execution because an existing optional test dependency was absent;
- Ruff findings introduced by P-GUI-03R were corrected or narrowly handled, and the existing pytest fixture-reexport false positives were narrowly configured; rerun is required before claiming Ruff PASS.

Detailed authority:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

## Attempt 02 preflight and gate

After updating the local checkout to current `main`:

```powershell
git pull --ff-only
python -m pip install -e ".[dev,mcp,vector-qdrant]"
python -m pip check
Get-Command sgokb
python -c "import qdrant_client; print(qdrant_client.__file__)"
```

Then run:

```powershell
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

P-GUI-04 canonical backend wiring remains blocked until these regressions complete successfully or any newly exposed runtime-only prerequisite is separately classified and resolved.

## Sequencing

```text
P-GUI-01 Complete
        ↓
P-GUI-02 Complete
        ↓
P-GUI-03 Complete
        ↓
P-GUI-03R Implemented / Verification In Progress
        ↓ Attempt 02 regression PASS
P-GUI-03R Complete / Accepted
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

Phase P is still in development. Current released system semantics remain governed by:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- release `v1.1.0`

P-GUI-03R code is implemented on `main`, but it is not accepted as a completed compatibility refactor until its dynamic regression gate passes.

## Next

```text
P-GUI-03R R9 Attempt 02 — fully provisioned dynamic regression / semantic-equivalence verification
```
