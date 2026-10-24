# N-06 Retrieval / Vector Quality — Reference Workstation Result

Updated: 2026-10-24

- Formal verdict: **PASS** (deterministic evaluator, all checks true).
- N-06 = **Complete / PASS**; N-07 = **Next / Pending**; Phase N = **Active / Not Complete**.
- Run: `20261024T155932+0900`; measured clean branch: `n06-retrieval-vector-quality`.
- Measured source HEAD: `3956de51ab00b3970595e5d359ca05b681523890`; baseline main: `10b6604e78d225b51d63e9591d09386b38966925`.
- Authority: `benchmark/n06-retrieval-vector-quality-contract-v1.json` and `N06_REFERENCE_WORKSTATION_CODEX_HANDOFF.md`.
- Aggregate: `benchmark/results/n06-retrieval-vector-quality.json`.
- Local raw evidence: `.local/n06/20261024T155932+0900/` (not committed).

## Execution and runtime identity

Executed A preflight, B R2 synthetic gold, C copied N-03 retrieval, D Statement ablation,
E reranker study, F 100k Exact/ANN, G deterministic evaluation, H safety/regression,
in that order. The main-based implementation branch was committed and clean before
formal measurement. Preflight full pytest, repository Ruff, compile, changed-file
format and diff checks all passed. Free disk before execution: 101.924 GiB.

Windows 11; Python 3.10.6; RTX 4090; PyTorch 2.6.0+cu124 / CUDA 12.4;
Transformers 5.20.1; sentence-transformers 6.1.0; qdrant-client 1.19.1;
Qdrant server 1.19.2 using the accepted external-storage runtime.
No material competing CUDA workload was present at preflight.

