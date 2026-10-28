# Phase P — GUI / RAW Grounding / Runtime Modernization

Updated: 2026-10-28

- Status: **Planned / Not Started**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Scope: GUI、External AI grounding input、local semantic runtime operations

## 1. Purpose

Phase Pでは、SGOKB v1.1.0で受入済みのcanonical Knowledge / Source / Evidence / Retrieval / CLI / MCP境界を保ちながら、日常運用をCLI中心からGUI中心へ拡張する。

同時に、外部AIへ渡すPackageのgrounding materialを、現行のEvidence本文再構成ファイルから、EvidenceのProvenanceを辿って取得したRaw Artifactへ変更する。また、Semantic / Hybrid / Similarity運用で利用するQdrantをWindows起動後に自動利用可能な状態へする。

Phase Pの3 Workstreamと優先順位は次で固定する。

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

ただしPackage / Result GUIはRAW Grounding contractの影響を直接受けるため、GUI基盤と主要read/write画面を先行実装し、Package / Result画面はRAW Grounding確定後に完成させる。

## 2. Workstream A — GUI

### 2.1 Goal

PySide6を用いて、operator-facing public `sgokb` CLIと意味的に互換なDesktop GUIを追加する。

GUIはCLI subprocess wrapperを主実装としない。CLIとGUIは同じApplication / Service boundaryを共有する。

```text
                    ┌─ CLI
                    │
Application / Service ─┼─ GUI (PySide6)
                    │
                    └─ MCP read boundary
```

GUIはcanonical SQLiteへ独自SQL contractで直接依存せず、既存Application / Service / Repository contractを再利用する。必要なApplication boundaryが不足する場合は、CLI専用ロジックをGUIへ複製せずtransport-neutralなApplication層へ移す。

### 2.2 CLI compatibility target

GUIは少なくともpublic `sgokb` command surfaceを機能互換対象とする。

- Source
- Object
- Association
- Evidence
- Registry
- Package
- Result
- Version
- Search
- Similarity
- Render
- MCP
- System / Maintenance

R2 generation operator `python -m sgokb.cli.generation` は通常GUIから分離し、必要な場合のみAdvanced / Maintenance surfaceとして扱う。

GUI上の操作はCLIのside-effect semanticsを保持する。

```text
READ        -> 原則即時実行
DERIVED     -> progress / completion表示
WRITE       -> 変更内容確認
EXTERNAL    -> destination / egress内容確認
MAINTENANCE -> 強い確認とrecovery情報
```

CLIのerror / warning区分もGUIで失わない。

### 2.3 GUI-specific capabilities

CLI互換に加え、Desktop GUIとして次を追加する。

- Workspace / DB selector
- Global navigation
- Master-detail list / detail views
- Filter / sort / search
- Long-running operation progress / cancellation boundary
- Error / warning center
- Diff / preview before important mutations
- Equivalent CLI command display
- Operation / audit history view
- Drag & Drop import
- Bulk review / selection where safe
- Saved view / layout persistence
- Keyboard navigation / command palette candidate
- Runtime health dashboard
- Markdown / structured diff preview
- Relation / Provenance visualization candidate

### 2.4 PySide6 decision

GUI frameworkは **PySide6 / Qt for Python** を採用する。

主な理由:

- SGOKB coreと同じPython processからApplication層を直接利用できる。
- Qt Model/View、Tree/Table、Dock、File Dialog、Status Bar、Settings、threading/event loop等がSGOKBの操作UIに適する。
- CLI / MCPとは独立したpresentation layerとして追加しやすい。

OSS配布時はPySide6 / QtのLGPLv3等のライセンス条件を満たすことをRelease gateへ含める。特にthird-party license notice、利用ライブラリのlicense情報、利用者によるLGPL library replacementを妨げない配布形態を確認する。GUI packaging時に改めてlicense auditを行う。

## 3. Workstream B — RAW Grounding

### 3.1 Goal

外部AIへ与えるsemantic materialを、Package Builderが再構成したEvidence Markdownではなく、選択EvidenceのProvenanceから遡った **Raw Artifactそのもの** へ変更する。

Evidenceは廃止しない。Evidenceは引き続き次の責務を持つ。

- Objectに関連するSource / generationを検索・選択する単位
- retrieval / budget / manual include-excludeの単位
- accepted Knowledgeの既存provenanceを追跡するcanonical data

