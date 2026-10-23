# N05D-04R2 / R2-06 — Overall Similarity Fourth Design Review

Updated: 2026-10-24

Status: **Candidate E accepted / Reference Workstation runtime verified on remediation branch**

## 1. Trigger

Candidate D revised (`canonical-Facet anchored Facet-cluster hierarchical aggregation`) was rejected by local diagnostic run `20261024T014359`.

It restored all four frozen Similarity cases, but two mandatory structural probes failed:

1. P1 — same-Facet weak-evidence monotonicity failed at the proposed score-based local Statement cap of 3.
2. P8 — max-over-Facet introduced a Facet-count opportunity bias under an explicit equal-quality null fixture.

No production source was changed. R2-08 remains Failed / Not Complete and R2-09 remains blocked.

## 2. What Candidate D proved

Candidate D validated several important boundaries that should be retained:

- canonical Facet membership, not Facet ANN appearance, is the semantic anchor;
- Statement discovery may recover a candidate even when Facet ANN misses;
- Statement evidence without a canonical same-Facet anchor must not create detail authority;
- Facet grouping must happen before Statement aggregation;
- missing Statement evidence and observed weak Statement evidence are semantically different;
- canonical anchor recovery from stored embeddings is feasible without re-embedding.

These parts are not the cause of rejection.

## 3. P1 root cause — score-based truncation breaks insertion monotonicity

Candidate D proposed a natural Facet-local Statement cap of 3. The diagnostic counterexample was:

```text
before admitted = [.9, .8, .1]
mean = .6

append .5 where .5 < .6
score-based top-3 => [.9, .8, .5]
mean = .733333...
```

The arithmetic mean itself is not the problem. The failure occurs because adding a new item changes which older item survives the score-based cap.

Therefore the next design must not use a score-ranked local Statement cap.

R2 already has a stronger structural bound upstream:

```text
selected source Statement queries <= 12 total
```

and one source Statement query retains at most one point per candidate Object.

Therefore a candidate can contribute at most 12 Statement observations total across all Facets. The next design can retain all candidate hits corresponding to the already-selected source Statement queries without introducing unbounded work and without score-based replacement inside a Facet.

## 4. P8 root cause — max-over-Facet is an opportunity-count statistic

Candidate D used:

```text
best_detail = max(Facet cluster scores)
```

The diagnostic held overview and the per-Facet null score law fixed while changing only the number of eligible Facets from 1 to 8.

Under a symmetric `.7/.9` per-Facet fixture:

```text
narrow expected Object score ~= .800000000
wide expected Object score   ~= .849609375
wide strict wins             = 127 / 256
wide strict losses           = 0 / 256
```

This is not a Harrier empirical-noise claim. It is a structural property of the maximum: more independent opportunities increase the expected maximum.

Canonical anchoring does not remove this effect.

Therefore `max(Facet)` must be rejected for overall Object Similarity.

## 5. Contract correction forced by P8

The previous Candidate D contract required that a weak different-Facet cluster must never dilute the strongest existing Facet.

That property led directly toward max-like aggregation and conflicts with the requirement that wider Objects not receive a systematic opportunity bonus merely because they expose more Facets.

The next contract is therefore revised:

- same-Facet weak evidence must not increase its Facet-local Statement aggregate;
- adding a weak different-Facet cluster may lower a multi-Facet detail aggregate;
- adding a strong different-Facet cluster may raise it;
- missing Facets remain unknown/not observed and are not synthesized as zero;
- Facet count itself must not be multiplied into the score or used as a bonus;
- support count must remain inspectable even when it is not itself a score term.

Overall Similarity is no longer defined as `overview + strongest shared Facet`.

## 6. External design precedent

Score/rank fusion literature includes median aggregation (`Median`, `CombMED`) alongside CombMAX, CombSUM and related unsupervised fusion rules. Median aggregation is not unique to SGOKB and provides a parameter-free robust center that is less sensitive to a single extreme score than max.

Relevant references consulted in design review:

- RankAggregation-Lib: https://github.com/nercms-mmap/RankAggregation-Lib
- Comparative rank aggregation study including CombMED: https://pmc.ncbi.nlm.nih.gov/articles/PMC9857885/
- Field-level IR fusion discussion including CombMax / CombMed: https://www.mdpi.com/2078-2489/15/11/695

