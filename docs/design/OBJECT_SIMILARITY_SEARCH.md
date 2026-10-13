# Object Similarity Search — Phase I / I-05

更新日: 2026-10-14

- Status: **Accepted / Implemented**
- Task: `I-05 [P0] find_similar_objectsを実装する`
- Prerequisites:
  - `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
  - `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
  - `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`
  - `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
- Next task: `I-06 [P1] Reranker / second-stage retrievalを評価する`

---

## 1. 結論

SGOKBのObject Similarityは、free-text Queryを新しくEmbeddingする検索ではない。

既存Objectのaccepted KnowledgeからI-01で生成済みのSearch Representationと、I-02で保存済みのEmbeddingをQuery Vectorとして再利用する。

```text
source Object
  ↓
current accepted Version
  ↓
object_overall または指定Facet Search Representation
  ↓
既存Embedding Vector
  ↓
I-03 VectorIndexAdapter / Qdrant
  ↓
current candidate Objects
  ↓
cosine similarity順
```

I-05で正式に提供するAPIは`ObjectSimilaritySearch.find_similar_objects()`とする。

---

## 2. overall similarity

Facetを指定しない場合は`object_overall`同士を比較する。

```text
Source Object A
  object_overall vector
       ↓
Candidate Object B object_overall
Candidate Object C object_overall
Candidate Object D object_overall
```

Statement hit数やFacet数を集約してSimilarity scoreを作らない。

I-01でObject全体用に決定論的に構築した`object_overall` Search RepresentationのVectorを、Object全体Similarity専用の比較単位とする。

---

## 3. Facet similarity

`facet="personality"`のようにFacetを指定した場合は、同じFacet同士だけを比較する。

```text
Source A / personality
        ↓
Candidate B / personality
Candidate C / personality
```

禁止:

- Sourceに指定Facetがない場合にoverallへfallbackする
- Candidateに指定Facetがない場合にscore=0として混ぜる
- 別FacetのVectorを代用する

Source Versionにcontent Facetが存在しない場合は明示的なvalidation errorとする。

Candidate側に同FacetがないObjectは、Vector Indexに該当Facet pointがないため候補にならない。

---

## 4. Source Version scope

既定ではSource Objectの`current_version_id`を利用する。

```text
find_similar_objects(object_id)
  ↓
source = current accepted Version
```

再現・比較用途では、accepted historical Versionを明示指定できる。

```text
find_similar_objects(
    object_id,
    source_version_id="...",
)
```

historical Sourceを使ってもCandidate側は既定でcurrent accepted Knowledgeだけを対象とする。

Source VersionのPrimary Classは、現在のObject Registry値ではなく、そのVersionのclassification snapshotから解決する。

これによりHistorical Versionの分類文脈を失わない。

---

## 5. Candidate scope

### 5.1 既定

Candidateは次を満たす。

```text
accepted Version
+ current Version
+ active Object
+ sourceと同じPrimary Class
+ source Object自身ではない
```

したがってCharacterを起点にした通常Similarityでは、Character内で比較する。

### 5.2 cross-class

Classを跨いだSimilarityは自動では有効化しない。

```text
cross_class=True
```

を明示した場合だけPrimary Class filterを外す。

例:

```text
Character ↔ Work
Concept ↔ Theme
Person ↔ Character
```

意味空間上の近さは取得できるが、Classを跨ぐ比較の解釈は利用側の責務とする。

---

## 6. Source Object自身の除外

SimilarityではSource Object自身は通常cosine=1に近く、何もしなければ必ず上位候補になる。

I-05ではtop-k取得後に自己一致を捨てるのではなく、Vector candidate生成前に除外する。

`VectorSearchFilter`へ後方互換の`excludes`を追加した。

概念:

```text
must:
  kind = object_overall
  is_current = true
  primary_class = character

must_not:
  object_id = source_object_id
```

Qdrant adapterでは`must_not` payload filterへ変換する。

これにより`limit=1`でもSource自身が1枠を消費しない。

---

## 7. Similarity score

I-04のHybrid Searchは異なるchannelのrankを統合するためRRFを使う。

I-05は異なる。

比較対象はすべて、

- 同じEmbedding Space
- 同じrepresentation kind
- Facet modeでは同じFacet
- 同じcosine metric

なので、raw cosine similarityをそのままSimilarity scoreとして返す。

```text
score_type = cosine_similarity
```

このscoreはKnowledgeのtruth、confidence、Source trustではない。

単にEmbedding Space上での意味的近さを表す。

---

## 8. Embedding再計算をしない

I-05はSource Objectの文章をEmbeddingProviderへ再送しない。

```text
search_representation_embeddings
```

に保存済みのVectorを使用する。

利点:

- 同じKnowledgeに対する不要なGPU計算をしない
- Providerが一時停止していても、既存Embedding + Vector IndexがあればSimilarity可能
- SourceとCandidateが同じEmbedding Spaceであることを保証できる
- historical Versionの再現性を維持できる

Source RepresentationのEmbeddingが対象Spaceに存在しない場合は、別modelやexternal providerへsilent fallbackせず明示的に失敗する。

---

## 9. Vector point / membership identity

I-04のmembership-scoped pointをそのまま利用する。

```text
Embedding cache:
representation_id -> vector

