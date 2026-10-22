# N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Status: **Accepted direction / Design change planning**
- Decision: **replace the giant active `object_overall` embedding path with hierarchical multi-representation retrieval**
- Trigger: N05D-02 / N05D-04 showed that the 18,847-token Large `object_overall` enters a severe full-attention / WDDM shared-memory regime on the Reference Workstation.
- Model during redesign baseline: **Harrier OSS v1 0.6B remains fixed**.
- Formal N-05: **BLOCKED / Not Complete** until this redesign is accepted, implemented, quality-validated, and formally remeasured.

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
- rollback remains possible without modifying canonical Knowledge.

Do not reuse the name `object_overall` for materially different v2 semantics unless the design task explicitly proves that compatibility is safer than a new kind. The default plan is a new `object_overview` kind.

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

Their exact builder/version migration rules must be reviewed, but this redesign does not intentionally remove their current semantic content.

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

Existing contribution-cap and RRF behavior is not automatically changed. It must be regression-tested and adjusted only with quality evidence.

### 4.2 Object Similarity

The current overall similarity path directly compares one source `object_overall` vector with candidate `object_overall` vectors. That contract must change because the giant vector is being retired.

The new `find_similar_objects(..., facet=None)` must become a hierarchical multi-vector similarity operation rather than silently treating the compact overview as equivalent to all detailed Knowledge.

The detailed aggregation algorithm is a design task. It must evaluate at least:

```text
object_overview ↔ object_overview broad similarity
same-Facet ↔ same-Facet similarity
bounded Statement-level evidence contribution
candidate-level aggregation with contribution caps
explainable matched Facet / Statement evidence
```

Requirements:

- one Object remains one final result;
- Object size / Statement count must not create unbounded score boost;
- source/candidate current-historical and Class filters remain correct;
- Facet-specific similarity retains same-Facet semantics;
- raw similarity/ranking score is never treated as truth/confidence;
- result evidence must retain representation/membership identity.

The algorithm must avoid `O(all source statements × all candidate statements)` unbounded execution. Candidate generation and bounded second-stage aggregation must be designed and benchmarked explicitly.

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

## 6. Data / schema / versioning impact

The redesign is Derived Search only. Canonical Object Knowledge, Source, Evidence, Version, Facet, Statement, Attribute, and Relation data must not be rewritten to implement it.

Expected affected contracts/assets include:

```text
docs/requirements/SEARCH_REQUIREMENTS.md
docs/design/SEARCH_REPRESENTATION_SCHEMA.md
docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md
docs/design/OBJECT_SIMILARITY_SEARCH.md
docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md     # status/baseline note only if needed
src/sgokb/domain/knowledge.py                          # representation kind contract
src/sgokb/retrieval/search_representation.py
src/sgokb/retrieval/hybrid_search.py
src/sgokb/retrieval/object_similarity.py or equivalent
src/sgokb/storage/semantic_repository.py
Derived Search migrations / rebuild tooling
Qdrant membership/index rebuild path
search-quality gold / benchmark assets
N-05 benchmark evidence / documentation
N-06 Retrieval / Vector quality evaluation inputs
```

Schema/migration design must decide how `object_overview` is represented in persistent kind constraints and how v1 `object_overall` remains readable during transition.

## 7. Migration and cutover strategy

Use a side-by-side Derived Search migration. Do not destructively overwrite v1 artifacts first.

Target flow:

```text
canonical accepted Knowledge
  ├─ build v1 historical object_overall      # retained until acceptance
  └─ build v2 object_overview + facet + statement
                ↓
        embed / index in isolated candidate state
                ↓
        quality + similarity + performance evaluation
                ↓
        accepted cutover
                ↓
        current retrieval uses v2 active memberships
```

Required safety properties:

- canonical DB content unchanged;
- old formal/diagnostic evidence untouched;
- old active Vector state not deleted before candidate rebuild and validation;
- failed candidate rebuild cannot leave current retrieval half-switched;
- rollback to the previous Derived Search generation is possible without canonical rollback;
- stale v1 memberships cannot silently mix with current v2 results after cutover.

Whether side-by-side state requires a new builder version only, a new representation kind, a new Embedding Space identity, a new Vector namespace/generation marker, or a combination is resolved before implementation.

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

The benchmark must record the new representation/builder identity so v1 and v2 results cannot be confused.

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

## 12. Completion condition

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
