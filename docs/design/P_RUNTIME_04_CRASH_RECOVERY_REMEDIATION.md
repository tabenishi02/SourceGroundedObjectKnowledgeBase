# P-RUNTIME-04 — Runtime Crash Recovery Remediation

Date: 2026-10-31
Status: **Implementation / repository acceptance in progress; reference-host retest required**
Task: `P-RUNTIME-04 runtime crash recovery remediation`

## 1. Problem statement

The initial P-RUNTIME-04 design used Windows Task Scheduler `RestartOnFailure` as both a task/action start retry and a long-running `qdrant.exe` crash supervisor.

Reference-host testing disproved the second assumption.

The supported Windows host successfully passed the login-start gate, but a forced termination of the already-running native Qdrant process did not cause Task Scheduler to launch a replacement process even though the task definition contained:

```text
RestartCount       = 10
RestartInterval    = PT1M
MultipleInstances  = IgnoreNew
ExecutionTimeLimit = unlimited
StartWhenAvailable = true
```

The behavior reproduced after correcting the task principal from an earlier S4U registration to the repository-authoritative Interactive / InteractiveToken principal. Therefore the principal mismatch was a configuration defect, but it was not the root cause of the crash-recovery failure.

## 2. Reference-host evidence

### Gate 1 — reboot / sign-in

```text
Windows restart
  -> user sign-in
  -> no manual Qdrant launch
  -> Task Scheduler launches native qdrant.exe
  -> Qdrant becomes available

Gate 1 = PASS
```

### Gate 2 — original restart-on-failure design

Two crash-recovery observations failed:

1. existing S4U task: forced Qdrant process termination did not produce a replacement process;
2. task re-registered through the repository script as InteractiveToken: Qdrant first reached `/readyz` HTTP 200, the process was then force-terminated, and more than one configured 60-second restart interval elapsed with no new process and no `/readyz` recovery.

After the second attempt the scheduled task returned to `Ready`; `LastRunTime` did not advance and `LastTaskResult` remained `0xFFFFFFFF`.

```text
Gate 2 = FAIL under RestartOnFailure-only crash supervision
```

This is accepted failure evidence and is the reason for this remediation. The failed Gate 2 attempts must not be rewritten as a successful acceptance.

## 3. Specification finding

Windows Task Scheduler supports more than one trigger per task and supports trigger repetition patterns. `MultipleInstances=IgnoreNew` suppresses a new launch when an instance of the same task is already running.

The Task Scheduler protocol description of `RestartOnFailure` is narrower than the original P-RUNTIME-04 assumption: it explicitly covers retry when start conditions prevent a run or when an action fails to start. The reference-host result confirms that it cannot be relied upon as the sole long-running-process crash supervisor for this deployment.

Therefore:

```text
RestartOnFailure
  != authoritative long-running qdrant.exe crash supervision
```

P-RUNTIME-04 retains `RestartOnFailure` only as a best-effort start/action-failure fallback.

## 4. Selected remediation

Use a **single Task Scheduler task with two triggers** and keep the direct `qdrant.exe` action:

```text
Task: \SGOKB\Qdrant

Trigger A
  = AtLogOn for configured interactive user
  = immediate login startup

Trigger B
  = repeating time trigger
  = first boundary: registration time + recovery interval
  = repetition interval: 60 seconds by default
  = no repetition duration (indefinite)
  = crash-recovery pulse

Action
  = qdrant.exe directly

Principal
  = Interactive / Limited

MultipleInstances
  = IgnoreNew
```

Normal operation:

```text
Qdrant running
  -> recovery pulse fires
  -> same task already Running
  -> IgnoreNew suppresses duplicate instance
```

Unexpected process exit:

```text
qdrant.exe exits unexpectedly
  -> task returns to Ready
  -> next recovery pulse fires
  -> Task Scheduler launches qdrant.exe again
  -> /readyz eventually returns HTTP 200
```

This keeps lifecycle ownership outside SGOKB and does not introduce a persistent SGOKB, GUI, CLI, or PowerShell supervisor process.

## 5. Why this design is preferred

### Selected: repeating time trigger + IgnoreNew

Advantages:

- lifecycle owner remains Windows Task Scheduler;
- Task action remains the native `qdrant.exe` directly;
- no third-party service wrapper;
- no persistent supervision process;
- no new SGOKB Application start/stop/restart operations;
- uses Task Scheduler's native multiple-trigger and repetition model;
- the recovery interval is explicit and testable;
- preserves the accepted P-RUNTIME-03 observer-only boundary.

