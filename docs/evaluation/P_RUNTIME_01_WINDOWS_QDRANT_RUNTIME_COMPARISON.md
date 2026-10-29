# P-RUNTIME-01 — Windows Qdrant Runtime Operational Design / Comparison

Date: 2026-10-30
Status: **Complete / Accepted**
Task: `P-RUNTIME-01 [P1] Windows Qdrant runtime operational design`

## 1. Purpose

Phase P requires Qdrant to become available automatically after Windows login without making the SGOKB GUI the lifecycle owner of Qdrant.

This task compares the practical Windows runtime choices and fixes the reference environment that P-RUNTIME-02 through P-RUNTIME-04 must implement and accept.

The accepted GUI architecture remains authoritative:

```text
SGOKB CLI / GUI
        |
        | observes / uses
        v
independent Qdrant runtime
```

The GUI must not spawn Qdrant as a child process and must not become responsible for keeping Qdrant alive.

## 2. Existing SGOKB constraints

The existing `QdrantVectorIndexAdapter` defaults to:

```text
HTTP URL    = http://localhost:6333
gRPC port   = 6334
prefer_grpc = true
```

Therefore the reference local runtime must make both loopback ports available:

```text
127.0.0.1:6333 -> Qdrant HTTP / monitoring / readiness
127.0.0.1:6334 -> Qdrant gRPC
```

Port `6335` is the distributed-deployment port and is not required for the accepted single-node Phase P reference environment.

The repository currently depends on `qdrant-client>=1.19,<2`; runtime provisioning itself is external to the Python package.

## 3. External facts checked

Research was performed against current upstream documentation on 2026-10-30.

### Qdrant

- Qdrant recommends Docker for development/testing and publishes the `qdrant/qdrant` container image.
- Qdrant documents REST on `6333` and gRPC on `6334`.
- Qdrant warns that Docker/WSL mounts on Windows are known to have filesystem problems that can cause data loss; its Windows quickstart specifically notes that a named Docker volume may be required instead of a local-folder mount.
- Qdrant requires persistent storage with block-level access and a POSIX-compatible filesystem.
- Qdrant provides `/healthz`, `/livez`, and `/readyz`; `/readyz` represents readiness to accept traffic.
- Qdrant upgrades must not arbitrarily skip minor versions; the latest patch of each intermediate minor version is required when advancing across multiple minor versions.
- The current upstream release is `v1.20.0`, published 2026-10-22. The release also contains a native Windows x86_64 MSVC ZIP asset.

Sources:

- https://qdrant.tech/documentation/quickstart/
- https://qdrant.tech/documentation/installation/
- https://qdrant.tech/documentation/interfaces/
- https://qdrant.tech/documentation/ops-monitoring/monitoring/
- https://qdrant.tech/documentation/upgrades/
- https://qdrant.tech/documentation/snapshots/
- https://github.com/qdrant/qdrant/releases/tag/v1.20.0

### Docker Desktop / Compose

- Docker Desktop has a Windows setting named **Start Docker Desktop when you sign in to your computer**.
- Docker restart policies allow an existing container to return when the Docker daemon returns. `unless-stopped` does not restart a container that was deliberately stopped before the daemon restart.
- Compose supports named volumes as first-class persistent service storage.
- Docker Desktop on Windows normally uses the WSL 2 backend.
- Docker Desktop is free for personal use, education, non-commercial open-source projects, and qualifying small businesses; other uses can require a paid Docker subscription. This is an external prerequisite/license boundary and must not be hidden by SGOKB.

Sources:

- https://docs.docker.com/desktop/settings-and-maintenance/settings/
- https://docs.docker.com/reference/compose-file/services/
- https://docs.docker.com/reference/cli/docker/container/run/
- https://docs.docker.com/desktop/setup/install/windows-install/
- https://docs.docker.com/subscription-billing/desktop-license/

### Windows Task Scheduler

Windows Task Scheduler supports both `ONSTART` and `ONLOGON` triggers. It can therefore launch a native executable or wrapper after login, but process supervision, logs, storage rules, update/rollback, and health semantics must be designed separately.

Source:

- https://learn.microsoft.com/windows-server/administration/windows-commands/schtasks-create

## 4. Candidate approaches

### A. Docker Desktop + Docker Compose

Proposed lifecycle:

```text
Windows login
  -> Docker Desktop auto-start
  -> Docker Engine becomes available
  -> previously created SGOKB Qdrant container is restored
     by restart policy
  -> Qdrant readiness becomes green
  -> SGOKB CLI / GUI may use the runtime
```

Strengths:

- reproducible declarative configuration in the repository;
- exact Qdrant image tag can be pinned;
- named volume gives a clear persistence boundary and avoids the Windows bind-mount risk called out by Qdrant;
- `restart: unless-stopped` provides daemon-level lifecycle recovery without SGOKB process ownership;
- health check, ports, environment, and storage can be represented in one Compose asset;
- startup behavior aligns directly with the Phase P target of automatic availability after user login;
- upgrades and rollback can be expressed as an image-version change plus explicit operator steps;
- the same runtime is available to CLI, GUI, MCP, and maintenance commands.

