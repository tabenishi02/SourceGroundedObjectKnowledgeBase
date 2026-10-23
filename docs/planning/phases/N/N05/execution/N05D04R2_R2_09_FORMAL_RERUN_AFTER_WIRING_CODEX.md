# N05D-04R2 / R2-09 — Formal rerun after runner-wiring remediation

Updated: 2026-10-24

- Task: `R2-09 [P0] — Performance/resource acceptance and formal N-05 rerun`
- Canonical branch: `main`
- Runner-wiring remediation runtime/source commit: `30f6bba79d2447d0708fa21f3313239d971bc4d6`
- R2-09R1 runner wiring remediation: **Accepted / integrated into main**
- R2-08: **Complete / PASS**
- R2-09: **Active / formal 46-sample rerun authorized after fresh preflight**
- R2-10: **Not Started**
- N-05: **BLOCKED / Not Complete until R2-09 returns a judgeable verdict**

## 1. Purpose

Resume R2-09 after the fresh-sample v1 fallback blocker was fixed and runtime-verified.

Do not repeat the already accepted Large diagnostic unless the current preflight or runtime identity differs materially from the accepted diagnostic environment.

The accepted diagnostic was executed on the exact runtime/source implementation now integrated into main:

```text
run_id: 20261024T040021+0900
runtime/source commit: 30f6bba79d2447d0708fa21f3313239d971bc4d6
profile: Large = 40 / 2000 / 350 / 1200
active contract: n05d04r2-hierarchical-v2
object_overview: 103 exact tokens
active object_overall leakage: 0
active memberships / Vector binding points: 1204 / 1204
derived_incremental_sync: 49.1221762 s
included total: 54.8322218 s
Torch peak allocated / reserved: 6.889365 / 7.072266 GiB
Windows Dedicated / Shared GPU peak: 7.525581 / 0.074219 GiB
canonical before/after: identical
R1 assets: identical
```

Historical v1 comparison remains:

```text
object_overall: 18,847 tokens
Torch peak allocated / reserved: ~51.061 / ~56.787 GiB
Windows Dedicated / Shared peak: ~23.2 / ~34.2 GiB
Object embedding: ~628–643 s
```

The accepted diagnostic is evidence that Stage A of the original R2-09 handoff is complete for this runtime/source implementation. It is not a substitute for the formal 46-sample evidence.

## 2. Synchronize and verify latest main

Local filesystem/terminal work is owned by Codex.

Use an isolated clean clone/worktree and fetch latest GitHub `main`.

Require before measurement:

```text
branch = main
HEAD == origin/main
git status --porcelain = empty
```

Record the exact measured HEAD. Documentation-only commits after `30f6bba...` are allowed; if any runtime/source/benchmark Python changed after `30f6bba...`, stop and review whether the accepted Large diagnostic must be repeated.

Preserve the three historical R1 assets byte-for-byte and record SHA-256 before the run.

## 3. Fresh mandatory preflight

Run immediately before the formal benchmark:

```powershell
python benchmark/tools/n05_resource_preflight.py `
  --qdrant-root C:\Qdrant\SGOKB `
  --output .local\n05\r2-09-resource-preflight-final.json

python -m pytest -q
python -m ruff check .
git diff --check
```

Also record:

```text
Qdrant root = C:\Qdrant\SGOKB
HTTP/gRPC = localhost:6333/6334
Qdrant version
nvidia-smi
Windows physical / virtual / page-file state
free disk
```

Hard start gates:

```text
free disk >= 32 GiB
Qdrant healthy
RTX 4090 CUDA runtime available
no material competing CUDA workload
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
clean main == origin/main
```

Do not stop unrelated GPU processes automatically. A material competing workload is BLOCKED.

If the fresh preflight shows a materially different model/runtime/package/Embedding Space identity from the accepted diagnostic, stop for review instead of silently measuring a changed system.

## 4. Fixed runtime / no tuning

Keep:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
overflow: reject / no truncation
batch policy: existing frozen N-05 policy
CUDA required
CPU fallback prohibited
```

Do not change:

- Harrier model/revision;
- PyTorch/CUDA;
- attention backend;
- workload sizes;
- cold/warm policy;
- timing boundary;
- Candidate E scoring;
- R2-05 Hybrid/Semantic behavior;
- ANN parameters;
- sample order/count;
- failed-sample policy.

## 5. Start a completely new formal run

Generate a new unique Asia/Tokyo run ID:

```text
YYYYMMDDTHHMMSS+0900
```

The run root must not already exist:

```text
.local\n05\<new_run_id>
```

Execute the frozen runner exactly once:

```powershell
python benchmark/tools/n05_run_performance.py `
  --run-root .local\n05\<new_run_id>
```

