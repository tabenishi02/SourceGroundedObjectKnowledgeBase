# P-GUI-04 — GUI Shell / Workspace / Navigation Foundation Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-04 [P0] GUI shell / Workspace / navigation foundation`
- Status: **Complete / Accepted**
- Baseline: P-GUI-03R **Complete / Accepted**
- GUI architecture: `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`
- GUI requirements: `docs/requirements/GUI_REQUIREMENTS.md`

## 1. Result summary

P-GUI-04 has an accepted executable PySide6 / Qt Widgets foundation on `main`.

Implemented scope:

```text
optional GUI dependency + sgokb-gui entrypoint
QApplication bootstrap / application identity
QMainWindow shell
11 accepted navigation destinations
QStackedWidget page host
Home / Dashboard foundation
Workspace open / create / recent handling
QSettings presentation-state persistence
serialized BackendWorker on dedicated QThread
BackendSession runtime cache without long-lived Repository
Workspace validation through OperatorSession(system.status)
open / migration failure presentation
busy-time Workspace switch prevention
busy-time application close prevention
status bar / global warning surface
P-GUI-04 automated test assets
```

P-GUI-05+ domain pages remain intentionally placeholders in this task.

## 2. Package / entrypoint

`pyproject.toml` adds:

```toml
[project.optional-dependencies]
gui = ["PySide6>=6.12,<6.13"]

[project.gui-scripts]
sgokb-gui = "sgokb.gui:main"
```

The base CLI install does not import PySide6 through `sgokb.gui.__init__`; the GUI launcher is loaded lazily.

New GUI modules:

```text
src/sgokb/gui/
├─ __init__.py
├─ main.py
├─ bootstrap.py
├─ operations.py
├─ worker.py
├─ workspace.py
├─ controllers/
│  ├─ __init__.py
│  └─ workspace_controller.py
└─ views/
   ├─ __init__.py
   └─ main_window.py
```

## 3. Backend execution boundary

The P-GUI-02/P-GUI-03R boundary is preserved:

```text
Qt main thread
  MainWindow / WorkspaceController
        │ queued Signal
        ▼
BackendCoordinator
        │
        ▼
BackendWorker(QObject) on dedicated QThread
        │
        ▼
OperatorSession
        │
        ▼
Repository per operation
```

Rules preserved by implementation:

- no GUI -> CLI subprocess business path;
- no GUI direct canonical SQL;
- no Repository connection is retained across operations;
- no SQLite connection crosses a thread boundary;
- `RuntimeFactory` can be retained as noncanonical BackendSession state;
- switching Workspace invalidates the prior runtime cache;
- `QThread.terminate()` is not used.

## 4. Workspace contract

`WorkspaceController` treats a DB path as a candidate until the backend executes:

```text
system.status
```

successfully through `OperatorSession`.

Only successful status results update `WorkspaceState` and recent-Workspace settings.

Consequences:

- a fresh path is created/migrated by the normal Repository path on the backend thread;
- an existing canonical DB is opened through the same path used by CLI semantics;
- prototype migration rejection or another open/migration failure does not replace the current active Workspace;
- a Workspace switch is rejected while a backend operation is already in flight.

A registration race found during desk review was removed by registering the candidate request in the controller before emitting the queued worker signal.

## 5. Presentation-only settings

`WorkspaceSettings` persists only GUI state:

```text
workspace/recent_paths
workspace/last_path
window/geometry
window/state
navigation/last_page
```

No canonical Object / Source / Evidence / Result / Registry data is written to QSettings.

## 6. Shell / navigation

The accepted P-GUI-01 navigation is present exactly as the initial shell inventory:

```text
Home / Dashboard
Objects
Sources
Evidence
Associations
Search
Packages
Results
Registry
System
Settings
```

The Dashboard currently displays:

- active Workspace path;
- Object count;
- Object count with current Knowledge;
- applied migration count;
- open/create entry actions.

Later task ownership remains explicit in placeholder pages so P-GUI-04 does not prematurely implement P-GUI-05..09 semantics.

## 7. Safe startup / failure / close behavior

Implemented failure behavior:

- Workspace migration/open failure is surfaced as the shared `OperationFailure` category/code/message;
- a global warning area retains the failure distinction;
- an error dialog is shown in normal interactive mode;
- the prior active Workspace is retained after candidate-open failure;
- Open/Create actions are disabled while backend work is active;
- close is rejected while a backend operation is active;
- normal close asks the worker thread to quit and waits for an orderly shutdown;
- no force termination path is provided.

`Create Workspace` refuses an already-existing target and directs the operator to Open Workspace instead of treating Create as overwrite.

## 8. Automated test assets

Added:

```text
tests/test_p_gui_04_optional_boundary.py
tests/test_p_gui_04_shell.py
```

The optional-boundary test runs without PySide6 and protects the lazy GUI package import.

When the `gui` extra is installed, the Qt test file runs with the offscreen platform and covers:

1. recent Workspace ordering / deduplication;
2. fresh Workspace creation through backend `system.status`;
3. prototype migration rejection;
4. preservation of the previous active Workspace after candidate failure;
5. the exact 11-item accepted navigation inventory;
6. clean backend shutdown from the shell.

## 9. Dynamic verification result

Verification was executed on Windows / Python 3.10.6 with PySide6 6.12.0 installed through the `gui` extra.

Entrypoint installation:

```text
Get-Command sgokb-gui
→ sgokb-gui.exe resolved successfully
```

Focused P-GUI-04 acceptance:

```text
python -m pytest \
  tests/test_p_gui_04_optional_boundary.py \
  tests/test_p_gui_04_shell.py

5 collected
5 passed
```

Full repository regression after P-GUI-04 implementation:

```text
800 collected
800 passed
2 warnings
0 failed
0 errors
```

The two warnings are the existing local-Qdrant capability warnings and are non-failing.

Final Ruff regression after applying Ruff's exact import normalization:

```text
python -m ruff check src tests
All checks passed!
```

Therefore the automated P-GUI-04 gate is:

```text
focused pytest = PASS (5 / 5)
full pytest    = PASS (800 / 800)
ruff           = PASS
```

## 10. Interactive smoke acceptance

Interactive GUI smoke was executed successfully.

Confirmed PASS:

```text
GUI normal startup                         PASS
11 navigation destinations                PASS
Create Workspace                          PASS
Dashboard Workspace/status display        PASS
Open Workspace                            PASS
Recent Workspaces persisted after restart PASS
GUI close / DB release                    PASS
same DB readable from CLI                 PASS
```

The accepted smoke Workspace was subsequently read from the CLI with:

```powershell
sgokb --db "C:\codex\SourceGroundedObjectKnowledgeBase\.local\202610290130_sql\sgokb.sqlite" system status
```

The command returned `ok: true`, migrations 3 through 18, zero Source/Object content for the fresh DB, and no warnings.

This confirms the P-GUI-04 completion criterion that the same canonical SQLite Workspace remains usable from the CLI after GUI use.

## 11. Final acceptance disposition

All implementation and acceptance gates are satisfied:

```text
implementation         = Complete
sgokb-gui entrypoint   = PASS
focused pytest         = PASS (5 / 5)
full pytest            = PASS (800 / 800)
ruff                   = PASS
interactive GUI smoke = PASS
GUI -> CLI DB reuse    = PASS
```

Formal disposition:

```text
P-GUI-04 = Complete / Accepted
P-GUI-05 = Unblocked / Next
```

P-GUI-05 may now implement the Object / Source / Evidence / Association GUI on top of this accepted shell and backend foundation.
