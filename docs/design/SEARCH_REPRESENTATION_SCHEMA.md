# Search Representation Schema Design

更新日: 2026-10-23  
対象: Phase I / I-01 contract + N05D-04R2 / R2-02 superseding revision  
Status: **Accepted / R2 v2 contract frozen**

Normative R2-02 decision: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

## 1. 目的

Search Representationは、accepted canonical Knowledge / canonical Evidenceを検索・Embedding向けの決定論的な文字列表現へ変換した**再構築可能な派生物**である。

```text
canonical SQLite data
  ↓ deterministic builder
Search Representation
  ↓ Embedding Provider
Embedding
  ↓ VectorIndexAdapter
Vector Index
```

Search Representation、Embedding、Vector Indexはいずれもcanonical Knowledgeではない。生成失敗・削除・再構築によってaccepted Object Knowledge Versionを変更またはrollbackしてはならない。

N05D-04R2では、Phase I v1の`object_overall`だけをactive contractから退役させ、canonical Object / Facet / Statement semantic boundariesを利用したhierarchical multi-vector構造へ改定する。

## 2. Active representation kinds

R2 active contract:

| kind | 意味 | canonical membership | active builder version |
|---|---|---|---:|
| `object_overview` | compact Object-level semantic context | Object + Version | 2 |
| `facet` | 1 content Facetの意味表現 | Object + Version + Facet | 1 while unchanged |
| `statement` | 1 accepted searchable Knowledge Statementの意味表現 | Object + Version + optional Facet + Statement | 1 while unchanged |
| `evidence` | 1 canonical Evidenceの意味表現 | Evidence + Source + Snapshot + Normalization Run | 1 |

`object_overall` is a **legacy v1 kind**. It remains identifiable only for migration, rollback, historical inspection, historical benchmark interpretation, and controlled cleanup. It is not an active post-R2 retrieval kind.

### 2.1 Compatibility rule

`object_overview` is not a rename or alias of `object_overall`.

Prohibited:

```text
old object_overall row -> relabel as object_overview
old representation ID -> reuse as overview identity
legacy object_overall -> deserialize as if overview
active retrieval -> continue selecting object_overall under a new display name
```

Any temporary enum/API alias is compatibility-only and must not blur persisted v1 semantics with active v2 semantics. The physical compatibility mechanism is R2-03 scope.

### 2.2 Relation

R2 does not create an independent `relation` representation kind.

Relation semantics remain Object-level context and are represented in `object_overview` using deterministic human-readable Relation/endpoint text. If a canonical `relationships` content Facet exists, Relation semantics may also be represented through that Facet contract.

This intentional semantic-role overlap does not permit copying unrelated Facet Statement bodies into the overview.

## 3. Content identity and membership identity

Content identity and membership identity remain separate.

### 3.1 Content identity

`search_representations` conceptually stores:

```text
id
kind
builder_key
builder_version
content
content_hash = SHA-256(UTF-8 content)
created_at
```

Reuse identity:

```text
(kind, builder_key, builder_version, content_hash)
```

The same representation content may be reused by different accepted Object Versions, but Version/current-historical identity remains on membership records.

### 3.2 Knowledge membership

`knowledge_search_representation_memberships` keeps:

```text
representation_id
object_id
version_id
target_kind
facet_id?
statement_id?
```

A shared content record never merges Version membership.

### 3.3 Evidence membership

Evidence remains a separate membership family:

```text
representation_id
evidence_id
source_id
snapshot_id
run_id
```

Generation/provenance IDs remain metadata rather than semantic embedding text.

## 4. current / historical scope

Normal Object Search:

```text
Object.status = active
AND Version.state = accepted
AND Object.current_version_id = membership.version_id
```

Historical Search:

```text
Version.state = accepted
AND explicit version scope
```

A reused representation/vector does not change membership currentness.

The active R2 generation must not mix v1 `object_overall` memberships with v2 `object_overview` memberships during normal retrieval. The physical generation/cutover mechanism is defined in R2-03.

## 5. Deterministic builder contract

Builder rules remain:

- no LLM generation;
- Unicode NFC normalization;
- deterministic whitespace normalization;
- fixed field order;
- no DB rowid/UUID/internal stable ID in semantic text;
- deterministic sorting for unordered collections;
- byte-identical UTF-8 output for the same canonical input and same content contract;
- builder content-contract version changes when semantic bytes/field contract changes.

### 5.1 Builder key

Keep:

```text
builder_key = sgokb-canonical-search
```

### 5.2 Builder version policy

Builder version is **content-contract identity**, not Derived Search generation identity.

```text
object_overall  -> historical version 1 only
object_overview -> version 2
facet           -> version 1 while its byte-level contract is unchanged
statement       -> version 1 while its byte-level contract is unchanged
evidence        -> version 1 / unchanged
```

If a later R2 task deliberately changes Facet or Statement bytes/semantic fields, that kind receives an explicit version bump then.

R2-03 must provide/confirm a separate active/candidate Derived Search generation identity for side-by-side rebuild and atomic cutover.

## 6. Statement representation

Statement remains a first-class semantic boundary.

The current semantic context remains:

```text
Object: <canonical name>
Primary Class: <class key> (<class display name>)
Facet: <facet name> (<facet key>)        # Facet所属時のみ
Temporal Scope: <normalized scope>       # 存在時のみ
Derivation: <derivation kind>            # direct_statement以外
Statement: <statement text>
```

Version ID、Statement ID、Facet IDはsemantic textへ入れない。

R2 does not arbitrarily split or truncate Statement text.

## 7. Facet representation

Facet remains a first-class semantic boundary.

`object_version_facets.status = content` only:

```text
Object
Primary Class
Facet
Statements (deterministic order)
```

