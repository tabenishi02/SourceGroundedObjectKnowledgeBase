# P-RUNTIME-04 — Windows login auto-start integration

Date: 2026-10-30
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Status: **Implementation / acceptance procedure defined; physical reboot acceptance required**

## 1. Purpose

P-RUNTIME-04 verifies the Phase P reference lifecycle selected in P-RUNTIME-01:

```text
Windows user sign-in
  -> Docker Desktop starts automatically
  -> Docker Engine becomes ready
  -> persisted Qdrant container returns under restart: unless-stopped
  -> Qdrant /readyz returns HTTP 200
  -> SGOKB may use semantic runtime
```

The acceptance condition is behavioral: after a real Windows restart and user sign-in, Qdrant must become ready without the operator manually starting Docker Desktop, Qdrant, or the Compose service.

Qdrant remains an independent runtime. SGOKB CLI, GUI, MCP, and this acceptance harness are observers/clients and do not become Docker Desktop or Qdrant supervisors.

## 2. Reference boundary

The accepted runtime remains unchanged from P-RUNTIME-01/02:

```text
Host                       = Windows 11 reference environment
Container runtime          = Docker Desktop / WSL 2 backend
Outer startup trigger      = Docker Desktop sign-in auto-start setting
Compose project            = sgokb-qdrant
Qdrant image               = qdrant/qdrant:v1.20.0
Restart policy             = unless-stopped
HTTP                       = 127.0.0.1:6333
preferred gRPC             = 127.0.0.1:6334
Persistent volume          = sgokb_qdrant_storage
Readiness authority        = GET http://127.0.0.1:6333/readyz -> 200
SGOKB lifecycle ownership  = none
```

P-RUNTIME-04 does not add Task Scheduler, a Startup-folder script, a Windows service wrapper, or a second process manager.

## 3. Docker Desktop sign-in setting

On the reference machine, open Docker Desktop:

```text
Settings
  -> General
  -> Start Docker Desktop when you sign in to your computer
  -> Enabled
```

This is an external operator setting owned by Docker Desktop. SGOKB does not edit Docker Desktop's `settings-store.json` to force it.

The current Docker documentation exposes the Windows settings-store location, but that storage format is not adopted as an SGOKB configuration API. The P-RUNTIME-04 harness records only whether the file exists for diagnostics and does not read or mutate the startup value.

Official Docker references reviewed for this task:

- Docker Desktop settings: https://docs.docker.com/desktop/settings-and-maintenance/settings/
- Docker restart policies: https://docs.docker.com/engine/containers/start-containers-automatically/
- Docker Desktop CLI: https://docs.docker.com/reference/cli/docker/desktop/

The Docker documentation states that the sign-in startup setting is disabled by default, so an operator must enable it on a fresh reference installation before formal P-RUNTIME-04 acceptance.

## 4. Initial bootstrap prerequisite

P-RUNTIME-04 verifies automatic return of an already provisioned runtime. It does not replace first-time P-RUNTIME-02 bootstrap.

Before reboot acceptance, provision and verify the service once:

```powershell
Set-Location runtime/qdrant
Copy-Item .env.example .env -ErrorAction SilentlyContinue
docker compose config
docker compose pull
docker compose up -d --wait --wait-timeout 120
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

Then confirm Docker Desktop's sign-in auto-start setting is enabled.

Do not run `docker compose stop` or `docker compose down` immediately before the reboot acceptance. A deliberately stopped/removed service is not the state whose automatic return is being accepted.

## 5. Restart-policy semantics

The Compose service deliberately remains:

```yaml
restart: unless-stopped
```

This has two important consequences.

### Unexpected process exit

After the container has successfully remained up long enough for Docker's restart policy to take effect, an unexpected container exit is automatically recovered by Docker. P-RUNTIME-04 exercises this behavior with an explicit test-only `docker kill` and verifies that:

- the same container identity returns;
- Docker `RestartCount` increases;
- no `docker start`, `docker compose start`, or `docker compose up` is issued after the kill;
- `/readyz` returns HTTP 200 again.

### Deliberate operator stop

A deliberate operator stop is not treated as a failure that SGOKB should override. If the operator intentionally runs `docker compose stop` or otherwise intentionally leaves the runtime stopped, P-RUNTIME-04 does not add a watchdog to defeat that intent.

To resume an intentionally stopped runtime, use the explicit operator command documented in P-RUNTIME-02:

```powershell
docker compose start
```

If the Compose container was removed with `docker compose down`, reconcile it explicitly:

```powershell
docker compose up -d --wait --wait-timeout 120
```

## 6. Startup ordering and bounded readiness

Windows sign-in is not itself a Qdrant readiness signal. The accepted ordering is asynchronous:

```text
sign-in
  -> Docker Desktop process startup
  -> Docker Engine ready
  -> persisted Qdrant container running
  -> Qdrant application ready
  -> host /readyz returns 200
