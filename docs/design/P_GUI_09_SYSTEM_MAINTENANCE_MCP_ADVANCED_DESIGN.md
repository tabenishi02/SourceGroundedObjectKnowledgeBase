# P-GUI-09 — System / Maintenance / MCP / Advanced GUI Design

Date: 2026-10-30
Task: `P-GUI-09 [P1] System / Maintenance / MCP / Advanced GUI`
Status: **Implementation candidate / acceptance pending**

## 1. Purpose

P-GUI-09 replaces the Phase P System placeholder with the operator-facing System / Maintenance surface while preserving the already accepted CLI/GUI shared Application boundary.

The GUI is not a CLI subprocess wrapper. Public System operations continue to execute through `OperatorSession`, while the separate R2 Search Generation operator receives its own transport-neutral session shared by its historical CLI entrypoint and the GUI.

## 2. Surface inventory

The System page contains seven presentation tabs:

```text
Overview
Derived
Vector Index
Backup
Restore
MCP
Advanced Generation
```

The page covers all fourteen public `system.*` operations:

```text
system.status
system.integrity
system.derived.status
system.derived.sync
system.index.status
system.index.rebuild
system.backup.status
system.backup.create
system.backup.composite.create
system.backup.composite.verify
system.restore.plan
system.restore.apply
system.restore.composite.plan
system.restore.composite.apply
```

It also exposes the six non-public Advanced Search Generation actions required by GUI-R-003:

```text
generation.status
generation.bootstrap
generation.build
generation.cutover
generation.rollback
generation.recover
```

The generation actions remain outside `PUBLIC_OPERATION_IDS`; therefore the accepted public `sgokb` parity count remains 67.

## 3. Shared execution boundary

### 3.1 Public System operations

Public System operations use the established path:

```text
SystemPage
  -> GuiOperationRequest
  -> BackendCoordinator
  -> BackendWorker / dedicated QThread
  -> OperatorSession
  -> SystemOperatorApplication / RecoveryOperatorApplication
```

No System button invokes `sgokb` as a child process and no GUI view performs direct SQL.

### 3.2 Advanced generation operations

P-GUI-09 introduces `GenerationOperatorSession` as the shared transport-neutral dispatcher for the separate Search Generation maintenance surface:

```text
GUI ------------------------------------┐
                                       v
                             GenerationOperatorSession
                                       |
python -m sgokb.cli.generation --------┘
                                       |
                             KnowledgeSearchGenerationApplication
```

The historical generation CLI parser and JSON presentation remain separate presentation concerns. Lifecycle semantics now live behind one session boundary rather than being duplicated between CLI and GUI.

`generation.status` is runtime-independent. Bootstrap/build/cutover/rollback/recover use the local semantic runtime and have no cloud fallback.

## 4. Runtime status

Overview consumes the P-RUNTIME-03 additive `system.status.runtime_health` projection. The GUI displays the component states for:

```text
sqlite
embedding
qdrant
generation
derived
```

This is observation only. P-GUI-09 does not add Docker/Qdrant start, stop, or restart capability. Qdrant lifecycle ownership remains external as fixed by P-RUNTIME-01..03.

## 5. Restore safety contract

Restore safety is stronger than a generic MAINTENANCE confirmation. Both SQLite and composite restore enforce this presentation sequence:

```text
enter targets
  -> Plan
  -> successful verified plan displayed
  -> exact input tuple retained as presentation state
  -> operator reviews target/existing state
  -> overwrite acknowledgement when required
  -> Apply
```

Rules:

1. Apply is disabled before a successful Plan.
2. Editing any plan-defining input invalidates the retained Plan and disables Apply.
3. SQLite Restore reads `requires_overwrite_acknowledgement` from the Application plan.
4. Composite Restore derives acknowledgement need from the verified plan's `existing` targets.
5. Apply still passes the explicit backend acknowledgement flag; the GUI does not replace backend enforcement.
6. The normal P-GUI-07 MAINTENANCE confirmation remains an additional final submission gate in interactive mode.
7. After restore Apply, the page instructs the operator to reopen the restored Workspace before further canonical operations.

The GUI therefore does not turn Plan + Apply into a hidden composite operation.

## 6. Backup and derived maintenance

SQLite backup, composite backup, derived sync, and index rebuild use the same backend QThread as other GUI operations. The Qt event loop remains responsive and no false cancellation control is added; the accepted operations remain non-cancellable unless their backend contract later changes.

Composite backup creation requires an explicit incoming Result root. Composite verification remains path-only and read/verification oriented.

## 7. MCP lifecycle resolution

### 7.1 Current transport fact

The current public MCP command is:

```text
sgokb --db <workspace> mcp serve [--semantic-runtime]
```

and the current transport is stdio. The MCP client's child-process stdin/stdout are therefore the connection itself.

### 7.2 P-GUI-09 decision

For the current stdio transport, MCP lifecycle is **external MCP-client-owned**, not detached GUI-owned.

P-GUI-09 provides:

- the active Workspace binding;
- semantic-runtime configuration;
- the exact client launch command;
- a copy action for that command;
- explicit lifecycle/state explanation;
- read-only contract explanation.

P-GUI-09 deliberately does **not** spawn a detached `mcp serve` child and label it a running server. Such a process would have no external client attached to the stdio transport and would not create a connectable daemon endpoint.

Consequences:

```text
MCP lifecycle owner     = external MCP client / launcher
GUI start detached MCP  = unsupported for current stdio transport
GUI stop external MCP   = unsupported
GUI close -> MCP stop   = no implied relationship
MCP canonical writes    = forbidden / unchanged
```

If SGOKB later adopts a socket/HTTP MCP transport or an explicit supervisor protocol, start/stop lifecycle ownership may be revisited in a separate contract. P-GUI-09 does not invent such a transport.

This resolves GUI-R-100/101 without violating GUI-R-141 or GUI-R-151.

## 8. Advanced Search Generation safety

Advanced Generation remains isolated from the normal Search page. Status is READ. Bootstrap/build/cutover/rollback/recover are presented as MAINTENANCE and use the common confirmation gate.

Cutover and rollback display:

- explicit generation ID;
- operator reason;
- smoke-verification selection;
- Equivalent CLI command.

Rollback with an empty generation field resolves to the frozen legacy generation identity exactly as the historical CLI does.

## 9. Equivalent CLI / audit behavior

Every submitted public System operation continues to appear in Operation Center with its safety class and equivalent public CLI command.

Advanced generation operations render the distinct historical command family:

```text
python -m sgokb.cli.generation --db <workspace> <action> ...
```

This string is presentation only. Backend execution remains in-process through the shared Application session.

MCP serve is not submitted to the synchronous backend because it is a transport lifecycle operation. Its exact public CLI command is displayed in the MCP tab instead.

## 10. Acceptance gates

P-GUI-09 is accepted only after:

- focused System / Maintenance / MCP / Advanced tests pass;
- all fourteen public System capabilities are reachable from the System page;
- all six Advanced Generation actions are reachable from the isolated Advanced tab;
- System status exposes the shared P-RUNTIME-03 runtime-health projection;
- Restore plan/input/acknowledgement gates pass;
- MCP stdio ownership/configuration presentation is verified;
- generation CLI and GUI are proven to share `GenerationOperatorSession`;
- existing GUI regression passes;
- Ruff passes;
- full repository regression passes on the established Windows acceptance environment.
