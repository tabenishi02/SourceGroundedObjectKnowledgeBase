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
| RAW | P-RAW-02 | **Complete / Accepted** | Deterministic Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03 | **Not Started / Next** | RAW-bearing Package v2 design |
| RAW | P-RAW-04..06 | Not Started | Raw-grounded Result design, implementation, acceptance |
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

Breaking contracts:

```text
Evidence-Markdown external semantic payload
Evidence-only Package grounding membership
Evidence-ID-only analysis grounding instructions
Evidence-ID-only Result grounding representation
Evidence-only Result membership validation
```

Migration-required contracts:

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

Therefore:

```text
P-RAW-01 = Complete / Accepted
```

## P-RAW-02 accepted provenance resolution contract

Authority:

- `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`

P-RAW-02 freezes the deterministic Raw resolution scope at the complete input set of the Evidence's own Normalization Run:

```text
resolution scope = normalization_run_inputs
```

For each selected or protected Evidence:

```text
Evidence
  -> its own Normalization Run
  -> ALL normalization_run_artifacts
  -> exact Snapshot / Source generation
  -> physical byte-size / SHA-256 verification before egress
```

The current schema does not store an exact per-Evidence Raw subset or byte range. Therefore P-RAW-02 deliberately avoids invented precision and treats the run input set as a provenance-complete Raw Input Covering Set.

Key rules:

1. every run input Raw Artifact is provenance-required;
2. same-Snapshot artifacts not used by the run are excluded by default;
3. multiple Evidence pointing to one Raw Artifact are deduplicated by `artifact_id` at Package identity level while every Evidence -> Raw edge is preserved;
4. distinct artifact IDs are never collapsed merely because SHA-256 matches;
5. historical carry-forward Evidence resolves through its original historical run, never the currently effective generation;
6. artifact kind, path, filename, media type or content similarity are not provenance-selection heuristics;
7. missing Raw, missing provenance, Snapshot mismatch, byte-size mismatch or hash mismatch fail closed;
8. there is no Evidence-Markdown fallback and no partial covering set may be presented as complete;
9. optional Package auxiliary artifacts remain separate from provenance-required grounding material.

The resolver contract is intentionally separated from Package v2 materialization policy. P-RAW-03 may block an otherwise valid provenance set because of media, budget, privacy, secret or egress rules, but it must not silently alter provenance to make packaging succeed.

No source code, runtime behavior, Package schema, Result schema, or DB schema changed in P-RAW-02. It is a design-contract task, so the regression suite was not rerun.

Therefore:

```text
P-RAW-02 = Complete / Accepted
```

## Sequencing

```text
P-GUI-01..07 Complete / Accepted
        ↓
P-RAW-01 Complete / Accepted
        ↓
P-RAW-02 Complete / Accepted
        ↓
P-RAW-03 RAW-bearing Package v2 design   <- NEXT
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

P-GUI-01 through P-GUI-07 and P-RAW-01 through P-RAW-02 are accepted development baselines. The current active design task is P-RAW-03.

## Next

```text
P-RAW-03 — RAW-bearing Package v2 design
```
