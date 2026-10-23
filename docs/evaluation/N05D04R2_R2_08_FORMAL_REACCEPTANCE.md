# N05D-04R2 / R2-08 — Formal Search-quality Re-acceptance

Updated: 2026-10-24

- Task: `R2-08 [P0] — Search-quality acceptance`
- Branch: `r2-06-similarity-regression-review`
- Accepted implementation commit: `d0eaa50efc97adb9fbba8756c3c83ac166f05bf0`
- Reference Workstation evidence run: `20261024T020709`
- Result: **PASS / Complete**
- R2-09: **Next / Not Started**
- Formal N-05 performance timing: **Not Started**

## 1. Decision

R2-08 is formally re-accepted.

The previous R2-08 failure was caused by two independent regressions:

1. R2-05 Semantic ranking flattened `object_overview`, Facet and Statement semantic roles at the outer Hybrid fusion boundary;
2. R2-06 Overall Similarity ranking used an aggregation rule that produced incorrect Work/Concept ordering.

Those causes were remediated separately before this review:

- R2-05 Semantic remediation is Complete / Accepted;
- R2-06 Candidate E Facet-median remediation is Complete / runtime verified on this branch.

No embedding-model, CUDA/PyTorch, representation truncation, canonical Knowledge, Qdrant backend or reranker change was used to hide the quality regression.

## 2. Evidence reuse / no duplicate local rerun

This formal review reuses the Reference Workstation execution produced while accepting Candidate E because that run already executed the R2-08 acceptance harness and every required post-remediation regression on the exact implementation that was committed as `d0eaa50...`.

Evidence:

```text
Candidate E implementation/runtime verification
run: 20261024T020709
branch: r2-06-similarity-regression-review
final commit: d0eaa50efc97adb9fbba8756c3c83ac166f05bf0
R2-08 automatic harness: PASS
R2-08 focused set + Candidate E tests: 99 passed
Windows full pytest: 654 passed / 0 failed / 0 skipped
```

The verification worktree was clean after commit/push and the remote branch head equals the accepted commit. A second identical local run would add no new acceptance dimension, so it is not required for this formal review.

## 3. Fixed causal baseline

