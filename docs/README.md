# SGOKB Documentation

このディレクトリは、**現行のSGOKB設計文書**と**過去のPrototype資料**を明確に分離する。

## まず読む文書

1. [目的要件](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md) — SGOKBが何を実現するシステムか。
2. [Object要件](requirements/OBJECT_REQUIREMENTS.md) — ObjectのIdentity、型、共通属性、Versionとの関係。
3. [再設計Decision](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md) — 旧Prototypeから何を変更し、なぜ変更するか。
4. [再設計タスク](planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md) — 現在の進捗と次に実施する作業。
5. [Object Type精緻化タスク](planning/OBJECT_TYPE_REFINEMENT_TASKS.md) — B-03前に実施するObject分類の詳細計画。
6. [再設計引継ぎ](planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md) — 別チャット・Codexへ引き継ぐための全体背景。

## 現行文書

### `requirements/`
現在有効な要件を置く。B-01の目的要件、B-02のObject要件を収録済み。B-03以降でSource / Evidence / Result / Search / NFR要件を追加する。

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
