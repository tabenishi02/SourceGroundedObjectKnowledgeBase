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
| GUI | P-GUI-06 | **Complete / Accepted** | Search / Similarity / Registry / Version GUI; Attempt 09 + interactive PASS |
| GUI | P-GUI-07 | **Complete / Accepted** | Progress / error / safety / audit UX; automated + interactive PASS |
| GUI | P-GUI-08 | **Complete / Accepted** | Package / Result GUI against accepted v2 Raw boundary |
| GUI | P-GUI-09 | **Not Started / Blocked by P-RUNTIME-03** | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01 | **Complete / Accepted** | Current Evidence Package / Result impact survey |
| RAW | P-RAW-02 | **Complete / Accepted** | Deterministic Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03 | **Complete / Accepted** | Versioned RAW-bearing Package v2 design |
| RAW | P-RAW-04 | **Complete / Accepted** | Raw-grounded Object Result v2 design |
| RAW | P-RAW-05 | **Complete / Accepted** | Resolver -> Package v2 -> Result v2 -> Raw provenance implementation |
| RAW | P-RAW-06 | **Complete / Accepted** | Formal Raw operational acceptance, compatibility/cutover disposition, documentation closure |
| Runtime | P-RUNTIME-01 | **Complete / Accepted** | Windows Qdrant runtime operational design / reference approach |
| Runtime | P-RUNTIME-02 | **Not Started / Next** | Qdrant Compose / configuration assets |
| Runtime | P-RUNTIME-03..06 | Not Started | Runtime health / login auto-start / GUI integration / acceptance |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## GUI baseline

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

## P-GUI-01..08 accepted baseline

```text
P-GUI-01..03R = Complete / Accepted
P-GUI-04      = Complete / Accepted
P-GUI-05      = Complete / Accepted
P-GUI-06      = Complete / Accepted
P-GUI-07      = Complete / Accepted
P-GUI-08      = Complete / Accepted
```

P-GUI-06 final evidence:

```text
focused regression = 29 / 29 PASS
Ruff               = PASS
full regression    = 818 / 818 PASS
warnings           = 2 known local-Qdrant warnings
interactive smoke  = PASS in accepted scope
```

P-GUI-07 final evidence:

```text
focused GUI gate   = 34 / 34 PASS
Ruff               = PASS
full regression    = 823 / 823 PASS
warnings           = 2 known local-Qdrant warnings
interactive smoke  = PASS in accepted scope
```

P-GUI-08 final evidence:

```text
focused Package / Result GUI = 4 / 4 PASS
GUI regression               = 38 / 38 PASS
Ruff src/tests               = PASS
full repository regression   = 837 / 837 PASS
warnings                     = 2 known local-Qdrant warnings
GitHub Actions PR run         = 40945757254
verified branch source        = 3015c01aaaecfe5800032ef25b7c9d92cb30e635
verified synthetic merge      = 4010fd93efe4e04f20acff8b98068593d0ac44b5
```

P-GUI-08 accepted workflow:

```text
GUI Evidence selection
  -> Package v2 build / Raw resolution
  -> Raw Artifact inclusion + Evidence->Raw inspection
  -> stage / preflight / acknowledged export
  -> external Result
  -> detect / receive / validate
  -> current Knowledge + Raw grounding review
  -> acknowledged import when required
  -> accepted Knowledge Version with raw_grounding_links
```

The GUI selects v2 explicitly for the accepted Raw-grounded path, while the shared Application/CLI omitted-version default remains v1 until P-CLOSE-01.

Final GUI authority includes:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`
- `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`
- `docs/evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`
- `docs/evaluation/P_GUI_08_PACKAGE_RESULT_GUI_IMPLEMENTATION.md`
- `docs/evaluation/P_GUI_08_PACKAGE_RESULT_GUI_ACCEPTANCE.md`
- `docs/operations/P_GUI_08_PACKAGE_RESULT_GUI_WORKFLOW.md`

P-GUI-08 is automated functional/contract acceptance. Final GUI-wide parity/usability closure remains owned by P-GUI-10.

## P-RAW accepted baseline

### P-RAW-01 — impact survey

Authority:

- `docs/evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md`

Accepted conclusion: Raw Grounding changes the external exchange / grounding boundary while preserving the core accepted Knowledge model. Evidence-Markdown external semantic authority, Evidence-only grounding membership, Evidence-ID-only Result grounding, and Evidence-only validation were identified as versioned breaking contracts.

### P-RAW-02 — deterministic provenance resolution

Authority:

- `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`

Accepted resolver scope:

```text
Evidence
  -> its own historical Normalization Run
  -> ALL normalization_run_artifacts
  -> exact Snapshot / Source generation
  -> byte-size / SHA-256 verification
