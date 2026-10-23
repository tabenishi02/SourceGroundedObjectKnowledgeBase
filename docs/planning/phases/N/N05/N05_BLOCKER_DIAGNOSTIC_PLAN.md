# N-05 — Formal Benchmark Blocker Diagnostic Plan

更新日: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Current formal verdict: **BLOCKED**
- N-05 completion: **Not Complete**
- Historical formal run: `20261022T130413+0900`
- Historical formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- Performance contract: `benchmark/n05-performance-contract-v1.json`
- Evaluation: `docs/evaluation/N05_PERFORMANCE.md`
- Current redesign: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- Redesign tasks: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

## 1. Purpose

N-05 formal benchmark reached multiple independent environmental/resource blockers before a judgeable formal PASS/FAIL was obtained.

The diagnostic/remediation chain is now:

```text
N05D-01 Qdrant storage/path blocker diagnosis       Complete
N05D-02 Long-input Harrier memory diagnosis         Complete
N05D-03 Evidence-based remediation checkpoint       Complete (historical decision)
        ↓
N05D-04 first formal rerun                          Environment BLOCKED / aborted
        ↓
N05D-04R1 attention-backend diagnostic              User-aborted partial evidence
        ↓
N05D-04R2 hierarchical multi-vector redesign        Active
        ↓
R2-09 new formal N-05 rerun                         Future
```

Diagnostic values are never mixed into N-05 formal p95 samples.

## 2. Observed blockers

### Blocker A — Qdrant storage/path

The first formal Standard profile reached 23/23 terminal sample failures at Derived Search Qdrant payload-index preparation.

Final disposition: resolved through N05D-01 environment remediation and external runtime root `C:\Qdrant\SGOKB`.

### Blocker B — giant long-input Object representation

The historical Large fixture produced:

```text
object_overall tokens: 18,847
embedding batch size: 1
Dedicated VRAM: ~23.2 GiB
Shared GPU memory: ~34.2 GiB
```

N05D-02 later measured:

```text
full times: 642.830 / 636.118 / 628.092 s
Torch peak allocated: 51.061 GiB
Torch peak reserved:  56.787 GiB
Windows peak shared:  ~34.2 GiB
```

The input completes, but it enters an operationally severe resource regime.

### Blocker C — disk exhaustion in first D04 rerun

Attempt `20261023T025413+0900` produced Standard cold 3/3 PASS and Standard warm 18 PASS / 2 FAIL before Qdrant reported disk exhaustion (`No space left on device` / WAL buffer cannot fit). Large had not completed the required sample set when the user stopped the run.

This attempt is environment BLOCKED / user-aborted evidence, not a performance FAIL.

A hard start gate of >=32 GiB free disk is now retained for future formal execution.

## 3. N05D-01 — Qdrant storage/path diagnosis

### Final outcome

**Complete**.

Classification: `QDRANT_ENVIRONMENT_DEFECT`.

Workspace-resident storage was replaced by the accepted external runtime root:

```text
C:\Qdrant\SGOKB
```

All 50 diagnostic cleanup `ACCESS DENIED` events were correlated as recovered Rust Windows POSIX rename fallback events; unrecovered/ambiguous failures, delete API failures, source survivors, terminal cleanup errors, and surfaced OS error 3/5 were zero.

Vector rebuild, semantic/filtered query, integrity, canonical invariance, and regression passed after cutover.

## 4. N05D-02 — Long-input Harrier memory diagnosis

### Final outcome

**Complete / VIABLE_FOR_FORMAL_RERUN under the old representation contract**.

The exact 18,847-token representation completed 3/3 fresh-process trials without OOM, kill, detected driver reset, CPU fallback, truncation, or chunking.

However, the observed ~51 GiB active allocation and ~628–643 second Object-level embedding made the representation a major performance/resource risk.

This verdict means memory completion only. It does not mean the representation is an appropriate long-term Derived Search design.

## 5. N05D-03 — Evidence-based remediation checkpoint

### Historical outcome

N05D-03 originally concluded **Complete / READY_FOR_N05D04** because D01 was repaired and D02 proved memory completion. It intentionally made no model/representation change before a formal rerun.

