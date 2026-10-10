# Source Grounded Object Knowledge Base — Knowledge Base 再設計 引き継ぎ資料

更新日: 2026-10-11

## 1. 本書の目的

本書は、Source Grounded Object Knowledge Base（以下 SGOKB）の Knowledge Base 再設計について、これまでの議論で合意した背景・目的・採用方針・責務境界・技術方針を、別チャットへ引き継ぐための資料である。

以降は `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md` の各 Phase を原則として個別チャットで実施する。各チャットは、本書とタスク文書を最初に確認し、既決事項を不用意に再検討しないこと。

本書は詳細設計書ではない。ここに記載した内容を「現時点で合意済みの要件・設計方針」とし、個別 Phase で未確定事項を具体化する。

### 1.1 最新進捗 — Phase B要件定義完了（B-02〜B-07）

B-02のObject Identity要件は完了済み。正本は `docs/requirements/OBJECT_REQUIREMENTS.md`。ObjectをSource / Document / Versionから独立した安定Identityとし、`object_id`はname・path・Source・Version等から独立させる。

その後、初期分類 `Character` / `Work` / `Concept` だけでは将来収集するWeb Sourceと対象Knowledgeの想定が不足し得るため、B-03前にObject分類を精緻化するB-02A〜B-02Dを追加した。詳細計画は `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md` を正本とする。

B-02A〜B-02Dは2026-10-10時点で完了している。B-02Cでは`Primary Class + Additional Classes + hierarchical Class Registry`方式を採用し、B-02Dでは正式Class hierarchy、Object / Facet / Relation / value / Source境界、初期Class Registry seed集合、fallback条件を確定した。正本は`docs/requirements/OBJECT_TYPE_BOUNDARIES.md`である。

Object Type Refinement series完了後、B-03 Source / Evidence要件、B-04 Object Result要件、B-05 Search / Retrieval要件、B-06 Human / Automation Workflow要件、B-07 Non-functional Requirementsまで完了した。Source / Evidenceの正本は`docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`、Object Resultの正本は`docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`、検索要件の正本は`docs/requirements/SEARCH_REQUIREMENTS.md`、Workflow責務境界の正本は`docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`、非機能要件の正本は`docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`である。B-07ではlocal-first、canonical / derived data分離、Provenance integrity、backup / restore、external egress security、failure recovery、Reference Environmentと性能Acceptanceを確定した。これによりPhase Bの要件定義更新は完了した。次に実施するのはPhase C — SGOKB / UPDS責務境界である。

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

Object IdentityとClassificationは分離する。Classificationは次を正本概念とする。

- `primary_class`: 必須1件
- `additional_classes`: 0件以上
- hierarchical Class Registry

`Character` / `Work` / `Concept`は主要ユースケースの基準Classとして維持するが、初期Class Registryをこの3 Classだけへ限定しない。B-02Dで正式なObject Classとして採用されたClassは、原則として通常のObjectデータ投入前にRegistryへ登録する。

Class Registryへの包含とClass固有Facet / UI / validation / search等の専用機能実装優先度は別軸とする。専用機能が未実装でも、共通Object contractで正しいClassを保持できなければならない。

最低限の共通属性候補:

- `object_id`
- `primary_class`
- `additional_classes`
- `name`
- `aliases`
- `status`
- `created_at`
- `updated_at`
- `current_version`

Objectの論理要件・Identity判断は `docs/requirements/OBJECT_REQUIREMENTS.md`、Classification modelは`docs/requirements/OBJECT_TYPE_MODEL.md`を正本とする。SQL table構成、Class Registryの物理Schema、seed方式はPhase Eで確定する。

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
SourceGroundedObjectKnowledgeBase/
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

B-05で検索要件を確定した。正本は`docs/requirements/SEARCH_REQUIREMENTS.md`とする。

主要決定:

- Object Identity Lookup、Object Lexical / Semantic / Hybrid Search、Object / Facet Similarity、Relation Search、Evidence Searchを別責務とする。
- 通常free-text Object検索はHybridを基本とする。
- accepted検索可能Knowledge Statementは標準で個別Embeddingし、Object / Facet / Statementのmulti-representationをSemantic candidate generationへ利用する。通常Object SearchはStatement-level hitを内部候補として扱い、結果を原則`1 Object = 1件`へ集約する。
- exact name / alias等のIdentity matchをSemantic候補で埋没させない。
- active Object + current accepted Knowledgeを通常既定scopeとし、archived / historicalは明示指定する。
- Object overall similarityは同じPrimary Classを既定candidate scopeとし、cross-classは明示的に拡張する。
- Object / Facet / Statement representationを別用途として併用し、Facet similarityを正式要件とする。Facet欠落時にoverallへsilent fallbackしない。
- Relation Searchは構造化1-hop traversalを必須とし、bounded multi-hopへ拡張可能とする。
- EvidenceはObject Knowledgeとは別にLexical / Semantic Searchし、Source metadata、Object association、active/effective / historical generation、Provenance integrityでfilterできる。
- conflict中のgrounded Statementは検索可能だが、gap / insufficient evidence / unresolved reference / Registry proposalは通常Semantic Searchへ混ぜない。
- FTS / Vector Indexは再構築可能な派生物であり、Embedding Space / representation builder version / Knowledge Version / Evidence generationを追跡する。Vector backendはAdapterで交換可能にする。
- Statement-level hitのObject Aggregation、representation hashによるVector reuse、Exact / sqlite系 / LanceDB / Qdrant比較をPhase Iで実施し、実測前にbackendを固定しない。
- search scoreはrelevance / similarity signalであり、truth / confidence / Source trustではない。
- Object / Knowledge hitからgrounding Evidence / Sourceへ追跡できる。

Phase IではObject / Facet / Statement / Evidence Search Representation、Embedding Provider / model、VectorIndexAdapter / backend、Object Aggregation、Hybrid fusion、Similarity、rerankerを実測で具体化する。

---

## 12.1 人間工程 / 自動工程の責務境界

B-06で標準WorkflowのHuman / Automation boundaryを確定した。正本は`docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`とする。

主要決定:

- 「自動」は無人で何でも進める意味ではなく、人間が開始した後に次のdecision boundaryまでlocal処理を継続する意味とする。
- Source採用、Persistent Object Identity確定、External Export、authoritative Result Import、Registry proposal適用を人間の明示decisionとする。
- Capture済みBundleのImport / Normalize / Evidence生成、Package Build、Result machine Validation、Import後のSearch Representation / Embedding / Index更新は自動処理へ寄せる。
- Package Buildはlocal staging、Package Exportはexternal data egressとして分離する。Drive同期directoryへのwriteもExternal Exportとみなす。
- Capture / Importした事実をGoogle Drive / ChatGPT / 外部API等への送信許可とみなさない。
- 外部Embedding / reranker等へKnowledge textを送る場合もExternal Processingとして扱う。
- Google Drive → ChatGPT → result.json返却は正式なHuman-in-the-loop工程とし、1 Object local automatic processingの10分目標から除外する。
- Result Validation成功を自動Import許可とみなさない。normal Resultはexplicit Importを人間control pointとするが、全Statementの逐語reviewは必須にしない。
- stale Resultは通常Importをblockし、partial / limited Resultはreview-requiredを既定とする。Registry proposalはKnowledge Importと分離してreviewする。
- accepted Version commit後のObject / Facet / Statement Embedding、Vector / Lexical Index、Markdown等の派生更新は自動化し、派生Index失敗で正本Knowledgeを失わない。
- 10分目標にはPackage Build等のpre-analysis local segmentとValidation / Import / Embedding / Index等のpost-analysis local segmentを含め、人間操作・ChatGPT生成待ち・external network待ちは除外する。

具体的CLI、state machine、Drive path、persistent export policy、review severity等はPhase G / H / Mで具体化する。非機能横断要件はB-07で確定済みである。

---

## 12.2 非機能要件

B-07でSGOKBのlocal-first / integrity / recovery / performance契約を確定した。正本は`docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`とする。

主要決定:

- SQLite、Raw、Object Knowledge Version、Evidence / Provenanceを優先保全対象とし、Search Representation、Embedding、Vector Index、Markdown、Package等をrebuildable derived layerとして分離する。
- Internet / ChatGPT / Google Drive / MCP / Vector backendが利用不能でも、canonical DBと利用可能なlocal read / Lexical機能を維持する。
- Vector Index failure時はstale / failedを検出し、古いVectorをcurrentとしてsilent利用しない。可能な場合はLexicalへgraceful degradationする。
- local provider failure時にexternal cloud providerへsilent fallbackしない。
- accepted Object Knowledge Versionを論理immutableとし、process interruptionでincomplete Versionを`current_version`が指さないtransaction / recoveryを要求する。
- Raw / Evidence / Version / accepted Result provenanceは参照中に自動purgeしない。Hard deleteはdependency preview / warning / auditを伴う管理操作とする。
- canonical backupの初期目標はRPO 24時間、同等環境でのcanonical restore RTO 4時間。default retention基準はdaily 7世代 + weekly 4世代以上とする。
- local-onlyをsecurity defaultとし、外部送信ではdata minimizationと`allow / review_required / blocked`相当のexport decisionを扱う。credential / secretをPackageやstandard logへ含めない。
- Primary supported environmentはWindows 11。Docker / always-on serverをCore必須にしない。
- Reference Workstationはi5-13600KF / 128 GB RAM / RTX 4090 24 GB。Standard Objectのlocal automated segmentはp95 10分以内、Large Objectは別profileでp95 20分targetとする。
- interactive warm queryの初期p95 targetはexact lookup 250 ms、Lexical 1 s、Semantic / Hybrid / Similarity 3 s、1-hop Relation 1 sとする。
- benchmarkはcommit、schema、hardware、workload、Embedding Space、backend、cold / warm、retry等を記録する。
- Phase Nではoffline、crash、disk full、broken provenance、Index loss / rebuild、backup restore、egress、secret redaction、provider failureをAcceptanceとして検証する。

これによりPhase Bの要件定義更新は完了した。以降のPhaseはB-01〜B-07を入力契約として具体化する。

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
 → Object / Facet / Statement Embedding
 → Semantic / Similarity Search
 → MCP get_object
