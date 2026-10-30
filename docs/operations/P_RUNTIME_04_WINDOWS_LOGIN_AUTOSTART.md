# P-RUNTIME-04 — Windows Login Auto-start Integration

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`

## 1. Purpose

The Phase P reference runtime must become available after Windows sign-in without requiring the operator to manually start Qdrant.

The accepted lifecycle remains:

```text
Windows sign-in
  -> Docker Desktop starts automatically
  -> Docker Engine becomes ready
  -> persisted Qdrant container returns under restart: unless-stopped
  -> Qdrant /readyz returns HTTP 200
  -> SGOKB CLI / GUI may use semantic runtime
```

SGOKB does not start Docker Desktop or Qdrant. Docker Desktop / Docker Engine remains the lifecycle owner and SGOKB remains a client / observer.

## 2. Required one-time configuration

### Docker Desktop sign-in startup

In Docker Desktop, enable:

```text
Settings
  -> General
  -> Start Docker Desktop when you sign in to your computer
```

This is the supported outer startup trigger for the Phase P Windows reference environment.

### Qdrant must already be initialized

The Docker restart policy applies to an existing container. Perform the P-RUNTIME-02 initialization once before testing login auto-start:

```powershell
Set-Location runtime/qdrant
Copy-Item .env.example .env
docker compose config
docker compose pull
docker compose up -d --wait --wait-timeout 120
```

Confirm the accepted runtime:

```powershell
docker compose ps
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

The repository Compose definition is authoritative and must retain `restart: unless-stopped`.

## 3. Observer-only readiness probe

After sign-in, use the repository probe:

```powershell
.\runtime\qdrant\verify-windows-login-readiness.ps1
```

The probe waits for startup ordering rather than assuming that Windows sign-in means Docker Engine is already ready. It:

1. waits for the Docker Engine to answer `docker info`;
2. locates the persisted `sgokb-qdrant` Qdrant service;
3. verifies the container restart policy is `unless-stopped`;
4. observes container state and health;
5. waits for `http://127.0.0.1:6333/readyz` to return HTTP 200;
6. emits a JSON readiness receipt.

Default timeout is 180 seconds. It can be changed for slower reference hosts:

```powershell
.\runtime\qdrant\verify-windows-login-readiness.ps1 -TimeoutSeconds 300
```

The probe intentionally does not execute `docker compose up`, `start`, or `restart`, does not launch Docker Desktop, and does not create a Scheduled Task. Passing the probe therefore demonstrates observed automatic recovery rather than recovery caused by the test itself.

## 4. Formal restart / login acceptance procedure

Before restarting Windows:

```powershell
Set-Location runtime/qdrant
docker compose ps
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

The Qdrant service must be running normally. Do not use `docker compose stop` immediately before this acceptance because a deliberately stopped service is outside the automatic-restart expectation for the accepted `unless-stopped` policy.

Then:

1. restart Windows normally;
2. sign in to the same Windows user account;
3. do not manually launch Docker Desktop;
4. do not execute a Qdrant start/up/restart command;
5. run the observer-only readiness probe;
6. retain the JSON receipt plus `docker compose ps` output as acceptance evidence.

Pass criteria:

```text
Docker Desktop manual launch after sign-in = none
Qdrant manual start/up/restart              = none
Docker Engine                               = becomes observable
Qdrant restart policy                       = unless-stopped
Qdrant readiness                            = /readyz HTTP 200
probe                                        = exit 0 / ready=true
```

## 5. Startup ordering and retry behavior

Docker Desktop startup, WSL 2 initialization, Docker Engine readiness, container restart, and Qdrant readiness are asynchronous. SGOKB must not assume a fixed ordering delay.

The accepted strategy is bounded observation:

```text
sign-in
  -> Docker Desktop startup may still be in progress
  -> retry Docker Engine observation
  -> once Engine is ready, observe existing Qdrant container
  -> retry /readyz until ready or timeout
```

The default observer budget is 180 seconds. A timeout is reported as a runtime availability failure; it does not trigger a hidden lifecycle mutation.

## 6. Unexpected-stop recovery

Docker restart policy recovery must be distinguished from an intentional operator stop.

For an explicit crash-style recovery check, first ensure Qdrant has been running successfully for more than 10 seconds, then resolve its container ID and terminate it without using the normal stop path:

```powershell
Set-Location runtime/qdrant
$ContainerId = docker compose ps -q qdrant
docker kill $ContainerId
.\verify-windows-login-readiness.ps1
```

Expected result: Docker applies `restart: unless-stopped`, the container returns, and `/readyz` becomes HTTP 200 without an SGOKB start/restart action.

This is an acceptance/diagnostic procedure, not a normal operating command.

## 7. Intentional stop semantics

The following is an operator intent to stop the service:

```powershell
docker compose stop
```

A service deliberately stopped under `restart: unless-stopped` is not required by this contract to become ready automatically at the next sign-in. If an operator intentionally stopped Qdrant, resume it explicitly:

```powershell
docker compose start
docker compose ps
```

Do not classify this case as a P-RUNTIME-04 auto-start defect.

## 8. Troubleshooting

### Docker Engine does not become ready

Check:

- Docker Desktop is installed and its terms have been accepted;
- `Start Docker Desktop when you sign in to your computer` is enabled;
- WSL 2 / virtualization prerequisites are healthy;
- Docker Desktop diagnostics and logs.

Useful probes:

```powershell
docker version
docker info
```

### Qdrant container does not exist

P-RUNTIME-04 does not create the runtime. Run the documented P-RUNTIME-02 one-time initialization.

### Container exists but remains stopped

Check whether it was deliberately stopped:

```powershell
docker compose ps -a
```

If it was intentionally stopped, use `docker compose start`. If it exited unexpectedly, inspect restart count and logs before changing state:

```powershell
$ContainerId = docker compose ps -q qdrant
docker inspect --format '{{.RestartCount}}' $ContainerId
docker compose logs --tail 200 qdrant
```

### Engine is ready but `/readyz` times out

Inspect:

```powershell
docker compose ps
docker compose logs --tail 200 qdrant
Invoke-WebRequest http://127.0.0.1:6333/healthz -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:6333/livez -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

`/readyz` remains the readiness authority.

### Port conflict

The accepted runtime owns loopback ports `6333` and `6334`. Do not silently change repository ports as a local workaround. Identify the conflicting process and resolve the conflict before restarting the accepted runtime.

## 9. Safety boundary

P-RUNTIME-04 adds no new canonical state and no new SGOKB lifecycle owner.

```text
Docker Desktop / Engine = runtime lifecycle owner
Compose restart policy  = automatic container recovery mechanism
SGOKB CLI / GUI          = client / observer
readiness probe          = observer only
canonical Knowledge      = SQLite; unaffected by runtime startup ordering
```

P-RUNTIME-05 may surface these observations in a dedicated GUI Runtime Dashboard, but it must preserve the same ownership boundary.

## 10. Authority

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`
- `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- `runtime/qdrant/compose.yaml`
- `runtime/qdrant/verify-windows-login-readiness.ps1`
- `tests/test_p_runtime_04_windows_login_autostart.py`
- Docker Desktop settings documentation
- Docker restart-policy documentation
