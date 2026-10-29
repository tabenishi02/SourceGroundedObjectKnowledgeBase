# P-RAW-04 — Raw-grounded Object Result v2 Design

Updated: 2026-10-30

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-RAW-04 [P0] Raw-grounded Object Result v2 design`
- Status: **Complete / Accepted**
- Released baseline: `v1.1.0`
- Depends on:
  - `P-RAW-01 — Current Evidence Package / Result impact survey`
  - `P-RAW-02 — Evidence -> Raw Artifact provenance resolution contract`
  - `P-RAW-03 — RAW-bearing Package v2 design`
- Scope: Result v2 / validation / accepted-grounding persistence design only; no runtime implementation or DB migration in this task
- Next: `P-RAW-05 — RAW Grounding implementation`

## 1. Purpose

P-RAW-04 defines the Object Result contract for the RAW-bearing Package v2 boundary.

The central requirement is:

```text
External AI grounding reference
    = material the AI was actually allowed to read
    = exact Raw Artifact membership of the bound Package v2
```

The Result must no longer require the external AI to emit an Evidence ID merely because Evidence was the upstream retrieval/selection unit.

The v2 chain is:

```text
selected / protected Evidence
        ↓ P-RAW-02
complete Raw Input Covering Set
        ↓ P-RAW-03
Package v2 exact Raw bytes
        ↓ external AI
Object Result v2 Raw grounding references
        ↓ validate against exact Package Raw membership
accepted Knowledge Version
        ↓
Raw grounding provenance retained without fabricating Evidence grounding
```

Evidence continues to explain **why Raw material entered the Package**. Raw Artifact references explain **what material grounded the Result**.

These are related provenance layers, but they are not the same assertion.

---

## 2. Existing v1 Result contract being versioned

Current Result v1 is:

```text
schema_version = sgokb.object-result/1.0
schema ID      = urn:sgokb:schema:object-result:1.0
```

Its grounding references are:

```json
{
  "evidence_id": "...",
  "role": "supports"
}
```

and accepted statement / attribute / relation grounding is persisted through `evidence_links`.

This is correct for Package v1 because the external semantic material is generated Evidence Markdown and `included_evidence_ids` is the v1 Package grounding-membership authority.

It is not truthful for Package v2 because the external AI reads Raw payloads instead.

Required versioning rule:

```text
Result v1 -> Evidence-grounded semantics
Result v2 -> Raw-grounded semantics
schema version determines meaning
```

A v2 validator MUST NOT reinterpret Result v1 Evidence references as Raw references, and a v1 validator MUST NOT accept Result v2 Raw references.

---

## 3. Result v2 identities

P-RAW-04 freezes these identities:

```text
OBJECT_RESULT_SCHEMA_VERSION = sgokb.object-result/2.0
OBJECT_RESULT_SCHEMA_ID      = urn:sgokb:schema:object-result:2.0
schema file                  = object-result-v2.schema.json
Package schema               = sgokb.object-evidence-package/2.0
instructions                 = sgokb.object-analysis/2.0
grounding contract           = sgokb.raw-grounding/1.0
```

Package v2 contains the canonical schema snapshot at:

```text
schema/object-result-v2.schema.json
```

The installed canonical schema and the Package snapshot must match exactly at build/stage time as required by P-RAW-03.

Result v1 schema/code remains an immutable compatibility contract.

---

## 4. What remains compatible from Result v1

The following semantic model is retained in v2 unless explicitly changed below:

- `result_status`;
- target Object binding;
- Primary / Additional Class binding;
- generation metadata;
- `knowledge.default_language`;
- summary statements;
- effective Facets and Facet status;
- structured Attributes and Attribute status/value rules;
- Relations;
- `derivation_kind` values:
  - `direct_statement`;
  - `synthesis`;
  - `interpretation`;
  - `reported_view`;
- attribution semantics;
- temporal scope semantics;
- conflicts;
- gaps;
- unresolved references;
- registry proposals;
- class extensions;
- local-key uniqueness rules;
- full-snapshot update semantics;
- Registry-driven Attribute / Relation / Facet specialization.

The breaking change is the grounding representation and the persistence/validation path that follows it.

---

## 5. Result v2 binding contract

Result v2 retains the existing exact Package binding and adds the Raw grounding identity required by Package v2.

Required conceptual shape:

```json
{
  "binding": {
    "package_id": "pkg_...",
    "package_schema_version": "sgokb.object-evidence-package/2.0",
    "manifest_sha256": "...",
    "package_created_at": "...",
    "base_version_id": null,
    "grounding_contract": "sgokb.raw-grounding/1.0",
    "grounding_set_sha256": "..."
  }
}
```

The following values MUST equal the exact audited Package manifest:

```text
package_id
package_schema_version
manifest_sha256
package_created_at
base_version_id
grounding_contract
grounding_set_sha256
```

`grounding_set_sha256` is copied from:

```text
manifest.raw_grounding.integrity.grounding_set_sha256
```

This prevents a Result from being rebound to a different Raw membership set even if target Object identity is the same.

---

## 6. Grounding target identity

### 6.1 Canonical identity

The v2 grounding target identity is:

```text
raw_artifact_id
```

The `raw_artifact_id` MUST be a member of:

```text
manifest.raw_grounding.included_raw_artifact_ids
```

The Result does not repeat Package-derived identity metadata such as:

- `source_id`;
- `snapshot_id`;
- `normalization_run_id`;
- `package_path`;
- `logical_path`;
- media type;
- byte size;
- SHA-256.

Those values are authoritative in the bound Package manifest and audit record. Duplicating them in the Result would create a second disagreeing authority.

### 6.2 Evidence ID is not a Result v2 grounding target

Result v2 grounding references MUST NOT contain `evidence_id`.

The external AI does not need to infer which Evidence caused a Raw Artifact to be selected.

When an operator needs the selection lineage, SGOKB obtains it from:

```text
Result raw_artifact_id
  -> bound Package raw_grounding.artifacts
  -> Package raw_grounding.evidence_bindings
  -> selected Evidence
