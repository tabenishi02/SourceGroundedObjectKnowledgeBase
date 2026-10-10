# SGOKB Embedding / Vector Search 技術調査

更新日: 2026-10-11

- Scope: B-05 Search / Retrieval要件の補足調査、Phase E / I / Nへの設計入力
- Status: Accepted as design input
- Related:
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `src/sgokb/search.py`
  - `src/sgokb/migrations/001_initial.sql`

---

## 1. 調査目的

B-05初版では、Object全体とFacet単位のsemantic representation / Embeddingを初期要件とし、Knowledge Statement個別Embeddingは実測後に追加判断する方針としていた。

その後の検討で、Facet全体を1 Vectorへ集約すると、次のような細粒度KnowledgeがSemantic Searchで薄まる可能性が高いことを確認した。

- 「失敗を長く引きずる」
- 「年下にだけ保護者的に振る舞う」
- 「家族を侮辱された場合だけ激昂する」
- 「物語序盤では敵対し、終盤では協力する」
- 「雨天時だけ能力が弱くなる」

SGOKBの目的は、保存したKnowledgeを後から検索・比較・再利用できる外部知識記憶にすることである。細かいKnowledgeを保存しても意味検索から発見できないなら、Knowledge Storeの価値を大きく損なう。

そのため本調査では、**accepted Object Knowledgeに含まれる検索可能なKnowledge Statementへ個別Semantic Representation / Embeddingを持たせることを標準方針とした場合の影響、既存ライブラリの流用可能性、SGOKBへ組み込む設計方法**を整理する。

---

## 2. 用語

### 2.1 Embedding

文章等を、意味的な近さを比較できる数値列へ変換したもの。

```text
「仲間を守るため自分を犠牲にする」
        ↓ Embedding model
[0.12, -0.31, 0.77, ...]
```

この数値列をVectorと呼ぶ。

EmbeddingそのものはKnowledgeの正本ではなく、検索のための派生データである。

### 2.2 Vector

Embedding modelが生成する多次元の数値列。

Vector同士のdistance / similarityを計算し、意味的に近い文章候補を探す。

### 2.3 Exact / Flat Search

Query Vectorを保存Vector全件と比較する検索。

- 長所: 近傍探索としての取りこぼしがない。
- 短所: Vector件数に比例して遅くなる。

SGOKBではANN方式のRecallを測るための基準として利用価値が高い。

### 2.4 ANN

Approximate Nearest Neighbor、近似最近傍検索。

全Vectorを毎回調べず、近そうな領域だけを探索して高速化する。

Exactと比較して検索結果が一部変わる可能性があるため、SGOKBではgold queryとExact baselineを使ってRecallを検証する。

### 2.5 HNSW

Hierarchical Navigable Small World。ANNを実現する代表的なGraph型Index。

大量Vectorを近接関係のGraphとして索引化し、上位の粗い探索から近い候補へ降りていくことで、全件走査を避ける。

QdrantやLanceDB等で利用可能な方式である。

### 2.6 Semantic Representation

Embeddingへ入力するためにSGOKBがKnowledgeから生成する検索用派生表現。

正本Knowledgeそのものと同一である必要はない。

例えば正本Statementが短すぎる場合、Object名・Facet・temporal scope等を付加してEmbedding用textを生成できる。

```text
正本Statement:
「主人公からの協力要請を拒絶した。」

Search Representation:
Object: Character A
Facet: relationships
Temporal scope: story_end
Statement: 主人公からの協力要請を拒絶した。
```

Search Representationは再生成可能であり、変更してもObject Knowledge Versionを書き換えない。

---

## 3. Statement-level Embeddingを標準化する理由

### 3.1 Facet Vectorだけでは意味が平均化される

例えばpersonality Facetが次を含む場合を考える。

```text
- 普段は温厚で協調的
- 自分の失敗を長く引きずる
- 年下に対して保護者的
- 家族を侮辱された場合だけ激昂する
```

Facet全体を1 Vectorへ変換すると、4つの意味が1つの表現へ統合される。

「失敗を引きずる人物」のような細かいQueryでは、その特徴がFacet全体のVector内で弱くなり、検索順位が低下する可能性がある。

StatementごとにVectorを持てば、Queryは対応Statementへ直接近づける。

### 3.2 条件・例外・時間変化を検索しやすい

特に次はStatement単位の方が検索に適している。

