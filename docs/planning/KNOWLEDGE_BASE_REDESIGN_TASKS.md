# Source Grounded Object Knowledge Base — Knowledge Base 再設計タスク

更新日: 2026-10-14

## 1. 目的

本書は、Source Grounded Object Knowledge Base（SGOKB）を、従来の「WebページをローカルLLMで細粒度にFragment化し、巨大な最終文書を自動生成するプロトタイプ」から、次の方針へ移行するための作業計画を定義する。

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

SGOKBは「外部世界のObject Knowledge」を担当する。ユーザー自身の嗜好・価値観・関心傾向の推論はUserPreferenceDiscoverySystem（UPDS）の責務とし、SGOKBには含めない。

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

- [x] **B-01 [P0] SGOKBの目的を再定義する**
  - SGOKBを「Curated Semantic Object Knowledge Base」として定義する。
  - 文書生成は目的ではなく派生表示とする。

- [x] **B-02 [P0] Object要件を定義する**
  - `docs/requirements/OBJECT_REQUIREMENTS.md` を正本とする。
  - ObjectをSource / Document / Versionから独立した安定Identityとして定義した。
  - `Character`, `Work`, `Concept`を主要ユースケースの基準Classとし、B-02Cで`Primary Class + Additional Classes + hierarchical Class Registry`へ精緻化した。B-02Dで正式採用したClassは原則として初期Registryへ広く登録する。
  - `object_id` / name / aliases / status / current_version / timestampの共通概念を定義し、B-02Cで分類概念を`primary_class` / `additional_classes` / Class Registryへ精緻化した。
  - 同名別Object、名称変更、複数Work所属、Concept / UPDS境界のIdentity判断方針を定義した。

### B-02 Object Type Refinement — B-03前の必須精緻化

詳細計画は `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md` を正本とする。

- [x] **B-02A [P0] 外部分類体系を正式調査する**
  - Schema.org / DBpedia / Wikidata / WordNet / Dublin Core等を比較する。
  - Object typeとSource typeを分離して整理する。
  - 成果物: `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`

- [x] **B-02B [P0] SGOKB Object候補を網羅的に整理する**
  - Character / Person / Organization / Work / Series / Place / Event / Artifact / Species / Concept等を検討する。
  - 各候補について独立Object化の価値、想定Source、Relation、Facet、Class固有機能の実装優先度を整理する。
  - 成果物: `docs/requirements/OBJECT_TYPE_CANDIDATES.md`

- [x] **B-02C [P0] Object Type / Class階層を設計する**
  - 1階層固定enumを避け、上位Typeとclass/subtypeを分ける方式等を比較する。
  - `instance of` / `subclass of`相当概念やType registryの要否を判断する。
  - B-02Dで正式採用したObject Classは原則として初期Class Registryへ登録し、Class固有機能の実装優先度とは分離する。
  - 成果物: `docs/requirements/OBJECT_TYPE_MODEL.md`

- [x] **B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する**
  - 全候補を上位Object Type / subtype・Class / Facet / Relation / 対象外へ分類する。
  - Character / Work / Conceptの既存要件を新分類モデルへ再マッピングする。
  - 正式採用Classの初期Registry集合を確定し、Class固有機能の実装優先度を別軸で記録する。
  - 汎用Classへの意味的に不正確なfallbackを防ぐ境界ルールを決める。
  - 正式Class hierarchy、初期Registry seed集合、Facet / Relation / value境界、fallback ruleを確定した。
  - 成果物: `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`

**Gate:** B-02A〜B-02Dは完了。Object分類境界が確定したためB-03へ進行可能。

- [x] **B-03 [P0] Source / Evidence要件を再確認する**
  - Source / Snapshot / Raw Artifact / Normalized Run / Evidenceを別責務として定義した。
  - Source IdentityをURL・path・title・content hashから独立させ、0件以上のlocatorを持てる要件とした。
  - SourceとObjectを多対多とし、candidate / confirmed / excludedの関連状態を論理要件として分離した。
  - 旧`source_type`単一軸を、Source本体のresource type / media type / document genre / publisher kind / provider / page purpose等と、Source↔Object association上のsubject relationshipへ分離した。
  - Evidenceを単一Snapshotへ必ず遡れる意味非改変の検索・引用単位とし、LLM summary / synthesis / inferenceを一次Evidenceへ昇格させない。
  - Object Knowledge → Evidence → Normalized Run → Snapshot → Raw Artifact → SourceのProvenance chainを定義した。
  - Source間の依存関係、重複・矛盾、Snapshot時間変化、Evidence lifecycle、Evidence StoreとPackageの境界を定義した。
  - B-04 / B-05 / E-03 / Phase Fへ必要な引き継ぎ条件を定義した。
  - 成果物: `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`

- [x] **B-04 [P0] Object Result要件を定義する**
  - Object Resultを1 Object単位のEvidence-groundedな「次期Object Knowledge Version候補」と定義し、AI出力を直接正本へ昇格させない。
  - Structured JSONを機械向け交換正本とし、Import後はローカルObject Knowledge Versionを永続正本、Markdownを派生表示とする。
  - Resultをtarget Object / Evidence Package / base Knowledge Versionへbindし、stale Resultを検出可能にする。
  - summary / structured attribute / Facet / Relationを構造化し、Knowledge StatementをResult内部のgrounding単位として定義した。
  - `direct_statement` / `synthesis` / `interpretation` / `reported_view`相当のderivation kindを定義し、数値confidenceを必須としない。`reported_view`はattributionを保持する。
  - Knowledge記述言語とEvidence原文言語を区別し、時間依存Knowledgeには必要に応じてtemporal scopeを持てる要件とした。
  - Statement / attribute / Relationを具体的Evidence IDへgroundingし、標準workflowではPackage membershipもValidationする。
  - conflict / insufficient evidence / gap、unresolved Object reference、Registry proposalを確定Knowledgeから分離した。
  - Resultは原則full Knowledge snapshotとし、Version IDはImporter側で発行する。
  - Schema適合と意味品質を分離し、Validatorが意味内容を推測修復しない要件を定義した。
  - 成果物: `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`

- [x] **B-05 [P0] 検索要件を定義する**
  - Object Identity Lookup、Object Lexical / Semantic / Hybrid Search、Object / Facet Similarity、Relation Search、Evidence Searchを別責務として定義した。
  - 通常free-text Object検索はHybridを基本とし、exact name / alias等のIdentity matchをSemantic候補で埋没させない要件とした。
  - accepted current Object Knowledgeを通常検索の既定scopeとし、historical Versionは明示scopeへ分離した。
  - Knowledge Statementをsemantic candidate単位として標準Embeddingしつつ、通常Object Searchは`1 Object = 1結果`へ集約すると確定した。2026-10-11の追加調査でObject / Facet / Statementのmulti-representation方針へ更新した。
  - Object overall similarityとFacet similarityを正式要件とし、Facet欠落時にoverallへsilent fallbackしない。
  - Relation Searchは構造化1-hop traversalを必須とし、bounded multi-hopへ拡張可能にした。
  - Evidence Lexical / Semantic Searchを維持し、Source分類、Object association、各種時刻、active/effective / historical generation、Provenance integrityでfilter可能とした。
  - conflict中のgrounded Statementは検索可能としつつ、gap / insufficient evidence / unresolved reference / Registry proposalを通常Semantic Searchから分離した。
  - Search Index / Embeddingを再生成可能な派生物とし、Embedding Space、Knowledge Version、Evidence generationを追跡する要件を定義した。
  - Ranking scoreをtruth / confidence / Source trustとみなさず、match channel / Facet / Statement / Version / groundingを説明可能にした。
  - Statement-level Embedding、Vector backend候補、Object Aggregation、incremental reuseの追加調査を`docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md`へ整理し、B-05要件へ反映した。
  - 成果物: `docs/requirements/SEARCH_REQUIREMENTS.md`

- [x] **B-06 [P0] 人間工程と自動工程を要件として分離する**
  - Human Decision / Human-triggered Automation / Local Automatic Maintenance / External Human-in-the-loopの4責務へWorkflowを分離した。
  - Source採用・Persistent Object Identity確定・External Export・authoritative Result Import・Registry変更を人間decision boundaryとした。
  - Capture済みBundleのImport / Normalize / Evidence、Package Build、Result machine Validation、明示Import後のVersion / Embedding / Index更新を自動化対象とした。
  - Package Buildをlocal staging、Package Exportをexternal data egressとして別操作にし、Google Drive同期directoryへのwriteもExternal Exportとして扱う。
  - Capture / Importしたこと自体をGoogle Drive / ChatGPT /外部API等へのexport permissionとみなさない。
  - external Embedding / reranker等へKnowledge textを送る場合もExternal Processingとして扱う。
  - standard ChatGPT workflowはDrive → ChatGPT → result.json返却を正式な手動工程とし、その時間を1 Object自動処理10分目標から除外した。
  - Validation成功と正本Importを分離し、normal Resultはexplicit Importを人間control point、stale / partial / Registry proposal等はreview-requiredとした。
  - 10分目標へ含むpre-analysis / post-analysis local segmentと、除外するhuman / external network時間を定義した。
  - 成果物: `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`

