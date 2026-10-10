# SGOKB Documentation

このディレクトリは、**現行のSGOKB設計文書**と**過去のPrototype資料**を明確に分離する。

## まず読む文書

1. [目的要件](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md) — SGOKBが何を実現するシステムか。
2. [Object要件](requirements/OBJECT_REQUIREMENTS.md) — ObjectのIdentity、共通属性、Versionとの関係。
3. [Object分類境界](requirements/OBJECT_TYPE_BOUNDARIES.md) — 正式Class hierarchyとObject / Facet / Relation / value境界。
4. [Source / Evidence要件](requirements/SOURCE_EVIDENCE_REQUIREMENTS.md) — Source Identity、Snapshot、Raw、Evidence、Provenanceの現行要件。
5. [Object Result要件](requirements/OBJECT_RESULT_REQUIREMENTS.md) — Structured Result、Facet/Relation、Evidence grounding、Version候補の現行要件。
6. [Search / Retrieval要件](requirements/SEARCH_REQUIREMENTS.md) — Object / Facet / Relation / EvidenceのLexical・Semantic・Similarity・履歴検索要件。
7. [再設計Decision](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md) — 旧Prototypeから何を変更し、なぜ変更するか。
8. [再設計タスク](planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md) — 現在の進捗と次に実施する作業。
9. [Object Type精緻化タスク](planning/OBJECT_TYPE_REFINEMENT_TASKS.md) — 完了したB-02A〜DのObject分類タスク記録。
10. [Object Type精緻化引継ぎ](planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md) — 完了したB-02A〜Dの決定とB-03反映結果をまとめた専用Handoff。
11. [再設計引継ぎ](planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md) — 別チャット・Codexへ引き継ぐための全体背景。

## 現行文書

### `requirements/`
現在有効な要件を置く。B-01の目的要件、B-02のObject要件、B-02A〜Dで確定したObject分類モデル・境界、B-03のSource / Evidence要件、B-04のObject Result要件、B-05のSearch / Retrieval要件を収録済み。B-06以降でWorkflow / NFR要件を追加する。

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
