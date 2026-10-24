# N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign

## R2-10 closure update (2026-10-24)

Status: **Complete / Accepted**.

```text
R2-01 ... R2-10 = Complete
N05D-04R2 = Complete
N05D-04   = Complete
N-05      = Complete / PASS
```

The redesign defined below is no longer a pending target. It is the accepted active Derived Search architecture. R2-08 quality acceptance and R2-09 formal performance/resource acceptance both passed. The accepted formal run used Harrier OSS v1 0.6B unchanged and required no truncation, CPU fallback, model downgrade, attention-backend substitution or performance-gate relaxation.

Accepted active structure:

```text
object_overview + facet + statement
→ bounded Hybrid Object aggregation
→ hierarchical Object Similarity
→ generation-scoped Qdrant serving
→ 1 Object = 1 result
```

Legacy `object_overall` remains historical/readable for compatibility and retained evidence but is excluded from active R2 serving.

Closure authority: `docs/evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md`.

---

## Historical design record retained below

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Status: **Active / R2-01〜R2-03 Design Freeze complete / implementation pending**
- Decision: **replace the giant active `object_overall` embedding path with hierarchical multi-representation retrieval**
- Trigger: N05D-02 / N05D-04 showed that the 18,847-token Large `object_overall` enters a severe full-attention / WDDM shared-memory regime on the Reference Workstation.
- Model during redesign baseline: **Harrier OSS v1 0.6B remains fixed**.
- Formal N-05: **BLOCKED / Not Complete** until this redesign is implemented, quality-validated, and formally remeasured.
- R2-01 freeze: `docs/planning/phases/N/N05/N05D04R2_IMPACT_SURVEY.md`
- R2-02 freeze: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`
- R2-03 freeze: `docs/planning/phases/N/N05/N05D04R2_PERSISTENCE_VERSIONING_MIGRATION_DESIGN.md`

## 1. Decision

SGOKB will not continue treating an Object's complete accepted Knowledge as one mandatory semantic text blob for active object-level retrieval.

The target Derived Search structure is:

```text
Object
├─ object_overview   # compact Object-level semantic representation
├─ facet             # existing per-Facet representation
└─ statement         # existing per-Statement representation
       ↓
 multi-representation candidate generation
       ↓
 Object aggregation / similarity aggregation
       ↓
 1 Object = 1 result
```

This is a structural remediation, not arbitrary fixed-size chunking. The partition boundaries come from SGOKB canonical semantics: Object / Facet / Knowledge Statement.

## 2. Why the current design changes

Phase I already adopted:

- Object / Facet / Statement multi-representation Semantic Retrieval;
- Statement-level Embedding;
- Statement → Object aggregation;
- membership-scoped Vector points;
- `1 Object = 1 result`.

However, current `SearchRepresentationBuilder.build_object_overall()` also concatenates every content-Facet Statement into `object_overall`, then `materialize_version()` separately emits the same Knowledge as Facet and Statement representations.

The active semantic layer therefore duplicates detailed Knowledge across:

```text
object_overall
facet
statement
```

For the N-05 Large fixture, that duplication produces an 18,847-token `object_overall`. N05D-02 measured approximately 51.1 GiB Torch peak allocation, approximately 34.2 GiB Windows Shared GPU memory, and approximately 628–643 seconds for this one full representation on the frozen Harrier 0.6B runtime.

The redesign removes this long-input duplication while preserving detail in existing Facet / Statement representations.

## 3. Target representation contract

### 3.1 New active Object-level kind: `object_overview`

Introduce a new Search Representation kind rather than silently changing the meaning of persisted `object_overall`.

`object_overview` is deterministic and contains only bounded Object-level context that is canonical without generative summarization:

```text
Object canonical name
aliases
Primary Class
Facet-less Summary Statements
content Facet identities (name/key), but not their full Statement bodies
known structured Attributes
Relation text
```

It MUST NOT re-copy every content-Facet Statement.

No LLM-generated summary is introduced by this redesign.

### 3.2 Historical `object_overall`

`object_overall` v1 remains identifiable as historical Derived Search evidence during migration and comparison.

After accepted cutover:

- new/current active materialization uses `object_overview`;
- old `object_overall` membership/vector artifacts are not used by normal current retrieval;
- historical diagnostic evidence is retained according to existing evidence-retention rules;
- rollback remains possible without modifying canonical Knowledge while the old generation remains compatibility-eligible.

`object_overall` is not renamed or reinterpreted as `object_overview`.

### 3.3 Facet and Statement representations

Existing Facet and Statement semantic boundaries remain the primary detailed Knowledge channels.

Facet:

```text
Object context
Primary Class
Facet identity
Statements belonging to that Facet
```

Statement:

```text
Object context
Primary Class
optional Facet context
optional Temporal Scope
optional Derivation
Statement text
```

R2-02 fixes their existing byte-level content contract as version 1 unless a later explicit design change modifies that content.

## 4. Search architecture after redesign

### 4.1 Free-text Object Search

The existing Phase I multi-channel architecture is preserved conceptually:

```text
query
 ├─ Registry lexical
 ├─ Knowledge lexical
 └─ Semantic
      ├─ object_overview
      ├─ facet
      └─ statement
             ↓
       channel-local Object aggregation
             ↓
       cross-channel fusion
             ↓
       1 Object = 1 result
