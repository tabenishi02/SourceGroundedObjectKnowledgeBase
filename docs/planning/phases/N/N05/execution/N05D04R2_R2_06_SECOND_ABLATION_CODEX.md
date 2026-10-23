# N05D-04R2 / R2-06 — Candidate C Second Ablation Codex Handoff

Updated: 2026-10-24

Use branch:

`r2-06-similarity-regression-review`

Read first:

1. `docs/evaluation/N05D04R2_R2_06_SECOND_DESIGN_REVIEW.md`
2. `docs/evaluation/N05D04R2_R2_06_SIMILARITY_REGRESSION_ROOT_CAUSE_REVIEW.md`
3. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md`

The first bounded remediation run rejected Candidate A and B. Do not reopen them and do not search new free parameters.

## Goal

Evaluate exactly one new architecture candidate:

**Candidate C — reciprocal-rank-discounted comparable-evidence pooling**.

No production implementation is allowed until the complete local acceptance boundary passes.

## Safety

Before local work:

- inspect current branch/HEAD/status/diff;
- preserve the three R1 user-aborted assets and record SHA-256 before/after;
- prefer an isolated clean worktree;
- do not touch canonical production DB or production Qdrant namespace.

Keep fixed:

```text
model = microsoft/harrier-oss-v1-0.6b
revision = f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
CUDA / bfloat16
dimension = 1024
normalization unchanged
truncation prohibited
```

Do not modify R2-05 Semantic remediation.

## Candidate C formula

For one overall Similarity component, after the existing same-Facet filtering, per-source-query Object deduplication, bounded cosine and evidence cap:

```text
admitted bounded scores sorted DESC:
c1 >= c2 >= ... >= cn

d_i = 1 / i

component_score = sum(d_i * c_i) / sum(d_i)
```

If there are no comparable admitted hits for a component, that component score is `0`.

Current caps mean:

```text
overview:  [1]
facet:     [1, 1/2]
statement: [1, 1/2, 1/3]
```

Outer weights stay exactly:

```text
overview=.50
facet=.30
statement=.20
```

No missing source slot is inserted into the denominator.

## Step 1 — exact same-hit replay

Using the saved first-run fixture/embedding space and exact existing hits where practical, replay:

- character_overall
- character_values
- work_overall
- concept_overall

Report exact component scores, weighted contributions, final scores and ranks for Candidate C.

Static design-review estimates are:

```text
character_overall
  Mika ~= .828969018
  Ren  ~= .828720797

work_overall
  Ash Garden ~= .857757151
  Iron Crown ~= .836515383

concept_overall
  Altruism ~= .825645182
  Autonomy ~= .816885737
```

Treat these only as cross-check values. Recompute from the actual saved evidence.

If exact replay contradicts the formula or does not restore all four frozen cases, stop before production code changes.

## Step 2 — required first-round probes

Candidate C must pass all four existing remediation probes:

1. partial strong match vs broad weak coverage;
2. missing is not zero;
3. present weak comparable evidence matters;
4. single-hit spike guard.

For probe 3, explicitly demonstrate:

```text
[.8]      -> .8
[.8, .2] -> .6
```

or equivalent fixture behavior under the implementation helper.

## Step 3 — stability and algebraic probes

Add non-production test/probe coverage for:

1. **small perturbation report** — for the close Character case, vary one admitted raw/bounded cosine by `+/-0.005` and `+/-0.01`; record rank stability. Do not tune the formula from these results.
2. **monotonicity** — increasing one admitted score cannot lower the component score.
3. **weak evidence monotonicity** — adding a score below the current discounted mean lowers the component score.
4. **strong evidence monotonicity** — adding a score above the current discounted mean raises the component score.
5. **permutation invariance** — input hit order does not affect the sorted discounted result.
6. **duplicate protection** — existing per-source-query Object deduplication still prevents duplicate candidate points from generating extra evidence.

A close Character margin is not automatically a failure, but report any rank flips under the fixed perturbations prominently for design review.

## Step 4 — complete quality gates

Run Candidate C through:

- all four frozen Phase-I Similarity cases;
- R2SIM-G01..G06;
- Facet-specific Similarity;
- Application/CLI/MCP serialization contracts;
- generation/current/history isolation;
- same-class/cross-class behavior;
- source exclusion;
- generation payload and SQLite membership integrity checks;
- R2-05 Semantic/Hybrid non-regression;
- R2-08 focused acceptance set.

Do not weaken or rewrite existing gold expectations.

## Step 5 — boundedness

Confirm unchanged:

```text
source Facet queries <= 8
source Statement queries <= 12
total ANN calls <= 21
raw ANN hit upper bound <= 464
candidate Objects <= 128
exposed evidence <= 1/2/3
```

Final score must remain `[0,1]` and `score_type=hierarchical_similarity`.

`object_overall` leakage must remain zero.

## Step 6 — production implementation only if every gate passes

If Candidate C passes every frozen case and required probe, implement it narrowly in the R2 overall Similarity component pooling path.

Preserve deterministic tie-breaking for evidence ordering after bounded cosine DESC.

Explainability must expose every admitted evidence item and its actual discounted contribution. Do not falsely describe reciprocal-rank order as canonical semantic importance; it is only score-derived evidence order.

Do not change:

- component weights;
- caps;
- source representation selection;
- candidate generation;
- ANN limits;
- same-Facet boundaries;
- Facet-specific cosine path;
- generation routing;
- canonical Knowledge;
- Search Representation contents;
- Harrier/runtime;
- R2-05 code.

If Candidate C fails any frozen case or required probe, make no production change and return to design review. Do not try geometric decay, discount exponents, thresholds, missing-value priors, component weight tuning or Class-specific rules in this task.

## Step 7 — verification if implemented

Run at minimum:

- focused Object Similarity tests;
- R2SIM mapped tests;
- R2-08 acceptance harness;
- R2-05 Semantic/Hybrid regression tests;
- Windows full pytest;
- compile;
- target Ruff;
- format check;
- `git diff --check`.

Leave the known unrelated repository-wide E501 unchanged.

Recompute all three R1 SHA-256 values after verification.

## Git rules

If accepted:

- commit implementation/tests/evaluation/docs to `r2-06-similarity-regression-review`;
- push branch;
- leave worktree clean.

Do not:

- merge to main;
- mark R2-08 Complete;
- start R2-09;
- start formal N-05 timing.

If rejected, leave tracked production source unchanged and preserve local diagnostic artifacts.

## Return report

Return:

1. exact Candidate C formula used;
2. four frozen case scores/ranks;
3. first-round probe 4/4 result;
4. six stability/algebraic probe results;
5. perturbation table for the Character close margin;
6. R2SIM-G01..G06;
7. Facet-specific and generation/current/history results;
8. R2-05 non-regression;
9. R2-08 focused result;
10. resource-bound result;
11. full pytest/static checks;
12. R1 hashes before/after;
13. production changed yes/no;
14. changed files;
15. commit SHA/push state if accepted;
16. final R2-06/R2-08/R2-09 status.