Vector Index:
membership_id -> vector + Version / Class / Facet metadata
```

Similarity queryのSourceはrepresentation embeddingからVectorを読む。

Candidateはmembership pointを検索する。

これにより、同一content vectorを複数Versionでreuseしても、Candidateのcurrent/historical identityを失わない。

---

## 10. Defensive current verification

QdrantはDerived Indexなので、current pointer変更直後などに一時的に古いpayloadが残る可能性をfailure modelとして考慮する。

Vector filterで`is_current=true`を要求したうえで、SQLite canonical DBでもCandidate membershipを再確認する。

```text
objects.current_version_id == membership.version_id
```

を満たさないhitは返さない。

同様に、

- accepted lifecycle
- Object active/archive scope
- expected representation kind
- Facet一致
- same Primary Class scope

を防御的に再確認する。

古いIndex pointをcurrent resultとしてsilent利用しない。

---

## 11. Result contract

### ObjectSimilarityResponse

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

### SimilarObjectResult

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

`version_id`は**Candidate側で実際に比較したtarget Knowledge Version**である。

`matched_facet`は、

```text
overall similarity -> null
Facet similarity   -> 指定Facet key
```

とする。

このため利用側は、Similarityの意味境界と対象Versionを追跡できる。

---

## 12. Failure behavior

次は明示失敗とする。

- unknown source Object
- sourceにcurrent Versionがない
- source Versionがacceptedでない
- unknown Facet
- Source Versionに指定content Facetがない
- Source Search Representationがない
- Source Embeddingが指定Embedding Spaceにない
- Vector backendが利用不能

禁止:

- Facet missing時のoverall fallback
- 別Embedding Spaceへのsilent切替
- 別Vector backendへのsilent fallback
- external Providerへのsilent fallback
- historical Candidateのsilent混入

canonical SQLite Knowledgeは変更しない。

---

## 13. I-04との責務差

### I-04 Hybrid Search

入力:

```text
free-text query
```

複数channel:

```text
Registry lexical
Knowledge lexical
Object semantic
Facet semantic
Statement semantic
```

出力ranking:

```text
RRF
```

### I-05 Similarity

入力:

```text
source Object ID
```

比較単位:

```text
object_overall
または
specified Facet
```

出力ranking:

```text
cosine similarity
```

したがってI-05はI-04のfree-text rankingを再設計しない。

---

## 14. 実装ファイル

新規:

```text
src/sgokb/retrieval/similarity.py
tests/test_object_similarity.py
```

更新:

```text
src/sgokb/domain/search.py
src/sgokb/domain/__init__.py
src/sgokb/domain/vector_index.py
src/sgokb/retrieval/__init__.py
src/sgokb/retrieval/vector_index.py
```

DB schema変更は不要なのでMigration 017は作成しない。

I-01〜I-04の既存canonical / derived schemaだけで実装できる。

---

## 15. Test coverage

I-05 focused testsでは少なくとも次を固定する。

- overall similarity
- source Object自身を除外
- same Primary Class default
- explicit cross-class expansion
- Facet similarityは同一Facetだけ
- Source missing Facetは明示error
- Candidate missing Facetは候補外
- current target Versionだけを返す
- target Versionをresultへ保持
- accepted historical source Versionの明示利用
- Source Embedding欠落時の明示failure
- invalid source Version / limit validation
- Qdrant adapterとのoverall / Facet integration
- Vector `must_not` exclusion filter
- native Windows Qdrant 1.19.2でsource除外`must_not`が動作すること

Native smokeでは、深いrepo-local Qdrant storage rootでWindows `os error 3`を再現し、短いstorage rootへ変更すると同一testが成功した。この運用制約はI-03設計書にも追記した。

---

## 16. I-05で固定しない事項

### I-06

- rerankerをSimilarity結果へ適用するか
- Cross Encoderの採否

Similarity first-stageにrerankerを自動追加しない。

### I-07

- 人間評価によるSimilarity品質
- overallとFacetの用途別評価
- cosine score distribution
- Class別threshold要否
- cross-class similarityの有用性
- ANN Recall / latency
- Harrier以外のquality ceiling profile比較

特定score thresholdをI-05で「似ている / 似ていない」の真理値として固定しない。

---

## 17. I-06への固定入力

I-06では次を変更せず利用する。

```text
Search Representation: I-01
Embedding Space:       Harrier OSS v1 0.6B / 1024-dim baseline
Vector backend:        local Qdrant HNSW
Hybrid Search:         I-04 RRF baseline
Similarity:            I-05 direct cosine baseline
Similarity scope:      same Primary Class default
Facet missing:         explicit, no fallback
```

**Status: I-05 Complete / I-06 Ready**
