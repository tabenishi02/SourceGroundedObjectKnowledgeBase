# Source Grounded Object Knowledge Base — Phase I Preparation

更新日: 2026-10-14

- Status: **Complete (I-01〜I-07 Complete)**
- Completed phase: Phase I — 意味検索・類似検索
- Next phase: Phase J — MCP Knowledge Access Layer
- Next task: `J-01 [P0] Retrieval CoreとMCP Adapterを分離する`
- Working branch: `integration/knowledge-base-redesign`
- Closure input: `docs/planning/PHASE_H_CLOSURE_AUDIT.md`
- Closure audit: `docs/planning/PHASE_I_CLOSURE_AUDIT.md`
- Phase J preparation: `docs/planning/PHASE_J_PREPARATION.md`

---

## 1. Phase Iの目的

Phase Iでは、SQLite上のaccepted canonical Knowledgeを変更せず、再構築可能な検索派生層を構築する。

最終的に次を実現する。

```text
canonical SQLite Knowledge
  ↓
Search Representation
  ↓
Embedding Provider
  ↓
Vector Index
  ↓
Lexical / Semantic / Hybrid retrieval
  ↓
Object Aggregation / Similarity
  ↓
1 Object = 1 result
```

Phase I完了条件:

> 「文字列が一致するObject」だけでなく、「意味・価値観・テーマ等が近いObject」を実用精度で取得できる。

---

## 2. Phase IのTask一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| I-01 Search Representation / Embedding対象 | P0 | Completed | Object / Facet / Statement / Evidenceの派生表現契約を設計 |
| I-02 Embedding Provider / 多言語Model比較 | P0 | Completed | 2026追加候補を含めHarrier OSS v1 0.6B / 1024-dim共通Embedding Spaceを固定 |
| I-03 VectorIndexAdapter / Backend比較 | P0 | Completed | Qdrant HNSWを標準backend、LanceDBを第2候補として固定 |
| I-04 Hybrid Search / Object Aggregation | P0 | Completed | Lexical + multi-representation SemanticをObjectへ集約 |
| I-05 `find_similar_objects` | P0 | Completed | overall / Facet similarity、same-Class既定scope、cross-class明示拡張 |
| I-06 Reranker評価 | P1 | Completed | BGE v2-m3をbalanced候補、zerank-2をquality候補として評価 |
| I-07 Search gold / Backend benchmark | P0 | Completed | frozen gold + 100k Exact/Qdrant + formal reranker benchmark |

I-01を先に確定しないままI-02/I-03を始めると、model/backend比較対象となるrepresentation自体が揺れるため、I-01をPhase Iの設計起点とする。

I-01は2026-10-13に完了した。確定contractは`docs/design/SEARCH_REPRESENTATION_SCHEMA.md`を正本とし、migration `014_search_representations.sql`、deterministic `SearchRepresentationBuilder`、focused regression testsへ反映済みである。

I-02も2026-10-13に完了した。初回比較後に2026年の新候補であるHarrier OSS v1 0.6B、Jina Embeddings v5 Text Small、Nemotron 3 Embed 1B / 8B、EmbeddingGemma 2を同一暫定corpusで追加実測し、Gemini Embedding 2もAPI試験対象としてharnessを固定した。GeminiはAPI key未設定のため実測blockedとして記録した。比較結果と確定Embedding Spaceは`docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`を正本とし、Phase I共通baselineをHarrier OSS v1 0.6B / 1024次元 / 32Kへ更新した。Migration `015_embedding_spaces.sql`の汎用contractとlocal Provider adapterへ反映済みである。I-03ではこのEmbedding Spaceを固定し、Vector backend差だけを比較する。