The frozen runtime remained:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dimension: 1024
CUDA / bfloat16
normalize_embeddings: true
overflow: reject / no truncation
```

Active R2 representation family:

```text
object_overview
facet
statement
```

Forbidden active representation:

```text
object_overall
```

## 4. Phase-I comparable quality review

The historical Phase-I gold and observed baseline were not rewritten.

### Search / retrieval

| Channel | Phase-I baseline | Accepted R2 result | Review |
|---|---|---|---|
| Exact lookup accuracy | 1.000 | 1.000 | unchanged |
| Semantic MRR | 1.000 | 1.000 | unchanged |
| Semantic Recall@1 | 0.854 | 0.8541666667 | unchanged at exact historical value |
| Semantic Recall@10 | 1.000 | 1.000 | unchanged |
| Semantic nDCG@10 | 0.993 | 0.9930829680 | unchanged at exact historical value |
| Hybrid MRR | 1.000 | 1.000 | unchanged |
| Hybrid Recall@1 | 0.854 | 0.8541666667 | unchanged at exact historical value |
| Hybrid Recall@10 | 1.000 | 1.000 | unchanged |
| Hybrid nDCG@10 | 1.000 | 1.000 | unchanged |
| Statement MRR | 1.000 | 1.000 | unchanged |
| Statement Recall@1 | 0.864 | 0.8636363636 | unchanged at exact historical value |
| Statement Recall@10 | 1.000 | 1.000 | unchanged |
| Statement nDCG@10 | 0.993 | 0.9927018899 | unchanged at exact historical value |

The R2-05 remediation record confirms all 24 Semantic/Hybrid rankings and case metrics match the verified parent. The Candidate E run preserves those results unchanged. All 22 Statement retrieval cases pass and the Statement path was not changed by Candidate E.

Therefore the `review_on_any_negative_delta` review finds **0 unexplained negative comparable deltas**.

### Existing Similarity

| Channel | Phase-I baseline | Accepted R2 result | Review |
|---|---|---|---|
| Overall Similarity MRR | 0.833 | 1.000 | improved |
| Overall Similarity Recall@1 | 0.667 | 1.000 | improved |
| Overall Similarity Recall@10 | 1.000 | 1.000 | unchanged |
| Overall Similarity nDCG@10 | 0.877 | 1.000 | improved |
| Facet Similarity MRR | 1.000 | 1.000 | unchanged |
| Facet Similarity Recall@10 | 1.000 | 1.000 | unchanged |
| Facet Similarity nDCG@10 | 1.000 | 1.000 | unchanged |

Four existing Similarity cases all rank their expected result first after Candidate E:

```text
Character overall : Mika       0.8312071178407453
Character values  : Mika       0.8341502142144167
Work overall      : Ash Garden 0.857757151406386
Concept overall   : Altruism   0.8256451816438397
```

## 5. R2 hierarchical Similarity gold

All frozen R2SIM cases pass without changing their expected outcomes:

```text
R2SIM-G01 PASS
R2SIM-G02 PASS
R2SIM-G03 PASS
R2SIM-G04 PASS
R2SIM-G05 PASS
R2SIM-G06 PASS
```

Result: **6 / 6 PASS**.

Candidate E additionally passed its structural E1-E12 diagnostics. These diagnostics are supporting remediation evidence, not replacements for R2SIM-G01..G06.

## 6. Contracts and Evidence Search

The frozen five contract cases pass:

```text
current_excludes_old PASS
historical_finds_old PASS
temporal_inside PASS
temporal_outside PASS
facet_hard_filter PASS
```

Result: **5 / 5 PASS**.

Evidence Search remains independent and non-regressed:

```text
lexical/association: MRR 1 / Recall@10 1 / nDCG@10 1
semantic:            MRR 1 / Recall@10 1 / nDCG@10 1
```

All three frozen Evidence Search cases pass on both required paths.

## 7. Structural / generation acceptance

The accepted harness audits:

```text
active generation contract = n05d04r2-hierarchical-v2
membership kinds           = facet / object_overview / statement
vector kinds               = facet / object_overview / statement
single generation payload  = PASS
one Object = one result     = PASS
object_overall leakage      = 0
```

Additional focused/full regressions cover:

- generation isolation;
- current / historical semantics;
- temporal / derivation contracts;
- Facet hard boundary and no fallback;
- source Object exclusion;
- same-class default / explicit cross-class;
- payload and SQLite generation membership integrity;
- Application / CLI / MCP serialization;
- Facet-specific raw-cosine compatibility.

## 8. Latency / resource observations

R2-08 records observations only; it does not issue the formal N-05 performance verdict.

Accepted synthetic quality run observations:

| Operation | Count | p50 | p95 | Mean |
|---|---:|---:|---:|---:|
| Semantic Object Search | 24 | 28.885 ms | 53.804 ms | 34.004 ms |
| Hybrid Object Search | 24 | 29.584 ms | 47.052 ms | 32.088 ms |
| Statement semantic | 22 | 0.621 ms | 7.341 ms | 1.425 ms |

Harness wall-clock:

```text
12.5137445 s
```

Available CUDA observations:

```text
device: NVIDIA GeForce RTX 4090
Torch max_memory_allocated: 1,338,302,464 bytes
Torch max_memory_reserved:  1,430,257,664 bytes
```

These numbers satisfy the R2-08 requirement to record resource/latency observations. They are **not** substituted for R2-09's formal Reference Workstation performance/resource acceptance.

## 9. Regression / repository integrity

Post-remediation evidence:

```text
Similarity + acceptance focused: 41 passed
R2SIM mapped:                    6 / 6 PASS
R2-08 focused + Candidate E:     99 passed
Windows full pytest:             654 passed / 0 failed / 0 skipped
compileall:                      PASS
Ruff src/tests/scripts:          PASS
changed-Python format check:     PASS
git diff --check:                PASS
```

Repository-wide Ruff still contains only the documented unrelated baseline:

```text
benchmark/tools/n05_resource_preflight.py:69 E501
```

It is unchanged and is not an R2-08 regression.

All three preserved R1 user-aborted assets have identical before/after SHA-256 values.

No production canonical DB, production Qdrant namespace or reference active pointer was changed by this acceptance review.

## 10. N-06 interaction review

R2-08 does not close N-06.

The current N-06 Search-quality authority remains the frozen Phase-I fixture/assets plus the R2-specific acceptance overlay:

```text
benchmark/search-quality-gold-v1.json
scripts/run_search_quality_gold.py
docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
benchmark/n05d04r2-search-quality-acceptance-v1.json
benchmark/n05d04r2-object-similarity-gold-v1.json
```

N-06 remains `Ready` and, when executed, must evaluate Retrieval / Vector quality with the R2 active generation and Candidate E Overall Similarity semantics rather than the retired active `object_overall` path.

R2-08 does not execute N-06 closure, the full 100k ANN/reranker study, or R2-09 formal performance timing.

## 11. Completion gate

| Gate | Result |
|---|---|
| Harrier 0.6B fixed runtime | PASS |
| R2 acceptance harness automatic gate | PASS |
| Phase-I 24 Object queries | PASS / reviewed |
| 22 Statement retrieval queries | PASS / reviewed |
| 5 filter/version/temporal contracts | 5/5 PASS |
| 4 existing Similarity cases | PASS / reviewed |
| 6 R2 hierarchical Similarity cases | 6/6 PASS |
| 3 Evidence Search cases / both paths | PASS |
| Facet Similarity compatibility | PASS |
| active generation isolation | PASS |
| active `object_overall` leakage | 0 |
| unexplained material metric regression | 0 |
| latency/resource observations | recorded |
| required/full regression | PASS |
| Ruff/format/diff | PASS |
| R1 preserved assets | SHA-256 unchanged |
| N-06 interaction | documented |

All R2-08 completion gates pass.

## 12. Final state

```text
R2-05 remediation = Complete / Accepted
R2-06 remediation = Complete / Accepted
R2-07             = Complete
R2-08             = Complete / PASS
R2-09             = Next / Not Started
N05D-04R2         = Active
N05D-04           = BLOCKED / Not Complete
N-05              = BLOCKED / Not Complete
performance target = Not Judgeable until R2-09
```

R2-08 explicitly authorizes the R2-09 performance/resource acceptance task.

Do not infer an N-05 performance PASS from this result.