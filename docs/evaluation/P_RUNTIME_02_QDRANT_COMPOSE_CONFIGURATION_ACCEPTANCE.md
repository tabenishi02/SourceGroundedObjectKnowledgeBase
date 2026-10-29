# P-RUNTIME-02 — Qdrant Compose / Configuration Assets Acceptance

Date: 2026-10-30
Status: **Complete / Accepted**
Task: `P-RUNTIME-02 [P1] Qdrant Compose / configuration assets`

## 1. Acceptance objective

P-RUNTIME-02 materializes the P-RUNTIME-01 Windows Qdrant runtime decision as reproducible repository-owned assets and verifies that the assets construct the intended real Qdrant runtime.

The task completion condition is:

> A fresh supported Windows environment can construct the same Qdrant runtime from documented repository commands.

Windows login auto-start ordering/recovery remains P-RUNTIME-04 scope. Shared Application-layer runtime health/status remains P-RUNTIME-03 scope.

## 2. Accepted repository assets

```text
runtime/qdrant/compose.yaml
runtime/qdrant/.env.example
runtime/qdrant/README.md
docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md
tests/test_p_runtime_02_qdrant_compose_assets.py
```

The accepted runtime contract is:

```text
Compose project          = sgokb-qdrant
Qdrant image             = qdrant/qdrant:v1.20.0
Restart policy           = unless-stopped
HTTP                     = 127.0.0.1:6333 -> 6333
gRPC                     = 127.0.0.1:6334 -> 6334
Distributed port 6335    = not published
Persistent storage       = Docker named volume sgokb_qdrant_storage
Container storage path   = /qdrant/storage
Readiness                = HTTP GET /readyz -> 200
Normal log level         = INFO
SGOKB lifecycle ownership = none; client / observer only
```

The image version, host ports, named-volume identity, restart policy, and storage path are intentionally fixed in `compose.yaml`. The local `.env` template exposes only `QDRANT_LOG_LEVEL` initially; it cannot silently alter the accepted runtime identity.

## 3. Healthcheck design verification

The upstream Qdrant v1.20.0 final image does not install `curl` or `wget` by default. The accepted Compose healthcheck therefore uses the image's `bash` and `/dev/tcp` support to send an HTTP request to `127.0.0.1:6333/readyz` and requires HTTP status 200.

This avoids building a derived SGOKB Qdrant image merely to add a probe utility and keeps the exact upstream image pin as the runtime artifact.

## 4. Automated contract tests

Focused test file:

```text
tests/test_p_runtime_02_qdrant_compose_assets.py
```

The tests verify that the repository assets preserve the accepted boundary:

- exact `qdrant/qdrant:v1.20.0` pin and no `latest`;
- `restart: unless-stopped`;
- loopback-only 6333 and 6334 publication;
- no 6335 publication;
- named-volume persistence at `/qdrant/storage`;
- stable volume identity `sgokb_qdrant_storage`;
- `/readyz` healthcheck;
- no Windows bind-mount path;
- no `.env` override for image / ports / volume identity;
- `QDRANT_LOG_LEVEL=INFO` environment template.

Final focused gate:

```text
2 / 2 PASS
```

## 5. Real runtime acceptance

Final GitHub Actions run:

```text
run                     = 40961873913
verified branch source  = 1732322b7a0d40dbd4838e3b62cebea1fb458baf
synthetic PR merge      = 56b2ee1d1c83e0f4c84c27575ed8fdbcbb7bade9
runtime runner          = Ubuntu 24.04.5
Docker Compose          = v2.38.2
```

The Runtime job executed the real repository Compose asset and verified:

1. `docker compose config` renders successfully.
2. Qdrant image `qdrant/qdrant:v1.20.0` pulls successfully.
3. `docker compose up -d --wait` reaches Docker `healthy` state.
4. `GET http://127.0.0.1:6333/readyz` returns `all shards are ready`.
5. Qdrant root endpoint reports:

```text
version = 1.20.0
commit  = 222b2e44ab1c3f17e8246396ead6558e45041df7
```

6. Published ports are loopback-only 6333-6334.
7. Docker creates the accepted named volume `sgokb_qdrant_storage`.
8. Normal `docker compose down` removes the container/network but preserves the named volume.
9. A subsequent `docker compose up -d --wait` reuses the volume and becomes healthy again.
10. `/readyz` succeeds again after recreation.
11. A second normal `down` still leaves the volume intact.

Result:

```text
real Qdrant runtime creation          = PASS
/readyz healthcheck                   = PASS
exact Qdrant v1.20.0 runtime          = PASS
loopback port contract                = PASS
named-volume creation                 = PASS
normal-down volume persistence        = PASS
recreate / second readiness           = PASS
```

## 6. Windows regression acceptance

The final run separates real Docker runtime acceptance from the SGOKB Windows regression gate. This is intentional:

- Docker runtime behavior is verified on an Actions runner with Docker Engine available.
- SGOKB repository compatibility is verified on the established Windows Server 2025 acceptance environment with full Git history and Qt offscreen mode.

Final Windows gate:

```text
runner                     = Microsoft Windows Server 2025
Python                     = 3.10.11
QT_QPA_PLATFORM            = offscreen
checkout                   = fetch-depth: 0
focused P-RUNTIME-02       = 2 / 2 PASS
Ruff src/tests             = PASS
full repository regression = 839 / 839 PASS
warnings                   = 2 known local-Qdrant warnings
```

The two warnings are unchanged known behavior from Qdrant local mode:

- payload indexes have no effect in local Qdrant except supported text-index cases;
- local mode performs brute-force search, so normal search parameters do not affect approximate-search behavior.

They do not affect the server-Qdrant Compose acceptance.

## 7. Historical verification attempts

### Attempt 01 — lint-only failure

The initial workflow rendered Compose successfully and passed the focused tests, but Ruff rejected import formatting in the new focused test. No Runtime acceptance was claimed. The import formatting was corrected.

### Attempt 02 — Runtime PASS / invalid full-regression environment

The second workflow successfully completed the real Qdrant runtime checks, including named-volume preservation and recreation. Its full-repository regression was run on Ubuntu with a shallow checkout and was not a valid SGOKB full-regression environment:

- GUI tests lacked the runner Qt/EGL environment expected by the accepted Windows gate;
- historical-commit audit tests lacked full Git history;
- platform-sensitive frozen benchmark checks differed.

These failures were not attributed to the Compose runtime assets. The final workflow therefore separated the real Docker runtime job from the established Windows full-regression job.

### Attempt 03 — final acceptance

Run `40961873913` passed both jobs completely and is the acceptance authority for P-RUNTIME-02.

## 8. Operational documentation acceptance

`docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md` now defines:

- prerequisites;
- fresh installation/start commands;
- startup, stop, restart, and normal shutdown commands;
- persistent volume identity and destructive-volume warnings;
- local port/security boundary;
- logs and troubleshooting probes;
- explicit version upgrade workflow;
- snapshot protection before upgrade;
- rollback boundary that forbids blind binary downgrade against possibly migrated storage;
- fresh-environment command sequence.

Qdrant Vector Index data remains derived runtime state under the existing SGOKB safety/recovery model. The upgrade snapshot procedure protects runtime state operationally; it does not redefine Qdrant as canonical Knowledge backup authority.

## 9. Disposition

The repository now contains a deterministic, version-pinned, local-only, persistent Qdrant Compose runtime that implements the P-RUNTIME-01 accepted design and has been exercised against the real pinned Qdrant server.

Therefore:

```text
P-RUNTIME-02 = Complete / Accepted
```

Next task:

```text
P-RUNTIME-03 — Runtime health/status application boundary
```
