# P-RUNTIME-05 — GUI Runtime Dashboard Operator Guide

Date: 2026-10-31  
Task: `P-RUNTIME-05 [P1] GUI Runtime Dashboard integration`  
Target GUI surface: `System > Overview`

## Purpose

This guide explains how to open the SGOKB Desktop GUI, select the existing acceptance Workspace, inspect the Runtime Dashboard, refresh the runtime snapshot, and interpret the result for P-RUNTIME-05 acceptance.

This procedure is read-only for the Runtime Dashboard. It does not start, stop, or restart Qdrant and does not require any maintenance action.

## Preconditions

Run from:

```text
C:\codex\SourceGroundedObjectKnowledgeBase
```

Use branch:

```text
phase-p/runtime-05-gui-runtime-dashboard
```

Update the branch first:

```powershell
cd C:\codex\SourceGroundedObjectKnowledgeBase
git pull
```

The reference Workspace used for acceptance is:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\sgokb-happy-path.sqlite
```

Qdrant should already be running through the externally owned Windows runtime. P-RUNTIME-05 does not manage Qdrant lifecycle.

## 1. Start the Desktop GUI

From PowerShell:

```powershell
.\.venv\Scripts\sgokb-gui.exe
```

Alternative launcher, if the generated entrypoint is unavailable:

```powershell
.\.venv\Scripts\python.exe -m sgokb.gui.main
```

Expected result:

- an `SGOKB` desktop window opens;
- the left navigation contains `Home / Dashboard`, `Objects`, `Sources`, `Evidence`, `Associations`, `Search`, `Packages`, `Results`, `Registry`, `System`, and `Settings`;
- if no Workspace is open, the status bar shows `No workspace`.

## 2. Open the reference Workspace

Use one of these equivalent methods:

- menu: `File > Open Workspace...`;
- shortcut: `Ctrl+O`;
- `Home / Dashboard > Open Workspace...`.

In the file chooser, select:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\sgokb-happy-path.sqlite
```

Then click `Open`.

Expected result:

- the window title changes to include the Workspace name;
- the status bar shows the Workspace path;
- a temporary `Workspace ready` message may appear;
- the Home page shows Object / current Knowledge / migration summary data.

If the Workspace does not open, stop the acceptance procedure and record the displayed error. Do not create a new Workspace as a substitute.

## 3. Open the Runtime Dashboard

In the left navigation, click:

```text
System
```

The page title is:

```text
System / Maintenance
```

Select the first tab:

```text
Overview
```

For P-RUNTIME-05 acceptance, do not use `Derived`, `Vector Index`, `Backup`, `Restore`, `MCP`, or `Advanced Generation` unless a later troubleshooting step explicitly requires them.

## 4. Refresh the runtime snapshot

On `System > Overview`, click:

```text
Refresh system status
```

Wait until the operation finishes. The dashboard should update from the same `system.status.runtime_health` projection used by the CLI.

The page contains these sections:

1. `Runtime health` summary line;
2. `Semantic Search readiness`;
3. `Runtime components`;
4. Qdrant lifecycle ownership note;
5. MCP visibility note;
6. `Runtime issues / troubleshooting`;
7. raw `system.status` JSON readout at the bottom.

The `Run integrity check` button is not required for the normal P-RUNTIME-05 smoke test.

## 5. Read the Runtime health summary

The top summary uses the form:

```text
Runtime health: overall=<status> | Semantic Search=<status>
```

The two statuses are intentionally different concepts.

- `overall` summarizes the complete runtime-health snapshot;
- `Semantic Search` answers whether semantic retrieval dependencies are ready, degraded, blocked, or unknown.

Therefore an overall `degraded` result does not automatically mean Semantic Search is blocked.

## 6. Read Semantic Search readiness

The readiness box can show:

```text
READY
DEGRADED
BLOCKED
UNKNOWN
```

Interpretation:

- `READY`: required semantic runtime dependencies are healthy;
- `DEGRADED`: semantic dependencies are available, but warnings exist;
- `BLOCKED`: at least one dependency prevents a safe ready claim;
- `UNKNOWN`: the runtime-health schema or required component data cannot be interpreted.

For the current reference Workspace, the expected result is:

```text
DEGRADED
```

It must not be `BLOCKED` solely because no active Search generation is selected or because only rendering-derived state is pending.

## 7. Read the Runtime components

The dashboard shows five components separately.

