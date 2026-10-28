# P-GUI-05 — Object / Source / Evidence / Association GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Status: **Implemented / Dynamic Verification Pending**
- Baseline: P-GUI-04 **Complete / Accepted**
- Requirements: `docs/requirements/GUI_REQUIREMENTS.md`
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`

## 1. Result summary

P-GUI-05 implements the four daily Knowledge-collection page families on top of the accepted P-GUI-04 shell and P-GUI-03R transport-neutral operator boundary.

```text
Objects       implemented
Sources       implemented
Evidence      implemented
Associations  implemented
```

The GUI does not introduce a second canonical behavior path. All domain operations are submitted through:

```text
Qt page/controller state
  -> GuiOperationRequest
  -> BackendCoordinator
  -> BackendWorker on dedicated QThread
  -> OperatorSession
  -> existing Application / Service layer
  -> Repository per operation
```

No GUI View or presentation model opens SQLite directly. No CLI subprocess is used as the GUI business boundary.

## 2. Operation parity inventory

P-GUI-05 owns 27 current public operations and all 27 are wired to GUI surfaces.

### Object — 12 / 12

```text
object.add
object.list
object.show
object.rename
object.status
object.alias.list
object.alias.add
object.class.set-primary
object.class.add
object.class.remove
object.events
object.relations
```

### Source — 6 / 6

```text
source.import
source.process
source.status
source.snapshots
source.select-snapshot
source.select-run
```

### Evidence — 5 / 5

```text
evidence.candidates
evidence.select
evidence.show
evidence.provenance
evidence.search
```

### Association — 4 / 4

```text
association.list
association.suggest
association.set
association.clear
```

```text
P-GUI-05 operation wiring = 27 / 27
unwired operations        = 0
```

## 3. Shared GUI operation layer

New shared presentation infrastructure:

```text
src/sgokb/gui/models/dict_table.py
src/sgokb/gui/views/operation_page.py
```

`DictTableModel` is a read-only Qt Model/View adapter for plain operation-result dictionaries. It is presentation cache only and is not canonical storage.

`OperationPage`:

- receives active `WorkspaceState`;
- creates a `GuiOperationRequest` before dispatch;
- records the request ID before the queued worker signal is emitted;
- consumes only its own result/failure/warning messages;
- preserves the shared `OperationFailure` category/code/message;
- never reaches into Repository or SQLite.

The backend completion order was also refined so chained refresh operations do not emit a false idle transition between a mutation result and its follow-up read.

## 4. Object GUI

Implemented in:

```text
src/sgokb/gui/views/object_page.py
```

Capabilities:

- Object list and master-detail selection;
- registry detail and current Knowledge display;
- add;
- rename;
- active / archived status;
- alias list / add;
- primary Class set;
- additional Class add / remove;
- registry events;
- accepted relations display.

Canonical mutation targeting always uses the selected stable `object_id`. Name/alias text is not silently resolved as a write target.

Accepted Relation records remain read-only. P-GUI-05 does not add direct Relation mutation and therefore preserves the Package -> Result -> Review -> Import write boundary.

## 5. Source GUI

Implemented in:

```text
src/sgokb/gui/views/source_page.py
```

Capabilities:

- Web Capture Bundle import with file dialog;
- local file/directory drag and drop;
- Source status;
- Snapshot list;
- selected/all Snapshot processing;
- chunk size / overlap / auxiliary controls;
- effective Snapshot selection with required interactive reason;
- effective normalization Run selection with required interactive reason;
- Snapshot metadata and locators;
- normalization Run list;
- Raw Artifact metadata display.

Raw Artifact display includes:

```text
artifact ID
artifact kind
logical path
media type
byte count
sha256
storage reference
```

### `source.snapshots` compatible enrichment

The existing transport-neutral `source.snapshots` read operation was extended without removing or renaming existing fields. It now also returns presentation-useful inspection data:

```text
source_label
locators
metadata
raw_artifacts
normalization_runs
effective_run_id
```

This avoids a GUI-only direct-storage read path and keeps CLI/GUI semantics on the shared Application boundary. Public operation count remains unchanged.

## 6. Evidence GUI

Implemented in:

```text
src/sgokb/gui/views/evidence_page.py
```

Capabilities:

- Object-scoped candidate retrieval;
- bounded Evidence selection;
- max candidate/item/token/byte controls;
- manual include / exclude / automatic state;
- Evidence detail;
- provenance;
- lexical / hybrid / semantic Evidence Search;
- optional selected-Object search scope;
- historical Evidence opt-in;
- explicit local semantic-runtime option.

Manual selection supports both mouse buttons and keyboard shortcuts:

```text
Ctrl+I = manual include
Ctrl+E = manual exclude
Ctrl+0 = return to automatic
```

Selection result reports at least:

```text
selected count
estimated tokens
bytes
omitted count
```

The include/exclude sets remain presentation/request state. Evidence selection itself is not written as a new canonical history model by the GUI.

Evidence detail/provenance continues to trace Source / Snapshot / normalization lineage through existing read applications.

Semantic/runtime failures remain explicit `OperationFailure`s. There is no cloud fallback.

## 7. Association GUI

Implemented in:

```text
src/sgokb/gui/views/association_page.py
```

Capabilities:

- Object selector;
- persistent association list;
- Source suggestion;
- optional semantic suggestion;
- set association;
- clear association;
- Source-side detail inspection.

Supported write fields preserve current contract:

```text
status = candidate / confirmed / excluded
subject_relationship
note
```

Suggestions remain read-only until the operator explicitly executes `association.set`.

## 8. Main-window integration

`MainWindow` now instantiates real P-GUI-05 pages for:

```text
Objects
Sources
Evidence
Associations
```

Later-task pages remain placeholders:

```text
Search           P-GUI-06
Packages         P-GUI-08 after P-RAW
Results          P-GUI-08 after P-RAW
Registry         P-GUI-06
System           P-GUI-09
Settings         later GUI task expansion
```

When the active Workspace changes, `MainWindow` passes the new `WorkspaceState` to all four domain pages. Each page clears its presentation cache and refreshes through the backend operation lane.

## 9. Automated acceptance assets

Added:

```text
tests/test_p_gui_05_domain_pages.py
```

The focused acceptance covers:

1. Object GUI mutations through stable IDs and independent canonical Repository verification;
2. Source import / processing / effective selection / Raw metadata inspection;
3. Evidence candidate retrieval / manual include / bounded selection / lexical search / detail / provenance;
4. Association set / suggest / clear with canonical effect verification;
5. MainWindow replacement of the four P-GUI-04 placeholders by real P-GUI-05 pages.

P-GUI-04 tests must also be rerun because P-GUI-05 modifies the shared shell and backend busy-completion sequencing.

## 10. Dynamic verification gate

No dynamic PASS is claimed in this implementation record yet.

Run from repository root with the already-installed `gui` extra:

```powershell
git pull --ff-only

