# SGOKB Design Index

Updated: 2026-10-31

This directory contains the current implementation-level design documents for Source Grounded Object Knowledge Base.

## Current architecture entry point

Start with:

1. [`SGOKB_CURRENT_ARCHITECTURE.md`](SGOKB_CURRENT_ARCHITECTURE.md) — current end-to-end architecture through Phase P.
2. [`../requirements/RAW_GROUNDING_REQUIREMENTS.md`](../requirements/RAW_GROUNDING_REQUIREMENTS.md) — current Raw-grounded exchange requirements.
3. [`../operations/OBJECT_STANDARD_WORKFLOW.md`](../operations/OBJECT_STANDARD_WORKFLOW.md) — operator-facing standard workflow.
4. [`../operations/OPERATIONAL_SAFETY_RECOVERY.md`](../operations/OPERATIONAL_SAFETY_RECOVERY.md) — safety / backup / recovery invariants.

Detailed contracts remain authoritative for their own domain.

## GUI / Application boundary

- [`P_GUI_APPLICATION_ARCHITECTURE.md`](P_GUI_APPLICATION_ARCHITECTURE.md) — PySide6 GUI over the shared Application/operator boundary.
- [`../reference/GUI_CLI_CAPABILITY_MATRIX.md`](../reference/GUI_CLI_CAPABILITY_MATRIX.md) — public operation coverage.
- [`../evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`](../evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md) — final GUI parity/regression acceptance.

The GUI does not own direct canonical SQLite/Repository writes and does not shell out to the CLI for canonical work.

## Source / Evidence / Raw-grounded exchange

Current primary exchange family is Package v2 / Result v2. Evidence remains selection/provenance lineage; claim-level external semantic authority is Package-member Raw Artifacts.

- [`SOURCE_INGESTION_PIPELINE.md`](SOURCE_INGESTION_PIPELINE.md)
- [`STANDARD_PIPELINE_BOUNDARY.md`](STANDARD_PIPELINE_BOUNDARY.md)
- [`OBJECT_EVIDENCE_RETRIEVAL.md`](OBJECT_EVIDENCE_RETRIEVAL.md)
- [`EVIDENCE_SELECTION_BUDGET.md`](EVIDENCE_SELECTION_BUDGET.md)
- [`OPERATOR_ASSOCIATION_CONTROLS.md`](OPERATOR_ASSOCIATION_CONTROLS.md)
- [`P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`](P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md)
- [`P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`](P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md)
- [`P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`](P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md)

Legacy v1 package design documents remain valid for explicit v1 compatibility but no longer describe the `2.0.0` default.

## Data model

- [`OBJECT_SCHEMA.md`](OBJECT_SCHEMA.md) — Object identity, Class registry, Relation skeleton.
- [`SEMANTIC_FACET_SCHEMA.md`](SEMANTIC_FACET_SCHEMA.md) — Facet / Statement / Attribute model.
- [`SOURCE_EVIDENCE_SCHEMA.md`](SOURCE_EVIDENCE_SCHEMA.md) — Source / Snapshot / Raw / Evidence / Provenance schema.
- [`VERSIONING_SCHEMA.md`](VERSIONING_SCHEMA.md) — accepted Knowledge Version lifecycle and immutability.
- [`OBJECT_RESULT_JSON_SCHEMA.md`](OBJECT_RESULT_JSON_SCHEMA.md) — legacy/current structured-result context; Phase P v2 contract is governed by P-RAW documents.

## Runtime / health

- [`P_RUNTIME_03_RUNTIME_HEALTH_STATUS_CONTRACT.md`](P_RUNTIME_03_RUNTIME_HEALTH_STATUS_CONTRACT.md) — shared CLI/GUI `system.status.runtime_health` contract.
- [`P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md`](P_RUNTIME_04_CRASH_RECOVERY_REMEDIATION.md) — accepted repeating-trigger recovery design.
- [`P_RUNTIME_05_GUI_RUNTIME_DASHBOARD.md`](P_RUNTIME_05_GUI_RUNTIME_DASHBOARD.md) — structured GUI Runtime Dashboard.
- [`P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_ACCEPTANCE.md`](P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_ACCEPTANCE.md) — failure/recovery acceptance design.

Windows authority is native `qdrant.exe` + Windows Task Scheduler. Qdrant lifecycle remains external to SGOKB.

## Retrieval / Vector

Current Object representation family is `object_overview / facet / statement`; Evidence Search uses `evidence`. Legacy `object_overall` is not active.

- [`SEARCH_REPRESENTATION_SCHEMA.md`](SEARCH_REPRESENTATION_SCHEMA.md)
- [`EMBEDDING_PROVIDER_MODEL_EVALUATION.md`](EMBEDDING_PROVIDER_MODEL_EVALUATION.md)
- [`VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`](VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md)
- [`HYBRID_SEARCH_OBJECT_AGGREGATION.md`](HYBRID_SEARCH_OBJECT_AGGREGATION.md)
- [`OBJECT_SIMILARITY_SEARCH.md`](OBJECT_SIMILARITY_SEARCH.md)
- [`RERANKER_SECOND_STAGE_EVALUATION.md`](RERANKER_SECOND_STAGE_EVALUATION.md)
- [`SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`](SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md)

Accepted embedding baseline: `microsoft/harrier-oss-v1-0.6b`, revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, 1024 dimensions. Qdrant is the standard Vector backend. Rerankers remain optional.

## Rendering / derived views

- [`MARKDOWN_RENDERER.md`](MARKDOWN_RENDERER.md)
- [`DIFF_REVIEW.md`](DIFF_REVIEW.md)

Rendered Markdown and diff views are derived representations, not canonical Knowledge.

## Access / integration contracts

- CLI: [`../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`](../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- MCP read tools: [`../decisions/J02_MCP_READ_TOOL_CONTRACT.md`](../decisions/J02_MCP_READ_TOOL_CONTRACT.md)
- Context Builder: [`../decisions/J04_CONTEXT_BUILDER_CONTRACT.md`](../decisions/J04_CONTEXT_BUILDER_CONTRACT.md)
- SGOKB -> UPDS: [`../requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`](../requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md)

MCP remains read-only. External consumers use stable `object_id` and explicit immutable Version identity where reproducibility is required.

## Historical / research design warning

Historical Prototype and Grounded Generation research files remain for reproducibility. They do not override the current architecture, Phase P Raw-grounding contract, GUI boundary or native-Windows runtime authority.

Use [`../archive/`](../archive/) for archived Prototype material.