I-03も2026-10-13に完了した。30,000件 / Harrier 1024次元の固定fixtureでNumPy Exact、sqlite-vec 0.1.9、SQLite-Vector 1.1.2 Exact / TurboQuant、LanceDB 0.40.0、native Windows Qdrant 1.19.2を比較した。`docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`を正本とし、標準backendをlocal Qdrant HNSW (`m=16`, `ef_construct=128`, `hnsw_ef=256`)へ固定した。LanceDB embeddedはserver不要の第2候補として保持する。backend-neutral `VectorIndexAdapter` contractとQdrant adapterを実装し、Qdrant停止・index消失はDerived Search failureとしてSQLite正本からrebuild可能とした。I-04ではこのbackend contractを固定し、Hybrid Search / Object Aggregationを実装する。

I-04も2026-10-13に完了した。`docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`を正本とし、Registry / Knowledge LexicalとObject / Facet / Statement SemanticをObject単位へ集約するHybrid Search Coreを実装した。異種raw scoreは直接加算せずRRF (`k=60`)で融合し、Object / Facet / Statement / Knowledge Lexicalのcontribution capをそれぞれ1 / 2 / 3 / 3へ固定した。exact name / aliasは別priority tierとし、current/historical、Primary/Additional/ancestor Class、Facet、derivation、temporal hard filterをcandidate generation前に適用する。Vector pointはSearch RepresentationではなくKnowledge membership単位とし、Embedding reuseとVersion/filter identityを両立した。Migration `016_hybrid_search.sql`、`HybridObjectSearch`、`KnowledgeVectorIndexBuilder`とfocused regression testsへ反映済みである。I-05ではこのretrieval contractを固定し、Object / Facet similarityを実装する。

I-05は2026-10-14に完了した。`docs/design/OBJECT_SIMILARITY_SEARCH.md`を正本とし、`ObjectSimilaritySearch.find_similar_objects()`で既存`object_overall` / Facet EmbeddingをQuery Vectorとして再利用するObject-to-Object Similarityを実装した。既定candidate scopeはsource Versionと同じPrimary Classのcurrent accepted Objectで、cross-classは`cross_class=True`の明示指定時だけ拡張する。Facet指定時は同一Facetのみを比較し、Source/CandidateのFacet欠落をoverallや0 scoreへsilent fallbackしない。結果はRRFではなく同一Embedding Space上のcosine similarityを返し、matched Facet、target Version、representation / membership identityを保持する。Vector filterへsource Object除外用`excludes`を追加し、Qdrantでは`must_not`としてcandidate generation前に適用する。I-06ではこのfirst-stage retrieval / similarity contractを固定してReranker導入を評価する。

I-06は2026-10-14に完了し、その後の最新model surveyを受けて同日追加評価した。`docs/design/RERANKER_SECOND_STAGE_EVALUATION.md`を正本とし、Harrier top 50固定candidateでBGE、Qwen3 0.6B / 4B、Jina v3.5に加え、KaLM Nano/Small R2、Qwen3-VL-Reranker-2B、ZeroEntropy zerank-2を実測した。追加評価ではzerank-2がMRR 0.971 / Recall@1 96.2% / nDCG@10 0.953で品質1位、BGEはMRR 0.944ながら同runtime再測定でp50約56 ms / peak VRAM約1.21 GiBと圧倒的に軽量だった。I-07ではBGEをbalanced/default候補、zerank-2をquality候補、暫定rerank depthをtop 50として正式goldで比較し、production mandatory化はそれまで保留する。

I-07は2026-10-14に完了した。`benchmark/search-quality-gold-v1.json`をfrozen goldとし、20 Object / 21 accepted Version / 24 QueryでLexical / Semantic / Hybrid、Statement、overall / Facet similarity、Evidence Search、filter / current-history / temporal contractを評価した。HybridはObject MRR 1.000 / Recall@10 100%、contract 5/5、Facet similarityはMRR 1.000だった。100k / 1024-dim backend benchmarkではNumPy Float32 ExactをreferenceにQdrant HNSWを評価し、100k scale tuningによりdefault `hnsw_ef`を256から768へ更新した。formal reranker goldではBGE / zerank-2ともObject MRR 1.000で、BGEをbalanced候補、zerank-2をquality候補として維持する。設計正本は`docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`。Phase I完了条件を満たし、次はPhase Jへ進む。

