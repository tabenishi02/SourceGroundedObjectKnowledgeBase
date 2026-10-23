# N05D-04R2 / R2-06 — Overall Similarity Remediation Reference Workstation Handoff

Updated: 2026-10-24

Status: **Local causal proof / bounded ablation required**

Authority:

```text
docs/evaluation/N05D04R2_R2_06_SIMILARITY_REGRESSION_ROOT_CAUSE_REVIEW.md
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md
benchmark/search-quality-gold-v1.json
benchmark/n05d04r2-object-similarity-gold-v1.json
docs/evaluation/N05D04R2_SEARCH_QUALITY_ACCEPTANCE.md
```

Do not start R2-09. Do not change R2-05 Semantic fusion except for regression testing.

## 1. Base and safety

Use branch:

```text
r2-06-similarity-regression-review
```

The branch was created from the verified R2-05 remediation commit:

```text
ed945da6fccc57f42e9497b2828e12e6faee666d
```

Resolve the remote branch HEAD before work.

Before checkout/pull/reset in the original workspace:

1. record current branch and HEAD;
2. record `git status` and `git diff`;
3. identify the three preserved R1 user-aborted assets;
4. record their SHA-256 values;
5. do not overwrite, clean, reset, stage or commit those assets;
6. prefer a separate clean verification worktree.

Use the synthetic R2-08 Search-quality fixture for causal/quality work. Do not mutate the reference canonical DB or production Qdrant namespace.

## 2. Frozen runtime

Keep exactly:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
CUDA / bfloat16
dimension: 1024
normalization: unchanged
truncation: prohibited
```

Do not introduce:

- another embedding model;
- Harrier 270M;
- CPU fallback;
- FlashAttention-2;
- PyTorch/CUDA update;
- tokenizer/model revision change;
- canonical Knowledge changes;
- cross-Facet fallback;
- arbitrary weight tuning.

## 3. Reproduce both failures before code changes

Reproduce:

```text
work_overall
source = obj:glass_sky
expected = obj:ash_garden
current wrong rank 1 = obj:iron_crown

concept_overall
source = obj:self_sacrifice
expected = obj:altruism
current wrong rank 1 = obj:autonomy
```

Do not change production code until the contribution decomposition is saved.

For source + expected candidate + wrong candidate, record all component evidence.

### Overview

```text
source/candidate representation + membership IDs
raw cosine
bounded cosine
weighted contribution
```

### Facet

For every selected source Facet query:

```text
source Facet key
source representation/membership
candidate same-Facet representation/membership if present
raw cosine
bounded cosine
per-source-query Object dedup result
whether admitted by final Facet evidence cap
current source slot denominator
current final contribution
```

### Statement

For every selected source Statement query:

```text
source Statement ID / Facet
candidate same-Facet Statement ID if present
raw cosine
bounded cosine
per-source-query Object dedup result
whether admitted by Statement cap
current source slot denominator
current final contribution
```

Also record:

```text
component scores
component weighted contributions
final hierarchical_similarity
final rank
```

Explicitly answer:

1. How much of `iron_crown`'s lead comes from its additional `tone` overlap?
2. How much of `autonomy`'s lead comes from its additional `implications` overlap?
3. Are `ash_garden/themes` and `altruism/definition` the strongest semantically relevant raw same-Facet matches?
4. Does overview independently prefer the wrong candidate?
5. Are candidate union / ANN recall / generation / current-Version semantics correct?
6. Is active `object_overall` leakage zero?

If the expected candidate is still weaker after removing missing-slot penalties, stop and report that the desk-review root cause is incomplete. Do not tune weights to force a pass.

## 4. Bounded counterfactual ablation

Prefer recomputing from the same captured candidate hits/embeddings before making production code changes.

### Control

Current source-slot mean:

```text
slots = min(component_cap, source_component_count)
component_score = sum(admitted bounded cosine) / slots
```

### Candidate A — preferred first candidate

Candidate-local comparable-evidence mean:

```text
admitted = candidate's top component hits after the existing cap

if admitted is empty:
    component_score = 0
else:
    component_score = sum(bounded cosine) / len(admitted)
