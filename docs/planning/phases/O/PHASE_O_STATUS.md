# Phase O — Documentation / Release / Git cleanup

Updated: 2026-10-25

- Phase: `Phase O — Documentation / Release / Git cleanup`
- Status: **Complete**
- Previous phase: `Phase N — Test / Evaluation / Acceptance` — **Complete / PASS**
- Current Phase O status authority: this document

## Current task state

| Task | Status | Summary |
|---|---|---|
| O-01 | **Complete** | Root READMEを新SGOKBの目的・Architecture・1 Object workflow・ChatGPT manual step・MCP利用例へ全面更新 |
| O-02 | **Complete** | Current Architecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundaryとoperations safety/recoveryを統合文書化 |
| O-03 | **Complete** | Prototype 0.2文書をArchived / Legacyとして明示しcurrent specificationとの誤認を防止 |
| O-04 | **Complete** | 全remote branch historyを`main`へ統合。統合commit `77d79ccac1017f167736c742ac199858a3a010a7` |
| O-05 | **Complete** | 不要remote branch 35本を削除し、remote branchを`main` 1本へ整理 |
| O-06 | **Complete** | `v1.0.0` release boundary / policy / Breaking Change / metadataを確定し、annotated tagをrelease commitへ作成・live verification |

Phase Oのcurrent statusは本書を正本とする。project-wide task masterに古いPhase O checklist/statusが残る場合、本書の状態が優先する。

## O-01 result

O-01では次をcurrent README surfaceとして整備した。

- `README.md`
  - SGOKBの目的と非目的
  - canonical / derived boundaryを含む全体Architecture
  - installation / local runtime
  - 1 Object標準workflow
  - Package export → ChatGPT → `result.json`返却のHuman-in-the-loop boundary
  - Lexical / Semantic / Hybrid / Similarity
  - read-only MCP serverと主要Tool利用例
  - Repository layout / documentation entrypoints / development verification
- `docs/README.md`
  - Phase N完了・Phase O開始後のcurrent documentation indexへ更新
- `docs/planning/README.md`
  - current phase / authority / directory layoutをPhase Oへ更新

O-01は既存のaccepted design contractをREADMEへ要約するTaskであり、Object / Evidence / Search / MCP semanticsそのものは変更していない。

## O-02 result

O-02ではPhase A〜Nのaccepted contractを現在形のsystem-wide designへ統合した。

### `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`

Current integrated architectureとして次を固定した。

- SGOKB core responsibility / non-goals
- Source / Snapshot / Raw / Evidence
- Object / Class / Facet / Statement / Relation / Version
- Evidence Package → external AI → Structured Result → explicit Import
- canonical / derived / transient classification
- R2 active representation family `object_overview / facet / statement` + Evidence Search
- frozen Harrier 0.6B revision / 1024-dim Embedding Space
- Qdrant Vector backend boundary
- Lexical / Semantic / Hybrid / Similarity
- Object-centered CLI
- read-only MCP / `build_context`
- SGOKB World/Object Knowledge Provider ↔ UPDS Personal Inference Consumer boundary
- runtime composition / failure isolation / security boundary
- detailed design authority map

### `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`

Operational designとして次を現在形へ統合した。

- local-first / Offline / graceful degradation
- External Egress / secret / untrusted Result boundary
- SQLite-only backupとcomplete Composite backupの区別
- Composite create / verify / alternate-root restore
- restore fail-closed conditions / atomic publication
- RPO <= 24 h / RTO <= 4 h target
- daily >=7 / weekly >=4 retention targetとscheduler未実装境界
- hard delete / archive policy
- canonical restore後のR2 Derived Search rebuild
- Failure / Recovery categories
- Reference Workstation / N-05 performance / retrieval benchmark conditions
- accepted limitationsをproduction-scale claimへ拡張しない境界

### `docs/design/README.md`

Current detailed design indexを追加し、current architecture / operations entrypointとhistorical Grounded Generation researchのnon-current ownership warningを明示した。

### Existing contracts

O-02は既存のaccepted Object / Evidence / Version / Retrieval / MCP contractの意味を変更していない。個別schema・algorithmは従来のdetail documentをnormative authorityとして維持する。

## O-03 result

`docs/archive/prototype-0.2/`を全件棚卸しした。

- Markdown document: **18 files**
- 既にArchive / Historical表示あり: **12 files**
- direct viewでArchive表示がなかった文書: **6 files**

未表示だった次の6文書へ、統一した `ARCHIVED / LEGACY — Prototype 0.2` warningを先頭追加した。

```text
AI_CAPABILITY_BENCHMARK.md
DEVELOPMENT_STATUS.md
KNOWLEDGE_PIPELINE_EFFICIENCY_REDESIGN.md
MODEL_COMPARISON_PLAN.md
PROTOTYPE.md
PROTOTYPE_UPGRADE.md
```

warningは次を明示する。

- Prototype 0.2の歴史資料である。
- current SGOKB specification / design / operationではない。
- current authorityとして`docs/design/SGOKB_CURRENT_ARCHITECTURE.md`とroot `README.md`を参照する。
- 本文は再現性・設計経緯のため当時のまま保持する。

