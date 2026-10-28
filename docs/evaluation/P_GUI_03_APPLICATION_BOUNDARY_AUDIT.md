# P-GUI-03 Transport-neutral Application Boundary Audit

Updated: 2026-10-28

- Status: **Accepted / P-GUI-03 audit**
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-03 [P0] Transport-neutral Application boundary audit / refactor plan`
- Baseline: current `main` after P-GUI-02
- Public parity baseline: **67 `sgokb` operations**
- GUI compatibility authority: `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- PySide6 architecture authority: `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`

---

## 1. Purpose

P-GUI-03 audits the current CLI execution path and identifies which semantics can be reused directly by a GUI and which semantics still live in CLI dispatch code, direct Repository calls, or transport-specific composition.

The objective is not to redesign canonical SGOKB semantics. The objective is to prevent the PySide6 client from copying CLI business/orchestration logic.

Target boundary:

```text
CLI parser / renderer ─┐
                       │
GUI controller/worker ─┼─> transport-neutral operator/application boundary
                       │                │
MCP read adapter ──────┘                ▼
                              Application / Service
                                       │
                                       ▼
                         Repository / Retrieval / Exchange
```

---

## 2. Audit method

The audit compared:

- `src/sgokb/cli/main.py`
- `src/sgokb/cli/runtime.py`
- `src/sgokb/cli/contracts.py`
- `src/sgokb/application.py`
- `src/sgokb/application_admin.py`
- `src/sgokb/application_read.py`
- `src/sgokb/application_derived.py`
- `src/sgokb/application_generation.py`
- exchange / review / rendering / system operation services
- current CLI <-> GUI 67-operation capability matrix

Each public operation is assigned one readiness class:

```text
A READY
  Existing Application boundary is suitable for direct GUI reuse.

B ORCHESTRATION EXTRACTION
  Lower-level Service/Application exists, but CLI currently owns sequencing,
  audit write, target resolution, batch handling, or result shaping.

C APPLICATION GAP
  CLI currently reaches Repository/direct SQL or owns material business semantics;
  a new/extended transport-neutral Application boundary is required.

D TRANSPORT-SPECIFIC
  Operation is inherently a transport lifecycle concern rather than canonical
  business logic.
```

---

## 3. Result summary

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
--------------------------------
Total                      67
```

There are no GUI capability gaps in the P-GUI-01 feature inventory, but **42 / 67 public operations must not be implemented by copying current CLI dispatch code**.

The current system is therefore structurally ready for GUI work on the read/search core, but not yet ready for a parity GUI across the full operator surface.

---

## 4. Existing strong reusable boundaries

### 4.1 KnowledgeReadApplication

`KnowledgeReadApplication` is already explicitly documented as the boundary for CLI, MCP and future clients. It owns Object read, Search, Similarity, Evidence read/search and Context Builder composition while requiring runtime providers/indexes to be injected externally.

This is the strongest existing GUI seam and should remain authoritative for Knowledge reads.

### 4.2 ObjectAdminApplication

Most Object Registry operations are already grouped under `ObjectAdminApplication`:

- add / list / rename / status
- alias list / add
- class set-primary / add / remove
- registry events
- class list / show

The main defects are:

1. `object show --knowledge` composition still lives in CLI dispatch.
2. relation-type reads inside `ObjectAdminApplication` use direct SQL and should move to a repository/application boundary with explicit ownership.

### 4.3 Application ingestion / association / evidence selection

`Application` already provides reusable Source import/process, Association operations, Evidence candidate retrieval and Evidence budget selection.

The CLI still owns multi-target enumeration and partial-result behavior for Source import/process.

### 4.4 DerivedSearchOperatorApplication

`system derived status/sync` and R2 generation lifecycle have explicit operator Application classes and are suitable for reuse after runtime composition is extracted from `sgokb.cli.runtime`.

---

## 5. CLI-local semantics that require extraction

### 5.1 Source operations

CLI currently owns:

- Source status assembly
- Snapshot list projection and `effective` calculation
- effective Snapshot selection response shaping
- effective Run selection response shaping
- directory recursion for batch import
- all-Snapshot enumeration for batch process
- per-item failure accumulation and partial outcome

The GUI must not reimplement these rules.

Required boundary: `SourceOperatorApplication`.

### 5.2 Object / Registry

CLI currently composes `object show --knowledge` by manually combining `ObjectAdminApplication` and `KnowledgeReadApplication`.

Registry Proposal operations call `repository.registry_proposals` directly from CLI.

Relation Type list/show currently reside in `ObjectAdminApplication` but issue SQL directly.

Required boundaries:

- extend Object application query composition
- `RegistryOperatorApplication`
- repository-owned Relation Type read methods

### 5.3 Evidence provenance

`evidence provenance` calls `repository.source_store.evidence_provenance` directly while `KnowledgeReadApplication.get_evidence()` already exposes a related transport-neutral view.

Required boundary: explicit `get_evidence_provenance()` or a documented projection option in the read application. Do not make GUI depend on SourceRepository objects directly.

### 5.4 Package exchange

`ObjectEvidencePackageBuilder` and `PackageTransferService` are reusable, but CLI owns important orchestration:

- creation of `PackageExchangeAuditRepository`
- audit event recording after stage/export
- manifest reload for audit fields
- construction of export return payload with audit event ID

Required boundary: `PackageExchangeApplication`.

P-RAW will later replace parts of Package semantics. The facade should be introduced without freezing the v1 payload as a permanent GUI contract.

### 5.5 Result exchange

Result services are reusable individually, but CLI composes the audit repository and selects among detect / receive / validate / review / import services.

Required boundary: `ResultExchangeApplication`.

The Application must preserve:

```text
receive -> validate -> review -> explicit import
```

and must not collapse validation/review acknowledgement rules.

### 5.6 Version

`version show` performs direct SQL against `object_versions` to resolve the Object before calling `KnowledgeReadApplication`.

`version diff` directly composes `DiffReviewService` and rendering choice in CLI.

Required boundary: `VersionReadApplication` or an extension of `KnowledgeReadApplication`/review application with:

- show version by stable Version ID
- structured diff
- Markdown diff as presentation rendering, not canonical semantics

### 5.7 Render

CLI resolves Object -> current Version and then invokes `MarkdownRenderService`.

Required boundary: `RenderApplication` with explicit target selector contract.

### 5.8 System / recovery

`system_ops.py` functions are transport-neutral functions, but the CLI owns their composition and mixes repository-bound and path-only operations.

`system index rebuild` additionally constructs semantic runtime and `KnowledgeVectorIndexBuilder` directly in CLI.

Composite backup/restore functions are also called directly.

Required boundary: `SystemOperatorApplication` plus path-only recovery entrypoints that can run without first opening the target Repository.

---

## 6. Runtime composition audit

`src/sgokb/cli/runtime.py` currently owns environment-driven construction of:

- sentence-transformer provider
- Qdrant adapter
- generation routing
- `KnowledgeReadApplication`

This module is CLI-namespaced even though the semantics are not CLI-specific.

Required change:

```text
sgokb.cli.runtime
      ↓ move shared composition
