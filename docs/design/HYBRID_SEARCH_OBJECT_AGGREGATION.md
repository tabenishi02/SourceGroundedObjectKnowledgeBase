# Multi-representation Hybrid Search / Object Aggregation — Phase I / I-04

更新日: 2026-10-13

- Status: **Accepted / Implemented**
- Task: `I-04 [P0] Multi-representation Hybrid Search / Object Aggregationを実装する`
- Prerequisites:
  - `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
  - `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
  - `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`
- Next task: `I-05 [P0] find_similar_objectsを実装する`

---

## 1. 結論

SGOKBの通常Object検索は、次の複数channelを独立に候補生成し、Object単位へ集約した後にRRFで融合する。

```text
query
 ├─ Registry lexical
 │    ├─ exact name
 │    ├─ exact alias
 │    └─ partial literal
 ├─ Knowledge lexical
 │    └─ Search Representation FTS / literal fallback
 └─ Semantic
      ├─ object_overall
      ├─ facet
      └─ statement
             ↓
       channel内 Object aggregation
             ↓
       cross-channel RRF
             ↓
       exact identity priority tier
             ↓
       1 Object = 1 result
```

BM25、cosine similarity、identity match等のraw scoreは尺度が異なるため直接加算しない。

標準fusionは次で固定する。

```text
RRF k = 60

object_overall semantic contribution cap = 1
facet semantic contribution cap          = 2
statement semantic contribution cap      = 3
knowledge lexical contribution cap       = 3
```

これにより、Statement数が多いObjectが単純なhit数だけで無制限にboostされることを防ぐ。

exact name / aliasはRRF scoreとは別のpriority tierとする。

```text
exact name
  > exact alias
  > non-exact lexical / semantic result
```

同tierではRRF score、最後にstable Object / Version IDで決定論的にtie-breakする。

---

## 2. Search mode

`ObjectSearchMode`は次の3種類とする。

```text
lexical
semantic
hybrid
```

### lexical

Embedding / Vector backendを必要としない。

- Object Registry name / alias
- Knowledge Search Representation lexical

を利用する。

### semantic

EmbeddingProvider + VectorIndexAdapterを必須とする。

Vector backendが利用不能なら明示的に失敗し、lexicalへsilent fallbackしない。

### hybrid

通常free-text Object Searchの標準経路とする。

Lexicalを実行した後にSemantic channelを追加する。Semantic backendが一時的に利用不能な場合は、canonical Knowledgeを壊さずLexical resultを返し、`degraded_channels`へ障害を明示する。

これは「backendを別backendへsilent fallbackする」こととは異なる。QdrantからLanceDBやexternal providerへ自動切替は行わない。

---

## 3. Search channel

I-04では次を明示channelとして扱う。

```text
exact_name
exact_alias
registry_lexical
knowledge_lexical
semantic_object_overall
semantic_facet
semantic_statement
```

### Registry lexical

Object identity discovery用。

- `objects.name`
- `object_aliases.value`

を対象とする。

Objectが`current_version_id = NULL`でも、Knowledge-specific filterがないIdentity / Lexical discoveryでは発見可能とする。

### Knowledge lexical

I-01のSearch Representationを対象とする。

対象kind:

```text
object_overall
facet
statement
```

EvidenceはObject Searchへ混ぜない。

### Semantic Object overall

Object全体の意味を広く候補生成する。

### Semantic Facet

特定観点の意味的matchを候補生成する。

### Semantic Statement

条件・例外・細粒度Knowledgeを拾う主要channelとする。

---

## 4. Lexical Index

Migration `016_hybrid_search.sql`で次の派生FTS5 tableを追加する。

```text
search_representation_fts
```

column:

```text
representation_id
kind
content
```

Tokenizerは現Prototype資産と同じtrigramを利用する。

`search_representations`のINSERT / UPDATE / DELETEに追従するtriggerを持つ。

Search Representation自体と同様、このFTS tableはcanonical Knowledgeではなく再構築可能な派生Indexである。

### 短い日本語query

trigramは1〜2文字queryをそのまま扱えないため、query termに3文字未満が含まれる場合はSQL literal containmentへ切り替える。

例:

```text
愛
剣
AI
```

短語を「検索不能」としないB-05要件を維持する。

---

## 5. Vector point identity

I-03まではVectorIndexAdapterのpoint identityを抽象化していた。