python -m pytest `
  tests/test_p_gui_04_optional_boundary.py `
  tests/test_p_gui_04_shell.py `
  tests/test_p_gui_05_domain_pages.py

python -m pytest
python -m ruff check src tests
```

Required automated disposition:

```text
focused P-GUI-04 + P-GUI-05 = PASS
full pytest                  = PASS
ruff                         = PASS
```

## 11. Interactive smoke acceptance

After automated gates pass, run:

```powershell
sgokb-gui
```

Confirm at minimum:

### Objects

- existing Object list/detail loads;
- add, rename, archive/reactivate and alias work;
- primary/additional Class operations target the selected Object;
- events and read-only relations display.

### Sources

- a valid `.webcapture.zip` imports through the file dialog;
- drag and drop accepts a local capture bundle;
- Snapshot list and Raw Artifact metadata render;
- process creates normalization Run / Evidence;
- effective Snapshot / Run changes require a reason and refresh correctly.

### Evidence

- candidate retrieval works for an Object with associated Source data;
- manual include/exclude works by mouse;
- `Ctrl+I`, `Ctrl+E`, and `Ctrl+0` work by keyboard;
- bounded selection shows selected/tokens/bytes/omitted usage;
- Evidence detail and provenance render;
- lexical Evidence Search returns results.

### Associations

- association list and suggestion load;
- `candidate`, `confirmed`, and `excluded` can be explicitly set;
- subject relationship and note are preserved;
- clear removes the explicit association.

The GUI must remain responsive while backend work executes.

## 12. Completion disposition

Current state:

```text
implementation      = Complete
desk audit          = Complete
operation wiring    = 27 / 27
automated acceptance = Pending
interactive smoke    = Pending
```

Therefore:

```text
P-GUI-05 = Implemented / Dynamic Verification Pending
```

P-GUI-05 becomes `Complete / Accepted` only after automated and interactive acceptance evidence is measured PASS.
