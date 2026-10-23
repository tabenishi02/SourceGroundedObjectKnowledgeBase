# N05D-04R2 / R2-06 — Candidate D Facet-cluster Diagnostic Ablation — Codex Handoff

Updated: 2026-10-24

Use branch:

`r2-06-similarity-regression-review`

Read first:

1. `docs/evaluation/N05D04R2_R2_06_THIRD_DESIGN_REVIEW.md`
2. `docs/evaluation/N05D04R2_R2_06_SECOND_DESIGN_REVIEW.md`
3. `docs/evaluation/N05D04R2_R2_06_SIMILARITY_REGRESSION_ROOT_CAUSE_REVIEW.md`
4. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md`

The first three remediation candidates were rejected. Do not reopen A/B/C and do not search numeric tuning parameters.

## Goal

Perform a **diagnostic-first** local ablation of Candidate D: Facet-cluster hierarchical aggregation.

Do not modify production code until one structural form passes the diagnostic boundary and the complete required verification. The preferred stopping behavior is to retain all diagnostics locally if both forms fail.

## Safety

Before local work:

- inspect branch / HEAD / status / diff;
- record SHA-256 for all three R1 user-aborted assets;
- preserve the original workspace changes;
- prefer an isolated clean worktree;
- do not modify canonical production SQLite or production Qdrant.

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

## Candidate D formula

Use the exact saved evidence from the previous ablations first. Group candidate evidence by canonical Facet identity.

For Facet F:

```text
facet_similarity(F) = admitted Facet cosine, if present
statement_mean(F) = arithmetic mean of admitted same-Facet Statement cosines
```

Facet-local cluster score:

```text
if facet and statements:
    cluster(F) = (.30 * facet_similarity(F)
                  + .20 * statement_mean(F)) / .50

if facet only:
    cluster(F) = facet_similarity(F)

if statements only:
    cluster(F) = statement_mean(F)
```

Do not introduce another weight or threshold.

Object detail:

```text
best_detail = max(cluster(F))
object_score = .50 * overview + .50 * best_detail
```

### Structural variants

Evaluate exactly these two variants:

```text
D1 permissive:
    statement-only Facet clusters are eligible for best_detail

D2 anchored:
    a Facet cluster is eligible for best_detail only if an admitted Facet
    representation for that canonical Facet exists; Statements refine the
    anchored Facet but cannot independently create the winning cluster
```

This is the only bounded comparison. Do not add D3 or numeric sweeps in this task.

## Step 1 — exact saved-hit replay

Using the immutable saved hits from runs `20261024T003934` / `20261024T010705`, calculate D1 and D2 for:

- character_overall;
- character_values (must remain the unchanged Facet-specific path);
- work_overall;
- concept_overall.

Report every Facet cluster:

- canonical Facet ID/name;
- admitted Facet representation/cosine if present;
- admitted same-Facet Statements/cosines;
- Statement mean;
- local normalized role contributions;
- cluster score;
- cluster eligibility under D1/D2;
- winning Facet;
- overview contribution;
- detail contribution;
- final score/rank.

Static cross-check values from design review for D1 are approximately:

```text
Character
  Mika ~= .833514616
  Ren  ~= .830275804

Work
  Ash Garden ~= .857757151
  Iron Crown ~= .846725707

Concept
  Altruism ~= .825645182
  Autonomy ~= .819947120
