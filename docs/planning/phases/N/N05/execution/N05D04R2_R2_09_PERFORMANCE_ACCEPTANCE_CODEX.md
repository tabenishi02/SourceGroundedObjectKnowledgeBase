# N05D-04R2 / R2-09 — Performance/resource acceptance — Codex Handoff

Updated: 2026-10-24

- Task: `R2-09 [P0] — Performance/resource acceptance and formal N-05 rerun`
- Canonical branch: `main`
- R2-08: `Complete / PASS`
- Formal N-05: `BLOCKED / Not Complete` until this task returns a judgeable verdict
- Formal performance contract: `benchmark/n05-performance-contract-v1.json`
- Runner: `benchmark/tools/n05_run_performance.py`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Resource preflight: `benchmark/tools/n05_resource_preflight.py`

## 1. Goal

Evaluate the accepted R2 system on the Reference Workstation under the frozen N-05 performance contract.

This task has two mandatory stages:

1. post-redesign Large diagnostic comparison;
2. a completely new 46-sample formal N-05 run.

Do not reuse or resume historical run IDs.

Historical evidence remains read-only:

```text
20261022T130413+0900  historical formal BLOCKED
20261023T025413+0900  environment BLOCKED / user-aborted
20261023T035147+0900  R1 user-aborted diagnostic
```

## 2. Fixed runtime / no tuning

Keep the accepted causal baseline unchanged:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
overflow: reject / no truncation
CUDA GPU runtime required
CPU fallback prohibited
```

Do not introduce:

- Harrier 270M;
- model/revision changes;
- PyTorch/CUDA changes;
- FlashAttention-2;
- CPU fallback;
- truncation;
- arbitrary token chunking;
- score or retrieval tuning;
- pre-scoring shortlist changes.

Candidate E Overall Similarity and R2-05 Semantic remediation are frozen for this measurement.

## 3. Synchronize local main safely

Local filesystem/terminal work is owned by Codex.

Before changing anything:

1. inspect `git status`, branch and local diff;
2. preserve the three historical R1 user-aborted assets byte-for-byte;
3. do not use `git reset --hard` on a workspace that contains those local assets;
4. use an isolated clean worktree if necessary;
5. fetch GitHub and synchronize to latest `origin/main`;
6. require:

```text
branch = main
git status --porcelain = empty
HEAD == origin/main
```

The formal runner independently checks this condition.

## 4. Mandatory preflight before any diagnostic/full run

### 4.1 Resource preflight

Run outside the timed samples:

```powershell
python benchmark/tools/n05_resource_preflight.py `
  --qdrant-root C:\Qdrant\SGOKB `
  --output .local\n05\r2-09-resource-preflight.json
```

Hard gate:

```text
free disk >= 32 GiB
```

for every volume hosting repository/formal evidence or Qdrant.

If this returns nonzero or reports less than 32 GiB free, stop as `BLOCKED_RESOURCE_PREFLIGHT`. Do not start any formal sample.

Record Windows physical/virtual/page-file state from the generated result.

### 4.2 Qdrant runtime

Verify read-only/runtime state before measurement:

```text
runtime root = C:\Qdrant\SGOKB
HTTP = localhost:6333
gRPC = localhost:6334
```

Record Qdrant version and confirm the service is healthy.

Do not point the benchmark at a different Qdrant root to obtain a favorable result.

### 4.3 GPU / competing workload

Record:

```powershell
nvidia-smi
```

Confirm RTX 4090 is available and that no material competing CUDA workload is present.

A material competing workload is a blocker. Do not kill unrelated processes automatically; report the blocker.

### 4.4 Required regression/static preflight

Run:

```powershell
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS before formal timing.

The previously documented `benchmark/tools/n05_resource_preflight.py:69 E501` was a preflight blocker and has been removed on main without changing benchmark semantics. Do not weaken `ruff check .`.

Recompute and record SHA-256 of the three preserved R1 assets before measurement.

## 5. Stage A — required Large v1 vs R2 diagnostic comparison

This diagnostic must finish before the formal 46-sample run begins.

Purpose: verify that the structural redesign actually leaves the old giant-object resource regime before spending the full formal run budget.

### 5.1 Historical v1 baseline

Use the already-accepted N05D-02 historical values as the v1 comparison baseline; do not rerun the 18,847-token v1 full representation unless a missing field absolutely requires it.

Known v1 facts:

```text
object_overall tokens: 18,847
Torch peak allocated: ~51.061 GiB
Torch peak reserved:  ~56.787 GiB
Windows dedicated:    ~23.2 GiB
Windows shared:       ~34.2 GiB
Object embedding wall-clock: ~628–643 s
```

Do not rewrite these historical observations.

### 5.2 R2 Large diagnostic

Use the frozen Large load shape:

```text
Source                   40
Evidence candidates      2000
Package Evidence         350
Knowledge Statements     1200
```

Create an isolated diagnostic under `.local/n05/`; do not mutate production/reference canonical data.

Measure at minimum:

```text
object_overview exact token count
derived_incremental_sync wall-clock
end-to-end included-segment wall-clock
Torch peak allocated
Torch peak reserved
Windows dedicated GPU memory peak
Windows shared GPU memory peak
```

Also record:

- Harrier model/revision/dtype/dimension;
- imported Statement count = 1200;
- active derived representation family = object_overview / facet / statement;
- `object_overall` active leakage = 0;
- no truncation;
- no CPU fallback.

For token count, use the existing exact diagnostic where applicable:

```text
benchmark/tools/n05d04r2_object_overview_diagnostic.py
```

