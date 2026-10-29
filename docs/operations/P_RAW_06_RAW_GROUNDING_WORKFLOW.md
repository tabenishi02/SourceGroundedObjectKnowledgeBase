# P-RAW-06 — Raw Grounding Operator Workflow

Updated: 2026-10-30

- Scope: Package v2 / Result v2 external AI workflow
- Status: **Accepted subject to P-RAW-06 final verification gate**
- Requirements: `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- Decision: `docs/decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md`

## 1. Purpose

This is the Phase P operator procedure for the Raw-grounded external analysis boundary.

The existing `OBJECT_STANDARD_WORKFLOW.md` remains valid for the released v1-compatible workflow. For a new Raw-grounded analysis cycle during Phase P, the operator MUST explicitly select Package v2 as shown below.

## 2. Variables

```powershell
$Db = ".local/sgokb.sqlite"
$ObjectId = "<object-id>"
$ExportRoot = "C:\path\to\sgokb-export"
$IncomingRoot = "exchange/incoming"
```

Confirm the Object and DB first:

```powershell
sgokb --db $Db object show --object $ObjectId --knowledge
sgokb --db $Db system integrity
```

## 3. Build Package v2

Use the version flag explicitly:

```powershell
$Build = sgokb --db $Db package build `
  --object $ObjectId `
  --package-version v2 | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { throw "Package v2 build failed" }
$PackageId = $Build.data.package_id
$BuildPath = $Build.data.path
```

A successful Package v2 build must have:

```text
schema_version = sgokb.object-evidence-package/2.0
raw_grounding.included_raw_artifact_ids = non-empty
raw_grounding.integrity.grounding_set_sha256 = 64-hex digest
files[].role includes raw_grounding
```

The Package must contain exact Raw payloads such as:

```text
raw/artifact_0001/payload
```

It must not rely on generated `evidence/source_*.md` as semantic grounding material.

If build fails because Raw bytes are missing, changed, unsupported, or over materialization budget, stop. Do not substitute Evidence Markdown or a different Raw generation.

## 4. Stage and preflight

```powershell
$Stage = sgokb --db $Db package stage $BuildPath | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Package v2 stage failed" }
$StagedPath = $Stage.data.path

$Preflight = sgokb --db $Db package preflight `
  $StagedPath `
  --destination $ExportRoot | ConvertFrom-Json

$Preflight.data
```

Required disposition handling:

- `blocked`: stop; do not export;
- `review_required`: inspect the reasons and use acknowledgement only after human approval;
- `allow`: normal export may proceed.

Preflight is expected to fail closed for missing/unexpected files, manifest/hash mismatch, changed Raw payload, unsafe path/layout, credential findings, blocking warnings, invalid destination nesting, or conflicting destination Package ID.

## 5. Export

```powershell
$Export = sgokb --db $Db package export `
  $StagedPath `
  --destination $ExportRoot | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { throw "Package v2 export failed" }
$ExportedPath = $Export.data.path
```

If the preflight disposition was `review_required` and the operator approved it, add `--acknowledge-review` explicitly.

## 6. External AI boundary

Give the complete exported Package directory to the external AI.

The analysis contract is:

1. `instructions.md` is authoritative for analysis behavior;
2. the Result must conform to `schema/object-result-v2.schema.json`;
3. semantic claims must be grounded in Package-member Raw Artifacts;
4. Result claim grounding uses `raw_artifact_id`, not Evidence ID;
5. a locator may be omitted when exact precision cannot be justified;
6. an asserted `byte_range` or `text_quote` must be mechanically true of the exact Raw payload;
7. Package-external knowledge must not be introduced as semantic evidence.

The returned artifact is `result.json` with:

```text
schema_version = sgokb.object-result/2.0
binding.grounding_contract = sgokb.raw-grounding/1.0
binding.grounding_set_sha256 = Package grounding_set_sha256
```

## 7. Receive and validate

Place or receive the result through the normal audited Result path:

```powershell
$ResultPath = Join-Path $IncomingRoot "drop\$PackageId\result.json"

$Receipt = sgokb --db $Db result receive `
  $ResultPath `
  --package-id $PackageId `
  --incoming-root $IncomingRoot | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { throw "Result receive failed" }
$ReceiptId = $Receipt.data.receipt_id

sgokb --db $Db result validate $ReceiptId --incoming-root $IncomingRoot
if ($LASTEXITCODE -ne 0) { throw "Result v2 validation failed" }
```

Validation must reject, among other failures:

- Raw ID outside audited Package membership;
- grounding-set mismatch;
- Raw provenance/audit mismatch;
- staged Raw payload size/hash mismatch;
- invalid Raw locator;
- stale Package/base Version binding;
- Result schema or Registry contract violation.

## 8. Review and import

```powershell
sgokb --db $Db result review `
  $ReceiptId `
  --incoming-root $IncomingRoot `
  --review-format markdown
```

Do not import when review is blocked. If review requires explicit acknowledgement, inspect the semantic and grounding changes before proceeding.

```powershell
$Imported = sgokb --db $Db result import `
  $ReceiptId `
  --incoming-root $IncomingRoot | ConvertFrom-Json

# Only when review explicitly requires and the operator approves it:
# $Imported = sgokb --db $Db result import `
#   $ReceiptId `
#   --incoming-root $IncomingRoot `
#   --acknowledge-review | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { throw "Result v2 import failed" }
```

## 9. Post-import provenance check

Confirm the accepted Version:

```powershell
$VersionId = $Imported.data.version_id
sgokb --db $Db version show $VersionId
sgokb --db $Db object show --object $ObjectId --knowledge
```

For the v2 claim path, the accepted read must report Raw grounding. The import must not fabricate Evidence claim links from Package selection lineage.

Expected logical state:

```text
grounding_kind = raw
claim provenance -> raw_grounding_links
Evidence claim links synthesized from v2 -> none
```

## 10. Compatibility rules

During Phase P:

```text
new Raw-grounded cycle      -> pass --package-version v2 explicitly
legacy v1 cycle             -> supported when explicitly/default selected and compatible
v1 current -> v2 update     -> supported
v2 current -> v1 update     -> blocked by default
```

The no-option package default remains v1 until the Phase P release/default decision in `P-CLOSE-01`. This is a compatibility safeguard, not the recommended Raw-grounded command.

## 11. Failure recovery

Do not repair a failed Package or Result by manually editing hashes, membership, IDs, or grounding references.

Instead:

1. fix the canonical Source/Raw/provenance condition if it is wrong;
2. rebuild a fresh Package v2;
3. rerun preflight/export;
4. obtain a Result bound to that new Package;
5. validate/review/import through the audited route.

This keeps Package identity, Raw material, Result binding, and accepted provenance consistent.