Harrier: `microsoft/harrier-oss-v1-0.6b`, revision
`f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, CUDA / bfloat16,
1024 dimensions, normalized vectors, overflow reject, no truncation or CPU fallback.
Active contract: `n05d04r2-hierarchical-v2`; families are `object_overview`, `facet`,
`statement`. Existing exact cached models were used without downloading replacements.

## B — Synthetic R2 gold

24 Object queries:

| Mode | MRR | R@1 | R@10 | nDCG@10 | p50 / p95 ms |
|---|---:|---:|---:|---:|---:|
| lexical | 0.166666667 | 0.145833333 | 0.145833333 | 0.157798108 | 0.525 / 0.807 |
| semantic | 1.000000000 | 0.854166667 | 1.000000000 | 1.000000000 | 39.030 / 59.613 |
| hybrid | 1.000000000 | 0.854166667 | 1.000000000 | 1.000000000 | 38.821 / 50.480 |

Exact identity accuracy = 1.0; filter/version/temporal contracts = 5/5;
existing Overall/Facet Similarity = 4/4; R2SIM-G01..G06 = 6/6;
Evidence Search = 3 cases across lexical-association and semantic paths, 6/6.
Similarity and Evidence MRR/R@10/nDCG@10 = 1.0. Active `object_overall` leakage = 0.

Direct Statement retrieval (22 frozen queries): MRR = 1.0,
R@1 = 0.8636363636363636, R@5/R@10 = 1.0,
nDCG@10 = 0.9927018899225625; p50/p95 = 28.858 / 33.933 ms.
Top-10 request timing is separate from the reranker top-50 candidate acquisition.

All strict Phase-I comparable gates passed. Semantic nDCG@10 increased from the
historical displayed 0.993 to 1.0; Overall Similarity MRR increased from displayed
0.833 to 1.0. The review flags for Statement R@1 versus displayed 0.864 and nDCG
versus displayed 0.993 are rounding artifacts: all 22 case-level metric dictionaries
exactly match accepted R2-08 at full precision. Unexplained comparable negative
deltas = 0. The flags and original evaluation evidence were retained, not edited.
Local `comparability-review.json` records each comparison.

## C — N-03 real data

Six Objects, 20 queries; the original evaluation DB was copied using SQLite backup.
Canonical input was not reconstructed from Web sources.

| Mode | MRR | R@1 | R@10 | nDCG@10 | p50 / p95 ms |
|---|---:|---:|---:|---:|---:|
| lexical | 0.900000000 | 0.900000000 | 0.900000000 | 0.900000000 | 0.687 / 1.018 |
| semantic | 0.929166667 | 0.900000000 | 1.000000000 | 0.946533828 | 61.512 / 105.742 |
| hybrid | 0.937500000 | 0.900000000 | 1.000000000 | 0.953080316 | 58.977 / 91.870 |

Required identity rank-1 and supported-target Semantic/Hybrid R@10 = 1.0;
current/generation leakage = 0. Lexical misses `saber:2` (King of Knights) and
`tsundere:2` (character archetype) are canonical wording coverage limitations:
independent inspection found the target's current R2 text lacks all required query
terms. No Knowledge was supplemented to repair these observations.

The small real-data set is ecological evidence, not a population-wide quality
claim. N-03 has no per-query Statement relevance gold; direct Statement rankings
were saved without inventing relevance labels.

## D — Statement Embedding ablation

The isolated ablation disables only Statement contribution to Object semantic
candidate acquisition; direct Statement retrieval remains enabled. Production
ranking was not modified.

| Dataset | Full MRR | Without Statement MRR | MRR gain | R@1 gain | nDCG@10 gain |
|---|---:|---:|---:|---:|---:|
| Synthetic, 24 | 1.000000000 | 0.972222222 | +0.027777778 | +0.041666667 | +0.020833333 |
| N-03 content, 10 | 0.858333333 | 0.853333333 | +0.005000000 | 0 | +0.004382375 |

R@10 remains 1.0 in both configurations. The observed marginal Object quality gain,
in addition to direct Statement retrieval, supports retaining Statement Embedding.
Raw case-level full/ablated rankings remain in `evidence.json`.

## E — Optional reranker study

Harrier Statement top-50 -> reranked Statements -> deterministic first-occurrence
Statement-to-Object grouping. Candidate Recall@50 = 1.0 for both models (22 cases).
No direct `object_overall` reranking or production reranker integration was used.

| Reranker | Statement MRR / R@1 / nDCG@10 | Grouped Object MRR / nDCG@10 | p50 / p95 ms | CUDA allocated / reserved GiB |
|---|---|---|---:|---:|
| BGE v2-m3 | .977272727 / .840909091 / .979262332 | 1 / .990446446 | 19.904 / 57.983 | 2.209 / 2.230 |
| zerank-2 | 1 / .863636364 / .996350945 | 1 / 1 | 36.068 / 148.094 | 9.090 / 9.314 |

Both have Statement R@5/R@10 = 1.0 and grouped Object R@1 = .840909091,
R@5/R@10 = 1.0. Pinned identities:

- `BAAI/bge-reranker-v2-m3`: `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`.
- `zeroentropy/zerank-2-reranker`: `5eae30d5ee3c6b2df2ef6d723bde45172d761c4c`.

CUDA peaks include resident Harrier and are not isolated model-weight sizes.
Recommendation: **remain optional**. There is no observed Object MRR gain over the
baseline; zerank-2 has a small Statement nDCG gain with additional latency/memory.
No production adoption or separate adoption study was started.

## F — 100k Exact versus Qdrant ANN

Source: 109 active-R2 gold embeddings, not legacy v1 `object_overall`.
Fixture uses the frozen deterministic Float32 mixture/noise construction. Namespace
`n068e741083cb5c_100k`; indexed points = 100000. Fixed profile:
`m=16`, `ef_construct=128`, `hnsw_ef=768`, `full_scan_threshold=10`.
No parameter was tuned after observing formal results.

| Mode | Exact p50 / p95 ms | ANN p50 / p95 ms | Mean / minimum Recall@10 |
|---|---:|---:|---:|
| Unfiltered | 104.365 / 131.453 | 7.293 / 11.652 | 1.0 / 1.0 |
| Filtered | 14.134 / 19.392 | 5.760 / 10.085 | 1.0 / 1.0 |

24 query directions x 3 repeats = 72 observations per mode; query/repeat and filtered
partition identity were independently checked. All 100000 live payloads were also
independently scrolled: no missing/duplicate IDs or fixture/scope/generation/space
violations. Initial build 65.431714 s; full rebuild 46.313927 s; update 100 points
0.076497 s; disk 645081069 bytes (615.197 MiB).
Qdrant process working-set snapshot: 1188618240 bytes (1133.555 MiB); this includes
existing collections and is not a collection-local or peak memory estimate.
Search-phase CUDA allocated/reserved peaks: 1271455744 /
1312817152 bytes.

## Generation, safety and independent review

Gold generation: `search-generation:r2:230f8ff2-926f-42d4-845a-e8752f5636b6`;
109 memberships; membership digest:
`e9bc4493ffb79a7ee38b50b701c2d47a0ada04d2763bac8c2181e8a63c75807d`.
The N-03 copy has its own R2 generation/namespace. Generation payloads and canonical
membership identity were validated before using Statement hits. Only run-owned
successful ANN collections were rebuilt. Original/reference Qdrant collection
counts and full reference point fingerprints matched before/after.

All H safety checks PASS: original canonical state unchanged, preserved N-03 source
unchanged, reference Qdrant unchanged, measurement HEAD/tracked state unchanged,
and all three original R1 user-aborted asset SHA-256 values unchanged.
Local `independent-review.json` and `comparability-review.json` preserve additional
100k payload, lexical-miss and Statement full-precision comparisons.

## Engineering checks and issue found

Preflight and post-run full pytest: **689 passed, 0 failed**.
Post-run focused N-06 tests: **20 passed**. Post-run full runtime 175.37 s;
focused runtime 1.73 s. Two existing warnings were reported.
Repository-wide Ruff and `git diff --check` passed; compile and changed-Python-file
format checks passed before measurement. Post-run command return codes are stored
in stage H. Documentation-only publication checks follow the same successful source
verification; raw logs are retained locally.

Historical run `20261024T154215+0900` at source
`187abacbdf9190443e8634d1197af9f262e65996` was BLOCKED in B: the direct Statement
benchmark helper incorrectly depended on a Hybrid request context already reset by
the preceding search. The helper now resolves and pins one R2 generation and checks
payload/membership integrity. Two focused checks cover context reset and corrupt
payload rejection. This was a harness-only correction; models, quality gold,
production scoring and formal gates were unchanged. The failed attempt remains
intact. The corrected source was committed before this fresh A-H run.

## Artifacts and completion decision

Local evidence directory contains `evidence.json`, `evaluation.json`,
`quality-evaluation.json`, preserved before/after canonical/reference fingerprints,
`statement-candidates.json`, both reranker results, ANN rankings, R2SIM logs,
`post-focused.log`, `post-full.log`, `post-ruff.log`, `post-diff.log`, and the two
independent review sidecars. Temporary DBs, logs, caches and raw text are not Git
artifacts. The published aggregate contains metrics, identities, gates and safety
results only.

The deterministic evaluator returned PASS after H; all formal gates and independent
safety checks agree. **N-06 = Complete / PASS. N-07 = Next / Pending. Phase N remains
Active / Not Complete.** N-07 has not been started.
