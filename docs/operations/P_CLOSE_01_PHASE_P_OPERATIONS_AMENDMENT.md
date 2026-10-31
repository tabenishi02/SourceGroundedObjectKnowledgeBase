# P-CLOSE-01 — Phase P Operations Amendment

Updated: 2026-10-31

- Status: **Current release-integration amendment**
- Target release: `2.0.0`
- Applies with: `OBJECT_STANDARD_WORKFLOW.md`, `OPERATIONAL_SAFETY_RECOVERY.md`

## Purpose

This amendment records the Phase P operational changes that supersede older Evidence-only / Docker-oriented assumptions without replacing the established backup, restore, retention and integrity rules.

## Exchange operation

The normal `2.0.0` Package build is Raw-grounded v2:

```powershell
sgokb --db <db> package build --object <OBJECT_ID>
```

Explicit legacy v1 remains:

```powershell
sgokb --db <db> package build --object <OBJECT_ID> --package-version v1
```

Package v2 resolves selected Evidence to the complete input Raw Artifact set of each Evidence's original Normalization Run, verifies exact bytes/hash and exports Raw material under the audited Package manifest. Result v2 claim grounding uses Package-member `raw_artifact_id` values.

Existing preflight/export and validate/review/import Human decision boundaries remain mandatory.

## Windows Qdrant operation

The accepted Windows runtime authority is:

```text
binary            = native qdrant.exe
Task Scheduler    = \SGOKB\Qdrant
startup           = AtLogOn
crash recovery    = repeating TimeTrigger / 60 s default
principal         = Interactive / Limited
readiness         = GET /readyz -> HTTP 200
SGOKB role        = observer/client only
```

Operator lifecycle action belongs to Windows Task Scheduler, not to SGOKB CLI/GUI.

Do not reintroduce the superseded S4U/hidden-console or RestartOnFailure-only configuration as the reference design.

## Runtime observation

Use:

```powershell
sgokb --db <db> system status
sgokb --db <db> system integrity
sgokb --db <db> system index status
```

The GUI uses `System > Overview` / Runtime Dashboard over the same `sgokb.runtime-health/1.0` projection.

Expected lifecycle projection:

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

## Failure / recovery

If Qdrant is unavailable:

- canonical reads and lexical operations remain available where their own dependencies are healthy;
- Semantic Search may be blocked/degraded explicitly;
- the GUI/CLI must show Qdrant unavailable rather than silently treating an open port as ready;
- accepted canonical Knowledge must not be rewritten.

After Qdrant recovery and `/readyz` HTTP 200, rebuildable Vector state may be recovered with:

```powershell
sgokb --db <db> system index rebuild
```

P-RUNTIME-06 accepted wrong-service fail-closed behavior, persistent collections across restart, public Vector rebuild, and post-rebuild SQLite/canonical-count integrity.

## GUI operation

The PySide6 GUI is a first-class operator interface over the shared Application/operator layer:

```powershell
sgokb-gui
```

It is not a CLI subprocess wrapper and does not own a separate canonical persistence path.

MCP remains external stdio lifecycle. Use the GUI MCP surface for configuration/command guidance, not daemon start/stop ownership.

## Backup / restore

Phase P does not change the canonical recovery priority established in `OPERATIONAL_SAFETY_RECOVERY.md`:

```text
canonical SQLite + required Raw / Result provenance
  -> restore / integrity verification
  -> derived Search Representation / Embedding / Qdrant / rendering rebuild
```

Vector state remains rebuildable and is not a substitute for canonical Raw/provenance backup closure.

## Distribution operation

P-CLOSE-01 closes the repository/source release. It does not publish a standalone GUI binary. Binary publication requires the separate project-license and Qt/PySide6 artifact license gate.
