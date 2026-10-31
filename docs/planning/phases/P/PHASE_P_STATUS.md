# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-31

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress / P-CLOSE-01 final regression pending**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current formal release: `v1.1.0`
- Release candidate: `2.0.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)
- Closure acceptance: [`P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md`](../../../evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md)

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01..10 | **Complete / Accepted** | PySide6 GUI, shared Application boundary, parity/usability/regression acceptance |
| RAW | P-RAW-01..06 | **Complete / Accepted** | Raw-bearing Package/Result v2 and Raw provenance workflow |
| Runtime | P-RUNTIME-01..06 | **Complete / Accepted** | native Windows Qdrant, shared runtime health, dashboard, failure/recovery acceptance |
| Closure | P-CLOSE-01 | **In Progress / Final Regression Pending** | docs/release integration implemented; latest-branch executable gate remains |

## Accepted Phase P architecture

```text
GUI
  = PySide6 / Qt Widgets
  = shared Application / OperatorSession boundary
  = no GUI-only canonical SQLite write path

Raw Grounding
  = Evidence selection/provenance
  -> original Normalization Run
  -> exact Package-member Raw bytes
  -> Package v2 / Result v2 raw_artifact_id grounding

Windows Runtime
  = native qdrant.exe
  = Task Scheduler external lifecycle
  = /readyz readiness
  = SGOKB observer/client only
```

## P-RUNTIME final state

P-RUNTIME-06 completed all G1-G12 reference-host gates:

```text
focused tests / Ruff                = PASS
pre-fault integrity                 = PASS
CLI/GUI outage projection           = PASS
wrong-service fail-closed           = PASS
Qdrant recovery                     = PASS
collection persistence              = PASS / 80 -> 80 / no diff
CLI/GUI baseline recovery           = PASS
Vector Index rebuild                = PASS / green / 126 points
post-rebuild integrity              = PASS
Object/current-Version counts       = 5 -> 5 / 5 -> 5
```

P-RUNTIME-04 hosted GitHub Actions verification remains deferred due the recorded billing/spending constraint and is not counted as CI PASS. Reference-host and local accepted evidence remain authoritative.

## P-CLOSE-01 release integration

Repository-side closure integration now targets `2.0.0`:

```text
project version       = 2.0.0
Package default       = v2
explicit v1           = retained legacy compatibility
release note          = docs/releases/v2.0.0.md
SemVer                = MAJOR by O06 public exchange-contract rule
GUI binary publishing = outside P-CLOSE source-release scope
```

The Package default change is the breaking release reason. Existing accepted v1 artifacts are not reinterpreted and explicit `--package-version v1` remains supported.

## Closure gate still required

Before Phase P can become `Complete / Accepted`:

```text
latest branch clean checkout
P-CLOSE focused release-contract tests PASS
full repository pytest PASS
Ruff src/tests PASS
no new unexplained failures/warnings
closure evidence updated
PR merged to main
merged main verified
v2.0.0 tag created only after the frozen main release commit is confirmed
```

## Distribution boundary

The source/repository release includes the implemented PySide6 GUI. P-CLOSE-01 does not publish/certify a standalone GUI binary because SGOKB project-license selection and artifact-specific Qt/PySide6 redistribution auditing remain separate prerequisites under P-GUI-02.

## Sequencing

```text
P-GUI-01..10      Complete / Accepted
        ↓
P-RAW-01..06      Complete / Accepted
        ↓
P-RUNTIME-01..06  Complete / Accepted
        ↓
P-CLOSE-01        <- CURRENT / FINAL REGRESSION PENDING
        ↓
Phase P Complete / Accepted
        ↓
v2.0.0 tag / publication boundary
```

## Next

Execute the P-CLOSE-01 focused release-contract tests, full repository regression and Ruff on `phase-p/close-01-release-integration`. If all gates pass, record exact evidence, merge to `main`, verify the merged release commit, then freeze the `v2.0.0` tag according to O06.
