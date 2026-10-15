# SGOKB Documentation

このディレクトリは、**現行のSGOKB設計文書**と**過去のPrototype資料**を明確に分離する。

## まず読む文書

1. [目的要件](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md) — SGOKBが何を実現するシステムか。
2. [World / Object Knowledge Layer要件](requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md) — SGOKBが所有するObject KnowledgeとPersonal Inferenceの境界。
3. [UPDS Personal Inference Layer要件](requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md) — UPDSが所有するSelection Event、Semantic Observation、Pattern、Preference Hypothesis等の責務境界。
4. [Concept Ownership Boundary要件](requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md) — Conceptのcanonical所有をSGOKBとし、UPDSはConcept ID参照によってPersonal Inferenceを構築する境界。
5. [SGOKB → UPDS Integration Contract要件](requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md) — stable Object ID、Knowledge Version、MCP read access、stale / cache / failure時の参照契約。
6. [Object要件](requirements/OBJECT_REQUIREMENTS.md) — ObjectのIdentity、共通属性、Versionとの関係。
7. [Object分類境界](requirements/OBJECT_TYPE_BOUNDARIES.md) — 正式Class hierarchyとObject / Facet / Relation / value境界。
8. [Source / Evidence要件](requirements/SOURCE_EVIDENCE_REQUIREMENTS.md) — Source Identity、Snapshot、Raw、Evidence、Provenanceの現行要件。
9. [Object Result要件](requirements/OBJECT_RESULT_REQUIREMENTS.md) — Structured Result、Facet/Relation、Evidence grounding、Version候補の現行要件。
10. [Search / Retrieval要件](requirements/SEARCH_REQUIREMENTS.md) — Object / Facet / Statement / Relation / EvidenceのLexical・Semantic・Similarity・履歴検索要件。
11. [人間工程 / 自動工程要件](requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md) — Human Decision、local automation、external export、Result Import、10分計測境界。
12. [非機能要件](requirements/NON_FUNCTIONAL_REQUIREMENTS.md) — local-first、integrity、backup / restore、security、failure recovery、性能Acceptance。
13. [Embedding / Vector Search技術調査](reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md) — Statement-level Embedding、Vector backend、Object aggregation、既存ライブラリ比較の設計入力。
14. [再設計Decision](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md) — 旧Prototypeから何を変更し、なぜ変更するか。
15. [再設計Branch Strategy](decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md) — `main` / integration / task branch、PR、同期、最終merge方針。
16. [Module Responsibility Design](decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md) — `src/sgokb`の責務別構造、依存方向、既存module mapping。
17. [Module Migration Policy](decisions/SGOKB_MODULE_MIGRATION_POLICY.md) — 既存moduleのmove / split / compatibility / PR分割・実施Wave。
18. [Runtime Data / Git Exclusion Policy](decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md) — canonical / generated / exchange / backup / secretの物理配置とGit管理境界。
19. [Git History Cleanup Policy](decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md) — branch / PR / tag / releaseの保持・救済・cleanup規則。
20. [再設計タスク](planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md) — 現在の進捗と次に実施する作業。
21. [再設計引継ぎ](planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md) — Phase A〜Eの確定事項と後続Phaseへの全体Handoff。
22. [Phase D Preparation](planning/PHASE_D_PREPARATION.md) — Phase D完了記録とPhase Eへの引継ぎ。
23. [Phase E Preparation](planning/PHASE_E_PREPARATION.md) — Phase D完了監査、domain package conversion、現行Prototype DB baseline、Phase E開始条件と完了記録。
24. [Phase F Preparation](planning/PHASE_F_PREPARATION.md) — Phase E完了監査、ingestion package移動、既存Pipelineとcanonical Source/Evidenceの差分、F-01開始条件。
25. [Object Schema Design](design/OBJECT_SCHEMA.md) — E-01で確定したObject / Class / Version / Relationの物理schema。
26. [Semantic Facet Schema Design](design/SEMANTIC_FACET_SCHEMA.md) — E-02で確定したFacet / Statement / Attribute / Temporal Scope / Search Representation schema。
27. [Facet Taxonomy Survey](design/FACET_TAXONOMY_SURVEY.md) — E-02Aで全62 Classの意味境界・Facet候補・非Facet境界・代表例/反例を横断整理したsurvey。
28. [Facet Vocabulary Review](design/FACET_VOCABULARY_REVIEW.md) — E-02Bで近義Facetを横断統合し、既存18 + 新規37 = 55 Facetのfreeze候補とprofile inheritance方針を整理した設計レビュー。
29. [Class / Facet Gold Cases](reference/CLASS_FACET_GOLD_CASES.md) — E-02Cで全62 Classと25 boundary caseをgold化し、55 Facet taxonomyをfreezeした回帰基準。
30. [Source / Evidence Schema Design](design/SOURCE_EVIDENCE_SCHEMA.md) — E-03で確定したSource Identity / locator / Snapshot / Raw / Normalization / Evidence / Evidence Link / Provenanceの物理schema。
31. [Source Ingestion Pipeline](design/SOURCE_INGESTION_PIPELINE.md) — F-01で実装したcanonical Capture / Import / Normalize / Evidence接続、Source resolution、effective generation selection。
32. [Standard Pipeline / Legacy Fragment Boundary](design/STANDARD_PIPELINE_BOUNDARY.md) — F-02で確定した標準Evidence pipelineと旧Fragment / Finalのlegacy・research境界。
33. [Object Evidence Retrieval](design/OBJECT_EVIDENCE_RETRIEVAL.md) — F-03で実装したeffective Evidence scope、association / name / alias / metadata / FTS / semantic / manual signal統合とselection reason契約。
34. [Evidence Selection Budget](design/EVIDENCE_SELECTION_BUDGET.md) — F-04で確定したtoken / byte / item hard budget、Source diversity、duplicate / overlap処理、omission reason契約。
35. [Operator Association / Evidence Selection Controls](design/OPERATOR_ASSOCIATION_CONTROLS.md) — F-05で確定したSource↔Object association、read-only suggestion、Evidence manual include / exclude、canonical CLI境界。
36. [Versioning Schema Design](design/VERSIONING_SCHEMA.md) — E-04で確定したfull snapshot Version lifecycle、stale判定、accepted immutability、current promotion / rollback、derived-state boundary。
37. [Object Result JSON Schema Design](design/OBJECT_RESULT_JSON_SCHEMA.md) — E-05で確定した`sgokb.object-result/1.0`、Package/Class/Facet binding、Evidence-grounded Result exchange contract。
38. [Search Representation Schema](design/SEARCH_REPRESENTATION_SCHEMA.md) — I-01で確定したObject / Facet / Statement / Evidenceの派生検索表現、membership、current/historical境界。
39. [Embedding Provider / Model Evaluation](design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md) — I-02で確定したProvider比較、Harrier OSS v1 0.6B / 1024-dim Embedding Space、Exact baseline。
40. [VectorIndexAdapter / Backend Evaluation](design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md) — I-03で確定したbackend-neutral contract、Qdrant HNSW標準、LanceDB第2候補、Exact/ANN benchmark。
41. [Hybrid Search / Object Aggregation](design/HYBRID_SEARCH_OBJECT_AGGREGATION.md) — I-04で確定したmulti-representation retrieval、hard filter、membership-scoped Vector point、RRF Object aggregation。
42. [Object Similarity Search](design/OBJECT_SIMILARITY_SEARCH.md) — I-05で確定したoverall / Facet similarity、same Primary Class既定scope、cross-class明示拡張、direct cosine result contract。
43. [Reranker / Second-stage Evaluation](design/RERANKER_SECOND_STAGE_EVALUATION.md) — I-06で評価したBGE v2-m3 balanced/default候補、zerank-2 quality候補、top-50 second-stage benchmark。
44. [Search Quality Gold / Backend Benchmark](design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md) — I-07 frozen gold、100k Exact/Qdrant、Similarity、Evidence、formal reranker benchmark。
45. [Phase I Closure Audit](planning/PHASE_I_CLOSURE_AUDIT.md) — I-01〜I-07の完了状態、正式gold、回帰試験、Phase J引継ぎを再監査したclosure記録。
46. [Phase J Preparation](planning/PHASE_J_PREPARATION.md) — MCP Knowledge Access Layer開始条件、Application/Retrieval boundaryのgap、J-01 Definition of Ready / Done。
47. [Object Type精緻化タスク](planning/OBJECT_TYPE_REFINEMENT_TASKS.md) — 完了したB-02A〜DのObject分類タスク記録。
48. [Object Type精緻化引継ぎ](planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md) — 完了したB-02A〜Dの決定とB-03反映結果をまとめた専用Handoff。