O-02完了commitとの比較で、この6ファイルはいずれも**7行追加 / 0行削除**であり、Prototype本文に意味変更を加えていないことを確認した。既存12文書のArchive表示とarchive-level `README.md`は歴史資料としてそのまま保持した。

## O-05 result

O-05開始時にlive GitHub branch inventoryを再取得した。

- remote branch: **36本**
- keep: `main`
- cleanup candidate: **35本**
- protected cleanup candidate: **0本**
- open pull request: **0件**

O-04時点の全branch integration後に新規branchは増えていなかった。独立系列の代表tipについてcurrent `main`へのcompareを再実施し、すべて`behind_by=0`かつmerge baseがbranch HEAD自身であることを確認した。

詳細なbranch inventory・HEAD・compare結果・削除policyは [`O05_BRANCH_CLEANUP.md`](O05_BRANCH_CLEANUP.md) を正本とする。

このChatGPT sessionにはremote branch / Git ref削除mutationが提供されていなかったため、ユーザーがGit clientから35本を削除した。削除後にlive GitHubを再確認し、次を確認した。

```text
remote branches = 1
remaining branch = main
open PR = 0
main HEAD before cleanup status update = 4f16835aef54206c248240c40d3870f1d0e35cfd
```

branch削除前後で`main` HEADは不変だったため、cleanupによる`main` historyの変更はない。35本の不要branch削除が完了し、O-05を**Complete**とする。

## O-06 result

O-06ではRelease / Tag / Breaking Change境界を次のように確定した。

```text
Legacy line      = Prototype 0.2.x (untagged historical line)
Current line     = SGOKB 1.x
First release    = 1.0.0
Git tag          = v1.0.0
Package version  = 1.0.0
```

実施内容:

- `docs/decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md`
  - Semantic Versioning
  - immutable `vMAJOR.MINOR.PATCH` tag
  - Prototype 0.2へretroactive tagを作らない方針
  - formal Release gate
  - Breaking Change記録要件
- `docs/releases/v1.0.0.md`
  - Prototype 0.2 → v1.0.0のBreaking Changes
  - DB / CLI / Search / AI workflow / MCP / UPDS boundary
  - migration guidance
  - acceptance basis / known limitations
- `docs/releases/README.md`
  - Release index
- `pyproject.toml`
  - `version = "1.0.0"`
  - Prototype説明をcurrent SGOKB descriptionへ更新
- root `README.md` / `docs/README.md`
  - `v1.0.0` release boundaryとRelease documentationへの入口を追加

O-06開始時点でlive GitHubを確認し、既存Git tag = **0件**、GitHub Release = **0件**だった。過去に存在しなかったPrototype release boundaryを後付けしない。

release payloadを含むfrozen release commitは次である。

```text
0e1a8464e9db98b4e99169cae6292821f3fd410c
```

ユーザーがGit clientからannotated tag `v1.0.0`を作成・pushした後、live GitHubで次を確認した。

```text
tag ref       = refs/tags/v1.0.0
tag object    = a418096b5139027cd9ccaaf47fb99a4309cb4b1e
tag type      = annotated tag
tag target    = 0e1a8464e9db98b4e99169cae6292821f3fd410c
tag message   = SGOKB v1.0.0
```

意図したrelease commitとtag targetは完全一致した。tagは以後immutable history markerとして扱い、silent move / reuseしない。

GitHub Release UI objectの作成はO-06の必須条件ではない。repository-side Release Noteと正式tagがcurrent release boundaryの正本であり、将来GitHub Releaseを公開する場合も`docs/releases/v1.0.0.md`と意味内容を一致させる。

**O-06 = Complete**。

## Phase O closure

Phase Oの完了条件「`main`が新設計を正本として示し、旧Prototypeと混同されない」を満たした。

- current README / design / operations documentationを整備済み。
- Prototype 0.2 documentationはArchived / Legacyとして明示済み。
- 全remote branch historyを`main`へ統合済み。
- 不要remote branchを削除し`main`のみへ整理済み。
- Release / Tag policyを確定済み。
- Prototype 0.2 ↔ current SGOKB境界を`v1.0.0`で明示済み。
- Breaking Changes / migration guidanceをrepository-side Release Noteへ記録済み。
- package metadataは`1.0.0`へ更新済み。
- `v1.0.0` annotated tag targetをlive GitHubで検証済み。

**Phase O = Complete**。

## Accepted status carried forward

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Complete
O-01 = Complete
O-02 = Complete
O-03 = Complete
O-04 = Complete
O-05 = Complete
O-06 = Complete
Current formal release = v1.0.0
Release commit = 0e1a8464e9db98b4e99169cae6292821f3fd410c
```

Phase N authority:

- `docs/evaluation/PHASE_N_CLOSURE_AUDIT.md`
- `docs/planning/phases/N/PHASE_N_CLOSURE_AUDIT.md`
- `benchmark/results/phase-n-closure-audit.json`

Current design / release authority entrypoints:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/design/README.md`
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- `docs/decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md`
- `docs/releases/v1.0.0.md`

## Next

Phase Oに残タスクはない。

次の開発Phase / maintenance taskは別途定義する。既存`v1.0.0` tagは移動・再利用せず、以後の正式ReleaseはO-06で確定したSemVer / Release policyに従う。
