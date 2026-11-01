# SGOKB Current System Architecture

Updated: 2026-10-31

- Status: **Current / Accepted through Phase P**
- Release candidate: `2.0.0`
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Closure task: `P-CLOSE-01`
- Historical Prototype / research documents do not override this document.

## 1. Purpose and authority

Source Grounded Object Knowledge Base (SGOKB) is a local-first knowledge base that preserves user-selected source material with provenance, transforms reviewed material into versioned Object Knowledge, and exposes that Knowledge through CLI, GUI, Search and read-only MCP interfaces.

This document is the current end-to-end architecture map. Detailed schema and domain contracts remain authoritative for their own scope.

Authority order:

```text
accepted requirements / decisions / design contracts
  -> current implementation contracts
  -> current operations / acceptance evidence
  -> this integrated architecture map
  -> historical / archived material
```

## 2. Architectural invariants

```text
canonical Knowledge        = SQLite Object / Version / Registry / grounding/provenance state
canonical source material  = Source / Snapshot / Normalization Run / Raw Artifact / Evidence lineage
accepted external result   = validated + reviewed Result imported into immutable Version history
rebuildable derived state  = rendering / Search Representation / Embedding / Qdrant Vector Index
operator interfaces        = CLI + PySide6 GUI over the shared Application/operator layer
MCP                        = read-only external stdio integration
Qdrant lifecycle           = external to SGOKB
external AI                = explicit Human-in-the-loop exchange boundary
```

GUI, Search, rendering and Vector state MUST NOT become independent canonical truth stores.

## 3. Current end-to-end flow

The `2.0.0` primary workflow is:

```text
Web Capture / local input
  -> Source
  -> Snapshot
  -> Raw Artifact
  -> Normalization Run
  -> Evidence
  -> Object association / Evidence selection
  -> Evidence-to-Raw provenance resolution
  -> Package v2 with exact verified Raw bytes
  -> explicit export / external AI
  -> Result v2 using raw_artifact_id grounding
  -> receive / validate / review / explicit import
  -> immutable accepted Knowledge Version
  -> derived Search Representation / Embedding / Qdrant / rendering
  -> CLI / GUI / Search / read-only MCP
```

Package v1 / Result v1 remains an explicit legacy compatibility family. Historical v1 artifacts retain their original semantics.

## 4. Object and Knowledge model

Stable identity is `object_id`. Names, aliases, Class membership and status may evolve without changing identity.

Accepted semantic Knowledge is versioned and immutable. A current Version pointer selects the effective accepted state; historical Versions remain addressable. Relations retain canonical direction and provenance rather than synthesizing duplicate inverse canonical facts.

Core semantic organization remains:

```text
Object
  -> Class membership
  -> Facet
  -> Statement / Attribute / Relation
  -> grounding / provenance
  -> immutable Knowledge Version
```

## 5. Source, Evidence and Raw grounding

Source capture preserves historical generations. A later Snapshot or Normalization Run does not silently replace an explicitly selected effective generation.

Evidence remains the operator-facing selection and provenance layer. For Package v2, claim-level external semantic authority is the Package-member Raw Artifact set, not generated Evidence Markdown.

```text
Evidence
  -> its original Normalization Run
  -> complete run-input Raw Artifact set
  -> exact byte/hash verification
  -> Package v2 membership
```

Result v2 claim grounding uses `raw_artifact_id` and optional mechanically verifiable locators. Successful v2 import stores `raw_grounding_links`; it does not synthesize Evidence claim links by reverse mapping.

## 6. Exchange contract

Release `2.0.0` changes the default:

```text
sgokb package build --object <OBJECT_ID>
  -> Package v2
```

Legacy behavior remains explicit:

```text
sgokb package build --object <OBJECT_ID> --package-version v1
```

Package export remains a Human decision boundary with `allow`, `review_required` and `blocked` dispositions. External Result import remains explicit after validation and review.

## 7. Shared Application boundary and interfaces

CLI and GUI are presentation surfaces over the same Application/operator operations.

