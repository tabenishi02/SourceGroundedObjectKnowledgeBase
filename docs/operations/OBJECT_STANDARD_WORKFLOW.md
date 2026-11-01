# 1 Object Standard Workflow

更新日: 2026-10-31

- Status: **Current / Accepted through Phase P**
- Release candidate: `2.0.0`
- CLI contract: `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- Raw-grounding authority: `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`

> 目的: 1 ObjectをObject登録からSource/Raw/Evidence、Raw-grounded Package v2、external analysis、Result v2 import、derived sync、Search、GUI/MCP readまで、public SGOKB interfacesだけで処理する。

## 0. PowerShell variables

```powershell
$Db = ".local/sgokb.sqlite"
$Bundle = "C:\path\to\capture.webcapture.zip"
$ObjectName = "Target Object"
$PrimaryClass = "character"
$ExportRoot = "C:\path\to\sgokb-export"
$IncomingRoot = "exchange/incoming"
```

Start with:

```powershell
sgokb --db $Db system integrity
sgokb --db $Db system status
sgokb --db $Db registry class show $PrimaryClass
```

Non-zero exit codes must be handled at the operation that produced them; do not continue a blocked/review-required/integrity-failed workflow silently.

## 1. Object -> Source -> Raw / Evidence

Create or resolve the Object:

```powershell
$ObjectResult = sgokb --db $Db object add --name $ObjectName --primary-class $PrimaryClass | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "object add failed" }
$ObjectId = $ObjectResult.data.object_id
```

Import and normalize the capture:

```powershell
$ImportResult = sgokb --db $Db source import $Bundle | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "source import failed" }
$SourceId = $ImportResult.data[0].source
$SnapshotId = $ImportResult.data[0].snapshot

$ProcessResult = sgokb --db $Db source process --snapshot $SnapshotId | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "source process failed" }
$RunId = $ProcessResult.data[0].run
```

For a follow-up generation on an existing Source, review it and explicitly select the accepted Snapshot/Run when appropriate:

```powershell
sgokb --db $Db source select-snapshot --source $SourceId --snapshot $SnapshotId --reason "operator reviewed follow-up capture"
sgokb --db $Db source select-run --snapshot $SnapshotId --run $RunId --reason "operator reviewed normalization"
```

Confirm Source/Object association and select Evidence:

```powershell
sgokb --db $Db association list --object $ObjectId
sgokb --db $Db association set --object $ObjectId --source $SourceId --status confirmed
sgokb --db $Db evidence candidates --object $ObjectId
sgokb --db $Db evidence select --object $ObjectId
```

Evidence is the selection/provenance layer. Package v2 resolves selected Evidence through each Evidence's original Normalization Run to the complete input Raw Artifact set.

## 2. Build Raw-grounded Package v2

In `2.0.0`, v2 is the no-option default:

```powershell
$Build = sgokb --db $Db package build --object $ObjectId | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "package build failed" }
$PackageId = $Build.data.package_id
$BuildPath = $Build.data.path
```

Equivalent explicit form:

```powershell
sgokb --db $Db package build --object $ObjectId --package-version v2
```

Legacy v1 is retained only when explicitly requested:

```powershell
sgokb --db $Db package build --object $ObjectId --package-version v1
```

Do not use v1 for a new Raw-grounded workflow.

Package v2 contains exact verified Package-member Raw bytes and binds the Raw grounding set. It does not make generated Evidence Markdown the claim-level semantic authority.

## 3. Stage / preflight / explicit export

```powershell
$Stage = sgokb --db $Db package stage $BuildPath | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "package stage failed" }
$StagedPath = $Stage.data.path

$Preflight = sgokb --db $Db package preflight $StagedPath --destination $ExportRoot | ConvertFrom-Json
$Preflight.data
```

Disposition handling:

```text
allow            -> export command may be executed explicitly
review_required  -> inspect and use --acknowledge-review only after Human approval
blocked          -> do not export
```

Normal export:

```powershell
$Export = sgokb --db $Db package export $StagedPath --destination $ExportRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "package export failed" }
$ExportedPath = $Export.data.path
```

Export remains a Human decision boundary.

## 4. External analysis

Give `$ExportedPath` to the external AI and treat the Package `instructions.md` as the authoritative analysis instruction.

For Package v2:

```text
new semantic claim grounding = Package-member raw_artifact_id only
current_object.json           = accepted base Knowledge context, not new evidence
locator                        = only when mechanically justifiable
Package-external knowledge    = not valid grounding
```

Save the resulting Structured Object Result as:

```text
<IncomingRoot>/drop/<PackageId>/result.json
```

External AI analysis remains outside the SGOKB runtime and Human-in-the-loop.

## 5. Result v2 -> accepted Knowledge Version

Detect and receive:

```powershell
sgokb --db $Db result detect --incoming-root $IncomingRoot

