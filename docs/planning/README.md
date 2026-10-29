# Planning documents

`docs/planning/` は、Source Grounded Object Knowledge Base（SGOKB）の進行計画、Phase準備/完了監査、Task一覧、実行handoffを管理する領域です。

Planning文書はPhase / Task単位で整理し、`docs/planning/`直下には原則としてこのIndexだけを置きます。

## Current phase

Phase O — Documentation / Release / Git cleanup は **Complete** です。

2026-10-28のHappy-Path Operational Acceptanceで **FULL SGOKB PASS** を確認し、current formal releaseは `v1.1.0` です。

現在の開発Phaseは **Phase P — GUI / RAW Grounding / Runtime Modernization** です。

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Complete
Happy-path operational acceptance = Complete / FULL SGOKB PASS
Current formal release = v1.1.0
Phase P = In Progress
P-GUI-01 = Complete / Accepted
P-GUI-02 = Complete / Accepted
P-GUI-03 = Complete / Accepted
P-GUI-03R = Complete / Accepted
P-GUI-04 = Complete / Accepted
P-GUI-05 = Complete / Accepted
P-GUI-06 = Complete / Accepted
P-GUI-07 = Complete / Accepted
P-RAW-01 = Complete / Accepted
Next = P-RAW-02 Evidence -> Raw Artifact provenance resolution contract
```

Phase PのWorkstream優先順位:

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

## Current authority

### Phase P planning

- Phase P plan: [`phases/P/PHASE_P_MODERNIZATION_PLAN.md`](phases/P/PHASE_P_MODERNIZATION_PLAN.md)
- Phase P tasks: [`phases/P/PHASE_P_TASKS.md`](phases/P/PHASE_P_TASKS.md)
- Phase P current status: [`phases/P/PHASE_P_STATUS.md`](phases/P/PHASE_P_STATUS.md)
- P-GUI-03R task amendment: [`phases/P/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](phases/P/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)
- Project task amendment: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md)

### P-GUI-01 accepted authority

- GUI requirements: [`../requirements/GUI_REQUIREMENTS.md`](../requirements/GUI_REQUIREMENTS.md)
- GUI compatibility / safety decision: [`../decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`](../decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md)
- CLI ↔ GUI capability matrix: [`../reference/GUI_CLI_CAPABILITY_MATRIX.md`](../reference/GUI_CLI_CAPABILITY_MATRIX.md)

### P-GUI-02 accepted authority

- Architecture / packaging / license review: [`../evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`](../evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md)
- Decision: [`../decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`](../decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md)
- Application architecture: [`../design/P_GUI_APPLICATION_ARCHITECTURE.md`](../design/P_GUI_APPLICATION_ARCHITECTURE.md)
- Distribution / license checklist: [`../operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`](../operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md)

### P-GUI-03 / P-GUI-03R accepted authority

- Application boundary audit: [`../evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`](../evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md)
- 67-operation boundary matrix: [`../reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`](../reference/GUI_APPLICATION_BOUNDARY_MATRIX.md)
- Transport-neutral Decision: [`../decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`](../decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md)
- Refactor plan: [`../design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`](../design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md)
- P-GUI-03R implementation result: [`../evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](../evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)
- R9 final acceptance: [`../evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`](../evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md)

### P-GUI-04 accepted authority

- Implementation / final acceptance: [`../evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md`](../evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md)

### P-GUI-05 accepted authority

- Final implementation record: [`../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`](../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md)
- Final automated verification: [`../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md`](../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md)
- Final interactive acceptance: [`../evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md)

### P-GUI-06 accepted authority