---

## 3. Phase Iのcanonical design inputs

### 3.1 Search requirements

`docs/requirements/SEARCH_REQUIREMENTS.md`

既に確定している主要要件:

- Identity LookupとSearchを分離する。
- accepted current Knowledgeを通常検索の既定scopeとする。
- historical Knowledgeは明示scopeでのみ検索する。
- Object / Facet / Statementのmulti-representation Semantic Retrievalを採用する。
- Evidence SearchをObject Knowledge Searchと独立して維持する。
- 通常Object Searchは内部Statement hitをObjectへ集約し、`1 Object = 1 result`とする。
- exact name / aliasをSemantic resultより優先可能にする。
- Class / Facet / Version / temporal等のhard filterをcandidate generation前に適用可能にする。
- scoreをtruth/confidenceへ変換しない。
- Search Indexをcanonical Knowledgeから再構築可能な派生物とする。

### 3.2 Embedding / Vector Search research

`docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md`

既に採用された設計入力:

```text
Object overall representation
Facet representation
Statement representation
Evidence representation
```

Statement-level Embeddingは標準方針とする。

同時に、

- `EmbeddingProvider`
- `VectorIndexAdapter`
- representation hashによるVector reuse
- Embedding Space isolation
- current / historical isolation
- Statement → Object Aggregator

を採用する。

### 3.3 Non-functional requirements

`docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`

Phase Iで特に維持する境界:

- local-only default
- external providerへのsilent fallback禁止
- derived index失敗でcanonical Knowledgeを失わない
- stale / failed / pending Index状態を検出可能にする
- SQLite正本からfull rebuild可能にする
- Windows運用コストもbackend評価対象にする

### 3.4 Phase H outputs

Phase HによりPhase Iの入力が安定した。

- accepted Versionだけを通常Index対象にできる。
- Version ID / current pointerが確定している。
- Summary / Facet / Statement / Attribute / Relationがstructured canonical Knowledgeとして存在する。
- Evidence Link / Provenanceへ追跡できる。
- rollback時にderived stateが新target Versionへpending化される。
- `object_derived_states`に`search_representation`, `embedding`, `vector_index`の再同期状態が存在する。

---

## 4. I-01で確定すべき論点

I-01ではmodel/backendを選ばず、まずSearch Representation contractを確定する。

### 4.1 Representation kind

最低限:

```text
object_overall
facet
statement
evidence
```

Relation text representationは必要性を評価し、独立kindとするかObject/Facet表現へ統合するか決める。

### 4.2 Canonical membershipとcontent identityの分離

Versioned Knowledge membership:

```text
object_id
version_id
facet_id / statement_id等
```

Embedding content identity:

```text
representation_kind
builder_version
representation_hash
embedding_space_id
```

を分離する。

同一content hashのVector reuseを許可しても、Version membership / current-historical scopeを失わない。

### 4.3 Contextual Search Representation Builder

Statement単体で文脈不足になる場合に、決定論的に必要なcontextを付加する。

候補:

```text
Object name
Primary Class
Facet key / name
temporal scope
derivation kind
Statement text
```

ただし管理情報を無条件に大量付与してEmbedding noiseを増やさない。

### 4.4 通常Semantic Indexから除外するもの

通常Statement Semantic Indexへ入れない:

- gap
- insufficient evidence
- unresolved reference
- Registry proposal

Conflict record自体も通常semantic contentへ混ぜない。

一方、conflict中のaccepted grounded Statement自体は検索可能にする。

### 4.5 current / historical scope

通常検索:

```text
active Object
+ current accepted Version
```

Historical Search:

```text
明示Version scope
```

古いStatement Vectorを新current Knowledgeとしてsilent利用しない。

### 4.6 Evidence representation

EvidenceはObject Knowledgeと別index familyとして扱う。

少なくとも、

- Evidence content
- effective Snapshot / Normalized Run generation
- Source metadata / filter metadata
- provenance identity

を維持する。

Package Retrievalで利用するため、Object Knowledge用representationと同一scopeへ混ぜない。