```

`semantic_object_overall` becomes `semantic_object_overview` in the active design.

The first R2 baseline keeps the accepted Phase-I RRF/contribution-cap values unless later R2 quality evidence requires a separately justified change.

### 4.2 Object Similarity

The current overall similarity path directly compares one source `object_overall` vector with candidate `object_overall` vectors. That contract changes because the giant vector is retired.

The new `find_similar_objects(..., facet=None)` is a hierarchical multi-vector similarity operation rather than treating the compact overview as equivalent to all detailed Knowledge.

The semantic components are:

```text
object_overview ↔ object_overview broad similarity
same-Facet ↔ same-Facet similarity
bounded Statement-level evidence contribution
candidate-level bounded aggregation
explainable matched overview / Facet / Statement evidence
```

Requirements:

- one Object remains one final result;
- Object size / Statement count must not create unbounded score boost;
- source/candidate current-historical and Class filters remain correct;
- Facet-specific similarity retains same-Facet semantics;
- final overall score type is `hierarchical_similarity`, not raw cosine;
- score is never treated as truth/confidence;
- result evidence retains representation/membership identity.

The exact bounded aggregation algorithm/caps/weights remain R2-06 implementation/evaluation work. It must avoid `O(all source statements × all candidate statements)` unbounded execution.

## 5. Embedding model policy during redesign

Keep the current accepted Embedding identity fixed for the first redesign baseline:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
```

Reason:

- changing representation structure and model simultaneously would destroy causal attribution;
- the redesign should first demonstrate whether removing the giant long-input path solves the resource problem;
- Harrier 270M remains a later candidate only if the redesigned system still fails performance/resource or operational goals.

N05D-04R1 attention-backend experimentation is retained as diagnostic evidence but is not the primary remediation path after this decision.

## 6. Data / schema / versioning impact — R2-03 resolved

The redesign is Derived Search only. Canonical Object Knowledge, Source, Evidence, Version, Facet, Statement, Attribute, and Relation data are not rewritten to implement it.

R2-03 fixes the persistence/versioning contract as follows.

### 6.1 Representation kind persistence

Active/legacy kinds coexist in persistence during migration:

```text
object_overview  # active R2
object_overall   # legacy v1 readable only
facet
statement
evidence
```

Existing `object_overall` rows are preserved and never relabeled to overview.

### 6.2 Builder version

```text
builder_key      = sgokb-canonical-search
object_overall   = builder version 1 / legacy only
object_overview  = builder version 2
facet            = builder version 1 while unchanged
statement        = builder version 1 while unchanged
evidence         = builder version 1 / unaffected
```

Builder content-contract version is separate from Derived Search generation identity.

### 6.3 Forward migration

The next migration is reserved as:

```text
018_search_generation_contract.sql
```

Historical migrations are not edited.

Migration 018 is a schema/coexistence migration. It does not perform R2 cutover and does not delete v1 artifacts.

### 6.4 Knowledge Search generation identity

R2 introduces explicit Knowledge Search generations.

Conceptually:

```text
Phase-I v1 generation
  object_overall + facet + statement

R2 v2 generation
  object_overview + facet + statement
```

Generation membership is stored by a separate generation→Knowledge-membership link. Existing Facet/Statement membership identity is not duplicated merely because both generations use it.

### 6.5 Embedding reuse

Embedding identity remains:

```text
representation_id + embedding_space_id
```

Therefore unchanged Facet/Statement embeddings may be reused in the same Harrier space; an `object_overview` cannot reuse an `object_overall` embedding.

### 6.6 Vector generation identity

Vector namespace identity becomes:

```text
Knowledge Search generation
+ Embedding Space
+ Vector backend
```

The v2 candidate receives a fresh Qdrant namespace rather than rebuilding the serving v1 collection in place.

Vector point identity remains Knowledge membership ID inside one generation-specific namespace. Payload gains generation identity for defensive verification.

### 6.7 Active routing

One explicit SQLite active-generation pointer is the serving truth.

Normal Knowledge lexical/semantic/similarity operations resolve this generation once at request start and must not mix generations across channels.

Evidence Search remains outside this Knowledge generation contract.

The normative persistence/migration design is:

`docs/planning/phases/N/N05/N05D04R2_PERSISTENCE_VERSIONING_MIGRATION_DESIGN.md`.

## 7. Migration and cutover strategy — R2-03 resolved

