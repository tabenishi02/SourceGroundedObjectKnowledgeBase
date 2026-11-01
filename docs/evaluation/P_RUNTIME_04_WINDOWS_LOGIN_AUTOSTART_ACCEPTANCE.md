# P-RUNTIME-04 — Windows Login Auto-start Acceptance

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Disposition: **Complete / Accepted**

> **Historical-evidence note — 2026-11-01:** references below to generation-related top-level degradation describe the runtime-health classifier as observed during P-RUNTIME-04. The supported no-explicit-generation legacy route is now `HEALTHY`; this does not change the P-RUNTIME-04 Qdrant auto-start/recovery evidence or external lifecycle ownership.

## 1. Acceptance objective

P-RUNTIME-04 removes the need to launch native Qdrant manually after Windows sign-in and requires automatic recovery after an unexpected `qdrant.exe` process exit.

Accepted Windows runtime authority:

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

P-RUNTIME-03 remains unchanged: Qdrant is externally owned and `system.status.runtime_health` observes it without exposing start/stop/restart actions.

## 2. Original repository baseline

The original native Task Scheduler assets were accepted by GitHub Actions run `41091876482 (#43)` on Windows Server 2025:

```text
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
synthetic /readyz                  = HTTP 200
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff                               = PASS
full repository regression         = 857 / 857 PASS
```

That baseline did not prove real-host long-running-process crash recovery.

## 3. Historical crash-recovery failure

Reference-host Gate 1, Windows restart -> sign-in -> automatic native Qdrant startup, passed.

The original `RestartOnFailure`-only recovery design failed twice:

```text
Attempt A: S4U task              -> forced qdrant.exe exit -> no recovery = FAIL
Attempt B: Interactive/Limited   -> forced qdrant.exe exit -> no recovery = FAIL
```

Attempt B established that the earlier S4U drift was not the root cause. `RestartOnFailure` was therefore rejected as the sole supervisor for a long-running Qdrant process.

Historical failures remain retained as root-cause evidence.

## 4. Accepted remediation

The selected remediation keeps the same direct native action and adds a periodic recovery pulse:

```text
Task      = \SGOKB\Qdrant
Trigger A = AtLogOn
Trigger B = repeating TimeTrigger
            default interval = 60 seconds
            Duration omitted = indefinite repetition
Action    = qdrant.exe directly
Principal = Interactive / Limited
Policy    = MultipleInstances=IgnoreNew
```

While Qdrant is running, periodic triggers are ignored. After the process exits and the task returns to Ready, the next pulse starts a replacement process.

Verifier receipt schema:

```text
sgokb.qdrant-windows-autostart-check/1.1
```

## 5. Reference-host remediation acceptance — PASS

The supported Windows workstation was re-registered from the remediation branch with the real native Qdrant runtime.

Pre-crash verifier result:

```text
principal_logon_type      = Interactive
trigger_count             = 2
recovery_interval         = PT1M
recovery_interval_seconds = 60
ready_status              = 200
```

The running Qdrant process was force-terminated. No manual `Start-ScheduledTask` was issued afterward.

The next recovery pulse launched a replacement Qdrant process and readiness recovered:

```text
recovered qdrant.exe PID = 41480
Task LastRunTime          = 2026-10-31 04:03:27 +09:00
Task LastTaskResult       = 267009 / 0x41301 / task running
GET /readyz               = HTTP 200
Content                   = all shards are ready
```

SGOKB then observed:

```text
runtime_health.components.qdrant.status    = healthy
runtime_health.components.qdrant.ready     = true
runtime_health.components.qdrant.version   = 1.19.2
runtime_health.lifecycle.qdrant_owner       = external
runtime_health.lifecycle.observe            = true
runtime_health.lifecycle.start/stop/restart = false / false / false
```

The top-level runtime status was degraded only because unrelated generation/derived-state components were degraded; the Qdrant component itself was healthy.

Formal reference-host disposition:

```text
Gate 1 reboot/sign-in automatic startup   = PASS
Gate 2 automatic replacement process      = PASS
Gate 2 recovered /readyz                  = PASS
Gate 2 SGOKB Qdrant health                = PASS
reference-host acceptance                 = Complete / Accepted
```

## 6. Local Windows remediation validation — PASS