新しい基本フローは次とする。

```text
Evidence Retrieval / Selection
        ↓
selected Evidence
        ↓ provenance traversal
Normalization Run
        ↓
Raw Artifact
        ↓ deduplicate / verify
RAW-bearing Object Package
        ↓ explicit export
External AI
        ↓
Structured Object Result
        ↓
Validate / Review / Explicit Import
```

### 3.2 Required redesign boundary

これはPackage内ファイルを置換するだけの変更ではない。

現行ResultはEvidence IDへのgroundingを前提とするため、External AIが直接読んだmaterialとResult grounding referenceが一致するよう、次を再設計する。

- Evidence -> Normalization Run -> Raw Artifact resolution contract
- Raw ArtifactのPackage inclusion / deduplication / integrity rule
- Package manifest schema
- `instructions.md`
- Object Result schema
- grounding reference semantics
- Result validation
- Review / diff表示
- Import時のProvenance保存
- current accepted Knowledgeとの互換・migration / versioning policy

Raw Artifactは既存canonical chainの`raw_artifacts.storage_ref` / `logical_path` / `sha256`等を利用し、export前にbytesとhashを再検証する。

### 3.3 Safety

RAW exportもExternal Egressであり、現行Package preflight / review-required / blocked境界を維持する。

Raw ArtifactにはEvidence再構成物より多くの情報が含まれる可能性があるため、credential / token / private metadata / oversized artifact等のpreflightを再評価する。

## 4. Workstream C — Runtime / Qdrant auto-start

### 4.1 Goal

Windowsログイン後、SGOKB GUIやCLIを使用する前にQdrantが利用可能になる運用を標準化する。

SGOKB GUIをQdrant processのlifecycle ownerにはしない。Qdrantは独立runtimeとして起動し、CLI / GUI / MCPのいずれからも利用可能にする。

```text
Windows runtime / container runtime
        ↓ owns
      Qdrant
        ↑
        │ observes / connects
CLI / GUI / MCP
```

### 4.2 Preferred baseline

初期候補は次とする。

- Docker / Docker Compose
- Qdrant image versionを明示的にpin
- named volumeを使用
- localhost (`127.0.0.1`) に限定してport公開
- restart policyによりcontainer runtime開始後に自動起動
- Windowsログイン時にcontainer runtimeを起動

最終採用構成はPhase P Runtime taskでReference Workstation上のstartup / shutdown / recovery / upgrade挙動を検証して固定する。

### 4.3 GUI integration

GUIのRuntime Dashboardでは少なくとも次を観測可能にする。

- SQLite availability
- Embedding provider availability
- Qdrant endpoint / health
- Vector generation / derived state
- MCP state where applicable

GUI終了をQdrant停止条件にはしない。

## 5. Sequencing

```text
GUI foundation / core screens
        ↓
RAW Grounding contract + implementation
        ↓
Package / Result GUI completion
        ↓
System / Maintenance GUI completion
        ↓
Qdrant auto-start + Runtime Dashboard integration
        ↓
Full Phase P compatibility / acceptance
```

GUIを最優先とするが、RAW Groundingによる作り直しを避けるためPackage / Result UIだけはRAW contract確定後に完成させる。

## 6. Non-goals

Phase Pでは次を自動的な目標としない。

- canonical Knowledge schema全体の再設計
- accepted Knowledgeの一般的なUndo / Ctrl+Z rollback
- MCP write capability追加
- External AI APIの自動呼出し
- Qdrantをcanonical storeへ昇格すること
- GUI依存によりCLI headless operationを廃止すること

## 7. Compatibility principle

Phase P後もCLIはfirst-class interfaceとして維持する。

GUIで可能なcanonical operationは、原則として同じApplication / Service contractをCLIからも実行可能であることを維持する。GUI固有機能はpresentation / workflow assistanceに限定し、GUIのみがcanonical dataへ到達できるhidden write pathを作らない。

## 8. Authority

本書はPhase Pの**計画authority**であり、実装済みcurrent architectureを直ちに置き換えない。

Phase P taskが完了するまでは、current runtime / Package / Result / CLI contractについて次が引き続きauthorityである。

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- current Package / Object Result design documents
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`

Task完了時にcurrent requirement / decision / design / operations文書へ昇格・統合する。