# P-RUNTIME-04 — Windows Login Auto-start Acceptance

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Disposition: **Crash-recovery remediation in progress / Reference-host Gate 2 retest pending**

## 1. Acceptance objective

P-RUNTIME-04 removes the need to launch Qdrant manually after Windows sign-in for the supported deployment where Qdrant runs directly on the local Windows host as `qdrant.exe`.

Completion requires both:

1. normal Windows restart/sign-in -> `/readyz` HTTP 200 without manual Qdrant launch;
2. unexpected Qdrant process exit -> automatic Windows-owned recovery -> `/readyz` HTTP 200 without manual restart.

## 2. Deployment correction and authority

The original P-RUNTIME-01 decision selected Docker Desktop / WSL 2 + Docker Compose. During P-RUNTIME-04 execution the supported deployment constraint was corrected: the actual Windows runtime is native Qdrant, not Docker.

A second correction was required after reference-host crash testing: Task Scheduler `RestartOnFailure` did not restart an already-running Qdrant process after force termination. The amended recovery authority is a repeating time trigger on the same scheduled task, with `MultipleInstances=IgnoreNew` suppressing duplicate launches while Qdrant is healthy.

Current authority:

```text
Windows reference runtime       = native qdrant.exe
Lifecycle owner                 = Windows Task Scheduler
Login startup trigger           = AtLogOn
Crash recovery trigger          = repeating time trigger
Default recovery interval       = 60 seconds
Duplicate suppression           = MultipleInstances=IgnoreNew
RestartOnFailure                = start/action-failure fallback only
Qdrant readiness authority      = GET /readyz -> HTTP 200
SGOKB runtime lifecycle role    = client / observer only
GUI lifecycle ownership         = none
Docker Compose                  = optional/development profile only
```

