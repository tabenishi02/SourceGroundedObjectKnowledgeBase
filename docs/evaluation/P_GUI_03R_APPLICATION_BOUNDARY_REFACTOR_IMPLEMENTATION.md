# P-GUI-03R — Transport-neutral Application Boundary Refactor Implementation Result

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation`
- Status: **Complete / Accepted**
- Design authority: `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`
- Decision authority: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- Final R9 acceptance: `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

## 1. Result summary

All implementation and verification slices are complete in `main`.

```text
R1 Shared operation/error contracts       Complete
R2 Shared runtime factory                 Complete
R3 Source/Object/Registry boundaries      Complete
R4 Evidence/Version/Render boundaries     Complete
R5 Package/Result boundaries              Complete
R6 System/Recovery boundary               Complete
R7 Operator dispatcher/session            Complete
R8 CLI cutover                            Complete
R9 Regression / semantic equivalence      Complete / PASS
```

No PySide6 widget, P-RAW schema, Qdrant auto-start, MCP write capability or canonical schema redesign was introduced.

## 2. Implemented shared boundary

The accepted operator path is:

```text
CLI parser / renderer ─┐
                       │
GUI worker ────────────┼─> OperationRequest
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

## 3. Shared modules

Implemented modules include:

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

`operation_contracts.py` defines transport-neutral `OperationRequest`, `OperationOutcome`, `OperationFailure`, shared failure categories and exception normalization. CLI exit-code constants remain outside the Application layer.

`runtime.py` defines `RuntimeConfig` and `RuntimeFactory`, keeps local-only semantic runtime construction, supports repository-aware generation routing and does not introduce a cloud fallback.

## 4. Public operation inventory

`application_operator.py` contains the complete public inventory:

```text
PUBLIC_OPERATION_IDS    = 67
TRANSPORT_OPERATION_IDS = 1  (mcp.serve)
SHARED_OPERATION_IDS    = 66
```

All 66 synchronous public operations have an `OperatorSession` execution path that does not require importing `sgokb.cli` presentation code.

## 5. Domain extraction and compatibility

The refactor moved CLI-owned orchestration into shared Applications while retaining established semantics:

- Source status/snapshots/effective selection/batch import/batch process;
- Object combined detail and exact selector behavior;
- Registry reads and Proposal lifecycle;
- Evidence show/provenance/search reads;
- Version target resolution and diff;
- Render target resolution;
- Package build/transfer and audit sequencing;
- Result receipt/validation/review/import sequencing;
- System derived/index/backup operations;
- path-only recovery verify/restore behavior.

Compatibility review and dynamic regression confirmed preservation of:

- `sgokb.cli/1.0` envelope;
- exit-code categories 1-8;
- Source batch partial semantics;
- Package/Result blocked behavior;
- hybrid degradation warnings and `--require-full-runtime` fail-closed behavior;
- no semantic cloud fallback;
- Registry Proposal separation;
- Relation Type public `id` field;
- restore acknowledgement and composite recovery safety;
- historical derived-runtime unavailable normalization.

## 6. CLI cutover

`src/sgokb/cli/main.py` now follows:

```text
argparse
  -> semantic Operation ID + arguments
  -> OperatorSession.execute()
  -> OperationOutcome / OperationFailure
  -> existing sgokb.cli/1.0 renderer / exit code
```

Presentation-only Markdown formatting remains in the CLI adapter. `src/sgokb/cli/runtime.py` remains a compatibility shim over the shared `RuntimeFactory`, preserving historical test patch points without owning runtime policy.

## 7. Regression asset

`tests/test_p_gui_03r_operator_boundary.py` covers the explicit inventory, shared-operation count, transport-only `mcp.serve`, direct operator execution, failure normalization and CLI envelope preservation.

High-value existing suites retained as compatibility authority include:

```text
tests/test_m01_cli.py
tests/test_m03_standard_workflow.py
tests/test_m01_registry_proposals.py
tests/test_j01_application_semantics.py
tests/test_m05_historical_derived_reconciliation.py
```

## 8. Dynamic acceptance evidence

Final accepted execution evidence on Windows / Python 3.10.6:

```text
operator-boundary + M01 CLI = 18 / 18 PASS
M03 standard workflow       = 2 / 2 PASS
Phase N closure audit       = 11 / 11 PASS
full pytest                 = 795 / 795 PASS
ruff                        = All checks passed!
```

The full regression emitted two local-Qdrant capability warnings only; there were no failures or errors.

R9 historical attempts are retained in:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_02.md`
- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_03.md`
- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

Attempt 04 is the final acceptance authority.

## 9. Completion disposition

All P-GUI-03R completion criteria are satisfied:

- 67 public operation IDs inventoried;
- 66 synchronous operations have a shared non-CLI execution path;
- MCP stdio remains transport-specific;
- CLI business orchestration identified by P-GUI-03 has been moved to shared Applications/session;
- GUI can target `OperatorSession` without importing CLI presentation modules;
- full dynamic regression and Ruff gates pass.

P-GUI-03R is formally **Complete / Accepted**.

P-GUI-04 canonical backend wiring is unblocked and is the next GUI task.