sgokb.runtime / sgokb.application_runtime
```

The shared runtime factory must remain:

- local-only
- explicit
- no silent cloud fallback
- environment/config driven
- usable by CLI and GUI BackendSession

The GUI BackendSession may cache expensive provider/vector clients, but Repository connections remain per operation as frozen in P-GUI-02.

---

## 7. Error contract audit

Current CLI maps Python exceptions to exit categories in `cli.main._error_exit` and renders them through `sgokb.cli/1.0`.

That mapping is currently transport-local. If GUI invents its own exception interpretation, semantic drift is likely.

Required shared model:

```text
OperationOutcome
  data
  warnings
  state = success | blocked | partial

OperationFailure
  category = internal | input | not_found | blocked |
             runtime | io | integrity
  code
  message
  details
```

CLI exit codes remain a CLI adapter concern:

```text
success   -> 0
internal  -> 1
input     -> 2
not_found -> 3
blocked   -> 4
runtime   -> 5
io        -> 6
integrity -> 7
partial   -> 8
```

GUI maps the same category to visual presentation rather than exit codes.

---

## 8. Batch semantics audit

Source import/process currently implement batch partial handling only in CLI.

The shared boundary must return item-level results and explicit aggregate state rather than throwing away successful items when some items fail.

Required shape:

```text
BatchOutcome
  total_count
  succeeded_count
  failed_count
  partial
  items[]
```

This allows CLI exit 8 and GUI partial-failure presentation to derive from one result.

---

## 9. Target identity audit

CLI object selectors allow exact name/alias resolution for operator convenience but ultimately execute writes by stable Object ID.

The shared boundary should separate:

```text
selector resolution
        ↓
stable canonical ID
        ↓
operation execution
```

GUI autocomplete/fuzzy browsing is presentation-only. A WRITE request must contain the resolved stable ID at execution time.

The same principle applies to Version, Source, Snapshot, Run, Proposal and receipt identifiers.

---

## 10. MCP exception

`sgokb mcp serve` is fundamentally transport lifecycle, not a normal canonical operation.

It should not be forced into the same synchronous `OperationRequest -> OperationOutcome` execution path.

The shared KnowledgeReadApplication remains the MCP business boundary.

P-GUI-09 may expose MCP lifecycle/configuration controls, but the MCP server transport remains isolated from canonical GUI operation dispatch.

This is the sole D-class public operation.

---

## 11. Direct SQL policy

P-GUI-01 prohibits hidden GUI canonical write paths. P-GUI-03 strengthens the boundary:

- GUI modules must not import `sqlite3` for SGOKB canonical data.
- GUI modules must not call `repository.db.execute`.
- CLI presentation code should also stop owning business SQL during the refactor.
- Application implementations may call repositories; storage-specific SQL should normally remain in repository/storage modules.

Existing direct SQL inside operator Application classes is technical debt to move toward repository ownership, not a pattern to copy.

---

## 12. Conclusion

The current codebase has a strong read boundary and several reusable domain services, so a GUI does not require a rewrite of SGOKB.

However, proceeding directly to P-GUI-04 would force the GUI either to:

1. duplicate 42 operations' orchestration/selection/error behavior, or
2. improperly call CLI dispatch/subprocess code.

Therefore a short implementation remediation must be inserted before the GUI shell uses the backend broadly.

Formal disposition:

```text
P-GUI-03 audit / design = PASS
Direct transition to full P-GUI-04 backend use = BLOCKED
Required next task = P-GUI-03R transport-neutral boundary refactor implementation
```
