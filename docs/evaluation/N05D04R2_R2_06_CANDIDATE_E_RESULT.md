# R2-06 Candidate E — Reference Workstation remediation result

Updated: 2026-10-24

Status: **Candidate E accepted / implementation runtime verified on remediation branch**.
Branch: `r2-06-similarity-regression-review`.
Execution baseline: `4ec0cf3b80102098671ddda8275094226dd9c638`.
Run: `20261024T020709`. Raw local artifacts remain under `.local/r2-06-facet-median-ablation/20261024T020709/`.
Machine-readable result: `benchmark/results/n05d04r2-r2-06-candidate-e-remediation.json`.

## Formula and boundary

For each same-Facet anchor in the pinned active generation/current accepted
candidate Version, retain all observations from selected source Statement queries,
after existing best-point-per-source-query/Object deduplication. No score top-k.
Statement mean is the arithmetic mean of those bounded cosines.
With Statements: cluster=(.30*Facet+.20*Statement mean)/.50.
Without observed Statements: cluster=Facet cosine. No anchor: no cluster.
Detail is ordinary median of all eligible clusters (middle value for odd count;
arithmetic mean of the middle two for even count). Final=.50*overview+.50*detail.
Shared-Facet count is support metadata, not a multiplier or reliability estimate.

Only the R2 overall scorer changed. Acquisition channels/source selection/ANN
limits/generation routing, Facet-specific raw cosine, v1 compatibility, canonical
Knowledge, representation text and R2-05 fusion are unchanged. Harrier OSS v1 0.6B
revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, CUDA/bfloat16, dimension1024,
normalization and reject/no-truncation remain fixed. Offline harness used only the
existing local cache; no package/model/runtime update or reconfiguration occurred.

## Exact frozen cases and median support

| Case | Rank 1 / score | Rank 2 / score | Median-support Facets |
|---|---|---|---|
| Character overall | Mika .8312071178407453 | Ren .8279432931429531 | Mika values; Ren values/personality |
| Character values, unchanged Facet cosine | Mika .8341502142144167 | Ren .8149387351704018 | requested values Facet |
| Work | Ash Garden .857757151406386 | Iron Crown .8314102208486642 | Ash themes; Iron themes/tone |
| Concept | Altruism .8256451816438397 | Autonomy .8153550453798410 | Altruism definition; Autonomy definition/implications |

All cluster scores, anchor IDs, means, support order and actual public evidence
are retained in the result. Production scores match immutable saved-hit replay.
Overall frozen quality: MRR=1, Recall@1=1, Recall@10=1, nDCG@10=1.
Facet-specific quality remains1. No frozen gold/assertion was weakened.

## Structural diagnostics E1-E12

All12 PASS under the handoff's stated boundaries; E10/E11 include explicit
report-only observations and do not assert universal support-count invariance.

- E1/E2: weak/strong insertion into the same Facet changes its mean in the required
  direction. [.9,.8,.1] -> .6; append .5 -> .575, retaining all four observations.
- E3/E4: no score eviction; duplicate candidate points from one query do not add
  observations. Real retrieval regressions additionally cover duplicates/order.
- E5: deliberately withhold Facet/overview ANN while retaining Statement discovery;
  canonical anchor recovered with1 lookup,2 stored reads,1 direct cosine. Real
  public Similarity operation also succeeds without an ANN Facet identity.
- E6: negative disposable generation fixture leaves Statement discovery but removes
  its canonical Facet link. No detail cluster/authority is created.
- E7/E8: weak/strong cross-Facet insertion respectively cannot raise/lower median.
- E9: exact symmetric .7/.9 null enumeration: expected Object scores .8/.8;
  wide wins64, losses64, ties128, out of256.
- E10: two fixed asymmetric probability-mass controls, no fitted parameter:

| Low/high multiplicity | Narrow expectation | Wide expectation | Win / loss / tie (65536 weighted outcomes) |
|---|---:|---:|---|
| 3 / 1 | .775 | .7570556640625 | 3468 / 15228 / 46840 |
| 1 / 3 | .825 | .8429443359375 | 15228 / 3468 / 46840 |

Median's finite-support expected value shifts under skewed laws; this is not
hidden. It is bidirectional and has genuine wins AND losses, unlike D/P8's
one-sided maximum dominance. The handoff explicitly allows this finite-sample
observation; no universal Facet-count invariance or empirical Harrier noise law
is claimed. No formula tuning followed.

- E11: equal overview .8, one genuinely high Facet .95 gives Object .875 versus
  four moderate Facets .8 giving Object .8. Counts1/4 are exposed. Sparse support
  has greater uncertainty; the score is typical observed similarity, not confidence.
  As specified, a genuinely higher one-Facet score is not automatically rejected.
- E12: Statement/Facet permutation invariance PASS.

