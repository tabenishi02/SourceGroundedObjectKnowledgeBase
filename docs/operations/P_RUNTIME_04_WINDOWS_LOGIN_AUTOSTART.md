# P-RUNTIME-04 — Windows Login Auto-start Integration

Date: 2026-10-31
Status: **Crash-recovery remediation implemented / repository acceptance and device retest pending**
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`

## 1. Purpose

This procedure is the Phase P Windows operational authority for a Qdrant server that runs **directly on the local Windows host as `qdrant.exe`**.

Target behavior:

```text
Windows sign-in
  -> Windows Task Scheduler starts native qdrant.exe
  -> Qdrant /readyz becomes HTTP 200
  -> SGOKB system.status.runtime_health reports Qdrant healthy

Unexpected qdrant.exe exit
  -> next Task Scheduler recovery pulse
  -> native qdrant.exe starts again
  -> /readyz returns HTTP 200
```

No Docker runtime is required for this Windows path. The earlier P-RUNTIME-02 Compose assets remain an optional Docker/development profile only.

## 2. Lifecycle ownership boundary

```text
Qdrant binary installation      = operator-owned
Qdrant process startup/recovery = Windows Task Scheduler-owned
Qdrant storage/configuration    = operator-owned native Qdrant runtime state
SGOKB CLI / GUI / MCP           = client / observer only
SGOKB start/stop/restart Qdrant = forbidden by the accepted Application boundary
Readiness authority             = GET http://127.0.0.1:6333/readyz -> HTTP 200
```

The GUI must not become a hidden process supervisor. P-RUNTIME-03 remains the shared observation boundary.

## 3. Crash-recovery remediation

The original implementation relied on Task Scheduler `RestartOnFailure` to recover an already-running Qdrant process after an external force termination. Reference-host testing showed that this did not restart Qdrant, including after the task principal was corrected to Interactive / InteractiveToken.

The accepted remediation design is documented in:

- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`

The task now contains two triggers:

```text
Trigger A = AtLogOn for the configured interactive user
Trigger B = repeating time trigger / recovery pulse
            default interval = 60 seconds
            finite duration  = none (indefinite)
```

`MultipleInstances=IgnoreNew` makes the recovery pulse safe while Qdrant is healthy:

```text
Qdrant task Running
  -> recovery pulse
  -> IgnoreNew
  -> no duplicate qdrant.exe
```

After an unexpected process exit the task returns to `Ready`, so the next recovery pulse starts a new instance.

`RestartOnFailure` remains configured only as a best-effort retry for task/action start failures. It is not the authoritative long-running process crash supervisor.

## 4. Repository assets

```text
runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1
runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1
tests/test_p_runtime_04_windows_login_autostart.py
docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md
```

Default scheduled-task identity:

```text
TaskPath = \SGOKB\
TaskName = Qdrant
```

The registration script creates the `\SGOKB\` Task Scheduler folder if it does not yet exist.

## 5. Prerequisites

Before registration, verify:

1. native Qdrant is already installed;
2. the exact `qdrant.exe` path is known;
3. required Qdrant arguments/configuration are known;
4. the existing working directory and storage configuration are known and preserved;
5. the same native configuration can reach `http://127.0.0.1:6333/readyz`;
6. port 6333 is not owned by an unrelated process.

P-RUNTIME-04 does not download Qdrant, choose a storage path, migrate storage, or invent command-line arguments.

## 6. Register or update the task

Open PowerShell as the Windows user that will run SGOKB. Elevation is not part of the runtime contract, although local security policy may require elevation to register or inspect Task Scheduler entries.

Example:

```powershell
$QdrantExe = 'C:\path\to\qdrant.exe'
$QdrantArgs = '--config-path C:\path\to\qdrant.yaml --disable-telemetry'
$WorkingDirectory = 'C:\path\to\qdrant-working-directory'

.\runtime\qdrant\windows\Register-SgokbQdrantAutoStart.ps1 `
  -QdrantExe $QdrantExe `
  -QdrantArguments $QdrantArgs `
  -WorkingDirectory $WorkingDirectory `
  -RecoveryIntervalSeconds 60 `
  -StartNow
