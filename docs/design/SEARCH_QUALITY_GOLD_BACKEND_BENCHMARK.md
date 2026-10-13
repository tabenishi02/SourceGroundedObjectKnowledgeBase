# Search Quality Gold / Backend Benchmark

更新日: 2026-10-14

- Status: **Accepted / I-07 Complete**
- Task: `I-07 [P0] 検索品質gold / Backend benchmarkを作成する`
- Frozen fixture: `benchmark/search-quality-gold-v1.json`
- Search harness: `scripts/run_search_quality_gold.py`
- ANN harness: `scripts/run_vector_backend_benchmark.py`
- Reranker harness: `scripts/run_search_gold_reranker_benchmark.py`

---

## 1. 結論

Phase Iの検索契約を正式goldで検証し、完了条件を満たした。

```text
Default free-text search: Hybrid
Embedding: microsoft/harrier-oss-v1-0.6b / 1024 dim
Vector backend: Qdrant HNSW 1.19.2
Qdrant search hnsw_ef: 768
Similarity: overall + explicit facet mode
Reranker: MVP mandatoryではない
Balanced reranker candidate: BAAI/bge-reranker-v2-m3
Quality reranker candidate: zeroentropy/zerank-2-reranker
```

Qdrantの`hnsw_ef`はI-03の30k benchmarkで採用した256から、I-07の100k benchmarkを受けて**768へ更新**する。

---

## 2. Frozen Search gold

Goldは外部Web内容の変化で揺れないhuman-authored synthetic canonical Knowledgeとした。

| Item | Count |
|---|---:|
| Object | 20 |
| accepted Version | 21 |
| Search Representation / Vector point | 109 |
| free-text Query | 24 |
| Statement評価Query | 22 |
| Similarity case | 4 |
| Evidence Search case | 3 |
| contract case | 5 |

Primary Class coverage:

```text
character / work / concept
person / organization / series / place / event
software / product / species / phenomenon / language / ability
```

Query categoryにはexact name / alias、日本語短語、細粒度Statement、Facet、条件・例外、時系列、Class filter、日本語、英語→日本語cross-lingualを含める。

---

## 3. Object Search quality

| Mode | MRR | Recall@1 | Recall@5 | Recall@10 | nDCG@10 | p50 |
|---|---:|---:|---:|---:|---:|---:|
| Lexical | 0.167 | 14.6% | 14.6% | 14.6% | 0.158 | 0.33 ms |
| Semantic | 1.000 | 85.4% | 100.0% | 100.0% | 0.993 | 35.89 ms |
| **Hybrid** | **1.000** | **85.4%** | **100.0%** | **100.0%** | **1.000** | **35.70 ms** |

Lexical平均が低いのはgoldの多くをliteral一致ではなくparaphrase / semantic queryへ意図的にしたためである。Identity専用caseではexact name / alias lookup accuracyは**100.0%**だった。

HybridはSemanticと同じObject Recallを維持しつつ、exact identity / lexical channelを保持するため、通常free-text Searchのdefaultを維持する。

### Statement Search

Statement Semantic Search:

```text
MRR        1.000
Recall@1   86.4%
Recall@10  100.0%
nDCG@10    0.993
```

### Statement Embedding ablation

22 fine-grained QueryについてStatement pointあり / なしを比較した。

| Condition | MRR | Recall@1 | Recall@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| with Statement point | 1.000 | 84.1% | 100.0% | 1.000 |
| without Statement point | 1.000 | 84.1% | 100.0% | 1.000 |

この20 Object goldではObject / Facet representationだけでも対象Objectを十分取得でき、**Object-level改善は未観測**だった。したがってStatement Embeddingの価値を過大評価しない。一方、Statement Search自体のRecall@10は100%で、matched Statement / grounding / 将来の大規模同一Facet競合に必要なため、標準representationから削除もしない。N-06で実データscaleを再評価する。

---

## 4. Filter / Version / Temporal correctness

Contract caseは **5 / 5 passed**。

検証内容:

- current searchがhistorical-only Statementを混ぜない
- explicit historical Versionで旧Statementを取得できる
- valid-at期間内のtemporal Statementを取得できる
- valid-at期間外では除外する
- Facet hard filterが別Facet / object_overallへsilent fallbackしない

---

## 5. Object Similarity human gold

Judgement channelは`human_authored_synthetic_gold`。

| Similarity | MRR | Recall@1 | Recall@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| overall | 0.833 | 66.7% | 100.0% | 0.877 |
| facet-specific | **1.000** | **100.0%** | **100.0%** | **1.000** |

