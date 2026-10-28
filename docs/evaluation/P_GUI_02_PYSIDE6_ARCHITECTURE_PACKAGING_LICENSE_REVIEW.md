# P-GUI-02 — PySide6 Architecture / Packaging / License Review

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-02 [P0] PySide6 application architecture / packaging / license design`
- Status: **Complete / Review basis for accepted Decision**
- Released implementation baseline: `v1.1.0`
- P-GUI-01 authority: `docs/requirements/GUI_REQUIREMENTS.md`
- P-GUI-01 compatibility authority: `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`

## 1. Purpose

P-GUI-02 fixes the technical baseline for the SGOKB Desktop GUI before implementation starts.

The review covers:

- PySide6 / Qt UI technology choice
- Qt Widgets vs Qt Quick
- GUI process and module boundaries
- Qt main-thread / backend-worker separation
- SQLite / Repository threading implications
- CLI / GUI shared Application composition
- Windows packaging alternatives
- `pyside6-deploy` / Nuitka baseline
- LGPLv3 and third-party license obligations
- OSS publication gates

This task does not implement the GUI. The implementation begins after the Application-boundary audit in P-GUI-03.

---

## 2. Repository constraints found in the current baseline

### 2.1 Python/runtime baseline

Current `pyproject.toml` requires Python `>=3.10` and currently has no GUI dependency group.

Current public script:

```text
sgokb = "sgokb.cli:main"
```

Current optional dependency groups cover development, MCP, local embedding, FastEmbed and Qdrant, but not PySide6.

### 2.2 SQLite connection ownership

`Repository` currently opens SQLite with:

```python
sqlite3.connect(path)
```

No `check_same_thread=False` override is used. Therefore the default Python SQLite thread-affinity rule applies: the connection must remain on the thread that created it.

The repository also enables:

```text
foreign_keys = ON
busy_timeout = 5000 ms
journal_mode = WAL
```

This means the GUI must not create one `Repository` on the Qt main thread and then pass it into background workers.

### 2.3 Existing application boundaries

The CLI already composes multiple transport-neutral or mostly transport-neutral services:

- `Application`
- `ObjectAdminApplication`
- `KnowledgeReadApplication`
- exchange services
- maintenance / recovery services
- derived-search services

However some composition logic still lives in `sgokb.cli.main` / `sgokb.cli.runtime`.

P-GUI-03 will audit and extract the remaining transport-specific composition before GUI feature implementation.

---

## 3. PySide6 / Qt framework review

Qt for Python provides the official Python bindings for Qt through PySide6 and is available under LGPLv3/GPLv3 and the Qt commercial license.

Official references:

- https://doc.qt.io/qtforpython-6/
- https://doc.qt.io/qtforpython-6/licenses.html
- https://www.qt.io/development/open-source-lgpl-obligations

PySide6 remains the selected framework from Phase P planning.

### 3.1 Qt Widgets vs Qt Quick

Qt documentation describes Qt Widgets as the mature, feature-rich technology for large/complex desktop applications, while Qt Quick is optimized for fluid, dynamic and touch-oriented UIs.

SGOKB is primarily:

- desktop keyboard/mouse operated
- table/tree/list heavy
- master-detail oriented
- form/dialog oriented
- operator/maintenance oriented
- diff/review oriented

Therefore the baseline is **Qt Widgets**, not QML / Qt Quick.

Qt Quick is not forbidden forever, but it is outside the core GUI baseline. A later isolated visualization may use it only after an explicit design and license/packaging review.

### 3.2 Widget/API baseline

The initial architectural toolbox is:

```text
QApplication
QMainWindow
QWidget / QDialog
QDockWidget
QStackedWidget
QTreeView
QTableView
QListView
QAbstractItemModel / QAbstractTableModel / QAbstractListModel
QSortFilterProxyModel
QFileDialog
QMessageBox
QStatusBar
QSettings
QThread + QObject worker
Qt signals / slots
```

`QTextBrowser` / standard rich-text widgets are preferred for the initial Markdown/HTML-like preview surface. `Qt WebEngine` is not part of the baseline because SGOKB does not require a browser engine for the initial GUI and avoiding it reduces binary, runtime and licensing complexity.

---

## 4. Threading architecture review

### 4.1 Main-thread rule

All QWidget creation and mutation remains on the Qt GUI thread.

The main thread must not perform operations that can block noticeably, including:

- Source import / process
- filesystem scans
- large SQLite reads
- Package / Result file operations
- backup / restore
- derived sync / index rebuild
- local embedding model initialization / inference
- Qdrant network requests
- integrity checks when potentially long

### 4.2 QThread pattern

Qt documentation recommends the worker-object approach for slot-based background work: a `QObject` worker is moved to a `QThread`, and queued signals/slots cross the thread boundary.

The baseline therefore uses a dedicated backend worker thread rather than placing business methods directly on a `QThread` subclass.

### 4.3 No forced termination

`QThread.terminate()` is explicitly discouraged by Qt because it can stop a thread while data is being modified or resources are locked.

SGOKB therefore forbids forced termination of canonical operations.

Cancellation is cooperative only:

```text
cancel request
    ↓
