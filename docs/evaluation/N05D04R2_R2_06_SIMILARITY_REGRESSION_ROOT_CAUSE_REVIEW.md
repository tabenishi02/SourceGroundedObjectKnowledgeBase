# N05D-04R2 / R2-06 — Overall Similarity Regression Root-Cause / Remediation Review

Updated: 2026-10-24

Status: **Root-cause review complete / remediation direction selected / local causal proof and bounded ablation pending**

Scope: the two R2-08 Overall Object Similarity regressions only. R2-05 Semantic Search remediation is already verified on the parent branch and is not reopened here. R2-09 remains prohibited.

## 1. Trigger

R2-08 quality acceptance found two unintended Overall Similarity regressions under the fixed Harrier OSS v1 0.6B runtime:

```text
Overall Similarity
Phase-I: MRR 0.833333 / Recall@1 0.666667 / nDCG@10 0.876977
R2:      MRR 0.666667 / Recall@1 0.333333 / nDCG@10 0.753953
Recall@10 remains 1.0
```

The case-level failures are:

```text
work_overall
source: obj:glass_sky / 硝子の空
expected rank 1: obj:ash_garden / 灰の庭
R2 order: obj:iron_crown, obj:ash_garden

concept_overall
source: obj:self_sacrifice / 自己犠牲
expected rank 1: obj:altruism / 利他主義
R2 order: obj:autonomy, obj:altruism
```

R2-05 Semantic remediation did not modify Similarity and its unchanged quality harness reproduces the same two losses. Therefore these are independent R2-06 quality failures.

## 2. Current R2-06 scoring contract

R2 overall similarity uses:

```text
overview candidate search
+ same-Facet candidate searches
+ bounded same-Facet Statement searches
        ↓
per-source-query candidate Object deduplication
        ↓
component scoring
        ↓
weighted sum
```

Current constants:

```text
weights:
  overview  = 0.50
  facet     = 0.30
  statement = 0.20

candidate evidence caps:
  overview  = 1
  facet     = 2
  statement = 3
```

The current scorer defines the denominator from the **source** representation count:

```text
slots_j = min(component_cap_j, selected_source_count_j)
component_score_j = sum(candidate top bounded cosine values) / slots_j
```

A candidate that has fewer comparable same-Facet hits than `slots_j` therefore receives implicit zero-valued missing slots.

## 3. Static structural diagnosis

### 3.1 `work_overall`

Source `硝子の空` has:

```text
themes: loss / trust recovery / rebuilding
 tone: quiet / introspective / calm
```

Expected similar Object `灰の庭` has:

```text
themes: grief / mutual support / regeneration
relationships: cooperation / trust
```

Wrong rank-1 Object `鉄の王冠` has:

```text
themes: power competition / legitimacy of rule
tone: conflict / tension / aggressive
```

The expected Object shares the semantically decisive `themes` Facet but does not have `tone`. The wrong Object shares both canonical Facet keys `themes` and `tone` despite being semantically dissimilar in both theme and tone.

With the current source-slot denominator, `灰の庭` can fill only one of two Facet slots and one of the source Statement slots for those Facets. `鉄の王冠` can fill both `themes` and `tone` slots. The second shared Facet therefore creates additional positive evidence opportunity for the wrong candidate while the expected candidate receives an implicit zero for the absent source Facet.

### 3.2 `concept_overall`

Source `自己犠牲` has:

```text
definition
implications
```

Expected `利他主義` has:

```text
definition
related_concepts
```

Wrong rank-1 `自律` has:

```text
definition
implications
```

Again, the expected Object shares the semantically decisive `definition` Facet but not the source's second Facet key. The wrong candidate shares both canonical Facet keys and can fill more source-defined slots.

### 3.3 Primary root-cause hypothesis

**The current overall scorer conflates “candidate has no comparable same-Facet evidence for this source Facet” with “candidate has zero semantic similarity for this source Facet”.**

That creates a **shared-Facet coverage bias**:

```text
more source Facet keys shared
        ↓
more score slots can be filled
        ↓
more opportunities for positive bounded cosine
```

This is different from the already-protected raw Statement-count problem. R2SIM-G03 proves that many candidate Statements from one source query cannot create unbounded count boost and that evidence beyond the cap does not add direct score. It does **not** test the case where a candidate overlaps more distinct source Facets/source queries than a more semantically similar Object.

The two R2-08 failures have exactly that uncovered shape.

## 4. Why this is likely an aggregation problem rather than candidate-generation failure