Authority documents:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`

P-RUNTIME-03 remains unchanged because its shared health contract already treats Qdrant as externally owned and observes `/readyz` without lifecycle actions.

## 3. Original repository implementation acceptance

Original implemented assets:

```text
runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1
runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1
tests/test_p_runtime_04_windows_login_autostart.py
docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md
```

Original repository CI was accepted:

```text
GitHub Actions workflow            = P-RUNTIME-04 Windows acceptance
run                                = 41091876482 (#43)
runner                             = Microsoft Windows Server 2025
Python                             = 3.10.11
verified branch HEAD               = 682f8446a3d00ab120c93fbed40a78aed3dee8e8
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
synthetic /readyz                  = HTTP 200
restart policy smoke               = 10 attempts / PT1M
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff src/tests                     = PASS
full repository regression         = 857 / 857 PASS
warnings                           = 2 known local-Qdrant warnings
```

That acceptance proved the original repository assets registered correctly. It did **not** prove real-host crash recovery.

## 4. Reference-host Gate 1 — reboot / sign-in

**Status: PASS**

The supported Windows workstation was restarted and Qdrant was observed running after sign-in without a manual Qdrant launch.

This establishes the startup portion of the contract:

```text
Windows restart
  -> sign-in
  -> Task Scheduler launches native qdrant.exe
  -> Qdrant available

Gate 1 = PASS
```

The crash-recovery remediation must preserve this behavior.

## 5. Reference-host Gate 2 — RestartOnFailure-only attempt A

**Status: FAIL**

Initial task state contained:

```text
LogonType           = S4U
RestartCount        = 10
RestartInterval     = PT1M
MultipleInstances   = IgnoreNew
ExecutionTimeLimit  = PT0S
StartWhenAvailable  = true
```

Qdrant was healthy before the test. After the Qdrant process was force-terminated, no replacement process appeared and `/readyz` did not recover. The task returned to `Ready` and did not begin a new run.

The S4U principal did not match the repository contract, so the task was re-registered before drawing the final root-cause conclusion.

## 6. Reference-host Gate 2 — RestartOnFailure-only attempt B

**Status: FAIL / ROOT-CAUSE EVIDENCE ACCEPTED**

The repository registration script was used to restore the intended principal:

```text
LogonType = Interactive / InteractiveToken
RunLevel  = Limited
```

The task XML still contained the intended fallback settings:

```text
RestartOnFailure:
  Count    = 10
  Interval = PT1M
```

Qdrant then reached:

```text
process state = running
port 6333     = LISTEN
/readyz       = HTTP 200 / all shards are ready
```

The running process was force-terminated. More than one configured 60-second interval elapsed. During the observation window:

```text
qdrant.exe    = absent
/readyz       = unavailable
Task state    = Ready
LastRunTime   = unchanged
LastTaskResult= 0xFFFFFFFF
```

No manual `Start-ScheduledTask` was issued during the failed recovery observation.

Therefore:

```text
RestartOnFailure-only long-running-process crash supervision = REJECTED
```

The S4U mismatch was real but was not the crash-recovery root cause because the failure reproduced with the accepted Interactive principal.

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

`RestartOnFailure` is retained only as a best-effort task/action start-failure fallback.

Remediation authority:

- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`

## 8. Remediated repository implementation

The repository remediation updates:

```text
runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1
runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1
tests/test_p_runtime_04_windows_login_autostart.py
.github/workflows/p-runtime-04-acceptance.yml
```

Registration changes:

- add `RecoveryIntervalSeconds`, default 60;
- keep `AtLogOn` startup trigger;
- add an indefinite repeating time trigger;
- keep the direct native executable action;
- keep Interactive / Limited principal;
- keep `MultipleInstances=IgnoreNew`;
- retain `RestartOnFailure` only as start/action-failure fallback.

Verification schema:

```text
sgokb.qdrant-windows-autostart-check/1.1
```

Verifier now requires exactly two triggers, the expected recovery interval, an indefinite repetition pattern, Interactive principal, one direct action, IgnoreNew, and `/readyz` HTTP 200.

## 9. Remediated Windows CI gate

**Status: PENDING at remediation implementation time**

The workflow must prove more than static registration. Its disposable Windows task uses a long-running worker process and must:

1. register the remediated task;
2. verify both triggers and the recovery interval;
3. start the worker through Task Scheduler;
4. record the worker PID;
5. force-terminate that worker process;
6. do not manually start the task again;
7. wait for the next recovery pulse;
8. require a different worker PID and task state `Running`;
9. then run focused tests, Ruff, and full regression.

A passing hosted CI proves the Task Scheduler mechanism against a disposable process. It does not replace the real Qdrant reference-host Gate 2 retest.

## 10. Reference-host Gate 2 retest after remediation

**Status: PENDING**

After the remediation is repository-accepted and installed on the supported workstation:

1. re-register `\SGOKB\Qdrant` with the real local `qdrant.exe`, current arguments, working directory, and default 60-second recovery interval;
2. run `Test-SgokbQdrantAutoStart.ps1` and require schema `1.1` plus `/readyz` HTTP 200;
3. record the current Qdrant PID;
4. force-terminate only that Qdrant process;
5. do not invoke `Start-ScheduledTask`;
6. wait one recovery interval plus normal Qdrant startup time;
7. require a different Qdrant PID;
8. require `/readyz` HTTP 200;
9. require SGOKB `system status` Qdrant component to return to healthy.

Only this successful retest closes Gate 2.

## 11. Maintenance change

Because the remediated task has an indefinite recovery pulse, intentional maintenance must disable the task before stopping it. `Stop-ScheduledTask` by itself is no longer a durable maintenance stop.

This does not change the SGOKB Application boundary; it is an operator-owned Windows operation.

## 12. Safety boundary

P-RUNTIME-04 does not:

- install or upgrade Qdrant;
- choose or migrate Qdrant storage;
- mutate canonical SGOKB SQLite data;
- make the GUI/CLI a Qdrant process supervisor;
- add public start/stop/restart operations to P-RUNTIME-03;
- redefine Qdrant as canonical Knowledge storage.

The recovery pulse covers process exit only. It does not claim recovery from a Qdrant process that remains alive but is hung/unready; that broader behavior remains for P-RUNTIME-06.

## 13. Current disposition

```text
native Windows design correction                    = Complete / Accepted
original repository implementation                  = Complete / Accepted
reference-host Gate 1 reboot/sign-in                = PASS
reference-host Gate 2 RestartOnFailure attempt A    = FAIL
reference-host Gate 2 Interactive attempt B         = FAIL / root-cause evidence accepted
crash-recovery remediation design                   = Complete
remediated repository implementation                = In Progress / CI pending
remediated reference-host Gate 2 retest             = Pending

P-RUNTIME-04 overall                                = In Progress / Remediation Acceptance Pending
P-RUNTIME-05                                        = blocked until formal P-RUNTIME-04 acceptance
```

The previous Gate 2 failures are historical acceptance evidence and must remain recorded after the remediation succeeds.
