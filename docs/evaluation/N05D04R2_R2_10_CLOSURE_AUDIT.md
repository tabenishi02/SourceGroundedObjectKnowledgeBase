# N05D-04R2 / R2-10 — Closure Audit and Phase N State Update

Date: 2026-10-24

## 1. Decision

R2-10 is **Complete**.

The hierarchical multi-vector redesign and the N-05 formal performance acceptance are closed with the following final state:

```text
R2-01 = Complete
R2-02 = Complete / Design Freeze
R2-03 = Complete / Design Freeze
R2-04 = Complete
R2-05 = Complete
R2-06 = Complete
R2-07 = Complete
R2-08 = Complete / PASS
R2-09 = Complete / PASS
R2-10 = Complete

N05D-04R2 = Complete
N05D-04   = Complete
N-05      = Complete / PASS
```

Phase N itself is **not complete**. The next P0 acceptance task is **N-06 — Retrieval / Vector quality**, followed by N-07 Failure / Recovery and the eventual Phase N closure audit.

This document is the current closure authority for N05D-04R2 and supersedes older `Active`, `BLOCKED`, `Next / Not Started`, or `Not Complete until R2-10` state notes when those notes describe the then-current state rather than historical evidence.

Historical blocked/failed/aborted attempts remain valid historical evidence and are not deleted or rewritten as PASS.

## 2. Closure inputs

### R2-08 quality acceptance

R2-08 was formally re-accepted after the R2-05 Semantic remediation and R2-06 Candidate E Similarity remediation.

Current accepted search behavior includes:

```text
active Object representation = object_overview
Facet representation          = first-class
Statement representation      = first-class
Hybrid semantic aggregation   = one bounded Object-level semantic vote
Overall Similarity            = hierarchical multi-vector / Facet-median Candidate E
Facet-specific Similarity     = same-Facet cosine / no fallback
legacy object_overall         = excluded from active R2 serving
```

Quality regressions that initially failed R2-08 were resolved without changing the frozen Harrier baseline.

### R2-09 performance/resource acceptance

Formal run:

```text
run_id:        20261024T044506+0900
measured HEAD: 2711d4c389c4d1c722e864e17a7b6afb05af4c62
result commit: 648c5f6eb5df1055f6a295a325d33a3016a78b4f
```

Exact sample set:

```text
Standard cold  3
Standard warm 20
Large cold     3
Large warm    20
```

Result:

```text
46 PASS
0 FAIL
0 ABORTED
0 retry
Evaluator Standard = PASS
Evaluator Large    = PASS
Evaluator overall  = PASS
```

Formal warm p95:

| Profile | warm p95 | Gate | Result |
|---|---:|---:|---|
| Standard | 12.2832216 s | <= 600 s | PASS |
| Large | 53.7066947 s | <= 1200 s | PASS |

The unchanged nearest-rank p95 rule was used.

## 3. Resource-remediation closure

Historical v1 Large behavior established the root problem:

```text
object_overall tokens        18,847
Torch peak allocated         ~51.061 GiB
Torch peak reserved          ~56.787 GiB
Windows Dedicated GPU        ~23.2 GiB
Windows Shared GPU           ~34.2 GiB
single Object embedding      ~628–643 s
```

The accepted R2 Large diagnostic established:

```text
object_overview tokens       103
Torch peak allocated         6.889365 GiB
Torch peak reserved          7.072266 GiB
Windows Dedicated GPU        7.525581 GiB
Windows Shared GPU           0.074219 GiB
derived_incremental_sync     49.1221762 s
included total               54.8322218 s
```

The formal run then confirmed stable performance across the required sample population. No model change, truncation, CPU fallback, FlashAttention substitution, ANN tuning, or performance-gate relaxation was needed.

Therefore the selected structural remediation is accepted as the root solution for N05D-04.

## 4. R2 serving and generation closure

Every formal sample passed independent generation/vector identity audit:

```text
active contract = n05d04r2-hierarchical-v2
active family   = object_overview / facet / statement
active object_overall leakage = 0
46 unique generation IDs
46 unique namespaces
34,684 audited Vector points
```

