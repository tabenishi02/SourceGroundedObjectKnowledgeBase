# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-31

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)
- P-RUNTIME-04 runtime-form amendment: [`P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`](P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md)
- P-RUNTIME-04 crash-recovery remediation: [`../../design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`](../../design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md)

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
| GUI | P-GUI-06 | **Complete / Accepted** | Search / Similarity / Registry / Version GUI |
| GUI | P-GUI-07 | **Complete / Accepted** | Progress / error / safety / audit UX |
| GUI | P-GUI-08 | **Complete / Accepted** | Package / Result GUI against accepted v2 Raw boundary |
| GUI | P-GUI-09 | **Complete / Accepted** | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | **Complete / Accepted** | Final GUI parity / usability / regression acceptance |
| RAW | P-RAW-01 | **Complete / Accepted** | Current Evidence Package / Result impact survey |
| RAW | P-RAW-02 | **Complete / Accepted** | Deterministic Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03 | **Complete / Accepted** | Versioned RAW-bearing Package v2 design |
| RAW | P-RAW-04 | **Complete / Accepted** | Raw-grounded Object Result v2 design |
| RAW | P-RAW-05 | **Complete / Accepted** | Resolver -> Package v2 -> Result v2 -> Raw provenance implementation |
| RAW | P-RAW-06 | **Complete / Accepted** | Formal Raw operational acceptance / compatibility / docs closure |
| Runtime | P-RUNTIME-01 | **Complete / Accepted / Amended** | Windows reference = native Qdrant + Task Scheduler; crash recovery amended to repeating recovery pulse |
| Runtime | P-RUNTIME-02 | **Complete / Accepted** | Compose assets retained as optional/historical Docker profile |
| Runtime | P-RUNTIME-03 | **Complete / Accepted** | Shared CLI/GUI runtime health/status Application boundary |
| Runtime | P-RUNTIME-04 | **In Progress / Remediation Acceptance Pending** | Reboot/sign-in PASS; RestartOnFailure crash recovery failed; repeating-trigger remediation implemented; CI/reference-host retest pending |
| Runtime | P-RUNTIME-05 | **Blocked / Not Started** | GUI Runtime Dashboard integration; blocked by P-RUNTIME-04 formal acceptance |
| Runtime | P-RUNTIME-06 | Not Started | Runtime failure / recovery acceptance |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## GUI workstream — Complete / Accepted

Accepted architecture:

```text
Framework             = PySide6 / Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation in worker thread
Backend concurrency   = serialized per Workspace initially
Windows deployment    = pyside6-deploy / Nuitka standalone directory
Qt linking            = dynamic / separate shared libraries
```

Final public capability parity remains:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = {mcp.serve}
shared GUI reachability = 66 / 66
MCP GUI reachability    = 1 / 1
unassigned operations   = 0
```

Final authority:

- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`
- `docs/evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`

Accepted P-GUI-10 Windows evidence remains run `41066089220 (#2)`: focused 6/6, scaled-DPI 1/1, complete GUI 50/50, CLI+MCP 59/59, Ruff PASS, full regression 854/854 with two known local-Qdrant warnings.

Therefore:

```text
P-GUI-01..10 = Complete / Accepted
P-GUI workstream = Complete / Accepted for Phase P
```

## P-RAW workstream — Complete / Accepted

Accepted external AI boundary:

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

Key authorities:

- `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`
- `docs/design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`
- `docs/design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`
- `docs/decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md`
- `docs/design/P_RAW_06_ACCEPTED_EXTERNAL_AI_BOUNDARY.md`
- `docs/operations/P_RAW_06_RAW_GROUNDING_WORKFLOW.md`
- `docs/evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md`

Therefore:

```text
P-RAW-01..06 = Complete / Accepted
P-RAW workstream = Complete / Accepted for Phase P
```

## P-RUNTIME accepted baseline

### P-RUNTIME-01 — Windows Qdrant runtime operational design