- [x] **B-07 [P1] 非機能要件を更新する**
  - local-firstを標準とし、Internet / ChatGPT / Drive / MCP / Vector backend停止時にもcanonical dataと利用可能なlocal read機能を維持する要件を定義した。
  - SQLite / Raw / Version / Evidence / Provenanceを保全対象とし、Search Representation / Embedding / Vector Index / Markdown / Packageを再生成可能なderived layerとして分離した。
  - crash consistency、transaction、idempotent retry、broken provenance isolation、stale Index検出とLexical fallbackを定義した。
  - accepted Knowledge Versionを論理immutableとし、Archive優先、参照中Evidence / Raw / Result provenanceを通常retentionで自動削除しないことを定義した。
  - canonical backupはRPO 24時間、同等環境でのcanonical restoreはRTO 4時間を初期目標とし、daily 7世代 + weekly 4世代以上をdefault retention基準とした。
  - local-only default、data minimization、`allow / review_required / blocked`相当のexport decision、secret非平文化、log redaction、no-silent-cloud-fallbackを定義した。
  - Embedding Space / Representation Builder / Vector backend generationを分離し、SQLite正本からVector Indexをfull rebuild可能とした。
  - Primary environmentをWindows 11とし、現行Reference Workstation（i5-13600KF / 128 GB RAM / RTX 4090 24 GB）でStandard Objectのlocal automated segmentをp95 10分以内とした。
  - Large Objectは別profileでp95 20分target、interactive warm searchはLexical p95 1秒、Semantic / Hybrid / Similarity p95 3秒等の初期目標を定義した。
  - Phase Nへoffline / crash / disk full / backup restore / egress / Index rebuild / provider failure等のAcceptanceを引き継いだ。
  - 成果物: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`

**完了条件:** 既存の要件定義書を新方針で置換または新版化し、旧Prototype要件との差分が説明可能である。

---

# Phase C — SGOKB / UPDS責務境界

- [x] **C-01 [P0] SGOKBをWorld/Object Knowledge Layerとして定義する**
  - SGOKBを、ObjectそのもののIdentity・分類・属性・意味・Semantic Facet・Relation・Knowledge Statement・Source / Evidence・Provenance・Version・検索表現を所有するWorld / Object Knowledge Layerとして正式定義した。
  - 第三者の主観的見解はattributionとEvidenceを保持するObject Knowledgeとして扱えるが、「ユーザーが好む」「なぜ選ぶ」等のPersonal Inferenceは保存しない。
  - Curation / workflow metadataは必要に応じて保持できるが、Capture・登録・検索・閲覧等の行動をPreferenceへ意味変換しない。
  - Object / Facet / Statement Embedding、Similarity、Search rankingをUser Preference scoreとして解釈しない。
  - Conceptのプロジェクト間所有契約はC-03、SGOKB → UPDS連携契約はC-04へ残した。
  - 成果物: `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`

- [x] **C-02 [P0] UPDSをPersonal Inference Layerとして定義する**
  - Selection Eventを観測事実としてUPDS所有とし、Preferenceそのものとは区別する。
  - Selection EventとSGOKB等のObject Knowledgeを組み合わせたSemantic Observation、Cross-source / Cross-object Pattern、Preference HypothesisをUPDS所有とした。
  - Preference Hypothesisは確定Factではなく、Alternative Explanation、supporting / contradicting Evidence、判断不能状態を保持可能にする。
  - User-oriented Evidence SetをSGOKB Source / Evidenceとは別責務として定義し、Object canonical KnowledgeをUPDSの第二の正本として複製しない。
  - non-selection、選択頻度、Similarity / Search scoreを単純にPreferenceへ変換しない。
  - 嗜好・関心は時間変化し得るものとし、単一Universal Preference Scoreへの圧縮を必須としない。
  - SGOKB → UPDSを基本依存方向とし、SGOKB CoreはUPDS schemaを知らなくても単独成立させる。
  - Concept所有契約はC-03、Object ID / Version参照・MCP等の具体的連携契約はC-04へ残した。
  - 成果物: `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`

- [x] **C-03 [P1] Conceptの所有境界を確定する**
  - Concept Objectのcanonical identity / classification / definition / Semantic Facet / Relation / Source / Evidence / Knowledge Version / Search Representation / EmbeddingをSGOKB所有とした。
  - UPDSはSGOKBのstable Concept Object IDを参照し、Semantic Observation / Pattern / Preference Hypothesis / User-oriented Evidenceを所有する。
  - SGOKB Concept RelationとUser-to-Concept Preference Relation、およびConcept EmbeddingとPreference Embeddingを別責務として分離した。
  - UPDS内部analytic vocabularyを自動的にSGOKB Conceptへ昇格させず、未登録Conceptはunresolved / provisional / proposalとして扱う。
  - Concept proposalとSGOKB canonical adoptionを分離し、UPDSがcanonical Concept IDをsilent作成したり近似Conceptへ強制fallbackしたりしない。
  - stable Concept `object_id`を参照の基本単位とし、推論再現性のため必要に応じKnowledge Versionを併記できる要件とした。
  - 具体的なObject / Version参照payload、MCP Tool、stale contractはC-04へ残した。
  - 成果物: `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`

- [x] **C-04 [P1] SGOKB→UPDS連携契約を定義する**
  - SGOKBをcanonical World / Object Knowledge Provider、UPDSをPersonal Inference Consumerとし、依存方向を原則SGOKB → UPDSに固定した。
  - stable `object_id`を永続参照の基本単位、immutable `knowledge_version_id`を推論再現用のVersion参照とした。
  - Version省略時はcurrent accepted Knowledgeを返しつつ、実際に解決した`resolved_version_id`を必ず識別可能にする契約とした。
  - UPDSがSemantic Observation / Hypothesis生成に使用したObject ID / Knowledge Version /取得時刻 / scopeを追跡できる要件とした。
  - staleをinvalidと同一視せず、過去推論はpinned Versionで再現し、current Knowledgeでの再評価は新しいObservation / Hypothesis revisionとして扱う。
  - merge / supersede / split / unavailable時にIDをsilent置換せず、resolution情報またはunresolved / review-requiredとして扱う。
  - Object / batch / Facet / Relation / Concept /必要時Evidence、およびSearch / Similarityの論理取得capabilityを定義した。
  - UPDS cacheはderived cacheとしてのみ許容し、`object_id` / Version / contract version / retrieved time / scopeを保持する。freshness未確認cacheをcurrentとsilent扱いしない。
  - 標準transportをSGOKB Retrieval / Application Core経由のMCP read accessとし、SQLite direct accessやcloud serviceへのsilent fallbackを禁止した。
  - Integration Contract version、partial response / warning、data minimization、SGOKB停止時のpending semantic enrichmentを定義した。
  - UPDS専用Preference推論をSGOKBへ埋め込まず、Personal Inferenceのcanonical write-backを禁止した。Concept proposal等のreverse directionはstaging / reviewとcanonical writeを分離する。
  - 具体的なDB schemaはPhase E、MCP Tool / JSON SchemaはPhase J、実UPDSでの受入はPhase Kへ引き継いだ。
  - 成果物: `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

**完了条件:** 両プロジェクトで同一ConceptやObject Knowledgeを重複生成せず、stable Identity / Version / Knowledge Access境界を介してUPDSがSGOKBを再利用できる責務・連携契約が決まっている。

---

# Phase D — Repository / Git / フォルダ構造再編

- [x] **D-01 [P0] 再設計用長期ブランチ戦略を決定する**
  - `main`を動作可能なstable baselineとして保持する。
  - 長期integration branchを`integration/knowledge-base-redesign`と確定した。
  - D-04以降の再設計はintegration branchを正規作業基盤とし、Phase OのO-04で`main`へ統合する。
  - code / migration / module move / schema等は原則`task/<task-id>-<slug>`短命branch + PRでintegrationへ統合する。
  - 小規模docs-only進捗更新はintegrationへ直接commit可能とし、設計Decision変更はPRを優先する。
  - `main`に再設計外fixが入った場合は速やかにintegrationへmergeし、長期branchの乖離を抑える。
  - move / renameとbehavior changeは別PRへ分離する。
  - D-01ではbranch protectionを変更せず、CI整備後かつ遅くともO-04前に再評価する。
  - 成果物: `docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md`

- [x] **D-02 [P0] 旧Prototype文書の扱いを決める**
  - 旧要件・Prototype設計・評価・速度/コスト/モデル比較資料を `docs/archive/prototype-0.2/` へ移動済み。
  - benchmark結果、評価結果、速度試験は「歴史的検証結果」として保持する。
  - `docs/README.md` とroot `README.md` から現行仕様と過去Prototypeを明確に分離する。

- [x] **D-03 [P0] 新しいdocs構造を決定する**
  - 現行文書と歴史資料を物理的に分離する。
  - `docs/README.md` を人間向けの正規入口とする。
  - 現在の構成:

```text
docs/
├─ README.md
├─ requirements/
│  ├─ KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md
│  ├─ SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md
│  ├─ UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md
│  ├─ CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md
│  ├─ SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md
│  ├─ OBJECT_REQUIREMENTS.md
│  ├─ OBJECT_TYPE_CANDIDATES.md
│  ├─ OBJECT_TYPE_MODEL.md
│  ├─ OBJECT_TYPE_BOUNDARIES.md
│  ├─ SOURCE_EVIDENCE_REQUIREMENTS.md
│  ├─ OBJECT_RESULT_REQUIREMENTS.md
│  ├─ SEARCH_REQUIREMENTS.md
│  ├─ WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md
│  └─ NON_FUNCTIONAL_REQUIREMENTS.md
├─ decisions/
│  ├─ KNOWLEDGE_BASE_REDESIGN_DECISION.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md
│  ├─ SGOKB_MODULE_RESPONSIBILITY_DESIGN.md
│  └─ SGOKB_RENAME_DECISION.md
├─ planning/
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
│  └─ PHASE_D_PREPARATION.md
├─ reference/
│  ├─ EMBEDDING_VECTOR_SEARCH_RESEARCH.md
│  ├─ KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md
│  └─ KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md
└─ archive/
   ├─ prototype-0.2/
   └─ rename-2026-10/
```

  - 今後Phase E以降で確定するArchitecture / Data Model / Retrieval / MCP等は、確定時に現行カテゴリを追加する。