### SQLite

Expected reference state:

```text
HEALTHY
journal=wal
```

A SQLite non-healthy state is a semantic hard blocker.

### Embedding

Expected reference state includes:

```text
HEALTHY
microsoft/harrier-oss-v1-0.6b
configured_not_loaded
```

`configured_not_loaded` is valid for the shallow health probe. It does not mean the embedding runtime is unavailable.

### Qdrant

Expected reference state:

```text
HEALTHY
http://localhost:6333
ready
v1.19.2
```

The dashboard is an observer only. It must not expose Qdrant Start / Stop / Restart controls.

### Search generation

Expected reference state:

```text
DEGRADED
active=none (legacy routing)
Knowledge exists but no active Search generation is selected
```

For this accepted reference state, this is a warning rather than a hard semantic blocker because legacy vector routing remains available.

### Derived state

Expected reference state:

```text
DEGRADED
current objects=5
unhealthy states=3
```

The current three unhealthy states are expected `rendering` pending states. The semantic kinds `search_representation`, `embedding`, and `vector_index` are ready, so this condition must be presented as a warning, not as a hard Semantic Search blocker.

## 8. Check Runtime issues / troubleshooting

The troubleshooting box should explain degraded or blocked components.

For the current reference Workspace, confirm that it contains guidance for:

- inactive Search generation / legacy routing;
- incomplete Derived state;
- the corresponding System tabs to inspect when needed.

A useful runtime issue must not be represented only by a generic `degraded` label with no reason.

## 9. Check Qdrant lifecycle ownership

Confirm that the lifecycle note states that Qdrant is externally owned and that SGOKB only observes runtime health.

The accepted lifecycle contract is:

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

There must be no Qdrant Start / Stop / Restart control on the Runtime Dashboard.

## 10. Check the MCP note

Confirm that the Overview page does not invent an MCP health state.

The note should state that MCP runtime state is not part of `sgokb.runtime-health/1.0` and should direct the operator to the existing `MCP` tab for the stdio launch/configuration contract.

## 11. Check the raw system.status JSON

After `Refresh system status`, scroll to the read-only JSON area at the bottom of the Overview tab.

Confirm that the raw output remains visible and contains:

```text
"runtime_health"
```

For the current reference Workspace, the authoritative values should include:

```text
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
```

The structured dashboard and raw JSON must describe the same runtime snapshot.

## 12. P-RUNTIME-05 acceptance checklist

Record PASS / FAIL for each item:

```text
[ ] GUI starts successfully
[ ] reference Workspace opens successfully
[ ] System > Overview is reachable
[ ] Refresh system status completes
[ ] Runtime health summary is visible
[ ] Semantic Search readiness is visible
[ ] Semantic Search = DEGRADED, not BLOCKED, for the reference Workspace
[ ] SQLite = HEALTHY
[ ] Embedding = HEALTHY
[ ] Qdrant = HEALTHY / ready / v1.19.2
[ ] Search generation = DEGRADED / inactive generation guidance visible
[ ] Derived state = DEGRADED / rendering-only warning visible
[ ] troubleshooting text explains the degraded conditions
[ ] Qdrant lifecycle owner is external
[ ] no Qdrant Start / Stop / Restart controls exist
[ ] MCP note points to the MCP tab without inventing health state
[ ] raw system.status JSON remains visible after refresh
[ ] structured dashboard agrees with the CLI runtime-health snapshot
```

If every item passes, report:

```text
GUI reference-workspace smoke = PASS
```

If any item fails, record the exact displayed text and which checklist item failed. Do not compensate by changing canonical data or running maintenance operations unless a separate remediation task is opened.

## Troubleshooting startup only

If `sgokb-gui.exe` is not found, first confirm the virtual environment and GUI dependency:

```powershell
Test-Path .\.venv\Scripts\python.exe
Test-Path .\.venv\Scripts\sgokb-gui.exe
.\.venv\Scripts\python.exe -c "import PySide6; print(PySide6.__version__)"
```

If the executable is absent but PySide6 imports correctly, use:

```powershell
.\.venv\Scripts\python.exe -m sgokb.gui.main
```

Do not reinstall or modify the environment as part of the acceptance test unless startup actually fails and the cause has been identified.

## Related documents

- `docs/design/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD.md`
- `docs/evaluation/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md`
- `docs/planning/phases/P/PHASE_P_STATUS.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
