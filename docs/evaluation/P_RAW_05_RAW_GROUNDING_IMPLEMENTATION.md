# P-RAW-05 — RAW Grounding Implementation

Updated: 2026-10-30

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-RAW-05 [P0] RAW Grounding implementation`
- Status: **Implementation Complete / Automated Verification Pending**
- Released baseline: `v1.1.0`
- Design authority:
  - `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`
  - `docs/design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`
  - `docs/design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`
- Next gate: focused regression + Ruff + full regression
- P-RAW-06 remains blocked until this implementation is verified.

## 1. Implementation disposition

P-RAW-05 implements the accepted Raw Grounding contracts as an **additive v2 path** rather than mutating the historical v1 exchange semantics.

Implemented flow:

```text
Evidence selection
  -> deterministic Evidence -> Raw resolver
  -> exact Raw-bearing Package v2
  -> stage / preflight / export + Raw audit
  -> Result v2 receive
  -> version-dispatched validation
  -> Raw-aware review / grounding diff
  -> version-dispatched import
  -> accepted Knowledge Version
  -> raw_grounding_links
  -> accepted read / Version diff
```

Legacy flow remains:

```text
Package v1 -> Result v1 -> evidence_links
```

No Result v2 import synthesizes Evidence claim grounding.

## 2. Database migration

Added:

```text
src/sgokb/migrations/019_raw_grounding_v2.sql
```

Additive tables:

```text
package_raw_grounding_metadata
package_raw_artifacts
package_evidence_raw_bindings
raw_grounding_links
```

The migration preserves existing `evidence_links` and v1 Package audit tables.

DB constraints/triggers enforce:

- Package Raw audit identity against canonical Raw/Snapshot/Source rows;
- Evidence -> Raw binding lineage against canonical Evidence provenance;
- claim-level Raw links only to Raw members of the originating Package;
- statement / attribute / relation target ownership by the same Version;
- `result_import` origin consistency;
- terminal accepted/abandoned Version immutability.

## 3. Evidence -> Raw resolver

Added:

```text
src/sgokb/exchange/raw_grounding.py
```

`EvidenceRawResolver` implements P-RAW-02 literally:

```text
Evidence
  -> its original Normalization Run
  -> every run input Raw Artifact
