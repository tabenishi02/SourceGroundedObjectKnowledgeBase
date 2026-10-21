# SGOKB Benchmark

このdirectoryには、現行canonical SGOKBのSearch / Similarity / Vector品質評価資産と、Phase N formal acceptance用のmachine-readable資産を置く。

## Current Search benchmark

Phase I / N-06の現行Search評価正本は`search-quality-gold-v1.json`。

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

## Current N-04 acceptance harness

2026-10-22のResponsibility Boundary Reconstruction後、N-04のcurrent formal harnessはSGOKBのKnowledge Access Boundaryだけを評価する。

Current authority:

```text
n04-knowledge-access-cases-v1.json
n04-knowledge-access-formal-harness-v1.json
tools/n04r03_harness_preflight.py
tools/n04r04_evaluate_evidence.py
```

正式評価範囲:

```text
SGOKB → Retrieval / Similarity → Context Builder → MCP public read → Consumer boundary
```

AI Consumerの生成品質、Atomicity / Content-Type classifier、verifier、Grounded Generation certificationはcurrent N-04 formal Gateではない。

Decision:

- [`docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`](../docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md)
- [`docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`](../docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md)

`n04-ai-use-cases-v1/v2/v3.json`、`n04-v2-formal-harness-v1.json`、`n04-v3-formal-harness-v1.json`およびG-20〜G-25関連資産はhistorical research evidenceとして保持する。current N-04 Completion prerequisiteではない。

## Retired Prototype benchmark

旧Fragment / Final Document / local generative LLM比較benchmarkはPhase L / L-04で退役した。

旧manifest、example labels、evaluation/preflight scripts、runtime SQLite benchmark DBはactive benchmark資産として保持しない。

歴史的な結果・判断根拠は`docs/archive/prototype-0.2/`を参照する。必要な旧実装はGit historyから確認する。

退役方針の正本:

- [`docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md`](../docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md)

## Sample Raw

`sample/`のWeb Capture corpusは旧benchmark DBとは別資産であり、Extractor / ingestion regression用として保持する。

benchmark DBのcleanupを理由に`sample/**/*.webcapture.zip`を削除してはならない。
