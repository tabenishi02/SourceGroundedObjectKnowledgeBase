# N05D-04R2 / R2-05 — Semantic Remediation Reference Workstation Handoff

Updated: 2026-10-23

Status: **Local diagnostic / bounded ablation required**

Authority:

```text
docs/evaluation/N05D04R2_R2_05_SEMANTIC_REGRESSION_ROOT_CAUSE_REVIEW.md
benchmark/search-quality-gold-v1.json
benchmark/n05d04r2-search-quality-acceptance-v1.json
scripts/run_n05d04r2_search_quality_acceptance.py
docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md
```

Do not start R2-06 remediation or R2-09 from this handoff.

## 1. Base and safety

Use branch:

```text
r2-05-semantic-regression-review
```

The branch was created from R2-08 candidate HEAD
`62b54658469814d55d63f67bddf2358f9444115d` and contains the review document.
Resolve the branch's current remote HEAD before work; do not assume a stale SHA.

Before checkout/pull/reset in the original workspace:

1. record `git status`, `git diff`, current branch and HEAD;
2. identify the three preserved R1 user-aborted assets used by R2-07/R2-08;
3. record their SHA-256 values;
4. do not overwrite, clean, reset, stage or commit those assets;
5. prefer a separate clean verification worktree.

No production/reference canonical DB mutation is required for the diagnostic.
Use the synthetic R2-08 quality fixture unless a step explicitly requires
read-only comparison against preserved evidence.

## 2. Frozen runtime

The following are immutable for this task:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
CUDA / bfloat16
dimension: 1024
normalization: unchanged
truncation: prohibited
```

Do not introduce:

- Harrier 270M or another model;
- CPU fallback;
- FlashAttention-2;
- PyTorch/CUDA update;
- tokenizer/model revision change;
- representation truncation;
- canonical Knowledge changes.

## 3. Reproduce the failed case first

Re-run only enough of the fixed R2-08 harness to reproduce:

```text
case: short_japanese_love
query: 愛
expected: obj:mika
current R2 observed rank: 3
```

Do not change code before the current contribution decomposition is captured.

For Mika and every Object currently above Mika, record each semantic family:

```text
object_overview
facet
statement
```

For each family record:

```text
representation_id / membership_id
facet / statement identity when applicable
raw cosine
representation-level source_rank
bounded hits admitted by the current cap
channel-local reciprocal-rank contribution
channel-local Object rank
final cross-channel RRF contribution
```

Also record the final Object fused score/rank.

If practical with the preserved fixture/Embedding Space, capture the same
Phase-I `object_overall` decomposition for the query. It is useful evidence but
must not block the R2 diagnostic if the historical point-level trace is not
available without rebuilding unrelated state.

## 4. Confirm the causal claim

The diagnostic must answer these questions explicitly:

1. Do Facet and Statement individually place/support Mika above the final
   distractors?
2. Which overview Object rank/contribution causes each final inversion?
3. Does the inversion occur only at the final cross-channel RRF stage, or is
   there already a channel-local aggregation anomaly?
4. Are any candidate/version/generation/filter mistakes involved?
5. Is active `object_overall` leakage exactly zero?

If question 3 shows the primary failure is inside Facet/Statement channel-local
aggregation rather than cross-channel fusion, stop and report that the desk
review's selected remediation direction must be revisited. Do not force the
weighted-inner-fusion hypothesis.

## 5. Bounded remediation ablation

Do not begin with permanent production code changes. Implement an isolated
experiment/helper or narrowly parameterized test path so candidate fusion rules
can be compared against the same captured hits.

Control:

```text
current equal-channel Object-rank RRF
```

Required candidate A — role-aware weighted semantic RRF:

```text
inner_semantic_score =
    w_overview * 1/(60 + overview_object_rank)
  + w_facet    * 1/(60 + facet_object_rank)
  + w_statement* 1/(60 + statement_object_rank)
