# N05D-04R2 / R2-08 — Search-quality acceptance

Updated: 2026-10-24

Status: **Complete / PASS**

Formal result:

`docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`

Accepted implementation commit:

`d0eaa50efc97adb9fbba8756c3c83ac166f05bf0`

Reference Workstation evidence run:

`20261024T020709`

R2-09 is now **Next / Not Started**. Formal N-05 performance timing has not started.

## 1. Goal

R2-08 detects retrieval-quality regressions introduced by the N05D-04R2 representation and similarity redesign before formal N-05 performance timing is authorized.

The accepted comparison remains causal:

```text
embedding model / space: fixed Harrier OSS v1 0.6B
canonical synthetic gold: fixed Phase-I search-quality-gold-v1
representation contract: v1 object_overall -> R2 object_overview + Facet + Statement
Object Similarity: Phase-I overall cosine -> hierarchical_similarity
```

This task does not change the model, truncate representations, tune CUDA/PyTorch, close N-06, or execute the R2-09 46-sample performance run.

## 2. Authority and assets

R2-08 uses these authorities without rewriting historical expectations:

```text
benchmark/search-quality-gold-v1.json
docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
benchmark/n05d04r2-object-similarity-gold-v1.json
benchmark/n05d04r2-search-quality-acceptance-v1.json
docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md
```

The Phase-I frozen fixture remains unchanged. R2-specific expectations are layered separately.

## 3. Accepted remediation chain

Historical first R2-08 execution failed because:

```text
R2-05 Semantic:
  short_japanese_love expected Mika rank1, observed rank3

R2-06 Overall Similarity:
  work_overall expected Ash Garden rank1, observed rank2
  concept_overall expected Altruism rank1, observed rank2
```

The regressions were remediated separately:

```text
R2-05 Semantic remediation
  semantic role-aware inner aggregation
  Complete / Accepted

R2-06 Overall Similarity remediation
  Candidate E — source-bounded canonical Facet clusters
  all selected-query Statement observations retained
  Facet-local arithmetic Statement mean
  eligible Facet detail = ordinary median
  final = 0.50 * overview + 0.50 * detail_median
  Complete / Accepted
```

No model/runtime change was used to hide the regressions.

## 4. Formal re-acceptance evidence

The Candidate E Reference Workstation verification already executed the complete R2-08 harness and required regressions on the implementation committed as `d0eaa50...`. The verification worktree was clean and the remote branch head matched the accepted commit after push, so the formal review reuses that evidence rather than duplicating the same local run.

Key evidence:

```text
R2 acceptance harness automatic verdict: PASS
R2-08 focused + Candidate E tests:       99 passed
Windows full pytest:                     654 passed / 0 failed / 0 skipped
R2SIM-G01..G06:                          6 / 6 PASS
R2-05 Semantic/Hybrid:                   24-query rankings/metrics unchanged
22 Statement retrieval queries:          PASS
5 filter/version/temporal contracts:      5 / 5 PASS
Evidence Search both paths:               PASS
Facet-specific Similarity:                PASS
active object_overall leakage:            0
R1 preserved assets:                      SHA-256 unchanged
```

Detailed review:

`docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`

Machine-readable remediation/quality evidence:

`benchmark/results/n05d04r2-r2-06-candidate-e-remediation.json`

## 5. Comparable quality result

### Object Search

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
```

These match the exact historical Phase-I comparable values. There are **0 unexplained negative metric deltas**.

### Similarity

Accepted R2 result:

```text
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

Overall Similarity improves over the Phase-I observed baseline while preserving the R2 hierarchical contracts.

Four existing frozen cases rank correctly:

```text
Character overall : Mika       0.8312071178407453
Character values  : Mika       0.8341502142144167
Work overall      : Ash Garden 0.857757151406386
Concept overall   : Altruism   0.8256451816438397
```

## 6. R2 hierarchical Similarity gold

All frozen cases pass without expectation rewrites:

