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
| Runtime | P-RUNTIME-01 | **Complete / Accepted / Amended** | Windows reference = native Qdrant + Task Scheduler; recovery mechanism amended |
| Runtime | P-RUNTIME-02 | **Complete / Accepted** | Compose retained as optional/historical Docker profile |
| Runtime | P-RUNTIME-03 | **Complete / Accepted** | Shared CLI/GUI runtime health/status Application boundary |
| Runtime | P-RUNTIME-04 | **In Progress / Repository CI Pending** | Reference-host reboot/sign-in and remediated crash recovery both PASS; only executable Windows CI remains unresolved |
| Runtime | P-RUNTIME-05 | **Blocked / Not Started** | GUI Runtime Dashboard integration; blocked until P-RUNTIME-04 formal repository acceptance |
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

## P-RUNTIME-04 — Windows login auto-start / crash recovery

### Historical evidence

Original Windows CI run `41091876482 (#43)` accepted the initial native Task Scheduler repository assets:

```text
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff                               = PASS
full repository regression         = 857 / 857 PASS
```

Real-host lifecycle evidence then showed:

```text
Gate 1 reboot -> sign-in -> automatic Qdrant start
= PASS

Gate 2 attempt A / S4U / RestartOnFailure-only
= FAIL

Gate 2 attempt B / InteractiveToken / RestartOnFailure-only
= FAIL
```

Attempt B established that the S4U mismatch was not the root cause. `RestartOnFailure` was rejected as the sole long-running-process crash supervisor.

### Accepted remediation design

```text
Task      = \SGOKB\Qdrant
Trigger A = AtLogOn
Trigger B = repeating time trigger / recovery pulse
            default interval = 60 seconds
            Duration omitted = indefinite repetition
Action    = qdrant.exe directly
Principal = Interactive / Limited
Policy    = MultipleInstances=IgnoreNew
```

Normal operation:

```text
Qdrant Running -> recovery pulse -> IgnoreNew -> no duplicate instance
```

Unexpected process exit:

```text
qdrant.exe exits -> task Ready -> next recovery pulse -> new qdrant.exe -> /readyz
```

### Remediated reference-host acceptance

The supported workstation was re-registered from PR #81 with verifier schema `sgokb.qdrant-windows-autostart-check/1.1`.

Pre-crash verification:

```text
principal_logon_type      = Interactive
trigger_count             = 2
recovery_interval         = PT1M
recovery_interval_seconds = 60
ready_status              = 200
```

Crash-recovery retest:

```text
force-terminate qdrant.exe
-> no manual Start-ScheduledTask
-> next recovery pulse executes task
-> replacement qdrant.exe PID = 41480
-> /readyz = HTTP 200 / all shards are ready
-> SGOKB system.status qdrant.status = healthy
-> qdrant.ready = true
-> qdrant.version = 1.19.2
```

The SGOKB top-level `runtime_health.overall_status` was `degraded` only because unrelated generation and derived-state components were degraded. The Qdrant component itself was healthy, so P-RUNTIME-04 reference-host acceptance is unaffected.

Therefore:

```text
reference-host Gate 1                          = PASS
reference-host Gate 2 automatic process        = PASS
reference-host Gate 2 /readyz                   = PASS
reference-host Gate 2 SGOKB Qdrant health       = PASS
P-RUNTIME-04 reference-host acceptance          = Complete / Accepted
```

### Current automated acceptance state

The remediation Windows workflow has repeatedly terminated before runner assignment. Observed jobs have:

```text
runner_id = 0
steps     = []
```

These are runner-start/infrastructure failures, not executed product/test failures. They also do not provide repository acceptance evidence.

Current state:

```text
remediation design                         = Complete
remediation implementation                 = Complete on PR #81
reference-host Gate 1                      = PASS
reference-host Gate 2 remediated design    = PASS
reference-host acceptance                  = Complete / Accepted
remediated Windows CI                      = Pending / runner infrastructure blocked
P-RUNTIME-04 overall                       = In Progress / Repository CI Pending
```

P-RUNTIME-05 remains blocked until P-RUNTIME-04 repository acceptance closes.

## Local Windows remediation validation (2026-10-31)

Tested HEAD `ad9c3b29d2d6571534d6bb72fcabe3e88255ca85`; local run `20261031T041657+0900`;
Windows 11 / PowerShell 7.6.9.

- Registration and verification PowerShell parse: PASS / 0 syntax errors each.
- Disposable `\SGOKB-Acceptance-Local\QdrantRecoverySmoke`: PASS; worker
  **38356 -> 42796**, no manual restart after force termination, 60-second
  repeating trigger, recovered Running and synthetic `/readyz` HTTP 200.
- Focused P-RUNTIME: **9 passed / 0 failed**; Ruff `src tests`: PASS.
- Full repository: **858 passed / 0 failed / 0 skipped / 2 existing local-Qdrant
  warnings**, verified from the actual warning messages.
- All disposable task/process/server/temp/folder resources cleaned up.
- Production PID **41480**, Task definition, config and canonical digest unchanged;
  production `/readyz` HTTP 200; SGOKB Qdrant healthy / ready=true / version 1.19.2.

```text
reference-host acceptance       = Complete / Accepted
local remediation validation    = PASS
GitHub Actions remediation CI   = Pending / runner infrastructure blocked
P-RUNTIME-04 overall            = In Progress / Repository CI Pending
P-RUNTIME-05                    = Blocked / Not Started
```

Local Windows validation does not substitute for hosted CI. Latest observed
remediation run `41112893738` had `runner_id=0` / `steps=[]`. A later push-triggered
run must be assessed independently. PR #81 is not merged by this validation.
Details: `docs/evaluation/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md`
section 15 and `benchmark/results/p-runtime-04-local-remediation-validation.json`.

## Sequencing

```text
P-GUI-01..10 Complete / Accepted
        ↓
P-RAW-01..06 Complete / Accepted
        ↓
P-RUNTIME-01..03 Complete / Accepted
        ↓
P-RUNTIME-04 reference-host PASS / repository CI pending  <- CURRENT
        ↓
P-RUNTIME-05
        ↓
P-RUNTIME-06
        ↓
P-CLOSE-01
```

## Current authority boundary

Phase P remains in development; released-system semantics continue to be governed by `v1.1.0` until Phase P closure/release integration. Qdrant remains independently owned outside SGOKB. `system.status.runtime_health` remains the shared CLI/GUI observation boundary and exposes no Qdrant lifecycle actions. The P-RUNTIME-04 remediation changes only the external Windows Task Scheduler configuration and operator procedure.

## Next

```text
1. obtain one executable Windows CI run for PR #81;
2. require dynamic scheduled-worker crash-recovery smoke PASS;
3. require focused P-RUNTIME tests, Ruff, and full regression PASS;
4. if PASS, merge PR #81 and close P-RUNTIME-04 as Complete / Accepted;
5. unblock P-RUNTIME-05.
```
