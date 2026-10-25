# SGOKB Happy-Path Operational Acceptance Test Procedures

Updated: 2026-10-25

- Scope: SGOKB v1.0.0 current accepted architecture
- Test type: manual / operational acceptance procedures
- Path: **normal / happy path only**
- Status: **Procedure ready / execution pending**
- Test plan: `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md`
- Standard workflow: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Architecture: `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`

---

## 1. Purpose

This document provides executable operator procedures for every happy-path acceptance item in `SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md`.

The procedures are intentionally limited to valid inputs and successful operational paths. Do not use this document for malformed input, stale Result, blocked export, runtime failure, corruption, crash recovery, destructive recovery, or performance/quality stress testing.

Each test must record at least:

```text
Result: PASS / FAIL / NOT RUN
Observed IDs:
Observed output:
Notes:
```

Stop the current chain if an operation that is expected to succeed returns a non-zero exit code. Do not weaken a test, skip a required step, or manually edit canonical SQLite state to continue.

---

## 2. Test workspace and variables

Run from the repository root in PowerShell.

Create dedicated test-owned directories first:

```powershell
$Db           = ".local/acceptance/sgokb-happy-path.sqlite"
$ExportRoot   = ".local/acceptance/export"
$IncomingRoot = ".local/acceptance/incoming"
$BuildRoot    = ".local/acceptance/package-build"
$StagingRoot  = ".local/acceptance/staging"
$RenderRoot   = ".local/acceptance/render"
$BackupRoot   = ".local/acceptance/backups"
$RestoreDb    = ".local/acceptance/restored/sgokb-happy-path.sqlite"

New-Item -ItemType Directory -Force `
  (Split-Path $Db), $ExportRoot, $IncomingRoot, $BuildRoot, `
  $StagingRoot, $RenderRoot, $BackupRoot, (Split-Path $RestoreDb) | Out-Null
```

Prepare valid Web Capture bundles before section C. Replace these placeholders with actual paths:

```powershell
$CaptureA1   = "C:\path\to\SRC-A1.webcapture.zip"
$CaptureA2   = "C:\path\to\SRC-A2.webcapture.zip"
$CaptureA1V2 = "C:\path\to\SRC-A1-V2.webcapture.zip"
$CaptureB1   = "C:\path\to\SRC-B1.webcapture.zip"
$CaptureC1   = "C:\path\to\SRC-C1.webcapture.zip"
$CaptureR1   = "C:\path\to\SRC-R1.webcapture.zip"
```

Use easy-to-recognize test Object names. These may be real Object names if the captures are real sources:

```powershell
$ObjectAName = "Acceptance Character A"
$ObjectBName = "Acceptance Work B"
$ObjectCName = "Acceptance Concept C"
```

Keep the following variables populated as the test progresses:

```text
$ObjectAId / $ObjectBId / $ObjectCId
$SourceA1Id / $SourceA2Id / $SourceB1Id / $SourceC1Id / $SourceR1Id
$SnapshotA1Id / ...
$EvidenceId
$PackageId / $BuildPath / $StagedPath / $ExportedPath
$ReceiptId
$Version1Id / $Version2Id
$ProposalRef
```

---

# A. Environment / CLI

## A-01 CLI startup

**Procedure**

```powershell
sgokb --help
if ($LASTEXITCODE -ne 0) { throw "A-01 failed" }
```

**Verify**

- Help is printed.
- Public command is `sgokb`.
- Domain commands include `source`, `object`, `association`, `evidence`, `registry`, `package`, `result`, `version`, `search`, `similar`, `render`, `mcp`, and `system`.

**PASS**: exit code `0` and expected command surface is visible.

## A-02 Isolated DB startup

Use only the isolated acceptance DB.

```powershell
sgokb --db $Db system status
if ($LASTEXITCODE -ne 0) { throw "A-02 failed" }
```

**Verify**: SGOKB can open/initialize the isolated DB with the current schema/migration state.

## A-03 System status

```powershell
$SystemStatus = sgokb --db $Db system status | ConvertFrom-Json
$SystemStatus
```

**PASS**: `ok = true`; status data is returned without using production state.

## A-04 Integrity

```powershell
$Integrity = sgokb --db $Db system integrity | ConvertFrom-Json
$Integrity
if ($LASTEXITCODE -ne 0) { throw "A-04 failed" }
```

**Verify**: SQLite integrity, foreign-key integrity, and migration state are valid.

## A-05 Class registry list

```powershell
$Classes = sgokb --db $Db registry class list | ConvertFrom-Json
$Classes.data
```

**PASS**: registered classes are returned and include the classes selected for the acceptance dataset.

## A-06 Class registry show

Run for all test classes:

```powershell
sgokb --db $Db registry class show character
sgokb --db $Db registry class show work
sgokb --db $Db registry class show concept
```

**PASS**: all selected class definitions are readable.

## A-07 Relation type registry

```powershell
$RelationTypes = sgokb --db $Db registry relation-type list | ConvertFrom-Json
$RelationTypes.data
```

Select one existing relation type that is appropriate for OBJ-A <-> OBJ-B and inspect it:

```powershell
sgokb --db $Db registry relation-type show <relation-type-ref>
```

**PASS**: relation-type list and selected definition are readable.

## A-08 JSON contract

```powershell
$JsonProbe = sgokb --db $Db system status | ConvertFrom-Json
$JsonProbe.schema_version
$JsonProbe.ok
$JsonProbe.command
$JsonProbe.warnings
```

**PASS**: `schema_version` is `sgokb.cli/1.0`, `ok` is true, and the response is valid JSON.

## A-09 Human-readable output

