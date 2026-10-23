# N05D-04 — Formal N-05 benchmark rerun handoff

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Status: **BLOCKED / Not Complete — hierarchical Derived Search redesign required before rerun**
- Historical authorization basis: `docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`
- Resource/VRAM research: `docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md`
- Adopted redesign: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- Redesign tasks: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`
- Frozen performance contract: `benchmark/n05-performance-contract-v1.json`
- Runner: `benchmark/tools/n05_run_performance.py`
- Evaluator: `benchmark/tools/n05_evaluate_performance.py`
- Old formal run: `20261022T130413+0900` — preserved BLOCKED evidence
- Aborted rerun: `20261023T025413+0900` — preserved environment-blocked evidence

## 1. Current decision

Do **not** start another formal 46-sample N-05 run yet.

After the aborted rerun and VRAM investigation, the user selected a structural Derived Search remediation:

```text
retire giant active object_overall usage
introduce compact object_overview
keep/use Facet representations
keep/use Statement representations
aggregate child matches to Object results
redesign overall Object Similarity as bounded hierarchical multi-vector similarity
```

The redesign is N05D-04R2. Formal N05D-04 execution is re-authorized only after R2-01 through R2-08 complete and Search-quality acceptance passes.

## 2. Why another immediate rerun is prohibited

N05D-02 established that the exact 18,847-token `object_overall` is technically memory-completable but enters a severe resource regime:

```text
~51.1 GiB Torch peak allocated
~34.2 GiB Windows Shared GPU memory
~628–643 s for the Object-level embedding alone
```

The first D04 rerun also encountered disk exhaustion and was stopped before a judgeable Large sample set existed.

R1 backend probing subsequently established partial evidence that native Windows auto-SDPA selected the math backend for the tested workload; forced Flash was unavailable in the current build and forced Efficient Attention rejected the tested GQA shape. R1 itself was user-aborted and is not an accepted runtime remediation.

Because current `object_overall` duplicates detailed Knowledge already represented as Facet and Statement vectors, continuing to optimize the giant single-vector path is no longer the selected primary solution.

## 3. Historical aborted attempt 20261023T025413+0900

Execution HEAD:

`280a2af9fc9c5338137f46b366bd4e18b0b9416a`

Observed before abort:

```text
Standard cold: 3/3 PASS
Standard warm: 18 PASS / 2 FAIL
```

The two warm failures were caused by Qdrant disk exhaustion (`No space left on device` / WAL buffer cannot fit), not by a valid performance-gate exceedance. Large had not completed its required sample set when the user stopped the run.

Therefore:

```text
attempt 20261023T025413+0900 = environment BLOCKED / user-aborted evidence
N05D-04 = Not Complete
N-05 = BLOCKED / Not Complete
```

Never resume or patch this run. Preserve its evidence.

## 4. Redesign prerequisites before formal rerun

Complete the task chain in:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

Required before formal timing:

```text
R2-01 impact survey / redesign freeze
R2-02 requirements + design contract revision
R2-03 persistence/versioning/migration design
R2-04 object_overview implementation
R2-05 Hybrid Search migration
R2-06 hierarchical Object Similarity implementation
R2-07 Derived Search rebuild/cutover/rollback validation
R2-08 Search-quality acceptance
```

Only R2-09 may authorize a new formal N-05 run.

## 5. Model policy during redesign

Keep Harrier 0.6B fixed for the first causal comparison:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
```

Do not combine the representation redesign with Harrier 270M adoption, PyTorch upgrade, FlashAttention-2 installation, CPU fallback, truncation, or arbitrary token chunking.

A later model-change task may be opened only if the hierarchical redesign still fails resource/performance or other explicit requirements.

## 6. Resource preflight retained

The accepted hard disk start gate remains:

```text
minimum free disk = 32 GiB
```

for every volume hosting formal evidence or active Qdrant runtime. Current topology places both on `C:`.

Before the future R2-09 run also confirm:

```text
main == origin/main
working tree clean
new unique run_id
Qdrant ready on localhost:6333/6334
active Qdrant runtime root = C:\Qdrant\SGOKB
CUDA available
no unexpected substantial competing CUDA workload
host available/committed memory recorded
Search-quality acceptance PASS
full regression / Ruff / diff PASS
```

## 7. Future formal workload and gates

The structural redesign does not lower the workload or performance requirements.

Future formal run still starts from the beginning:

```text
Standard cold  3
Standard warm 20
Large cold     3
Large warm    20
```

Workload remains:

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

Formal gates remain:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
terminal failure / abort = 0
nearest-rank p95
```

No failed/aborted sample replacement.

## 8. Timed boundary remains unchanged

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

The new representation architecture is part of normal `derived_incremental_sync`; diagnostic redesign timing is not substituted for formal evidence.

## 9. Formal result recording after R2-09

Update at minimum:

```text
docs/evaluation/N05_PERFORMANCE.md
docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
this handoff
```

Record representation/builder identity so pre-redesign and post-redesign results cannot be confused.

## 10. Current state

```text
N05D-01 = Complete
N05D-02 = Complete / VIABLE_FOR_FORMAL_RERUN under old representation
N05D-03 = Complete historical closure decision
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = user-aborted diagnostic evidence; not selected remediation
N05D-04R2 = Active / redesign planning
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
