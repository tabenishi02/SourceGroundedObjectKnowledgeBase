# N05D-04R2 / R2-06 — Overall Similarity Third Design Review

Updated: 2026-10-24

Status: **Third design review revised / flattened pooling rejected / Candidate D canonical-Facet anchored design selected for diagnostic ablation only**

## 1. Trigger

Candidate C (reciprocal-rank-discounted comparable-evidence pooling) was rejected by local run `20261024T010705`.

It restored all four frozen Similarity cases and passed the first-round probes, but failed the mandatory weak-evidence monotonicity property:

```text
before: [.8, .2] -> .6
append: .5 (< .6)
after: [.8, .5, .2] -> .609090909...
```

The failure is structural. Sorting by score and changing rank discounts means insertion can reduce the weight of older weak evidence enough to raise the aggregate even when the inserted item is below the prior aggregate.

Candidate C also showed a narrow `character_overall` margin and 21/44 rank flips under fixed +/-0.005 and +/-0.01 perturbations. This is not the formal rejection reason, but it is additional evidence that continued tuning of flat score-order pooling would overfit the current gold.

Do **not** reopen reciprocal exponents, geometric decay constants, temperatures, thresholds, missing-value priors, Class-specific weights, or similar scalar tuning on a flattened evidence list.

## 2. External design review conclusion

A follow-up review compared Candidate D against established multi-vector / late-interaction and field-aware retrieval designs.

The relevant common pattern is:

```text
preserve local semantic units
  -> score locally
  -> aggregate after local structure is retained
```

ColBERT-style late interaction preserves multiple local vectors rather than collapsing them into one representation before scoring. Field-aware / multi-vector systems likewise keep semantically distinct vector fields separate and fuse them only at a later stage. Nested retrieval systems also commonly allow child/local matches to be aggregated into a parent result.

Candidate D therefore has a defensible architectural basis: **Facet is the semantic grouping boundary, not merely metadata attached to otherwise exchangeable evidence.**

However, the original D1/D2 draft had two weaknesses:

1. `statement-only` clusters could claim Object detail authority without a canonical Facet anchor;
2. D2 treated an admitted Facet ANN hit as the anchor, conflating retrieval/cap behavior with canonical Facet existence.

The revised design removes both weaknesses.

## 3. Design conclusion: flattening heterogeneous Facets is the primary error

The rejected policies expose a common boundary problem.

- Control/source-slot mean synthesizes cross-Facet missing evidence as zero and creates shared-Facet coverage bias.
- Candidate A/candidate-local mean removes the missing penalty, but sparse high-scoring evidence can receive full component authority.
- Candidate B/max pooling ignores additional weak comparable evidence.
- Candidate C/rank-discounted pooling preserves secondary evidence but violates weak-evidence monotonicity because score ordering changes weights.

All of them aggregate evidence from different Facets inside one flat Facet bucket and one flat Statement bucket.

That is inconsistent with the R2 hierarchy:

```text
Object
  -> Facet
      -> Statement
```

A `behavior` Statement, `values` Statement and `personality` Statement are not repeated samples of one scalar latent variable. The same applies to `themes` vs `tone`, and `definition` vs `implications`.

The scorer must therefore preserve canonical Facet identity before aggregation.

## 4. Revised semantic contract

Candidate D uses the following semantics.

1. Evidence is grouped by canonical Facet before detail aggregation.
2. Missing evidence in another Facet is **not** synthesized as numeric zero.
3. Within one Facet, all admitted bounded Statements remain real evidence.
4. Adding a weaker same-Facet Statement below the existing Statement mean must not increase that Facet's Statement mean.
5. A weak unrelated Facet must not dilute an already stronger Facet merely because the Object exposes more semantic dimensions.
6. A stronger different-Facet cluster may replace the current winning Facet.
7. A Statement may discover a candidate Object, but it may not independently create Object detail authority without a valid canonical Facet anchor.
8. Facet-specific Similarity remains direct same-Facet cosine and is unchanged.
9. Overall Object Similarity is defined as **broad Object similarity plus the strongest shared canonical Facet**, not breadth-of-Facet coverage.

This is a semantic correction to aggregation boundaries, not a benchmark-specific exception.

## 5. Candidate D — canonical-Facet anchored hierarchical aggregation

Candidate D is selected for **diagnostic ablation only**. It is not production-approved from static replay.

### 5.1 Candidate acquisition remains unchanged