```

This traversal is an audit/selection relationship. It MUST NOT be presented as proof that the AI directly grounded a claim to that Evidence record.

---

## 7. Raw grounding reference schema

Every Result v2 grounding reference has this conceptual shape:

```json
{
  "raw_artifact_id": "raw-...",
  "role": "supports",
  "locator": null
}
```

`locator` is optional. In the actual JSON Schema, absence is preferred over explicit `null`; the example above shows the conceptual cardinality only.

Required fields:

```text
raw_artifact_id
role
```

Allowed roles remain:

```text
supports
contradicts
contextualizes
```

This preserves v1 role semantics while changing only the grounding target identity.

### 7.1 No Package path in Result references

A Result MUST NOT ground by `raw/artifact_NNNN/payload` path.

Package path is transport metadata. `raw_artifact_id` is the canonical identity.

A path-only reference would be unsafe because path allocation is Package-instance-specific and not canonical provenance identity.

### 7.2 No hash-only identity

A Result MUST NOT ground by SHA-256 alone.

P-RAW-02/P-RAW-03 explicitly preserve distinct Raw Artifact identities even when byte hashes match.

---

## 8. Optional Raw locator contract

A Raw Artifact reference is sufficient grounding by itself. Locator precision is optional.

The baseline v2 contract supports two locator kinds only:

```text
byte_range
text_quote
```

This intentionally avoids inventing unverifiable page/time/DOM semantics across heterogeneous Raw media.

A future schema version may add typed locators such as PDF page, image region, media time range, DOM selector or JSON Pointer.

### 8.1 `byte_range`

Shape:

```json
{
  "kind": "byte_range",
  "start": 120,
  "end": 184
}
```

Semantics:

```text
zero-based
half-open interval [start, end)
coordinates apply to exact packaged Raw payload bytes
0 <= start < end <= Raw byte_size
```

A byte range is valid for any Raw media type.

### 8.2 `text_quote`

Shape:

```json
{
  "kind": "text_quote",
  "exact": "quoted source text",
  "prefix": "optional preceding context",
  "suffix": "optional following context"
}
```

Rules:

1. the Package Raw artifact must declare a usable non-null charset;
2. the exact packaged payload bytes are decoded using that declared charset;
3. `exact` must occur in the decoded Raw text;
4. when `exact` occurs more than once, `prefix` and/or `suffix` must disambiguate to exactly one occurrence;
5. supplied prefix/suffix must match the immediately adjacent decoded context used for disambiguation;
6. an unresolved or ambiguous quote locator is invalid.

The AI may omit a locator when it cannot truthfully provide this precision.

### 8.3 Locator is precision, not membership authority

A locator never changes Raw membership.

```text
membership authority = raw_artifact_id in exact Package v2
locator              = optional narrowing within that artifact
```

An invalid locator does not fall back silently to artifact-only grounding. If the Result asserted locator precision, that assertion must validate or the Result is invalid. The producer may instead emit the Raw reference without a locator.

---

## 9. Grounding field replacement

Result v2 replaces the v1 field name:

```text
evidence
```

with:

```text
grounding
```

for every Result surface that currently carries Evidence references.

### 9.1 Statement

Conceptual shape:

```json
{
  "local_key": "s1",
  "text": "...",
  "derivation_kind": "direct_statement",
  "grounding": [
    {
      "raw_artifact_id": "raw-a",
      "role": "supports"
    }
  ]
}
```

Requirement:

```text
statement grounding minItems = 1
```

### 9.2 Attribute

For `status = known`:

```text
grounding minItems = 1
```

For non-known states:

```text
grounding may be empty
```

This preserves the v1 Attribute status behavior.

### 9.3 Relation

Requirement:

```text
relation grounding minItems = 1
```

### 9.4 Conflicts

Result v1 requires at least two Evidence refs for a conflict. Result v2 changes this to:

```text
conflict grounding minItems = 1
```

Reason: one Raw Artifact can legitimately contain two contradictory passages. Raw Artifact identity is coarser than an extracted Evidence record, and locator use is optional. Requiring two Raw refs would force fabricated duplicate references or false precision.

When distinct conflicting locations can be identified, multiple grounding refs and/or locators are encouraged but not required structurally.

### 9.5 Gaps

Gap grounding may remain empty, as in v1.

### 9.6 Unresolved references

Requirement:

```text
unresolved_reference grounding minItems = 1
```

### 9.7 Registry proposals

Requirement:

```text
registry_proposal grounding minItems = 1
```

A Registry proposal remains review-only and is never auto-applied.

---

## 10. Result v2 top-level conceptual shape

```json
{
  "schema_version": "sgokb.object-result/2.0",
  "result_status": "complete",
  "target": {},
  "binding": {
    "package_id": "pkg_...",
    "package_schema_version": "sgokb.object-evidence-package/2.0",
    "manifest_sha256": "...",
    "package_created_at": "...",
    "base_version_id": null,
    "grounding_contract": "sgokb.raw-grounding/1.0",
    "grounding_set_sha256": "..."
  },
  "generation": {},
  "knowledge": {
    "default_language": "ja",
    "summary": [],
    "facets": [],
    "attributes": [],
    "relations": []
  },
  "conflicts": [],
  "gaps": [],
  "unresolved_references": [],
  "registry_proposals": [],
  "class_extensions": []
}
```

All normal Result objects continue to use `additionalProperties: false` unless an existing extension contract explicitly permits data.

Result v2 has no top-level Evidence grounding section because Package v2 already owns the Evidence selection trace and Raw membership inventory.

---

## 11. Derivation / attribution / temporal semantics

P-RAW-04 deliberately does not change the semantic-role model.

### Derivation kinds

```text
direct_statement
synthesis
interpretation
reported_view
```

remain unchanged.

A derivation kind is not inferred from number of Raw references.

For example:

- `synthesis` may combine multiple passages in one Raw Artifact;
- `direct_statement` may require more than one Raw Artifact for complete context;
- `interpretation` may use one or several Raw Artifacts.

Therefore no v2 rule requires a particular Raw-reference count per derivation kind beyond the general minimum grounding cardinality.

### Attribution

`reported_view` continues to require attribution exactly as v1.

Source/Object/named actor/community attribution semantics remain separate from Raw grounding. A Source attribution does not replace a Raw reference.

### Temporal semantics

`as_of`, `valid_from`, `valid_to`, `context_object_id`, and label semantics remain unchanged.

Raw locator coordinates are not temporal scope.

---

## 12. Result v2 static validation

JSON Schema validates at least:

- exact Result schema version;
- required top-level fields;
- target/binding/generation shapes;
- `grounding` rather than `evidence` fields;
- Raw reference role enum;
- locator discriminated union;
- locator numeric/string structural constraints;
- minimum grounding cardinalities;
- Attribute known/non-known rules;
- derivation/attribution structural rules;
- local key syntax;
- conflict/gap/unresolved/proposal/class-extension shape.

Because `additionalProperties: false` is retained, a Result v2 containing a v1 `evidence` field is structurally invalid.

Likewise, a Result v1 containing a v2 `grounding` field is invalid under the v1 schema.

---

## 13. Version-dispatched validation pipeline

Result validation must dispatch from the audited Package version and expected Result version before applying schema-specific semantics.

Conceptual routing:

```text
Package v1
  -> expected Result v1
  -> v1 static schema
  -> Evidence membership/provenance validation

