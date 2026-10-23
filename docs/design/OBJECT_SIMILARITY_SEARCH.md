# Object Similarity Search — Phase I / I-05 + R2 v2

更新日: 2026-10-23

- Status: **Phase-I v1 implemented / R2-02 v2 semantics frozen / R2-06 Complete / runtime verified**
- Original task: `I-05 [P0] find_similar_objects`
- Superseding task: `N05D-04R2 / R2-02 Requirements + representation contract revision`
- Prerequisites:
  - `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
  - `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
  - `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`
  - `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
- Normative R2 decision: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

---

## 1. 結論

`find_similar_objects()` remains an Object-to-Object retrieval operation that reuses stored Search Representation embeddings rather than embedding a new free-text query.

R2 splits the semantic contract by mode:

```text
facet=None
  -> hierarchical multi-vector Object similarity
     overview + same-Facet + bounded Statement evidence
     score_type = hierarchical_similarity

facet=<key>
  -> direct same-Facet vector similarity
     score_type = cosine_similarity
```

The Phase I v1 design used one `object_overall` vector for overall similarity. N05D-04R2 retires that monolithic comparison unit because the giant active representation caused unacceptable resource behavior and duplicated detailed Facet/Statement Knowledge.

The public Object-level operation remains stable; callers do not need to know or pass `object_overview`.

---

## 2. Overall similarity — active R2 semantics

When `facet is None`, similarity is hierarchical:

```text
Source Object
  ├─ object_overview
  ├─ content Facets
  └─ Statements
          ↓ bounded candidate/evidence work
Candidate Objects
  ├─ object_overview
  ├─ compatible/same Facets
  └─ Statements
          ↓ bounded aggregation
1 Object = 1 similarity result
```

The verified R2-06 algorithm combines:

```text
overview <-> overview
same-Facet <-> same-Facet
bounded Statement-level evidence
```

`object_overview` provides broad Object-level context but is **not** semantically equivalent to complete detailed Knowledge.

R2-06 selects candidate B and fixes the formula, query limits and evidence caps in Section 16. Local deterministic gold/regression verification passes; production cutover and real-model quality/performance acceptance remain later tasks.

---

## 3. Hierarchical invariants

Any R2-06 implementation must satisfy all of the following:

1. one Object remains one final result;
2. no active dependency on `object_overall`;
3. overview evidence compares `object_overview` to `object_overview`;
4. Facet evidence compares compatible/same Facet semantics;
5. Statement evidence contribution is bounded independently of Object Statement count;
6. no unbounded all-source-Statement x all-candidate-Statement comparison;
7. candidate count and per-channel contribution are bounded;
8. a large Object cannot win merely because it contains more Statements;
9. Source Object is excluded before final candidate limit;
10. current/historical Version semantics are preserved;
11. same Primary Class is the default candidate scope;
12. `cross_class=True` remains explicit expansion;
13. all raw vector comparisons occur within one Embedding Space;
14. deterministic final tie-break is retained;
15. contributing overview/Facet/Statement evidence remains inspectable.

---

## 4. Facet similarity — unchanged semantic contract

With `facet="personality"` or another explicit Facet key, compare only the same Facet:

```text
Source A / personality
        ↓
Candidate B / personality
Candidate C / personality
```

The direct vector-pair score remains:

```text
score_type = cosine_similarity
```

Forbidden:

- Source missing Facet -> overview fallback;
- Candidate missing Facet -> assign score 0;
- another Facet -> substitute;
- legacy `object_overall` -> substitute;
- `object_overview` -> substitute.

A Source Version without the requested content Facet is explicit unavailable/validation failure according to the existing API behavior. A Candidate without that Facet is not a candidate.

---

## 5. Source Version scope

Default source:

```text
find_similar_objects(object_id)
  ↓
