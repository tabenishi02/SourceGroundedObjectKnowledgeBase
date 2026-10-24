# Phase O — Documentation / Release / Git cleanup

Updated: 2026-10-25

- Phase: `Phase O — Documentation / Release / Git cleanup`
- Status: **Active**
- Previous phase: `Phase N — Test / Evaluation / Acceptance` — **Complete / PASS**

## Current task state

| Task | Status | Summary |
|---|---|---|
| O-01 | **Complete** | Root READMEを新SGOKBの目的・Architecture・1 Object workflow・ChatGPT manual step・MCP利用例へ全面更新 |
| O-02 | **Next / Not Started** | 現行設計書をArchitecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundary等で整理 |
| O-03 | Not Started | Prototype文書へArchived / Legacy表示を追加 |
| O-04 | **Complete** | 全remote branch historyを`main`へ統合。統合commit `77d79ccac1017f167736c742ac199858a3a010a7` |
| O-05 | Not Started | 不要branch cleanup |
| O-06 | Not Started | Release / Tag policyとBreaking Change記録 |

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

## Accepted status carried forward

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 = Complete
O-04 = Complete
Next = O-02
```

Phase N authority:

- `docs/evaluation/PHASE_N_CLOSURE_AUDIT.md`
- `docs/planning/phases/N/PHASE_N_CLOSURE_AUDIT.md`
- `benchmark/results/phase-n-closure-audit.json`

## Next

`O-02 [P0] 現行設計書を更新する`。

O-02ではREADMEの概要を正本設計へ置き換えるのではなく、Architecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundary、Offline / Backup / Restore / Retention / Security / External Egress / Failure Recovery / Benchmark条件をcurrent design documentationとして整理する。
