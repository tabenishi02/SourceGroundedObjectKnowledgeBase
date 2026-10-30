# P-GUI-09 — System / Maintenance / MCP / Advanced GUI Acceptance

Date: 2026-10-30
Task: `P-GUI-09 [P1] System / Maintenance / MCP / Advanced GUI`
Disposition: **Complete / Accepted**

## 1. Accepted scope

P-GUI-09 replaces the System placeholder with a real operator-facing System / Maintenance surface while preserving the accepted transport-neutral CLI/GUI Application boundary.

Accepted coverage:

```text
System / Overview
System / Derived
System / Vector Index
System / Backup
System / Restore
System / MCP
System / Advanced Generation
```

All fourteen public `system.*` operations are reachable through the existing `OperatorSession` path. The separate six-action R2 Search Generation operator is reachable from an isolated Advanced surface through the new transport-neutral `GenerationOperatorSession` shared by CLI and GUI.

No GUI control shells out to the public CLI to perform canonical work.

## 2. Public System capability coverage

The accepted GUI surface covers:

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

`system.status` consumes the accepted P-RUNTIME-03 `data.runtime_health` projection and displays SQLite, Embedding, Qdrant, generation, and derived state without moving Qdrant lifecycle ownership into the GUI.

## 3. Restore safety acceptance

Both SQLite and composite restore preserve the required destructive-maintenance boundary:

```text
enter targets
  -> Plan
  -> verified preview
  -> retain exact plan-defining inputs
  -> explicit overwrite acknowledgement when required
  -> Apply
```

Accepted safety properties:

- Apply is disabled before a successful Plan.
- Editing any plan-defining input invalidates the retained Plan.
- SQLite restore uses the Application plan's overwrite-acknowledgement requirement.
- Composite restore derives the acknowledgement requirement from the verified plan's existing targets.
- The explicit backend acknowledgement flag remains authoritative; the GUI does not bypass backend enforcement.
- The common P-GUI-07 MAINTENANCE confirmation remains an additional submission gate.
- Plan and Apply remain distinct operations; no hidden composite mutation is introduced.

## 4. MCP lifecycle disposition

Current MCP transport is stdio. The useful process is therefore owned by the external MCP client/launcher that starts the child process and connects to its stdin/stdout.

Accepted P-GUI-09 lifecycle contract:

```text
transport                     = stdio
server process owner          = external MCP client / launcher
GUI observes/configures       = yes
GUI displays serve command    = yes
GUI detached start            = no
GUI stop external client      = no
GUI close stops MCP           = no implied relationship
semantic runtime option       = configurable
canonical MCP write surface   = none
```

The GUI provides Workspace binding, semantic-runtime configuration, lifecycle explanation, the exact `sgokb --db <workspace> mcp serve [--semantic-runtime]` launch command, and copy-to-clipboard support. It does not pretend that a detached stdio child is a connectable daemon.

This disposition supersedes only the provisional P-GUI-01 wording for MCP lifecycle. Public parity remains 67 operations and MCP remains read-only.

## 5. Advanced Search Generation acceptance

The Advanced surface covers the six non-public generation actions:

```text
generation.status
generation.bootstrap
generation.build
generation.cutover
generation.rollback
generation.recover
```

These actions remain outside `PUBLIC_OPERATION_IDS` and outside the normal Search screen. CLI and GUI share `GenerationOperatorSession`; lifecycle semantics are no longer duplicated in the historical generation CLI adapter.

Cutover and rollback preserve explicit generation identity, operator reason, smoke-verification choice, common MAINTENANCE confirmation, and equivalent historical CLI presentation.

## 6. Verification history

Early acceptance attempts exposed two verification-only issues rather than product-contract failures:

1. Windows PowerShell did not expand the pytest glob used by the temporary CI workflow. The workflow was corrected to enumerate GUI test files explicitly.
2. The pre-P-RUNTIME-03 P-GUI-04 helper used a 5-second Qt signal wait. `system.status` now includes a bounded live Qdrant health probe, and hosted-runner variance could exceed that historical helper budget. The helper was increased to 10 seconds without changing product timeout or runtime semantics.

Focused P-GUI-09 behavior passed throughout the final remediation sequence.

## 7. Final Windows acceptance

Final GitHub Actions run:

```text
run                         = 41049707411 (#8)
runner                      = Microsoft Windows Server 2025
Python                      = 3.10.11
QT_QPA_PLATFORM             = offscreen
verified branch source      = e0456b12dfdfc8897ed21358dbc4c04ffef6c43d
verified synthetic PR merge = bfcd5caf63c5e072a1e844c85e47bc2411d57c19
```

Results:

```text
focused P-GUI-09            = 6 / 6 PASS
P-GUI regression            = 44 / 44 PASS
Ruff src/tests              = PASS
full repository regression  = 848 / 848 PASS
warnings                    = 2 known local-Qdrant warnings
```

The two warnings are the already-known local-Qdrant warnings:

- payload indexes are mostly ineffective in local Qdrant;
- local mode performs exact/brute-force search and ignores normal approximate-search parameters.

They do not affect P-GUI-09 acceptance.

## 8. Authority

P-GUI-09 is governed by:

- `docs/design/P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_DESIGN.md`
- `docs/decisions/P_GUI_09_MCP_STDIO_LIFECYCLE_DECISION.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`
- `src/sgokb/application_generation_operator.py`
- `src/sgokb/gui/views/system_page.py`
- `tests/test_p_gui_09_system_maintenance.py`
- this acceptance document.

The earlier design-document header `Implementation candidate / acceptance pending` records its pre-acceptance drafting state; this acceptance document is the final disposition authority.

## 9. Final disposition

```text
P-GUI-09 = Complete / Accepted
```

P-GUI-10 remains responsible for final GUI-wide CLI parity, usability, keyboard/DPI/restart scenarios, representative canonical-state equivalence, and overall GUI regression closure.
