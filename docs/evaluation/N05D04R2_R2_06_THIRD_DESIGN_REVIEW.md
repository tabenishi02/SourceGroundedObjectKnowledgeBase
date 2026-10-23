# N05D-04R2 / R2-06 — Overall Similarity Third Design Review

Updated: 2026-10-24

Status: **Third design review complete / flattened component pooling rejected / Candidate D selected for diagnostic ablation only**

## 1. Trigger

Candidate C (reciprocal-rank-discounted comparable-evidence pooling) was rejected by local run `20261024T010705`.

It restored all four frozen Similarity cases and passed the first-round four probes, but failed the mandatory weak-evidence monotonicity property:

```text
before: [.8, .2] -> .6
append: .5 (< .6)
after: [.8, .5, .2] -> .609090909...
```

The failure is structural. Sorting by score and changing rank discounts means insertion can reduce the weight of an older weak item enough to raise the aggregate even when the inserted item is below the previous aggregate.

Candidate C also showed a very narrow `character_overall` margin and 21/44 rank flips under the fixed +/-0.005 and +/-0.01 perturbations. This is not the formal rejection reason, but it is additional evidence that continuing to tune score-order discounts would be overfitting.

Therefore do **not** search reciprocal exponents, geometric decay constants, temperature, missing-value priors, Class-specific weights, thresholds, or other scalar tuning on the flattened evidence list.

## 2. Design conclusion: the deeper problem is flattening heterogeneous Facets

The first three rejected policies now expose a more fundamental boundary problem.

- Control/source-slot mean treats missing cross-Facet evidence as numeric zero and creates shared-Facet coverage bias.
- Candidate A/candidate-local arithmetic mean removes the missing penalty, but a sparse set of high Statement hits can obtain full component authority and regress `character_overall`.
- Candidate B/max pooling restores the frozen cases but ignores additional weak comparable evidence.
- Candidate C/rank-discounted pooling keeps secondary evidence, but score-order reweighting violates weak-evidence monotonicity.

All four policies aggregate evidence from different Facets inside one flat Facet bucket and one flat Statement bucket.

That is inconsistent with the R2 hierarchy:

```text
Object
  -> Facet
      -> Statement
```

A `behavior` Statement, a `values` Statement and a `personality` Statement are not repeated samples of one scalar latent variable. They belong to separate semantic dimensions. The same is true for `themes` vs `tone` and `definition` vs `implications`.

The next design must therefore restore the Facet boundary **inside the scorer**, rather than continue searching for another flat pooling formula.

## 3. Revised semantic properties

The prior `present weak comparable evidence matters` and weak-evidence monotonicity requirements remain valid **within one Facet cluster**.

They must not be interpreted as requiring a weak evidence item from a different Facet to lower the strongest unrelated Facet match.

Revised contract:

1. Missing evidence inside another Facet is not synthesized as cosine zero.
2. Within one Facet, every admitted Statement remains real evidence and a weaker added Statement must not increase that Facet-local score.
3. Evidence from different Facets is grouped first; it is not treated as exchangeable samples.
4. A weak unrelated Facet must not dilute a stronger Facet merely because the Object exposes more semantic dimensions.
5. A single Statement may not independently claim the entire detail half of Object Similarity without a valid Facet parent/cluster path.
6. Facet-specific Similarity remains raw same-Facet cosine and is unchanged.

This is a semantic correction to the aggregation boundary, not a relaxation made only to pass the frozen cases.

## 4. Candidate D — Facet-cluster hierarchical aggregation

Candidate D is selected for **diagnostic ablation**, not production implementation.

### 4.1 Build Facet clusters

For each source Facet represented in the existing R2 query set, group candidate evidence by canonical Facet identity:

```text
Facet cluster F
  facet_similarity(F)          # if admitted
  statement_similarities(F)    # zero or more admitted same-Facet Statements
```

Do not move evidence between Facets.

### 4.2 Statement aggregation inside one Facet

Within a Facet cluster, aggregate admitted Statement cosines by ordinary arithmetic mean:

```text
statement_mean(F) = mean(statement similarities in F)
```

This is intentionally simple. Arithmetic mean has the desired insertion property for non-negative bounded scores:

```text
new evidence < current mean  -> new mean decreases
new evidence > current mean  -> new mean increases
```

No score-order weight, temperature, exponent or threshold is introduced.

### 4.3 Facet-local detail score

Use the existing detail-role weights only, normalized over the evidence roles actually available inside that Facet cluster:

```text
facet role weight     = .30
statement role weight = .20

if facet and statements are present:
    cluster_score(F)
      = (.30 * facet_similarity(F)
         + .20 * statement_mean(F)) / .50

if only facet is present:
    cluster_score(F) = facet_similarity(F)

if only statements are present:
    cluster_score(F) = statement_mean(F)
```

The diagnostic must report whether allowing statement-only clusters is safe. Production eligibility is not granted yet for that boundary.

### 4.4 Object detail score

For the diagnostic candidate, select the strongest Facet cluster:

```text
best_detail = max_F cluster_score(F)
```

Then combine with the overview using the existing top-level allocation:

