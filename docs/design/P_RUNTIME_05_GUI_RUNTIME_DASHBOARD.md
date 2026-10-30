# P-RUNTIME-05 — GUI Runtime Dashboard Design

Date: 2026-10-31  
Task: `P-RUNTIME-05 [P1] GUI Runtime Dashboard integration`

## 1. Purpose

Expose semantic-runtime state in the existing Desktop System surface so an operator can judge runtime insufficiency before running Semantic Search, without making the GUI a runtime lifecycle owner.

The authoritative backend projection remains P-RUNTIME-03:

```text
operation   = system.status
projection  = data.runtime_health
schema      = sgokb.runtime-health/1.0
components  = sqlite / embedding / qdrant / generation / derived
```

No new public runtime API is introduced by P-RUNTIME-05.

## 2. UI integration

The existing `System / Maintenance > Overview` page remains the runtime entrypoint. P-RUNTIME-05 adds a structured dashboard above the existing raw `system.status` JSON:

```text
Runtime health overall summary
Semantic Search readiness
Runtime components
  SQLite
  Embedding
  Qdrant
  Search generation
  Derived state
Qdrant lifecycle boundary
MCP visibility note
Runtime issues / troubleshooting
Refresh system status / integrity check
Raw system.status JSON
```

The raw projection remains visible so the dashboard does not hide authoritative details.

## 3. Presentation boundary

`src/sgokb/gui/runtime_dashboard.py` is a pure presentation layer. It accepts a `sgokb.runtime-health/1.0` mapping and returns immutable presentation records. It performs no I/O, database access, process control, Qdrant lifecycle action, or semantic model load.

`RuntimeDashboardSystemPage` subclasses the accepted P-GUI-09 `SystemPage`. The MainWindow uses the subclass for the normal System navigation surface while retaining all existing maintenance tabs and operations.

## 4. Semantic Search readiness semantics

The dashboard does not equate `runtime_health.overall_status` with Semantic Search availability. The overall status can be degraded by unrelated replaceable derived work such as rendering.

### Blocked

Semantic Search is shown as `blocked` when an observed dependency makes semantic retrieval unavailable or unsafe to claim as ready:

- SQLite is not healthy;
- local Embedding runtime is not healthy;
- Qdrant is not healthy or `/readyz` is not ready;
- the active generation pointer is broken;
- an active generation / vector binding is not current and ready, including a missing expected Qdrant collection.

### Degraded

The dashboard shows `degraded` when runtime dependencies remain available but the operator should review state before relying on full semantic freshness:

- Knowledge exists but no active Search generation is selected. Current retrieval code can fall back to legacy vector routing, so this is not automatically classified as a hard runtime block;
- semantic derived kinds (`search_representation`, `embedding`, `vector_index`) have non-ready state;
- non-semantic derived state such as rendering is incomplete.

### Ready

`ready` requires the observed SQLite, Embedding, Qdrant, generation-integrity and semantic-derived checks to expose no blocker or warning.

### Unknown

An unsupported runtime-health schema or missing required component data results in `unknown`. The GUI must not claim semantic readiness from a projection it does not understand.

These labels are preflight guidance. The Search Application remains the execution authority: pure Semantic errors still fail, and Hybrid Search continues to expose `degraded_channels` according to the existing retrieval contract.

## 5. Component summaries and troubleshooting

Each component shows its status plus selected non-secret details:

- SQLite: Workspace DB path and journal mode;
- Embedding: configured model and shallow/load readiness;
- Qdrant: endpoint, `/readyz` state, version and missing-collection count;
- Search generation: active generation identity and source-catalog currency;
- Derived: current Object count and unhealthy derived-state count.

If a component is not healthy, the dashboard shows its authoritative `issue.message` and a GUI troubleshooting entrypoint. Troubleshooting does not mutate runtime automatically.

## 6. Lifecycle safety

P-RUNTIME-03 remains unchanged:

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

P-RUNTIME-05 must not add Qdrant start/stop/restart buttons, background supervision, Task Scheduler mutation, Docker lifecycle ownership, or hidden process-control paths.

## 7. MCP scope

`sgokb.runtime-health/1.0` has no MCP component. P-RUNTIME-05 therefore does not invent MCP health state.

The dashboard states that MCP runtime health is not included in the current runtime-health schema and points the operator to the existing MCP tab for the external stdio launch/configuration contract.

## 8. Compatibility

- CLI `system status` output is unchanged.
- P-RUNTIME-03 schema is unchanged.
- Existing System / Maintenance operations are unchanged.
- Existing Search execution semantics are unchanged.
- The GUI still reaches backend operations through the shared `BackendCoordinator` / Application boundary.
- The existing raw JSON status remains available.

## 9. Acceptance

P-RUNTIME-05 local acceptance requires:

1. pure presenter tests for ready, blocked, degraded and unknown states;
2. Qdrant unavailable/missing-collection coverage;
3. generation and derived-state semantic distinctions;
4. GUI binding test on the System Overview;
5. explicit absence of GUI Qdrant lifecycle controls;
6. existing P-GUI-09 System tests remain green;
7. P-RUNTIME-03 boundary tests remain green;
8. Ruff passes;
9. full repository regression passes;
10. a local GUI smoke confirms an operator can inspect runtime readiness before Semantic Search.

Hosted GitHub Actions are currently unavailable due the documented account billing/spending limit and are not a prerequisite for starting local P-RUNTIME-05 acceptance.
