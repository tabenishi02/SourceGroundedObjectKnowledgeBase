# P-RUNTIME-01 — Windows Qdrant Runtime Decision

Date: 2026-10-30
Status: **Accepted / Amended by P-RUNTIME-04**
Decision scope: Phase P reference Windows runtime for Qdrant

## Amendment

The original P-RUNTIME-01 decision selected Docker Desktop / WSL 2 + repository-owned Docker Compose as the reference Windows runtime. During P-RUNTIME-04 execution the supported deployment constraint was corrected: **Qdrant runs directly on the local Windows host as `qdrant.exe`, not in Docker**.

That correction changes the Phase P Windows operational authority. The native Windows deployment defined below supersedes the earlier Docker choice for the Windows acceptance path. The already accepted P-RUNTIME-02 Compose assets and their acceptance evidence remain valid historical/reproducibility evidence and may be used as an **optional Docker/development profile**, but they are no longer the authoritative Windows login auto-start runtime.

## Amended decision

SGOKB adopts **native Windows Qdrant + Windows Task Scheduler** as the Phase P reference Qdrant runtime on Windows.

The accepted lifecycle is:

```text
Windows user sign-in
  -> Windows Task Scheduler fires the SGOKB Qdrant AtLogOn task
  -> Task Scheduler starts the configured native qdrant.exe directly
  -> Qdrant opens the configured local storage and endpoints
  -> Qdrant /readyz becomes HTTP 200
  -> SGOKB CLI / GUI may use Qdrant
```

Qdrant remains an **independent shared runtime**. Windows Task Scheduler owns launch/restart behavior. SGOKB GUI, CLI, and MCP consumers remain clients/observers and must not spawn Qdrant as a hidden child process or become its process supervisor.

## Fixed Phase P Windows runtime parameters

```text
Runtime form             = native Windows qdrant.exe
Binary installation      = operator-managed; SGOKB does not download/install it
Version selection        = explicit/operator-recorded; no SGOKB auto-update
Startup owner            = Windows Task Scheduler
Startup trigger          = AtLogOn for the configured interactive user
Task identity            = \SGOKB\Qdrant by default
Process action           = qdrant.exe directly, with explicit optional arguments
Working directory        = explicit; defaults to qdrant.exe parent directory
Failure restart          = Task Scheduler restart-on-failure
Restart interval         = >= 60 seconds (Windows Task Scheduler minimum)
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

Windows Task Scheduler is the reference outer startup owner. The repository provides:

- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1` — deterministic task registration/update;
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1` — task-contract and `/readyz` verification;
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md` — operational and acceptance procedure.

Login completion is not itself a readiness guarantee. Consumers continue to use the P-RUNTIME-03 shared runtime-health contract, whose Qdrant readiness authority is `/readyz` and whose lifecycle actions remain disabled.

## Failure / restart semantics

The scheduled task directly launches `qdrant.exe`, allowing Task Scheduler to track the long-running process. The task is configured with restart-on-failure and `MultipleInstances=IgnoreNew`.

An **unexpected process failure** is therefore expected to enter the Task Scheduler restart policy. An **intentional operator stop** through Task Scheduler is different and must not be misclassified as an auto-start failure. P-RUNTIME-04 acceptance uses process-failure/reboot-login scenarios separately from intentional maintenance stops.

Windows Task Scheduler requires restart intervals of at least one minute; the repository registration default is 60 seconds. The retry budget is finite and explicit.

## Upgrade / rollback decision

Native Qdrant upgrades are operator-controlled changes, not SGOKB self-update actions.

Required rules:

1. do not let SGOKB silently replace `qdrant.exe`;
2. record the installed Qdrant version used for an accepted environment;
3. protect Qdrant runtime state before an upgrade;
4. preserve the scheduled-task executable/arguments/working-directory contract or re-register it explicitly;
5. wait for `/readyz` after the change;
6. verify SGOKB runtime health and collection/generation state;
7. do not define rollback as merely starting an older binary against possibly migrated storage.

## Docker / Compose disposition

P-RUNTIME-02 created and accepted a reproducible Docker Compose profile before the native-Windows deployment correction was supplied. Those artifacts are not deleted and their historical acceptance is not rewritten.

Their current disposition is:

```text
runtime/qdrant/compose.yaml and .env.example = retained optional Docker/development profile
P-RUNTIME-02 historical acceptance          = retained
Phase P Windows reference runtime           = native qdrant.exe + Task Scheduler
P-RUNTIME-04 login auto-start authority      = native Windows only
```

Docker Desktop is therefore no longer a prerequisite for the supported Windows path.

## Rejected Windows lifecycle alternatives

| Alternative | Disposition | Primary reason |
|---|---|---|
| Native Qdrant + Task Scheduler | **Selected** | OS-owned AtLogOn and restart policy without making SGOKB a supervisor |
| Native Qdrant + Windows service wrapper | Rejected | adds privileged third-party lifecycle dependency |
| GUI/CLI launches Qdrant | Rejected | violates accepted external-runtime ownership boundary |
| Startup folder / ad-hoc shortcut | Rejected | weak restart, diagnostics, and deterministic configuration semantics |
| Docker Desktop / Compose | Optional profile, not Windows reference | does not match the actual supported local deployment |
| WSL distro + systemd | Rejected | additional distro/startup/network/filesystem operational boundary |

## OSS / third-party installation boundary

SGOKB does not bundle or automatically install the Qdrant server binary.

Repository responsibility:

- Task Scheduler registration/verification assets;
- expected startup/restart/readiness contract;
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

Remains **Complete / Accepted** as historical Compose/configuration work. Its assets are retained as an optional Docker/development profile and are not the Windows auto-start dependency after this amendment.

### P-RUNTIME-03

Remains valid without code changes: it models Qdrant as an external runtime and exposes readiness/version/collection state without lifecycle ownership.

### P-RUNTIME-04

Owns native Task Scheduler registration, login/restart ordering, `/readyz` retry behavior, troubleshooting, unexpected process-failure recovery, and no-manual-action readiness after reboot/login.

### P-GUI-09 / P-RUNTIME-05

GUI surfaces may show runtime health and troubleshooting entry points, but must not turn the GUI into the Qdrant supervisor.

## Authority

Original comparison / historical source review:

- `docs/evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md`

Amended native Windows operations:

- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`

Task authority:

- `docs/planning/phases/P/PHASE_P_TASKS.md`

This amendment is part of P-RUNTIME-04 and does not invalidate P-RUNTIME-03's external lifecycle boundary.
