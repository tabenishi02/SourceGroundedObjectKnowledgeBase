# P-GUI Application Architecture

Updated: 2026-10-28

- Status: **Accepted design / not yet implemented**
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-02`
- Decision: `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- Requirement: `docs/requirements/GUI_REQUIREMENTS.md`

## 1. Scope

This document defines the target technical architecture for the PySide6 desktop client. It is a Phase P planned design and does not claim that the current v1.1.0 implementation already contains these modules.

---

## 2. Layering

```text
┌─────────────────────────────────────────────────────┐
│ PySide6 Presentation                               │
│ QMainWindow / Views / Dialogs / Qt Models          │
│ Controllers / Workspace / Operation UI             │
└───────────────────────────┬─────────────────────────┘
                            │ typed operation request
                            ▼
┌─────────────────────────────────────────────────────┐
│ GUI Backend Execution Boundary                     │
│ BackendWorker(QObject) on dedicated QThread        │
│ BackendSession / runtime cache                     │
└───────────────────────────┬─────────────────────────┘
                            │ transport-neutral call
                            ▼
┌─────────────────────────────────────────────────────┐
│ Application / Service layer                        │
│ Application / ObjectAdminApplication               │
│ KnowledgeReadApplication / exchange / maintenance  │
│ future shared composition factories                │
└───────────────────────────┬─────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────┐
│ Repository / Retrieval / Exchange / Filesystem     │
│ SQLite / Embedding / Qdrant / package/result files │
└─────────────────────────────────────────────────────┘
```

No arrow goes from GUI Views directly to SQLite.

---

## 3. GUI package layout

Target package:

```text
src/sgokb/gui/
├─ __init__.py
├─ main.py
├─ bootstrap.py
├─ workspace.py
├─ operations.py
├─ worker.py
├─ controllers/
├─ models/
├─ views/
├─ dialogs/
├─ widgets/
└─ resources/
```

### `main.py`

Responsibilities:

- GUI entrypoint
- minimal exception guard before Qt event loop
- delegates construction to bootstrap

Must not contain business dispatch.

### `bootstrap.py`

Responsibilities:

- create `QApplication`
- application identity / icon / metadata
- create GUI-level services
- create backend thread / worker
- create top-level window
- application shutdown sequence

### `workspace.py`

Contains noncanonical workspace/session state:

```text
WorkspaceState
- db_path
- display label
- open/closed state
- current operation summary
- runtime availability snapshot
```

It does not mirror canonical Object/Source tables.

### `operations.py`

Defines GUI transport DTOs independent from individual Widgets.

Expected concepts:

```text
OperationRequest
OperationResult
OperationProgress
OperationWarning
OperationFailure
OperationId
SafetyClass
CancellationMode
```

These DTOs are presentation transport objects; canonical domain models remain in existing SGOKB modules.

### `worker.py`

Owns the QObject worker implementation and backend-session lifetime.

It must not own QWidget instances.

### `controllers/`

Coordinates user intent and typed operations.

Controllers:

- validate presentation-level required fields
- resolve selected rows to stable IDs
- request confirmation according to SafetyClass
- submit operations
- transform result DTOs into presentation state

Controllers do not implement canonical validation already owned by the Application/Service layer.

### `models/`

Qt Model/View adapters.

Examples:

- Object list model
- Source/Snapshot model
- Evidence result model
- Result inbox model
- Registry proposal model
- Search result model
- Version diff model

The model can cache display rows, but it is not canonical storage.

### `views/`, `dialogs/`, `widgets/`

Presentation only.

---

## 4. Planned top-level window

Baseline:

```text
QMainWindow
├─ left navigation
├─ central QStackedWidget / page host
├─ optional QDockWidget utility panels
├─ menu / command actions
└─ QStatusBar
```

Initial page families remain those accepted in P-GUI-01:

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

`System -> Advanced` hosts R2 generation maintenance if exposed.

---

## 5. Thread ownership

### Qt main thread owns

```text
QApplication
all QWidget/QDialog instances
Qt presentation models
controllers
workspace presentation state
navigation state
```

### Backend thread owns

```text
BackendWorker QObject
BackendSession runtime objects
per-operation Repository
Application/Service instances created for the operation
blocking filesystem/database/provider execution
```

### Cross-thread communication

Only queued signals/slots or equivalent Qt-safe queued invocation cross the boundary.

Do not call worker-owned objects directly from the GUI thread.

Do not pass live SQLite connections across the boundary.

Result payloads should be immutable/plain DTO-like Python values whenever practical.

---

## 6. Operation lifecycle

```text
User action
  ↓
Controller builds OperationRequest
  ↓
Safety confirmation if required
  ↓
Operation queued to BackendWorker
  ↓
GUI marks operation running
  ↓
Worker opens Repository in worker thread
  ↓
Worker composes Application / Service
  ↓
Worker executes
  ├─ progress signals
  ├─ warning signals
  └─ cancellation check where supported
  ↓
Repository closes
  ↓
OperationResult / OperationFailure emitted
  ↓
GUI model/view update
```

