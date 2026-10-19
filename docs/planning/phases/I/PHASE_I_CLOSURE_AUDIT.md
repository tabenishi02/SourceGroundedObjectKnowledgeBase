# Source Grounded Object Knowledge Base — Phase I Closure Audit

更新日: 2026-10-14

- Status: **Complete**
- Phase: `Phase I — 意味検索・類似検索`
- Scope: I-01〜I-07の完了状態、検索品質、回帰試験、Phase Jへの引継ぎ
- Next phase: `Phase J — MCP Knowledge Access Layer`
- Next task: `J-01 [P0] Retrieval CoreとMCP Adapterを分離する`

---

## 1. 結論

Phase Iの残タスクを再監査した結果、**未完了Taskは0件**だった。

I-01〜I-07はすべて完了し、正式Search goldと100k Vector backend benchmarkを含むPhase I完了条件を満たしている。

```text
I-01 Search Representation                  Complete
I-02 Embedding Provider / Model             Complete
I-03 VectorIndexAdapter / Backend           Complete
I-04 Hybrid Search / Object Aggregation     Complete
I-05 Object / Facet Similarity              Complete
I-06 Reranker evaluation                    Complete
I-07 Search gold / Backend benchmark        Complete
```

Phase Iを**Complete**とし、Phase Jへ移行可能と判定する。

---

## 2. Task別監査

| Task | Status | 主な正本 / 実装 |
|---|---|---|
| I-01 | Complete | `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`, Migration 014, `retrieval/search_representation.py` |
| I-02 | Complete | `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`, Migration 015, `retrieval/embedding.py`, `storage/embedding_repository.py` |
| I-03 | Complete | `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`, `domain/vector_index.py`, `retrieval/vector_index.py` |
| I-04 | Complete | `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`, Migration 016, `retrieval/hybrid_search.py` |
| I-05 | Complete | `docs/design/OBJECT_SIMILARITY_SEARCH.md`, `retrieval/similarity.py` |
| I-06 | Complete | `docs/design/RERANKER_SECOND_STAGE_EVALUATION.md` |
| I-07 | Complete | `benchmark/search-quality-gold-v1.json`, `docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`, benchmark harness群 |

MigrationはI-07では追加しておらず、最新は`016_hybrid_search.sql`のままである。

---

## 3. Phase I完了条件の確認

Phase Iの完了条件は、

> 「文字列が一致するObject」だけでなく、「意味・価値観・テーマ等が近いObject」を実用精度で取得できる。

である。

正式goldでは次を確認した。

- exact name / alias lookup accuracy: **100%**
- Hybrid Object Search: MRR **1.000**, Recall@10 **100%**, nDCG@10 **1.000**
- Statement Semantic Search: MRR **1.000**, Recall@10 **100%**
- filter / current-history / temporal contract: **5 / 5 passed**
- Overall Similarity: MRR **0.833**, Recall@10 **100%**
- Facet Similarity: MRR **1.000**, Recall@10 **100%**
- Evidence Search: lexical/association・semanticともMRR / Recall@10 **1.000**

通常free-text検索はHybridを標準とし、Identity一致をSemantic resultへ埋没させない。

---

## 4. Backend / derived layer監査

100,000 Vector / 1024-dim正式fixtureでNumPy Float32 ExactをreferenceとしてQdrant HNSWを評価した。

```text
Qdrant server        1.19.2
m                    16
ef_construct         128
hnsw_ef              768
full_scan_threshold  10
```

正式fixtureではunfiltered / hard-filteredともExact top-10に対しRecall@10 100%を確認した。

I-03の30k benchmarkで採用した`hnsw_ef=256`は、I-07の100k評価を受けて`768`へ更新した。

Vector Indexは引き続きcanonical backupではなくDerived Search Indexであり、SQLiteのSearch Representation / Embedding cacheからfull rebuild可能とする。

---

## 5. Statement Embeddingの扱い

I-07の20 Object goldではStatement Embeddingあり / なしでObject-level Recall改善は観測されなかった。

これはPhase I失敗とは扱わない。

理由:

- Statement Search自体はRecall@10 100%を確認している。
- matched Statement / groundingを返すためStatement representationが必要である。
- 小規模synthetic goldではFacet / Object representationだけでも対象Objectが十分分離された。

したがってStatement Embeddingは標準representationとして維持し、**実データ・大規模scaleでの増分価値の再評価をN-06へ引き継ぐ。**

---

## 6. Rerankerの扱い

正式goldではBGE v2-m3 / zerank-2ともObject-level MRR 1.000だった。

- Balanced candidate: `BAAI/bge-reranker-v2-m3`
- Quality candidate: `zeroentropy/zerank-2-reranker`
- Phase I MVP mandatory reranker: **No**

Hybrid first-stageだけでObject Recall@10 100%を満たしたため、MCP read pathへRerankerを必須依存として持ち込まない。

---

## 7. Regression / quality gate

Phase I完了時に次を確認した。

```text
I-01〜I-07 focused + Qdrant dependency
  41 passed

通常環境 full suite
  273 passed / 3 skipped / 1 deselected

Qdrant dependency込み full suite
  280 passed / 1 deselected / 2 warnings

Ruff
  All checks passed

git diff --check
  errorなし
```

`deselected` 1件は既知のPackage Transfer regressionで、期待messageが`SHA-256 mismatch`、実際が`Package file size mismatch`になる既存問題である。I-07由来ではない。

Qdrant local-mode testの2 warningはpayload index / HNSW parameterがlocal in-process modeでは有効にならない既知warningであり、native Windows Qdrant serverによる100k benchmarkは別途完了している。

---

## 8. Phase Jへ固定して渡す検索契約

Phase Jでは原則として次を再設計しない。

```text
canonical store         SQLite
normal free-text        Hybrid
Embedding Space         Harrier OSS v1 0.6B / 1024 dim
Vector backend          local Qdrant
Qdrant hnsw_ef          768
Object result unit      1 Object = 1 result
normal version scope    current accepted
historical              explicit Version only
Similarity default      same Primary Class
Facet similarity        same Facet only / no silent fallback
Evidence Search         Object Searchと別capability
score semantics         relevance / similarity, not truth/confidence
fallback                no silent cloud/backend/provider fallback
```

MCP Adapterはこれらの意味契約を変更せずApplication / Retrieval Coreを呼ぶ。

---

## 9. Phase Jへ引き継ぐ実装Gap

Phase Iの検索Coreは完成しているが、MCP公開の前に次のApplication boundaryが必要である。

1. `HybridObjectSearch`をApplication read use caseとして公開する。
2. `ObjectSimilaritySearch`をApplication read use caseとして公開する。
3. Object / Version / Facet / Relation / Evidence取得を、MCPがStorageへ直接触れず利用できるApplication APIへ揃える。
4. current requestでも実際に返した`resolved_version_id`をResponseから識別可能にする。
5. provider / Vector backend dependencyをMCP Adapter内部で勝手に生成せず、Application compositionから注入する。
6. MCP専用SQL、MCP専用ranking、MCP専用fallbackを作らない。

これらはPhase Iの残タスクではなく、J-01以降の責務である。

---

## 10. Closure decision

Phase Iの残タスクは0件であり、追加修正を要求するPhase I blockerは存在しない。

**Phase IをCloseし、Phase J Readyとする。**

次Task:

```text
J-01 [P0] Retrieval CoreとMCP Adapterを分離する
```
