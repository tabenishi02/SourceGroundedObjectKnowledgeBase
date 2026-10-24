# N-06 — Retrieval / Vector Quality Acceptance

Updated: 2026-10-24

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-06 [P0] — Retrieval / Vector quality`
- Status: **Complete / PASS**
- Parent state: N-05 `Complete / PASS`; Phase N `Active / Not Complete`
- Active search generation: `n05d04r2-hierarchical-v2`
- Embedding baseline: `microsoft/harrier-oss-v1-0.6b`
- Revision: `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`
- Vector backend: native Qdrant 1.19.2
- R2-10 closure: `docs/evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md`
- R2 search-quality acceptance: `docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md`
- Phase-I historical benchmark: `docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`
- Real-data dataset: `benchmark/n03-real-data-vertical-slice-v1.json`

## 1. Goal

N-06 determines whether the accepted R2 retrieval and vector stack is sufficiently accurate, bounded, explainable, and operationally viable on the Reference Workstation.

N-06 is broader than R2-08. R2-08 accepted the search-quality changes required to unblock N-05, but explicitly did not close:

```text
full 100k ANN/backend study
R2-compatible reranker study
real-data N-03 retrieval acceptance
Statement Embedding marginal-value review at N-06 scope
```

N-06 must evaluate those dimensions without reopening N-05 or changing the accepted R2 ranking/model merely to improve benchmark results.

## 2. Frozen architecture under test

```text
canonical SQLite Knowledge
        ↓
R2 Search Representation
  object_overview
  facet
  statement
        ↓
Harrier OSS v1 0.6B / 1024-dim
        ↓
generation-scoped Qdrant
        ↓
Lexical / Semantic / Hybrid
        ↓
Object aggregation / Candidate E Overall Similarity
        ↓
1 Object = 1 result
```

Hard constraints:

- active `object_overall` leakage = 0;
- one request resolves one active generation;
- no generation mixing;
- no silent provider/backend/CPU fallback;
- no truncation;
- current/historical and Facet boundaries remain hard contracts;
- score remains relevance/similarity, not truth/confidence;
- reranker is evaluation-only unless a separate later design task explicitly adopts it.

## 3. Evaluation stages

### N06-A — preflight / identity / regression

Require before benchmark execution:

```text
clean main == origin/main
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
Qdrant healthy
RTX 4090 available for Harrier/reranker evaluation
no material competing CUDA workload
```

Record exact package/runtime versions and git HEAD.

The three historical R1 local assets must remain byte-identical if present in the original workspace.

### N06-B — R2 frozen synthetic Search gold

Use:

```text
benchmark/search-quality-gold-v1.json
benchmark/n05d04r2-search-quality-acceptance-v1.json
benchmark/n05d04r2-object-similarity-gold-v1.json
```

Evaluate at minimum:

```text
exact identity
Lexical Object Search
Semantic Object Search
Hybrid Object Search
Statement Semantic Search
Overall Object Similarity
Facet Similarity
Evidence Search
current / historical
Class / Facet / temporal / derivation filters
generation isolation
```

Metrics:

```text
MRR
Recall@1
Recall@5
Recall@10
nDCG@10
p50 / p95 latency
```

Acceptance:

- R2-08 frozen required contracts remain PASS;
- exact identity accuracy = 1.0;
- Semantic / Hybrid / Statement Recall@10 = 1.0 on the frozen gold;
- Hybrid MRR = 1.0;
- R2 hierarchical Similarity frozen cases = 6/6 PASS;
- Facet Similarity frozen cases PASS;
- Evidence Search frozen cases PASS on both required paths;
- unexplained negative comparable delta from accepted R2-08 = 0;
- active `object_overall` leakage = 0.

This stage is a new N-06 evidence run, not a reinterpretation of the R2-08 result.

### N06-C — N-03 real-data retrieval acceptance

Use a copy/snapshot of the completed N-03 evaluation DB and its machine-readable manifest. Do not mutate the preserved N-03 canonical evidence in place.

Dataset:

```text
6 Objects
8 real Web Captures
Character: Saber / Ichigo Kurosaki
Work: Fate/stay night / BLEACH
Concept: Tsundere / Hero's Journey
```

Use the manifest/human notes as the judgement source; do not invent external facts or add new web data.

Evaluate all frozen `expected_search_queries`, including identity/alias and content/paraphrase probes, in the applicable channels.

Record:

```text
query count
ranked Object IDs
MRR
Recall@1 / @5 / @10
nDCG@10
per-query failure analysis
Lexical vs Semantic vs Hybrid
```

Acceptance policy:

- canonical name/alias identity probes must rank the target first;
- Hybrid must retrieve every supported target within top 10;
- Semantic must retrieve every supported semantic target within top 10;
- any Lexical miss must be classified as either retrieval defect or canonical Knowledge/wording coverage limitation, not silently counted as semantic failure;
- no query may succeed by historical-version or generation leakage;
- unsupported/out-of-scope manifest items are not converted into positive gold.

Because the N-03 set is small, report metrics but do not treat them as a statistically general population estimate.

### N06-D — Statement Embedding ablation

On both the frozen synthetic query set and the applicable N-03 content-query set, compare:

```text
R2 full semantic family
  overview + facet + statement

