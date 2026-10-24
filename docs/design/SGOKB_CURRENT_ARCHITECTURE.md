# SGOKB Current System Architecture

Updated: 2026-10-25

- Status: **Current / Accepted**
- Phase: `Phase O — Documentation / Release / Git cleanup`
- Task: `O-02 [P0] 現行設計書を更新する`
- Scope: current SGOKB core architecture after Phase N acceptance
- Historical Prototype / Grounded Generation research documents do not override this document.

## 1. Purpose and authority

Source Grounded Object Knowledge Base（SGOKB）は、ユーザーが選択・収集したWeb資料を追跡可能なSource / Evidenceとして保存し、Character・Work・Concept等のWorld / Object Knowledgeへ変換して長期保存し、検索・比較・MCP・外部AIから再利用するlocal-first Knowledge Baseである。

本書は、Phase A〜Nで確定した個別要件・Decision・実装設計を**現在の全体Architectureとして統合して読むための正本**である。

詳細なschemaやalgorithmは既存の個別contractを正本とし、本書はそれらを置き換えない。矛盾がある場合は次の優先順で解決する。

```text
current accepted requirement / decision / design contract
  > Phase N accepted implementation / evaluation evidence
  > this integrated architecture summary
  > historical planning / failed experiment / Prototype archive
```

Phase N closureはC01-C07 PASSとして受理済みであり、本書はそのaccepted system boundaryを前提とする。

---

## 2. System boundary

SGOKBの責務は次である。

- Source / Snapshot / Raw Artifactを保存する。
- Normalized contentとEvidence / Provenanceを管理する。
- stable Object IdentityとClass / Facet / Relation registryを管理する。
- Evidenceを選択し、外部意味統合用Packageを構築する。
- 外部AIが返したStructured Object Resultを検証・reviewし、明示Importによってaccepted Knowledge Versionへ昇格する。
- accepted KnowledgeからLexical / Semantic / Hybrid / Similarity / Relation / Evidence retrievalを提供する。
- CLIとread-only MCPを通じて人間・AI・UPDSへKnowledgeを提供する。
- backup / restore / integrity / derived rebuildを提供する。

SGOKB coreの責務ではないもの:

- Web全体の無差別Crawler。
- 特定LLM向け巨大Final DocumentをKnowledgeの正本にすること。
- Packageを外部AIへ無確認で自動送信すること。
- AI出力をvalidation / reviewなしでcanonical Knowledgeへ書き込むこと。
- ユーザーの嗜好・価値観・Preference Hypothesisを推論すること。
- Consumer側の自然言語presentation品質をSGOKB core acceptanceとすること。

---

## 3. End-to-end architecture

```text
Web / local capture
        │
        ▼
Capture / Source Import
        │
        ▼
Source ─ Snapshot ─ Raw Artifact
        │
        ▼
Normalize
        │
        ▼
Evidence + Provenance
        │
        ├─────────────────────────────────────────────┐
        │                                             │
        ▼                                             │
Object Registry / Association                         │
        │                                             │
        ▼                                             │
Evidence Retrieval / Selection                        │
        │                                             │
        ▼                                             │
Object Evidence Package                               │
        │                                             │
        │ explicit preflight + export                 │
        ▼                                             │
External ChatGPT / other capable AI                   │
(manual semantic integration)                         │
        │                                             │
        ▼                                             │
Structured Object Result (`result.json`)              │
        │                                             │
        ▼                                             │
Receive → Validate → Review → explicit Import         │
        │                                             │
        ▼                                             │
Accepted Object Knowledge Version                     │
        │                                             │
        ├──────────────┬──────────────┬───────────────┘
        │              │              │
        ▼              ▼              ▼
Lexical read     Search Representation   Markdown / view
                 + Embedding
                 + Vector Index
                        │
                        ▼
              Semantic / Hybrid / Similarity
                        │
                        ▼
               KnowledgeReadApplication
                        │
                 ┌──────┴──────┐
                 ▼             ▼
                CLI       read-only MCP
                               │
                               ▼
                    ChatGPT / Local LLM / UPDS
```

