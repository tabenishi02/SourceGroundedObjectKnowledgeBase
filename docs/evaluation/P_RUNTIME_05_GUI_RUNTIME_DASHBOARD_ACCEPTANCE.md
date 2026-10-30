# P-RUNTIME-05 — GUI Runtime Dashboard Acceptance

Date: 2026-10-31  
Task: `P-RUNTIME-05 [P1] GUI Runtime Dashboard integration`  
PR: `#82 P-RUNTIME-05 integrate GUI Runtime Dashboard`

## Status

**Implementation complete / Local acceptance pending**

GitHub-hosted Actions are unavailable under the current account billing/spending limit. P-RUNTIME-05 therefore uses the supported Windows workstation for acceptance, while preserving hosted CI as separate deferred verification.

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

## Required local gates

Run from the repository root on branch `phase-p/runtime-05-gui-runtime-dashboard`.

### 1. Focused P-RUNTIME-05 / System / runtime boundary

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_p_runtime_05_gui_runtime_dashboard.py `
  tests/test_p_gui_09_system_maintenance.py `
  tests/test_p_runtime_03_runtime_health_boundary.py `
  tests/test_p_gui_06_search_runtime_state.py
```

Required: all PASS.

### 2. Ruff

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
```

Required: PASS.

### 3. Full regression

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Required: zero failures. Existing accepted local-Qdrant warnings must be distinguished from new warnings.

### 4. Reference Workspace CLI projection

With the existing acceptance DB:

```powershell
$Db = ".local/acceptance/sgokb-happy-path.sqlite"
.\.venv\Scripts\sgokb.exe --db $Db system status
```

Record the authoritative runtime-health snapshot used for the GUI comparison.

### 5. GUI smoke

Open the same Workspace in the Desktop GUI and navigate to `System > Overview`.

Verify:

- `Semantic Search readiness` is visible before opening the Search page;
- SQLite, Embedding, Qdrant, Search generation and Derived state are individually visible;
- the displayed status/reasons agree with the CLI `system status` snapshot;
- the known reference state with Qdrant healthy but inactive Search generation is represented as degraded guidance rather than falsely reporting Qdrant unavailable;
- runtime issue text exposes a useful troubleshooting entrypoint;
- Qdrant lifecycle note says ownership is external;
- no Qdrant start/stop/restart control exists;
- MCP note does not invent MCP health state and points to the existing MCP tab;
- raw `system.status` JSON remains visible after refresh.

## Acceptance disposition template

```text
focused runtime/dashboard tests = PASS / FAIL
Ruff                            = PASS / FAIL
full regression                 = PASS / FAIL
GUI reference-workspace smoke   = PASS / FAIL
P-RUNTIME-03 lifecycle boundary = preserved / violated
new regressions                 = none / describe

P-RUNTIME-05 overall            = Pending
```

After all gates pass, update this document with exact counts, tested HEAD and reference-workspace observations, then mark P-RUNTIME-05 `Complete / Accepted` and merge PR #82.