```

If a manually launched Qdrant already owns port 6333, stop that manual instance before `-StartNow` so the scheduled task becomes the lifecycle owner.

The registration is idempotent for `\SGOKB\Qdrant`; `-Force` replaces the task definition while leaving Qdrant binaries, configuration, and storage untouched.

## 7. Accepted task settings

The registration script creates a direct `qdrant.exe` action with:

```text
Startup trigger          = AtLogOn for current Windows user
Crash-recovery trigger   = repeating time trigger
Recovery interval        = 60 seconds by default
Recovery duration        = indefinite
Principal logon type     = Interactive
Run level                = Limited
RestartOnFailure         = retained start/action-failure fallback
Restart attempts         = 10 by default
Restart interval         = 60 seconds by default
Multiple instances       = IgnoreNew
Execution time limit     = unlimited
Start when available     = enabled
Battery start/continue   = allowed
```

Windows Task Scheduler repetition and restart intervals have a one-minute minimum in this contract, so values below 60 seconds are rejected by the registration script.

The task still executes `qdrant.exe` directly. It does not invoke SGOKB, the GUI, Docker, Compose, `cmd.exe`, or a persistent PowerShell supervision loop in the production path.

## 8. Verify without reboot

Inspect the task:

```powershell
$Task = Get-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'

$Task.Principal | Format-List UserId,LogonType,RunLevel
$Task.Triggers | Format-List *
$Task.Settings | Format-List MultipleInstances,RestartCount,RestartInterval,ExecutionTimeLimit,StartWhenAvailable
```

Run the repository verifier:

```powershell
.\runtime\qdrant\windows\Test-SgokbQdrantAutoStart.ps1 `
  -ExpectedQdrantExe $QdrantExe `
  -ExpectedRecoveryIntervalSeconds 60
```

A successful result is JSON containing:

```text
schema_version              = sgokb.qdrant-windows-autostart-check/1.1
principal_logon_type        = Interactive
trigger_count               = 2
recovery_interval_seconds   = 60
ready_status                = 200
```

Also confirm the SGOKB observation path:

```powershell
.\.venv\Scripts\sgokb.exe --db <DB_PATH> system status
```

Expected Qdrant projection:

```text
data.runtime_health.components.qdrant.status = healthy
```

## 9. Reboot/login acceptance procedure

The supported host has already produced a successful reboot/sign-in observation for P-RUNTIME-04. After this remediation is installed, the login path must remain intact.

For any formal recheck:

1. verify `\SGOKB\Qdrant` exists and the verifier reports both triggers;
2. verify Qdrant is ready before reboot;
3. restart Windows normally;
4. sign in as the task user;
5. do not manually launch Qdrant, SGOKB GUI, Docker, or another Qdrant shortcut;
6. run `Test-SgokbQdrantAutoStart.ps1`;
7. require `/readyz` HTTP 200;
8. require SGOKB `system status` to report Qdrant healthy.

A brief unavailable/degraded startup interval is allowed. The readiness authority is eventual `/readyz` HTTP 200.

## 10. Unexpected process-stop recovery acceptance

This is the remaining P-RUNTIME-04 reference-host gate after repository remediation.

1. Begin from scheduled-task-managed Qdrant with `/readyz` HTTP 200.
2. Confirm the task reports `Running` and record the current Qdrant PID.
3. Force-terminate only the Qdrant process, for example:

```powershell
$OldPid = (Get-Process qdrant).Id
Stop-Process -Id $OldPid -Force
```

4. Do **not** run `Start-ScheduledTask`.
5. Wait one configured recovery interval plus normal Qdrant startup time.
6. Confirm a new process exists and its PID differs from `$OldPid`.
7. Require `/readyz` HTTP 200.
8. Run `Test-SgokbQdrantAutoStart.ps1` and SGOKB `system status`.
9. Require Qdrant runtime health to return to healthy.

Expected default recovery begins at the next 60-second recovery pulse. The exact wall-clock delay depends on where the process exit occurs within the pulse interval plus Qdrant startup time.

This test validates process-exit recovery only. A Qdrant process that remains alive but is hung/unready is outside this remediation and is reserved for broader P-RUNTIME-06 failure/recovery acceptance.

## 11. Intentional maintenance

Because the task now has an indefinite recovery pulse, `Stop-ScheduledTask` alone is **not** a durable maintenance stop. The next pulse may start Qdrant again.

For intentional maintenance:

```powershell
Disable-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
Stop-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant' -ErrorAction SilentlyContinue
```

Perform maintenance, then:

```powershell
Enable-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
Start-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'

Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