Candidate acquisition still uses the existing bounded R2 paths:

```text
object_overview ANN
Facet ANN
Statement ANN
        -> candidate Object union
```

A candidate may therefore be discovered by a Statement hit even if its Facet vector did not appear in the bounded Facet ANN result.

This is intentional: **candidate discovery and scoring authority are separate concerns.**

### 5.2 Canonical Facet anchor

For every candidate Object and source Facet that contributes admitted evidence, resolve whether the candidate has the corresponding **canonical active-generation Facet membership** in SQLite/generation membership state.

The anchor condition is:

```text
candidate has canonical same-Facet membership
in the active generation/current accepted Version
```

The anchor condition is **not**:

```text
candidate happened to return a Facet ANN hit
```

If the canonical same-Facet membership exists, retrieve/reuse its stored embedding in the fixed Embedding Space and compute the direct source-Facet <-> candidate-Facet cosine for scoring when needed.

This prevents ANN top-k/cap misses from being misinterpreted as semantic absence.

### 5.3 Statement-only cluster is not production-eligible

A Statement hit may add the candidate Object to the union, but no Facet cluster is eligible for Object detail scoring unless the canonical same-Facet anchor exists.

Therefore:

```text
Statement ANN hit
+ no canonical same-Facet candidate membership
=> no detail cluster for that Facet
```

This eliminates the prior D1 single-Statement authority path.

### 5.4 Build Facet clusters before applying local evidence caps

For each canonical anchored Facet F:

```text
Facet cluster F
  canonical facet_similarity(F)
  admitted same-Facet Statement similarities(F)
```

Do not flatten Facets before clustering.

The order is:

```text
1. candidate Object union
2. canonical Facet grouping / anchor resolution
3. collect same-Facet Statement evidence
4. apply Facet-local Statement cap
5. compute Facet cluster score
6. select winning Facet cluster
7. combine with overview
```

The previous global `Statement evidence cap = 3` must not be applied across heterogeneous Facets **before** clusters are formed, because doing so allows one Facet to remove another Facet's local evidence merely by score ordering.

The diagnostic must preserve bounded work and bounded explanation. Any production design must define a Facet-local cap and a final explanation cap explicitly before cutover; this task may not introduce an unbounded all-Statement comparison.

### 5.5 Statement aggregation inside one Facet

Within one anchored Facet cluster:

```text
statement_mean(F) = arithmetic mean(admitted bounded same-Facet Statement cosines)
```

Arithmetic mean is retained because for bounded non-negative evidence:

```text
new value < current mean -> mean decreases
new value > current mean -> mean increases
```

No score-order discount, exponent, temperature or threshold is introduced.

### 5.6 Facet-local cluster score

Use the existing relative detail-role weights:

```text
facet role     = .30
statement role = .20
```

If both canonical Facet cosine and Statement evidence are present:

```text
cluster_score(F)
  = (.30 * facet_similarity(F)
     + .20 * statement_mean(F)) / .50
```

If the canonical Facet exists but no admitted Statement evidence exists:

```text
cluster_score(F) = facet_similarity(F)
```

There is no statement-only branch.

This deliberately treats missing Statement evidence as unknown/not observed, while an actually observed weak Statement is real evidence and lowers the cluster score. That sparse-information behavior must be validated explicitly rather than hidden by a synthetic zero.

### 5.7 Object detail score

Select the strongest complete anchored Facet cluster:

```text
best_detail = max_F cluster_score(F)
```

The max occurs **between complete Facet clusters**, not between raw Facet or Statement hits.

Then:

```text
object_score = .50 * overview + .50 * best_detail
```

The existing top-level authority remains:

```text
overview = .50
detail   = .50
```

Candidate D therefore defines overall similarity as:

> broad Object-level similarity plus the strongest observed shared canonical Facet.

It does **not** claim that the winning Facet is canonically the most important Facet of either Object.

## 6. Why the revised D differs from Candidate B

Candidate B applies max pooling to raw Facet and raw Statement components separately. A weaker same-Facet Statement can disappear entirely from the score.

Revised Candidate D first binds all Statement evidence to its canonical Facet parent and completes the Facet-local score. Weak same-Facet Statements remain visible through `statement_mean(F)`.

Only then is max applied between completed Facet clusters.

Therefore:

```text
same-Facet weak Statement
  -> affects/lower that Facet-local score

cross-Facet weak cluster
  -> does not dilute another Facet

stronger complete Facet cluster
  -> may replace current winner
```

