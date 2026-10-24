# N-05 — Performance Benchmark

## R2-10 closure update (2026-10-24)

This is the current authoritative state for this document and supersedes older current-state / next-task notes retained below.

```text
R2-10     = Complete
N05D-04R2 = Complete
N05D-04   = Complete
N-05      = Complete / PASS
Phase N   = Active / Not Complete
Next      = N-06 Retrieval / Vector quality
```

Formal run `20261024T044506+0900` completed the frozen benchmark exactly: Standard cold/warm `3/20`, Large cold/warm `3/20`, 46 PASS, zero FAIL/ABORTED/retry. Standard warm nearest-rank p95 was `12.2832216 s <= 600 s`; Large was `53.7066947 s <= 1200 s`. All samples used the R2 generation family with active `object_overall` leakage 0. Post-run canonical/tracked/HEAD invariance and regression/static gates passed.

The benchmark contract remains frozen evidence for this acceptance. Another N-05 rerun is not part of R2-10.

Closure authority: `docs/evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md`.

---

## Historical planning/evidence record retained below

## Current acceptance update (2026-10-24)

This update supersedes historical BLOCKED/next-task notes below.
**R2-08 = Complete / PASS; R2-09 = Complete / PASS;
R2-10 = Next / Not Started.** N05D-04R2 remains Active until R2-10 closure;
N05D-04 and N-05 are Not Complete until that separate closure.

Formal run `20261024T044506+0900` measured clean main
`2711d4c389c4d1c722e864e17a7b6afb05af4c62`: exact 3/20/3/20 samples,
46 PASS, 0 FAIL/ABORTED/retry. Standard warm p50/p95/max =
11.3099469 / 12.2832216 / 12.3947986 s; Large =
49.9412004 / 53.7066947 / 54.1282194 s. Evaluator Standard/Large/overall PASS
against unchanged 600/1200 s Gates. Every sample used R2 only, overall leakage 0;
46 namespaces / 34684 live points audited. Original canonical snapshots, measured
HEAD, tracked state and all three R1 asset hashes were unchanged. Post-run evaluator
8 tests / full suite 669 tests / repository-wide Ruff / diff PASS. Accepted Large
resource diagnostic was reused without rerun; source/runtime identity unchanged.
No R2-10 closure, performance tuning or additional benchmark was started.

Formal result: `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`.
Aggregate: `benchmark/results/n05d04r2-r2-09-performance-acceptance.json`.


更新日: 2026-10-23

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-05 [P0] — Performance`
- Status: **Formal performance PASS / N-05 Not Complete until R2-10 closure**
- Contract: `benchmark/n05-performance-contract-v1.json`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Runner: `benchmark/tools/n05_run_performance.py`
- Workflow fixture: `benchmark/tools/n05_performance_workflow.py`
- Resource preflight: `benchmark/tools/n05_resource_preflight.py`
- Historical formal run: `20261022T130413+0900`
- First D04 rerun: `20261023T025413+0900` — environment BLOCKED / user-aborted
- R1 diagnostic: `20261023T035147+0900` — partial / user-aborted
- Current redesign: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- Redesign tasks: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`
- Parent requirements: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md` NFR-PERF-01〜

## 1. Purpose

SGOKBの1 Objectあたりlocal automatic processingが、Reference Workstation上で実用上の性能目標を満たすことを確認する。

正式Gate:

```text
Standard Object warm p95 <= 600 s
Large Object warm p95    <= 1200 s
```

N-05は外部AIや人間の待ち時間を測るTaskではない。SGOKB自身が実行するlocal automatic segmentだけを測定する。

## 2. Measurement boundary

Included:

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

`package_build`はEvidence Retrieval / selectionを含む。

`derived_incremental_sync`はSearch Representation / Embedding / Vector Indexの通常incremental pathを含む。

Excluded:

```text
Source探索
Web Capture network time
human Package review
external export / Drive sync
ChatGPT / external AI操作・生成待ち
Result返却transport
human review / approval wait
full Vector Index rebuild
```

## 3. Reference Environment

```text
OS   Windows 11
CPU  Intel Core i5-13600KF
RAM  128 GB
GPU  NVIDIA GeForce RTX 4090 24 GB
```

Accepted Qdrant runtime after N05D-01:

```text
runtime root: C:\Qdrant\SGOKB
config:       C:\Qdrant\SGOKB\qdrant.yaml
HTTP/gRPC:    6333 / 6334
```

Future formal execution additionally requires the resource preflight described below.

## 4. Workload profiles

### Standard

```text
Source                   10
Evidence candidates      500
Package Evidence         120
Knowledge Statements     300
Gate                      warm p95 <= 600 s
```

### Large

```text
Source                   40
Evidence candidates      2000
Package Evidence         350
Knowledge Statements     1200
Gate                      warm p95 <= 1200 s
```

The R2 redesign does not reduce these workload counts.

## 5. Fixture / isolation policy

N-03 remains a real-data ecological reference, while N-05 load shape is reproduced with isolated deterministic fixtures.

Each sample starts from the same state. SQLite/package/result/render artifacts and Qdrant collection prefixes are sample-specific. Production canonical DB is not used as benchmark workload.

The external-AI interval is replaced with a deterministic prebuilt valid Result that still traverses normal Validation / Diff / Import contracts.

## 6. Cold / Warm policy

```text
Cold diagnostic:
  >=3 samples/profile
  non-gating

Warm formal:
  >=20 samples/profile
  nearest-rank p95
  terminal failure / abort = 0
  retry time included in total
