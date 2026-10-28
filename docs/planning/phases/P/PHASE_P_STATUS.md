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
| GUI | P-GUI-06 | **Automated Verification PASS / Interactive Smoke Pending** | Derivation selector + validity-range remediation verified; 24/24 focused + 819/819 full PASS |
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

P-GUI-05 is **Complete / Accepted**. Final evidence:

```text
focused GUI regression = 12 / 12 PASS
Ruff                   = All checks passed!
full regression         = 807 / 807 PASS
visual smoke            = PASS
functional smoke        = PASS
```

## P-GUI-06 current implementation

P-GUI-06 replaces the Search and Registry placeholders with real operator-backed pages. Similarity is grouped with Search; Version / Diff / Render are grouped under Registry. The accepted 11-destination navigation inventory remains unchanged.

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

### Search / Similarity

Search Hard Filters provide:

- Registry-backed dropdowns for Primary / Additional / Ancestor Class;
- Facet dropdown with editable historical fallback;
- Version dropdown with editable historical fallback;
- Temporal Scope dropdown with editable historical fallback;
- `Knowledge valid From` / `Knowledge valid To` date-range fields;
- fixed-value Derivation Kind dropdown;
- archived-Object filter.

Candidate composition remains above Repository storage:

```text
registry.class.list
object.list
    -> current_version_id
    -> version.show(current accepted Version)
    -> Facet / Temporal Scope / Version presentation choices
```

Similarity uses Object-scoped Facet and Version selectors while retaining its existing semantic contract: Object / optional Facet / optional source Version / cross-Class / archived scope.

Knowledge validity range keeps the historical `valid_at` transport slot and accepts:

```text
YYYY-MM-DD..YYYY-MM-DD
YYYY-MM-DD..
..YYYY-MM-DD
```

Plain single-date `valid_at` keeps point-in-time behavior. Range filtering uses temporal overlap, treats `as_of` as a point interval, supports one-sided ranges, and keeps timeless Statements eligible.

The false-negative remediation fixes the case where an active derived R2 Search generation lags a newer current accepted Version:

```text
Registry identity range eligibility
    -> canonical accepted Knowledge

Knowledge lexical / semantic channels
    -> active R2 Search generation
```

This preserves current Object name/alias discoverability without bypassing generation isolation for derived Knowledge channels.

### Registry / Version / Render

Registry behavior remains:

- Class list/detail;
- Relation Type list/detail;
- Registry Proposal list/detail and decision filter;
- Accept / Reject separate from Apply;
- explicit confirmation before Apply.

Version / Render behavior remains:

- accepted Version Show;
- Before / After Version Diff;
- structured and Markdown Diff;
- Object/Version Markdown render/export and preview.

## P-GUI-06 automated verification

Current automated authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`
- `docs/evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`
- `docs/evaluation/P_GUI_06_DERIVATION_KIND_SELECTOR_IMPROVEMENT.md`
- `docs/evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`
- `docs/evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`

Attempt history:

```text
Attempt 01 = PASS, pre-amendment
Attempt 02 = PASS, selector/range baseline
Attempt 03 = FAIL, verification fixture + Ruff defects; product assertion not reached
Attempt 04 = PASS, current post-remediation authority
```

Measured current result:

```text
focused P-GUI-04 / 05 / 06 regression = 24 / 24 PASS
Ruff                                  = All checks passed!
full pytest                            = 819 / 819 PASS
known local-Qdrant warnings            = 2
```

The two warnings are existing local-Qdrant limitations and are not failures.

Current disposition:

```text
implementation         = Complete
desk audit             = Complete
operation wiring       = 14 / 14
automated verification = PASS
interactive smoke      = Pending
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

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 has passed its current automated gate and remains pending interactive smoke acceptance. None of these tasks alone advance the formal released version.

## Next

```text
P-GUI-06 — interactive GUI smoke acceptance
```
