# N-05 — Performance Evaluation

更新日: 2026-10-23

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **BLOCKED / Not Complete — N05D-04R2 hierarchical redesign active**
- Historical formal run: `20261022T130413+0900`
- Historical formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- First D04 rerun: `20261023T025413+0900` — environment BLOCKED / user-aborted
- R1 backend diagnostic: `20261023T035147+0900` — partial / user-aborted
- Current redesign: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- Current tasks: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`
- Current performance target: **Not Judgeable until redesigned system reaches R2-09 formal rerun**

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

The hierarchical redesign does not lower these formal gates or workload counts.

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
benchmark/tools/n05_resource_preflight.py
tests/test_n05_performance_evaluator.py
tests/test_n05_performance_workflow.py
tests/test_n05_resource_preflight.py
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md
```

formal runnerはproduction canonical dataを使用せず、isolated SQLite fixtureとsample固有Qdrant namespaceを使用する。

## 6. Historical formal execution — 20261022T130413+0900

### Standard

Planned 3 cold + 20 warm. All 23 samples ended in terminal failure at Derived Search Qdrant payload-index preparation under the old workspace-resident storage environment.

N05D-01 later classified this as `QDRANT_ENVIRONMENT_DEFECT` and cut the active runtime over to:

```text
C:\Qdrant\SGOKB
```

### Large

`cold-01` exposed the old-contract giant Object representation:

```text
object_overall tokens: 18,847
batch size: 1
Dedicated VRAM: ~23.2 GiB
Shared GPU memory: ~34.2 GiB
```

The run did not reach a complete Large sample set.

### Evaluator result

```text
N-05 formal verdict = BLOCKED
performance target = Not Judgeable
```

No missing sample/timing was imputed and no failed sample was replaced.

## 7. N05D-01 — Qdrant remediation

Status: **Complete**.

Classification: `QDRANT_ENVIRONMENT_DEFECT`.

Accepted runtime:

```text
runtime root: C:\Qdrant\SGOKB
config:       C:\Qdrant\SGOKB\qdrant.yaml
Qdrant:       native 1.19.2
HTTP/gRPC:    6333 / 6334
```

External-storage cutover, Vector rebuild, real semantic/filtered query, integrity, canonical invariance, and regression passed.

## 8. N05D-02 — Long-input Harrier diagnosis

Status: **Complete / VIABLE_FOR_FORMAL_RERUN under the old representation contract**.

Exact 18,847-token input, fresh process 3/3 PASS:

```text
full times: 642.830 / 636.118 / 628.092 s
Torch peak allocated: 51.061 GiB
Torch peak reserved:  56.787 GiB
Windows peak shared:  ~34.2 GiB
```

No OOM, process kill, detected driver reset, CPU fallback, truncation, chunking, or model change.

This proved memory completion only. It did not prove that the giant representation was an appropriate long-term Derived Search design or that formal performance would pass.

## 9. N05D-03 — historical remediation checkpoint

N05D-03 originally concluded **Complete / READY_FOR_N05D04** because the Qdrant environment was repaired and the long Harrier input could complete.

That checkpoint is retained as historical evidence. Later D04/R1 evidence and design review superseded its current planning conclusion; the historical evaluation document is not rewritten as if it had known the later evidence.

## 10. First N05D-04 rerun — 20261023T025413+0900

Execution HEAD:

`280a2af9fc9c5338137f46b366bd4e18b0b9416a`

Observed:

```text
Standard cold: 3/3 PASS
Standard warm: 18 PASS / 2 FAIL
```

The two warm failures were caused by Qdrant disk exhaustion:

```text
No space left on device
WAL buffer size exceeds available disk space
```

Large had not completed its required formal sample set when the user stopped the run.

Classification:

```text
environment BLOCKED / user-aborted
not a judgeable performance FAIL
```

The preserved run must never be resumed or converted into a formal PASS/FAIL dataset.

## 11. Resource preflight added

Future formal N-05 execution requires at least:

```text
minimum free disk = 32 GiB
```

on each volume hosting formal evidence or the active Qdrant runtime. Current topology places both on `C:`.

This is an SGOKB Reference Workstation safety gate, not a general Qdrant product minimum.

## 12. N05D-04R1 backend diagnostic — partial

Run:

`20261023T035147+0900`

Status: **partial / user-aborted**.

Confirmed before abort:

```text
auto SDPA smoke: PASS; profiler observed math backend
forced FLASH_ATTENTION: FAIL; required Flash kernel unavailable in tested Windows build
forced EFFICIENT_ATTENTION: FAIL; tested Q=16 / KV=8 GQA shape rejected
full auto trial: ABORTED_by_user
```

After process termination, GPU memory returned near idle. Therefore no persistent cross-process VRAM leak was established.

R1 is retained as diagnostic evidence but is not the selected root remediation.

## 13. Adopted root remediation — N05D-04R2

Design review established that current `object_overall` duplicates detailed Knowledge already materialized separately as `facet` and `statement` representations.

Selected structure:

```text
Object
├─ object_overview   # compact Object-level context
├─ facet             # detailed Facet representation
└─ statement         # detailed Statement representation
       ↓
 bounded multi-representation candidate generation
       ↓
 Object aggregation / hierarchical similarity
       ↓
 1 Object = 1 result
```

This is semantic hierarchical partitioning based on canonical Object/Facet/Statement boundaries, not arbitrary token chunking.

The redesign introduces `object_overview` rather than silently changing persisted `object_overall` semantics. Historical v1 artifacts remain distinguishable during migration and comparison.

For the first causal acceptance, Harrier OSS v1 0.6B remains fixed. Harrier 270M and runtime/backend changes are later contingencies only if the structural redesign still fails explicit requirements.

## 14. R2 task chain

```text
R2-01 Impact survey / redesign freeze
R2-02 Requirements + representation contract revision
R2-03 Persistence/versioning/migration design
R2-04 compact object_overview implementation
R2-05 Hybrid Search migration
R2-06 Hierarchical Object Similarity redesign
R2-07 Derived Search rebuild/cutover/rollback
R2-08 Search-quality acceptance
R2-09 Performance/resource acceptance + formal N-05 rerun
R2-10 Closure / Phase N state update
```

Formal timing is prohibited before R2-08 passes.

## 15. Future R2-09 formal execution

When authorized, use a new run ID and start again from Standard cold-01:

```text
Standard cold 3 + warm 20
Large cold    3 + warm 20
```

The gates remain:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
terminal failure / abort = 0
```

Diagnostic timings from old-contract D02 or R1 are never mixed into the new formal evidence.

Before R2-09 require:

```text
R2-08 quality acceptance PASS
main == origin/main
working tree clean
free disk >= 32 GiB
Qdrant root = C:\Qdrant\SGOKB
no material competing CUDA workload
host memory/commit recorded
full regression / Ruff / diff PASS
```

## 16. Current conclusion

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Next / Not Started
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

Next: **R2-01 — Impact survey / redesign freeze**.


## R2-09 execution update (2026-10-24)

This execution result supersedes earlier R2-09 next-task notes:
**R2-09 = BLOCKED / Not Complete; N-05 = BLOCKED / Not Complete;
N05D-04R2 = Active; R2-10 = Not Started.** R2-08 quality acceptance is unchanged.

Mandatory preflight PASS (654 pytest passed; repository-wide Ruff/diff PASS;
124.740 GiB free; external Qdrant healthy; no material competing CUDA workload).
Before GPU timing, source inspection established that the frozen performance
workflow uses default v1 `materialize_version` for fresh samples, producing
`object_overall` instead of the required R2 family. No Large diagnostic or formal
sample was started. Runner/model/scoring/gates were not changed. R1 assets remain
byte-identical. A separately reviewed R2 benchmark-wiring change is required
before a new acceptance attempt; no closure or optimization is started here.

Execution record: `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`.
