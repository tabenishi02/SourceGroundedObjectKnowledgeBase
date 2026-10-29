# Planning documents

`docs/planning/` は、Source Grounded Object Knowledge Base（SGOKB）の進行計画、Phase準備/完了監査、Task一覧、実行handoffを管理する領域です。

Planning文書はPhase / Task単位で整理し、`docs/planning/`直下のこのファイルは current-state / authority index として扱います。Phase P の詳細状態は [`phases/P/PHASE_P_STATUS.md`](phases/P/PHASE_P_STATUS.md) を正本とします。

## Current phase

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Complete
Happy-path operational acceptance = Complete / FULL SGOKB PASS
Current formal release = v1.1.0
Phase P = In Progress

P-GUI-01..08 = Complete / Accepted
P-RAW-01..06 = Complete / Accepted
P-GUI-09 = Not Started / blocked by P-RUNTIME-03
P-GUI-10 = Not Started
P-RUNTIME-01 = Not Started / Next
P-RUNTIME-02..06 = Not Started
P-CLOSE-01 = Not Started
```

Phase P の Workstream 優先順位は次です。

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

GUI と RAW Grounding の優先作業は P-GUI-08 まで完了しています。残る GUI の P-GUI-09 は P-RUNTIME-03 に依存するため、現在の実行順では Runtime workstream が次です。

## Phase P planning authority

- Phase P plan: [`phases/P/PHASE_P_MODERNIZATION_PLAN.md`](phases/P/PHASE_P_MODERNIZATION_PLAN.md)
- Phase P tasks: [`phases/P/PHASE_P_TASKS.md`](phases/P/PHASE_P_TASKS.md)
- Phase P current status: [`phases/P/PHASE_P_STATUS.md`](phases/P/PHASE_P_STATUS.md)
- P-GUI-03R task amendment: [`phases/P/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](phases/P/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)
- Project task amendment: [`project/KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md`](project/KNOWLEDGE_BASE_REDESIGN_TASKS_PHASE_P_AMENDMENT.md)

## Accepted GUI authority

### P-GUI-01

- Requirements: [`../requirements/GUI_REQUIREMENTS.md`](../requirements/GUI_REQUIREMENTS.md)
- Compatibility / safety decision: [`../decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`](../decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md)
- CLI ↔ GUI capability matrix: [`../reference/GUI_CLI_CAPABILITY_MATRIX.md`](../reference/GUI_CLI_CAPABILITY_MATRIX.md)

### P-GUI-02

- Architecture / packaging / license review: [`../evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`](../evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md)
- Decision: [`../decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`](../decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md)
- Application architecture: [`../design/P_GUI_APPLICATION_ARCHITECTURE.md`](../design/P_GUI_APPLICATION_ARCHITECTURE.md)
- Distribution / license checklist: [`../operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`](../operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md)

### P-GUI-03 / P-GUI-03R

