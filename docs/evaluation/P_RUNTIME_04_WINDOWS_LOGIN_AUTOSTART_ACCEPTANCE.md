# P-RUNTIME-04 — Windows Login Auto-start Acceptance

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Disposition: **Repository Accepted / Formal Reference-host Acceptance Pending**

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
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`

P-RUNTIME-03 remains valid because its shared health contract already treats Qdrant as externally owned and observes `/readyz` without start/stop/restart actions.

## 3. Repository implementation completed

Implemented assets:

```text
runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1
runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1
tests/test_p_runtime_04_windows_login_autostart.py
docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md
```

The registration asset provides:

- explicit operator-supplied `qdrant.exe` path;
- optional existing Qdrant arguments and working directory;
- Task Scheduler folder creation where required;
- `AtLogOn` trigger for the current Windows user;
- direct `qdrant.exe` action rather than a GUI/CLI supervisor;
- restart-on-failure policy;
- 60-second default restart interval;
- `MultipleInstances=IgnoreNew`;
- `StartWhenAvailable` and unlimited execution time;
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

## 5. Windows CI / repository acceptance gates

The P-RUNTIME-04 Windows workflow validates:

```text
PowerShell parse: registration script           = required PASS
PowerShell parse: verification script           = required PASS
Task Scheduler registration smoke               = required PASS
focused P-RUNTIME regression                    = required PASS
Ruff src/tests                                   = required PASS
full repository regression                      = required PASS
```

The Task Scheduler smoke uses a disposable Windows-runner task and a local synthetic `/readyz` endpoint. It validates registration/folder/task-contract mechanics without claiming that a hosted runner reproduced the user's real Qdrant installation or reboot lifecycle.

### Final CI result — PASS

Accepted repository-level evidence:

```text
GitHub Actions workflow            = P-RUNTIME-04 Windows acceptance
run                                = 41091876482 (#43)
runner                             = Microsoft Windows Server 2025
Python                             = 3.10.11
verified branch HEAD               = 682f8446a3d00ab120c93fbed40a78aed3dee8e8
checkout history                   = fetch-depth: 0
PowerShell parse                   = PASS
Task Scheduler registration smoke = PASS
synthetic /readyz                  = HTTP 200
restart policy smoke               = 10 attempts / PT1M
focused P-RUNTIME regression       = 8 / 8 PASS
Ruff src/tests                     = PASS
full repository regression         = 857 / 857 PASS
warnings                           = 2 known local-Qdrant warnings
```

The preceding run failed only because the workflow itself omitted the historical Git data and `sentence-transformers` package metadata required by pre-existing full-suite tests. The workflow was aligned with the already accepted Windows full-regression environment (`fetch-depth: 0` plus metadata-only `sentence-transformers` installation); no product/runtime semantics were relaxed.

Repository implementation and automated Windows acceptance are therefore **Complete / Accepted**.

## 6. Reference-host gate — reboot / sign-in

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

## 7. Reference-host gate — unexpected process failure

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

## 8. Current disposition

Repository implementation can be accepted independently of the physical reboot/crash test, but the **P-RUNTIME-04 task itself is not Complete / Accepted until both reference-host gates pass**.

Current formal state:

```text
native Windows design correction       = Complete / Accepted
Task Scheduler registration asset       = Complete / Accepted
Task Scheduler verification asset       = Complete / Accepted
operations / troubleshooting            = Complete / Accepted
Windows CI / repository acceptance      = Complete / Accepted
actual reboot -> login -> ready          = Pending reference-host acceptance
unexpected process failure -> recovery  = Pending reference-host acceptance

P-RUNTIME-04 repository side            = Complete / Accepted
P-RUNTIME-04 overall                    = In Progress / Reference-host Acceptance Pending
next executable gate                    = real reference-host reboot/sign-in and crash-recovery acceptance
P-RUNTIME-05                            = not yet unblocked by formal P-RUNTIME-04 acceptance
```

Once both reference-host gates pass, this document can be amended to `Complete / Accepted` and Phase P sequencing can advance to P-RUNTIME-05.
