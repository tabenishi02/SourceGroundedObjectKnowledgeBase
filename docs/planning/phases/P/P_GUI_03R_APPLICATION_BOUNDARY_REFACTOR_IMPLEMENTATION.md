# P-GUI-03R — Transport-neutral Application Boundary Refactor Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **Complete / Accepted**
- Priority: **P0**
- Introduced by: `P-GUI-03`
- Design authority: `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`
- Decision authority: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`
- Implementation result: `docs/evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`
- Final R9 acceptance: `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

## 1. Reason for insertion

P-GUI-03 audited all 67 public `sgokb` operations and found:

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
```

Proceeding directly to P-GUI-04 canonical backend wiring would have required the GUI to duplicate CLI orchestration or depend on CLI modules, violating P-GUI-01/P-GUI-02 contracts.

P-GUI-03R therefore inserted and implemented the shared transport-neutral Application/operator boundary before GUI backend integration.

## 2. Completed scope

Implemented and accepted:

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
- regression/equivalence test assets and dynamic acceptance

## 3. Execution slices

```text
R1 Shared operation/error contracts       Complete
R2 Shared runtime factory                 Complete
R3 Source/Object/Registry boundaries      Complete
R4 Evidence/Version/Render boundaries     Complete
R5 Package/Result boundaries              Complete
R6 System/Recovery boundary               Complete
R7 Operator dispatcher/session            Complete
R8 CLI cutover                            Complete
R9 Regression / semantic-equivalence      Complete / PASS
```

## 4. Accepted boundary

The public inventory is explicit in `src/sgokb/application_operator.py`:

```text
PUBLIC_OPERATION_IDS    = 67
TRANSPORT_OPERATION_IDS = 1  (mcp.serve)
SHARED_OPERATION_IDS    = 66
```

The synchronous path is:

```text
CLI parser / GUI worker
        ↓
OperationRequest
        ↓
OperatorSession
        ↓
Domain Application facades
        ↓
Repository / Retrieval / Exchange
```

`mcp.serve` remains a transport-specific stdio lifecycle operation and is intentionally excluded from synchronous `OperatorSession` dispatch.

## 5. Hard constraints preserved

- no intended public CLI semantic change
- no GUI widget implementation in this task
- no P-RAW schema changes
- no canonical schema redesign
- no cloud semantic fallback
- no presentation-layer canonical SQL path
- `mcp serve` remains transport-specific
- Registry Proposal accept/reject/apply remains separate
- Package/Result audit lifecycle remains explicit
- Restore acknowledgement/safety remains delegated to the existing recovery contract

## 6. Final R9 acceptance evidence

After iterative remediation and reverification, the accepted final state is:

```text
operator-boundary + M01 CLI = 18 / 18 PASS
M03 standard workflow       = 2 / 2 PASS
Phase N closure audit       = 11 / 11 PASS
full pytest                 = 795 / 795 PASS
ruff                        = All checks passed!
```

The full pytest run produced only two local-Qdrant capability warnings and no failures/errors.

Historical verification records:

- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_02.md`
- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_03.md`
- `docs/evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

Attempt 04 is the final acceptance authority.

## 7. Completion gate

| Gate | State |
|---|---|
| 67 public operation IDs inventoried | Satisfied |
| 66 synchronous operations callable without CLI presentation import | Satisfied |
| `mcp serve` transport lifecycle separated | Satisfied |
| CLI moved to shared operator boundary | Satisfied |
| New operator-boundary regression test exists | Satisfied |
| Operator boundary + M01 CLI regression | **PASS — 18/18** |
| M03 public CLI vertical slice | **PASS — 2/2** |
| Phase N closure audit fixture | **PASS — 11/11** |
| Full pytest regression | **PASS — 795/795** |
| Full Ruff regression | **PASS — All checks passed!** |
| Package/Result lifecycle preserved | Satisfied |
| Restore safety preserved | Satisfied |

P-GUI-03R is therefore **Complete / Accepted**.

## 8. Dependency update

Effective dependency chain:

```text
P-GUI-03 Complete / Accepted
        ↓
P-GUI-03R Complete / Accepted
        ↓
P-GUI-04 GUI shell / Workspace / navigation
```

P-GUI-04 canonical backend wiring is now unblocked.

This document remains the Phase P task amendment that superseded the original direct `P-GUI-03 -> P-GUI-04` execution assumption.
