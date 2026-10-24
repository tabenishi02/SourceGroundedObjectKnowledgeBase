# Source Grounded Object Knowledge Base (SGOKB)

**Source Grounded Object Knowledge Base（SGOKB）** は、ユーザーが選択・収集したWeb上の資料を追跡可能な **Source / Evidence** として保持し、Character・Work・Conceptなどを長期利用可能な **Object Knowledge** として構造化・版管理するローカルKnowledge Baseです。

SGOKBの正本は巨大なMarkdown文書ではありません。Source / Evidenceへ遡れる構造化Knowledgeを正本として保持し、検索・類似検索・Relation参照・MCP・Markdown表示・AI向けContextなどをその上に構築します。

## Status

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 README update = Complete
O-02 Current design documentation = Complete
O-03 Prototype Archived / Legacy labels = Complete
O-04 main integration = Complete
Next = O-05 Branch cleanup
```

Phase NはReference Workstationでのclosure audit C01-C07 PASSと独立レビューを完了しています。Phase OではDocumentation / Release / Git cleanupを進めます。Release / TagはO-06まで未確定です。

現在のPhase O状態は [Phase O Status](docs/planning/phases/O/PHASE_O_STATUS.md)、現行全体設計は [Current System Architecture](docs/design/SGOKB_CURRENT_ARCHITECTURE.md)、運用安全・復旧設計は [Operational Safety / Backup / Recovery](docs/operations/OPERATIONAL_SAFETY_RECOVERY.md) を参照してください。

---

## What SGOKB is for

SGOKBの目的は、個別チャットや特定AIのContext Windowへ閉じ込めず、ユーザーが価値を認めた資料とObject Knowledgeを長期保存し、将来のAIや他システムから再利用できる外部知識記憶を構築することです。

主な性質:

- **Source grounded** — Knowledgeから根拠となるEvidence / Raw Sourceへ遡れる。
- **Object centered** — Character / Work / Conceptなどをstable Object IDで管理する。
- **Versioned** — accepted Knowledgeを上書きせずVersionとして保持する。
- **Semantic** — Object / Facet / Statement単位で検索・比較・類似検索できる。
- **Local first** — canonical Knowledgeはローカルで成立し、特定cloud AIを必須としない。
- **Human in the loop** — 高度な意味統合はChatGPT等へ明示的に依頼できるが、外部送信・Importの境界はSGOKB側で管理する。
- **Model independent** — Knowledgeの正本を特定LLM・Embedding model・MCP clientへ依存させない。

SGOKBが主要目的としないもの:

- Web全体を無差別に巡回するCrawler
- 巨大なFinal Documentを唯一の正本とするDocument Generator
- すべてを生成AIへ通す完全自動Pipeline
- ChatGPT APIがなければ成立しないservice
- ユーザー自身の嗜好・価値観を推論するPersonal Inference system

ユーザー嗜好・価値観・Selection Eventからの推論は **UserPreferenceDiscoverySystem（UPDS）** 側の責務です。SGOKBはWorld / Object Knowledge Layerとして独立します。

---

## Architecture

```text
Web / local capture
        │
        ▼
Capture / Import
        │
        ▼
Source / Snapshot / Raw Artifact
        │
        ▼
Normalize / Evidence
        │
        ├───────────────┐
        │               │
        ▼               │
Object Evidence         │
Retrieval / Selection   │
        │               │
        ▼               │
Evidence Package        │
        │               │
        │ explicit export
        ▼               │
ChatGPT / external AI   │
(manual semantic        │
 integration)           │
        │               │
        ▼               │
Structured Object       │
Result (`result.json`)  │
        │               │
        ▼               │
Validate / Review       │
        │               │
        ▼               │
Explicit Import         │
        │               │
        ▼               │
Object Knowledge Version
        │
        ├───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
Lexical Search   Search Representation  Markdown
                 / Embedding / Vector   Rendering
                        │
                        ▼
                 Semantic / Hybrid /
                 Similarity Search
                        │
                        ▼
              CLI / MCP read boundary
                        │
                        ▼
             ChatGPT / Local LLM / UPDS
```

### Canonical vs derived

| Layer | Role | Rebuildable? |
|---|---|---|
| Source / Snapshot / Raw Artifact | 取得した一次資料と履歴 | **No — preserve** |
| Evidence / Provenance | Knowledgeの根拠・追跡情報 | **No — preserve** |
| Object Registry / accepted Knowledge Version | Object Knowledgeの正本 | **No — preserve** |
| Search Representation / Embedding | 検索用派生表現 | Yes |
| Qdrant Vector Index | Semantic / Similarity用派生index | Yes |
| Markdown Render | 人間向け表示 | Yes |
| Evidence Package | 外部AIへ渡す交換artifact | Yes / reproducible from current source state |

Vector IndexやMarkdownを失っても、それらをcanonical Knowledgeの代わりにはしません。

現行Architectureの詳細なauthority mapは [SGOKB Current System Architecture](docs/design/SGOKB_CURRENT_ARCHITECTURE.md) を参照してください。

---

## Requirements

- Python **3.10+**
- SQLite（Python標準runtimeを利用）
- Semantic / Hybrid / Similarityを利用する場合:
  - local Embedding runtime
  - Qdrant runtime
- MCPを利用する場合:
  - MCP Python SDK optional dependency

初期MVPはWindows 11をPrimary environmentとして検証していますが、core Python packageは特定GUIへ依存しません。

---

## Installation

### Core + development

PowerShell例:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\sgokb.exe --help
```

