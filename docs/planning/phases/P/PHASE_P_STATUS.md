# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-31

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)
- P-RUNTIME-04 runtime-form amendment: [`P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`](P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md)
- P-RUNTIME-04 crash-recovery remediation: [`P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`](../../../design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md)
- P-RUNTIME-04 acceptance: [`P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md`](../../../evaluation/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md)
- P-RUNTIME-04 hosted-CI deferred verification: [`P_RUNTIME_04_GITHUB_ACTIONS_BILLING_BLOCKER.md`](../../../evaluation/P_RUNTIME_04_GITHUB_ACTIONS_BILLING_BLOCKER.md)
- P-RUNTIME-05 design: [`P_RUNTIME_05_GUI_RUNTIME_DASHBOARD.md`](../../../design/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD.md)
- P-RUNTIME-05 acceptance: [`P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md`](../../../evaluation/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md)

## Accepted modernization direction

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01..10 | **Complete / Accepted** | PySide6 GUI, shared Application boundary, parity/usability/regression acceptance |
| RAW | P-RAW-01..06 | **Complete / Accepted** | Raw-bearing Package/Result v2 and raw provenance workflow |
| Runtime | P-RUNTIME-01 | **Complete / Accepted / Amended** | Windows reference = native Qdrant + Task Scheduler; repeating-trigger crash recovery accepted |
| Runtime | P-RUNTIME-02 | **Complete / Accepted** | Compose retained as optional/historical Docker profile |
| Runtime | P-RUNTIME-03 | **Complete / Accepted** | Shared CLI/GUI runtime health/status Application boundary |
| Runtime | P-RUNTIME-04 | **Complete / Accepted** | Reference-host and local remediation validation PASS; hosted Windows CI deferred as non-blocking verification debt due GitHub billing/spending limit |
| Runtime | P-RUNTIME-05 | **In Progress / Final Local Verification Pending** | Runtime Dashboard implemented; focused/full regression and reference CLI projection PASS; Ruff findings remediated; latest-head focused/Ruff and GUI smoke remain |
| Runtime | P-RUNTIME-06 | Not Started | Runtime failure / recovery acceptance |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## GUI workstream — Complete / Accepted

Accepted architecture remains:

```text
Framework             = PySide6 / Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation in worker thread
Backend concurrency   = serialized per Workspace initially
Windows deployment    = pyside6-deploy / Nuitka standalone directory
```

P-GUI-10 final Windows acceptance remains run `41066089220 (#2)`: focused 6/6, scaled-DPI 1/1, complete GUI 50/50, CLI+MCP 59/59, Ruff PASS, full regression 854/854.

## P-RAW workstream — Complete / Accepted

Accepted boundary remains:

```text
selected Evidence
  -> original Normalization Run
  -> ALL input Raw Artifacts
  -> exact verified Raw bytes
  -> Package v2
  -> external AI
  -> Result v2 raw_artifact_id grounding
  -> validate / review / import
  -> raw_grounding_links
  -> accepted Version
```

## P-RUNTIME accepted baseline

### P-RUNTIME-01 — Windows Qdrant runtime

Current accepted Windows reference:

```text
runtime form             = native Windows qdrant.exe
lifecycle owner          = Windows Task Scheduler
startup trigger          = AtLogOn for configured interactive user
crash recovery           = repeating time trigger on same task
recovery interval        = 60 seconds by default
recovery duration        = indefinite
multiple instances       = IgnoreNew
RestartOnFailure         = start/action-failure fallback only
default task identity    = \SGOKB\Qdrant
storage/configuration    = operator-owned native Qdrant runtime state
readiness                = Qdrant /readyz
GUI / CLI lifecycle role = client / observer only
```

### P-RUNTIME-03 — Runtime health/status boundary

The accepted observer-only contract remains unchanged:

```text
operation                  = system.status
projection                 = data.runtime_health
schema                     = sgokb.runtime-health/1.0
components                 = sqlite / embedding / qdrant / generation / derived
qdrant lifecycle owner     = external
observe                    = true
start / stop / restart     = false / false / false
qdrant readiness authority = /readyz
```

## P-RUNTIME-04 — Complete / Accepted

### Historical root-cause evidence

Original Windows CI run `41091876482 (#43)` accepted the initial native Task Scheduler repository assets, but the real host later proved `RestartOnFailure` alone did not restart an already-running long-lived Qdrant process after forced termination.

```text
Gate 1 reboot -> sign-in -> automatic Qdrant start                    = PASS
Gate 2 attempt A / S4U / RestartOnFailure-only                         = FAIL
Gate 2 attempt B / Interactive / RestartOnFailure-only                 = FAIL
```

Attempt B established that the S4U drift was not the crash-recovery root cause.

