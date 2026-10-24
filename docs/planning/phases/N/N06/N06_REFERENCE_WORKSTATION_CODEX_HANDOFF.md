# N-06 — Retrieval / Vector Quality — Codex Handoff

Updated: 2026-10-24

## 1. Task

Execute `N-06 [P0] — Retrieval / Vector quality` on the Reference Workstation.

Canonical inputs:

```text
docs/planning/phases/N/N06/N06_RETRIEVAL_VECTOR_QUALITY_ACCEPTANCE.md
benchmark/n06-retrieval-vector-quality-contract-v1.json
docs/evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md
docs/evaluation/N05D04R2_R2_08_FORMAL_REACCEPTANCE.md
docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
benchmark/n03-real-data-vertical-slice-v1.json
```

Do not start N-07.

## 2. Local-work ownership

All filesystem, terminal, model, GPU, Qdrant and local DB operations are owned by Codex.

Use an isolated clean clone/worktree if the normal workspace contains historical R1 local assets or uncommitted evidence. Preserve those assets byte-for-byte.

## 3. Start state

Synchronize to the latest `origin/main`.

Require:

```text
branch = main
HEAD == origin/main
git status --porcelain = empty
```

Record exact HEAD before implementation and again before formal measurement.

## 4. Existing harness compatibility review

Before writing code, inspect:

```text
scripts/run_search_quality_gold.py
scripts/run_vector_backend_benchmark.py
scripts/run_search_gold_reranker_benchmark.py
benchmark/n05d04r2-search-quality-acceptance-v1.json
benchmark/n05d04r2-object-similarity-gold-v1.json
current R2 generation/maintenance APIs
```

Important known issues:

1. `scripts/run_search_quality_gold.py` is historical I-07 and materializes v1 `object_overall`; it is not sufficient as the N-06 R2 runner.
2. `scripts/run_search_gold_reranker_benchmark.py` directly reads `object_overall` for object-level reranking; do not use that branch as N-06 R2 evidence.
3. `scripts/run_vector_backend_benchmark.py` derives its 100k fixture from whichever gold DB was prepared; for N-06 the source DB must be active R2 and contain zero active `object_overall` leakage.

Reuse algorithms/helpers where safe, but implement N-06-specific orchestration rather than weakening the R2 contract.

## 5. Required implementation

Create an N-06 benchmark/evaluator path with focused tests.

Recommended files:

```text
benchmark/tools/n06_retrieval_vector_quality.py
benchmark/tools/n06_evaluate_retrieval_vector_quality.py
tests/test_n06_retrieval_vector_quality.py
```

Additional helper modules are allowed if they reduce duplication.

Do not modify production search/scoring behavior to make the benchmark pass.

### 5.1 R2 frozen-gold builder

Build the historical search-gold canonical fixture, then materialize it through the accepted R2 generation-aware path:

```text
active contract = n05d04r2-hierarchical-v2
membership kinds = object_overview / facet / statement
active object_overall memberships = 0
provider.space = frozen Harrier space
Qdrant/evaluation namespace = isolated N-06 namespace
```

Do not call legacy `materialize_version()` as the active path.

### 5.2 Synthetic quality evaluation

Run all channels/gates in the frozen N-06 contract and emit per-case rankings plus aggregate metrics.

Use the accepted Candidate E Overall Similarity semantics already in production code; do not reproduce its formula in benchmark-only code.

### 5.3 N-03 real-data evaluation

Locate the completed N-03 evaluation DB from the original workspace. Verify its checksum/state before use.

Copy it into `.local/n06/` and operate on the copy only.

If the N-03 DB is unavailable, do not reconstruct its canonical Knowledge from external web sources. Return `BLOCKED_N03_ASSET_UNAVAILABLE` with evidence.

Use `benchmark/n03-real-data-vertical-slice-v1.json` and the human ground-truth notes in `docs/evaluation/N03_REAL_DATA_VERTICAL_SLICE.md` as the only judgement source.

Bring derived search state on the copy to the accepted active R2 contract without changing canonical Knowledge.

Evaluate the frozen expected queries and record every ranking.

### 5.4 Statement channel ablation

Do not mutate canonical data or delete stored Statement representations.

Implement the ablation by constructing an evaluation index/retrieval configuration that excludes Statement points from Object-level semantic fusion while leaving direct Statement Search available.

Compare full R2 vs overview+Facet on exactly the same query set/order.

### 5.5 Reranker study

Do not perform direct `object_overall` reranking.

Use:

```text
Harrier Statement top-50
→ BGE or zerank-2 rerank
→ bounded first-occurrence Statement-to-Object grouping
```

Measure both models under their frozen revisions.

If a model is absent from the local cache and network download is required, record that fact. Downloading the exact frozen public model revision is allowed for this evaluation if normal project policy permits it; do not substitute another reranker.

Reranker results are evaluation-only. Do not wire either model into production search in N-06.

### 5.6 100k ANN

