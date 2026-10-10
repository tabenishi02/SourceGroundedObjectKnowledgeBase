# Source Grounded Object Knowledge Base — Knowledge Base 再設計タスク

更新日: 2026-10-11

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

- [ ] **B-07 [P1] 非機能要件を更新する**
  - オフライン継続利用と、外部AI / cloud service停止時のgraceful degradation。
  - Source / Knowledge / Search Representation / Indexの再生成可能性。
  - Raw / Snapshot / Evidence / Result artifact / PackageのProvenance integrityを検証可能にする。
  - 破壊的更新を避けるVersioning。
  - retention / backup / hard deleteでも参照中EvidenceのProvenanceを不用意に破壊しない。
  - Embedding model / Representation Builder / Vector backend変更時のIndex分離・再構築。
  - External Processing / data egressのsecurity / privacy / credential要件。
  - Background job失敗、Index stale / pending / failed時のretry / recovery / graceful degradation。
  - 1 Object local automatic processing 10分目標のbenchmark hardware / workload / percentile条件。
  - MCPが停止しても正本DBが利用可能であること。

**完了条件:** 既存の要件定義書を新方針で置換または新版化し、旧Prototype要件との差分が説明可能である。

---

# Phase C — SGOKB / UPDS責務境界

- [ ] **C-01 [P0] SGOKBをWorld/Object Knowledge Layerとして定義する**
  - Objectそのものの属性・意味・関係・根拠のみを扱う。
  - 「ユーザーが好む」等のユーザー推論を保存しない。

- [ ] **C-02 [P0] UPDSをPersonal Inference Layerとして定義する**
  - Selection Event、Pattern、Preference HypothesisはUPDS所有とする。
  - SGOKBはUPDSを知らなくても単独で成立させる。

- [ ] **C-03 [P1] Conceptの所有境界を確定する**
  - Conceptそのものの定義・Relation・EmbeddingはSGOKBで管理する案を第一候補とする。
  - UPDSはSGOKB Concept IDを参照してPreference Evidenceを構築できるようにする。

- [ ] **C-04 [P1] SGOKB→UPDS連携契約を定義する**
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
│  ├─ OBJECT_REQUIREMENTS.md
│  ├─ OBJECT_TYPE_CANDIDATES.md
│  ├─ OBJECT_TYPE_MODEL.md
│  ├─ OBJECT_TYPE_BOUNDARIES.md
│  ├─ SOURCE_EVIDENCE_REQUIREMENTS.md
│  ├─ OBJECT_RESULT_REQUIREMENTS.md
│  ├─ SEARCH_REQUIREMENTS.md
│  └─ WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md
├─ decisions/
│  ├─ KNOWLEDGE_BASE_REDESIGN_DECISION.md
│  └─ SGOKB_RENAME_DECISION.md
├─ planning/
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
│  └─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
├─ reference/
│  ├─ EMBEDDING_VECTOR_SEARCH_RESEARCH.md
│  ├─ KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md
│  └─ KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md
└─ archive/
   ├─ prototype-0.2/
   └─ rename-2026-10/
```

  - 今後Phase E以降で確定するArchitecture / Data Model / Retrieval / MCP等は、確定時に現行カテゴリを追加する。

- [ ] **D-04 [P0] `src/sgokb`の責務別再編を設計する**
  - 例:

```text
src/sgokb/
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
  - Class Registry / Class hierarchy / Object-Class membershipの物理schema。
  - B-02Dで正式採用したClassを、本番Object投入前に初期Registryへ決定論的にseedする方式。
  - Class Registry包含とClass固有extension実装の有無を独立して管理する方式。
  - 未登録Classが必要なObjectを、意味的に不正確な汎用Classへ自動fallbackさせないstaging / review方針。
  - Object Registry metadataとObject Knowledge Version dataを分離し、Result内Registry proposalを通常Knowledge Importの副作用として自動適用しない。
  - Relation Type vocabulary / RegistryをObject Class Registryと分離して管理できる物理契約。

