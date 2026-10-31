# SGOKB GUI Happy-Path Acceptance Checklist

Updated: 2026-11-01

- Baseline release: `v2.0.0`
- Release commit: `1adae99ee62c3054a35b1325b8a43716943ff06a`
- Checklist creation baseline: `main` at `2ca4902de7944e6aaefcda0dd86baa9f0fa1dbb7`
- Scope: PySide6 desktop GUI normal-path acceptance
- Status: **Prior accepted evidence reconciled / GUI-HP-14 interactive PASS / one integrated check remains**

## 1. Purpose

This document turns the GUI happy-path scenarios into one operator-facing acceptance checklist and records which scenarios are already covered by accepted Phase P evidence.

This is not a replacement for the original P-GUI/P-RUNTIME acceptance records. It is an integration checklist for post-`v2.0.0` GUI normal-path verification.

## 2. Status rules

| Status | Meaning |
|---|---|
| `OK` | The scenario, or a materially equivalent behavior, already passed accepted evidence. |
| `NOT RUN` | The exact integrated happy-path scenario has not yet been demonstrated. This is not a failure. |

Evidence type:

- `Interactive`: operator-confirmed real GUI smoke/functional evidence.
- `Automated`: accepted Windows/Qt automated functional or contract evidence.
- `Interactive + Automated`: both forms of evidence exist for the relevant behavior.

An `OK` entry does **not** imply that the exact scenario was manually rerun after the `v2.0.0` tag unless an explicit post-release interactive record is identified. Phase P acceptance remains the evidence source for inherited entries. P-CLOSE-01 subsequently passed the final repository regression (`876 passed`, two known local-Qdrant warnings) and Ruff before the release freeze.

## 3. Summary

```text
Total happy-path scenarios = 50
OK                         = 49
NOT RUN                    = 1
Remaining                  = #49
```

The remaining work is intentionally integration-focused:

1. One continuous real-data GUI workflow in a single Workspace from Object/Source preparation through Result import, Search, Render, and final integrity verification.

## 4. Happy-path checklist

