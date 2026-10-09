# Source Grounded Object Knowledge Base — Knowledge Base 再設計 引き継ぎ資料

更新日: 2026-10-09

## 1. 本書の目的

本書は、Source Grounded Object Knowledge Base（以下 SGOKB）の Knowledge Base 再設計について、これまでの議論で合意した背景・目的・採用方針・責務境界・技術方針を、別チャットへ引き継ぐための資料である。

以降は `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md` の各 Phase を原則として個別チャットで実施する。各チャットは、本書とタスク文書を最初に確認し、既決事項を不用意に再検討しないこと。

本書は詳細設計書ではない。ここに記載した内容を「現時点で合意済みの要件・設計方針」とし、個別 Phase で未確定事項を具体化する。

---

## 2. 再設計に至った背景

初回 Prototype は、Web Capture Bundleから Evidence を生成し、ローカル生成LLMで大量の Fragment を抽出し、Embedding / Hybrid Searchを経て Entityごとの最終文書を生成する構成だった。

実データ評価では、代表8 Captureだけで次の規模になった。

- Evidence: 737
- Fragment: 5246
- AI呼び出し: 1038
- AI応答待ち: 約5.1時間
- AI応答待ちが全体処理時間の99%以上
- Character Final: 約50万文字
- Work Final: 約378万文字

この結果から、次の問題が明確になった。

1. 全Evidenceをローカル生成LLMで細粒度解析するコストが大きすぎる。
2. Fragmentを大量に作ること自体が目的化し、最終用途に対して過剰である。
3. 巨大なFinal Documentは人間にもAIにも日常利用しにくい。
4. 高性能なChatGPTを利用できるのに、API自動化へこだわることでローカルLLMに高度な意味理解を負わせていた。
5. SGOKBの本来の目的は「文書を生成すること」ではなく、「対象について再利用可能な知識を蓄積すること」にある。

したがって、Prototypeの自動化率を高める方向ではなく、人間・通常プログラム・Embeddingモデル・ChatGPTの役割を明確に分離する方向へ再設計する。

---

## 3. SGOKBで実現したい本質的な目的

SGOKBの目的は、次のように捉える。

> 自分が関心を持って収集したキャラクター・作品・概念などを、Web上の根拠まで追跡可能な「意味のあるObject」として長期保存し、将来どのAIからでも検索・比較・参照・創作材料として利用できる、モデル非依存の外部知識記憶を構築する。

SGOKBは単なるCharacter Document Generatorではなく、**Curated Semantic Object Knowledge Base** を目指す。

主な利用例:

- Character情報をAIへ渡してRoleplayする。
- あるWorkに意味的に類似する別Workを検索・比較する。
- 複数ConceptをAIへ渡して新しいCharacterや設定を創作する。
- Character / Work / Concept間のRelationを辿る。
- Semantic Facet単位で類似性を調べる。
- UserPreferenceDiscoverySystem（UPDS）がSGOKB Knowledgeを利用し、ユーザー自身の潜在的嗜好・価値観を分析する。

---

## 4. 再設計後の基本アーキテクチャ

```text
Web
 ↓
Source Capture / Import
 ↓
Source / Evidence Store
 ↓
Object Evidence Retrieval
  ├─ metadata
  ├─ name / alias
  ├─ FTS
  └─ semantic retrieval
 ↓
Object Evidence Package
 ↓
Google Drive
 ↓  手作業
ChatGPT（APIを標準利用しない）
 ↓
Structured Object Result
 ↓
Schema / Provenance Validation
 ↓
Object Knowledge Store
  ├─ Object
  ├─ Facet
  ├─ Relation
  ├─ Version
  └─ Evidence Link
 ↓
Lexical / Semantic / Similarity / Relation Retrieval
 ↓
MCP Knowledge Access Layer
 ↓
ChatGPT / Local LLM / UPDS / Other Clients
```

### 基本思想

- Raw Source / Evidenceは一次資料として保持する。
- Object KnowledgeはEvidenceから派生するが、Evidenceそのものとは分離する。
- 高度な意味理解・統合は原則としてChatGPTへ任せる。
- SGOKB内部の自動処理では、生成LLMを必須にしない。
- Embeddingは生成LLMとは別物として積極利用する。
- Google Driveは交換場所であり、正本ではない。
- 正本はローカルのObject Knowledge DBとする。
- AI固有の仕様をSGOKB Coreへ持ち込まず、将来別AIへ交換可能にする。