Character overall caseではAoiに対してRenがMikaより上に来たが、`values` Facetを指定するとMikaが正しく1位になった。これはI-05の「Facet指定時はoverallへfallbackしない」設計を支持する結果である。

> 比較したい意味軸が既知ならFacet similarityを優先し、overall similarityは広い探索用途として扱う。

---

## 6. Evidence Search

Lexical/association path、semantic pathとも3 gold caseでMRR / Recall@10 / nDCG@10 = **1.000**だった。Evidence SearchはObject Knowledge Searchへ混ぜず、F-03の独立retrievalとして維持する。

---

## 7. Formal reranker gold

Harrier Statement top-50 candidate RecallはBGE / zerank-2とも100%。

| Reranker | Statement MRR | Statement R@10 | Statement→Object MRR | Object-level MRR | Object nDCG@10 | Statement p50 | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| **BGE v2-m3** | 0.970 | 100.0% | 1.000 | 1.000 | 0.996 | 19.4 ms | 2.24 GiB |
| zerank-2 | **1.000** | **100.0%** | 1.000 | 1.000 | **1.000** | 48.3 ms | 9.43 GiB |

zerank-2はStatement単位品質が最高だが、Object-levelでは差がほぼ消える。BGEは大幅に軽いためbalanced/default候補、zerank-2はquality profileとして維持する。

Phase I MVPではRerankerをmandatoryにしない。gold上でHybrid単体がObject MRR 1.000 / Recall@10 100%であり、Rerankerは追加latency / dependencyと引き換えになるためである。N-06の実データ評価で必要性を再判定する。

---

## 8. 100k Vector backend benchmark

Scale fixtureは109個のfrozen gold Vectorを基に、3本の実Vectorを決定論的な重みで混合しGaussian noiseを加えた100,000 unique-like vectors。単純tile + 微小noiseによるnear-duplicate ID Recall歪みを避ける。

```text
Points: 100,000
Dimension: 1024 Float32
Queries: 24
Hard filter partitions: 8
Exact reference: NumPy Float32 cosine
```

### Exact vs Qdrant

| Backend | Unfiltered p50 | Filtered p50 | Unfiltered R@10 | Filtered R@10 |
|---|---:|---:|---:|---:|
| NumPy Exact | 12.17 ms | 16.79 ms | 100% reference | 100% reference |
| Qdrant HNSW | 8.16 ms | 6.19 ms | 100.0% | 100.0% |

Qdrant profile:

```text
server 1.19.2
m=16
ef_construct=128
hnsw_ef=768
full_scan_threshold=10
```

`hnsw_ef=256`は100k scaleでRecallが不足するrunがあった。追加tuningで768がlatency増を小さく抑えながらRecallを改善したため、Phase I defaultを768へ更新する。

### Build / update / rebuild / size

| Metric | Result |
|---|---:|
| Initial build | 53.76 s |
| Full rebuild | 52.77 s |
| Incremental update 100 points | 84.7 ms |
| Disk size | 1.09 GiB |
| Indexed points | 100,000 |

Vector Indexは引き続きcanonical backupではなく、SQLiteからrebuildできるDerived Search Indexとする。

---

## 9. Acceptance decision

I-07 goldから次を確認した。

1. exact name / aliasはSemanticに埋没しない。
2. paraphrase / cross-lingual / fine-grained queryをSemantic / Hybridで取得できる。
3. Statement Searchは細粒度Knowledgeを直接取得できる。
4. Class / Facet / Version / temporal filterがcandidate scopeを正しく制限する。
5. current / historical Knowledgeがsilent混合されない。
6. overall similarityとFacet similarityを区別でき、Facet指定が比較軸を改善できる。
7. Evidence Searchを独立して維持できる。
8. 100k VectorでQdrant ANNをExact referenceと比較し、build/update/rebuild/diskを測定できる。
9. Reranker有無をfirst-stage Recallと分離して評価できる。

したがってPhase I完了条件、

> 「文字列が一致するObject」だけでなく、「意味・価値観・テーマ等が近いObject」を実用精度で取得できる。

を満たしたと判断する。

---

## 10. Reproduction

```powershell
# frozen canonical Search gold
python scripts/run_search_quality_gold.py --local-files-only

# native Qdrantをlocalhostで起動後
python scripts/run_vector_backend_benchmark.py --count 100000 --hnsw-ef 768

# BGE / zerank-2 formal reranker comparison
python scripts/run_search_gold_reranker_benchmark.py
```

Benchmark outputは`.local/`へ保存しGit管理しない。正本入力fixture / harness /集計結果の設計判断をGit管理する。

**Status: I-07 Complete / Phase I Complete / Phase J Ready**
