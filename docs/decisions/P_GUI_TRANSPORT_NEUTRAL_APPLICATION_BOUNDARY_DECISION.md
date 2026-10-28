# P-GUI Transport-neutral Application Boundary Decision

Updated: 2026-10-28

- Status: **Accepted / P-GUI-03**
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-03 [P0] Transport-neutral Application boundary audit / refactor plan`
- Audit: `docs/evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`
- Matrix: `docs/reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`

---

## 1. Decision

CLI and GUI shall share a transport-neutral operator execution boundary.

The target architecture is:

```text
CLI parser/renderer ───────┐
                           │
GUI controller/worker ─────┼────> OperatorSession
                           │            │
                           │            ├─ OperationRequest
                           │            ├─ OperationOutcome / OperationFailure
                           │            │
                           │            └─ Domain Application facades
                           │                    │
MCP read adapter ──────────┘                    ▼
                                    Repository / Retrieval / Exchange
```

MCP read traffic continues to use `KnowledgeReadApplication` directly through its MCP adapter and is not forced through operator mutation dispatch.

---

## 2. Shared operation contract

Introduce a transport-neutral operation identity and outcome model.

Conceptual contract:

```text
OperationRequest
  operation_id
  arguments

OperationOutcome
  operation_id
  data
  warnings[]
  state = success | blocked | partial

OperationFailure
  operation_id
  category
  code
  message
  details
```

`operation_id` is semantic and transport-independent, for example:

```text
object.add
source.select_snapshot
registry.proposal.apply
package.export
system.restore.apply
```

It is not an argv string and does not contain presentation formatting options.

---

## 3. Error categories

Shared failure categories:

```text
internal
input
not_found
blocked
runtime
io
integrity
```

Partial is represented as an `OperationOutcome.state`, not an exception category.

CLI maps these to the existing exit codes 1-8. GUI maps the same categories to dialogs/banner/detail surfaces.

The exception-to-category mapping shall move out of `sgokb.cli.main._error_exit` into a transport-neutral module.

CLI-specific JSON schema `sgokb.cli/1.0` remains a CLI presentation contract only.

---

## 4. OperatorSession

`OperatorSession` is a non-Qt, transport-neutral execution context.

Responsibilities:

- hold Workspace/DB path
- hold runtime configuration/factory reference
- create a Repository for each canonical operation
- compose required Application facades
- execute one `OperationRequest`
- close Repository deterministically
- normalize warnings / blocked / partial / failure categories

Non-responsibilities:

- Qt thread ownership
- Widgets / dialogs
- stdout/stderr
- argparse
- JSON CLI rendering
- filesystem picker UI

GUI `BackendSession` from P-GUI-02 may wrap or own one `OperatorSession`, but PySide6 types must not enter the operator module.

---

## 5. Repository lifetime

The P-GUI-02 rule remains authoritative:

```text
one operation
  -> open Repository on execution thread
  -> execute Application semantics
  -> close Repository on same thread
```

`OperatorSession` therefore must not retain a SQLite Repository connection between operations.

Expensive noncanonical runtime clients may be retained separately by a RuntimeFactory/session cache.

---

## 6. RuntimeFactory

Move reusable semantic runtime construction out of `sgokb.cli.runtime`.

Target responsibilities:

```text
RuntimeConfig
  model_cache
  local_files_only
  qdrant_url
  qdrant_grpc_port
  prefer_grpc
  collection_prefix

RuntimeFactory
  get_embedding_provider()
  get_vector_index()
  build_read_application(repository, semantic=...)
  build_derived_application(repository, semantic=...)
