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
Next = P-GUI-06 interactive GUI smoke acceptance
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

Accepted R9 evidence:

```text
operator-boundary + M01 CLI = 18 / 18 PASS
M03 standard workflow       = 2 / 2 PASS
Phase N closure audit       = 11 / 11 PASS
full pytest                 = 795 / 795 PASS
ruff                        = All checks passed!
```

### P-GUI-04 accepted authority

- Implementation / final acceptance: [`../evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md`](../evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md)

P-GUI-04 acceptance evidence:

```text
focused pytest = 5 / 5 PASS
full pytest    = 800 / 800 PASS
ruff           = PASS
interactive GUI shell / Workspace acceptance = PASS
```

### P-GUI-05 accepted authority

- Final implementation record: [`../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`](../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md)
- Final automated verification: [`../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md`](../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md)
- Final interactive acceptance: [`../evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md)
- Add Object Class selector improvement: [`../evaluation/P_GUI_05_ADD_OBJECT_CLASS_SELECTOR_IMPROVEMENT.md`](../evaluation/P_GUI_05_ADD_OBJECT_CLASS_SELECTOR_IMPROVEMENT.md)
- Object Class mutation selector improvement: [`../evaluation/P_GUI_05_OBJECT_CLASS_MUTATION_SELECTOR_IMPROVEMENT.md`](../evaluation/P_GUI_05_OBJECT_CLASS_MUTATION_SELECTOR_IMPROVEMENT.md)
- Recursive Source ZIP import improvement: [`../evaluation/P_GUI_05_SOURCE_RECURSIVE_ZIP_IMPORT_IMPROVEMENT.md`](../evaluation/P_GUI_05_SOURCE_RECURSIVE_ZIP_IMPORT_IMPROVEMENT.md)

Final P-GUI-05 evidence:

```text
focused GUI regression = 12 / 12 PASS
Ruff                   = All checks passed!
full regression         = 807 / 807 PASS
visual smoke            = PASS
functional smoke        = PASS
P-GUI-05                = Complete / Accepted
```

### P-GUI-06 current authority

- Main implementation / interactive procedure: [`../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`](../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md)
- Current automated verification: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md)
- Current range identity / GUI runtime-state remediation: [`../evaluation/P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md`](../evaluation/P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md)
- Historical Attempt 04 verification: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md)
- Historical Attempt 03 fixture/lint failure: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_03.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_03.md)
- Historical selector/range verification: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_02.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_02.md)
- Historical pre-amendment verification: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md)
- Search selector / validity-range amendment: [`../evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`](../evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md)
- First validity-range false-negative remediation: [`../evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`](../evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md)
- Derivation Kind selector improvement: [`../evaluation/P_GUI_06_DERIVATION_KIND_SELECTOR_IMPROVEMENT.md`](../evaluation/P_GUI_06_DERIVATION_KIND_SELECTOR_IMPROVEMENT.md)

P-GUI-06 keeps the 14 assigned operations wired:

```text
Search       1 / 1
Similarity   1 / 1
Registry     9 / 9
Version      2 / 2
Render       1 / 1
------------------
Total       14 / 14
```

Current Search / Similarity surface includes:

- Lexical / Semantic / Hybrid Search;
- Registry-backed Primary / Additional / Ancestor Class dropdowns;
- Facet / Version / Temporal Scope selectors with editable historical fallback;
- `Knowledge valid From` / `Knowledge valid To` temporal-overlap range;
- fixed-value Derivation Kind selector;
- explicit semantic-runtime / strict full-runtime controls;
- degraded-channel display;
- per-request runtime-state reset/failure presentation;
- Object-scoped Similarity Facet / Version selectors;
- cross-Class and archived scope controls;
- no silent local-runtime or cloud fallback.

The final validity-range boundary is:

```text
Registry identity eligibility under From/To -> canonical accepted Knowledge
Knowledge lexical / semantic channels       -> active R2 Search generation
```

The remediation covers both stale derived-generation and Statement-less accepted-Version identity false negatives. Statement-specific Facet / Derivation Kind / Temporal Scope filters remain strict.

Current Registry / Version / Render surface remains:

- Class list/detail;
- Relation Type list/detail;
- Registry Proposal list/detail / decision filter;
- Accept / Reject separate from Apply;
- explicit Apply confirmation;
- Version Show;
- structured / Markdown Version Diff;
- Object/Version render/export and generated Markdown preview.

Current automated evidence from Attempt 05:

```text
focused P-GUI-04 / 05 / 06 regression = 31 / 31 PASS
Ruff                                  = All checks passed!
full regression                        = 826 / 826 PASS
known local-Qdrant warnings            = 2
```

The focused gate includes the Statement-less range identity regression, GUI runtime-state regression, and real in-memory Qdrant + R2 generation + From/To semantic regression. Attempt 03 remains historical fixture/lint failure evidence; Attempt 04 remains the prior successful authority before the latest interactive remediation.

Current status:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

### Current released system

Phase P remains in development. Released `v1.1.0` semantics remain governed by current architecture, decision, operations and release documents.

P-GUI-01 through P-GUI-05 are accepted development baselines. P-GUI-06 has passed the current automated gate and remains pending interactive acceptance. These tasks do not by themselves advance the formal release version.

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
Semantic runtime      = expensive noncanonical runtime may be lazy-cached
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

## Document placement rules

1. 全Phase共通の進捗 / project-wide handoff → `project/`
2. Phase単位のstatus / preparation / closure / task authority → `phases/<Phase>/`
3. 特定Taskに複数文書が増える場合 → `phases/<Phase>/<Task>/`
4. 一時的な実行handoff → 対象Task配下の`execution/`
5. 結果・調査報告 → `docs/evaluation/`
6. 設計Decision → `docs/decisions/`
7. 実装設計 → `docs/design/`
8. operator手順 / operational safety → `docs/operations/`
9. Release Note / compatibility boundary → `docs/releases/`

## Next

```text
P-GUI-06 — interactive GUI smoke acceptance
```