- Application boundary audit: [`../evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`](../evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md)
- Boundary matrix: [`../reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`](../reference/GUI_APPLICATION_BOUNDARY_MATRIX.md)
- Transport-neutral decision: [`../decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`](../decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md)
- Refactor plan: [`../design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`](../design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md)
- Implementation: [`../evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](../evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)
- Final R9 acceptance: [`../evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`](../evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md)

### P-GUI-04..07

- P-GUI-04 implementation / acceptance: [`../evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md`](../evaluation/P_GUI_04_GUI_SHELL_WORKSPACE_NAVIGATION_IMPLEMENTATION.md)
- P-GUI-05 implementation: [`../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`](../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md)
- P-GUI-05 automated acceptance: [`../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md`](../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_07.md)
- P-GUI-05 interactive acceptance: [`../evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_05_FINAL_INTERACTIVE_ACCEPTANCE.md)
- P-GUI-06 implementation: [`../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md`](../evaluation/P_GUI_06_SEARCH_SIMILARITY_REGISTRY_VERSION_IMPLEMENTATION.md)
- P-GUI-06 automated acceptance: [`../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`](../evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md)
- P-GUI-06 interactive acceptance: [`../evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md)
- P-GUI-07 design: [`../design/P_GUI_OPERATION_SAFETY_AUDIT_UX.md`](../design/P_GUI_OPERATION_SAFETY_AUDIT_UX.md)
- P-GUI-07 implementation: [`../evaluation/P_GUI_07_PROGRESS_ERROR_SAFETY_AUDIT_UX_IMPLEMENTATION.md`](../evaluation/P_GUI_07_PROGRESS_ERROR_SAFETY_AUDIT_UX_IMPLEMENTATION.md)
- P-GUI-07 automated acceptance: [`../evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`](../evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md)
- P-GUI-07 interactive acceptance: [`../evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`](../evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md)

### P-GUI-08 — Package / Result GUI

- Implementation: [`../evaluation/P_GUI_08_PACKAGE_RESULT_GUI_IMPLEMENTATION.md`](../evaluation/P_GUI_08_PACKAGE_RESULT_GUI_IMPLEMENTATION.md)
- Final automated acceptance: [`../evaluation/P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md`](../evaluation/P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md)
- Operator workflow: [`../operations/P_GUI_08_PACKAGE_RESULT_GUI_WORKFLOW.md`](../operations/P_GUI_08_PACKAGE_RESULT_GUI_WORKFLOW.md)

Final P-GUI-08 gate:

```text
P-GUI-08 focused acceptance = 4 / 4 PASS
GUI regression              = 38 / 38 PASS
Ruff src/tests              = PASS
full repository regression  = 837 / 837 PASS
warnings                    = 2 known local-Qdrant warnings
GitHub Actions PR run        = 40945757254
verified branch source       = 3015c01aaaecfe5800032ef25b7c9d92cb30e635
verified synthetic merge     = 4010fd93efe4e04f20acff8b98068593d0ac44b5
```

Accepted P-GUI-08 boundary:

```text
GUI Package v2 = explicit Raw-grounded normal path
GUI Package v1 = explicit legacy compatibility path
shared omitted-version Package default = v1, unchanged
Result v2 review shows Raw grounding references
Result v2 import persists raw_grounding_links
Result v2 Evidence claim-link synthesis = forbidden
```

P-GUI-08 is automated functional/contract acceptance. GUI-wide parity/usability closure remains owned by P-GUI-10.

## Accepted RAW Grounding authority

### P-RAW-01 — impact survey

- [`../evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md`](../evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md)

### P-RAW-02 — deterministic Evidence -> Raw provenance

- [`../design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`](../design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md)

### P-RAW-03 — Package v2

- [`../design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`](../design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md)

### P-RAW-04 — Result v2

- [`../design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`](../design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md)

### P-RAW-05 — implementation / verification

- Implementation: [`../evaluation/P_RAW_05_RAW_GROUNDING_IMPLEMENTATION.md`](../evaluation/P_RAW_05_RAW_GROUNDING_IMPLEMENTATION.md)
- Historical verification failure/remediation: [`../evaluation/P_RAW_05_VERIFICATION_ATTEMPT_01.md`](../evaluation/P_RAW_05_VERIFICATION_ATTEMPT_01.md)
- Final acceptance: [`../evaluation/P_RAW_05_VERIFICATION_ATTEMPT_02.md`](../evaluation/P_RAW_05_VERIFICATION_ATTEMPT_02.md)

### P-RAW-06 — operational acceptance / compatibility / documentation

- Requirements: [`../requirements/RAW_GROUNDING_REQUIREMENTS.md`](../requirements/RAW_GROUNDING_REQUIREMENTS.md)
- Compatibility / cutover decision: [`../decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md`](../decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md)
- Accepted external-AI boundary: [`../design/P_RAW_06_ACCEPTED_EXTERNAL_AI_BOUNDARY.md`](../design/P_RAW_06_ACCEPTED_EXTERNAL_AI_BOUNDARY.md)
- Operator workflow: [`../operations/P_RAW_06_RAW_GROUNDING_WORKFLOW.md`](../operations/P_RAW_06_RAW_GROUNDING_WORKFLOW.md)
- Final acceptance: [`../evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md`](../evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md)

Final P-RAW-06 gate:

```text
P-RAW-06 focused acceptance       = 6 / 6 PASS
P-RAW / legacy v1 exchange gate   = 91 / 91 PASS
Ruff src/tests                    = PASS
full repository regression        = 833 / 833 PASS
warnings                          = 2 known local-Qdrant warnings
GitHub Actions run                = 40937273709
```

Accepted compatibility / cutover boundary:

```text
Package v2 / Result v2 = accepted Raw-grounded external AI boundary
v1 current -> v2 update = supported
v2 current -> v2 update = supported
v2 current -> v1 update = blocked by default
Result v2 -> fabricated Evidence claim links = forbidden
Phase P Raw operation = explicit --package-version v2
no-option package default = v1 until P-CLOSE-01 release/default decision
```

Therefore:

```text
P-RAW-01..06 = Complete / Accepted
P-RAW workstream = Complete / Accepted for Phase P
P-GUI-01..08 = Complete / Accepted
```

## Phase P architecture summary

```text
GUI framework          = PySide6 / Qt Widgets
CLI/GUI boundary       = shared Application / Service layer
GUI backend            = QObject worker on dedicated QThread
SQLite                 = Repository per operation in worker thread
Backend concurrency    = serialized per Workspace initially
Qdrant                 = independent shared runtime
Raw semantic boundary  = Package v2 exact Raw -> Result v2 raw_artifact_id
```

## Remaining workstreams

### GUI

`P-GUI-09` remains Not Started and depends on `P-RUNTIME-03`. `P-GUI-10` is the final GUI parity / regression acceptance task.

### Runtime

`P-RUNTIME-01` is the next executable task. `P-RUNTIME-01..06` establish Windows-login automatic Qdrant availability while keeping Qdrant an independent shared runtime rather than a GUI-owned child process.

### Closure

`P-CLOSE-01` owns full Phase P regression, documentation/release integration, and the final decision on the no-option Package version default.

## Next

```text
P-RUNTIME-01 — Windows auto-start方式比較
```