## 現行文書

### `requirements/`
現在有効な要件を置く。Phase Bで目的、Object、Object分類、Source / Evidence、Object Result、Search / Retrieval、Human / Automation Workflow、非機能要件を確定した。Phase CではC-01としてSGOKBをWorld / Object Knowledge Layer、C-02としてUPDSをPersonal Inference Layer、C-03としてConceptのcanonical所有をSGOKB、Conceptを利用したPersonal InferenceをUPDSとする境界を定義し、C-04でstable `object_id` / Knowledge Version / MCP read access / stale・cache・failure時のSGOKB→UPDS参照契約を確定した。**Phase Cは完了している。**

### `decisions/`
現在も有効なArchitecture Decisionを置く。

- [Knowledge Base再設計Decision](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md)
- [Knowledge Base再設計Branch Strategy](decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md)
- [SGOKB Module Responsibility Design](decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md)
- [SGOKB Module Migration Policy](decisions/SGOKB_MODULE_MIGRATION_POLICY.md)
- [SGOKB Runtime Data / Git Exclusion Policy](decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md)
- [SGOKB Git History / Branch / PR / Tag / Release Cleanup Policy](decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md)
- [SGOKB名称変更Decision](decisions/SGOKB_RENAME_DECISION.md)
- [L-01 Fragment Retirement Policy](decisions/L01_FRAGMENT_RETIREMENT_POLICY.md)
- [L-02 Final Document Retirement Policy](decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md)
- [L-03 Canonical DB Clean Rebuild Policy](decisions/L03_CANONICAL_DB_CLEAN_REBUILD_POLICY.md)
- [L-04 Legacy Benchmark Retirement Policy](decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md)
- [L-05 Legacy Compatibility Cleanup Policy](decisions/L05_LEGACY_COMPATIBILITY_CLEANUP_POLICY.md)
- [Phase L Closure Audit](planning/PHASE_L_CLOSURE_AUDIT.md)

