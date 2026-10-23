# N05D-04R2 / R2-06 — Candidate D Revised Facet-cluster Diagnostic Ablation — Codex Handoff

Updated: 2026-10-24

Use branch:

`r2-06-similarity-regression-review`

Read first:

1. `docs/evaluation/N05D04R2_R2_06_THIRD_DESIGN_REVIEW.md`
2. `docs/evaluation/N05D04R2_R2_06_SECOND_DESIGN_REVIEW.md`
3. `docs/evaluation/N05D04R2_R2_06_SIMILARITY_REGRESSION_ROOT_CAUSE_REVIEW.md`
4. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md`

Candidate A/B/C were rejected. The original Candidate D D1/D2 comparison is superseded by the revised design below. Do not reopen D1 statement-only or D2 admitted-Facet-hit anchoring.

## Goal

Evaluate exactly one architecture:

**Candidate D revised — canonical-Facet anchored Facet-cluster hierarchical aggregation.**

This is diagnostic-first. Production code may be changed only after the complete structural and regression boundary passes.

## Safety

Before local work:

- inspect branch / HEAD / status / diff;
- record SHA-256 for the three R1 user-aborted assets;
- preserve original workspace changes byte-for-byte;
- prefer an isolated clean worktree;
- do not modify canonical production SQLite or production Qdrant namespace.

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

## Candidate D revised contract

### 1. Candidate acquisition stays unchanged

Use existing bounded acquisition:

```text
object_overview ANN
Facet ANN
Statement ANN
        -> candidate Object union
```

A Statement hit is allowed to discover a candidate even if that candidate did not appear in Facet ANN.

Do not change source query selection or ANN query limits.

### 2. Canonical Facet anchor

For each candidate Object and source Facet that has relevant admitted evidence, determine whether the candidate has the canonical same-Facet membership in the active generation/current accepted Version.

Anchor condition:

```text
canonical same-Facet membership exists in active generation/current accepted Version
```

Not anchor condition:

```text
Facet ANN happened to return a hit
```

If the canonical membership exists, reuse the stored Facet embedding and compute/recover the direct source-Facet <-> candidate-Facet cosine in the frozen Embedding Space.

A Facet ANN miss must therefore not be treated as canonical Facet absence.

If canonical same-Facet membership does not exist, Statement evidence cannot fabricate an eligible Facet cluster.

### 3. No statement-only detail cluster

```text
Statement hit
+ canonical Facet anchor absent
=> candidate may remain in union from discovery
=> no eligible detail cluster for that Facet
```

Do not restore D1 behavior.

### 4. Cluster before cap

Group by canonical Facet first.

Required ordering:

```text
candidate union
-> canonical Facet grouping / anchor resolution
-> collect same-Facet Statement evidence
-> apply Facet-local Statement cap
-> calculate Facet-local cluster score
-> select winning Facet
-> combine with overview
```

Do not apply one global Statement top-N across heterogeneous Facets before clustering.

The diagnostic must remain bounded. Measure the exact local work introduced by canonical anchor resolution and direct Facet cosine reuse.

### 5. Facet-local formula

For anchored Facet F:

```text
facet_similarity(F) = direct source-Facet/candidate-Facet bounded cosine
statement_mean(F) = arithmetic mean of admitted bounded same-Facet Statement cosines
```

If Statements exist:

```text
cluster(F)
  = (.30 * facet_similarity(F)
     + .20 * statement_mean(F)) / .50
