# Planning documents

`docs/planning/` は、Source Grounded Object Knowledge Base（SGOKB）の進行計画、Phase準備/完了監査、Task一覧、実行handoffを管理する領域です。

Planning文書はPhase / Task単位で整理し、`docs/planning/`直下には原則としてこのIndexだけを置きます。

## Current phase

Phase O — Documentation / Release / Git cleanup は **Complete** です。

2026-10-28のHappy-Path Operational Acceptanceで **FULL SGOKB PASS** を確認し、current formal releaseは `v1.1.0` です。

現在の開発Phaseは **Phase P — GUI / RAW Grounding / Runtime Modernization** です。

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Complete
Happy-path operational acceptance = Complete / FULL SGOKB PASS
Current formal release = v1.1.0
Phase P = In Progress
P-GUI-01 = Complete / Accepted
Next = P-GUI-02 — PySide6 application architecture / packaging / license design
```

Phase PのWorkstream優先順位は次で固定します。

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

## Current authority

### Phase P planning

- Phase P plan: [`phases/P/PHASE_P_MODERNIZATION_PLAN.md`](phases/P/PHASE_P_MODERNIZATION_PLAN.md)
- Phase P tasks: [`phases/P/PHASE_P_TASKS.md`](phases/P/PHASE_P_TASKS.md)
- Phase P current status: [`phases/P/PHASE_P_STATUS.md`](phases/P/PHASE_P_STATUS.md)
- Project task amendment: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md)

### P-GUI-01 accepted authority

- GUI requirements: [`../requirements/GUI_REQUIREMENTS.md`](../requirements/GUI_REQUIREMENTS.md)
- GUI compatibility / safety decision: [`../decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`](../decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md)
- CLI <-> GUI capability matrix: [`../reference/GUI_CLI_CAPABILITY_MATRIX.md`](../reference/GUI_CLI_CAPABILITY_MATRIX.md)

### Current implemented system

Phase P GUIは未実装のため、実システムのcurrent specificationは引き続き次を正本とします。

- Current integrated architecture: [`../design/SGOKB_CURRENT_ARCHITECTURE.md`](../design/SGOKB_CURRENT_ARCHITECTURE.md)
- Current design index: [`../design/README.md`](../design/README.md)
- Object-centered CLI contract: [`../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`](../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- Operational safety / recovery: [`../operations/OPERATIONAL_SAFETY_RECOVERY.md`](../operations/OPERATIONAL_SAFETY_RECOVERY.md)
- 1 Object標準運用: [`../operations/OBJECT_STANDARD_WORKFLOW.md`](../operations/OBJECT_STANDARD_WORKFLOW.md)
- Current release note: [`../releases/v1.1.0.md`](../releases/v1.1.0.md)

### Historical closure authority

- Phase O closure: [`phases/O/PHASE_O_STATUS.md`](phases/O/PHASE_O_STATUS.md)
- Phase N closure planning authority: [`phases/N/PHASE_N_CLOSURE_AUDIT.md`](phases/N/PHASE_N_CLOSURE_AUDIT.md)
- Phase N formal result: [`../evaluation/PHASE_N_CLOSURE_AUDIT.md`](../evaluation/PHASE_N_CLOSURE_AUDIT.md)
- Happy-path operational acceptance: [`../evaluation/SGOKB_HAPPY_PATH_ACCEPTANCE_20261028.md`](../evaluation/SGOKB_HAPPY_PATH_ACCEPTANCE_20261028.md)

Project-wide task masterにはhistorical next-task記述が残るため、Phase Pのcurrent stateについては`KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md`と`phases/P/`配下を優先します。

## Phase P summary

### Workstream A — GUI

PySide6 / Qt for Pythonを採用し、public `sgokb` CLIと意味的に互換なDesktop GUIを追加します。

基本境界:

```text
CLI ─┐
     ├─> Application / Service ─> Repository / Retrieval / Exchange
GUI ─┤
     └─ MCP read boundary
