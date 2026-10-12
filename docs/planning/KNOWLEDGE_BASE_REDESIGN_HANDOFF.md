# Source Grounded Object Knowledge Base — Knowledge Base 再設計 引き継ぎ資料

更新日: 2026-10-12

## 1. 本書の目的

本書は、Source Grounded Object Knowledge Base（SGOKB）のKnowledge Base再設計について、別チャット・Codex・後続Phaseへ引き継ぐための全体Handoffである。

詳細要件の正本は各`docs/requirements/*.md`とし、本書はそれらを再掲する完全設計書ではない。後続Phaseでは、本書・Task master・対象要件を読み、既決事項を不用意に再検討しないこと。

Task master:

- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

現在地点:

> **Phase A / B / C / DとPhase EのE-01 / E-02 core schema / E-02A / E-02Bは完了。全62 Classのsurveyに続き、Facet候補を既存18 + 新規37 = 55 Facetのfreeze候補へ横断統合し、shared / inherited / class-specific profile方針を`docs/design/FACET_VOCABULARY_REVIEW.md`へ整理済み。次の未完了TaskはE-02C [P0] Class / Facet境界gold casesを作成する。再設計の正規作業基盤は`integration/knowledge-base-redesign`。**

Phase D / E移行資料:

- `docs/planning/PHASE_D_PREPARATION.md`
- `docs/planning/PHASE_E_PREPARATION.md`

---

## 2. 再設計の目的

旧Prototypeは、Web Capture BundleからEvidenceを生成し、ローカル生成LLMで大量のFragmentを抽出し、巨大なFinal Documentを生成する構成だった。

実データ評価で、AI応答待ちが処理時間の大部分を占め、Fragment数・Final Document量も日常利用には過大となった。このため再設計では、自動化率の最大化ではなく次を優先する。

- Knowledge品質
- Source / Evidenceまでの追跡可能性
- 長期保守性
- モデル非依存性
- 人間・通常プログラム・Embedding・ChatGPTの責務分離
- local-first

SGOKBの目的は次の通り。

> Web上のSource / Evidenceを根拠としてCharacter / Work / Concept等をObject Knowledgeとして構造化・版管理し、検索・比較・AI利用できるローカルKnowledge Baseを構築する。

SGOKBはDocument Generatorではなく、**Source GroundedなCurated Semantic Object Knowledge Base**として扱う。

---

## 3. 基本アーキテクチャ

```text
Web
 ↓
Source Capture / Import
 ↓
Source / Evidence Store
 ↓
Object Evidence Retrieval
 ↓
Object Evidence Package
 ↓
Google Drive
 ↓  Human-in-the-loop
ChatGPT（標準WorkflowではAPIを使用しない）
 ↓
Structured Object Result
 ↓
Validation / Import / Versioning
 ↓
Object Knowledge Store
 ↓
Lexical / Semantic / Similarity / Relation Retrieval
 ↓
MCP Knowledge Access Layer
 ↓
ChatGPT / Local LLM / UPDS / Other Clients
```

基本原則:

- SQLiteをcanonical Knowledge Storeとする。
- Raw / Evidence / Version / Provenanceを優先保全する。
- Search Representation / Embedding / Vector Index / Markdown / Packageは再生成可能なderived layerとする。
- Google Driveは交換領域であり正本ではない。
- ChatGPT出力を直接canonical Knowledgeへ昇格させない。
- MCPはKnowledge Access Layerであり、推論・創作の主体ではない。

---

## 4. Phase A — 方針・既存資産棚卸し

Phase Aは完了済み。

主要決定:

- 全Evidenceへの生成LLM Fragment化を標準Pipelineから外す。
- 巨大Final DocumentをKnowledgeの正本にしない。
- ChatGPT APIを標準Knowledge生成Workflowに必須としない。
- 既存資産をKeep / Modify / Replace / Retireへ分類した。
- 全面rewriteを前提とせず、Capture / Evidence / SQLite / FTS / Embedding等を可能な範囲で再利用する。

正本・参考:

- `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
- `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
- `docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`

---

## 5. Phase B — 要件定義

Phase B（B-01〜B-07）は完了済み。

### 5.1 Object

- ObjectはSource / Document / Knowledge Versionから独立したstable Identityを持つ。
- `object_id`はname / alias / path / Source / Version / Classification等から独立する。
- Classificationは`primary_class` 1件 + `additional_classes` 0件以上 + hierarchical Class Registryとする。
- 同名別Objectを許容する。
- 正式採用Classを、専用UI等の実装有無とは独立してRegistryへ保持できるようにする。
- 未登録Classを理由に意味的に不正確な別Classへsilent fallbackしない。