```

If no admitted Statement exists:

```text
cluster(F) = facet_similarity(F)
```

No statement-only branch.

No new scalar, threshold, exponent, temperature, Class-specific rule, coverage bonus or missing-value prior.

### 6. Object-level formula

```text
best_detail = max(cluster(F) for eligible canonical anchored Facets F)
object_score = .50 * overview + .50 * best_detail
```

The semantic interpretation is fixed:

> overall Object Similarity = broad Object-level similarity + strongest shared canonical Facet.

The winning Facet is score-derived comparison evidence, not canonical importance.

## Step 1 — exact replay / canonical-anchor reconstruction

Start from saved hits from runs `20261024T003934` and `20261024T010705`, but do not assume the saved Facet ANN hit set is complete enough to define anchor existence.

For each candidate/source Facet pair needed by the four frozen cases:

1. inspect canonical active-generation membership;
2. distinguish `Facet ANN miss` from `canonical Facet absent`;
3. reuse the stored embedding for canonical Facet membership;
4. compute/recover exact direct Facet cosine if needed;
5. group Statements under that Facet;
6. compute cluster score;
7. report winning Facet and final Object score.

Evaluate:

```text
character_overall
character_values  # unchanged Facet-specific path
work_overall
concept_overall
```

Previous approximate D values may be used only as cross-checks, not assertions:

```text
Mika        ~= .833514616
Ren         ~= .830275804
Ash Garden  ~= .857757151
Iron Crown  ~= .846725707
Altruism    ~= .825645182
Autonomy    ~= .819947120
```

If the revised architecture fails any frozen case at exact replay, stop before production changes.

## Step 2 — structural probes

### P1 — same-Facet weak evidence monotonicity

Within one anchored Facet, adding a Statement below the current Statement mean must lower the Statement mean and must not raise the cluster score.

### P2 — same-Facet strong evidence monotonicity

Adding a Statement above the current Statement mean must not lower the Statement mean or cluster score.

### P3 — cross-Facet weak evidence non-dilution

Adding a weak different-Facet cluster must not lower the current winning cluster/Object score merely because another semantic dimension exists.

### P4 — stronger-Facet replacement

A complete different-Facet cluster with score above the current winner must replace it and increase Object score.

### P5 — Statement discovery with canonical anchor present

Construct/use a candidate discovered via Statement ANN where the corresponding Facet was not returned by Facet ANN, but canonical same-Facet membership exists.

Expected:

```text
candidate remains valid
canonical Facet anchor is recovered from generation membership
Facet cosine is scored from stored embeddings
cluster is eligible
```

This proves ANN miss != semantic absence.

### P6 — Statement evidence with canonical anchor absent

Construct/use a Statement evidence condition where no canonical same-Facet candidate membership exists.

Expected:

```text
no eligible Facet cluster
Statement alone cannot claim detail authority
```

Do not weaken this probe to preserve statement-only recall.

### P7 — facet-only sparse-information behavior

Explicitly compare:

```text
A: facet=.8, no admitted Statement
B: facet=.8, Statement=.2
C: facet=.8, Statement=.9
```

Report the resulting cluster values and judge against the semantic contract:

```text
missing Statement = unknown/not observed
present weak Statement = real weaker evidence
present strong Statement = real stronger evidence
```

Do not add synthetic zeros or bonuses in this task.

### P8 — maximum-selection / Facet-count spike guard

Compare candidates with different numbers of valid shared Facets.

Required observations:

- extra weak Facets must not improve score;
- a candidate must not win solely because it has more Facets and therefore more opportunities for an accidental maximum;
- a single strong winning Facet should be semantically inspectable, not a duplicate/retrieval artifact.

If a structural maximum-selection defect appears, stop for design review rather than tuning max-k or thresholds.

### P9 — cluster-before-cap ordering

Create/use a case where Statements from multiple Facets would compete under the old global top-N.

Expected:

- each eligible Facet cluster is formed before its local Statement cap;
- strong evidence in Facet A cannot evict all local evidence from Facet B merely through one global ranking list;
- total work/explanation remains bounded.

### P10 — permutation invariance

Reordering Statements inside a Facet must not change its arithmetic mean or cluster result.

### P11 — duplicate source-query protection

Duplicate candidate points from one source query must not create extra evidence or alter a cluster/result.

## Step 3 — local boundedness design measurement

The frozen ANN acquisition limits remain:

```text
source Facet queries <= 8
source Statement queries <= 12
ANN calls <= 21
raw ANN hit slots <= 464
candidate Objects <= 128
```

Measure and report additional scorer-local work introduced by the revised design:

```text
canonical Facet membership lookups
stored embedding reads
additional direct Facet cosine calculations
maximum eligible Facet clusters per candidate
maximum Facet-local Statement evidence retained
final explanation size
```

Do not introduce unbounded all-source-Statement x all-candidate-Statement work.

Before production eligibility, propose/freeze explicit bounds for:

- canonical anchor resolutions;
- direct Facet cosine calculations;
- Facet-local Statement cap;
- final exposed evidence cap.

These bounds must follow from existing source/candidate caps where possible rather than arbitrary quality tuning.

## Step 4 — Character sensitivity report

Repeat the fixed perturbation protocol against revised Candidate D exact evidence:

```text
-0.010
-0.005
+0.005
+0.010
```

Perturb each admitted/recovered cosine independently and report Mika/Ren flips.

Do not tune formula or weights from these results.

## Step 5 — R2SIM / frozen structural verification

If Steps 1-4 remain eligible, run:

- R2SIM-G01..G06;
- source exclusion;
- same-class / cross-class behavior;
- current/history/generation isolation;
- Facet-specific Similarity unchanged;
- Application / CLI / MCP serialization contracts;
- score in `[0,1]`;
- `score_type=hierarchical_similarity`;
- active `object_overall` leakage = 0.

Do not rewrite frozen gold expectations to fit Candidate D.

## Step 6 — production eligibility decision

Candidate D revised is production-eligible only if:

- all four frozen cases PASS;
- P1-P11 PASS without assertion weakening;
- canonical anchor behavior is correct;
- cluster-before-cap behavior is correct;
- maximum-selection behavior has no structural defect;
- bounded scorer-local work is explicitly defined and acceptable;
- R2SIM-G01..G06 PASS;
- Facet-specific path unchanged;
- generation/current/history/source-exclusion contracts PASS;
- no active object_overall leakage.

If any structural probe fails, make no production change and return to design review.

Do not search:

```text
max-k
softmax temperature
Facet-count bonuses
thresholds
new weights
missing priors
Class-specific rules
```

in the same task.

## Step 7 — production implementation only after full diagnostic PASS

If Candidate D revised passes the full diagnostic boundary, implement narrowly in the R2 overall Similarity scoring path.

Keep unchanged:

- public API;
- candidate acquisition channels;
- source query selection;
- ANN query limits;
- overview `.50` allocation;
- total detail `.50` allocation;
- Facet `.30` / Statement `.20` relative local roles;
- same-Facet filtering;
- generation routing;
- current/history semantics;
- Facet-specific Similarity;
- canonical Knowledge;
- Search Representation content;
- Harrier/runtime;
- R2-05 code.

Explainability must expose the complete winning Facet cluster and its actual contributing evidence.

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

Leave the known unrelated repository-wide E501 unchanged.

Recompute all three R1 SHA-256 values after verification.

## Git rules

If Candidate D revised is rejected:

- tracked production source remains unchanged;
- retain diagnostic artifacts under `.local/...`;
- no production commit/push;
- return to design review.

If fully accepted and implemented:

- commit implementation/tests/evaluation/docs to `r2-06-similarity-regression-review`;
- push branch;
- leave verification worktree clean.

Do not:

- merge to main;
- mark R2-08 Complete independently;
- start R2-09;
- start formal N-05 performance timing.

## Return report

Return:

1. exact revised Candidate D formula;
2. exact four frozen-case scores/ranks;
3. canonical anchor vs Facet ANN-miss cases;
4. per-Facet cluster decomposition;
5. P1-P11 results;
6. facet-only sparse-information analysis;
7. maximum-selection / Facet-count analysis;
8. cluster-before-cap evidence;
9. additional scorer-local work counts and proposed bounds;
10. Character perturbation summary;
11. R2SIM-G01..G06;
12. Facet-specific Similarity result;
13. generation/current/history/source-exclusion results;
14. resource bounds and object_overall leakage;
15. production eligibility decision;
16. if implemented, R2-05/R2-08/full regression results;
17. R1 SHA comparison;
18. changed files / commit SHA / push state;
19. final R2-06 / R2-08 / R2-09 status.
