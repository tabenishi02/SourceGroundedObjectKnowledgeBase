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
| GUI | P-GUI-06 | **Automated Verification PASS / Interactive Smoke Pending** | Attempt 08: From/To removed; 28/28 focused + 817/817 full PASS |
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

```text
P-GUI-01..03R = Complete / Accepted
P-GUI-04      = Complete / Accepted
P-GUI-05      = Complete / Accepted
```

P-GUI-05 final evidence remains:

```text
focused GUI regression = 12 / 12 PASS
Ruff                   = PASS
full regression         = 807 / 807 PASS
visual smoke            = PASS
functional smoke        = PASS
```

## P-GUI-06 current implementation

P-GUI-06 provides operator-backed Search / Similarity / Registry / Version / Render pages.

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

Current Search hard filters are:

```text
Primary Class
Additional Class
Ancestor Class
Facet
Version ID
Temporal Scope ID
Derivation Kind
Include archived Objects
```

The experimental `Knowledge valid From` / `Knowledge valid To` range filter has been removed.

```text
From/To GUI controls            = removed from operator surface
GUI valid_at="FROM..TO"         = no longer emitted
range-aware retrieval adapters  = removed
canonical R2 HybridObjectSearch = restored directly
```

The pre-existing non-GUI single-point `valid_at` / `knowledge_valid_at` contract remains intact. Canonical Temporal Scope data and the Temporal Scope ID filter are unchanged.

Current amendment authority:

- `docs/evaluation/P_GUI_06_FROM_TO_FILTER_REMOVAL.md`

### Local semantic runtime / GUI native preload

The local embedding profile remains:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

Verified operator environment before this amendment:

```text
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

The GUI process-level Semantic runtime crash was remediated by preloading PyTorch / Transformers / Sentence Transformers native dependencies on the Qt main thread before the backend QThread starts. This remediation is retained.

### Registry / Version / Render

Registry behavior remains Class/Relation Type browse, Proposal review with Accept/Reject separated from Apply, Version Show/Diff, and derived Markdown Render/export.

## P-GUI-06 current automated authority

Attempt 08 is the current post-removal automated verification authority:

```text
focused regression = 28 / 28 PASS
Ruff               = PASS
full regression    = 817 / 817 PASS
warnings           = 2 known local-Qdrant warnings
```

Authority document:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_08.md`

Attempt 07 remains historical evidence for the pre-removal surface.

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
P-GUI-06 Automated Verification PASS
        ↓ interactive Search / Semantic / Similarity / Registry / Version / Render smoke
P-GUI-06 Interactive Smoke Pending   <- CURRENT
        ↓ PASS
P-GUI-06 Complete / Accepted
        ↓
P-GUI-07 Progress / error / safety / audit UX
```

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 automated verification is PASS; only the refreshed interactive smoke gate remains open.

## Next

```text
1. confirm From/To controls are absent
2. confirm remaining Search hard filters and Lexical Search are usable
3. confirm Semantic runtime ON remains crash-free
4. confirm Similarity behavior
5. confirm Registry / Version / Render behavior
6. if all PASS, close P-GUI-06 as Complete / Accepted
```
