# N-05 — Reference Workstation Performance Execution Handoff

更新日: 2026-10-22

- Task: `N-05 [P0] — Performance`
- Status: **Execution pending / BLOCKED by current workstation command access**
- Contract: `benchmark/n05-performance-contract-v1.json`
- Evidence template: `benchmark/n05-performance-evidence-template-v1.json`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Plan: `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`

## 1. Goal

Reference WorkstationでSGOKBの1 Object local automatic segmentを計測し、次を正式判定する。

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

外部AI生成、人間待ち、Source Capture network、Drive/export、Result返送は計測しない。

## 2. Start conditions

GitHub `main`を正本とし、開始時点のcommit SHAをraw evidenceへ記録する。

Repository:

```text
C:\codex\SourceGroundedObjectKnowledgeBase
```

開始前にworking treeを確認し、意図しないlocal変更がある場合はformal runを開始しない。

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
```

正式runは`main == origin/main`を原則とする。差異が必要な場合は、その理由とcommit/blob identityをevidenceへ明示する。

## 3. Mandatory preflight

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

失敗時はformal sampleへ進まず、原因を記録する。

## 4. Environment evidence

最低限次を保存する。

```text
git HEAD
Windows version
CPU
RAM GiB
GPU
Python version
Embedding model
Embedding exact revision
Qdrant version
Qdrant transport
Qdrant collection prefix
model cache mode
benchmark volume / free space
```

N-04P-06で受入済みのlocal Semantic / Qdrant runtimeを基本とし、model/backendを変更した場合は別runとして扱う。

## 5. Fixture policy

N-03 real-data DBはecological referenceとして保持するが、N-05のload envelopeを満たすための正式負荷fixtureは隔離して作成する。

Target:

```text
Standard
  Source                 10
  Evidence candidates    500
  Package Evidence       120
  Knowledge Statements   300

Large
  Source                 40
  Evidence candidates    2000
  Package Evidence       350
  Knowledge Statements   1200
```

fixtureはcanonical schema / public workflowと同等の処理経路を通す。検索品質・意味品質を評価するためのfixtureではないため、合成contentでよい。

各sampleは同一starting stateから開始し、前sampleのaccepted Version / Embedding / Vector stateを引き継がない。

## 6. Sample layout

```text
.local/n05/<run_id>/
  environment.json
  fixture/
  standard/
    cold-01/
    cold-02/
    cold-03/
    warm-01/
    ...
    warm-20/
  large/
    cold-01/
    cold-02/
    cold-03/
    warm-01/
    ...
    warm-20/
  performance-evidence.json
  performance-evaluation.json
```

SQLite DB / package / result / render outputをsample directory配下へ隔離する。

Qdrant collection prefixもsample固有にする。

## 7. Timed segments

各sampleでmonotonic wall-clockにより次を独立記録する。

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

### package_build

ObjectEvidencePackageBuilderが行うEvidence Retrieval / selection / budget / package materializationを含む。

### derived_incremental_sync

通常のincremental pathだけを含む。

```text
Search Representation sync
Embedding sync
Vector Index incremental sync
```

full rebuildをこの時間へ混ぜない。

## 8. External boundary handling

Packageが外部AIへ送信されてからResultが戻るまでの時間はN-05対象外。

Formal fixtureでは、この区間をdeterministic prebuilt valid Resultで置き換えてよい。

重要なのは、Result生成時間を短縮してN-05を有利にすることではなく、**元から性能要件の対象外である外部処理を計測境界から除外すること**である。

Result自体は通常のValidation / Diff / Import contractを通過しなければならない。

## 9. Cold run

各profile最低3回。

目的:

- first-use model load
- Qdrant/client initialization
- filesystem/cache cold-start

を診断する。

coldは正式10/20分Gateには使用しない。

## 10. Warm formal run

各profile最低20回。

- warm conditionを固定する。
- 成功sampleだけを選び直してはならない。
- `FAIL`/`ABORTED` sampleを削除しない。
- automatic retryの時間をtotalへ含める。
- retry countを記録する。

20 sampleならnearest-rank p95は19番目に遅い値ではなく、昇順19番目（上位側2番目）を採用する。

## 11. Evidence format

`benchmark/n05-performance-evidence-template-v1.json`をコピーしてraw evidenceを作成する。

各sample:

```json
{
  "sample_id": "standard-warm-01",
  "status": "PASS",
  "total_seconds": 12.345,
  "retry_count": 0,
  "segments": {
    "package_build": 1.0,
    "package_stage": 0.1,
    "package_preflight": 0.2,
    "result_validation": 0.5,
    "diff_review": 0.4,
    "result_import": 1.2,
    "derived_incremental_sync": 8.5,
    "render": 0.445
  }
}
```

上記数値はschema例であり、formal benchmark値ではない。

## 12. Deterministic evaluation

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

raw evidenceは最終判定後も保持する。

## 13. Post-run regression

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

benchmarkによってtracked fileやproduction canonical dataが変化していないことを確認する。

## 14. Result recording

正式run後、次を更新する。

```text
docs/evaluation/N05_PERFORMANCE.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
```

必要ならmachine-readable aggregate resultを`benchmark/results/`へ保存する。

## 15. Current blocker

2026-10-22、このTaskを実行するためRemote Desktop CommanderでReference Workstationへ接続したが、current monthly execution limitによりcommand executionが拒否された。

したがってformal timing samplesはまだ存在しない。

```text
N-05 formal verdict = BLOCKED (execution access)
N-05 task status    = Active / not Complete
```

これは性能目標未達を意味しない。
