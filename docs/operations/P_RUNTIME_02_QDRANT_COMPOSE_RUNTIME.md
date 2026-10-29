# P-RUNTIME-02 — Qdrant Compose Runtime Operations

Date: 2026-10-30
Status: **Complete / Accepted**
Task: `P-RUNTIME-02 [P1] Qdrant Compose / configuration assets`

## 1. Scope

This document is the operator procedure for the Phase P reference Qdrant runtime selected by P-RUNTIME-01.

The repository-owned runtime definition is:

```text
runtime/qdrant/compose.yaml
runtime/qdrant/.env.example
```

The reference Windows environment is Docker Desktop with the WSL 2 backend. Qdrant remains an independent shared runtime. SGOKB CLI / GUI / MCP are clients and observers; they do not own the Qdrant process lifecycle.

P-RUNTIME-02 acceptance is recorded in `docs/evaluation/P_RUNTIME_02_QDRANT_COMPOSE_CONFIGURATION_ACCEPTANCE.md`.

## 2. Fixed reference contract

```text
Compose project         = sgokb-qdrant
Qdrant image            = qdrant/qdrant:v1.20.0
Restart policy          = unless-stopped
HTTP                    = 127.0.0.1:6333 -> 6333
gRPC                    = 127.0.0.1:6334 -> 6334
Distributed port        = 6335 not published
Primary data            = Docker named volume sgokb_qdrant_storage
Container storage path  = /qdrant/storage
Readiness               = HTTP GET /readyz must return 200
Normal log level        = INFO
```

The image version, port mappings, named volume, and restart policy are deliberately fixed in `compose.yaml`. They are not local `.env` overrides because changing them changes the accepted runtime contract.

`QDRANT_LOG_LEVEL` is the only initial environment-template override.

## 3. Prerequisites

Install and start Docker Desktop using the Windows WSL 2 backend. Docker Desktop is an external prerequisite and is not installed or licensed by SGOKB.

Verify the runtime before continuing:

```powershell
docker version
docker compose version
```

P-RUNTIME-04 owns formal Windows login auto-start acceptance. For normal Phase P operation, Docker Desktop should have **Start Docker Desktop when you sign in to your computer** enabled.

## 4. Fresh installation / first start

From the repository root:

```powershell
Set-Location runtime/qdrant
Copy-Item .env.example .env

docker compose config
docker compose pull
docker compose up -d --wait --wait-timeout 120
```

The `.env` copy is optional because `compose.yaml` has an `INFO` default. It is shown so local log-level overrides have one documented location. `.env` is ignored by Git.

Verify service state:

```powershell
docker compose ps
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
Invoke-RestMethod http://127.0.0.1:6333/
```

Expected readiness result is HTTP 200 from `/readyz`.

The Compose health check sends an HTTP request to `/readyz` from inside the Qdrant container. The official Qdrant v1.20.0 image does not install `curl` or `wget` in its final image by default, so the repository health check uses the image's `bash` and `/dev/tcp` support rather than adding packages to the upstream image.

## 5. Normal start / stop

Start or reconcile the service:

```powershell
Set-Location runtime/qdrant
docker compose up -d --wait --wait-timeout 120
```

Stop and remove the container/network while preserving persistent Qdrant data:

```powershell
docker compose down
```

`docker compose down` does **not** remove the named volume and is the normal full shutdown command.

To stop without removing the container:

```powershell
docker compose stop
```

Because the accepted policy is `restart: unless-stopped`, a container deliberately stopped by the operator remains stopped across Docker daemon restarts until explicitly started again. This is expected Docker restart-policy behavior.

Resume a stopped service:

```powershell
docker compose start
docker compose ps
```

## 6. Persistent storage

Qdrant canonical vector runtime state is stored in the Docker named volume:

```text
sgokb_qdrant_storage
```

Inspect it with:

```powershell
docker volume inspect sgokb_qdrant_storage
```

Do not depend on or manually edit Docker Desktop's internal Windows/WSL filesystem path. The volume name is the supported operator identity.

Removing/recreating the Qdrant container or running `docker compose down` preserves this volume.

The following is **destructive** and is not a normal shutdown procedure:

```powershell
docker compose down -v
```

Likewise, this explicitly deletes the runtime state:

```powershell
docker volume rm sgokb_qdrant_storage
```

Only use destructive volume removal when intentionally resetting the vector runtime and when the corresponding SGOKB derived-state rebuild/recovery procedure is understood.

Qdrant Vector Index state is derived from SGOKB canonical Knowledge, but accidental deletion still creates an availability/rebuild event and must not be hidden as routine cleanup.

## 7. Ports and local security boundary

The Compose asset binds only:

```text
127.0.0.1:6333
127.0.0.1:6334
```

No wildcard host binding and no `6335` publication are part of the reference runtime.

This is intentionally a local-machine single-node runtime. Do not change the binding to `0.0.0.0`, a LAN address, or a remote host as an informal convenience. Remote exposure requires a separate authentication/TLS/firewall/security decision.