```powershell
sgokb --db $Db --format text system status
```

**PASS**: human-readable text is displayed and command succeeds.

---

# B. Object Registry

## B-01 Create Character / OBJ-A

```powershell
$A = sgokb --db $Db object add `
  --name $ObjectAName `
  --primary-class character | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "B-01 failed" }
$ObjectAId = $A.data.object_id
$ObjectAId
```

Record `$ObjectAId`.

## B-02 Create Work / OBJ-B

```powershell
$B = sgokb --db $Db object add `
  --name $ObjectBName `
  --primary-class work | ConvertFrom-Json
$ObjectBId = $B.data.object_id
$ObjectBId
```

## B-03 Create Concept / OBJ-C

```powershell
$C = sgokb --db $Db object add `
  --name $ObjectCName `
  --primary-class concept | ConvertFrom-Json
$ObjectCId = $C.data.object_id
$ObjectCId
```

**PASS B-01..B-03**: three non-empty, mutually distinct stable Object IDs are returned.

## B-04 List Objects

```powershell
$Objects = sgokb --db $Db object list | ConvertFrom-Json
$Objects.data
```

**Verify**: OBJ-A, OBJ-B, and OBJ-C are all present.

## B-05 Read OBJ-A by ID

```powershell
$ById = sgokb --db $Db object show --object $ObjectAId | ConvertFrom-Json
$ById.data
```

**PASS**: returned `object_id` matches `$ObjectAId`.

## B-06 Read OBJ-A by exact name

```powershell
$ByName = sgokb --db $Db object show --name $ObjectAName | ConvertFrom-Json
$ByName.data
```

**PASS**: the resolved Object ID is `$ObjectAId`.

## B-07 Add alias

```powershell
$ObjectAAlias = "Acceptance Alias A"
sgokb --db $Db object alias add --object $ObjectAId $ObjectAAlias
```

## B-08 List aliases

```powershell
sgokb --db $Db object alias list --object $ObjectAId
```

**PASS**: `$ObjectAAlias` is present.

## B-09 Resolve by alias

```powershell
$AliasRead = sgokb --db $Db object show --name $ObjectAAlias | ConvertFrom-Json
$AliasRead.data
```

**PASS**: alias resolves to `$ObjectAId`.

## B-10 Rename OBJ-A

Preserve the old name for later comparison:

```powershell
$ObjectAOriginalName = $ObjectAName
$ObjectAName = "$ObjectAName Renamed"
sgokb --db $Db object rename --object $ObjectAId --to $ObjectAName
$RenameRead = sgokb --db $Db object show --object $ObjectAId | ConvertFrom-Json
$RenameRead.data
```

**PASS**: canonical name changed; Object ID remains `$ObjectAId`.

## B-11 Add additional class

Choose an existing compatible class from A-05 that is not the current primary class:

```powershell
sgokb --db $Db object class add --object $ObjectAId <additional-class-ref>
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: additional class is visible and Object ID is unchanged.

## B-12 Change primary class and restore

Choose a valid existing class for the temporary change:

```powershell
sgokb --db $Db object class set-primary --object $ObjectAId <temporary-class-ref>
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object class set-primary --object $ObjectAId character
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: both mutations succeed; final primary class is `character`; Object ID remains unchanged.

## B-13 Inspect Object events

```powershell
sgokb --db $Db object events --object $ObjectAId
```

**Verify**: creation, alias/name/class/status-related Registry events created so far are inspectable according to the event contract.

## B-14 Archive and reactivate

```powershell
sgokb --db $Db object status --object $ObjectAId --set archived
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object status --object $ObjectAId --set active
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: final state is active and Object ID remains `$ObjectAId`.

---

# C. Source / Snapshot / Raw Artifact

For each import, parse and record returned Source and Snapshot IDs.

## C-01 Import SRC-A1

```powershell
$ImportA1 = sgokb --db $Db source import $CaptureA1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "C-01 failed" }
$SourceA1Id   = $ImportA1.data[0].source
$SnapshotA1Id = $ImportA1.data[0].snapshot
$SourceA1Id
$SnapshotA1Id
```

**PASS**: both IDs are returned.

## C-02 Process SRC-A1 Snapshot

```powershell
sgokb --db $Db source process --snapshot $SnapshotA1Id
if ($LASTEXITCODE -ne 0) { throw "C-02 failed" }
```

**PASS**: normalization/evidence processing succeeds.

## C-03 Source status

```powershell
sgokb --db $Db source status
```

**Verify**: imported/processed source state includes SRC-A1.

## C-04 Snapshot list

```powershell
sgokb --db $Db source snapshots
```

**Verify**: `$SnapshotA1Id` is present.

## C-05 Import/process SRC-A2

```powershell
$ImportA2 = sgokb --db $Db source import $CaptureA2 | ConvertFrom-Json
$SourceA2Id   = $ImportA2.data[0].source
$SnapshotA2Id = $ImportA2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA2Id
```

**PASS**: `$SourceA2Id` is distinct from `$SourceA1Id` for an independent logical source.

## C-06 Import/process SRC-B1

```powershell
$ImportB1 = sgokb --db $Db source import $CaptureB1 | ConvertFrom-Json
$SourceB1Id   = $ImportB1.data[0].source
$SnapshotB1Id = $ImportB1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotB1Id
```

## C-07 Import/process SRC-C1

```powershell
$ImportC1 = sgokb --db $Db source import $CaptureC1 | ConvertFrom-Json
$SourceC1Id   = $ImportC1.data[0].source
$SnapshotC1Id = $ImportC1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotC1Id
```

## C-08 Later Snapshot for the same logical Source

`$CaptureA1V2` must be a valid later capture of the same source identity/URL as SRC-A1.

```powershell
$ImportA1V2 = sgokb --db $Db source import $CaptureA1V2 | ConvertFrom-Json
$SourceA1V2Id   = $ImportA1V2.data[0].source
$SnapshotA1V2Id = $ImportA1V2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA1V2Id
```

**Verify**

- Source identity follows the current ingestion identity contract.
- A new Snapshot ID is created for the later capture.
- The previous Snapshot remains listed.

## C-09 Raw Artifact preservation

```powershell
sgokb --db $Db source snapshots
```

Then inspect the Source/Snapshot details exposed by the command output and, where the capture path is reported, verify the retained raw artifact exists under the test-owned storage.

**PASS**: prior Raw/Snapshot history was not replaced by processing or later capture.

---

# D. Source <-> Object Association

Before D-06, import/process SRC-R1:

```powershell
$ImportR1 = sgokb --db $Db source import $CaptureR1 | ConvertFrom-Json
$SourceR1Id   = $ImportR1.data[0].source
$SnapshotR1Id = $ImportR1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotR1Id
```

## D-01 Inspect OBJ-A associations

```powershell
sgokb --db $Db association list --object $ObjectAId
```

## D-02 Confirm SRC-A1 -> OBJ-A

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1Id --status confirmed
```