Both expected candidates remain in the result set at rank 2 and Recall@10 remains 1.0. Therefore the current evidence does not indicate an ANN-recall or candidate-union miss.

Generation isolation, current-Version isolation, same-Facet hard boundaries, R2SIM-G01..G06, and Facet-specific cosine all pass. The failure is in **ordering among already retrieved candidates**.

The fixed Harrier model/revision/runtime must therefore remain unchanged during remediation.

## 5. Semantic interpretation of a missing Facet in overall mode

Explicit Facet Similarity has a strict contract: a candidate without the requested Facet is not a candidate.

Overall Object Similarity is different. Objects of the same Class may legitimately expose different content Facets. The R2 contract requires that Facet evidence compare only compatible same-Facet semantics; it does not require every candidate to contain every source Facet.

For overall ranking, absence of a comparable Facet should therefore be treated first as **missing / not comparable evidence**, not automatically as semantic dissimilarity of score zero.

A candidate that does contain the same Facet may still receive a low bounded cosine, and that low score is genuine comparable evidence of dissimilarity.

This distinction is the central remediation boundary.

## 6. Remediation options

### Option A — Candidate-local comparable-evidence mean

For each component, retain the current bounded top evidence selection, but normalize by evidence actually available for that candidate:

```text
candidate_hits_j = top bounded hits for component j, up to cap

if candidate_hits_j is empty:
    component_score_j = 0
else:
    component_score_j = sum(bounded_cosine(hit)) / len(candidate_hits_j)
```

The outer component weights remain:

```text
overview=.50 / facet=.30 / statement=.20
```

Advantages:

- directly removes the source-Facet coverage bias;
- missing same-Facet evidence is neutral rather than an implicit zero;
- a present but semantically poor same-Facet match still lowers the mean;
- preserves multiple corroborating/contradicting comparable evidence items;
- keeps all current caps, candidate generation, same-Facet boundaries, explainability and `[0,1]` final-score range;
- adds no tuning parameter.

Risk:

- one strong matched Facet can represent the whole Facet component when it is the only comparable Facet;
- adding a genuinely weak comparable Facet can reduce a candidate's component score. This is semantically defensible as additional evidence of mismatch, but must be tested.

Verdict: **preferred first remediation candidate**.

### Option B — Strongest-evidence / Max pooling

```text
component_score_j = max(bounded_cosine(candidate_hits_j))
```

Advantages:

- completely removes within-component coverage/count advantage;
- simple, bounded and parameter-free;
- allows a highly diagnostic same-Facet match to dominate generic secondary Facets.

Disadvantages:

- discards corroborating and contradictory secondary evidence;
- can overreact to one accidental high-similarity hit;
- hard MaxSim is a known multi-vector retrieval pattern, but hard maximum pooling can be brittle compared with smoothed alternatives, so it should not be frozen without local quality evidence.

Verdict: **bounded fallback ablation if Option A fails or shows unstable behavior**.

### Option C — Weight tuning only

Examples:

```text
increase overview weight
reduce Facet/Statement weight
```

Rejected as the first remedy. The observed failure is structurally tied to the denominator/coverage semantics. Weight tuning can hide the two cases without fixing the distinction between missing and dissimilar evidence and risks weakening R2SIM-G01/G02 detail tie-breaking.

### Option D — Class/Facet-specific importance weights

Rejected. SGOKB has no canonical global importance order such as `themes > tone` or `definition > implications`. Encoding such priorities from two benchmark cases would be brittle, Class-specific benchmark tuning.

### Option E — Cross-Facet fallback/comparison

Rejected. R2SIM-G04 and the frozen R2 contract require canonical Facet boundaries to remain hard. `relationships` must not be compared to `tone` merely to avoid a missing slot.

## 7. Selected remediation direction

Select the **missing-vs-zero correction** as the architectural direction.

The Reference Workstation must first verify the exact contribution decomposition. If the failure occurs as predicted, evaluate Option A as the primary candidate and Option B as a bounded fallback. Do not change weights, model, candidate limits, source query caps, Facet boundaries or representation content in the first ablation.

The exact pooling rule is **not frozen from static review alone**.

## 8. Required local causal proof

For both failing cases, record the source representations and both the expected and wrong candidate.

For every candidate record:

```text
overview:
  raw cosine
  bounded cosine
  contribution

facet:
  source Facet
  candidate same-Facet membership
  raw cosine
  bounded cosine
  admitted/rejected by cap
  current denominator slot count
  current contribution

statement:
  source Statement / Facet
  candidate same-Facet Statement
  raw cosine
  bounded cosine
  admitted/rejected by cap
  current denominator slot count
  current contribution

final:
  overview/facet/statement component scores
  weighted contributions
  hierarchical_similarity
  rank
```