That was a valid checkpoint given the evidence available at that time.

### Superseding evidence

The subsequent formal rerun and R1 investigation exposed additional operational evidence:

- disk exhaustion during a multi-hour formal attempt;
- recurrence of the severe Large shared-memory regime;
- partial R1 profiler evidence that the native Windows auto-SDPA workload selected math attention;
- forced Flash unavailable in the tested build;
- forced Efficient Attention rejected the tested GQA shape;
- process termination returned GPU memory near idle, so a persistent cross-process VRAM leak was not established.

Most importantly, design review established that current `object_overall` duplicates detailed Statements that are already independently materialized as Facet and Statement representations.

Therefore N05D-03's historical “no redesign required” decision is superseded for current planning by N05D-04R2. The historical document remains evidence and is not rewritten as if it had reached the later conclusion.

## 6. N05D-04 — Formal rerun state

N05D-04 remains **BLOCKED / Not Complete**.

Do not resume historical run IDs:

```text
20261022T130413+0900
20261023T025413+0900
```

Do not start a new 46-sample formal run until the hierarchical redesign task chain reaches R2-09 authorization.

Formal workload/gates remain unchanged unless a separate requirements decision explicitly changes them:

```text
Standard cold 3 + warm 20
Large cold    3 + warm 20

Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

## 7. N05D-04R1 — attention-backend diagnostic

Run `20261023T035147+0900` is partial/user-aborted diagnostic evidence.

Confirmed before abort:

```text
auto SDPA smoke: math backend observed
forced Flash: unsupported in current tested Windows build
forced Efficient: tested Q=16 / KV=8 GQA shape rejected
full auto trial: ABORTED_by_user
```

R1 is not the selected root remediation. Preserve evidence, but do not resume the full trial automatically.

## 8. N05D-04R2 — hierarchical multi-vector redesign

User-selected root remediation:

```text
compact object_overview
+ Facet representations
+ Statement representations
+ bounded Object aggregation
+ hierarchical Object Similarity
```

This follows canonical semantic boundaries and is not arbitrary token chunking.

The existing Phase I architecture already includes Object / Facet / Statement multi-representation retrieval and Statement → Object aggregation. R2 removes the redundant giant active `object_overall` detail duplication and redesigns the remaining overall similarity dependency.

Model policy for first acceptance:

```text
Harrier OSS v1 0.6B remains fixed
```

Harrier 270M, FlashAttention-2, PyTorch upgrade, CPU fallback, and truncation are not bundled into R2 baseline execution.

Design plan:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`

Task plan:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

## 9. Current next task

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = partial user-aborted evidence
N05D-04R2 = Active
R2-01 = Next / Not Started
N-05 = BLOCKED / Not Complete
```

Next: **R2-01 — Impact survey / redesign freeze**.

## 10. Historical investigation chronology

### N05D-01 local diagnosis

Run `20261022T161445+0900` established that an isolated short Qdrant storage path behaved materially better than the existing runtime, while path/access errors remained unresolved at that stage.

### ProcMon investigation

Run `20261022T172340+0900` found a concrete cleanup rename overlap with a `Code.exe` `ShareMode: None` open but did not prove a unique VS Code/root-cause relationship.

### N05D-01C external storage

Run `20261022T191928+0900` passed the direct/adapter stress workload but exposed 50 raw cleanup rename `ACCESS DENIED` events, which initially failed the then-overstrict raw-event Gate.

### N05D-01D final interpretation/cutover

The 50 events were proven recoverable internal primary rename attempts followed by successful fallback. The semantic Gate was corrected and `C:\Qdrant\SGOKB` became the accepted runtime.

### N05D-02 long-input diagnosis

Run `20261022T230242+0900` measured the exact Large representation and established the severe 12k→16k shared-memory regime while proving full-input completion.

Details remain in:

- `docs/evaluation/N05D01_QDRANT_STORAGE_PATH_DIAGNOSIS.md`
- `docs/evaluation/N05D02_HARRIER_MEMORY_DIAGNOSIS.md`
- `docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`
- `docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md`


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