## D-03 Confirm SRC-A2 -> OBJ-A

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA2Id --status confirmed
```

## D-04 Confirm SRC-B1 -> OBJ-B

```powershell
sgokb --db $Db association set `
  --object $ObjectBId --source $SourceB1Id --status confirmed
```

## D-05 Confirm SRC-C1 -> OBJ-C

```powershell
sgokb --db $Db association set `
  --object $ObjectCId --source $SourceC1Id --status confirmed
```

## D-06 Many-to-many SRC-R1 association

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceR1Id --status confirmed
sgokb --db $Db association set `
  --object $ObjectBId --source $SourceR1Id --status confirmed
```

## D-07 Re-read associations

```powershell
sgokb --db $Db association list --object $ObjectAId
sgokb --db $Db association list --object $ObjectBId
sgokb --db $Db association list --object $ObjectCId
```

**PASS D-01..D-07**: each Object contains the intended confirmed Source set and SRC-R1 is visible for both OBJ-A and OBJ-B.

---

# E. Evidence / Provenance

## E-01 Evidence candidates for OBJ-A

```powershell
$CandidatesA = sgokb --db $Db evidence candidates --object $ObjectAId | ConvertFrom-Json
$CandidatesA.data
```

**Verify**: candidate Evidence exists from confirmed Sources.

## E-02 Evidence selection

```powershell
$SelectedA = sgokb --db $Db evidence select --object $ObjectAId | ConvertFrom-Json
$SelectedA.data
```

Record at least one returned Evidence ID as `$EvidenceId`.

## E-03 Evidence detail

```powershell
sgokb --db $Db evidence show $EvidenceId
```

**PASS**: content and metadata are readable and correspond to the expected capture.

## E-04 Provenance

```powershell
sgokb --db $Db evidence provenance $EvidenceId
```

**Verify manually**: Evidence traces through normalization/snapshot/source identity to the expected Raw capture.

## E-05 Multi-source grounding

Run candidates/selection and inspect Source IDs:

```powershell
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: Evidence from SRC-A1 and SRC-A2 can be distinguished through provenance.

## E-06 Evidence search

Choose a distinctive phrase that exists in one of the captures:

```powershell
$EvidenceQuery = "<distinctive phrase from a test capture>"
sgokb --db $Db evidence search $EvidenceQuery --mode lexical --object $ObjectAId
```

**PASS**: the expected Evidence is returned.

---

# F. Evidence Package

## F-01 Build Package

```powershell
$Build = sgokb --db $Db package build `
  --object $ObjectAId `
  --build-root $BuildRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "F-01 failed" }
$PackageId = $Build.data.package_id
$BuildPath = $Build.data.path
$PackageId
$BuildPath
```

## F-02 Inspect manifest

```powershell
Get-ChildItem -Recurse $BuildPath
Get-Content (Join-Path $BuildPath "manifest.json") -Raw
```

**Verify**: target Object ID, package identity, base Version state if present, and selected Evidence membership match this test run.

## F-03 Inspect instructions

```powershell
Get-Content (Join-Path $BuildPath "instructions.md") -Raw
```

**PASS**: instructions are present and readable.

## F-04 Inspect packaged Evidence

```powershell
Get-ChildItem -Recurse $BuildPath
```

Open representative Evidence payload files and compare their IDs/content to E-02/E-04.

**PASS**: packaged Evidence is the selected grounded Evidence, not unrelated material.

## F-05 Stage Package

```powershell
$Stage = sgokb --db $Db package stage `
  $BuildPath --staging-root $StagingRoot | ConvertFrom-Json
$StagedPath = $Stage.data.path
$StagedPath
```

## F-06 Preflight

```powershell
$Preflight = sgokb --db $Db package preflight `
  $StagedPath --destination $ExportRoot | ConvertFrom-Json
$Preflight.data
```

**PASS**: the normal exportable disposition expected by this happy-path dataset is returned. If the selected dataset legitimately produces `review_required`, record that condition and use the standard explicit acknowledgement path only after human review; do not treat a true blocked condition as PASS.

## F-07 Explicit export

Normal exportable path:

```powershell
$Export = sgokb --db $Db package export `
  $StagedPath --destination $ExportRoot | ConvertFrom-Json