operation checks cancellation boundary
    ↓
clean rollback / stop where supported
```

If a service has no safe cancellation point, the GUI must display it as non-cancellable.

### 4.4 SQLite / Repository ownership

Because current `Repository` connections are thread-bound, each backend operation opens and closes its own `Repository` inside the backend worker thread.

Baseline:

```text
Qt GUI thread
  owns Widgets / Controllers / ViewModels / Qt Models
          │ queued signal
          ▼
Backend worker thread
  owns backend operation execution
  opens Repository(db_path)
  creates Application / Service instances
  executes operation
  closes Repository
          │ result signal
          ▼
Qt GUI thread
  updates presentation models/widgets
```

The GUI must not solve the issue by setting `check_same_thread=False` and sharing one SQLite connection across threads.

### 4.5 Initial serialization policy

P0 baseline uses one serialized backend operation lane per open Workspace.

Reasons:

- deterministic canonical effects
- avoids concurrent-write complexity
- matches the current CLI mental model
- keeps SQLite connection ownership simple
- keeps mutation/restore/package operations ordered

The UI remains responsive because the lane is not the Qt main thread.

Parallel read lanes may be introduced later only after explicit concurrency tests and a separate design change.

### 4.6 Semantic runtime caching

Repeatedly loading the local embedding model for every semantic operation is undesirable.

The planned backend session may lazily retain expensive provider/runtime objects within the worker-thread lifetime while continuing to open a fresh `Repository` per operation.

Conceptually:

```text
BackendSession
├─ workspace DB path
├─ lazy embedding provider
├─ lazy vector client
└─ per-operation Repository
```

The exact transport-neutral factory is finalized in P-GUI-03.

---

## 5. GUI process/module architecture options

### Option A — GUI shells out to `sgokb`

Rejected as the primary architecture.

Advantages:

- minimal refactoring
- stable CLI JSON already exists

Disadvantages:

- duplicates process/composition overhead
- awkward progress/cancellation
- harder rich preview and typed error handling
- turns CLI transport into an internal application API
- risks semantic divergence between direct services and CLI wrappers

This conflicts with P-GUI-01.

### Option B — GUI calls Repository directly

Rejected.

Advantages:

- simple prototype path

Disadvantages:

- creates hidden canonical write paths
- bypasses validation/safety contracts
- duplicates business logic
- violates the accepted CLI/GUI Application-boundary rule

### Option C — CLI and GUI share Application / Service layer

**Accepted.**

```text
CLI presentation ─┐
                  ├─> Application / Service layer
GUI presentation ─┘            │
                               ▼
                 Repository / Retrieval / Exchange