```

このVertical Sliceが成立した後に、Work / Concept、Relation拡張、UPDS連携へ進む。

---

## 18. 現時点で確定したこと

以下は、以後のPhaseで特別な理由なく覆さない。

1. SGOKBの中心はDocumentではなくObject Knowledgeである。
2. Object ClassificationはPrimary Class + Additional Classes + hierarchical Class Registryとし、具体境界は`OBJECT_TYPE_BOUNDARIES.md`を正本とする。
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
29. ObjectはSource / Document / Knowledge Versionから独立した安定Identityとする。
30. `object_id`はname / alias / path / Source / Version / Project名 / Classification等から独立させる。
31. Classificationは`primary_class` 1件 + `additional_classes` 0件以上 + hierarchical Class Registryを正本概念とする。
32. name / aliasは一意でなく、同名別Objectを許容する。
33. Object lifecycle statusは最低限active / archivedを持ち、Knowledge生成状態やconfidenceと分離する。
34. Knowledge未生成Objectを許容し、`current_version`が空の状態を正常とする。
35. 同一Characterの複数Work登場は原則1 Object + Relationとし、別continuity等は別Objectにできる。
36. Class固有Knowledgeは共通Object identityへ固定列として詰め込まず、Facet等の拡張構造へ分離する。
37. B-02Dで正式採用したObject Classは、原則として通常データ投入前に初期Class Registryへ登録する。
38. Class Registryへの包含とClass固有Facet / UI / validation / search等の専用機能実装優先度を分離する。
39. Class未登録を理由に、意味的に異なる`Concept` / `Work` / `Character`等へObjectを自動fallbackさせない。
40. Source IdentityはURL / title / path / content hashから独立させ、URL等はlocatorとして扱う。
41. Source / Snapshot / Raw Artifact / Normalized Run / Evidenceを別責務とし、過去世代のProvenanceを保持する。
42. Source classificationは単一`source_type`へ混在させず、Source本体のresource type / media type / document genre / publisher kind / provider / page purpose等と、Source↔Object association上のsubject relationshipへ分離する。
43. Evidenceは単一Snapshotへ必ず遡れる意味非改変の検索・引用単位とし、LLM summary / synthesis / inferenceを一次Evidenceへ自動昇格させない。
44. Evidence StoreとObject Evidence Packageを分離し、PackageをSource of truthとしない。
45. Capture / Importしたこと自体をGoogle Drive / ChatGPT等への外部export許可とはみなさない。
46. Object Resultは1 Object単位のEvidence-groundedな次期Object Knowledge Version候補であり、AI出力を直接正本へ昇格させない。
47. Structured JSONを機械向け交換正本とし、Import後はローカルObject Knowledge Versionを永続正本、Markdownを派生表示とする。
48. Resultはtarget Object / Evidence Package / base Versionへbindし、stale Resultをsilent overwriteしない。
49. Knowledge StatementはResult / Version内部のgrounding単位であり、旧Fragmentのような全Evidence大量抽出対象・coverage KPIにはしない。
50. Statement / structured attribute / Relationは原則Evidence IDへgroundingし、標準workflowでは入力Package membershipまでValidationする。
51. derivationは`direct_statement` / `synthesis` / `interpretation` / `reported_view`相当を区別し、`reported_view`はattributionを保持する。数値confidenceを必須にしない。
52. conflict / insufficient evidence / gap、unresolved Object reference、Registry proposalを確定Knowledgeから分離する。
53. 初期標準Resultはfull Knowledge snapshotとし、Persistent Version IDはSGOKB Importer側で発行する。
54. Schema / ID / grounding Validation成功は意味品質・真実性の保証を意味しない。
55. Knowledge記述言語とEvidence原文言語を区別し、時間依存するStatement / attribute / Relationには必要に応じてtemporal scopeを持てるようにする。
56. 通常free-text Object検索はLexical + SemanticのHybridを基本とし、通常結果は原則1 Object = 1件へ集約する。
57. active Object + current accepted Knowledgeを通常検索の既定scopeとし、historical / archivedは明示scopeへ分離する。
58. Object overall similarityとFacet similarityを別機能とし、Facet欠落時にoverallへsilent fallbackしない。
59. accepted検索可能Knowledge Statementは標準で個別Embeddingし、Object / Facet / Statementのmulti-representation retrievalを行う。
60. Statement-level hitはObject単位へ集約し、Statement数の単純合計でObjectを無制限boostしない。
61. Relation Searchは構造化edge traversal、Evidence SearchはObject Knowledgeとは別のLexical / Semantic retrievalとして扱う。
62. gap / insufficient evidence / unresolved reference / Registry proposalを通常Semantic Searchへ混ぜない。
63. Search Representation / Embedding / Vector Indexは正本ではなく再生成可能な派生物とし、search scoreをtruth / confidenceとして扱わない。
64. Vector backendはAdapterで交換可能にし、SQLite canonical Knowledgeから再構築可能にする。
65. SGOKBの自動処理は、人間が開始した後に次のdecision boundaryまでlocal処理を継続する意味とし、無制限な無人判断とは区別する。
66. Source採用、Persistent Object Identity確定、External Export、authoritative Result Import、Registry変更はHuman Decision boundaryとする。
67. Package Buildはlocal staging、Package Exportはexternal data egressとして分離し、Capture / Importを外部送信許可とみなさない。
68. Google Drive / ChatGPT標準Knowledge生成は正式なHuman-in-the-loop工程とし、人間操作・ChatGPT待ち・external network待ちは1 Object local automatic processing 10分目標から除外する。
69. Result Validation成功とImportを分離し、normal Resultはexplicit Importを要求する一方、全Statement逐語reviewを必須にしない。staleはblock、partial / limitedはreview-requiredを既定とする。
70. Registry proposal / unresolved referenceはKnowledge Importの副作用として自動適用・自動Object化しない。
71. accepted Version commit後のSearch Representation / Object・Facet・Statement Embedding / Index / derived renderingは自動更新対象とする。
72. 派生Index更新失敗でaccepted Knowledgeを破壊せず、stale / pending / failedを検出してretry / rebuild可能にする。
73. 外部Embedding / reranker等へtextを送る場合もExternal Processingとして明示的なdata egress policyの対象とする。
74. SGOKB Coreはlocal-firstとし、Internet / cloud serviceをcanonical data閲覧の成立条件にしない。
75. SQLite / Raw / Version / Evidence / Provenanceをcanonical / provenance-bearing dataとして優先保全し、Search Representation / Embedding / Vector Index / Markdown / Packageを再生成可能なderived layerとする。
76. Derived subsystem障害でaccepted Knowledgeをrollback /破壊せず、stale / failedを検出してLexical等へgraceful degradationする。
77. local provider failureからexternal providerへsilent fallbackしない。
78. accepted Object Knowledge Versionは論理immutableとし、Hard deleteよりArchive / Version追加を優先する。
79. canonical backupはRPO 24時間、同等環境でのcanonical restoreはRTO 4時間を初期目標とし、daily 7世代 + weekly 4世代以上をdefault retention基準とする。
80. 外部送信はlocal-only default、data minimization、`allow / review_required / blocked`相当のexport decision、secret保護を適用する。
81. remote MCP / service exposureはdefault無効とし、loopback外ではexplicit enable + authentication / scopeを要求する。
82. Primary supported environmentはWindows 11とし、Docker / always-on serverをCore必須にしない。
83. Reference Workstationはi5-13600KF / 128 GB RAM / RTX 4090 24 GBとし、Standard Object local automationはp95 10分以内をAcceptance targetとする。
84. Large Objectはp95 20分targetで別集計し、interactive warm retrievalはLexical p95 1秒、Semantic / Hybrid / Similarity p95 3秒等を初期目標とする。
85. Phase Nでoffline / crash / disk full / backup restore / broken provenance / Index rebuild / no-silent-cloud-fallback / egress boundaryをFailure Recovery Acceptanceとして検証する。

---

## 19. 現時点で未確定の主要事項

以下は今後のPhaseで決定する。

- Object共通contractの物理DB schema・`object_id`形式
- Class Registry / Class hierarchy / Object-Class membership / Class固有Facetの物理Schema拡張方式
- Facetの正式一覧と拡張方式
- Relation schema / relation type管理
- Evidence Packageの具体的形式・容量上限（Store / Package責務境界はB-03で確定済み）
- ChatGPTへ渡すinstructions / prompt
- Google Driveの具体的なフォルダ・同期方式
- External Exportのpersistent policy物理schema / export decision判定rule / credential backend
- Result JSON Schemaの物理field配置・syntax（論理contractはB-04で確定済み）
- Import / Validationの具体state machine / review severity / stale rebase方式（Human boundaryはB-06で確定済み）
- Version lifecycle
- Object更新時の全体再生成 / 差分更新方針
- Embeddingモデル
- Vector index実装（sqlite-vec等）
- Hybrid fusion / rerankingの具体アルゴリズム・weight
- Object / Facet semantic representationの具体的構築方式・Facet weighting
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

1. 最初に本書と `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md` を読む。
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
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md

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

- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - 再設計の全Phase / Task一覧。
- `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
  - Human Decision / local automation / external export / Result Import / 10分計測境界。
