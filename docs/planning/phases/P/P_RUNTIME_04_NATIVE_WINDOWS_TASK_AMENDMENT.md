# P-RUNTIME-04 — Native Windows Task Amendment

Date: 2026-10-31
Status: **Active task-local amendment**
Applies to: `P-RUNTIME-04 [P1] Windows login auto-start integration`

## Purpose

`PHASE_P_TASKS.md` was written when Phase P still treated Docker Desktop / Docker Compose as the Windows Qdrant reference runtime. During P-RUNTIME-04 execution the supported deployment constraint was corrected: **Qdrant runs directly on the local Windows host as `qdrant.exe`**.

This task-local amendment supersedes only the runtime-form wording for P-RUNTIME-04 and the Windows-reference interpretation of P-RUNTIME-01/P-RUNTIME-02. It does not change the accepted P-RUNTIME-03 observation boundary or the sequencing of later Phase P tasks.

## Amended P-RUNTIME-04 scope

Replace the earlier P-RUNTIME-04 implementation item:

```text
container runtime auto-start configuration
```

with:

```text
native Windows qdrant.exe auto-start through Windows Task Scheduler
```

P-RUNTIME-04 implementation scope is therefore:

- native Qdrant executable path / arguments / working-directory registration;
- Windows Task Scheduler `AtLogOn` trigger;
- Task Scheduler restart-on-failure policy;
- duplicate-instance suppression;
- readiness polling through Qdrant `/readyz`;
- Windows login/startup ordering;
- unexpected native Qdrant process failure recovery;
- operator-visible troubleshooting;
- real restart/sign-in acceptance without a manual Qdrant launch.

## Lifecycle ownership

```text
Qdrant binary/config/storage      = operator-owned
Qdrant startup/restart            = Windows Task Scheduler-owned
SGOKB CLI / GUI / MCP             = client / observer only
SGOKB Qdrant start/stop/restart   = not exposed by the shared Application boundary
readiness authority               = Qdrant /readyz
```

The GUI must not become a Qdrant supervisor.

## P-RUNTIME-01 disposition

`P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md` is amended by P-RUNTIME-04:

```text
old Windows reference = Docker Desktop / Compose
new Windows reference = native qdrant.exe + Windows Task Scheduler
```

The external-runtime ownership principle remains unchanged.

## P-RUNTIME-02 disposition

P-RUNTIME-02 remains **Complete / Accepted** as historical/reproducibility work. Its repository-owned Compose assets are retained as an optional Docker/development profile but are no longer the supported Windows login auto-start dependency.

This means P-RUNTIME-04 no longer depends operationally on Docker Desktop or Docker Engine becoming ready after sign-in.

## P-RUNTIME-03 disposition

No semantic change is required. P-RUNTIME-03 already defines Qdrant as externally owned and exposes health/readiness without start/stop/restart lifecycle actions.

## Completion gate

The original completion intent is preserved in native form:

```text
Windows restart / sign-in
  -> no manual Qdrant launch
  -> Task Scheduler starts qdrant.exe
  -> /readyz becomes HTTP 200
  -> SGOKB runtime health reports Qdrant healthy
```

P-RUNTIME-04 is not `Complete / Accepted` until the supported Windows reference host also passes unexpected-process-failure recovery through the configured Task Scheduler restart policy.

## Authorities

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
- `docs/evaluation/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART_ACCEPTANCE.md`
- `runtime/qdrant/windows/Register-SgokbQdrantAutoStart.ps1`
- `runtime/qdrant/windows/Test-SgokbQdrantAutoStart.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`

Until Phase P closure rewrites the consolidated task authority, this document is the authoritative amendment for the P-RUNTIME-04 runtime form.
