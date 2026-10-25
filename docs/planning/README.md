# Planning documents

`docs/planning/` は、Source Grounded Object Knowledge Base（SGOKB）の進行計画、Phase準備/完了監査、Task一覧、実行handoffを管理する領域です。

Planning文書はPhase / Task単位で整理し、`docs/planning/`直下には原則としてこのIndexだけを置きます。

## Current phase

Phase O — Documentation / Release / Git cleanup は **Complete** です。

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Complete
O-01 README update = Complete
O-02 Current design documentation = Complete
O-03 Prototype Archived / Legacy labels = Complete
O-04 main integration = Complete
O-05 Branch cleanup = Complete
O-06 Release / Tag policy = Complete
Current formal release = v1.0.0
Release commit = 0e1a8464e9db98b4e99169cae6292821f3fd410c
```

Phase Nのformal closure run `20261025T014024+0900` はC01-C07 PASSで、独立ChatGPT reviewにより受理済みです。旧N-07 `47 PASS / 3 FAIL`等のhistorical evidenceは保持し、後続remediation / re-acceptanceと区別します。

Phase Oのclosure stateは [`phases/O/PHASE_O_STATUS.md`](phases/O/PHASE_O_STATUS.md) を参照してください。

## Current authority

- Phase O closure status: [`phases/O/PHASE_O_STATUS.md`](phases/O/PHASE_O_STATUS.md)
- O-05 branch cleanup result: [`phases/O/O05_BRANCH_CLEANUP.md`](phases/O/O05_BRANCH_CLEANUP.md)
- O-06 Release / Tag / Breaking Change policy: [`../decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md`](../decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md)
- v1.0.0 Release Note: [`../releases/v1.0.0.md`](../releases/v1.0.0.md)
- Release index: [`../releases/README.md`](../releases/README.md)
- Current integrated architecture: [`../design/SGOKB_CURRENT_ARCHITECTURE.md`](../design/SGOKB_CURRENT_ARCHITECTURE.md)
- Current design index: [`../design/README.md`](../design/README.md)
- Operational safety / recovery: [`../operations/OPERATIONAL_SAFETY_RECOVERY.md`](../operations/OPERATIONAL_SAFETY_RECOVERY.md)
- 1 Object標準運用: [`../operations/OBJECT_STANDARD_WORKFLOW.md`](../operations/OBJECT_STANDARD_WORKFLOW.md)
- 全体task master: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- 全体handoff: [`project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`](project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md)
- Phase N closure planning authority: [`phases/N/PHASE_N_CLOSURE_AUDIT.md`](phases/N/PHASE_N_CLOSURE_AUDIT.md)
- Phase N formal result: [`../evaluation/PHASE_N_CLOSURE_AUDIT.md`](../evaluation/PHASE_N_CLOSURE_AUDIT.md)

project-wide task masterにhistorical planning stateが残る場合、Phase Oについては`PHASE_O_STATUS.md`のclosure stateを優先する。

## Phase O task state

| Task | Status | Purpose |
|---|---|---|
| O-01 | **Complete** | READMEを新SGOKBへ全面更新 |
| O-02 | **Complete** | current architecture / operations designを整理・更新 |
| O-03 | **Complete** | Prototype文書へArchived / Legacy表示 |
| O-04 | **Complete** | branch historyを`main`へ統合 |
| O-05 | **Complete** | 不要remote branch 35本を削除し`main`のみへ整理 |
| O-06 | **Complete** | `v1.0.0` Release / Tag policy、Prototype境界、Breaking Change記録、tag publication / verification |

O-04はPhase Oの通常順序より先にユーザー指示で実施済みです。全remote branch historyの最終統合commitは`77d79ccac1017f167736c742ac199858a3a010a7`です。

## O-02 result

O-02では次をcurrent design authority surfaceとして追加・整理した。

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
  - Architecture / Data Model / Evidence Exchange / Retrieval / CLI / MCP / UPDS Boundary
  - canonical / derived / transient boundary
  - current R2 representation family / Harrier / Qdrant baseline
  - responsibility / failure isolation / authority map
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
  - Offline / graceful degradation
  - Security / External Egress
  - Composite Backup / Verify / Restore
  - RPO / RTO
  - Retention / Hard delete
  - Failure Recovery
  - Benchmark / Reference Workstation conditions
- `docs/design/README.md`
  - current detailed design index
  - historical / research design warning

既存のObject / Source / Evidence / Version / Retrieval / MCP個別contract自体の意味は変更していない。O-02はそれらを現在形のsystem-wide designへ統合したTaskである。

## O-03 result

`docs/archive/prototype-0.2/`の18 Markdown文書を棚卸しした。12文書は既にArchive / Historical表示を持っていたため保持し、direct viewで表示がなかった次の6文書へ統一 `ARCHIVED / LEGACY — Prototype 0.2` warningを追加した。

```text
AI_CAPABILITY_BENCHMARK.md
DEVELOPMENT_STATUS.md
KNOWLEDGE_PIPELINE_EFFICIENCY_REDESIGN.md
MODEL_COMPARISON_PLAN.md
PROTOTYPE.md
PROTOTYPE_UPGRADE.md
```

O-02完了commitとの差分では6文書すべてが7行追加・0行削除で、歴史本文の意味内容は変更していない。

## O-05 result

O-05開始時のlive GitHub inventoryではremote branchは36本で、`main`以外の35本をcleanup candidateとした。open PRは0件、cleanup candidateのprotected branchも0本。

O-04の全branch integration確認に加え、O-05ではplanning再編 / Phase N closure / N07 / N06 / R2 / N04の代表tipをcurrent `main`と再比較し、すべて`behind_by=0`かつbranch HEAD自身がmerge baseであることを確認した。削除後に失われる未統合historyはないと判定した。

ユーザーがGit clientから35本を削除した後、live GitHubを再確認した結果:

```text
remote branches = 1
remaining branch = main
open PR = 0
main HEAD before status updates = 4f16835aef54206c248240c40d3870f1d0e35cfd
```

branch cleanup前後で`main` HEADは不変であり、history変更はない。O-05はComplete。詳細は [`phases/O/O05_BRANCH_CLEANUP.md`](phases/O/O05_BRANCH_CLEANUP.md) を参照する。

## O-06 result

Release / Tag policyを次のように固定した。

```text
Legacy line      = Prototype 0.2.x (untagged historical line)
Current line     = SGOKB 1.x
First release    = 1.0.0
Git tag          = v1.0.0
Package version  = 1.0.0
```

Prototype 0.2にはretroactive tag / GitHub Releaseを作らない。historical authorityは`docs/archive/prototype-0.2/`とGit historyに残す。

v1.0.0 Release Noteでは次をBreaking Changeとして記録した。

- Fragment / Final Document canonical modelの廃止
- Prototype DBのin-place migration非対応
- Object-centered `sgokb` CLIへの変更
- hierarchical multi-vector R2 Searchへの変更
- explicit Evidence Package / Structured Result boundary
- read-only MCP contract
- SGOKB World/Object Knowledge ↔ UPDS Personal Inference boundary

`pyproject.toml`は`version = "1.0.0"`へ更新し、Prototype descriptionもcurrent SGOKBへ更新した。

frozen release commit:

```text
0e1a8464e9db98b4e99169cae6292821f3fd410c
```

live GitHub verification:

```text
tag ref    = refs/tags/v1.0.0
tag object = a418096b5139027cd9ccaaf47fb99a4309cb4b1e
tag target = 0e1a8464e9db98b4e99169cae6292821f3fd410c
```

意図したrelease commitとtag targetが一致したため、O-06はComplete。Phase OもCompleteへclosureした。

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
      ├─ PHASE_O_STATUS.md
      └─ O05_BRANCH_CLEANUP.md
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

1. 全Phase共通の進捗 / project-wide handoff → `project/`
2. Phase単位のstatus / preparation / closure → `phases/<Phase>/`
3. 特定Taskに複数文書が増える場合 → `phases/<Phase>/<Task>/`
4. 一時的な実行handoff → 対象Task配下の`execution/`
5. 結果・調査報告 → `docs/evaluation/`
6. 設計Decision → `docs/decisions/`
7. 実装設計 → `docs/design/`
8. operator手順 / operational safety → `docs/operations/`
9. Release Note / compatibility boundary → `docs/releases/`

## Next

Phase Oに残タスクはない。

次の開発Phaseまたはmaintenance taskは別途定義する。以後のReleaseはO-06で確定したSemVer / immutable tag / Breaking Change policyに従う。