### `design/`

Phase E以降で確定した物理Architecture / Data Model設計を置く。

- [Object Schema Design](design/OBJECT_SCHEMA.md)
- [Semantic Facet Schema Design](design/SEMANTIC_FACET_SCHEMA.md)
- [Facet Taxonomy Survey](design/FACET_TAXONOMY_SURVEY.md)
- [Facet Vocabulary Review](design/FACET_VOCABULARY_REVIEW.md)
- [Source / Evidence Schema Design](design/SOURCE_EVIDENCE_SCHEMA.md)
- [Source Ingestion Pipeline](design/SOURCE_INGESTION_PIPELINE.md)
- [Standard Pipeline / Legacy Fragment Boundary](design/STANDARD_PIPELINE_BOUNDARY.md)
- [Object Evidence Retrieval](design/OBJECT_EVIDENCE_RETRIEVAL.md)
- [Evidence Selection Budget](design/EVIDENCE_SELECTION_BUDGET.md)
- [Operator Association / Evidence Selection Controls](design/OPERATOR_ASSOCIATION_CONTROLS.md)
- [Versioning Schema Design](design/VERSIONING_SCHEMA.md)
- [Object Result JSON Schema Design](design/OBJECT_RESULT_JSON_SCHEMA.md)
- [Search Representation Schema](design/SEARCH_REPRESENTATION_SCHEMA.md)
- [Embedding Provider / Model Evaluation](design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md)
- [VectorIndexAdapter / Backend Evaluation](design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md)
- [Hybrid Search / Object Aggregation](design/HYBRID_SEARCH_OBJECT_AGGREGATION.md)
- [Object Similarity Search](design/OBJECT_SIMILARITY_SEARCH.md)
- [Reranker / Second-stage Evaluation](design/RERANKER_SECOND_STAGE_EVALUATION.md)
- [Search Quality Gold / Backend Benchmark](design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md)

### `planning/`
進行中の計画・タスク・引継ぎ資料を置く。Phase A〜LはComplete。[Phase L Closure Audit](planning/PHASE_L_CLOSURE_AUDIT.md)を完了監査の正本とし、次Taskは`M-01 [P0] 新しいObject中心CLIを設計する`（未着手）。

L-04で旧benchmark inputs/scriptsとlocal DBを削除し、L-05でFragment / Final / old benchmark / Generative LLM / Prototype Search・migration001/002・runtime compatibilityを撤去した。current Search quality gold / Vector / Reranker benchmarkとSample RawはKeepする。historical resultは`archive/prototype-0.2/`、旧実装はGit historyを参照する。

### `reference/`
再設計で参照する既存資産・依存関係の調査結果とgold corpusを置く。

- [Class / Facet Gold Cases](reference/CLASS_FACET_GOLD_CASES.md) — E-02Cのtaxonomy regression正本。

## Archive

### `archive/prototype-0.2/`
旧CharacterPageCollector / SGOKB Prototype 0.2時代の資料。旧要件、Prototype設計、評価、速度試験、モデル比較、コスト試算等を保存する。**現行仕様の判断には使用しない。**

### `archive/rename-2026-10/`
CharacterPageCollectorからSource Grounded Object Knowledge Baseへの名称変更作業記録。名称変更自体は完了済み。

## Component documentation

Web Page Captureは独立したコンポーネントとして [`../extensions/web-page-capture/README.md`](../extensions/web-page-capture/README.md) 以下に固有設計・Capture Bundle仕様・受入手順を保持する。

## 文書追加ルール

- 現在有効な仕様を`archive/`へ置かない。
- 過去の評価結果・廃止設計を現行カテゴリへ戻さない。
- 現行文書からArchiveを参照する場合は「歴史資料」であることを明記する。
- 新規文書は目的に応じて`requirements` / `decisions` / `planning` / `reference`へ配置し、必要なら将来`design` / `operations`等を追加する。
