# P-RAW-06 — Raw Grounding Compatibility / Cutover Decision

Updated: 2026-10-30

- Task: `P-RAW-06 [P0] RAW Grounding acceptance / compatibility / documentation`
- Decision status: **Accepted subject to final P-RAW-06 verification gate**

## Decision

SGOKB accepts Package v2 / Result v2 as the Phase P Raw-grounded external AI boundary.

The accepted contract is:

```text
Package v2  -> exact Raw payloads
Result v2   -> raw_artifact_id grounding
Import v2   -> raw_grounding_links
```

Evidence remains internal selection/provenance lineage and is not emitted by the AI as claim grounding in Result v2.

## Compatibility matrix

| Current / input state | Next operation | Disposition |
|---|---|---|
| no current Version | explicit Package v1 | supported legacy path |
| no current Version | Package v2 | supported / Raw-grounded path |
| v1 accepted Version | Package v1 update | supported legacy path |
| v1 accepted Version | Package v2 update | **supported migration path** |
| v2 accepted Version | Package v2 update | **supported normal Raw path** |
| v2 accepted Version | Package v1 update | **blocked by default** |
| Result v1 | v1 Package audit | version-routed validation/import |
| Result v2 | v2 Package audit | version-routed validation/import |
| Result v2 Raw reference | synthesize Evidence claim link | **forbidden** |

## CLI / Application default disposition

P-RAW-06 does **not** silently change the no-option package default during the unreleased Phase P integration window.

```text
PackageExchangeApplication.build(... package_version omitted) = v1
sgokb package build ... --package-version omitted             = v1
```

Reason:

1. `v1.1.0` remains the current released baseline while Phase P is incomplete;
2. changing the no-option behavior before P-GUI-08 and P-CLOSE-01 would alter existing automation without a release boundary;
3. version routing already allows Raw-grounded operation to be selected explicitly and safely;
4. the accepted Raw workflow can therefore advance without creating a hidden compatibility break.

For all Phase P Raw-grounded operational acceptance and new Raw-grounded external analysis, the required command is explicit:

```powershell
sgokb --db $Db package build --object $ObjectId --package-version v2
```

`P-CLOSE-01` owns the final release-default decision. It may change the default only with release notes, CLI compatibility review, regression coverage, and updated operator documentation.

## Why v2 -> v1 is blocked

Once current accepted Knowledge contains Raw claim grounding, a legacy v1 Package cannot faithfully serialize that claim-grounding model without either losing provenance or inventing Evidence grounding.

Therefore SGOKB fails closed rather than performing an implicit downgrade.

## Carry-forward rule

For a v2 current Version, Package v2 may recover historical Evidence only as selection lineage by reopening the originating Package Evidence->Raw bindings. The recovered Evidence is resolved through its original Normalization Run.

This rule preserves historical Raw provenance while keeping the following distinction intact:

```text
Evidence = selection/provenance lineage
Raw      = claim grounding authority
```

## Acceptance authority

This decision becomes final when `docs/evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md` records a PASS for:

- P-RAW-06 focused acceptance tests;
- P-RAW/v1 compatibility regression;
- Ruff;
- full repository regression.