A second isolated Windows validation reproduced the remediation workflow's dynamic crash-recovery scenario using a disposable Task Scheduler task and synthetic `/readyz` endpoint. The production Qdrant task was not fault-injected during this validation.

Environment and results:

```text
Windows                         = Windows 11
PowerShell                      = 7.6.9
Register script parse           = PASS / 0 syntax errors
Test script parse               = PASS / 0 syntax errors
Disposable task                 = \SGOKB-Acceptance-Local\QdrantRecoverySmoke
Initial worker PID              = 38356
Recovered worker PID            = 42796
Manual restart after crash      = none
Recovery interval               = 60 seconds / repeating TimeTrigger
Dynamic recovery smoke          = PASS
Focused P-RUNTIME               = 9 passed / 0 failed
Ruff                            = PASS
Full repository regression      = 858 passed / 0 failed / 0 skipped
Warnings                        = 2 existing local-Qdrant warnings / no new warning
Production Qdrant post-test     = PID 41480 unchanged / readyz 200
SGOKB production Qdrant health  = healthy / ready=true / 1.19.2
```

Cleanup confirmed no disposable task, worker, synthetic HTTP server, temporary directory or dedicated Task Scheduler folder remained. Production Task definition, Qdrant config and canonical DB content digest were unchanged.

Aggregate evidence:

`benchmark/results/p-runtime-04-local-remediation-validation.json`

## 7. Hosted GitHub Actions status — deferred verification

Hosted remediation runs did not execute product steps because GitHub blocked runner assignment before execution. Run `41115542118`, attempt 2, reported:

```text
runner_id = 0
steps     = []
```

GitHub CLI exposed the authoritative annotation:

```text
The hosted job was not started because an external GitHub Actions availability constraint prevented runner assignment.
```

This is neither a product/test failure nor a CI PASS.

The formal Phase P task definition for P-RUNTIME-04 requires automatic Windows startup/readiness and unexpected-stop recovery; it does not make GitHub-hosted Windows CI a mandatory completion condition. The hosted remediation workflow was an additional verification gate introduced during remediation.

Because the supported reference host passed the actual lifecycle acceptance, the isolated local Windows reproduction passed the workflow-equivalent recovery scenario, focused tests/Ruff/full regression passed, and hosted execution is blocked solely by an external hosted-runner availability condition, hosted CI is reclassified as:

```text
GitHub Actions remediation CI = Deferred / non-blocking verification debt
```

This is explicitly not a CI success claim.

Evidence:

`docs/evaluation/P_RUNTIME_04_HOSTED_CI_AVAILABILITY_BLOCKER.md`

## 8. Deferred verification debt

When GitHub Actions capacity is available again, execute the hosted Windows workflow and record:

- PowerShell asset parse validation;
- disposable dynamic scheduled-task crash recovery;
- focused P-RUNTIME tests;
- Ruff;
- full repository regression.

A later PASS closes only this portability/hosted-environment verification debt. P-RUNTIME-05 and later Phase P work are not blocked by it.

If a later hosted execution reveals a genuine product or portability regression, treat that as new remediation work and update this acceptance record.

## 9. Maintenance and safety boundary

Because the task has an indefinite recovery pulse, intentional maintenance uses:

```text
Disable task
-> Stop task
-> maintenance
-> Enable task
-> Start task
```

P-RUNTIME-04 does not install/upgrade Qdrant, migrate storage, mutate canonical Knowledge, make GUI/CLI/MCP a Qdrant supervisor, or add public lifecycle actions to P-RUNTIME-03.

Recovery of a process that remains alive but hung/unready remains broader P-RUNTIME-06 scope.

## 10. Final disposition

```text
native Windows design correction          = Complete / Accepted
crash-recovery remediation design         = Complete / Accepted
remediation implementation                = Complete
reference-host acceptance                 = Complete / Accepted
local remediation validation              = PASS
GitHub Actions remediation CI             = Deferred / external hosted-runner availability constraint
P-RUNTIME-04 overall                      = Complete / Accepted
P-RUNTIME-05                              = Unblocked / Ready
```

PR #81 may merge on this acceptance evidence. Hosted CI remains recorded as deferred verification debt and must not be described as passing until an actual hosted runner executes the workflow successfully.