Required sequence and counts:

```text
Standard cold  3
Standard warm 20
Large cold     3
Large warm    20
```

Do not resume prior attempts, skip/reorder samples, or replace failed/aborted samples.

## 6. Runtime identity checks during formal samples

The runner-wiring remediation must remain active in every sample.

Audit evidence so that each sample uses:

```text
active contract = n05d04r2-hierarchical-v2
representation family = object_overview / facet / statement
active object_overall leakage = 0
sample-specific generation namespace
provider.space == bootstrap frozen_harrier_space
```

Cold provider/model construction must remain inside timed `derived_incremental_sync`.

Warm workers retain the existing preloaded-provider policy.

`build_r2_candidate()` or any full Vector rebuild must not be inserted into the timed path.

If any sample falls back to v1, treat the run as invalid/BLOCKED and preserve evidence. Do not patch or continue with altered samples.

## 7. Formal gates

The deterministic evaluator is authoritative.

```text
Standard warm nearest-rank p95 <= 600 s
Large warm nearest-rank p95    <= 1200 s
formal warm failure / abort    = 0
```

No failed/aborted warm sample replacement.

PASS / FAIL / BLOCKED meanings remain exactly those in `benchmark/n05-performance-contract-v1.json` and `benchmark/tools/n05_evaluate_performance.py`.

## 8. Required evidence review

After runner completion inspect at minimum:

```text
status.json
environment.json
performance-evidence.json
performance-evaluation.json
canonical-before.json
canonical-after.json
safety.json
preflight.json
post-run.json
all sample.json files
all worker/evaluator logs
```

Verify exact workload counts:

```text
Standard = 10 / 500 / 120 / 300
Large    = 40 / 2000 / 350 / 1200
```

Verify sample counts exactly 3/20/3/20.

Record Standard/Large:

- min / p50 / nearest-rank p95 / max;
- all eight segment p95 values;
- failures / aborts;
- retry counts.

## 9. Post-run safety

Require and record:

```text
canonical-before == canonical-after
tracked repository state unchanged during benchmark
HEAD unchanged during benchmark
post-run full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
three R1 SHA-256 before/after identical
```

Preserve raw evidence and benchmark Qdrant namespaces until review is complete.

## 10. Documentation after measurement

Create/update the formal R2-09 result record and the authoritative N-05 documents with the exact measured run ID, measured HEAD, evaluator result and safety evidence.

At minimum review/update:

```text
docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md
docs/evaluation/N05_PERFORMANCE.md
docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md
```

Commit/push documentation only after preserving the original measured HEAD in the result record.

## 11. State transition

If evaluator = PASS and safety gates PASS:

```text
R2-09 = Complete / PASS
R2-10 = Next / Not Started
N05D-04R2 = Active until R2-10 closure
N05D-04 = Not Complete until R2-10
N-05 = Not Complete until R2-10
```

If evaluator = judgeable FAIL:

```text
R2-09 = Complete / FAIL
R2-10 = Not Started
N-05 = FAIL / Not Complete
```

Do not tune or silently continue R2.

If environment/evidence/runtime identity is insufficient:

```text
R2-09 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
```

Record the blocker and stop.

Do not execute R2-10 in this task.

## 12. Final report

Return:

1. measured main HEAD;
2. fresh preflight result;
3. free disk / Windows memory / Qdrant / GPU;
4. R1 SHA before/after;
5. accepted Large diagnostic reference and whether rerun was necessary;
6. new formal run ID;
7. exact Standard/Large cold/warm sample counts;
8. failure/abort/retry counts;
9. Standard warm p50/p95/max vs 600 s;
10. Large warm p50/p95/max vs 1200 s;
11. per-segment warm p95 for both profiles;
12. evaluator profile/overall verdict;
13. R2 representation/generation identity audit;
14. canonical/safety/post-run regression result;
15. artifact paths;
16. documentation commit/push;
17. final R2-09 / R2-10 / N05D-04R2 / N-05 state.
