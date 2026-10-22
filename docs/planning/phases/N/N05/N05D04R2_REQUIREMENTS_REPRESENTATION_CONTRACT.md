# N05D-04R2 — Requirements + Representation Contract Revision

Status: **R2-02 Complete / Design Freeze**  
Date: **2026-10-23**  
Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`  
Prerequisite: `N05D04R2_IMPACT_SURVEY.md` — **R2-01 Complete**

## 1. Purpose

This document completes **R2-02 [P0] — Requirements and design contract revision**.

R2-01 established that the N05D-04 blocker is caused by the active representation architecture: one monolithic `object_overall` duplicates detailed canonical Knowledge that already exists under Facet and Statement boundaries and forces the full duplicate through one full-attention embedding input.

R2-02 freezes the implementation-visible semantics that replace that contract:

```text
compact object_overview
+ Facet representations
+ Statement representations
+ bounded Object aggregation
+ hierarchical Object Similarity
```

This is a semantic-boundary redesign. It is **not** arbitrary fixed-token chunking, token truncation, LLM summarization, a model downgrade, or a change to canonical Object / Facet / Statement Knowledge.

The following remain outside R2-02:

- no production code implementation;
- no migration SQL or schema cutover execution;
- no embedding/vector rebuild execution;
- no Hybrid Search production cutover;
- no hierarchical Similarity production implementation;
- no search-quality acceptance run;
- no formal N-05 rerun;
- no Harrier model change;
- no FlashAttention-2 introduction;
- no PyTorch/CUDA upgrade;
- no CPU fallback;
- no truncation workaround.

## 2. Current state after this decision

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Complete
R2-02 = Complete
R2-03 = Next / Not Started
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

R2-02 completion does not authorize formal N-05 timing.

## 3. Normative precedence

This document is the R2-02 amendment for the following active contracts:

```text
docs/requirements/SEARCH_REQUIREMENTS.md
docs/design/SEARCH_REPRESENTATION_SCHEMA.md
docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md
docs/design/OBJECT_SIMILARITY_SEARCH.md
```

Where older Phase I wording conflicts with this R2-02 contract, **R2-02 takes precedence** for the active R2 design.

The following remain historical records of what Phase I originally accepted and are not rewritten as if R2 had existed at that time:

```text
docs/planning/phases/I/PHASE_I_PREPARATION.md
docs/planning/phases/I/PHASE_I_CLOSURE_AUDIT.md
```

Those documents receive a superseding-amendment note only. Phase I remains historically Complete; N05D-04R2 is a later evidence-driven contract revision.

## 4. Canonical Knowledge boundary — unchanged

R2 does not change canonical semantic ownership.

The following remain canonical and unchanged:

- Object;
- Object Version;
- Class / classification snapshot;
- Facet;
- Knowledge Statement;
- Structured Attribute;
- Relation;
- Source;
- Evidence;
- Evidence Link;
- Provenance;
- temporal scope;
- accepted/current/historical semantics.

Derived Search remains:

```text
canonical SQLite Knowledge / Evidence
        ↓ deterministic representation builder
Search Representation
        ↓ Embedding Provider
Embedding
        ↓ Vector Index Adapter
Vector Index
```

Search Representation, Embedding, FTS, and Vector Index remain rebuildable derived state and cannot become canonical Knowledge.

## 5. Active representation kinds

### 5.1 Knowledge Search Representation family

The active R2 Knowledge family is:

| kind | semantic role | canonical membership |
|---|---|---|
| `object_overview` | compact Object-level context / broad discovery anchor | Object + Version |
| `facet` | one canonical content Facet | Object + Version + Facet |
| `statement` | one searchable accepted Knowledge Statement | Object + Version + optional Facet + Statement |

`evidence` remains the independent Evidence Search representation family and is not changed by this redesign.

### 5.2 `object_overall` is retired from active retrieval

`object_overall` is a **v1 legacy Derived Search kind** after R2 cutover.

It may be recognized only for:

- forward migration;
- rollback/recovery mechanics;
- historical inspection;
- historical benchmark/evidence interpretation;
- controlled cleanup of v1 derived artifacts.

It must not be used by normal active post-R2:

- Search Representation materialization;
- Object Semantic Search;
- Knowledge lexical search as the active broad Object representation;
- overall Object Similarity;
- new embedding memberships;
- new Vector Index memberships.

### 5.3 `object_overview` is not a rename or semantic alias

The following are prohibited:

```text
relabel old object_overall row -> object_overview
reuse old object_overall representation ID as overview identity
parse old object_overall and silently expose it as overview
keep active code selecting object_overall while only changing display name
```

The new kind has a different content contract and therefore a different content identity.

Any temporary code-level compatibility alias must be bounded to legacy handling and must not blur persisted v1 semantics with active v2 semantics. R2-03 will define the exact enum/schema compatibility mechanism.

## 6. Exact `object_overview` semantic contract

`object_overview` is deterministic, non-generative, and structurally compact. It contains only canonical Object-level context that is useful across broad retrieval modes without copying detailed Facet Statement bodies.

### 6.1 Included fields

In deterministic order, the representation contains:

1. **Object canonical name**.
2. **Aliases**, deterministically normalized and ordered.
3. **Primary Class** from the represented Version's classification snapshot.
4. **Facet-less Summary Statements** belonging to that accepted Version.
5. **Content Facet identity inventory**: Facet key/name only, deterministically ordered.
6. **Known searchable Structured Attributes** represented as canonical key/display-value text without internal IDs.
7. **Relations**, represented deterministically from canonical Relation semantics and human-readable endpoint/Relation labels.

A representative logical form is:

```text
Object: <canonical name>
Aliases: <deterministic aliases>
Primary Class: <class key> (<display name>)
Summary:
  <facet-less summary statement(s)>
