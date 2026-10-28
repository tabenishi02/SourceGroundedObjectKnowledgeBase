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
| GUI | P-GUI-05 | **Complete / Accepted** | Object / Source / Evidence / Association GUI; automated + visual + functional acceptance PASS |
| GUI | P-GUI-06 | **Next / Not Started** | Search / Similarity / Registry / Version GUI |
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

## P-GUI-01..04 accepted baseline

P-GUI-01 fixed semantic parity for all 67 current public CLI operations:

```text
assigned = 67 / 67
unassigned = 0
```

P-GUI-02 fixed PySide6 / threading / packaging / license design.

P-GUI-03 / P-GUI-03R established the shared transport-neutral boundary:

```text
CLI parser / GUI worker
        ↓
OperationRequest
        ↓
OperatorSession
        ↓
Application facades
        ↓
Repository / Retrieval / Exchange
```

P-GUI-03R final evidence:

```text
operator-boundary + M01 CLI = 18 / 18 PASS
M03 standard workflow       = 2 / 2 PASS
Phase N closure audit       = 11 / 11 PASS
full pytest                 = 795 / 795 PASS
ruff                        = All checks passed!
```

P-GUI-04 accepted shell evidence:

```text
sgokb-gui entrypoint                      PASS
focused pytest                            5 / 5 PASS
full pytest                               800 / 800 PASS
ruff                                      PASS
GUI normal startup                        PASS
11 navigation destinations                PASS
Create / Open Workspace                   PASS
recent Workspace persistence              PASS
GUI close / DB release                    PASS
same DB readable from CLI                 PASS
```

## P-GUI-05 accepted implementation

P-GUI-05 is **Complete / Accepted**.

The four daily-collection pages are real operator surfaces:

```text
Objects
Sources
Evidence
Associations
```

Operation wiring:

```text
Object       12 / 12
Source        6 / 6
Evidence      5 / 5
Association   4 / 4
------------------
Total        27 / 27
```

Accepted Object behavior includes:

- stable `object_id` targeting;
- add / rename / status / alias;
- registry/current Knowledge detail;
- events and read-only relations;
- Add Object Primary Class selector from active registry Classes;
- Set Primary Class selector from all registry Classes;
- Add Class selector from all registry Classes except current Primary;
- Remove Class selector from assigned Additional Classes only, disabled when none exist;
- Class mutations use stable `class_id` values.

Accepted Source behavior includes:

- single ZIP import;
- recursive folder ZIP discovery/import via `Import Folder...` and folder drag/drop;
- all `.zip` discovery targets, with existing WebCaptureImporter validation retained;
- per-target partial failure handling;
- Snapshot / Raw Artifact / normalization Run inspection;
- Source processing;
- effective Snapshot / Run selection with explicit free-text audit reasons.

Accepted Evidence behavior includes:

- candidates / bounded selection;
- manual include / exclude / automatic state by mouse and keyboard;
- `Ctrl+I` / `Ctrl+E` / `Ctrl+0`;
- budget usage;
- detail / provenance;
- Evidence Search.

Accepted Association behavior includes:

- list / suggest / set / clear;
- status / subject relationship / note;
- Object / Source review.

`source.snapshots` remains a shared Application boundary and now exposes presentation-useful Raw/Run metadata. Canonical `raw_artifacts.bytes` is normalized to DTO `byte_count`.

### Final automated evidence

```text
focused GUI regression = 12 / 12 PASS
Ruff                   = All checks passed!
full regression         = 807 / 807 PASS
known warnings          = 2 local-Qdrant warnings
```

Attempts 05 and 06 identified test defects only. Attempt 07 is the final automated PASS for the accepted code.

### Final interactive evidence

```text
visual rendering smoke = PASS
functional smoke       = PASS
```

The operator confirmed normal behavior for the targeted functional test scope.

Acceptance authority:

- `docs/evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`
- `docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md`
- `docs/evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`
- supporting amendment records under `docs/evaluation/P_GUI_05_*_IMPROVEMENT.md`

Final verdict:

```text
P-GUI-05 = Complete / Accepted
```

## Sequencing

```text
P-GUI-01 Complete / Accepted
        ↓
P-GUI-02 Complete / Accepted
        ↓
P-GUI-03 Complete / Accepted
        ↓
P-GUI-03R Complete / Accepted
        ↓
P-GUI-04 Complete / Accepted
        ↓
P-GUI-05 Complete / Accepted
        ↓
P-GUI-06 Search / Similarity / Registry / Version GUI   <- NEXT
        ↓
P-GUI-07 Progress / error / safety / audit UX
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

Phase P remains in development. Released system semantics continue to be governed by:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- release `v1.1.0`

P-GUI-01 through P-GUI-05 are accepted development baselines. Their acceptance does not by itself advance the formal released version.

## Next

```text
P-GUI-06 [P0] Search / Similarity / Registry / Version GUI
```
