# P-GUI-03R — Transport-neutral Application Boundary Refactor Implementation Result

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation`
- Status: **Implemented / Dynamic Verification Pending**
- Design authority: `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`
- Decision authority: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`

## 1. Result summary

R1-R8 implementation slices are complete in `main`.

```text
R1 Shared operation/error contracts       Implemented
R2 Shared runtime factory                 Implemented
R3 Source/Object/Registry boundaries      Implemented
R4 Evidence/Version/Render boundaries     Implemented
R5 Package/Result boundaries              Implemented
R6 System/Recovery boundary               Implemented
R7 Operator dispatcher/session            Implemented
R8 CLI cutover                            Implemented
R9 Regression / semantic equivalence      Test assets + static review complete;
                                          dynamic execution pending
```

No PySide6 widget, P-RAW schema, Qdrant auto-start, MCP write capability or canonical schema redesign was introduced.

## 2. Implemented shared boundary

The operator path is now:

```text
CLI parser / renderer ─┐
                       │
future GUI worker ─────┼─> OperationRequest
                       │       ↓
                       │   OperatorSession
                       │       ↓
                       │   Domain Application facades
                       │       ↓
                       │   Repository / Retrieval / Exchange
                       │
MCP read transport ────┘  (read boundary remains separate)
```

`mcp.serve` remains a transport lifecycle operation and is intentionally excluded from synchronous `OperatorSession.execute()`.

## 3. New shared modules

Added:

```text
src/sgokb/operation_contracts.py
src/sgokb/runtime.py
src/sgokb/application_source.py
src/sgokb/application_registry.py
src/sgokb/application_evidence.py
src/sgokb/application_version.py
src/sgokb/application_render.py
src/sgokb/application_exchange.py
src/sgokb/application_system.py
src/sgokb/application_operator.py
```

### Operation contract

`operation_contracts.py` defines:

- `OperationRequest`
- `OperationOutcome`
- `OperationFailure`
- transport-neutral error categories
- shared exception normalization

CLI exit-code constants are not imported into the Application layer.

### Runtime factory

`runtime.py` defines:

- `RuntimeConfig`
- `RuntimeFactory`
- local-only Embedding + Qdrant construction
- repository-aware generation routing
- lazy noncanonical runtime caching

No cloud fallback was added.

## 4. Public operation inventory

`application_operator.py` contains the complete public inventory.

```text
PUBLIC_OPERATION_IDS    = 67
TRANSPORT_OPERATION_IDS = 1  (mcp.serve)
SHARED_OPERATION_IDS    = 66
```

All 66 synchronous public operations have an `OperatorSession` execution path that does not require importing `sgokb.cli` presentation code.

## 5. Domain extraction

### Source

`SourceOperatorApplication` owns:

- status / snapshots
- effective Snapshot / Run selection
- batch import
- batch process
- item-level partial failure result

Single-item canonical behavior still delegates to the established `Application` methods.

### Object / Registry

`ObjectAdminApplication.show()` now owns registry + accepted Knowledge combined detail semantics.

Relation Type SQL was moved into `ObjectRepository`; `RegistryOperatorApplication` exposes registry reads and Proposal lifecycle. Public Relation Type payload continues to use the historical `id` field rather than leaking the internal dataclass field name `relation_type_id`.

Proposal accept/reject remains separate from apply.

### Evidence / Version / Render

Dedicated facades now own:

- Evidence show/provenance/search operator reads
- Version ID -> Object resolution and Version diff
- Object -> current Version render target resolution

CLI presentation code no longer performs those SQL/target-resolution steps.

### Package / Result

`PackageExchangeApplication` owns Package Builder / Transfer sequencing plus stage/export audit writes.

`ResultExchangeApplication` owns receipt, validation, review and import service composition.

Existing Package / Result v1 semantics are unchanged; P-RAW remains a later task.

### System / Recovery

`SystemOperatorApplication` owns repository-bound status, integrity, derived/index and backup operations.

