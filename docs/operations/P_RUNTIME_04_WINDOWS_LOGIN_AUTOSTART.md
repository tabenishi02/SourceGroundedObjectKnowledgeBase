# P-RUNTIME-04 — Windows Login Auto-start Integration

Date: 2026-10-31
Status: **Implementation Complete / Device Acceptance Pending**
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`

## 1. Purpose

This procedure is the Phase P Windows operational authority for a Qdrant server that runs **directly on the local Windows host as `qdrant.exe`**.

The target behavior is:

```text
Windows sign-in
  -> Windows Task Scheduler starts native qdrant.exe
  -> Qdrant /readyz becomes HTTP 200
  -> SGOKB system.status.runtime_health reports Qdrant healthy
```

No Docker runtime is required for this Windows path. The earlier P-RUNTIME-02 Compose assets remain an optional Docker/development profile only.

## 2. Lifecycle ownership boundary

```text
Qdrant binary installation      = operator-owned
Qdrant process startup/restart  = Windows Task Scheduler-owned
Qdrant storage/configuration    = operator-owned native Qdrant runtime state
SGOKB CLI / GUI / MCP           = client / observer only
SGOKB start/stop/restart Qdrant = forbidden by the accepted Application boundary
Readiness authority             = GET http://127.0.0.1:6333/readyz -> HTTP 200
```

The GUI must not become a hidden process supervisor. P-RUNTIME-03 remains the shared observation boundary.

## 3. Repository assets

```text
runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1
runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1
tests/test_p_runtime_04_windows_login_autostart.py
```

Default scheduled-task identity:

```text
TaskPath = \SGOKB\
TaskName = Qdrant
```

The registration script creates the `\SGOKB\` Task Scheduler folder if it does not yet exist.

## 4. Prerequisites

Before registration, verify all of the following once:

1. native Qdrant is already installed;
2. the exact `qdrant.exe` path is known;
3. any required Qdrant arguments/configuration are known;
4. the existing working directory and storage configuration are known and preserved;
5. launching that same native configuration manually reaches `http://127.0.0.1:6333/readyz`;
6. port 6333 is not owned by an unrelated process.

P-RUNTIME-04 does not download Qdrant, choose a storage path, migrate storage, or invent command-line arguments.

## 5. Register the auto-start task

Open PowerShell as the Windows user that will run SGOKB. Elevation is not part of the contract, but local security policy may require it to register Task Scheduler entries.

Set the real native binary path:

```powershell
$QdrantExe = 'C:\path\to\qdrant.exe'
$QdrantArgs = ''
```

If a manually launched Qdrant instance is currently using the same endpoint, stop that manual instance before using `-StartNow`; the scheduled task must become the process owner rather than creating a second server competing for port 6333.

Register/update the task and start it immediately for an initial readiness check:

```powershell
.\runtime\qdrant\windows\Register-SgokbQdrantAutoStart.ps1 `
  -QdrantExe $QdrantExe `
  -QdrantArguments $QdrantArgs `
  -StartNow
```

If the Qdrant working directory is not the executable directory, pass it explicitly:

```powershell
-WorkingDirectory 'C:\path\to\qdrant-working-directory'
```

The registration is idempotent for `\SGOKB\Qdrant`; `-Force` replaces the task definition while leaving Qdrant storage untouched.

## 6. Accepted task settings

The registration script creates a direct `qdrant.exe` action with:

```text
Trigger                = AtLogOn for the current Windows user
Principal logon type   = Interactive
Run level              = Limited
Restart on failure     = enabled
Restart attempts       = 10 by default
Restart interval       = 60 seconds by default
Multiple instances     = IgnoreNew
Execution time limit   = unlimited
Start when available   = enabled
Battery start/continue = allowed
```

Windows Task Scheduler requires restart intervals of at least one minute, so values below 60 seconds are rejected by the script.

The task directly executes `qdrant.exe`. It does not invoke SGOKB, the GUI, Docker, Compose, `cmd.exe`, or a persistent PowerShell runtime wrapper as the production supervisor.

## 7. Verify without reboot

Inspect the task:

```powershell
Get-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant' |
  Format-List TaskName,TaskPath,State,Actions,Triggers,Settings
```

Run the repository verifier:

```powershell
.\runtime\qdrant\windows\Test-SgokbQdrantAutoStart.ps1 `
  -ExpectedQdrantExe $QdrantExe
```

A successful result is JSON with:

```text
schema_version = sgokb.qdrant-windows-autostart-check/1.0
ready_status   = 200
```

Also confirm the shared SGOKB observation path:

```powershell
.\.venv\Scripts\sgokb.exe --db <DB_PATH> system status
```

Expected Qdrant projection:

```text
data.runtime_health.components.qdrant.status = healthy
```

## 8. Reboot/login acceptance procedure

This is the P-RUNTIME-04 completion gate and must be executed on the actual supported Windows machine.

### A. Pre-reboot state

1. Verify `\SGOKB\Qdrant` exists.
2. Verify Qdrant is ready.
3. Record the current Qdrant version from runtime health or the root endpoint.
4. Do not intentionally disable or stop the scheduled task before reboot.