### Rejected: continue relying only on RestartOnFailure

Rejected because the actual supported host failed twice, including after the InteractiveToken contract was restored.

### Rejected: persistent PowerShell supervisor loop

A wrapper could detect process exit reliably, but it would replace the accepted direct-action design with another long-running supervisor process and add shutdown/maintenance semantics that are unnecessary if native trigger repetition succeeds.

### Rejected: GUI / CLI supervision

Still violates the accepted external-runtime ownership boundary.

### Rejected: Windows service wrapper

Still adds a third-party privileged lifecycle dependency that Phase P does not require.

## 6. Configuration contract

The registration script adds:

```text
RecoveryIntervalSeconds = 60 by default
minimum                  = 60 seconds
maximum                  = 31 days
```

The existing settings remain:

```text
RestartCount             = 10 by default
RestartIntervalSeconds   = 60 by default
MultipleInstances        = IgnoreNew
ExecutionTimeLimit       = unlimited
StartWhenAvailable       = true
Battery start/continue   = allowed
```

`RestartCount` / `RestartIntervalSeconds` are no longer the authoritative process-crash recovery mechanism. They remain a fallback for task/action start failures.

The verifier must require:

- exactly one `MSFT_TaskLogonTrigger`;
- exactly one repeating `MSFT_TaskTimeTrigger`;
- the configured recovery interval;
- no finite repetition duration;
- Interactive principal;
- exactly one direct action;
- `MultipleInstances=IgnoreNew`;
- `/readyz` HTTP 200.

Verifier schema becomes:

```text
sgokb.qdrant-windows-autostart-check/1.1
```

## 7. Maintenance semantics

A repeating recovery pulse changes intentional maintenance behavior.

`Stop-ScheduledTask` by itself is no longer a durable maintenance stop because the next recovery pulse may start the task again.

Intentional maintenance must use:

```text
Disable-ScheduledTask
  -> Stop-ScheduledTask
  -> maintenance
  -> Enable-ScheduledTask
  -> Start-ScheduledTask
  -> verify /readyz
```

Disabling the scheduled task is an operator action and does not change the SGOKB Application lifecycle boundary.

## 8. Failure boundary

This remediation covers **unexpected process exit**.

It does not claim to recover a Qdrant process that remains alive but is hung or permanently fails `/readyz`. While the task remains Running, `IgnoreNew` intentionally suppresses recovery pulses. Readiness-failure remediation belongs to the broader P-RUNTIME-06 failure/recovery acceptance unless a later design explicitly changes the lifecycle contract.

## 9. Repository acceptance

Repository acceptance requires:

1. registration and verification scripts parse on Windows;
2. a disposable scheduled task registers with both triggers;
3. exported/runtime task state proves the repeating recovery interval;
4. Windows smoke proves the recovery trigger launches a new action instance after the prior long-running action is force-terminated, without manual `Start-ScheduledTask`;
5. focused P-RUNTIME tests pass;
6. Ruff passes;
7. full repository regression passes.

Hosted CI validates the Task Scheduler mechanism, not the user's physical Qdrant storage/configuration.

## 10. Reference-host retest

After repository acceptance, the supported Windows host must be re-registered with the remediated script and Gate 2 must be repeated:

1. start from scheduled-task-managed Qdrant with `/readyz` HTTP 200;
2. record the current Qdrant PID;
3. force-terminate only the Qdrant process;
4. do not run `Start-ScheduledTask`;
5. wait one recovery interval plus Qdrant startup time;
6. require a different Qdrant PID;
7. require `/readyz` HTTP 200;
8. require `system status` Qdrant health to return to healthy.

Only after this reference-host retest passes can P-RUNTIME-04 be `Complete / Accepted`.

## 11. External specification references

- Microsoft Learn — `New-ScheduledTaskTrigger`: tasks may contain multiple triggers.
- Microsoft Learn — Task Scheduler `Repetition`: trigger repetition controls how often a task is run.
- Microsoft Learn — `MultipleInstancesPolicy`: `IgnoreNew` suppresses a new instance while one is already running.
- Microsoft Open Specifications `[MS-TSCH] RestartOnFailure`: retry semantics for start-condition/action-start failures.

## 12. Authority impact

This remediation amends the failure-recovery portions of:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/planning/phases/P/P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
- `docs/evaluation/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md`
- `docs/planning/phases/P/PHASE_P_STATUS.md`

P-RUNTIME-03 remains unchanged.