- [x] **D-04 [P0] `src/sgokb`の責務別再編を設計する**
  - 現行15 moduleと内部importを棚卸しし、既存ファイル単位の1対1 moveでは責務分離できないことを確認した。
  - 正規構造を`domain / ingestion / storage / retrieval / exchange / rendering / application / cli / mcp`へ確定した。
  - 旧Fragment / Final系を通常責務へ混在させない移行用`_legacy/`境界を追加した。これはPhase Lまでの一時領域であり恒久layerではない。
  - `domain`を最内層、`application`を複数capabilityの調停、`cli / mcp`を外側adapterとする依存方向を定義した。
  - `mcp -> SQLite direct access`および新設計moduleから`_legacy`への依存を禁止した。
  - `repository.py`, `domain.py`, `providers.py`は単純moveではなく責務別split対象と確定した。
  - Phase Eの物理DB schema、Vector backend、MCP Tool等は先取りしていない。
  - 実ファイルmove / behavior changeはD-05以降へ分離した。
  - 成果物: `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`

- [x] **D-05 [P1] 既存モジュール移動方針を決める**
  - moduleをdirect move / package conversion / split / legacyの4分類へ整理した。
  - structural PRは`git mv`中心commitとimport/package-data repair commitを分離し、behavior / schema変更を別PRへ送る。
  - 旧top-level importは必要期間、ロジックを持たない明示re-export shimで互換維持し、新規codeはcanonical pathのみを使用する。
  - `domain.py`はPhase E前、`application.py`は新use case導入時、`cli.py`はPhase Mでpackage conversionする。
  - `repository.py` / `providers.py`はwholesale moveせず責務別splitし、`capture.py` / `final.py`等はreplacement成立後にlegacy隔離する。
  - migrations / promptsはloader・package-data・legacy処遇を伴う適切なPhaseまで早期移動しない。
  - Phase E〜Lへまたがる移動Waveとstructural PR検証Gateを確定した。
  - 成果物: `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`

- [x] **D-06 [P1] `.local/` / generated / Google Drive exchangeデータのGit除外方針を更新する**
  - `.local/`をGit管理外runtime rootとし、`canonical/`と`transient/`を意味上分離した。
  - `/generated/`をSearch Representation / Embedding / Vector Index / rendering等のrebuildable derived専用rootとしてGit ignoreした。
  - `/exchange/`をlocal Package staging / Result incoming等のGit管理外rootとし、Google Drive同期directoryは原則Repository外pathとした。
  - `/backups/`を誤commit防止でignoreする一方、production backupの唯一の保存先にはせず、Repository外 / 別deviceへ配置可能にする方針を確定した。
  - root `sample/`は実験・評価local corpusとしてignore維持し、Git管理するsynthetic fixtureは`tests/fixtures/` / `examples/`等へ分離する。
  - `.env.*`, `.secrets/`, local config / credential file、SQLite journalを追加保護した。
  - D-06時点でruntime-like tracked fileが存在しないことを確認し、既存dataの`git rm --cached`は不要と判断した。
  - 成果物: `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`
  - root `.gitignore`を本方針へ更新した。

- [x] **D-07 [P1] 旧branch / PR / tag / releaseの整理ルールを決める**
  - local / remote branch、PR #1〜#9、tag、GitHub Releaseを実査した。PR #1〜#9はすべてmerged、open PR 0件、tag 0件、Release 0件だった。
  - squash mergeでは`git branch --merged`だけを削除判定に使用せず、GitHub PRのmerged状態・head SHA・base・merge後追加commit有無を確認する方針とした。
  - merge済み短命task branchは検証後にlocal / remoteから早期削除できる方針とし、D-04〜D-06 branchをcleanup対象とした。
  - `feature/cpc-prototype` / `feature/cpc-prototype-upgrade`はintegrationにunique commit 0を確認し、local cleanup対象とした。
  - `archive/pre-rename-local-main`には未統合unique commit 11件があるため削除せず、historical archiveとしてremoteにも保全する方針とした。
  - existing tag / Releaseはimmutable historyとして保持し、D-07時点では存在しないためretroactive tag / Releaseを作成しない。
  - 新SGOKBのversion / tag / Release境界はO-06で確定し、integration途中から正式Releaseを作らない。
  - 成果物: `docs/decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md`

**完了条件:** 新旧資産の配置ルールとGit移行手順が決まり、移動による履歴消失・誤削除を防げる。

---

# Phase E — Object Knowledgeデータモデル

**Phase E開始準備（2026-10-12）:** Phase D完了を再監査し未完了Task 0件を確認した。D-05 Wave 1として`domain.py -> domain/` package conversionをstructural-only PR #11で完了し、現行Prototypeの`entities / entity_relations / entity_evidence` schemaとの差分とE-01 Definition of Readyを`docs/planning/PHASE_E_PREPARATION.md`へ整理した。

- [x] **E-01 [P0] Object schemaを設計する**
  - `objects`
  - `object_aliases`
  - `object_versions`
  - `object_relations`
  - Class Registry / Class hierarchy / Object-Class membershipの物理schema。
  - B-02Dで正式採用したClassを、本番Object投入前に初期Registryへ決定論的にseedする方式。
  - Class Registry包含とClass固有extension実装の有無を独立して管理する方式。
  - 未登録Classが必要なObjectを、意味的に不正確な汎用Classへ自動fallbackさせないstaging / review方針。
  - Object Registry metadataとObject Knowledge Version dataを分離し、Result内Registry proposalを通常Knowledge Importの副作用として自動適用しない。
  - Relation Type vocabulary / RegistryをObject Class Registryと分離して管理できる物理契約。

- [x] **E-02 [P0] Semantic Facet schemaを設計する**
  - Character例: overall / personality / values / motivation / behavior / relationships / role / themes。
  - Work例: overall / themes / worldview / narrative / tone / characters / relationships。
  - Concept例: definition / properties / implications / related_concepts / examples。
  - Class固有FacetをDB列へ固定しすぎない。
  - 初期Registryへ登録済みでも専用Facetが未定義のClassを許容し、共通Object contractで保持できるようにする。
  - Facet Registry / Class-to-Facet profileとcommon Facetを設計する。
  - Facet内Knowledge Statement、Facet status、typed attribute key/valueの配置をB-04契約へ合わせて設計する。
  - Object / Facet / Statement Search Representationを正本Knowledgeから分離し、representation builder version / content hash /対象Version membershipを追跡できる論理契約を設計する。
  - Statement / attribute / Relationのtemporal scopeをVersion作成時刻と分離して表現する方式を設計する。

- [x] **E-02A [P0] 全ClassのFacet taxonomy surveyを実施する**
  - E-01で初期Registryへ登録した全62 Classを対象に、Classごとの意味境界を横断確認する。
  - 各Classについて「含めるもの / 含めないもの / 想定Knowledge / representative examples / counterexamples」を整理する。
  - 各Classの専用Facet候補と、common Facetだけで十分なClassを区別する。
  - KnowledgeをFacetへ置くべきか、独立Object / typed attribute / Relation / Statementへ置くべきかの境界を明記する。
  - `overall`を未設計Knowledgeの恒久的な逃げ場にせず、専用Facet不足によるClass意味幅の膨張を検出する。
  - 成果物: `docs/design/FACET_TAXONOMY_SURVEY.md`
  - Migration 003の62 Classとsurvey rowを機械比較し、62/62、欠落0、重複0を確認した。
  - Structural / Additional-only Classも省略せず、直接profile不要またはfamily-level inheritance候補として明示した。
  - 近義Facet候補、Relation / Attributeへ出す情報、E-02C gold case論点をE-02B / E-02Cへ引き渡した。

- [x] **E-02B [P0] Facet vocabularyを横断統合する**
  - E-02Aで列挙したFacet候補をClass横断で比較し、`purpose / function / role / usage / application`等の近義語乱立を検出する。
  - shared Facet / Class-specific Facet / ancestorから継承するFacetを区別する。
  - 同一意味を複数Facet IDへ分裂させない命名・再利用ルールを確定する。
  - cross-class Facet similarityで比較価値のあるFacetを可能な範囲で共通Registry entryへ統合する。
  - 初期18 Facet seedの維持・追加・名称整理を検証し、必要なRegistry変更案を確定する。
  - 成果物: `docs/design/FACET_VOCABULARY_REVIEW.md`
  - 初期18 Facetはstable ID / keyを含め全件維持し、意味境界だけを明確化した。
  - E-02Aの局所候補を横断統合し、E-02Cで検証するfreeze候補を既存18 + 新規37 = 55 Facetへ整理した。
  - `purpose / function / usage`、`history / chronology`、`effects / implications`等、検索上の意味差が大きい近義語は意図的に分離した。
  - Relation / typed attributeへ置く候補をFacet IDから除外し、parent / Structural Classを利用するprofile inheritance案を確定した。
  - Migration 004は変更せず、E-02C通過後に新しいadditive migrationでRegistry / profileを反映する方針とした。