$ExportedPath = $Export.data.path
$ExportedPath
```

If F-06 legitimately required human acknowledgement and the operator approved it, use `--acknowledge-review`.

## F-08 Export integrity

```powershell
Get-ChildItem -Recurse $ExportedPath
```

**PASS**: manifest, instructions, and Evidence payload expected from the staged Package are present and readable.

---

# G. External ChatGPT / Structured Object Result

## G-01 Give the Package to ChatGPT

1. Open a new ChatGPT conversation dedicated to this acceptance object.
2. Provide the exported Package from `$ExportedPath`.
3. Do not add unrelated web facts or supplementary evidence for this test.

**PASS**: ChatGPT can read the Package contents.

## G-02 Establish instruction authority

Tell ChatGPT that `instructions.md` inside the Package is the authoritative analysis instruction and that the returned artifact must follow the current SGOKB Structured Object Result contract.

**PASS**: the generated result follows the Package instruction/schema requirements rather than free-form prose only.

## G-03 Inspect grounding

Before importing anything, manually inspect the result and compare representative claims with Package Evidence IDs.

**PASS**: claims intended for accepted Knowledge are grounded in Evidence actually present in the Package; no fabricated Evidence ID is used.

## G-04 Produce `result.json`

Have ChatGPT produce the final Structured Object Result and save it with the exact filename:

```text
result.json
```

**PASS**: artifact is syntactically JSON and follows current Result schema.

## G-05 Inspect Facets

Open `result.json` and identify the generated Facets for OBJ-A.

**PASS**: Facets are appropriate to the selected Object/class and grounded material.

## G-06 Inspect Statements

Inspect representative Statements under generated Facets.

**PASS**: Statements are structured, meaningful, and refer to valid packaged Evidence.

## G-07 Inspect Relation

For the test relation supported by SRC-R1, confirm the Result represents the intended OBJ-A <-> OBJ-B relation using the selected relation type and valid Evidence grounding.

**PASS**: relation target resolves to the intended stable Object identity and carries appropriate Evidence support.

## G-08 Place Result in incoming drop

```powershell
$DropDir = Join-Path $IncomingRoot "drop\$PackageId"
New-Item -ItemType Directory -Force $DropDir | Out-Null
Copy-Item "C:\path\to\generated\result.json" (Join-Path $DropDir "result.json") -Force
$ResultPath = Join-Path $DropDir "result.json"
Test-Path $ResultPath
```

**PASS**: `Test-Path` returns true and filename is exactly `result.json`.

---

# H. Result Intake / Validation / Import

## H-01 Detect Result

```powershell
sgokb --db $Db result detect --incoming-root $IncomingRoot
```

**PASS**: the Package drop containing `result.json` is detected.

## H-02 Receive Result

```powershell
$Receipt = sgokb --db $Db result receive `
  $ResultPath `
  --package-id $PackageId `
  --incoming-root $IncomingRoot | ConvertFrom-Json
$ReceiptId = $Receipt.data.receipt_id
$ReceiptId
```

Record `$ReceiptId`.

## H-03 List Results

```powershell
sgokb --db $Db result list --package-id $PackageId
```

**PASS**: `$ReceiptId` is visible.

## H-04 Pending Results

```powershell
sgokb --db $Db result pending
```

**PASS**: the received Result is visible in the expected pre-import state.

## H-05 Validate

```powershell
sgokb --db $Db result validate $ReceiptId --incoming-root $IncomingRoot
if ($LASTEXITCODE -ne 0) { throw "H-05 failed" }
```

**PASS**: Result reaches valid state with the normal happy-path artifact.

## H-06 Human review

```powershell
sgokb --db $Db result review `
  $ReceiptId --incoming-root $IncomingRoot --review-format markdown
```

Review Object identity, base Version, Facets, Statements, Relations, Evidence IDs, and Registry proposals before continuing.

**PASS**: proposed Knowledge is understandable and matches the intended result.

## H-07 Explicit Import

```powershell
$Imported = sgokb --db $Db result import `
  $ReceiptId --incoming-root $IncomingRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "H-07 failed" }
$Imported.data
```

If a legitimate review acknowledgement is required by the accepted normal flow, perform the human review first and use `--acknowledge-review` explicitly.

Record the newly created Knowledge Version ID as `$Version1Id` from the import response or H-08 read.

## H-08 Verify current pointer

```powershell
$CurrentA = sgokb --db $Db object show --object $ObjectAId --knowledge | ConvertFrom-Json
$CurrentA.data
```

**PASS**: current accepted Knowledge corresponds to the imported Result and `$Version1Id` is current.

## H-09 Verify Evidence links

Use the Knowledge read plus representative Evidence lookups:

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
sgokb --db $Db object relations --object $ObjectAId
```

For representative Statement/Relation Evidence IDs:

```powershell
sgokb --db $Db evidence show <evidence-id>
sgokb --db $Db evidence provenance <evidence-id>
```

**PASS**: accepted Knowledge links resolve to existing, correct Evidence.

---

# I. Registry Proposal

Use a Result containing one valid, harmless proposal that is supported by the test data. A supported alias proposal is a practical choice when appropriate.

## I-01 Verify proposal intake

After importing the Result containing the proposal:

```powershell
sgokb --db $Db registry proposal list --decision pending
```

Record the proposal reference as `$ProposalRef`.

**PASS**: proposal is pending and has not been silently applied.

## I-02 List pending proposals

```powershell
sgokb --db $Db registry proposal list --decision pending
```

**PASS**: `$ProposalRef` is present.

## I-03 Inspect proposal

```powershell
sgokb --db $Db registry proposal show $ProposalRef
```

**Verify**: kind, target/payload, and review context match the intended harmless change.

## I-04 Accept proposal

```powershell
sgokb --db $Db registry proposal accept `
  $ProposalRef --note "happy-path acceptance reviewed"
```

