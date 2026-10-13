# VectorIndexAdapter / Backend Evaluation — Phase I / I-03

更新日: 2026-10-13

- Status: **Accepted / Implemented**
- Task: `I-03 [P0] VectorIndexAdapterを設計しBackendを比較決定する`
- Prerequisite: `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
- Next task: `I-04 [P0] Multi-representation Hybrid Search / Object Aggregationを実装する`

---

## 1. 結論

Phase Iの標準Vector backendは、**local Qdrant HNSW**とする。

```text
Backend             Qdrant
Server              1.19.2 benchmarked
Client              qdrant-client 1.19.1 benchmarked / >=1.19,<2
Distance            cosine
Embedding Space     I-02 Harrier OSS v1 0.6B / 1024 dim
HNSW m              16
HNSW ef_construct   128
Search hnsw_ef      256
full_scan_threshold 10
indexing_threshold  1000
Payload filter      enabled
Telemetry           disabled for local server operation
Fallback            none
```

第2候補は**LanceDB embedded IVF_FLAT**とする。

LanceDBはserver不要・rebuild高速・disk小であり、30,000 vector試験では
`64 partitions / nprobes=48 / refine_factor=1`でExact top-10に対するRecall@10 100%を得た。
しかし同条件でQdrantはより低latencyで100% Recallを得ており、payload filter・incremental update・将来の大量Statement scaleに対する余力を優先した。

Qdrant停止時にLanceDBへ**silent fallbackしない**。
Backend変更は明示的なconfiguration変更とDerived Index rebuildとして扱う。

---

## 2. I-03で固定した境界

I-03ではEmbedding品質を再評価しない。

```text
Canonical SQLite Knowledge
        ↓
I-01 Search Representation
        ↓
I-02 Harrier Embedding Space
        ↓
Float32 representation embedding cache
        ↓
I-03 VectorIndexAdapter
        ↓
Qdrant HNSW derived index
```

固定Embedding Space:

```text
Provider        sentence-transformers
Model           microsoft/harrier-oss-v1-0.6b
Revision        f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Dimension       1024
Normalization   L2
Context         32768
Overflow        reject
```

Vector backend差とEmbedding model差を混同しない。

---

## 3. VectorIndexAdapter contract

`src/sgokb/domain/vector_index.py`をbackend非依存contractとする。

主要型:

```text
VectorIndexPoint
  point_id
  vector
  metadata

VectorSearchFilter
  matches
  ranges

VectorSearchHit
  point_id
  score
  rank
  metadata

VectorIndexMetadata
  backend_key / backend_version
  space_id / dimension / distance
  points_count / indexed_points_count
  approximate / status / configuration