Disabling the scheduled task is an operator-owned lifecycle action. It does not add SGOKB Application lifecycle operations.

## 12. Startup ordering and retry behavior

```text
Windows user session
  -> Task Scheduler AtLogOn
  -> qdrant.exe
  -> /readyz
  -> SGOKB clients

Task Scheduler recovery pulse every N seconds
  -> if task Running: IgnoreNew
  -> if task Ready: launch qdrant.exe
```

There is no Docker Engine dependency and no SGOKB-before-Qdrant ordering dependency. SGOKB clients must tolerate temporary Qdrant unavailability and use the P-RUNTIME-03 health projection.

## 13. Troubleshooting

### Task does not contain two triggers

Re-register with the current repository script, then run the verifier. A valid remediated task contains exactly one logon trigger and one repeating time trigger.

### Principal is S4U instead of Interactive

Re-register with the current repository script. The accepted principal is `Interactive` / `InteractiveToken`, `Limited` run level.

### Task exists but crash recovery does not occur

Inspect:

```powershell
$Task = Get-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
$Task.Triggers | Format-List *
Get-ScheduledTaskInfo -TaskPath '\SGOKB\' -TaskName 'Qdrant' | Format-List *
Export-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
```

Require a time trigger with a repetition interval matching `RecoveryIntervalSeconds` and no finite repetition duration.

Enable/inspect **Event Viewer -> Applications and Services Logs -> Microsoft -> Windows -> TaskScheduler -> Operational** if additional scheduler diagnostics are required.

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

Do not launch a second Qdrant instance to work around the conflict.

### Process exists but `/readyz` is not 200

Check native Qdrant logs/configuration and storage state. Process existence is not acceptance evidence. The recovery pulse intentionally does not replace a still-running process; broader hung/unready recovery belongs to P-RUNTIME-06.

## 14. Removal

Disable and stop first if Qdrant is running:

```powershell
Disable-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant'
Stop-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant' -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskPath '\SGOKB\' -TaskName 'Qdrant' -Confirm:$false
```

Unregistering the task does **not** delete Qdrant binaries or storage.

## 15. Safety boundary

P-RUNTIME-04 changes only Qdrant process lifecycle integration. It must not:

- mutate canonical SGOKB SQLite data;
- move/delete Qdrant storage;
- install or upgrade Qdrant automatically;
- expose Qdrant ports beyond the local configuration;
- add GUI/CLI start/stop/restart actions;
- redefine Qdrant as canonical Knowledge storage.

## 16. Acceptance boundary

Repository Windows CI must prove the remediated trigger contract and a disposable process-exit recovery cycle. It cannot substitute for the physical reference-host test against the actual Qdrant process/configuration/storage.

P-RUNTIME-04 may be marked `Complete / Accepted` only after:

1. reboot -> login -> Qdrant `/readyz` HTTP 200 without manual launch remains accepted;
2. the remediated repeating recovery pulse restarts Qdrant after unexpected process exit without manual restart;
3. `/readyz` and SGOKB runtime health return to healthy.

Until Gate 2 is re-run successfully on the reference host, P-RUNTIME-04 remains **In Progress / Remediation acceptance pending**.

## 17. Authority

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`
