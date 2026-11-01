# Source Grounded Object Knowledge Base (SGOKB)

**Source Grounded Object Knowledge Base (SGOKB)** is a local-first knowledge base that preserves user-selected source material with provenance and turns reviewed material into long-lived, versioned Object Knowledge.

Canonical Knowledge stays in structured SQLite-backed Object/Version state. Raw source material and provenance remain traceable. Search, rendering, GUI and Vector state are derived layers rather than replacement truth stores.

## Status

```text
Phase A ... Phase O        = Complete
Phase P GUI workstream     = Complete / Accepted
Phase P RAW workstream     = Complete / Accepted
Phase P Runtime workstream = Complete / Accepted
P-CLOSE-01                 = Complete / Accepted
Current formal release     = v2.0.0
Project state              = Paused / no active implementation task
```

The annotated `v2.0.0` tag is frozen on release commit `1adae99ee62c3054a35b1325b8a43716943ff06a`. Later `main` commits may contain post-release documentation bookkeeping without moving that immutable release boundary.

## What changed in 2.0.0

### Raw-grounded Package v2 is the default

```text
selected Evidence
  -> original Normalization Run
  -> complete input Raw Artifact set
  -> exact verified Raw bytes
  -> Package v2
  -> external AI
  -> Result v2 raw_artifact_id grounding
  -> validate / review / import
  -> accepted Knowledge Version
```

The no-option Package command targets v2:

```powershell
sgokb --db <db> package build --object <OBJECT_ID>
```

Legacy Package v1 remains available explicitly:

```powershell
sgokb --db <db> package build --object <OBJECT_ID> --package-version v1
```

### PySide6 desktop GUI

SGOKB includes a PySide6/Qt Widgets desktop client over the same Application/operator boundary as the CLI.

```powershell
sgokb-gui
```

For a Windows source checkout with the repository virtual environment installed, the normal consoleless operator launcher is also available:

```text
scripts\launch-sgokb-gui.vbs
```

The VBS launcher uses `.venv\Scripts\pythonw.exe`, leaves no PowerShell/CMD/script console open, and shows the SGOKB startup splash before the main window while runtime/view modules and local semantic native dependencies are initialized. The packaged `sgokb-gui` entrypoint remains supported and is not replaced by this repository-local launcher.

The GUI does not shell out to the CLI for canonical work and does not own a parallel SQLite write path. It covers the accepted public operation inventory through domain pages, Package/Result workflow, Search, Registry, System/Maintenance and Runtime Dashboard surfaces.

### Native Windows Qdrant runtime

The accepted Windows reference runtime is native `qdrant.exe` owned by Windows Task Scheduler:

```text
Task                = \SGOKB\Qdrant
startup             = AtLogOn
crash recovery      = repeating 60 s trigger
readiness           = GET /readyz -> HTTP 200
SGOKB lifecycle     = observer/client only
```

SGOKB exposes runtime health but no Qdrant start/stop/restart actions.

## Installation

Python 3.10+ is required.

Base development environment with the accepted GUI, local embedding and Qdrant client can be installed with:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,mcp,gui,local-embedding,vector-qdrant]"
```

Minimal installations may select only the optional groups they need.

## Standard workflow

### 1. Prepare and verify a Workspace

```powershell
$Db = ".local/sgokb.sqlite"
sgokb --db $Db system integrity
sgokb --db $Db system status
```

### 2. Create an Object and ingest source material

```powershell
$Object = sgokb --db $Db object add --name "Target Object" --primary-class character | ConvertFrom-Json
$ObjectId = $Object.data.object_id

$Import = sgokb --db $Db source import C:\path\capture.webcapture.zip | ConvertFrom-Json
$SnapshotId = $Import.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotId
```

Associate the Source with the Object and review/select Evidence through the normal operator workflow.

### 3. Build the default Raw-grounded Package v2

```powershell
$Build = sgokb --db $Db package build --object $ObjectId | ConvertFrom-Json
$PackagePath = $Build.data.path

$Stage = sgokb --db $Db package stage $PackagePath | ConvertFrom-Json
sgokb --db $Db package preflight $Stage.data.path --destination C:\path\export
```

Export remains an explicit Human decision boundary.

### 4. External analysis and Result import

The external AI must follow the Package `instructions.md` and Result v2 schema. New claim grounding is limited to Package-member Raw Artifacts.

After receiving `result.json`:

```powershell
sgokb --db $Db result detect --incoming-root exchange/incoming
sgokb --db $Db result receive <result.json> --package-id <PACKAGE_ID> --incoming-root exchange/incoming
sgokb --db $Db result validate <RECEIPT_ID> --incoming-root exchange/incoming
sgokb --db $Db result review <RECEIPT_ID> --incoming-root exchange/incoming --review-format markdown
sgokb --db $Db result import <RECEIPT_ID> --incoming-root exchange/incoming
```

Validation/review must not be bypassed.

### 5. Rebuild derived state and search

```powershell
sgokb --db $Db system derived sync --object $ObjectId
sgokb --db $Db search "query" --mode lexical
```

With the local semantic runtime configured:

```powershell
sgokb --db $Db system derived sync --object $ObjectId --semantic-runtime
sgokb --db $Db search "query" --mode semantic --semantic-runtime --require-full-runtime
sgokb --db $Db similar --object $ObjectId
```

### 6. GUI and MCP

GUI:

```powershell
sgokb-gui
```

Read-only MCP server:

```powershell
sgokb --db $Db mcp serve
```

MCP remains an external stdio lifecycle; the GUI does not claim ownership of a detached MCP daemon.

## Runtime health and recovery

```powershell
sgokb --db $Db system status
sgokb --db $Db system integrity
sgokb --db $Db system index status
```

`system status` exposes the shared `sgokb.runtime-health/1.0` projection used by the GUI Runtime Dashboard. When current accepted Knowledge exists without an explicit Search-generation pointer, the supported compatibility route is reported as `Search generation = HEALTHY` with `active=none (legacy routing)`; only a broken/stale explicit generation is degraded.

If the rebuildable Vector Index needs recovery after Qdrant is healthy:

```powershell
sgokb --db $Db system index rebuild
```

Canonical Knowledge must not be rewritten to repair derived runtime state.

## Current architecture

Start with:

- `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- `docs/evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md`
- `docs/releases/v2.0.0.md`

## Release and distribution boundary

`v2.0.0` is the current formal MAJOR release. The breaking change is that the default public Package/Result exchange semantics move from v1 to Raw-grounded v2.

The repository/source release includes the PySide6 GUI implementation, but P-CLOSE-01 does not publish or certify a standalone GUI binary artifact. The SGOKB project license has not been separately selected, and packaged Qt/PySide6 redistribution remains subject to the P-GUI-02 license/artifact gate. Those items are deferred future distribution work, not unfinished `v2.0.0` release work.

See `docs/decisions/P_CLOSE_01_RELEASE_INTEGRATION_DECISION.md` and `docs/evaluation/P_CLOSE_01_THIRD_PARTY_LICENSE_INVENTORY.md`.

## Project checkpoint

There is no active implementation task after Phase P / `v2.0.0`. The project is intentionally paused at this stable checkpoint. Future work should begin from the current `main` documentation state while treating tag `v2.0.0` as the immutable released baseline.