Facets:
  <facet key/name inventory only>
Attributes:
  <searchable structured attribute text>
Relations:
  <canonical relation text>
```

Exact delimiters and normalization are builder details, but the semantic field set above is frozen.

### 6.2 Excluded fields

`object_overview` must not contain:

- content-Facet Statement bodies;
- copies of all Statement text under each Facet;
- Statement IDs / UUIDs;
- Facet IDs / internal database IDs;
- Evidence content or Evidence IDs;
- gap records;
- insufficient-evidence management text;
- unresolved-reference records;
- Registry proposals;
- conflict-management records themselves;
- workflow/status/debug metadata;
- LLM-generated synthetic summaries;
- token-window filler or arbitrary chunks.

### 6.3 Relation decision

Relation semantics remain Object-level context and therefore **stay in `object_overview`**.

If a canonical `relationships` content Facet exists, the same Relation semantics may also be represented in that Facet according to the existing Facet contract. This is an intentional semantic-role overlap, not permission to duplicate arbitrary Facet Statement bodies into the overview.

R2 does not introduce an independent `relation` representation kind.

### 6.4 Boundedness rule

The overview is bounded by **semantic role**, not by destructive token truncation.

The N-05 Large-fixture engineering diagnostic target remains:

```text
object_overview <= 4096 tokens
```

No truncation is allowed to force that target. If the deterministic included fields exceed it, R2 returns to design review before acceptance.

## 7. Facet representation contract — retained

Facet remains a first-class canonical semantic boundary.

Active Facet representation continues to mean:

```text
Object context
Primary Class
Facet identity
Statements belonging to that content Facet
```

Only `status = content` Facets participate in the normal semantic family.

`insufficient_evidence`, `not_applicable`, and `not_analyzed` do not become semantic content merely because R2 changes Object-level representation.

R2 does not split Facets into arbitrary token chunks.

## 8. Statement representation contract — retained

Statement remains the finest standard semantic boundary for accepted searchable Knowledge.

Active Statement representation continues to include only the deterministic context required to preserve meaning, such as:

```text
Object context
Primary Class
optional Facet context
optional Temporal Scope
optional Derivation
Statement text
```

Statement IDs and other internal identities remain membership/provenance metadata rather than semantic text.

R2 does not merge unrelated Statements into synthetic chunks and does not truncate Statement text to repair the N05D-04 blocker.

## 9. Evidence representation — unchanged

Evidence Search remains independent from Object Knowledge Search.

R2 does not change the `evidence` representation contract, Evidence generation identity, or provenance semantics.

Evidence must not be mixed into the Object overview merely to improve search recall.

## 10. Builder key / version policy

Content identity and Derived Search generation identity remain separate concepts.

### 10.1 Builder key

Keep:

```text
builder_key = sgokb-canonical-search
```

R2 is a versioned contract change of the canonical search builder, not a new unrelated builder family.

### 10.2 Builder version

Freeze the active version policy as follows:

```text
object_overall     -> historical builder version 1 only
object_overview    -> builder version 2
facet              -> version 1 while its byte-level content contract is unchanged
statement          -> version 1 while its byte-level content contract is unchanged
evidence           -> version 1; unaffected by R2
```

A builder version is a **content-contract identity**, not a whole-index generation number. Unchanged Facet/Statement/Evidence content must not be falsely version-bumped merely to label a cutover.

If a later R2 task changes Facet or Statement byte-level content, that kind must receive its own explicit version bump at that time.

R2-03 must introduce/confirm a separate Derived Search generation/cutover identity so a coherent v2 active set can contain representation kinds with different content-contract versions without allowing mixed v1/v2 active retrieval.

## 11. Search Representation identity / reuse

Reuse remains valid only under:

```text
same kind
AND same builder_key
AND same builder_version
AND same content_hash
```

Therefore:

- old `object_overall` content cannot be reused as `object_overview`;
- unchanged Facet/Statement content may remain reuse-eligible under their existing kind/version/content identity;
- Version membership/current-historical identity is never merged merely because representation content is reusable;
- Embedding reuse additionally requires the same Embedding Space.

## 12. Hybrid Object Search v2 contract

### 12.1 Active channels

The active post-R2 channels are:

```text
exact_name
exact_alias
registry_lexical
knowledge_lexical
semantic_object_overview
semantic_facet
semantic_statement
```

`semantic_object_overall` is legacy-only after cutover.

Knowledge lexical search uses the active Knowledge representation family:

```text
object_overview
facet
statement
```

### 12.2 Fusion baseline

R2 retains the accepted Phase I baseline unless R2-08 quality evidence later requires a separately justified change:

```text
RRF k = 60

