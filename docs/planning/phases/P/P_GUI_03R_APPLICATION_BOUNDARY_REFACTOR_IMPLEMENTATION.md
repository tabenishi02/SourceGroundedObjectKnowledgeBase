# P-GUI-03R — Transport-neutral Application Boundary Refactor Implementation

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **Next / Not Started**
- Priority: **P0**
- Introduced by: `P-GUI-03`
- Design authority: `docs/design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`
- Decision authority: `docs/decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`

## 1. Reason for insertion

P-GUI-03 audited all 67 public `sgokb` operations and found:

```text
A READY                    25
B ORCHESTRATION EXTRACTION 26
C APPLICATION GAP          15
D TRANSPORT-SPECIFIC        1
```

P-GUI-03 itself is an audit/refactor-plan task. It intentionally does not change implementation code.

Proceeding directly to P-GUI-04 canonical operation wiring would require the GUI to duplicate CLI orchestration or depend on CLI modules, violating P-GUI-01/P-GUI-02 contracts.

Therefore this remediation implementation task is inserted before P-GUI-04 backend integration.

## 2. Scope

Implement the accepted transport-neutral boundary:

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
- regression/equivalence tests

## 3. Execution slices

```text
R1 Shared operation/error contracts
R2 Shared runtime factory
R3 Source/Object/Registry boundaries
R4 Evidence/Version/Render boundaries
R5 Package/Result boundaries
R6 System/Recovery boundary
R7 Operator dispatcher/session
R8 CLI cutover
R9 Regression / semantic-equivalence acceptance
```

## 4. Hard constraints

- no intended public CLI semantic change
- no GUI implementation in this task
- no P-RAW schema changes
- no canonical schema redesign unless an unforeseen blocker is documented and separately approved
- no cloud semantic fallback
- no direct GUI/CLI presentation SQL after refactor for audited operation semantics
- `mcp serve` remains transport-specific

## 5. Completion gate

P-GUI-03R is Complete only when:

- 67 public operation IDs are inventoried in the shared boundary;
- 66 synchronous public operations are executable without importing CLI presentation code;
- `mcp serve` remains explicitly handled as transport lifecycle;
- existing CLI tests pass;
- `sgokb.cli/1.0`, exit codes, warnings, partial behavior and canonical/audit effects remain compatible;
- package/result lifecycle and restore safety boundaries remain unchanged;
- P-GUI-04 can connect its BackendWorker to OperatorSession.

## 6. Dependency update

Effective dependency chain:

```text
P-GUI-03 Complete / Accepted
        ↓
P-GUI-03R implementation
        ↓
P-GUI-04 GUI shell / Workspace / navigation + backend wiring
```

This document is a Phase P task amendment and supersedes the direct `P-GUI-03 -> P-GUI-04` execution assumption in the original Phase P task list.
