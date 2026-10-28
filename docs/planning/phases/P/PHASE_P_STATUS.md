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
| GUI | P-GUI-06 | **Automated Verification PASS / Interactive Smoke Pending** | Search / Similarity / Registry / Version / Render GUI; 14 operations wired; 16/16 focused + 811/811 full PASS |
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

Accepted Object behavior includes stable `object_id` targeting, registry-backed Class selectors,
alias/status mutation, event inspection and read-only relations.

Accepted Source behavior includes single and recursive folder ZIP import, per-target partial
failure handling, Raw / normalization inspection, processing, and effective Snapshot / Run
selection with explicit audit reasons.

Accepted Evidence behavior includes candidate retrieval, bounded selection, manual
include/exclude/automatic state, budget display, detail/provenance and Evidence Search.

Accepted Association behavior includes list / suggest / set / clear with status, subject
relationship and note.

Final P-GUI-05 evidence:

```text
focused GUI regression = 12 / 12 PASS
Ruff                   = All checks passed!
full regression         = 807 / 807 PASS
visual smoke            = PASS
functional smoke        = PASS
```

Acceptance authority:

- `docs/evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`
- `docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md`
- `docs/evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`

Final verdict:

```text
P-GUI-05 = Complete / Accepted
```

## P-GUI-06 implementation and automated verification state

P-GUI-06 implementation is complete and its automated verification gate is **PASS**. Interactive
GUI smoke remains pending.

The accepted shell placeholders are replaced by real pages for:

```text
Search
Registry
```

Version / Diff / Render are grouped as Registry tabs; Similarity is grouped with Search. The
accepted 11-destination navigation inventory therefore remains unchanged.

Operation wiring:

```text
Search       1 / 1
Similarity   1 / 1
Registry     9 / 9
Version      2 / 2
Render       1 / 1
------------------
Total       14 / 14
```

Implemented Search behavior includes:

- Lexical / Semantic / Hybrid modes;
- semantic-runtime opt-in and strict `require_full_runtime` control;
- result / candidate limits;
- left-side hard-filter panel for Primary / Additional / Ancestor Class, Facet, Version,
  Temporal Scope, Knowledge-valid-at, Derivation Kind and archive scope;
- ranked result detail;
- explicit degraded-channel display.

Implemented Similarity behavior includes:

- stable Object selection through `object.list`;
- overall and optional Facet-specific Similarity;
- optional source Version pinning;
- cross-Class and archived scope controls;
- explicit local semantic-runtime requirement with no silent fallback.

Implemented Registry behavior includes:

- Class list/detail;
- Relation Type list/detail;
- Registry Proposal list/detail and decision filter;
- separate Accept / Reject decision actions;
- separate Apply action, enabled only for accepted unapplied proposals;
- explicit confirmation before Apply.

Implemented Version / Render behavior includes:

- accepted Version Show;
- Before / After Version Diff;
- structured Diff view;
- Markdown Diff using the existing H-04 renderer;
- Object/Version Markdown render/export;
- generated derived Markdown preview.

No GUI direct SQL or CLI-subprocess business path was introduced. Proposal Accept and Apply remain
separate canonical operations. Search/runtime failure and degradation semantics remain owned by
the existing Application/operator boundary.

Automated evidence:

```text
focused P-GUI-04 / 05 / 06 regression = 16 / 16 PASS
Ruff                                  = All checks passed!
full pytest                            = 811 / 811 PASS
known local-Qdrant warnings            = 2
```

The two warnings are the existing local-Qdrant limitations and do not represent test failures.

Implementation / verification authority:

- `docs/evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`
- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

Current P-GUI-06 disposition:

```text
implementation       = Complete
desk audit           = Complete
operation wiring     = 14 / 14
automated acceptance = PASS
interactive smoke    = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
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
P-GUI-06 Automated Verification PASS / Interactive Smoke Pending   <- CURRENT
        ↓ interactive smoke PASS
P-GUI-06 Complete / Accepted
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

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 has passed measured
automated verification but still requires interactive smoke acceptance. None of these tasks alone
advance the formal released version.

## Next

```text
P-GUI-06 — interactive GUI smoke acceptance
```
