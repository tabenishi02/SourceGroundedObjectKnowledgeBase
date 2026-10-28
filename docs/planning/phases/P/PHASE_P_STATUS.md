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

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01 | **Complete / Accepted** | GUI requirements / compatibility contract |
| GUI | P-GUI-02 | **Complete / Accepted** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | **Complete / Accepted** | Transport-neutral Application boundary audit / refactor plan |
| GUI | P-GUI-03R | **Implemented / Dynamic Verification In Progress** | Shared Application/operator boundary refactor; Attempt 03 final compatibility remediation applied |
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

## P-GUI-03R implementation state

R1-R8 are implemented:

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

The CLI synchronous path is:

```text
argparse
  -> OperationRequest
  -> OperatorSession
  -> OperationOutcome / OperationFailure
  -> existing sgokb.cli/1.0 rendering / exit codes
```

Implementation authority:

- `docs/evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`

## R9 Attempt 01

```text
operator-boundary + M01 CLI = 17 / 17 PASS
M03                         = blocked before execution: sgokb console script absent
full pytest                 = blocked at collection: qdrant-client absent
ruff                        = findings; remediation applied
```

Authority:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

## R9 Attempt 02

```text
operator-boundary + M01 CLI = 17 / 17 PASS
M03 standard workflow       = 2 / 2 PASS
full pytest                 = 770 passed / 9 failed / 15 errors (794 collected)
ruff                        = PASS / All checks passed
```

The 24 non-passing full-suite cases were classified as:

```text
19 = P-GUI-03R CLI compatibility-hook regression
 3 = verification environment missing sentence-transformers distribution
 2 = historical Phase N closure test coupled to current HEAD
```

Remediation after Attempt 02 restored the historical CLI monkeypatch seams through a compatibility RuntimeFactory adapter, stabilized the Phase N historical fixture at formal closure candidate `fb9b0d6a6f670d1b0f053148769ce8cd448ea217`, and added the `local-embedding` extra to the verification environment.

Authority:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_02.md`

## R9 Attempt 03

Attempt 03 ran with `dev,mcp,vector-qdrant,local-embedding` installed.

```text
focused remediation suite  = 144 passed / 2 failed (146 collected)
operator-boundary + M01 CLI = 18 / 18 PASS
M03 standard workflow       = 2 / 2 PASS
full pytest                 = 793 passed / 2 failed (795 collected)
ruff                        = 1 import-order finding
```

Both remaining test failures were the same historical derived-runtime failure-semantic contract:

```text
system derived status --semantic-runtime
system derived sync --semantic-runtime
```

A monkeypatched plain `RuntimeError("local runtime unavailable")` was reaching the generic operation mapper and becoming internal / exit 1, whereas the pre-refactor CLI contract wrapped semantic composition failures as `DerivedMaintenanceRuntimeUnavailableError` / exit 5.

Final compatibility remediation after Attempt 03:

1. `SystemOperatorApplication._derived()` now preserves the historical runtime-unavailable normalization for semantic composition failures.
2. `tests/test_phase_n_closure_audit.py` import grouping is aligned with Ruff.
3. No Search/Similarity/index-rebuild error contract was broadened by the derived-only compatibility fix.

Authority:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_03.md`

## Attempt 04 final gate

After pulling current `main`, run:

```powershell
python -m pytest tests/test_n04p05_derived_cli.py tests/test_phase_n_closure_audit.py
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

P-GUI-03R becomes `Complete / Accepted` only after all five commands pass.

## Sequencing

```text
P-GUI-01 Complete
        ↓
P-GUI-02 Complete
        ↓
P-GUI-03 Complete
        ↓
P-GUI-03R Implemented / Verification In Progress
        ↓ Attempt 04 final regression PASS
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

P-GUI-03R code is implemented on `main`, but it is not accepted as a completed compatibility refactor until R9 passes.

## Next

```text
P-GUI-03R R9 Attempt 04 — final dynamic regression / semantic-equivalence verification
```