- 条件付き性質
- 例外
- 特定時期だけ成立する情報
- 小さなRelation説明
- Facetの少数派特徴
- 相互に矛盾するgrounded Statement

### 3.3 Lexical Searchだけでは言い換えを拾えない

保存:

```text
「閉所に対して強い恐怖を示す」
```

Query:

```text
「狭い場所を怖がる人物」
```

文字列一致は弱いがSemantic Searchなら取得可能性が高い。

### 3.4 Statement Embeddingは旧Fragment大量生成とは異なる

旧Fragment Pipelineでは、全EvidenceをLLMで大量のFragmentへ変換すること自体が高コストだった。

新設計のKnowledge Statementは、Object Result / accepted Knowledge Version内ですでに意味的に整理されたKnowledge単位である。

したがってStatement Embeddingは、

```text
Evidence
↓ 高コストLLMで大量Fragment生成
↓ Fragment Vector化
```

を復活させるものではない。

```text
accepted Object Knowledge Version
↓ 既存Statementから決定論的Search Representation生成
↓ Embedding
```

という検索派生処理である。

---

## 4. 採用するsemantic representation階層

SGOKBは少なくとも次の3階層を併用する。

```text
Object overall representation
  └─ Object全体の意味・類似検索

Facet representation
  └─ personality / values / themes等の観点別検索・類似検索

Statement representation
  └─ 細かいKnowledge、条件、例外、時系列情報の意味検索
```

Evidence representationも別系統として維持する。

```text
Evidence representation
  └─ Knowledge生成前のSource/Evidence検索、監査、再分析
```

Object / Facet / Statement / EvidenceのVectorは用途が異なるため、単一の「Vector一覧」として意味を混在させない。

---

## 5. 推奨アーキテクチャ

```text
                    SQLite
                 canonical DB
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     Object          Facet        Statement
       │              │              │
       └──────── Search Representation ─────────┐
                                                │
                                      EmbeddingProvider
                                                │
                                      FastEmbed / other
                                                │
                                                ↓
                                       VectorIndexAdapter
                          ┌─────────────┼─────────────┐
                          │             │             │
                     sqlite系       LanceDB       Qdrant
                          │
                          ↓
                  Statement-level hits
                          │
                   Object Aggregator
                          │
                Hybrid Fusion / Rerank
                          │
                          ↓
                   1 Object = 1 result
```

### 5.1 SQLite

Object / Version / Facet / Statement / Relation / Evidence等の正本。

Vector backendを変更・削除してもKnowledgeを失わない。

### 5.2 Search Representation Builder

正本KnowledgeからEmbeddingに適したtextを決定論的に生成する。

最低限、representationの生成versionを追跡する。

Statement representationでは必要に応じて次を付加できる。

- Object name / stable ID context
- Primary Class
- Facet key
- temporal scope
- derivation kind
- Statement text

ただし、検索ノイズとなる管理情報を無条件に入れない。

### 5.3 EmbeddingProvider

text → Vector変換を抽象化する。

SGOKB Coreが特定model / libraryへ直接依存しないようにする。

候補:

- FastEmbed
- SentenceTransformers系
- OpenAI-compatible embedding provider
- その他将来provider

### 5.4 VectorIndexAdapter

Vector保存・近傍検索のbackend差を隔離する。

論理的には少なくとも次を表現できることを求める。

```text
upsert representations
search vector
filter by metadata
remove/invalidate representations
rebuild index
report backend/index metadata
```

SGOKB CoreからQdrant/LanceDB/sqlite拡張固有APIを直接呼ばない。

### 5.5 Statement-level hit

Semantic candidate generationの内部結果。

通常UI / MCPでそのまま大量表示しない。

### 5.6 Object Aggregator

Statement / Facet / Object representationのhitを`object_id`単位へ集約する。

B-05の`1 Object = 1 result`を維持する。

同じObjectの多数Statementがhitしても、Statement数の単純合計でObject scoreを無制限に上げない。

候補となる集約設計:

- best Statement score
- top-N capped contribution
- Facet diversity
- Object overall / Facet scoreとのfusion

具体式はPhase Iでgold評価して決定する。

### 5.7 Hybrid Fusion / Rerank

Identity / Lexical / Semantic各channelを統合する。

BM25 scoreとcosine similarity等のraw scoreを単純加算しない。

