# N05D-04R2 — Next Chat Handoff

Updated: 2026-10-24

- Project: Source Grounded Object Knowledge Base
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent task: `N-05 [P0] — Performance`
- Current remediation: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Current branch: `r2-06-similarity-regression-review`
- Current accepted implementation commit: `d0eaa50efc97adb9fbba8756c3c83ac166f05bf0`
- R2-08 formal acceptance record: `docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`
- Current next task: **R2-09 — Performance/resource acceptance + formal N-05 rerun**
- R2-09 start prerequisite: **accepted remediation/acceptance state must be integrated to clean `main == origin/main` first**
- Formal N-05: **BLOCKED / Not Complete**
- Formal performance target: **Not Judgeable until R2-09**

## 1. Read these documents first

Read in this order:

1. `docs/planning/phases/N/N05/execution/N05D04R2_NEXT_CHAT_HANDOFF.md`
2. `docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`
3. `docs/evaluation/N05D04R2_SEARCH_QUALITY_ACCEPTANCE.md`
4. `docs/evaluation/N05D04R2_R2_06_CANDIDATE_E_RESULT.md`
5. `docs/evaluation/N05D04R2_R2_05_SEMANTIC_REGRESSION_ROOT_CAUSE_REVIEW.md`
6. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`
7. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
8. `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`
9. `docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md`
10. `docs/evaluation/N05_PERFORMANCE.md`
11. `docs/planning/phases/N/PHASE_N_PREPARATION.md`

The accepted remediation is currently on `r2-06-similarity-regression-review`, not `main`. Do not begin R2-09 formal timing from an older `main` tree.

## 2. Current state

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active

R2-01 = Complete
R2-02 = Complete
R2-03 = Complete
R2-04 = Complete
R2-05 = Complete / Semantic remediation Accepted
R2-06 = Complete / Candidate E Accepted
R2-07 = Complete
R2-08 = Complete / PASS
R2-09 = Next / Not Started
R2-10 = Not Started

N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

## 3. R2-08 formal result

R2-08 is formally accepted using the already-complete Reference Workstation evidence from the Candidate E remediation run because that run executed the full R2-08 acceptance harness and post-remediation regressions on the implementation committed as `d0eaa50...`.

Key accepted evidence:

```text
Harrier OSS v1 0.6B fixed
R2 acceptance harness automatic verdict = PASS
Phase-I 24 Object queries = PASS / reviewed
22 Statement retrieval queries = PASS / reviewed
5 filter/version/temporal contracts = 5/5 PASS
4 existing Similarity cases = PASS / reviewed
R2SIM-G01..G06 = 6/6 PASS
3 Evidence Search cases / both paths = PASS
Facet-specific Similarity = PASS
active generation isolation = PASS
object_overall active leakage = 0
unexplained material metric regression = 0
R2-08 focused + Candidate E tests = 99 passed
Windows full pytest = 654 passed / 0 failed / 0 skipped
Ruff/format/diff = PASS
R1 assets = SHA-256 unchanged
N-06 interaction = documented
```

Formal record:

`docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`

## 4. Accepted Search-quality metrics

```text
Semantic
  MRR        1.0
  Recall@1   0.8541666666666666
  Recall@10  1.0
  nDCG@10    0.9930829680165895

Hybrid
  MRR        1.0
  Recall@1   0.8541666666666666
  Recall@10  1.0
  nDCG@10    1.0

Statement semantic
  MRR        1.0
  Recall@1   0.8636363636363636
  Recall@10  1.0
  nDCG@10    0.9927018899225625

Overall Similarity
  MRR        1.0
  Recall@1   1.0
  Recall@10  1.0
  nDCG@10    1.0

Facet Similarity
  MRR        1.0
  Recall@10  1.0
  nDCG@10    1.0
```

Semantic/Hybrid/Statement values match the exact historical comparable Phase-I values. Overall Similarity improves after the accepted remediation.

## 5. Accepted R2-06 Overall Similarity semantics

Candidate A/B/C/D were rejected during remediation.

Accepted Candidate E:

```text
candidate acquisition:
  object_overview ANN
  + same-Facet Facet ANN
  + same-Facet Statement ANN

canonical same-Facet anchor required

Facet-local Statement score:
  retain all observations from selected source Statement queries
  after one-best-point-per-source-query/Object dedup
  no score-based local eviction
  statement_mean = arithmetic mean

Facet cluster:
  with Statements:
    (.30 * Facet cosine + .20 * Statement mean) / .50
  without Statements:
    Facet cosine

Object detail:
  ordinary median of all eligible canonical Facet cluster scores

final:
  .50 * overview + .50 * detail_median

score_type:
  hierarchical_similarity
```

`eligible_shared_facet_count` is support metadata, not confidence or a score multiplier.

## 6. R2-08 resource observations

R2-08 records these observations only; they are not the formal N-05 performance verdict:

```text
Semantic p95:  53.804 ms
Hybrid p95:    47.052 ms
Statement p95: 7.341 ms
quality harness wall-clock: 12.5137445 s
CUDA: NVIDIA GeForce RTX 4090
Torch max allocated: 1,338,302,464 bytes
Torch max reserved:  1,430,257,664 bytes
```

R2-09 owns formal resource/performance acceptance.

## 7. N-06 interaction

N-06 remains `Ready` and is not closed by R2-08.

When N-06 is eventually executed, it must evaluate Retrieval / Vector quality using:

```text
R2 active generation
object_overview / Facet / Statement active family
Candidate E Overall Similarity semantics
```

Do not return to the retired active `object_overall` path.

## 8. Important R2-09 prerequisite

The accepted remediation branch has not been merged to `main`.

R2-09 preflight requires:

```text
clean main == origin/main
```

Therefore before R2-09 formal timing:

1. review the accepted branch diff/commit history;
2. integrate the accepted R2-05/R2-06/R2-08 state to `main` through the user's chosen Git workflow;
3. verify `main == origin/main` and clean worktree;
4. preserve the three R1 user-aborted assets byte-for-byte;
5. only then perform the R2-09 preflight and formal performance work.

Do not silently merge or reset the user's local workspace.

## 9. R2-09 scope reminder

R2-09 performs performance/resource acceptance and then the new formal N-05 run.

Before the 46 formal samples, compare v1 vs R2 Large fixture for:

```text
object-level token length
peak allocated/reserved GPU memory
Dedicated/Shared GPU memory
derived_incremental_sync wall-clock
end-to-end sample wall-clock
```

Formal samples remain:

```text
Standard cold 3 + warm 20
Large cold    3 + warm 20
```

Use a new run ID. Do not reuse historical N-05 verdicts.

## 10. Fixed model/runtime policy

For R2-09 keep the accepted causal baseline unless an explicit later task changes it:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
truncation: prohibited
```

Do not introduce Harrier 270M, CPU fallback, FlashAttention-2, PyTorch/CUDA upgrades or arbitrary token chunking as part of R2-09.

## 11. Final handoff state

```text
R2-08 = Complete / PASS
R2-09 = Next / Not Started
R2-10 = Not Started
N05D-04R2 = Active
N05D-04 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

Next action: integrate the accepted remediation state to `main`, then execute R2-09 preflight/performance acceptance.