```

P-GUI-03 will move any remaining CLI-only business/composition logic to a transport-neutral boundary.

---

## 6. Planned GUI source layout

Accepted target layout:

```text
src/sgokb/gui/
├─ __init__.py
├─ main.py                 # GUI entrypoint only
├─ bootstrap.py            # QApplication + top-level composition
├─ workspace.py            # selected DB / session state, no canonical data
├─ operations.py           # operation request/result/progress/error DTOs
├─ worker.py               # QThread worker boundary
├─ controllers/
│  └─ ...
├─ models/
│  └─ ...                  # Qt presentation models
├─ views/
│  └─ ...
├─ dialogs/
│  └─ ...
├─ widgets/
│  └─ ...
└─ resources/
   └─ ...
```

Rules:

- `gui/` contains presentation and orchestration, not canonical SQL.
- domain/application services must not import PySide6.
- Qt types must not leak into domain/storage contracts.
- GUI-only settings must not be stored in canonical SGOKB tables.
- CLI code must not import GUI modules.

A transport-neutral runtime/composition module outside `sgokb.cli` is expected, but its exact shape is deferred to P-GUI-03.

---

## 7. Python package entrypoint / dependency design

Planned source-install interface:

```toml
[project.optional-dependencies]
gui = ["PySide6>=6.12,<6.13"]

[project.scripts]
sgokb = "sgokb.cli:main"