object_overview semantic contribution cap = 1
facet semantic contribution cap           = 2
statement semantic contribution cap       = 3
knowledge lexical contribution cap        = 3
```

The overview contributes at most one Object-level semantic hit. Facet and Statement count cannot produce unbounded Object boost.

Exact identity remains a separate priority tier:

```text
exact name
  > exact alias
  > non-exact lexical / semantic result
```

### 12.3 Scope safety

Facet-scoped search must exclude `object_overview` from candidate generation.

Facet-scoped active semantic kinds are:

```text
facet
statement
```

with the requested Facet boundary enforced.

Derivation/temporal filters that apply to individual Statements remain Statement-only where broader aggregate representations cannot safely satisfy the filter.

No overview, other Facet, or broad Object representation may silently satisfy a narrower semantic filter.

### 12.4 Result unit and explainability

The public result unit remains:

```text
1 Object = 1 result
```

Object aggregation must retain bounded matched evidence and identify `object_overview`, Facet, or Statement as the actual matching representation kind.

`representation_kind=object_overall` is not emitted by normal active post-R2 retrieval.

## 13. Overall Object Similarity v2 contract

### 13.1 Public operation remains stable

The public operation remains conceptually:

```text
find_similar_objects(object_id, facet=None, ...)
```

Callers are not required to know or send `object_overview`.

### 13.2 Overall similarity becomes hierarchical multi-vector

When `facet is None`, Object similarity is no longer defined as one `object_overall` cosine comparison.

The semantic components are:

```text
overview <-> overview
same-Facet <-> same-Facet
bounded Statement-level evidence
        ↓
bounded candidate-level aggregation
        ↓
1 Object = 1 similarity result
```

The final score is a **derived hierarchical Object-ranking score**, not a raw cosine similarity.

Freeze:

```text
score_type = hierarchical_similarity
```

This value means a bounded multi-vector aggregate in one Embedding Space. It must not be interpreted as a probability, truth score, confidence score, or a single-vector cosine.

The exact bounded candidate-generation/aggregation formula, numeric caps, and any component weights are selected and quality/latency-validated in R2-06. That task may choose among algorithms only if all choices obey the semantic contract in this section.

### 13.3 Required hierarchical invariants

Any R2-06 algorithm must satisfy all of the following:

- `object_overview` provides broad Object-level context but is not treated as equivalent to full detailed Knowledge;
- Facet evidence compares compatible/same Facet semantics;
- Statement evidence contribution is bounded independently of Object Statement count;
- no unbounded all-source-Statement x all-candidate-Statement comparison;
- candidate count and per-channel contribution are bounded;
- large Objects cannot win merely because they contain more Statements;
- Source Object is excluded before final candidate limit;
- same Primary Class remains default candidate scope;
- `cross_class=True` remains explicit expansion;
- historical Source/current Candidate semantics remain intact;
- all compared raw vectors are from the same Embedding Space;
- deterministic final tie-break is retained.

### 13.4 Facet-specific Similarity remains direct same-Facet similarity

When a Facet is explicitly requested:

```text
source Facet vector <-> candidate same-Facet vector
score_type = cosine_similarity
```

No fallback to overview or another Facet is allowed.

A missing Source Facet is explicit unavailable/error according to the existing API contract. A candidate without that Facet is not a candidate; it is not assigned zero similarity.

## 14. Multi-vector Similarity explainability contract

The existing public response shape should remain source-compatible where possible, but overall hierarchical mode requires additive evidence fields.

### 14.1 Compatibility anchors

For overall mode, the existing single-representation identity fields may identify the source/candidate `object_overview` membership as the broad Object-level anchor, but they must **not** imply that final `score` is the cosine between those two vectors.

Facet mode keeps the current single-Facet representation/membership semantics.

### 14.2 Required additive component evidence

Overall results must be able to expose a bounded set of contributing matches with at least:

```text
channel                    # overview | facet | statement
source_representation_id
source_membership_id
candidate_representation_id
candidate_membership_id
representation_kind
facet?                     # when applicable
source_statement_id?       # when applicable
candidate_statement_id?    # when applicable
raw_score
raw_score_type             # cosine_similarity for vector pair evidence
contribution               # implementation-defined aggregate contribution
```

The response/result must also preserve:

```text
source_object_id
source_version_id
candidate object_id
candidate version_id
rank
final score
final score_type
matched_facet              # null in overall mode; requested key in Facet mode
```

The detailed response DTO name/serialization shape is implementation work, but the information semantics above are frozen.

## 15. No arbitrary chunking or truncation

R2 explicitly forbids using representation-loss techniques as the redesign itself.

Do not solve N05D-04 by:

- splitting `object_overall` every N tokens;
- silently dropping later Statements;
- clipping to the embedding model context limit;
- selecting a prefix of canonical Knowledge;
- generating an LLM summary and discarding underlying semantic boundaries;
- switching to a smaller model before measuring the structural correction.

Facet and Statement are the existing canonical semantic boundaries and therefore the correct detailed multi-vector units.

## 16. Embedding/runtime control

The first R2 implementation and acceptance baseline keeps:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
```