```

Start with:

```text
w_facet = 1.0
w_statement = 1.0
w_overview in {0.25, 0.50, 0.75}
```

This is a bounded design experiment. Do not run an unrestricted parameter
search.

For each candidate weight:

1. create one semantic Object rank from the inner score;
2. evaluate Semantic mode over all 24 frozen Object queries;
3. evaluate Hybrid mode over all 24 frozen Object queries using that single
   semantic Object ranking as the semantic input to outer Hybrid fusion;
4. record case-level rank/relevance changes, not only aggregate metrics.

If implementing the single-semantic-rank outer fusion solely for the experiment
is materially invasive, first run an inner-only rank simulation from captured
channel ranks, then implement the smallest isolated prototype required to verify
actual Search behavior. Do not commit a production algorithm before candidate
selection.

## 6. Overview-owned guard probes

The current frozen gold is not sufficient by itself to prove that lowering
`object_overview` authority preserves its unique semantic role. Add synthetic,
non-production probes that make the expected match depend on overview-owned
content rather than a duplicated content-Facet Statement body.

At minimum cover:

1. Structured Attribute semantic query;
2. Relation semantic query;
3. facet-less Summary semantic query.

The probe fixture must make the target distinguishable by the relevant overview
content and avoid placing the same decisive phrase in a content-Facet Statement.

These probes are remediation regression candidates. Keep them separate from the
frozen Phase-I gold unless the design is later approved to extend the formal
gold contract.

## 7. Selection rule

A candidate may be recommended only if:

```text
short_japanese_love                     restored
24-query Semantic quality               no unexplained regression
24-query Hybrid quality                 no unexplained regression
overview-owned probes                   PASS
exact identity                          unchanged
Facet no-fallback                       unchanged
temporal / derivation Statement scope   unchanged
current/history isolation               unchanged
generation isolation                    PASS
active object_overall leakage           0
```

Prefer the **largest overview weight** that satisfies the complete gate and is
stable at an adjacent tested setting. A candidate that passes only one exact
scalar while neighboring settings fail is not a stable design selection.

If none of `0.25 / 0.50 / 0.75` satisfies the complete gate, do not expand into
arbitrary tuning. Report the failure and evaluate a non-weighted semantic
sub-aggregation rule against the root-cause review before any production change.

## 8. Production implementation only after candidate selection

If one candidate is stable, implement the selected R2 semantic sub-aggregation
with these invariants:

- candidate generation still queries overview / Facet / Statement separately;
- generation and hard-filter behavior is unchanged;
- actual matches retain their public semantic channel identities;
- one internal semantic Object rank is produced;
- outer Hybrid fusion consumes that semantic rank without inventing raw-score
  comparability with lexical channels;
- exact identity tier remains unchanged;
- no overview fallback in Facet-scoped search;
- no change to R2-06 Object Similarity.

Add focused tests for:

- the failed semantic fusion shape;
- overview-owned Attribute/Relation/Summary cases;
- semantic result uniqueness/explainability;
- Hybrid behavior;
- existing generation/filter contracts.

## 9. Verification after implementation

Run at minimum:

```text
python -m pytest -q tests/test_hybrid_search.py tests/test_hybrid_search_r2.py
python -m pytest -q tests/test_n05d04r2_search_quality_acceptance.py
python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only
```

Then run the same focused R2-08 regression set and Windows full pytest used in
the failed R2-08 acceptance. Run compile, targeted Ruff, format check and
`git diff --check`.

Re-hash all three preserved R1 assets and prove start/end SHA-256 equality.

Do not repair the known unrelated repository-wide E501 by changing
`benchmark/tools/n05_resource_preflight.py` in this task.

## 10. Report

Return:

```text
branch / final HEAD
clean/dirty status
R1 asset SHA before/after
diagnostic trace for Mika and each higher-ranked Object
exact stage where rank inversion occurs
all candidate weight results
24 Semantic metrics + case deltas for each candidate
24 Hybrid metrics + case deltas for each candidate
overview-owned probe results
selected candidate or no-selection result
focused/full regression results
Ruff/format/diff results
Harrier/runtime identity
active object_overall leakage
```

If implementation was performed, also list the exact changed production/test
files and explain the contract change.

Do **not** mark R2-08 Complete. The R2-06 Overall Similarity regressions remain
unresolved. Do **not** start R2-06 remediation or R2-09.
