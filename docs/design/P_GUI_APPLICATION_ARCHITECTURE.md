# P-GUI Application Architecture

Updated: 2026-10-31

- Status: **Implemented / Complete / Accepted**
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Original design task: `P-GUI-02`
- Final acceptance: `docs/evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`
- Decision: `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- Requirement: `docs/requirements/GUI_REQUIREMENTS.md`

## 1. Scope

This document records the implemented PySide6 desktop architecture accepted by Phase P. It is no longer a future-only design.

## 2. Layering

```text
PySide6 Presentation
QMainWindow / Views / Dialogs / Qt Models
        |
        | operation request
        v
BackendCoordinator / QObject worker on dedicated QThread
        |
        | shared operation boundary
        v
OperatorSession / Application services
        |
        v
Repository / Retrieval / Exchange / Filesystem
SQLite / Embedding / Qdrant / Package/Result files
```

No canonical arrow goes from a GUI View directly to SQLite, direct Repository mutation or a CLI subprocess wrapper.

## 3. Shared CLI / GUI contract

The GUI is an operator presentation over the same Application/operator operation inventory used by the CLI.

Final accepted inventory:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = {mcp.serve}
```

The 66 shared operations are GUI-reachable through domain/System surfaces. `mcp.serve` remains an externally launched stdio transport surface; the GUI exposes configuration/lifecycle information without pretending to own a detached daemon.

## 4. Backend execution

Long-running/canonical operations execute off the Qt UI thread through the accepted worker/coordinator boundary. Repository lifetime is operation/session controlled rather than shared as an unsafe cross-thread SQLite connection.

Initial concurrency policy remains serialized per Workspace unless a later accepted contract changes it.

GUI presentation state such as navigation position, window geometry, recent Workspace paths and Operation Center history is noncanonical.

## 5. Domain surfaces

The accepted Phase P GUI includes operator surfaces for:

```text
Workspace / Object / Source / Evidence
Package / Result
Registry
Search / Similarity
System / Maintenance
Runtime Dashboard
MCP external-launch/configuration guidance
```

Package/Result operations preserve the same Human decision boundaries and review-required semantics as the CLI.

## 6. Runtime health

`System > Overview` consumes the shared `system.status.runtime_health` projection rather than inventing a GUI-only health model.

The accepted runtime-health schema is `sgokb.runtime-health/1.0` for SQLite, Embedding, Qdrant, Search generation and derived state.

Qdrant lifecycle remains:

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

The GUI provides no Qdrant lifecycle control.

## 7. Failure and usability behavior

P-GUI-10 accepted:

- keyboard navigation and standard shortcuts;
- presentation-state restoration across restart;
- scaled-DPI behavior;
- backend failure followed by successful operation on the same session;
- absence of hidden GUI-only canonical writes;
- representative direct-vs-GUI backend state equivalence;
- complete GUI regression, explicit CLI/MCP regression and full repository regression.

P-RUNTIME-05/06 additionally accepted Runtime Dashboard degradation, Qdrant failure -> Semantic Search `BLOCKED`, and return to the normal `DEGRADED` reference-Workspace baseline after recovery.

## 8. Packaging / license boundary

PySide6/Qt Widgets remains the accepted framework. The accepted packaging direction is a standalone directory using dynamic Qt shared libraries, not a one-file/static-Qt baseline.

P-CLOSE-01 includes the GUI source/dependency in the `2.0.0` repository release but does not certify/publish a standalone GUI binary artifact. Public binary redistribution requires the project-license and artifact-specific Qt/PySide6 license gate recorded in `P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`.

## 9. Authority

Current authority is the combination of:

- `docs/requirements/GUI_REQUIREMENTS.md`;
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md` and accepted amendments;
- `docs/evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`;
- accepted P-GUI-05..09 evaluation documents;
- current `src/sgokb/gui/` implementation;
- this integrated architecture document.