### MCP + local semantic runtimeを含める場合

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,mcp,local-embedding,vector-qdrant]'
```

Qdrant server自体は別途起動・構成してください。local Embedding providerが失敗してもcloud providerへsilent fallbackしません。

---

## 1 Object standard workflow

詳細な手順は [1 Object Standard Workflow](docs/operations/OBJECT_STANDARD_WORKFLOW.md) を正本とします。以下は最小概要です。

### 1. Objectを登録する

```powershell
$Db = ".local/sgokb.sqlite"
sgokb --db $Db object add --name "Target Object" --primary-class character
```

SGOKBではstable `object_id`をauthoritative identityとして扱います。write operationでは可能な限りObject IDを使用します。

### 2. SourceをimportしてEvidenceを作る

```powershell
sgokb --db $Db source import "C:\path\to\capture.webcapture.zip"
sgokb --db $Db source process --snapshot <snapshot-id>
```

Sourceが対象Objectの根拠であることを確認してassociationを設定します。

```powershell
sgokb --db $Db association set --object <object-id> --source <source-id> --status confirmed
sgokb --db $Db evidence candidates --object <object-id>
sgokb --db $Db evidence select --object <object-id>
```

### 3. Evidence Packageを作る

```powershell
sgokb --db $Db package build --object <object-id>
sgokb --db $Db package stage <build-path>
sgokb --db $Db package preflight <staged-path> --destination <export-root>
sgokb --db $Db package export <staged-path> --destination <export-root>
```

`package export`はSGOKB外へのdata egressです。`blocked`は送信せず、`review_required`は人間が内容・destination・warningを確認した場合だけ明示承認します。

### 4. ChatGPTで意味統合する

ExportしたPackageをChatGPTへ手動で渡します。標準Packageには少なくとも対象Object、manifest、`instructions.md`、選択されたEvidenceが含まれます。

ChatGPT側では:

1. `instructions.md`を分析指示の正本として扱う。
2. Package内Evidenceを根拠としてObject Knowledgeを構造化する。
3. Package外の情報をEvidence IDとして創作しない。
4. Structured Object Resultを **`result.json`** として返す。

この工程はSGOKB coreからChatGPT APIを自動呼出しする処理ではありません。Google Drive同期directory等を交換場所に使うことはできますが、SGOKBはGoogle Drive APIやChatGPT APIを成立条件としません。

### 5. Resultをvalidate / review / importする

```powershell
sgokb --db $Db result detect --incoming-root exchange/incoming
sgokb --db $Db result receive <result-path> --package-id <package-id> --incoming-root exchange/incoming
sgokb --db $Db result validate <receipt-id> --incoming-root exchange/incoming
sgokb --db $Db result review <receipt-id> --incoming-root exchange/incoming --review-format markdown
sgokb --db $Db result import <receipt-id> --incoming-root exchange/incoming
```

Validation成功だけで自動Importしません。stale / partial / review-required状態を確認し、accepted Knowledgeへの昇格はexplicit Import boundaryを通します。

Registry proposalもKnowledge Importの副作用として自動適用せず、accept/rejectとapplyを別操作にします。

### 6. accepted Knowledgeを確認する

```powershell
sgokb --db $Db object show --object <object-id> --knowledge
sgokb --db $Db object relations --object <object-id>
sgokb --db $Db render --object <object-id>
sgokb --db $Db search "query" --mode lexical
```

---

## Search and Similarity

SGOKBは用途を分けて検索します。

### Lexical

SQLiteだけで成立するlocal read pathです。

```powershell
sgokb --db $Db search "character name" --mode lexical
```

### Semantic / Hybrid

local Embedding providerとVector runtimeを明示的にcompositionします。

```powershell
sgokb --db $Db search "責任感が強く自己犠牲的な人物" --mode semantic --semantic-runtime --require-full-runtime
sgokb --db $Db search "責任感" --mode hybrid --semantic-runtime
```

Hybrid Searchはsemantic channelが利用不能な場合、contract上許される範囲でLexicalへdegradeできます。その場合はwarningとして明示されます。

### Similarity

```powershell
sgokb --db $Db similar --object <object-id>
```

Facet-specific Similarityも利用できます。missing Facetをoverall similarityへsilent fallbackしません。

---

## MCP access

SGOKBの初期MCP surfaceは **read-only** です。MCP transportからSQLiteへ直接アクセスせず、`KnowledgeReadApplication`を経由します。

Server:

```powershell
sgokb --db .local/sgokb.sqlite mcp serve
```

Semantic runtimeを必要とするclientでは、環境構成に応じてsemantic runtimeを明示して起動します。

Active read capabilities:

```text
search_objects
find_similar_objects
get_object
get_objects
get_object_relations
get_object_evidence
search_evidence
build_context
```

MCP clientからの概念的な呼出し例:

```text
search_objects({
  "query": "自己犠牲を重視するcharacter",
  "mode": "hybrid",
  "limit": 10
})