Canonical KnowledgeとDerived Searchを分離し、検索・MCP・renderingの障害がcanonical stateを破壊しない構造を維持する。

---

## 4. Layer responsibilities

### 4.1 Capture / Source layer

SourceはWeb URLやfile pathそのものではなくstable Source Identityを持つ。取得時点はSnapshotとして世代管理し、Raw ArtifactはEvidence再抽出・監査・再生成の原資料として保持する。

```text
Source
  └─ Snapshot
       └─ Raw Artifact
            └─ Normalized Run
                 └─ Evidence
```

SourceとObjectは多対多であり、associationは`candidate / confirmed / excluded`等の明示状態として扱う。EvidenceをObject Knowledgeへ直接埋め込んで原資料を失わせない。

Detailed authority:

- `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
- `docs/design/SOURCE_EVIDENCE_SCHEMA.md`
- `docs/design/SOURCE_INGESTION_PIPELINE.md`
- `docs/design/OBJECT_EVIDENCE_RETRIEVAL.md`

### 4.2 Object / Knowledge layer

ObjectはSource・Document・Versionから独立したstable identityを持つ。新規Object IDはUUID系のstable text identityであり、name変更・再分類・Knowledge更新で再発番しない。

主要論理構造:

```text
Object
  ├─ canonical name / alias
  ├─ Primary Class
  ├─ Additional Class
  ├─ current accepted Version pointer
  └─ Registry events

Accepted Knowledge Version
  ├─ Summary / Attribute
  ├─ Facet
  │    └─ Statement
  ├─ Relation
  └─ Evidence Link
```

accepted Knowledge Versionは論理immutableであり、修正は新Versionとして表現する。rollbackは履歴削除ではなくcurrent pointer / promotionの変更として扱う。

Detailed authority:

- `docs/requirements/OBJECT_REQUIREMENTS.md`
- `docs/requirements/OBJECT_TYPE_MODEL.md`
- `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
- `docs/design/OBJECT_SCHEMA.md`
- `docs/design/SEMANTIC_FACET_SCHEMA.md`
- `docs/design/VERSIONING_SCHEMA.md`

### 4.3 Evidence-grounded exchange layer

高度な意味統合はExternal Human-in-the-loopとして分離する。

```text
canonical Evidence
  ↓
Package build / stage
  ↓
preflight
  ↓
explicit export
  ↓
ChatGPT / external AI
  ↓
Structured Object Result
  ↓
receive / validate / review
  ↓
explicit import
```

Packageは外部AIへ送信するderived exchange artifactでありcanonical Knowledgeではない。Packageはtarget Object、base Version、Evidence membership、instructions / schema等へbindingされる。

Resultも受信した時点ではcanonical Knowledgeではない。schema / identity / Evidence membership / stale conditionを検証し、人間review境界を通した後、明示Importで新Knowledge Versionを作る。

Registry proposalはResult Importの副作用として自動applyしない。accept/rejectとapplyを別操作とする。

Detailed authority:

- `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
- `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md`
- `docs/design/OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`
- `docs/design/OBJECT_ANALYSIS_INSTRUCTIONS.md`
- `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`
- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`

### 4.4 Derived Search layer

Search Representation、Embedding、Vector Indexはcanonical Knowledgeから再構築できるderived stateである。

Current R2 representation family:

```text
object_overview
facet
statement
evidence
```

`object_overall`はlegacy v1 representationであり、current post-R2 retrievalへ参加しない。

Object Knowledge retrievalのactive semantic familyは`object_overview / facet / statement`である。Evidence Searchは別結果型として`evidence` representationを扱う。

Current Embedding Space baseline:

