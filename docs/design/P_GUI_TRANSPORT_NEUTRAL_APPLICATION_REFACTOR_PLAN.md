# P-GUI Transport-neutral Application Refactor Plan

Updated: 2026-10-28

- Status: **Accepted design / P-GUI-03**
- Implementation follow-up: `P-GUI-03R`
- Audit: `docs/evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`
- Decision: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- Matrix: `docs/reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`

---

## 1. Goal

Refactor the current CLI-oriented composition into a transport-neutral operator layer without changing public CLI semantics.

The implementation must make it possible for both CLI and PySide6 GUI to execute the same operation semantics without:

- invoking CLI subprocesses
- parsing CLI JSON internally
- duplicating repository/audit orchestration
- exposing raw SQL to GUI code

---

## 2. Target module layout

Planned additions:

```text
src/sgokb/
├─ application_source.py
├─ application_registry.py
├─ application_exchange.py
├─ application_version.py
├─ application_render.py
├─ application_system.py
├─ application_operator.py
├─ runtime.py
└─ operation_contracts.py
```

The exact filenames may be consolidated during implementation if responsibilities remain equivalent.

Existing modules remain reusable:

```text
application.py
application_admin.py
application_read.py
application_derived.py
application_generation.py
application_maintenance.py
```

GUI modules must depend on the new/shared Application surface, not on CLI dispatch functions.

---

## 3. Shared contracts

### 3.1 OperationId

Use stable semantic IDs matching the current command hierarchy:

```text
source.import
source.process
source.status
...
system.restore.composite.apply
```

Do not embed argv syntax in the ID.

### 3.2 OperationRequest

Initial internal DTO:

```python
@dataclass(frozen=True, slots=True)
class OperationRequest:
    operation_id: str
    arguments: Mapping[str, object]
```

P0 does not require a schema framework dependency. Validation continues inside domain Application/services.

### 3.3 OperationOutcome

```python
@dataclass(frozen=True, slots=True)
class OperationOutcome:
    operation_id: str
    data: object
    warnings: tuple[str, ...] = ()
    state: str = "success"  # success | blocked | partial
```

### 3.4 OperationFailure

```python
class OperationFailure(Exception):
    operation_id: str
    category: str
    code: str
    message: str
    details: Mapping[str, object]
```

Shared categories are defined by the P-GUI-03 Decision.

---

## 4. Shared error normalization

Move the semantic content of `cli.main._error_exit` to a transport-neutral mapper, for example:

```text
normalize_operation_error(exc) -> OperationFailure
```

CLI adapter:

```text
OperationFailure.category -> exit code -> sgokb.cli/1.0 JSON/text
```

GUI adapter:

```text
OperationFailure.category -> GUI severity / dialog / inline details
```

Do not make Application code depend on CLI exit-code constants.

---

## 5. Runtime extraction

Move semantic runtime construction from `src/sgokb/cli/runtime.py` to a shared module.

Suggested structure:

```text
RuntimeConfig
RuntimeFactory
```

`RuntimeConfig.from_environment()` is allowed for CLI convenience.

GUI later constructs equivalent config from settings/environment.

The factory may lazy-cache:

- embedding provider
- base Qdrant adapter

Repository-aware generation routing is applied when composing each Application operation.

The shared factory must preserve explicit local-only failure and no-cloud-fallback behavior.

---

## 6. Source refactor

Create `SourceOperatorApplication`.

Methods:

```text
status()
snapshots()
select_snapshot(source_id, snapshot_id, reason)
select_run(snapshot_id, run_id, reason)
import_path(path, ...)
process(snapshot_id=None, ...)
```

Batch methods return structured batch outcomes.

Reuse `Application.import_source_path()` and `Application.process_source_snapshot()` for single-item canonical behavior.

CLI `_source_dispatch` becomes argument adaptation only.

---

## 7. Object / Registry refactor

### Object

Retain `ObjectAdminApplication` but add a transport-neutral combined object detail method, either in the same class or a small query facade:

```text
show(object_id, include_knowledge=False, version_id=None)
```

Do not duplicate current-version handling in GUI.

### Registry

Create `RegistryOperatorApplication`.

Methods:

```text
classes()
class_show(ref)
relation_types()
relation_type_show(ref)
proposals(decision=None)
proposal_show(ref)
proposal_decide(ref, accepted|rejected, note)
proposal_apply(ref)
```

Move Relation Type SQL out of `ObjectAdminApplication` into repository/storage ownership.

Keep `accept/reject` separate from `apply`.

---

## 8. Evidence read refactor

Extend `KnowledgeReadApplication` with an explicit provenance method if CLI parity requires the current dedicated provenance payload.

Do not make GUI call `SourceRepository.evidence_provenance()` directly.

No redesign of Evidence semantics occurs in P-GUI-03R.

---

## 9. Package exchange refactor

Create `PackageExchangeApplication`.

Constructor dependencies:

```text
repository
package builder factory/service
transfer service
package audit repository/factory
```

Methods:

```text
build(...)
stage(...)
preflight(...)
export(...)
```

The facade owns all audit writes currently performed in CLI.

P-RAW will modify the underlying Package contract later. Keep GUI-facing operation result transport-neutral and avoid exposing the internal Evidence-Markdown file layout as a durable UI API.

---

## 10. Result exchange refactor

Create `ResultExchangeApplication`.

Methods:

```text
detect(...)
receive(...)
list(package_id=None)
pending()
validate(receipt_id, ..., force=False)
review(receipt_id, ...)
import_result(receipt_id, ..., acknowledge_review=False)
```

Structured review data is authoritative. Markdown review rendering stays outside the canonical operation semantics.

The facade owns audit repository construction and service sequencing.

---

## 11. Version / Render refactor

### VersionReadApplication

```text
show(version_id)
diff(before_version_id, after_version_id)
```

Version-to-Object resolution must not remain direct SQL in CLI presentation code.

### RenderApplication

```text
render(object_id=None, version_id=None, output_root=...)
```

It owns Object->current Version resolution and validates exactly one target selector.

---

## 12. System / recovery refactor

Create `SystemOperatorApplication` with repository-bound methods:

```text
status()
integrity()
derived_status(...)
derived_sync(...)
index_status()
index_rebuild(...)
backup_status(...)
backup_create(...)
composite_backup_create(...)
```

And recovery/path methods that can be invoked without opening the target workspace Repository:

```text
composite_backup_verify(...)
restore_plan(...)
restore_apply(...)
composite_restore_plan(...)
composite_restore_apply(...)
```

`index_rebuild` receives runtime dependencies through the shared RuntimeFactory rather than constructing them in CLI.

---

## 13. Operator dispatcher

Create `OperatorApplication` / `OperatorDispatcher` as a thin semantic router.

Responsibilities:

```text
OperationId
  -> domain facade method
  -> OperationOutcome
```

It is not allowed to contain raw SQL or duplicate domain business algorithms.

The dispatcher centralizes:

- blocked outcome handling
- partial outcome handling
- warnings collection
- shared error normalization

The CLI command hierarchy and GUI capability IDs map to the same OperationIds.

---

## 14. OperatorSession lifecycle

Pseudo-flow:

```text
execute(request):
    if request is path-only recovery operation:
        execute recovery facade without opening target Repository
    else:
        repo = Repository(workspace_path)
        try:
            compose domain applications with RuntimeFactory
            dispatch request
        finally:
            repo.close()
```

For GUI, this method runs on the dedicated backend QThread.

For CLI, one session is created per process invocation.

---

## 15. CLI migration

Refactor `src/sgokb/cli/main.py` into these responsibilities only:

```text
argparse
  -> OperationRequest
  -> OperatorSession.execute()
  -> CLI renderer / exit code
```

Remove from CLI presentation code:

- direct repository mutation
- direct SQL
- Package/Result audit orchestration
- semantic runtime construction
- version target lookup
- render target lookup
- index rebuild construction
- exception-category business mapping

Keep in CLI:

- parser/options
- argv-specific defaults
- text/JSON rendering
- stdout/stderr
- exit code mapping

---

## 16. GUI handoff

P-GUI-04 can then implement:

```text
Qt action/form
   -> OperationRequest
   -> BackendWorker
   -> OperatorSession
   -> OperationOutcome / OperationFailure
   -> GUI presentation
```

No GUI screen needs to know whether the equivalent CLI route is implemented by argparse.

Equivalent CLI command display is generated separately for transparency only.

---

## 17. Implementation slices for P-GUI-03R

### R1 — Shared operation/error contracts

- add OperationId/request/outcome/failure types
- move error normalization semantics out of CLI
- tests for category <-> existing CLI exit code parity

### R2 — Shared runtime factory

- extract `semantic_runtime()` and read composition from CLI namespace
- keep environment compatibility
- tests for no-cloud-fallback/runtime-unavailable behavior

### R3 — Source / Object / Registry

- add SourceOperatorApplication
- add object combined show
- add RegistryOperatorApplication
- move Relation Type SQL to storage layer

### R4 — Evidence / Version / Render

- provenance read method
- VersionReadApplication
- RenderApplication

### R5 — Package / Result

- PackageExchangeApplication
- ResultExchangeApplication
- preserve audit state and acknowledgement behavior

### R6 — System / Recovery

- SystemOperatorApplication
- shared index rebuild composition
- path-only restore handling

### R7 — Operator dispatcher/session

- map 67 public OperationIds
- preserve MCP exception
- introduce structured batch outcome

### R8 — CLI cutover to shared boundary

- parser -> request adaptation
- result -> existing CLI envelope
- remove direct orchestration from CLI

### R9 — Regression / semantic-equivalence tests

Required tests include:

- all existing CLI tests pass
- command output schema unchanged
- exit code mapping unchanged
- canonical DB state equivalence for representative writes
- Package stage/export audit equivalence
- Result validate/review/import equivalence
- Source partial-batch exit 8 equivalence
- restore overwrite acknowledgement equivalence
- Hybrid degradation warning equivalence
- semantic runtime unavailable equivalence
- 67 public operations have dispatcher mapping

---

## 18. Non-goals of P-GUI-03R

Do not implement:

- PySide6 widgets
- P-RAW Package v2 semantics
- Qdrant auto-start
- MCP write support
- new CLI capabilities
- public CLI breaking changes
- canonical schema redesign

---

## 19. Completion gate

P-GUI-03R is complete only when:

1. all 67 public operations are represented in the shared operation inventory;
2. all except `mcp serve` have a shared synchronous Application/operator path;
3. CLI presentation no longer owns direct canonical SQL/business orchestration identified by the audit;
4. current CLI regression passes unchanged;
5. GUI can invoke the shared boundary without importing CLI modules;
6. P-GUI-04 may safely connect UI controls to the backend worker.