These references support median as a recognized fusion family. They do not prove SGOKB quality; the local diagnostic remains mandatory.

## 7. Candidate E — source-bounded Facet-median aggregation

Candidate E keeps the valid hierarchy from Candidate D but replaces both rejected operations.

```text
bounded candidate acquisition
        ↓
canonical same-Facet anchor resolution
        ↓
Facet clusters
        ↓
all retained observations from already-selected source Statement queries
        ↓
Facet-local Statement arithmetic mean
        ↓
median across eligible Facet cluster scores
        ↓
0.50 * overview + 0.50 * detail_median
```

### 7.1 Candidate acquisition

Unchanged:

```text
object_overview ANN
Facet ANN
Statement ANN
        -> candidate Object union
```

Source query bounds remain:

```text
Facet queries <= 8
Statement queries <= 12
ANN calls <= 21
raw ANN hit slots <= 464
```

### 7.2 Canonical Facet anchor

Retain Candidate D's validated rule:

```text
canonical same-Facet membership exists
in active generation/current accepted Version
```

Facet ANN appearance is not the anchor condition.

If needed, recover/reuse the candidate's stored canonical Facet embedding and compute direct cosine in the frozen Embedding Space.

No canonical anchor => no eligible Facet cluster.

### 7.3 Statement aggregation — no score-based local cap

For anchored Facet `F`, retain every candidate Statement observation produced by the already-selected source Statement queries for that same Facet after the existing per-source-query candidate-Object deduplication.

Do **not** select top-k Statements by candidate score inside the Facet.

Because there are at most 12 selected source Statement queries globally:

```text
candidate Statement observations across all Facets <= 12
candidate Statement observations in one Facet <= 12
```

Then:

```text
statement_mean(F)
  = arithmetic mean(all retained bounded same-Facet observations for F)
```

This restores the insertion property across distinct selected source queries:

```text
new score < current mean -> new mean decreases
new score > current mean -> new mean increases
```

Candidate Statement multiplicity within one source query remains protected by the existing per-source-query Object dedup rule.

### 7.4 Facet-local cluster score

Keep Candidate D's local role semantics:

```text
if Statement observations exist:
    cluster(F)
      = (.30 * facet_similarity(F)
         + .20 * statement_mean(F)) / .50

if no Statement observation exists:
    cluster(F) = facet_similarity(F)
```

There is no statement-only branch.

### 7.5 Object detail — median, not maximum

Let the eligible canonical anchored cluster scores be:

```text
s1, s2, ... sn
```

Define:

```text
detail_median = median(s1, ..., sn)
```

Use the ordinary statistical median:

- odd `n`: middle sorted value;
- even `n`: arithmetic mean of the two middle sorted values.

No threshold, exponent, temperature, coverage bonus or learned parameter is introduced.

Final score:

```text
object_score
  = .50 * bounded overview
  + .50 * detail_median
```

If there is no eligible anchored Facet cluster:

```text
detail_median = 0
```

### 7.6 Semantic interpretation

Candidate E changes the detail meaning to:

> **the typical shared canonical Facet similarity among the Facets for which comparable canonical evidence exists**

Therefore overall Object Similarity becomes:

> broad Object-level similarity + typical shared-Facet similarity

It is not breadth coverage, maximum similarity, probability or truth.

Missing Facets are not zero. Shared-Facet count is support metadata, not a multiplicative score bonus.

## 8. Static replay from Candidate D exact cluster scores

Using the exact Candidate D frozen-case cluster scores, Candidate E gives:

```text
Character overall
Mika:
  overview = .8281027313265004
  clusters = [.838926501197526,
              .8343115043549902,
              .7371034435099357]
  median   = .8343115043549902
  Object   = .8312071178407453

Ren:
  overview = .8327890599777558
  clusters = [.8277625481782572,
              .8184325044380436]
  median   = .8230975263081504
  Object   = .8279432931429531

Work
Ash Garden:
  median = .842605764295576
  Object = .857757151406386

Iron Crown:
  median = (.8341021500113786 + .7728402074003127) / 2
         = .8034711787058456
  Object = .8314102208486642

Concept
Altruism:
  median = .8068829591714837
  Object = .8256451816438397

Autonomy:
  median = (.7861060393665431 + .7677377411512384) / 2
         = .7769218902588908
  Object = .8153550453798410
```

