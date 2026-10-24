# Phase O — Documentation / Release / Git cleanup

Updated: 2026-10-25

- Phase: `Phase O — Documentation / Release / Git cleanup`
- Status: **Active**
- Previous phase: `Phase N — Test / Evaluation / Acceptance` — **Complete / PASS**
- Current Phase O status authority: this document

## Current task state

| Task | Status | Summary |
|---|---|---|
| O-01 | **Complete** | Root READMEを新SGOKBの目的・Architecture・1 Object workflow・ChatGPT manual step・MCP利用例へ全面更新 |
| O-02 | **Complete** | Current Architecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundaryとoperations safety/recoveryを統合文書化 |
| O-03 | **Complete** | Prototype 0.2文書をArchived / Legacyとして明示しcurrent specificationとの誤認を防止 |
| O-04 | **Complete** | 全remote branch historyを`main`へ統合。統合commit `77d79ccac1017f167736c742ac199858a3a010a7` |
| O-05 | **BLOCKED** | 35 branchの削除安全性は確認済み。current GitHub action setにremote branch/ref削除mutationがなく削除自体は未実行 |
| O-06 | Not Started | Release / Tag policyとBreaking Change記録 |

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

## O-05 audit / blocker

O-05開始時にlive GitHub branch inventoryを再取得した。

- remote branch: **36本**
- keep: `main`
- cleanup candidate: **35本**
- protected cleanup candidate: **0本**
- open pull request: **0件**

O-04時点の全branch integration後に新規branchは増えていない。独立系列の代表tipについてcurrent `main`へのcompareを再実施し、すべて`behind_by=0`かつmerge baseがbranch HEAD自身であることを確認した。

- `docs/planning-structure-reorganization`
- `phase-n-closure-audit`
- `n07-r01-composite-backup-restore`
- `n06-retrieval-vector-quality`
- `r2-09-runner-wiring-remediation`
- `phase-n/n04g25a-development-classifier-benchmark`

これらはplanning再編、Phase N closure、N07、N06、R2、N04の各独立系列を代表する。O-04の全branch統合確認と合わせ、35本すべてについて削除後に失われる未統合historyはないと判定した。

詳細なbranch inventory・HEAD・compare結果・削除policyは [`O05_BRANCH_CLEANUP.md`](O05_BRANCH_CLEANUP.md) を正本とする。

ただし、現在このChatGPT sessionで利用可能なGitHub action setにはremote branch / Git ref削除mutationが提供されていない。branchを`main`へforce-moveする等の代替操作を削除済みとは扱わない。

したがってO-05は**安全性監査まで完了、remote branch削除は未実行、Status = BLOCKED**とする。削除mutationが利用可能なGitHub API / Git client環境で35本を削除し、remote branchが`main`のみになったことを再確認した時点でCompleteへ進める。

## Accepted status carried forward

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 = Complete
O-02 = Complete
O-03 = Complete
O-04 = Complete
O-05 = BLOCKED
Next = O-05 remote branch deletion
```

Phase N authority:

- `docs/evaluation/PHASE_N_CLOSURE_AUDIT.md`
- `docs/planning/phases/N/PHASE_N_CLOSURE_AUDIT.md`
- `benchmark/results/phase-n-closure-audit.json`

Current design authority entrypoints:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/design/README.md`
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`

## Next

`O-05 [P1] 不要branchを削除する` のremote deletionを完了する。

削除後はbranch inventoryを再取得し、`main`のみが残ることを確認したうえでO-05をCompleteにする。O-06へはその後進む。