```

Rules:

- no cloud fallback
- local runtime failures remain explicit
- CLI environment variables may populate `RuntimeConfig`
- GUI Settings may populate the same config later
- runtime clients may be lazy cached
- generation routing remains Repository-aware and is applied during Application composition

---

## 7. Domain facade decisions

### 7.1 SourceOperatorApplication

Own:

- source status projection
- snapshot list projection
- effective Snapshot / Run selection
- import single/batch
- process single/batch
- item-level batch outcome

Reuse existing `Application` ingestion methods internally.

### 7.2 Object / Registry

Keep `ObjectAdminApplication` for Object mutations.

Add/extend transport-neutral query composition for `object show --knowledge`.

Create `RegistryOperatorApplication` for:

- Class list/show
- Relation Type list/show
- Proposal list/show
- Proposal accept/reject
- Proposal apply

Relation Type SQL belongs in storage/repository, not GUI or CLI presentation.

### 7.3 Knowledge read

Keep `KnowledgeReadApplication` as the canonical read/search/similarity boundary.

Add explicit Evidence provenance projection if needed for CLI parity.

### 7.4 PackageExchangeApplication

Own:

- build
- stage
- preflight
- export
- Package audit recording
- manifest/audit correlation

It must remain adaptable to P-RAW. GUI shall not bind to internal v1 Evidence Markdown structure through this facade.

### 7.5 ResultExchangeApplication

Own:

- detect
- receive
- list
- pending
- validate
- review
- import

Preserve explicit review/acknowledgement boundaries.

### 7.6 VersionReadApplication

Own:

- version lookup by stable Version ID
- version show
- structured version diff

Markdown diff rendering remains a presentation helper layered over the structured report.

### 7.7 RenderApplication

Own target resolution:

```text
object_id -> current accepted version -> render
version_id -> render
```

### 7.8 SystemOperatorApplication

Own:

- system status / integrity
- derived status / sync composition
- index status / rebuild
- backup status / create
- composite backup create / verify

Recovery operations that target a DB file before it can safely be opened remain path-based methods in the same system/recovery Application surface.

### 7.9 Search Generation Maintenance

Reuse `KnowledgeSearchGenerationApplication` / `DerivedSearchOperatorApplication` behind the shared runtime factory.

The six generation lifecycle actions remain Advanced operations and are outside the 67 public parity gate.

---

## 8. Selector rule

Presentation layers may help users find a target, but execution uses stable IDs.

CLI exact-name selector resolution and GUI autocomplete must converge to the same stable ID before mutation.

No Application method shall accept a fuzzy human label as the authoritative target for a canonical mutation.

---

## 9. Batch rule

Batch behavior is Application semantics when partial success is meaningful.

Source batch import/process must return a structured aggregate result so both transports preserve:

- successful items
- failed items
- partial=true

CLI translates `partial=true` to exit code 8. GUI shows item-level partial failure.

---

## 10. Presentation-only transformations

The following remain outside canonical Application semantics:

- CLI JSON/text rendering
- Markdown pretty rendering of an already-structured diff/review
- Equivalent CLI command display
- table sort/filter
- widget state
- file picker interaction

These may transform an `OperationOutcome` but must not change canonical meaning.

---

## 11. MCP transport exception

`mcp serve` is not a normal `OperationRequest` because serving stdio is a long-lived transport lifecycle.

The business boundary remains:

```text
Repository -> KnowledgeReadApplication -> MCPReadAdapter -> MCP transport
```

GUI lifecycle control, if implemented, is handled separately in P-GUI-09.

---

## 12. Prohibited patterns

After P-GUI-03R:

- GUI importing `sgokb.cli.main` to perform business operations: prohibited
- GUI launching `sgokb ...` subprocesses for canonical operations: prohibited
- GUI direct SQLite canonical reads/writes: prohibited
- duplicate CLI/GUI exception categorization logic: prohibited
- duplicate CLI/GUI Package/Result audit orchestration: prohibited
- retaining one Repository connection across Qt threads: prohibited

A subprocess may still be appropriate for an inherently separate transport/service lifecycle, such as a future MCP process, but not as the canonical business API.

---

## 13. Compatibility requirement

CLI migration to the shared boundary must preserve:

- command names/options
- `sgokb.cli/1.0` envelope
- exit codes
- warnings/degradation semantics
- canonical DB effects
- audit effects
- review/acknowledgement safety
- batch partial behavior

P-GUI-03R is therefore a refactor with **zero intended public CLI semantic change**.

---

## 14. Gate

P-GUI-03 design is accepted.

Before full P-GUI-04 backend integration, implement the remediation task:

```text
P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation
```

P-GUI-04 may begin only with shell/presentation work that does not bypass this boundary; canonical operation wiring depends on P-GUI-03R completion.