```

主要operation:

```text
upsert(space, points)
search(space, query_vector, limit, filters)
delete(space, point_ids)
rebuild(space, points)
metadata(space)
drop(space)
```

### 3.1 Hard filter

`VectorSearchFilter`はcandidate生成中に適用するhard filterである。

- equality / IN: `VectorMatch`
- numeric range: `VectorRange`

backendがfilterをtop-k取得後にだけ適用し、候補Recallを黙って落とす実装は禁止する。
Qdrant adapterではpayload filterとしてqueryへ渡す。

### 3.2 Score semantics

Adapter APIのscoreは「高いほどqueryに近い」検索scoreとして扱う。

これはFact confidence、Evidence strength、truth probabilityではない。
検索scoreをKnowledgeの信頼度へ流用しない。

### 3.3 Embedding Space isolation

Vector IndexはEmbedding Spaceごとに物理的に分離する。

異なるmodel / revision / dimension / preprocessingのvectorを同じcollectionへ混在させない。

---

## 4. Qdrant physical mapping

実装:

`src/sgokb/retrieval/vector_index.py`

### 4.1 Collection identity

Windowsでは、64桁`space_id`をそのまま深いQdrant storage pathのcollection名へ使うと、内部pathが長くなり`os error 3`が発生するケースを実機で確認した。

そのためcollection名は次とする。

```text
<collection_prefix>_<space_id first 24 hex chars>
```

完全な`space_id`はQdrant collection metadataへ保存する。

```text
metadata.sgokb_space_id = full 64-char space_id
```

既存collection再利用時は、

1. dimension一致
2. full `sgokb_space_id`一致

を両方確認する。

24 hex chars = 96 bitのprefixは物理名短縮専用であり、Embedding Space identityそのものではない。

2026-10-14のI-05 native smokeで、collection名を短縮していてもQdrantのstorage root自体が深い場合、payload index内部path生成で同じ`os error 3`が再現することを確認した。短いstorage rootへ変更すると同一Qdrant 1.19.2 / 同一collection構成で正常動作した。

したがってWindows運用では、collection名短縮に加えて**Qdrant storage rootも十分短いpathへ配置する**ことを推奨する。これはcanonical SQLite配置とは独立したDerived Index運用制約である。

### 4.2 Point identity

SGOKBの`representation_id`はQdrant固有IDへ露出させない。

Qdrant point IDは、

```text
UUIDv5(namespace, full space_id + SGOKB point_id)
```

で決定論的に生成する。

元のSGOKB IDはpayloadの予約fieldへ保持する。

```text
__sgokb_point_id
__sgokb_space_id
```

これにより任意文字列のrepresentation IDでもQdrantへ格納できる。

### 4.3 Filter payload

標準index対象metadata:

```text
kind
object_id
version_id
facet_id
statement_id
evidence_id
source_id
snapshot_id
primary_class
additional_classes
ancestor_classes
object_status
derivation_kind
is_current
```

I-04でObject aggregation / Class filterを実装する際、この派生metadataをQdrantへコピーする。
正本はSQLite membershipであり、Qdrant payloadはcanonicalではない。

---

## 5. Rebuild / update strategy

### Full rebuild

Qdrantのfull rebuildは次の順序とする。

```text
1. existing collection drop
2. HNSW collection作成
3. payload index作成
4. indexing_threshold = 0
5. Float32 vectorをbulk upload
6. indexing_threshold = 1000へ戻す
7. optimizer完了を待つ
8. metadata/statusを確認
```

bulk投入中に小batchごとHNSWを再構築しない。

ready判定は、

```text
expected point count reached
AND collection status = green
AND optimizer status = ok
```

とする。

小規模collectionではQdrantが意図的にHNSWを作らずExact/Flat検索する場合があるため、
`indexed_vectors_count == points_count`を常に要求しない。

### Incremental update

`upsert()`を利用する。

同一SGOKB point IDは同じ決定論的Qdrant UUIDへ写像されるため、再生成vectorは同一pointを更新する。

### Delete / invalidate

canonical Version rollbackやrepresentation invalidation時は`delete()`で派生pointを除去できる。

ただしcanonical Knowledge自体は変更しない。

---

## 6. Benchmark methodology

正式Search goldはI-07で作る。
I-03ではbackend差を測るため、I-02と同じHarrier vectorを固定した。

実データ4,851件だけではANN差が小さいため、30,000 vectorのdeterministic scale fixtureも作成した。

```text
source vectors: I-02 SGOKB 4,851 Harrier embeddings
scale:          30,000
method:         real vectorsをtile
                + deterministic Gaussian noise sigma=0.002
                + L2 normalize