**PASS**: decision becomes accepted, but Registry mutation has not yet occurred solely because of acceptance.

## I-05 Apply proposal

```powershell
sgokb --db $Db registry proposal apply $ProposalRef
```

**PASS**: apply succeeds.

## I-06 Verify affected Registry/Object state

Choose the read command matching the proposal kind. For an alias proposal:

```powershell
sgokb --db $Db object alias list --object $ObjectAId
```

**PASS**: expected Registry mutation is now visible.

---

# J. Knowledge Versioning

## J-01 Capture Version 1 identity

From H-07/H-08, set and record:

```powershell
$Version1Id = "<accepted V1 knowledge_version_id>"
sgokb --db $Db version show $Version1Id
```

**PASS**: V1 is readable.

## J-02 Add later Evidence

Use the later SRC-A1 Snapshot from C-08, and ensure it is confirmed for OBJ-A if not already associated:

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1V2Id --status confirmed
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: new Evidence is available for a second analysis cycle.

## J-03 Build update Package

```powershell
$Build2 = sgokb --db $Db package build `
  --object $ObjectAId --build-root $BuildRoot | ConvertFrom-Json
$PackageId2 = $Build2.data.package_id
$BuildPath2 = $Build2.data.path
```

Inspect `manifest.json` and confirm the Package is bound to OBJ-A and current/base V1 as required by the current contract.

## J-04 Produce Result 2

Repeat F-05 through G-08 for `$PackageId2`, using the newly available Evidence and producing a valid updated `result.json`.

Record the second Result path as `$ResultPath2`.

## J-05 Validate/review/import Result 2

```powershell
$Receipt2 = sgokb --db $Db result receive `
  $ResultPath2 --package-id $PackageId2 --incoming-root $IncomingRoot | ConvertFrom-Json
$ReceiptId2 = $Receipt2.data.receipt_id

sgokb --db $Db result validate $ReceiptId2 --incoming-root $IncomingRoot
sgokb --db $Db result review $ReceiptId2 --incoming-root $IncomingRoot --review-format markdown
$Imported2 = sgokb --db $Db result import $ReceiptId2 --incoming-root $IncomingRoot | ConvertFrom-Json
```

Record `$Version2Id` from the import/current read.

## J-06 Verify V2 is current

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: V2 is current.

## J-07 Verify V1 remains preserved

```powershell
sgokb --db $Db version show $Version1Id
```

**PASS**: V1 still exists and is readable.

## J-08 Read both Versions directly

```powershell
sgokb --db $Db version show $Version1Id
sgokb --db $Db version show $Version2Id
```

## J-09 Diff V1 -> V2

```powershell
sgokb --db $Db version diff $Version1Id $Version2Id --diff-format markdown
```

**PASS**: expected additions/changes are represented and no unrelated destructive rewrite is observed.

## J-10 Historical Object read

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge --version $Version1Id
```

**PASS**: historical V1 state is returned rather than V2.

## J-11 Version-specific grounding

For representative V1 and V2 Statements/Relations, resolve their Evidence IDs with `evidence show` and `evidence provenance`.

**PASS**: both immutable Versions preserve their own correct grounding.

---

# K. Relation

## K-01 Verify imported Relation

```powershell
sgokb --db $Db object relations --object $ObjectAId
```

**PASS**: the Result-imported relation to OBJ-B is present in accepted Knowledge.

## K-02 Read from OBJ-A

```powershell
$RelationsA = sgokb --db $Db object relations --object $ObjectAId | ConvertFrom-Json
$RelationsA.data
```

**PASS**: target resolves to `$ObjectBId` as expected.

## K-03 Read related state from OBJ-B

```powershell
sgokb --db $Db object relations --object $ObjectBId
```

**PASS**: relation visibility/direction matches the selected relation-type contract. Do not require an inverse relation if the relation type does not define one.

## K-04 Inspect Relation Evidence

Read relation output with Evidence enabled (default), select a cited Evidence ID, then:

```powershell
sgokb --db $Db evidence show <relation-evidence-id>
sgokb --db $Db evidence provenance <relation-evidence-id>
```

**PASS**: evidence supports the relation.

## K-05 Version-specific Relation read

```powershell
sgokb --db $Db object relations --object $ObjectAId --version $Version1Id
sgokb --db $Db object relations --object $ObjectAId --version $Version2Id
```

**PASS**: each Version returns its own relation state; current/historical scope is not mixed.

---

# L. Render

## L-01 Render current OBJ-A

```powershell
$RenderCurrent = sgokb --db $Db render `
  --object $ObjectAId --output-root $RenderRoot | ConvertFrom-Json
$RenderCurrent.data
```

Open the generated Markdown file.

**PASS**: current accepted Knowledge is human-readable.

## L-02 Render a specific Version

```powershell
sgokb --db $Db render --version $Version1Id --output-root $RenderRoot
```

**PASS**: historical Version can be rendered independently.

## L-03 Verify Facets

Open the current render and compare its Facets with:

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: rendered Facets represent the same accepted Knowledge.

## L-04 Verify Relations

Compare rendered relation content with:

```powershell
sgokb --db $Db object relations --object $ObjectAId
```

**PASS**: relationship information is consistent.

## L-05 Verify grounding/provenance references

Follow representative Evidence identifiers shown by the read/render surface with:

```powershell
sgokb --db $Db evidence provenance <evidence-id>
```