```

Rules implemented:

- run input rows use `normalization_run_artifacts.role = input`;
- exact Raw membership is sorted by `artifact_id`;
- payload identity is deduplicated only by exact `artifact_id`;
- every Evidence -> Raw binding is retained;
- Source/Snapshot/run lineage is rechecked;
- exact physical bytes are read and checked against canonical byte size and SHA-256;
- webcapture ZIP-backed Raw uses the canonical internal logical artifact bytes;
- directly-file-backed Raw is accepted only when the file itself matches canonical size/hash;
- no Evidence-Markdown fallback exists.

`SourceRepository` now exposes canonical Raw lookup and normalization-run input lookup used by the resolver.

## 4. Package v2 implementation

Added:

```text
src/sgokb/exchange/raw_package_builder.py
src/sgokb/exchange/package_manifest_v2.py
src/sgokb/exchange/package_transfer_v2.py
src/sgokb/exchange/instructions_v2.py
src/sgokb/exchange/schemas/object-evidence-package-v2.schema.json
```

Implemented identities:

```text
Package       = sgokb.object-evidence-package/2.0
Instructions  = sgokb.object-analysis/2.0
Result        = sgokb.object-result/2.0
Grounding     = sgokb.raw-grounding/1.0
Resolution    = sgokb.evidence-to-raw/1.0
```

Package v2 stores exact bytes at deterministic paths:

```text
raw/artifact_0001/payload
raw/artifact_0002/payload
...
```

The Package contains no reconstructed `evidence/source_*.md` semantic payload.

Implemented manifest properties include:

- Evidence selection membership and reasons;
- complete Evidence -> Raw bindings;
- canonical Raw identity / Source / Snapshot / metadata / size / SHA-256;
- `included_raw_artifact_ids` grounding membership authority;
- `grounding_set_sha256`;
- separate Raw materialization budget/usage;
- exhaustive `files[]` Raw inventory;
- standard export/preflight integrity and credential scanning.

Current Phase-P standard materialization profile is deliberately narrow:

```text
text/*
application/json
application/xml
```

A required unsupported media type blocks Package v2 rather than converting or dropping it. Broader real-media acceptance belongs to P-RAW-06 operational acceptance / policy refinement if required.

Current implementation defaults:

```text
max_total_raw_bytes  = 16 MiB
max_single_raw_bytes = 8 MiB
max_raw_artifacts    = 64
```

These are implementation defaults, not a redefinition of provenance.

## 5. v1/v2 Package dispatch

`PackageExchangeApplication` now dispatches build/stage/preflight/export by explicit Package version.

CLI adds:

```text
sgokb package build --package-version v1|v2
```

During the Phase-P compatibility period the CLI default remains `v1`, so existing scripts are not silently changed before P-RAW-06 acceptance.

`v2` must be explicitly selected for the new Raw boundary.

A current Version with accepted `raw_grounding_links` blocks a new legacy v1 Package build by default. This implements the accepted one-way current-Version migration direction:

```text
v1 current -> v2 update = supported
v2 current -> v1 update = blocked
```

## 6. Historical carry-forward

`PackageBuildReadRepository.current_grounding_selection_evidence_ids()` supports both grounding families.

For v1:

```text
accepted evidence_links -> carry-forward Evidence
```

For v2:

```text
accepted raw_grounding_links
  -> originating package_id / grounded Raw IDs
  -> package_evidence_raw_bindings
  -> Evidence bindings intersecting actually grounded Raw
  -> carry-forward selection Evidence
  -> original Evidence run -> Raw covering set
```

Recovered Evidence remains selection lineage only. It is not written as claim grounding for a v2 Version.

The legacy Package v1 `current_object.json` shape is preserved by default. Package v2 explicitly opts into Raw grounding fields in its update context.

## 7. Result v2 implementation

Added:

```text
src/sgokb/exchange/object_result_v2.py
src/sgokb/exchange/result_validation_v2.py
src/sgokb/exchange/result_validation_router.py
src/sgokb/exchange/schemas/object-result-v2.schema.json
```

Result v2 replaces `evidence[]` claim references with:

```json
{
  "grounding": [
    {
      "raw_artifact_id": "...",
      "role": "supports"
    }
  ]
}
```

Optional locator implementation:

```text
byte_range
text_quote
```

Validation checks:

- exact Result/Package/instructions binding;
- `grounding_contract` and `grounding_set_sha256`;
- exact audited Package Raw membership;
- canonical Raw existence and lineage;
- canonical/package byte size + SHA-256 agreement;
- staged payload integrity;
- byte-range bounds;
- text-quote charset/occurrence/optional prefix-suffix uniqueness;
- existing Class/Facet/Attribute/Relation, attribution, temporal, proposal, and stale-base rules.

Canonical Raw outside the exact bound Package remains invalid.

## 8. Review and diff

Added:

```text
src/sgokb/review/raw_diff.py
src/sgokb/review/router.py
```

For Result v2, review separates:

```text
Knowledge content diff
grounding diff
```

Grounding is stripped from the content comparison, then compared independently. This prevents a v1 Evidence-grounded -> v2 Raw-grounded migration from being mislabeled as destructive semantic deletion.

Accepted Version diff automatically selects the Raw-aware diff when either Version contains Raw grounding.

The existing Markdown renderer adds a `Grounding` section only when a Raw-aware report supplies that section; legacy v1 Markdown output does not gain the new section.

## 9. Import and accepted provenance

Added:

```text
src/sgokb/storage/result_import_repository_v2.py
src/sgokb/exchange/result_import_v2.py
src/sgokb/exchange/result_import_router.py
src/sgokb/storage/raw_grounding_repository.py
```

Result v2 reuses canonical Version / statement / Attribute / Relation creation semantics, but claim grounding dispatches to:

```text
raw_grounding_links
```

It does **not** create `evidence_links`.

Package Raw membership/audit and accepted claim grounding therefore remain separately queryable.

## 10. Accepted Knowledge reads

`ObjectKnowledgeReader` and `VersionReadApplication` are Raw-aware.

For Raw-grounded Versions:

- statement / Attribute / Relation payloads expose `grounding` references;
- v1-compatible `evidence` remains empty rather than fabricated;
- Object/Version read indicates Raw grounding when present;
- Version diff uses the Raw-aware content/grounding split.

For legacy v1 Versions, Raw-only fields are not emitted merely because the newer software is installed. This preserves the existing response shape where no Raw grounding exists.

## 11. Automated coverage added

Added focused implementation coverage:

```text
tests/test_p_raw_05_raw_grounding_v2.py
```

It covers:

1. Package v2 exact Raw payload and same-Raw multi-Evidence dedup;
2. Result v2 validate -> review -> import -> accepted Raw grounding read;
3. no `evidence_links` fabrication during v2 import;
4. Package-outside Raw rejection;
5. invalid locator rejection;
6. v2 accepted grounding -> historical carry-forward selection lineage;
7. v2 current -> v1 Package downgrade block.

The existing full regression suite remains the compatibility authority for Package/Result v1 and all unrelated system behavior.

## 12. Verification state

No local test execution is claimed by this implementation record.

Required gate:

```text
focused P-RAW/v1 exchange regression
Ruff src/tests
full pytest regression
```

Until those pass:

```text
P-RAW-05 = Implementation Complete / Automated Verification Pending
P-RAW-06 = Blocked
```

A failing gate reopens P-RAW-05; it must not be waived into P-RAW-06.