```text
Provider:         sentence-transformers
Model:            microsoft/harrier-oss-v1-0.6b
Revision:         f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Dimension:        1024
Normalization:    L2
CUDA dtype:       bfloat16
Persisted dtype:  float32
Fallback:         none
```

Vector backendのcurrent standardはQdrantである。Vector backendはcanonical Knowledge storeではない。

Detailed authority:

- `docs/requirements/SEARCH_REQUIREMENTS.md`
- `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
- `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
- `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`
- `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
- `docs/design/OBJECT_SIMILARITY_SEARCH.md`

### 4.5 Search semantics

Object Searchは用途を分離する。

```text
Identity lookup
Lexical Object Search
Semantic Object Search
Hybrid Object Search
Object / Facet Similarity
Relation traversal
Evidence Search
```

通常free-text Object Searchでは1 Object = 1 resultへbounded aggregationする。R2 semantic channelsはoverview / facet / statementを独立にcandidate generationし、Object単位へbounded aggregationした後にcross-channel fusionする。

Exact name / aliasはSemantic resultに埋没させない。Facet-specific SimilarityでFacetが存在しない場合、overallへsilent fallbackしない。

Current / historical Version scopeを混在させず、normal retrievalはcurrent accepted Knowledgeを既定scopeとする。

### 4.6 Application / CLI layer

operator-facing public CLIは`sgokb`へ統一する。

```text
sgokb source ...
sgokb object ...
sgokb association ...
sgokb evidence ...
sgokb registry ...
sgokb package ...
sgokb result ...
sgokb version ...
sgokb search ...
sgokb similar ...
sgokb render ...
sgokb mcp ...
sgokb system ...
```

raw SQLをoperator-facing public APIとしない。write operationはApplication / Repository contractを通す。

CLI machine-readable contractは`sgokb.cli/1.0`。Semantic runtime不足等は明示error/degradationとして扱い、cloudへsilent fallbackしない。

Authority: `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`。

### 4.7 MCP Knowledge Access layer

MCP MVPは**read-only**である。

```text
Repository / Retrieval Core
        ↓
KnowledgeReadApplication
        ↓
MCPReadAdapter
        ↓
MCP Server
        ↓
stdio
```

MCP transportからSQLite / Qdrantへ直接アクセスしない。current active read capabilityは次の8 Toolである。

```text
search_objects
find_similar_objects
get_object
get_objects
get_object_relations
get_object_evidence
search_evidence
build_context
```

`build_context`はLLM推論・要約生成を行わず、保存済みKnowledgeをpurpose profileと明示optionから決定論的に選別する。

Canonical write、Result Import、Registry mutation、Package exportはMCP read Toolの責務外である。

Detailed authority:

- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`
- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- Phase J MCP server / resource decisions

### 4.8 SGOKB / UPDS boundary

SGOKBはWorld / Object Knowledge Provider、UPDSはPersonal Inference Consumerである。

```text
SGOKB canonical Object Knowledge
        ↓
Retrieval / Application Core
        ↓
MCP read boundary
        ↓
UPDS
        ↓
Selection-related Semantic Observation
Pattern
Preference Hypothesis
```

Persistent integration identityはSGOKBのstable `object_id`を使用する。推論再現性が必要な場合、UPDSは実際に取得したimmutable `knowledge_version_id`を記録する。

禁止境界:

- UPDSがSGOKB SQLite schemaをdirect contractとして読むこと。
- UPDSがPersonal Preference推論をSGOKB canonical Knowledgeへsilent write-backすること。
- display nameやsearch rankingをObject identityとして保存すること。

Detailed authority:

