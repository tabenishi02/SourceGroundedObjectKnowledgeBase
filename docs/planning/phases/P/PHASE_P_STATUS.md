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
| Runtime | P-RUNTIME-04 | **In Progress / Remediation Acceptance Pending** | Reboot/sign-in PASS; RestartOnFailure crash recovery failed; repeating-trigger remediation implemented; CI/reference-host retest pending |
| Runtime | P-RUNTIME-05 | **Blocked / Not Started** | GUI Runtime Dashboard integration; blocked by P-RUNTIME-04 formal acceptance |
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

Final public capability inventory remains 67 public operations, 66 shared GUI-reachable operations, and the external-client-owned `mcp.serve` transport operation. P-GUI-10 Windows acceptance remains run `41066089220 (#2)`: focused 6/6, scaled-DPI 1/1, complete GUI 50/50, CLI+MCP 59/59, Ruff PASS, full regression 854/854.

Authorities:

- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`
- `docs/evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`

## P-RAW workstream — Complete / Accepted

Accepted boundary:

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

Accepted contract family:

```text
Package schema     = sgokb.object-evidence-package/2.0
instructions       = sgokb.object-analysis/2.0
Result schema      = sgokb.object-result/2.0
Raw grounding      = sgokb.raw-grounding/1.0
resolver contract  = sgokb.evidence-to-raw/1.0
```

Authorities include `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`, the P-RAW-02/03/04 design documents, and the P-RAW-06 decision/operations/acceptance documents.

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

Authorities:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/planning/phases/P/P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`

### P-RUNTIME-02 — optional Docker profile

P-RUNTIME-02 remains Complete / Accepted as historical/reproducibility work. `runtime/qdrant/compose.yaml` and related assets remain optional Docker/development assets and are not the supported Windows lifecycle dependency.

### P-RUNTIME-03 — Runtime health/status boundary

The accepted observer-only contract is unchanged:

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

Authorities:

- `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- `docs/evaluation/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_ACCEPTANCE.md`
- `src/sgokb/runtime_health.py`
- `src/sgokb/application_system.py`

## P-RUNTIME-04 — Windows login auto-start / crash recovery

### Previously accepted repository baseline

Original Windows CI run `41091876482 (#43)` accepted the initial native Task Scheduler implementation:

```text
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff                               = PASS
full repository regression         = 857 / 857 PASS
```

### Reference-host evidence

```text
Gate 1
Windows restart -> sign-in -> no manual launch -> native Qdrant available
= PASS

Gate 2 attempt A
S4U task -> force qdrant.exe exit -> no automatic recovery
= FAIL

Gate 2 attempt B
repository-authoritative InteractiveToken task
-> /readyz HTTP 200
-> force qdrant.exe exit
-> >60 seconds observation
-> no replacement process / no readiness recovery
= FAIL
```

Attempt B proves that the S4U mismatch was not the crash-recovery root cause. The accepted conclusion is that `RestartOnFailure` cannot be relied upon as the sole long-running-process crash supervisor for the supported host.

### Selected remediation

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

Microsoft Task Scheduler's repetition schema defines `Duration` as optional; omitting it means the repetition pattern continues indefinitely. `RestartOnFailure` remains only a task/action-start failure fallback.

### Remediation implementation

PR #81 updates:

- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`
- `.github/workflows/p-runtime-04-acceptance.yml`
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- P-RUNTIME-01 decision, P-RUNTIME-04 amendment, operations, acceptance, and runtime README

Verifier schema is now:

```text
sgokb.qdrant-windows-autostart-check/1.1
```

The verifier requires exactly one LogonTrigger and one repeating TimeTrigger, the expected recovery interval, indefinite repetition, Interactive principal, one direct action, `IgnoreNew`, and `/readyz` HTTP 200.

The Windows workflow now includes a disposable long-running scheduled worker. It force-terminates the worker and requires the next recovery pulse to create a different live PID without a second manual `Start-ScheduledTask`.

### Current automated acceptance state

The remediation workflow has repeatedly failed **before runner assignment**. The observed jobs have `runner_id=0` and `steps=[]`, including an explicit rerun and the latest remediation HEAD. Therefore these are runner-start/infrastructure failures, not executed product/test failures; however they do not provide repository acceptance evidence either.

Current state:

```text
remediation design                         = Complete
remediation implementation                 = Complete on PR #81
remediated Windows CI                      = Pending / runner infrastructure blocked
reference-host Gate 1                      = PASS
reference-host Gate 2 old design           = FAIL / root-cause evidence accepted
reference-host Gate 2 remediated design    = Pending
P-RUNTIME-04 overall                       = In Progress / Remediation Acceptance Pending
```

P-RUNTIME-05 remains blocked until P-RUNTIME-04 is formally accepted.

## Sequencing

```text
P-GUI-01..10 Complete / Accepted
        ↓
P-RAW-01..06 Complete / Accepted
        ↓
P-RUNTIME-01..03 Complete / Accepted
        ↓
P-RUNTIME-04 remediation implementation + acceptance  <- CURRENT
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
1. obtain an executable Windows CI run for PR #81 and record remediated repository acceptance;
2. re-register the remediated task on the supported Windows reference host;
3. rerun Gate 2: force qdrant.exe exit -> no manual task start -> new PID -> /readyz 200 -> system.status healthy;
4. if PASS, close P-RUNTIME-04 as Complete / Accepted and unblock P-RUNTIME-05.
```