- [x] **E-02C [P0] Class / Facet境界gold casesを作成する**
  - 全62 Classについて少なくともpositive / negative Class例を用意し、Class意味境界を試験可能にする。
  - 代表KnowledgeについてFacet / Object / Attribute / Relation / Statementの期待配置をgold caseとして記録する。
  - ancestor profile inheritance、専用profileなしClass、cross-class shared Facet、意味的に不正確なfallback禁止を含める。
  - E-05 Result Validator、I-07検索品質gold、N-01/N-02 testへ再利用可能な形式にする。
  - Facet taxonomy変更時にgold casesでregressionを検出できるようにする。
  - 成果物: `docs/reference/CLASS_FACET_GOLD_CASES.md` と `tests/fixtures/class_facet_gold_cases.json`。
  - 初期62 Classを62/62 coverageし、各Classのpositive / negative例と代表Knowledge配置をfixture化した。
  - 近義Facet、inheritance、Relation / Attribute境界、fallback禁止等を25件のcross-cutting boundary caseとして固定した。
  - E-02Bの55 Facet freeze候補に矛盾がないことを確認し、Facet taxonomyを55 Facetでfreezeした。
  - `005_facet_taxonomy_freeze.sql`で新規37 Facetと169 profile rowをadditiveに反映し、Registryを55 Facet / 188 profile rowへ更新した。
  - `tests/test_class_facet_gold_cases.py`を追加し、Class Registry・Facet Registry・profile inheritance・gold fixtureの整合を回帰試験化した。

**E-02 follow-up Gate:** E-02A〜E-02Cは完了し、Facet taxonomyは55 Facetでfreeze済み。Migration 005でFacet Registry / Class profileへ物理反映した。E-03以降はこのtaxonomyを前提とし、変更時はgold fixtureでregressionを確認する。

- [x] **E-03 [P0] Source / Evidence / Evidence Link / Provenance schemaを設計する**
  - Source Identityと0..N locator、Snapshot、Raw Artifact、Normalized Run、Evidenceの物理schemaをB-03要件から設計する。
  - 既存`url UNIQUE`前提を解消し、既存`source_id` / `snapshot_id` / `evidence_id`を可能な限り維持するmigration契約を定義する。
  - resource type / media type / document genre / publisher kind等のSource分類と、Source↔Objectごとのsubject relationshipを物理的に分離する。
  - Object/Facet/Relationから具体的Evidence IDを経由してRaw / Sourceまで遡れるようにする。
  - Evidence generation / location / extraction mode / content hash / provenance integrityを表現する。
  - ChatGPT出力が存在しないEvidence / Source IDを参照できないValidationを定義する。
  - Knowledge Statement / structured attribute / RelationからEvidenceへのLinkと、`supports` / `contradicts` / `contextualizes`等のEvidence roleを表現する。
  - 標準ResultのEvidence referenceが入力Package manifestに含まれることをValidation可能にする。

  - 成果物: `docs/design/SOURCE_EVIDENCE_SCHEMA.md`。
  - Migration 006でURL等から独立した`source_records` + 0..N `source_locators`、Snapshot / Raw Artifact / Normalization Run / Evidenceのcanonical provenance chainをadditiveに追加した。
  - 旧Prototypeの`sources / snapshots / artifacts / normalized_runs / evidence`は破壊せず、Phase Lで既存`source_id / snapshot_id / evidence_id`を可能な限り維持して移行できる共存構造とした。
  - Source classificationの各axisとcaptured / deterministic / inferred / override provenanceを、Source↔Object associationの`subject_relationship`から物理的に分離した。
  - Source dependency Registry、Evidence location / extraction mode / content hash、Provenance immutability guardを追加した。
  - Statement / structured attribute / RelationからEvidenceへの`evidence_links`と、`supports / contradicts / contextualizes` Evidence Role Registryを追加した。
  - Facet自体へEvidence一覧を直接bindせず、Facet内Knowledge Statementをgrounding単位とする契約を確定した。
  - Source / Evidence ID存在確認と、将来Package manifestのEvidence集合を入力してPackage外参照を拒否できるstorage validation primitiveを追加した。

- [x] **E-04 [P0] Versioningを設計する**
  - Final Object Dataは上書きではなくVersion追加を基本とする。
  - B-04のfull snapshot Resultを次期Version候補として扱う。
  - package / base version preconditionとstale Result処理を定義する。
  - omission / deletion semantics、current切替、rollback、Diff境界を定義する。
  - Version切替時にSearch Representation / Vector Indexをinvalid/updateする境界を定義する。
  - 同一Embedding Space + representation hashによるVector reuseを許容しつつ、Version membershipとcurrent / historical scopeを分離して追跡する。
  - Persistent Version IDはSGOKB側で発行する。
  - accepted Versionを論理immutableとし、Version commit / current切替とpost-import derived jobをfailure domainとして分離する。
  - process interruption時にincomplete Versionをcurrentが指さないtransaction / recovery contractを定義する。
  - 成果物: `docs/design/VERSIONING_SCHEMA.md`。
  - Migration 007で`candidate / accepted / abandoned` lifecycle、base Version、Version Classification snapshot、append-only Version event、derived state trackingをadditiveに追加した。
  - `accepted`と`current`を分離し、historical Versionもacceptedのまま保持する。rollbackは過去accepted Versionへcurrent pointerを戻すだけで、Version content / lifecycleを変更しない契約とした。
  - 標準Versionをfull snapshotへ固定し、`version_number`をObject内の作成順序、`base_version_id`をlineage / stale preconditionとした。rollback後は例として`v4 / base=v1`のbranchを許容する。
  - candidate作成時のPrimary / Additional Class snapshotを保存し、baseまたはClassificationがaccept前に変化したcandidateをstaleとして拒否する。
  - accepted / abandoned後はStatement / Attribute / Relation / Facet / temporal scope / Evidence Link / Classification snapshotをDB triggerでimmutableにした。
  - acceptance時に`content` FacetのStatement存在と、Statement / known Attribute / RelationのEvidence Linkを必須とした。Package membership等のResult-level validationはE-05 / H-01へ分離した。
  - candidate acceptance + current promotion + derived target state更新を1 SQLite transactionとし、Embedding / Vector / rendering実処理を別failure domainへ分離した。
  - `object_derived_states`のrevision tokenで古いworkerのlate completionが新current stateを上書きしない契約を追加した。
  - pre-E-04 `object_versions`はMigration 007適用時にacceptedとしてbackfillし、既存current pointer / Version IDを維持するupgrade contractを確認した。

- [x] **E-05 [P1] JSON Schemaを作成する**
  - 共通Object Result schema。
  - Class別extension schema。
  - Primary / Additional ClassがClass Registryに存在することをValidationする。
  - 専用extension未実装のClassでも共通schemaを利用可能とし、別Classへの自動fallbackを要求しない。
  - ChatGPTへ渡す出力契約とImport Validatorで同一Schemaを利用する。
  - Object Result Envelope、package/base Version binding、generation provenanceをSchema化する。
  - Knowledge Statement / derivation kind / reported-view attribution / Evidence role、Knowledge language / temporal scope、Facet / attribute / Relation、conflict / gap、unresolved reference / Registry proposalを表現する。
  - partial / insufficient evidence状態を処理失敗と区別する。
  - 成果物: `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`、`src/sgokb/exchange/schemas/object-result-v1.schema.json`。
  - Object Result schema versionを`sgokb.object-result/1.0`、JSON Schema dialectをDraft 2020-12として固定した。
  - 単一のcanonical base SchemaをChatGPT出力契約とImport Validatorで共有し、`ObjectResultContract`でtarget / Package / base Version / Classification / effective Facet profileをruntime合成する方式を採用した。
  - full snapshot Resultではeffective Facetをちょうど1回ずつ全件明示し、`content / insufficient_evidence / not_applicable / not_analyzed`でomission ambiguityを解消した。
  - Statement / known Attribute / RelationのEvidence grounding、`reported_view` attribution、temporal scope、conflict / gap / unresolved reference / Registry proposalをSchema化した。
  - persistent Version IDをResultから排除し、unknown fieldを原則rejectする。未登録Objectは`unresolved_references`、Registry変更候補は`registry_proposals`へ分離した。
  - Class固有差分はFacet / Attribute / RelationのRegistry contractを基本とし、真に固有構造が必要な場合だけregistered `class_extensions`を利用する。専用extensionなしClassもcommon Schemaで有効とした。
  - `collect_evidence_ids()`を追加し、H-01がE-03のEvidence存在 / Package membership / Provenance validationへ接続できる境界を用意した。
  - E-05 focused test 15件、full suite 137件を通過した。Migration追加はなくschema migration countは7のままである。

**Phase E完了条件:** ChatGPT出力、DB、検索、MCPの共通契約となるObject schemaが確定した。E-01〜E-05は完了し、Phase E — Object Knowledgeデータモデルを完了とする。

---

# Phase F — Source / Evidenceパイプラインの簡略化

**Phase F開始準備（2026-10-12）:** Phase Eを再監査しE-01〜E-05の未完了Taskが0件であることを確認した。D-05 Wave 2として`importer.py / extraction.py / context.py`を`src/sgokb/ingestion/`へstructural-onlyで移動し、旧top-level pathはcompatibility shimとして保持した。既存Prototype ingestionとE-03 canonical Source / Evidence contractのgap、Source resolution / effective Snapshot・Run selection、F-01実装順序を`docs/planning/PHASE_F_PREPARATION.md`へ整理した。behavior / schema適応はF-01へ分離している。