Use a side-by-side Derived Search migration. Do not destructively overwrite v1 artifacts first.

Target flow:

```text
canonical accepted Knowledge
  ├─ Phase-I v1 generation                 # retained serving/rollback candidate
  └─ R2 v2 candidate generation
       ├─ object_overview v2 membership
       ├─ reusable facet v1 memberships
       └─ reusable statement v1 memberships
                ↓
        reuse/generate Harrier embeddings
                ↓
        build isolated generation-specific Qdrant namespace
                ↓
        membership/digest/payload/quality validation
                ↓
        atomic SQLite active-generation pointer switch
                ↓
        current retrieval uses v2 only
```

Required safety properties:

- canonical DB content unchanged;
- old formal/diagnostic evidence untouched;
- old active Vector state not deleted before candidate rebuild and validation;
- failed/interrupted candidate rebuild leaves active pointer unchanged;
- active retrieval never infers the newest generation automatically;
- v1/v2 Knowledge candidate sets are never unioned in one normal request;
- old v1 remains a rollback target only while its catalog/integrity state is compatible;
- rollback changes Derived Search routing only and never rolls back canonical Knowledge;
- stale v1 memberships cannot silently mix with current v2 results after cutover.

Cutover is a routing transaction after the candidate artifacts already exist; Qdrant mutation is not performed inside the switch transaction.

## 8. Resource acceptance goals

This redesign is not allowed to pass by truncating the accepted Knowledge.

For the existing N-05 Large fixture, acceptance must demonstrate:

1. no active mandatory representation concatenates all 1,200 Statements into one model input;
2. `object_overview` does not contain content-Facet Statement bodies;
3. no silent truncation / chunk loss / CPU fallback occurs;
4. every accepted Statement remains searchable through Statement representation;
5. every content Facet remains searchable through Facet representation;
6. total Derived Search sync can complete under the Reference Workstation resource envelope;
7. the 32 GiB formal disk preflight remains in force;
8. Harrier 0.6B stays fixed for the first redesign acceptance run.

Engineering diagnostic target:

```text
Large fixture object_overview <= 4096 tokens without truncation
```

This is not a semantic truncation rule. If deterministic Object-level canonical fields exceed the target, the design must be reviewed rather than cutting text to fit.

## 9. Search-quality acceptance

Before N-05 formal rerun, the redesign must pass Retrieval acceptance because it changes semantic candidate generation and Object Similarity behavior.

At minimum:

- existing frozen search gold remains runnable;
- Hybrid Object Search does not materially regress required Recall/MRR/nDCG contracts;
- Statement and Facet retrieval remain intact;
- exact identity priority remains intact;
- current/historical, Class, Facet, temporal, derivation filters remain intact;
- overall Object Similarity receives dedicated new gold cases that require detailed Facet/Statement semantics, not only names/summaries;
- ranking explanations retain matched representation/membership identity;
- generation isolation/no-mixing is explicitly checked;
- N-06 evaluation is rerun or extended as required before final design acceptance.

No model downgrade is used to mask a representation-quality regression.

## 10. Performance acceptance

After quality acceptance, N-05 is rerun from the beginning with a new run ID.

The formal workload and gates remain unchanged unless a separate requirement decision changes them:

```text
Standard cold 3 + warm 20
Large cold    3 + warm 20

Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

The benchmark must record the active generation and representation/builder identity so v1 and v2 results cannot be confused.

## 11. Non-goals

This redesign does not automatically:

- switch to Harrier 270M;
- install FlashAttention-2;
- upgrade PyTorch/CUDA/driver;
- change Qdrant backend;
- introduce LLM-generated summaries;
- truncate Object Knowledge to a token cap;
- replace canonical Facet/Statement structure with arbitrary token chunks;
- change N-05 performance gates;
- make Vector Search canonical state.

Any of those may become a separate future task only if evidence requires it.

## 12. Current execution state

```text
R2-01 Impact survey / redesign freeze                    Complete
R2-02 Requirements + representation contract revision   Complete
R2-03 Persistence/versioning/migration design            Complete
R2-04 object_overview builder implementation             Next
R2-05 Hybrid Search migration                            Not Started
R2-06 Hierarchical Object Similarity redesign            Not Started
R2-07 Derived Search rebuild / cutover / rollback        Not Started
R2-08 Search-quality acceptance                          Not Started
R2-09 Performance/resource + formal N-05 rerun           Not Started
R2-10 Closure                                            Not Started
```

## 13. Completion condition

N05D-04R2 is complete only when:

```text
requirements/design contracts updated
schema/versioning/cutover contract fixed
object_overview builder implemented
hybrid retrieval updated
hierarchical Object Similarity implemented
Derived Search rebuild/cutover verified
search-quality acceptance PASS
resource/performance pre-acceptance PASS
formal N-05 rerun is re-authorized
```

Task breakdown: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`.