```

Recompute from exact evidence; these are not assertions.

If both D1 and D2 fail any frozen case at exact replay, stop with no production change.

## Step 2 — Facet-boundary semantic probes

Do not reuse the old flat weak-evidence probe without semantic grouping. Implement explicit probes for the new hierarchy.

### P1 same-Facet weak evidence monotonicity

Within one Facet:

```text
statement scores [.8] -> .8
append same-Facet .2 -> .5
```

or equivalent full cluster calculation. A weaker same-Facet Statement below the existing Statement mean must lower the Statement mean and, when that role affects the cluster, must not raise the cluster score.

### P2 same-Facet strong evidence monotonicity

Adding a same-Facet Statement above the existing Statement mean must not lower the cluster score.

### P3 cross-Facet weak evidence non-dilution

Add a new weak **different-Facet** cluster. It must not lower an already stronger winning Facet cluster or Object score merely because the Object exposes another semantic dimension.

### P4 stronger-Facet replacement

Add a different-Facet cluster whose complete cluster score exceeds the current winner. It must become the winning detail Facet and increase Object score.

### P5 single-Statement spike guard

A very high statement-only cluster must not create an unacceptable Object-level spike. Compare D1 and D2 directly. This probe is expected to be the principal discriminator between the permissive and anchored forms.

### P6 legitimate statement-only evidence

Construct/use a case where a candidate has a legitimate same-Facet Statement hit but no admitted Facet hit because of retrieval/cap behavior, not because the canonical Facet is absent. Record whether D2 loses meaningful signal. Do not weaken P5 to make D1 pass and do not weaken P6 to make D2 pass.

### P7 permutation invariance

Reordering Statements inside one Facet must not change Statement mean or result.

### P8 duplicate source-query protection

Existing duplicate candidate points from the same source query must not create extra Statement/Facet evidence or change result.

## Step 3 — Character sensitivity report

Repeat the fixed Candidate C perturbation protocol on Candidate D's exact evidence:

- each admitted cosine independently at `-0.010`;
- `-0.005`;
- `+0.005`;
- `+0.010`.

Report rank flips for Mika/Ren separately for D1 and D2.

Do not tune the architecture from the perturbation results.

A narrow/unstable margin is not by itself the only rejection criterion, but unexplained sensitivity must be surfaced for design review.

## Step 4 — R2SIM / frozen structural checks

For each D variant still eligible after Steps 1-3, run:

- R2SIM-G01..G06;
- source exclusion;
- same-class / cross-class behavior;
- current/history/generation isolation;
- Facet-specific Similarity unchanged;
- Application / CLI / MCP serialization contracts;
- score in `[0,1]`;
- `score_type=hierarchical_similarity`;
- object_overall leakage = 0.

Do not modify frozen gold expectations.

## Step 5 — resource / boundedness checks

Confirm the candidate does not increase retrieval work:

```text
source Facet queries <= 8
source Statement queries <= 12
total ANN calls <= 21
raw ANN hit upper bound <= 464
candidate Objects <= 128
existing evidence caps remain 1 / 2 / 3
```

Candidate D changes aggregation only. Candidate generation and query counts must remain unchanged.

## Step 6 — production eligibility decision

A variant is production-eligible only if:

- all four frozen cases PASS;
- P1-P8 PASS without assertion weakening;
- R2SIM-G01..G06 PASS;
- Facet-specific path unchanged;
- generation/current/history/source-exclusion contracts PASS;
- resource bounds unchanged;
- no active object_overall leakage.

If both D1 and D2 pass, prefer D2 only if P6 demonstrates no unacceptable loss of legitimate statement-only signal. Otherwise stop for design review rather than choosing by benchmark score.

If only one passes all structural gates, that variant may proceed to Step 7.

If neither passes, stop. Do not introduce thresholds, temperatures, alternative max-k values, component weights, coverage bonuses, or Class-specific rules.

## Step 7 — production implementation only after complete diagnostic PASS

If exactly one variant is clearly eligible, implement narrowly in the R2 overall Similarity aggregation path.

Keep unchanged:

- overview representation and `.50` Object-level allocation;
- total detail allocation `.50`;
- existing Facet `.30` / Statement `.20` relative role allocation inside cluster;
- candidate generation;
- ANN limits;
- evidence caps;
- same-Facet filtering;
- generation routing;
- Facet-specific Similarity;
- canonical Knowledge;
- Search Representation content;
- Harrier/runtime;
- R2-05 code.

Explainability must expose the full winning Facet cluster and all admitted same-Facet evidence used to form it.

Do not describe the winning Facet as canonical importance; it is the strongest observed shared Facet for the comparison.

## Step 8 — full verification if implemented

Run at minimum:

- focused Object Similarity tests;
- all R2SIM mapped tests;
- R2-08 focused acceptance harness;
- R2-05 Semantic/Hybrid non-regression;
- Windows full pytest;
- compile;
- target Ruff;
- relevant format check;
- `git diff --check`.

Do not fix the known unrelated repository-wide E501.

Recompute all three R1 SHA-256 values after verification.

## Git rules

If no variant is accepted:

- no tracked production change;
- no commit/push required for local diagnostics;
- retain diagnostics under `.local/...`;
- return to design review.

If one variant is fully accepted and implemented:

- commit implementation/tests/evaluation/docs to `r2-06-similarity-regression-review`;
- push branch;
- leave verification worktree clean.

In either case do not:

- merge to main;
- mark R2-08 Complete;
- start R2-09;
- start formal N-05 performance timing.

## Return report

Return:

1. D1 and D2 exact formulas actually used;
2. exact four-case scores/ranks;
3. per-Facet cluster decomposition;
4. P1-P8 results;
5. D1 vs D2 single-Statement / legitimate-statement-only behavior;
6. Character perturbation summary;
7. R2SIM-G01..G06;
8. Facet-specific Similarity result;
9. generation/current/history/source-exclusion results;
10. resource bounds and object_overall leakage;
11. production eligibility decision;
12. if implemented, R2-05/R2-08/full regression results;
13. R1 SHA comparison;
14. changed files / commit SHA / push state;
15. final R2-06 / R2-08 / R2-09 status.
