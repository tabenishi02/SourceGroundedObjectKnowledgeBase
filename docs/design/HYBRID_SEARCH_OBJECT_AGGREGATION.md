# Multi-representation Hybrid Search / Object Aggregation — Phase I / I-04 + R2 v2

更新日: 2026-10-23

- Status: **Accepted Phase-I baseline / R2-02 v2 contract frozen**
- Original task: `I-04 [P0] Multi-representation Hybrid Search / Object Aggregation`
- Superseding task: `N05D-04R2 / R2-02 Requirements + representation contract revision`
- Prerequisites:
  - `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
  - `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
  - `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`
- Normative R2 decision: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

---

## 1. 結論

SGOKBの通常Object検索は、複数channelを独立にcandidate generationし、channel内でObjectへbounded aggregationした後にRRFで融合する。

R2 active contract:

```text
query
 ├─ Registry lexical
 │    ├─ exact name
 │    ├─ exact alias
 │    └─ partial literal
 ├─ Knowledge lexical
 │    └─ active Search Representation FTS / literal fallback
 └─ Semantic
      ├─ object_overview
      ├─ facet
      └─ statement
             ↓
       channel内 bounded Object aggregation
             ↓
       cross-channel RRF
             ↓
       exact identity priority tier
             ↓
       1 Object = 1 result
```

`object_overall` is no longer an active channel after R2 cutover.

BM25、cosine similarity、identity match等のraw scoreは尺度が異なるため直接加算しない。

The first R2 baseline keeps the Phase I fusion constants:

```text
RRF k = 60

object_overview semantic contribution cap = 1
facet semantic contribution cap           = 2
statement semantic contribution cap       = 3
knowledge lexical contribution cap        = 3
```

Statement数やFacet数が多いObjectが単純なhit数だけで無制限にboostされないことがhard requirementである。

Exact identity remains a separate priority tier:

```text
exact name
  > exact alias
  > non-exact lexical / semantic result
```

同tierではRRF fused score、最後にstable Object / Version identityでdeterministic tie-breakする。

---

## 2. Search mode

`ObjectSearchMode` remains:

```text
lexical
semantic
hybrid
```

### lexical

Embedding / Vector backend不要。

- Object Registry name / alias;
- active Knowledge Search Representation lexical index.

### semantic

EmbeddingProvider + VectorIndexAdapter必須。

Vector backend利用不能時はexplicit failure。lexicalへsilent fallbackしない。

### hybrid

通常free-text Object Searchの標準経路。

Lexical実行後にSemantic channelsを追加する。Semantic backendが一時的に利用不能な場合は、canonical Knowledgeを変更せずLexical resultsを返し、`degraded_channels`へ障害を明示する。

別Provider / 別Vector backendへのsilent fallbackは禁止。

---

## 3. Active search channels

```text
exact_name
exact_alias
registry_lexical
knowledge_lexical
semantic_object_overview
semantic_facet
semantic_statement
```

Legacy-only:

```text
semantic_object_overall
```

### Registry lexical

Object identity discovery:

- `objects.name`;
- `object_aliases.value`.

KnowledgeがなくてもIdentity discoveryは可能。

### Knowledge lexical

Active Object Knowledge representation kinds:

```text
object_overview
facet
statement
```

EvidenceはObject Searchへ混ぜない。

### Semantic Object overview

Object canonical name / aliases / Primary Class / facet-less Summary / Facet inventory / searchable Attributes / Relationsからなるcompact broad contextで候補生成する。

Overviewは詳細Knowledgeの代替ではなく、content-Facet Statement bodiesを含まない。

### Semantic Facet

観点別意味matchを候補生成する。

### Semantic Statement

条件、例外、時間限定、細粒度Knowledgeを拾う主要channelとする。

---

## 4. Lexical Index

`search_representation_fts` remains a Derived FTS index over Search Representation content.

Conceptual columns:

```text
representation_id
kind
content
```

R2 migration must make active lexical retrieval see `object_overview / facet / statement` and must prevent legacy `object_overall` from participating in the active generation after cutover.

