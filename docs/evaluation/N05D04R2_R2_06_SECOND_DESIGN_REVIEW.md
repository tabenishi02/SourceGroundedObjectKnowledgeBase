# N05D-04R2 / R2-06 — Overall Similarity Second Design Review

Updated: 2026-10-24

Status: **Second design review complete / Candidate C selected for local ablation / production change prohibited until local acceptance**

Parent review:

`docs/evaluation/N05D04R2_R2_06_SIMILARITY_REGRESSION_ROOT_CAUSE_REVIEW.md`

Reference local run:

```text
run_id = 20261024T003934
branch = r2-06-similarity-regression-review
head   = f20e88c320148f25d822ea4e53c2de009d552b81
```

## 1. Result of the first bounded ablation

The first remediation ablation confirmed the original root cause but rejected both proposed production candidates.

| Policy | Character overall | Character values | Work | Concept | Required probes |
|---|---|---|---|---|---|
| Control / source-slot mean | PASS | PASS | FAIL | FAIL | 1/4 |
| A / candidate-local mean | FAIL | PASS | PASS | PASS | 4/4 |
| B / max pooling | PASS | PASS | PASS | PASS | 3/4 |

No production source was changed.

The shared-Facet coverage bias is causal:

```text
Work / Ash Garden
Control = .647105710
Candidate-local missing-slot correction = .857757151
Iron Crown Control = .831410221

Concept / Altruism
Control = .623924442
Candidate-local missing-slot correction = .825645182
Autonomy Control = .815355045
```

However, Candidate A over-rewards sparse high-scoring evidence. In `character_overall`, Ren has only two comparable Statement hits. Removing the missing source slot raises its Statement component from `.549940880` to `.824911321`, moving its total from `.772949205` to `.827943293` and incorrectly above Mika `.825480494`.

Candidate B avoids that failure but ignores contradictory/weak additional comparable evidence. A component with scores `[.8]` and `[.8, .2]` remains `.8`, violating the required `present_weak_evidence_matters` probe.

Therefore the second design must satisfy all three semantic requirements simultaneously:

1. missing same-Facet evidence is not numeric zero;
2. sparse evidence must not automatically receive full component authority merely because missing entries are ignored;
3. additional weak comparable evidence must still reduce the component score.

## 2. Candidate C — reciprocal-rank-discounted comparable-evidence pooling

For one component, take the already bounded/admitted candidate evidence after all existing same-Facet and evidence-cap rules.

Sort admitted bounded cosine values descending:

```text
c1 >= c2 >= ... >= cn
```

Use a deterministic reciprocal-rank discount:

```text
d_i = 1 / i

component_score
  = sum(d_i * c_i for i=1..n)
    / sum(d_i for i=1..n)
```

If `n == 0`, the component contributes `0` because there is no comparable evidence at all. No source-side missing slot is inserted into this denominator.

With the frozen current evidence caps this means:

```text
overview:  d = [1]
facet:     d = [1, 1/2]
statement: d = [1, 1/2, 1/3]
```

The outer component weights remain unchanged:

```text
overview  = .50
facet     = .30
statement = .20
```

### 2.1 Why this is structurally different from A and B

Candidate A uses equal weights over every present hit. It therefore allows two sparse high Statement hits to claim essentially the whole Statement component.

Candidate B uses only the best hit. It therefore cannot express negative evidence from a weaker second or third comparable hit.

Candidate C is a deterministic middle contract:

- the strongest comparable evidence has the most authority;
- second/third evidence remains visible and changes the score;
- missing evidence is not synthesized as zero;
- no learned scalar, Class-specific Facet priority, score threshold, model change, or free parameter search is introduced.

For the required weak-evidence probe:

```text
[.8]      -> .8
[.8, .2] -> (.8 + .5*.2) / 1.5 = .6
```

Thus weak present evidence matters, unlike Max pooling.

## 3. Static replay against the observed local scores

Using the exact scores already recorded by run `20261024T003934`, Candidate C gives the following preliminary totals.

### 3.1 Character overall

```text
Mika
  overview  = .828102731
  facet     = weighted mean(.839256714, .834150214) = .837554547
  statement = weighted mean(.838431183, .834553440, .733286716) = .818256440
  final     = .828969018

Ren
  overview  = .832789060
  facet     = weighted mean(.828837925, .814938735) = .824204862
  statement = weighted mean(.826149483, .823673158) = .825324041
  final     = .828720797
```

Preliminary order:

```text
Mika .828969018 > Ren .828720797
```