source = current accepted Version
```

Historical source remains explicit:

```text
find_similar_objects(
    object_id,
    source_version_id="...",
)
```

A historical Source Version does not silently switch Candidate scope to historical. Candidate Objects remain current accepted by default.

Source Primary Class is resolved from the represented Version classification snapshot, not from a later Registry value.

---

## 6. Candidate scope

### 6.1 Default

```text
accepted Version
+ current Version
+ active Object
+ same Primary Class as source Version
+ source Object excluded
```

### 6.2 Cross-class

Only explicit:

```text
cross_class=True
```

removes the same-Primary-Class constraint.

Class-crossing similarity remains a derived semantic relation for discovery, not canonical Object Relation truth.

---

## 7. Source Object exclusion

Self exclusion remains a candidate-generation constraint, not a post-limit cleanup.

R2 overall mode must exclude source `object_id` from every candidate-acquisition channel before channel/final limits are consumed.

Facet mode retains the same behavior.

---

## 8. Score semantics

### 8.1 Overall mode

Final score:

```text
score_type = hierarchical_similarity
```

This is a bounded derived Object-ranking score composed from multiple representation-level signals.

It is not:

- a raw cosine similarity;
- a probability;
- truth;
- confidence;
- Source trust.

Raw component vector pairs may use:

```text
raw_score_type = cosine_similarity
```

within the fixed Harrier Embedding Space.

Section 16 defines the selected formula so the numerical meaning of `hierarchical_similarity` is reproducible.

### 8.2 Facet mode

Because Source/Candidate compare the same Facet representation in the same Embedding Space:

```text
score_type = cosine_similarity
```

The score is still semantic proximity, not truth/confidence.

---

## 9. Embedding reuse

Similarity reuses stored embeddings. It does not re-embed canonical text on every query.

Benefits remain:

- no unnecessary GPU recomputation;
- deterministic Source representation reuse;
- same Embedding Space enforcement;
- historical Source reproducibility.

Missing required Source embeddings produce explicit failure. Do not silently switch model/provider/backend.

The first R2 baseline remains Harrier OSS v1 0.6B / 1024-dim.

---

## 10. Representation / membership identity

Embedding cache and Vector Index remain membership-aware:

```text
Embedding cache:
representation_id -> vector

