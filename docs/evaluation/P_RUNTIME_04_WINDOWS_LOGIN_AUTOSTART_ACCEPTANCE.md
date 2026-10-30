# P-RUNTIME-04 — Windows Login Auto-start Acceptance

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Disposition: **Reference-host Accepted / Repository remediation CI pending**

## 1. Acceptance objective

P-RUNTIME-04 removes the need to launch Qdrant manually after Windows sign-in and requires automatic recovery after an unexpected native Qdrant process exit.

Completion intent:

1. normal Windows restart/sign-in -> `/readyz` HTTP 200 without manual Qdrant launch;
2. unexpected `qdrant.exe` exit -> Windows-owned automatic recovery -> new process -> `/readyz` HTTP 200 -> SGOKB runtime health returns Qdrant `healthy` without manual restart.

## 2. Current Windows runtime authority

```text
Windows reference runtime       = native qdrant.exe
Lifecycle owner                 = Windows Task Scheduler
Login startup trigger           = AtLogOn
Crash recovery trigger          = repeating time trigger
Default recovery interval       = 60 seconds
Recovery repetition duration    = indefinite
Duplicate suppression           = MultipleInstances=IgnoreNew
RestartOnFailure                = start/action-failure fallback only
Principal                       = Interactive / Limited
Qdrant readiness authority      = GET /readyz -> HTTP 200
SGOKB runtime lifecycle role    = client / observer only
Docker Compose                  = optional/development profile only
```