The margin is only about `.000248221`. Therefore this is a **promising candidate, not an acceptance result**. Exact local execution and stability checks are mandatory.

### 3.2 Work overall

```text
Ash Garden = .857757151
Iron Crown = .836515383
```

Preliminary order restores the frozen gold.

### 3.3 Concept overall

Using the exact recorded definition/implications scores:

```text
Altruism = .825645182
Autonomy = .816885737
```

Preliminary order restores the frozen gold.

### 3.4 Character values

Facet-specific Similarity does not use the overall hierarchical pooling path and must remain unchanged.

## 4. Why Candidate C is preferred for the second ablation

Candidate C directly addresses the two first-round failure modes without introducing benchmark-specific semantic knowledge.

It does not encode:

- `themes > tone`;
- `definition > implications`;
- Character-specific coverage bonuses;
- Class-specific weights;
- Harrier/model changes;
- arbitrary missing-value priors.

The reciprocal-rank discount is fixed by evidence order and cap. It preserves the existing meaning that stronger evidence should have more influence while retaining inspectable secondary evidence.

This is conceptually closer to rank-discounted late interaction than to pure MaxSim. External multi-vector retrieval work shows why strongest local alignment can be useful, but Max-style pooling can over-reward one alignment and fail to represent weak/contradictory secondary evidence. External literature is supporting context only; SGOKB's frozen semantic contracts and gold remain authoritative.

## 5. Additional risks revealed by the static replay

### 5.1 Character margin is narrow

Candidate C's preliminary Character margin is extremely small. Acceptance must not rely only on the four frozen ranking cases.

Add deterministic stability probes that do not tune the formula:

1. perturb one admitted cosine by small fixed deltas (`±0.005`, `±0.01`) and report whether the expected order flips;
2. verify monotonicity: increasing an admitted score cannot lower the component score;
3. verify weak-evidence monotonicity: adding a score below the current discounted mean lowers the component score;
4. verify strong-evidence monotonicity: adding a score above the current discounted mean raises the component score;
5. verify permutation invariance before sorting;
6. verify duplicate source-query contribution remains prevented by the existing per-source-query Object deduplication.

A narrow gold margin alone is not an automatic rejection, but unexplained instability under small reasonable perturbations is.

### 5.2 Evidence rank is score-derived, not semantic importance

The discount order is determined only by bounded cosine. Do not claim that rank 1 is canonically more important as Knowledge. It is only the strongest observed similarity evidence for this component.

Explainability must continue to expose every admitted evidence item and its discounted contribution.

## 6. Second-ablation acceptance boundary

Candidate C is eligible only if all of the following pass under the unchanged frozen runtime:

```text
Phase-I Similarity frozen cases
  character_overall  PASS
  character_values   PASS
  work_overall       PASS
  concept_overall    PASS

R2SIM-G01..G06       PASS
first-round probes   4/4 PASS
new stability probes PASS
Facet-specific cosine unchanged
R2-05 Semantic/Hybrid unchanged
generation/current/history unchanged
source exclusion unchanged
same-Facet hard boundary unchanged
object_overall leakage = 0
resource bounds unchanged
score range [0,1]
score_type = hierarchical_similarity
```

If Candidate C fails any frozen case or required probe, stop. Do not search discount exponents, geometric factors, score thresholds, missing priors, component weights, or Class-specific rules in the same task.

## 7. Production implementation boundary if accepted

Only R2 overall component pooling may change.

The intended change is from source-slot or equal/max pooling to:

```text
admitted = sorted(candidate component evidence by bounded cosine DESC,
                  deterministic existing tie-breakers)
weights  = [1/(rank+1) for rank in zero_based_index]
component_score = weighted_mean(admitted bounded cosine, weights)
```

Keep unchanged:

- overview/facet/statement component weights `.50/.30/.20`;
- source Facet/Statement selection;
- ANN query limits;
- candidate union/cap;
- same-Facet filtering;
- evidence caps `1/2/3`;
- bounded cosine;
- generation routing;
- current/history semantics;
- Facet-specific raw cosine;
- R2-05 Semantic/Hybrid fusion;
- canonical Knowledge and Search Representation content;
- Harrier OSS v1 0.6B runtime.

## 8. Current state

```text
R2-05 Semantic remediation = Complete / verified
R2-06 original implementation = historical Complete
R2-06 first remediation candidates A/B = rejected
R2-06 second design review = Complete
R2-06 Candidate C local ablation = Pending
R2-08 = FAIL / Not Complete
R2-09 = blocked / Not Started
N05D-04R2 = Active
N-05 = BLOCKED / Not Complete
```

Do not start R2-09.