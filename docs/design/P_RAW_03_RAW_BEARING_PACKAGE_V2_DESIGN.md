# P-RAW-03 — RAW-bearing Package v2 Design

Updated: 2026-10-30

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-RAW-03 [P0] RAW-bearing Package v2 design`
- Status: **Complete / Accepted**
- Released baseline: `v1.1.0`
- Depends on:
  - `P-RAW-01 — Current Evidence Package / Result impact survey`
  - `P-RAW-02 — Evidence -> Raw Artifact provenance resolution contract`
- Scope: Package v2 design only; no runtime implementation, DB migration, or Result v2 grounding schema implementation in this task
- Next: `P-RAW-04 — Raw-grounded Object Result v2 design`

## 1. Purpose

P-RAW-03 defines the versioned Object Evidence Package contract that carries the **exact Raw Artifact bytes** resolved from operator-selected Evidence under P-RAW-02.

The v2 boundary is:

```text
Evidence retrieval / operator selection
        ↓
selected / protected Evidence
        ↓ P-RAW-02
Evidence -> original Normalization Run -> ALL run input Raw Artifacts
        ↓
verify canonical lineage / physical byte size / SHA-256
        ↓
RAW-bearing Object Evidence Package v2
        ↓ explicit preflight / egress
External AI
```

Evidence remains the retrieval and human-selection unit. It is **not** the authoritative external semantic payload in Package v2.

Package v2 must answer, without inference:

```text
Which Evidence decisions selected this material?
Which exact Raw Artifact identities were required by those decisions?
Which exact bytes were exported?
Which Source / Snapshot / Normalization Run produced each binding?
Was the complete P-RAW-02 Raw Input Covering Set included?
Did the exported bytes still match canonical size/hash metadata?
```

This task does not define the final statement/attribute/relation grounding JSON emitted by the external AI. P-RAW-04 owns that contract.

---

## 2. Existing v1 contract being versioned

Current Package v1 is:

```text
schema_version = sgokb.object-evidence-package/1.0
schema ID      = urn:sgokb:schema:object-evidence-package:1.0
instructions   = sgokb.object-analysis/1.1
Result schema  = sgokb.object-result/1.0
```

Its semantic payload is reconstructed Markdown:

```text
manifest.json
instructions.md
schema/object-result-v1.schema.json
current_object.json              # update Package only
evidence/source_*.md             # authoritative external source material in v1
```

The v1 manifest binds Evidence items to Source / Snapshot / Normalization Run and to the generated `evidence/source_*.md` files. `included_evidence_ids` is therefore both selection membership and the grounding-membership authority.

P-RAW-01 determined that this meaning cannot be changed in place.

Required rule:

```text
v1 remains Evidence-grounded
v2 is Raw-grounded
schema version determines semantics
```

---

## 3. Package v2 version identities

Package v2 reserves and freezes these identities:

```text
PACKAGE_SCHEMA_VERSION = sgokb.object-evidence-package/2.0
PACKAGE_SCHEMA_ID      = urn:sgokb:schema:object-evidence-package:2.0
manifest schema file   = object-evidence-package-v2.schema.json
instructions version   = sgokb.object-analysis/2.0
expected Result        = sgokb.object-result/2.0
Result schema snapshot = schema/object-result-v2.schema.json
```

`sgokb.object-result/2.0` is reserved here only because the Package must bind the expected Result family. P-RAW-04 defines its grounding representation and complete JSON Schema.

Package v1 constants, schema, instructions and behavior remain immutable compatibility contracts. A v2 implementation must add explicit version dispatch rather than changing the meaning of the v1 parser/builder.

There is no in-place v1 -> v2 relabel operation.

---

## 4. Package v2 semantic roles

Package v2 separates four concepts that v1 partially conflates.

### 4.1 Selection intent

Evidence records why material was selected:

- retrieval;
- manual include;
- carry-forward protection;
- source diversity / relevance metadata.

Evidence content is not recopied into Package v2 as authoritative Markdown.

### 4.2 Grounding material

The authoritative external source material is the exact Raw Artifact byte set resolved by P-RAW-02.

```text
Raw grounding membership authority
    = manifest.raw_grounding.included_raw_artifact_ids
