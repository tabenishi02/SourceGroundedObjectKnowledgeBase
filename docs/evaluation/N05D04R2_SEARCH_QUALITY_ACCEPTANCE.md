# N05D-04R2 / R2-08 — Search-quality acceptance

Updated: 2026-10-23

Status: **Implementation Complete / Local Quality Verification Pending**

R2-08 is not Complete until the frozen Harrier 0.6B gold run and the required R2 regression suite pass on a local/reference runtime. R2-09 is not started.

## 1. Goal

R2-08 detects retrieval-quality regressions introduced by the N05D-04R2 representation and similarity redesign before formal N-05 performance timing is authorized.

The accepted comparison is causal:

```text
embedding model / space: fixed Harrier OSS v1 0.6B
canonical synthetic gold: fixed Phase-I search-quality-gold-v1
representation contract: v1 object_overall -> R2 object_overview + Facet + Statement
Object Similarity: Phase-I overall cosine -> bounded hierarchical_similarity
```

This task does not change the model, truncate representations, tune CUDA/PyTorch, or execute the R2-09 46-sample performance run.

## 2. Authority and assets

R2-08 uses these existing authorities without rewriting their historical expectations:

```text
benchmark/search-quality-gold-v1.json
  Phase-I / N-06 current frozen synthetic Search gold

docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
  accepted Phase-I baseline metrics

benchmark/n05d04r2-object-similarity-gold-v1.json
  R2-06 six hierarchical similarity cases

docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md
  active representation / Hybrid contract

docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md
  hierarchical Object Similarity contract
```

R2-08 adds:

```text
benchmark/n05d04r2-search-quality-acceptance-v1.json
scripts/run_n05d04r2_search_quality_acceptance.py
tests/test_n05d04r2_search_quality_acceptance.py
```

The Phase-I frozen fixture remains unchanged. R2-specific expectations are layered in a separate acceptance contract.

## 3. Phase-I observed baseline

Accepted I-07 observations used for comparison:

| Domain | Metric | Phase-I observed |
|---|---|---:|
| exact identity | accuracy | 1.000 |
| Hybrid | MRR | 1.000 |
| Hybrid | Recall@1 | 0.854 |
| Hybrid | Recall@10 | 1.000 |
| Hybrid | nDCG@10 | 1.000 |
| Semantic | MRR | 1.000 |
| Semantic | Recall@1 | 0.854 |
| Semantic | Recall@10 | 1.000 |
| Semantic | nDCG@10 | 0.993 |
| Statement semantic | MRR | 1.000 |
| Statement semantic | Recall@1 | 0.864 |
| Statement semantic | Recall@10 | 1.000 |
| Statement semantic | nDCG@10 | 0.993 |
| Overall Similarity | MRR | 0.833 |
| Overall Similarity | Recall@1 | 0.667 |
| Overall Similarity | Recall@10 | 1.000 |
| Overall Similarity | nDCG@10 | 0.877 |
| Facet Similarity | MRR | 1.000 |
| Facet Similarity | Recall@10 | 1.000 |
| Facet Similarity | nDCG@10 | 1.000 |
| Evidence lexical/association | MRR / Recall@10 / nDCG@10 | 1.000 / 1.000 / 1.000 |
| Evidence semantic | MRR / Recall@10 / nDCG@10 | 1.000 / 1.000 / 1.000 |
| Search contract cases | pass | 5 / 5 |

The machine-readable contract stores the published rounded observations. Metrics that were perfect in the accepted baseline form strict non-regression gates. Other comparable metrics are reported as deltas and any negative delta requires case-level explanation rather than an invented tolerance.

Overall Similarity is specifically review-classified because R2 intentionally changes its scoring semantics from a single overall vector to `hierarchical_similarity`; a change is acceptable only when it is explained by the frozen R2-06 contract and does not violate the six R2 similarity gold cases.

## 4. R2 acceptance harness

`scripts/run_n05d04r2_search_quality_acceptance.py` creates a fresh synthetic SQLite DB under `.local/` and does not touch the production/reference database.

The harness:

1. loads the frozen Phase-I gold;
2. populates the same canonical synthetic Knowledge;
3. materializes R2 `object_overview + facet + statement` representations for every accepted Version;
4. creates an isolated synthetic ready R2 generation and makes it the only active Knowledge generation in that temporary DB;
5. verifies the provider is the frozen Harrier OSS v1 0.6B revision / 1024-dimensional space;
6. embeds only R2 generation representations;
7. builds an Exact Vector reference over only that generation;
8. re-runs Object Semantic/Hybrid, Statement retrieval, filters/current-history/temporal, Facet/overall Similarity, and Evidence Search;
9. records result metrics, latency, representation/vector counts and available Torch CUDA peak allocation/reservation;
10. audits the active representation family and rejects `object_overall` leakage, mixed generation payload, or duplicate Object results;
11. compares results to the accepted Phase-I observations.

The harness writes:

```text
.local/n05d04r2-search-quality-result.json
```

Its `automatic_verdict` is not by itself the R2-08 final verdict. The required R2 contract tests and manual classification of any negative comparable metric delta must also pass.

## 5. Hierarchical Similarity gold integration

`benchmark/n05d04r2-object-similarity-gold-v1.json` contains six frozen cases:

| ID | Contract |
|---|---|
| R2SIM-G01 | same-Facet detail breaks an overview tie |
| R2SIM-G02 | bounded Statement evidence may break overview/Facet ties |
| R2SIM-G03 | unrelated Statement volume gives no count boost |
| R2SIM-G04 | canonical Facet boundary is hard; no fallback |
| R2SIM-G05 | one generation / current-candidate isolation / no object_overall |
| R2SIM-G06 | work is bounded by the R2 caps |

