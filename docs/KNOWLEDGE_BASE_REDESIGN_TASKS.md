# CharacterPageCollector — Knowledge Base 再設計タスク

更新日: 2026-10-09

## 1. 目的

本書は、CharacterPageCollector（CPC）を、従来の「WebページをローカルLLMで細粒度にFragment化し、巨大な最終文書を自動生成するプロトタイプ」から、次の方針へ移行するための作業計画を定義する。

> Web上の情報をSource / Evidenceとして保持し、Character / Work / Concept等をObjectとして整理する。Objectに必要な根拠を検索・抽出してChatGPTへ渡し、ChatGPTが生成した構造化Object Dataを検証・版管理して正本DBへ保存する。保存済みKnowledgeは全文検索・意味検索・類似検索・Relation検索を提供し、MCP経由でChatGPT、ローカルLLM、UserPreferenceDiscoverySystem等から利用可能にする。

本再設計では、自動化率の最大化よりも、処理時間、品質、追跡可能性、保守性、人間とAIの責務分離を優先する。

## 2. 再設計後の基本境界

```text
Web
 ↓
Source Capture / Import
 ↓
Source / Evidence Store
 ↓
Retrieval（FTS + Semantic）
 ↓
Object Evidence Package
 ↓
Google Drive
 ↓  手動工程
ChatGPT（APIを使用しない）
 ↓
Structured Object Result
 ↓
Validation / Import / Versioning
 ↓
Object Knowledge Store
 ↓
FTS / Semantic / Similarity / Relation Retrieval
 ↓
MCP
 ↓
ChatGPT / Local LLM / UPDS / Other Clients
```

CPCは「外部世界のObject Knowledge」を担当する。ユーザー自身の嗜好・価値観・関心傾向の推論はUserPreferenceDiscoverySystem（UPDS）の責務とし、CPCには含めない。

---

# Phase A — 方針確定・既存資産棚卸し

- [x] **A-01 [P0] 再設計Decision Recordを作成する**
  - 旧Prototypeの問題点と再設計理由を記録する。
  - 「全Evidenceを生成LLMでFragment化する方式を標準パイプラインから外す」ことを明記する。
  - 「巨大Final DocumentをKnowledgeの正本としない」ことを明記する。
  - ChatGPT APIを標準処理に使用しない方針を明記する。

- [x] **A-02 [P0] 既存機能を Keep / Modify / Replace / Retire に分類する**
  - Keep候補: Web Capture、Raw Import、Source/Snapshot、Evidence抽出、checksum、Provenance、SQLite、FTS、Embedding provider abstraction、Hybrid Search基盤。
  - Modify候補: Entity → Object、検索対象・Facet、CLI、評価基盤。
  - Replace候補: Fragment中心Knowledge Model、Final Document生成。
  - Retire候補: 全Evidenceへの高コストLLM Fragment抽出を前提とする処理・benchmark。

- [x] **A-03 [P1] 既存DB・CLI・モジュール・テストの依存関係を棚卸しする**
  - Fragment / Final Documentを削除した場合の影響範囲を一覧化する。
  - 既存実データDBの移行可否を確認する。

**完了条件:** 再利用する資産と廃止する資産が明文化され、以降の設計が旧Prototypeの暗黙仕様に依存しない。

---

# Phase B — 要件定義の全面更新

- [ ] **B-01 [P0] CPCの目的を再定義する**
  - CPCを「Curated Semantic Object Knowledge Base」として定義する。
  - 文書生成は目的ではなく派生表示とする。

- [ ] **B-02 [P0] Object要件を定義する**
  - 共通Object + `object_type` を基本とする。
  - 初期型: `Character`, `Work`, `Concept`。
  - 将来拡張型を固定列挙しすぎない。
  - name / aliases / type / status / version等の共通属性を定義する。

- [ ] **B-03 [P0] Source / Evidence要件を再確認する**
  - SourceとObjectを多対多とする。
  - Raw / normalized / evidenceのProvenanceを保持する。
  - LLM解析結果と一次資料を混同しない。

