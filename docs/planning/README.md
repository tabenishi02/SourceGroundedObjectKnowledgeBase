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
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
Next = repeat P-GUI-06 interactive smoke
```

Phase PのWorkstream優先順位は次で固定します。

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

### P-GUI-06 current authority

- Main implementation / interactive procedure: [`../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`](../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md)
- **Current automated verification**: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_07.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_07.md)
- **Current interactive remediation**: [`../evaluation/P_GUI_06_INTERACTIVE_ATTEMPT_07_FAILURE_AND_REMEDIATION.md`](../evaluation/P_GUI_06_INTERACTIVE_ATTEMPT_07_FAILURE_AND_REMEDIATION.md)
- Current range/runtime dependency remediation: [`../evaluation/P_GUI_06_RANGE_CONTRACT_SEMANTIC_RUNTIME_DEPENDENCY_REMEDIATION.md`](../evaluation/P_GUI_06_RANGE_CONTRACT_SEMANTIC_RUNTIME_DEPENDENCY_REMEDIATION.md)
- Historical Attempt 06: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md)
- Historical Attempt 05: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md)
- Prior range/runtime-state remediation: [`../evaluation/P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md`](../evaluation/P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md)
- Search selector / validity-range amendment: [`../evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`](../evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md)
- First validity-range false-negative remediation: [`../evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`](../evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md)
- Derivation Kind selector improvement: [`../evaluation/P_GUI_06_DERIVATION_KIND_SELECTOR_IMPROVEMENT.md`](../evaluation/P_GUI_06_DERIVATION_KIND_SELECTOR_IMPROVEMENT.md)

P-GUI-06 keeps all 14 assigned Search / Similarity / Registry / Version / Render operations wired.

Current From/To contract is:

```text
Registry exact/lexical identity
  -> canonical name/alias identity discovery
  -> From/To alone does not remove the result
  -> no current Version or Statement is required

Knowledge lexical Statement
  -> From/To temporal-overlap filter

Semantic Statement
  -> From/To temporal-overlap filter
```

Current local semantic dependency contract is:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

The operator environment is verified with PyTorch `2.6.0+cu124`, CUDA 12.4 available on RTX 4090, and `pip check` clean. After production GUI testing exposed a process-level Semantic-runtime crash, GUI startup now preloads PyTorch / Transformers / Sentence Transformers native imports on the Qt main thread before the backend QThread starts; the model remains lazy.

Current automated evidence from Attempt 07:

```text
focused P-GUI-03R / 04 / 05 / 06 regression = 42 / 42 PASS
Ruff                                           = All checks passed!
full regression                                = 831 / 831 PASS
known local-Qdrant warnings                    = 2
```

Attempt 07 adds production `KnowledgeReadApplication` + active-R2 coverage for unversioned Registry identity under From/To and verifies main-thread semantic native preload ordering. Attempt 06 remains historical because interactive testing afterward exposed those two additional defects.

Current status:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

### Current released system

Phase P remains in development. Released `v1.1.0` semantics remain governed by current architecture, decision, operations and release documents.

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 has passed the current automated gate and remains open for interactive re-smoke acceptance only. These tasks do not by themselves advance the formal release version.

## Phase P GUI decisions so far

### Compatibility

All 67 public CLI operations are mapped to GUI capability inventory. GUI compatibility means same use case / target identity / canonical effect / validation / safety / degradation / failure semantics, not replaying CLI strings.

### Technical architecture

```text
Framework            = PySide6
UI                    = Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation, created in worker thread
Backend concurrency   = serialized per Workspace initially
Semantic runtime      = native stack preloaded on main thread; model lazy-cached in backend
Windows deployment    = pyside6-deploy / Nuitka
Deployment mode       = standalone directory / portable ZIP
Qt linking            = dynamic / separate shared libraries
```

### Application boundary

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

P-GUI-04 established the queued QThread foundation. P-GUI-05 and P-GUI-06 reuse it without GUI direct SQL or a CLI-subprocess business path.

## Workstream B — RAW Grounding

Evidence remains the retrieval / selection unit, while External AI semantic material will move from reconstructed Evidence Markdown to Raw Artifacts traced through provenance.

## Workstream C — Runtime

Windows login should make Qdrant automatically available. Qdrant remains an independent shared runtime rather than a GUI-owned process.

## Phase P task families

```text
P-GUI-01 .. P-GUI-10
P-RAW-01 .. P-RAW-06
P-RUNTIME-01 .. P-RUNTIME-06
P-CLOSE-01
```

## Next

```text
P-GUI-06 — repeat From/To and Semantic-runtime interactive smoke, then finish the remaining Search / Similarity / Registry / Version / Render smoke
```
