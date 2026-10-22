# N05D-04 — Formal N-05 benchmark rerun handoff

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Status: **Ready / Not Started**
- Authorization basis: `docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`
- Frozen contract: `benchmark/n05-performance-contract-v1.json`
- Runner: `benchmark/tools/n05_run_performance.py`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Old formal run: `20261022T130413+0900` — preserved BLOCKED evidence

## 1. Goal

Execute a completely new formal N-05 run under the unchanged contract and obtain a judgeable PASS/FAIL result for:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

Diagnostic timings from N05D-01/N05D-02 are not formal samples.

## 2. Start prerequisites

Before starting any formal sample, verify and record:

```text
main == origin/main
working tree clean
new unique run_id
Qdrant ready on localhost:6333/6334
active Qdrant runtime root = C:\Qdrant\SGOKB
active config = C:\Qdrant\SGOKB\qdrant.yaml
Harrier model/revision unchanged
CUDA available; no CPU fallback
no unexpected substantial competing CUDA workload
host available/committed memory snapshot
```

The preserved old Qdrant workspace storage and all previous N-05/N05D evidence must not be deleted or overwritten.

If the remediated Qdrant runtime is not active, the model/profile differs, or another substantial CUDA workload materially confounds the Reference Workstation, stop before formal samples and classify the attempt BLOCKED. Do not kill unrelated user processes automatically.

## 3. Frozen embedding profile

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
device: cuda
batch_size: 1
max_sequence_length: 32768
overflow_policy: reject
normalize_embeddings: true
dimension: 1024
```

Do not introduce truncation, CPU fallback, model changes, sequence-limit reduction, or representation chunking.

## 4. Mandatory preflight

Run the existing formal preflight exactly as required by the runner/plan. At minimum:

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Do not proceed if preflight fails.

## 5. Formal sample sequence

Start from the beginning with the new run ID:

```text
Standard cold  3
Standard warm 20
Large cold     3
Large warm    20
```

Warm samples use the runner's frozen persistent preloaded-provider policy.

Never remove or replace a failed/aborted formal sample. Automatic retry time, if any, remains part of the sample total.

## 6. Formal workload

### Standard

```text
Source                 10
Evidence candidates    500
Package Evidence       120
Knowledge Statements   300
```

### Large

```text
Source                 40
Evidence candidates    2000
Package Evidence       350
Knowledge Statements   1200
```

No workload reduction is authorized by N05D-03.

## 7. Timed segments

The existing eight-segment boundary remains unchanged:

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

External AI generation/return wait remains excluded according to the frozen contract.

## 8. Known risk carried into the run

N05D-02 established memory viability but also showed that the exact 18,847-token Large Object embedding takes approximately 628–643 seconds in fresh processes and enters heavy WDDM shared-memory spill.

This is not a reason to alter the benchmark. The formal run must determine whether the complete Large workflow remains within 1,200 seconds and whether the persistent warm process remains stable across all required samples.

If a formal sample terminally fails under the frozen valid environment, retain that failure as formal evidence.

## 9. Evaluation

After measurement, run the deterministic evaluator against the new evidence only:

```powershell
python benchmark/tools/n05_evaluate_performance.py `
  --evidence .local/n05/<new_run_id>/performance-evidence.json `
  --output .local/n05/<new_run_id>/performance-evaluation.json
```

Do not merge historical or diagnostic samples into the new evidence set.

## 10. Post-run validation

Run:

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Confirm canonical fingerprints and tracked-file invariance according to the existing runner contract.

## 11. Result recording

Update at minimum:

```text
docs/evaluation/N05_PERFORMANCE.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
```

Record new run ID, execution HEAD, Standard/Large cold/warm counts, p50/p95/max where judgeable, segment statistics, terminal failures, regression results, and final N-05 verdict.

## 12. Current state

```text
N05D-01 = Complete
N05D-02 = Complete
N05D-03 = Complete / READY_FOR_N05D04
N05D-04 = Ready / Not Started
N-05     = BLOCKED / Not Complete
```
