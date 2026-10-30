# SGOKB Qdrant Runtime

This directory contains the repository-owned Docker Compose definition for the Phase P reference Qdrant runtime.

Reference contract:

```text
image       = qdrant/qdrant:v1.20.0
HTTP        = 127.0.0.1:6333
gRPC        = 127.0.0.1:6334
storage     = named volume sgokb_qdrant_storage
restart     = unless-stopped
readiness   = GET /readyz
```

From this directory on the supported Windows reference environment:

```powershell
Copy-Item .env.example .env
docker compose config
docker compose pull
docker compose up -d --wait --wait-timeout 120
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

For automatic availability after Windows sign-in, enable Docker Desktop **Settings > General > Start Docker Desktop when you sign in to your computer**. Docker Desktop remains the outer lifecycle owner; SGOKB does not add a Windows service, scheduled task, Startup-folder launcher, or GUI/CLI supervisor.

P-RUNTIME-04 reboot/login acceptance is performed with:

```powershell
pwsh -File .\windows\Invoke-PRuntime04Acceptance.ps1 -Mode PrepareReboot -AsJson
# Restart Windows and sign in without manually starting Docker Desktop/Qdrant.
pwsh -File .\windows\Invoke-PRuntime04Acceptance.ps1 -Mode VerifyAfterLogin -AsJson
pwsh -File .\windows\Invoke-PRuntime04Acceptance.ps1 -Mode ExerciseUnexpectedStop -AsJson
```

Formal P-RUNTIME-04 procedure and troubleshooting:

- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`

Normal shutdown preserves persistent data:

```powershell
docker compose down
```

Do **not** use `docker compose down -v` as routine cleanup. The `-v` form removes the persistent Qdrant volume and is destructive.

A deliberate `docker compose stop`/`down` is not overridden by the login acceptance harness. `restart: unless-stopped` is intentionally retained so SGOKB does not defeat an explicit operator stop.

Authoritative operating and upgrade procedure:

- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`

Architecture decision:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
