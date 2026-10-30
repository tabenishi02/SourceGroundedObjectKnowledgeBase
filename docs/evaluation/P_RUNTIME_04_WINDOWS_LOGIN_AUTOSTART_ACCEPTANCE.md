# P-RUNTIME-04 — Windows Login Auto-start Acceptance

Date: 2026-10-31
Status: **Implementation Complete / Device Acceptance Pending**
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`

## 1. Acceptance objective

P-RUNTIME-04 removes the need to launch Qdrant manually after Windows sign-in for the supported deployment where Qdrant runs directly on the local Windows host as `qdrant.exe`.

The completion condition remains:

> After a normal Windows restart and sign-in, Qdrant reaches `/readyz` HTTP 200 without a manual Qdrant launch.

The task also requires recovery from an unexpected Qdrant process failure through the Windows-owned restart policy.

## 2. Deployment correction and authority

The original P-RUNTIME-01 decision selected Docker Desktop / WSL 2 + Docker Compose. During P-RUNTIME-04 execution the supported deployment constraint was corrected: the actual Windows runtime is native Qdrant, not Docker.

The amended authority is:

```text
Windows reference runtime       = native qdrant.exe
Login startup owner             = Windows Task Scheduler
Startup trigger                 = AtLogOn
Failure restart owner           = Windows Task Scheduler
Qdrant readiness authority      = GET /readyz -> HTTP 200
SGOKB runtime lifecycle role    = client / observer only
GUI lifecycle ownership         = none
Docker Compose                  = retained optional/development profile only
```

Authority documents:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/operations/P_RUNTIME_04_NATIVE_WINDOWS_QDRANT_AUTOSTART.md`

P-RUNTIME-03 remains valid because its shared health contract already treats Qdrant as externally owned and observes `/readyz` without start/stop/restart actions.

## 3. Implemented repository assets

```text
runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1
runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1
tests/test_p_runtime_04_windows_autostart_assets.py
docs/operations/P_RUNTIME_04_NATIVE_WINDOWS_QDRANT_AUTOSTART.md
```

The registration asset provides:

- explicit operator-supplied `qdrant.exe` path;
- optional existing Qdrant arguments and working directory;
- `AtLogOn` trigger for the current interactive Windows user;
- direct `qdrant.exe` action rather than a GUI/CLI/wrapper supervisor;
- restart-on-failure policy;
- 60-second default restart interval;
- `MultipleInstances=IgnoreNew`;
- unlimited execution time for the long-running server;
- optional immediate start plus `/readyz` polling.

The verification asset checks the scheduled-task contract and requires `/readyz` HTTP 200 before reporting success.

## 4. Safety boundary

P-RUNTIME-04 does not:

- install or upgrade Qdrant;
- choose or migrate Qdrant storage;
- mutate canonical SGOKB SQLite data;
- make the GUI/CLI a Qdrant process supervisor;
- add public start/stop/restart operations to the P-RUNTIME-03 Application contract;
- redefine Qdrant as canonical Knowledge storage.

This preserves the existing canonical-data and external-runtime ownership boundaries.

## 5. Automated repository acceptance

Focused contract test:

```text
tests/test_p_runtime_04_windows_autostart_assets.py
```

It verifies:

1. the registration asset uses `AtLogOn` and direct native Qdrant execution;
2. restart-on-failure and single-instance settings are present;
3. the default readiness authority is `/readyz`;
4. no Docker/Compose dependency is present in the native registration asset;
5. the verifier checks task identity/trigger/restart/readiness semantics;
6. the runtime decision and operations document identify native Windows Task Scheduler as the current Windows authority;
7. on Windows, both PowerShell assets pass the Windows PowerShell 5.1 parser.

### CI result

Pending PR workflow execution.

This section must be updated with the accepted workflow run before repository-level acceptance is claimed.

## 6. Device acceptance gate — reboot / sign-in

**Status: PENDING**

Required procedure on the actual supported Windows workstation:

1. register `\SGOKB\Qdrant` with the real local `qdrant.exe` path and existing arguments/configuration;
2. prove `/readyz` is HTTP 200 before reboot;
3. restart Windows normally;
4. sign in as the scheduled-task user;
5. do not manually launch Qdrant, SGOKB GUI, Docker, or another Qdrant shortcut;
6. run `Test-SgokbQdrantAutoStart.ps1` within the acceptance timeout;
7. require `/readyz` HTTP 200;
8. require `system status` to report the Qdrant component healthy.

A brief interval of `unavailable/degraded` during startup is allowed. The acceptance authority is eventual `/readyz` readiness within the documented timeout, not process existence or sign-in completion.

## 7. Device acceptance gate — unexpected process failure

**Status: PENDING**

Required procedure on the actual supported Windows workstation:

1. begin from a healthy scheduled-task-managed Qdrant process;
2. terminate that Qdrant process unexpectedly (`Stop-Process -Force` or equivalent);
3. do not invoke `Start-ScheduledTask` manually;
4. allow the configured Task Scheduler restart interval plus Qdrant startup time;
5. require a new Qdrant process to appear;
6. require `/readyz` HTTP 200;
7. require `system status` to return to healthy.

An intentional `Stop-ScheduledTask` is a maintenance stop and is not interchangeable with this crash-recovery acceptance case.

## 8. Disposition

The repository implementation can be accepted independently of the physical reboot/crash test, but the **P-RUNTIME-04 task itself is not Complete / Accepted until both device gates pass**.

Current disposition:

```text
native Windows design correction       = COMPLETE
Task Scheduler registration asset       = COMPLETE
Task Scheduler verification asset       = COMPLETE
operations / troubleshooting            = COMPLETE
automated repository acceptance         = PENDING CI
actual reboot -> login -> ready          = PENDING DEVICE ACCEPTANCE
unexpected process failure -> recovery  = PENDING DEVICE ACCEPTANCE

P-RUNTIME-04 overall                    = IMPLEMENTATION COMPLETE / DEVICE ACCEPTANCE PENDING
```

The next task after formal P-RUNTIME-04 acceptance remains:

```text
P-RUNTIME-05 — GUI Runtime Dashboard integration
```