- [ ] **E-02 [P0] Semantic Facet schemaを設計する**
  - Character例: overall / personality / values / motivation / behavior / relationships / role / themes。
  - Work例: overall / themes / worldview / narrative / tone / characters / relationships。
  - Concept例: definition / properties / implications / related_concepts / examples。
  - Class固有FacetをDB列へ固定しすぎない。
  - 初期Registryへ登録済みでも専用Facetが未定義のClassを許容し、共通Object contractで保持できるようにする。
  - Facet Registry / Class-to-Facet profileとcommon Facetを設計する。
  - Facet内Knowledge Statement、Facet status、typed attribute key/valueの配置をB-04契約へ合わせて設計する。
  - Object / Facet / Statement Search Representationを正本Knowledgeから分離し、representation builder version / content hash /対象Version membershipを追跡できる論理契約を設計する。
  - Statement / attribute / Relationのtemporal scopeをVersion作成時刻と分離して表現する方式を設計する。

- [ ] **E-03 [P0] Source / Evidence / Evidence Link / Provenance schemaを設計する**
  - Source Identityと0..N locator、Snapshot、Raw Artifact、Normalized Run、Evidenceの物理schemaをB-03要件から設計する。
  - 既存`url UNIQUE`前提を解消し、既存`source_id` / `snapshot_id` / `evidence_id`を可能な限り維持するmigration契約を定義する。
  - resource type / media type / document genre / publisher kind等のSource分類と、Source↔Objectごとのsubject relationshipを物理的に分離する。
  - Object/Facet/Relationから具体的Evidence IDを経由してRaw / Sourceまで遡れるようにする。
  - Evidence generation / location / extraction mode / content hash / provenance integrityを表現する。
  - ChatGPT出力が存在しないEvidence / Source IDを参照できないValidationを定義する。
  - Knowledge Statement / structured attribute / RelationからEvidenceへのLinkと、`supports` / `contradicts` / `contextualizes`等のEvidence roleを表現する。
  - 標準ResultのEvidence referenceが入力Package manifestに含まれることをValidation可能にする。

- [ ] **E-04 [P0] Versioningを設計する**
  - Final Object Dataは上書きではなくVersion追加を基本とする。
  - B-04のfull snapshot Resultを次期Version候補として扱う。
  - package / base version preconditionとstale Result処理を定義する。
  - omission / deletion semantics、current切替、rollback、Diff境界を定義する。
  - Version切替時にSearch Representation / Vector Indexをinvalid/updateする境界を定義する。
  - 同一Embedding Space + representation hashによるVector reuseを許容しつつ、Version membershipとcurrent / historical scopeを分離して追跡する。
  - Persistent Version IDはSGOKB側で発行する。

- [ ] **E-05 [P1] JSON Schemaを作成する**
  - 共通Object Result schema。
  - Class別extension schema。
  - Primary / Additional ClassがClass Registryに存在することをValidationする。
  - 専用extension未実装のClassでも共通schemaを利用可能とし、別Classへの自動fallbackを要求しない。
  - ChatGPTへ渡す出力契約とImport Validatorで同一Schemaを利用する。
  - Object Result Envelope、package/base Version binding、generation provenanceをSchema化する。
  - Knowledge Statement / derivation kind / reported-view attribution / Evidence role、Knowledge language / temporal scope、Facet / attribute / Relation、conflict / gap、unresolved reference / Registry proposalを表現する。
  - partial / insufficient evidence状態を処理失敗と区別する。

**完了条件:** ChatGPT出力、DB、検索、MCPの共通契約となるObject schemaが確定している。

---

# Phase F — Source / Evidenceパイプラインの簡略化