```

Same Raw ID is deduplicated at Package identity level; distinct Raw IDs are never collapsed merely because hashes match. Missing or inconsistent provenance fails closed and has no Evidence-Markdown fallback.

### P-RAW-03 — Package v2

Authority:

- `docs/design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`

Accepted Package family:

```text
Package schema     = sgokb.object-evidence-package/2.0
instructions       = sgokb.object-analysis/2.0
expected Result    = sgokb.object-result/2.0
Raw grounding      = sgokb.raw-grounding/1.0
resolver contract  = sgokb.evidence-to-raw/1.0
```

Package v2 transports exact Raw bytes at safe deterministic paths such as `raw/artifact_0001/payload`. Evidence remains selection/provenance metadata; semantic grounding membership authority is `manifest.raw_grounding.included_raw_artifact_ids`.

### P-RAW-04 — Result v2

Authority:

- `docs/design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`

Accepted Result family:

```text
Result schema      = sgokb.object-result/2.0
grounding target   = Package-member raw_artifact_id
grounding field    = grounding[]
```

Optional mechanically verifiable locators are `byte_range` and `text_quote`. Import persistence remains version-specific:

```text
v1 -> evidence_links
v2 -> raw_grounding_links
```

Result v2 import must not synthesize Evidence claim links.

### P-RAW-05 — implementation

Authority:

- `docs/evaluation/P_RAW_05_RAW_GROUNDING_IMPLEMENTATION.md`
- `docs/evaluation/P_RAW_05_VERIFICATION_ATTEMPT_01.md` — historical FAIL / remediation record
- `docs/evaluation/P_RAW_05_VERIFICATION_ATTEMPT_02.md` — final PASS / acceptance

Final P-RAW-05 evidence:

```text
focused P-RAW/v1 regression = 91 / 91 PASS
migration regression        = 56 / 56 PASS
Ruff                        = PASS
full regression             = 827 / 827 PASS
warnings                    = 2 known local-Qdrant warnings
```

### P-RAW-06 — formal acceptance / compatibility / documentation

Authorities:

- `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- `docs/decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md`
- `docs/design/P_RAW_06_ACCEPTED_EXTERNAL_AI_BOUNDARY.md`
- `docs/operations/P_RAW_06_RAW_GROUNDING_WORKFLOW.md`
- `docs/evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md`

Accepted operational boundary:

```text
selected Evidence
  -> original Normalization Run
  -> exact verified Raw bytes
  -> Package v2
  -> external AI
  -> Result v2 raw_artifact_id grounding
  -> validate / review / import
  -> raw_grounding_links
  -> accepted Version
```

Final Windows acceptance evidence:

```text
P-RAW-06 focused acceptance       = 6 / 6 PASS
P-RAW / legacy v1 exchange gate   = 91 / 91 PASS
Ruff src/tests                    = PASS
full repository regression        = 833 / 833 PASS
warnings                          = 2 known local-Qdrant warnings
GitHub Actions run                = 40937273709
verified branch source            = 5e4c8729f8d79c3f3fa956af9208aae98b1a2a48
```

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
P-GUI-01..08 = Complete / Accepted
```

## P-RUNTIME-01 accepted baseline

Authorities:

- `docs/evaluation/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_COMPARISON.md`
- `docs/decisions/P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md`

Accepted reference Windows runtime:

```text
container runtime       = Docker Desktop / WSL 2
runtime definition      = repository-owned Docker Compose
Qdrant initial pin      = qdrant/qdrant:v1.20.0
startup                 = Docker Desktop at user sign-in
container restart       = unless-stopped
persistent storage      = Docker named volume
HTTP                     = 127.0.0.1:6333 -> 6333
gRPC                     = 127.0.0.1:6334 -> 6334
distributed port 6335    = not published
readiness                = Qdrant /readyz
GUI / CLI lifecycle role = client / observer only
```

The two local ports are required because the current `QdrantVectorIndexAdapter` uses `http://localhost:6333`, `grpc_port=6334`, and `prefer_grpc=True` by default.

Windows host bind mounts are not the reference Qdrant storage path. Qdrant's Windows Docker/WSL filesystem warning makes a named Docker volume the accepted persistence boundary.

Native `qdrant.exe` + Task Scheduler, Windows service wrappers, WSL/systemd-only deployment, and ad-hoc Startup-folder scripts are not Phase P supported acceptance paths. The official native Windows binary is acknowledged only as an operator-controlled manual/experimental alternative.

Docker Desktop remains an external prerequisite with its own installation and subscription terms; SGOKB does not bundle or silently install it.

Therefore:

```text
P-RUNTIME-01 = Complete / Accepted
P-RUNTIME-02 = Unblocked / Next
```

## Sequencing

```text
P-GUI-01..08 Complete / Accepted
        ↓
P-RAW-01..06 Complete / Accepted
        ↓
P-RUNTIME-01 Complete / Accepted
        ↓
P-RUNTIME-02   <- NEXT
        ↓
P-RUNTIME-03
        ↓
P-GUI-09
        ↓
P-RUNTIME-04..06 / P-GUI-10
        ↓
P-CLOSE-01
```

`P-GUI-09` depends on `P-RUNTIME-03`, so the reference runtime assets and shared health boundary must now advance before the remaining GUI workstream can continue.

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by release `v1.1.0` until Phase P closure/release integration.

P-GUI-01 through P-GUI-08, P-RAW-01 through P-RAW-06, and P-RUNTIME-01 are accepted development baselines. Runtime implementation assets are not yet accepted; P-RUNTIME-02 is the next task.

## Next

```text
P-RUNTIME-02 — Qdrant Compose / configuration assets
```