---

## 5. Object中心モデル

SGOKBの中心概念は `Object` とする。

初期Object Type:

- `Character`
- `Work`
- `Concept`

将来、Person / Organization / Place等を追加できるよう、共通Object + `object_type` を基本とする。

最低限の共通属性候補:

- `object_id`
- `object_type`
- `name`
- `aliases`
- `status`
- `created_at`
- `updated_at`
- `current_version`

詳細SchemaはPhase Eで確定する。

### SourceとObject

SourceとObjectは一対一ではなく多対多とする。

1つのWebページには複数Objectが含まれ得る。また、1つのObjectは複数Sourceを根拠に持つ。

```text
Source A ─┬─ Character X
          ├─ Work Y
          └─ Concept Z

Source B ─── Character X
```

---

## 6. Semantic Facet

Object全体を1本の長文としてのみ管理しない。

Object Typeごとに、意味的な観点を `Semantic Facet` として分離可能にする。

候補例:

### Character

- overall
- personality
- values
- motivation
- behavior
- relationships
- role
- themes

### Work

- overall
- themes
- worldview
- narrative
- tone
- characters
- relationships

### Concept

- definition
- properties
- implications
- related_concepts
- examples

Facetを固定DB列へ焼き込みすぎず、将来拡張可能にする。

意味検索・類似検索では、Object全体だけでなくFacet単位のEmbeddingを利用できることを目指す。

これにより、例えば「性格が似る」と「価値観が似る」を区別する。

---

## 7. Source / Evidenceと高度解析の分離

Prototypeでは、全Evidenceを生成LLMへ渡してFragment化していた。

再設計後は、この工程を標準パイプラインから外す。

```text
旧:
Evidence
 ↓
Local Generative LLM
 ↓
Fragment
 ↓
Final Document

新:
Evidence
 ↓
Deterministic + Retrieval
 ↓
Objectに関連しそうなEvidenceを高Recallで選択
 ↓
ChatGPT
 ↓
Structured Object Result
```

Object Evidence Retrievalでは、以下の組み合わせを使用する。

- Object name / alias
- Source metadata
- SQLite FTS5
- Embedding semantic search
- 必要なら将来reranker

この段階では、「この文章はCharacterの価値観を示す」等の高度な意味判断を無理に行わない。

最終的な意味理解はChatGPTに任せる。

### Fragmentの扱い

Fragmentは標準Knowledge Modelではなくなる。

既存Fragment機能を研究・比較用途として残すか、完全廃止するかはPhase F / Lで判断する。

---

## 8. ChatGPTの位置づけ

ChatGPT APIは標準処理に使用しない。

ChatGPT Web/DesktopとGoogle Driveを利用し、人間が明示的に処理を依頼するHuman-in-the-loop方式を採用する。

想定フロー:

```text
SGOKB
 ↓
Evidence Package生成
 ↓
Google Driveへ配置
 ↓
人間がChatGPTへ分析を依頼
 ↓
ChatGPTが定義済みSchemaでResultを生成
 ↓
ResultをSGOKBへ戻す
 ↓
Validation
 ↓
DBへVersion追加
```

1 Objectあたり「SGOKB側の自動処理」は概ね10分以内を目標とする。

人間がChatGPTを操作する時間は、この10分目標から除外する。

自動化率を最大化することは要件ではない。

---

## 9. Google Driveの役割

Google DriveはSGOKBとChatGPT間の交換場所として利用する。

正本にはしない。

例:

```text
Source Grounded Object Knowledge Base/
└─ exchange/
   └─ <object-id>/
      ├─ manifest.json
      ├─ instructions.md
      ├─ current_object.json
      └─ evidence/
         ├─ source_001.md
         ├─ source_002.md
         └─ ...
```

ChatGPTから返すResultも、同じ交換領域へ置ける構造を検討する。

具体的なディレクトリ、命名、同期・回収方式はPhase Gで決定する。

---

## 10. Object Resultと正本

最終Knowledgeは長大なMarkdown文書を正本としない。

**Structured JSONを機械向け正本**とする。

