# N-05 — Performance Evaluation

更新日: 2026-10-22

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **BLOCKED — formal benchmark executed but performance target not judgeable**
- Task completion: **Not Complete**
- Formal run: `20261022T130413+0900`
- Formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- Blocker class: **runtime/backend + long-input embedding resource pressure**

## 1. Evaluation question

Reference Workstation上で、SGOKBの1 Object local automatic processingが次を満たすかを評価する。

```text
Standard Object warm p95 <= 600 s
Large Object warm p95    <= 1200 s
```

正式対象はSGOKB自身のlocal automatic segmentだけである。

## 2. Frozen evaluation contract

Machine-readable contract:

`benchmark/n05-performance-contract-v1.json`

Formal warm sample:

```text
>= 20 samples / profile
nearest-rank p95
terminal failure / abort 0
retry時間をtotalへ含む
```

Cold diagnostic:

```text
>= 3 samples / profile
non-gating
```

## 3. Measurement boundary

Included:

```text
Package build / Evidence retrieval-selection
Package stage
Package preflight
Result validation
Diff review
Result import / current promotion
incremental Search Representation / Embedding / Vector sync
Render
```

Excluded:

```text
Source探索 / Capture network
human review wait
external export / Drive sync
ChatGPT / external AI generation wait
Result return transport
full Vector rebuild
```

## 4. Workload profiles

### Standard

```text
Source                 10
Evidence candidates    500
Package Evidence       120
Knowledge Statements   300
Gate                    warm p95 <= 600 s
```

### Large

```text
Source                 40
Evidence candidates    2000
Package Evidence       350
Knowledge Statements   1200
Gate                    warm p95 <= 1200 s
```

## 5. Implemented evaluation assets

```text
benchmark/n05-performance-contract-v1.json
benchmark/n05-performance-evidence-template-v1.json
benchmark/tools/n05_evaluate_performance.py
benchmark/tools/n05_performance_workflow.py
benchmark/tools/n05_run_performance.py
tests/test_n05_performance_evaluator.py
tests/test_n05_performance_workflow.py
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/execution/N05_REFERENCE_WORKSTATION_HANDOFF.md
```

formal runnerはproduction canonical dataを使用せず、isolated SQLite fixtureとsample固有Qdrant namespaceを使用する。

外部AI生成は計測境界から除外し、deterministic prebuilt valid Resultを通常のValidation / Diff / Import contractへ通す。

## 6. Formal execution

### Run identity

```text
run_id: 20261022T130413+0900
HEAD:   a7147f9842f94e96944bc7f67b4c3986970462b0
```

Reference Workstationで実Harrier / real Qdrantを使用した。

### Standard

計画:

```text
cold 3
warm 20
合計23 sample
```

結果:

```text
23 / 23 sample terminal failure
```

失敗地点はDerived SearchのVector同期で、Qdrant payload index作成時にserver-side storage path errorが発生した。

観測されたエラーは`gridstore`のpathが見つからない旨を示した。

全sampleがRenderまで到達していないため、formal sample schemaに必要な全segment timingが揃っていない。

### Large

`cold-01`のEmbedding処理中にユーザー指示で中断した。

観測:

```text
Object representation: 18,847 tokens
embedding batch size: 1
Dedicated VRAM: 約23.2 GiB
Shared GPU memory: 約34.2 GiB
```

後続sampleは実行していない。

この観測はlong-input embeddingのresource pressureを示すが、Attention kernel / allocator内訳を取得していないためroot causeを断定しない。

## 7. Formal evaluator result

```text
N-05 formal verdict = BLOCKED
```

理由:

- Standardはterminal failureしたが、Render未実行のためrequired segment evidenceが欠けている。
- Largeは必要cold/warm sample数を満たしていない。
- したがってStandard/Largeのformal warm p95を算出できない。

失敗sampleの削除、成功sampleによる置換、欠損値の補完は行っていない。

この`BLOCKED`を次の意味へ読み替えてはならない。

```text
Standard p95 > 600 s
Large p95 > 1200 s
performance requirement failed
performance requirement passed
```

性能目標の達成・未達は未判定である。

## 8. Post-run validation

Reference Workstation post-run:

```text
Evaluator tests: 8 PASS
Full pytest:      517 PASS
Ruff:             PASS
git diff --check: PASS
```

安全性:

```text
production canonical DB unchanged
tracked files unchanged during formal run
formal run HEAD unchanged
```

formal run自体がcanonical user dataを破壊した証拠はない。

## 9. Findings

### 9.1 Qdrant real-path gap

Unit/Integration testがPASSしていても、Reference Workstationのreal Qdrant storage lifecycleが正常であることまでは保証していなかった。

今回、actual payload-index creation pathでstorage-related failureが発生した。

現時点ではQdrant environment、filesystem、benchmark runner、SGOKB adapter、backend本体のどこがroot causeかは未確定である。

### 9.2 Long Object representation resource pressure

Large Objectの18,847-token representationはHarrierのconfigured 32,768-token上限内ではある。

しかしReference WorkstationのRTX 4090 24GB上で、batch size 1でもdedicated VRAMをほぼ使い切りshared GPU memoryへ大きく退避した。

したがって「入力長がcontract上許容される」ことと「Reference Workstationで実用的なresource profileで処理できる」ことは別問題である。

## 10. Diagnostic work before rerun

正式benchmarkをそのまま再実行しない。

次の診断をformal timingとは分離して行う。

```text
N05D-01 Qdrant storage/path blocker diagnosis
N05D-02 Long-input Harrier memory diagnosis
N05D-03 Evidence-based remediation
N05D-04 Formal benchmark rerun
```

正本:

`docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`

Gateは維持する。

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

## 11. Current conclusion

今回のN-05 formal executionは有効なBLOCKED evidenceである。

- benchmark runnerはReference Workstationで実行された。
- Standard/Large workloadを開始できた。
- 2つの独立したruntime blockerを発見した。
- 性能targetのPASS/FAIL判定に必要なformal sampleは揃わなかった。

したがって:

```text
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
next = N05D-01 Qdrant diagnosis
```