Costs / limitations:

- Docker Desktop / WSL 2 is an additional external runtime;
- Docker Desktop has its own subscription/license terms;
- login auto-start is not the same thing as a machine service guaranteed ready before any user login;
- Docker Desktop readiness can lag Windows login, so SGOKB must tolerate a temporary `starting/unavailable` state rather than assuming immediate availability.

Assessment: **Best fit for the Phase P reference environment.**

### B. Native Qdrant Windows binary + Task Scheduler

Possible lifecycle:

```text
Windows login
  -> Task Scheduler ONLOGON
  -> pinned qdrant.exe
  -> fixed config/storage paths
```

Strengths:

- no Docker Desktop dependency;
- official Qdrant releases currently publish an x86_64 Windows binary;
- lower idle infrastructure overhead;
- Task Scheduler can trigger at login and can apply a startup delay.

Costs / risks:

- SGOKB would need to define its own process supervision contract;
- logging, restart-after-crash, stale-process handling, configuration, storage, update, rollback, and troubleshooting all become SGOKB-specific operational work;
- Qdrant's general installation guidance recommends Docker for development/testing and states persistent-storage filesystem requirements that require additional Windows-native validation;
- a native path would create a second runtime implementation that P-RUNTIME-02..06 would need to test and maintain for parity.

Assessment: **Not accepted as a Phase P supported runtime contract.** The upstream Windows binary is acknowledged as an operator-controlled experimental/manual alternative, but Phase P will not promise parity, automated setup, or acceptance coverage for it.

### C. Native Qdrant + third-party Windows service wrapper

Examples include service wrappers that register `qdrant.exe` as a Windows service.

Strengths:

- can start before user login;
- Windows Service Control Manager can provide recovery semantics.

Costs / risks:

- adds a third-party lifecycle dependency not otherwise needed by SGOKB;
- installation generally requires elevated/service administration;
- SGOKB would own wrapper selection, versioning, service configuration, logging, permissions, removal, and upgrades;
- duplicates lifecycle capabilities already supplied by the container reference design.

Assessment: **Rejected for the Phase P reference environment.**

### D. WSL distribution + systemd-managed Qdrant

Strengths:

- Linux-native process supervision;
- no Docker Desktop requirement if the operator manages a WSL Linux environment directly.

Costs / risks:

- introduces a managed Linux distribution as an SGOKB prerequisite;
- Windows login / WSL VM activation / systemd startup ordering becomes a separate lifecycle problem;
- networking, filesystem location, backup, and troubleshooting cross the Windows/WSL boundary;
- higher operator complexity than Compose for the intended Windows reference environment.

Assessment: **Rejected for the Phase P reference environment.**

### E. Startup folder / ad-hoc PowerShell or batch launcher

Strengths:

- minimal setup.

Costs / risks:

- weak process supervision;
- no declarative version/storage/health contract;
- poor failure recovery and troubleshooting;
- easy to accidentally couple Qdrant lifecycle to the GUI or a terminal window.

Assessment: **Rejected.**

## 5. Comparison matrix

| Criterion | Docker Desktop + Compose | Native + Task Scheduler | Service wrapper | WSL + systemd | Startup script |
|---|---|---|---|---|---|
| Independent from GUI | Strong | Strong if designed correctly | Strong | Strong | Weak/variable |
| Login auto-start | Strong | Strong | Strong | Medium | Strong |
| Declarative reproducibility | Strong | Medium | Medium | Medium | Weak |
| Version pinning | Strong | Strong | Strong | Strong | Medium |
| Restart/recovery | Strong | Medium; custom work | Strong | Strong | Weak |
| Named-volume persistence | Strong | N/A | N/A | N/A | N/A |
| Windows storage risk isolation | Strong | Requires validation | Requires validation | Medium | Requires validation |
| Health-check integration | Strong | Custom work | Custom work | Custom work | Custom work |
| Upgrade/rollback clarity | Strong | Custom work | Custom work | Custom work | Weak |
| Additional SGOKB maintenance | Low | High | High | High | High |
| External license consideration | Docker Desktop terms | Qdrant only | Wrapper + Qdrant | WSL/Qdrant | Qdrant only |
| Phase P reference suitability | **Accept** | No | No | No | No |

## 6. Accepted reference design

P-RUNTIME-01 accepts the following reference runtime:

```text
Host OS                 = Windows 11 reference environment
Container runtime       = Docker Desktop, WSL 2 backend
Startup trigger         = Docker Desktop start at Windows user sign-in
Runtime definition      = repository-owned Docker Compose asset
Qdrant server version   = exact version tag; initial Phase P pin v1.20.0
Container restart       = unless-stopped
Persistent storage      = Docker named volume
HTTP binding            = 127.0.0.1:6333:6333
gRPC binding            = 127.0.0.1:6334:6334
Distributed port 6335   = not published
Readiness authority     = Qdrant HTTP readiness endpoint on port 6333
SGOKB lifecycle role    = observer/client only
GUI lifecycle ownership = forbidden
```

