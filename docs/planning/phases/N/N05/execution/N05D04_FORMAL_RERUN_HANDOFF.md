# N05D-04 — Formal N-05 benchmark rerun handoff

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Status: **BLOCKED / Not Complete — resource remediation before a new run**
- Authorization basis: `docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`
- Resource/VRAM research: `docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md`
- VRAM diagnostic handoff: `docs/planning/phases/N/N05/execution/N05D04R1_HARRIER_SDPA_VRAM_DIAGNOSIS_HANDOFF.md`
- Frozen contract: `benchmark/n05-performance-contract-v1.json`
- Runner: `benchmark/tools/n05_run_performance.py`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Old formal run: `20261022T130413+0900` — preserved BLOCKED evidence
- Aborted rerun: `20261023T025413+0900` — preserved environment-blocked evidence

## 1. Goal

Execute a completely new formal N-05 run under the accepted contract and obtain a judgeable PASS/FAIL result for:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

Diagnostic timings from N05D-01/N05D-02/N05D-04R1 are not formal samples.

## 2. Aborted attempt 20261023T025413+0900

The first D04 rerun started from execution HEAD `280a2af9fc9c5338137f46b366bd4e18b0b9416a` with the remediated Qdrant runtime and an initially uncongested RTX 4090.

During the attempt:

```text
Standard cold: 3/3 PASS
Standard warm: 18 PASS / 2 FAIL
```

The warm failures were caused by Qdrant disk exhaustion (`No space left on device` / WAL buffer cannot fit), not by a measured performance-gate exceedance. During Large cold, Harrier again entered the known near-full dedicated-VRAM + large Shared GPU memory spill regime. The user stopped the run before the Large formal sample set completed.

The runner/workers were stopped, evidence retained, and no disk cleanup or sample replacement was performed by the benchmark task.

Therefore:

```text
attempt 20261023T025413+0900 = environment BLOCKED / user-aborted evidence
N05D-04 = Not Complete
N-05 = BLOCKED / Not Complete
```

Do not resume this run. A future formal attempt must use a new run ID and start again at Standard cold-01.

## 3. Resource remediation before another formal attempt

A new formal run is not authorized until the resource preflight and N05D-04R1 VRAM investigation are completed/reviewed.

### Disk hard gate

Run:

```powershell
python benchmark/tools/n05_resource_preflight.py `
  --qdrant-root C:\Qdrant\SGOKB `
  --output .local\n05d04\resource-preflight.json
```

Required:

```text
minimum free disk = 32 GiB
scope = every volume hosting repository/formal evidence or active Qdrant runtime
current topology = C: for both
```

This is an SGOKB Reference Workstation safety gate, not a general Qdrant minimum. The rationale combines Qdrant WAL/temp headroom with Windows page-file growth under the Harrier Shared-GPU-memory/commit load. See the resource research document for sources and derivation.

If free space is below 32 GiB, do not start formal samples.

### VRAM investigation

Before another many-hour formal run, execute/review:

```text
N05D-04R1 — Harrier SDPA backend / VRAM A-B diagnosis
```

Priority is to determine whether PyTorch built-in fused SDPA backends can lower the exact 18,847-token Harrier memory/latency profile without changing model/revision/tokenizer/representation/batch size.

Do not install arbitrary runtime changes or modify the production provider before the diagnostic result is reviewed.

## 4. Formal start prerequisites after resource review

Before starting any new formal sample, verify and record:

```text
main == origin/main
working tree clean
new unique run_id
resource preflight PASS (>=32 GiB free)
Qdrant ready on localhost:6333/6334
active Qdrant runtime root = C:\Qdrant\SGOKB
active config = C:\Qdrant\SGOKB\qdrant.yaml
accepted Harrier runtime/backend from the completed VRAM review
CUDA available; no CPU fallback
no unexpected substantial competing CUDA workload
host available/committed memory snapshot
```

The preserved old Qdrant workspace storage and all previous N-05/N05D evidence must not be deleted or overwritten by the runner.

If the runtime differs from the accepted reviewed state or another substantial CUDA workload materially confounds the workstation, stop before formal samples and classify the attempt BLOCKED. Do not kill unrelated user processes automatically.

## 5. Frozen semantic/model identity

Unless a separately reviewed VRAM-backend remediation is accepted, keep:

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

No truncation, CPU fallback, model/revision change, sequence-limit reduction, or representation chunking is authorized as a benchmark shortcut.

An accepted attention-kernel/backend optimization must be documented with numerical/retrieval validation before the formal run and becomes part of the new execution environment evidence.

## 6. Mandatory preflight

Run the resource preflight first, then the existing formal preflight:

```powershell
python benchmark/tools/n05_resource_preflight.py --qdrant-root C:\Qdrant\SGOKB
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Do not proceed if any mandatory preflight fails.

## 7. Formal sample sequence

Start from the beginning with a new run ID:

```text
Standard cold  3
Standard warm 20
Large cold     3
Large warm    20
```

Never remove or replace a failed/aborted formal sample. Automatic retry time, if any, remains part of the sample total.

## 8. Formal workload

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

No workload reduction is authorized.

## 9. Timed segments

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

## 10. Evaluation and post-run validation

Evaluate only the new run evidence:

```powershell
python benchmark/tools/n05_evaluate_performance.py `
  --evidence .local\n05\<new_run_id>\performance-evidence.json `
  --output .local\n05\<new_run_id>\performance-evaluation.json
```

Then run:

```powershell
python -m pytest -q tests/test_n05_performance_evaluator.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Confirm canonical fingerprints, tracked-file invariance, execution HEAD invariance, Qdrant runtime identity, and resource evidence.

## 11. Result recording

Update at minimum:

```text
docs/evaluation/N05_PERFORMANCE.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
this handoff
```

Record run ID, execution HEAD, sample counts, p50/p95/max where judgeable, segment statistics, terminal failures, resource preflight, regression results, and final N-05 verdict.

## 12. Current state

```text
N05D-01 = Complete
N05D-02 = Complete
N05D-03 = Complete / READY_FOR_N05D04
N05D-04 = BLOCKED / Not Complete after environment-aborted attempt
N05D-04R1 = Next / Ready
N-05 = BLOCKED / Not Complete
```
