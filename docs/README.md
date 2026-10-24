# SGOKB Documentation

`docs/` はSource Grounded Object Knowledge Base（SGOKB）の要件・Decision・設計・評価・運用・計画・歴史資料を用途別に管理します。

## Current status

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 README update = Complete
O-04 main integration = Complete
Next = O-02 Current design documentation
```

Phase Nのformal closure run `20261025T014024+0900` はC01-C07 PASSとなり、独立ChatGPT reviewで受理済みです。旧N-07 `47 PASS / 3 FAIL`はhistorical evidenceとして保持され、N07-R01 Composite backup / restore remediationの後続PASSでclosureしています。

現在のPhase O状態は [`planning/phases/O/PHASE_O_STATUS.md`](planning/phases/O/PHASE_O_STATUS.md) を参照してください。

## Start here

システム全体を把握する場合は、次の順で読むことを推奨します。

1. [`../README.md`](../README.md) — SGOKB概要、Architecture、標準workflow、MCP利用例
2. [`requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md) — SGOKBの目的・非目的
3. [`requirements/OBJECT_REQUIREMENTS.md`](requirements/OBJECT_REQUIREMENTS.md) — Object identity / lifecycle
4. [`requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`](requirements/SOURCE_EVIDENCE_REQUIREMENTS.md) — Source / Evidence / Provenance
5. [`requirements/SEARCH_REQUIREMENTS.md`](requirements/SEARCH_REQUIREMENTS.md) — Retrieval / Similarity
6. [`operations/OBJECT_STANDARD_WORKFLOW.md`](operations/OBJECT_STANDARD_WORKFLOW.md) — 1 Object標準運用
7. [`planning/README.md`](planning/README.md) — current planning / task state

## Documentation map

### [`requirements/`](requirements/)

現在有効な要件定義。

主な内容:

- SGOKBの目的・責務
- World / Object KnowledgeとUPDS Personal Inferenceの境界
- Object / Class / Facet / Relation
- Source / Evidence / Provenance
- Object Result
- Search / Retrieval / Similarity
- Human / Automation / External Egress boundary
- local-first / integrity / backup / restore / security / performance

### [`decisions/`](decisions/)

Architecture Decision、Design Freeze、public contract、運用上の固定方針。

特にoperator / client surface:

- [`M01_OBJECT_CENTERED_CLI_CONTRACT.md`](decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- [`J02_MCP_READ_TOOL_CONTRACT.md`](decisions/J02_MCP_READ_TOOL_CONTRACT.md)
- [`J04_CONTEXT_BUILDER_CONTRACT.md`](decisions/J04_CONTEXT_BUILDER_CONTRACT.md)

### [`design/`](design/)

確定した実装設計。

主な領域:

- Object / Facet / Version data model
- Source / Evidence pipeline
- Object Result JSON schema
- Search Representation / Embedding / Vector Index
- Hybrid Search / Similarity
- Package / Result exchange
- Rendering

O-02では、これらの現行設計をArchitecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundaryと運用要件の観点から再整理します。

### [`evaluation/`](evaluation/)

試験結果、benchmark、formal acceptance、failure analysis。

Phase N最終authority:

- [`PHASE_N_CLOSURE_AUDIT.md`](evaluation/PHASE_N_CLOSURE_AUDIT.md)
- [`N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`](evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md)
- [`N06_RETRIEVAL_VECTOR_QUALITY.md`](evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md)
- [`N05D04R2_R2_10_CLOSURE_AUDIT.md`](evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md)
- [`N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`](evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md)

Historical FAIL / BLOCKED evidenceは削除せず、current authorityと区別して保持します。

### [`operations/`](operations/)

実運用手順。

- [`OBJECT_STANDARD_WORKFLOW.md`](operations/OBJECT_STANDARD_WORKFLOW.md) — Object登録 → Evidence → Package → ChatGPT → Result → Import → Search / MCP

### [`planning/`](planning/)

Project / Phase / Taskの現在状態、handoff、実行計画。

主要入口:

- [`planning/README.md`](planning/README.md) — planning index
- [`planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md) — 全体task master
- [`planning/phases/O/PHASE_O_STATUS.md`](planning/phases/O/PHASE_O_STATUS.md) — current Phase O state
- [`planning/phases/N/PHASE_N_CLOSURE_AUDIT.md`](planning/phases/N/PHASE_N_CLOSURE_AUDIT.md) — Phase N closure contract / final state
- [`planning/phases/N/PHASE_N_PREPARATION.md`](planning/phases/N/PHASE_N_PREPARATION.md) — Phase N authority history

### [`reference/`](reference/)

外部分類体系調査、inventory、gold cases、Embedding / Vector技術調査など、設計判断の入力資料。

### [`archive/`](archive/)

旧Prototypeや名称変更等の歴史資料。

Archiveはcurrent specificationの正本として使用しません。

- [`archive/prototype-0.2/`](archive/prototype-0.2/) — 旧Fragment / Final Document中心Prototype
- [`archive/rename-2026-10/`](archive/rename-2026-10/) — 名称変更履歴

## Current architecture boundary

現行SGOKBは概念的に次の境界を持ちます。

```text
Source / Raw / Evidence
        ↓
Evidence Retrieval / Package
        ↓
Explicit External Export
        ↓
ChatGPT manual semantic integration
        ↓
Structured Object Result
        ↓
Validation / Review / Explicit Import
        ↓
Versioned Object Knowledge
        ↓
Lexical / Semantic / Hybrid / Similarity / Relation
        ↓
CLI / read-only MCP
```

- Raw / Evidence / accepted Knowledgeはcanonical保全対象。
- Search Representation / Embedding / Vector Index / Markdownはderived。
- ChatGPT APIはstandard Knowledge generationの成立条件ではない。
- MCP MVPはread-only。
- Personal InferenceはUPDSの責務。

## Placement rules

新規文書は内容に応じて配置します。

```text
requirement       -> docs/requirements/
architecture ADR -> docs/decisions/
design            -> docs/design/
test / research   -> docs/evaluation/
operation         -> docs/operations/
plan / handoff    -> docs/planning/
reference         -> docs/reference/
historical        -> docs/archive/
```

Planning文書は`docs/planning/`直下へ増やさず、原則として`project/`または`phases/<Phase>/...`へ配置します。