## 8. Logs and troubleshooting

Show current status:

```powershell
docker compose ps
```

Follow Qdrant logs:

```powershell
docker compose logs --tail 200 -f qdrant
```

Inspect the container health record:

```powershell
docker inspect --format '{{json .State.Health}}' sgokb-qdrant-qdrant-1
```

If a custom Compose container name appears because an operator changed the project name, use `docker compose ps -q qdrant` to resolve the container ID instead of relying on the generated name:

```powershell
$ContainerId = docker compose ps -q qdrant
docker inspect --format '{{json .State.Health}}' $ContainerId
```

Useful direct probes:

```powershell
Invoke-WebRequest http://127.0.0.1:6333/healthz -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:6333/livez -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
```

`/readyz` is the acceptance/readiness authority; `/healthz` and `/livez` are diagnostics.

## 9. Upgrade procedure

Qdrant upgrades are deliberate repository changes. Do not edit a local `.env` to select a different image and do not replace the image with `latest`.

Before changing the pinned image, protect the current state. For this single-node runtime, create a full Qdrant storage snapshot and download it outside the container:

```powershell
$SnapshotResponse = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:6333/snapshots

$SnapshotName = $SnapshotResponse.result.name
New-Item -ItemType Directory -Force backups/qdrant | Out-Null
Invoke-WebRequest `
  -Uri "http://127.0.0.1:6333/snapshots/$SnapshotName" `
  -OutFile "backups/qdrant/$SnapshotName"
```

The repository `backups/` path is ignored by Git. A snapshot left only inside the running container is not sufficient protection for a recreate/rollback procedure; retain the downloaded snapshot independently.

Then:

1. read the Qdrant release notes and upgrade guide;
2. if crossing multiple minor versions, follow Qdrant's required intermediate-minor sequence;
3. change the exact `qdrant/qdrant:vX.Y.Z` tag in `runtime/qdrant/compose.yaml` through normal repository review;
4. validate the new Compose configuration;
5. pull and recreate Qdrant;
6. wait for `/readyz`;
7. verify Qdrant version and SGOKB vector/generation state.

Commands after the reviewed version change:

```powershell
Set-Location runtime/qdrant
docker compose config
docker compose pull qdrant
docker compose up -d --wait --wait-timeout 120
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
Invoke-RestMethod http://127.0.0.1:6333/
```

## 10. Rollback boundary

Rollback is **not** defined as simply changing the image tag back and starting an older Qdrant binary against storage already opened or migrated by a newer version.

If an upgrade must be reversed:

1. stop the failed/new runtime;
2. follow the Qdrant-supported restore procedure for the protected snapshot and target version;
3. restore into compatible state rather than reusing possibly migrated storage blindly;
4. start the pinned target version;
5. verify `/readyz`, server version, collections, and SGOKB derived-generation state.

Formal backup/recovery acceptance remains owned by the existing SGOKB safety/recovery contract and later Runtime acceptance tasks.

## 11. Configuration changes

The reference runtime intentionally uses Qdrant's production defaults except for the repository-owned Compose boundary and optional log level.

Supported local override template:

```powershell
Copy-Item runtime/qdrant/.env.example runtime/qdrant/.env
```

Current template:

```text
QDRANT_LOG_LEVEL=INFO
```

A change to image version, ports, persistent volume identity, restart policy, security exposure, or Qdrant storage path is a runtime-contract change and belongs in repository review, not an untracked local override.

## 12. Fresh-environment acceptance command sequence

A fresh supported Windows environment should be able to construct the same reference runtime with:

```powershell
git clone <repository-url>
Set-Location SourceGroundedObjectKnowledgeBase/runtime/qdrant
Copy-Item .env.example .env
docker compose config
docker compose pull
docker compose up -d --wait --wait-timeout 120
Invoke-WebRequest http://127.0.0.1:6333/readyz -UseBasicParsing
docker volume inspect sgokb_qdrant_storage
```

Successful completion means the P-RUNTIME-02 reproducibility boundary is satisfied. Windows login ordering/recovery after reboot is a separate P-RUNTIME-04 acceptance concern.

## 13. Acceptance authority

Final P-RUNTIME-02 gate:

```text
GitHub Actions run         = 40961873913
verified branch source     = 1732322b7a0d40dbd4838e3b62cebea1fb458baf
verified synthetic merge   = 56b2ee1d1c83e0f4c84c27575ed8fdbcbb7bade9
focused contract tests     = 2 / 2 PASS
real Qdrant runtime        = PASS
normal-down volume retain  = PASS
recreate readiness         = PASS
Ruff src/tests             = PASS
Windows full regression    = 839 / 839 PASS
warnings                   = 2 known local-Qdrant warnings
```

Authority files:

- P-RUNTIME-01 decision: `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- Compose asset: `runtime/qdrant/compose.yaml`
- environment template: `runtime/qdrant/.env.example`
- acceptance: `docs/evaluation/P_RUNTIME_02_QDRANT_COMPOSE_CONFIGURATION_ACCEPTANCE.md`
- task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
