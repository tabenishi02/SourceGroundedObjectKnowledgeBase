# P-GUI-10 — GUI parity / usability / regression acceptance

Date: 2026-10-30
Task: `P-GUI-10 [P0] GUI parity / usability / regression acceptance`
Disposition: **Complete / Accepted**

## 1. Acceptance scope

P-GUI-10 closes the Phase P GUI workstream by verifying that the accepted PySide6 desktop client remains a CLI-compatible operator interface rather than an independent canonical execution path.

Acceptance covers:

- the complete 67-operation public CLI inventory;
- representative canonical-state equivalence through the shared Application/operator boundary;
- absence of GUI-only canonical persistence or shell write bypasses;
- keyboard navigation and standard desktop shortcuts;
- presentation-state restoration after GUI restart;
- scaled-DPI layout behavior;
- normalized backend failure recovery;
- complete existing GUI regression;
- explicit CLI and MCP regression;
- full repository regression.

The final public capability authority is the P-GUI-01 capability matrix together with the P-GUI-09 MCP lifecycle amendment.

## 2. Final public capability inventory

The public operator inventory remains:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = {mcp.serve}
```

Final parity disposition:

```text
66 shared public operations = GUI-reachable through domain/System surfaces
mcp.serve                   = GUI-observable/configurable stdio transport surface
unassigned public operation = 0
```

For the 66 shared operations, the final gate verifies a GUI reachability point for every accepted public operation ID. These operations continue through the accepted `OperationPage.submit -> BackendCoordinator -> OperatorSession` boundary; GUI views do not own a parallel canonical command implementation.

MCP row 53 is evaluated under `GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`. The live `SystemPage` exposes the exact external-client-managed stdio serve command, semantic-runtime option, and lifecycle explanation without pretending that the GUI owns a detached MCP daemon.

## 3. Canonical-state equivalence and hidden-write audit

Representative direct-vs-GUI-backend read equivalence was verified for:

```text
object.list
registry.class.list
system.integrity
```

The test prepares canonical state through `OperatorSession`, executes the same reads through `BackendCoordinator`, and requires identical operation ID, outcome state, and returned data.

The GUI view tree is also gated against direct canonical persistence/shell bypasses. The final audit rejects view-layer use of direct SQLite connections, direct `Repository` construction, direct repository SQL execution, subprocess execution, and `os.system` shell execution.

Result:

```text
representative shared-state equivalence = PASS
GUI-only hidden canonical write path     = not detected
```

This is additive to the accepted P-GUI-05..09 functional tests that already exercise mutation, Package/Result, Registry, System/Maintenance, and generation behavior through the shared operator boundary.

## 4. Usability / desktop behavior acceptance

The final focused gate verifies:

- keyboard navigation across the main navigation list;
- standard shortcuts `Ctrl+O`, `Ctrl+N`, `Ctrl+Z`, and `Ctrl+Y`;
- last-page presentation state persistence and restoration across a complete MainWindow/backend restart;
- a separate Qt process with `QT_SCALE_FACTOR=1.5`;
- usable nonzero page/layout geometry under scaled DPI;
- a normalized failed operation followed by a successful operation on the same backend session;
- no poisoned busy/session state after the failure.

Result:

```text
keyboard navigation / shortcuts = PASS
restart presentation restore     = PASS
1.5x DPI smoke                   = PASS
backend error recovery           = PASS
```

The accepted GUI does not claim operation cancellation where the shared operation contract does not provide it. Existing P-GUI-07 busy/progress/close-safety behavior remains authoritative for long-running operations.

## 5. Verification history

### Attempt 1 — acceptance-test defect

GitHub Actions run:

```text
run = 41065681837 (#1)
```

The first run stopped in the focused P-GUI-10 gate with:

```text
5 passed / 1 failed
```

The failure was not a product parity failure. The test incorrectly required the literal contiguous source string `"mcp serve"` to appear in `system_page.py`, while the accepted implementation builds the command dynamically.

The test was corrected to instantiate the real `SystemPage` and verify the generated command and accepted external-client-owned stdio lifecycle text. No product implementation was relaxed or changed to satisfy this failure.

### Attempt 2 — final PASS

Final GitHub Actions run:

```text
run                         = 41066089220 (#2)
runner                      = Microsoft Windows Server 2025
Python                      = 3.10.11
QT_QPA_PLATFORM             = offscreen
verified branch source      = 225c99293e3fb346098e42d66625ddac3b30a501
verified synthetic PR merge = 7ec7dddfd6e5a2f5cb35df0c0f449fd33993fc7a
```

Results:

```text
focused P-GUI-10                 = 6 / 6 PASS
scaled DPI smoke                 = 1 / 1 PASS (5 deselected)
complete P-GUI regression        = 50 / 50 PASS
explicit CLI + MCP regression    = 59 / 59 PASS
Ruff src/tests                   = PASS
full repository regression       = 854 / 854 PASS
warnings                         = 2 known local-Qdrant warnings
```

The full repository run completed in 789.20 seconds.

The two warnings are the existing local-Qdrant warnings:

- payload indexes are mostly ineffective in local Qdrant except supported text/scoring cases;
- local mode uses exact/brute-force search and ignores ordinary approximate-search parameters except `idf`.

They are unchanged from prior Phase P acceptance runs and do not affect P-GUI-10 disposition.

## 6. Accepted GUI compatibility disposition

The final accepted desktop boundary is:

```text
GUI canonical execution        = shared Application/operator layer
GUI CLI subprocess wrapper     = no
GUI direct Repository writes   = no
GUI direct SQLite writes       = no
GUI shell-based canonical work = no
public CLI capability coverage = 67 / 67
MCP transport ownership        = external MCP client / launcher
Qdrant lifecycle ownership     = external
```

The GUI may maintain presentation-only state such as navigation position, recent Workspace paths, window geometry, and Operation Center history. Those remain explicitly noncanonical.

## 7. Authority

P-GUI-10 is governed by:

- `docs/planning/phases/P/PHASE_P_TASKS.md`;
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`;
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`;
- the accepted P-GUI-05..09 evaluation documents;
- `src/sgokb/gui/views/operation_page.py`;
- `src/sgokb/gui/worker.py`;
- `tests/test_p_gui_10_parity_usability_acceptance.py`;
- this acceptance document.

## 8. Final disposition

```text
P-GUI-10       = Complete / Accepted
P-GUI-01..10   = Complete / Accepted
GUI workstream = Complete / Accepted for Phase P
```

The next Phase P task is:

```text
P-RUNTIME-04 — Windows login auto-start integration
```

P-RUNTIME-05, P-RUNTIME-06, and P-CLOSE-01 remain subsequent work.