Explicitly answer:

1. Does the expected Object have the strongest semantically relevant same-Facet raw cosine?
2. How much of the wrong Object's lead comes from filling the second Facet/Statement slot?
3. Does overview independently prefer the wrong Object?
4. Would candidate-local normalization alone reverse both failures?
5. Would top-1 pooling reverse both failures?
6. Are generation/current-Version/ANN candidate-union errors absent?
7. Is `object_overall` leakage zero?

If the wrong candidate remains stronger even after removing missing-slot penalties, stop. The static root-cause hypothesis is incomplete and weight tuning must not be used to force a pass.

## 9. Bounded ablation

Use exactly the same frozen embeddings and candidate hits where practical.

Compare:

```text
Control
  current source-slot mean

Candidate A
  candidate-local comparable-evidence mean

Candidate B
  strongest-evidence / max pooling
```

Do not run unrestricted parameter search.

For each candidate rule evaluate:

- all four frozen Phase-I Similarity cases;
- all six R2SIM-G01..G06 cases;
- Facet-specific Similarity unchanged;
- source/current/generation/filter contracts;
- work bounds unchanged;
- public score remains `[0,1]` and `score_type=hierarchical_similarity`.

Also add targeted synthetic probes:

1. **partial strong match vs broad weak coverage** — source has two Facets; true candidate has one strongly matching Facet and lacks the second; distractor has both Facets but both are weaker;
2. **missing is not zero** — absence of a source Facet must not itself create a numeric dissimilarity penalty in overall mode;
3. **present weak comparable evidence matters** — when both candidates have the same Facet, a genuinely weak second same-Facet match may lower the candidate-local mean rather than being ignored;
4. **single-hit spike guard** — one accidental high detail hit with poor broad context must not automatically defeat a consistently similar Object.

## 10. Selection rule

Prefer Candidate A if it:

```text
restores work_overall
restores concept_overall
preserves character_overall
preserves character_values
passes R2SIM-G01..G06
passes the four new probes
preserves Facet-specific cosine behavior
preserves generation/current/history behavior
preserves <=21 ANN / <=464 raw-hit / <=128 candidate bounds
preserves <=1/2/3 exposed evidence caps
introduces no new R2-05 Semantic regression
```

Candidate B is considered only if A fails or if local decomposition shows that averaging comparable evidence itself is the cause of an unexplained quality loss.

If neither passes, stop and return to design review. Do not alter Harrier or expand into arbitrary weight/pooling searches.

## 11. Implementation boundary after candidate selection

If Candidate A is accepted, the intended production change is narrowly inside R2 overall candidate scoring:

```text
current:
slots = min(cap, source_count)
component contribution denominator = slots

candidate:
admitted = candidate component hits after existing cap
component contribution denominator = len(admitted)
```

No change is intended to:

- source Facet/Statement selection;
- ANN query count/limits;
- candidate union/cap;
- same-Facet filtering;
- overview/facet/statement weights;
- evidence caps;
- bounded cosine;
- generation routing;
- current/historical semantics;
- Facet-specific raw cosine;
- Harrier/runtime;
- R2-05 Hybrid/Semantic fusion.

Update the R2-06 formula documentation and focused tests only after the local causal proof selects the rule.

## 12. External design note — non-normative

Multi-vector late-interaction retrieval commonly uses strongest local alignment rather than requiring every candidate vector set to cover every query-side vector in the same structural slot. ColBERT/ColBERTv2 are useful reference points for this design family, but SGOKB is not token-level ColBERT and must preserve canonical Facet boundaries.

Recent work also reports brittleness in hard maximum pooling and compares it with smoother top-k/softmax aggregation. This is why this review treats Max pooling as an ablation/fallback rather than assuming it is automatically superior.

External research is supporting context only. SGOKB's frozen gold and semantic contracts remain authoritative.

## 13. Current state

```text
R2-05 Semantic remediation = Complete / verified on parent branch
R2-06 original implementation = Complete
R2-06 quality remediation review = Complete
R2-06 local causal proof / remediation implementation = Pending
R2-08 = FAIL / Not Complete
R2-09 = blocked / Not Started
N05D-04R2 = Active
N-05 = BLOCKED / Not Complete
```

Do not start R2-09. Do not mark R2-08 Complete until the Similarity regressions are repaired and the unchanged full R2-08 acceptance is rerun.
