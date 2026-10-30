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

For the Phase P Windows login auto-start configuration, enable Docker Desktop **Settings > General > Start Docker Desktop when you sign in to your computer**. After sign-in, the repository observer can verify the asynchronous Engine -> container -> `/readyz` sequence without starting or restarting runtime state:

```powershell
.\verify-windows-login-readiness.ps1
```

Normal shutdown preserves persistent data:

```powershell
docker compose down
```

Do **not** use `docker compose down -v` as routine cleanup. The `-v` form removes the persistent Qdrant volume and is destructive.

Authoritative operating procedures:

- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`

Architecture decision:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
