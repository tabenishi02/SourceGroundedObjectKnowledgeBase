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
Current formal release = v2.1.0
Phase P = Complete / Accepted / Released

P-GUI-01..10 = Complete / Accepted
P-RAW-01..06 = Complete / Accepted
P-RUNTIME-01..06 = Complete / Accepted
P-CLOSE-01 = Complete / Accepted
Post-release GUI startup/runtime-health update = Interactive PASS / released in v2.1.0
```

Phase P の Workstream 優先順位は次です。

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

Phase P は P-GUI-01..10、P-RAW-01..06、P-RUNTIME-01..06、P-CLOSE-01 まで完了し、`v2.0.0` として release/freeze 済みです。その後の post-Phase-P update として、2026-11-01 に consoleless Windows launcher、startup splash、supported legacy Search routing の HEALTHY classification、GUI normality verification、documentation consistency audit を完了し、これらを後方互換な MINOR release `v2.1.0` として正式化しました。詳細は `../evaluation/POST_RELEASE_GUI_STARTUP_RUNTIME_HEALTH_2026_11_01.md` と `../releases/v2.1.0.md` を参照します。

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

### P-GUI-09 — System / Maintenance / MCP / Advanced GUI

- Design: [`../design/P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_DESIGN.md`](../design/P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_DESIGN.md)
- MCP lifecycle decision: [`../decisions/P_GUI_09_MCP_STDIO_LIFECYCLE_DECISION.md`](../decisions/P_GUI_09_MCP_STDIO_LIFECYCLE_DECISION.md)
- Capability-matrix amendment: [`../reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`](../reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md)
- Final acceptance: [`../evaluation/P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_ACCEPTANCE.md`](../evaluation/P_GUI_09_SYSTEM_MAINTENANCE_MCP_ADVANCED_ACCEPTANCE.md)

Accepted P-GUI-09 boundary:

```text
public System operations         = 14 / 14 GUI-reachable
Advanced Search Generation       = 6 / 6 GUI-reachable
System execution                 = shared OperatorSession
Generation execution             = shared GenerationOperatorSession
Restore                          = Plan -> preview -> acknowledgement -> Apply
MCP transport                    = stdio
MCP lifecycle owner              = external MCP client / launcher
GUI detached MCP start/stop      = no
Qdrant lifecycle owner           = external
system.status runtime projection = P-RUNTIME-03 data.runtime_health
```

Final P-GUI-09 gate:

```text
GitHub Actions run               = 41049707411 (#8)
verified branch source           = e0456b12dfdfc8897ed21358dbc4c04ffef6c43d
verified synthetic merge         = bfcd5caf63c5e072a1e844c85e47bc2411d57c19
focused P-GUI-09                 = 6 / 6 PASS
GUI regression                   = 44 / 44 PASS
Ruff src/tests                   = PASS
full repository regression       = 848 / 848 PASS
warnings                         = 2 known local-Qdrant warnings
```

P-GUI-09 is automated functional/contract acceptance. GUI-wide parity/usability closure remains owned by P-GUI-10.

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
P-GUI-01..09 = Complete / Accepted
```

## Accepted Runtime authority

### P-RUNTIME-01 — Windows Qdrant runtime operational design

- Comparison / external research: [`../evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md`](../evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md)
- Accepted decision: [`../decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`](../decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md)

Accepted reference:

```text
Windows runtime           = Docker Desktop + WSL 2 + Docker Compose
Qdrant initial pin        = qdrant/qdrant:v1.20.0
startup                   = Docker Desktop at user sign-in
restart policy            = unless-stopped
persistent state          = Docker named volume
HTTP                      = 127.0.0.1:6333
preferred gRPC            = 127.0.0.1:6334
Qdrant distributed port   = not published
readiness                 = /readyz
SGOKB lifecycle ownership = none; observer/client only
```

The existing SGOKB adapter defaults to REST `localhost:6333`, gRPC `6334`, and `prefer_grpc=True`, so both local ports are part of the reference contract.

Native Windows Qdrant + Task Scheduler was evaluated but is not a supported Phase P acceptance path. Docker Desktop is an external prerequisite with independent installation/license terms and is not bundled by SGOKB.

### P-RUNTIME-02 — Qdrant Compose / configuration assets

- Compose: [`../../runtime/qdrant/compose.yaml`](../../runtime/qdrant/compose.yaml)
- environment template: [`../../runtime/qdrant/.env.example`](../../runtime/qdrant/.env.example)
- runtime README: [`../../runtime/qdrant/README.md`](../../runtime/qdrant/README.md)
- operations: [`../operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`](../operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md)
- final acceptance: [`../evaluation/P_RUNTIME_02_QDRANT_COMPOSE_CONFIGURATION_ACCEPTANCE.md`](../evaluation/P_RUNTIME_02_QDRANT_COMPOSE_CONFIGURATION_ACCEPTANCE.md)

Final P-RUNTIME-02 gate:

```text
GitHub Actions run          = 40961873913
verified branch source      = 1732322b7a0d40dbd4838e3b62cebea1fb458baf
verified synthetic merge    = 56b2ee1d1c83e0f4c84c27575ed8fdbcbb7bade9
Compose render              = PASS
focused contract tests      = 2 / 2 PASS
real Qdrant v1.20.0         = PASS
/readyz                     = PASS
named-volume persistence    = PASS
recreate / second readiness = PASS
Ruff src/tests              = PASS
Windows full regression     = 839 / 839 PASS
warnings                    = 2 known local-Qdrant warnings
```

Accepted runtime boundary:

```text
image                    = qdrant/qdrant:v1.20.0
restart                  = unless-stopped
ports                    = loopback 6333 + 6334 only
persistent volume        = sgokb_qdrant_storage
container storage        = /qdrant/storage
readiness                = /readyz -> HTTP 200
operator local override  = QDRANT_LOG_LEVEL only
```

### P-RUNTIME-03 — Runtime health/status Application boundary

- Design / contract: [`../design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`](../design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md)
- Final acceptance: [`../evaluation/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_ACCEPTANCE.md`](../evaluation/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_ACCEPTANCE.md)

Accepted shared observation boundary:

```text
operation                  = system.status
projection                 = data.runtime_health
schema                     = sgokb.runtime-health/1.0
components                 = sqlite / embedding / qdrant / generation / derived
qdrant lifecycle owner     = external
observe                    = true
start / stop / restart     = false / false / false
embedding status           = shallow / no model load / no download
qdrant readiness authority = /readyz
```

Final P-RUNTIME-03 gate:

```text
GitHub Actions run          = 40968417323
verified branch source      = 90f699a094d9426a7b26c1995b46fdb7ce377150
verified synthetic merge    = 1cbf1cabca97477e9932795c2ce5700ebe058897
focused contract tests      = 3 / 3 PASS
Ruff src/tests              = PASS
real Qdrant v1.20.0         = healthy
live system.status probe    = PASS
reported Qdrant version     = 1.20.0
Windows full regression     = 842 / 842 PASS
warnings                    = 2 known local-Qdrant warnings
```

P-RUNTIME-03 preserves external Qdrant lifecycle ownership and gives CLI/GUI the same read-only runtime status model. Windows login auto-start remains P-RUNTIME-04 scope.

## Phase P architecture summary

```text
GUI framework          = PySide6 / Qt Widgets
CLI/GUI boundary       = shared Application / Service layer
GUI backend            = QObject worker on dedicated QThread
SQLite                 = Repository per operation in worker thread
Backend concurrency    = serialized per Workspace initially
Qdrant                 = independent shared runtime
Qdrant Windows ref     = Docker Desktop / WSL2 / Compose / named volume
Runtime health         = shared system.status.runtime_health observation model
MCP transport          = stdio; external client-owned lifecycle
Generation maintenance = shared GenerationOperatorSession
Raw semantic boundary  = Package v2 exact Raw -> Result v2 raw_artifact_id
```

## Remaining workstreams

### GUI

`P-GUI-01` through `P-GUI-09` are Complete / Accepted. `P-GUI-10` is now the next GUI task and owns final CLI↔GUI capability coverage, representative canonical-state equivalence, usability, keyboard/DPI/restart scenarios, and GUI-wide regression closure.

### Runtime

`P-RUNTIME-01` through `P-RUNTIME-03` are Complete / Accepted. P-RUNTIME-04 retains Windows login auto-start integration/acceptance ownership; later Runtime Dashboard/recovery work must consume the accepted observation boundary without moving Qdrant lifecycle ownership into the GUI.

### Closure

`P-CLOSE-01` owns full Phase P regression, documentation/release integration, and the final decision on the no-option Package version default.

## Next

```text
P-GUI-10 — GUI parity / usability / regression acceptance
```
