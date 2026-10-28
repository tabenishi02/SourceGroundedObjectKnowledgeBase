# P-GUI-03R — Transport-neutral Application Boundary Refactor Implementation

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **Implemented / Dynamic Verification In Progress**
- Priority: **P0**
- Introduced by: `P-GUI-03`
- Design authority: `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`
- Decision authority: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- Implementation result: `docs/evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`
- R9 Attempt 01: `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

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
R9 Regression / semantic-equivalence      In Progress
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

## 6. Regression asset / R9 Attempt 01

Added:

```text
tests/test_p_gui_03r_operator_boundary.py
```

Operator execution on Windows/Python 3.10.6 produced:

```text
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
→ 17 passed / PASS

python -m pytest tests/test_m03_standard_workflow.py
→ NOT RUN / environment blocked
   installed `sgokb` console script not found

python -m pytest
→ NOT RUN / collection environment blocked
   `qdrant_client` optional dependency missing

python -m ruff check src tests
→ findings found; remediation applied after Attempt 01
```

The targeted 17-test PASS validates the new shared boundary regression asset together with the existing M01 CLI contract tests.

The M03 errors occurred before workflow execution because `WorkflowCLI` intentionally requires the installed public `sgokb` entry point. The full-suite errors occurred during collection because the Qdrant Python client was not installed. Neither result is classified as a semantic regression.

Ruff findings were classified and remediated after Attempt 01:

- new P-GUI-03R E501/F841 findings in small Application facades were corrected;
- the explicit operator dispatch table received narrow E501/I001 per-file handling;
- two existing pytest fixture re-export modules received narrow F811 per-file handling.

A clean Ruff PASS is not asserted until rerun.

Detailed evidence:

`docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

## 7. Attempt 02 environment preflight

From the repository root after updating to current `main`:

```powershell
git pull --ff-only
python -m pip install -e ".[dev,mcp,vector-qdrant]"
python -m pip check
Get-Command sgokb
python -c "import qdrant_client; print(qdrant_client.__file__)"
```

This provides:

- the public `sgokb` console script required by M03;
- pytest / Ruff;
- MCP SDK so the M03 MCP-read path executes;
- Qdrant Python client required by the existing full-suite collection.

## 8. Attempt 02 verification commands

```powershell
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

If a later full-suite test requires an external service rather than only an installed Python package, record that separately as a runtime-environment gate.

## 9. Completion gate state

| Gate | State |
|---|---|
| 67 public operation IDs inventoried | Satisfied |
| 66 synchronous operations callable without CLI presentation import | Satisfied |
| `mcp serve` transport lifecycle separated | Satisfied |
| CLI moved to shared operator boundary | Satisfied |
| New operator-boundary regression test exists | Satisfied |
| New boundary + M01 CLI targeted regression | **PASS — 17/17** |
| M03 public CLI vertical slice | **Pending rerun after editable install** |
| Full pytest regression | **Pending rerun after Qdrant client install** |
| Full Ruff regression | **Remediation applied / rerun pending** |
| Package/Result lifecycle preserved | Pending M03/full regression confirmation |
| Restore safety preserved | Pending full regression confirmation |

Therefore the task state remains **Implemented / Dynamic Verification In Progress**, not Complete/PASS.

## 10. Dependency update

Effective dependency chain:

```text
P-GUI-03 Complete / Accepted
        ↓
P-GUI-03R Implemented / Verification In Progress
        ↓ Attempt 02 PASS
P-GUI-03R Complete / Accepted
        ↓
P-GUI-04 GUI shell / Workspace / navigation + backend wiring
```

P-GUI-04 presentation-only planning is possible, but canonical backend wiring remains blocked until the P-GUI-03R regression gate passes.

This document is a Phase P task amendment and supersedes the direct `P-GUI-03 -> P-GUI-04` execution assumption in the original Phase P task list.