```

A Raw Artifact is groundable only when it is a member of the exact bound Package.

### 4.3 Analysis control/context

The following Package files remain analysis controls or update context, not external source grounding material:

- `instructions.md`;
- Result JSON Schema snapshot;
- `current_object.json` for update Packages;
- `manifest.json` itself.

`current_object.json` represents the previously accepted state used for full-snapshot update semantics. It does not authorize new factual claims without v2 grounding material.

### 4.4 Transport inventory

`files[]` remains the exhaustive transport/integrity inventory for every Package file other than `manifest.json` itself.

Raw grounding identity is carried by `raw_grounding`; `files[]` describes the bytes physically present in the Package.

---

## 5. Package v2 physical layout

Baseline layout:

```text
<package-root>/
├─ manifest.json
├─ instructions.md
├─ current_object.json                    # update Package only
├─ schema/
│  └─ object-result-v2.schema.json
└─ raw/
   ├─ artifact_0001/
   │  └─ payload
   ├─ artifact_0002/
   │  └─ payload
   └─ ...
```

### 5.1 No reconstructed Evidence payload

Package v2 MUST NOT contain `evidence/source_*.md` as source material.

There is no fallback such as:

```text
Raw missing/unsupported -> generate Evidence Markdown instead
```

If required Raw cannot be packaged, the v2 operation is blocked.

### 5.2 Deterministic Raw package paths

The physical Package path is not a canonical Raw identity and does not reuse untrusted `logical_path` directly.

Path allocation is deterministic:

1. deduplicate required Raw membership by exact `artifact_id`;
2. sort unique Raw Artifacts by `artifact_id` using ordinal string order;
3. assign a one-based, zero-padded sequence;
4. use `raw/artifact_NNNN/payload`.

Example:

```text
raw/artifact_0001/payload
raw/artifact_0002/payload
```

The original `logical_path`, media type and charset remain manifest metadata. They do not control the Package filesystem path.

This prevents path traversal, absolute-path leakage, filename collision and platform-specific separator behavior from becoming part of the external Package contract.

### 5.3 Exact byte copy

`raw/.../payload` is an exact byte-for-byte copy of the canonical Raw Artifact identified in the manifest.

Package v2 baseline does not:

- normalize line endings;
- transcode charset;
- rewrite HTML;
- extract archives;
- OCR documents;
- convert PDF/images to text;
- strip metadata;
- concatenate Raw files;
- truncate Raw bytes.

A future derived representation may be designed separately, but it must never be mislabeled as the canonical Raw Artifact.

### 5.4 Auxiliary semantic files

Baseline Package v2 has **no auxiliary semantic representation** of Raw material.

Same-Snapshot artifacts that were not Normalization Run inputs remain excluded by P-RAW-02. Generated conversions/extractions are also excluded unless a future versioned contract explicitly introduces them.

This keeps the statement "the external AI received these Raw Artifacts" mechanically true.

---

## 6. Manifest v2 top-level contract

Package v2 preserves the useful v1 structure while separating Evidence selection from Raw grounding.

Conceptual top-level shape:

```json
{
  "schema_version": "sgokb.object-evidence-package/2.0",
  "package_id": "pkg_...",
  "created_at": "...",
  "extracted_at": "...",
  "target": {},
  "binding": {},
  "artifacts": {},
  "evidence": {},
  "raw_grounding": {},
  "selection": {},
  "materialization": {},
  "files": [],
  "warnings": [],
  "export_preflight": {},
  "integrity": {}
}
```

All JSON objects use `additionalProperties: false` unless a later P-RAW-04 field explicitly requires an extension point.

---

## 7. Binding and singleton artifacts

### 7.1 `binding`

Required v2 binding:

```json
{
  "base_version_id": null,
  "expected_result_schema_version": "sgokb.object-result/2.0",
  "instructions_version": "sgokb.object-analysis/2.0",
  "grounding_contract": "sgokb.raw-grounding/1.0"
}
```

`grounding_contract` identifies the semantic meaning of Package Raw membership independently from the outer Package schema.

### 7.2 `artifacts`

```json
{
  "instructions_path": "instructions.md",
  "result_schema_path": "schema/object-result-v2.schema.json",
  "current_object_path": null
}
```

Rules remain:

```text
initial Package -> base_version_id = null and current_object_path = null
update Package  -> base_version_id != null and current_object_path = current_object.json
```

The v2 Result schema snapshot must exactly match the installed canonical v2 Result schema when the Package is built/staged. P-RAW-04 provides that canonical schema.

---

## 8. Evidence selection section

`evidence` remains required because it captures the operator/retrieval decision that caused Raw material to enter the Package.

Conceptual shape:

```json
{
  "included_source_ids": ["..."],
  "included_evidence_ids": ["..."],
  "items": [
    {
      "evidence_id": "...",
      "source_id": "...",
      "snapshot_id": "...",
      "normalization_run_id": "...",
      "selected_by": "protected",
      "package_roles": ["carry_forward"],
      "retrieval_reasons": ["manual"],
      "related_selected_evidence_ids": []
    }
  ]
}
```

The v1 `file_path` field is removed from Evidence items because v2 has no generated Evidence Markdown file.

The v1 `source_generations[].file_path` model is also removed. Exact Source/Snapshot/run lineage is retained in Evidence items and the direct Evidence -> Raw bindings described below.

`included_evidence_ids` remains authoritative for **selection membership only**. It is not the v2 grounding membership authority.

---

## 9. Raw grounding section

`raw_grounding` is the authoritative Package v2 grounding-membership structure.

Conceptual shape:

```json
{
  "resolution_contract": "sgokb.evidence-to-raw/1.0",
  "included_raw_artifact_ids": ["raw-a", "raw-b"],
  "artifacts": [
    {
      "raw_artifact_id": "raw-a",
      "source_id": "source-a",
      "snapshot_id": "snapshot-a",
      "artifact_kind": "...",
      "package_path": "raw/artifact_0001/payload",
      "logical_path": "original/path/name.ext",
      "media_type": "...",
      "charset": null,
      "byte_size": 1234,
      "sha256": "..."
    }
  ],
  "evidence_bindings": [
    {
      "evidence_id": "evidence-a",
      "source_id": "source-a",
      "snapshot_id": "snapshot-a",
      "normalization_run_id": "run-a",
      "raw_artifact_ids": ["raw-a", "raw-b"]
    }
  ],
  "integrity": {
    "hash_algorithm": "sha256",
    "canonicalization": "sgokb-json-c14n-v1",
    "grounding_set_sha256": "..."
  }
}
```

### 9.1 Artifact entry semantics

Each `raw_grounding.artifacts[]` entry records the canonical identity and verified egress metadata for one distinct Raw Artifact:

```text
raw_artifact_id  canonical identity
source_id        verified Source via Snapshot lineage
snapshot_id      canonical Snapshot identity
artifact_kind    canonical capture/import kind
package_path     deterministic Package-local payload path
logical_path     canonical descriptive logical path; never used as Package path
media_type       canonical media type
charset          canonical charset or null
byte_size        canonical byte size, reverified from physical bytes
sha256           canonical SHA-256, reverified from physical bytes
```

`storage_path` / local filesystem path is intentionally **not exported**. It is local infrastructure metadata and can leak workstation layout. The Package records only Package-relative `package_path` plus semantic `logical_path`.

### 9.2 Evidence -> Raw binding semantics

For every selected Evidence there is exactly one `evidence_bindings[]` item.

Its `raw_artifact_ids` MUST equal the complete P-RAW-02 Raw Input Covering Set for that Evidence's own Normalization Run.

No subset is allowed.

Two Evidence items may map to the same Raw Artifact. In that case:

```text
Raw payload file count = 1
Raw artifact entry count = 1
Evidence -> Raw edges = retained for both Evidence items
```

Distinct Raw Artifact IDs MUST remain distinct entries even when their SHA-256 values are equal.

### 9.3 Required cross-field invariants

Manifest validation must enforce at least:

1. `evidence.items[].evidence_id` exactly matches `included_evidence_ids` membership;
2. every Evidence item has exactly one Evidence binding;
3. every Evidence binding refers to an Evidence in the Package;
4. binding Source/Snapshot/run matches the corresponding Evidence item;
5. every `raw_artifact_id` in a binding exists in `raw_grounding.artifacts`;
6. every `raw_grounding.artifacts` item is referenced by at least one selected Evidence binding;
7. `included_raw_artifact_ids` exactly matches `raw_grounding.artifacts[].raw_artifact_id` in canonical order;
8. each Raw `package_path` is unique and safe;
9. each Raw `package_path` has exactly one matching `files[]` entry with role `raw_grounding`;
10. Raw media type, size and SHA-256 in `files[]` exactly match the Raw artifact entry;
11. the complete resolved covering set is present for every Evidence;
12. a Raw Artifact from a different Snapshot/Source generation cannot be substituted merely because bytes or hashes match.

The complete-covering-set check requires canonical Repository access during build/validation; JSON Schema alone cannot prove it.

---

## 10. Deterministic ordering

To make diffs, testing and material fingerprinting stable, v2 canonical ordering is:

```text
evidence.items                    = selected Evidence order from the deterministic selector
included_evidence_ids             = exact evidence.items order
included_source_ids               = first-seen Source order from evidence.items
raw_grounding.artifacts           = ascending raw_artifact_id
included_raw_artifact_ids         = exact raw_grounding.artifacts order
evidence_bindings                 = evidence.items order
binding.raw_artifact_ids          = ascending raw_artifact_id
files singleton controls          = instructions, current_object if present, result_schema
files Raw entries                 = ascending raw_artifact_id
warnings                          = deterministic producer order/code order
```

Package ID and timestamps remain intentionally unique/time-dependent. Deterministic ordering does not require two independently built Package directories to have the same `manifest_sha256`.

---

## 11. Selection budget vs Raw materialization budget

Package v2 separates two different limits.

### 11.1 Evidence selection budget

The existing Evidence selection budget remains an upstream retrieval-control mechanism:

```text
max_estimated_tokens
max_bytes
max_items
```

Its usage describes Evidence candidate/selection material, not exported Raw byte volume.

This budget still answers:

```text
Which Evidence should be selected?
```

### 11.2 Raw materialization budget

After P-RAW-02 resolution and `artifact_id` deduplication, v2 applies a separate Raw materialization budget over exact Raw bytes.

Required conceptual fields:

```json
{
  "budget": {
    "max_total_raw_bytes": 0,
    "max_single_raw_bytes": 0,
    "max_raw_artifacts": 0
  },
  "usage": {
    "total_raw_bytes": 0,
    "largest_raw_bytes": 0,
    "raw_artifact_count": 0,
    "selected_evidence_count": 0,
    "source_count": 0
  },
  "policy_profile": "..."
}
```

The numeric values above are shape examples only. P-RAW-05 selects implementation defaults/configuration after operational testing; they are not fixed by this document.

Budget accounting rules:

- Raw bytes/count are charged once per unique `artifact_id` physically included;
- duplicate Evidence -> Raw edges do not duplicate byte charges;
- same-hash but distinct artifact IDs remain distinct and are each charged;
- control files (`instructions`, schema, current object, manifest) are reported in total Package size but not in `total_raw_bytes`;
- no Raw artifact may be truncated to satisfy a budget;
- no required Raw artifact may be dropped to satisfy a budget.

If the P-RAW-02 covering set exceeds a Raw materialization limit:

```text
resolution = valid
Package materialization = BLOCKED
```

The operator must change the Evidence selection or explicit configured limit and rebuild. The builder must not silently mutate provenance.

---

## 12. Media and analysis-capability policy

Exact Raw bytes may include HTML, JSON, text, PDF, images, archives or other capture formats. Consumer capability varies.

Package v2 therefore records a `materialization.policy_profile` used to decide whether every required Raw item is eligible for the intended external-analysis path.

Rules:

1. media eligibility is a **Package/materialization policy**, not provenance selection;
2. unsupported required media blocks the v2 Package for that profile;
3. unsupported Raw is never replaced by Evidence Markdown;
4. unsupported Raw is never silently converted into another file under the same Raw identity;
5. the exact allow/review/block media profile is implementation/configuration data to be fixed in P-RAW-05 and recorded in the manifest/build audit;
6. a future conversion layer requires a separately identified derived representation contract.

`media_type` metadata does not override physical integrity. A misleading media-type declaration cannot justify changing or dropping Raw bytes.

---

## 13. Preflight / External Egress contract

P-RAW-03 preserves the existing explicit `build -> stage -> preflight -> export` safety principle and expands preflight coverage to Raw material.

### 13.1 Required checks before a Package becomes exportable

For every provenance-required Raw Artifact:

```text
canonical Raw row exists
canonical Snapshot exists
Snapshot belongs to expected Source
Raw belongs to expected Snapshot
Normalization Run binding is valid
physical storage object exists
not a symlink/path escape where filesystem-backed
actual byte_size == canonical byte_size
actual SHA-256 == canonical sha256
media policy permits analysis
single-item and aggregate size budgets pass
credential/secret policy passes
Package path is safe
staged bytes still match declared size/hash
```

The Package as a whole additionally requires:

```text
manifest schema/semantic validation
all declared files present
no undeclared files
Result schema snapshot matches canonical v2 schema
instructions version matches v2 contract
manifest hash valid
grounding_set_sha256 valid
current_object presence matches base_version binding
```

### 13.2 Credential / secret policy

Raw artifacts can contain more information than extracted Evidence. Standard v2 egress therefore applies secret/credential checks to **all exported Raw bytes**, not only text synthesized by SGOKB.

At minimum, detected private-key material or known credential/token forms are blocking findings for standard export.

Opaque/container material that cannot be adequately inspected must not be treated as "clean" merely because scanning was impossible. The selected materialization policy must classify such cases explicitly as allowed, review-required, or blocked; absence of scanner coverage is itself reportable.

### 13.3 No integrity override

User acknowledgement may satisfy a `review_required` policy warning where explicitly supported.

It must never override:

- missing provenance;
- missing Raw bytes;
- Snapshot/Source mismatch;
- byte-size mismatch;
- SHA-256 mismatch;
- unsafe package path/layout;
- incomplete Raw covering set;
- detected credential material where the standard policy says blocked.

### 13.4 External Egress summary

Before export, CLI/GUI must be able to show at least:

```text
Package ID
Object ID/name
Package schema version
selected Evidence count
unique Raw Artifact count
Source count
total Raw bytes
total Package bytes
Raw media-type summary
review/block warnings
credential/secret findings
external destination
```

P-GUI-08 consumes this contract rather than inventing a GUI-only egress interpretation.

---

## 14. `files[]` transport inventory

Package v2 extends the file role set:

```text
instructions
current_object
result_schema
raw_grounding
```

There is no v2 `evidence` file role.

Every Raw payload has a `files[]` entry:

```json
{
  "path": "raw/artifact_0001/payload",
  "role": "raw_grounding",
  "media_type": "text/html",
  "size_bytes": 1234,
  "sha256": "..."
}
```

Unlike v1, `files[].media_type` cannot be limited to Markdown/JSON because Raw media is heterogeneous. It remains a non-empty media-type string subject to semantic validation and the selected materialization policy.

The generic file entry and the corresponding Raw artifact entry must agree exactly on path, media type, byte size and hash.

---

## 15. Integrity and reproducibility

Package v2 retains two different integrity identities.

### 15.1 Manifest integrity

The existing canonical JSON profile is retained:

```text
hash_algorithm   = sha256
canonicalization = sgokb-json-c14n-v1
manifest_sha256  = SHA-256(canonical manifest projection excluding manifest_sha256)
```

Because Package ID and timestamps are included in the manifest, this digest identifies one exact Package instance.

### 15.2 Stable Raw grounding-set fingerprint

Package v2 adds:

```text
raw_grounding.integrity.grounding_set_sha256
```

It is computed from the canonical JSON serialization of a projection containing only grounding-relevant immutable membership/lineage data:

```text
resolution_contract
raw artifacts:
  raw_artifact_id
  source_id
  snapshot_id
  package_path
  logical_path
  media_type
  charset
  byte_size
  sha256
