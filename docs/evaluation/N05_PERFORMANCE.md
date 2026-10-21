# N-05 — Performance Evaluation

更新日: 2026-10-22

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **BLOCKED — Reference Workstation formal measurement not executed**
- Task completion: **Not Complete**
- Blocker type: **Execution access / not a performance failure**

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

Reference target:

```text
Source                 10
Evidence candidates    500
Package Evidence       120
Knowledge Statements   300
```

Formal limit:

```text
p95 <= 600 s
```

### Large

Reference target:

```text
Source                 40
Evidence candidates    2000
Package Evidence       350
Knowledge Statements   1200
```

Formal limit:

```text
p95 <= 1200 s
```

## 5. Implemented evaluation assets

```text
benchmark/n05-performance-contract-v1.json
benchmark/n05-performance-evidence-template-v1.json
benchmark/tools/n05_evaluate_performance.py
tests/test_n05_performance_evaluator.py
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/execution/N05_REFERENCE_WORKSTATION_HANDOFF.md
```

Evaluator behavior:

- environment metadata不足 → BLOCKED
- workload envelope外 → BLOCKED
- minimum sample不足 → BLOCKED
- warm terminal failureあり → FAIL
- warm p95 target超過 → FAIL
- Standard/Largeとも条件内 → PASS

## 6. Reference Workstation execution attempt

2026-10-22、Remote Desktop Commanderを使用してReference Workstationで次を確認しようとした。

```text
repository working tree
branch
local HEAD
origin/main
```

Reference Workstationへのdevice connectionは取得できた。

しかしcommand executionはRemote Desktop Commanderのcurrent monthly execution limitにより拒否された。

そのため:

```text
preflight tests      Not executed on Reference Workstation
cold samples         0 formal samples
warm samples         0 formal samples
Standard p95         Not measured
Large p95            Not measured
formal performance   Not judgeable
```

## 7. Formal verdict

```text
N-05 verdict = BLOCKED
```

理由:

> Reference Workstation上でformal measurementを実行するためのcommand accessを現在利用できず、required raw evidenceが存在しない。

この`BLOCKED`は以下を意味しない。

```text
SGOKB is too slow
Standard > 600 s
Large > 1200 s
performance requirement failed
```

実測していないため、PASSまたはFAILを推定してはならない。

## 8. Evidence integrity

本Taskでは性能値の代替としてUnit Test時間や過去Phaseのwall-clockを流用しない。

理由:

- workloadが異なる。
- timing boundaryが異なる。
- cold/warm条件が異なる。
- Standard/Large profileを満たす保証がない。

したがって正式N-05 resultはReference Workstation raw evidenceからのみ確定する。

## 9. Remaining work to complete N-05

1. Reference Workstation command accessを利用可能にする。
2. mandatory preflightをPASSさせる。
3. isolated Standard/Large fixtureを構築する。
4. cold各3以上を取得する。
5. warm各20以上を取得する。
6. raw evidenceを保存する。
7. deterministic evaluatorを実行する。
8. post-run regressionをPASSさせる。
9. この文書へ実測p50/p95/max/segment p95/retry/failureを記録する。
10. PASS/FAILを確定し、N-05 statusを更新する。

## 10. Current conclusion

N-05の測定方法、負荷profile、formal Gate、evidence schema、判定器、実行handoffまでは確定した。

**性能値そのものだけは未測定であるため、N-05は現時点でCompleteではない。**