| # | Scenario | Expected normal result | Status | Evidence type | Existing authority |
|---:|---|---|---|---|---|
| 1 | GUI startup / Workspace | `sgokb-gui` starts; Workspace can be opened/created; current path is visible; recent Workspace survives restart | **OK** | Interactive + Automated | `P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md` |
| 2 | Dashboard | Dashboard opens and shows active Workspace/status and normal entry points | **OK** | Interactive + Automated | `P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md` |
| 3 | Main navigation | Home, Objects, Sources, Evidence, Associations, Search, Packages, Results, Registry, System, Settings are reachable | **OK** | Interactive + Automated | P-GUI-04; P-GUI-10 |
| 4 | Object creation | Name / Primary Class / aliases can be supplied and a canonical Object is created | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 5 | Object basic mutation | Rename, alias, status, Primary/Additional Class operations work and refreshed state is shown | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 6 | Source import | A capture can be imported and Source/Snapshot/Raw state is created | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 7 | Source detail / Raw inspection | Snapshot and Raw Artifact information is inspectable from the Source workflow | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 8 | Source processing | Snapshot processing/normalization completes and Run/Evidence state is shown | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 9 | Effective Snapshot / Run selection | Effective Snapshot/Run can be changed with an explicit audit reason | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 10 | Object-Source Association | Association inspect/suggest/set/clear and metadata handling work | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 11 | Evidence candidates | Candidate retrieval and candidate inspection work | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 12 | Evidence provenance | Evidence detail can trace Source / Snapshot / Run / Raw provenance | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 13 | Evidence selection | Bounded selection, manual include/exclude/automatic state, and budget display work | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 14 | Evidence Search — Lexical / Semantic / Hybrid | Evidence Search modes execute normally with the expected local runtime/degradation semantics | **OK** | Interactive | Post-`v2.0.0` GUI-HP-14 operator run, 2026-11-01; all checklist items PASS |
| 15 | Package v2 Build | Package page selects the accepted Raw-grounded v2 path; build succeeds and Raw/binding information is visible | **OK** | Automated | `P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md`; P-CLOSE-01 focused regression |
| 16 | Package Stage | Built Package can be staged and stage state is shown | **OK** | Automated | `P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md` |
| 17 | Package Preflight | Destination-aware preflight succeeds on a valid Package and returns an allowed/non-blocked disposition | **OK** | Automated | `P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md` |
| 18 | Package Export | Reviewed Raw inclusion/preflight acknowledgement permits explicit external export | **OK** | Automated | `P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md` |
| 19 | Result Detect | Valid incoming Result is detected | **OK** | Automated | P-GUI-08 accepted GUI round trip |
| 20 | Result Receive | Result is received with Package binding and receipt state | **OK** | Automated | P-GUI-08 accepted GUI round trip |
| 21 | Result List / Pending | Receipt list and pending-only list are available and refresh correctly | **OK** | Automated | `P_GUI_08_PACKAGE_RESULT_GUI_IMPLEMENTATION.md` / accepted P-GUI-08 regression |
| 22 | Result Validate | Valid Result v2 passes validation and lifecycle state is shown | **OK** | Automated | P-GUI-08 accepted GUI round trip |
| 23 | Result Review | Current Knowledge / Raw grounding review and diff are available | **OK** | Automated | P-GUI-08 accepted GUI round trip |
| 24 | Result Import | Explicit import creates an accepted Knowledge Version with Raw grounding links | **OK** | Automated | P-GUI-08 accepted GUI round trip |
| 25 | Version display | Current / explicit accepted Version can be displayed without confusing historical and current state | **OK** | Automated | P-GUI-06 accepted operation wiring/regression |
| 26 | Version Diff | Before/after Version diff is available | **OK** | Automated | P-GUI-06 accepted operation wiring/regression |
| 27 | Render | Accepted Version can be rendered to derived Markdown without changing canonical Knowledge | **OK** | Automated | `P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md` |
| 28 | Object Relations | Relation inspection from Object detail works; no direct accepted-Relation edit path is introduced | **OK** | Interactive + Automated | `P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 29 | Search — Lexical | Lexical Search executes normally and returns ranked results | **OK** | Interactive + Automated | P-GUI-06 final acceptance/regression |
| 30 | Search — Semantic | Semantic Search requests its local semantic runtime and executes normally | **OK** | Interactive + Automated | `P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 31 | Search — Hybrid | Hybrid Search executes normally with accepted semantic-runtime coupling | **OK** | Interactive + Automated | `P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 32 | Search filters | Accepted GUI filters/selectors (Class, Facet, Version, Temporal Scope, Derivation Kind, archived, limits) work | **OK** | Automated | `P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md` |
| 33 | Similarity | Overall / Facet-specific Similarity and scope controls execute normally | **OK** | Automated | P-GUI-06 accepted operation wiring/regression |
| 34 | Registry Class | Class list/detail is available | **OK** | Automated | P-GUI-06 accepted operation wiring/regression |
| 35 | Registry Relation Type | Relation Type list/detail is available | **OK** | Automated | P-GUI-06 accepted operation wiring/regression |
| 36 | Registry Proposal workflow | Proposal list/detail, Accept/Reject, and separate explicit Apply preserve the required state transition | **OK** | Automated | P-GUI-06 accepted operation wiring/regression |
| 37 | System Status | System Overview/status can be refreshed and shared runtime-health projection is shown | **OK** | Interactive + Automated | P-GUI-09; `P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md` |
| 38 | System Integrity | Integrity operation is GUI-reachable and returns the shared Application result | **OK** | Automated | P-GUI-09 accepted System coverage |
| 39 | Derived Status / Sync | Derived status/sync operations are available with shared operation semantics | **OK** | Automated | P-GUI-09 accepted System coverage |
| 40 | Vector Index | Index status/rebuild operations are available through the shared System surface | **OK** | Automated | P-GUI-09 accepted System coverage; P-RUNTIME acceptance |
| 41 | Backup | Backup status/create/composite create/verify are GUI-reachable through the maintenance surface | **OK** | Automated | P-GUI-09 accepted System coverage |
| 42 | Restore normal path | Restore Plan and Apply remain distinct; valid plan can proceed with required overwrite acknowledgement; composite path follows the same safety model | **OK** | Automated | `P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_ACCEPTANCE.md` |
| 43 | Runtime Dashboard | System > Overview shows SQLite/Embedding/Qdrant/generation/derived health and external Qdrant ownership; no lifecycle controls are invented | **OK** | Interactive + Automated | `P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md` |
| 44 | MCP display | MCP Workspace binding, semantic-runtime option, exact stdio serve command, and external-client lifecycle explanation are visible | **OK** | Automated | P-GUI-09; P-GUI-10 |
| 45 | Keyboard operation | Main navigation keyboard use and `Ctrl+O`, `Ctrl+N`, `Ctrl+Z`, `Ctrl+Y` behave as accepted | **OK** | Automated | `P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md` |
| 46 | Presentation-state persistence | Last page / recent Workspace and presentation-only state survive restart without becoming canonical DB state | **OK** | Interactive + Automated | P-GUI-04; P-GUI-10 |
| 47 | Scaled-DPI / layout smoke | GUI remains usable under accepted 1.5x DPI smoke and nonzero layout geometry | **OK** | Automated | P-GUI-10 |
| 48 | Long-running operation UX | Running/progress/busy state, close safety, warning/error surfaces, and available cancellation presentation behave normally | **OK** | Interactive + Automated | `P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md` |
| 49 | One continuous full real-data GUI happy path | In one real Workspace: Object -> Source -> process -> Association -> Evidence -> Package v2 -> external Result -> validate/review/import -> Version -> Search -> Render -> integrity | **NOT RUN** | — | Individual segments are accepted, and P-GUI-08 has an automated Package/Result round trip, but no authority records this entire sequence as one continuous real-GUI run |
| 50 | GUI normal exit / restart | GUI closes cleanly, presentation state can be restored, canonical DB remains usable, and external runtime ownership is preserved | **OK** | Interactive + Automated | P-GUI-04; P-GUI-10; P-RUNTIME lifecycle contract |

## 5. Important scope corrections

### 5.1 Search filter scope

The accepted Search GUI does **not** expose the experimental `Knowledge valid From` / `Knowledge valid To` range fields. Those fields were removed by operator decision during P-GUI-06.

Current accepted GUI filter scope includes Registry-backed Class selectors, Facet, Version, Temporal Scope, Derivation Kind, archived opt-in, and result/candidate limits. The historical non-GUI single-point `valid_at` / `knowledge_valid_at` contract remains separate.

### 5.2 Package default

P-GUI-08 already used v2 as the first explicit GUI Package selection. P-CLOSE-01 later changed the no-option public Package default to v2 for release `2.0.0`. The current happy-path therefore treats Package v2 as the normal path and v1 as explicit legacy compatibility.

### 5.3 Manual versus automated acceptance

P-GUI-08 and P-GUI-09 provide strong Windows automated functional acceptance, but their automated PASS is not rewritten here as an interactive manual PASS. The `Evidence type` column preserves that distinction.

## 6. Normal-path execution records

### GUI-HP-14 — Evidence Search Lexical / Semantic / Hybrid — PASS

The operator completed the post-`v2.0.0` GUI-HP-14 checklist on 2026-11-01 and reported every required item as successful:

```text
Workspace opened normally                         PASS
SQLite HEALTHY                                    PASS
Embedding HEALTHY                                 PASS
Qdrant HEALTHY / ready                            PASS
Lexical search completed normally                 PASS
Lexical results returned                          PASS
Semantic search completed normally                PASS
Semantic results returned                         PASS
Hybrid + Full local semantic runtime ON completed PASS
Hybrid results returned                           PASS
Hybrid Lexical / Semantic scores both visible     PASS
Evidence Detail opened                            PASS
Provenance opened                                 PASS
Degraded channel absent                           PASS
Unexpected error absent                           PASS
```

Disposition:

```text
GUI-HP-14 = OK / Interactive PASS
```

### GUI-HP-49 — Continuous real-data GUI standard workflow — NOT RUN

Goal: demonstrate the complete normal operator path once, in order, through the real desktop GUI and one test Workspace.

Procedure:

1. Open/create a dedicated acceptance Workspace.
2. Create an Object with Primary Class.
3. Import a real Web Capture Bundle.
4. Process the Snapshot and inspect generated Run/Evidence/Raw provenance.
5. Confirm Object-Source Association.
6. Retrieve/select Evidence within a bounded budget.
7. Build the normal Package v2 path; inspect Raw inclusion/binding.
8. Stage, preflight, acknowledge, and export the Package.
9. Produce a valid external Result v2 using the exported Package.
10. Detect, receive, validate, and review the Result.
11. Explicitly import the Result and confirm the new current accepted Version.
12. Inspect Version / Relation / Raw grounding state.
13. Run Lexical, Semantic, and Hybrid Object Search as applicable.
14. Run Similarity and Render.
15. Open `System > Integrity` and confirm a successful integrity result.
16. Close and reopen the GUI; confirm the same Workspace/canonical state remains usable.

PASS criterion: the sequence completes without bypassing review/acknowledgement boundaries, and the final canonical state remains valid after restart.

## 7. Evidence authority

Primary accepted evidence used to initialize this checklist:

- [`P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md`](P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md)
- [`P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`](P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md)
- [`P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`](P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md)
- [`P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`](P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md)
- [`P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`](P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md)
- [`P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md`](P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md)
- [`P_GUI_08_PACKAGE_RESULT_GUI_IMPLEMENTATION.md`](P_GUI_08_PACKAGE_RESULT_GUI_IMPLEMENTATION.md)
- [`P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_ACCEPTANCE.md`](P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_ACCEPTANCE.md)
- [`P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`](P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md)
- [`P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md`](P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md)
- [`P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md`](P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md)

## 8. Current disposition

```text
Existing accepted evidence reconciled = 49 / 50 OK
Remaining normal-path checks          = 1 / 50 NOT RUN
Remaining                             = GUI-HP-49
Blocking product defect identified    = none
```

GUI-HP-14 is closed by the post-release interactive run above. The checklist remains open only for GUI-HP-49. Its `NOT RUN` state is not a regression against the already accepted `v2.0.0` release.