The current accepted Windows reference is:

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

P-RUNTIME-02 remains **Complete / Accepted** as historical/reproducibility work. `runtime/qdrant/compose.yaml` and related assets remain available as an optional Docker/development profile and are not the supported Windows login/recovery dependency.

### P-RUNTIME-03 — Runtime health/status Application boundary

Accepted observation contract remains unchanged:

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

### Accepted evidence before remediation

Original repository implementation was accepted by Windows CI run `41091876482 (#43)`:

```text
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff                               = PASS
full repository regression         = 857 / 857 PASS
```

Reference-host evidence then established:

```text
Gate 1: Windows restart -> sign-in -> native Qdrant auto-start
        = PASS

Gate 2 attempt A: S4U task + forced qdrant.exe exit
        -> no automatic recovery
        = FAIL

Gate 2 attempt B: repository-authoritative InteractiveToken task
        + healthy /readyz 200
        + forced qdrant.exe exit
        + >60 seconds observation
        -> no replacement process / no readiness recovery
        = FAIL
```

The second failure proves that the S4U mismatch was not the root cause. `RestartOnFailure` cannot be the sole long-running-process crash-recovery authority for the supported host.

### Selected remediation

```text
\SGOKB\Qdrant
  Trigger A = AtLogOn
  Trigger B = repeating time trigger / recovery pulse
              default interval 60 seconds
              Duration omitted => indefinite repetition
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

Microsoft Task Scheduler schema defines repetition `Duration` as optional; when no duration is specified, repetition is indefinite. `RestartOnFailure` remains only as a best-effort task/action-start failure fallback.

### Repository remediation assets

- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`
- `.github/workflows/p-runtime-04-acceptance.yml`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
- `docs/evaluation/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md`

The verifier receipt is now `sgokb.qdrant-windows-autostart-check/1.1` and requires two triggers, Interactive principal, expected recovery interval, indefinite repetition, direct action, IgnoreNew, and `/readyz` HTTP 200.

The Windows workflow now includes a disposable long-running scheduled worker. It force-terminates the worker and requires the next recovery pulse to produce a different live PID without manual `Start-ScheduledTask`.

### Current CI state

PR #81 workflow attempts at the remediation HEAD have so far failed **before runner assignment** (`runner_id=0`, zero executed steps), including one explicit rerun. These are runner-start/infrastructure failures and are not product/test failures, but they also do not constitute repository acceptance.

Therefore:

```text
P-RUNTIME-04 remediation design                  = Complete
P-RUNTIME-04 remediation implementation          = Complete on PR branch
P-RUNTIME-04 remediated Windows CI               = Pending / runner infrastructure blocked
P-RUNTIME-04 reference-host Gate 1               = PASS
P-RUNTIME-04 reference-host Gate 2 old design    = FAIL / root-cause evidence accepted
P-RUNTIME-04 reference-host Gate 2 remediated    = Pending
P-RUNTIME-04 overall                             = In Progress / Remediation Acceptance Pending
```

P-RUNTIME-05 remains blocked until P-RUNTIME-04 formal acceptance.

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

Phase P remains in development. Released-system semantics continue to be governed by release `v1.1.0` until Phase P closure/release integration.

The Qdrant runtime remains independently owned outside SGOKB. `system.status.runtime_health` remains the shared CLI/GUI observation boundary and exposes no Qdrant lifecycle actions. The P-RUNTIME-04 remediation changes only the external Windows Task Scheduler configuration and operator procedure.

## Next

```text
1. obtain a Windows runner execution for PR #81 and record remediated repository acceptance;
2. re-register the remediated task on the supported Windows reference host;
3. rerun Gate 2: force qdrant.exe exit -> no manual task start -> new PID -> /readyz 200 -> system.status healthy;
4. if PASS, close P-RUNTIME-04 as Complete / Accepted and unblock P-RUNTIME-05.
```
