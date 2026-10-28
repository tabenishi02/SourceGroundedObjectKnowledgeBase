# P-GUI-05 — Object / Source / Evidence / Association GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-05 [P0] Object / Source / Evidence / Association GUI`
- Status: **Complete / Accepted**
- Baseline: P-GUI-04 **Complete / Accepted**
- Requirements: `docs/requirements/GUI_REQUIREMENTS.md`
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Final acceptance: `docs/evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`

## 1. Result summary

P-GUI-05 implements and accepts the four daily Knowledge-collection page families on top of the P-GUI-04 shell and P-GUI-03R transport-neutral operator boundary.

```text
Objects       Complete / Accepted
Sources       Complete / Accepted
Evidence      Complete / Accepted
Associations  Complete / Accepted
```

The GUI does not introduce a second canonical behavior path. Domain operations use:

```text
Qt page/controller state
  -> GuiOperationRequest
  -> BackendCoordinator
  -> BackendWorker on dedicated QThread
  -> OperatorSession
  -> Application / Service layer
  -> Repository per operation
```

No GUI View or presentation model opens SQLite directly. No CLI subprocess is used as the GUI business boundary.

## 2. Operation parity inventory

P-GUI-05 owns 27 current public operations and all 27 are wired.

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

Shared presentation infrastructure:

```text
src/sgokb/gui/models/dict_table.py
src/sgokb/gui/views/operation_page.py
```

`DictTableModel` is a read-only Qt Model/View adapter for operation-result dictionaries and is not canonical storage.

`OperationPage`:

- receives active `WorkspaceState`;
- creates a `GuiOperationRequest` before dispatch;
- correlates result/failure/warning messages by request ID;
- preserves shared `OperationFailure` category/code/message semantics;
- never reaches into Repository or SQLite.

Backend completion ordering keeps mutation -> refresh chains from exposing a false idle transition.

## 4. Object GUI

Implemented in:

```text
src/sgokb/gui/views/object_page.py
```

Capabilities:

- Object list / master-detail;
- registry detail and current Knowledge display;
- add / rename / active / archived;
- alias list / add;
- Primary / Additional Class management;
- registry events;
- accepted relations display.

Canonical mutation targeting always uses stable `object_id`.

Class controls were improved during acceptance:

```text
Add Object Primary Class = active registry Classes
Set Primary Class        = every registry Class
Add Class                = every registry Class except current Primary Class
Remove Class             = assigned Additional Classes only
Remove Class enabled     = only when Additional Classes exist
```

All Class writes pass stable `class_id` values rather than free-text labels.

Accepted Relation records remain read-only, preserving the Package -> Result -> Review -> Import write boundary.

## 5. Source GUI

Implemented in:

```text
src/sgokb/gui/views/source_page.py
```

Capabilities:

- single Web Capture Bundle import;
- recursive folder ZIP import;
- local file / directory drag and drop;
- Source status;
- Snapshot list;
- selected/all Snapshot processing;
- chunk size / overlap / auxiliary controls;
- effective Snapshot selection with explicit free-text audit reason;
- effective normalization Run selection with explicit free-text audit reason;
- Snapshot metadata and locators;
- normalization Run list;
- Raw Artifact metadata display.

Recursive folder import behavior:

```text
selected directory
  -> recursive traversal
  -> every regular file whose suffix case-folds to .zip
  -> deterministic sorted target list
  -> attempt each through existing source.import semantics
```

All ZIPs are discovery targets, but existing `WebCaptureImporter` validation remains authoritative. Invalid ZIPs are reported per target and do not stop later valid targets.

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

`source.snapshots` was extended backward-compatibly with:

```text
source_label
locators
metadata
raw_artifacts
normalization_runs
effective_run_id
```

The Application/operator DTO normalizes canonical `raw_artifacts.bytes` to presentation-neutral `byte_count`.

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
- Evidence detail / provenance;
- lexical / hybrid / semantic Evidence Search;
- optional selected-Object scope;
- historical Evidence opt-in;
- explicit local semantic-runtime option.

Keyboard shortcuts:

```text
Ctrl+I = manual include
Ctrl+E = manual exclude
Ctrl+0 = automatic
```

Selection reports selected count, estimated tokens, bytes and omitted count. Manual include/exclude sets remain presentation/request state rather than a separate canonical history model.

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
- set / clear association;
- Source-side detail inspection.

Supported write fields:

```text
status = candidate / confirmed / excluded
subject_relationship
note
```

Suggestions remain read-only until explicit `association.set`.

## 8. Main-window integration

`MainWindow` provides real P-GUI-05 pages for:

```text
Objects
Sources
Evidence
Associations
```

Later-task pages remain outside P-GUI-05:

```text
Search           P-GUI-06
Registry         P-GUI-06
Packages         P-GUI-08 after P-RAW
Results          P-GUI-08 after P-RAW
System           P-GUI-09
Settings         later GUI expansion
```

Workspace changes are propagated through `WorkspaceState`; pages clear presentation state and refresh through the backend operation lane.

## 9. Automated acceptance

Final focused coverage includes:

```text
tests/test_p_gui_04_optional_boundary.py
tests/test_p_gui_04_shell.py
tests/test_p_gui_05_domain_pages.py
tests/test_p_gui_05_object_class_selector.py
tests/test_p_gui_05_object_class_controls.py
tests/test_p_gui_05_source_recursive_zip_import.py
```

Final automated result:

```text
focused GUI regression = 12 / 12 PASS
Ruff                   = All checks passed!
full regression         = 807 / 807 PASS
known warnings          = 2 local-Qdrant warnings
```

Final automated authority:

- `docs/evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md`

Attempts 05 and 06 identified test defects only; the product recursive import behavior was functioning.

## 10. Interactive acceptance

Visual smoke had already passed for all four page families.

The operator then confirmed normal behavior for the targeted P-GUI-05 functional test set, including representative Object, Source, Evidence and Association paths and the amendments introduced during acceptance review.

Final interactive authority:

- `docs/evaluation/P_GUI_05_INTERACTIVE_SMOKE_ATTEMPT_01.md` — historical visual-only partial pass;
- `docs/evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md` — final functional PASS and closure.

## 11. Completion disposition

```text
implementation       = Complete
desk audit           = Complete
operation wiring     = 27 / 27
automated acceptance = PASS
visual smoke         = PASS
functional smoke     = PASS
```

Therefore:

```text
P-GUI-05 = Complete / Accepted
```

The formal released baseline remains `v1.1.0`; P-GUI-05 acceptance advances Phase P development state but does not by itself create a release.

## 12. Next

```text
P-GUI-06 [P0] Search / Similarity / Registry / Version GUI
```