Markdown等の人間向け表示はJSONから生成する派生物とする。

Object Resultには少なくとも以下を持てる構造を検討する。

```text
Object
├─ identity
├─ summary
├─ facets
├─ relations
├─ evidence_links
└─ generation / provenance metadata
```

ResultはそのままDBへ投入せず、SGOKB側で形式的Validationを行う。

Validation例:

- JSON Schema適合
- object_id存在確認
- source/evidence ID存在確認
- Relation先Object存在確認
- 必須項目確認
- 不正フィールド拒否

「内容が意味的に正しいか」をローカルLLMで自動判定することは標準要件としない。

---

## 11. Versioning / Provenance

最終Object Dataは原則として上書きしない。

```text
Object X
├─ version 1
├─ version 2
└─ version 3 ← current
```

新Source追加や再分析時は新Versionを生成し、過去Versionへ戻れるようにする。

Object / Facet / Relationから、根拠となるSource / Evidenceへ遡れることを維持する。

ChatGPTの出力も絶対的事実ではなく、Evidenceから作られた派生Knowledgeとして扱う。

---

## 12. 検索要件

以下は必須とする。

- Lexical Search
- Semantic Search
- Object Similarity Search
- Relation Search

Facet単位のSimilarity Searchも設計対象とする。

Evidence Searchは監査・再分析用途として残す。

### Hybrid Search

Embeddingだけでは固有名詞に弱く、FTSだけでは意味的類似を拾えないため、FTS + Vectorを組み合わせる。

SGOKB Prototypeに既存のLexical / Semantic / Hybrid Search基盤は再利用候補とする。

### Embedding

ローカル生成LLMとは分離する。

Embedding専用モデルを使用し、日本語を含む多言語性能を評価して選定する。

BGE-M3等は候補であり、現時点で採用確定ではない。

Vector専用DBの導入を必須とはしない。

SQLiteを正本DBとし、sqlite-vec等をAdapter経由で利用する案を第一候補とするが、具体的ライブラリはPhase Iで評価・決定する。

---

## 13. MCPの役割

MCP ServerはAIそのものではない。

SGOKB Knowledgeを、ChatGPT・ローカルLLM・Agent・UPDS等が標準化された方法で検索・取得するための **Knowledge Access Layer** とする。

MCPからDBテーブルを直接公開するのではなく、SGOKB Retrieval Coreを介する。

```text
SQLite / Index
      ↓
SGOKB Retrieval Core
      ├─ CLI
      ├─ Application
      └─ MCP Adapter
```

想定Core API:

- `search_objects()`
- `semantic_search_objects()`
- `find_similar_objects()`
- `get_object()`
- `get_objects()`
- `get_object_relations()`
- `get_object_evidence()`
- `build_context()`

MCP Tool名・Resource URI等の具体仕様はPhase Jで決定する。

### MCPからLLMへKnowledgeを提供する考え方

例えばRoleplayの場合、MCPがRoleplayを実行するのではない。

```text
User
 ↓
LLM
 ↓ MCP Tool call
SGOKB
 ↓
Character Knowledge
 ↓
LLM Context
 ↓
LLMがRoleplay
```

「検索・Context提供」はSGOKB、「推論・創作・説明」は利用側LLMの責務とする。

### AIからSGOKBへの書き込み

初期版MCPはRead / Search中心とする。

将来的な書き込み機能は、Final DBへ直接自由書き込みさせず、Draft / Staging / Validationを経由する設計を検討する。

---

## 14. SGOKBとUPDSの責務分割

両者は統合しない。

### SGOKB = World / Object Knowledge Layer

問い:

> Xとは何か。Xにはどのような特徴・意味・関係があるか。

所有するもの:

- Character
- Work
- Concept
- Object attribute
- Semantic Facet
- Object Relation
- Source / Evidence
- Object Embedding

SGOKBには「ユーザーがこれを好き」という意味を入れない。

### UPDS = Personal Inference Layer

問い:

> ユーザーはなぜXを選ぶのか。複数の選択にどのような無意識の傾向があるか。

所有するもの:

- Selection Event
- Semantic Observation（必要に応じてSGOKB Knowledgeを参照）
- Cross-source / Cross-object Pattern
- Preference Hypothesis
- Alternative Explanation
- User-oriented Evidence Set

