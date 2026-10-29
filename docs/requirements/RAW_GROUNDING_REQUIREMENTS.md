# RAW Grounding Requirements

更新日: 2026-10-30

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-RAW-06 [P0] RAW Grounding acceptance / compatibility / documentation`
- Status: **Accepted subject to P-RAW-06 final verification gate**
- Applies to: Package v2 / Result v2 external analysis boundary
- Design authorities:
  - `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`
  - `docs/design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`
  - `docs/design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`

## 1. Purpose

This document records the Phase P requirement baseline for external AI grounding after the migration from generated Evidence Markdown to exact Raw material.

Earlier requirements that describe Object Result grounding only in terms of Evidence IDs remain authoritative for the legacy Package v1 / Result v1 family. For Package v2 / Result v2, the requirements below supersede Evidence-only grounding assumptions.

## 2. External semantic authority

For Package v2, new semantic claims produced by external AI MUST be grounded only in Raw Artifacts that are members of the audited Package.

```text
semantic grounding authority
  = manifest.raw_grounding.included_raw_artifact_ids
```

`Evidence` remains selection and provenance lineage. It is not claim-level grounding authority in Result v2.

`current_object.json`, when present, represents the accepted base Knowledge Version. It is update context, not a substitute for new Raw evidence.

The external analysis path MUST NOT require the AI to invent or reconstruct an Evidence ID merely because the system internally used Evidence to select Raw inputs.

## 3. Deterministic Evidence -> Raw resolution

For each selected or protected Evidence item, SGOKB MUST resolve the complete input Raw Artifact set of that Evidence's own Normalization Run.

Required behavior:

1. follow `Evidence -> Normalization Run -> normalization_run_artifacts`;
2. include all run-input Raw Artifacts;
3. preserve the exact historical Snapshot / Source generation;
4. deduplicate repeated inclusion of the same `raw_artifact_id` at Package payload level;
5. preserve every Evidence -> Raw lineage edge;
6. never collapse distinct Raw Artifact IDs merely because byte content or SHA-256 is identical;
7. never narrow the covering set by artifact kind, path, media type, filename or content heuristic;
8. fail closed when provenance is missing or inconsistent.

## 4. Exact Raw material requirement

A Package v2 Raw payload MUST be the exact canonical bytes identified by the Raw Artifact record.

Before materialization or export, SGOKB MUST verify at least:

- physical bytes are resolvable;
- byte size matches canonical metadata;
- SHA-256 matches canonical metadata;
- Snapshot / Source provenance matches the selected Evidence generation.

Raw payloads MUST NOT be normalized, summarized, truncated, rewritten, converted to Evidence Markdown, or silently replaced by a newer effective generation.

## 5. Package v2 requirements

Package v2 MUST use:

```text
schema            = sgokb.object-evidence-package/2.0
instructions      = sgokb.object-analysis/2.0
expected Result   = sgokb.object-result/2.0
grounding         = sgokb.raw-grounding/1.0
resolver          = sgokb.evidence-to-raw/1.0
```

Required package properties:

- exact Raw payloads live under deterministic safe Package paths;
- local storage paths are not exported;
- `files[]` is the exhaustive transport/hash inventory;
- Raw membership is explicit and ordered;
- `grounding_set_sha256` binds the Raw grounding set;
- `manifest_sha256` binds the Package instance;
- Evidence metadata remains available for selection/provenance traceability;
- no generated `evidence/source_*.md` semantic payload is required or authoritative;
- materialization budget is separate from Evidence-selection budget;
- unsupported media, size/count overflow, unsafe layout, credential findings, hash mismatch, missing files or destination collision block egress rather than altering provenance.

## 6. Result v2 grounding requirements

Every claim-level grounding reference in Result v2 MUST use `raw_artifact_id` and MUST refer to a member of the audited Package Raw set.

Allowed baseline locator forms are:

- `byte_range`: zero-based half-open byte interval over the exact Raw bytes;
- `text_quote`: exact decoded text with optional prefix/suffix disambiguation.

A producer MAY omit a locator when exact precision cannot be justified. A producer MUST NOT provide a fabricated locator. An asserted locator that cannot be mechanically verified is invalid.

Result v2 MUST bind to both:

- Package `manifest_sha256`;
- Package `grounding_set_sha256`.

## 7. Validation and import requirements

Validation MUST fail closed for at least:

- Raw Artifact outside Package membership;
- Raw provenance mismatch;
- Package audit membership mismatch;
- Raw payload size/hash mismatch;
- grounding-set fingerprint mismatch;
- invalid Raw locator;
- stale Package/base-version binding;
- invalid Result v2 schema or Registry reference.

On successful Result v2 import:

```text
claim grounding -> raw_grounding_links
```

SGOKB MUST NOT synthesize `evidence_links` by reverse-mapping Raw references through Package Evidence selection metadata.

Accepted Object/Version reads MUST expose Raw grounding as Raw grounding and MUST preserve Evidence selection lineage separately.

## 8. Compatibility requirements

The supported compatibility direction is:

```text
Package v1 / Result v1             = retained legacy compatibility family
v1 accepted Version -> v2 update   = supported
v2 accepted Version -> v1 update   = blocked by default
v2 Result -> evidence_links         = forbidden synthesis
```

Historical v1 artifacts remain interpretable under the v1 contract. They MUST NOT be silently reinterpreted as v2.

Historical Raw-grounded accepted Knowledge must recover carry-forward Evidence only as selection lineage, then resolve that Evidence through its original run. This recovery does not convert Evidence into claim grounding.

## 9. Operational requirement after P-RAW-06

For Phase P development operations, Raw-grounded analysis MUST be requested explicitly with:

```text
sgokb package build --object <OBJECT_ID> --package-version v2
```

The no-option CLI/Application default remains `v1` during the unreleased Phase P integration window as an explicit backward-compatibility safeguard. This default is not permission to use v1 for a new Raw-grounded acceptance flow. Final release-default disposition is deferred to `P-CLOSE-01`.

## 10. Acceptance requirement

P-RAW-06 is complete only when one automated acceptance gate demonstrates all of the following on the reference Windows semantics:

- deterministic Raw resolution;
- same-ID dedup and distinct-ID preservation even with identical hashes;
- missing/modified Raw fail-closed behavior;
- Package manifest/file integrity and egress safety;
- Result membership and grounding-set validation;
- v1 -> v2 supported transition and v2 -> v1 downgrade rejection;
- Package v2 -> external-result simulation -> validate -> review -> import end-to-end;
- accepted provenance stored only as Raw grounding for the v2 claim path;
- legacy exchange regression and full repository regression remain green.
