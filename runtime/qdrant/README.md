# SGOKB Qdrant Runtime

Phase P has two Qdrant deployment profiles in this directory.

## Windows reference runtime — native Qdrant

The supported Windows path runs Qdrant directly as a native `qdrant.exe` process. Windows Task Scheduler owns login auto-start and restart-on-failure behavior; SGOKB remains a client / observer only.

Assets:

```text
windows/Register-SgokbQdrantAutoStart.ps1
windows/Test-SgokbQdrantAutoStart.ps1
```

Authoritative procedure:

- `docs/operations/P_RUNTIME_04_NATIVE_WINDOWS_QDRANT_AUTOSTART.md`

Architecture decision:

- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`

The registration script requires the operator to supply the actual local `qdrant.exe` path. SGOKB does not download Qdrant, invent its storage path, or silently replace the installed binary.

Readiness authority remains:

```text
GET http://127.0.0.1:6333/readyz -> HTTP 200
```

## Optional Docker / development profile

The repository-owned Docker Compose definition created by P-RUNTIME-02 is retained as an optional Docker/development profile and as historical reproducibility evidence. It is no longer the Windows login auto-start reference runtime.

Compose contract:

```text
image       = qdrant/qdrant:v1.20.0
HTTP        = 127.0.0.1:6333
gRPC        = 127.0.0.1:6334
storage     = named volume sgokb_qdrant_storage
restart     = unless-stopped
readiness   = GET /readyz
```

Optional Docker profile commands:

```powershell
Copy-Item .env.example .env
docker compose config
docker compose pull
docker compose up -d --wait --wait-timeout 120
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

Normal Docker-profile shutdown preserves persistent data:

```powershell
docker compose down
```

Do **not** use `docker compose down -v` as routine cleanup. The `-v` form removes the Docker profile's persistent Qdrant volume and is destructive.

Historical/optional Docker procedure:

- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`