UPDSはSGOKBをKnowledge Providerとして利用可能とする。

SGOKBはUPDSを知らなくても単独成立させる。

依存関係は原則一方向とする。

```text
SGOKB
 ↓ MCP
UPDS
```

### Conceptの扱い

Conceptそのものの定義・Relation・EmbeddingはSGOKBで管理する案を第一候補とする。

UPDS側はSGOKB Concept IDを参照し、「ユーザーがConceptを好む可能性」のようなPreference Hypothesisを持つ。

詳細契約はPhase Cで確定する。

---

## 15. 既存SGOKB資産の扱い

全面作り直しを前提としない。

### Keep候補

- Web Page Capture Chrome extension
- Native Host
- Raw Import
- Source / Snapshot
- Evidence extraction
- checksum / duplicate detection
- Provenance
- SQLite基盤
- FTS
- Embedding provider abstraction
- Lexical / Semantic / Hybrid Searchの一部
- Evaluation / fixtureの一部

### Modify候補

- Entity → Object
- Search target / Facet
- CLI
- DB schema
- package/module structure
- evaluation strategy

### Replace候補

- Fragment中心Knowledge Model
- 巨大Final Documentを中心とする生成処理

### Retire候補

- 全Evidenceへの高コスト生成LLM Fragment抽出を標準運用する設計
- Fragment生成性能を最終目的とするbenchmark

正式分類はPhase Aで実コード・DB依存を確認して確定する。

---

## 16. Git / Repository再編方針

大規模なrenameとbehavior changeを同一commitへ混在させない。

設計が確定する前に大量ファイル移動を行わない。

候補docs構造:

```text
docs/
├─ requirements/
├─ design/
├─ operations/
├─ archive/
│  └─ prototype-0.2/
├─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
└─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
```

候補code構造:

```text
src/sgokb/
├─ domain/
├─ ingestion/
├─ storage/
├─ retrieval/
├─ exchange/
├─ rendering/
├─ mcp/
├─ cli/
└─ application/
```

これらは「候補構造」であり、Phase Dで確定する。

Prototypeの過去評価・benchmark・設計文書は、原則削除せずarchiveし、歴史的検証結果として残す。

---

## 17. 初期Vertical Slice

再設計実装では、最初から全Object Type・全MCP Toolを実装しない。

まず次の1本を成立させる。

```text
既存Web Capture
 → Evidence
 → Character Object 1件
 → Evidence Retrieval
 → Evidence Package
 → Google Drive
 → ChatGPT手動分析
 → result.json
 → Validation / Import
 → Object DB
 → Facet Embedding
 → Semantic / Similarity Search
 → MCP get_object
```

このVertical Sliceが成立した後に、Work / Concept、Relation拡張、UPDS連携へ進む。

---

## 18. 現時点で確定したこと

以下は、以後のPhaseで特別な理由なく覆さない。

1. SGOKBの中心はDocumentではなくObject Knowledgeである。
2. Character / Work / Conceptを初期Object Typeとする。
3. Raw Source / Evidenceを保持し、Provenanceを維持する。
4. SourceとObjectは多対多とする。
5. 全Evidenceの生成LLM Fragment化を標準パイプラインから外す。
6. ローカル生成LLMへ重い意味抽出を極力担当させない。
7. EmbeddingによるSemantic Search / Similarity Searchは必須とする。
8. Lexical Searchも保持し、Hybrid Retrievalを基本とする。
9. 高度なObject統合はChatGPTを利用する。
10. ChatGPT APIは標準運用に使用しない。
11. Google Drive + ChatGPTの手動工程を正式なWorkflowとして扱う。
12. Google Driveは交換領域であり、Knowledgeの正本ではない。
13. Structured JSONをObject Knowledgeの機械向け正本とする。
14. Markdownは派生表示とする。
15. Object KnowledgeはVersioningする。
16. Object / Facet / RelationからEvidenceへ遡れるようにする。
17. MCPをKnowledge Access Layerとして提供する。
18. MCPは推論・創作を担当せず、検索・Context提供を中心とする。
19. SGOKBとUPDSは別プロジェクトとして維持する。
20. SGOKBはWorld/Object Knowledge、UPDSはPersonal Inferenceを担当する。
21. SGOKB → UPDSの一方向依存を基本とし、SGOKB単体で成立させる。
22. ConceptそのものはSGOKB所有を第一候補とする。
23. SQLiteを正本DBとして維持する方向を基本とする。
24. Vector専用DBやGraph DBを初期要件とはしない。
25. 1 ObjectあたりのSGOKB自動処理は概ね10分以内を目標とし、人間操作時間は除外する。
26. 自動化率の最大化を目的にしない。
27. 既存SGOKB資産を可能な限り再利用し、全面rewriteを前提としない。
28. 大規模Git移動は責務・Schema決定後に行う。