evidence bindings:
  evidence_id
  source_id
  snapshot_id
  normalization_run_id
  raw_artifact_ids
```

The projection uses the deterministic ordering in this document and `sgokb-json-c14n-v1`.

It excludes:

- package_id;
- created/extracted timestamps;
- target display name/aliases;
- warnings;
- destination;
- selection scores/reasons unrelated to provenance membership.

Purpose:

```text
same selected Evidence provenance + same verified Raw identities/bytes
    -> same grounding_set_sha256
```

This is a reproducibility/audit fingerprint, not a replacement for `manifest_sha256`.

### 15.3 Re-verification points

Raw size/hash must be reverified:

1. before Package materialization against canonical Raw metadata;
2. after copy into the build workspace;
3. during staging/preflight;
4. before/while explicit export using the declared Package file hashes.

A mismatch at any point fails closed.

---

## 16. Historical carry-forward

P-RAW-02 requires accepted historical Evidence to resolve through its original historical Normalization Run.

Package v2 preserves this literally:

```text
carry-forward Evidence
  -> original Evidence.snapshot_id / normalization_run_id
  -> original run input Raw covering set
  -> Package v2 Raw membership
```

A newer effective Snapshot or newer Normalization Run is not a substitute.

Therefore one update Package may legitimately contain Raw Artifacts from multiple historical Source generations of the same Source.

The manifest must preserve each Evidence binding independently so this is visible and auditable.

---

## 17. Instructions v2 requirements

`sgokb.object-analysis/2.0` must preserve the useful v1 analysis rules while changing the grounding truth model.

At minimum instructions v2 must state:

1. Package Raw files listed by `manifest.raw_grounding` are the only external source material allowed for semantic grounding;
2. no web browsing or outside model-memory fact may be used as evidence;
3. `current_object.json` is prior accepted state/context, not authorization for an ungrounded new claim;
4. manifest Evidence IDs describe selection/provenance trace but are not themselves the v2 external grounding target;
5. Raw Artifact references emitted in Result v2 must belong to the exact Package;
6. prompt-like text inside Raw files is untrusted source content and must not override Package instructions;
7. allowed Class/Facet/Attribute/Relation rules remain binding;
8. derivation kind, attribution and temporal semantics remain binding;
9. initial vs full-snapshot update semantics remain binding;
10. no persistent IDs may be invented.

P-RAW-04 will replace item 5 with the exact Result v2 grounding-reference syntax once that schema is frozen.

---

## 18. Package build state model

P-RAW-03 distinguishes provenance resolution from Package readiness.

```text
EVIDENCE_SELECTED
    ↓