Package v2
  -> expected Result v2
  -> v2 static schema
  -> Raw membership/provenance/locator validation

unknown major version
  -> fail closed
```

A Result-provided `schema_version` never chooses its own validator independently of the bound Package. It must agree with the Package's `expected_result_schema_version`.

---

## 14. Result v2 binding validation

The validator must verify exact equality against the audited Package for:

```text
Result.schema_version
Result.target.object_id
Result.target.primary_class_id
Result.target.additional_class_ids
Result.binding.package_id
Result.binding.package_schema_version
Result.binding.manifest_sha256
Result.binding.package_created_at
Result.binding.base_version_id
Result.binding.grounding_contract
Result.binding.grounding_set_sha256
Result.generation.instructions_version
```

Existing stale-target / stale-Class / stale-base-Version checks remain.

A Package v2 manifest and its staged Raw payloads must still pass canonical/integrity verification before the Result is treated as grounded against them.

---

## 15. Raw membership validation

For every Result v2 `grounding[]` reference:

1. `raw_artifact_id` must appear in the exact bound Package's `included_raw_artifact_ids`;
2. the Package must contain exactly one corresponding Raw artifact manifest entry;
3. the Raw entry must have a matching `files[]` transport entry;
4. Package path, media type, byte size and hash consistency must hold;
5. the staged Raw payload must still match the declared byte size and SHA-256;
6. Package `grounding_set_sha256` must validate;
7. canonical Raw Artifact identity must still resolve consistently with the Package audit/canonical lineage;
8. same-hash Raw Artifact substitution is prohibited;
9. a Raw Artifact known to canonical storage but absent from this exact Package is rejected;
10. an Evidence ID, Source ID, Snapshot ID or path cannot substitute for Raw membership.

Required error semantics include distinct conditions for at least:

```text
raw_grounding_outside_package
raw_grounding_artifact_missing
raw_grounding_package_metadata_mismatch
raw_grounding_payload_integrity_mismatch
raw_grounding_canonical_provenance_mismatch
grounding_set_sha256_mismatch
```

Exact public error-code spelling may be finalized during implementation, but the failure categories are frozen here.

---

## 16. Locator validation

### Byte range

Validator checks:

```text
integer start/end
0 <= start < end
end <= exact Package Raw byte_size
```

No decoded-text assumptions are made.

### Text quote

Validator checks against the exact staged Package payload:

```text
manifest charset is usable
payload decodes using declared charset
exact quote occurs
prefix/suffix, when supplied, match adjacent context
the selector resolves to exactly one occurrence
```

Locator failure is an error, not a review warning.

Reason:

```text
invalid locator = false grounding precision assertion
```

The producer can avoid that assertion by omitting the locator.

---

## 17. Evidence selection lineage is not claim grounding

Package v2 retains:

```text
manifest.evidence.items
manifest.raw_grounding.evidence_bindings
```

These structures answer:

```text
Why was this Raw material selected?
Which Evidence/run provenance caused it to enter the Package?
```

Result v2 grounding answers:

```text
Which Raw material supports/contextualizes/contradicts this Result item?
```

The validator/importer MUST NOT transform:

```text
Result raw_artifact_id
  -> matching Package Evidence binding
  -> evidence_links row