- [ ] **F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する**
  - B-03 / E-03で定義したSource Identity / locator / Snapshot / Raw Artifact / Normalized Run / Evidence契約へ既存pipelineを接続する。
  - Raw Artifactを原資料として維持し、EvidenceをRawと同一視しない。
  - 既存`source_id` / `snapshot_id` / `evidence_id`とProvenanceを可能な限り維持する。
  - 旧`source_type` / Page Context metadataを新分類軸へbest-effort mappingまたはlegacy保持する。
  - 最新Snapshotを無条件にeffectiveとしないselection policyを設計する。

- [ ] **F-02 [P0] 標準パイプラインからFragment生成を外す**
  - `fragment`を必須工程から除外する。
  - 互換・研究用途として残すか完全廃止するかを決定する。

- [ ] **F-03 [P0] Object Evidence Retrievalを実装する**
  - name / alias / explicit association / Source metadata / FTS / embeddingを組み合わせる。
  - 高Recall優先とし、最終的な意味判断はChatGPTへ渡す。
  - Evidence選択理由（explicit link / name / alias / FTS / semantic / manual等）を追跡可能にする。

- [ ] **F-04 [P1] Evidence Selectionのtoken/size budgetを設計する**
  - Evidence granularityはsection / paragraph / table / post等のSource構造を優先し、固定文字数だけで決めない。
  - 1 Objectで無制限に全Evidenceを出力しない。
  - Source多様性と関連性を維持しつつPackageを構築する。
  - chunk overlap /近接Evidenceの扱いを設計する。
  - 切り捨て理由を追跡可能にする。

- [ ] **F-05 [P1] ObjectとSource/Evidenceの明示linkを維持できるUI/CLIを設計する**
  - Source↔Object associationのcandidate / confirmed / excludedを扱えるようにする。
  - 自動検索候補 + 人間による追加/除外を許可する。
  - Objectごとのsubject relationship等のassociation metadataを扱えるようにする。

**完了条件:** 生成LLMなしでObjectに関連するEvidence Packageを作成できる。

---

# Phase G — Google Drive / ChatGPT交換ワークフロー

- [ ] **G-01 [P0] Object Evidence Package formatを確定する**
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

- [ ] **G-02 [P0] `manifest.json` schemaを定義する**
  - object_id / primary_class / additional_classes / name / aliases。
  - package version。
  - included sources/evidence IDs。
  - extraction timestamp。
  - expected result schema version。
  - package identity / manifest hash / base Object Knowledge Version等、Result bindingに必要なprecondition。

- [ ] **G-03 [P0] ChatGPT用`instructions.md`を設計する**
  - Primary Class / ancestor Class別の分析目的。
  - Fact / synthesis / interpretationの区別。
  - Evidence ID参照ルール。
  - Relation生成ルール。
  - 不明情報を創作しないルール。
  - `direct_statement` / `synthesis` / `interpretation` / `reported_view`相当のderivation区分。
  - Package外Evidence IDや未知Object IDを創作しないルール。
  - Evidence不足・矛盾・unresolved referenceを構造化して返すルール。

- [ ] **G-04 [P0] Local Package staging / Google Drive export方式を実装する**
  - Package Buildはまずlocal stagingへ生成し、External Exportと分離する。
  - 初期版は明示export → Drive同期フォルダでも可。同期対象directoryへのwriteもExternal Exportとして扱う。
  - export前にpackage identity / target Object / file・Evidence scope / warning / destinationをpreflight表示可能にする。
  - SGOKB本体をGoogle Drive APIへ強く依存させるかは別途判断する。

- [ ] **G-05 [P1] Result受け取り運用を定義する**
  - `result.json`必須。
  - MarkdownをChatGPTに作らせる場合も正本にはしない。
  - 手動配置場所とvalidation triggerを定義する。
  - Result検出 / Validationは自動化可能だが、検出だけを理由にauthoritative Importしない。
  - Google Drive / ChatGPT手動工程の開始・返却・失敗時運用を1 Object単位で定義する。

**完了条件:** APIを利用せず、ユーザーがChatGPTとの手動工程を介して1 Objectを往復できる。

---

# Phase H — Result Validation / Import / Rendering