- Final implementation: [`../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`](../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md)
- Final automated verification — Attempt 09: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md)
- Final interactive acceptance: [`../evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md)
- Search mode / Semantic runtime coupling remediation: [`../evaluation/P_GUI_06_SEMANTIC_RUNTIME_MODE_COUPLING_REMEDIATION.md`](../evaluation/P_GUI_06_SEMANTIC_RUNTIME_MODE_COUPLING_REMEDIATION.md)
- From/To removal: [`../evaluation/P_GUI_06_FROM_TO_FILTER_REMOVAL.md`](../evaluation/P_GUI_06_FROM_TO_FILTER_REMOVAL.md)

P-GUI-06 final automated evidence:

```text
focused regression = 29 / 29 PASS
Ruff               = PASS
full regression    = 818 / 818 PASS
known local-Qdrant warnings = 2
```

```text
P-GUI-06 = Complete / Accepted
```

### P-GUI-07 accepted authority

- Design: [`../design/P_GUI_OPERATION_SAFETY_AUDIT_UX.md`](../design/P_GUI_OPERATION_SAFETY_AUDIT_UX.md)
- Final implementation: [`../evaluation/P_GUI_07_PROGRESS_ERROR_SAFETY_AUDIT_UX_IMPLEMENTATION.md`](../evaluation/P_GUI_07_PROGRESS_ERROR_SAFETY_AUDIT_UX_IMPLEMENTATION.md)
- Automated verification — Attempt 01: [`../evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`](../evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md)
- Final interactive acceptance: [`../evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md)

Final automated verification:

```text
focused GUI gate = 34 / 34 PASS
Ruff             = PASS
full regression  = 823 / 823 PASS
warnings         = 2 known local-Qdrant warnings
```

Final interactive smoke completed with no problem reported in the exercised scope.

```text
P-GUI-07 = Complete / Accepted
```

### P-RAW-01 accepted authority

- Impact survey: [`../evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md`](../evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md)

P-RAW-01 confirms that the Raw Grounding redesign primarily affects the external exchange / grounding boundary.

Breaking v1 assumptions:

```text
Evidence Markdown as authoritative external semantic payload
included_evidence_ids as the complete grounding membership authority
Evidence-ID-only analysis instructions
Evidence-ID-only Result grounding
Evidence-only Package membership validation
```

Migration-required areas:

```text
Evidence -> Raw deterministic provenance resolution
Raw membership / Package audit trace
budget / preflight / egress coverage
review grounding presentation
import grounding persistence / accepted provenance
v1/v2 receive / validation routing
tests / benchmark fixtures / operations documentation
```

Compatibility targets:

```text
Evidence retrieval / human selection
Source / Snapshot / Raw canonical storage
Object / Registry / Association semantics
core Knowledge semantic fields
Version lifecycle
semantic diff core
Search / Similarity / derived indexing
```

The survey explicitly requires versioned v1/v2 semantics: legacy Evidence-grounded artifacts must not be silently interpreted as Raw-grounded artifacts.

P-RAW-01 does not choose the physical DB migration or final Package/Result v2 JSON shape; those decisions remain in P-RAW-02..05.

```text
P-RAW-01 = Complete / Accepted
```

### Current released system

Phase P remains in development. Released `v1.1.0` semantics remain governed by current architecture, decision, operations and release documents.

P-GUI-01 through P-GUI-07 and P-RAW-01 are accepted development baselines.

## Phase P GUI architecture

```text
Framework             = PySide6 / Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation, created in worker thread
Backend concurrency   = serialized per Workspace initially
Semantic runtime      = native stack preloaded on main thread; model lazy-cached in backend
Operation UX          = session Operation Center + safety metadata
Windows deployment    = pyside6-deploy / Nuitka
Deployment mode       = standalone directory / portable ZIP
Qt linking            = dynamic / separate shared libraries
```

Application boundary:

```text
CLI parser / GUI worker
        ↓
OperationRequest
        ↓
OperatorSession
        ↓
Application facades
        ↓
Repository / Retrieval / Exchange
```

## Workstream B — RAW Grounding

Evidence remains the retrieval / selection unit, while External AI semantic material will move from reconstructed Evidence Markdown to Raw Artifacts traced through provenance.

P-RAW-01 impact survey is accepted. The next task is P-RAW-02, which must define deterministic Evidence -> Raw resolution without yet implementing Package v2.

`P-GUI-08` remains blocked until completion of `P-RAW-01..P-RAW-06`.

## Workstream C — Runtime

Windows login should make Qdrant automatically available. Qdrant remains an independent shared runtime rather than a GUI-owned process.

`P-GUI-09` depends on `P-RUNTIME-03`, so that GUI task remains unavailable until the runtime workstream advances.

## Phase P task families

```text
P-GUI-01 .. P-GUI-10
P-RAW-01 .. P-RAW-06
P-RUNTIME-01 .. P-RUNTIME-06
P-CLOSE-01
```

## Next

```text
P-RAW-02 — Evidence -> Raw Artifact provenance resolution contract
```