- [x] **F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する**
  - B-03 / E-03で定義したSource Identity / locator / Snapshot / Raw Artifact / Normalized Run / Evidence契約へ既存pipelineを接続する。
  - Raw Artifactを原資料として維持し、EvidenceをRawと同一視しない。
  - 既存`source_id` / `snapshot_id` / `evidence_id`とProvenanceを可能な限り維持する。
  - 旧`source_type` / Page Context metadataを新分類軸へbest-effort mappingまたはlegacy保持する。
  - 最新Snapshotを無条件にeffectiveとしないselection policyを設計する。
  - **完了（2026-10-12）:** `Application.import_source_path()` / `process_source_snapshot()`としてlegacy pathと分離したcanonical ingestion use caseを実装した。URL/canonical URLはIdentityではなくresolution signalとして扱い、曖昧一致をrejectする。`capture_id`をSnapshot IDとして維持し、Bundle内全Raw Artifact、Normalization Run、Evidence、DOM/heading/block-order locationをcanonical `SourceRepository`へ保存する。Migration 008でappend-only `source_selection_events`を追加し、最初のusable Snapshot / successful Runのみ自動選択、後続世代はmanual selectionなしにeffectiveへ昇格しない方針を確定した。failed generationはeffectiveへ昇格しない。旧`import_path()` / `process()`は変更せず、dual-writeもしない。設計正本: `docs/design/SOURCE_INGESTION_PIPELINE.md`。

- [x] **F-02 [P0] 標準パイプラインからFragment生成を外す**
  - `fragment`を必須工程から除外する。
  - 互換・研究用途として残すか完全廃止するかを決定する。
  - **完了（2026-10-12）:** canonical標準経路をSource / Snapshot / Raw Artifact → Normalization Run → Evidenceで停止するよう固定した。CLIの`import` / `process` / `status` / `snapshots`はcanonical側を標準動作とし、旧Prototype経路は`--legacy`でのみ選択する。Fragment / Final /旧benchmarkは`legacy-fragment` / `legacy-generate` / `legacy-benchmark`へ明示し、旧command名はPhase Lまでcompatibility aliasとして保持する。`Application`にも`legacy_*` APIを追加し、旧method名はshimとして維持する。標準処理ではFragment・`ai_runs`・旧Final artifactを生成しない。物理`_legacy/`移動や削除はModule Migration PolicyどおりPhase Lへ残す。設計正本: `docs/design/STANDARD_PIPELINE_BOUNDARY.md`。

- [x] **F-03 [P0] Object Evidence Retrievalを実装する**
  - name / alias / explicit association / Source metadata / FTS / embeddingを組み合わせる。
  - 高Recall優先とし、最終的な意味判断はChatGPTへ渡す。
  - Evidence選択理由（explicit link / name / alias / FTS / semantic / manual等）を追跡可能にする。
  - **完了（2026-10-12）:** `ObjectEvidenceRetriever`と`Application.retrieve_object_evidence()`を追加し、Fragmentを介さずcanonical `evidence_records`を直接検索する標準Retrievalを実装した。既定scopeはF-01で選択されたeffective Snapshot / Runのみ。`confirmed / candidate / excluded` Source↔Object association、Object name / alias、effective Source metadata、Migration 009のcanonical Evidence FTS、明示設定されたEmbedderによるsemantic cosine、manual include / excludeを統合する。各候補は複数のselection reasonと補助scoreを保持し、ranking scoreをtruth / confidenceとして扱わない。Generative LLMは呼ばない。semanticはPhase Iまでのon-demand baselineとし、永続Vector Indexは先取りしない。設計正本: `docs/design/OBJECT_EVIDENCE_RETRIEVAL.md`。

- [x] **F-04 [P1] Evidence Selectionのtoken/size budgetを設計する**
  - Evidence granularityはsection / paragraph / table / post等のSource構造を優先し、固定文字数だけで決めない。
  - 1 Objectで無制限に全Evidenceを出力しない。
  - Source多様性と関連性を維持しつつPackageを構築する。
  - chunk overlap /近接Evidenceの扱いを設計する。
  - 切り捨て理由を追跡可能にする。
  - **完了（2026-10-12）:** `EvidenceBudget` / `EvidencePackageSelector`と`Application.select_object_evidence()`を実装した。推定token / UTF-8 byte / item数をhard limitとし、初期defaultは12,000 estimated tokens / 65,536 bytes / 64 Evidenceとする。manual includeはprotectedとしてsilent omissionせず、Source diversity pass後にF-03 relevance順で残余budgetを充填する。canonical Evidenceは再chunkせず、Source構造由来の`structure_group`と近接Evidence関係を保持する。exact duplicate、同一Sourceのnear-duplicate、高overlap chunkはPackage-localに抑制し、budget / duplicateによる非採用理由をEvidence単位で記録する。F-03 selection reasonとProvenanceは保持する。設計正本: `docs/design/EVIDENCE_SELECTION_BUDGET.md`。

- [x] **F-05 [P1] ObjectとSource/Evidenceの明示linkを維持できるUI/CLIを設計する**
  - Source↔Object associationのcandidate / confirmed / excludedを扱えるようにする。
  - 自動検索候補 + 人間による追加/除外を許可する。
  - Objectごとのsubject relationship等のassociation metadataを扱えるようにする。
  - **完了（2026-10-12）:** canonical `source_object_associations`をoperator操作へ接続し、`Application.list/set/clear_source_object_association()`とread-only `suggest_source_associations()`を追加した。CLIに`association list/suggest/set/clear`を追加し、manual操作は`origin_kind=manual`としてcandidate / confirmed / excluded、`subject_relationship`、noteを維持できる。自動suggestionはF-03 Evidence候補をSource単位に集約するだけで永続化しない。Evidence単位overrideは`evidence candidates/select --include-evidence/--exclude-evidence`からF-03/F-04へ渡し、Packageごとのselection controlとして扱う。Source association、Package selection override、Knowledge `evidence_links`を別責務として固定し、legacy `entity link`へ依存しない。設計正本: `docs/design/OPERATOR_ASSOCIATION_CONTROLS.md`。

**完了条件:** 生成LLMなしでObjectに関連するEvidence Packageを作成できる。

---

# Phase G — Google Drive / ChatGPT交換ワークフロー

- [x] **G-01 [P0] Object Evidence Package formatを確定する**
  - 更新Packageではcurrent Knowledgeを評価・carry-forwardできるよう、現Versionが参照するEvidenceを必要に応じて含める。
  - Package外Evidenceを標準Resultが引用しないB-04契約とtoken budgetを両立させる。
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

- [x] **G-02 [P0] `manifest.json` schemaを定義する**
  - object_id / primary_class / additional_classes / name / aliases。
  - package version。
  - included sources/evidence IDs。
  - extraction timestamp。
  - expected result schema version。
  - package identity / manifest hash / base Object Knowledge Version等、Result bindingに必要なprecondition。

- [x] **G-03 [P0] ChatGPT用`instructions.md`を設計する**
  - Primary Class / ancestor Class別の分析目的。
  - Fact / synthesis / interpretationの区別。
  - Evidence ID参照ルール。
  - Relation生成ルール。
  - 不明情報を創作しないルール。
  - `direct_statement` / `synthesis` / `interpretation` / `reported_view`相当のderivation区分。
  - Package外Evidence IDや未知Object IDを創作しないルール。
  - Evidence不足・矛盾・unresolved referenceを構造化して返すルール。

- [x] **G-04 [P0] Local Package staging / Google Drive export方式を実装する**
  - Package Buildはまずlocal stagingへ生成し、External Exportと分離する。
  - 初期版は明示export → Drive同期フォルダでも可。同期対象directoryへのwriteもExternal Exportとして扱う。
  - export前にpackage identity / target Object / file・Evidence scope / warning / destinationをpreflight表示可能にする。
  - B-07の`allow / review_required / blocked`相当export decisionを扱い、credential / secretを標準Packageへ含めない。
  - SGOKB本体をGoogle Drive APIへ強く依存させるかは別途判断する。

- [x] **G-05 [P1] Result受け取り運用を定義する**
  - `result.json`必須。
  - MarkdownをChatGPTに作らせる場合も正本にはしない。
  - 手動配置場所とvalidation triggerを定義する。
  - Result検出 / Validationは自動化可能だが、検出だけを理由にauthoritative Importしない。
  - Google Drive / ChatGPT手動工程の開始・返却・失敗時運用を1 Object単位で定義する。

**完了条件:** APIを利用せず、ユーザーがChatGPTとの手動工程を介して1 Objectを往復できる。

Phase G completion: `docs/planning/PHASE_G_COMPLETION.md`

---

# Phase H — Result Validation / Import / Rendering

- [x] **H-01 [P0] Result JSON Validatorを実装する**
  - Syntax / Schema、Binding / Precondition、Referential、Grounding / Provenance、Domain Contract Validationを分離する。
  - object_id / package / base Version一致。
  - Source/Evidence ID存在確認 + Package membership確認。
  - Facet / attribute / Relation Type contractを確認する。
  - Relation target存在確認または未解決参照として明示管理。
  - 不正field / schema version拒否。
  - Validatorが意味内容や未知IDを推測修復しない。
  - `ResultValidationService`でG-05 immutable receiptを検証し、`pending -> running -> valid/invalid/error`を監査保存する。
  - `docs/design/RESULT_VALIDATION.md`をH-01設計・実装正本とする。

- [x] **H-02 [P0] Object Version Importを実装する**
  - Validation成功後も標準ではexplicit Import operationを要求し、Result検出だけでsilent commitしない。
  - normal ResultではImport開始後のVersion発行 / current切替 /派生Index更新を追加confirmationへ過剰分割しない。
  - stale Resultは通常Importをblockし、partial / limited Resultはreview-requiredを既定とする。
  - Validation成功後のみDBへcommitする。
  - 既存currentを破壊しない。
  - Import run / timestamp / source package / original Result artifact provenanceを記録する。
  - Persistent Version IDをSGOKB側で発行し、同一Resultの重複Import候補を検出する。
  - Registry proposalをObject Knowledge Importの副作用として自動適用しない。
  - process interruption / retryに対してtransaction-safeかつidempotentにし、incomplete Versionをcurrentへ昇格させない。
  - canonical commit後のEmbedding / Index等はpending / ready / failed / stale相当の独立derived jobとして扱う。
  - `ObjectVersionImportService`でH-01 valid receiptを明示Importし、candidate作成からcurrent promotionまでを単一transaction化する。
  - Import provenance / Validation snapshot / Result review metadataをMigration 013でimmutableに保持する。
  - `docs/design/OBJECT_VERSION_IMPORT.md`をH-02設計・実装正本とする。

