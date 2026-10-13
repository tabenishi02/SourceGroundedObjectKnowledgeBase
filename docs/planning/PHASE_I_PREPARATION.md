# Source Grounded Object Knowledge Base — Phase I Preparation

更新日: 2026-10-13

- Status: Ready to Start
- Completed phase: Phase H — Result Validation / Import / Rendering
- Current phase: Phase I — 意味検索・類似検索
- Next task: `I-01 [P0] Search Representation / Embedding対象を設計する`
- Working branch: `integration/knowledge-base-redesign`
- Closure input: `docs/planning/PHASE_H_CLOSURE_AUDIT.md`

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
| I-01 Search Representation / Embedding対象 | P0 | Next | Object / Facet / Statement / Evidenceの派生表現契約を設計 |
| I-02 Embedding Provider / 多言語Model比較 | P0 | Pending | providerとmodelを分離して日本語・cross-lingual評価 |
| I-03 VectorIndexAdapter / Backend比較 | P0 | Pending | Exact / sqlite系 / LanceDB / Qdrant等を比較 |
| I-04 Hybrid Search / Object Aggregation | P0 | Pending | Lexical + multi-representation SemanticをObjectへ集約 |
| I-05 `find_similar_objects` | P0 | Pending | overall / Facet similarity |
| I-06 Reranker評価 | P1 | Pending | first-stage recall確保後に導入判断 |
| I-07 Search gold / Backend benchmark | P0 | Pending | Recall / MRR / nDCG / latency / rebuild等を評価 |

I-01を先に確定しないままI-02/I-03を始めると、model/backend比較対象となるrepresentation自体が揺れるため、I-01をPhase Iの設計起点とする。

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

したがってPhase Iは**Ready to Start**とする。

次に実施するTask:

```text
I-01 [P0] Search Representation / Embedding対象を設計する
```