Tokenizer/short-query behavior remains Phase I baseline. 1〜2文字queryはliteral containment fallbackを維持し、日本語短語を検索不能にしない。

FTS remains rebuildable Derived Search state, not canonical Knowledge.

---

## 5. Vector point identity

Knowledge Vector Index point identity remains **Knowledge membership ID**, not Search Representation ID.

```text
Embedding cache
  representation_id -> vector

Vector Index
  membership -> vector + Version / Object / Facet / Statement metadata
```

This preserves:

- embedding/content reuse;
- current / historical membership identity;
- Version identity;
- Object identity;
- Facet / Statement scope;
- derivation / temporal filters;
- classification snapshot filters.

R2-03 defines how active/candidate generation identity is represented without mixing v1/v2 memberships.

---

## 6. Vector payload metadata

The existing semantic metadata contract remains valid:

```text
membership_id
representation_id
kind
object_id
version_id
primary_class
additional_classes
ancestor_classes
object_status
is_current
facet_id
facet
statement_id
derivation_kind
temporal_scope_id
valid_from_ordinal
valid_to_ordinal
```

R2 changes active `kind` from legacy `object_overall` to `object_overview` for the broad Object representation.

Classification metadata remains Version-snapshot based. Query-time SQLite current pointer verification remains mandatory because Vector Index is derived state.

---

## 7. Hard filters and semantic-scope safety

Supported filter semantics remain:

```text
primary_class
additional_class
ancestor_class
facet
version_id
temporal_scope_id
knowledge_valid_at
derivation_kind
include_archived
```

Unknown Class / Facet is never silently ignored.

### 7.1 current / historical

Default:

```text
active Object
+ accepted Version
+ Object.current_version_id == membership.version_id
```

Historical:

```text
explicit version_id
+ accepted Version
```

Do not mix current and historical silently.

### 7.2 Facet filter

When a Facet is requested, `object_overview` is excluded from candidate generation.

Active semantic kinds:

```text
facet
statement
```

and the requested Facet boundary is enforced.

Do not fall back to:

- overview;
- another Facet;
- legacy `object_overall`.

### 7.3 derivation / temporal filters

`derivation_kind`, `temporal_scope_id`, and `knowledge_valid_at` remain Statement-only where the condition is defined on an individual Statement.

Overview/Facet aggregate representations cannot claim to satisfy a narrower Statement condition merely because one child Statement might match.

---

## 8. Temporal hard filter

Statement point temporal metadata remains:

```text
valid_from_ordinal
valid_to_ordinal
```

`knowledge_valid_at` semantics remain:

```text
valid_from <= query_date <= valid_to
```

Timeless Statement semantics and exact `temporal_scope_id` behavior remain unchanged.

Version history and Knowledge valid time remain separate dimensions.

---

## 9. Filter application position

Hard filters are applied before candidate limit whenever possible.

### Lexical

Filter inside canonical membership/Version/Class/Facet joins, not only after retrieving global FTS top-k.

### Semantic

Convert Class / Facet / Version / temporal conditions to Vector payload hard filters before ANN candidate limit.

This preserves Recall for narrow scopes.

---

## 10. Bounded Object aggregation

### 10.1 Channel-local Object aggregation

Fine-grained hits are not final results. Hits are grouped by Object / Version before cross-channel fusion.

### 10.2 Contribution caps

First R2 baseline:

```text
Object overview     top 1 contribution
Facet               top 2 contributions
Statement           top 3 contributions
Knowledge lexical   top 3 contributions
```

The number of canonical Statements/Facets cannot directly translate into unbounded score contribution.

### 10.3 Cross-channel fusion

Object ranks from each channel are fused using:

```text
fused_score = Σ 1 / (60 + channel_object_rank)
```

Raw BM25 and raw cosine are not added directly.

### 10.4 Exact identity tier

Final sort concept remains:

```text
exact identity tier DESC
RRF fused score DESC
object_id ASC
version_id ASC
```

---