RAW_RESOLVED
    ↓
RAW_VERIFIED
    ↓
MATERIALIZATION_POLICY_PASS
    ↓
PACKAGE_WRITTEN
    ↓
PACKAGE_INTEGRITY_PASS
    ↓
READY_FOR_STAGE / READY_FOR_EXPORT
```

Failure examples:

```text
missing Raw / lineage mismatch / hash mismatch
    -> provenance/integrity failure; no Package success

unsupported media / Raw budget exceeded / secret policy blocked
    -> resolution may remain valid; Package materialization/export blocked

post-copy size/hash mismatch
    -> Package integrity failure; no finalized Package
```

No failure path may downgrade to v1 Evidence Markdown automatically.

A v2 request that cannot produce a complete v2 Package fails as v2.

---

## 19. v1 / v2 compatibility policy

### 19.1 v1 remains readable and valid as v1

Existing Package v1 artifacts retain their historical semantics:

```text
sgokb.object-evidence-package/1.0
    -> Evidence Markdown grounding
    -> sgokb.object-result/1.0
```

They are not migrated merely by reading them with newer software.

### 19.2 v2 is explicitly dispatched

```text
sgokb.object-evidence-package/2.0
    -> Raw grounding
    -> sgokb.object-result/2.0
```

Builder, validator, stage/preflight, receipt validation and audit must dispatch from explicit schema version.

Unknown Package major versions fail closed.

### 19.3 No semantic fallback

The following are prohibited:

```text
v2 Raw resolution fails -> silently build v1
v2 unsupported media -> silently emit Evidence Markdown
v1 Package -> reinterpret included_evidence_ids as Raw grounding
v2 Package -> validate Result with v1 Evidence-membership semantics
```

If an operator explicitly requests legacy v1 generation during a documented compatibility period, that is a separate explicit operation/mode and the resulting artifact remains v1.

P-RAW-05 decides the operator/API switch and support period. P-RAW-06 tests both version routes where retained.

---

## 20. Exchange audit requirements for implementation

P-RAW-05 must extend logical Package audit capability so an exported v2 Package can later answer:

```text
package schema/version
package_id + manifest_sha256
grounding_set_sha256
selected Evidence IDs
included Raw Artifact IDs
Evidence -> Raw bindings
Raw artifact hashes / byte sizes / package paths
Source / Snapshot / Normalization Run lineage
preflight disposition / warnings
export destination / time
```

P-RAW-03 does not choose physical tables. P-RAW-04/05 may introduce new Raw-grounding persistence/audit structures rather than overloading Evidence-only rows.

---

## 21. Validation responsibility split

### JSON Schema can validate

- required fields and types;
- fixed version identities;
- path/media/hash syntax;
- uniqueness constraints where expressible;
- allowed role/enumeration values;
- basic structural shape.

### Semantic validator must validate

- exact Evidence membership/order invariants;
- Evidence item <-> Evidence binding identity;
- Raw binding membership;
- file inventory <-> Raw entry equality;
- initial/update current-object rule;
- manifest and grounding-set digests;
- deterministic path allocation;
- no orphan Raw entries;
- no incomplete covering set;
- canonical Source/Snapshot/run/Raw lineage when Repository access is available;
- physical Raw size/hash before materialization/egress.

### Transfer preflight must validate

- actual directory/file scope;
- no symlinks/path escape;
- staged/exported file size/hash;
- credential/secret findings;
- policy warnings/blockers;
- destination collision/safety.

This keeps structural, canonical-semantic and physical-egress responsibilities separate.

---

## 22. Implementation handoff to P-RAW-05

When P-RAW-04 is also accepted, implementation must add rather than mutate v1 behavior in place.

Expected implementation areas include:

```text
src/sgokb/exchange/schemas/object-evidence-package-v2.schema.json
version-dispatched package manifest validation
Raw provenance resolver service from P-RAW-02
ObjectEvidencePackageBuilder v2 path
instructions v2 renderer
Result schema v2 snapshot from P-RAW-04
Raw materialization policy/budget
Raw-aware transfer/preflight
Raw-aware Package exchange audit
CLI/Application explicit version behavior
```

The current transport-neutral `PackageExchangeApplication` lifecycle remains a compatibility target:

```text
build -> stage -> preflight -> export
```

Its internal Package semantics may become version-dispatched without creating a GUI-only path.

---

## 23. Deferred to P-RAW-04

P-RAW-03 intentionally does not finalize:

- Result v2 statement grounding object shape;
- Result v2 attribute grounding object shape;
- Result v2 relation grounding object shape;
- whether a Raw reference may include a locator/span/page/JSON pointer in addition to `raw_artifact_id`;
- locator validation rules;
- accepted Knowledge Raw-grounding persistence shape;
- v1 Evidence link coexistence/migration in accepted Knowledge;
- review display of candidate Raw grounding.

Package v2 guarantees the exact Raw membership and lineage that P-RAW-04 can safely reference.

---

## 24. Acceptance criteria for this design

P-RAW-03 design is accepted when all of the following are fixed:

1. Package v2 has a new schema identity and never mutates v1 semantics in place.
2. Raw bytes, not reconstructed Evidence Markdown, are authoritative external semantic material.
3. exact Evidence -> Raw traceability is present in the manifest.
4. Raw membership is deduplicated by `artifact_id` without dropping Evidence mapping edges.
5. deterministic safe Package paths do not reuse local `storage_path` or untrusted logical paths.
6. exact byte size/hash are recorded and reverified.
7. Evidence selection budget and Raw materialization budget are separate.
8. required Raw cannot be truncated/dropped to satisfy budget or media policy.
9. preflight/egress checks cover all Raw payload bytes.
10. historical carry-forward remains bound to its original generation.
11. manifest integrity and a stable Raw grounding-set fingerprint are both defined.
12. v1/v2 dispatch and no-fallback rules are explicit.
13. P-RAW-04 has a precise Package Raw membership authority to target.

All criteria are satisfied by this document.

Therefore:

```text
P-RAW-03 = Complete / Accepted
```

No source code, runtime behavior, Package schema implementation, Result schema implementation or DB schema is changed by this task. No regression suite is rerun for this design-only task.
