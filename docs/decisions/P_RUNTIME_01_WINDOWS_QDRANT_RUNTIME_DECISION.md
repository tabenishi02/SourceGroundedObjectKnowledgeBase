# P-RUNTIME-01 — Windows Qdrant Runtime Decision

Date: 2026-10-31
Status: **Accepted / Amended by P-RUNTIME-04 and crash-recovery remediation**
Decision scope: Phase P reference Windows runtime for Qdrant

## Amendment

The original P-RUNTIME-01 decision selected Docker Desktop / WSL 2 + repository-owned Docker Compose as the reference Windows runtime. During P-RUNTIME-04 execution the supported deployment constraint was corrected: **Qdrant runs directly on the local Windows host as `qdrant.exe`, not in Docker**.

Reference-host acceptance then exposed a second correction: Task Scheduler `RestartOnFailure` cannot be relied upon as the sole supervisor for an already-running long-lived Qdrant process after external force termination. The accepted crash-recovery design therefore uses a repeating Task Scheduler trigger plus `MultipleInstances=IgnoreNew`; `RestartOnFailure` remains only a start/action-failure fallback.

These amendments supersede the earlier Docker choice and the earlier restart-on-failure-only crash-supervision assumption for the Windows acceptance path. P-RUNTIME-02 Compose assets remain valid historical/reproducibility evidence and an optional Docker/development profile.

## Amended decision

SGOKB adopts **native Windows Qdrant + Windows Task Scheduler** as the Phase P reference Qdrant runtime on Windows.

Accepted lifecycle:

```text
Windows user sign-in
  -> Task Scheduler AtLogOn trigger
  -> configured native qdrant.exe starts directly
  -> Qdrant /readyz becomes HTTP 200
  -> SGOKB CLI / GUI may use Qdrant

Unexpected qdrant.exe exit
  -> task returns to Ready
  -> next repeating recovery trigger fires
  -> Task Scheduler launches qdrant.exe again
  -> /readyz returns HTTP 200
```

Qdrant remains an **independent shared runtime**. Windows Task Scheduler owns launch/recovery behavior. SGOKB GUI, CLI, and MCP remain clients/observers and must not spawn Qdrant as a hidden child process or become its process supervisor.

## Fixed Phase P Windows runtime parameters

```text
Runtime form             = native Windows qdrant.exe
Binary installation      = operator-managed; SGOKB does not download/install it
Version selection        = explicit/operator-recorded; no SGOKB auto-update
Startup owner            = Windows Task Scheduler
Startup trigger          = AtLogOn for configured interactive user
Crash recovery owner     = Windows Task Scheduler
Crash recovery trigger   = repeating time trigger on the same task
Recovery interval        = 60 seconds by default; minimum 60 seconds
Recovery duration        = indefinite
Task identity            = \SGOKB\Qdrant by default
Process action           = qdrant.exe directly, with explicit optional arguments
Working directory        = explicit; defaults to qdrant.exe parent directory
RestartOnFailure role    = start/action-failure fallback, not process-crash authority
Restart fallback         = 10 attempts / >=60-second interval by default
Multiple instances       = IgnoreNew
Execution time limit     = unlimited for the long-running server process
HTTP                     = loopback Qdrant endpoint, normally 127.0.0.1:6333
gRPC                     = normally 127.0.0.1:6334 when enabled by Qdrant config
Readiness authority      = HTTP /readyz on port 6333
SGOKB lifecycle role     = client / observer only
```

The repository does not guess the local Qdrant installation path, storage path, or existing Qdrant command-line arguments. P-RUNTIME-04 registration requires the operator to pass the real executable path and preserves the existing native Qdrant runtime configuration.

## Storage decision

Native Qdrant storage remains **operator-managed runtime state** at the location selected by the local Qdrant configuration. P-RUNTIME-04 does not migrate, copy, delete, or reinterpret that storage.

Qdrant vector/search state remains derived runtime state under SGOKB's existing safety model; canonical Knowledge remains SQLite-owned. Startup/recovery automation therefore must not introduce any write path to canonical SQLite and must not make Qdrant a canonical backup authority.

Before changing Qdrant versions or storage layout, operators must protect runtime state using the Qdrant-supported snapshot/backup path appropriate to the installed version. A binary downgrade must not be treated as a safe rollback against storage already migrated by a newer Qdrant version.

## Auto-start decision

Phase P targets availability **after Windows login**, not a pre-login machine service.

Windows Task Scheduler is the reference outer lifecycle owner. The repository provides:

- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1` — deterministic task registration/update;
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1` — task-contract and `/readyz` verification;
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md` — operational and acceptance procedure;
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md` — crash-recovery correction.

Login completion is not itself a readiness guarantee. Consumers continue to use the P-RUNTIME-03 shared runtime-health contract, whose Qdrant readiness authority is `/readyz` and whose lifecycle actions remain disabled.

## Failure / recovery semantics

### Startup

`AtLogOn` starts Qdrant immediately after the configured user signs in.

### Process-exit recovery