query:          I-02 26 queries
filter:         8 partitionのうち1 partitionをhard filter
vector:         Float32 / 1024 dim
reference:      NumPy Exact cosine top-10
hardware:       RTX 4090環境の同一Windows PC
```

評価:

- query p50 / p95
- Exact top-10に対するRecall@10
- filtered Recall@10
- build / index時間
- disk
- incremental update
- Windows運用コスト

---

## 7. Benchmark results

### 7.1 初期比較

| Backend | Profile | Build | p50 | R@10 | Filter p50 | Filter R@10 | Disk |
|---|---|---:|---:|---:|---:|---:|---:|
| NumPy Exact | in-memory | - | 3.81 ms | 100% | 3.96 ms | 100% | RAM only |
| sqlite-vec 0.1.9 | Flat | 49.82 s | 187.45 ms | 100% | 22.83 ms | 100% | 135 MB |
| SQLite-Vector 1.1.2 | Exact AVX2 | 0.62 s | 161.81 ms | 100% | 179.72 ms | 100% | 139 MB |
| SQLite-Vector 1.1.2 | TurboQuant 4-bit | 1.44 s | 12.78 ms | 86.5% | 34.53 ms | 90.4% | 154 MB* |
| LanceDB 0.40.0 | Flat | 0.26 s | 111.74 ms | 100% | 115.26 ms | 100% | 123 MB |
| LanceDB 0.40.0 | IVF_FLAT 64 / nprobes16 | 2.32 s | 11.53 ms | 93.1% | 6.78 ms | 87.7% | 246 MB |
| Qdrant 1.19.2 | HNSW ef128 | 8.98 s | 2.68 ms | 100% | 1.29 ms | 99.2% | 約327 MiB steady |

`*` SQLite-Vector diskはExact table + quantized dataを同じDBで測定した値。

### 7.2 ANN tuning

LanceDB:

```text
64 partitions
nprobes=48
refine_factor=1

unfiltered: p50 9.85 ms / R@10 100%
filtered:   p50 5.21 ms / R@10 100%
```

Qdrant:

```text
m=16
 ef_construct=128
hnsw_ef=256

unfiltered: p50 2.35 ms / p95 3.14 ms / R@10 100%
filtered:   p50 2.53 ms / p95 7.13 ms / R@10 100%
```

今回のfixtureでは`hnsw_ef=256`を標準とする。

### 7.3 Incremental update 100 points

| Backend | 100 point update |
|---|---:|
| SQLite-Vector ordinary Float32 row | 約0.8 ms |
| LanceDB merge/upsert | 約30.9 ms |
| Qdrant HNSW upsert | 約53.6 ms |
| sqlite-vec delete + insert | 約164 ms |

SQLite-Vectorの値はordinary Float32 row updateであり、TurboQuant再構築コストを含まない。

---

## 8. Backend decision

### Qdrant — 採用

採用理由:

- 30,000 / 1024-dim試験で`hnsw_ef=256`ならExact top-10に対して100% Recall。
- unfiltered / filteredとも数ms。
- payload filterをANN query内で適用できる。
- incremental upsertが可能。
- 将来I-04のObject grouping / payload-based filteringへ拡張しやすい。
- SQLite canonical storeから完全rebuild可能。
- Windows native server 1.19.2で実機動作確認済み。

欠点:

- 常駐processが必要。
- LanceDBよりdiskが大きい。
- binary/runtimeのversion管理が追加される。
- server telemetryを明示的にdisableする必要がある。

これらはDerived Search Indexとして許容する。

### LanceDB — 第2候補

長所:

- embeddedでserver不要。
- rebuildが速い。
- Qdrantよりdiskが小さい。
- `nprobes=48`で今回100% Recall。

不採用理由:

- 同Recall条件でQdrantよりquery latencyが高い。
- scale増大時、IVFのpartition / nprobes再調整が必要。
- Qdrantのpayload-filtered HNSWの方がI-04以降の検索用途に余力がある。

Qdrantの運用コストが将来問題になった場合の第一再評価候補とする。

### sqlite-vec — Exact fallback/reference候補のみ

stable 0.1.9は今回の対象ではFlat/Exactとして評価した。
ANN系機能は2026-10時点でalpha系列のため、Phase I標準にはしない。

### SQLite-Vector — Exact / quantized reference

Exactは単純でupdateが非常に軽いが、30,000件 / 1024次元でquery latencyが大きい。
TurboQuant 4-bitは高速だが今回のRecall損失が大きく、標準にはしない。

### NumPy Exact — benchmark reference

30,000件では非常に速かったが、全vectorのRAM常駐、永続index/filter/update責務を持たない。
I-07でANN Recallを測るExact referenceとして保持する。

---

## 9. Local-only / failure boundary

Qdrantは**localhostのみ**をPhase I標準とする。

```text
Qdrant unavailable
  ↓
