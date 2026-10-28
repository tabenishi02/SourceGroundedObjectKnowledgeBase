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
P-GUI-05 = Automated Verification Refresh Pending / Visual Smoke PASS / Functional Smoke Pending
Next = P-GUI-05 refreshed focused/full/Ruff verification, then representative functional GUI smoke acceptance
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
- CLI <-> GUI capability matrix: [`../reference/GUI_CLI_CAPABILITY_MATRIX.md`](../reference/GUI_CLI_CAPABILITY_MATRIX.md)

### P-GUI-02 accepted authority

- PySide6 architecture / packaging / license review: [`../evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`](../evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md)
- PySide6 application / packaging / license Decision: [`../decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`](../decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md)
- GUI application architecture: [`../design/P_GUI_APPLICATION_ARCHITECTURE.md`](../design/P_GUI_APPLICATION_ARCHITECTURE.md)
- Distribution / license checklist: [`../operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md`](../operations/P_GUI_DISTRIBUTION_AND_LICENSE_CHECKLIST.md)

### P-GUI-03 / 03R accepted authority

- Application boundary audit: [`../evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`](../evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md)
- 67-operation boundary matrix: [`../reference/GUI_APPLICATION_BOUNDARY_MATRIX.md`](../reference/GUI_APPLICATION_BOUNDARY_MATRIX.md)
- Transport-neutral Application Decision: [`../decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md`](../decisions/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_BOUNDARY_DECISION.md)
- Refactor design / execution slices: [`../design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md`](../design/P_GUI_TRANSPORT_NEUTRAL_APPLICATION_REFACTOR_PLAN.md)
- P-GUI-03R task/status: [`phases/P/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](phases/P/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)
- P-GUI-03R implementation result: [`../evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md`](../evaluation/P_GUI_03R_APPLICATION_BOUNDARY_REFACTOR_IMPLEMENTATION.md)
- R9 final acceptance: [`../evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md`](../evaluation/P_GUI_03R_R9_DYNAMIC_VERIFICATION_ATTEMPT_04.md)

Final accepted R9 evidence:

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
sgokb-gui entrypoint                     PASS
focused pytest                           5 / 5 PASS
full pytest                              800 / 800 PASS
ruff                                     All checks passed!
GUI normal startup                       PASS
11 navigation destinations               PASS
Create Workspace                         PASS
Dashboard Workspace/status display       PASS
Open Workspace                           PASS
Recent Workspaces persisted after restart PASS
GUI close / DB release                    PASS
same DB readable from CLI                 PASS
```

### P-GUI-05 implementation authority

- Implementation / verification procedure: [`../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md`](../evaluation/P_GUI_05_OBJECT_SOURCE_EVIDENCE_ASSOCIATION_IMPLEMENTATION.md)
- Add Object Class selector improvement: [`../evaluation/P_GUI_05_ADD_OBJECT_CLASS_SELECTOR_IMPROVEMENT.md`](../evaluation/P_GUI_05_ADD_OBJECT_CLASS_SELECTOR_IMPROVEMENT.md)
- Object Class mutation selector improvement: [`../evaluation/P_GUI_05_OBJECT_CLASS_MUTATION_SELECTOR_IMPROVEMENT.md`](../evaluation/P_GUI_05_OBJECT_CLASS_MUTATION_SELECTOR_IMPROVEMENT.md)
- Recursive Source ZIP import improvement: [`../evaluation/P_GUI_05_SOURCE_RECURSIVE_ZIP_IMPORT_IMPROVEMENT.md`](../evaluation/P_GUI_05_SOURCE_RECURSIVE_ZIP_IMPORT_IMPROVEMENT.md)
- Latest completed automated verification before the newest amendment: [`../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_04.md`](../evaluation/P_GUI_05_DYNAMIC_VERIFICATION_ATTEMPT_04.md)

P-GUI-05 implements real Qt pages for:

```text
Objects
Sources
Evidence
Associations
```

Current operation wiring:

```text
Object       12 / 12
Source        6 / 6
Evidence      5 / 5
Association   4 / 4
------------------
Total        27 / 27
```

The pages use the existing `BackendCoordinator -> BackendWorker -> OperatorSession` path. Stable IDs remain authoritative for Object writes, Relations remain read-only, Source effective selection requires interactive reasons, Raw Artifact metadata is exposed through the shared Source read boundary, Evidence manual selection supports mouse and keyboard, and Association suggestion remains read-only until explicit set.

Object Class controls use registry-backed non-editable selectors:

```text
Add Object Primary Class = active registry Classes
Set Primary Class        = every registry Class
Add Class                = every registry Class except current Primary Class
Remove Class             = assigned Additional Classes only; disabled when none exist
```

Sources now support both single-file and recursive folder import:

```text
Import Capture... = one selected ZIP
Import Folder...  = every ZIP below the selected folder, recursively
folder drag/drop  = same recursive ZIP behavior
```

The recursive scan accepts `.zip` suffixes case-insensitively and preserves existing per-target partial-failure semantics.

The previous automated PASS was measured before this newest Source import amendment:

```text
focused GUI regression = 11 / 11 PASS
Ruff                   = All checks passed!
full regression         = 806 / 806 PASS
known warnings          = 2 local-Qdrant warnings
```

Current status:

```text
Automated Verification Refresh Pending / Visual Smoke PASS / Functional Smoke Pending
```

### Current released system

Phase P is still in development. Released v1.1.0 semantics remain governed by:

- Current integrated architecture: [`../design/SGOKB_CURRENT_ARCHITECTURE.md`](../design/SGOKB_CURRENT_ARCHITECTURE.md)
- Current design index: [`../design/README.md`](../design/README.md)
- Object-centered CLI contract: [`../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`](../decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md)
- Operational safety / recovery: [`../operations/OPERATIONAL_SAFETY_RECOVERY.md`](../operations/OPERATIONAL_SAFETY_RECOVERY.md)
- 1 Object標準運用: [`../operations/OBJECT_STANDARD_WORKFLOW.md`](../operations/OBJECT_STANDARD_WORKFLOW.md)
- Current release note: [`../releases/v1.1.0.md`](../releases/v1.1.0.md)

P-GUI-03R and P-GUI-04 are accepted development baselines. P-GUI-05 is implemented development code pending refreshed automated verification and representative functional GUI smoke and does not by itself advance the formal release version.

## Phase P GUI decisions so far

### Compatibility — P-GUI-01

current public `sgokb` 67 operationsをGUI capabilityへ全件mappingしました。

```text
assigned = 67 / 67
unassigned = 0
```

GUI compatibilityはCLI文字列の再生ではなく、same use case / target identity / canonical effect / validation / safety / degradation / failure semanticsを維持するsemantic parityです。

### Technical architecture — P-GUI-02

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
One-file              = not initial baseline
```

GUI dependencyはbase CLI installから分離され、package surfaceは `.[gui]` + `sgokb-gui` として実装済みです。

現repositoryにはroot `LICENSE`がないため、private developmentは継続できますがpublic OSS publicationはproject-level license Decisionまでblockとします。

### Application boundary — P-GUI-03 / P-GUI-03R / P-GUI-04 / P-GUI-05

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

P-GUI-04 established the queued QThread backend foundation. P-GUI-05 reuses it for all four daily-collection page families and does not add GUI direct SQL or a CLI-subprocess business path.

## Workstream B — RAW Grounding

Evidenceはretrieval / selection単位として維持しますが、External AIへ送るsemantic materialはEvidence本文の再構成Markdownではなく、Evidence provenanceから遡ったRaw Artifactへ変更します。

```text
Evidence Retrieval / Selection
        ↓
selected Evidence
        ↓ provenance traversal
Normalization Run
        ↓
Raw Artifact
        ↓
RAW-bearing Package
        ↓
External AI
        ↓
Structured Object Result
```

Package Manifest、instructions、Object Result schema、Validation、Review、Import、ProvenanceをRaw-grounded contractへ更新します。

## Workstream C — Runtime

Windowsログイン後にQdrantが自動利用可能になる運用を標準化します。

QdrantはGUI processに所有させず、CLI / GUI / MCPから共有可能な独立runtimeとします。初期baseline候補はDocker / Compose、pinned Qdrant、named volume、localhost binding、restart policyです。

## Phase P task families

```text
P-GUI-01 .. P-GUI-03
P-GUI-03R
P-GUI-04 .. P-GUI-10
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
P-GUI-05 — refreshed focused pytest / Ruff / full regression, then representative functional GUI smoke acceptance
```
