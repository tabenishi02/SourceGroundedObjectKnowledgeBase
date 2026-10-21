# Planning documents

`docs/planning/` は、進行計画・Phase準備/完了監査・タスク一覧・実行handoffを置く領域です。

従来は多数の文書が直下に混在していたため、2026-10-20に用途とPhaseで再配置しました。

## 現在地

現在の開発Phaseは **Phase N** です。

N-04は2026-10-22にresponsibility boundaryを再構築し、Reference Workstation再受入で**Complete / PASS**となりました。現行N-04は、外部AIの生成品質ではなく、**SGOKBが外部Consumerへ正しいKnowledgeをpublic read boundaryから提供できること**をformal acceptance対象とします。

N-04R-05まで完了し、旧Grounded Generation資産のowner / future dispositionも確定しました。Grounded Generation chainにSGOKB `KEEP_CORE`資産はありません。

Phase Nの次のP0 TaskはN-05 / N-06です。順次進める場合は **N-05 — Performance** を次Taskとします。

### Current authority

- 全体タスク正本: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- N-04 Task master amendment: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md)
- 全体handoff: [`project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`](project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md)
- N-04 project handoff amendment: [`project/KNOWLEDGE_BASE_REDESIGN_HANDOFF_N04_AMENDMENT.md`](project/KNOWLEDGE_BASE_REDESIGN_HANDOFF_N04_AMENDMENT.md)
- Phase N準備/状態: [`phases/N/PHASE_N_PREPARATION.md`](phases/N/PHASE_N_PREPARATION.md)
- N-04 responsibility Decision: [`../decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`](../decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md)
- N-04 Harness freeze: [`../decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`](../decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md)
- N-04 asset disposition: [`../decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`](../decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md)
- N-04 current acceptance spec: [`../evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`](../evaluation/N04_AI_USE_CASE_ACCEPTANCE.md)
- N-04 formal result: [`../evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`](../evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md)
- N-04 reconstruction tasks: [`phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`](phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md)

### Current machine-readable N-04 assets

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/n04r05-grounded-generation-asset-disposition-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
```

### Historical N-04 remediation

旧G-01〜G-25資産はR-05 Decisionに従って分類します。

- `MOVE_CONSUMER_SIDE`: Grounded Generation実装 / verifier / pipeline / architecture contracts
- `KEEP_EXPERIMENTAL`: failure analysis / Frozen 47 / G-25A research evidence
- `RETIRE`: old generation-quality harness / execution tooling / superseded handoff
- `KEEP_CORE`: Grounded Generation chainからは0件

Historical fileは再現性のため今回削除していません。

## Directory layout

```text
docs/planning/
├─ README.md
├─ project/
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
│  └─ KNOWLEDGE_BASE_REDESIGN_HANDOFF_N04_AMENDMENT.md
└─ phases/
   ├─ B/
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
   └─ N/
      ├─ N01_UNIT_TEST_COVERAGE.md
      ├─ N02_INTEGRATION_TESTS.md
      ├─ PHASE_N_PREPARATION.md
      └─ N04/
         ├─ N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md
         ├─ N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md
         ├─ derived-search/
         ├─ post-g12/
         └─ execution/
```

## Classification rules

### `project/`

Phaseをまたぐ全体タスク・全体handoff・Task master / handoff amendmentを置きます。

### `phases/<Phase>/`

各Phase固有のPreparation、Status、Closure Auditを置きます。

### `phases/N/N04/derived-search/`

N-04の前提となるderived search pipeline文書を置きます。

### `phases/N/N04/post-g12/`

G-12以降のhistorical remediation / researchを保持します。current authorityとして使用しません。

### `phases/N/N04/execution/`

Reference Workstation/Codexの実行handoffを保持します。R-04は完了済みであり、新規N-04実行の入口ではありません。

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
