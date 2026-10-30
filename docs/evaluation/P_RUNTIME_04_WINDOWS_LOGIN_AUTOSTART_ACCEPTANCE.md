# P-RUNTIME-04 — Windows Login Auto-start Acceptance

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Disposition: **Implementation Complete / Formal Reference-host Acceptance Pending**

## 1. Scope

P-RUNTIME-04 verifies that the accepted Phase P Qdrant runtime can become ready after Windows sign-in without a manual Docker Desktop or Qdrant start action.

The accepted lifecycle remains:

```text
Windows sign-in
  -> Docker Desktop auto-start
  -> Docker Engine ready
  -> persisted Qdrant container restart under unless-stopped
  -> /readyz HTTP 200
  -> SGOKB semantic runtime available
```

SGOKB remains an observer/client and does not become a process supervisor.

## 2. Repository implementation completed

The task adds:

- `runtime/qdrant/verify-windows-login-readiness.ps1`
  - bounded Docker Engine readiness polling;
  - persisted Qdrant service discovery;
  - `unless-stopped` policy verification;
  - container state/health observation;
  - `/readyz` polling;
  - structured JSON receipt;
  - no lifecycle mutation.
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
  - Docker Desktop sign-in startup configuration;
  - one-time initialization prerequisite;
  - reboot/login acceptance procedure;
  - startup ordering and timeout behavior;
  - crash-style recovery procedure;
  - intentional-stop distinction;
  - troubleshooting and safety boundary.
- `tests/test_p_runtime_04_windows_login_autostart.py`
  - observer-only probe gate;
  - accepted Compose contract preservation;
  - operations/safety documentation gate.

The existing Compose definition remains unchanged because it already owns the accepted `restart: unless-stopped`, loopback ports, named-volume persistence, and `/readyz` health contract.

## 3. External behavior authority

Current Docker documentation confirms:

- Docker Desktop provides the General setting `Start Docker Desktop when you sign in to your computer`;
- Docker recommends restart policies for automatic container restart rather than layering a host process manager over Docker;
- `unless-stopped` restarts a container after exits/daemon restarts except when the service has been deliberately stopped;
- restart policy monitoring becomes active after a container has successfully remained running for at least 10 seconds.

These semantics match the P-RUNTIME-01 decision and are reflected in the P-RUNTIME-04 procedures.

## 4. Static / CI-verifiable acceptance gates

Required repository gates:

```text
probe is observer-only                         = required PASS
accepted Compose restart policy preserved      = required PASS
accepted loopback/readiness contract preserved = required PASS
login/startup/recovery procedure documented    = required PASS
intentional stop separated from failure        = required PASS
existing P-RUNTIME-02/03 regression             = required PASS
full repository regression                     = required PASS before merge
```

These gates can be executed without changing the runtime ownership model.

## 5. Reference-host gate that cannot be substituted by hosted CI

The P-RUNTIME-04 task completion condition is explicitly a real Windows restart/sign-in transition. A GitHub-hosted Windows job cannot prove that the user's supported Docker Desktop installation starts from an interactive Windows sign-in and survives an actual host reboot while preserving the same Docker Desktop/WSL runtime state.

Formal completion therefore requires evidence from a supported Windows reference host:

1. Qdrant is running and ready before reboot;
2. Docker Desktop sign-in auto-start is enabled;
3. Windows is restarted;
4. the user signs in;
5. Docker Desktop is not launched manually;
6. no `docker compose up/start/restart` action is executed;
7. `verify-windows-login-readiness.ps1` returns exit 0 and `ready=true`;
8. `/readyz` is HTTP 200;
9. the receipt and `docker compose ps` output are retained.

An additional crash-style check should use `docker kill` after Qdrant has been healthy for more than 10 seconds and require the observer-only probe to return to `ready=true` without SGOKB lifecycle action.

## 6. Current disposition

Repository implementation is complete, but a real reference-host restart/sign-in has not been executed by this acceptance record. It would be incorrect to mark the task `Complete / Accepted` based only on static tests or a hosted Windows runner.

Current formal state:

```text
P-RUNTIME-04 repository implementation = Complete
P-RUNTIME-04 reference-host acceptance = Pending
P-RUNTIME-04 overall                    = In Progress / Acceptance Pending
next executable gate                    = real Windows restart/sign-in acceptance
P-RUNTIME-05                            = not yet unblocked by formal P-RUNTIME-04 acceptance
```

Once the reference-host evidence is recorded and all repository regression gates pass, this document can be amended to `Complete / Accepted` and Phase P sequencing can advance to P-RUNTIME-05.
