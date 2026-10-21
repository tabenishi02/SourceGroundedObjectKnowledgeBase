# N-05 — Performance Benchmark

更新日: 2026-10-22

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **Active — benchmark contract frozen / Reference Workstation formal measurement pending**
- Contract: `benchmark/n05-performance-contract-v1.json`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
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

### Included

Pre-analysis:

```text
Evidence Retrieval
Package selection / budget
manifest / instructions
Package build
Package stage
Package preflight
```

Post-analysis:

```text
Result Validation
Diff / Review artifact generation
Version Import / current promotion
Search Representation update
incremental Object / Facet / Statement Embedding
incremental Vector Index update
standard derived rendering
```

Machine evidenceでは次の8 segmentとして記録する。

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

`package_build`はObjectEvidencePackageBuilder内部のEvidence Retrieval / selectionを含む。

`derived_incremental_sync`はSearch Representation / Embedding / Vector Indexの通常incremental pathを含む。

### Excluded

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

full rebuildはFailure / Recoveryまたはbackend lifecycleの別計測であり、1 Object normal p95へ混ぜない。

## 3. Reference Environment

正式結果はNFR-PERF-02のReference Workstationだけで判定する。

```text
OS   Windows 11
CPU  Intel Core i5-13600KF
RAM  128 GB
GPU  NVIDIA GeForce RTX 4090 24 GB
Disk benchmark時の実device / volume / free spaceを記録
```

さらに次をraw evidenceへ固定する。

```text
git HEAD
Python version
Embedding model + exact revision
Qdrant version
Qdrant transport
collection prefix
model cache mode
```

別PC、GPU無効、別Embedding model、別Vector backendの値をReference resultへ混ぜない。

## 4. Workload profiles

### Standard

Requirement envelope:

```text
Source                   5..20
Evidence candidates      <= 1000
Package Evidence         50..200
Knowledge Statements     <= 500
```

Reference fixture target:

```text
Source                   10
Evidence candidates      500
Package Evidence         120
Knowledge Statements     300
```

Gate:

```text
warm p95 <= 600 s
```

### Large

Requirement envelope:

```text
Source                   20..100
Evidence candidates      <= 5000
Package Evidence         200..500
Knowledge Statements     <= 2000
```

Reference fixture target:

```text
Source                   40
Evidence candidates      2000
Package Evidence         350
Knowledge Statements     1200
```

Gate:

```text
warm p95 <= 1200 s
```

## 5. Why N-03 alone is not the performance fixture

N-03は6 Object / 8 real Web Captureで、実データvertical sliceとして後続Phase Nに再利用する。

しかしN-05 Standard/Large workloadは1 Objectに5〜100 Source、最大500 Package Evidence、最大2000 Knowledge Statementを持つload profileであり、N-03 datasetだけではそのload shapeを保証しない。

したがって:

```text
N-03 = ecological / real-data integration reference
N-05 synthetic load fixture = deterministic performance load shape
N-06 = retrieval / ranking quality evidence
```

と責務を分離する。

N-05 synthetic fixtureはcanonical schema/public workflowを使って作るが、検索品質や意味品質の証拠として使用しない。

## 6. Isolation

benchmarkはproduction DBを使用しない。

各sampleで:

```text
.local/n05/<run_id>/<profile>/<condition>/<sample_id>/
```

へSQLite / Package / Result / Render evidenceを隔離する。

Qdrantもsample固有collection prefixを使用する。

各sampleは同一のfrozen starting stateから開始する。前sampleのImport、Embedding、Vectorが後sampleへ累積してはならない。

## 7. Cold / Warm policy

### Cold diagnostic

各profile最低3 sample。

- cold値は正式10/20分Gateへ使用しない。
- first-use/model/backend initialization costを診断するため保存する。
- cold sampleの失敗もraw evidenceから削除しない。

### Warm formal

各profile最低20 sample。

- Standard/Largeの正式p95はwarm sampleだけから算出する。
- p95はnearest-rank `ceil(0.95 * n)`。
- warm sampleに`FAIL`または`ABORTED`が1件でもあれば、そのprofileはFAIL。
- 失敗sampleの代わりに追加成功sampleを採用してはならない。
- bounded automatic retryを行った場合、retry時間をtotalへ含め`retry_count`へ記録する。

## 8. Timing semantics

各sampleの`total_seconds`はIncluded segmentのlocal automatic wall-clockを対象とする。

外部境界で停止している時間は加算しない。

segment timerはmonotonic clockを使用する。

結果には最低限:

```text
min
p50
p95
max
segment p95
retry count
warm failure count
cold diagnostic
```

を残す。

## 9. Result semantics

### PASS

- Standard / Large両方のworkloadがcontract内。
- required environment metadataあり。
- cold各3以上、warm各20以上。
- formal warm failure 0。
- Standard warm p95 <= 600 s。
- Large warm p95 <= 1200 s。

### FAIL

valid formal workloadで:

- warm p95がtarget超過、または
- warm sampleにterminal failure / abortがある。

### BLOCKED

- workloadがenvelope外。
- sample不足。
- environment metadata不足。
- Reference runtimeを実行できない。
- raw evidenceが不足/破損。

`BLOCKED`をSGOKB性能FAILへ読み替えない。

## 10. Deterministic evaluator

```powershell
python benchmark/tools/n05_evaluate_performance.py `
  --evidence .local/n05/<run_id>/performance-evidence.json `
  --output .local/n05/<run_id>/performance-evaluation.json
```

exit code:

```text
0 PASS
1 FAIL
2 BLOCKED
```

Evaluator自身の回帰:

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
```

## 11. Mandatory preflight before formal measurement

Reference Workstationでformal sampleを開始する前に:

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

さらに:

- `main` / expected Git HEADを記録。
- Qdrant reachableを確認。
- frozen local Embedding model/revisionを記録。
- disk / free spaceを記録。
- production canonical DBを参照していないことを確認。

## 12. Current execution state

2026-10-22、Reference WorkstationへのRemote Desktop Commander接続は確認した。

ただしRemote Desktop Commanderのcurrent monthly execution limitによりcommand実行が拒否されたため、Reference Workstationでのformal samplesは未実行である。

したがって現時点では:

```text
Benchmark contract   Frozen
Evaluator            Implemented
Evaluator tests      Added / Reference Workstation execution pending
Formal raw evidence  Not produced
N-05 verdict         BLOCKED (execution access), not FAIL
N-05 status          Active / not Complete
```

実測値を推定・捏造してPASS/FAILを付けない。

## 13. Completion condition

N-05 Completeには次が必要。

1. Reference Workstation preflight PASS。
2. Standard cold >=3 / warm >=20取得。
3. Large cold >=3 / warm >=20取得。
4. raw evidence保存。
5. deterministic evaluator実行。
6. Standard / Large formal verdict確定。
7. full regression / Ruff / diff check。
8. human-readable evaluation documentへ実測結果を記録。

実測が完了するまでN-05をCompleteとしない。
