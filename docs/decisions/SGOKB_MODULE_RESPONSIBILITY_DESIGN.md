# SGOKB Module Responsibility Design

更新日: 2026-10-12

- Decision: Accepted
- Task: `D-04 [P0] src/sgokbの責務別再編を設計する`
- Scope: module responsibility / dependency direction / migration mapping
- Out of scope: physical file move, behavior change, production DB schema

## 1. 目的

Phase A〜Cで確定したSGOKBの論理境界を、将来の実装変更に耐える`src/sgokb`の責務境界へ落とし込む。

D-04では「理想フォルダへ既存ファイルを機械的に移動する」ことを目的としない。既存moduleは旧Prototypeの複数責務を1ファイルに持つため、まず新しい責務境界と依存方向を確定し、D-05以降のmove / split / compatibility方針の入力とする。

## 2. 現状調査

現在の`src/sgokb`は単一階層で、主に次の15 moduleからなる。

```text
__init__.py
__main__.py
application.py
benchmark.py
capture.py
cli.py
context.py
domain.py
extraction.py
final.py
importer.py
knowledge_repository.py
providers.py
repository.py
search.py
```

調査上の重要点:

- `repository.py`はSource / Snapshot / EvidenceだけでなくEntity / Fragment / Search / Embedding / Documentまで保持する大きなSQLite façadeである。
- `knowledge_repository.py`はHigh Recall Fragment Extraction、coverage、structured document、benchmark checkpointへの依存が強い。
- `application.py`はImport / Normalize / Fragment / Final / Embedding / Searchを1 serviceで横断する。
- `domain.py`はBundle / Block、SearchFilter / EmbeddingSpace、LLM / Embedder / VectorIndex / Reranker、hash/JSON helper、Fragment validationを混在させる。
- `providers.py`は新設計でも必要なEmbedding providerと、標準Knowledge生成から外れるGenerative LLM providerを混在させる。
- `capture.py`という名称はWeb Capture入力処理ではなく、旧High Recall Fragment生成を指しており、新設計の`ingestion`へそのまま移すと責務を誤認させる。
- `final.py`はFragment前提のFinal Document生成が中心で、将来のMarkdown renderingとして再利用できるのは一部だけである。

したがって、既存ファイル単位の1対1 moveでは責務分離にならない。

## 3. 確定する責務別構造

長期的な正規構造を次とする。

```text
src/sgokb/
├─ domain/        # Object Knowledgeの純粋な意味モデル・契約
├─ ingestion/     # Capture Bundle import / normalize / Evidence生成
├─ storage/       # SQLite / migration / repository / transaction
├─ retrieval/     # lexical / embedding / vector / hybrid / similarity
├─ exchange/      # Evidence Package / Result交換形式・validation補助
├─ rendering/     # canonical Knowledgeからの派生表示
├─ application/   # use case orchestration
├─ cli/           # CLI adapter
├─ mcp/           # MCP adapter
└─ _legacy/       # 移行期間だけの旧Prototype隔離領域
```

`_legacy/`は恒久的なArchitecture layerではない。Phase Lで削除・research-only・legacy read-onlyの最終処遇を決めるまで、旧Fragment / Final系を通常責務へ混在させないための一時隔離領域とする。

D-04では上記directoryをまだ作成しない。物理moveはD-05の移動方針確定後に行う。

## 4. 各責務

### 4.1 `domain/`

SGOKBが意味として所有するKnowledgeの中心契約を置く。

対象:

- Object Identity / Classificationのdomain contract
- Knowledge Versionのdomain contract
- Facet / Knowledge Statement / Relationのdomain contract
- Evidence reference / temporal scope等の意味契約
- domain-level validation

禁止:

- SQLite SQL
- filesystem I/O
- HTTP / external provider
- CLI / MCP
- Google Drive
- concrete Embedding model
- Fragment / Final Document旧model

Object / Version / Relation / Facetの**具体的な物理DB schemaや全fieldはPhase Eで決定する**。D-04はpackage責務だけを確定する。

### 4.2 `ingestion/`

外部Sourceをcanonical Source / Snapshot / Evidenceへ取り込むまでの処理を置く。

対象:

- Capture Bundle reader / validation
- Raw Artifact検証
- normalize
- DOM / HTML extraction
- Block / Evidence生成
- Source metadata / Page Context解析
- import時の安全性検証

原則として、ingestion自身がObject Knowledgeを生成しない。EvidenceからPreferenceやObject意味を推論しない。

### 4.3 `storage/`

canonical SQLiteと永続化責務を置く。

対象:

- connection / pragma / transaction
- migration runner
- Source / Snapshot / Evidence repository
- Object Knowledge repository（Phase Eで具体化）
- canonical read/write
- integrity / recoveryに必要な低レベル永続化

禁止:

- ranking logic
- HTML parsing
- ChatGPT / Google Drive
- CLI formatting
- Markdown rendering

