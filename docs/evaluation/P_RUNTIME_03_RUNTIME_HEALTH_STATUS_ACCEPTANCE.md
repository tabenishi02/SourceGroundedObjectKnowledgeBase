# P-RUNTIME-03 — Runtime Health / Status Application Boundary Acceptance

Date: 2026-10-30
Task: `P-RUNTIME-03 [P1] Runtime health/status application boundary`
Verdict: **PASS / Complete / Accepted**

## 1. Accepted scope

P-RUNTIME-03 adds a transport-neutral runtime observation model to the existing shared `system.status` operation.

The accepted contract is:

```text
system.status.runtime_health
schema_version = sgokb.runtime-health/1.0
```

The historical `system.status` fields remain available. CLI and GUI both reach the same Application/operator path; neither needs transport-specific runtime logic.

Observed components are:

- SQLite connection/runtime state;
- shallow Embedding provider/dependency/configuration state;
- Qdrant endpoint, readiness, version and collections;
- active Search generation and Vector bindings;
- current Object derived-state aggregate.

The health read is observational. It does not start, stop or restart Docker/Qdrant, trigger rebuilds, load the Harrier model, download model files, or run embedding inference.

## 2. Lifecycle ownership acceptance

The accepted model explicitly reports:

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

This satisfies the Phase P requirement that GUI can observe Qdrant/runtime state without becoming the Qdrant lifecycle owner.

P-RUNTIME-04 retains Windows login auto-start ownership. GUI presentation of this model remains later GUI work.

## 3. Error model acceptance

Component failures are represented inside the runtime-health snapshot with stable `category / code / message` issue data rather than normally failing the whole `system.status` operation.

The accepted status vocabulary is:

```text
healthy
degraded
unavailable
not_configured
```

A Qdrant readiness failure, for example, is returned as a runtime component issue rather than converting the read-only status operation into an exception path.

## 4. Final automated acceptance

Final GitHub Actions run:

```text
run                         = 40968417323
workflow                    = P-RUNTIME-03 acceptance / run #5
branch source               = 90f699a094d9426a7b26c1995b46fdb7ce377150
PR synthetic merge          = 1cbf1cabca97477e9932795c2ce5700ebe058897
```

### Runtime integration job — Ubuntu 24.04 / Python 3.10.22

```text
focused P-RUNTIME-03 tests  = 3 / 3 PASS
Ruff src/tests              = PASS
qdrant/qdrant:v1.20.0       = started / healthy
P-RUNTIME-02 /readyz        = PASS
system.status SQLite health = healthy
system.status Qdrant health = healthy
reported Qdrant version     = 1.20.0
observer-only lifecycle     = PASS
job conclusion              = PASS
```

The real Compose runtime exposed only the accepted loopback ports `6333` and `6334`, reached healthy state, and the runtime-health Application boundary successfully observed the live server.

### Windows regression job — Windows Server 2025 / Python 3.10.11

```text
focused P-RUNTIME-03 tests  = 3 / 3 PASS
Ruff src/tests              = PASS
full repository regression  = 842 / 842 PASS
warnings                    = 2 known local-Qdrant warnings
job conclusion              = PASS
```

The two warnings are the pre-existing local-Qdrant warnings about local payload-index behavior and brute-force search parameters. No new warning or regression is introduced by P-RUNTIME-03.

## 5. Historical verification note

An earlier acceptance attempt reported one full-regression failure after the focused/Ruff/runtime-integration gates had passed. The diagnostic rerun used the same implementation with verbose fail-fast full regression and did **not** reproduce the failure:

```text
842 collected
842 passed
```

No product-code relaxation or test exclusion was used to obtain the final PASS.

## 6. Accepted implementation authority

- design / contract: `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- runtime projection: `src/sgokb/runtime_health.py`
- shared system operation integration: `src/sgokb/application_system.py`
- runtime factory observation support: `src/sgokb/runtime.py`
- focused acceptance: `tests/test_p_runtime_03_runtime_health_boundary.py`
- Qdrant reference runtime: `runtime/qdrant/compose.yaml`

## 7. Final disposition

```text
P-RUNTIME-03 = Complete / Accepted
P-GUI-09     = Unblocked / Next in Phase P sequencing
```

P-RUNTIME-03 establishes the shared health/status Application boundary only. Runtime Dashboard presentation is not part of this task, and Qdrant lifecycle ownership remains external to SGOKB.