- [ ] **H-01 [P0] Result JSON Validatorを実装する**
  - Syntax / Schema、Binding / Precondition、Referential、Grounding / Provenance、Domain Contract Validationを分離する。
  - object_id / package / base Version一致。
  - Source/Evidence ID存在確認 + Package membership確認。
  - Facet / attribute / Relation Type contractを確認する。
  - Relation target存在確認または未解決参照として明示管理。
  - 不正field / schema version拒否。
  - Validatorが意味内容や未知IDを推測修復しない。

- [ ] **H-02 [P0] Object Version Importを実装する**
  - Validation成功後も標準ではexplicit Import operationを要求し、Result検出だけでsilent commitしない。
  - normal ResultではImport開始後のVersion発行 / current切替 /派生Index更新を追加confirmationへ過剰分割しない。
  - stale Resultは通常Importをblockし、partial / limited Resultはreview-requiredを既定とする。
  - Validation成功後のみDBへcommitする。
  - 既存currentを破壊しない。
  - Import run / timestamp / source package / original Result artifact provenanceを記録する。
  - Persistent Version IDをSGOKB側で発行し、同一Resultの重複Import候補を検出する。
  - Registry proposalをObject Knowledge Importの副作用として自動適用しない。

- [ ] **H-03 [P1] Markdown Rendererを実装する**
  - DB/JSONから人間向けObject文書を生成する。
  - Markdownを編集正本にしない。

- [ ] **H-04 [P1] Diff / Review表示を実装する**
  - v1→v2の属性・Facet・Relation差分を確認できるようにする。
  - stale / partial / destructive omission / Registry proposal / Identity ambiguity等のreview-required reasonを表示する。
  - 手動承認を採用する場合の状態遷移を定義する。
  - full snapshotで消えるStatement / attribute / Relation、conflict、Registry proposal、stale baseを目立たせる。

**完了条件:** ChatGPT出力を壊れた状態で正本DBへ登録できず、過去versionへ戻れる。

---

# Phase I — 意味検索・類似検索

- [ ] **I-01 [P0] Search Representation / Embedding対象を設計する**
  - Evidence representation / embedding。
  - Object overall representation / embedding。
  - Facet representation / embedding。
  - accepted検索可能Knowledge Statementの個別representation / embeddingを標準対象とする。
  - 必要に応じRelation text representation。
  - Statement単体で文脈不足の場合、Object / Class / Facet / temporal scope等を付加するContextual Search Representation Builderを設計する。
  - representation kind / Object Version / Facet / Statement membership / Evidence generation / builder version / content hashを追跡する。
  - `gap` / `insufficient evidence` / `unresolved reference` / Registry proposalは通常Statement Semantic Indexへ入れない。

- [ ] **I-02 [P0] Embedding Provider / 多言語Modelを比較する**
  - 日本語を含むSGOKB実データで評価する。
  - FastEmbed等のlocal provider adapterと、BGE-M3等のmodel候補を分離して評価する。
  - Object / Facet / Statement / Evidenceで同一modelが最適かも確認する。
  - model / revision / dimension / preprocessing / normalization / provider configurationをEmbedding Space metadataへ記録する。
  - Vector backend比較時はEmbedding Spaceを固定し、model比較とbackend比較を混同しない。

- [ ] **I-03 [P0] VectorIndexAdapterを設計しBackendを比較決定する**
  - SQLiteをcanonical Knowledge Storeとし、Vector backendを再構築可能なDerived Search Indexとして分離する。
  - `VectorIndexAdapter`相当の共通契約でupsert / search / filter / invalidate / rebuild / metadata取得を抽象化する。
  - SQLite系Float32 Exact / FlatをANN Recallの基準にする。
  - sqlite-vectorのFloat32 / quantized条件をbaseline候補として評価する。
  - sqlite-vecをSQLite内軽量backend候補として評価する。
  - LanceDB ANNをserver不要のembedded ANN候補として評価する。
  - Qdrant HNSW + payload filter + Object groupingを高性能 / 高機能基準として評価する。
  - Query latency、Statement/Object Recall@K、Exactに対するANN Recall、Index build/update/rebuild時間、RAM、disk size、Windows運用コストで比較する。
  - 実測前に最終backendを固定しない。