I-04ではKnowledge Vector Indexのpoint identityを**Search Representation IDではなくKnowledge membership ID**とする。

理由:

```text
同一Search Representation content
        ↓
同一Embedding / Vectorをreuse可能
        ↓
しかし
v1 membership != v2 membership
```

同一representation/vectorを複数Versionでreuseしても、次はmembershipごとに異なり得る。

- current / historical
- Object
- Version
- Facet
- Statement
- derivation
- temporal scope
- Class snapshot

したがってDerived Vector Indexでは、同一Vectorをmembershipごとのpointとして持つ。

```text
Embedding cache
  representation_id -> vector     1回

Vector Index
  membership-v1 -> same vector + v1 metadata
  membership-v2 -> same vector + v2 metadata
```

Embedding計算のdedupとfilter correctnessを両立する。

---

## 6. Vector payload metadata

`KnowledgeVectorIndexBuilder`はaccepted Knowledge membershipからQdrant pointを再構築する。

主要payload:

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

### Class metadata

Primary / Additional ClassはVersion classification snapshotを使用する。

Historical Version検索時に現在のObject classificationを誤って流用しない。

`ancestor_classes`はPrimary / Additional Class自身を含むlineage key集合とし、ancestor Class filterをQdrant payload hard filterへ直接渡せるようにする。

### current metadata

`is_current`はIndex構築時点のcurrent pointerから導出する。

ただしVector IndexはDerived artifactなので、query-timeでもSQLite current pointerを防御的に再確認する。

stale Indexを新current Knowledgeとしてsilent利用しない。

---

## 7. Hard filter

I-04で正式に扱うObject Search filter:

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

unknown Class / Facetはsilent無視せずvalidation errorとする。

### current / historical

既定:

```text
active Object
+ accepted Version
+ Object.current_version_id == membership.version_id
```

Historical:

```text
version_idを明示
+ そのVersionがaccepted
```

currentとhistoricalを同一queryへsilent混合しない。

### Facet

Facet指定時、`object_overall`はcandidate generation対象から除外する。

対象:

```text
facet
statement
```

別Facetやoverallへsilent fallbackしない。

### derivation / temporal

`derivation_kind`、`temporal_scope_id`、`knowledge_valid_at`指定時はStatement-only retrievalとする。

Object overall / Facetは複数Statementを集約した表現であり、個別Statementのtemporal / derivation条件を安全に適用できないためである。

---

## 8. Temporal hard filter

Statement pointには、比較用のderived integer metadataを持たせる。

```text
valid_from_ordinal
valid_to_ordinal
```

### valid_from / valid_to

```text
valid_from <= query_date <= valid_to
```

### as_ofのみ

その日だけを成立点として扱う。

### temporal scopeなし

timeless Knowledgeとして、全期間を覆うrangeを持つ。

したがって`knowledge_valid_at`検索では、明示的に期間外のStatementは除外し、timeless Statementは候補として残る。

`temporal_scope_id`指定時は完全一致filterとする。

Version historyとKnowledge valid timeは引き続き別filterである。

---

## 9. Filter適用位置

hard filterは原則としてcandidate limitより前に適用する。

### Lexical

FTS resultへ後からObject filterするのではなく、FTS tableとcanonical membership / Version / Class / FacetをJOINしたSQL内でfilterする。

### Semantic

Class / Facet / Version / temporal等を`VectorSearchFilter`へ変換し、Qdrant payload filterとしてVector candidate generationへ渡す。

このため、例えば「Personality Facetだけ」の少数candidate検索で、全Facet top-k取得後のpost-filterによってRecallを失わない。

---

## 10. Object aggregation

### 10.1 まずchannel内でObjectへ集約する

Semantic Statement top-kをそのままfinal resultへしない。

同一Object / Versionの複数hitをgroupする。

### 10.2 contribution cap

同一Objectの類似Statement大量保持による過剰boostを抑える。

I-04 baseline:

```text
Object overall  上位1件
Facet           上位2件
Statement       上位3件
Knowledge lexical 上位3件
```

channel内Object scoreは、上記上限以内のhit rankに対するRRF寄与で算出する。

そのscoreで各channel内のObject rankを作る。

### 10.3 cross-channel fusion

各channelのObject rankを再度RRFで融合する。

```text
fused_score = Σ 1 / (60 + channel_object_rank)
```

raw BM25とraw cosineを直接足さない。

### 10.4 exact identity tier

