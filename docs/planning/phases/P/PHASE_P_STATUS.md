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
| GUI | P-GUI-08 | **Not Started / Unblocked / Next** | Package / Result GUI against accepted v2 Raw boundary |
| GUI | P-GUI-09 | Not Started | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01 | **Complete / Accepted** | Current Evidence Package / Result impact survey |
| RAW | P-RAW-02 | **Complete / Accepted** | Deterministic Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03 | **Complete / Accepted** | Versioned RAW-bearing Package v2 design |
| RAW | P-RAW-04 | **Complete / Accepted** | Raw-grounded Object Result v2 design |
| RAW | P-RAW-05 | **Complete / Accepted** | Resolver -> Package v2 -> Result v2 -> Raw provenance implementation |
| RAW | P-RAW-06 | **Complete / Accepted** | Formal Raw operational acceptance, compatibility/cutover disposition, documentation closure |
| Runtime | P-RUNTIME-01..06 | Not Started | Windows Qdrant auto-start / health / GUI integration |
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

## P-GUI-01..07 accepted baseline

```text
P-GUI-01..03R = Complete / Accepted
P-GUI-04      = Complete / Accepted
P-GUI-05      = Complete / Accepted
P-GUI-06      = Complete / Accepted
P-GUI-07      = Complete / Accepted
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

Final GUI authority includes:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`
- `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`
- `docs/evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`

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
P-GUI-08 = Unblocked / Next
```

## Sequencing

```text
P-GUI-01..07 Complete / Accepted
        ↓
P-RAW-01..06 Complete / Accepted
        ↓
P-GUI-08 Package / Result GUI   <- NEXT
        ↓
P-GUI-09 / P-GUI-10 and Runtime dependencies
        ↓
P-CLOSE-01
```

`P-GUI-09` also depends on `P-RUNTIME-03`.

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by release `v1.1.0` until Phase P closure/release integration.

P-GUI-01 through P-GUI-07 and P-RAW-01 through P-RAW-06 are accepted development baselines. The Raw external-AI boundary is now formally accepted and no longer blocks Package / Result GUI work.

## Next

```text
P-GUI-08 — Package / Result GUI
```