RRF、normalized score fusion、reranker等を比較する。

---

## 6. Statement Embedding導入の影響

### 6.1 利点

- 細粒度KnowledgeのSemantic Recall向上。
- 言い換えQueryへの耐性向上。
- 条件・例外・時間限定Knowledgeを発見しやすい。
- 検索結果の説明性向上。どのStatementがhitしたか示せる。
- Statement → Evidence Linkを通じてProvenanceへ直接遡りやすい。

### 6.2 Vector件数増加

Object数よりStatement数の方が大幅に多くなる。

例:

```text
10,000 Objects
平均30 Statements / Object
→ 300,000 Statement vectors
```

そのためPrototypeのPython brute-force cosineをそのまま本番利用することは難しくなる可能性が高い。

### 6.3 保存容量増加

float32 Vector本体の概算は次のとおり。

| Vector数 | 768次元 | 1024次元 | 1536次元 |
|---:|---:|---:|---:|
| 10,000 | 約29 MiB | 約39 MiB | 約59 MiB |
| 100,000 | 約293 MiB | 約391 MiB | 約586 MiB |
| 1,000,000 | 約2.86 GiB | 約3.81 GiB | 約5.72 GiB |

実際にはIndex / metadata / ID等の追加領域が必要になる。

PrototypeのようなJSON TEXT Vector保存を大規模Statement Indexへそのまま利用しない。

### 6.4 Versioningによる重複

B-04ではObject Resultをfull snapshotとしているため、v1 / v2 / v3に同一内容のStatementが残ることがある。

Embedding identityをStatement local IDだけへ結び付けると、同じSearch RepresentationをVersionごとに再Embeddingする無駄が生じる。

そのため次を分離する。

```text
Knowledge membership identity
  object_id / version_id / statement local reference

Embedding content identity
  embedding_space_id
  representation_version
  representation_hash
```

同一Embedding Space + 同一representation hashならVector reuse / dedupを可能にする。

ただしKnowledge Versionへの所属は別に追跡し、historical/current scopeを混同しない。

### 6.5 current / historical isolation

通常検索ではcurrent accepted Knowledgeだけを対象とする。

過去VersionのStatement Vectorが通常searchへ混ざらないよう、candidate filterまたはIndex scopeを持たせる。

Historical Searchでは明示Version scopeを利用する。

### 6.6 Context不足

Statement単体が「それ」「彼」等を含むとVector品質が落ちる可能性がある。

Search Representation BuilderでObject / Facet / temporal context等を必要に応じ補う。

正本Statementを書き換えて検索用文脈を埋め込まない。

### 6.7 同一Objectのhit独占

Statement単位検索では同一Objectから複数hitしやすい。

そのためStatement top-kをそのまま通常Object resultにしない。

Object Aggregatorでgroupし、代表matchと追加match detailを返す。

### 6.8 重複Statementによる過剰boost

似たStatementを大量に持つObjectが単純加算で有利にならないようにする。

同一Facet / 近似Statement contributionの上限、best score、diversity等を比較する。

---

## 7. 既存SGOKB資産の再利用

Prototypeには次が存在する。

- `EmbeddingSpace`
- Embedding provider abstraction
- Lexical / Semantic channel分離
- cosine search baseline
- RRF相当fusion
- replaceable reranker
- FTS5

これらの思想は維持できる。

変更が必要なのは検索対象である。

```text
旧:
search_items
├─ Evidence
└─ Fragment

新:
Search Representation
├─ Object overall
├─ Facet
├─ Knowledge Statement
└─ Evidence
```

`src/sgokb/search.py`のbrute cosineは小規模baseline / Exact比較用途として再利用できるが、Statement大量化後の最終backendとはみなさない。

---

## 8. 既存ライブラリ / アプリ調査

### 8.1 sqlite-vec

用途:

- SQLiteにVector検索を追加する軽量候補。
- SGOKBのSQLite中心設計と親和性が高い。

評価ポイント:

- 同一DBで運用しやすい。
- metadata / partitionを利用したscope分離を検討できる。
- 外部server不要。
- ANN機能の成熟度・Windows運用・性能を実測する必要がある。

公式:

- https://github.com/asg017/sqlite-vec
- https://alexgarcia.xyz/sqlite-vec/

### 8.2 sqlite-vector / SQLite Vector

用途:

- SQLite内Vector検索。
- Float32だけでなくFloat16 / BFloat16 / Int8 / UInt8 / 1-bit等を比較可能。
- Exact / quantized baseline候補。

公式APIではVectorをBLOBとして扱い、COSINE等のdistanceを指定できる。

SGOKBでは特に、Float32 exactをANN Recall測定の基準とする用途に向く。

公式:

- https://github.com/sqliteai/sqlite-vector
- https://github.com/sqliteai/sqlite-vector/blob/main/API.md

### 8.3 Qdrant

SGOKBのStatement検索要件との機能適合が高い。

特にQuery Groupsでpayload fieldを`group_by`できるため、

```text
Statement point
  payload.object_id
```

を検索し、Object単位へgroupする設計を参考または直接利用できる。

filterとVector Searchを同じQueryで組み合わせられるため、current Version / Class / Facet等のfilterにも適する。

通常は独立serviceとなるため、SQLite正本とは別のDerived Search Indexとして扱う。

公式:

- https://qdrant.tech/documentation/
- https://api.qdrant.tech/api-reference/search/query-points-groups

### 8.4 LanceDB

embedded local Vector DB候補。

Vector columnにIndexがなければflat search、IndexがあればANN searchを行える。HNSW / IVF系Index、scalar index、FTS / Hybrid等を比較できる。

Qdrant Serverほど運用を増やさず、SQLiteとは別のDerived Search Indexを持つ中間候補として有力。

Statement → Object groupingはSGOKB側Aggregationが必要になる可能性が高い。

公式:

- https://lancedb.github.io/lancedb/python/python/
- https://lancedb.com/docs/

### 8.5 Weaviate

初期backend候補としてより、multi-representation / fusion設計の参考価値が高い。

複数target vectorを同時検索し、minimum / sum / average / manual weights / relative score等でjoinできる。

またHybrid Searchではkeyword + vector結果をfusionする。

SGOKBのObject / Facet / Statement複数representationのscore統合設計を比較する参考とする。

公式:

- https://docs.weaviate.io/weaviate/search/multi-vector
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search

### 8.6 Haystack

検索backendそのものよりRetrieval Pipeline設計の参考とする。

`AutoMergingRetriever`はchild node hitが一定数を超えた場合にparent documentを返す。

これはSGOKBの、

```text
Statement hits
↓
Facet / Objectへ集約
```

という設計の参考になる。

`SentenceWindowRetriever`は細かいhitの前後contextを取得するため、Statement hitから関連Statement / Facet contextを組み立てる際の参考になる。

公式:

- https://docs.haystack.deepset.ai/reference/retrievers-api
- https://docs.haystack.deepset.ai/docs/sentencewindowretriever

### 8.7 FastEmbed

EmbeddingProvider候補。

Dense / Sparse Embedding、reranking等をローカル実行するための選択肢としてPhase Iで評価できる。

SGOKB CoreにはFastEmbed固有契約を持ち込まずProvider Adapter経由で利用する。

公式:

- https://qdrant.github.io/fastembed/
- https://qdrant.tech/documentation/fastembed/

---

## 9. Backend比較方針

Phase Iでは最低限次を比較する。

| 条件 | SGOKBでの位置づけ |
|---|---|
| SQLite系 Float32 Exact / Flat | ANN Recallの基準 |
| sqlite-vec | SQLite内軽量backend候補 |
| LanceDB ANN | embedded ANN候補 |
| Qdrant HNSW + grouping | 高性能・高機能基準 |

`sqlite-vector`はExact / quantized条件としてSQLite系baselineへ含めて比較する。

最初から1 backendへ固定しない。

---

## 10. 比較指標

### 10.1 検索品質

- Statement Recall@K
- Object Recall@K
- MRR
- nDCG
- fine-grained query hit率
- cross-lingual retrieval
- Class / Facet / current/history filter correctness

### 10.2 ANN品質

Exact結果を基準に、ANN top-kがどこまで一致するか測る。

`ANNが速い`だけでは採用しない。

### 10.3 性能

- Query latency
- p50 / p95 latency
- Index build time
- incremental update time
- rebuild time
- RAM
- Disk size

### 10.4 運用

- Windowsでの導入容易性
- server processの要否
- backup / rebuild容易性
- dependency maturity
- SQLite正本からの再構築容易性
- 障害時graceful degradation

---

## 11. Embedding Model / Provider比較

