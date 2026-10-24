# Planning documents

`docs/planning/` は、Source Grounded Object Knowledge Base（SGOKB）の進行計画、Phase準備/完了監査、Task一覧、実行handoffを管理する領域です。

Planning文書はPhase / Task単位で整理し、`docs/planning/`直下には原則としてこのIndexだけを置きます。

## Current phase

現在の開発Phaseは **Phase O — Documentation / Release / Git cleanup** です。

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 README update = Complete
O-04 main integration = Complete
Next = O-02 Current design documentation
```

Phase Nのformal closure run `20261025T014024+0900` はC01-C07 PASSで、独立ChatGPT reviewにより受理済みです。旧N-07 `47 PASS / 3 FAIL`等のhistorical evidenceは保持し、後続remediation / re-acceptanceと区別します。

Phase Oのcurrent task stateは [`phases/O/PHASE_O_STATUS.md`](phases/O/PHASE_O_STATUS.md) を参照してください。

## Current authority

- Phase O current status: [`phases/O/PHASE_O_STATUS.md`](phases/O/PHASE_O_STATUS.md)
- 全体task master: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- 全体handoff: [`project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`](project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md)
- Phase N closure planning authority: [`phases/N/PHASE_N_CLOSURE_AUDIT.md`](phases/N/PHASE_N_CLOSURE_AUDIT.md)
- Phase N preparation/history: [`phases/N/PHASE_N_PREPARATION.md`](phases/N/PHASE_N_PREPARATION.md)
- Phase N formal result: [`../evaluation/PHASE_N_CLOSURE_AUDIT.md`](../evaluation/PHASE_N_CLOSURE_AUDIT.md)
- 1 Object標準運用: [`../operations/OBJECT_STANDARD_WORKFLOW.md`](../operations/OBJECT_STANDARD_WORKFLOW.md)

Phase Oでは、Phase N以前の完了済みhandoffをcurrent workとして再利用しません。必要な場合はhistorical evidenceとして参照します。

## Phase O task state

| Task | Status | Purpose |
|---|---|---|
| O-01 | **Complete** | READMEを新SGOKBへ全面更新 |
| O-02 | **Next / Not Started** | 現行設計書を整理・更新 |
| O-03 | Not Started | Prototype文書へArchived / Legacy表示 |
| O-04 | **Complete** | branch historyを`main`へ統合 |
| O-05 | Not Started | 不要branch cleanup |
| O-06 | Not Started | Release / Tag policy |

O-04はPhase Oの通常順序より先にユーザー指示で実施済みです。全remote branch historyの最終統合commitは`77d79ccac1017f167736c742ac199858a3a010a7`です。

## Directory layout

```text
docs/planning/
├─ README.md
├─ project/
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
│  ├─ KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md
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
   ├─ N/
   │  ├─ N01_UNIT_TEST_COVERAGE.md
   │  ├─ N02_INTEGRATION_TESTS.md
   │  ├─ PHASE_N_PREPARATION.md
   │  ├─ PHASE_N_CLOSURE_AUDIT.md
   │  ├─ N04/
   │  ├─ N05/
   │  ├─ N06/
   │  └─ N07/
   └─ O/
      └─ PHASE_O_STATUS.md
```

## Classification rules

### `project/`

Phaseをまたぐ全体task、project-wide handoff、amendmentを置きます。

### `phases/<Phase>/`

各Phase固有のPreparation、Status、Closure Auditを置きます。

### `phases/<Phase>/<Task>/`

1 Taskで複数の設計・実行文書が必要な場合に使用します。

### `execution/`

Reference Workstation / Codex等へ渡す一時的な実行handoffを対象Task配下へ置きます。完了後も再現性のため保持できますが、current authorityとは区別します。

## Phase N historical structure

Phase NではN-04〜N-07の検証過程で多数のremediation / benchmark文書が生成されました。

- `phases/N/N04/post-g12/` — Grounded Generation系のhistorical remediation / research
- `phases/N/N04/execution/` — N-04実行handoff
- `phases/N/N05/execution/` — N-05 / R2実行handoff
- `phases/N/N06/` — Retrieval / Vector quality
- `phases/N/N07/` — Failure / Recovery / N07-R01

これらの途中FAIL / BLOCKEDを削除せず、最終Phase N closure authorityと併存させます。

## Document placement rules

今後Planning文書を追加する際は次に従います。

1. 全Phase共通の進捗 / project-wide handoff → `project/`
2. Phase単位のstatus / preparation / closure → `phases/<Phase>/`
3. 特定Taskに複数文書が増える場合 → `phases/<Phase>/<Task>/`
4. 一時的な実行handoff → 対象Task配下の`execution/`
5. 結果・調査報告 → `docs/evaluation/`
6. 設計Decision → `docs/decisions/`
7. 実装設計 → `docs/design/`
8. operator手順 → `docs/operations/`

## Next

次Taskは:

```text
O-02 [P0] 現行設計書を更新する
```

対象はArchitecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundary、およびOffline / Backup / Restore / Retention / Security / External Egress / Failure Recovery / Benchmark条件です。