```

Keep current weights exactly:

```text
overview=.50
facet=.30
statement=.20
```

### Candidate B — fallback only

Strongest-evidence pooling:

```text
component_score = max(bounded cosine of admitted hits)
```

Do not introduce extra scalar parameters or a broader search.

## 5. Required evaluation for each candidate

Evaluate all four frozen Phase-I Similarity cases:

```text
character_overall
character_values
work_overall
concept_overall
```

Evaluate all six R2 gold contracts:

```text
R2SIM-G01 .. R2SIM-G06
```

Facet-specific Similarity must remain raw same-Facet cosine.

Record case-level ordering and aggregate metrics, not just PASS/FAIL.

## 6. Add targeted remediation probes

Add isolated synthetic probes for:

### Probe 1 — partial strong match vs broad weak coverage

Source has at least two Facets. True candidate has one strongly matching same-Facet representation and lacks the second. Distractor has both same Facets but only weak/moderate matches. True candidate must rank first.

### Probe 2 — missing is not zero

Demonstrate that absence of a source Facet in overall mode is treated as missing/non-comparable evidence under Candidate A rather than an implicit zero slot.

### Probe 3 — present weak comparable evidence matters

Candidate A should not simply ignore a weak same-Facet match when that Facet is actually present and comparable. Show the mean changes appropriately.

### Probe 4 — single-hit spike guard

Construct a candidate with one very high detail match but poor broad context and a competitor with consistently good overview/detail similarity. Candidate A must not create an obvious one-hit pathological win.

Keep these probes separate from the frozen Phase-I gold unless a later accepted design explicitly extends the formal gold.

## 7. Selection rule

Prefer Candidate A if all are true:

```text
work_overall restored
concept_overall restored
character_overall preserved
character_values preserved
R2SIM-G01..G06 PASS
4 targeted probes PASS
Facet-specific cosine unchanged
generation/current/history isolation unchanged
source query bounds unchanged
ANN/raw hit/candidate caps unchanged
1/2/3 evidence caps unchanged
final score remains [0,1]
R2-05 Semantic/Hybrid quality unchanged
```

Candidate B may be selected only if Candidate A fails or local evidence shows that averaging comparable evidence produces a separate unexplained quality defect.

If neither passes, stop and report. Do not tune component weights or model/runtime.

## 8. Production implementation after selection

If Candidate A passes, keep the production change narrowly within R2 overall candidate scoring.

Expected conceptual delta:

```text
before:
slots = min(cap, source_counts[component])
contribution denominator = slots

after:
admitted_hits = candidate component hits after existing cap
contribution denominator = len(admitted_hits)
```

Do not change:

- `R2_COMPONENT_WEIGHTS`;
- `R2_COMPONENT_EVIDENCE_CAPS`;
- source Facet cap 8;
- source Statement cap 12;
- ANN limits 128/24/12;
- candidate cap 128;
- same-Facet hard filters;
- bounded cosine behavior;
- generation routing;
- Facet-specific Similarity;
- R2-05 Hybrid/Semantic fusion.

Update the R2-06 design/formula document and tests to match the selected semantics.

## 9. Verification after implementation

At minimum run:

```powershell
python -m pytest -q tests/test_object_similarity.py tests/test_object_similarity_r2.py
python -m pytest -q tests/test_n05d04r2_search_quality_acceptance.py
python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only
```

Then run the R2-08 focused regression set, including the R2-05 Semantic fusion tests, and Windows full pytest.

Also run:

```text
python -m compileall -q src tests scripts
Ruff for src/tests/scripts
format check for changed Python files
git diff --check
```

Repository-wide Ruff may retain only the already documented unrelated `benchmark/tools/n05_resource_preflight.py:69 E501`; do not modify it in this task.

Re-hash all three preserved R1 assets and prove before/after equality.

## 10. R2-08 status after implementation

If both Overall Similarity regressions are restored and all unchanged R2-08 gates pass, report that the code is **eligible for a formal R2-08 re-acceptance review**.

Do **not** independently mark R2-08 Complete unless the complete unchanged acceptance contract has been reviewed and accepted. Do not start R2-09.

## 11. Git operation

If the causal hypothesis is disproved, do not commit a forced production fix. Commit/push only evidence/design updates if useful and report the stop condition.

If a candidate is selected and verified:

- commit implementation + focused tests + design/evaluation updates + machine-readable result;
- push to `r2-06-similarity-regression-review`;
- do not merge to main;
- leave the verification worktree clean.

## 12. Final report

Return:

1. measured causal decomposition for `work_overall`;
2. measured causal decomposition for `concept_overall`;
3. source-slot coverage penalty attributable to the extra shared Facet/Statement evidence;
4. Candidate A result;
5. Candidate B result if evaluated;
6. selected rule and reason;
7. all four frozen Similarity case orders/metrics;
8. R2SIM-G01..G06 results;
9. four new probe results;
10. R2-05 Semantic/Hybrid non-regression result;
11. focused/full pytest and static checks;
12. R1 asset SHA equality;
13. changed files;
14. commit SHA / push state / worktree state;
15. final R2-06 / R2-08 / R2-09 status.