---

## 5. I-01で意図的に決めない事項

次は後続Taskへ送る。

### I-02

- 最終Embedding model
- dimension
- provider library
- normalization設定
- multilingual / cross-lingual model採用

### I-03

- 最終Vector backend
- ANN方式
- HNSW parameter
- quantization
- server process採否

### I-04

- Object Aggregation式
- Hybrid fusion式
- lexical / semantic channel weight
- final result schema詳細

### I-06

- reranker採否
- cross encoder model

I-01でこれらを先行固定しない。

---

## 6. 既存実装の扱い

`src/sgokb/search.py`には旧Prototype由来の次の資産がある。

- `SQLiteCosineIndex`
- `merge_candidates()`によるRRF系fusion
- `SimpleReranker`
- `HybridSearch`
- `EmbeddingSpace` isolation

これらは削除対象と決めない。

ただし現在の実装は旧`search_items`前提の小規模baselineであり、Phase Iの最終architectureとはみなさない。

再利用方針:

```text
SQLiteCosineIndex
  → Exact / small-scale baseline候補

merge_candidates / SimpleReranker
  → fusion比較時のbaseline候補

EmbeddingSpace
  → model/revision/dimension/config isolation思想を継承
```

I-01で新Search Representation contractを確定後、既存search.pyをadapter可能な部分と置換対象に分ける。

---

## 7. I-02 / I-03評価を混ぜない

Embedding model比較とVector backend比較は独立させる。

推奨順序:

```text
I-01 Representation contract確定
  ↓
固定Exact baselineを作る
  ↓
I-02 Embedding model/provider比較
  ↓
Embedding Spaceを固定
  ↓
I-03 Vector backend比較
  ↓
最終候補組み合わせ再評価
```

backend差とmodel差を同時に変える比較は禁止する。

---

## 8. I-07 goldを早期に設計する理由

Task番号上はI-07だが、I-01〜I-03の判断基準としてgold queryの骨格は早期に利用する。

最低限含めるquery category:

- exact name / alias
- 日本語短語
- fine-grained Statement meaning
- Facet-specific query
- conditional / exception query
- temporal query
- cross-lingual query
- Object overall similarity
- Facet similarity
- Evidence lexical / semantic
- current / historical isolation
- Class / Facet filter correctness

ただし正式benchmark fixture / acceptance suite化はI-07で行う。

---

## 9. Phase Iで守るFailure Domain

Phase Hで確立したcanonical / derived separationを維持する。

```text
accepted Object Version
  = canonical

Search Representation
Embedding
Vector Index
  = derived
```

Embedding / Vector生成が失敗しても、

- current Versionをrollbackしない
- canonical Knowledgeを削除しない
- external providerへsilent fallbackしない
- stale Vectorをready扱いしない

`object_derived_states`を通じて`pending / ready / failed / stale相当`を検出・再実行可能にする。

---

## 10. Phase I開始時の実装順序

推奨順序:

1. I-01 Search Representation domain modelを定義する。
2. SQLite persistence / membership / content hashの必要schemaを設計する。
3. deterministic Representation Builderを実装する。
4. Object / Facet / Statement / Evidence fixtureでbuilder出力を固定する。
5. current/historical scopeとrepresentation reuse条件をtestする。
6. I-02用Exact / provider evaluation interfaceを準備する。

I-01完了時点ではANN backendを実装する必要はない。

---

## 11. Phase I移行判定

Phase H closure auditによりH-01〜H-04と完了条件は満たされている。

Phase Iに必要な前提も、

- structured accepted Knowledge
- immutable Version
- current/historical identity
- Evidence grounding
- derived-state lifecycle
- Search requirements
- Embedding / Vector技術調査

が揃っている。

Phase IはI-01〜I-07を完了し、正式Search gold / 100k Backend benchmarkを含む完了条件を満たした。Phase Iを**Complete**とする。

次に実施するTask:

```text
J-01 [P0] Retrieval CoreとMCP Adapterを分離する
```