正本:

- `docs/requirements/OBJECT_REQUIREMENTS.md`
- `docs/requirements/OBJECT_TYPE_MODEL.md`
- `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`

### 5.2 Source / Evidence

- Source / Snapshot / Raw Artifact / Normalized Run / Evidenceを別責務とする。
- Source IdentityをURL / path / title / content hashから独立させる。
- SourceとObjectは多対多。
- Evidenceは単一Snapshotへ遡れる意味非改変の検索・引用単位。
- LLM summary / synthesis / inferenceを一次Evidenceへ自動昇格させない。
- Object KnowledgeからEvidence→Snapshot→Raw→Sourceまで追跡可能にする。

正本:

- `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`

### 5.3 Object Result / Version

- Object Resultは1 Object単位のEvidence-groundedな次期Knowledge Version候補。
- Structured JSONを交換正本とし、Import後はlocal Object Knowledge Versionを永続正本とする。
- Markdownは派生表示。
- Resultをtarget Object / Package / base Versionへbindする。
- `direct_statement` / `synthesis` / `interpretation` / `reported_view`を区別する。
- conflict / gap / insufficient evidence / unresolved reference / Registry proposalを確定Knowledgeから分離する。
- accepted Versionは論理immutableとし、訂正は新Versionで行う。

正本:

- `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`

### 5.4 Search

- Identity Lookup、Lexical / Semantic / Hybrid Object Search、Object / Facet Similarity、Relation Search、Evidence Searchを分離する。
- 通常free-text Object SearchはHybridを基本とする。
- Object / Facet / Statementのmulti-representationを利用する。
- Knowledge Statementを標準Semantic candidate単位とするが、通常結果は`1 Object = 1件`へ集約する。
- exact name / aliasをSemantic候補で埋没させない。
- current accepted Knowledgeを通常scopeとし、historicalをsilent混合しない。
- Search scoreをtruth / confidence / preference probabilityとして扱わない。

正本:

- `docs/requirements/SEARCH_REQUIREMENTS.md`
- `docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md`

### 5.5 Human / Automation

- Human Decision / Human-triggered Automation / Local Automatic Maintenance / External Human-in-the-loopを分ける。
- Source採用、Persistent Object Identity、External Export、authoritative Result Import、Registry変更を主要Human Decision boundaryとする。
- Package BuildとExternal Exportを分離する。
- Capture / Importを外部送信許可とみなさない。
- Drive → ChatGPT → result返却は正式なHuman-in-the-loop工程。

正本:

- `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`

### 5.6 Non-functional

- local-first。
- canonical / derived layerを分離。
- no-silent-cloud-fallback。
- canonical backup初期目標: RPO 24時間、restore RTO 4時間。
- default retention目安: daily 7世代 + weekly 4世代以上。
- Primary supported environment: Windows 11。
- Standard Object local automated segment: p95 10分以内target。
- Large Object: p95 20分target。

正本:

- `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`

---

## 6. Phase C — SGOKB / UPDS責務境界

**Phase C（C-01〜C-04）は2026-10-12に完了した。**

### 6.1 C-01 — SGOKB = World / Object Knowledge Layer

SGOKBは、ObjectそのものについてのKnowledgeを所有する。

主な所有対象:

- Object Identity / Classification
- Attribute
- Semantic Facet
- World / Object Relation
- Knowledge Statement
- Source / Evidence / Provenance
- Version / temporal scope
- Object / Facet / Statement Search Representation

SGOKBは次のPersonal Inferenceを所有しない。

- ユーザーがObjectを好むか
- なぜ選んだか
- 選択群から推測される嗜好・価値観・心理傾向
- User Preference Embedding / Taste Vector

正本:

- `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`

### 6.2 C-02 — UPDS = Personal Inference Layer

UPDSは次を所有する。

- Selection Event
- Semantic Observation
- Cross-source / Cross-object Pattern
- Preference Hypothesis
- Alternative Explanation
- Supporting / Contradicting User-oriented Evidence Set

重要な境界:

```text
Objectを保存した
≠
Objectを好む
```

Selection Eventは観測事実であり、Preference factではない。

non-selection、選択頻度、SGOKB Similarity / Search scoreをPreferenceへ単純変換しない。Evidence不足時には判断不能を許容する。

正本:

- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`

### 6.3 C-03 — Concept ownership

Concept Objectそのもののcanonical所有者はSGOKBとする。

SGOKBが所有:

- Concept `object_id`
- Classification
- Definition / Facet
- World Relation
- Source / Evidence
- Knowledge Version
- Concept Search Representation / Embedding

UPDSはSGOKB Concept `object_id`を参照してPersonal Inferenceを構築する。

UPDS内部analytic vocabularyを自動的にSGOKB Conceptへ昇格させない。未登録Conceptはunresolved / provisional / proposalとして扱い、canonical adoptionとは分離する。

正本:

- `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`

### 6.4 C-04 — SGOKB → UPDS Integration Contract

標準依存方向:

```text
SGOKB canonical store
        ↓
Retrieval / Application Core
        ↓
MCP read access
        ↓
UPDS Personal Inference
```

主要契約:

- SGOKB = canonical World / Object Knowledge Provider。
- UPDS = Personal Inference Consumer。
- 長期参照の基本はstable `object_id`。
- 推論再現性が必要な場合はimmutable `knowledge_version_id`を記録する。
- current取得でも実際に解決した`resolved_version_id`を識別可能にする。
- 過去Versionは新Version発生だけでinvalidにしない。
- current Knowledgeで再評価する場合は過去Hypothesisをsilent overwriteせず、新revisionとして扱う。
- Object merge / supersede / split / unavailable時に名前一致等でsilent置換しない。
- UPDSはObject / batch / Facet / Relation / Concept /必要時Evidence / Search / Similarityを取得できる論理capabilityを持つ。
- Cacheはderived cacheであり第二正本ではない。
- MCP停止時にSGOKB SQLiteへdirect fallbackしない。
- cloud serviceへsilent fallbackしない。
- SGOKB停止中もSelection Eventは記録可能だがSemantic enrichmentはpendingにできる。
- UPDS Preference HypothesisをSGOKB canonical Knowledgeへ自動write-backしない。

C-04では意味契約を確定した。具体的なDB schemaはPhase E、MCP Tool / Resource / JSON SchemaはPhase J、実UPDS結合試験はPhase Kで確定する。

正本:

- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

### 6.5 Phase C完了条件

- [x] SGOKB / UPDSの責務を分離した。
- [x] 同一Object / Concept Knowledgeを両プロジェクトで二重正本化しない境界を確定した。
- [x] Concept canonical ownershipを確定した。
- [x] stable Object ID / Knowledge Version / MCP read accessの連携意味契約を確定した。
- [x] stale / cache / failure / reverse write境界を確定した。
- [x] 詳細をPhase E / J / Kへ適切に引き継いだ。

---

## 7. Phase D開始時のRepository / Git状態

2026-10-12のD-01実施時にGit状態を再確認した。

- D-01開始直前のGitHub branch: `main`のみ
- D-01開始直前の`main` head: `7ab2093655687878e1406fd97d88c648b5ffd27d`
- open PR: 0件
- `main` branch protection: `protected: false`
- D-01で長期integration branchを`integration/knowledge-base-redesign`と確定し、D-01文書反映commitを起点として作成する。
- Phase DのD-01 / D-02 / D-03は完了。
- 次の未完了Task: D-04。

正本:

- `docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md`
- `docs/planning/PHASE_D_PREPARATION.md`

D-04以降の再設計では、明示的な理由がない限り`main`ではなく`integration/knowledge-base-redesign`を作業基盤とする。

---

## 8. Phase D — Repository / Git / フォルダ構造再編

Phase Dの目的は、Phase A〜Cで確定した論理境界を、将来の実装変更に耐えるRepository / module / Git運用へ落とし込むことである。

現在のTask状態:

```text
D-01 [P0] 長期ブランチ戦略                         完了
D-02 [P0] 旧Prototype文書の扱い                   完了
D-03 [P0] docs構造                                完了
D-04 [P0] src/sgokb責務別再編                     完了
D-05 [P1] 既存module移動方針                      完了
D-06 [P1] .local/generated/exchange Git除外方針   完了
D-07 [P1] branch / PR / tag / release整理ルール   完了