**PASS**: rendered/read Knowledge remains traceable.

## L-06 Compare V1/V2 render

Render both Versions and compare the files manually or with PowerShell:

```powershell
# Substitute the actual output paths returned by render.
Compare-Object `
  (Get-Content "<V1-render-path>") `
  (Get-Content "<V2-render-path>")
```

**PASS**: expected Version differences are reflected.

---

# M. Lexical Search

## M-01 Search canonical name

```powershell
sgokb --db $Db search $ObjectAName --mode lexical
```

**PASS**: OBJ-A is returned.

## M-02 Search alias

```powershell
sgokb --db $Db search $ObjectAAlias --mode lexical
```

**PASS**: OBJ-A is discoverable according to the current lexical identity/search contract.

## M-03 Search distinctive Knowledge term

Pick a term present in accepted V2 Knowledge:

```powershell
$KnowledgeTerm = "<distinctive accepted-knowledge term>"
sgokb --db $Db search $KnowledgeTerm --mode lexical
```

**PASS**: expected Object is returned.

## M-04 Multi-object query

Choose a term shared by at least two test Objects:

```powershell
sgokb --db $Db search "<shared term>" --mode lexical --limit 10
```

**PASS**: multiple relevant Objects can be returned without duplicate Object identity rows being interpreted as separate Objects.

## M-05 Current scope

Use a term that changed between V1 and V2 and compare:

```powershell
sgokb --db $Db search "<current-specific term>" --mode lexical
sgokb --db $Db search "<historical-specific term>" --mode lexical --version $Version1Id
```

**PASS**: normal search uses current accepted scope; explicit Version filter can address historical scope.

## M-06 Cross-class lexical retrieval

Run class-relevant queries for OBJ-A/B/C and optionally class-filter them:

```powershell
sgokb --db $Db search "<character term>" --mode lexical --primary-class character
sgokb --db $Db search "<work term>" --mode lexical --primary-class work
sgokb --db $Db search "<concept term>" --mode lexical --primary-class concept
```

**PASS**: each class can be retrieved correctly.

---

# N. Semantic Search

Before N, ensure the accepted local Embedding runtime and Qdrant runtime are running and configured. This procedure must use the frozen local semantic composition; do not enable a cloud fallback.

## N-01 Start/verify semantic runtime

```powershell
sgokb --db $Db system index status
```

Then run a simple full-runtime semantic query:

```powershell
sgokb --db $Db search "<semantic query for OBJ-A>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: command succeeds with no runtime-unavailable exit.

## N-02 Index status

```powershell
sgokb --db $Db system index status
```

**PASS**: current index/Embedding Space state is reported as usable for this test composition.

## N-03 Rebuild index

```powershell
sgokb --db $Db system index rebuild
if ($LASTEXITCODE -ne 0) { throw "N-03 failed" }
```

If current environment requires semantic derived synchronization before/after index rebuild, run:

```powershell
sgokb --db $Db system derived sync --semantic-runtime
```

**PASS**: derived semantic state is rebuilt from canonical Knowledge without modifying canonical Versions.

## N-04 Semantic paraphrase query

Use a query that describes OBJ-A without copying exact source/Knowledge wording:

```powershell
sgokb --db $Db search `
  "<paraphrased semantic description of OBJ-A>" `
  --mode semantic --semantic-runtime --require-full-runtime --limit 10
```

**PASS**: OBJ-A is retrieved at a reasonable rank for the small acceptance dataset.

## N-05 Overview-level semantic retrieval

Use a broad query corresponding to the Object overview rather than one exact Statement.

```powershell
sgokb --db $Db search "<broad OBJ-A description>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: OBJ-A can be retrieved through current R2 representation family.

## N-06 Facet semantic retrieval

Select a real Facet from OBJ-A and query its meaning:

```powershell
sgokb --db $Db search "<facet semantic query>" `
  --mode semantic --semantic-runtime --require-full-runtime `
  --facet <facet-ref>
```

**PASS**: OBJ-A is returned for the intended Facet context.

## N-07 Statement semantic retrieval

Use a paraphrase of one distinctive Statement:

```powershell
sgokb --db $Db search "<statement paraphrase>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: OBJ-A is returned even when wording differs.

## N-08 Current Version scope

Use a V2-specific semantic concept, then explicitly query V1 when appropriate:

```powershell
sgokb --db $Db search "<V2-specific semantic concept>" `
  --mode semantic --semantic-runtime --require-full-runtime

sgokb --db $Db search "<V1-specific semantic concept>" `
  --mode semantic --semantic-runtime --require-full-runtime `
  --version $Version1Id
```

**PASS**: current and historical scopes remain distinct.

## N-09 Cross-class semantic retrieval

Run meaningful semantic queries that should identify OBJ-A, OBJ-B, and OBJ-C.

**PASS**: semantic retrieval is not limited to one test class.

---

# O. Hybrid Search

Use `--mode hybrid --semantic-runtime --require-full-runtime` so this acceptance section proves both channels are actually available.

## O-01 Name + meaning query

```powershell
sgokb --db $Db search `
  "$ObjectAName <semantic description>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: OBJ-A is returned and no degradation warning indicates a missing semantic channel.

## O-02 Exact identity prominence

```powershell
sgokb --db $Db search $ObjectAName `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: exact identity remains easy to find and is not lost among semantically similar Objects.

## O-03 Lexically distinctive Knowledge query

```powershell
sgokb --db $Db search "<distinctive literal knowledge phrase>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: relevant Object is retrieved.

## O-04 Semantically descriptive query

```powershell
sgokb --db $Db search "<paraphrased meaning>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: semantic contribution can retrieve the intended Object.