```text
CLI -------------------+
                       |
PySide6 GUI -----------+-> shared Application / OperatorSession
                       |        -> Repository / domain services
MCP read adapter ------+        -> canonical SQLite + derived services
```

The GUI MUST NOT shell out to the CLI for canonical work and MUST NOT own direct SQLite/Repository writes from view code.

The accepted Phase P capability inventory is 67 public operations: 66 shared Application operations plus external `mcp.serve` transport behavior.

GUI presentation-only state such as window geometry, navigation position and operation history is noncanonical.

## 8. Search and derived state

Current Object semantic representation family:

```text
object_overview
facet
statement
```

Evidence Search uses its own Evidence representation. Legacy `object_overall` is not active.

Accepted embedding baseline:

```text
model     = microsoft/harrier-oss-v1-0.6b
revision  = f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dimension = 1024
```

Qdrant is the standard Vector backend. Search Representation, Embedding, Vector Index and rendering are rebuildable derived state. Canonical restore/recovery does not depend on preserving those derived artifacts.

## 9. Runtime architecture

### Windows reference

```text
runtime form             = native qdrant.exe
lifecycle owner          = Windows Task Scheduler
Task                     = \SGOKB\Qdrant
startup                  = AtLogOn
crash recovery           = repeating TimeTrigger, 60 s default
principal                = Interactive / Limited
multiple instances       = IgnoreNew
readiness authority      = GET /readyz -> HTTP 200
SGOKB lifecycle actions  = none
```

Docker Compose remains optional/historical and is not Windows authority.

### Runtime health

CLI and GUI share:

```text
operation   = system.status
projection  = data.runtime_health
schema      = sgokb.runtime-health/1.0
components  = sqlite / embedding / qdrant / generation / derived
```

Qdrant lifecycle projection remains:

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

Runtime failure degrades or blocks affected derived capabilities without rewriting accepted canonical Knowledge.

## 10. Recovery boundary

Operational priority remains:

```text
integrity / provenance
  > recoverability
  > explicit Human decision boundary
  > availability / graceful degradation
  > performance
```

Canonical recovery uses SQLite plus required Raw/Result provenance closure. Derived search state may be rebuilt separately with `system derived sync` and `system index rebuild`.

P-RUNTIME-06 accepted real-host Qdrant outage, wrong-service fail-closed behavior, automatic/native recovery, collection persistence, Vector rebuild and post-recovery canonical integrity.

## 11. MCP and external consumers

MCP remains read-only for canonical operations. It resolves accepted Object Knowledge through the same current/historical Version semantics rather than exposing SQLite tables as an integration contract.

UPDS and other external consumers use stable Object identity and explicit Version identity where reproducibility is required.

## 12. GUI distribution boundary

PySide6/Qt Widgets is the accepted GUI framework. The source/repository release includes the GUI implementation and dependency declaration.

SGOKB source code is licensed under the MIT License, copyright (c) 2026 tabenishi02. P-CLOSE-01 still does not certify or publish a standalone GUI binary artifact because packaged Qt/PySide6 redistribution requires the separate P-GUI-02 artifact license gate.

This distribution limitation does not alter the accepted runtime architecture.

## 13. Current authoritative references

- Requirements: `docs/requirements/`
- Current design index: `docs/design/README.md`
- Raw Grounding: `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- GUI architecture: `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`
- Runtime health: `docs/design/P_RUNTIME_03_RUNTIME_HEALTH_STATUS_CONTRACT.md`
- Native Windows runtime: `docs/planning/phases/P/P_RUNTIME_04_NATIVE_WINDOWS_TASK_AMENDMENT.md`
- Runtime failure/recovery: `docs/evaluation/P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_ACCEPTANCE.md`
- Standard operator workflow: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Safety/recovery: `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`
- Release policy: `docs/decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md`
- Phase P closure: `docs/evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md`

## 14. Release state

Phase P implementation workstreams are accepted. `P-CLOSE-01` integrates them into the `2.0.0` release line. The formal `v2.0.0` tag is created only after latest-branch full regression, Ruff and merged-main verification pass.