exact name / aliasは通常Object discoveryで意味検索へ埋没させない。

最終sort key概念:

```text
exact identity tier DESC
RRF fused score DESC
object_id ASC
version_id ASC
```

---

## 11. Search result contract

`ObjectSearchResult`は少なくとも次を保持する。

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

`ObjectSearchMatch`:

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

これにより、Objectへ集約した後も「なぜhitしたか」を失わない。

raw match score typeは例として次を明示する。

```text
identity_literal
registry_literal
bm25
literal_contains
cosine_similarity
```

これらはquery relevance signalであり、truth / confidenceへ変換しない。

---

## 12. Evidence groundingとの境界

I-04 final resultはStatement ID / Version IDを保持する。

StatementからEvidence Linkへ辿る既存canonical relationを利用できるため、検索hitのgroundingを後続Application / MCP layerで取得可能である。

I-04でEvidence本文をObject resultへ無制限に展開しない。

Evidence Semantic Search自体もObject Searchへ混ぜず、独立familyを維持する。

---

## 13. Failure / degraded behavior

Search dependencyのfailure domain:

```text
SQLite canonical Knowledge
  └─ 正本

FTS / Search Representation / Embedding / Vector Index
  └─ Derived
```

### Semantic mode

Embedding Provider / Vector backendが利用不能:

```text
explicit failure
```

### Hybrid mode

Semantic channelが利用不能:

```text
Lexical resultsを返す
+ degraded_channelsへ明示
```

禁止:

- external Providerへのsilent fallback
- Qdrantから別Vector backendへのsilent fallback
- stale historical pointをcurrentとして利用
- canonical Version rollback

---

## 14. Index rebuild

`KnowledgeVectorIndexBuilder`を追加した。

処理:

```text
accepted Knowledge memberships
       +
EmbeddingRepository vector cache
       ↓
Version classification snapshot / filter metadata結合
       ↓
membership-scoped VectorIndexPoint
       ↓
VectorIndexAdapter.rebuild()
```

Vector generation自体は行わない。

Embeddingが欠けているaccepted membershipがある場合、Indexを「完全」と偽装せずrebuildを失敗させる。

canonical Knowledgeは変更しない。

性能上、membership contextとAdditional Class snapshotはbulk取得し、Class lineageはClassごとにcacheする。

---

## 15. 実装ファイル

新規:

```text
src/sgokb/domain/search.py
src/sgokb/retrieval/hybrid_search.py
src/sgokb/migrations/016_hybrid_search.sql
tests/test_hybrid_search.py
```

更新:

```text
src/sgokb/domain/__init__.py
src/sgokb/retrieval/__init__.py
src/sgokb/retrieval/vector_index.py
migration count regression tests
```

---

## 16. Test coverage

I-04 focused testsでは少なくとも次を固定した。

- FTS migration / trigger
- membership-scoped vector pointとVector reuse
- exact alias priority
- 1 Object = 1 result
- current / historical isolation
- Facet hard filter
- Primary / Additional / ancestor Class hard filter
- unknown Class / Facet validation
- temporal valid-at filter
- temporal scope exact filter
- 1文字日本語Lexical fallback
- Hybrid semantic outage時の明示degrade
- Semantic-only outage時のexplicit failure
- Statement contribution top-3 cap
- Qdrant adapterとのmembership payload integration

---

## 17. I-04で固定しない事項

### I-05

- `find_similar_objects`
- overall similarity専用query
- Facet similarity専用query
- same Primary Class default scope

### I-06

- reranker
- cross encoder

### I-07

- 正式Search gold
- RRF kの再調整
- channel weight導入要否
- contribution cap 1/2/3の最終妥当性
- Object Recall / MRR / nDCG
- actual canonical corpus latency
- candidate_limit tuning

I-04のRRFとcapは、無根拠な最終最適値ではなく、I-07で比較可能な**明示baseline**として固定する。

---

## 18. I-05への固定入力

I-05では次を変更せず利用する。

```text
Search Representation: I-01 contract
Embedding Space:       Harrier OSS v1 0.6B / 1024-dim
Vector backend:        local Qdrant HNSW
Vector point identity: Knowledge membership ID
current/history:       membership + canonical current pointer
Class/Facet metadata:  Version snapshot based
```

I-05はHybrid free-text rankingを再設計するTaskではない。

**Status: I-04 Complete / I-05 Ready**