P-RUNTIME-02 owns the concrete Compose and configuration assets. This task does not create those assets early.

## 7. Version policy

The reference runtime must never use an unpinned `latest` image in repository-owned assets.

Initial implementation target:

```text
qdrant/qdrant:v1.20.0
```

Rules:

1. image version is explicit in repository configuration;
2. upgrades are deliberate repository changes;
3. Qdrant's documented intermediate-minor upgrade rule must be respected;
4. snapshot/backup protection is required before an upgrade that can affect persistent state;
5. rollback is not defined as blindly starting an older binary against already migrated storage;
6. P-RUNTIME-02 and later tasks must document the exact update and recovery sequence.

An immutable image digest may additionally be recorded once P-RUNTIME-02 fixes the registry/image source, but an exact version tag is the minimum accepted pin.

## 8. Storage policy

The Windows reference environment must use a Docker named volume for `/qdrant/storage`.

Rejected reference storage:

```text
C:\... bind mount -> /qdrant/storage
```

Reason: Qdrant explicitly warns of filesystem problems/data-loss risk with Docker/WSL Windows mounts. The named-volume approach also keeps Qdrant's internal storage inside the container runtime's Linux filesystem boundary.

The named volume is persistent state. Removing the container must not implicitly remove it. Commands such as `docker compose down -v` are therefore destructive maintenance operations and must not appear as normal shutdown guidance.

## 9. Networking / local security boundary

The reference runtime is local-machine only.

Required published ports:

```text
127.0.0.1:6333:6333
127.0.0.1:6334:6334
```

Rationale:

- SGOKB's current adapter uses `http://localhost:6333`;
- the adapter defaults to `prefer_grpc=True` and `grpc_port=6334`;
- no Phase P requirement needs Qdrant distributed port `6335`;
- binding explicitly to loopback prevents the normal reference configuration from becoming a LAN service accidentally.

Any future LAN/remote exposure requires a separate security decision for authentication, TLS, firewalling, and threat model. It is outside P-RUNTIME-01.

## 10. Startup and failure semantics

The reference design does not promise that Qdrant is ready at the instant the Windows desktop appears.

Accepted state model:

```text
Windows login
  -> container runtime starting
  -> Qdrant starting
  -> Qdrant ready
```

SGOKB must therefore distinguish at least:

```text
runtime unavailable
runtime starting / retryable
runtime ready
runtime degraded / error
```

P-RUNTIME-03 owns the shared health/status Application model. P-RUNTIME-04 owns actual reboot/login ordering and recovery acceptance.

For Compose health, `/readyz` is the preferred readiness probe because Qdrant documents it as the endpoint indicating the instance can accept traffic. `/healthz` and `/livez` remain useful diagnostics.

## 11. Upgrade / rollback boundary

Accepted operator model:

```text
protect state / snapshot
  -> stop or recreate service through Compose
  -> change pinned image version deliberately
  -> pull / recreate
  -> wait for readiness
  -> verify SGOKB collection/generation state
```

Qdrant documents that minor-version upgrades cannot be skipped arbitrarily. A single-node local deployment also has unavoidable restart downtime during version replacement.

Rollback must be treated as a state-aware recovery operation. If a newer Qdrant version has migrated storage, reverting only the image tag is not sufficient evidence of safe rollback. Snapshot compatibility and the documented Qdrant upgrade path govern recovery.

## 12. OSS installation boundary

SGOKB will not bundle or silently install Docker Desktop, Qdrant binaries, or a Windows service wrapper.

The installation boundary is:

```text
SGOKB repository owns:
  - Compose/configuration assets
  - exact Qdrant version selection
  - health expectations
  - documented lifecycle commands
  - SGOKB-side diagnostics

Operator owns:
  - installation and licensing of Docker Desktop/reference container runtime
  - enabling Windows/WSL prerequisites
  - accepting third-party license terms
  - machine-level virtualization/security policy
```

Docker Desktop's license permits several free-use categories, including personal use and non-commercial open-source projects, but it is not universally free for all organizational use. SGOKB documentation must therefore point users to Docker's current terms rather than representing Docker Desktop as an unrestricted bundled dependency.

A compatible alternative container engine may be usable by experienced operators, but only the documented Docker Desktop + Compose environment is the Phase P Windows acceptance reference unless a later task explicitly broadens that matrix.

## 13. P-RUNTIME-01 disposition

```text
Reference Windows runtime = Docker Desktop + WSL 2 + Docker Compose
Qdrant pin                = v1.20.0 initially
Persistent storage        = named Docker volume
Restart policy            = unless-stopped
Published ports           = loopback 6333 + 6334 only
Automatic startup         = Docker Desktop at sign-in + persisted container restart
GUI/CLI role              = client / observer, never lifecycle owner
Native Windows runtime    = not a supported Phase P acceptance path
```

Therefore:

```text
P-RUNTIME-01 = Complete / Accepted
P-RUNTIME-02 = Unblocked / Next
```