- [ ] **B-04 [P0] Object Result要件を定義する**
  - JSONを機械向け正本とする。
  - MarkdownはJSONから生成可能な派生表示とする。
  - Object type別Facetを定義可能にする。
  - Relation、Evidence参照、生成来歴を保持する。

- [ ] **B-05 [P0] 検索要件を定義する**
  - Lexical Search必須。
  - Semantic Search必須。
  - Object Similarity Search必須。
  - Facet単位Similarity Searchを設計対象とする。
  - Relation Search必須。
  - Evidence Searchを監査・再分析用途として残す。

- [ ] **B-06 [P0] 人間工程と自動工程を要件として分離する**
  - CPC自動処理の目標時間: 1 Objectあたり概ね10分以内。
  - Google Drive → ChatGPT → Result返却は手動工程として時間目標から除外する。
  - 人間の明示操作が必要な箇所をUI/CLI仕様に明記する。

- [ ] **B-07 [P1] 非機能要件を更新する**
  - オフライン継続利用。
  - Source/Knowledgeの再生成可能性。
  - 破壊的更新を避けるVersioning。
  - Embedding model変更時のIndex分離・再構築。
  - MCPが停止しても正本DBが利用可能であること。

**完了条件:** 既存の要件定義書を新方針で置換または新版化し、旧Prototype要件との差分が説明可能である。

---

# Phase C — CPC / UPDS責務境界

- [ ] **C-01 [P0] CPCをWorld/Object Knowledge Layerとして定義する**
  - Objectそのものの属性・意味・関係・根拠のみを扱う。
  - 「ユーザーが好む」等のユーザー推論を保存しない。

- [ ] **C-02 [P0] UPDSをPersonal Inference Layerとして定義する**
  - Selection Event、Pattern、Preference HypothesisはUPDS所有とする。
  - CPCはUPDSを知らなくても単独で成立させる。

- [ ] **C-03 [P1] Conceptの所有境界を確定する**
  - Conceptそのものの定義・Relation・EmbeddingはCPCで管理する案を第一候補とする。
  - UPDSはCPC Concept IDを参照してPreference Evidenceを構築できるようにする。

- [ ] **C-04 [P1] CPC→UPDS連携契約を定義する**
  - Object IDの安定性。
  - Object / Facet / Relationの取得方式。
  - MCP経由を基本とし、DB直結を前提としない。

**完了条件:** 両プロジェクトで同一ConceptやObject Knowledgeを重複生成しない責務境界が決まっている。

---

# Phase D — Repository / Git / フォルダ構造再編

- [ ] **D-01 [P0] 再設計用長期ブランチ戦略を決定する**
  - `main`は動作可能な基準点として保持する。
  - 大規模移行は例: `feature/knowledge-base-redesign` で実施する。
  - サブ変更は必要に応じて短命branch + PRとし、巨大な未レビュー差分を避ける。

- [ ] **D-02 [P0] 旧Prototype文書の扱いを決める**
  - 削除せず、原則として `docs/archive/prototype-0.2/` へ移動する案を検討する。
  - benchmark結果、評価結果、速度試験は「歴史的検証結果」として残す。
  - READMEからは現行仕様と過去Prototypeを明確に分ける。

- [ ] **D-03 [P0] 新しいdocs構造を決定する**
  - 例:

```text
docs/
├─ requirements/
│  ├─ SYSTEM_REQUIREMENTS.md
│  └─ ACCEPTANCE_CRITERIA.md
├─ design/
│  ├─ ARCHITECTURE.md
│  ├─ DATA_MODEL.md
│  ├─ RETRIEVAL.md
│  ├─ GOOGLE_DRIVE_EXCHANGE.md
│  ├─ MCP.md
│  └─ CPC_UPDS_BOUNDARY.md
├─ operations/
│  ├─ OBJECT_WORKFLOW.md
│  └─ MIGRATION.md
├─ archive/
│  └─ prototype-0.2/
└─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
```

- [ ] **D-04 [P0] `src/cpc`の責務別再編を設計する**
  - 例:

