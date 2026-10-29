# P-GUI-08 — Package / Result GUI Implementation

Status: **Complete / Accepted**

Date: 2026-10-30

## Scope

P-GUI-08 exposes the accepted Phase P Package v2 / Result v2 Raw-grounded external-AI workflow through the PySide6 desktop client without duplicating CLI business logic.

The GUI continues to submit canonical operations through the shared `ApplicationOperator` / `BackendCoordinator` boundary.

## Package GUI

The `Packages` page now provides:

- Object selection
- explicit Package contract selection
  - `v2 — Raw grounded (Phase P accepted)` is the first GUI selection
  - `v1 — Evidence grounded (legacy compatibility)` remains selectable
- manual Evidence include / exclude selection
- Evidence and Raw materialization budgets
- `package.build`
- Raw Artifact inclusion inspection
- Evidence -> Raw binding inspection
- Package binding / selection / materialization / integrity inspection
- `grounding_set_sha256` and manifest-integrity presentation
- `package.stage`
- destination-aware `package.preflight`
- stale-state invalidation when Package inputs or destination change
- explicit Raw-inclusion / preflight acknowledgement before `package.export`

The GUI sends an explicit `package_version`. This does **not** change the shared Application / CLI no-option default, which remains v1 until the P-CLOSE-01 release/default decision.

## Result GUI

The `Results` page now provides:

- external Result detection
- immutable Result receipt
- receipt list and pending-only list
- validation-state presentation
- forced revalidation control
- Result validation
- review against current Knowledge
- current Knowledge diff presentation
- Raw grounding reference diff presentation
- blocked / review-required / ready-to-import lifecycle presentation
- explicit acknowledgement when review-required changes are imported
- accepted Knowledge Version import

The Result GUI uses the same version-aware router used by the CLI/Application boundary. Result v2 remains Raw-grounded and does not synthesize Evidence claim links.

## Safety model

P-GUI-08 retains the P-GUI-07 operation-safety boundary:

- Package export remains an `EXTERNAL` operation.
- Result import remains a strong `WRITE` operation.
- request ownership, progress, error, partial-result, blocked-state, confirmation, and audit behavior continue to be handled by `OperationPage` / the shared worker boundary.
- changing Package build inputs invalidates the built/staged/preflight state.
- changing the export destination invalidates preflight acknowledgement.
- export is disabled until the current preflight is non-blocked and the operator explicitly acknowledges the reviewed Raw inclusion set.
- import is disabled until review is non-blocked; `review_required` additionally requires explicit acknowledgement.

## Architecture

Implemented GUI modules:

- `src/sgokb/gui/views/package_result_page.py`
- `src/sgokb/gui/views/package_result_detection.py`
- `src/sgokb/gui/views/main_window_package_result.py`
- amended `src/sgokb/gui/views/__init__.py`

Focused acceptance:

- `tests/test_p_gui_08_package_result.py`

The MainWindow amendment replaces the former Package / Result placeholders while delegating every other accepted page to the existing MainWindow implementation.

No CLI subprocess wrapper was introduced. Package / Result semantics remain owned by the shared Application layer.

## Automated end-to-end coverage

The focused acceptance performs a real SQLite-backed GUI round trip:

```text
Object / Source / Snapshot / Raw / Normalization Run / Evidence
  -> GUI Package v2 build
  -> Raw inclusion + Evidence->Raw presentation
  -> stage
  -> preflight
  -> acknowledged export
  -> external result.json
  -> GUI detect
  -> receive
  -> validate
  -> review
  -> Raw grounding diff
  -> import
  -> accepted Knowledge Version
```

The final DB assertions require:

```text
raw_grounding_links >= 1
evidence_links      == 0
```

for the imported Result v2 Version.

## Compatibility disposition

```text
GUI v2 Package selection = accepted Raw-grounded normal path
GUI v1 Package selection = supported legacy compatibility path
shared omitted-version default = v1, unchanged
v2 Result grounding = raw_artifact_id
v2 import persistence = raw_grounding_links
v2 Evidence claim-link synthesis = forbidden
```

P-GUI-08 therefore satisfies the task requirement that the accepted P-RAW Package / Result contract is fully displayable and operable from the GUI.
