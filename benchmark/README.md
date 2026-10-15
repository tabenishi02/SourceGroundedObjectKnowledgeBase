# SGOKB Benchmark

このdirectoryには、**現行canonical SGOKBのSearch / Similarity / Vector品質評価に使用するbenchmark資産だけを置く**。

## Current benchmark

Phase Iの現行Search評価正本は`search-quality-gold-v1.json`。

外部Web内容に依存しないfrozen synthetic canonical Knowledgeを使用し、次を評価する。

- Object Search
- Statement / Facet retrieval
- Similarity Search
- Evidence Search
- ANN backend
- Reranker regression

実行例:

```powershell
python scripts/run_search_quality_gold.py --local-files-only
python scripts/run_vector_backend_benchmark.py --count 100000 --hnsw-ef 768
python scripts/run_search_gold_reranker_benchmark.py
```

設計・結果の正本:

- [`docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`](../docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md)
- [`docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`](../docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md)
- [`docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`](../docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md)
- [`docs/design/RERANKER_SECOND_STAGE_EVALUATION.md`](../docs/design/RERANKER_SECOND_STAGE_EVALUATION.md)

## Retired Prototype benchmark

旧Fragment / Final Document / local generative LLM比較benchmarkはPhase L / L-04で退役した。

旧manifest、example labels、evaluation/preflight scripts、runtime SQLite benchmark DBはactive benchmark資産として保持しない。

歴史的な結果・判断根拠は`docs/archive/prototype-0.2/`を参照する。必要な旧実装はGit historyから確認する。

退役方針の正本:

- [`docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md`](../docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md)

## Sample Raw

`sample/`のWeb Capture corpusは旧benchmark DBとは別資産であり、Extractor / ingestion regression用として保持する。

benchmark DBのcleanupを理由に`sample/**/*.webcapture.zip`を削除してはならない。