## O-05 Object aggregation

Run a query matching several Facets/Statements of OBJ-A:

```powershell
$Hybrid = sgokb --db $Db search "<multi-aspect OBJ-A query>" `
  --mode hybrid --semantic-runtime --require-full-runtime --limit 10 | ConvertFrom-Json
$Hybrid.data
```

**PASS**: OBJ-A is represented as one Object result, not repeated as separate overview/facet/statement result rows.

---

# P. Similarity

Similarity requires configured semantic runtime/index state.

## P-01 Object similarity

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

**PASS**: similar Objects are returned and source Object identity is handled according to the similarity contract.

## P-02 Facet-specific similarity

Select an actual Facet present in OBJ-A:

```powershell
sgokb --db $Db similar `
  --object $ObjectAId --facet <facet-ref> --limit 10
```

**PASS**: facet-specific comparison succeeds and uses the requested Facet.

## P-03 Human sanity check of ranking

Compare the top results with the known content of OBJ-B/OBJ-C and the selected small dataset.

**PASS**: ordering is semantically plausible enough for operational use; this is a sanity check, not the Phase N formal ANN-quality benchmark.

## P-04 Current Version similarity

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

Then explicitly compare a historical Version where supported:

```powershell
sgokb --db $Db similar --object $ObjectAId --version $Version1Id --limit 10
```

**PASS**: default/current and explicit historical scope are distinguishable.

## P-05 Cross-class similarity

```powershell
sgokb --db $Db similar `
  --object $ObjectAId --cross-class --limit 10
```

**PASS**: cross-class candidates can be returned according to current similarity semantics.

---

# Q. MCP Read Boundary

Configure the MCP client to launch the acceptance DB, not production DB.

Core/lexical server command:

```text
sgokb --db <ABSOLUTE_ACCEPTANCE_DB_PATH> mcp serve
```

For semantic MCP tests:

```text
sgokb --db <ABSOLUTE_ACCEPTANCE_DB_PATH> mcp serve --semantic-runtime
```

Use the connected MCP client UI/tool inspector for Q-01..Q-12.

## Q-01 `get_object`

Call:

```text
get_object({"object_id":"<OBJ-A-ID>"})
```

**PASS**: Object ID and current accepted Version match CLI `object show --knowledge`.

## Q-02 `get_objects`

Call with OBJ-A/B/C IDs according to the exposed schema.

**PASS**: all requested Objects are returned with correct stable identities.

## Q-03 `search_objects`

Call a lexical query first:

```text
search_objects({"query":"<known term>","mode":"lexical","limit":10})
```

Then, on semantic-enabled server, call a hybrid query.

**PASS**: expected Objects match the CLI retrieval semantics.

## Q-04 `find_similar_objects`

```text
find_similar_objects({"object_id":"<OBJ-A-ID>","limit":10})
```

**PASS**: similarity read succeeds through MCP.

## Q-05 `get_object_relations`

```text
get_object_relations({"object_id":"<OBJ-A-ID>"})
```

**PASS**: expected OBJ-A -> OBJ-B relation is returned with the same accepted Version semantics as CLI.

## Q-06 `get_object_evidence`

```text
get_object_evidence({"object_id":"<OBJ-A-ID>"})
```

**PASS**: grounded Evidence is returned for OBJ-A.

## Q-07 `search_evidence`

Call with the distinctive E-06 query according to the tool schema.

**PASS**: expected Evidence is found.

## Q-08 `build_context`

```text
build_context({
  "object_ids":["<OBJ-A-ID>","<OBJ-B-ID>"],
  "purpose":"comparison",
  "max_characters":12000
})
```

**PASS**: deterministic Knowledge subset is returned; no new LLM-authored fact is inserted by Context Builder.

## Q-09 CLI/MCP consistency

Compare Q-01 with:

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: both resolve the same current accepted Knowledge Version.

## Q-10 Comparison context

Use OBJ-A and OBJ-B with `purpose = comparison`.

**PASS**: returned subset contains relevant stored Knowledge from both Objects.

## Q-11 Character budget

Call `build_context` with a deliberately modest but valid budget such as `max_characters = 6000`.

**PASS**: returned context remains within the requested budget contract.

## Q-12 Determinism

Repeat Q-08 with identical inputs and unchanged DB state.

**PASS**: selected content/order is identical according to the deterministic Context Builder contract.

---

# R. Derived Index

## R-01 Index status

```powershell
sgokb --db $Db system index status
sgokb --db $Db system derived status --semantic-runtime
```

Record current derived state.

## R-02 Rebuild derived/index state

```powershell
sgokb --db $Db system derived sync --semantic-runtime
sgokb --db $Db system index rebuild
```

**PASS**: rebuild/sync succeeds using canonical accepted Knowledge.

## R-03 Lexical read after rebuild

Repeat M-01/M-03.

**PASS**: canonical/lexical read remains correct after derived maintenance.

## R-04 Semantic read after rebuild

Repeat N-04.

**PASS**: expected Object is returned.

## R-05 Similarity after rebuild

Repeat P-01/P-02.

**PASS**: similarity remains functional.

## R-06 Representation/Embedding reuse sanity check

Run derived sync a second time without changing canonical Knowledge:

```powershell
$Before = sgokb --db $Db system derived status --semantic-runtime | ConvertFrom-Json
sgokb --db $Db system derived sync --semantic-runtime
$After = sgokb --db $Db system derived status --semantic-runtime | ConvertFrom-Json
$Before.data
$After.data
```

**PASS**: unchanged canonical Knowledge does not produce semantically duplicated current state; IDs/counts reported by the status surface remain consistent with reuse/idempotent maintenance semantics. This is an operational sanity check, not the internal N-02 deterministic fixture assertion.

---

# S. Backup / Restore Happy Path

Use only the acceptance DB and test-owned backup/restore paths.

## S-01 Backup status

```powershell
sgokb --db $Db system backup status --root $BackupRoot
```

**PASS**: backup subsystem status is readable.

## S-02 Create backup

```powershell
$Backup = sgokb --db $Db system backup create --root $BackupRoot | ConvertFrom-Json
$Backup.data
```

Record the returned backup path as `$BackupPath`.

## S-03 Verify backup integrity

If the backup command returns integrity/verification metadata, inspect it. Also run:

```powershell
Test-Path $BackupPath
```

**PASS**: backup exists and creation completed successfully with its normal integrity verification.

## S-04 Restore plan

Plan restore to the isolated restore target according to the command output/contract:

```powershell
sgokb --db $RestoreDb system restore plan $BackupPath
```

**PASS**: plan describes the intended test-owned backup and restore target. Do not continue if it resolves to production state.

## S-05 Apply restore

For a fresh restore target, run the normal restore apply path:

```powershell
sgokb --db $RestoreDb system restore apply $BackupPath
```

If the current CLI requires explicit overwrite acknowledgement because the target file already exists, delete/recreate the test-owned target as appropriate or use `--acknowledge-overwrite` only after confirming the target is the disposable acceptance restore DB.

**PASS**: restore completes successfully.

## S-06 Restored integrity

```powershell
sgokb --db $RestoreDb system integrity
```

**PASS**: integrity succeeds.

## S-07 Restored Objects

```powershell
sgokb --db $RestoreDb object show --object $ObjectAId --knowledge
sgokb --db $RestoreDb object show --object $ObjectBId --knowledge
sgokb --db $RestoreDb object show --object $ObjectCId --knowledge
```

**PASS**: Object stable identities are preserved.

## S-08 Restored Versions

```powershell
sgokb --db $RestoreDb version show $Version1Id
sgokb --db $RestoreDb version show $Version2Id
```

**PASS**: accepted Version history is preserved.

## S-09 Restored Evidence / Provenance

```powershell
sgokb --db $RestoreDb evidence show $EvidenceId
sgokb --db $RestoreDb evidence provenance $EvidenceId
```

**PASS**: grounded provenance remains resolvable.

## S-10 Rebuild derived state after restore

Configure the restored test environment to use a test-owned semantic/vector target, then:

```powershell
sgokb --db $RestoreDb system derived sync --semantic-runtime
sgokb --db $RestoreDb system index rebuild
```

**PASS**: derived state can be regenerated from restored canonical state.

## S-11 Search restored Knowledge

```powershell
sgokb --db $RestoreDb search $ObjectAName --mode lexical
sgokb --db $RestoreDb search "<semantic OBJ-A query>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: both local lexical and configured semantic read paths work after restore.