Provider space matched the frozen bootstrap declaration for every sample. Cold model construction remained inside the timed incremental sync boundary; warm-provider reuse remained the frozen benchmark policy.

The fresh-sample v1 fallback discovered during the first R2-09 attempt was resolved by connecting normal maintenance to the existing generation-aware representation builder, empty-R2 bootstrap, generation-routed Vector maintenance and generation metadata refresh. That remediation is part of the accepted final design, not a benchmark-only bypass.

## 5. Safety closure

The accepted run established:

- canonical before/after invariance PASS;
- original N-03 evaluation database full-table fingerprint unchanged;
- measured HEAD unchanged during the run;
- tracked repository state unchanged during the run;
- all three preserved R1 asset SHA-256 values unchanged;
- post-run evaluator tests: 8/8 PASS;
- post-run full pytest: 669 passed / 0 failed;
- repository-wide Ruff PASS;
- `git diff --check` PASS;
- no hidden traceback/OOM/access-denied/OS-error failure in worker/evaluator logs.

No historical evidence was deleted.

## 6. Phase-I superseding closure

Phase I remains historically **Complete**. R2 does not invalidate its historical closure; it supersedes only the active Derived Search semantics that later proved unsuitable for Large Objects.

Final active semantics after R2 closure are:

```text
v1 historical
  object_overall + facet + statement
  semantic_object_overall
  overall similarity = object_overall cosine

R2 active
  object_overview + facet + statement
  bounded semantic Object aggregation
  overall similarity = hierarchical multi-vector
  Candidate E Facet-median detail aggregation
```

Preserved Phase-I foundations include canonical SQLite authority, Harrier OSS v1 0.6B / 1024-dim Embedding Space, Qdrant as rebuildable derived Vector backend, membership-scoped identity, current/historical separation, same-Facet Facet Similarity and no silent backend/provider fallback.

`object_overall` remains historical/readable for compatibility and migration evidence, but it is not an active R2 serving representation.

## 7. Historical evidence disposition

The following remain historical and must not be reinterpreted as the current state:

- first N-05 formal Qdrant storage/path failure;
- N05D-02 long-input memory viability measurements;
- N05D-04 first rerun environment BLOCKED / user-aborted evidence;
- N05D-04R1 partial attention-backend experiment;
- first R2-08 quality FAIL;
- first R2-09 fresh-sample v1-wiring BLOCKED attempt.

They remain useful root-cause and regression evidence. Current closure is based on the later accepted quality and formal performance runs.

## 8. N-05 final acceptance statement

N-05 asked whether SGOKB's local automatic 1-Object processing meets the frozen Reference Workstation targets:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

The accepted formal result is:

```text
Standard warm p95 = 12.2832216 s
Large warm p95    = 53.7066947 s
N-05 verdict      = Complete / PASS
```

This closes N05D-04, N05D-04R2 and N-05.

## 9. Phase N state after closure

```text
N-01 = Complete
N-02 = Complete
N-03 = Complete
N-04 = Complete / PASS
N-05 = Complete / PASS
N-06 = Next / Ready
N-07 = Pending
Phase N = Active / Not Complete
```

R2 quality acceptance already exercised the R2-sensitive search-quality assets, but that does not silently mark the full N-06 task Complete. N-06 must be handled as its own Phase N acceptance task.

## 10. Authoritative evidence

- `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`
- `benchmark/results/n05d04r2-r2-09-performance-acceptance.json`
- `docs/evaluation/N05D04R2_R2_09_RUNNER_WIRING_REMEDIATION.md`
- `docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`
- `docs/evaluation/N05D04R2_R2_06_CANDIDATE_E_RESULT.md`
- `docs/evaluation/N05D04R2_R2_05_SEMANTIC_REGRESSION_ROOT_CAUSE_REVIEW.md`
- `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`
- `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

## 11. Next task

**N-06 [P0] — Retrieval / Vector quality** is the next Phase N task.

Do not reopen N-05 or change its accepted model/runtime/performance contract unless new evidence establishes a regression or a separately approved design change requires re-acceptance.