Phase D                                           完了
```

D-01で確定したGit運用:

- `main` = stable baseline。
- `integration/knowledge-base-redesign` = D-04以降〜O-04までの再設計integration branch。
- code / migration / move / schema変更 = 原則`task/<task-id>-<slug>`からintegrationへのPR。
- move / renameとbehavior changeを別PRへ分離する。
- `main`のfixはintegrationへ速やかにmergeして乖離を抑える。
- branch protectionはD-01では変更せず、CI整備後かつ遅くともO-04前に再評価する。

正本: `docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md`

Phase Dで守る原則:

1. move / renameとbehavior changeを可能な限り別commit / PRへ分ける。
2. Phase B / Cの意味要件をRepository構造変更の都合で変更しない。
3. Archiveを現行仕様へ戻さない。
4. Phase EのDB schemaをPhase Dで先取りしない。
5. 既存moduleを調査してから再配置し、理想ディレクトリへの全面moveを前提にしない。
6. branch作成・大量moveは対応Taskで決定後に実施する。

D-04で責務別code構造を次のとおり確定した:

```text
src/sgokb/
├─ domain/
├─ ingestion/
├─ storage/
├─ retrieval/
├─ exchange/
├─ rendering/
├─ application/
├─ cli/
├─ mcp/
└─ _legacy/   # Phase Lまでの一時隔離領域
```

`domain`は外部I/Oを持たない最内層、`application`はcapability間の調停、`cli / mcp`はadapterとする。現行`repository.py / domain.py / providers.py`は複数責務を持つため単純moveではなくsplit対象である。`capture.py / final.py / knowledge_repository.py`の旧Fragment / Final責務は新標準layerへ混ぜず、replacement完了までlegacy境界として扱う。

D-05で移動方針も確定した。moduleをdirect move / package conversion / split / legacyへ分類し、旧top-level importは必要期間だけ明示re-export shimで互換維持する。実移動はPhase E〜Lでstructural PRとbehavior PRを分離して段階実施する。

D-06ではruntime data境界を確定した。`.local/`はGit管理外runtime root、`/generated/`はrebuildable derived、`/exchange/`はPackage / Result交換、`/backups/`は誤commit防止対象とする。Google Drive同期先は原則Repository外pathとし、同期directoryへのwriteをExternal Exportとして扱う。root `sample/`はlocal corpusとしてignore維持し、Git管理fixtureは`tests/fixtures/` / `examples/`へ分離する。

D-07ではGit history cleanup policyを確定した。PR #1〜#9はすべてmerged、open PR / tag / Releaseは0件。merge済み短命branchはPR metadataとhead SHAを確認して早期削除可能とし、squash merge時に`git branch --merged`だけへ依存しない。`archive/pre-rename-local-main`は11 unique commitを持つためhistorical archiveとして保全し、新SGOKBのtag / Release境界はO-06へ延期した。

Phase E開始準備としてD-05 Wave 1を実行し、旧`domain.py`を内容変更なしで`domain/_prototype.py`へ移動、`domain/__init__.py`で既存public importを維持した。PR #11をintegrationへmerge済み。E-01の詳細開始条件と現行Prototype DBとの差分は`docs/planning/PHASE_E_PREPARATION.md`を正本とする。

正本:

- `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
- `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
- `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`
- `docs/decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md`

---

## 9. 初期Vertical Slice

再設計実装では最初から全機能を完成させない。

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
 → Object / Facet / Statement embedding
 → Semantic / Similarity Search
 → MCP get_object
```

このVertical Slice成立後にWork / Concept / Relation拡張 / UPDS連携を広げる。

---

## 10. 今後の主要未確定事項

以下は後続Phaseで具体化する。

### Phase D

Phase DはD-01〜D-07まで完了した。branch / PR / merge戦略、`src/sgokb`責務別構造、module move / split / compatibility順序、runtime data / Git exclusion、branch / PR / tag / Release cleanup policyは確定済みである。

Phase D由来で後続へ残る事項は、O-05での最終branch cleanupとO-06での新SGOKB version / tag / Release境界の確定である。

### Phase E

E-01 / E-02 core schemaは完了し、Object / Class / Version / Relation骨格とSemantic Facet / Statement / Attribute / Temporal Scope / Search Representation schemaを確定した。その後の設計レビューで、Class意味幅の膨張防止と試験詳細化のためFacet taxonomy hardening taskを追加した。残る主な未確定事項は次である。

- E-02: Core Complete — `docs/design/SEMANTIC_FACET_SCHEMA.md`
- E-02A: Complete — `docs/design/FACET_TAXONOMY_SURVEY.md`
- E-02B: Complete — `docs/design/FACET_VOCABULARY_REVIEW.md`
- E-02C: Class / Facet境界gold cases
- E-03: Source / Evidence / Evidence Link / Provenance schema
- E-04: Version lifecycle / stale / rollback / current promotion
- E-05: Object Result JSON Schemaの物理field

E-02A〜E-02Cでは全Class向け機能実装を先行させず、意味境界・Facet候補・語彙再利用・gold testを事前設計する。E-05のClass別extension / Facet profile validationをfreezeする前に完了させる。

### Phase F〜H

- Evidence Retrieval / Package具体実装
- Drive交換形式
- Validation / Import state machine
- Diff / Review表示

### Phase I

- Embedding model
- Vector backend
- Hybrid fusion / Object aggregation / reranker

