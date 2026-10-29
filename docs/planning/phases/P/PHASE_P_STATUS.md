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
| GUI | P-GUI-06 | **Automated Verification Refresh Pending / Interactive Smoke Pending** | From/To Registry-boundary correction + semantic runtime dependency remediation implemented |
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

### Search / Similarity

Search Hard Filters provide Registry-backed Class selectors, Facet / Version / Temporal Scope selectors, `Knowledge valid From` / `Knowledge valid To`, fixed-value Derivation Kind, and archived-Object scope.

The frozen R2 Search contract now governs the From/To boundary explicitly:

```text
Registry name / alias identity
    -> canonical identity discovery
    -> From/To alone does not remove the identity result

Knowledge lexical Statement channel
    -> From/To temporal overlap filter

Semantic Statement channel
    -> From/To temporal overlap filter
```

`knowledge_valid_at`, `temporal_scope_id`, and `derivation_kind` remain Statement-scoped conditions. Facet / Derivation / Temporal Scope combinations therefore still require a matching Statement where their narrowed semantics apply.

The previous Statement-less/stale-generation exception-based remediation is now historical. The current implementation corrects the underlying contract boundary instead of adding further identity exceptions.

Search presentation continues to clear prior result/degradation state for every request and displays the current normalized failure.

### Local semantic runtime dependency

The local embedding profile uses Sentence Transformers / Transformers and now declares:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

This matches the current Transformers PyTorch floor. Dependency initialization failures are normalized to `RetrievalRuntimeUnavailableError`; the known `name 'nn' is not defined` failure produces actionable PyTorch-upgrade guidance rather than `internal/internal_error`.

Existing virtual environments are not modified by Git updates and may require an explicit PyTorch upgrade.

### Registry / Version / Render

Registry behavior remains Class/Relation Type browse, Proposal review with Accept/Reject separated from Apply, Version Show/Diff, and derived Markdown Render/export.

## P-GUI-06 verification history

Current remediation authority:

- `docs/evaluation/P_GUI_06_RANGE_CONTRACT_SEMANTIC_RUNTIME_DEPENDENCY_REMEDIATION.md`

Historical automated authority before the latest interactive failures:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md`
- `docs/evaluation/P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md`

Attempt history:

```text
Attempt 01 = PASS, pre-amendment
Attempt 02 = PASS, selector/range baseline
Attempt 03 = FAIL, verification fixture + Ruff defects; product assertion not reached
Attempt 04 = PASS, first validity-range remediation
Attempt 05 = PASS, range identity/runtime-state/Qdrant regression set
latest interactive smoke = FAIL, From/To still hid Registry identity; semantic runtime exposed nn dependency failure
```

Historical Attempt 05 evidence:

```text
focused P-GUI-04 / 05 / 06 regression = 31 / 31 PASS
Ruff                                  = All checks passed!
full pytest                            = 826 / 826 PASS
known local-Qdrant warnings            = 2
```

That result predates the current contract/runtime changes and is no longer closure authority.

Current disposition:

```text
implementation amendment        = Complete
range contract correction       = Implemented
runtime dependency correction   = Implemented
automated verification refresh  = Pending
operator environment torch check= Pending
interactive smoke               = Pending
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
        ↓ dependency/runtime correction + automated PASS
P-GUI-06 Interactive Smoke Pending
        ↓ interactive smoke PASS
P-GUI-06 Complete / Accepted
        ↓
P-GUI-07 Progress / error / safety / audit UX
```

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 remains open until the current remediation passes automated and interactive verification.

## Next

```text
1. verify / correct operator PyTorch version
2. refresh focused + full automated verification
3. repeat From/To + semantic-runtime interactive smoke
```
