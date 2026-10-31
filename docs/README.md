# SGOKB Documentation

`docs/` contains the current requirements, decisions, design, evaluation, operations, planning, release and historical material for Source Grounded Object Knowledge Base (SGOKB).

## Current status

```text
Phase A ... Phase O        = Complete
P-GUI-01..10               = Complete / Accepted
P-RAW-01..06               = Complete / Accepted
P-RUNTIME-01..06           = Complete / Accepted
P-CLOSE-01                 = Complete / Accepted
Phase P                    = Complete / Accepted
Current formal release     = v2.0.0
Project state              = Paused / no active implementation task
```

The annotated `v2.0.0` tag is frozen on release commit `1adae99ee62c3054a35b1325b8a43716943ff06a`. Later `main` changes may document the completed release without moving the tag.

## Start here

For the current system, read in this order:

1. [`design/SGOKB_CURRENT_ARCHITECTURE.md`](design/SGOKB_CURRENT_ARCHITECTURE.md) — integrated current architecture through Phase P.
2. [`requirements/RAW_GROUNDING_REQUIREMENTS.md`](requirements/RAW_GROUNDING_REQUIREMENTS.md) — Package v2 / Result v2 Raw-grounding requirements and `2.0.0` default.
3. [`operations/OBJECT_STANDARD_WORKFLOW.md`](operations/OBJECT_STANDARD_WORKFLOW.md) — normal Object -> Source -> Package -> Result -> Search workflow.
4. [`operations/OPERATIONAL_SAFETY_RECOVERY.md`](operations/OPERATIONAL_SAFETY_RECOVERY.md) — safety, backup, recovery and runtime handling.
5. [`evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md`](evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md) — completed Phase P release closure evidence.
6. [`releases/v2.0.0.md`](releases/v2.0.0.md) — formal `v2.0.0` Release Note.

## Phase P authority

Planning:

- [`planning/phases/P/PHASE_P_MODERNIZATION_PLAN.md`](planning/phases/P/PHASE_P_MODERNIZATION_PLAN.md)
- [`planning/phases/P/PHASE_P_TASKS.md`](planning/phases/P/PHASE_P_TASKS.md)
- [`planning/phases/P/PHASE_P_STATUS.md`](planning/phases/P/PHASE_P_STATUS.md)

GUI:

- [`requirements/GUI_REQUIREMENTS.md`](requirements/GUI_REQUIREMENTS.md)
- [`design/P_GUI_APPLICATION_ARCHITECTURE.md`](design/P_GUI_APPLICATION_ARCHITECTURE.md)
- [`evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md`](evaluation/P_GUI_10_PARITY_USABILITY_REGRESSION_ACCEPTANCE.md)

Raw Grounding:

- [`requirements/RAW_GROUNDING_REQUIREMENTS.md`](requirements/RAW_GROUNDING_REQUIREMENTS.md)
- [`design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`](design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md)
- [`design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`](design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md)
- [`design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`](design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md)
- [`evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md`](evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md)

Runtime:

- [`design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_CONTRACT.md`](design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_CONTRACT.md)
- [`planning/phases/P/P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`](planning/phases/P/P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md)
- [`evaluation/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md`](evaluation/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md)
- [`evaluation/P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_ACCEPTANCE.md`](evaluation/P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_ACCEPTANCE.md)

Closure / release:

- [`decisions/P_CLOSE_01_RELEASE_INTEGRATION_DECISION.md`](decisions/P_CLOSE_01_RELEASE_INTEGRATION_DECISION.md)
- [`evaluation/P_CLOSE_01_THIRD_PARTY_LICENSE_INVENTORY.md`](evaluation/P_CLOSE_01_THIRD_PARTY_LICENSE_INVENTORY.md)
- [`evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md`](evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md)
- [`decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md`](decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md)
- [`releases/README.md`](releases/README.md)

## Current architecture boundary

```text
Source / Snapshot / Raw / Evidence lineage
  -> Evidence-to-Raw resolution
  -> Raw-bearing Package v2
  -> external Human-in-the-loop analysis
  -> Result v2 raw_artifact grounding
  -> immutable accepted Object Knowledge Version
  -> rebuildable Search / Embedding / Qdrant / rendering
  -> CLI / PySide6 GUI / read-only MCP
```

The GUI and CLI share the Application/operator boundary. Qdrant lifecycle is external to SGOKB. MCP remains read-only and externally launched.

## Documentation authority rules

- Files under `docs/requirements/`, accepted `docs/decisions/`, current `docs/design/`, and accepted evaluation/operation contracts are active documentation.
- `docs/archive/` is historical and must not override current architecture.
- Phase-specific research documents remain evidence for their task but do not override later accepted integration decisions.
- Release notes describe frozen release boundaries. `releases/v2.0.0.md` is the formal Release Note for tag `v2.0.0`.

## Distribution note

The `v2.0.0` source/repository release includes the PySide6 GUI implementation. P-CLOSE-01 does not certify a standalone GUI binary distribution because project-license selection and artifact-specific Qt/PySide6 redistribution auditing remain separate future gates under P-GUI-02. They are not unfinished Phase P work.

## Project checkpoint

There is no active implementation task after Phase P / `v2.0.0`. The project is intentionally paused. When work resumes, current `main` is the documentation authority and `v2.0.0` is the immutable released baseline.