Vector backend比較とEmbedding model比較を同時に混ぜない。

原則として、

1. 固定Embedding Spaceでbackend比較。
2. 固定backendまたはExact baselineでEmbedding model比較。
3. 最終候補組み合わせを再評価。

とする。

Embedding Spaceは最低限、

- model
- revision
- dimension
- preprocessing / normalization
- provider configuration

を識別する。

異なるEmbedding Spaceのraw scoreを直接比較しない。

---

## 12. Incremental Embedding / Reuse

Object Version Import後に全Knowledgeを毎回再Embeddingしない。

```text
accepted Version
↓
Search Representation生成
↓
representation hash計算
↓
同一Embedding Space + hashが既存か?
├─ yes → Vector reuse
└─ no  → 新規Embedding
```

Versionごとのmembership / current scopeは別metadataとして保持する。

Vector reuseはKnowledge Versionの独立性を壊してはならない。

---

## 13. Index lifecycle

Vector Indexは正本ではない。

最低限次を可能にする。

- incremental upsert
- current Version切替に伴うscope更新
- archived Object除外
- Embedding Space変更時の別Index構築
- Representation Builder変更時の再生成
- index corruption時のfull rebuild
- backend変更時の再構築

SQLite正本から再構築できることを必須とする。

---

## 14. 通常検索で除外する管理情報

B-04 / B-05の方針を維持し、次は通常Statement Semantic Indexへ入れない。

- gap
- insufficient evidence
- unresolved reference
- Registry proposal

これらはObject自身の意味KnowledgeではなくKnowledge Baseの管理状態だからである。

conflict中でもaccepted / grounded Statement自体は検索可能とし、conflict flagを保持する。

---

## 15. 設計への正式反映方針

### B-05

旧方針:

> Knowledge Statement個別Embeddingは初期必須としない。

を撤回する。

新方針:

> accepted Object Knowledgeに含まれる検索可能なKnowledge Statementは、原則として個別Semantic Representationを生成可能とし、標準実装ではStatement-level Embeddingを生成する。

Object / Facet Embeddingも維持し、3階層のmulti-representation retrievalとする。

### Phase E

E-02でStatementとSearch Representationの対応を設計する。

E-04でVersion切替時のrepresentation invalidation / reuse / historical scopeを設計する。

Search Representation / Vector自体はObject Knowledge正本へ含めない。

### Phase I

I-01でObject / Facet / Statement / EvidenceのRepresentation Builder契約を設計する。

I-02でEmbedding Provider / Modelを比較する。

I-03でVectorIndexAdapterを定義し、Exact / sqlite系 / LanceDB / Qdrantを比較する。

I-04でStatement candidate → Object aggregation → Hybrid fusionを実装・評価する。

I-07でfine-grained Statement queryをgoldへ追加する。

### Phase N

Statement Embedding有無のRecall差、Exact vs ANN Recall、backend性能、incremental update、Index rebuildを受入評価へ追加する。

---

## 16. 現時点で採用しない固定判断

本調査時点では次を固定しない。

- 最終Embedding model
- 最終Embedding dimension
- 最終Vector backend
- sqlite-vec採用
- LanceDB採用
- Qdrant採用
- HNSW parameter
- Object aggregation score式
- Hybrid fusion式
- reranker採否
- quantization採否

これらはPhase Iの実測で決定する。

---

## 17. 推奨結論

SGOKBでは、検索Index件数を抑えるためにStatement-level Embeddingを省略するより、**細粒度Knowledgeを意味検索可能な状態で保持することを優先する。**

容量・速度問題は、

- VectorIndexAdapter
- Exact / ANN backend比較
- incremental Embedding
- representation hashによるVector reuse
- current / historical filter
- Statement → Object aggregation
- backend交換可能性

で解決する。

推奨する論理構造は次である。

```text
SQLite canonical Knowledge
↓
Object / Facet / Statement / Evidence Search Representation
↓
EmbeddingProvider
↓
VectorIndexAdapter
↓
Statement / Facet / Object candidates
↓
Object Aggregator
↓
Lexical + Semantic Hybrid Fusion
↓
1 Object = 1 result
```

Vector backendは正本ではなく再生成可能なDerived Search Indexとし、SGOKBのKnowledge Modelを特定Vector DBへ従属させない。

**Status: Research Complete / Design Input Accepted (2026-10-11)**
