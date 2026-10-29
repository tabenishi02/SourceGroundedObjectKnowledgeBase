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

Normal shutdown preserves persistent data:

```powershell
docker compose down
```

Do **not** use `docker compose down -v` as routine cleanup. The `-v` form removes the persistent Qdrant volume and is destructive.

Authoritative operating and upgrade procedure:

- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`

Architecture decision:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