- `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
  - local-first、canonical / derived data、integrity、backup / restore、security、failure recovery、performance Acceptance。
- `README.md`
  - SGOKBの現行概要とDocumentation Indexへの入口。
- `docs/archive/prototype-0.2/DEVELOPMENT_STATUS.md`
  - Prototype 0.2の実データ評価と現状。
- `docs/archive/prototype-0.2/KNOWLEDGE_PIPELINE_EFFICIENCY_REDESIGN.md`
  - Fragment/LLM処理肥大化を受けた外部RAG事例との比較調査。
- `UserPreferenceDiscoverySystem/docs/PROJECT_CONCEPT.md`
  - UPDSの目的、Selection Event / Observation / Pattern / Preference Hypothesisの設計思想。

---

## 23. 現在地点

Phase AおよびPhase B（B-01〜B-07）は完了している。

Object Identityと共通属性の正本は`docs/requirements/OBJECT_REQUIREMENTS.md`、Classification modelは`docs/requirements/OBJECT_TYPE_MODEL.md`、具体的Class hierarchyとObject / Facet / Relation / value境界は`docs/requirements/OBJECT_TYPE_BOUNDARIES.md`、Source / Snapshot / Evidence / Provenance契約は`docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`、Structured Object Result / Evidence grounding / Version候補契約は`docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`、Object / Facet / Statement / Relation / Evidence検索契約は`docs/requirements/SEARCH_REQUIREMENTS.md`、Human Decision / local automation / external export / authoritative Import境界は`docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`、local-first / integrity / backup / security / recovery / performance契約は`docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`を正本とする。

次の作業は **Phase C — SGOKB / UPDS責務境界** である。まずC-01でSGOKBをWorld/Object Knowledge Layerとして確定し、C-02〜C-04でUPDSとの所有・参照・MCP連携境界を定義する。
