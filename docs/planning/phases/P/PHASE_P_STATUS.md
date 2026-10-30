# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-30

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)

## Accepted modernization direction

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01 | **Complete / Accepted** | GUI requirements / compatibility contract |
| GUI | P-GUI-02 | **Complete / Accepted** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | **Complete / Accepted** | Transport-neutral Application boundary audit / refactor plan |
| GUI | P-GUI-03R | **Complete / Accepted** | Shared Application/operator boundary refactor; R9 regression PASS |
| GUI | P-GUI-04 | **Complete / Accepted** | GUI shell / Workspace / navigation foundation |
| GUI | P-GUI-05 | **Complete / Accepted** | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | **Complete / Accepted** | Search / Similarity / Registry / Version GUI |
| GUI | P-GUI-07 | **Complete / Accepted** | Progress / error / safety / audit UX |
| GUI | P-GUI-08 | **Complete / Accepted** | Package / Result GUI against accepted v2 Raw boundary |
| GUI | P-GUI-09 | **Complete / Accepted** | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | **Complete / Accepted** | Final GUI parity / usability / regression acceptance |
| RAW | P-RAW-01 | **Complete / Accepted** | Current Evidence Package / Result impact survey |
| RAW | P-RAW-02 | **Complete / Accepted** | Deterministic Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03 | **Complete / Accepted** | Versioned RAW-bearing Package v2 design |
| RAW | P-RAW-04 | **Complete / Accepted** | Raw-grounded Object Result v2 design |
| RAW | P-RAW-05 | **Complete / Accepted** | Resolver -> Package v2 -> Result v2 -> Raw provenance implementation |
| RAW | P-RAW-06 | **Complete / Accepted** | Formal Raw operational acceptance / compatibility / docs closure |
| Runtime | P-RUNTIME-01 | **Complete / Accepted** | Windows Qdrant runtime operational design / reference approach |
| Runtime | P-RUNTIME-02 | **Complete / Accepted** | Reproducible pinned Qdrant Compose / configuration assets |
| Runtime | P-RUNTIME-03 | **Complete / Accepted** | Shared CLI/GUI runtime health/status Application boundary |
| Runtime | P-RUNTIME-04 | **Not Started / Next** | Windows login auto-start integration |
| Runtime | P-RUNTIME-05 | Not Started | GUI Runtime Dashboard integration |
| Runtime | P-RUNTIME-06 | Not Started | Runtime failure / recovery acceptance |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## GUI workstream — Complete / Accepted

### Accepted architecture

```text
Framework             = PySide6 / Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation in worker thread
Backend concurrency   = serialized per Workspace initially
Windows deployment    = pyside6-deploy / Nuitka standalone directory
Qt linking            = dynamic / separate shared libraries
```

GUI is not a CLI subprocess wrapper. Qdrant remains an independent shared runtime.

### Final public capability parity

Normative inventory:

- `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- `docs/reference/GUI_CLI_CAPABILITY_MATRIX_P_GUI_09_AMENDMENT.md`

Accepted final inventory:

```text
PUBLIC_OPERATION_IDS    = 67
SHARED_OPERATION_IDS    = 66
TRANSPORT_OPERATION_IDS = {mcp.serve}
shared GUI reachability = 66 / 66
MCP GUI reachability    = 1 / 1 via external-client-owned stdio command/configuration surface
unassigned operations   = 0
```

All canonical GUI operations continue through `OperatorSession` or, for the separate Advanced Search Generation inventory, `GenerationOperatorSession`. The GUI does not gain a hidden SQLite/Repository/shell canonical-write path.

### P-GUI-10 final evidence

Authority:

- `docs/evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`
- `tests/test_p_gui_10_parity_usability_acceptance.py`

Final Windows acceptance:

```text
GitHub Actions run                = 41066089220 (#2)
runner                            = Microsoft Windows Server 2025
Python                            = 3.10.11
verified branch source            = 225c99293e3fb346098e42d66625ddac3b30a501
verified synthetic PR merge       = 7ec7dddfd6e5a2f5cb35df0c0f449fd33993fc7a
focused P-GUI-10                  = 6 / 6 PASS
scaled DPI smoke (1.5x)           = 1 / 1 PASS
complete P-GUI regression         = 50 / 50 PASS
CLI + MCP focused regression      = 59 / 59 PASS
Ruff src/tests                    = PASS
full repository regression        = 854 / 854 PASS
warnings                          = 2 known local-Qdrant warnings
```

Historical run `41065681837 (#1)` failed only because the new acceptance test incorrectly expected a single literal `"mcp serve"` source string. The MCP assertion was replaced with live `SystemPage` behavior verification; product code and runtime semantics were not relaxed.

Therefore:

```text
P-GUI-01..10 = Complete / Accepted
P-GUI workstream = Complete / Accepted for Phase P
```

Earlier GUI implementation and acceptance authorities remain authoritative for their task-local contracts, including P-GUI-06/07 interactive acceptance, P-GUI-08 Raw-grounded Package/Result workflow, and P-GUI-09 System/Maintenance/MCP/Advanced behavior.

## P-RAW workstream — Complete / Accepted

### Accepted external AI boundary

```text
selected Evidence
  -> original Normalization Run
  -> ALL input Raw Artifacts
  -> exact verified Raw bytes
  -> Package v2
  -> external AI
  -> Result v2 raw_artifact_id grounding
  -> validate / review / import
  -> raw_grounding_links
  -> accepted Version
```

Accepted contract family:

```text
Package schema     = sgokb.object-evidence-package/2.0
instructions       = sgokb.object-analysis/2.0
Result schema      = sgokb.object-result/2.0
Raw grounding      = sgokb.raw-grounding/1.0
resolver contract  = sgokb.evidence-to-raw/1.0
```

Key authorities:

- `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`
- `docs/design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`
- `docs/design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`
- `docs/evaluation/P_RAW_05_VERIFICATION_ATTEMPT_02.md`
- `docs/decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md`
- `docs/design/P_RAW_06_ACCEPTED_EXTERNAL_AI_BOUNDARY.md`
- `docs/operations/P_RAW_06_RAW_GROUNDING_WORKFLOW.md`
- `docs/evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md`

Compatibility/cutover disposition:

```text
v1 accepted Version -> v2 update = supported
v2 accepted Version -> v2 update = supported
v2 accepted Version -> v1 update = blocked by default
Result v2 -> Evidence claim-link synthesis = forbidden
Phase P Raw operation = explicit --package-version v2
no-option package default = v1 until P-CLOSE-01 release/default decision
```

Therefore:

```text
P-RAW-01..06 = Complete / Accepted
P-RAW workstream = Complete / Accepted for Phase P
```

## P-RUNTIME accepted baseline

### P-RUNTIME-01 — Windows Qdrant runtime operational design

Accepted reference runtime:

```text
container runtime        = Docker Desktop / WSL 2
runtime definition       = repository-owned Docker Compose
Qdrant initial pin       = qdrant/qdrant:v1.20.0
startup                  = Docker Desktop at user sign-in
container restart        = unless-stopped
persistent storage       = Docker named volume
HTTP                     = 127.0.0.1:6333 -> 6333
gRPC                     = 127.0.0.1:6334 -> 6334
distributed port 6335    = not published
readiness                = Qdrant /readyz
GUI / CLI lifecycle role = client / observer only
```

Authorities:

- `docs/evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md`
- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`

### P-RUNTIME-02 — Qdrant Compose / configuration assets

Accepted repository runtime:

```text
Compose project        = sgokb-qdrant
image                  = qdrant/qdrant:v1.20.0
restart                = unless-stopped
HTTP                   = 127.0.0.1:6333
preferred gRPC         = 127.0.0.1:6334
persistent volume      = sgokb_qdrant_storage
container storage      = /qdrant/storage
health/readiness       = /readyz -> HTTP 200
local override         = QDRANT_LOG_LEVEL only
```

Authorities:

- `runtime/qdrant/compose.yaml`
- `runtime/qdrant/.env.example`
- `runtime/qdrant/README.md`
- `docs/operations/P_RUNTIME_02_QDRANT_COMPOSE_RUNTIME.md`
- `docs/evaluation/P_RUNTIME_02_QDRANT_COMPOSE_CONFIGURATION_ACCEPTANCE.md`

### P-RUNTIME-03 — Runtime health/status Application boundary

Accepted shared observation contract:

```text
operation                  = system.status
projection                 = data.runtime_health
schema                     = sgokb.runtime-health/1.0
components                 = sqlite / embedding / qdrant / generation / derived
qdrant lifecycle owner     = external
observe                    = true
start / stop / restart     = false / false / false
embedding status read      = shallow / no model load / no download
qdrant readiness authority = /readyz
```

Authorities:

- `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_APPLICATION_BOUNDARY.md`
- `docs/evaluation/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_ACCEPTANCE.md`
- `src/sgokb/runtime_health.py`
- `src/sgokb/application_system.py`

Therefore:

```text
P-RUNTIME-01 = Complete / Accepted
P-RUNTIME-02 = Complete / Accepted
P-RUNTIME-03 = Complete / Accepted
```

P-RUNTIME-04 still owns actual Windows login/restart startup ordering, readiness/retry, troubleshooting, and unexpected-stop recovery verification. P-RUNTIME-05 owns the dedicated GUI Runtime Dashboard; P-RUNTIME-06 owns failure/recovery acceptance.

## Sequencing

```text
P-GUI-01..10 Complete / Accepted
        ↓
P-RAW-01..06 Complete / Accepted
        ↓
P-RUNTIME-01..03 Complete / Accepted
        ↓
P-RUNTIME-04   <- NEXT
        ↓
P-RUNTIME-05
        ↓
P-RUNTIME-06
        ↓
P-CLOSE-01
```

## Current authority boundary

Phase P remains in development. Released-system semantics continue to be governed by release `v1.1.0` until Phase P closure/release integration.

P-GUI-01 through P-GUI-10, P-RAW-01 through P-RAW-06, and P-RUNTIME-01 through P-RUNTIME-03 are accepted development baselines. The Qdrant runtime remains independently owned outside SGOKB; `system.status.runtime_health` is the accepted shared observation boundary for CLI/GUI, while MCP stdio lifecycle remains external-client-owned.

## Next

```text
P-RUNTIME-04 — Windows login auto-start integration
```
