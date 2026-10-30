# P-RUNTIME-05 — GUI Runtime Dashboard Acceptance

Date: 2026-10-31  
Task: `P-RUNTIME-05 [P1] GUI Runtime Dashboard integration`  
PR: `#82 P-RUNTIME-05 integrate GUI Runtime Dashboard`

## Status

**Implementation complete / Local acceptance in progress**

GitHub-hosted Actions are unavailable under the current account billing/spending limit. The observed GitHub Actions annotation states that the job was not started because recent account payments failed or the spending limit must be increased. P-RUNTIME-05 therefore uses the supported Windows workstation for acceptance, while preserving hosted CI as separate deferred verification.

## Implemented contract

```text
source operation       = system.status
projection             = data.runtime_health
schema                 = sgokb.runtime-health/1.0
GUI surface            = System > Overview
Qdrant lifecycle owner = external
observe                = true
start/stop/restart     = false / false / false
```

The dashboard adds Semantic Search readiness, component-level status, issue reasons and troubleshooting entrypoints without changing the P-RUNTIME-03 backend contract.

## Local acceptance evidence — 2026-10-31

### Focused P-RUNTIME-05 / System / runtime boundary

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_p_runtime_05_gui_runtime_dashboard.py `
  tests/test_p_gui_09_system_maintenance.py `
  tests/test_p_runtime_03_runtime_health_boundary.py `
  tests/test_p_gui_06_search_runtime_state.py
```

Observed result on pre-style-remediation HEAD `3810cab6d228db918f7b30d098037baabecb89e0`:

```text
22 passed in 8.96s
```

Disposition: **PASS**.

### Ruff

Command:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
```

Observed result on the same pre-style-remediation HEAD:

```text
9 x E501 line-too-long findings
```

All nine findings were confined to P-RUNTIME-05 additions in:

- `src/sgokb/gui/runtime_dashboard.py`
- `tests/test_p_runtime_05_gui_runtime_dashboard.py`

They were remediated by line wrapping only, without changing readiness logic or the runtime-health contract. Latest remediation HEAD after the style fixes is `91ebce0385e9a9ff01d67c373153b44943f8282e`.

Disposition: **REMEDIATED / re-run required on latest HEAD**.

### Full regression

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Observed result on pre-style-remediation HEAD `3810cab6d228db918f7b30d098037baabecb89e0`:

```text
869 passed, 2 warnings in 250.83s
```

The two warnings are the known accepted local-Qdrant warnings:

1. local Qdrant payload indexes have no effect;
2. local exact-search mode ignores `search_params` except `idf`.

No test failures or new warnings were observed.

Disposition: **PASS on pre-style-remediation HEAD**. Because the subsequent patch is line wrapping only, the regression evidence remains informative, but final closure should record at least focused tests and Ruff on the latest HEAD.

### Reference Workspace CLI projection

Database:

```text
.local/acceptance/sgokb-happy-path.sqlite
```

Observed authoritative runtime-health snapshot:

```text
schema                 = sgokb.runtime-health/1.0
overall_status          = degraded
sqlite                  = healthy
embedding               = healthy
qdrant                  = healthy
qdrant.ready            = true
qdrant.version          = 1.19.2
generation              = degraded
generation issue        = generation_not_active
derived                 = degraded
derived issue           = derived_state_incomplete
qdrant_owner            = external
observe                 = true
start/stop/restart      = false / false / false
```

Reference details relevant to P-RUNTIME-05:

- SQLite is healthy, WAL active, foreign keys enabled.
- Embedding dependencies are healthy and configured but not loaded by the shallow probe.
- Qdrant `http://localhost:6333` is healthy and `/readyz` is ready.
- Qdrant version is `1.19.2`.
- no active Search generation is selected while five current Objects exist;
- Derived state has 17 ready states and 3 pending `rendering` states;
- semantic kinds `search_representation`, `embedding`, and `vector_index` are all ready for all five current Objects;
- the top-level degraded state therefore must not be represented as Qdrant failure or a hard Semantic Search block.

Expected dashboard interpretation for this reference snapshot:

```text
Semantic Search readiness = degraded
hard blocker             = none
warning 1                = no active Search generation; legacy vector routing may be used
warning 2                = non-semantic derived state is incomplete
Qdrant                    = healthy / ready / v1.19.2
lifecycle                 = external observer-only
```

This is the intended P-RUNTIME-05 distinction between overall runtime degradation and actual semantic-runtime unavailability.

Disposition: **PASS**.

## Remaining local gates

### 1. Re-run latest-head focused tests and Ruff

After pulling HEAD `91ebce0385e9a9ff01d67c373153b44943f8282e` or later:

```powershell
git pull

.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_p_runtime_05_gui_runtime_dashboard.py `
  tests/test_p_gui_09_system_maintenance.py `
  tests/test_p_runtime_03_runtime_health_boundary.py `
  tests/test_p_gui_06_search_runtime_state.py

.\.venv\Scripts\python.exe -m ruff check src tests
```

Required: all PASS.

### 2. GUI reference-workspace smoke

Open the same Workspace in the Desktop GUI and navigate to `System > Overview`.

Verify:

- `Semantic Search readiness` is visible before opening the Search page;
- SQLite, Embedding, Qdrant, Search generation and Derived state are individually visible;
- the displayed status/reasons agree with the CLI `system status` snapshot;
- the reference state is shown as Semantic Search `DEGRADED`, not `BLOCKED`;
- Qdrant is shown as healthy/ready rather than unavailable;
- generation guidance identifies the inactive Search generation and legacy-routing condition;
- Derived state degradation is shown as a warning rather than a semantic hard blocker because only `rendering` is pending;
- runtime issue text exposes a useful troubleshooting entrypoint;
- Qdrant lifecycle note says ownership is external;
- no Qdrant start/stop/restart control exists;
- MCP note does not invent MCP health state and points to the existing MCP tab;
- raw `system.status` JSON remains visible after refresh.

## Current disposition

```text
focused runtime/dashboard tests = PASS on 3810cab; latest-head re-run pending
Ruff                            = FAIL on 3810cab -> remediated; re-run pending
full regression                 = PASS, 869 passed / 2 known warnings
reference CLI projection        = PASS
GUI reference-workspace smoke   = pending
P-RUNTIME-03 lifecycle boundary = preserved
new regressions                 = none observed

P-RUNTIME-05 overall            = In Progress / Final Local Verification Pending
```

After the latest-head focused tests, Ruff and GUI smoke pass, update this document with the final tested HEAD, mark P-RUNTIME-05 `Complete / Accepted`, and merge PR #82.