## 7. Static replay status

The previous saved-hit static calculations remain useful only as rough cross-checks because the revised canonical-anchor design may directly recover a Facet cosine even when that Facet was absent from the bounded Facet ANN result.

The prior approximate values were:

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

These are **not acceptance evidence** and must not be treated as frozen expected scores.

## 8. Risks that must be tested

### 8.1 Facet-only sparse-information advantage

Because missing Statement evidence is not synthesized as zero:

```text
Candidate X
facet=.80, no admitted Statements
cluster=.80

Candidate Y
facet=.80, statement=.20
cluster=(.30*.80 + .20*.20)/.50=.56
```

This is mathematically intentional under `missing = unknown`, but it can create a sparse-information advantage if Knowledge density differs greatly between Objects.

Required probe:

```text
facet-only
vs
facet + weak Statement
vs
facet + strong Statement
```

The design review must judge whether this semantic behavior is acceptable for SGOKB overall similarity.

### 8.2 Max-over-Facet semantics / maximum-selection bias

Max-over-Facet removes breadth/coverage reward, but an Object with more comparable Facets has more chances to obtain a high maximum.

Required probes must compare Objects with different counts of valid shared Facets and verify that a broad Object does not win merely from an accidental single spike.

Do not add a Facet-count bonus or threshold in this task.

### 8.3 Local cap ordering

Facet clusters must be formed before Statement evidence is capped for local scoring. The diagnostic must prove that evidence from one Facet cannot evict another Facet's local evidence merely because of a global score ordering.

### 8.4 Canonical anchor versus retrieval artifact

A candidate discovered through Statement ANN but missing from Facet ANN must still be scoreable when the canonical same-Facet membership exists.

Conversely, if no canonical same-Facet membership exists, Statement evidence may not fabricate that Facet cluster.

### 8.5 Explainability

Expose at minimum:

- winning canonical Facet identity;
- canonical Facet membership / representation IDs;
- direct Facet cosine;
- all admitted same-Facet Statement IDs/cosines used by the cluster;
- Statement mean;
- local role contributions;
- overview contribution;
- final score.

The winning Facet is score-derived comparison evidence, not canonical importance.

## 9. Diagnostic acceptance boundary

The prior D1/D2 comparison is superseded.

The next local task evaluates exactly one revised architecture:

```text
Candidate D revised
= canonical-Facet anchored Facet-cluster hierarchical aggregation
```

Required checks:

- four frozen Phase-I Similarity cases;
- R2SIM-G01..G06;
- same-Facet weak-evidence monotonicity;
- same-Facet strong-evidence monotonicity;
- cross-Facet weak-evidence non-dilution;
- stronger-Facet replacement;
- Statement-only discovery with canonical Facet anchor present;
- Statement evidence with canonical Facet anchor absent must not create detail authority;
- facet-only sparse-information behavior;
- maximum-selection / Facet-count spike guard;
- cluster-before-cap ordering;
- permutation invariance inside one Facet;
- duplicate source-query protection;
- fixed Character perturbation report;
- Facet-specific Similarity unchanged;
- generation/current/history/source exclusion unchanged;
- R2-05 Semantic/Hybrid unchanged only if Candidate D reaches full verification.

If any structural property fails, stop and return to design review. Do not search numerical parameters.

## 10. Resource boundary

Candidate D may change scorer-local lookup/aggregation work but must not reopen unbounded retrieval.

Frozen ANN acquisition remains:

```text
source Facet queries <= 8
source Statement queries <= 12
ANN calls <= 21
raw ANN hit slots <= 464
candidate Objects <= 128
```

Canonical anchor resolution and direct Facet cosine reuse must be bounded by the candidate set and selected source Facets. Stored embeddings must be reused; do not re-embed canonical text per query.

Before production cutover, define and verify:

- maximum canonical anchor lookups;
- maximum direct Facet cosine calculations;
- Facet-local Statement evidence cap;
- final explanation cap.

No unbounded all-source-Statement x all-candidate-Statement comparison is permitted.

## 11. Status

```text
R2-05 Semantic remediation = Complete / verified
R2-06 Candidate A = Rejected
R2-06 Candidate B = Rejected
R2-06 Candidate C = Rejected
R2-06 Candidate D original D1/D2 draft = Superseded
R2-06 Candidate D revised canonical-anchor diagnostic = Pending
R2-08 = FAIL / Not Complete
R2-09 = Blocked / Not Started
```
