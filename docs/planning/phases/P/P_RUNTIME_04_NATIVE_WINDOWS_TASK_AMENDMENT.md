# P-RUNTIME-04 — Native Windows Task Amendment

Date: 2026-10-31
Status: **Active task-local amendment / crash-recovery remediation incorporated**
Applies to: `P-RUNTIME-04 [P1] Windows login auto-start integration`

## Purpose

`PHASE_P_TASKS.md` was written when Phase P still treated Docker Desktop / Docker Compose as the Windows Qdrant reference runtime. During P-RUNTIME-04 execution the supported deployment constraint was corrected: **Qdrant runs directly on the local Windows host as `qdrant.exe`**.

Reference-host acceptance then exposed a second correction: Task Scheduler `RestartOnFailure` did not restart an already-running Qdrant process after forced termination. P-RUNTIME-04 therefore now uses a repeating Task Scheduler recovery trigger on the same native Qdrant task, with `MultipleInstances=IgnoreNew` suppressing duplicate launches while Qdrant is healthy.

This task-local amendment supersedes the runtime-form wording for P-RUNTIME-04, the Windows-reference interpretation of P-RUNTIME-01/P-RUNTIME-02, and the earlier restart-on-failure-only crash-recovery assumption. It does not change P-RUNTIME-03's observer-only Application boundary or the sequencing of later Phase P tasks.

## Amended P-RUNTIME-04 scope

Replace the earlier implementation item:

```text
container runtime auto-start configuration
```

with:

```text
native Windows qdrant.exe lifecycle through Windows Task Scheduler
  - AtLogOn startup
  - repeating crash-recovery trigger
  - IgnoreNew duplicate suppression
```

P-RUNTIME-04 implementation scope is therefore:

- native Qdrant executable path / arguments / working-directory registration;
- Windows Task Scheduler `AtLogOn` trigger;
- repeating time trigger for unexpected process-exit recovery;
- default 60-second recovery interval;
- `MultipleInstances=IgnoreNew` duplicate-instance suppression;
- `RestartOnFailure` retained only as a task/action start-failure fallback;
- readiness polling through Qdrant `/readyz`;
- Windows login/startup ordering;
- unexpected native Qdrant process failure recovery;
- operator-visible troubleshooting and maintenance semantics;
- real restart/sign-in acceptance without a manual Qdrant launch;
- real process-exit recovery acceptance without manual `Start-ScheduledTask`.

## Lifecycle ownership

```text
Qdrant binary/config/storage      = operator-owned
Qdrant startup/recovery           = Windows Task Scheduler-owned
SGOKB CLI / GUI / MCP             = client / observer only
SGOKB Qdrant start/stop/restart   = not exposed by the shared Application boundary
readiness authority               = Qdrant /readyz
```

The GUI must not become a Qdrant supervisor.

## P-RUNTIME-01 disposition

`P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md` is amended by P-RUNTIME-04:

```text
old Windows reference            = Docker Desktop / Compose
new Windows reference            = native qdrant.exe + Windows Task Scheduler
old crash authority assumption   = RestartOnFailure
new crash authority              = repeating time trigger + IgnoreNew
```

The external-runtime ownership principle remains unchanged.

## P-RUNTIME-02 disposition

P-RUNTIME-02 remains **Complete / Accepted** as historical/reproducibility work. Its repository-owned Compose assets are retained as an optional Docker/development profile but are not the supported Windows login auto-start dependency.

## P-RUNTIME-03 disposition

No semantic change is required. P-RUNTIME-03 already defines Qdrant as externally owned and exposes health/readiness without start/stop/restart lifecycle actions.

## Reference-host evidence already recorded

```text
Gate 1: reboot -> sign-in -> Qdrant auto-start                  = PASS
Gate 2: forced process exit -> RestartOnFailure-only recovery   = FAIL
Gate 2 after InteractiveToken re-registration                   = FAIL
```

The two Gate 2 failures are accepted evidence that motivated the remediation and must remain visible in the task history.

Detailed remediation authority:

- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`

## Completion gate

The startup completion intent remains:

```text
Windows restart / sign-in
  -> no manual Qdrant launch
  -> Task Scheduler starts qdrant.exe
  -> /readyz becomes HTTP 200
  -> SGOKB runtime health reports Qdrant healthy
```

The crash-recovery completion gate is amended to:

```text
healthy scheduled-task-managed qdrant.exe
  -> process force-terminated
  -> no manual Start-ScheduledTask
  -> next repeating recovery trigger launches a new process
  -> /readyz returns HTTP 200
  -> SGOKB runtime health returns to healthy
```

P-RUNTIME-04 is not `Complete / Accepted` until the remediated Gate 2 passes on the supported Windows reference host after repository acceptance.

## Maintenance semantic change

Because the task has an indefinite recovery trigger, `Stop-ScheduledTask` alone is not a durable maintenance stop. Intentional maintenance must disable the task before stopping it, then enable/start it when maintenance is complete.

This remains an operator-owned Windows action and does not expand SGOKB lifecycle APIs.

## Authorities

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/design/P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
- `docs/evaluation/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`

Until Phase P closure rewrites the consolidated task authority, this document remains the authoritative task-local amendment for the P-RUNTIME-04 Windows runtime form and recovery mechanism.
