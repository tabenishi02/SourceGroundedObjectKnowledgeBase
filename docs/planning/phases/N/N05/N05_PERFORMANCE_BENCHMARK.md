# N-05 — Performance Benchmark

更新日: 2026-10-22

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **Active / BLOCKED — formal run executed; performance target not judgeable**
- Contract: `benchmark/n05-performance-contract-v1.json`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Runner: `benchmark/tools/n05_run_performance.py`
- Workflow fixture: `benchmark/tools/n05_performance_workflow.py`
- Formal run: `20261022T130413+0900`
- Formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- Parent requirements: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md` NFR-PERF-01〜

## 1. Purpose

SGOKBの1 Objectあたりlocal automatic processingが、Reference Workstation上で実用上の性能目標を満たすことを確認する。

正式Gate:

```text
Standard Object warm p95 <= 600 s
Large Object warm p95    <= 1200 s
```

N-05は外部AIや人間の待ち時間を測るTaskではない。SGOKB自身が実行するlocal automatic segmentだけを測定する。

## 2. Measurement boundary

Included:

```text
package_build
package_stage
package_preflight
result_validation
diff_review
result_import
derived_incremental_sync
render
```

`package_build`はEvidence Retrieval / selectionを含む。

`derived_incremental_sync`はSearch Representation / Embedding / Vector Indexの通常incremental pathを含む。

Excluded:

```text
Source探索
Web Capture network time
human Package review
external export / Drive sync
ChatGPT / external AI操作・生成待ち
Result返却transport
human review / approval wait
full Vector Index rebuild
```

## 3. Reference Environment

正式結果はNFR-PERF-02のReference Workstationだけで判定する。

```text
OS   Windows 11
CPU  Intel Core i5-13600KF
RAM  128 GB
GPU  NVIDIA GeForce RTX 4090 24 GB
```

raw evidenceへGit HEAD、Python、Embedding model/revision、Qdrant version/transport、collection prefix、cache mode、disk情報を固定する。

## 4. Workload profiles

### Standard

```text
Source                   10
Evidence candidates      500
Package Evidence         120
Knowledge Statements     300
Gate                      warm p95 <= 600 s
```

Requirement envelope:

```text
Source                   5..20
Evidence candidates      <= 1000
Package Evidence         50..200
Knowledge Statements     <= 500
```

### Large

```text
Source                   40
Evidence candidates      2000
Package Evidence         350
Knowledge Statements     1200
Gate                      warm p95 <= 1200 s
```

Requirement envelope:

```text
Source                   20..100
Evidence candidates      <= 5000
Package Evidence         200..500
Knowledge Statements     <= 2000
```

## 5. Fixture / isolation policy

N-03はreal-data ecological referenceとして保持するが、N-05 workload shapeはisolated deterministic synthetic fixtureで再現する。

各sampleは同一starting stateから開始し、SQLite / package / result / renderをsample directory配下へ隔離する。

Qdrant collection prefixもsample固有とする。

production canonical DBをbenchmark workloadとして変更しない。

外部AI区間はdeterministic prebuilt valid Resultで置換してよいが、通常のValidation / Diff / Import contractを通す。

## 6. Cold / Warm policy

Cold diagnostic:

```text
>= 3 samples / profile
non-gating
```

Warm formal:

```text
>= 20 samples / profile
nearest-rank p95
terminal failure / abort 0
retry時間をtotalへ含む
```

失敗sampleを削除したり追加成功sampleで置換してはならない。

## 7. Deterministic evaluator

```powershell
python benchmark/tools/n05_evaluate_performance.py `
  --evidence .local/n05/<run_id>/performance-evidence.json `
  --output .local/n05/<run_id>/performance-evaluation.json
```

```text
0 PASS
1 FAIL
2 BLOCKED
```

## 8. Formal runner

Reference Workstation runner:

```text
benchmark/tools/n05_performance_workflow.py
benchmark/tools/n05_run_performance.py
```

runnerは:

- canonical APIsでfixtureを構築する。
- sampleごとにSQLiteをcloneする。
- actual Harrier embeddingを使用する。
- sample固有Qdrant collection prefixを使用する。
- 8 segmentをmonotonic wall-clockで計測する。
- production canonical DB before/after fingerprintを比較する。
- post-run regressionを保存する。

## 9. Formal run 20261022T130413+0900

実行HEAD:

`a7147f9842f94e96944bc7f67b4c3986970462b0`

### Standard

計画どおり23 sampleを開始したが、23 / 23がterminal sample failureとなった。

失敗地点:

```text
Derived Search sync
→ Qdrant payload index creation
→ server-side storage path error
```

観測されたmessageは`gridstore` pathが見つからない旨を示した。

Renderへ到達していないため、required 8-segment evidenceは完成していない。

### Large

`cold-01`のEmbedding処理中に中断した。

観測:

```text
Object representation: 18,847 tokens
batch size: 1
Dedicated VRAM: 約23.2 GiB
Shared GPU memory: 約34.2 GiB
```

後続sampleは実行していない。

このためLargeのrequired sample countを満たさない。

## 10. Formal result

```text
N-05 formal verdict = BLOCKED
N-05 status         = Active / Not Complete
performance target  = Not Judgeable
```

これは性能目標未達を意味しない。

Standard/Largeのformal warm p50 / p95 / maxは報告しない。

## 11. Post-run validation

```text
Evaluator tests: 8 PASS
Full pytest:      517 PASS
Ruff:             PASS
git diff --check: PASS
```

formal runの安全性:

```text
canonical DB unchanged
tracked files unchanged during run
HEAD unchanged during run
```

## 12. Diagnostic phase before rerun

formal runの単純再試行は禁止する。

次を分離して診断する。

```text
N05D-01 Qdrant storage/path blocker diagnosis
N05D-02 Long-input Harrier memory diagnosis
N05D-03 Evidence-based remediation
N05D-04 Formal benchmark rerun
```

詳細:

`docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`

N05D-01 / D-02の診断値はformal performance sampleへ混ぜない。

Gateは変更しない。

## 13. Completion condition

N-05 Completeには次が必要。

1. N05D-01とN05D-02のblockerを診断する。
2. evidenceに基づいて必要な修復を行う。
3. 新しいrun_idでformal benchmarkを最初から実行する。
4. Standard cold >=3 / warm >=20を取得する。
5. Large cold >=3 / warm >=20を取得する。
6. deterministic evaluatorでPASS/FAILを確定する。
7. full regression / Ruff / diff checkをPASSする。
8. human-readable evaluationへ正式統計を記録する。

## 14. Current next task

```text
N05D-01 — Qdrant storage/path blocker diagnosis
```

N-06はN-05のblockerとは独立して進行可能である。
