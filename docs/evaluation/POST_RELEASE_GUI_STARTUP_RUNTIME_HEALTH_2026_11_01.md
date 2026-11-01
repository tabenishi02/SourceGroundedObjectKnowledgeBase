# Post-release GUI startup / Runtime health update

Updated: 2026-11-01

- Repository authority: current `main`
- Baseline release: `v2.0.0` (immutable; tag not changed)
- Scope: Windows GUI launch UX and Runtime Dashboard Search-generation health semantics
- Status: **Local Windows regression PASS; implementation accepted on current `main`**

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

## 7. Local Windows execution verification — PASS

Execution host: `FNB1Main`

Verified source:

```text
main HEAD = a8ae38d9eb734b1f19e53177b5bf1cc77bdc9664
```

Focused regression and static checks:

```text
24 passed in 9.82s
Ruff src/tests = All checks passed!
```

Full repository regression:

```text
881 passed, 2 warnings in 282.06s
```

The two warnings are the existing local-Qdrant behavior warnings for payload indexes and local-mode search parameters; no new failure or warning class was introduced.

Real Workspace runtime-health verification used:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\gui-hp-49\sgokb.sqlite
```

Observed state:

```text
runtime_health.overall_status = healthy
generation.status             = healthy
generation.routing_mode       = legacy
generation.active_generation  = null
generation.current_object_count = 1
derived.status                = healthy
qdrant.status                 = healthy
```

This confirms the original false `DEGRADED` Search-generation projection is corrected on the accepted real-data GUI-HP-49 Workspace without creating or cutting over an explicit generation.

The VBS launcher was also executed through `wscript.exe`. Five seconds after invocation:

```text
matching wscript.exe launcher process = 0
pythonw.exe -m sgokb.gui.main         = running
launcher smoke                         = PASS
```

The spawned GUI processes were terminated after the smoke check. The process-level smoke confirms that the script host does not remain open and that the GUI entry point is launched through `pythonw.exe`. Splash sequencing is covered by the focused Qt regression, which locks `QSplashScreen` before SGOKB runtime imports/native semantic preload/backend construction and finishes it only after the main window is shown.

Disposition:

```text
Consoleless launcher       PASS
Startup splash sequencing  PASS
Search generation health   PASS
Focused regression         PASS / 24 passed
Ruff                       PASS
Full repository regression PASS / 881 passed / 2 known warnings
Post-release update        ACCEPTED on current main
```

No change is made to the immutable `v2.0.0` tag; this remains a post-release `main` update.
## 8. Interactive normality confirmation checklist

Purpose: perform an operator-visible normal-path confirmation of the three post-release additions after the automated/local regression above. This checklist is intentionally separate from automated acceptance because it verifies what the operator actually sees and experiences on the Windows desktop.

Recommended Workspace:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\gui-hp-49\sgokb.sqlite
```

Before starting, close any already-running SGOKB GUI instance so the launcher behavior is unambiguous.

| ID | Confirmation item | Expected normal result | Status |
|---|---|---|---|
| POST-GUI-01 | Double-click `scripts\launch-sgokb-gui.vbs` | SGOKB startup begins without requiring PowerShell/CMD | NOT RUN |
| POST-GUI-02 | Observe the desktop immediately after launch | No console, PowerShell, CMD, or persistent script window remains visible | NOT RUN |
| POST-GUI-03 | Observe startup before the main window appears | SGOKB loading splash is displayed before the main GUI | NOT RUN |
| POST-GUI-04 | Observe the splash during startup | Splash remains responsive/visible while startup progresses; no blank console substitute or fatal error dialog appears | NOT RUN |
| POST-GUI-05 | Wait for startup completion | Splash closes and the normal SGOKB main window becomes visible and usable | NOT RUN |
| POST-GUI-06 | Open/reopen the existing GUI-HP-49 Workspace | Workspace opens normally and the accepted `孫悟空` Knowledge state remains available | NOT RUN |
| POST-GUI-07 | Open `System / Maintenance > Overview` and refresh status | Runtime Dashboard refresh completes without unexpected error | NOT RUN |
| POST-GUI-08 | Inspect overall runtime state | Overall runtime health is `HEALTHY` when SQLite, Qdrant, derived state, and configured embedding runtime are otherwise normal | NOT RUN |
| POST-GUI-09 | Inspect `Search generation` | Status is `HEALTHY`, not `DEGRADED` | NOT RUN |
| POST-GUI-10 | Inspect Search-generation summary/details | Summary identifies `active=none (legacy routing)` / legacy routing; no false generation warning or troubleshooting action is shown | NOT RUN |
| POST-GUI-11 | Confirm no unintended generation mutation | No explicit active Search generation is created merely by opening/refreshing the dashboard | NOT RUN |
| POST-GUI-12 | Run Object Search in Lexical mode | Search completes normally and returns the expected `孫悟空` result | NOT RUN |
| POST-GUI-13 | Run Object Search in Semantic mode | Semantic Search completes normally and returns the expected `孫悟空` result | NOT RUN |
| POST-GUI-14 | Run Object Search in Hybrid mode | Hybrid Search completes normally and returns the expected `孫悟空` result without a new runtime-health degradation | NOT RUN |
| POST-GUI-15 | Close SGOKB normally, then launch again with the VBS | GUI closes cleanly; second launch again shows the splash, no console remains, Workspace state persists, and Search generation remains `HEALTHY` | NOT RUN |

### 8.1 PASS criteria

The interactive confirmation is PASS only when all 15 items above are `OK`.

```text
Total items = 15
OK          = 0
NOT RUN     = 15
FAIL        = 0
Disposition = NOT RUN
```

A failure in `POST-GUI-09` or `POST-GUI-10` is specifically a regression of the Search-generation health correction. A failure in `POST-GUI-12` through `POST-GUI-14` means the health presentation may look correct while the actual retrieval path is not healthy, so the update must not be accepted on display state alone.

### 8.2 Operator result recording

When the checklist is executed, record at minimum:

```text
execution date
verified main HEAD
Workspace path
POST-GUI-01..15 result
observed Search generation status
observed Search generation summary
Lexical / Semantic / Hybrid Search result
normal exit / relaunch result
unexpected warnings or errors, if any
final disposition = Interactive PASS / FAIL
```

Do not change the frozen `v2.0.0` tag when recording this post-release interactive result.