---

## 19. 現時点で未確定の主要事項

以下は今後のPhaseで決定する。

- Object共通Schemaの詳細
- Object Type別Schema拡張方式
- Facetの正式一覧と拡張方式
- Relation schema / relation type管理
- Evidence Package形式・容量上限
- ChatGPTへ渡すinstructions / prompt
- Google Driveの具体的なフォルダ・同期方式
- Result JSON Schema
- Import / Validation規則
- Version lifecycle
- Object更新時の全体再生成 / 差分更新方針
- Embeddingモデル
- Vector index実装（sqlite-vec等）
- Hybrid scoring / reranking
- Similarityの定義・Facet weighting
- MCP Tool / Resource / Promptの具体仕様
- MCP transport / deployment方式
- AIからSGOKBへのwrite機能を初期版に含めるか
- ConceptのSGOKB/UPDS間の最終契約
- 既存Fragment / Final関連コードを残す範囲
- DB migration方針
- Repository最終フォルダ構造
- Release version境界

未確定事項を、既決事項と混同しないこと。

---

## 20. Phase実施ルール

各Phaseを別チャットで実施する際は、次を原則とする。

1. 最初に本書と `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md` を読む。
2. 対象Phaseと、それ以前のPhaseで確定済みの成果物を確認する。
3. 既決事項を理由なく再検討しない。
4. 対象Phaseの論点が大きい場合は、実装前に設計判断を文書化する。
5. 将来Phaseの詳細を先回りして過剰設計しない。
6. 既存コードを変更する前に、再利用可能な実装を確認する。
7. move/renameとbehavior changeを可能な限り分離する。
8. 変更後は対応ドキュメント・テスト・TASKの状態を同時に更新する。
9. Phase完了時に、決定事項・未決事項・次Phaseへの入力を明記する。
10. Phase間で仕様が変わった場合は、本書も更新する。

---

## 21. 各新規チャットで使用する開始指示の基本形

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。

まずGitHubリポジトリの以下を確認し、これまでの合意事項と現在のタスクを把握してください。
- docs/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md

既決事項は維持し、今回の対象Phaseに必要な範囲だけを具体化してください。

今回実施するタスク:
Phase X — <Phase名>

Phase内のタスクを確認し、必要な調査・設計・実装・テスト・ドキュメント更新まで実施してください。
Phase完了時には、決定事項、実施内容、未決事項、次Phaseへの引き継ぎを報告してください。
```

特定のTaskだけ行う場合は、最後を次のようにする。

```text
今回実施するタスク:
X-YY [Priority] <Task名>
```

---

## 22. 関連文書

- `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - 再設計の全Phase / Task一覧。
- `README.md`
  - 現行Prototypeの概要。再設計完了までは旧実装の説明を含む。
- `docs/DEVELOPMENT_STATUS.md`
  - Prototype 0.2の実データ評価と現状。
- `docs/KNOWLEDGE_PIPELINE_EFFICIENCY_REDESIGN.md`
  - Fragment/LLM処理肥大化を受けた外部RAG事例との比較調査。
- `UserPreferenceDiscoverySystem/docs/PROJECT_CONCEPT.md`
  - UPDSの目的、Selection Event / Observation / Pattern / Preference Hypothesisの設計思想。

---

## 23. 現在地点

要件の概要整理と、再設計全体のPhase/Task分解まで完了したものとする。

まだ新Knowledge Baseの詳細要件・DB Schema・フォルダ構造・実装変更は確定していない。

次の作業は `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md` の **Phase A — 方針確定・既存資産棚卸し** から開始する。