### Accepted remediation

```text
Task      = \SGOKB\Qdrant
Trigger A = AtLogOn
Trigger B = repeating TimeTrigger / recovery pulse
            default interval = 60 seconds
            duration = indefinite
Action    = qdrant.exe directly
Principal = Interactive / Limited
Policy    = MultipleInstances=IgnoreNew
```

### Reference-host acceptance

```text
verifier schema                         = sgokb.qdrant-windows-autostart-check/1.1
principal                              = Interactive
trigger count                           = 2
recovery interval                       = 60 seconds
forced qdrant.exe termination           = performed
manual Start-ScheduledTask after crash  = none
replacement qdrant.exe                  = PID 41480
recovered /readyz                       = HTTP 200 / all shards are ready
SGOKB qdrant.status                     = healthy
SGOKB qdrant.ready                      = true
SGOKB qdrant.version                    = 1.19.2
reference-host acceptance               = Complete / Accepted
```

### Local workflow-equivalent validation

Windows 11 / PowerShell 7.6.9 validation passed:

```text
Register/Test script parse      = PASS / 0 syntax errors
Disposable recovery smoke       = PASS / PID 38356 -> 42796
Manual restart after crash      = none
Focused P-RUNTIME               = 9 passed / 0 failed
Ruff                            = PASS
Full regression                 = 858 passed / 0 failed / 0 skipped
Warnings                        = 2 existing local-Qdrant warnings / no new warning
Production Qdrant after test    = unchanged / readyz 200 / SGOKB healthy
```

### Hosted CI deferred verification

GitHub-hosted remediation jobs did not execute workflow steps. Run `41115542118`, attempt 2, was blocked before runner assignment with GitHub's billing/spending annotation:

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased.
```

Observed state:

```text
runner_id = 0
steps     = []
```

The task authority for P-RUNTIME-04 does not require GitHub-hosted CI as a mandatory completion condition. Because reference-host lifecycle acceptance and local workflow-equivalent validation both passed, hosted CI is retained as **non-blocking deferred verification debt**, not counted as a CI PASS.

Formal closure:

```text
reference-host acceptance       = Complete / Accepted
local remediation validation    = PASS
GitHub Actions remediation CI   = Deferred / external billing-spending constraint
P-RUNTIME-04 overall            = Complete / Accepted
P-RUNTIME-05                    = In Progress
```

When GitHub Actions capacity returns, run the hosted Windows workflow. A later genuine product/portability failure becomes new remediation work; it does not invalidate the fact that P-RUNTIME-04 met its accepted reference-host completion criteria at closure.

## P-RUNTIME-05 — In Progress / Final Local Verification Pending

The Runtime Dashboard is implemented on PR #82 using only the accepted P-RUNTIME-03 observation boundary.

Current evidence:

```text
focused runtime/dashboard tests = PASS / 22 passed on pre-style-remediation HEAD
full regression                 = PASS / 869 passed / 2 known local-Qdrant warnings
reference CLI projection        = PASS
Qdrant                          = healthy / ready=true / v1.19.2
Search generation               = degraded / generation_not_active
Derived                         = degraded / rendering pending only
Ruff                            = 9 E501 findings -> remediated by line wrapping
latest-head focused/Ruff        = pending re-run
GUI reference-workspace smoke   = pending
```

The reference snapshot must be presented as Semantic Search `degraded`, not `blocked`: SQLite, Embedding, Qdrant and all semantic derived kinds are ready; the inactive Search generation may use legacy vector routing and the remaining Derived degradation is rendering-only.

Qdrant remains externally owned. The dashboard exposes no start, stop or restart action.

## Sequencing

```text
P-GUI-01..10 Complete / Accepted
        ↓
P-RAW-01..06 Complete / Accepted
        ↓
P-RUNTIME-01..04 Complete / Accepted
        ↓
P-RUNTIME-05  <- IN PROGRESS / FINAL LOCAL VERIFICATION
        ↓
P-RUNTIME-06
        ↓
P-CLOSE-01
```

## Current authority boundary

Phase P remains in development; released-system semantics continue to be governed by `v1.1.0` until Phase P closure/release integration. Qdrant remains independently owned outside SGOKB. `system.status.runtime_health` remains the shared CLI/GUI observation boundary and exposes no Qdrant lifecycle actions.

## Next

```text
1. re-run P-RUNTIME-05 focused tests and Ruff on the latest branch HEAD;
2. perform the reference-workspace GUI smoke in System > Overview;
3. if both pass, record final P-RUNTIME-05 acceptance and merge PR #82;
4. then begin P-RUNTIME-06 Runtime failure / recovery acceptance;
5. retain hosted P-RUNTIME-04 CI as deferred verification debt.
```