## S-12 Render restored Knowledge

```powershell
sgokb --db $RestoreDb render --object $ObjectAId --output-root "$RenderRoot/restored"
```

**PASS**: current restored Knowledge renders successfully.

---

# T. Final uninterrupted end-to-end run

After A-S have been understood individually, run one fresh Object through the normal workflow without manually editing SQLite or bypassing a boundary.

## T-01 Full normal operational chain

Use a new valid test Object and one or more new valid capture bundles.

Execute in this order:

```text
1.  system integrity
2.  object add
3.  source import
4.  source process
5.  association set --status confirmed
6.  evidence candidates
7.  evidence select
8.  package build
9.  package stage
10. package preflight
11. package export
12. external ChatGPT analysis under instructions.md
13. save exact result.json
14. result detect
15. result receive
16. result validate
17. result review
18. result import
19. object show --knowledge
20. object relations
21. render
22. lexical search
23. semantic search with full runtime
24. hybrid search with full runtime
25. similar
26. MCP get_object
27. MCP search_objects
28. MCP build_context
29. system backup create
30. final system integrity
```

At each step record returned stable IDs and verify that the identity chain remains internally consistent.

**T-01 PASS requires all of the following**:

- no required step is skipped;
- every command expected to succeed exits successfully;
- external export is explicit;
- external AI uses Package Evidence rather than fabricated provenance;
- Result is validated and reviewed before explicit Import;
- accepted Knowledge is a Version, not an overwrite of historical accepted state;
- representative Knowledge remains traceable to Evidence and Raw Source lineage;
- lexical, semantic, hybrid, similarity, render, and MCP read surfaces resolve the same canonical Object/Version semantics;
- backup creation succeeds after the completed workflow;
- final `system integrity` succeeds.

---

# 3. Completion decision

## Core PASS

Declare **Core PASS** only when all applicable tests through the local canonical/read workflow have passed, including:

```text
A Environment / CLI
B Object Registry
C Source / Snapshot / Raw
D Association
E Evidence / Provenance
F Evidence Package
G External semantic integration
H Result intake / validation / review / import
I Registry Proposal
J Versioning
K Relation
L Render
M Lexical Search
T end-to-end core chain
```

## Full SGOKB PASS

Declare **Full SGOKB PASS** only when Core PASS plus all optional-runtime/full-system acceptance sections are complete:

```text
N Semantic Search
O Hybrid Search
P Similarity
Q MCP read boundary
R Derived Index
S Backup / Restore
T full uninterrupted run including semantic/MCP/backup steps
```

The final acceptance record must include the exact DB path, test date, repository commit/release identity, semantic runtime identity where used, Object/Version IDs, and overall verdict.