[project.gui-scripts]
sgokb-gui = "sgokb.gui:main"
```

Rationale:

- CLI stays installable without Qt.
- GUI users explicitly install `.[gui]`.
- `gui-scripts` is the GUI launcher boundary for Python installs.
- packaged Windows distribution remains a separate deployment artifact.

Version policy:

- package metadata uses a tested PySide6 minor line rather than unrestricted `<7` drift.
- packaged release artifacts record the exact PySide6 / Qt / build-tool versions.
- minor-line upgrades require GUI smoke/regression tests and license inventory review.

The initial design baseline is the Qt/PySide6 6.12 line because current official deployment behavior and documentation are based on that line. If implementation preflight finds a platform/wheel incompatibility, changing the minor line requires an explicit P-GUI-02 amendment rather than an untracked downgrade.

---

## 8. Windows deployment alternatives

### 8.1 `pyside6-deploy` / Nuitka

**Accepted baseline.**

Qt for Python officially recommends `pyside6-deploy`; the tool wraps Nuitka. Current official documentation supports `pyproject.toml` deployment intent and uses `standalone` as the default mode in the current 6.12 line.

Advantages:

- Qt-official deployment path
- integrated PySide6 module/plugin discovery
- Windows support
- `pyproject.toml` integration
- standalone directory mode fits LGPL replacement/inspection requirements better than a sealed one-file artifact

### 8.2 PyInstaller

Supported by Qt documentation, but not the baseline.

It remains a fallback if a concrete `pyside6-deploy` blocker is found.

### 8.3 cx_Freeze

Also supported, but not the baseline. No current SGOKB requirement justifies adding a second deployment system.

### 8.4 One-file executable

**Not accepted as the initial release baseline.**

Reasons:

- harder to inspect/replace dynamically linked Qt components
- less transparent third-party license inventory
- harder field diagnosis
- unnecessary for the first OSS desktop release

A one-file build may be evaluated later only after a fresh legal/compliance and replacement-mechanism review.

---

## 9. Accepted Windows distribution baseline

The first packaged GUI release uses:

```text
Build platform       = Windows x64
Deployment tool      = pyside6-deploy / Nuitka
Deployment mode      = standalone directory
Qt UI technology     = Qt Widgets
Static Qt linking    = prohibited
One-file mode        = not baseline
Installer            = not required for first acceptance
Portable ZIP/folder  = baseline artifact
```

Expected artifact shape:

```text
SGOKB/
├─ SGOKB.exe
├─ Qt6Core.dll
├─ Qt6Gui.dll
├─ Qt6Widgets.dll
├─ platform/plugins/...
├─ Python/runtime dependencies...
├─ LICENSES/
├─ THIRD_PARTY_NOTICES.md
└─ BUILD_MANIFEST.json
```

The exact generated filenames may differ; the contract is that Qt shared libraries remain separate replaceable components in the standalone distribution.

### Release build reproducibility

Release builds must:

- use a clean virtual environment
- use pinned/locked build requirements
- avoid uncontrolled build-time dependency installation
- prefer `pyside6-deploy --no-install` after dependencies are explicitly installed for release builds
- record Python / PySide6 / Qt / Nuitka and relevant dependency versions
- record the source commit and artifact hash

---

## 10. LGPL / OSS distribution review

### 10.1 PySide6 licensing

Qt for Python Community Edition is available under LGPLv3/GPLv3; individual Qt modules can have different open-source licensing, so module selection must be audited.

SGOKB baseline uses the core LGPL-oriented desktop modules required for Qt Widgets and does not assume every optional Qt module is LGPL-safe.

### 10.2 Distribution obligations adopted as release gates

For an LGPL-based Qt/PySide6 distribution, the SGOKB release process must at minimum ensure:

- Qt/PySide6 use is explicitly acknowledged.
- applicable LGPL license text is distributed.
- third-party notices for actually bundled components are distributed.
- exact Qt/PySide6 version is recorded.
- corresponding Qt/PySide6 source availability / written offer or equivalent instructions are provided in a durable release artifact.
- users are not prohibited from replacing/relinking the LGPL libraries.
- reverse engineering for debugging modifications to LGPL components is not contractually prohibited.
- Qt is dynamically linked / distributed as separate shared libraries in the baseline artifact.
- modifications to LGPL-covered Qt/PySide6 code, if any, are tracked and their corresponding source is made available as required.

This document records engineering compliance requirements, not legal advice. Public redistribution should still receive a final license review.

### 10.3 Project license is currently unresolved

The repository currently has **no root `LICENSE` file**.

Therefore SGOKB must not describe the repository itself as formally OSS-licensed yet.

Before public OSS release, a separate project-level license Decision must select and add the SGOKB application license. P-GUI-02 intentionally does not choose MIT / Apache-2.0 / GPL or another license without an explicit project decision.

This is a **public-release blocker**, not a blocker for private GUI development.

### 10.4 New Qt module gate

Adding any new Qt module outside the approved baseline requires:

1. necessity review
2. open-source license review
3. packaging-size/runtime review
4. third-party component inventory update

In particular, browser/multimedia/other large add-ons must not be added incidentally by convenience widgets.

---

## 11. Settings and persistence boundary

GUI presentation state uses Qt settings facilities, not canonical SQLite tables.

Examples of GUI-only state:

- recent Workspace paths
- window geometry
- dock layout
- column widths
- last selected tab
- saved presentation filters where they do not change canonical semantics

Forbidden in GUI settings:

- accepted Knowledge
- Object identity
- Source/Evidence canonical records
- Registry decision state
- Result review/import state
- security-sensitive credentials unless a separately approved secure-storage design exists

---

## 12. Testing implications

P-GUI-02 requires later tests for:

- GUI module import without changing CLI behavior
- Qt main-thread ownership
- backend worker result/error signal delivery
- Repository created/closed on worker thread
- Workspace switching only after in-flight operation handling
- no forced `QThread.terminate()` path
- package source install without GUI extra still supports CLI
- `.[gui]` installation launches GUI entrypoint
- packaged standalone artifact smoke test on Windows
- bundled license/notice/source-offer manifest test

These are implemented in later P-GUI tasks.

---

## 13. Decision summary

Accepted:

```text
GUI framework        = PySide6
UI technology        = Qt Widgets
Architecture         = shared Application / Service layer
Backend threading    = QObject worker on dedicated QThread
DB connection model  = per-operation Repository created in worker thread
Operation lane       = serialized per Workspace initially
Packaging            = pyside6-deploy / Nuitka
Windows artifact     = standalone directory / portable ZIP baseline
Qt linking           = dynamic / separate libraries
One-file             = not baseline
CLI dependency       = GUI optional; CLI remains Qt-free
Project OSS license  = unresolved; public-release blocker
```

P-GUI-03 may refine the transport-neutral Application factory and operation DTOs, but must not violate these decisions without an explicit P-GUI-02 amendment.
