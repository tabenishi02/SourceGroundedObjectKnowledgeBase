# P-GUI-10 — GUI parity / usability / regression acceptance

Date: 2026-10-30
Task: `P-GUI-10 [P0] GUI parity / usability / regression acceptance`
Disposition: **Complete / Accepted**

## 1. Acceptance scope

P-GUI-10 is the final GUI-wide acceptance gate for the P-GUI workstream. It re-evaluates the complete public CLI inventory against the accepted GUI implementation from P-GUI-01 through P-GUI-09 and verifies that the desktop interface remains a transport-neutral client of the same Application/operator contracts used by CLI and MCP.

The acceptance authority is the P-GUI-01 capability matrix together with the normative P-GUI-09 MCP amendment:

- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`

The public inventory remains:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = {mcp.serve}
```

All 66 shared operations are GUI-reachable. `mcp.serve` remains the single transport-lifecycle exception and is represented by the accepted external-client-owned stdio configuration/command surface rather than a fake detached daemon lifecycle.

## 2. Capability parity result

Final parity disposition:

```text
public CLI operations              = 67
shared Application operations      = 66 / 66 GUI-reachable
MCP transport operation            = 1 / 1 GUI-reachable by configured stdio command surface
unassigned public operations       = 0
GUI-only hidden canonical writes   = 0 detected
CLI subprocess canonical execution = none
```

The focused gate scans the current GUI view implementation for every shared public operation ID and verifies the live `SystemPage` MCP surface for the transport-only operation.

The GUI-view boundary also rejects direct canonical persistence or shell bypasses by checking for direct SQLite connection, Repository construction, repository SQL execution, subprocess execution, and shell execution from `src/sgokb/gui/views/`.

Canonical work continues through:

```text
GUI page
  -> OperationPage.submit
  -> BackendCoordinator
  -> dedicated backend QThread
  -> OperatorSession / GenerationOperatorSession
  -> shared Application / Repository boundary
```

## 3. Representative canonical-state equivalence

P-GUI-10 compares representative GUI-backend results with direct shared `OperatorSession` execution against the same Workspace.

Accepted representatives:

```text
object.list
registry.class.list
system.integrity
```

For each representative read, operation identity, outcome state, and returned data are identical between the GUI backend lane and direct Application/operator execution.

Earlier P-GUI acceptance suites continue to cover canonical write equivalence for Object, Source, Association, Package/Result, Registry, and maintenance operations; all of those tests are re-executed in the final GUI regression gate.

## 4. Usability / safety scenarios

P-GUI-10 directly verifies:

- keyboard navigation through the primary navigation list;
- standard Workspace and form-edit shortcuts (`Ctrl+O`, `Ctrl+N`, `Ctrl+Z`, `Ctrl+Y`);
- last-page restoration across a GUI restart using presentation-only `QSettings` state;
- a separate Qt process at `QT_SCALE_FACTOR=1.5` for scaled-DPI layout smoke testing;
- backend error normalization followed by a successful subsequent operation, proving that one failed request does not poison the serialized backend lane.

The complete GUI regression also re-executes the accepted P-GUI-07 long-operation/progress, busy-state, warning/degradation, partial-result, confirmation, audit, and noncanonical Undo/Redo safety coverage.

## 5. MCP and CLI regression boundary

The dedicated CLI/MCP gate re-executes representative public CLI and MCP suites including:

- core CLI behavior;
- Source effective-selection CLI;
- Derived maintenance CLI;
- retrieval/MCP boundary;
- MCP read tools and resources;
- MCP write-separation;
- MCP client acceptance.

Result:

```text
CLI + MCP focused regression = 59 / 59 PASS
```

No GUI change introduces MCP canonical write capability or changes the accepted stdio lifecycle ownership model.

## 6. Verification history

### Attempt 1 — historical verification-only FAIL

GitHub Actions run:

```text
run                         = 41065681837 (#1)
verified branch source      = 7a852c2115507d824e5b6290a47232aa1e405261
verified synthetic PR merge = 33a72f5e064ad362f582fe600c22974c38ec4c68
```

Result:

```text
focused P-GUI-10 = 5 PASS / 1 FAIL
```

The failure was in the new acceptance test, not in product behavior. The test incorrectly required the literal substring `"mcp serve"` to occur as one source-code string in `system_page.py`. The existing P-GUI-09 implementation constructs the command dynamically and its accepted behavior was already covered by the live widget test.

Remediation changed only the acceptance assertion: MCP parity is now verified through a live `SystemPage`, including the generated command, external-client-owned stdio lifecycle wording, and `--semantic-runtime` mode. No product code or runtime semantics were relaxed.

### Attempt 2 — final PASS

GitHub Actions run:

```text
run                         = 41066089220 (#2)
runner                      = Microsoft Windows Server 2025
Python                      = 3.10.11
QT_QPA_PLATFORM             = offscreen
verified branch source      = 225c99293e3fb346098e42d66625ddac3b30a501
verified synthetic PR merge = 7ec7dddfd6e5a2f5cb35df0c0f449fd33993fc7a
```

Final results:

```text
focused P-GUI-10                  = 6 / 6 PASS
scaled DPI smoke (1.5x)           = 1 / 1 PASS
complete P-GUI regression         = 50 / 50 PASS
CLI + MCP focused regression      = 59 / 59 PASS
Ruff src/tests                    = PASS
full repository regression        = 854 / 854 PASS
full regression duration          = 789.20 s
warnings                          = 2 known local-Qdrant warnings
```

The two warnings are the existing local-Qdrant limitations already accepted in earlier phases:

- payload indexes are mostly ineffective in local Qdrant except supported text/scoring cases;
- local Qdrant performs exact/brute-force search and normal approximate-search parameters do not apply.

They are not P-GUI-10 regressions.

## 7. Accepted final GUI boundary

```text
GUI framework                 = PySide6 / Qt Widgets
public capability parity      = 67 / 67
shared-operation GUI path     = shared OperatorSession
advanced generation GUI path  = shared GenerationOperatorSession
canonical GUI subprocess path = none
hidden GUI canonical write    = none detected
MCP transport                 = stdio
MCP process owner             = external MCP client / launcher
Qdrant lifecycle owner        = external
GUI runtime observation       = shared system.status.runtime_health
GUI backend concurrency       = serialized per Workspace
GUI worker execution          = dedicated QThread
```

P-GUI-10 does not change released-system defaults or the P-RAW v1/v2 cutover decision. Those release/default decisions remain P-CLOSE-01 scope.

## 8. Authority

P-GUI-10 is governed by:

- `docs/planning/phases/P/PHASE_P_TASKS.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`
- `tests/test_p_gui_10_parity_usability_acceptance.py`
- the accepted P-GUI-01 through P-GUI-09 design/evaluation authorities;
- this acceptance document.

## 9. Final disposition

```text
P-GUI-10        = Complete / Accepted
P-GUI workstream = Complete / Accepted for Phase P
```

The next Phase P task is `P-RUNTIME-04 — Windows login auto-start integration`.