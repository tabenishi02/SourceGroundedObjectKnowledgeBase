# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)

## Accepted modernization direction

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

### GUI

- PySide6 / Qt for Pythonを採用する。
- public `sgokb` CLIと意味的に互換なDesktop GUIを追加する。
- GUIはCLI subprocess wrapperを主実装にせず、Application / Service層をCLIと共有する。
- CLIはPhase P後もfirst-class interfaceとして維持する。
- OSS配布時のPySide6 / Qt license complianceをRelease gateへ含める。

### RAW Grounding

- Evidence retrieval / selectionは維持する。
- External AIへ送るsemantic materialは、Evidence本文再構成物ではなくEvidence provenanceから遡ったRaw Artifactへ変更する。
- Package / Result / Validation / Review / Import / Provenance contractをRaw-grounded modelへ再設計する。
- Package ExportのExternal Egress safety boundaryは維持する。

### Runtime

- Windowsログイン後にQdrantを自動利用可能にする。
- QdrantはGUI processの子process / lifecycle-owned serviceとせず、CLI / GUI / MCPから共有可能な独立runtimeとして扱う。
- Docker / Compose + pinned Qdrant + named volume + localhost binding + restart policyを初期baseline候補とする。
- GUIにはRuntime Dashboardを追加する。

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01 | **Complete / Accepted** | GUI requirements / compatibility contract |
| GUI | P-GUI-02 | **Next / Not Started** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | Not Started | Application boundary audit / refactor plan |
| GUI | P-GUI-04 | Not Started | GUI shell / Workspace / navigation |
| GUI | P-GUI-05 | Not Started | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | Not Started | Search / Similarity / Registry / Version GUI |
| GUI | P-GUI-07 | Not Started | Progress / error / safety / audit UX |
| GUI | P-GUI-08 | Blocked by P-RAW | Package / Result GUI |
| GUI | P-GUI-09 | Not Started | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01..06 | Not Started | Raw-grounded exchange redesign / implementation / acceptance |
| Runtime | P-RUNTIME-01..06 | Not Started | Windows Qdrant auto-start / health / GUI integration |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## P-GUI-01 completion

P-GUI-01でCLI互換GUIの要件とcompatibility / safety boundaryを正式化した。

成果物:

- `docs/requirements/GUI_REQUIREMENTS.md`
  - GUI functional / safety / error / progress / identity requirements
  - Workspace / navigation / Object / Source / Evidence / Association / Registry / Package / Result / Version / Search / Similarity / Render / MCP / System requirements
  - GUI-only convenienceとcanonical operationの境界
- `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
  - semantic parity definition
  - shared Application / Service boundary
  - READ / DERIVED / WRITE / EXTERNAL / MAINTENANCE safety contract
  - hidden canonical write prohibition
  - existing Relation / Proposal / Result / Restore / runtime safety preservation
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
  - current public `sgokb` 67 operationsをGUI capabilityへ全件mapping
  - assigned = 67 / 67
  - unassigned = 0
  - R2 generation operator 6 actionsをAdvanced / Search Generation Maintenanceへ分離

P-GUI-01で固定したcompatibility定義:

```text
GUI compatible
  = same use case
  + same target identity
  + same canonical effect
  + same validation / precondition
  + same safety boundary
  + same degradation / warning semantics
  + equivalent failure meaning
```

GUIはCLI parser / stdout JSON / subprocessをprimary business-logic boundaryとして使用しない。P-GUI-03でtransport-neutral Application boundaryを監査する。

Package / Result capabilityはpublic parity対象として割当済みだが、最終GUI semanticsはP-RAW contract確定後のP-GUI-08で実装する。

## Sequencing note

GUIが最優先である。ただしPackage / Result UIはP-RAWのPackage / Result schemaを直接表示するため、次の順を採用する。

```text
GUI foundation / core screens
        ↓
RAW Grounding
        ↓
Package / Result GUI
        ↓
Runtime integration
        ↓
Full Phase P acceptance
```

P-RUNTIME設計は独立して並行可能だが、project priority上はGUI / RAW Groundingより後に置く。

## Current authority boundary

Phase Pは実装途中であるため、現時点の実システム仕様は引き続き以下を正本とする。

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- release `v1.1.0`

P-GUI-01で追加したGUI documentsはPhase P GUIのaccepted future contractであり、未実装GUIをcurrent runtime capabilityとして扱わない。

## Next

次に実施するTaskは次である。

```text
P-GUI-02 [P0] PySide6 application architecture / packaging / license design
```