$ResultPath = Join-Path $IncomingRoot "drop\$PackageId\result.json"
$Receipt = sgokb --db $Db result receive $ResultPath --package-id $PackageId --incoming-root $IncomingRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "result receive failed" }
$ReceiptId = $Receipt.data.receipt_id
```

Validate and review:

```powershell
sgokb --db $Db result validate $ReceiptId --incoming-root $IncomingRoot
if ($LASTEXITCODE -ne 0) { throw "result validation failed" }

sgokb --db $Db result review $ReceiptId --incoming-root $IncomingRoot --review-format markdown
```

Import only after validation/review and required Human acknowledgement:

```powershell
$Imported = sgokb --db $Db result import $ReceiptId --incoming-root $IncomingRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "result import failed" }
```

For v2 claim grounding, successful import stores Raw grounding as Raw grounding. Do not synthesize Evidence claim links by reverse-mapping Package selection lineage.

Registry proposals remain a separate explicit review/apply workflow.

## 6. Accepted Knowledge and derived state

Verify canonical Knowledge:

```powershell
sgokb --db $Db object show --object $ObjectId --knowledge
sgokb --db $Db object relations --object $ObjectId
sgokb --db $Db render --object $ObjectId
```

Synchronize lexical derived state before expecting Knowledge-body lexical retrieval:

```powershell
sgokb --db $Db system derived status --object $ObjectId
sgokb --db $Db system derived sync --object $ObjectId
sgokb --db $Db system derived status --object $ObjectId
```

Then verify lexical retrieval:

```powershell
sgokb --db $Db search $ObjectName --mode lexical
sgokb --db $Db search "<distinctive accepted-knowledge term>" --mode lexical
```

With the accepted local semantic runtime configured:

```powershell
sgokb --db $Db system derived sync --object $ObjectId --semantic-runtime
sgokb --db $Db search $ObjectName --mode semantic --semantic-runtime --require-full-runtime
sgokb --db $Db similar --object $ObjectId
```

Search Representation, Embedding, Qdrant Vector Index and rendering are derived/rebuildable; they must not overwrite accepted canonical Knowledge.

## 7. GUI verification

Windows source-checkout normal launch:

```text
scripts\launch-sgokb-gui.vbs
```

The launcher must leave no console/script window open and should show the startup Splash before the main window. The package entrypoint remains valid for explicit shell launch:

```powershell
sgokb-gui
```

Open the same Workspace. GUI reads/writes must resolve through the shared Application/operator layer and therefore the same canonical state as the CLI.

Use `System > Overview` to inspect the shared runtime-health projection. Qdrant lifecycle owner must remain `external`; no Start/Stop/Restart control is part of the accepted GUI boundary. If current accepted Knowledge exists with no explicit Search-generation pointer, the supported state is `Search generation = HEALTHY / active=none (legacy routing)` and dashboard refresh must not create an explicit generation.

## 8. MCP read verification

Configure an MCP client to launch:

```text
sgokb --db <DB_PATH> mcp serve
```

Read the Object and confirm that it resolves the same accepted Version as `object show --knowledge`.

MCP is read-only for canonical operations and is externally launched; the GUI does not own a detached MCP daemon.

## 9. Runtime / recovery checks

Minimum operational checks:

```powershell
sgokb --db $Db system status
sgokb --db $Db system integrity
sgokb --db $Db system index status
```

If Qdrant-derived Vector state must be rebuilt after runtime recovery:

```powershell
sgokb --db $Db system index rebuild
```

On Windows, Qdrant is externally owned by Task Scheduler task `\SGOKB\Qdrant`; SGOKB observes `/readyz` but does not start/stop/restart Qdrant itself.

## 10. Completion criteria

A normal `2.0.0` Object workflow is complete when:

- Object identity and Source/Raw/Evidence provenance are preserved;
- Package v2 is built from exact Raw material resolved from selected Evidence lineage;
- export and import Human decision boundaries are not bypassed;
- Result v2 validates and claim grounding is Package-member Raw grounding;
- accepted Version is created without rewriting history;
- derived state can be synchronized/rebuilt from canonical state;
- CLI and GUI resolve the same canonical state;
- MCP read resolves the same accepted Version;
- runtime degradation does not mutate canonical Knowledge;
- final `system integrity` is successful.
