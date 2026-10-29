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
| GUI | P-GUI-06 | **Complete / Accepted** | Search / Similarity / Registry / Version GUI; Attempt 09 + interactive PASS |
| GUI | P-GUI-07 | **Complete / Accepted** | Progress / error / safety / audit UX; automated + interactive PASS |
| GUI | P-GUI-08 | Blocked by P-RAW | Package / Result GUI |
| GUI | P-GUI-09 | Not Started | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01 | **Complete / Accepted** | Current Evidence Package / Result impact survey |
| RAW | P-RAW-02 | **Not Started / Next** | Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03..06 | Not Started | Raw-bearing Package / Result design, implementation, acceptance |
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

## P-GUI-01..07 accepted baseline

```text
P-GUI-01..03R = Complete / Accepted
P-GUI-04      = Complete / Accepted
P-GUI-05      = Complete / Accepted
P-GUI-06      = Complete / Accepted
P-GUI-07      = Complete / Accepted
```

P-GUI-06 final evidence:

```text
focused regression = 29 / 29 PASS
Ruff               = PASS
full regression    = 818 / 818 PASS
warnings           = 2 known local-Qdrant warnings
interactive smoke  = PASS in accepted scope
```

P-GUI-07 final evidence:

```text
focused GUI gate = 34 / 34 PASS
Ruff             = PASS
full regression  = 823 / 823 PASS
warnings         = 2 known local-Qdrant warnings
interactive smoke = PASS in accepted scope
```

Final GUI authority includes:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`
- `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`
- `docs/evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`

## P-RAW-01 accepted impact survey

Authority:

- `docs/evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md`

The survey confirms that Raw Grounding impact is concentrated at the external exchange / grounding boundary rather than the core accepted Knowledge model.

### Breaking contracts

```text
Evidence-Markdown external semantic payload
Evidence-only Package grounding membership
Evidence-ID-only analysis grounding instructions
Evidence-ID-only Result grounding representation
Evidence-only Result membership validation
```

These contracts must be versioned rather than silently changing the semantics of `sgokb.object-evidence-package/1.0` or the v1 Result schema.

### Migration-required contracts

```text
Evidence -> Raw provenance resolution
Package audit / Raw membership trace
Package budget / preflight / egress coverage
review grounding presentation
import grounding persistence / accepted provenance
v1/v2 receive and validation routing
tests / fixtures / grounded-generation benchmarks
operator / acceptance documentation
```

P-RAW-01 requires richer provenance logically but deliberately does not select a physical DB schema migration. That is deferred to P-RAW-04/05.

### Compatible targets

```text
Evidence retrieval / operator selection intent
Source / Snapshot / Raw canonical storage
Object / Registry / Association semantics
core statement / attribute / relation semantics
derivation / attribution / temporal semantics
Version lifecycle
semantic diff core
Search / Similarity / derived indexing
```

Key compatibility constraints established by P-RAW-01:

1. Evidence remains the retrieval / human-selection unit.
2. Raw becomes the authoritative external semantic material in v2.
3. grounding must still belong to the exact bound Package.
4. Evidence <-> Raw traceability must be preserved.
5. accepted historical grounding must remain protected across Source-generation changes.
6. v1 Evidence-grounded artifacts must never be silently reinterpreted as v2 Raw-grounded artifacts.
7. canonical Knowledge semantics should remain stable unless later design finds a concrete blocker.

No source code changed and no regression suite was rerun for P-RAW-01; it is a documentation/design survey task.

Therefore:

```text
P-RAW-01 = Complete / Accepted
```

## Sequencing

```text
P-GUI-01..07 Complete / Accepted
        ↓
P-RAW-01 Complete / Accepted
        ↓
P-RAW-02 Evidence -> Raw Artifact provenance resolution contract   <- NEXT
        ↓
P-RAW-03 RAW-bearing Package v2 design
        ↓
P-RAW-04 Raw-grounded Object Result v2 design
        ↓
P-RAW-05 RAW Grounding implementation
        ↓
P-RAW-06 RAW Grounding acceptance
        ↓
P-GUI-08 Package / Result GUI
```

`P-GUI-08` remains blocked until `P-RAW-01..P-RAW-06` complete. `P-GUI-09` also depends on `P-RUNTIME-03`.

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-07 and P-RAW-01 are accepted development baselines. The current active design task is P-RAW-02.

## Next

```text
P-RAW-02 — Evidence -> Raw Artifact provenance resolution contract
```