get_object({
  "object_id": "<stable-object-id>",
  "facets": ["personality", "values"]
})

find_similar_objects({
  "object_id": "<stable-object-id>",
  "facet": "themes",
  "limit": 10
})

build_context({
  "object_ids": ["<object-id-a>", "<object-id-b>"],
  "purpose": "comparison",
  "max_characters": 12000
})
```

`build_context`はLLM推論を行わず、保存済みKnowledgeから用途別に決定論的なsubsetを選択します。

Canonical write、Result Import、Registry変更などはMCP read Toolから行いません。

詳細:

- [MCP Read Tool Contract](docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md)
- [Context Builder Contract](docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md)
- [Object-centered CLI Contract](docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)

---

## Safety and operational boundaries

SGOKBでは次の境界を明示します。

- Source / Raw / Evidence / accepted Knowledgeをderived indexで置換しない。
- accepted Knowledge Versionは論理immutableとして扱う。
- Package Exportは明示的なexternal egress operationとする。
- Result Validationとcanonical Importを分離する。
- Registry proposalをsilent applyしない。
- local provider failureからcloudへsilent fallbackしない。
- MCP MVPはread-onlyとする。
- Vector Indexはcanonical SQLite / Search Representationから再構築可能にする。
- backup / restoreではcanonical dataとRaw / Provenanceを保全する。

Failure / Recovery、Composite backup / restore、RPO / RTOはPhase Nで正式受入済みです。現行運用設計は [Operational Safety / Backup / Recovery](docs/operations/OPERATIONAL_SAFETY_RECOVERY.md)、formal evidenceは [N07-R01 Re-Acceptance](docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md) を参照してください。

---

## Repository layout

```text
README.md
benchmark/                   # acceptance contract / result / benchmark tools
docs/
  requirements/              # current requirements
  decisions/                 # accepted decisions / design freeze
  design/                    # implementation-level current design
  evaluation/                # benchmark / acceptance / failure analysis
  operations/                # operator workflow / recovery
  planning/                  # project / phase / task status and handoff
  reference/                 # survey / inventory / gold/reference material
  archive/                   # historical Prototype / rename material
extensions/web-page-capture/ # Web Page Capture extension / Native Host
scripts/                     # evaluation / maintenance helpers
src/sgokb/                   # Python implementation
tests/                       # automated regression tests
```

Web取得部分の詳細は [Web Page Capture README](extensions/web-page-capture/README.md) を参照してください。

---

## Documentation

入口:

- [Documentation Index](docs/README.md)
- [Current Design Index](docs/design/README.md)
- [Current System Architecture](docs/design/SGOKB_CURRENT_ARCHITECTURE.md)
- [Operational Safety / Backup / Recovery](docs/operations/OPERATIONAL_SAFETY_RECOVERY.md)
- [Planning Index](docs/planning/README.md)
- [Phase O Status](docs/planning/phases/O/PHASE_O_STATUS.md)
- [Project Task Master](docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- [1 Object Standard Workflow](docs/operations/OBJECT_STANDARD_WORKFLOW.md)

主要な現行contract:

- [Purpose Requirements](docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md)
- [Object Requirements](docs/requirements/OBJECT_REQUIREMENTS.md)
- [Source / Evidence Requirements](docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md)
- [Search Requirements](docs/requirements/SEARCH_REQUIREMENTS.md)
- [Workflow Responsibility Requirements](docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md)
- [Non-functional Requirements](docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md)
- [Object-centered CLI Contract](docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- [MCP Read Tool Contract](docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md)
- [Phase N Closure Result](docs/evaluation/PHASE_N_CLOSURE_AUDIT.md)

旧Prototypeの要件・設計・評価・モデル比較等は [`docs/archive/prototype-0.2/`](docs/archive/prototype-0.2/) に保存しています。O-03でArchived / Legacy stateを明示済みであり、Archiveはcurrent specificationではありません。

---

## Development verification

基本回帰:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m compileall -q src benchmark/tools tests
git diff --check
```

Phase N closureではfull suite **783 passed / 0 failed / 0 skipped** を確認しています。

Repository-wide `ruff format --check .`にはaccepted baseline由来の既存22ファイルが残っています。O-01/O-02のようなdocumentation変更では無関係なhistorical/baseline fileを一括formatせず、変更対象のformatとdiff hygieneを維持してください。詳細は [Phase N Closure Audit](docs/evaluation/PHASE_N_CLOSURE_AUDIT.md) を参照してください。

---

## Historical Prototype

旧PrototypeはFragment生成と巨大Final Document生成を中心としていました。現在のSGOKBではそのpipelineを標準runtimeから撤去し、Source / Evidence / Object Knowledge / Version / Retrieval / MCPをcurrent architectureとしています。

旧挙動を調査する場合はGit historyと [Prototype 0.2 Archive](docs/archive/prototype-0.2/) を参照し、current SGOKB contractと混同しないでください。