```

The acceptance harness therefore waits in two bounded stages:

1. `docker version --format {{.Server.Version}}` must begin returning a server version;
2. the accepted Qdrant container must be running and `/readyz` must return HTTP 200.

Default acceptance budget:

```text
TimeoutSeconds = 180
PollSeconds    = 2
```

These values are harness wait budgets, not product-side Docker/Qdrant startup controls. They can be overridden for slow reference machines without changing lifecycle ownership.

## 7. Acceptance harness

Repository asset:

```text
runtime/qdrant/windows/Invoke-PRuntime04Acceptance.ps1
```

Modes:

```text
Observe                 current engine/container/readiness observation
PrepareReboot           capture pre-reboot receipt
VerifyAfterLogin        prove a newer Windows boot and no-manual-start readiness
ExerciseUnexpectedStop  prove restart-policy recovery after test-only docker kill
```

The harness validates the accepted runtime identity when ready:

- image is `qdrant/qdrant:v1.20.0`;
- restart policy is `unless-stopped`;
- named volume includes `sgokb_qdrant_storage`;
- container is running;
- host `/readyz` returns HTTP 200.

It never automatically issues:

```text
docker desktop start
docker desktop restart
docker start
docker compose start
docker compose up
```

Those remain explicit operator troubleshooting/reconciliation actions.

## 8. Formal reboot/login acceptance

### Step A — pre-reboot receipt

From repository root, while Qdrant is healthy:

```powershell
pwsh -File .\runtime\qdrant\windows\Invoke-PRuntime04Acceptance.ps1 `
  -Mode PrepareReboot `
  -AsJson
```

This records the current Windows boot time and healthy runtime state to:

```text
%TEMP%\sgokb-p-runtime-04-pre-reboot.json
```

A custom receipt path may be supplied with `-ReceiptPath`.

### Step B — restart Windows

Restart Windows normally.

After login:

- do not manually open/start Docker Desktop;
- do not run `docker desktop start`;
- do not run `docker start`;
- do not run `docker compose start`;
- do not run `docker compose up`.

The Docker Desktop sign-in setting is the only outer trigger under test.

### Step C — post-login verification

After signing in, run only:

```powershell
pwsh -File .\runtime\qdrant\windows\Invoke-PRuntime04Acceptance.ps1 `
  -Mode VerifyAfterLogin `
  -AsJson
```

PASS requires all of the following:

```text
newer Windows boot observed                 = true
Docker Engine reached ready state           = true
existing accepted Qdrant container observed = true
Qdrant /readyz                              = HTTP 200
manual runtime start command required       = false
accepted image/restart/volume identity       = true
```

The harness fails if the receipt belongs to the same Windows boot, preventing a normal stop/start test from being mislabeled as reboot/login acceptance.

## 9. Unexpected-stop recovery acceptance

After the reboot/login PASS, run:

```powershell
pwsh -File .\runtime\qdrant\windows\Invoke-PRuntime04Acceptance.ps1 `
  -Mode ExerciseUnexpectedStop `
  -AsJson
```

This is an intentionally disruptive acceptance test. It issues `docker kill` against the Qdrant container, then only observes recovery.

PASS requires:

```text
same container ID after recovery = true
RestartCount increased           = true
Qdrant /readyz returned to 200   = true
post-kill start command issued   = false
```

Do not confuse this with P-RUNTIME-06, which owns broader runtime failure/recovery acceptance such as runtime unavailable, port conflicts, storage corruption/recovery boundaries, and canonical-safety behavior.

## 10. Troubleshooting

### Docker Engine never becomes ready

Inspect Docker Desktop status:

```powershell
docker desktop status
```

Inspect current Desktop logs where supported:

```powershell
docker desktop logs
```

Confirm the sign-in setting is still enabled in Docker Desktop Settings > General.

For explicit operator recovery only, current Docker Desktop versions expose:

```powershell
docker desktop start
docker desktop restart
```

Using these commands can recover the machine, but a run that required either command is **not** a P-RUNTIME-04 no-manual-action reboot/login PASS. Fix the underlying startup issue and repeat the reboot acceptance.

### Engine is ready but Qdrant is absent

From `runtime/qdrant`:

```powershell
docker compose ps -a
docker compose logs --tail 200 qdrant
docker inspect $(docker compose ps -q qdrant)
```

If the service was intentionally stopped, use `docker compose start`. If it was removed, use `docker compose up -d --wait --wait-timeout 120`. Then repeat formal reboot acceptance from the prepared state.

### Qdrant runs but `/readyz` does not return 200

Check:

```powershell
Invoke-WebRequest http://127.0.0.1:6333/healthz -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:6333/livez -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
docker compose logs --tail 200 qdrant
```

`/readyz` remains the formal acceptance authority.

### Port conflict

Check host ownership of the accepted ports:

```powershell
Get-NetTCPConnection -LocalPort 6333,6334 -ErrorAction SilentlyContinue
```

Do not silently change the accepted ports to work around a conflict. Port-conflict recovery is part of later runtime failure/recovery acceptance.

## 11. What P-RUNTIME-04 does not do

P-RUNTIME-04 does not:

- install Docker Desktop;
- accept Docker's terms on behalf of the operator;
- edit Docker Desktop internal settings files;
- create a Windows Task Scheduler task;
- create a Windows service;
- add a Startup-folder process launcher;
- make SGOKB GUI/CLI a runtime supervisor;
- automatically override an intentional operator stop;
- change the accepted Qdrant image, ports, storage, or restart policy.

## 12. Acceptance evidence boundary

Repository/static/CI verification can prove:

- harness syntax and safety contract;
- accepted Compose policy remains unchanged;
- observer-only login verification path;
- bounded readiness logic;
- explicit unexpected-stop recovery test semantics;
- project regressions.

Only a real supported Windows environment can prove the final completion condition:

```text
Windows restart / login
  -> no manual runtime start action
  -> Qdrant /readyz becomes ready
```

Therefore P-RUNTIME-04 must not be marked `Complete / Accepted` solely from hosted CI. The physical reboot/login receipt and unexpected-stop recovery output must be recorded in the final acceptance document before closure.

## 13. Related authorities

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`
- `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- `runtime/qdrant/compose.yaml`
- `runtime/qdrant/windows/Invoke-PRuntime04Acceptance.ps1`
- `docs/planning/phases/P/PHASE_P_TASKS.md`
