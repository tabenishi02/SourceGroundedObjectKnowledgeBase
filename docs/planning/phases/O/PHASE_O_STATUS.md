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
| O-03 | **Next / Not Started** | Prototype文書へArchived / Legacy表示を追加 |
| O-04 | **Complete** | 全remote branch historyを`main`へ統合。統合commit `77d79ccac1017f167736c742ac199858a3a010a7` |
| O-05 | Not Started | 不要branch cleanup |
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

## Accepted status carried forward

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 = Complete
O-02 = Complete
O-04 = Complete
Next = O-03
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

`O-03 [P1] Prototype文書へArchived/Legacy表示を追加する`。

O-03では旧Prototype資料がcurrent SGOKB specificationと誤認されないよう、archive入口・代表文書・必要なreference linkにArchived / Legacy stateを明示する。Historical evidence自体は削除・改変しない。