- [x] **H-03 [P1] Markdown Rendererを実装する**
  - DB/JSONから人間向けObject文書を生成する。
  - Markdownを編集正本にしない。
  - accepted VersionからSummary / Facet / Attribute / Relation / temporal scope / attribution / Evidence / Import provenanceを含むMarkdownを生成する。
  - managed artifactをatomic writeし、current targetの`rendering` derived stateをrevision CAS付きで`ready / failed`へ更新する。
  - historical Version renderとJSON pure renderはcurrent derived stateを変更しない。
  - `docs/design/MARKDOWN_RENDERER.md`をH-03設計・実装正本とする。

- [x] **H-04 [P1] Diff / Review表示を実装する**
  - v1→v2の属性・Facet・Relation差分を確認できるようにする。
  - stale / partial / destructive omission / Registry proposal / Identity ambiguity等のreview-required reasonを表示する。
  - 手動承認を採用する場合の状態遷移を定義する。
  - full snapshotで消えるStatement / attribute / Relation、conflict、Registry proposal、stale baseを目立たせる。
  - immutable Result receiptとbase VersionのImport前Review Preview、およびaccepted Version同士のhistorical Diffを実装する。
  - destructive omissionをStatement / Attribute / Relation削除、Facet content downgrade、Conflict / Registry proposal消失としてdeterministicに検出する。
  - H-01 findingsを再利用し、`blocked / review_required / ready_to_import / imported`を表示する。
  - Conflict存在単独ではImport blockせず`attention`として可視化する。
  - manual acceptanceはH-02 `--acknowledge-review`へ接続し、H-04専用の孤立approval stateを作らない。
  - `docs/design/DIFF_REVIEW.md`をH-04設計・実装正本とする。

**完了条件:** ChatGPT出力を壊れた状態で正本DBへ登録できず、過去versionへ戻れる。

Phase H closure audit: `docs/planning/PHASE_H_CLOSURE_AUDIT.md`

---

# Phase I — 意味検索・類似検索

Preparation: `docs/planning/PHASE_I_PREPARATION.md`

- [x] **I-01 [P0] Search Representation / Embedding対象を設計する**
  - Evidence representation / embedding。
  - Object overall representation / embedding。
  - Facet representation / embedding。
  - accepted検索可能Knowledge Statementの個別representation / embeddingを標準対象とする。
  - 必要に応じRelation text representation。
  - Statement単体で文脈不足の場合、Object / Class / Facet / temporal scope等を付加するContextual Search Representation Builderを設計する。
  - representation kind / Object Version / Facet / Statement membership / Evidence generation / builder version / content hashを追跡する。
  - `gap` / `insufficient evidence` / `unresolved reference` / Registry proposalは通常Statement Semantic Indexへ入れない。
  - **完了 (2026-10-13):** `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`を正本とし、`object_overall / facet / statement / evidence`、content identity / membership分離、current/historical境界、deterministic Builder、Evidence別membership familyを確定した。
  - migration `014_search_representations.sql`、`SearchRepresentationBuilder`、focused regression testsを実装した。Embedding model / backend / fusion / rerankerは後続Taskへ明示的に留保する。

