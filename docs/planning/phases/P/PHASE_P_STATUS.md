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
| GUI | P-GUI-05 | **Complete / Accepted** | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | **Automated Verification Refresh Pending / Interactive Smoke Pending** | Search selector + validity-range amendment after prior automated PASS |
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

## P-GUI-01..05 accepted baseline

P-GUI-01 fixed semantic parity for all 67 current public CLI operations:

```text
assigned = 67 / 67
unassigned = 0
```

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

P-GUI-04 accepted shell evidence:

```text
focused pytest = 5 / 5 PASS
full pytest    = 800 / 800 PASS
ruff           = PASS
interactive GUI shell / Workspace acceptance = PASS
```

P-GUI-05 is **Complete / Accepted**. Its accepted pages are Objects, Sources, Evidence and
Associations. Final evidence:

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

## P-GUI-06 current implementation

P-GUI-06 replaces the Search and Registry placeholders with real operator-backed pages.
Similarity is grouped with Search; Version / Diff / Render are grouped under Registry. The
accepted 11-destination navigation inventory remains unchanged.

Operation wiring remains:

```text
Search       1 / 1
Similarity   1 / 1
Registry     9 / 9
Version      2 / 2
Render       1 / 1
------------------
Total       14 / 14
```

### Search / Similarity amendment

The latest amendment improves filter input without adding GUI direct SQL or changing the public
67-operation inventory.

Search Hard Filters now provide:

- Registry-backed dropdowns for Primary / Additional / Ancestor Class;
- Facet dropdown with editable historical fallback;
- Version dropdown with editable historical fallback;
- Temporal Scope dropdown with editable historical fallback;
- `Knowledge valid From` / `Knowledge valid To` date-range fields;
- existing Derivation Kind and archived-Object filters.

Candidate composition is:

```text
registry.class.list
object.list
    -> current_version_id
    -> version.show(current accepted Version)
    -> Facet / Temporal Scope / Version presentation choices
```

Similarity now uses Object-scoped Facet and Version selectors. Its semantic contract remains the
existing Object / optional Facet / optional source Version / cross-Class / archived scope; Search-
only Class and Temporal-Scope filters were not added to Similarity.

Knowledge validity range uses backward-compatible `valid_at` encoding:

```text
YYYY-MM-DD..YYYY-MM-DD
YYYY-MM-DD..
..YYYY-MM-DD
```

Plain single-date `valid_at` retains the historical point-in-time behavior. Range filtering uses
temporal overlap, supports one-sided ranges, treats `as_of` as a point interval, and keeps
Statements without a Temporal Scope eligible as timeless Knowledge.

Implementation authority:

- `docs/evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`
- `docs/evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`

### Registry / Version / Render

Registry behavior remains:

- Class list/detail;
- Relation Type list/detail;
- Registry Proposal list/detail and decision filter;
- Accept / Reject decisions separate from Apply;
- explicit confirmation before Apply.

Version / Render behavior remains:

- accepted Version Show;
- Before / After Version Diff;
- structured and Markdown Diff;
- Object/Version Markdown render/export and preview.

The latest user message contained an unfinished bullet beginning `Registryタブの`. No additional
Registry-page requirement was inferred from that incomplete fragment.

## P-GUI-06 verification state

The pre-amendment implementation passed:

```text
focused P-GUI-04 / 05 / 06 regression = 16 / 16 PASS
Ruff                                  = All checks passed!
full pytest                            = 811 / 811 PASS
known local-Qdrant warnings            = 2
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

Those results do **not** certify the later Search selector / validity-range amendment. New focused
tests were added:

```text
tests/test_p_gui_06_search_filter_selectors.py
tests/test_search_validity_range.py
```

Current disposition:

```text
implementation                 = Complete
desk audit                     = Complete
operation wiring               = 14 / 14
pre-amendment automated gate   = PASS
automated verification refresh = Pending
interactive smoke              = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
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
P-GUI-06 Automated Verification Refresh Pending   <- CURRENT
        ↓ refreshed automated PASS + interactive smoke PASS
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

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 remains development code
until the amended automated gate and interactive smoke acceptance pass. None of these tasks alone
advance the formal released version.

## Next

```text
P-GUI-06 — refreshed focused pytest / Ruff / full regression, then interactive GUI smoke
```
