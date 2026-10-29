# P-RUNTIME-01 — Windows Qdrant Runtime Decision

Date: 2026-10-30
Status: **Accepted**
Decision scope: Phase P reference Windows runtime for Qdrant

## Decision

SGOKB adopts **Docker Desktop with the WSL 2 backend + repository-owned Docker Compose** as the Phase P reference Qdrant runtime on Windows.

The accepted lifecycle is:

```text
Windows user sign-in
  -> Docker Desktop starts automatically
  -> Docker Engine becomes ready
  -> existing Qdrant Compose container returns under `restart: unless-stopped`
  -> Qdrant `/readyz` becomes ready
  -> SGOKB CLI / GUI may use Qdrant
```

Qdrant remains an **independent shared runtime**. SGOKB GUI, CLI, and MCP consumers may observe and use it, but the GUI must not spawn Qdrant as a child process or become its process supervisor.

## Fixed Phase P reference parameters

```text
Qdrant image version     = qdrant/qdrant:v1.20.0 initially
Version selection        = explicit; never repository-owned `latest`
Storage                  = Docker named volume mounted at /qdrant/storage
Restart policy           = unless-stopped
HTTP                     = 127.0.0.1:6333 -> 6333
gRPC                     = 127.0.0.1:6334 -> 6334
Distributed port         = 6335 not published
Readiness                = HTTP /readyz on port 6333
Container startup owner  = Docker Desktop / Docker Engine
SGOKB lifecycle role     = client / observer only
```

Both 6333 and 6334 are required because the current SGOKB `QdrantVectorIndexAdapter` defaults to `http://localhost:6333`, `grpc_port=6334`, and `prefer_grpc=True`.

## Storage decision

Windows host bind mounts are not the reference persistence mechanism.

The reference configuration uses a Docker named volume because Qdrant's current documentation warns that Docker/WSL Windows mounts can encounter filesystem problems causing data loss and its Windows quickstart recommends a named volume when local-folder mounting is problematic.

The volume is persistent application state. Normal stop/start documentation must preserve it. Removing the volume is a destructive maintenance action.

## Auto-start decision

Phase P targets availability **after Windows login**, not a pre-login machine service.

Docker Desktop's supported setting **Start Docker Desktop when you sign in to your computer** is the reference outer startup trigger. Once Docker Engine is available, the persisted Qdrant container returns according to its restart policy.

Because runtime readiness can lag login, clients must not treat login completion as a readiness guarantee. P-RUNTIME-03 must expose runtime state and P-RUNTIME-04 must verify login/restart ordering and retry behavior.

## Upgrade / rollback decision

Qdrant runtime upgrades are explicit repository changes to the pinned image version.

Required rules:

1. do not track `latest`;
2. follow Qdrant's supported minor-version upgrade sequence;
3. protect persistent state before an upgrade;
4. recreate the service through Compose and wait for readiness;
5. verify SGOKB collection/generation state after the change;
6. do not define rollback as merely starting an older image against storage already migrated by a newer version.

P-RUNTIME-02 will document the concrete commands. Later backup/recovery acceptance remains responsible for proving the state-restoration path.

## No-Docker decision

A native Windows Qdrant binary is **not** a supported Phase P acceptance runtime.

Qdrant currently publishes an official `qdrant-x86_64-pc-windows-msvc.zip`, and Windows Task Scheduler can launch a process on `ONLOGON`. However, accepting that path would require SGOKB to maintain a second process-supervision, logging, restart, storage, update, and recovery design. It would also need separate validation against Qdrant's persistent-storage requirements.

Accordingly:

```text
native qdrant.exe + Task Scheduler = acknowledged manual/experimental alternative
Phase P support/acceptance         = no
```

Third-party Windows service wrappers, WSL/systemd-only deployment, and Startup-folder scripts are also outside the Phase P supported runtime matrix.

## OSS / third-party installation boundary

SGOKB does not bundle or automatically install Docker Desktop or Qdrant server binaries.

Repository responsibility:

- Compose/config assets;
- Qdrant version pin;
- storage/port/health contract;
- lifecycle and upgrade documentation;
- SGOKB-side health/status reporting.

Operator responsibility:

- install Docker Desktop/reference container runtime;
- satisfy Windows/WSL/virtualization prerequisites;
- accept and comply with Docker/Qdrant third-party terms;
- administer machine-level security policy.

Docker Desktop is free for several categories including personal use and non-commercial open-source projects, but its terms require paid subscriptions in some organizational/commercial contexts. SGOKB documentation must disclose this boundary and direct operators to current Docker licensing rather than presenting Docker Desktop as an unrestricted bundled dependency.

## Alternatives rejected as reference

| Alternative | Disposition | Primary reason |
|---|---|---|
| Native Qdrant + Task Scheduler | Not supported reference | duplicates supervision/storage/update acceptance work |
| Native Qdrant + Windows service wrapper | Rejected | adds privileged third-party lifecycle dependency |
| WSL distro + systemd | Rejected | additional distro/startup/network/filesystem operational boundary |
| Startup folder / ad-hoc script | Rejected | weak supervision, health, and recovery semantics |

## Consequences for subsequent tasks

### P-RUNTIME-02

Must create the reproducible Compose/configuration assets implementing this decision, including:

- `qdrant/qdrant:v1.20.0` pin;
- loopback-only 6333/6334 mappings;
- named volume;
- `restart: unless-stopped`;
- `/readyz` health check;
- startup/shutdown/update commands;
- explicit warning around destructive volume removal.

### P-RUNTIME-03

Must model Qdrant as an external runtime and expose readiness/version/collection state without lifecycle ownership.

### P-RUNTIME-04

Must verify Docker Desktop login auto-start, engine/container ordering, retry behavior, unexpected stop recovery, and no-manual-action readiness after reboot/login.

### P-GUI-09 / P-RUNTIME-05

GUI surfaces may show runtime health and troubleshooting entry points, but must not turn the GUI into the Qdrant supervisor.

## Authority

Detailed comparison and source review:

- `docs/evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md`

Task authority:

- `docs/planning/phases/P/PHASE_P_TASKS.md`

This decision unblocks P-RUNTIME-02.