- [x] **I-02 [P0] Embedding Provider / 多言語Modelを比較する**
  - 日本語を含むSGOKB実データで評価する。
  - FastEmbed等のlocal provider adapterと、BGE-M3等のmodel候補を分離して評価する。
  - Object / Facet / Statement / Evidenceで同一modelが最適かも確認する。
  - model / revision / dimension / preprocessing / normalization / provider configurationをEmbedding Space metadataへ記録する。
  - Vector backend比較時はEmbedding Spaceを固定し、model比較とbackend比較を混同しない。
  - **完了 (2026-10-13):** `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`を正本とし、ProviderとModelを分離して初回候補Qwen3-Embedding-0.6B / 4B、multilingual-e5-large-instruct、BGE-M3、FastEmbedを評価した。
  - 2026年追加候補としてHarrier OSS v1 0.6B、Jina Embeddings v5 Text Small、Nemotron 3 Embed 1B / 8B、EmbeddingGemma 2を同一4,851 representation / 26 QueryのExact条件で実測した。Gemini Embedding 2も試験対象へ追加したが、API key未設定のため実測blockedとしてharness / statusを記録した。
  - 追加試験の結果、Phase I共通baselineを`sentence-transformers + microsoft/harrier-oss-v1-0.6b`、revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`、native/output 1024次元、L2 normalize、max 32768 token、overflow=`reject`へ更新した。外部Providerへのsilent fallbackは行わない。
  - `Nemotron-3-Embed-8B-BF16`は今回最高品質のquality ceiling / reference profile、`multilingual-e5-large-instruct`はshort Statement高速profile、Jina v5はlicense上benchmark/reference profileとして保持し、複数Embedding Spaceの正式採否はI-07へ留保した。
  - Migration `015_embedding_spaces.sql`、`EmbeddingSpaceSpec`、`EmbeddingRepository`、`SentenceTransformerEmbeddingProvider` / `FastEmbedEmbeddingProvider`、Float32 Exact cosine baselineを実装した。default local profileとoptional dependency条件をHarrier / sentence-transformers 6.1+へ更新した。
  - I-03ではHarrier 1024-dim Embedding Spaceを固定し、Vector backendのみを比較する。

- [x] **I-03 [P0] VectorIndexAdapterを設計しBackendを比較決定する**
  - SQLiteをcanonical Knowledge Storeとし、Vector backendを再構築可能なDerived Search Indexとして分離する。
  - `VectorIndexAdapter`相当の共通契約でupsert / search / filter / invalidate / rebuild / metadata取得を抽象化する。
  - SQLite系Float32 Exact / FlatをANN Recallの基準にする。
  - sqlite-vectorのFloat32 / quantized条件をbaseline候補として評価する。
  - sqlite-vecをSQLite内軽量backend候補として評価する。
  - LanceDB ANNをserver不要のembedded ANN候補として評価する。
  - Qdrant HNSW + payload filter + Object groupingを高性能 / 高機能基準として評価する。
  - Query latency、Statement/Object Recall@K、Exactに対するANN Recall、Index build/update/rebuild時間、RAM、disk size、Windows運用コストで比較する。
  - 実測前に最終backendを固定しない。
  - Vector backend停止 / Index消失時もcanonical read / Lexical Searchを継続し、SQLite正本からfull rebuildできることを必須とする。
  - local provider失敗時にexternal providerへsilent fallbackしない。
  - **完了 (2026-10-13):** `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`を正本とし、30,000件 / 1024次元固定fixtureでNumPy Exact、sqlite-vec、SQLite-Vector Exact / TurboQuant、LanceDB、Qdrant HNSWを比較した。
  - 標準backendをlocal Qdrant HNSWへ固定した。実測profileはQdrant server 1.19.2、`m=16`、`ef_construct=128`、`hnsw_ef=256`で、無filter / 1-of-8 hard filterともExact top-10に対しRecall@10 100%を確認した。LanceDB 0.40.0はserver不要の第2候補として保持する。
  - `VectorIndexAdapter`、`VectorIndexPoint`、`VectorSearchFilter`、`VectorSearchHit`、`VectorIndexMetadata`と`QdrantVectorIndexAdapter`を実装した。Embedding Spaceごとにcollectionを分離し、hard filterをQdrant payload filterへ渡す。
  - Windowsの深いstorage pathで64桁space hashをcollection名へ直接使うとpath errorが発生したため、物理collection名は96-bit prefixへ短縮し、full `space_id`をcollection metadataへ保存・照合する方式を採用した。
  - Qdrant停止 / Index消失時もcanonical SQLite / Lexical Searchを維持し、silent backend fallbackを禁止する。Vector IndexはSQLiteのSearch Representation / Embedding cacheからfull rebuild可能なDerived Search Indexとする。

- [x] **I-04 [P0] Multi-representation Hybrid Search / Object Aggregationを実装する**
  - FTS + Object / Facet / Statement vector searchを組み合わせる。
  - Statement-level hitを内部candidateとして扱い、通常Object検索は1 Object = 1結果へ集約するObject Aggregatorを実装する。
  - matched Statement / Facet / representative snippet / groundingをresult detailとして保持する。
  - 同一Objectの多数Statement hitを単純合計して無制限boostしない。best hit / top-N capped contribution / Facet diversity等をgoldで比較する。
  - primary/additional/ancestor class / facet / version / temporal scope等のhard filterをcandidate生成前に適用可能にする。
  - exact name/aliasをSemantic Searchより優先できるようにする。
  - current accepted Knowledgeを既定scopeとし、historical Statement Vectorをsilent混合しない。
  - lexical / Object / Facet / Statement各channelのfusionとmatch reasonを説明可能にする。
  - **完了 (2026-10-13):** `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`を正本とし、Registry / Knowledge Lexical + Object / Facet / Statement SemanticをObjectへ集約する`HybridObjectSearch`を実装した。
  - raw BM25 / cosineを直接加算せず、RRF (`k=60`)をbaselineとした。Object overall / Facet / Statement / Knowledge Lexicalの同一Object内contributionを1 / 2 / 3 / 3へcapし、exact name / aliasは別priority tierでsemantic resultより優先可能とした。
  - Primary / Additional / ancestor Class、Facet、accepted Version、derivation、temporal scope / valid-atをcandidate generation前のhard filterとして実装した。current accepted Knowledgeが既定で、historicalは明示Versionだけを検索する。
  - Migration `016_hybrid_search.sql`でSearch Representation FTS5を追加し、1〜2文字日本語queryはliteral fallbackする。Knowledge Vector Indexはmembership-scoped pointとし、Embedding content reuseを維持したままcurrent/history/filter identityを保持する。
  - Qdrant adapter integrationを含むfocused testsを追加し、semantic backend障害時はSemantic modeをexplicit failure、Hybrid modeをLexical + `degraded_channels`として扱う。別Vector backend / external providerへのsilent fallbackは行わない。

- [x] **I-05 [P0] `find_similar_objects`を実装する**
  - overall similarity。
  - 既定candidate scopeは同じPrimary Classとし、cross-classは明示拡張とする。
  - facet指定similarity。
  - missing Facetを0 similarityやoverallへsilent fallbackしない。
  - scoreとmatched facet / target Versionを返せる構造。
  - **完了 (2026-10-14):** `docs/design/OBJECT_SIMILARITY_SEARCH.md`を正本とし、`ObjectSimilaritySearch.find_similar_objects()`でObject overall / Facet similarityを実装した。
  - Sourceの保存済みSearch Representation EmbeddingをQuery Vectorとして再利用し、Providerへ再Embeddingしない。overallは`object_overall`同士、Facet指定時は同一Facet同士だけをdirect cosineで比較する。
  - 既定candidate scopeをsource Versionと同じPrimary Classのcurrent accepted Objectへ固定し、`cross_class=True`時だけ明示的にClass境界を外す。Source Object自身はVector candidate生成前に除外する。
  - Source missing Facetは明示error、Candidate missing Facetは候補外とし、overall / 別Facet / score=0へのsilent fallbackを禁止した。accepted historical source Versionも明示指定可能とした。
  - Resultへcosine score、matched Facet、candidate target Version、representation / membership identityを保持する。Vector filterへ後方互換の`excludes`を追加し、Qdrant `must_not`へ変換する。

- [x] **I-06 [P1] Reranker / second-stage retrievalを評価する**
  - 初期版MVPには必須としない。
  - FastEmbed等で利用可能なCross Encoderを含め候補を比較する。
  - first-stageで取得できなかったObjectをrerankerは救えないため、Statement Recallを先に評価する。
  - retrieval品質とlatencyの実測で導入を判断する。

  - **完了 (2026-10-14):** `docs/design/RERANKER_SECOND_STAGE_EVALUATION.md`を正本とし、Harrier top 50固定candidateでsecond-stage rerankerを比較した。
  - BGE reranker v2-m3はMRR 0.944 / Recall@10 100% / nDCG@10 0.921、50候補p50約35 ms、peak VRAM約1.21 GiB。Qwen3 Reranker 4BはMRR 0.949と僅差で上回るが、p50約607 ms / peak約8.06 GiBのためquality referenceとした。
  - Qwen3 Reranker 0.6B、Jina Reranker v3.5も比較した。Jina v3.5はCC BY-NC 4.0のためresearch/reference扱い。GTE multilingual rerankerは現行Transformers 5.19 / PyTorch 2.8 CUDA環境のcustom runtime互換性問題で実測blockedとした。
  - first-stage candidate Recallはtop 30まで96.2%、top 40 / 50で100%だったため、I-07の暫定rerank depthを50とする。Rerankerはcandidate集合外のObjectを救えないためfirst-stage Recall評価を先行する。
  - 追加model survey後、KaLM Nano/Small R2、Qwen3-VL-Reranker-2B、ZeroEntropy zerank-2を同じtop-50 fixtureで追加実測した。zerank-2がMRR 0.971 / Recall@1 96.2% / nDCG@10 0.953で品質1位、BGEは同runtime再測定でMRR 0.944 / p50約56 ms / peak約1.21 GiBだった。I-07ではBGEをbalanced/default候補、zerank-2をquality候補として比較し、正式gold通過前はHybrid Searchへmandatory second-stageとして組み込まない。

- [x] **I-07 [P0] 検索品質gold / Backend benchmarkを作成する**
  - Character / Work / Conceptに加え、Person / Organization / Series / Place / EventとLater support Classの代表Queryを用意する。
  - Facet全体では薄まりやすい細粒度Statement Query、条件・例外・時系列Queryを明示的に含める。
  - 日本語Queryとcross-lingual Queryを含める。
  - Statement Embeddingあり / なしを比較し、細粒度Recall改善を確認する。
  - lexical / semantic / hybrid / overall similarity / facet similarity / Evidence Searchを比較する。
  - Float32 Exact結果をANN backend評価のreferenceにする。
  - exact lookup、Statement Recall@K、Object Recall@K、ANN Recall@K、MRR、nDCG、filter correctness、current/historical isolation、人間Similarity評価を記録する。
  - latency / index size / build / incremental update / rebuildを同一workloadで測定する。
  - **完了 (2026-10-14):** `benchmark/search-quality-gold-v1.json`、`scripts/run_search_quality_gold.py`、`scripts/run_vector_backend_benchmark.py`、`scripts/run_search_gold_reranker_benchmark.py`を追加し、正式gold / harnessを固定した。Hybrid Object SearchはMRR 1.000 / Recall@10 100%、Statement Recall@10 100%、exact lookup 100%、filter/current-history/temporal contract 5/5を確認した。
  - human-authored Similarity goldではoverall MRR 0.833 / Recall@10 100%、Facet-specific MRR 1.000。Evidence Searchはlexical/association・semanticともMRR 1.000。Statement Embedding有無は20 Object goldではObject-level差が未観測だったため、標準representationは維持しつつN-06で実データscale再評価とした。
  - 100k / 1024-dim backend benchmarkでNumPy Float32 ExactとQdrant HNSWを比較し、I-03の`hnsw_ef=256`を100k tuning結果に基づき`768`へ更新した。build / 100-point update / full rebuild / disk sizeを同一workloadで記録した。
  - formal reranker goldではBGE / zerank-2ともObject MRR 1.000。BGEをbalanced/default候補、zerank-2をquality候補として維持し、MVP mandatory rerankerとはしない。設計正本: `docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`。

**完了条件:** 「文字列が一致するObject」だけでなく、「意味・価値観・テーマ等が近いObject」を実用精度で取得できる。

**Phase I closure（2026-10-14）:** I-01〜I-07の未完了Taskが0件であることを再監査し、正式gold・100k Backend benchmark・回帰試験結果を`docs/planning/PHASE_I_CLOSURE_AUDIT.md`へ固定した。Phase IをCompleteとし、`docs/planning/PHASE_J_PREPARATION.md`でJ-01開始条件とApplication / Retrieval / MCP境界のgapを整理した。

---

# Phase J — MCP Knowledge Access Layer

Preparation: `docs/planning/PHASE_J_PREPARATION.md`

- [x] **J-01 [P0] Retrieval CoreとMCP Adapterを分離する**
  - MCPからSQLiteへ直接SQLを公開しない。
  - CLIとMCPが同じApplication/Retrieval APIを使用する。

- [x] **J-02 [P0] MCP read toolsを定義する**
  - `search_objects`
  - `semantic_search_objects`
  - `find_similar_objects`
  - Facet similarity相当の検索機能
  - `get_object`
  - `get_objects`
  - `get_object_relations`
  - `get_object_evidence`
  - `search_evidence`
  - `build_context` または同等機能。
  - **完了 (2026-10-14):** `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`を正本とし、active read Toolを`search_objects` / `find_similar_objects` / `get_object` / `get_objects` / `get_object_relations` / `get_object_evidence` / `search_evidence`の7個へ整理した。
  - `semantic_search_objects`は重複Tool化せず`search_objects(mode="semantic")`、Facet Similarityは`find_similar_objects(facet=...)`で表現する。`build_context`はJ-04まで予約・非activeとした。
  - MCP Tool contract `sgokb.mcp-read-tools.v1`、JSON Schema Draft 2020-12、read-only / closed-world annotation、public limitを固定した。general `EvidenceSearch`もApplication境界へ追加し、effective世代を既定・historicalを明示opt-inとした。
  - J-02 + J-01 + Phase I focused regressionはRuff成功、Pytest 38 passed / 2 skipped。

- [x] **J-03 [P1] MCP Resourcesを定義する**
  - 例: `sgokb://object/<id>`。
  - ToolとResourceの責務重複を整理する。
  - **完了 (2026-10-14):** `docs/decisions/J03_MCP_RESOURCE_CONTRACT.md`を正本とし、Resourceを既知stable IDのdereference専用surfaceとして定義した。
  - Resource Templateは`sgokb://object/{object_id}` / `sgokb://object/{object_id}/version/{version_id}` / `sgokb://evidence/{evidence_id}`の3種類。全recordを`resources/list`で列挙しない。
  - Search / filter / batch / Relation traversal / Context selectionはTool側に残し、Resource URIへのquery parameter埋め込みを禁止した。Resource contractは`sgokb.mcp-resources.v1`。
  - `KnowledgeReadApplication.get_evidence()`とMCP Resource Adapterを実装し、Ruff成功、J-03〜J-01 focused regressionは48 passed / 2 skipped。