```

as if the external AI cited that Evidence.

Such a transformation would recreate the exact provenance fiction P-RAW is designed to eliminate.

---

## 18. Accepted Knowledge persistence model

P-RAW-04 freezes a two-family persistence model.

### 18.1 v1 accepted grounding

Existing v1 accepted Versions remain:

```text
claim -> evidence_links -> Evidence
```

No migration/backfill is required merely because newer software supports v2.

### 18.2 v2 accepted grounding

v2 accepted statement / attribute / relation grounding uses a new canonical Raw grounding link family conceptually named:

```text
raw_grounding_links
```

Each link must retain at least:

```text
id
version_id
target_kind              # statement | attribute | relation
target_id
raw_artifact_id
role                      # supports | contradicts | contextualizes
locator_json              # nullable canonical JSON
origin_kind               # result_import
origin_ref                # import ID
created_at
```

Implementation may normalize locator fields further, but the canonical read semantics above must be preserved.

`raw_grounding_links.raw_artifact_id` refers to canonical Raw Artifact identity, not Package path or hash-only identity.

### 18.3 Version grounding context

Each imported Version must retain enough immutable context to identify which grounding family and exact exchange artifact produced it.

Conceptual version grounding metadata:

```text
version_id
result_schema_version
package_id
package_schema_version
manifest_sha256
grounding_kind            # evidence_v1 | raw_v2
grounding_contract        # nullable for v1
grounding_set_sha256      # nullable for v1
```

P-RAW-05 may store this as a dedicated table or as a normalized extension of current import/audit metadata, but it MUST be queryable without guessing from missing rows.

### 18.4 No v2 shadow Evidence links

For a Result v2 import:

```text
raw_grounding_links = written
evidence_links      = NOT synthesized from Package Evidence bindings
```

This is a hard compatibility boundary.

---

## 19. Review metadata persistence

Current conflicts/gaps/unresolved references/registry proposals are stored as Result metadata JSON rather than normalized claim rows.

Result v2 keeps that approach initially:

- their `grounding` arrays are stored exactly as validated v2 metadata;
- no claim-level `raw_grounding_links` row is required for those review-only collections;
- review/read surfaces must still render their Raw references using Package/canonical provenance metadata.

A future normalization of review-only grounding does not require a Result v2 schema change if semantic meaning remains the same.

---

## 20. Historical carry-forward after the first v2 import

This is a required migration rule.

Current v1 Package building protects historical grounding through:

```text
accepted Version evidence_links
    -> carry_forward Evidence IDs