R2-08 does not duplicate these scenarios into a second competing gold. The acceptance contract requires all six IDs and the R2 unit/regression suite that implements them.

## 6. Required contract regression

At minimum the local acceptance run must execute:

```text
tests/test_n05d04r2_search_quality_acceptance.py
tests/test_hybrid_search_r2.py
tests/test_object_similarity_r2.py
tests/test_generation_lifecycle_r2.py
tests/test_generation_lifecycle_qdrant_r2.py
tests/test_object_overview_r2.py
tests/test_search_quality_gold.py
tests/test_j02_evidence_search.py
```

The acceptance review must prove:

- exact name > alias > non-exact identity ordering remains intact;
- one Object appears at most once in public Search results;
- broad queries can use `object_overview`;
- Facet/Statement channels can resolve detail ties;
- Facet-scoped Search excludes overview and other Facets and never falls back silently;
- temporal / derivation filters remain Statement-only;
- current/historical semantics remain correct;
- same-Facet Similarity remains raw cosine;
- hierarchical Similarity honors same-Facet boundaries, component caps and deterministic ordering;
- source Object is excluded from candidate results;
- same Primary Class is default and cross-class remains opt-in;
- all active R2 vector evidence belongs to one generation;
- `object_overall` is absent from active R2 Search/Similarity evidence;
- Evidence Search remains independent and non-regressed;
- degraded/runtime behavior remains compatible with the accepted public Search contract.

## 7. N-06 impact review

`PHASE_N_PREPARATION.md` defines N-06 as **Ready; redesign interaction required** and identifies the relevant channels as Identity, Lexical, Semantic, Hybrid, Overall Similarity, Facet Similarity, Evidence Search, and relation/filter/current-historical isolation.

At the R2-07 completion HEAD there is no separate committed `N06*` execution asset/result tree. The current Search-quality authority is still the Phase-I fixture and harness referenced by `benchmark/README.md`:

```text
benchmark/search-quality-gold-v1.json
scripts/run_search_quality_gold.py
docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
```

R2-08 therefore does not close N-06. It re-accepts the changed Retrieval semantics against those current assets and records the R2-specific contract. When N-06 is executed, it must run with the R2 active generation rather than the retired `object_overall` serving path.

R2-08 also does not repeat the full 100k ANN backend or reranker study because the R2 change is representation/aggregation semantics, not a Vector backend or reranker replacement. N-06 remains responsible for its full Retrieval/Vector-quality scope.

## 8. Local verification command

From a clean verification worktree based on the candidate branch:

```powershell
python -m pytest `
  tests/test_n05d04r2_search_quality_acceptance.py `
  tests/test_hybrid_search_r2.py `
  tests/test_object_similarity_r2.py `
  tests/test_generation_lifecycle_r2.py `
  tests/test_generation_lifecycle_qdrant_r2.py `
  tests/test_object_overview_r2.py `
  tests/test_search_quality_gold.py `
  tests/test_j02_evidence_search.py -q

python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only
```

Then inspect `.local/n05d04r2-search-quality-result.json` and classify every `review_on_negative_delta` item. If any negative delta is unexplained, R2-08 fails and returns to R2-05/R2-06; do not proceed to R2-09 and do not change the embedding model to hide the regression.

After focused acceptance, run the relevant full regression, compile, Ruff/format/diff checks, and verify the three preserved R1 assets still have their pre-run SHA-256 values.

## 9. Completion gate

R2-08 may become Complete only when all of the following are evidenced:

```text
Harrier 0.6B fixed runtime                         PASS
R2 acceptance harness automatic gate              PASS
Phase-I 24 Object queries re-run                   PASS / reviewed
22 Statement retrieval queries                     PASS / reviewed
5 filter/version/temporal contract cases           5/5 PASS
4 existing Similarity cases                        PASS / reviewed
6 R2 hierarchical Similarity cases                 6/6 PASS
3 Evidence Search cases, both paths                PASS
Facet Similarity compatibility                     PASS
active generation isolation                        PASS
object_overall active leakage                      0
unexplained material metric regression             0
latency/resource observations                      recorded
required regression/full regression                PASS
Ruff/format/diff                                    PASS
R1 user-aborted assets                             SHA-256 unchanged
N-06 interaction                                   documented
```

Only after this gate passes may the task tracker change to:

```text
R2-08 = Complete
R2-09 = Next / Not Started
```

Until then:

```text
R2-08 = FAIL / Not Complete (separate R2-06 Overall Similarity losses)
R2-09 = Not Started
N05D-04R2 = Active
N05D-04 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

## 10. Current result (2026-10-24)

**R2-08 = FAIL / Not Complete. R2-09 = blocked / Not Started.**

Reference Workstation execution is now evidenced. R2-05 Semantic remediation
restores `short_japanese_love` from rank 3 to rank 1; all 24 Semantic and Hybrid
queries have no negative case-level metric delta versus the saved comparable
Phase-I result. The fixed Harrier harness automatic gate passes.

The separate R2-06 `work_overall` and `concept_overall` losses remain unchanged;
this task does not implement Similarity remediation or close R2-08. Re-run the
full R2-08 acceptance after separately addressing that cause.

Detailed runtime proof, ablations, overview probes and regression counts:
`N05D04R2_R2_05_SEMANTIC_REGRESSION_ROOT_CAUSE_REVIEW.md`, Reference Workstation
remediation verification section. Machine-readable synthetic result:
`benchmark/results/n05d04r2-r2-05-semantic-remediation.json`.

N-05 remains BLOCKED / Not Complete. No formal performance run was started.