Authorities:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`

P-RUNTIME-03 remains unchanged. Qdrant is externally owned and SGOKB observes it through `system.status.runtime_health` without exposing start/stop/restart actions.

## 3. Original repository baseline

Original Windows CI run `41091876482 (#43)` accepted the first native Task Scheduler implementation:

```text
runner                             = Microsoft Windows Server 2025
Python                             = 3.10.11
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
synthetic /readyz                  = HTTP 200
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff                               = PASS
full repository regression         = 857 / 857 PASS
```

That result proved the original repository assets registered correctly, but it did not prove real-host crash recovery.

## 4. Reference-host Gate 1 — reboot / sign-in

**Status: PASS**

The supported Windows workstation was restarted and Qdrant started automatically after user sign-in without a manual Qdrant launch.

```text
Windows restart
  -> sign-in
  -> Task Scheduler launches native qdrant.exe
  -> Qdrant available

Gate 1 = PASS
```

## 5. Historical Gate 2 failure — RestartOnFailure-only attempt A

**Status: FAIL / historical evidence retained**

The first real-host crash test used a task that had drifted to `LogonType=S4U`. Qdrant was healthy before the test. After force-terminating the process, no replacement process appeared and `/readyz` did not recover.

Because S4U did not match the repository contract, the task was re-registered before drawing the root-cause conclusion.

## 6. Historical Gate 2 failure — RestartOnFailure-only attempt B

**Status: FAIL / root-cause evidence accepted**

The task was re-registered through the repository script with:

```text
LogonType = Interactive / InteractiveToken
RunLevel  = Limited
RestartOnFailure.Count    = 10
RestartOnFailure.Interval = PT1M
```

Before termination:

```text
qdrant.exe    = running
port 6333     = LISTEN
/readyz       = HTTP 200 / all shards are ready
```

After force termination, more than one configured restart interval elapsed with:

```text
qdrant.exe     = absent
/readyz        = unavailable
Task state     = Ready
LastRunTime    = unchanged
LastTaskResult = 0xFFFFFFFF
```

No manual `Start-ScheduledTask` was issued during the failed recovery observation.

Accepted conclusion:

```text
RestartOnFailure-only long-running-process crash supervision = REJECTED
```

The earlier S4U mismatch was real but was not the crash-recovery root cause because the failure reproduced with the accepted Interactive principal.

## 7. Crash-recovery remediation

Selected design:

```text
single task: \SGOKB\Qdrant

Trigger A = AtLogOn
Trigger B = repeating time trigger / recovery pulse
            interval = 60 seconds by default
            duration = indefinite

Action    = qdrant.exe directly
Principal = Interactive / Limited
Policy    = MultipleInstances=IgnoreNew
```

While the task is Running, recovery pulses are ignored. After an unexpected process exit, the task becomes Ready and the next pulse launches a new instance.

`RestartOnFailure` is retained only as a task/action start-failure fallback.

Verifier schema:

```text
sgokb.qdrant-windows-autostart-check/1.1
```

## 8. Remediated reference-host registration — PASS

The supported workstation re-registered `\SGOKB\Qdrant` from the remediation branch with the actual runtime configuration:

```text
Executable        = C:\codex\SourceGroundedObjectKnowledgeBase\.local\qdrant-1.19.2\qdrant.exe
Arguments         = --config-path C:\Qdrant\SGOKB\qdrant.yaml --disable-telemetry
WorkingDirectory  = C:\Qdrant\SGOKB
Principal         = Interactive / Limited
Trigger count     = 2
Recovery interval = PT1M / 60 seconds
Restart fallback  = 10 attempts / PT1M
```

The repository verifier returned:

```text
schema_version            = sgokb.qdrant-windows-autostart-check/1.1
task_path                 = \SGOKB\Qdrant
task_state                = Running
principal_logon_type      = Interactive
trigger_count             = 2
recovery_interval         = PT1M
recovery_interval_seconds = 60
ready_status              = 200
```

**Registration / pre-crash verification = PASS**

## 9. Remediated reference-host Gate 2 — PASS

The running Qdrant process was force-terminated. No manual `Start-ScheduledTask` was issued afterward.

The next scheduled recovery pulse created a replacement Qdrant process:

```text
recovered qdrant.exe PID = 41480
Task LastRunTime          = 2026-10-31 04:03:27 +09:00
Task LastTaskResult       = 267009 / 0x41301 / task running
Task NextRunTime          = 2026-10-31 04:04:26 +09:00
```

The recovered process reached:

```text
GET http://127.0.0.1:6333/readyz
StatusCode = 200
Content    = all shards are ready
```

SGOKB then observed:

```text
command                                      = system.status
runtime_health.components.qdrant.status      = healthy
runtime_health.components.qdrant.ready       = true
runtime_health.components.qdrant.version     = 1.19.2
runtime_health.lifecycle.qdrant_owner         = external
runtime_health.lifecycle.observe              = true
runtime_health.lifecycle.start/stop/restart   = false / false / false
```

The top-level runtime health was `degraded` only because unrelated generation and derived-state components were degraded. The Qdrant component itself was healthy and ready, so those unrelated conditions do not fail P-RUNTIME-04.

Therefore:

```text
reference-host Gate 2 automatic process recovery = PASS
reference-host Gate 2 /readyz recovery           = PASS
reference-host Gate 2 SGOKB Qdrant health        = PASS
reference-host Gate 2 overall                     = PASS
```

## 10. Reference-host acceptance disposition

```text
Gate 1 reboot -> sign-in -> automatic Qdrant start        = PASS
Gate 2 forced qdrant.exe exit -> automatic new process    = PASS
Gate 2 recovered /readyz                                  = PASS
Gate 2 recovered SGOKB qdrant health                      = PASS

P-RUNTIME-04 reference-host acceptance                    = Complete / Accepted
```

No further physical-host lifecycle gate is required for P-RUNTIME-04.

## 11. Remediated repository CI status

**Status: PENDING / Windows runner infrastructure blocked**

The remediation workflow was strengthened to prove the repeating-trigger mechanism using a disposable long-running scheduled worker. It must:

1. register the remediated task;
2. verify both triggers and the recovery interval;
3. start the worker and record its PID;
4. force-terminate the worker;
5. avoid any second manual `Start-ScheduledTask`;
6. require the next recovery pulse to create a different live PID;
7. run focused P-RUNTIME tests, Ruff, and full regression.

Multiple remediation workflow attempts, including the latest remediation HEAD, ended before runner assignment with:

```text
runner_id = 0
steps     = []
```

These are infrastructure/runner-start failures, not executed product/test failures. They also do not constitute repository acceptance evidence.

Repository remediation CI therefore remains the only unresolved P-RUNTIME-04 acceptance item.

## 12. Maintenance change

Because the remediated task has an indefinite recovery pulse, intentional maintenance must disable the task before stopping it:

```text
Disable task
-> Stop task
-> maintenance
-> Enable task
-> Start task
```

`Stop-ScheduledTask` alone is not a durable maintenance stop because a later recovery pulse may start the task again.

## 13. Safety boundary

P-RUNTIME-04 does not:

- install or upgrade Qdrant;
- choose or migrate Qdrant storage;
- mutate canonical SGOKB SQLite data;
- make GUI/CLI/MCP a Qdrant process supervisor;
- add public start/stop/restart operations to P-RUNTIME-03;
- redefine Qdrant as canonical Knowledge storage.

The recovery pulse covers process exit only. Recovery from a Qdrant process that remains alive but is hung/unready remains broader P-RUNTIME-06 scope.

## 14. Current disposition

```text
native Windows design correction                    = Complete / Accepted
original repository implementation                  = Complete / Accepted
reference-host Gate 1 reboot/sign-in                = PASS
historical RestartOnFailure attempt A               = FAIL / evidence retained
historical Interactive attempt B                    = FAIL / root-cause evidence retained
crash-recovery remediation design                   = Complete
remediated repository implementation                = Complete on PR #81
remediated reference-host Gate 2                    = Complete / Accepted
remediated Windows CI                               = Pending / runner infrastructure blocked

P-RUNTIME-04 reference-host side                    = Complete / Accepted
P-RUNTIME-04 overall                                = In Progress / Repository CI Pending
P-RUNTIME-05                                        = blocked until formal repository acceptance
```

The historical Gate 2 failures remain part of the acceptance record because they explain why the recovery contract changed from RestartOnFailure-only to a repeating recovery trigger.