- [x] **J-04 [P0] Context Builderを設計する**
  - roleplay / comparison / analysis / creative等の用途に応じて返すFacetを制御する。
  - LLM推論は行わず、決定論的なKnowledge selectionを担当する。
  - **完了 (2026-10-14):** `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`を正本とし、Context BuilderをLLM推論から分離したdeterministic Knowledge selectorとして設計・実装した。
  - `general` / `analysis` / `comparison` / `roleplay` / `creative`の固定Purpose Profileを定義し、Facet priority、attributes / relations / evidence refsの既定値を用途別に固定した。明示`facets`はprofileをoverrideする。
  - length controlはmodel依存tokenizerを避け、selected Knowledge itemのserialized JSON character budgetを採用した。Statement途中切断を禁止し、複数Objectではequal-shareで配分する。
  - J-02で予約していた`build_context`をactive MCP read Tool化した。Context Builder contractは`sgokb.context-builder.v1`。
  - Ruff成功、J-04〜J-01 + Phase I focused regressionは55 passed / 2 skipped。

- [x] **J-05 [P1] MCP write系はread系と分離する**
  - 初期MVPではread-onlyを第一候補とする。
  - 将来`propose_object`等を追加する場合もstagingへ限定する。
  - **完了 (2026-10-14):** `docs/decisions/J05_MCP_WRITE_BOUNDARY.md`を正本とし、初期MCP MVPをread-onlyへ固定した。
  - read / writeを別contract・別Adapter境界へ分離し、`MCPWriteAdapter`はMVPでTool 0個・全call拒否とした。
  - future writeはproposal/staging-onlyとし、canonical direct mutation / automatic promotionを禁止した。explicit enable / authorization scope / audit recordを必須policyとした。
  - MCP write policyは`sgokb.mcp-write-policy.v1`、将来Tool contract namespaceは`sgokb.mcp-write-tools.v1`。Ruff成功、J-05〜J-01 + Phase I focused regressionは59 passed / 2 skipped。

- [x] **J-06 [P0] ローカルMCP Clientで受入試験する**
  - Local LLM HostからObject取得。
  - 複数Object取得。
  - Semantic Search / Similarity Search。
  - Context長制御。
  - MCP停止時にcanonical DB / CLIが継続利用できること。
  - loopback外へ公開する場合はexplicit enable + authentication / scopeを要求する。
  - **完了 (2026-10-14):** `docs/decisions/J06_LOCAL_MCP_CLIENT_ACCEPTANCE.md`を正本とし、MCP Python SDK v2のlocal stdio Server bindingとWindows local Client受入試験を実施した。
  - final fixtureは実SQLite Repository / `KnowledgeReadApplication` / Search Representation / `ExactVectorIndexAdapter`を使用し、single/batch Object read、Semantic Search、Similarity Search、Context length control、Resource dereferenceをMCP越しに確認した。
  - MCP subprocess停止時もcanonical Application readとCLIが独立して利用可能であることを確認した。初期MVPはstdio read-onlyでnetwork listenerを持たず、将来の非loopback公開はexplicit enable + authentication / authorization scopeを必須とする。
  - 実測環境はWindows Server 2025 / Python 3.12.10 / MCP Python SDK 2.3.0。Ruff成功、J-06〜J-01 + Phase I focused regressionは61 passed / 2 skipped。
  - J-01〜J-06完了によりPhase J — MCP Knowledge Access Layerを完了した。

**完了条件:** LLM/AgentがDB構造を知らずにSGOKB Knowledgeを取得できる。

---

# Phase K — SGOKB / UPDS連携試験

- [ ] **K-01 [P1] UPDSからSGOKB Objectを参照する最小ユースケースを定義する**
  - 「選択したCharacter群のvalues/personality/themesを取得する」等。

- [ ] **K-02 [P1] Stable Object ID参照を検証する**
  - SGOKB側version更新でUPDS Selection Event参照が壊れないこと。

- [ ] **K-03 [P1] SGOKBとUPDSのSemantic Indexを混同しないことを確認する**
  - SGOKB: World/Object Knowledge。
  - UPDS: Observation/Pattern/Preference Evidence。

- [ ] **K-04 [P2] UPDS向けContext/Profileを追加するか評価する**
  - SGOKB固有にUPDSロジックを埋め込まず、汎用Facet取得で不足する場合のみ追加する。

**完了条件:** UPDSがSGOKB Knowledgeを再解析せず再利用でき、SGOKBはUPDSなしでも独立している。

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

- [ ] **L-05 [P0] 不要依存関係・互換層を削除する**
  - 標準運用から生成LLM Providerが不要になった場合、optional/research dependencyへ降格する。
  - D-05で導入した旧top-level import compatibility shimのうち不要になったものを削除する。
  - Embedding dependencyは維持する。

**完了条件:** 旧Prototypeの高コスト処理が通常運用に残存していない。

---

# Phase M — CLI / 操作フロー

- [ ] **M-01 [P0] 新しいObject中心CLIを設計する**
  - `object add/list/show`
  - `object relate`
  - `package build`（local derived artifact）
  - `package export`（external side effect）
  - `result validate`
  - `result import`（authoritative write）
  - Registry proposal review / apply相当操作
  - `search`
  - `similar`
  - `render`
  - `mcp serve` 等。
  - integrity / derived-index / backup / background-job status確認と、rebuild / restore補助操作を設計する。

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
  - Import → Object / Facet / Statement Embed → Index update → Search。
  - 同一representation hashのVector reuseとVersion scope更新。
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
  - B-06で定義したpre-analysis local segment + post-analysis local segmentを計測対象とする。
  - Source探索 / Capture network、Package human review、Drive sync、ChatGPT操作 /生成待ち、Result返却、review-required判断等のhuman / external時間を分離記録する。
  - Package生成、Validation、Import、Object / Facet / Statement Embedding増分更新、Vector Index更新が目標時間内か確認する。
  - B-07 Reference WorkstationでStandard Objectをp95 10分以内、Large profileを別集計でp95 20分targetとして評価する。
  - cold / warm、model load、storage、retry、Git commit、Embedding Space / backend等のbenchmark metadataを記録する。

- [ ] **N-06 [P0] Retrieval / Vector Backend品質を評価する**
  - Lexical / Semantic / Hybrid / Similarity / Evidence Searchを別々に評価する。
  - Statement Embeddingあり / なしのfine-grained Recall差を確認する。
  - Exact baselineとANN backendのStatement / Object Recall@Kを比較する。
  - Recall@K / MRR / nDCG等を必要に応じ利用する。
  - exact name / alias lookup、Class / Facet filter、current / historical isolationも検証する。
  - Statement → Object AggregationがStatement数の多いObjectを不当にboostしないことを検証する。
  - 類似検索は人間評価も併用する。
  - backend別にlatency / RAM / disk / index build / incremental update / rebuildを比較する。

- [ ] **N-07 [P1] Failure / Recovery試験を行う**
  - 不正JSON。
  - 存在しないEvidence ID。
  - schema version不一致。
  - Embedding model / representation builder変更とfull re-embed。
  - Vector Index消失・破損からSQLite正本によるfull rebuild。
  - Vector backend交換。
  - Result検出後にImport未承認の状態を保持できること。
  - stale / partial Resultがsilent current promotionされないこと。
  - Package Build後、External Export未承認の状態で外部送信されないこと。
  - Derived Index更新失敗後も正本Knowledgeを保持し、stale状態を検出できること。
  - MCP停止。
  - 部分Import失敗 / process killとtransaction recovery。
  - disk full / partial file。
  - Raw欠損 / checksum mismatch / broken provenance isolation。
  - Internet / external service停止時のoffline / graceful degradation。
  - local provider failure時にcloudへsilent fallbackしないこと。
  - backup generation /別path restore / integrity validation / RPO・RTO確認。
  - external exportの`blocked` itemとcredential / log redaction。

**完了条件:** 新しい目的に対する受入条件を満たし、Prototype時代の「Schema適合=品質合格」という評価誤認を避けられる。

---

# Phase O — Documentation / Release / Git cleanup

- [ ] **O-01 [P0] READMEを新SGOKBへ全面更新する**
  - SGOKBの目的。
  - 全体アーキテクチャ。
  - 1 Object標準フロー。
  - ChatGPT手動工程。
  - MCP利用例。

- [ ] **O-02 [P0] 現行設計書を更新する**
  - Architecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundary。
  - Offline / Backup / Restore / Retention / Security / External Egress / Failure Recovery / Benchmark条件。

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
C  SGOKB/UPDS境界
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
 → Object / Facet / Statement embedding
 → semantic/similarity search
 → MCP get_object
```

このVertical Sliceが成立した後に、Work / Concept、UPDS連携、migration、最適化を拡張する。

---

# 4. 最初に実施すべきタスク

Phase A〜Iは完了している。Phase Gは`docs/planning/PHASE_G_COMPLETION.md`、Phase Hは`docs/planning/PHASE_H_CLOSURE_AUDIT.md`、Phase Iは`docs/planning/PHASE_I_CLOSURE_AUDIT.md`をclosure正本とする。

現在はPhase J — MCP Knowledge Access Layerへ移行する。準備内容と開始条件は`docs/planning/PHASE_J_PREPARATION.md`を正本とする。

次の最優先Task:

```text
J-01 [P0] Retrieval CoreとMCP Adapterを分離する
```

J-01ではPhase Iで完成した`HybridObjectSearch` / `ObjectSimilaritySearch`等をApplication read boundaryへ接続し、MCP AdapterがSQLite / Repository / Qdrant固有APIへ直接依存しない構造を先に確立する。Tool名・Resource URI・Context Builder・write capabilityはJ-02以降で確定する。

再設計の正規作業基盤は引き続き`integration/knowledge-base-redesign`である。
