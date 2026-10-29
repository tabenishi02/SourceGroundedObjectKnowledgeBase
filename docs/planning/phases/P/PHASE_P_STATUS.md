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
| GUI | P-GUI-06 | **Automated Verification Refresh Pending / Interactive Smoke Pending** | Semantic Search mode now forces Semantic runtime; Hybrid defaults runtime ON |
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

The experimental From/To date range is removed. The current Search mode/runtime contract is:

```text
Lexical  -> Semantic runtime OFF / disabled
Semantic -> Semantic runtime ON / disabled
Hybrid   -> Semantic runtime ON by default; explicit opt-out remains available
```

The operator report after Attempt 08 showed that the previous independent controls allowed `mode=semantic` with `semantic_runtime=false`, producing the expected missing EmbeddingProvider/VectorIndexAdapter error. This GUI contract defect is now corrected in `src/sgokb/gui/views/search_page_derivation.py` and covered by `tests/test_p_gui_06_search_runtime_state.py`.

Current amendment authorities:

- `docs/evaluation/P_GUI_06_FROM_TO_FILTER_REMOVAL.md`
- `docs/evaluation/P_GUI_06_SEMANTIC_RUNTIME_MODE_COUPLING_REMEDIATION.md`

### Local semantic runtime / GUI native preload

The local embedding profile remains:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

Verified operator environment:

```text
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

The GUI process-level native crash remediation remains: PyTorch / Transformers / Sentence Transformers native dependencies are preloaded on the Qt main thread before the backend QThread starts. Harrier model construction remains lazy.

### Registry / Version / Render

Registry behavior remains Class/Relation Type browse, Proposal review with Accept/Reject separated from Apply, Version Show/Diff, and derived Markdown Render/export.

## P-GUI-06 verification history

Latest historical automated authority:

```text
Attempt 08
focused regression = 28 / 28 PASS
Ruff               = PASS
full regression    = 817 / 817 PASS
warnings           = 2 known local-Qdrant warnings
```

Attempt 08 verified the post-From/To-removal surface but predates the Search mode / Semantic runtime coupling correction. It is therefore historical evidence, not current closure authority.

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
        ↓ focused + Ruff + full regression PASS
P-GUI-06 Interactive Smoke Pending
        ↓ Semantic / Hybrid + remaining smoke PASS
P-GUI-06 Complete / Accepted
        ↓
P-GUI-07 Progress / error / safety / audit UX
```

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 remains open until the new Search mode/runtime contract passes refreshed automated and interactive verification.

## Next

```text
1. refresh focused P-GUI-06 + Ruff gate
2. refresh full regression
3. re-run Semantic Search: runtime must be requested automatically
4. re-run Hybrid Search: semantic channel is attempted by default
5. finish Similarity / Registry / Version / Render interactive smoke
6. if all PASS, close P-GUI-06 as Complete / Accepted
```