```

Failed/aborted formal samples are never deleted or replaced.

## 7. Deterministic evaluator

```powershell
python benchmark/tools/n05_evaluate_performance.py `
  --evidence .local\n05\<run_id>\performance-evidence.json `
  --output .local\n05\<run_id>\performance-evaluation.json
```

Exit meaning:

```text
0 PASS
1 FAIL
2 BLOCKED
```

## 8. Historical run chain

### Initial formal run — 20261022T130413+0900

- Standard: 23/23 terminal sample failure at old Qdrant storage/payload-index path.
- Large: `cold-01` exposed the 18,847-token Object representation and severe shared-GPU-memory regime.
- Evaluator: BLOCKED / Not Judgeable.

N05D-01 subsequently repaired Qdrant through `C:\Qdrant\SGOKB` external-storage cutover.

### N05D-02 long-input diagnosis

Old-contract exact 18,847-token input completed fresh-process 3/3:

```text
628.092–642.830 s
Torch peak allocated ~51.1 GiB
Torch peak reserved ~56.8 GiB
Windows Shared GPU memory ~34.2 GiB
```

This is diagnostic memory viability, not formal performance evidence.

### First N05D-04 rerun — 20261023T025413+0900

Observed:

```text
Standard cold: 3/3 PASS
Standard warm: 18 PASS / 2 FAIL
```

The two failures were caused by Qdrant disk exhaustion (`No space left on device` / WAL buffer cannot fit). Large had not completed when the user stopped the run.

Classification: environment BLOCKED / user-aborted. Do not resume this run.

### N05D-04R1 — 20261023T035147+0900

Partial diagnostic evidence before user abort:

```text
auto SDPA smoke -> math backend observed
forced Flash -> unavailable in tested Windows PyTorch build
forced Efficient -> tested Q=16 / KV=8 GQA shape rejected
full auto trial -> ABORTED_by_user
```

R1 is historical diagnostic evidence, not an accepted runtime remediation.

## 9. Resource preflight

Before any future formal N-05 run:

```text
minimum free disk = 32 GiB
```

on every volume hosting formal evidence or the active Qdrant runtime. Current topology uses `C:` for both.

Run:

```powershell
python benchmark/tools/n05_resource_preflight.py `
  --qdrant-root C:\Qdrant\SGOKB
```

This gate exists because the first rerun exhausted disk and because the long-input Harrier workload also creates high Windows commit/page-file pressure.

## 10. Selected structural remediation — N05D-04R2

The current active `object_overall` duplicates detailed Facet Statements even though the same accepted Knowledge is separately represented as Facet and Statement representations.

Selected target:

```text
Object
├─ compact object_overview
├─ facet representations
└─ statement representations
       ↓
 bounded multi-representation candidate generation
       ↓
 Object aggregation / hierarchical Object Similarity
```

This is semantic partitioning along canonical Object/Facet/Statement boundaries, not arbitrary token chunking.

The redesign introduces `object_overview` as a new active kind rather than silently changing the meaning of existing persisted `object_overall` v1 artifacts.

## 11. Model policy during R2

Keep the existing embedding identity fixed for the first redesign acceptance:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
```

Do not combine R2 baseline work with Harrier 270M, PyTorch upgrade, FlashAttention-2 installation, CPU fallback, truncation, or arbitrary chunking.

This isolates the effect of the representation architecture.

## 12. R2 execution order

```text
R2-01 Impact survey / design freeze
  ↓
R2-02 Requirements + representation contract revision
  ↓
R2-03 Persistence/versioning/migration design
  ↓
R2-04 compact object_overview implementation
  ├─→ R2-05 Hybrid Search migration
  └─→ R2-06 Hierarchical Object Similarity redesign
          ↓
R2-07 Derived Search rebuild / cutover / rollback
          ↓
R2-08 Search-quality acceptance
          ↓
R2-09 Performance/resource acceptance + formal N-05 rerun
          ↓
R2-10 Closure / Phase N state update
```

Do not start formal timing before R2-08 passes.

## 13. R2-09 formal start conditions

Future formal execution requires:

1. R2-01〜R2-07 Complete.
2. R2-08 Search-quality acceptance PASS.
3. clean `main == origin/main`.
4. new unique run ID; old evidence retained.
5. free disk >=32 GiB.
6. remediated Qdrant `C:\Qdrant\SGOKB` ready on 6333/6334.
7. Harrier 0.6B R2 baseline fixed.
8. no material competing CUDA workload.
9. host available/committed memory recorded.
10. full regression / Ruff / `git diff --check` PASS.
11. Standard cold-01から全sampleを最初から実行する.
12. FAIL/ABORTED sampleを置換しない.

## 14. R2-09 diagnostic comparison before formal samples

Before the new 46-sample run, compare old v1 vs redesigned v2 Large fixture for:

```text
Object-level representation token length
Torch peak allocated/reserved
Dedicated/Shared GPU memory
derived_incremental_sync wall-clock
end-to-end sample wall-clock
```

This comparison is diagnostic only and never substitutes for the formal samples.

## 15. N-05 completion condition

N-05 Complete requires:

1. redesigned retrieval/search architecture has passed R2-08 quality acceptance;
2. a completely new formal run reaches Standard cold>=3/warm>=20 and Large cold>=3/warm>=20;
3. deterministic evaluator returns judgeable PASS/FAIL;
4. post-run canonical/tracked/HEAD invariance evidence is complete;
5. full regression / Ruff / diff check PASS;
6. human-readable evaluation records formal statistics and final verdict.

## 16. Current state

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Next / Not Started
N-05 = BLOCKED / Not Complete
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