```text
src/cpc/
├─ domain/        # Object / Relation / Facet / Version
├─ ingestion/     # Capture / Import / Normalize / Evidence
├─ storage/       # SQLite repository / migration
├─ retrieval/     # FTS / vector / hybrid / similarity
├─ exchange/      # Evidence Package / Result Import
├─ rendering/     # JSON -> Markdown等
├─ mcp/           # MCP adapter
├─ cli/           # CLI adapter
└─ application/   # use cases / orchestration
```

- [ ] **D-05 [P1] 既存モジュール移動方針を決める**
  - 大量renameとロジック変更を同一commitへ混在させない。
  - 「move only」と「behavior change」を別commit/PRに分割する。

- [ ] **D-06 [P1] `.local/` / generated / Google Drive exchangeデータのGit除外方針を更新する**
  - Object package、result、DB、vector index、生Sourceを誤commitしない。
  - Schema、sample、fixtureのみGit管理する。

- [ ] **D-07 [P1] 旧branch / PR / tag / releaseの整理ルールを決める**
  - 再設計開始前の未統合branchが存在する場合は、必要commitを救済してからclose/archiveする。
  - Prototype tagは履歴として保持する。
  - 再設計完了時に新しいversion境界を設定する。

**完了条件:** 新旧資産の配置ルールとGit移行手順が決まり、移動による履歴消失・誤削除を防げる。

---

# Phase E — Object Knowledgeデータモデル

- [ ] **E-01 [P0] Object schemaを設計する**
  - `objects`
  - `object_aliases`
  - `object_versions`
  - `object_relations`
  - type別schema拡張方式。

- [ ] **E-02 [P0] Semantic Facet schemaを設計する**
  - Character例: overall / personality / values / motivation / behavior / relationships / role / themes。
  - Work例: overall / themes / worldview / narrative / tone / characters / relationships。
  - Concept例: definition / properties / implications / related_concepts / examples。
  - type固有FacetをDB列へ固定しすぎない。

- [ ] **E-03 [P0] Evidence Link / Provenance schemaを設計する**
  - Object/Facet/RelationからSource/Evidenceまで遡れるようにする。
  - ChatGPT出力が存在しないSource IDを参照できないValidationを定義する。

- [ ] **E-04 [P0] Versioningを設計する**
  - Final Object Dataは上書きではなくVersion追加を基本とする。
  - `current_version`を明示する。
  - rollback可能にする。

- [ ] **E-05 [P1] JSON Schemaを作成する**
  - 共通Object Result schema。
  - type別extension schema。
  - ChatGPTへ渡す出力契約とImport Validatorで同一Schemaを利用する。

**完了条件:** ChatGPT出力、DB、検索、MCPの共通契約となるObject schemaが確定している。

---

# Phase F — Source / Evidenceパイプラインの簡略化

- [ ] **F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する**
  - Raw Sourceを正本Evidenceとして維持する。
  - 既存Provenanceを壊さない。

- [ ] **F-02 [P0] 標準パイプラインからFragment生成を外す**
  - `fragment`を必須工程から除外する。
  - 互換・研究用途として残すか完全廃止するかを決定する。

- [ ] **F-03 [P0] Object Evidence Retrievalを実装する**
  - name / alias / metadata / FTS / embeddingを組み合わせる。
  - 高Recall優先とし、最終的な意味判断はChatGPTへ渡す。

- [ ] **F-04 [P1] Evidence Selectionのtoken/size budgetを設計する**
  - 1 Objectで無制限に全Evidenceを出力しない。
  - Source多様性と関連性を維持しつつPackageを構築する。
  - 切り捨て理由を追跡可能にする。

- [ ] **F-05 [P1] ObjectとSource/Evidenceの明示linkを維持できるUI/CLIを設計する**
  - 自動検索候補 + 人間による追加/除外を許可する。

**完了条件:** 生成LLMなしでObjectに関連するEvidence Packageを作成できる。

---

# Phase G — Google Drive / ChatGPT交換ワークフロー

- [ ] **G-01 [P0] Object Evidence Package formatを確定する**
  - 例:

```text
<object-id>/
├─ manifest.json
├─ instructions.md
├─ current_object.json        # 既存versionがある場合
└─ evidence/
   ├─ source_001.md
   ├─ source_002.md
   └─ ...
```