`RecoveryOperatorApplication` owns path-only verify/restore operations that must run without first opening the target workspace database.

Overwrite acknowledgement and composite restore safety behavior remain delegated to the existing recovery implementation.

## 6. CLI cutover

`src/sgokb/cli/main.py` now follows:

```text
argparse
  -> semantic Operation ID + arguments
  -> OperatorSession.execute()
  -> OperationOutcome / OperationFailure
  -> existing sgokb.cli/1.0 renderer / exit code
```

Presentation-only Markdown formatting for Result review and Version diff remains in the CLI adapter.

`mcp.serve` remains in the CLI transport adapter because its stdio lifecycle is not a synchronous canonical operation.

`src/sgokb/cli/runtime.py` remains as a compatibility shim over the shared `RuntimeFactory`, preserving patch points used by existing CLI tests while removing ownership of the runtime policy from the CLI namespace.

## 7. Compatibility preservation reviewed

Static review checked the following existing contracts:

- `sgokb.cli/1.0` success/error envelope remains owned by `cli/contracts.py`.
- exit categories remain mapped to existing exit codes 1-8.
- Source import/process partial batches map to exit 8 through `OperationOutcome.state=partial`.
- Package preflight blocked maps to exit 4 and preserves the existing warning.
- Result validation that does not reach `valid` maps to exit 4 and preserves the existing warning.
- Hybrid degraded channels remain warnings.
- `--require-full-runtime` remains fail-closed.
- no semantic runtime cloud fallback was introduced.
- Object exact selector/ambiguity semantics remain in `ObjectAdminApplication`.
- Package stage/export audit sequencing moved intact to the Package Application facade.
- Result validation/review/import sequencing moved intact to the Result Application facade.
- restore plan/apply and overwrite acknowledgement remain unchanged.
- Registry Proposal accept/reject/apply lifecycle remains separate.
- Relation Type public payload retains the prior `id` key.
- shared GUI-facing defaults use the same canonical constants as CLI for Package build, Result incoming and Render output.

## 8. Regression test asset

Added:

```text
tests/test_p_gui_03r_operator_boundary.py
```

It covers at minimum:

- exact public inventory count: 67
- exact shared synchronous count: 66
- `mcp.serve` transport-only classification
- direct Object write/read through `OperatorSession` without CLI import
- selector failure normalization
- CLI `sgokb.cli/1.0` envelope after cutover
- synchronous rejection of `mcp.serve`

Existing high-value regression suites reviewed for compatibility include:

```text
tests/test_m01_cli.py
tests/test_m03_standard_workflow.py
tests/test_m01_registry_proposals.py
tests/test_j01_application_semantics.py
tests/test_m05_historical_derived_reconciliation.py
```

`test_m03_standard_workflow.py` remains the important public CLI vertical slice covering Source -> Evidence -> Package -> Result -> Import -> Render -> Search and MCP read.

## 9. Dynamic verification status

The current ChatGPT execution environment used for this repository edit provides GitHub file operations but not an authorized Python/pytest execution environment for this local repository. No GitHub Actions workflow existed in the repository at this task boundary, and this task did not add unrelated CI infrastructure solely to manufacture a PASS result.

Therefore **no dynamic pytest/ruff PASS is claimed**.

Required verification commands on the project environment are:

```text
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

The M03 MCP test may require the existing optional MCP dependency as before.

## 10. Completion disposition

Implementation completion criteria are satisfied for R1-R8:

- 67 public operation IDs inventoried;
- 66 synchronous operations have a shared non-CLI execution path;
- MCP stdio remains transport-specific;
- CLI business orchestration identified by P-GUI-03 has been moved to shared Applications/session;
- GUI can target `OperatorSession` without importing CLI presentation modules.

Formal task closure remains **Verification Pending** until the regression commands above pass on an executable project environment.

P-GUI-04 canonical backend wiring must remain gated on that verification result. Presentation-only planning is not blocked.