```text
R2SIM-G01 PASS
R2SIM-G02 PASS
R2SIM-G03 PASS
R2SIM-G04 PASS
R2SIM-G05 PASS
R2SIM-G06 PASS
```

Result: **6 / 6 PASS**.

## 7. Structural acceptance

The active synthetic R2 run confirms:

```text
active generation contract = n05d04r2-hierarchical-v2
membership kinds           = facet / object_overview / statement
vector kinds               = facet / object_overview / statement
single generation payload  = PASS
one Object = one result     = PASS
Facet hard boundary        = PASS
current/history isolation  = PASS
temporal/derivation        = PASS
source exclusion           = PASS
same/cross class           = PASS
object_overall leakage     = 0
```

Facet-specific Similarity remains same-Facet raw cosine with no overview/other-Facet fallback.

## 8. Evidence Search

The three frozen Evidence Search cases pass on both required paths:

```text
lexical/association
  MRR / Recall@10 / nDCG@10 = 1 / 1 / 1

semantic
  MRR / Recall@10 / nDCG@10 = 1 / 1 / 1
```

Evidence Search remains independent of the Knowledge generation redesign.

## 9. Latency / resource observations

R2-08 records observations but does not issue a formal performance verdict.

```text
Semantic Search, 24 queries
  p50  28.885 ms
  p95  53.804 ms
  mean 34.004 ms

Hybrid Search, 24 queries
  p50  29.584 ms
  p95  47.052 ms
  mean 32.088 ms

Statement semantic, 22 queries
  p50  0.621 ms
  p95  7.341 ms
  mean 1.425 ms

quality harness wall-clock
  12.5137445 s

CUDA device
  NVIDIA GeForce RTX 4090

Torch peak allocated
  1,338,302,464 bytes

Torch peak reserved
  1,430,257,664 bytes
```

These observations satisfy R2-08's recording requirement only. R2-09 owns formal performance/resource acceptance.

## 10. Regression / static verification

```text
Similarity + acceptance focused: 41 passed
R2-08 focused + Candidate E:     99 passed
Windows full pytest:             654 passed / 0 failed / 0 skipped
compileall:                      PASS
Ruff src/tests/scripts:          PASS
changed Python format check:     PASS
git diff --check:                PASS
```

Repository-wide Ruff retains only the documented unrelated baseline `benchmark/tools/n05_resource_preflight.py:69 E501`; it is unchanged.

All three R1 user-aborted assets retain identical before/after SHA-256 values.

## 11. N-06 interaction

R2-08 does not close N-06.

N-06 remains `Ready` and must later evaluate Retrieval / Vector quality with the R2 active generation and Candidate E semantics. The current authority remains the frozen Phase-I assets plus the R2 acceptance overlay.

R2-08 does not repeat the full N-06 ANN/reranker study.

## 12. Completion gate

```text
Harrier 0.6B fixed runtime                         PASS
R2 acceptance harness automatic gate              PASS
Phase-I 24 Object queries                         PASS / reviewed
22 Statement retrieval queries                    PASS / reviewed
5 filter/version/temporal contract cases          5/5 PASS
4 existing Similarity cases                       PASS / reviewed
6 R2 hierarchical Similarity cases                6/6 PASS
3 Evidence Search cases, both paths                PASS
Facet Similarity compatibility                     PASS
active generation isolation                        PASS
object_overall active leakage                      0
unexplained material metric regression             0
latency/resource observations                      recorded
required/full regression                           PASS
Ruff/format/diff                                    PASS
R1 user-aborted assets                             SHA-256 unchanged
N-06 interaction                                   documented
```

All completion gates pass.

## 13. Final state

```text
R2-08 = Complete / PASS
R2-09 = Next / Not Started
N05D-04R2 = Active
N05D-04 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable until R2-09
```

R2-08 explicitly authorizes R2-09 performance/resource acceptance and the subsequent formal N-05 rerun.