## 11. Search result contract

`ObjectSearchResult` continues to expose conceptually:

```text
object_id
name
primary_class
version_id
rank
fused_score
score_type = rrf
exact_identity
channels
matched_facets
matches
```

`ObjectSearchMatch` continues to preserve:

```text
channel
version_id
representation_id
membership_id
representation_kind
facet
statement_id
snippet
score
score_type
source_rank
```

Active post-R2 `representation_kind` values for Object Knowledge matches are:

```text
object_overview
facet
statement
```

Normal post-cutover results must not expose `object_overall` as if it were active v2 evidence.

Raw match score types may still include:

```text
identity_literal
registry_literal
bm25
literal_contains
cosine_similarity
```

These are query relevance signals, not truth/confidence.

---

## 12. Evidence grounding boundary

Object result detail retains Version / Statement membership identity so canonical Evidence Links remain reachable.

Object Search does not expand all Evidence text into results and does not merge Evidence Semantic Search into Object Search.

---

## 13. Failure / degraded behavior

Canonical/derived boundary remains:

```text
SQLite canonical Knowledge
  └─ source of truth

FTS / Search Representation / Embedding / Vector Index
  └─ derived
```

### Semantic mode

Provider/backend failure -> explicit failure.

### Hybrid mode

Semantic failure -> lexical results + explicit `degraded_channels`.

Forbidden:

- silent external-provider fallback;
- silent Qdrant->other-backend fallback;
- stale historical point as current;
- canonical Version rollback;
- active v1/v2 membership mixing.

---

## 14. Derived rebuild implications

The conceptual rebuild path remains:

```text
accepted active-generation Knowledge memberships
       +
EmbeddingRepository vector cache
       ↓
Version classification/filter metadata
       ↓
membership-scoped VectorIndexPoint
       ↓
VectorIndexAdapter candidate generation
```

R2-03/R2-07 must ensure a coherent active generation and side-by-side rebuild/cutover. Missing required embedding membership must not be reported as a complete index.

---

## 15. R2 migration mapping

Historical v1 -> active v2:

```text
semantic_object_overall  -> semantic_object_overview
object_overall lexical    -> object_overview lexical
facet                      -> facet (retained)
statement                  -> statement (retained)
```

This is a semantic replacement, not a database-string rename. Old v1 rows/vectors are legacy derived artifacts and must not be relabeled in place.

---

## 16. Regression requirements

R2 implementation must prove:

- `1 Object = 1 result`;
- exact name/alias priority unchanged;
- current/historical isolation;
- Primary / Additional / ancestor Class filters;
- Facet filter excludes overview;
- derivation/temporal Statement-only safety;
- unknown Class/Facet validation;
- short Japanese lexical fallback;
- Hybrid semantic outage explicit degradation;
- Semantic-only outage explicit failure;
- overview contribution max 1;
- Facet contribution max 2;
- Statement contribution max 3;
- Knowledge lexical contribution max 3;
- Qdrant/SQLite result semantics agree;
- normal active results contain no legacy `object_overall` membership.

---

## 17. What R2-02 does not change

Unless later quality evidence requires a separate accepted revision, keep:

```text
RRF k = 60
exact identity tier
Facet cap = 2
Statement cap = 3
Knowledge lexical cap = 3
membership-scoped vector point identity
current/historical semantics
hard-filter-before-limit policy
hybrid degraded behavior
1 Object = 1 result
```

R2-08 is the gate for deliberate search-quality changes. Do not tune these constants merely to work around N05D-04 resource failure.

---

## 18. Historical Phase I note

Phase I/I-04 originally used:

```text
semantic_object_overall
+ semantic_facet
+ semantic_statement
```

with `object_overall` cap 1.

That design was valid for the Phase I acceptance corpus and remains historical evidence. N05D-04 later exposed a real large-Object resource failure, so R2 supersedes only the broad Object representation/channel while preserving the bounded multi-representation Hybrid architecture.

**Status: R2-02 Hybrid contract frozen / R2-05 implementation pending.**