```

A truthful v2 import does not create `evidence_links`, so this mechanism cannot be used unchanged after a v2 Version becomes current.

### 20.1 v1 base Version

When current accepted Version is Evidence-grounded v1:

```text
carry-forward source = existing claim-level evidence_links
```

P-RAW-02 then resolves those historical Evidence records through their original Normalization Runs.

This supports a direct v1 -> v2 grounding-model upgrade.

### 20.2 v2 base Version

When current accepted Version is Raw-grounded v2:

1. collect distinct `raw_artifact_id` values referenced by accepted statement/attribute/relation `raw_grounding_links`;
2. identify the exact originating Package from Version grounding/import metadata;
3. read that Package's preserved `evidence_bindings`;
4. select every Package Evidence binding whose `raw_artifact_ids` intersects the accepted referenced Raw set;
5. treat those Evidence IDs as **carry-forward selection lineage**, not claim grounding;
6. protect those Evidence IDs in the next Package selection;
7. resolve each through its original historical run using P-RAW-02.

Conceptually:

```text
accepted v2 claim
  -> Raw grounding link
  -> originating Package Raw membership
  -> Package Evidence->Raw selection binding
  -> carry-forward selection Evidence
  -> original historical run
  -> complete Raw Input Covering Set
```

All matching Evidence bindings are retained rather than choosing an arbitrary single Evidence when several selected Evidence records caused the same Raw Artifact to be available.

This can be conservative, but it does not claim that the AI cited those Evidence records.

### 20.3 No Raw-only carry-forward orphan

P-RAW-03 requires every packaged Raw Artifact to remain explained by Evidence selection/provenance binding. Therefore a next Package must not inject a historical Raw Artifact directly without an Evidence selection lineage.

If the prior Package audit required to recover that lineage is unavailable or inconsistent, carry-forward fails closed.

---

## 21. Current Object snapshot in Package v2

`current_object.json` is prior accepted context, not new grounding authority.

For Package v2, the current-object read model must make the prior grounding family explicit rather than silently converting it.

Recommended v2 snapshot representation for each accepted Knowledge item:

```json
{
  "grounding": [
    {
      "kind": "evidence",
      "evidence_id": "...",
      "role": "supports"
    }
  ]
}
```

for a historical v1 base, or:

```json
{
  "grounding": [
    {
      "kind": "raw",
      "raw_artifact_id": "...",
      "role": "supports",
      "locator": {
        "kind": "text_quote",
        "exact": "..."
      }
    }
  ]
}
```

for a v2 base.

The snapshot should also expose a version-level grounding model marker:

```text
grounding_model = evidence_v1 | raw_v2
```

Rules:

1. historical v1 Evidence grounding remains labeled as Evidence;
2. historical v2 Raw grounding remains labeled as Raw;
3. no cross-kind synthesis occurs merely for display;
4. Result v2 MUST still emit only Package-v2 Raw grounding refs regardless of prior grounding kind;
5. `current_object.json` never authorizes an ungrounded new claim.

Exact presentation fields may include current display IDs/names as today, but the grounding identity rules above are frozen.

---

## 22. Review / diff semantics

The current review engine includes Evidence references inside statement/attribute/relation semantics. P-RAW-05 must make review grounding-aware without confusing semantic content change with grounding-model migration.

Required review model separates:

```text
Knowledge content diff
Grounding diff
```

### 22.1 Knowledge content diff

Content identity includes the existing semantic fields:

- statement text / derivation / language / temporal / attribution;
- Attribute identity/status/value/language/temporal;
- Relation endpoints/type/temporal;
- Facet/status structure.

Grounding changes alone MUST NOT be classified as destructive Knowledge deletion.

### 22.2 Grounding diff

Review separately reports grounding changes such as:

```text
Evidence -> Raw grounding-model transition
Raw Artifact added/removed
role changed
locator added/removed/changed
grounding_set/package changed
```

### 22.3 v1 -> v2 review

A first v2 update over a v1 base will normally show:

```text
semantic Knowledge may be unchanged
grounding model changes evidence_v1 -> raw_v2
```

That transition is expected and must not by itself be reported as destructive omission.

### 22.4 Operator display

For Raw grounding, review/GUI must be able to show:

```text
raw_artifact_id
role
locator
Source ID
Snapshot ID
media type
logical path
byte size
SHA-256
Package-local path
origin Package ID / grounding_set_sha256
```

The display may also show which Package Evidence selections caused the Raw to be included, but must label that as **selection lineage**, not claim grounding.

---

## 23. Result receipt compatibility

The receive lifecycle remains:

```text
detect -> receive -> pending -> validate -> review -> import
```

Receipt intake remains mostly version-neutral and may parse routing fields for early diagnostics.

Authoritative validation dispatch, however, is version-specific.

Receipt/audit records must retain enough parsed routing information to diagnose at least:

```text
Result schema version
Package ID
Package schema version
manifest hash
base Version
grounding contract / grounding-set hash where v2
```

P-RAW-05 may extend receipt audit columns or retain these fields in versioned JSON metadata.

---

## 24. v1 / v2 compatibility and migration policy

### 24.1 Historical v1 artifacts remain valid as v1

Existing v1 Packages/Results/accepted Versions are not rewritten merely because v2 support is installed.

```text
v1 Package -> v1 Result -> evidence_links
```

remains a supported historical interpretation.

### 24.2 v2 artifacts remain v2

```text
v2 Package -> v2 Result -> raw_grounding_links
```

No Evidence-link shadow conversion is performed.

### 24.3 v1 -> v2 update is supported

A v2 Package may use an accepted v1 Version as its base.

Historical Evidence grounding from that base supplies carry-forward selection Evidence, which P-RAW-02 resolves to historical Raw. The new Result then emits Raw grounding and the accepted new Version becomes `raw_v2`.

This is the normal grounding-model migration path.

### 24.4 v2 -> v1 downgrade is not supported by default

Once the current accepted Version is Raw-grounded v2, a legacy v1 update cannot truthfully reconstruct claim-level Evidence grounding from the v2 Version.

Therefore:

```text
current Version grounding_kind = raw_v2
legacy v1 Package update       = blocked by default
```

A future explicit migration contract could define otherwise, but no implicit Raw -> Evidence downgrade is allowed.

### 24.5 No artifact relabeling

Prohibited:

```text
change schema_version field and reuse same payload
v1 Result parsed under v2 grounding semantics
v2 Result converted to v1 by substituting Evidence IDs
v2 Raw refs converted into Evidence links by Package binding lookup
```

---

## 25. Import preconditions for Result v2

Immediately before import, v2 must re-check at least:

```text
receipt is valid
immutable Result hash/byte count still match receipt
review requirements acknowledged
Object remains active
current Version still equals base_version_id
Class/Facet/Attribute/Relation contracts remain current
Package audit record still matches Result binding
Package schema is v2
grounding contract/hash match audited Package
all referenced Raw IDs are exact Package members
all referenced canonical Raw Artifacts still exist consistently
locator assertions remain valid against immutable staged Package bytes
```

Import then writes Knowledge and Raw grounding atomically in the same transaction as Version acceptance.

A partial state such as:

```text
Knowledge committed
Raw grounding links missing
```

is prohibited.

---

## 26. Read-model compatibility

Canonical read surfaces must stop assuming that every accepted grounding record is an Evidence link.

Required version-aware behavior:

```text
v1 Version -> expose Evidence grounding
v2 Version -> expose Raw grounding
```

A compatibility read model may expose a tagged union:

```json
{
  "kind": "evidence",
  "evidence_id": "...",
  "role": "supports"
}
```

or:

```json
{
  "kind": "raw",
  "raw_artifact_id": "...",
  "role": "supports",
  "locator": null
}
```

but it MUST NOT fabricate one kind from the other.

Search / Similarity / derived index content remains based on accepted Knowledge semantic text/values and should not require a new embedding representation solely because grounding identity changed. P-RAW-05/06 must regression-test this assumption.

---

## 27. Instructions v2 exact grounding rules

`sgokb.object-analysis/2.0` must tell the external AI at minimum:

1. only Raw Artifacts listed in `manifest.raw_grounding.included_raw_artifact_ids` are allowed grounding material;
2. do not use web browsing or outside model-memory facts as evidence;
3. do not cite Package Evidence IDs in Result v2;
4. emit `grounding[]` with Package-member `raw_artifact_id` values;
5. `role` must be `supports`, `contradicts`, or `contextualizes`;
6. locator is optional; omit it rather than inventing precision;
7. if using `byte_range`, use zero-based half-open exact Raw byte coordinates;
8. if using `text_quote`, quote text that exists in the exact Raw payload and add prefix/suffix when required to disambiguate;
9. `current_object.json` is prior accepted context, not a source of ungrounded new facts;
10. Evidence metadata in the manifest describes selection lineage only;
11. allowed Facet/Attribute/Relation and derivation/attribution/temporal rules remain binding;
12. no persistent IDs may be invented.

---

## 28. Implementation handoff to P-RAW-05

Implementation is expected to add versioned behavior rather than mutate v1 in place.

Primary areas:

```text
src/sgokb/exchange/schemas/object-result-v2.schema.json
version-dispatched Object Result schema loader/validator
Result v2 contract specialization
Raw grounding reference collection
Raw membership/locator validator
Result receipt/audit v2 routing metadata
Raw-grounding import persistence
version grounding context persistence
current_object version-aware grounding read model
v2 historical carry-forward selection reconstruction
review/diff content-vs-grounding separation
instructions v2 exact Result syntax
Package v2 schema snapshot integration
```

P-RAW-05 also implements the P-RAW-02 resolver and P-RAW-03 Package v2 design, so Package and Result version dispatch should be introduced coherently rather than as isolated patches.

---

## 29. Test obligations for P-RAW-05 / P-RAW-06

At minimum add coverage for:

### Schema / version dispatch

- v1 Package + v1 Result accepted on v1 path;
- v2 Package + v2 Result accepted on v2 path;
- v1 Package + v2 Result rejected;
- v2 Package + v1 Result rejected;
- unknown major version rejected;
- v2 `evidence` field rejected;
- v1 `grounding` field rejected.

### Raw membership

- Package-member Raw accepted;
- canonical-but-outside-Package Raw rejected;
- same-hash different Raw ID substitution rejected;
- missing Package Raw metadata rejected;
- modified staged Raw bytes rejected;
- grounding-set hash mismatch rejected.

### Locator

- valid byte range accepted;
- out-of-bounds/empty byte range rejected;
- valid unique text quote accepted;
- missing text quote rejected;
- ambiguous text quote without sufficient context rejected;
- disambiguated text quote accepted;
- locator omitted accepted.

### Persistence

- v2 import writes Raw grounding links;
- v2 import does not synthesize Evidence links;
- v1 import remains Evidence-link based;
- transaction rollback removes Knowledge and Raw links together;
- version grounding context identifies v1/v2 correctly.

### Migration / carry-forward

- v1 base -> v2 Package/Result/import transition;
- v2 base -> next v2 carry-forward selection lineage reconstruction;
- multiple Evidence bindings for one referenced Raw remain conservative carry-forward candidates;
- missing prior Package audit blocks v2 carry-forward;
- v2 current Version -> legacy v1 update blocked.

### Review / read models

- grounding-only change is not destructive Knowledge omission;
- v1 -> v2 grounding-model change is displayed separately;
- Raw provenance display does not label selection Evidence as claim grounding;
- current_object preserves prior grounding kind explicitly.

---

## 30. Acceptance criteria for this design

P-RAW-04 is accepted when all of the following are fixed:

1. Result v2 has its own schema identity and never changes v1 meaning in place.
2. `raw_artifact_id` is the canonical Result v2 grounding target.
3. Evidence IDs are absent from Result v2 grounding references.
4. Package path/hash/source metadata are not duplicated as competing grounding identity.
5. optional locator semantics are defined and mechanically verifiable.
6. statement/attribute/relation grounding schemas use Raw references.
7. conflict cardinality accounts for multiple contradictory passages in one Raw Artifact.
8. exact Package Raw membership and grounding-set binding are validated.
9. derivation kind, attribution and temporal semantics remain compatible.
10. v2 accepted grounding is persisted separately from `evidence_links`.
11. no v2 claim-level Evidence link is synthesized from Package selection provenance.
12. prior v1 and v2 grounding are represented explicitly in current-object/read models.
13. v1 -> v2 transition is supported without rewriting historical v1 Versions.
14. v2 -> v1 implicit downgrade is prohibited.
15. historical carry-forward after v2 import is recovered through Raw -> originating Package Evidence-selection lineage without treating that lineage as claim grounding.
16. review separates semantic Knowledge changes from grounding changes.
17. P-RAW-05 has a concrete implementation and test handoff.

All criteria are satisfied by this document.

Therefore:

```text
P-RAW-04 = Complete / Accepted
```

No source code, runtime behavior, implemented JSON Schema, or DB schema is changed by this design-only task. No regression suite is rerun for P-RAW-04.