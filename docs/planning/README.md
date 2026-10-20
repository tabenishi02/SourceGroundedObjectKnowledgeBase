# Planning documents

`docs/planning/` は、進行計画・Phase準備/完了監査・タスク一覧・実行handoffを置く領域です。

従来は多数の文書が直下に混在していたため、2026-10-20に用途とPhaseで再配置しました。

## 現在地

現在の開発Phaseは **Phase N** です。

- 全体タスク正本: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- 全体handoff: [`project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`](project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md)
- Phase N準備/状態: [`phases/N/PHASE_N_PREPARATION.md`](phases/N/PHASE_N_PREPARATION.md)
- N-04 Grounded Generation task: [`phases/N/N04/N04_GROUNDED_GENERATION_TASKS.md`](phases/N/N04/N04_GROUNDED_GENERATION_TASKS.md)
- N-04 historical post-G12 remediation: [`phases/N/N04/post-g12/N04_POST_G12_REMEDIATION_TASKS.md`](phases/N/N04/post-g12/N04_POST_G12_REMEDIATION_TASKS.md)
- **N-04 current post-G22 remediation: [`phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`](phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md)**
- **N-04 current chat handoff: [`phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_CHAT_HANDOFF.md`](phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_CHAT_HANDOFF.md)**

## Directory layout

```text
docs/planning/
├─ README.md
├─ project/
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
│  └─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
└─ phases/
   ├─ B/
   │  └─ object-type-refinement/
   ├─ D/
   ├─ E/
   ├─ F/
   ├─ G/
   ├─ H/
   ├─ I/
   ├─ J/
   ├─ K/
   ├─ L/
   ├─ M/
   │  └─ M03/
   └─ N/
      ├─ N01_UNIT_TEST_COVERAGE.md
      ├─ N02_INTEGRATION_TESTS.md
      ├─ PHASE_N_PREPARATION.md
      └─ N04/
         ├─ N04_GROUNDED_GENERATION_TASKS.md
         ├─ N04_GROUNDED_GENERATION_HANDOFF.md
         ├─ N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md
         ├─ derived-search/
         ├─ post-g12/
         └─ execution/
```

## Classification rules

### `project/`
Phaseをまたぐ全体タスクと全体handoffを置きます。

### `phases/<Phase>/`
各Phase固有のPreparation、Status、Closure Auditを置きます。

### `phases/N/N04/derived-search/`
N-04の前提となるderived search pipelineのP02〜P06を置きます。

### `phases/N/N04/post-g12/`
N-04のG-12以降のremediation task、G-22以降の追加remediation、chat handoffを置きます。

### `phases/N/N04/execution/`
Reference Workstation/Codexで使用した実行handoffを置きます。これらは実行記録の再現性のため保持します。

## 文書配置ルール

今後Planning文書を追加する際は、原則として直下へ追加せず、以下に従います。

1. 全Phase共通の進捗/全体handoff → `project/`
2. Phase単位 → `phases/<Phase>/`
3. 特定Taskに複数文書が増える場合 → `phases/<Phase>/<Task>/`
4. 一時的な実行handoff → 対象Task配下の`execution/`
5. 結果・調査報告 → `docs/evaluation/`
6. 設計Decision → `docs/decisions/`
7. 実装設計 → `docs/design/`

`docs/planning/`直下には、この`README.md`以外を原則置きません。