- [ ] **I-04 [P0] Multi-representation Hybrid Search / Object Aggregationを実装する**
  - FTS + Object / Facet / Statement vector searchを組み合わせる。
  - Statement-level hitを内部candidateとして扱い、通常Object検索は1 Object = 1結果へ集約するObject Aggregatorを実装する。
  - matched Statement / Facet / representative snippet / groundingをresult detailとして保持する。
  - 同一Objectの多数Statement hitを単純合計して無制限boostしない。best hit / top-N capped contribution / Facet diversity等をgoldで比較する。
  - primary/additional/ancestor class / facet / version / temporal scope等のhard filterをcandidate生成前に適用可能にする。
  - exact name/aliasをSemantic Searchより優先できるようにする。
  - current accepted Knowledgeを既定scopeとし、historical Statement Vectorをsilent混合しない。
  - lexical / Object / Facet / Statement各channelのfusionとmatch reasonを説明可能にする。

- [ ] **I-05 [P0] `find_similar_objects`を実装する**
  - overall similarity。
  - 既定candidate scopeは同じPrimary Classとし、cross-classは明示拡張とする。
  - facet指定similarity。
  - missing Facetを0 similarityやoverallへsilent fallbackしない。
  - scoreとmatched facet / target Versionを返せる構造。

- [ ] **I-06 [P1] Reranker / second-stage retrievalを評価する**
  - 初期版MVPには必須としない。
  - FastEmbed等で利用可能なCross Encoderを含め候補を比較する。
  - first-stageで取得できなかったObjectをrerankerは救えないため、Statement Recallを先に評価する。
  - retrieval品質とlatencyの実測で導入を判断する。

- [ ] **I-07 [P0] 検索品質gold / Backend benchmarkを作成する**
  - Character / Work / Conceptに加え、Person / Organization / Series / Place / EventとLater support Classの代表Queryを用意する。
  - Facet全体では薄まりやすい細粒度Statement Query、条件・例外・時系列Queryを明示的に含める。
  - 日本語Queryとcross-lingual Queryを含める。
  - Statement Embeddingあり / なしを比較し、細粒度Recall改善を確認する。
  - lexical / semantic / hybrid / overall similarity / facet similarity / Evidence Searchを比較する。
  - Float32 Exact結果をANN backend評価のreferenceにする。
  - exact lookup、Statement Recall@K、Object Recall@K、ANN Recall@K、MRR、nDCG、filter correctness、current/historical isolation、人間Similarity評価を記録する。
  - latency / index size / build / incremental update / rebuildを同一workloadで測定する。

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
  - Facet similarity相当の検索機能
  - `get_object`
  - `get_objects`
  - `get_object_relations`
  - `get_object_evidence`
  - `search_evidence`
  - `build_context` または同等機能。

- [ ] **J-03 [P1] MCP Resourcesを定義する**
  - 例: `sgokb://object/<id>`。
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

- [ ] **L-05 [P0] 不要依存関係を削除する**
  - 標準運用から生成LLM Providerが不要になった場合、optional/research dependencyへ降格する。
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
  - 通常Objectと大きめObjectを分け、B-07で確定するpercentile条件で評価する。

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
  - 部分Import失敗。

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

最優先は **A-01〜A-03 → B-01〜B-07 → C-01〜C-04** とする。

実装変更を先に始めると、旧PrototypeのEntity / Fragment / Final Document概念を新設計へ引きずる可能性がある。まず目的・責務・データ境界を確定し、その後 **E-01 Object schema** を起点として実装を再構成する。

Git上の物理的な大量移動（D-03〜D-05）は、要件・責務境界が確定した後に行う。