現行`Repository`のような全責務巨大façadeを最終形としない。repositoryはaggregate / persistence responsibility単位へ分割可能な構造とする。

### 4.4 `retrieval/`

検索・Embedding・類似度計算を置く。

対象:

- Lexical / FTS
- Search Representation
- Embedding Space
- Embedder abstraction / local provider adapter
- VectorIndex abstraction / backend adapter
- Hybrid Search
- Object aggregation
- similarity
- reranker
- SearchFilter

Vector index / Embeddingはderived layerであり、canonical Knowledgeを所有しない。

Generative LLM providerはここへ入れない。

### 4.5 `exchange/`

local SGOKBとExternal Human-in-the-loop工程の間の交換契約を置く。

対象:

- Evidence Package format
- manifest serialization / validation
- package staging representation
- Structured Object Result format補助
- Result binding / package membership検証の機械的処理

Google Driveへの実送信やauthoritative import開始等の副作用はapplication use caseから明示的に呼ぶ。`exchange`を第二の正本にしない。

### 4.6 `rendering/`

canonical Object Knowledgeから再生成可能な人間向け表示を作る。

対象:

- Object JSON / domain model → Markdown
- Diff表示用representation
- 将来のread-only view生成

禁止:

- canonical write
- Final Markdownを正本扱いすること
- Fragment clusterを新Knowledge modelとして復活させること

### 4.7 `application/`

複数責務をまたぐuse caseを調停する。

例:

- Capture Bundle import
- Source processing
- Evidence Package build
- External export preflight
- Result validate/import
- derived index更新
- search / similar / get object
- render

`application`だけが複数capabilityの実行順序を組み合わせる。SQL、HTML parser、provider固有HTTP等の詳細実装は持たない。

### 4.8 `cli/`

CLIは薄いadapterとする。

責務:

- argument parsing
- human-readable output
- application use case呼び出し
- exit code

CLIからRepositoryへ直接SQL相当の操作を追加しない。

### 4.9 `mcp/`

MCP Knowledge Access Layerのadapterを置く。

責務:

- MCP Tool / Resource transport
- input/output schema adapter
- application use case呼び出し

MCPからSQLiteへ直接アクセスしない。これはC-04のSGOKB → UPDS contractを物理構造でも維持するための制約である。

### 4.10 `_legacy/`

旧Prototype機能の一時隔離領域。

候補:

- High Recall Fragment Capture
- Fragment validation / generation
- Final Document generation
- Fragment coverage / extraction job
- 旧structured document
- 旧Fragment/Final中心benchmark
- 標準runtimeから外れる旧Generative LLM orchestration

新機能から`_legacy`へ依存してはならない。既存互換・履歴閲覧・移行だけが参照可能とする。

## 5. 依存方向

基本依存方向を次とする。

```text
                 cli        mcp
                  \        /
                   application
          /      /    |      \       \
 ingestion  storage  retrieval  exchange  rendering
      \       |        |          /        /
       +------+--------+---------+--------+
                         |
                       domain
```

許可する基本関係:

- `domain` → Python標準ライブラリのみを基本とする。
- `ingestion` → `domain`
- `storage` → `domain`
- `retrieval` → `domain`, 必要最小限の`storage` read API
- `exchange` → `domain`
- `rendering` → `domain`
- `application` → `domain`, `ingestion`, `storage`, `retrieval`, `exchange`, `rendering`
- `cli` / `mcp` → `application`

禁止する方向:

- `domain` → storage / retrieval / application / adapter
- storage → application / cli / mcp
- ingestion → retrieval / exchange / cli / mcp
- retrieval → application / cli / mcp
- exchange → cli / mcp
- rendering → storageへの直接write
- 新設計module → `_legacy`
- mcp → SQLite direct access

複数capability間の調停が必要な場合は、相互importで解決せず`application`へ上げる。

## 6. generic `utils`を作らない

現行`domain.py`には`digest`, `json_text`, `uid`, `now`等の技術helperも混在する。

D-04では`common/`や`utils/`という無制限な共有領域を新設しない。

原則:

1. helperは最も近い責務へ置く。
2. 複数責務で本当に共有が必要な場合のみ、D-05以降で狭い契約を抽出する。
3. shared helperを理由にdomainへ技術I/O責務を押し込まない。

## 7. 既存moduleから新責務へのmapping