Ablation
  overview + facet
  statement channel excluded from Object-level candidate/fusion
```

Do not delete Statement representations or change direct Statement Search.

Record Object-level:

```text
MRR
Recall@1 / @10
nDCG@10
case-by-case rank changes
```

Also record direct Statement Search separately.

Decision rule:

- if Statement channel yields a reproducible Object-level gain, retain that gain as evidence for current architecture;
- if Object-level gain is not observed, keep Statement representation because direct Statement retrieval, matched-grounding evidence, and future same-Facet competition remain independent requirements;
- N-06 must not remove Statement representation solely because this ablation shows no Object-level gain.

### N06-E — R2-compatible reranker study

The historical I-07 object reranker reads `object_overall` and is therefore not an R2 acceptance path.

Evaluate rerankers only on bounded first-stage Statement candidates:

```text
Harrier Statement top-50
  ↓
BGE v2-m3 OR zerank-2
  ↓
reranked Statements
  ↓
first occurrence / bounded Statement→Object grouping
```

Frozen candidates:

```text
BAAI/bge-reranker-v2-m3
revision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e

zeroentropy/zerank-2-reranker
revision 5eae30d5ee3c6b2df2ef6d723bde45172d761c4c
```

Measure:

```text
candidate Recall@50
Statement MRR / Recall@10 / nDCG@10
Statement→Object MRR / Recall@10 / nDCG@10
p50 / p95 rerank latency
peak allocated/reserved VRAM
```

Compare against the accepted first-stage R2 Hybrid/Object result.

Decision rule:

- reranker remains optional unless it provides a material Object-level quality gain that justifies its latency/resource/dependency cost;
- no production reranker adoption is made inside N-06; a positive adoption decision requires a separate implementation/design task.

### N06-F — 100k Exact vs Qdrant ANN acceptance

Rebuild the 100k benchmark from embeddings produced by the active R2 frozen gold generation. Do not source the fixture from a legacy v1-only `object_overall` materialization.

Fixture policy remains deterministic:

```text
100,000 vectors
1024 Float32
24 query directions
8 hard-filter partitions
NumPy Float32 cosine = Exact reference
3-way weighted mixture of real frozen R2 gold vectors + Gaussian noise
noise sigma = 0.005
```

Qdrant profile is frozen for acceptance:

```text
Qdrant 1.19.2
m = 16
ef_construct = 128
hnsw_ef = 768
full_scan_threshold = 10
```

Do not tune ANN parameters inside the formal acceptance run.

Measure:

```text
Exact unfiltered p50 / p95
Exact filtered p50 / p95
Qdrant unfiltered p50 / p95
Qdrant filtered p50 / p95
mean and minimum Recall@10
initial build time
full rebuild time
incremental update 100 points
indexed point count
collection disk bytes
Qdrant process memory where available
```

Acceptance:

- indexed point count = 100,000;
- unfiltered mean Recall@10 >= 0.99;
- filtered mean Recall@10 >= 0.99;
- minimum per-query Recall@10 >= 0.90 for both modes;
- build, update, filtered query, unfiltered query and full rebuild all complete without hidden error;
- no payload/generation/filter identity violation;
- no parameter tuning after seeing the formal result.

Latency, memory and disk are recorded as operational measurements, not independent hard FAIL gates unless execution becomes invalid or unsafe.

## 4. Resource observations

N-06 records retrieval/vector resource characteristics, not N-05 end-to-end processing performance.

At minimum record:

```text
Search harness CUDA max allocated/reserved
reranker CUDA max allocated/reserved
Qdrant index disk bytes
Qdrant process working set/RSS if practical
100k build/rebuild/update times
retrieval p50/p95
```

N-05 formal performance results remain separate and are not recomputed here.

## 5. Canonical / derived safety

N-06 must use isolated evaluation artifacts or copies.

Require:

```text
production/reference canonical state unchanged
N-03 preserved canonical DB unchanged
active production/reference pointer not changed
sample/benchmark Qdrant namespaces isolated
tracked repository state unchanged during measured runs
```

Derived benchmark collections may be created/deleted only inside their dedicated N-06 namespace/root.

## 6. Deterministic verdict

N-06 returns one of:

```text
PASS
FAIL
BLOCKED
```

PASS requires all mandatory quality/contract gates and the ANN acceptance gates to pass with complete evidence.

FAIL means valid evidence shows a mandatory quality/ANN gate violation.

BLOCKED means environment, missing evidence, runtime failure, or harness incompatibility prevents a judgeable result.

Do not reinterpret FAIL as BLOCKED or vice versa.

## 7. Regression gate

After measured execution require:

```text
focused N-06 tests PASS
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
canonical invariance PASS
```

New benchmark/harness code must have focused deterministic tests.

## 8. Deliverables

Create/update at minimum:

```text
benchmark/n06-retrieval-vector-quality-contract-v1.json
docs/evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md
benchmark/results/n06-retrieval-vector-quality.json
N-06 benchmark/harness code + focused tests
Phase N current-state documentation
```

Raw benchmark logs, model caches, temporary DB copies and Qdrant storage remain under `.local/n06/` and are not committed.

## 9. Final state transition

If PASS:

```text
N-06 = Complete / PASS
N-07 = Next / Pending
Phase N = Active / Not Complete
```

If FAIL:

```text
N-06 = Complete / FAIL
Phase N = Active / Not Complete
```

Create an explicit remediation/design task; do not silently tune production ranking/model/backend.

If BLOCKED:

```text
N-06 = BLOCKED / Not Complete
```

isolate the blocker and stop.

## 10. Formal completion / next action

Formal run `20261024T155932+0900`, source HEAD
`3956de51ab00b3970595e5d359ca05b681523890`, completed stages A-H.
Deterministic evaluator: PASS. Synthetic contracts 5/5, R2SIM 6/6,
Statement R@10 1.0, supported N-03 Semantic/Hybrid R@10 1.0.
100k indexed points: unfiltered and filtered mean/min Recall@10 1.0/1.0,
payload identity violations 0. Canonical, preserved N-03, reference Qdrant,
measurement HEAD/tracked state and all three R1 assets unchanged.
Post-run focused 20 / full 689 passed; Ruff and diff PASS.
Rerankers remain optional; no production tuning or integration was performed.

Result: `docs/evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md`.
Aggregate: `benchmark/results/n06-retrieval-vector-quality.json`.
Historical BLOCKED attempt and all raw evidence remain under `.local/n06/`.

```text
N-06 = Complete / PASS
N-07 = Next / Pending
Phase N = Active / Not Complete
```

N-07 was not started in this task.