- [ ] **G-02 [P0] `manifest.json` schemaを定義する**
  - object_id / type / name / aliases。
  - package version。
  - included sources/evidence IDs。
  - extraction timestamp。
  - expected result schema version。

- [ ] **G-03 [P0] ChatGPT用`instructions.md`を設計する**
  - Object type別の分析目的。
  - Fact / synthesis / interpretationの区別。
  - Evidence ID参照ルール。
  - Relation生成ルール。
  - 不明情報を創作しないルール。

- [ ] **G-04 [P0] Google Driveへのexport方式を実装する**
  - 初期版はローカルexport → Drive同期フォルダでも可。
  - CPC本体をGoogle Drive APIへ強く依存させるかは別途判断する。

- [ ] **G-05 [P1] Result受け取り運用を定義する**
  - `result.json`必須。
  - MarkdownをChatGPTに作らせる場合も正本にはしない。
  - 手動配置場所とimportコマンドを定義する。

**完了条件:** APIを利用せず、ユーザーがChatGPTとの手動工程を介して1 Objectを往復できる。

---

# Phase H — Result Validation / Import / Rendering

- [ ] **H-01 [P0] Result JSON Validatorを実装する**
  - JSON Schema validation。
  - object_id一致。
  - Source/Evidence ID存在確認。
  - Relation target存在確認または未解決参照として明示管理。
  - 不正field / schema version拒否。

- [ ] **H-02 [P0] Object Version Importを実装する**
  - Validation成功後のみDBへcommitする。
  - 既存currentを破壊しない。
  - Import run / timestamp / source packageを記録する。

- [ ] **H-03 [P1] Markdown Rendererを実装する**
  - DB/JSONから人間向けObject文書を生成する。
  - Markdownを編集正本にしない。

- [ ] **H-04 [P1] Diff / Review表示を実装する**
  - v1→v2の属性・Facet・Relation差分を確認できるようにする。
  - 手動承認を採用する場合の状態遷移を定義する。

**完了条件:** ChatGPT出力を壊れた状態で正本DBへ登録できず、過去versionへ戻れる。

---

# Phase I — 意味検索・類似検索

- [ ] **I-01 [P0] Embedding対象を再設計する**
  - Evidence embedding。
  - Object overall embedding。
  - Facet embedding。
  - 必要に応じRelation text representation。

- [ ] **I-02 [P0] 多言語Embedding Modelを比較する**
  - 日本語を含むCPC実データで評価する。
  - BGE-M3等を候補とするが、実測で決定する。
  - model/revision/dimensionをIndex metadataへ記録する。

- [ ] **I-03 [P0] Vector storageを決定する**
  - 第一候補: SQLite + sqlite-vec adapter。
  - pre-v1依存リスクをadapterで隔離する。
  - 専用Vector DBは必要性が確認されるまで導入しない。

- [ ] **I-04 [P0] Hybrid SearchをObject Knowledge向けに再実装/改修する**
  - FTS + vector。
  - type / facet / source等のfilter。
  - exact name/aliasをSemantic Searchより優先できるようにする。

- [ ] **I-05 [P0] `find_similar_objects`を実装する**
  - overall similarity。
  - facet指定similarity。
  - scoreとmatched facetを返せる構造。

- [ ] **I-06 [P1] Reranker導入を評価する**
  - 初期版MVPには必須としない。
  - retrieval品質評価で必要性を判断する。

- [ ] **I-07 [P0] 検索品質goldを作成する**
  - Character / Work / Conceptごとに日本語Queryを用意する。
  - lexical / semantic / hybrid / similarityを比較する。

**完了条件:** 「文字列が一致するObject」だけでなく、「意味・価値観・テーマ等が近いObject」を実用精度で取得できる。

---

# Phase J — MCP Knowledge Access Layer

- [ ] **J-01 [P0] Retrieval CoreとMCP Adapterを分離する**
  - MCPからSQLiteへ直接SQLを公開しない。
  - CLIとMCPが同じApplication/Retrieval APIを使用する。

- [ ] **J-02 [P0] MCP read toolsを定義する**
  - `search_objects`
  - `semantic_search_objects`
  - `find_similar_objects`
  - `get_object`
  - `get_objects`
  - `get_object_relations`
  - `get_object_evidence`
  - `search_evidence`
  - `build_context` または同等機能。