## Boundedness and local work

Frozen acquisition constants unchanged: source Facet<=8, Statement<=12,
ANN calls<=21, raw slots<=464; public results<=128 AFTER full union scoring.
There is no new pre-ranking shortlist.

Cardinality-only synthetic unit-vector fixture (not Harrier quality/performance):
164 distinct Objects scored,128 exposed;5 calls with limits128/24/24/12/12,
200 raw slots;328 candidate anchor lookups,282 memoized embedding reads,
280 direct Facet cosines,48 reused ANN cosines. Production counts match the
pre-implementation experiment. Max clusters2, observations per Facet1/Object2,
median input2, numerical evidence4 items (unobserved overview is not fabricated).
The dedicated twelve-query fixture retains/explains all12 observations in one
Facet:14 raw numerical evidence items with a real overview and Facet anchor.

Conservative envelopes from existing upstream bounds: union<=464; relevant Facet
keys<=20 (8 Facet queries plus12 Statement query Facets); candidate anchor reads
and direct cosines<=9280; source Facet resolutions<=20; memoized embedding reads
<=9300; clusters/median inputs<=20 per Object; all observations<=12 per Object,
and therefore<=12 per Facet. Median-support numerical evidence<=15 plus<=20
bounded cluster summary rows. These are per-operation bounds, not new quality
parameters. Read/cache and scalar dot-product work is finite and acceptable for
this diagnostic; it is not formal N-05 latency acceptance or a 4090 throughput
claim. R2-09 must later measure performance. No unbounded Statement cross-product.

## Explanation/API compatibility

Existing service arguments, public base dataclasses and core result fields are
unchanged. R2 evidence carries additive `facet_median` metadata: all eligible
cluster scores/anchor IDs, count, observation counts/means, middle Facets and
both top-level contributions. Raw evidence for every observation used by the
median-support Facets remains present; its contributions sum to the result score.
No score-relevant observation is evicted. Source-query-selected Facets outside
the eight Facet ANN queries are also resolved canonically. A recovered anchor
need not itself be an ANN hit: existing identity fields use an already-validated
acquisition membership. Statement discovery without any eligible detail carries
zero contribution and no fabricated cluster. v1/Facet-specific payloads unchanged.

## Character sensitivity

48 independent perturbations over12 overview/Facet/Statement values:

| Delta | Trials | Rank flips | Median-support changes |
|---|---:|---:|---:|
| -.010 | 12 | 1 | 1 |
| -.005 | 12 | 0 | 0 |
| +.005 | 12 | 0 | 0 |
| +.010 | 12 | 1 | 1 |

Both rank flips are overview perturbations (Mika -.010, Ren +.010). Support changes
are separately recorded; no formula adjustment followed these observations.

## Production verification

```text
python -m pytest -q tests/test_object_similarity.py tests/test_object_similarity_r2.py tests/test_object_similarity_facet_median.py tests/test_n05d04r2_search_quality_acceptance.py
  41 passed
R2SIM-G01..G06 mapped tests
  6/6 PASS, unchanged expectations
R2-08 focused set plus new Candidate E tests
  99 passed
python -m pytest -q
  654 passed, 0 failed, 0 skipped
python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only --cache <existing-local-cache>
  automatic PASS; no formal R2-08 Complete declaration
python -m compileall -q src tests scripts
  PASS
python -m ruff check src tests scripts
  PASS
python -m ruff format --check <three changed Python files>
  PASS
git diff --check
  PASS
```

R2-05 all24 Semantic/Hybrid rankings AND case metrics match the verified parent
exactly. Semantic MRR1 / nDCG@10 .9930829680165895; Hybrid MRR1 / nDCG@10 1.
22 Statement retrieval queries,5 filter/version/temporal contracts, Evidence
Search, Facet-specific Similarity, Application/CLI/MCP, same/cross class,
current/history/generation, source exclusion, payload and SQLite membership
integrity regressions PASS. Single-generation audit PASS, active overall leakage0.

Known unrelated repository-wide `benchmark/tools/n05_resource_preflight.py:69 E501`
is unchanged. All3 original R1 SHA-256 values match before/after; their modified/
untracked state remains untouched. No production canonical DB, Qdrant namespace
or reference active pointer changed. One manual explanation check initially
imported the original workspace via shared editable venv; its invalid artifact
is excluded, retained locally and superseded by an explicit-worktree import check.
The actual verification workers and pytest use the correct worktree import path.

## State

R2-06 Candidate E remediation = Complete / runtime verified on branch.
R2-08 = Not Complete; the former Similarity defects are repaired on this branch,
but formal re-acceptance review/closure remains separate. Prior FAIL is not closed.
R2-09 = blocked / Not Started. N-05 remains BLOCKED / Not Complete.
No main merge, reference runtime cutover or formal N-05 timing was performed.