```

GUIはCLI subprocess wrapperを主実装とせず、既存Application / Service layerを共有します。CLIはPhase P後もfirst-class interfaceとして維持します。

P-GUI-01でcurrent public `sgokb` 67 operationsをGUI capabilityへ全件mappingし、assigned 67 / 67、unassigned 0を確認しました。GUI互換は同じCLI文字列を再生することではなく、same use case / target identity / canonical effect / validation / safety / degradation / failure semanticsを維持するsemantic parityとして定義しました。

主な追加GUI capability:

- Workspace / DB selector
- Object / Source / Evidence / Association management
- Search / Similarity / Registry / Version
- Package / Result workflow
- System / Maintenance
- progress / warning / error / diff / preview
- Equivalent CLI表示
- Runtime Dashboard

OSS配布時のPySide6 / Qt license complianceをRelease gateへ含めます。

### Workstream B — RAW Grounding

Evidenceはretrieval / selection単位として維持しますが、External AIへ送るsemantic materialはEvidence本文の再構成Markdownではなく、Evidence provenanceから遡ったRaw Artifactへ変更します。

```text
Evidence Retrieval / Selection
        ↓
selected Evidence
        ↓ provenance traversal
Normalization Run
        ↓
Raw Artifact
        ↓
RAW-bearing Package
        ↓
External AI
        ↓
Structured Object Result
```

Package Manifest、instructions、Object Result schema、Validation、Review、Import、ProvenanceをRaw-grounded contractへ更新します。

### Workstream C — Runtime

Windowsログイン後にQdrantが自動利用可能になる運用を標準化します。

QdrantはGUI processに所有させず、CLI / GUI / MCPから共有可能な独立runtimeとします。初期baseline候補はDocker / Compose、pinned Qdrant、named volume、localhost binding、restart policyです。

## Phase P task families

```text
P-GUI-01 .. P-GUI-10
P-RAW-01 .. P-RAW-06
P-RUNTIME-01 .. P-RUNTIME-06
P-CLOSE-01
```

詳細なscope / dependency / completion criteriaは [`phases/P/PHASE_P_TASKS.md`](phases/P/PHASE_P_TASKS.md) を参照してください。

GUIが最優先ですが、Package / Result UIはRAW Grounding contractに依存するため、GUI foundationと主要画面を先行し、Package / Result UIはP-RAW完了後に完成させます。

## Directory layout

```text
docs/planning/
├─ README.md
├─ project/
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md
│  └─ historical amendments ...
└─ phases/
   ├─ B/ ... O/
   └─ P/
      ├─ PHASE_P_MODERNIZATION_PLAN.md
      ├─ PHASE_P_TASKS.md
      └─ PHASE_P_STATUS.md
```

## Classification rules

### `project/`

Phaseをまたぐ全体task、project-wide handoff、amendmentを置きます。

### `phases/<Phase>/`

各Phase固有のPreparation、Status、Closure Audit、Phase-level task authorityを置きます。

### `phases/<Phase>/<Task>/`

1 Taskで複数の設計・実行文書が必要な場合に使用します。

### `execution/`

Reference Workstation / Codex等へ渡す一時的な実行handoffを対象Task配下へ置きます。完了後も再現性のため保持できますが、current authorityとは区別します。

## Document placement rules

1. 全Phase共通の進捗 / project-wide handoff → `project/`
2. Phase単位のstatus / preparation / closure / task authority → `phases/<Phase>/`
3. 特定Taskに複数文書が増える場合 → `phases/<Phase>/<Task>/`
4. 一時的な実行handoff → 対象Task配下の`execution/`
5. 結果・調査報告 → `docs/evaluation/`
6. 設計Decision → `docs/decisions/`
7. 実装設計 → `docs/design/`
8. operator手順 / operational safety → `docs/operations/`
9. Release Note / compatibility boundary → `docs/releases/`

## Next

次のTaskは次です。

```text
P-GUI-02 [P0] PySide6 application architecture / packaging / license design
```

P-GUI-02ではPySide6 application architecture、Qt Model/View / QMainWindow / Dock / Settings境界、thread / worker ownership、packaging方式、OSS配布license complianceを設計します。