| 現行module | 分類 | 新責務 / 方針 |
|---|---|---|
| `importer.py` | Keep | `ingestion`。Bundle reader / validationをほぼそのまま再利用候補。 |
| `extraction.py` | Keep | `ingestion`。DOM→Block→Evidence基盤を再利用。 |
| `context.py` | Keep/Modify | `ingestion`。Source metadata / Page Context責務として再配置候補。 |
| `repository.py` | Split/Modify | `storage`中心。Source/Evidence保持部分を再利用し、Entity/Fragment/Search/Document責務を分解。 |
| `knowledge_repository.py` | Mostly Replace | 主に`_legacy`。汎用checkpoint / observation思想だけ必要なら個別抽出。 |
| `domain.py` | Split/Modify | Bundle/Block→`ingestion`、Search/Embedding contracts→`retrieval`、LLM→legacy/optional、Fragment validation→`_legacy`。新Object domainはPhase Eで`domain`へ追加。 |
| `search.py` | Modify | `retrieval`。RRF / vector / reranker骨格を再利用しObject中心へ変更。 |
| `providers.py` | Split | Embedding provider→`retrieval`。Generative LLM provider→標準runtime外、`_legacy`または将来research adapter。 |
| `application.py` | Replace use cases / Keep role | `application`。orchestratorという役割は維持し、Fragment/Final中心use caseを新Workflowへ差し替える。 |
| `cli.py` | Modify | `cli` adapter。parser/dispatchをObject中心へ再構成。 |
| `capture.py` | Replace/Legacy | Web capture入力ではない。High Recall Fragment生成として`_legacy`対象。 |
| `final.py` | Replace/Partial reuse | Fragment Final生成は`_legacy`。純粋rendering部分のみ`rendering`へ再利用候補。 |
| `benchmark.py` | Retire/Modify | 旧Fragment KPIはlegacy。Retrieval評価はPhase N向けに別評価責務として再構成。 |
| `__main__.py` | Keep/Modify | CLI entrypointへの薄いforwarderとして維持可能。 |
| `__init__.py` | Modify | public APIを責務別packageへ合わせて最小化。 |

## 8. 現行重要クラス / 関数の配置判断

- `Bundle`, `Block` → `ingestion`
- `SearchFilter`, `EmbeddingSpace`, `Embedder`, `VectorIndex`, `Reranker`, `validate_vectors` → `retrieval`
- `LLM` protocol → 標準Coreから除外しlegacy/optional側
- `validate_fragments` → `_legacy`
- `WebCaptureImporter` → `ingestion`
- `GenericExtractor`, `WikipediaExtractor`, `PixivExtractor`, `ExtractorRegistry` → `ingestion`
- `SQLiteCosineIndex`, `HybridSearch`, `SimpleReranker`, `merge_candidates` → `retrieval`
- `CompatibleEmbedder`, `SentenceTransformerEmbedder` → `retrieval`
- `CompatibleLLM`, `StrataLLM`, `LMStudioLLM` → standard runtime外
- `HighRecallCapture` → `_legacy`
- `StructuredFinal`, Fragment cluster logic → `_legacy`
- 現行`Application` →新`application`の参考にするが、method単位でそのままpublic APIとしない

## 9. D-04で固定しない事項

次は後続Phaseの責務であり、D-04では確定しない。

- Object / Version / Facet / Relation tableの列定義
- repository classの最終個数・class名
- JSON Schemaのfield
- Vector backend
- Embedding model
- Search ranking parameter
- MCP Tool名 / transport
- Google Drive API採否
- legacy table削除時期
- compatibility shimの具体的実装期間

## 10. D-05への入力 — move / splitの原則順序

D-05では次の順序を基準として具体的移動方針を決める。

1. **独立Keep module**: importer / extraction / context等、意味変更なしで責務が明確なもの。
2. **Retrieval基盤**: searchとEmbedding provider。配置変更とcandidate model変更を分ける。
3. **Storage基盤**: SQLite接続・migration・Source/Evidence persistenceをFragment/Document責務から分離する。
4. **Application / adapters**: 新しい責務へのimport pathを揃えてからorchestrator / CLIを再構成する。
5. **Legacy隔離**: replacement pathが成立した機能から旧Fragment / Finalを`_legacy`へ隔離する。

重要:

- move-onlyとbehavior changeを同一PRへ混在させない。
- `repository.py` / `domain.py` / `providers.py`のsplitは単純renameではないため、移動だけのPRとして扱わない。
- compatibility importが必要な場合は期限と削除Taskを明記する。
- Phase E schemaを先に作るためだけの空module大量生成は行わない。

## 11. D-06 / D-07への影響

D-06では、上記code責務とruntime data配置を混同しないよう、`.local/`, canonical DB, generated index, package/result exchange, backupをGit管理外として整理する。

D-07では、module移行の履歴を追えるようmove-only PRを残し、Prototype tagを保持する。`_legacy`はGit履歴削除ではなく責務隔離である。

## 12. D-04完了条件

- [x] 現行15 moduleを棚卸しした。
- [x] 再利用 / split / replace / legacyの責務を整理した。
- [x] 正規`src/sgokb`責務別構造を確定した。
- [x] 各packageの責務と禁止事項を定義した。
- [x] 依存方向と禁止依存を定義した。
- [x] 現行module → 新責務mappingを定義した。
- [x] Phase Eの物理DB schemaを先取りしていない。
- [x] D-05へmove / split順序の入力を定義した。
- [x] 実ファイルのmove / behavior changeを行っていない。

次Taskは`D-05 [P1] 既存モジュール移動方針を決める`とする。