Do not concurrently introduce:

- Harrier 270M;
- FlashAttention-2;
- PyTorch/CUDA upgrade;
- CPU fallback;
- truncation.

This isolates the effect of representation architecture.

## 17. Public CLI / MCP / Application compatibility

The following public capability names remain stable:

```text
search objects
similar objects
search_objects
find_similar_objects
Derived Search sync/status/rebuild operations
```

Callers do not pass a representation kind for normal Object Search or Object Similarity.

R2 may add explainability fields and change internal `representation_kind` values from legacy `object_overall` to active `object_overview`, but it must not require consumers to understand the old/new representation architecture merely to perform the same Object-level operation.

## 18. Acceptance implications

Before R2-02 semantics can be considered successfully implemented, later tasks must prove:

1. exactly one active deterministic `object_overview` is materialized per accepted represented Object Version;
2. it contains the frozen included field set and no content-Facet Statement bodies;
3. every searchable content Facet remains represented;
4. every searchable accepted Statement remains represented;
5. normal active retrieval has no dependency on `object_overall`;
6. Hybrid Search uses `semantic_object_overview + semantic_facet + semantic_statement` with bounded contributions;
7. Facet/temporal/derivation scope safety is preserved;
8. overall Object Similarity reports `hierarchical_similarity`, not raw cosine;
9. Facet Similarity remains same-Facet cosine with no fallback;
10. multi-vector result evidence is inspectable and bounded;
11. no v1/v2 active generation mixing occurs;
12. canonical Knowledge is unchanged;
13. Harrier 0.6B remains the first comparison baseline;
14. Large-fixture overview meets the <=4096-token engineering target without truncation or returns to design review.

## 19. R2-03 handoff

R2-03 may now design persistence/versioning/migration without reopening the semantic questions frozen here.

R2-03 must decide the physical mechanism for:

```text
SearchRepresentationKind.object_overview
legacy object_overall parse/read compatibility
DB CHECK/enum migration
Derived Search generation identity
active/candidate generation separation
membership uniqueness
side-by-side rebuild
embedding/vector reuse eligibility
Qdrant namespace/generation identity
atomic cutover
rollback
legacy cleanup
```

It must preserve the semantic rules in this document, especially:

- `object_overview != object_overall`;
- builder content-version identity is not generation identity;
- unchanged Facet/Statement content may remain content-reuse eligible;
- active post-cutover retrieval cannot mix v1 and v2 generations.

## 20. R2-02 exit decision

The required R2-02 design questions are frozen:

```text
object_overview semantic fields                 FROZEN
object_overall deprecation behavior             FROZEN
Relation placement                              FROZEN
builder key/version policy                      FROZEN
Hybrid active channels/caps                     FROZEN
Object Similarity semantic aggregation boundary FROZEN
Similarity score type                           FROZEN
multi-vector explainability semantics           FROZEN
no arbitrary chunking/truncation                FROZEN
```

**R2-02 = Complete.**

**Next: R2-03 [P0] — Persistence / versioning / migration design.**
