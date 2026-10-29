# P-RUNTIME-03 — Runtime Health / Status Application Boundary

Date: 2026-10-30
Status: **Complete / Accepted**
Task: `P-RUNTIME-03 [P1] Runtime health/status application boundary`

## 1. Purpose

P-RUNTIME-03 defines one transport-neutral observation model for the runtime state needed by CLI and the future P-GUI-09 Runtime Dashboard.

The boundary is deliberately observational. Qdrant remains the external shared runtime selected by P-RUNTIME-01 and materialized by P-RUNTIME-02. SGOKB does not gain ownership of Docker Desktop, the Docker daemon, or the Qdrant container.

## 2. Shared transport surface

The existing shared operation remains the transport entry point:

```text
system.status
```

Its historical fields are preserved. P-RUNTIME-03 adds:

```text
system.status.runtime_health
```

with schema:

```text
sgokb.runtime-health/1.0
```

CLI, GUI worker, and any future transport that uses `OperatorSession` therefore receive the same runtime projection without invoking CLI subprocesses or duplicating runtime logic in Qt.

## 3. Health model

Top-level shape:

```text
schema_version
  = sgokb.runtime-health/1.0

overall_status
  = healthy | degraded | unavailable

lifecycle
  qdrant_owner = external
  observe      = true
  start        = false
  stop         = false
  restart      = false

components
  sqlite
  embedding
  qdrant
  generation
  derived
```

Component status values are:

```text
healthy
  the observed component contract is available

degraded
  the component exists but a required current-state invariant is not satisfied

unavailable
  the component could not be reached or its required dependency is unavailable

not_configured
  the component has no applicable active state yet, for example an empty database with
  no active Search generation
```

`not_configured` does not by itself degrade the overall status. `degraded` or `unavailable` on a non-SQLite component produces an overall `degraded` state. An unavailable SQLite connection makes the runtime snapshot `unavailable`.

## 4. Stable component issue contract

A component failure does not normally fail the `system.status` operation. Instead the affected component carries:

```text
issue.category
issue.code
issue.message
```

Categories reuse the shared operation taxonomy where applicable, especially:

```text
runtime
integrity
```

Initial stable issue codes include:

```text
sqlite_health_unavailable
sqlite_runtime_degraded
embedding_dependency_unavailable
qdrant_endpoint_unavailable
qdrant_readiness_failed
qdrant_collection_unavailable
generation_not_active
active_generation_missing
generation_runtime_degraded
derived_state_incomplete
```

This lets GUI presentation map a component state to badges/actions without parsing exception class names or provider-specific text.

## 5. SQLite probe

The SQLite component observes the already-open operation-scoped Repository connection. It checks:

- a trivial read succeeds;
- `PRAGMA foreign_keys` is active;
- current journal mode is reported;
- the database path is reported.

P-RUNTIME-03 does not duplicate the full `system.integrity` scan. Runtime status is a low-cost observation path; formal integrity remains the existing dedicated operation.

## 6. Embedding provider probe

Runtime status must not load or download the frozen Harrier model merely because an operator opens a dashboard.

The default Embedding probe is therefore deliberately shallow:

- reports the frozen provider/model/revision configuration;
- reports cache path and `local_files_only` policy;
- checks local Python dependency availability;
- reports an already-cached semantic runtime if one exists;
- reports a GUI native-preload failure if one was already observed;
- does **not** call the provider factory;
- does **not** run inference;
- does **not** download model files.

This distinguishes a health/status read from a semantic-runtime activation. A later semantic operation remains authoritative for full model-load/inference readiness.

## 7. Qdrant probe

Qdrant is actively probed because P-RUNTIME-02 defines `/readyz` as the runtime readiness authority.

P-RUNTIME-03 observes:

```text
configured HTTP endpoint
configured gRPC port
prefer_grpc setting
collection prefix
GET /readyz
GET /
GET /collections
server version
available collections
expected active-generation Qdrant collections
missing expected collections
```

The probe is HTTP-only and read-only. It does not invoke Docker, Compose, PowerShell, WSL, or Qdrant lifecycle commands.

An endpoint failure is component-level `unavailable`. A live Qdrant server with a missing collection referenced by the active Search generation is `degraded` with `qdrant_collection_unavailable`.

## 8. Search generation probe

The generation component reuses the canonical `KnowledgeSearchGenerationApplication` persisted state and reports:

- active generation ID;
- activation revision;
- active generation row;
- active Vector bindings;
- current canonical source-catalog digest;
- whether the active generation source catalog is current.

A non-empty Knowledge catalog without an active generation is degraded. An empty database without an active generation is `not_configured`.

An active generation is healthy only when:

- its persisted state is `ready`;
- its source-catalog digest matches current canonical Knowledge;
- at least one active Vector binding exists;
- every active binding is `ready`.

Live collection existence is checked separately by the Qdrant component.

## 9. Derived-state probe

For every Object with a current accepted Version, the boundary aggregates existing derived lifecycle records by:

- status;
- derived kind;
- missing-state Object IDs;
- total unhealthy count.

Any current Object with `pending`, `stale`, `failed`, or missing derived state makes this component degraded. No rebuild is triggered by the health read.

## 10. GUI / CLI boundary

CLI already routes `system.status` through `OperatorSession` and receives the new runtime projection automatically.

The GUI backend also accepts arbitrary shared `OperationRequest` values and executes them on its dedicated backend QThread. P-GUI-09 can therefore request `system.status` and render `runtime_health` without:

- constructing a Qdrant client in a Qt view;
- importing CLI parser/renderer code;
- starting/stopping Qdrant;
- invoking Docker subprocesses;
- duplicating error classification.

P-RUNTIME-03 intentionally does not add Runtime Dashboard widgets. That presentation work remains P-GUI-09.

## 11. Lifecycle ownership invariant

The health schema explicitly publishes:

```text
qdrant_owner = external
start        = false
stop         = false
restart      = false
```

P-RUNTIME-03 therefore cannot accidentally evolve an observation call into a container/process manager. P-RUNTIME-04 owns Windows login auto-start acceptance. P-RUNTIME-05/P-GUI-09 may expose status and operator guidance, but they must preserve this ownership boundary unless a later explicit architecture decision replaces it.

## 12. Authority

- P-RUNTIME-01: `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`
- P-RUNTIME-02: `docs/evaluation/P_RUNTIME_02_QDRANT_COMPOSE_CONFIGURATION_ACCEPTANCE.md`
- P-RUNTIME-03 acceptance: `docs/evaluation/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_ACCEPTANCE.md`
- shared operator decision: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- implementation: `src/sgokb/runtime_health.py`
- shared system surface: `src/sgokb/application_system.py`