- `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

---

## 5. Canonical / derived / transient classification

| Class | Examples | Loss handling |
|---|---|---|
| Canonical / authoritative | SQLite Object / Version / Registry / Source / Snapshot / Relation / Evidence Link, Raw Artifact | restore required |
| Provenance-bearing retained data | Evidence, Normalized Run, accepted original Result / audit record | preserve while referenced |
| Rebuildable derived | Search Representation, Embedding, Qdrant Vector Index, render output | rebuild |
| Transient / exchange | Package staging, temporary files, caches | cleanup by policy |

Evidenceは再抽出可能な場合でもaccepted Versionが`evidence_id`へgroundingしているため、参照中は単なるcacheとして扱わない。

---

## 6. Runtime composition

Core minimum:

```text
Python 3.10+
SQLite
local filesystem
sgokb CLI
```

Optional semantic composition:

```text
sentence-transformers / local Embedding provider
Qdrant
CUDA-capable GPU profile (Reference WorkstationではRTX 4090)
```

Optional MCP composition:

```text
MCP Python SDK
stdio MCP server
```

Core local read pathはInternet、ChatGPT、Google Drive、Qdrant、GPUを必須としない。Lexical readとcanonical Object readはSQLiteだけで成立する。

---

## 7. Failure isolation rules

以下の失敗をcanonical Knowledgeのrollback / delete理由にしない。

- Embedding生成失敗。
- Qdrant / Vector Index障害。
- FTS / derived rebuild失敗。
- Markdown render失敗。
- MCP server停止。
- Google Drive等の交換先停止。
- ChatGPT / external AI停止。

Semantic-only operationが必要runtimeを失った場合はexplicit unavailableとし、HybridがLexicalへdegradeする場合もwarningを返す。

---

## 8. Security / external boundary

default security postureはlocal-onlyである。

Package Exportは明示的External Egress operationとして扱い、preflightの`allow / review_required / blocked` boundaryを維持する。credential / token / secretは標準Packageへ含めない。

外部AIから返るResultはuntrusted inputであり、JSON内path / URL / stringをcommandやarbitrary filesystem operationとして実行しない。

MCPは初期releaseではlocal read-only surfaceであり、remote network exposureをdefaultにしない。

Operational details: `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`。

---

## 9. Acceptance baseline carried forward

Phase Nで次をformal acceptance済みとして扱う。

- Unit / Integration / real-data vertical slice。
- Knowledge Access boundary。
- R2 hierarchical multi-vector performance acceptance。
- Retrieval / Vector quality。
- Failure / Recovery。
- Composite canonical backup / alternate-root restore。
- Phase N closure C01-C07。

Historical failuresは証跡として保持するが、後続accepted remediationでclosureしたものをcurrent failureとして再解釈しない。

Phase N closure authority:

- `docs/evaluation/PHASE_N_CLOSURE_AUDIT.md`
- `benchmark/results/phase-n-closure-audit.json`

---

## 10. Current design document map

### Architecture / data model

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md` — 本書。
- `docs/design/OBJECT_SCHEMA.md`
- `docs/design/SEMANTIC_FACET_SCHEMA.md`
- `docs/design/SOURCE_EVIDENCE_SCHEMA.md`
- `docs/design/VERSIONING_SCHEMA.md`
- `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`

### Evidence / exchange

- `docs/design/SOURCE_INGESTION_PIPELINE.md`
- `docs/design/OBJECT_EVIDENCE_RETRIEVAL.md`
- `docs/design/EVIDENCE_SELECTION_BUDGET.md`
- `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md`
- `docs/design/OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`
- `docs/design/OBJECT_ANALYSIS_INSTRUCTIONS.md`

### Retrieval

- `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
- `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
- `docs/design/VECTOR_INDEX_ADAPTER_BACKEND_EVALUATION.md`
- `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
- `docs/design/OBJECT_SIMILARITY_SEARCH.md`

### Access / integration

- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`
- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

### Operations

- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`

---

## 11. Historical / non-current design warning

`docs/archive/`はhistorical materialでありcurrent specificationではない。

また、Phase N / N-04のGrounded Generation研究資産のうちconsumer-generation implementation / verifier / presentation pipelineはSGOKB core responsibilityから外れている。failure analysisやgold benchmarkはresearch evidenceとして保持するが、本書のcurrent core Architectureをoverrideしない。
