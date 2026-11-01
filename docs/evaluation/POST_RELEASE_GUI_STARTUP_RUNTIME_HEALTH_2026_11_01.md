# Post-release GUI startup / Runtime health update

Updated: 2026-11-01

- Repository authority: current `main`
- Baseline release: `v2.0.0` (immutable; tag not changed)
- Scope: Windows GUI launch UX and Runtime Dashboard Search-generation health semantics
- Status: **Implemented on `main`; execution verification pending operator/local regression**

## 1. Requirements

The post-release update implements three operator requirements:

1. Launch the GUI from a script without leaving a script/console window open.
2. Show a loading surface immediately during GUI startup.
3. Stop reporting the supported no-explicit-generation compatibility route as `DEGRADED`; show `Search generation = HEALTHY` when legacy routing is the active valid route.

## 2. Consoleless Windows launcher

Added:

```text
scripts/launch-sgokb-gui.vbs
```

The launcher:

- resolves the repository root relative to the script location;
- requires `.venv\Scripts\pythonw.exe`;
- sets the working directory to the repository root;
- launches `pythonw.exe -m sgokb.gui.main`;
- relies on the normal Windows `wscript.exe` host for `.vbs` plus `pythonw.exe`, so no console/script window remains open;
- uses `WScript.Shell.Run(..., 1, False)`: the launched Qt application is allowed to display normally while the script does not wait for GUI termination;
- reports a visible error only when the expected virtual-environment `pythonw.exe` is missing.

Normal Windows launch path:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\scripts\launch-sgokb-gui.vbs
```

## 3. Immediate startup loading surface

Changed:

```text
src/sgokb/gui/bootstrap.py
src/sgokb/gui/main.py
```

Startup order is now:

```text
pythonw / sgokb.gui.main
  -> QApplication
  -> show QSplashScreen
  -> paint event flush
  -> import SGOKB runtime/view modules
  -> preload local semantic native dependencies on Qt main thread
  -> construct BackendCoordinator / MainWindow
  -> show MainWindow
  -> finish splash
  -> Qt event loop
```

The splash therefore appears before SGOKB runtime/view imports and before the PyTorch / Transformers / Sentence Transformers native preload. The accepted safety contract is preserved: semantic native preload still occurs on the Qt main thread before `BackendCoordinator` creates the worker QThread.

Current splash phases are:

```text
SGOKB
Starting...

SGOKB
Loading application modules...

SGOKB
Loading local semantic runtime...

SGOKB
Preparing workspace UI...
```

## 4. Search generation health correction

Changed:

```text
src/sgokb/runtime_health.py
```

### 4.1 Root cause

The previous runtime-health projection treated this state as degraded:

```text
current accepted Knowledge exists
AND
knowledge_search_active_generation has no explicit pointer
```

That conflicted with the actual retrieval contract. Generation-aware Search/Vector routing explicitly supports the no-pointer state as the historical Phase-I / legacy compatibility route.

Consequently the Runtime Dashboard could show:

```text
Search generation  DEGRADED
active=none (legacy routing)
```

even while the supported legacy route was operating normally.

### 4.2 Corrected contract

The health projection now distinguishes supported routing from actual failure:

```text
No current accepted Knowledge + no pointer
  -> NOT_CONFIGURED

Current accepted Knowledge + no pointer
  -> HEALTHY
  -> routing_mode = legacy

Explicit active generation present and ready/current/bound
  -> HEALTHY
  -> routing_mode = generation

Explicit active pointer references missing generation
  -> DEGRADED

Explicit generation is stale/not ready or Vector binding is not ready
  -> DEGRADED
```

This is a health-classification correction only. It does not automatically build, cut over, or mutate Search generations and does not change canonical Knowledge.

For a normal legacy-routed Workspace the GUI Runtime Dashboard should now present:

```text
Search generation  HEALTHY
active=none (legacy routing)
```

## 5. Regression coverage

Added:

```text
tests/test_post_release_gui_startup_runtime_health.py
```

Coverage locks:

- the VBS launcher uses `pythonw.exe`, a normal visible Qt launch state, and non-waiting execution without a console host;
- accepted Knowledge with no explicit generation pointer is `HEALTHY` with `routing_mode=legacy`;
- Runtime Dashboard presents that state as `HEALTHY` and semantic readiness as `ready` when other runtime components are healthy;
- the splash is shown before SGOKB dependency loading, semantic native preload, and backend construction;
- the splash is finished only after the main window is shown.

Updated:

```text
tests/test_p_gui_04_shell.py
```

The historical preload-order test now disables the splash explicitly and continues to lock the required ordering:

```text
semantic native preload -> BackendCoordinator worker thread
```

## 6. Verification commands

Focused regression:

```powershell
python -m pytest -q tests/test_post_release_gui_startup_runtime_health.py tests/test_p_gui_04_shell.py tests/test_p_runtime_03_runtime_health_boundary.py tests/test_p_runtime_05_gui_runtime_dashboard.py
```

Static checks:

```powershell
python -m ruff check src tests
```

Operator smoke after pulling current `main`:

```text
1. Double-click scripts\launch-sgokb-gui.vbs.
2. Confirm no console/script window remains visible.
3. Confirm the SGOKB loading splash appears before the main window.
4. Open the existing Workspace.
5. Open System / Maintenance > Overview.
6. Refresh system status.
7. Confirm Search generation = HEALTHY and summary = active=none (legacy routing), unless an explicit broken generation is actually active.
```

The existing GitHub Actions Windows workflow is PR-triggered for `main` and does not run automatically for these direct `main` commits, so this document does not claim an unexecuted CI PASS.
