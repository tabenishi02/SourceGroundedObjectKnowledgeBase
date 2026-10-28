# P-GUI-03R — Transport-neutral Application Boundary Refactor Implementation

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **Implemented / Dynamic Verification Pending**
- Priority: **P0**
- Introduced by: `P-GUI-03`
- Design authority: `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`
- Decision authority: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- Implementation result: `docs/evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`

## 1. Reason for insertion

P-GUI-03 audited all 67 public `sgokb` operations and found:

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
```

P-GUI-03 itself was an audit/refactor-plan task and intentionally did not change implementation code.

Proceeding directly to P-GUI-04 canonical operation wiring would require the GUI to duplicate CLI orchestration or depend on CLI modules, violating P-GUI-01/P-GUI-02 contracts.

Therefore this remediation implementation task was inserted before P-GUI-04 backend integration.

## 2. Scope

Implemented transport-neutral boundary:

- shared operation request/outcome/failure contracts
- shared error normalization
- shared semantic runtime factory
- SourceOperatorApplication
- Object combined detail query
- RegistryOperatorApplication
- Evidence provenance read boundary
- PackageExchangeApplication
- ResultExchangeApplication
- VersionReadApplication
- RenderApplication
- SystemOperatorApplication / recovery surface
- Operator dispatcher/session
- CLI migration to the shared boundary
- regression/equivalence test asset

## 3. Execution slices

```text
R1 Shared operation/error contracts       Implemented
R2 Shared runtime factory                 Implemented
R3 Source/Object/Registry boundaries      Implemented
R4 Evidence/Version/Render boundaries     Implemented
R5 Package/Result boundaries              Implemented
R6 System/Recovery boundary               Implemented
R7 Operator dispatcher/session            Implemented
R8 CLI cutover                            Implemented
R9 Regression / semantic-equivalence      Test asset + static review complete;
                                          dynamic execution pending
```

## 4. Implemented boundary

The public inventory is now explicit in `src/sgokb/application_operator.py`:

```text
PUBLIC_OPERATION_IDS    = 67
TRANSPORT_OPERATION_IDS = 1  (mcp.serve)
SHARED_OPERATION_IDS    = 66
```

The synchronous path is:

```text
CLI parser / future GUI worker
        ↓
OperationRequest
        ↓
OperatorSession
        ↓
Domain Application facades
        ↓
Repository / Retrieval / Exchange
```

`mcp.serve` remains a transport-specific stdio lifecycle operation and is not dispatched as a synchronous `OperatorSession` call.

## 5. Hard constraints preserved

- no intended public CLI semantic change
- no GUI implementation in this task
- no P-RAW schema changes
- no canonical schema redesign
- no cloud semantic fallback
- no new presentation-layer canonical SQL path
- `mcp serve` remains transport-specific
- Registry Proposal accept/reject/apply remains separate
- Package/Result audit lifecycle remains explicit
- Restore acknowledgement/safety remains delegated to the existing recovery contract

## 6. Regression asset / verification

Added:

```text
tests/test_p_gui_03r_operator_boundary.py
```

Static compatibility review also covered the existing high-value suites:

```text
tests/test_m01_cli.py
tests/test_m03_standard_workflow.py
tests/test_m01_registry_proposals.py
tests/test_j01_application_semantics.py
tests/test_m05_historical_derived_reconciliation.py
```

The current ChatGPT repository-edit environment does not provide an authorized Python/pytest execution surface for this local repository, and the repository had no existing GitHub Actions workflow at the task boundary. No synthetic CI workflow was added solely to claim a PASS.

Required dynamic verification:

```text
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

No dynamic PASS is claimed until these complete successfully.

## 7. Completion gate state

| Gate | State |
|---|---|
| 67 public operation IDs inventoried | Satisfied |
| 66 synchronous operations callable without CLI presentation import | Satisfied |
| `mcp serve` transport lifecycle separated | Satisfied |
| CLI moved to shared operator boundary | Satisfied |
| Package/Result lifecycle preserved by design/static review | Satisfied pending regression execution |
| Restore safety preserved by design/static review | Satisfied pending regression execution |
| New operator-boundary regression test exists | Satisfied |
| Existing CLI test suite passes | **Pending dynamic execution** |
| Full pytest/ruff regression passes | **Pending dynamic execution** |

Therefore the task state is **Implemented / Dynamic Verification Pending**, not Complete/PASS.

## 8. Dependency update

Effective dependency chain:

```text
P-GUI-03 Complete / Accepted
        ↓
P-GUI-03R Implemented / Verification Pending
        ↓ verification PASS
P-GUI-03R Complete / Accepted
        ↓
P-GUI-04 GUI shell / Workspace / navigation + backend wiring
```

P-GUI-04 presentation-only planning is possible, but canonical backend wiring remains blocked until the P-GUI-03R regression gate passes.

This document is a Phase P task amendment and supersedes the direct `P-GUI-03 -> P-GUI-04` execution assumption in the original Phase P task list.