```text
object_score = .50 * overview + .50 * best_detail
```

This preserves the existing total overview/detail authority (`.50` / `.50`) without inventing a new scalar.

The max occurs **between Facet clusters**, not between raw evidence items. Weak Statements inside the winning Facet still affect that cluster score.

## 5. Static replay from the saved exact hits

Using the exact saved Candidate C evidence, Candidate D has the following preliminary values.

### 5.1 Character overall

Facet clusters:

```text
Mika
personality ~= (.30*.839256714 + .20*.838431183)/.50 = .838926501
values      ~= (.30*.834150214 + .20*.834553440)/.50 = .834311504
behavior    ~= statement-only .733286716
best detail = personality .838926501

Ren
personality ~= (.30*.828837925 + .20*.826149483)/.50 = .827762548
values      ~= (.30*.814938735 + .20*.823673158)/.50 = .818432504
best detail = personality .827762548
```

Preliminary Object scores:

```text
Mika = .50*.828102731 + .50*.838926501 = .833514616
Ren  = .50*.832789060 + .50*.827762548 = .830275804
```

This restores Mika with a substantially wider preliminary margin than Candidate C.

### 5.2 Work overall

```text
Ash Garden themes ~= .842605764
Iron Crown tone   ~= .834102150
Iron Crown themes ~= .772840207

Ash Garden = .857757151
Iron Crown = .846725707
```

### 5.3 Concept overall

```text
Altruism definition ~= .806882959
Autonomy implications ~= .786106039
Autonomy definition   ~= .767737741

Altruism = .825645182
Autonomy = .819947120
```

These are static calculations only. They are not acceptance evidence.

## 6. Why this candidate is different from Candidate B

Candidate B performs max pooling over raw Facet hits and raw Statement hits independently. A weaker second Statement can therefore disappear from the score entirely.

Candidate D first binds Statement evidence to its canonical Facet parent and computes a Facet-local score. Weak same-Facet Statements remain visible through `statement_mean(F)`.

Only after the Facet-local score is complete does the Object-level detail selector choose the strongest semantic Facet.

Therefore the next probes must distinguish:

```text
same-Facet weak evidence      -> must affect/lower that Facet-local score
cross-Facet weak evidence     -> must not automatically dilute another Facet
new stronger Facet cluster    -> may replace the previous winning Facet
```

## 7. Risks that must be tested before any production change

### 7.1 Statement-only cluster risk

A high Statement with no admitted Facet representation could become a winning cluster. Test both:

- permissive diagnostic: statement-only cluster allowed;
- anchored diagnostic: cluster eligible for Object detail only when an admitted Facet representation exists.

This is a bounded architectural comparison, not a parameter sweep.

If the permissive form creates a single-hit spike and the anchored form preserves legitimate cases, prefer the anchored contract for the next design review. Do not implement either yet.

### 7.2 Max-over-Facet semantics

Candidate D intentionally says that overall Object similarity should be anchored by the strongest shared semantic Facet plus overview, rather than by breadth of matching Facet count.

This must be tested against synthetic cases where:

- one Facet is very strong and another is weak;
- two moderate Facets should not automatically beat one genuinely strong Facet;
- a stronger new Facet should improve the score;
- a weak unrelated new Facet should not reduce the score;
- within the winning Facet, weaker Statements must reduce its local score.

### 7.3 Explainability

Expose:

- Facet cluster identity;
- Facet cosine;
- all admitted same-Facet Statement cosines;
- Statement mean;
- normalized local role contributions;
- winning detail Facet;
- overview contribution;
- final Object score.

Do not call the winning Facet canonically more important. It is only the strongest observed shared Facet for this query/object comparison.

## 8. Diagnostic acceptance boundary

Candidate D is not production-eligible from static replay alone.

The next local task is diagnostic-first. It must compare exactly two structural forms:

```text
D1 = Facet-cluster max, statement-only clusters allowed
D2 = Facet-cluster max, admitted Facet anchor required
```

Both use the same fixed formulas above. No scalar tuning is allowed.

Required checks:

- four frozen Phase-I Similarity cases;
- R2SIM-G01..G06;
- existing first-round probes reinterpreted at the correct Facet boundary;
- same-Facet weak-evidence monotonicity;
- cross-Facet weak-evidence non-dilution;
- stronger-Facet replacement;
- single-Statement spike guard;
- statement-only legitimate-match probe;
- permutation invariance inside a Facet;
- duplicate source-query protection;
- fixed Character perturbation report;
- Facet-specific Similarity unchanged;
- R2-05 Semantic/Hybrid unchanged if and only if a candidate reaches full verification.

If neither D1 nor D2 satisfies the structural probes and frozen cases, stop and return to design review. Do not search numerical parameters.

## 9. Status

```text
R2-05 Semantic remediation = Complete / verified
R2-06 Candidate A = Rejected
R2-06 Candidate B = Rejected
R2-06 Candidate C = Rejected
R2-06 third design review = Complete
R2-06 Candidate D diagnostic ablation = Pending
R2-08 = FAIL / Not Complete
R2-09 = Blocked / Not Started
```
