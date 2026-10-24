# SGOKB Documentation

`docs/` はSource Grounded Object Knowledge Base（SGOKB）の要件・Decision・設計・評価・運用・計画・歴史資料を用途別に管理します。

## Current status

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Active
O-01 README update = Complete
O-02 Current design documentation = Complete
O-03 Prototype Archived / Legacy labels = Complete
O-04 main integration = Complete
Next = O-05 Branch cleanup
```

Phase Nのformal closure run `20261025T014024+0900` はC01-C07 PASSとなり、独立ChatGPT reviewで受理済みです。旧N-07 `47 PASS / 3 FAIL`はhistorical evidenceとして保持され、N07-R01 Composite backup / restore remediationの後続PASSでclosureしています。

現在のPhase O状態は [`planning/phases/O/PHASE_O_STATUS.md`](planning/phases/O/PHASE_O_STATUS.md) を参照してください。

## Start here

システム全体を把握する場合は、次の順で読むことを推奨します。

1. [`../README.md`](../README.md) — SGOKB概要、標準workflow、MCP利用例
2. [`design/SGOKB_CURRENT_ARCHITECTURE.md`](design/SGOKB_CURRENT_ARCHITECTURE.md) — current end-to-end Architecture / Data Model / Retrieval / Exchange / MCP / UPDS Boundary
3. [`operations/OPERATIONAL_SAFETY_RECOVERY.md`](operations/OPERATIONAL_SAFETY_RECOVERY.md) — Offline / Backup / Restore / Retention / Security / External Egress / Failure Recovery / Benchmark条件
4. [`design/README.md`](design/README.md) — current detailed design map
5. [`operations/OBJECT_STANDARD_WORKFLOW.md`](operations/OBJECT_STANDARD_WORKFLOW.md) — 1 Object標準運用
6. [`planning/README.md`](planning/README.md) — current planning / task state

要件から確認する場合:

- [`requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md)
- [`requirements/OBJECT_REQUIREMENTS.md`](requirements/OBJECT_REQUIREMENTS.md)
- [`requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`](requirements/SOURCE_EVIDENCE_REQUIREMENTS.md)
- [`requirements/SEARCH_REQUIREMENTS.md`](requirements/SEARCH_REQUIREMENTS.md)
- [`requirements/NON_FUNCTIONAL_REQUIREMENTS.md`](requirements/NON_FUNCTIONAL_REQUIREMENTS.md)

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

主要surface:

- [`M01_OBJECT_CENTERED_CLI_CONTRACT.md`](decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- [`J02_MCP_READ_TOOL_CONTRACT.md`](decisions/J02_MCP_READ_TOOL_CONTRACT.md)
- [`J04_CONTEXT_BUILDER_CONTRACT.md`](decisions/J04_CONTEXT_BUILDER_CONTRACT.md)

### [`design/`](design/)

確定した実装設計。

Current entry points:

- [`design/SGOKB_CURRENT_ARCHITECTURE.md`](design/SGOKB_CURRENT_ARCHITECTURE.md) — O-02 current integrated architecture
- [`design/README.md`](design/README.md) — detailed design index / authority map

主要領域:

- Object / Facet / Version data model
- Source / Evidence pipeline
- Object Result / Package exchange
- Search Representation / Embedding / Vector Index
- Hybrid Search / Similarity
- Rendering

Post-R2 current Object semantic representationは`object_overview / facet / statement`であり、legacy `object_overall`はactive retrieval kindではありません。

### [`operations/`](operations/)

実運用手順・運用安全設計。

- [`operations/OBJECT_STANDARD_WORKFLOW.md`](operations/OBJECT_STANDARD_WORKFLOW.md) — Object登録 → Evidence → Package → ChatGPT → Result → Import → Search / MCP
- [`operations/OPERATIONAL_SAFETY_RECOVERY.md`](operations/OPERATIONAL_SAFETY_RECOVERY.md) — Offline / Backup / Restore / Retention / Security / External Egress / Failure Recovery / Benchmark

### [`evaluation/`](evaluation/)

試験結果、benchmark、formal acceptance、failure analysis。

Phase N最終authority:

- [`PHASE_N_CLOSURE_AUDIT.md`](evaluation/PHASE_N_CLOSURE_AUDIT.md)
- [`N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`](evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md)
- [`N06_RETRIEVAL_VECTOR_QUALITY.md`](evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md)
- [`N05D04R2_R2_10_CLOSURE_AUDIT.md`](evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md)
- [`N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`](evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md)

Historical FAIL / BLOCKED evidenceは削除せず、current authorityと区別して保持します。

### [`planning/`](planning/)

Project / Phase / Taskの現在状態、handoff、実行計画。

主要入口:

- [`planning/README.md`](planning/README.md)
- [`planning/phases/O/PHASE_O_STATUS.md`](planning/phases/O/PHASE_O_STATUS.md)
- [`planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- [`planning/phases/N/PHASE_N_CLOSURE_AUDIT.md`](planning/phases/N/PHASE_N_CLOSURE_AUDIT.md)

Phase Oの実行中は`planning/phases/O/PHASE_O_STATUS.md`をcurrent Phase O status authorityとする。project-wide task masterの古いPhase O checklist記述と状態が異なる場合、このstatus文書のcurrent stateを優先する。

### [`reference/`](reference/)

外部分類体系調査、inventory、gold cases、Embedding / Vector技術調査など、設計判断の入力資料。

### [`archive/`](archive/)

旧Prototypeや名称変更等の歴史資料。

Archiveはcurrent specificationの正本として使用しません。

- [`archive/prototype-0.2/`](archive/prototype-0.2/) — O-03でArchived / Legacy stateを明示済み
- [`archive/rename-2026-10/`](archive/rename-2026-10/)

## Current architecture boundary

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
- complete canonical backupにはSQLiteだけでなくRaw / accepted Result provenanceを含むComposite generationを使用する。

## Placement rules

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