- [ ] **J-03 [P1] MCP Resourcesを定義する**
  - 例: `cpc://object/<id>`。
  - ToolとResourceの責務重複を整理する。

- [ ] **J-04 [P0] Context Builderを設計する**
  - roleplay / comparison / analysis / creative等の用途に応じて返すFacetを制御する。
  - LLM推論は行わず、決定論的なKnowledge selectionを担当する。

- [ ] **J-05 [P1] MCP write系はread系と分離する**
  - 初期MVPではread-onlyを第一候補とする。
  - 将来`propose_object`等を追加する場合もstagingへ限定する。

- [ ] **J-06 [P0] ローカルMCP Clientで受入試験する**
  - Local LLM HostからObject取得。
  - 複数Object取得。
  - Semantic Search / Similarity Search。
  - Context長制御。

**完了条件:** LLM/AgentがDB構造を知らずにCPC Knowledgeを取得できる。

---

# Phase K — CPC / UPDS連携試験

- [ ] **K-01 [P1] UPDSからCPC Objectを参照する最小ユースケースを定義する**
  - 「選択したCharacter群のvalues/personality/themesを取得する」等。

- [ ] **K-02 [P1] Stable Object ID参照を検証する**
  - CPC側version更新でUPDS Selection Event参照が壊れないこと。

- [ ] **K-03 [P1] CPCとUPDSのSemantic Indexを混同しないことを確認する**
  - CPC: World/Object Knowledge。
  - UPDS: Observation/Pattern/Preference Evidence。

- [ ] **K-04 [P2] UPDS向けContext/Profileを追加するか評価する**
  - CPC固有にUPDSロジックを埋め込まず、汎用Facet取得で不足する場合のみ追加する。

**完了条件:** UPDSがCPC Knowledgeを再解析せず再利用でき、CPCはUPDSなしでも独立している。

---

# Phase L — 旧Prototype移行・削除

- [ ] **L-01 [P0] Fragment table / code / CLIの移行方針を確定する**
  - 完全削除、legacy read-only、research-onlyのいずれかを決める。

- [ ] **L-02 [P0] Final Document table / code / CLIの移行方針を確定する**
  - Knowledge正本用途を廃止する。
  - Rendererとして再利用できる部分のみ残す。

- [ ] **L-03 [P1] 既存Prototype DB migrationを設計する**
  - Source / Snapshot / Evidence / Entity等、再利用可能なデータを保持する。
  - Fragment/Documentは必要ならlegacy tableまたはarchive DBへ退避する。

- [ ] **L-04 [P1] 旧benchmarkをarchiveする**
  - Fragment生成速度の比較を現行MVPの性能指標から外す。
  - 歴史的結果としてREADME/Archiveから参照可能にする。

- [ ] **L-05 [P0] 不要依存関係を削除する**
  - 標準運用から生成LLM Providerが不要になった場合、optional/research dependencyへ降格する。
  - Embedding dependencyは維持する。

**完了条件:** 旧Prototypeの高コスト処理が通常運用に残存していない。

---

# Phase M — CLI / 操作フロー

- [ ] **M-01 [P0] 新しいObject中心CLIを設計する**
  - `object add/list/show`
  - `object relate`
  - `package build`
  - `package export`
  - `result validate/import`
  - `search`
  - `similar`
  - `render`
  - `mcp serve` 等。

- [ ] **M-02 [P1] 旧CLIとの互換性を決定する**
  - deprecated warning期間を設けるか、Prototypeとして明示的に切るか判断する。

- [ ] **M-03 [P1] 1 Object標準手順を1ページで実行可能にする**
  - Object登録 → Evidence Package生成 → Drive → ChatGPT → Result Import → Search/MCP確認。

**完了条件:** 日常運用で内部DB操作を必要としない。

---

# Phase N — Test / Evaluation / Acceptance

- [ ] **N-01 [P0] Unit Testを新ドメインへ更新する**
  - Object / Relation / Facet / Version / Validation / Retrieval。

