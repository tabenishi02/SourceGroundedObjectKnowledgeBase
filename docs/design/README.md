# SGOKB Design Index

Updated: 2026-10-25

This directory contains current implementation-level design documents for Source Grounded Object Knowledge Base.

## Current architecture entry point

Start with:

1. [`SGOKB_CURRENT_ARCHITECTURE.md`](SGOKB_CURRENT_ARCHITECTURE.md) — current end-to-end architecture and authority map.
2. [`../operations/OPERATIONAL_SAFETY_RECOVERY.md`](../operations/OPERATIONAL_SAFETY_RECOVERY.md) — Offline / Backup / Restore / Retention / Security / External Egress / Failure Recovery / benchmark conditions.
3. [`../operations/OBJECT_STANDARD_WORKFLOW.md`](../operations/OBJECT_STANDARD_WORKFLOW.md) — operator-facing 1 Object workflow.

The integrated architecture documents summarize accepted contracts; detailed files below remain normative for their own domain.

## Data model

- [`OBJECT_SCHEMA.md`](OBJECT_SCHEMA.md) — Object identity, Class registry, Relation skeleton.
- [`SEMANTIC_FACET_SCHEMA.md`](SEMANTIC_FACET_SCHEMA.md) — Facet / Statement / Attribute model.
- [`SOURCE_EVIDENCE_SCHEMA.md`](SOURCE_EVIDENCE_SCHEMA.md) — Source / Snapshot / Raw / Evidence / Provenance schema.
- [`VERSIONING_SCHEMA.md`](VERSIONING_SCHEMA.md) — accepted Knowledge Version lifecycle and immutability.
- [`OBJECT_RESULT_JSON_SCHEMA.md`](OBJECT_RESULT_JSON_SCHEMA.md) — structured external Result exchange contract.

## Source / Evidence / Exchange

- [`SOURCE_INGESTION_PIPELINE.md`](SOURCE_INGESTION_PIPELINE.md)
- [`STANDARD_PIPELINE_BOUNDARY.md`](STANDARD_PIPELINE_BOUNDARY.md)
- [`OBJECT_EVIDENCE_RETRIEVAL.md`](OBJECT_EVIDENCE_RETRIEVAL.md)
- [`EVIDENCE_SELECTION_BUDGET.md`](EVIDENCE_SELECTION_BUDGET.md)
- [`OPERATOR_ASSOCIATION_CONTROLS.md`](OPERATOR_ASSOCIATION_CONTROLS.md)
- [`OBJECT_EVIDENCE_PACKAGE_FORMAT.md`](OBJECT_EVIDENCE_PACKAGE_FORMAT.md)
- [`OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`](OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md)
- [`OBJECT_ANALYSIS_INSTRUCTIONS.md`](OBJECT_ANALYSIS_INSTRUCTIONS.md)

## Retrieval / Vector

Current post-R2 representation family is `object_overview / facet / statement` for Object Knowledge plus `evidence` for Evidence Search. Legacy `object_overall` is not an active retrieval kind.

- [`SEARCH_REPRESENTATION_SCHEMA.md`](SEARCH_REPRESENTATION_SCHEMA.md)
- [`EMBEDDING_PROVIDER_MODEL_EVALUATION.md`](EMBEDDING_PROVIDER_MODEL_EVALUATION.md)
- [`VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`](VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md)
- [`HYBRID_SEARCH_OBJECT_AGGREGATION.md`](HYBRID_SEARCH_OBJECT_AGGREGATION.md)
- [`OBJECT_SIMILARITY_SEARCH.md`](OBJECT_SIMILARITY_SEARCH.md)
- [`RERANKER_SECOND_STAGE_EVALUATION.md`](RERANKER_SECOND_STAGE_EVALUATION.md)
- [`SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`](SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md)

Current accepted Embedding baseline is `microsoft/harrier-oss-v1-0.6b`, revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, 1024 dimensions. Qdrant is the current standard Vector backend. Rerankers remain optional.

## Rendering / human-readable derived views

- [`MARKDOWN_RENDERER.md`](MARKDOWN_RENDERER.md)
- [`DIFF_REVIEW.md`](DIFF_REVIEW.md)

Rendered Markdown and diff views are derived representations, not canonical Knowledge.

## Access / integration contracts outside this directory

- CLI: [`../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`](../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- MCP read tools: [`../decisions/J02_MCP_READ_TOOL_CONTRACT.md`](../decisions/J02_MCP_READ_TOOL_CONTRACT.md)
- Context Builder: [`../decisions/J04_CONTEXT_BUILDER_CONTRACT.md`](../decisions/J04_CONTEXT_BUILDER_CONTRACT.md)
- SGOKB → UPDS: [`../requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`](../requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md)

MCP MVP is read-only. UPDS consumes stable `object_id` and, where reproducibility is needed, the resolved immutable Knowledge Version. UPDS does not use SGOKB SQLite tables as its integration contract.

## Historical / research design warning

Some files in `docs/design/` were produced during Phase N Grounded Generation research. These are preserved for reproducibility but do **not** override the current SGOKB core responsibility boundary.

In particular, consumer-side prose generation / verifier / presentation pipeline work is not part of the current SGOKB core acceptance boundary. Use the current architecture and N-04 responsibility decisions to determine ownership before treating such files as active core design.

For historical Prototype material, use [`../archive/`](../archive/). Archive content is not current specification.
