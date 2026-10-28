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
- primary UI technologyはQt Widgetsとする。
- public `sgokb` CLIと意味的に互換なDesktop GUIを追加する。
- GUIはCLI subprocess wrapperを主実装にせず、Application / Service層をCLIと共有する。
- CLIはPhase P後もfirst-class interfaceとして維持する。
- GUI main threadではblocking backend operationを行わない。
- backendは専用QThread上のQObject workerで実行する。
- Repositoryはoperationごとにworker thread内で生成・破棄する。
- Windows distribution baselineは`pyside6-deploy` / Nuitkaのstandalone directoryとする。
- OSS配布時のPySide6 / Qt LGPLv3等のlicense complianceをRelease gateへ含める。

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
| GUI | P-GUI-02 | **Complete / Accepted** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | **Next / Not Started** | Application boundary audit / refactor plan |
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

主要成果物:

- `docs/requirements/GUI_REQUIREMENTS.md`
- `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`

current public `sgokb` 67 operationsをGUI capabilityへ全件mappingし、assigned 67 / 67、unassigned 0を確認した。

GUI compatibility:

```text
same use case
+ same target identity
+ same canonical effect
+ same validation / precondition
+ same safety boundary
+ same degradation / warning semantics
+ equivalent failure meaning
```

## P-GUI-02 completion

P-GUI-02でDesktop GUIの技術基盤を正式化した。

成果物:

- `docs/evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`
  - Qt Widgets / Qt Quick比較
  - Repository / SQLite thread-affinity review
  - CLI subprocess / direct SQL / shared Application architecture比較
  - Windows deployment方式比較
  - PySide6 / Qt LGPL distribution review
- `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
  - PySide6 + Qt Widgets正式採用
  - QObject worker on dedicated QThread
  - per-operation Repository ownership
  - serialized backend lane
  - `pyside6-deploy` / Nuitka standalone distribution
  - dynamic Qt libraries / no baseline onefile
  - CLI remains Qt-free optional installation
- `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`
  - target module layout
  - main-thread / worker-thread ownership
  - BackendSession / operation lifecycle
  - settings / shutdown / cancellation boundaries
  - P-GUI-03 handoff
- `docs/operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`
  - Windows build / smoke / thread safety gates
  - LGPL / notices / source availability gates
  - build manifest / dependency inventory requirements

Accepted technical baseline:

```text
Framework            = PySide6
UI                    = Qt Widgets
GUI execution        = Qt main thread
Backend              = QObject worker on dedicated QThread
DB                    = Repository per operation in worker thread
Runtime cache         = expensive noncanonical providers may be lazy-cached in BackendSession
Operation concurrency = serialized per Workspace initially
Packaging             = pyside6-deploy / Nuitka
Mode                  = standalone directory / portable ZIP
Onefile               = not baseline
Static Qt linking     = prohibited
```

Current repository has no root `LICENSE` file. This does not block private Phase P development, but public OSS publication is blocked until a project-level license Decision is made and the root license is added.

Planned Python package surface is:

```text
base install        -> CLI, no PySide6 required
.[gui]              -> PySide6 GUI dependency
sgokb               -> CLI
sgokb-gui           -> GUI launcher
```

Exact implementation of dependency/entrypoint is deferred until the GUI implementation task; P-GUI-02 is design-only.

## Sequencing note

GUIが最優先である。ただしPackage / Result UIはP-RAWのPackage / Result schemaを直接表示するため、次の順を採用する。

```text
P-GUI-03 Application boundary audit / refactor plan
        ↓
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

## Current authority boundary

Phase Pは実装途中であるため、現時点の実システム仕様は引き続き以下を正本とする。

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- release `v1.1.0`

P-GUI-01/P-GUI-02で追加したGUI documentsはPhase P GUIのaccepted future contract/designであり、未実装GUIをcurrent runtime capabilityとして扱わない。

## Next

次に実施するTaskは次である。

```text
P-GUI-03 [P0] Transport-neutral Application boundary audit / refactor plan
```