- [ ] **N-02 [P0] Integration Testを追加する**
  - Capture → Evidence → Package。
  - Result → Validate → Import → Version。
  - Import → Embed → Search。
  - MCP → Retrieval Core。

- [ ] **N-03 [P0] 実データVertical Sliceを作る**
  - Character 2件以上。
  - Work 2件以上。
  - Concept 2件以上。
  - 複数Sourceを持つObjectを含める。

- [ ] **N-04 [P0] 3つの代表AI利用ケースを受入試験する**
  1. Character DataをローカルLLMへ渡しRoleplayできる。
  2. Work Dataから意味的に類似する別Workを検索し、AIが比較説明できる。
  3. Concept A/Bを取得し、ローカルLLMが両概念を組み合わせたCharacter創作に利用できる。

- [ ] **N-05 [P0] 1 Object自動処理時間を測定する**
  - ChatGPT手動操作時間を除外する。
  - Package生成、Validation、Import、Embedding更新が目標時間内か確認する。

- [ ] **N-06 [P0] Retrieval品質を評価する**
  - Recall@K / MRR / nDCG等を必要に応じ利用する。
  - 類似検索は人間評価も併用する。

- [ ] **N-07 [P1] Failure / Recovery試験を行う**
  - 不正JSON。
  - 存在しないEvidence ID。
  - schema version不一致。
  - Embedding model変更。
  - MCP停止。
  - 部分Import失敗。

**完了条件:** 新しい目的に対する受入条件を満たし、Prototype時代の「Schema適合=品質合格」という評価誤認を避けられる。

---

# Phase O — Documentation / Release / Git cleanup

- [ ] **O-01 [P0] READMEを新CPCへ全面更新する**
  - CPCの目的。
  - 全体アーキテクチャ。
  - 1 Object標準フロー。
  - ChatGPT手動工程。
  - MCP利用例。

- [ ] **O-02 [P0] 現行設計書を更新する**
  - Architecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundary。

- [ ] **O-03 [P1] Prototype文書へArchived/Legacy表示を追加する**
  - 現行仕様と誤認されないようにする。

- [ ] **O-04 [P0] 再設計branchをmainへ統合する**
  - CI / tests / docs link / migration手順を確認してからmergeする。

- [ ] **O-05 [P1] 不要branchを削除する**
  - merge済み・救済済みであることを確認してから削除する。

- [ ] **O-06 [P1] Release / Tag方針を決定する**
  - Prototypeと新Knowledge Base版の境界をtagで明示する。
  - Breaking ChangeをRelease Noteへ記載する。

**完了条件:** mainが新設計を正本として示し、旧Prototypeと混同されない。

---

# 3. 推奨実施順序

```text
A  方針・棚卸し
↓
B  要件
↓
C  CPC/UPDS境界
↓
D  Repository/Git構造方針
↓
E  Object Data Model
↓
F  Evidence Pipeline簡略化
↓
G  Google Drive / ChatGPT Exchange
↓
H  Result Import / Versioning
↓
I  Semantic / Similarity Retrieval
↓
J  MCP
↓
K  UPDS連携
↓
L  Legacy移行
↓
M  CLI / 運用
↓
N  Test / Acceptance
↓
O  Documentation / Release / Cleanup
```

ただし実装では、E〜Jを一括で完成させるのではなく、まず次のVertical Sliceを優先する。

```text
既存Web Capture
 → Evidence
 → Character Object 1件
 → Evidence Package
 → ChatGPT手動処理
 → result.json import
 → Object DB
 → Facet embedding
 → semantic/similarity search
 → MCP get_object
```

このVertical Sliceが成立した後に、Work / Concept、UPDS連携、migration、最適化を拡張する。

---

# 4. 最初に実施すべきタスク

最優先は **A-01〜A-03 → B-01〜B-07 → C-01〜C-04** とする。

実装変更を先に始めると、旧PrototypeのEntity / Fragment / Final Document概念を新設計へ引きずる可能性がある。まず目的・責務・データ境界を確定し、その後 **E-01 Object schema** を起点として実装を再構成する。

Git上の物理的な大量移動（D-03〜D-05）は、要件・責務境界が確定した後に行う。