Do not produce normal semantic content for:

- `insufficient_evidence`;
- `not_applicable`;
- `not_analyzed`.

Facet Statement order remains deterministic.

R2 does not split Facets into fixed-token chunks.

## 8. Object overview representation — active v2 contract

Exactly one active `object_overview` is materialized for each represented accepted Object Version.

It is deterministic, non-generative, and structurally compact.

### 8.1 Included semantic fields

In deterministic order:

1. Object canonical name.
2. Aliases, deterministically normalized/ordered.
3. Version classification snapshot Primary Class.
4. Facet-less Summary Statements.
5. `content` Facet identity inventory: Facet key/name only.
6. Known searchable Structured Attributes as canonical key/display-value text.
7. Deterministic canonical Relation text.

Representative logical form:

```text
Object: <canonical name>
Aliases: <aliases>
Primary Class: <class key> (<class display name>)
Summary:
  <facet-less summary statements>
Facets:
  <facet key/name inventory>
Attributes:
  <searchable structured attributes>
Relations:
  <subject name> <relation display name> <target name>
```

Exact delimiters/formatting are builder implementation details; the semantic field set is frozen.

### 8.2 Explicit exclusions

Do not include:

- content-Facet Statement bodies;
- copies of all Statements under each Facet;
- Statement/Facet/internal database IDs;
- Evidence content or Evidence IDs;
- gap / insufficient-evidence management text;
- unresolved references;
- Registry proposals;
- conflict management records;
- workflow/debug metadata;
- LLM-generated summaries;
- arbitrary fixed-token chunks.

### 8.3 Boundedness

The overview is bounded by semantic role, not destructive truncation.

N-05 Large-fixture engineering diagnostic:

```text
object_overview <= 4096 tokens
```

No truncation is allowed to force this. If the deterministic included fields exceed the target, return to design review.

## 9. Historical `object_overall` v1 contract

The Phase I v1 representation was:

```text
Object canonical name
aliases
Primary Class
Facet-less Summary Statements
all content-Facet Statement bodies
known structured Attributes
Relation text
```

That historical definition is retained only to explain persisted v1 data, tests, and benchmark evidence.

It is retired from active post-R2 materialization/retrieval because it duplicates detailed Facet/Statement Knowledge into a monolithic embedding input.

## 10. Evidence representation

Evidence contract is unchanged.

Semantic text may include:

```text
Source label          # 存在時
Snapshot title        # 存在時
Language              # 存在時
Source classification # 存在時
Evidence content
```

Keep generation/provenance IDs in membership/canonical metadata rather than embedding text.

Evidence remains an independent search family and is not merged into Object overview.

## 11. Normal semantic-index exclusions

The following remain administrative/review metadata, not normal semantic Knowledge:

- gap;
- insufficient-evidence Facet state;
- unresolved reference;
- Registry proposal;
- conflict record metadata itself.

Accepted grounded `knowledge_statements` remain searchable even when involved in a conflict.

## 12. Reuse rule

Search Representation reuse:

```text
same kind
AND same builder_key
AND same builder_version
AND same SHA-256(content)
```

May reuse:

- content representation record;
- same-Embedding-Space vector for the same representation identity.

Must not merge/reuse as semantic identity:

- Version membership;
- current/historical state;
- Evidence generation identity;
- filter scope.

Consequences:

- `object_overall` cannot be reused as `object_overview`;
- unchanged Facet/Statement representations remain content-reuse eligible;
- active generation coherence is a separate R2-03 concern.

## 13. Retrieval-facing semantics

Active Object Search representation family:

```text
object_overview
facet
statement
```

Facet-scoped retrieval excludes overview.

Statement-specific temporal/derivation filters remain Statement-only where aggregate representations cannot satisfy the hard condition safely.

Overall Object Similarity must not treat `object_overview` as equivalent to complete detailed Knowledge. It uses hierarchical multi-vector semantics defined in `OBJECT_SIMILARITY_SEARCH.md`.

## 14. Failure domain / rebuild

Derived layers:

```text
Search Representation
Embedding
Vector Index
```

remain rebuildable from canonical SQLite Knowledge/Evidence.

Failure must not:

- rollback accepted Version;
- delete canonical Statement/Evidence;
- silently change provider/backend;
- expose stale/failed derived state as ready;
- mix active v1/v2 generations.

## 15. Persistence impact boundary

R2-02 freezes semantics only.

R2-03 must define the physical implementation for:

```text
object_overview kind persistence
legacy object_overall readability
DB CHECK/enum migration
active/candidate Derived Search generation identity
membership uniqueness
side-by-side rebuild
embedding/vector reuse eligibility
Qdrant generation/namespace
atomic cutover
rollback
legacy cleanup
```

Historical migration `014_search_representations.sql` must not be edited in place.

## 16. Embedding baseline control

The first R2 implementation/evaluation baseline keeps:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
normalization: unchanged
```

No concurrent Harrier 270M, FlashAttention-2, PyTorch/CUDA upgrade, CPU fallback, or truncation is introduced.

## 17. R2-02 frozen decisions

```text
active Object kind                         object_overview
legacy overall kind                        object_overall / legacy-only
object_overview content fields             FROZEN
Facet representation                       retained
Statement representation                   retained
Evidence representation                    unchanged
Relation placement                         overview + canonical relationships Facet where applicable
independent relation kind                  no
builder key                                sgokb-canonical-search
object_overview builder version            2
unchanged facet/statement/evidence version 1
arbitrary chunking                         prohibited
truncation                                 prohibited
```

The active Hybrid and Similarity composition contracts are defined in:

- `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
- `docs/design/OBJECT_SIMILARITY_SEARCH.md`

**Status: R2-02 representation contract frozen / R2-03 persistence design ready.**
