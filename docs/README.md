# SGOKB Documentation

このディレクトリは、**現行のSGOKB設計文書**と**過去のPrototype資料**を明確に分離する。

## まず読む文書

1. [目的要件](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md) — SGOKBが何を実現するシステムか。
2. [World / Object Knowledge Layer要件](requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md) — SGOKBが所有するObject KnowledgeとPersonal Inferenceの境界。
3. [UPDS Personal Inference Layer要件](requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md) — UPDSが所有するSelection Event、Semantic Observation、Pattern、Preference Hypothesis等の責務境界。
4. [Object要件](requirements/OBJECT_REQUIREMENTS.md) — ObjectのIdentity、共通属性、Versionとの関係。
5. [Object分類境界](requirements/OBJECT_TYPE_BOUNDARIES.md) — 正式Class hierarchyとObject / Facet / Relation / value境界。
6. [Source / Evidence要件](requirements/SOURCE_EVIDENCE_REQUIREMENTS.md) — Source Identity、Snapshot、Raw、Evidence、Provenanceの現行要件。
7. [Object Result要件](requirements/OBJECT_RESULT_REQUIREMENTS.md) — Structured Result、Facet/Relation、Evidence grounding、Version候補の現行要件。
8. [Search / Retrieval要件](requirements/SEARCH_REQUIREMENTS.md) — Object / Facet / Statement / Relation / EvidenceのLexical・Semantic・Similarity・履歴検索要件。
9. [人間工程 / 自動工程要件](requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md) — Human Decision、local automation、external export、Result Import、10分計測境界。
10. [非機能要件](requirements/NON_FUNCTIONAL_REQUIREMENTS.md) — local-first、integrity、backup / restore、security、failure recovery、性能Acceptance。
11. [Embedding / Vector Search技術調査](reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md) — Statement-level Embedding、Vector backend、Object aggregation、既存ライブラリ比較の設計入力。
12. [再設計Decision](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md) — 旧Prototypeから何を変更し、なぜ変更するか。
13. [再設計タスク](planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md) — 現在の進捗と次に実施する作業。
14. [Object Type精緻化タスク](planning/OBJECT_TYPE_REFINEMENT_TASKS.md) — 完了したB-02A〜DのObject分類タスク記録。
15. [Object Type精緻化引継ぎ](planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md) — 完了したB-02A〜Dの決定とB-03反映結果をまとめた専用Handoff。
16. [再設計引継ぎ](planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md) — 別チャット・Codexへ引き継ぐための全体背景。

## 現行文書

### `requirements/`
現在有効な要件を置く。Phase Bで目的、Object、Object分類、Source / Evidence、Object Result、Search / Retrieval、Human / Automation Workflow、非機能要件を確定した。Phase CではC-01としてSGOKBをWorld / Object Knowledge Layer、C-02としてUPDSをPersonal Inference Layerと定義し、Object KnowledgeとPersonal Inferenceの両側の責務境界を要件化した。次はC-03 Concept所有境界、C-04 SGOKB→UPDS連携契約を具体化する。

### `decisions/`
現在も有効なArchitecture Decisionを置く。

- [Knowledge Base再設計Decision](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md)
- [SGOKB名称変更Decision](decisions/SGOKB_RENAME_DECISION.md)

### `planning/`
進行中の計画・タスク・引継ぎ資料を置く。

### `reference/`
再設計で参照する既存資産・依存関係の調査結果を置く。通常は最初から読む必要はない。

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
