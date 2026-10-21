# SGOKB Benchmark

このdirectoryには、現行canonical SGOKBのSearch / Similarity / Vector品質評価資産、Phase N formal acceptance用machine-readable資産、および明示的にhistorical / experimentalとして保持する評価資産を置く。

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

N-04R-04は2026-10-22に3/3 Case PASSし、N-04はCompleteとなった。

AI Consumerの生成品質、Atomicity / Content-Type classifier、verifier、Grounded Generation certificationはcurrent N-04 formal Gateではない。

Decision:

- [`docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`](../docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md)
- [`docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`](../docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md)

## Current N-05 performance benchmark

N-05は1 Object local automatic segmentの性能をReference Workstationで評価する。

Current machine-readable assets:

```text
n05-performance-contract-v1.json
n05-performance-evidence-template-v1.json
tools/n05_evaluate_performance.py
```

Formal Gate:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

Formal sample policy:

```text
cold >= 3 / profile   diagnostic only
warm >= 20 / profile  formal
p95 = nearest-rank
formal warm terminal failure must not be discarded/replaced
```

N-05の計測対象はPackage buildからResult Validation / Import / derived incremental sync / RenderまでのSGOKB local automatic segment。Source探索、Capture network、人間待ち、external AI生成待ち、Drive/export、full Vector rebuildはformal 1 Object p95から除外する。

Current status:

```text
contract/evaluator    implemented
formal timing samples not measured
formal verdict        BLOCKED (Reference Workstation command execution access)
N-05                  Active / not Complete
```

`BLOCKED`はperformance failureではない。formal raw evidenceなしにPASS/FAILを推定してはならない。

Planning / evaluation:

- [`docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`](../docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md)
- [`docs/planning/phases/N/N05/execution/N05_REFERENCE_WORKSTATION_HANDOFF.md`](../docs/planning/phases/N/N05/execution/N05_REFERENCE_WORKSTATION_HANDOFF.md)
- [`docs/evaluation/N05_PERFORMANCE.md`](../docs/evaluation/N05_PERFORMANCE.md)

## N-04R-05 Grounded Generation disposition

Machine-readable disposition:

```text
n04r05-grounded-generation-asset-disposition-v1.json
```

Decision:

[`docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`](../docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md)

分類:

```text
MOVE_CONSUMER_SIDE
  Grounded Generation implementation / verifier / architecture

KEEP_EXPERIMENTAL
  failure-analysis evidence
  Frozen 47 / semantic research corpus
  G-25A corpus / VALID_FAIL_NO_SELECTION result

RETIRE
  old N-04 generation-quality harnesses
  old verifier / judge / classifier execution tooling

KEEP_CORE
  Grounded Generation chainから0件
```

### Historical / experimental N-04 assets

以下の資産はファイルとして保持するが、current N-04 formal harnessではない。

```text
n04-ai-use-cases-v1/v2/v3.json
n04-v2-formal-harness-v1.json
n04-v3-formal-harness-v1.json
n04g20-*.json
n04g23*.json
n04g25a-*.json/jsonl
results/n04g*.json
tools/n04g*.py
```

特に`n04g23a-atomicity-role-gold-v1.json`の47 Goldはresearch corpusとして保持するが、N-04 completion確認として再実行しない。

Retired toolingを「benchmark directoryに存在する」ことだけを理由にactive benchmarkとして実行してはならない。

## Retired Prototype benchmark

旧Fragment / Final Document / local generative LLM比較benchmarkはPhase L / L-04で退役した。

旧manifest、example labels、evaluation/preflight scripts、runtime SQLite benchmark DBはactive benchmark資産として保持しない。

歴史的な結果・判断根拠は`docs/archive/prototype-0.2/`を参照する。必要な旧実装はGit historyから確認する。

退役方針の正本:

- [`docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md`](../docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md)

## Sample Raw

`sample/`のWeb Capture corpusは旧benchmark DBとは別資産であり、Extractor / ingestion regression用として保持する。

benchmark DBのcleanupを理由に`sample/**/*.webcapture.zip`を削除してはならない。