### Phase J

- MCP Tool正式名
- Tool input / output JSON Schema
- Resource URI
- transport / auth / permission
- read / write capability分離

### Phase K

- 実UPDSとの最小連携ユースケース
- stable ID / Version参照の実機検証
- Semantic Index責務分離
- UPDS専用Contextが必要かの評価

### Phase L以降

- Fragment / Final Document旧実装の最終処遇
- migration
- CLI / operation
- Acceptance
- release / tag境界

ConceptのSGOKB / UPDS所有契約そのものは**未確定事項ではない**。Phase Cで確定済みである。

---

## 11. Phase実施ルール

各Phase / Taskでは次を守る。

1. 最初に本書とTask masterを読む。
2. 対象Taskに必要な正本要件を確認する。
3. 既決事項を理由なく再検討しない。
4. 大きな設計判断は実装前に文書化する。
5. 後続Phaseを過剰に先取りしない。
6. 既存実装を変更する前に再利用可能部分を調査する。
7. move / renameとbehavior changeを分離する。
8. 変更後はdocs / tests / Task statusを同時更新する。
9. Phase完了時に決定事項・未決事項・次Phaseへの入力を明記する。
10. Phase間で仕様変更があれば本書も更新する。

---

## 12. 新規チャット開始指示

Phase全体を扱う場合:

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。

まずGitHubリポジトリの以下を確認し、これまでの合意事項と現在のTaskを把握してください。
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md

既決事項は維持し、対象Phaseに必要な範囲だけ具体化してください。

今回実施するTask:
Phase X — <Phase名>

Phase内のTaskを確認し、必要な調査・設計・実装・テスト・ドキュメント更新まで実施してください。
Phase完了時には、決定事項、実施内容、未決事項、次Phaseへの引き継ぎを報告してください。
```

Phase Eを開始する場合:

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。
Phase A〜Dは完了しています。

再設計の正規作業基盤はintegration/knowledge-base-redesignです。
まず以下を確認してください。
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md
- docs/requirements/OBJECT_REQUIREMENTS.md
- docs/requirements/OBJECT_TYPE_MODEL.md
- docs/requirements/OBJECT_TYPE_BOUNDARIES.md
- docs/requirements/OBJECT_RESULT_REQUIREMENTS.md
- docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md
- docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md
- docs/decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md

今回実施するTask:
E-02C [P0] Class / Facet境界gold casesを作成する

E-02A / E-02Bは完了しています。`docs/design/FACET_TAXONOMY_SURVEY.md`と`docs/design/FACET_VOCABULARY_REVIEW.md`を主要入力として、全62 Classのpositive / negative例と代表KnowledgeのFacet / Object / Attribute / Relation / Statement期待配置をgold case化してください。55 Facet freeze候補、ancestor profile inheritance、`overall` fallback禁止、Relation / Attribute境界、近義Facet境界を具体例で検証し、`docs/reference/CLASS_FACET_GOLD_CASES.md`へまとめてください。必要なら機械可読fixtureも追加してください。
```

---

## 13. 関連文書

### Phase B正本

- `docs/requirements/OBJECT_REQUIREMENTS.md`
- `docs/requirements/OBJECT_TYPE_MODEL.md`
- `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
- `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
- `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- `docs/requirements/SEARCH_REQUIREMENTS.md`
- `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
- `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`

### Phase C正本

- `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

### Planning / reference

- `docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md`
- `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
- `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
- `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`
- `docs/decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md`
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
- `docs/planning/PHASE_D_PREPARATION.md`
- `docs/planning/PHASE_E_PREPARATION.md`
- `docs/design/FACET_TAXONOMY_SURVEY.md`
- `docs/design/FACET_VOCABULARY_REVIEW.md`
- `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
- `docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`
- `README.md`

Prototype資料は`docs/archive/prototype-0.2/`へ分離済みであり、現行仕様の判断には使用しない。

---

## 14. 現在地点

Phase A、Phase B、Phase C、Phase Dは完了している。

**次の作業はE-02C [P0] Class / Facet境界gold casesを作成する。**

E-02Aで全62 Classのtaxonomy survey、E-02Bで55 Facetのfreeze候補とprofile inheritance方針を確定した。E-02Cで具体例によるboundary regression corpusを固定し、Facet taxonomyをfreezeした後、E-03のSource / Evidence / Provenance設計へ戻る。

再設計の正規作業基盤は`integration/knowledge-base-redesign`である。Phase DでRepository / Git / module / runtime data / history cleanupの境界は確定した。Phase EではObject / Class / Relation / Versionを中心とする物理Data Modelへ進む。