A second trigger on the same task is a repeating time trigger. While Qdrant is running, the task state is `Running`, so `MultipleInstances=IgnoreNew` suppresses each recovery pulse. If `qdrant.exe` exits unexpectedly, the task returns to `Ready`; the next recovery pulse can launch a replacement process.

This mechanism was selected because reference-host testing showed that `RestartOnFailure` did not relaunch Qdrant after a forced termination of an already-running process, even with the principal corrected to Interactive / InteractiveToken.

### RestartOnFailure

`RestartOnFailure` remains configured as a best-effort fallback for task/action start failures. It is not the acceptance authority for long-running process crash recovery.

### Hung/unready process

The repeating trigger does not replace a process that remains running but fails `/readyz`; `IgnoreNew` intentionally suppresses duplicate launches. Broader hung/readiness-failure recovery belongs to P-RUNTIME-06 unless a later accepted design changes this boundary.

## Intentional maintenance semantics

A repeating recovery trigger means `Stop-ScheduledTask` alone is not a durable maintenance stop. Operators must disable the task before stopping it:

```text
Disable task -> stop task -> maintenance -> enable task -> start task -> verify /readyz
```

This is an operator-owned Windows lifecycle action, not an SGOKB Application operation.

## Upgrade / rollback decision

Native Qdrant upgrades are operator-controlled changes, not SGOKB self-update actions.

Required rules:

1. do not let SGOKB silently replace `qdrant.exe`;
2. record the installed Qdrant version used for an accepted environment;
3. protect Qdrant runtime state before an upgrade;
4. preserve the scheduled-task executable/arguments/working-directory contract or re-register it explicitly;
5. preserve both accepted triggers and the Interactive principal;
6. wait for `/readyz` after the change;
7. verify SGOKB runtime health and collection/generation state;
8. do not define rollback as merely starting an older binary against possibly migrated storage.

## Docker / Compose disposition

P-RUNTIME-02 created and accepted a reproducible Docker Compose profile before the native-Windows deployment correction was supplied. Those artifacts are retained as optional Docker/development assets and historical evidence.

```text
runtime/qdrant/compose.yaml and .env.example = retained optional Docker/development profile
P-RUNTIME-02 historical acceptance          = retained
Phase P Windows reference runtime           = native qdrant.exe + Task Scheduler
P-RUNTIME-04 login/recovery authority        = native Windows only
```

Docker Desktop is not a prerequisite for the supported Windows path.

## Rejected Windows lifecycle alternatives

| Alternative | Disposition | Primary reason |
|---|---|---|
| Native Qdrant + Task Scheduler AtLogOn + repeating recovery trigger | **Selected** | OS-owned startup and process-exit recovery without making SGOKB a supervisor |
| RestartOnFailure-only supervision | Rejected as crash authority | failed twice on the supported reference host |
| Persistent PowerShell supervisor | Rejected | adds another long-running supervisor process and maintenance boundary |
| Native Qdrant + Windows service wrapper | Rejected | adds privileged third-party lifecycle dependency |
| GUI/CLI launches Qdrant | Rejected | violates accepted external-runtime ownership boundary |
| Startup folder / ad-hoc shortcut | Rejected | weak recovery, diagnostics, and deterministic configuration semantics |
| Docker Desktop / Compose | Optional profile, not Windows reference | does not match the actual supported local deployment |
| WSL distro + systemd | Rejected | additional distro/startup/network/filesystem operational boundary |

## OSS / third-party installation boundary

SGOKB does not bundle or automatically install the Qdrant server binary.

Repository responsibility:

- Task Scheduler registration/verification assets;
- expected startup/recovery/readiness contract;
- SGOKB-side health/status reporting;
- troubleshooting and acceptance procedure.

Operator responsibility:

- install and version-control the native Qdrant binary operationally;
- provide the real `qdrant.exe` path, arguments, working directory, and storage/configuration choices;
- satisfy Qdrant third-party terms;
- administer Windows security policy and Task Scheduler permissions;
- protect Qdrant runtime state before upgrade/recovery work.

## Consequences for subsequent tasks

### P-RUNTIME-02

Remains **Complete / Accepted** as historical Compose/configuration work. Its assets remain an optional Docker/development profile.

### P-RUNTIME-03

Remains valid without semantic changes: it models Qdrant as an external runtime and exposes readiness/version/collection state without lifecycle ownership.

### P-RUNTIME-04

Owns native Task Scheduler registration, login ordering, repeating process-exit recovery, `/readyz` retry behavior, troubleshooting, and no-manual-action reference-host acceptance.

### P-GUI-09 / P-RUNTIME-05

GUI surfaces may show runtime health and troubleshooting entry points, but must not become the Qdrant supervisor.

## Authority

Historical comparison:

- `docs/evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md`

Amended native Windows runtime:

- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`

Task authority:

- `docs/planning/phases/P/PHASE_P_TASKS.md`
- `docs/planning/phases/P/P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`

This amendment does not invalidate P-RUNTIME-03's external lifecycle boundary.
