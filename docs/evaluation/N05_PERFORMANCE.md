# N-05 — Performance Evaluation

更新日: 2026-10-23

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **BLOCKED / Not Complete — N05D-01〜03 Complete; N05D-04 formal rerun Ready**
- Historical formal run: `20261022T130413+0900`
- Historical formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- Current performance target: **Not Judgeable until N05D-04**

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
docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md
```

formal runnerはproduction canonical dataを使用せず、isolated SQLite fixtureとsample固有Qdrant namespaceを使用する。

外部AI生成は計測境界から除外し、deterministic prebuilt valid Resultを通常のValidation / Diff / Import contractへ通す。

## 6. Historical formal execution

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

## 7. Historical formal evaluator result

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

## 8. Historical post-run validation

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

## 9. Blocker diagnosis and remediation

### 9.1 N05D-01 — Qdrant

N05D-01は**Complete**。

Qdrant問題は`QDRANT_ENVIRONMENT_DEFECT`として分類し、workspace-resident storageから外部runtimeへ切り替えた。

```text
runtime root: C:\Qdrant\SGOKB
config:       C:\Qdrant\SGOKB\qdrant.yaml
Qdrant:       native 1.19.2
HTTP/gRPC:    6333 / 6334
```

旧storageはrollback/evidenceとして保持し、active runtimeには使用しない。

50件のcleanup `ACCESS DENIED`は50/50でRust Windows POSIX rename fallbackにより回復した内部eventであることを相関確認した。未回復rename、delete API failure、残存source directory、terminal cleanup error、surfaced OS error 3/5はいずれも0。

切替後、Vector rebuild、real semantic/filtered query、system integrity、canonical invariance、regressionがPASSした。

### 9.2 N05D-02 — Long-input Harrier

N05D-02は**Complete / VIABLE_FOR_FORMAL_RERUN**。

正式run由来のexact 18,847-token Large Object representationを、frozen Harrier profileのままfresh processで3回実行し、3/3 PASSした。

```text
full trial times: 642.830 / 636.118 / 628.092 s
Torch peak allocated: 51.061 GiB
Torch peak reserved:  56.787 GiB
Windows peak dedicated: ~23.2 GiB
Windows peak shared:    ~34.2 GiB
```

OOM、process kill、検出されたdriver reset、CPU inference fallback、truncation、chunking、model changeはない。

12,278〜16,383 tokenの間で大きなWDDM/shared-memory spill regimeへ入る。これはperformance/host-memoryの重大riskだが、memory completionは成立している。

このdiagnostic値はformal sample/p95ではない。

### 9.3 N05D-03 — Evidence-based remediation

N05D-03は**Complete / READY_FOR_N05D04**。

Evidence reviewの結果:

- D01で必要なQdrant environment remediationは既に適用・受入済み。
- current SGOKB adapter/backendに追加production defectは確定していない。
- D02はcurrent Harrier/representation contractのmemory viabilityを確認済み。
- benchmark runner defectを示す残Evidenceはない。
- よってmodel/revision、Search Representation、batch size、max sequence length、workload、formal Gateは変更しない。
- silent truncation、CPU fallback、任意chunking等のbenchmark shortcutは導入しない。

正本:

`docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`

## 10. Remaining formal risk

N05D-03で解消すべきruntime blockerは残っていないが、formal performance riskは大きい。

特にLargeでは、Object-level Embeddingだけでdiagnostic上約628〜643秒を使用する。完全なformal sampleでは、Package/Validation/Import、他Search RepresentationのEmbedding、Vector sync、Render等も同一totalに含まれる。

したがってLarge warm p95 <= 1200 sを満たすかは未判定であり、N05D-04でのみ決める。

またformal warm policyはpersistent preloaded providerで20 samplesを連続実行する。D02の3回はmemory viability切り分けのためfresh processだった。この差もformal benchmarkが実測すべき対象であり、追加shortcutの理由にはしない。

## 11. N05D-04 authorization

N05D-04は開始可能である。

開始条件:

1. clean `main == origin/main`。
2. 新しいrun_idを使用し、旧formal/D01/D02 evidenceを保持。
3. remediated Qdrant `C:\Qdrant\SGOKB` がlocalhost 6333/6334でready。
4. frozen Harrier model/revision/BF16/CUDA/batch 1/max 32768/overflow rejectを維持。
5. unexpected substantial competing CUDA workloadがないことを記録。勝手に他processを終了しない。
6. host available/committed memoryをenvironment evidenceとして記録。新しいnumeric Gateにはしない。
7. mandatory preflightをPASS。
8. Standard cold-01から正式runを最初から開始。
9. terminal failure/abortを置換しない。

Execution handoff:

`docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md`

## 12. Current conclusion

```text
N05D-01 = Complete
N05D-02 = Complete / VIABLE_FOR_FORMAL_RERUN
N05D-03 = Complete / READY_FOR_N05D04
N05D-04 = Ready / Not Started
N-05     = BLOCKED / Not Complete
performance target = Not Judgeable
```

Next: **N05D-04 — Formal benchmark rerun under the frozen contract**.