Generate the 100k vectors from active-R2 frozen-gold embeddings.

Use the frozen Qdrant profile exactly:

```text
m=16
ef_construct=128
hnsw_ef=768
full_scan_threshold=10
```

Do not tune after observing the result.

Use an N-06-specific collection name/storage namespace; never delete or reuse production/reference collections.

Record exact-reference and Qdrant rankings per query so minimum Recall@10 is independently auditable.

## 6. Mandatory focused tests before expensive execution

At minimum test:

```text
1. R2 gold bootstrap selects object_overview/facet/statement only
2. active object_overall leakage is zero
3. generation ID/payload/membership identity agrees
4. unsupported/wrong generation fails closed
5. Statement ablation excludes only Object-level Statement channel
6. direct Statement Search remains enabled in ablation
7. reranker candidate path never reads object_overall
8. Statement-to-Object grouping is deterministic
9. 100k fixture source vectors come from active-R2 generation
10. ANN recall evaluator uses Exact top-10 reference correctly
11. filtered Exact/Qdrant use the same filter partition
12. PASS/FAIL/BLOCKED verdict is deterministic
13. N-03 preserved source DB is never opened for mutation
14. production/default Qdrant namespace is never targeted
```

## 7. Preflight

After implementation and focused tests, before formal measurement:

```text
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS.

Record:

```text
nvidia-smi
Qdrant health/version
free disk
physical/virtual memory
Python/PyTorch/CUDA/transformers/sentence-transformers/qdrant-client versions
```

Material competing CUDA workload is a blocker. Do not terminate unrelated processes automatically.

## 8. Formal execution order

Use one new N-06 run ID under:

```text
.local/n06/<run_id>/
```

Execute without changing parameters between stages:

```text
A preflight snapshot
B R2 synthetic Search gold
C N-03 real-data retrieval
D Statement Embedding ablation
E BGE + zerank-2 reranker study
F 100k Exact vs Qdrant ANN
G deterministic evaluator
H post-run safety/regression
```

If one mandatory stage is BLOCKED, preserve evidence and stop before later expensive stages unless the later stage is explicitly independent and the result document clearly separates it. Never fabricate a complete verdict from partial evidence.

## 9. Formal gates

Use `benchmark/n06-retrieval-vector-quality-contract-v1.json` as the machine-readable authority.

In particular:

```text
synthetic exact identity = 1.0
synthetic Semantic R@10 = 1.0
synthetic Hybrid R@10 = 1.0
synthetic Hybrid MRR = 1.0
synthetic Statement R@10 = 1.0
R2SIM = 6/6
active object_overall leakage = 0

N-03 supported Semantic target R@10 = 1.0
N-03 supported Hybrid target R@10 = 1.0
identity rank1 required

ANN unfiltered mean R@10 >= .99
ANN filtered mean R@10 >= .99
ANN min per-query R@10 >= .90 in both modes
indexed points = 100000
identity violations = 0
```

Reranker and Statement ablation are decision evidence; they do not have an arbitrary mandatory quality-improvement threshold.

## 10. Post-run safety

Require:

```text
preserved N-03 canonical DB before/after checksum or normalized full-table digest unchanged
production/reference canonical state unchanged
production/reference Qdrant state unchanged
tracked HEAD/state unchanged during measurement
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
historical R1 asset hashes unchanged if those assets exist
```

## 11. Result publication

Create:

```text
docs/evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md
benchmark/results/n06-retrieval-vector-quality.json
```

Update:

```text
docs/planning/phases/N/N06/N06_RETRIEVAL_VECTOR_QUALITY_ACCEPTANCE.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
```

If PASS, state:

```text
N-06 = Complete / PASS
N-07 = Next / Pending
Phase N = Active / Not Complete
```

Do not mark Phase N Complete.

## 12. Git policy

Implementation may be performed on a dedicated branch, e.g.:

`n06-retrieval-vector-quality`

After all formal evidence is complete and reviewed, commit/push the implementation/result set. Do not merge a failing or blocked experiment into `main` unless the result/diagnostic record itself is intentionally being preserved and the code is safe/non-production benchmark infrastructure.

Do not start N-07.

## 13. Final report

Return at least:

1. measured git HEAD;
2. preflight/runtime versions;
3. synthetic Search metrics and contract results;
4. N-03 real-data metrics and failed-query classifications;
5. Statement ablation delta;
6. direct Statement Search metrics;
7. BGE reranker metrics/latency/VRAM;
8. zerank-2 metrics/latency/VRAM;
9. reranker production-adoption recommendation (`remain optional` or `open separate adoption study` only);
10. 100k Exact latency;
11. Qdrant unfiltered/filtered p50/p95 and mean/min Recall@10;
12. build/rebuild/update/disk/process-memory observations;
13. generation/payload/namespace audit;
14. canonical/N-03/Qdrant safety result;
15. full regression/Ruff/diff;
16. result artifact paths;
17. commit SHA/push state;
18. final N-06/N-07/Phase N state.