Every operation receives a unique GUI operation ID for presentation history and correlation.

This ID is not a replacement for canonical audit IDs generated by SGOKB.

---

## 7. Safety-class integration

The GUI operation metadata includes the P-GUI-01 side-effect class:

```text
READ
DERIVED
WRITE
EXTERNAL
MAINTENANCE
```

The backend does not trust the visual classification as an authorization mechanism; existing service preconditions remain authoritative.

Presentation uses the class to choose:

- confirmation
- preview requirements
- button wording
- progress persistence
- cancellation policy
- completion notification

---

## 8. Error model

Backend exceptions are normalized into GUI failure categories compatible with CLI meaning:

```text
internal
invalid_input
not_found_or_ambiguous
blocked_or_precondition
runtime_unavailable
io_or_external
integrity
partial_failure
```

The GUI may show a user-friendly title, but must retain:

- stable category
- technical message
- relevant details
- operation context

No generic error dialog may discard an integrity or blocked distinction.

P-GUI-03 determines whether the shared error normalization should be extracted from current CLI-only code.

---

## 9. Repository and SQLite model

Current Repository connection is thread-affine.

Therefore:

```text
one operation
  -> one Repository connection
  -> connection created in backend thread
  -> connection closed in backend thread
```

No application-global shared SQLite connection.

No `check_same_thread=False` shortcut.

WAL and `busy_timeout` remain repository concerns.

Initial backend operation serialization avoids concurrent GUI writers. External CLI processes may still operate concurrently subject to existing SQLite/SGOKB consistency boundaries; GUI must surface resulting lock/precondition failures rather than hiding them.

---

## 10. BackendSession

A long-lived backend session exists to cache expensive noncanonical runtime objects.

Target shape:

```text
BackendSession
- workspace db path
- runtime configuration snapshot
- embedding provider: optional/lazy
- vector client: optional/lazy
- future runtime health cache
```

It must not own a long-lived Repository connection.

Workspace switch invalidates the session.

Embedding/provider initialization failures become runtime-unavailable operation failures; there is no cloud fallback.

---

## 11. Cancellation contract

Each operation advertises:

```text
not_cancellable
cooperative_cancellable
```

No force-kill mode.

A cooperative operation receives a cancellation token/check callback only after its underlying service is designed to stop safely.

Closing the main window while a non-cancellable WRITE/EXTERNAL/MAINTENANCE operation is running must trigger a close workflow rather than terminating the thread abruptly.

---

## 12. Shutdown sequence

Normal shutdown:

```text
request main-window close
  ↓
inspect in-flight operation
  ├─ none -> continue
  ├─ safely cancellable -> offer cancel/wait
  └─ non-cancellable mutation -> require completion or explicit OS-level abort outside normal app semantics
  ↓
stop accepting new operations
  ↓
request worker event-loop quit
  ↓
wait for orderly worker shutdown
  ↓
release BackendSession
  ↓
exit QApplication
```

The application does not call `QThread.terminate()`.

---

## 13. Settings design

Use Qt settings only for presentation state.

Proposed keys:

```text
workspace/recent_paths
window/geometry
window/state
navigation/last_page
table/<view>/column_state
filters/<view>/presentation_filter
```

Do not store canonical values as an alternative database.

Do not store credentials in QSettings without a future secure-storage Decision.

---

## 14. Entry points

Source-installed package target:

```text
CLI: sgokb
GUI: sgokb-gui
```

GUI dependency remains an optional dependency.

Packaged Windows executable may be named `SGOKB.exe`.

---

## 15. Packaging layout

Baseline distribution is a directory/ZIP, not one-file.

Conceptual contents:

```text
SGOKB/
├─ SGOKB.exe
├─ Qt shared libraries
├─ Qt platform plugins
├─ packaged Python/runtime dependencies
├─ application resources
├─ LICENSES/
├─ THIRD_PARTY_NOTICES.md
└─ BUILD_MANIFEST.json
```

`BUILD_MANIFEST.json` should record at least:

```text
sgokb_version
source_commit
build_timestamp
python_version
pyside6_version
qt_version
deployment_tool_version
nuitka_version
platform
artifact_sha256
```

---

## 16. License boundary in architecture

The UI architecture intentionally minimizes Qt module surface.

Initial imported modules should remain under the QtCore / QtGui / QtWidgets family unless a requirement forces expansion.

Any added Qt module becomes an architecture dependency and triggers:

- license audit
- binary inventory update
- deployment smoke test
- release notice update

---

## 17. P-GUI-03 handoff

P-GUI-03 must inspect every CLI dispatch path and answer:

1. Which use cases already have transport-neutral Application methods?
2. Which CLI dispatch blocks contain business/composition logic that must move?
3. Which shared runtime factory should replace `sgokb.cli.runtime` ownership?
4. Which shared error/result concepts should exist below CLI/GUI?
5. Which operations need progress/cancellation hooks before GUI implementation?
6. Which maintenance operations cannot safely share normal Repository lifetime?

P-GUI-03 may refine class/module names, but must preserve the architecture constraints in this document.