### B. Reboot and sign in

Restart Windows normally, then sign in as the user bound to the task. Do not manually launch Qdrant, SGOKB GUI, Docker, or a Qdrant shortcut.

### C. Verify readiness

From the repository root:

```powershell
.\runtime\qdrant\windows\Test-SgokbQdrantAutoStart.ps1 `
  -ExpectedQdrantExe $QdrantExe `
  -ReadyTimeoutSeconds 120
```

Then verify:

```powershell
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

Acceptance requires HTTP 200 with no manual Qdrant launch after sign-in.

### D. Verify SGOKB observation

Run `system status` and confirm the Qdrant component is healthy. A short startup interval where the component is unavailable/degraded is allowed; login completion itself is not the readiness authority. The final state within the acceptance timeout must be ready.

## 9. Unexpected process-stop recovery acceptance

This check validates Task Scheduler's restart-on-failure behavior. It is intentionally different from an operator-requested `Stop-ScheduledTask`.

1. Confirm Qdrant is ready and the task is running.
2. Record the current Qdrant process ID.
3. Terminate the Qdrant process unexpectedly, for example with `Stop-Process -Id <PID> -Force`.
4. Do not invoke `Start-ScheduledTask` manually.
5. Allow at least the configured restart interval plus normal Qdrant startup time.
6. Run `Test-SgokbQdrantAutoStart.ps1`.
7. Confirm `/readyz` returns HTTP 200 again and that a new Qdrant process exists.

Expected default recovery begins after the 60-second Task Scheduler restart interval. P-RUNTIME-04 does not require sub-minute crash recovery because Windows Task Scheduler does not support a shorter restart-on-failure interval.

An intentional `Stop-ScheduledTask` is maintenance, not a crash-recovery test. Restart it explicitly when maintenance is complete.

## 10. Startup ordering and retry behavior

The startup order is deliberately minimal:

```text
Windows user session
  -> Task Scheduler
  -> qdrant.exe
  -> Qdrant local ports/storage
  -> /readyz
  -> SGOKB clients
```

There is no Docker Engine dependency and no SGOKB-before-Qdrant ordering dependency. SGOKB clients must tolerate Qdrant being temporarily unavailable and use the P-RUNTIME-03 health projection rather than assuming readiness from process existence.

Both repository scripts poll `/readyz` where readiness is required; they do not treat process creation or Windows sign-in completion as sufficient readiness evidence.

## 11. Troubleshooting

### Task does not exist

```powershell
Get-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
```

Re-run the registration script with the real executable path.

### Task exists but is not running

```powershell
Get-ScheduledTaskInfo -TaskPath '\SGOKB\' -TaskName 'Qdrant' |
  Format-List LastRunTime,LastTaskResult,NextRunTime,NumberOfMissedRuns
```

Inspect **Event Viewer -> Applications and Services Logs -> Microsoft -> Windows -> TaskScheduler -> Operational** for start/action failures.

### Wrong executable or working directory

```powershell
(Get-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant').Actions
```

Re-register with the correct `-QdrantExe`, `-QdrantArguments`, and `-WorkingDirectory` values.

### Port 6333 conflict

```powershell
Get-NetTCPConnection -LocalPort 6333 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Resolve the conflicting process or align the Qdrant/SGOKB endpoint configuration. Do not launch a second Qdrant instance to work around the conflict.

### Process exists but `/readyz` is not 200

Check native Qdrant logs/configuration and storage state. Process existence is not acceptance evidence.

### Task repeatedly restarts

Treat this as a Qdrant startup/runtime failure, not proof that auto-start works. Inspect `LastTaskResult`, Task Scheduler history, native Qdrant logs, configuration, storage permissions, and port conflicts before increasing the retry count.

## 12. Intentional maintenance / removal

Stop the scheduled task only for intentional maintenance:

```powershell
Stop-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
```

Start it again:

```powershell
Start-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
```

Remove only the auto-start definition:

```powershell
Unregister-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant' -Confirm:$false
```

Unregistering the task does **not** delete Qdrant binaries or storage.

## 13. Safety boundary

P-RUNTIME-04 changes only Qdrant process lifecycle integration. It must not:

- mutate canonical SGOKB SQLite data;
- move/delete Qdrant storage;
- install or upgrade Qdrant automatically;
- expose Qdrant ports beyond the local configuration;
- add GUI/CLI start/stop/restart actions;
- redefine Qdrant as canonical Knowledge storage.

## 14. Acceptance boundary

Repository/Windows-runner acceptance can prove that the Task Scheduler assets are syntactically valid, register correctly, and preserve the intended contract. It **cannot** prove a real machine reboot/login sequence.

P-RUNTIME-04 may be marked `Complete / Accepted` only after the actual supported Windows machine passes both:

1. reboot -> login -> Qdrant `/readyz` HTTP 200 without manual launch;
2. unexpected Qdrant process failure -> Task Scheduler restart -> `/readyz` HTTP 200 without manual restart.

Until those device checks are recorded, the task remains **Implementation Complete / Device Acceptance Pending**.

## 15. Authority

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`