Semantic Vector channel = unavailable
  ↓
canonical SQLite read = 継続
Lexical Search = 継続
  ↓
検索結果にはdegraded状態を明示
```

禁止:

- cloud Qdrantへのsilent接続
- LanceDBへのsilent backend切替
-別Embedding Spaceへのsilent切替
- external embedding providerへのsilent fallback

Qdrant index消失はcanonical corruptionではない。
`search_representation_embeddings` + membership metadataからfull rebuildする。

Qdrant storage自体をcanonical backup対象にはしない。

---

## 10. Qdrant local operation

I-03実測では公式Windows x86_64 `qdrant.exe` 1.19.2を使用した。

benchmark時設定:

```text
HTTP  localhost:6335
 gRPC  localhost:6336
telemetry disabled
```

production portはconfigurationで決定し、adapterへ明示注入する。

SGOKB coreがQdrant processを暗黙起動しない。
process lifecycleはoperation layerの責務とする。

Qdrant停止時は明示的なVector Search unavailableとして扱う。

---

## 11. Implementation

追加:

```text
src/sgokb/domain/vector_index.py
src/sgokb/retrieval/vector_index.py
tests/test_vector_index.py
```

`pyproject.toml`:

```toml
vector-qdrant = ["qdrant-client>=1.19,<2"]
```

Qdrant local modeによるcontract testと、native Windows Qdrant serverによるremote smoke testの両方を実施した。

---

## 12. I-04へ固定して渡す条件

I-04では原則として次を変更しない。

```text
Embedding model     Harrier OSS v1 0.6B
Embedding dim       1024
Vector backend      Qdrant
Distance            cosine
HNSW m              16
HNSW ef_construct   128
HNSW search ef      256
Hard filter         VectorSearchFilter → Qdrant payload filter
Current scope       accepted/current membership metadata
Score direction     higher = more similar
```

I-04が実装するもの:

- FTS + Semantic candidate fusion
- Object / Facet / Statement / Evidence channel
- point metadata作成
- current/historical scopeのhard filter
- Object aggregation
- matched Statement / Facet / snippet / grounding
- degraded semantic-channel表示

Vector backend固有APIをI-04へ漏らさない。

---

## 13. I-07へ残す事項

I-03の30,000 vector fixtureはbackend比較用であり、正式Search goldではない。

I-07では次を再測定する。

- actual accepted canonical Knowledge
- 100k / 300k / 1M scale可能範囲
- Object / Facet / Statement / Evidence別Recall
- Class / Facet / current / historical / temporal filter
- nDCG / MRR / Recall
- HNSW ef sensitivity
- payload filter cardinality別latency
- rebuild / crash recovery
- index disk / RAM
- Qdrant停止・再起動・full rebuild

I-07でQdrantの運用コストが性能差に見合わないと判明した場合のみ、LanceDB embeddedを再評価する。

---

## 14. Public implementation references used for I-03

- Qdrant releases / filtering / Python client documentation
- LanceDB vector and scalar index documentation
- sqlite-vec stable release / metadata filtering documentation
- SQLite-Vector / sqliteai-vector exact and TurboQuant documentation

外部benchmark値だけでは採用せず、最終判断はSGOKB固定Embedding Spaceを使ったローカル実測を優先した。


---

## I-07 100k tuning follow-up

I-03の30k benchmarkでは`hnsw_ef=256`でRecall@10 100%だった。I-07ではfrozen Search gold由来の100k / 1024-dim workloadへ拡大し、Exact top-10との比較を再実施した。100kでは256でRecall不足runが発生したため、`384 / 512 / 768 / 1024`を追加評価し、latencyとRecallの均衡から**Phase I current defaultを`hnsw_ef=768`へ更新する**。`m=16 / ef_construct=128 / full_scan_threshold=10`は維持する。正式結果は`SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`を正本とする。