If the existing benchmark runner does not directly expose Torch or WDDM dedicated/shared peaks, collect those read-only around the diagnostic with temporary `.local` instrumentation only. Do not modify production scoring/search code. Reuse the established Windows GPU Process Memory performance counters if available; otherwise document the exact counter/source used.

### 5.3 Diagnostic decision

This stage is diagnostic, not the formal PASS/FAIL evaluator.

Proceed to the 46 samples only if:

- R2 Large diagnostic completes successfully;
- object_overview remains compact and untruncated;
- no catastrophic resource regime comparable to old v1 appears;
- no disk/Qdrant/CUDA blocker appears;
- no canonical state mutation occurs.

If R2 enters Shared-GPU/page-file pressure or resource behavior that makes the formal run operationally unsafe, stop as `BLOCKED_R2_RESOURCE_DIAGNOSTIC` and report exact evidence. Do not tune the model/runtime in this task.

## 6. Stage B — new formal 46-sample N-05 run

Generate a completely new unique run ID using local Asia/Tokyo time in the established format, for example:

```text
YYYYMMDDTHHMMSS+0900
```

The run root must be:

```text
.local\n05\<new_run_id>
```

It must not already exist.

Start the frozen runner exactly from Standard cold-01:

```powershell
python benchmark/tools/n05_run_performance.py `
  --run-root .local\n05\<new_run_id>
```

Do not manually skip/reorder/replace samples.

The required sequence remains:

```text
Standard cold  3
Standard warm 20
Large cold     3
Large warm    20
```

Warm workers intentionally produce the 20 warm samples in one preloaded model process per profile.

Formal gates:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
formal warm failure / abort = 0
p95 = nearest-rank
```

No failed/aborted sample replacement.

If a worker exits nonzero, preserve the partial evidence and let the deterministic evaluator classify it. Do not create replacement samples.

## 7. Required evidence review

After the runner finishes, inspect at minimum:

```text
.local/n05/<run_id>/status.json
.local/n05/<run_id>/environment.json
.local/n05/<run_id>/performance-evidence.json
.local/n05/<run_id>/performance-evaluation.json
.local/n05/<run_id>/canonical-before.json
.local/n05/<run_id>/canonical-after.json
.local/n05/<run_id>/safety.json
.local/n05/<run_id>/preflight.json
.local/n05/<run_id>/post-run.json
```

Review all sample directories and worker/evaluator logs for hidden failures.

Validate exact workload counts:

```text
Standard: 10 / 500 / 120 / 300
Large:    40 / 2000 / 350 / 1200
```

Validate sample counts exactly:

```text
Standard cold  = 3
Standard warm  = 20
Large cold     = 3
Large warm     = 20
```

## 8. Deterministic verdict

`benchmark/tools/n05_evaluate_performance.py` is authoritative for formal profile PASS/FAIL/BLOCKED classification.

Expected result semantics:

```text
PASS:
  both warm p95 values within target
  and no warm failure
  and all required evidence valid

FAIL:
  valid warm p95 exceeds target
  or any formal warm sample fails/aborts

BLOCKED:
  evidence/runtime/workload/sample count insufficient
  or preflight/environment prevents a valid run
```

Do not reinterpret a deterministic FAIL as BLOCKED merely because the result is undesirable.

Do not reinterpret an environment/evidence BLOCKED as performance FAIL.

## 9. Post-run safety gates

Require:

```text
canonical-before == canonical-after
tracked repository state unchanged during benchmark
HEAD unchanged during benchmark
full post-run regression PASS
Ruff PASS
git diff --check PASS
R1 three asset SHA-256 unchanged
```

Do not clean/delete historical evidence or Qdrant artifacts until the review is complete.

## 10. Result documentation

After the run, update the formal repository records with the actual new run ID and exact observations:

```text
docs/evaluation/N05_PERFORMANCE.md
docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md
```

Also create an R2-09 execution/evaluation record containing:

- preflight result;
- v1/R2 Large diagnostic comparison;
- run ID / git HEAD;
- environment;
- all 46 sample completion counts;
- Standard/Large nearest-rank warm p95;
- segment p95 values;
- failures/retries;
- evaluator verdict;
- safety/invariance result;
- R1 SHA comparison;
- exact final task state.

If documentation changes are made after the benchmark, commit/push them only after preserving the benchmark's original measured HEAD in the result record.

## 11. State transition

### Formal PASS

Set:

```text
R2-09 = Complete / PASS
R2-10 = Next / Not Started
N05D-04R2 = Active until R2-10 closure
N05D-04 = Not Complete until R2-10 closure
N-05 = Not Complete until R2-10 closure
```

Do not perform R2-10 closure unless explicitly requested.

### Judgeable FAIL

Set:

```text
R2-09 = Complete / FAIL
R2-10 = Not Started
N05D-04R2 implementation/quality = Complete
N-05 = FAIL / Not Complete
```

Create a new explicit optimization/design task. Do not silently continue R2 or change model/runtime.

### BLOCKED

Set:

```text
R2-09 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
```

Record the newly isolated blocker and stop.

## 12. Final report to return

Return:

1. synchronized main HEAD used for measurement;
2. preflight result including free disk / Windows memory / Qdrant / GPU;
3. three R1 SHA-256 before/after;
4. v1 vs R2 Large diagnostic table;
5. new formal run ID;
6. exact sample counts and any failure/abort;
7. Standard warm nearest-rank p95 and target;
8. Large warm nearest-rank p95 and target;
9. per-segment warm p95 for both profiles;
10. retries;
11. evaluator overall/profile verdicts;
12. canonical before/after invariance;
13. post-run regression/Ruff/diff status;
14. paths to all result artifacts;
15. documentation commit/push status;
16. final R2-09 / R2-10 / N05D-04R2 / N-05 state.