Vector Index:
membership_id -> vector + Object / Version / Class / Facet / Statement metadata
```

R2 overall similarity may consume multiple representation/membership pairs for one Source and one Candidate, but every contributing pair remains individually identifiable.

Content reuse never merges current/historical membership semantics.

---

## 11. Defensive current verification

Qdrant remains Derived Search state. Candidate hits must be defensively verified against canonical SQLite state.

At minimum verify:

```text
accepted Version
active/archive scope
Object.current_version_id == membership.version_id
expected active representation kind
effective generation identity
same Primary Class unless cross_class=True
same Facet in facet-specific mode
```

Stale legacy `object_overall` points must not enter active R2 results even if they remain physically present during side-by-side migration.

---

## 12. Result contract

The public operation remains source-compatible where possible.

### 12.1 ObjectSimilarityResponse

Conceptual stable fields:

```text
source_object_id
source_name
source_primary_class
source_version_id
source_representation_id
facet
cross_class
results
```

For overall R2 mode, `source_representation_id` may identify the source `object_overview` as the broad anchor. It must not be documented as the sole representation used to compute the final score.

### 12.2 SimilarObjectResult

Stable/base fields:

```text
object_id
name
primary_class
version_id
rank
score
score_type
matched_facet
representation_id
membership_id
```

Overall R2 mode:

```text
score_type = hierarchical_similarity
matched_facet = null
representation_id / membership_id = candidate object_overview anchor where retained for compatibility
```

Facet mode:

```text
score_type = cosine_similarity
matched_facet = requested Facet
representation_id / membership_id = compared Facet membership
```

`version_id` is always the Candidate Version actually scored.

---

## 13. Additive multi-vector explainability

Overall hierarchical results require bounded component evidence.

The result must be able to expose a bounded list equivalent to:

```text
channel                    # overview | facet | statement
source_representation_id
source_membership_id
candidate_representation_id
candidate_membership_id
representation_kind
facet?
source_statement_id?
candidate_statement_id?
raw_score
raw_score_type             # cosine_similarity
contribution               # selected algorithm's bounded contribution
```

`ObjectSimilarityEvidence` implements these frozen information semantics as additive result evidence; the existing result fields remain available.

Do not emit an unbounded list of every Statement pair merely for explanation.

---

## 14. Failure behavior

Explicit failure/unavailable remains required for:

- unknown source Object;
- no current Source Version when current is requested;
- Source Version not accepted;
- unknown Facet;
- Source missing requested content Facet;
- required active Search Representation missing;
- required Source embedding missing from selected Embedding Space;
- Vector backend unavailable;
- active generation incoherent/unavailable.

Forbidden:

- missing Facet -> overall/overview fallback;
- another Embedding Space -> silent switch;
- another Vector backend -> silent switch;
- external Provider -> silent switch;
- historical Candidate -> silent mix;
- legacy `object_overall` -> active R2 fallback.

Canonical SQLite Knowledge is not modified by Similarity failure.

---

## 15. Relationship to Hybrid Search

### Hybrid Object Search

Input:

```text
free-text query
```

Active semantic channels:

```text
object_overview
facet
statement
```

Final score:

```text
rrf
```

### Object Similarity

Input:

```text
source Object ID
```

Overall mode:

```text
hierarchical multi-vector aggregate
score_type = hierarchical_similarity
```

Facet mode:

```text
same-Facet vector pair
score_type = cosine_similarity
```

Hybrid RRF and overall Similarity aggregation are separate contracts even if R2-06 later chooses rank-fusion techniques internally.

---

## 16. Verified R2-06 algorithm

Candidate B is implemented: overview + same-Facet + bounded same-Facet Statement
candidate union, followed by bounded component aggregation. Candidate A loses
child-only discovery; candidate C does not preserve inspectable detailed evidence.
The implementation record documents the selection rationale and tie-breaking:
[Hierarchical Object Similarity](../planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md).

| Component | Source queries | Hits per query | Base weight | Evidence cap |
|---|---:|---:|---:|---:|
| overview | 1 | 128 | 0.50 | 1 |
| Facet | 8 | 24 | 0.30 | 2 |
| Statement | 12 | 12 | 0.20 | 3 |

Select Facets by canonical key, then select faceted Statements deterministically
by round-robin over canonical Facets. Every query excludes the source before its
limit, and filters generation/current membership, Class and exact Facet as applicable.
Per source query retain only the best hit per candidate Object. The maximum work
is 21 ANN calls / 464 returned hit slots. Aggregate and deterministically order
Objects, then cap candidates at 128 before applying the caller's result limit.

For active source components, normalize their base weights to sum to one. For
component `j`, `slots_j = min(evidence_cap_j, selected_source_count_j)`. Preserve raw
cosine in evidence, but use `max(0, min(1, cosine))` for ranking. Sum the top capped
bounded cosines, divide by `slots_j`, then multiply by the normalized component
weight. Missing candidate evidence contributes zero. Sum the component contributions
for `hierarchical_similarity` in `[0,1]`. Explanation is capped at six items.

G01-G06 deterministic gold contracts pass: Facet/Statement tie-breaking, no count
boost, canonical Facet boundary, generation/history integrity and boundedness.
These checks establish bounded work and deterministic semantics; they do not claim
measured production ANN latency or real-model retrieval quality. R2-07 remains
Not Started; R2-08/R2-09 retain quality/resource/performance acceptance.

---

## 17. R2 implementation test requirements

Focused regression must cover at least:

- hierarchical overall similarity;
- source Object exclusion before limits;
- same Primary Class default;
- explicit cross-class expansion;
- Facet similarity same-Facet only;
- Source missing Facet explicit failure;
- Candidate missing Facet excluded;
- current Candidate Version only;
- historical accepted Source Version explicit use;
- target Version preserved in result;
- no active legacy `object_overall` dependence;
- same Embedding Space enforcement;
- bounded Statement contribution;
- deterministic tie-break;
- additive component explainability bounded;
- SQLite/Qdrant semantic parity;
- legacy v1 points cannot leak into active v2 results.

---

## 18. Historical Phase I v1 note

Phase I/I-05 originally defined overall similarity as:

```text
object_overall <-> object_overall
score_type = cosine_similarity
```

This remains historical evidence and explains existing v1 implementation/tests/results. It is superseded for active R2 by the hierarchical contract above.

Facet-specific direct cosine semantics remain valid and are carried forward.

---

## 19. R2-02 freeze / R2-06 handoff

Frozen in R2-02:

```text
public Object-level operation stable
facet=None => hierarchical multi-vector
facet=<key> => same-Facet cosine
final overall score_type = hierarchical_similarity
raw component score type = cosine_similarity
same-Class default / cross-class explicit
self exclusion before limit
current/historical semantics preserved
bounded contributions and bounded explanation
no object_overall active fallback
no unbounded Statement cross-product
```

Selected and locally verified in R2-06:

```text
candidate B: overview + same-Facet + same-Facet Statement union
query caps 1/8/12; per-query limits 128/24/12
21 ANN calls; 464 raw hit slots; 128 candidate Objects
weights 0.50/0.30/0.20; contribution/evidence caps 1/2/3
bounded cosine, active-source weight normalization, deterministic ordering
```

Pre-cutover and active Phase-I v1 generations retain `object_overall` raw-cosine
semantics. Only an active R2 generation uses the hierarchical family. Application,
CLI and MCP require no new representation/generation arguments; additive evidence,
source membership and generation identifiers preserve the base output fields.

**Status: R2-02 semantics frozen / R2-06 Complete / R2-07 Next, Not Started.**