Static ordering therefore restores all frozen Overall Similarity cases. `character_values` remains the unchanged Facet-specific cosine path.

These calculations are not acceptance evidence.

## 9. Static replay of the D/P8 null fixture

Using the same symmetric per-Facet `.7/.9` fixture and equal overview `.8`:

```text
1 Facet expected Object score = .8
8 Facet expected Object score = .8
```

For the exact 256 outcomes when the first Facet is shared between narrow/wide candidates:

```text
wide wins   = 64
wide losses = 64
 ties        = 128
```

Thus the specific one-sided maximum opportunity bias disappears in this fixture.

This does not prove facet-count invariance for every possible score distribution. The local diagnostic must test additional asymmetric and real-score cases and report any remaining support-count effect.

## 10. Risks that remain explicit

### 10.1 Sparse-support variance

A candidate with one shared Facet has `median = that one Facet score`. A candidate with many Facets has a more stable center.

Candidate E intentionally does not add a coverage bonus or missing penalty in the first diagnostic. The diagnostic must report whether one-Facet high-score cases create unacceptable sparse-support spikes.

### 10.2 Missing remains unknown

A missing Facet is not treated as zero. Therefore Candidate E does not reward coverage directly.

If later acceptance requires a coverage-aware score, that is a separate semantic design problem and must not be smuggled into this ablation through a hidden prior.

### 10.3 Explanation size

Candidate E can use up to 12 Statement observations total per candidate plus canonical Facet anchors. Explanation must stay bounded.

The diagnostic must distinguish:

- evidence needed to reproduce the numeric median;
- additional support metadata useful for inspection;
- public response payload limits.

Do not silently drop score-relevant observations before computing the score.

### 10.4 Candidate union before scoring

Candidate D noted that the current implementation truncates to 128 Objects after scoring the full union, while raw acquisition can expose up to 464 distinct Objects.

Candidate E must measure the bounded scorer-local cost under the actual order. Do not assume a pre-scoring 128 cap unless the design explicitly introduces and quality-validates such a boundary later.

## 11. Candidate E diagnostic acceptance boundary

Candidate E is not production-eligible from static replay.

Required checks include:

1. four frozen Phase-I Similarity cases;
2. Facet-specific path unchanged;
3. same-Facet weak insertion monotonicity across distinct selected source queries;
4. same-Facet strong insertion monotonicity;
5. no score-based local Statement replacement;
6. canonical Facet ANN-miss recovery;
7. no statement-only cluster without canonical anchor;
8. cross-Facet weak insertion must not increase the detail median;
9. cross-Facet strong insertion must not decrease the detail median;
10. D/P8 symmetric null fixture must lose its one-sided width advantage;
11. additional asymmetric facet-count fixtures;
12. one-Facet sparse-support spike probe;
13. permutation invariance;
14. duplicate source-query protection;
15. bounded scorer-local work and explanation;
16. fixed Character perturbation report;
17. R2SIM-G01..G06 if structural gates pass;
18. generation/current/history/source-exclusion contracts if structural gates pass;
19. active object_overall leakage = 0.

Do not tune numeric weights or introduce thresholds in this diagnostic.

If Candidate E fails a mandatory structural property, stop and return to design review.

## 12. Status

```text
R2-05 Semantic remediation = Complete / verified
R2-06 Candidate A = Rejected
R2-06 Candidate B = Rejected
R2-06 Candidate C = Rejected
R2-06 Candidate D revised = Rejected
R2-06 fourth design review = Complete
R2-06 Candidate E diagnostic ablation = Pending
R2-08 = FAIL / Not Complete
R2-09 = Blocked / Not Started
```


## Reference Workstation outcome (2026-10-24)

Candidate E diagnostic and production regression PASS. E10/E11 observations remain
explicit; no universal support-count invariance is claimed. See
`N05D04R2_R2_06_CANDIDATE_E_RESULT.md` and the machine-readable result.
R2-08 is not Complete; R2-09 remains blocked. No main merge.
