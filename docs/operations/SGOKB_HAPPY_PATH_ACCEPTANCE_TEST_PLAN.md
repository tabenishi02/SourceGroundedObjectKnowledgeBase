# SGOKB Happy-Path Operational Acceptance Test Plan

Updated: 2026-10-28

- Scope: SGOKB v1.0.0 current accepted architecture
- Test type: manual / operational acceptance
- Path: **normal / happy path only**
- Status: **Complete / FULL SGOKB PASS**
- Final result: `docs/evaluation/SGOKB_HAPPY_PATH_ACCEPTANCE_20261028.md`
- Related workflow: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Related architecture: `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
- Related safety/recovery: `docs/operations/OPERATIONAL_SAFETY_RECOVERY.md`

---

## 1. Purpose

This plan verifies that SGOKB can be used end-to-end as an operator-facing system after the v1.0.0 release.

The objective is not to repeat Phase N failure/recovery, adversarial, performance, or benchmark work. Instead, this plan confirms that the current released product behaves correctly when valid inputs, valid runtime composition, and valid operator decisions are supplied.

The test covers the complete normal operational chain:

```text
Environment / CLI
  -> Object Registry
  -> Source / Snapshot / Raw Artifact
  -> Normalize / Evidence / Provenance
  -> Source/Object Association
  -> Evidence Selection
  -> Evidence Package
  -> explicit Export
  -> External ChatGPT / semantic integration
  -> Structured Object Result
  -> Detect / Receive / Validate / Review / Import
  -> accepted Knowledge Version
  -> Registry Proposal / explicit accept / apply
  -> Versioning / Relation / Render
  -> Lexical / Semantic / Hybrid / Similarity
  -> read-only MCP
  -> Derived Index maintenance
  -> Backup / Restore
```

The central acceptance principle is not merely that each command exits successfully. The same information must preserve **Object identity, Version identity, Evidence grounding, Provenance, and current/historical scope** across the entire workflow.

---

## 2. Out of scope

This test intentionally excludes abnormal and destructive cases.

Do not include the following in this run:

- invalid or malformed capture files;
- nonexistent Object IDs;
- ambiguous Object names;
- invalid / stale / partial Result artifacts;
- blocked external export cases;
- unapproved review-required flows;
- unavailable Embedding runtime;
- unavailable Qdrant runtime;
- cloud fallback behavior;
- disk full / permission denied;
- process kill / crash recovery;
- corrupted backup;
- intentionally broken foreign keys or migrations;
- conflicting writes;
- duplicate / retry / idempotency stress cases;
- performance / ANN quality / benchmark threshold evaluation.

Those concerns are covered by existing automated, Phase N, safety, recovery, and evaluation assets and are not part of this happy-path acceptance run.

---

## 3. Safety rules

1. Use an **isolated acceptance-test SQLite DB**. Do not use the daily production DB.
2. Use a dedicated export directory and incoming directory.
3. Use only test-owned capture files and test-owned Qdrant collections/index state.
4. Never overwrite a production backup or production DB during restore testing.
5. Record stable IDs as soon as they are created:
   - `object_id`
   - `source_id`
   - `snapshot_id`
   - `evidence_id`
   - `package_id`
   - `receipt_id`
   - `knowledge_version_id`
6. For every WRITE / EXTERNAL / MAINTENANCE operation, record the intended target before execution.

Recommended PowerShell variables:

```powershell
$Db = ".local/acceptance/sgokb-happy-path.sqlite"
$ExportRoot = ".local/acceptance/export"
$IncomingRoot = ".local/acceptance/incoming"
```

---

## 4. Recommended acceptance dataset

Use at least three Objects so that identity, class differences, Relation, Search, and Similarity can all be observed.

| Logical ID | Suggested class | Purpose |
|---|---|---|
| `OBJ-A` | `character` | Main Object; multiple Sources and at least two accepted Versions |
| `OBJ-B` | `work` | Relation target and cross-class retrieval |
| `OBJ-C` | `concept` | Semantic / Similarity / cross-class retrieval |

Recommended Sources:

| Logical ID | Purpose |
|---|---|
| `SRC-A1` | Primary source for OBJ-A |
| `SRC-A2` | Independent second source for OBJ-A |
| `SRC-A1-V2` | Later snapshot/content update for the same logical source |
| `SRC-B1` | Source for OBJ-B |
| `SRC-C1` | Source for OBJ-C |
| `SRC-R1` | Evidence supporting an OBJ-A <-> OBJ-B relation |

Five to eight real capture files are sufficient for this acceptance run. The content should be easy for the operator to understand manually so semantic quality and grounding can be inspected without ambiguity.

For a fresh acceptance DB, the Relation Type Registry may legitimately start empty. The test must not add a Relation Type by direct SQLite manipulation or an ad-hoc write. If no suitable Relation Type already exists, the first Result must propose a `new_relation_type`; the operator then accepts and applies that proposal before a later Result imports the actual Relation.

---

## 5. Result recording convention

For each item record:

```text
Result: PASS / FAIL / NOT RUN
Observed IDs:
Observed output:
Notes:
```

A test is PASS only when both the command operation and the semantic expectation are satisfied.

---

# A. Environment / CLI

| ID | Test | Operation | Expected result |
|---|---|---|---|
| A-01 | CLI startup | `sgokb --help` | Help is displayed and process exits successfully |
| A-02 | Isolated DB startup | Run SGOKB against the isolated DB | DB is usable with current migrations/schema |
| A-03 | System status | `sgokb --db $Db system status` | Current system state is returned successfully |
| A-04 | Integrity | `sgokb --db $Db system integrity` | SQLite integrity, FK integrity, and migration state are valid |
| A-05 | Class registry list | `registry class list` | Current registered classes are returned |
| A-06 | Class registry show | `registry class show <class>` | Selected class definition is returned |
| A-07 | Relation type registry | `registry relation-type list`; if non-empty, `show` one suitable type | Registry is readable. An empty list is valid for a fresh DB; existing definitions, when present, can be read individually |
| A-08 | JSON contract | Run a normal READ command | Output follows `sgokb.cli/1.0`, `ok=true` |
| A-09 | Human-readable output | Use `--format text` where supported | A readable representation is displayed |

Acceptance focus:

- the public entrypoint is `sgokb`;
- no legacy `sgokb-package` workflow is needed;
- normal reads are possible before semantic runtime is involved;
- an empty fresh Relation Type Registry is not treated as corruption or CLI failure.

---

# B. Object Registry

| ID | Test | Operation | Expected result |
|---|---|---|---|
| B-01 | Create Character | Add OBJ-A | Stable `object_id` is issued |
| B-02 | Create Work | Add OBJ-B | Independent stable `object_id` is issued |
| B-03 | Create Concept | Add OBJ-C | Independent stable `object_id` is issued |
| B-04 | List Objects | `object list` | All three Objects are visible |
| B-05 | Read by ID | `object show --object <id>` | Correct Object is returned |
| B-06 | Read by exact name | `object show --name <name>` | Same Object resolves successfully |
| B-07 | Add alias | `object alias add` on OBJ-A | Alias is stored |
| B-08 | List aliases | `object alias list` | New alias is visible |
| B-09 | Resolve by alias | Use exact alias with `--name` | Same stable `object_id` resolves |
| B-10 | Rename Object | `object rename` OBJ-A | Canonical name changes; `object_id` does not |
| B-11 | Add additional class | `object class add` | Additional class is stored |
| B-12 | Change primary class and restore | `object class set-primary` | Identity remains stable through class change |
| B-13 | Inspect events | `object events` | Registry changes are visible in event history |
| B-14 | Archive and reactivate | `object status ... archived`, then `active` | State changes without identity replacement |

Critical invariant:

```text
rename / alias / class / status mutation
    MUST NOT change stable object_id
```

---

# C. Source / Snapshot / Raw Artifact

| ID | Test | Operation | Expected result |
|---|---|---|---|
| C-01 | Import primary capture | `source import SRC-A1` | Source and Snapshot are created |
| C-02 | Process primary snapshot | `source process --snapshot <id>` | Normalized Run and Evidence are produced |
| C-03 | Source status | `source status` | Imported/processed state is visible |
| C-04 | Snapshot list | `source snapshots` | Snapshot is listed |
| C-05 | Import second OBJ-A source | Import/process SRC-A2 | Independent Source/Evidence is created |
| C-06 | Import OBJ-B source | Import/process SRC-B1 | Successful |
| C-07 | Import OBJ-C source | Import/process SRC-C1 | Successful |
| C-08 | Later snapshot | Import/process SRC-A1-V2 as later capture of the same logical source where supported by the ingestion identity contract | New Snapshot history is retained without losing prior source history |
| C-09 | Raw artifact preservation | Inspect imported source/snapshot state | Original raw capture remains retained |

Expected traceability shape:

```text
Source
  -> Snapshot
     -> Raw Artifact
        -> Normalized Run
           -> Evidence
```

---

# D. Source <-> Object Association

| ID | Test | Operation | Expected result |
|---|---|---|---|
| D-01 | Inspect associations | `association list --object OBJ-A` | Current association state is readable |
| D-02 | Confirm primary source | SRC-A1 -> OBJ-A `confirmed` | Association is stored |
| D-03 | Confirm second source | SRC-A2 -> OBJ-A `confirmed` | One Object can use multiple Sources |
| D-04 | Work association | SRC-B1 -> OBJ-B | Successful |
| D-05 | Concept association | SRC-C1 -> OBJ-C | Successful |
| D-06 | Many-to-many association | Associate SRC-R1 with both OBJ-A and OBJ-B | One Source can support multiple Objects |
| D-07 | Re-read associations | List each Object | Expected Source membership is preserved |

---

# E. Evidence / Provenance

| ID | Test | Operation | Expected result |
|---|---|---|---|
| E-01 | Evidence candidates | `evidence candidates --object OBJ-A` | Relevant Evidence candidates are returned |
| E-02 | Evidence selection | `evidence select --object OBJ-A` | Package-eligible Evidence set is returned |
| E-03 | Evidence detail | `evidence show <evidence-id>` | Evidence content and metadata are readable |
| E-04 | Provenance | `evidence provenance <evidence-id>` | Evidence traces to Source/Snapshot/Normalization Run |
| E-05 | Multi-source grounding | Inspect OBJ-A Evidence | Evidence from SRC-A1 and SRC-A2 is distinguishable |
| E-06 | Evidence search | `evidence search <query>` | Matching Evidence can be found by content |

Critical invariant:

```text
accepted knowledge grounding
  -> evidence_id
  -> normalization/snapshot/source
  -> preserved raw artifact
```

must remain inspectable.

---

# F. Evidence Package

| ID | Test | Operation | Expected result |
|---|---|---|---|
| F-01 | Build Package | `package build --object OBJ-A` | `package_id` and build path are returned |
| F-02 | Inspect manifest | Open generated Package | Target Object, base Version, and Evidence membership are correct |
| F-03 | Inspect instructions | Open `instructions.md` | Current analysis instructions are present |
| F-04 | Inspect Evidence payload | Review packaged Evidence | Selected Evidence is present and identifiable |
| F-05 | Stage Package | `package stage <build-path>` | Staged artifact is created |
| F-06 | Preflight | `package preflight ... --destination $ExportRoot` | Normal exportable disposition is returned |
| F-07 | Explicit export | `package export ... --destination $ExportRoot` | Package is copied outside the SGOKB boundary |
| F-08 | Export integrity | Inspect exported directory | Required Package files are present and readable |

For this happy-path plan, choose data/destination that follows the normal exportable path. Do not intentionally construct a blocked or unapproved review-required case.

---

# G. External ChatGPT / Structured Object Result

This section is outside the SGOKB runtime but is part of the standard human-in-the-loop workflow.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| G-01 | Give Package to ChatGPT | Upload/provide exported Package | Package can be analyzed |
| G-02 | Instruction authority | Tell the model to follow `instructions.md` | Output follows the Package contract |
| G-03 | Evidence grounding | Review generated knowledge | Claims are grounded in packaged Evidence |
| G-04 | Structured Result | Produce `result.json` | Result conforms to current SGOKB Result schema |
| G-05 | Facet generation | Review OBJ-A knowledge | Appropriate facets are represented |
| G-06 | Statement generation | Review facet statements | Statements are evidence-grounded and structured |
| G-07 | Relation-type proposal on fresh registry | If A-07 found no suitable Relation Type, include an Evidence-grounded `new_relation_type` Registry Proposal instead of inventing/using a nonexistent Relation Type | Proposal is structured and Evidence-grounded; no actual Relation using the not-yet-applied type is emitted in V1 |
| G-08 | Place Result | `<IncomingRoot>/drop/<PackageId>/result.json` | SGOKB intake can discover the artifact |

Do not add external facts as fabricated SGOKB Evidence IDs. External AI is a semantic integration consumer/producer, not an authority that can invent provenance.

If A-07 found an already-existing suitable Relation Type, G-07 may use that existing type and the proposal-specific I path can use another benign proposal. For a fresh unseeded Relation Type Registry, prefer the deterministic `new_relation_type` path described above.

---

# H. Result Intake / Validation / Import

| ID | Test | Operation | Expected result |
|---|---|---|---|
| H-01 | Detect Result | `result detect --incoming-root $IncomingRoot` | `result.json` is detected |
| H-02 | Receive Result | `result receive ...` | `receipt_id` is issued |
| H-03 | List Results | `result list` | Receipt is visible |
| H-04 | Pending Results | `result pending` | Pending intake state is visible as expected |
| H-05 | Validate | `result validate <receipt-id>` | Result reaches valid state |
| H-06 | Human review | `result review ... --review-format markdown` | Operator can inspect proposed Knowledge |
| H-07 | Explicit Import | `result import <receipt-id>` | New accepted Knowledge Version is created |
| H-08 | Current pointer | `object show --object OBJ-A --knowledge` | Imported Version is current |
| H-09 | Evidence links | Inspect imported Knowledge | Statements and any Relations already valid for this Version remain grounded to valid Evidence IDs |

Critical boundary:

```text
valid Result != automatically accepted Knowledge
```

Validation, review, and explicit import must remain distinct normal steps.

---

# I. Registry Proposal

For a fresh DB whose Relation Type Registry is empty, this section must exercise a `new_relation_type` proposal that will later permit the supported OBJ-A -> OBJ-B Relation. A representative semantic meaning is "character appears in work"; use the exact key/name/payload produced under the current Result/Registry contract rather than inventing a direct DB row.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| I-01 | Proposal intake | Import Result containing `new_relation_type` proposal | Proposal becomes pending; it is not silently applied |
| I-02 | List proposals | `registry proposal list --decision pending` | Proposal is visible |
| I-03 | Inspect proposal | `registry proposal show <proposal-ref>` | `proposal_kind = new_relation_type`, payload, rationale, Evidence, and review context are readable |
| I-04 | Accept proposal | `registry proposal accept ...` | Human decision is recorded; Relation Type is not created merely by acceptance |
| I-05 | Apply proposal | `registry proposal apply ...` | Relation Type Registry mutation occurs only now |
| I-06 | Verify Relation Type Registry | Re-run `registry relation-type list/show` | Applied Relation Type now exists and can be read individually |

Critical invariant:

```text
Result Import
  -> pending new_relation_type proposal
  -> explicit human accept
  -> explicit apply
  -> Relation Type becomes usable by a later Knowledge Version
```

Do not rewrite V1 in place after applying the proposal. The actual Relation is introduced by a later Result and therefore belongs to a later immutable Knowledge Version.

---

# J. Knowledge Versioning

Create at least two accepted Versions for OBJ-A.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| J-01 | Capture Version 1 identity | Record first `knowledge_version_id` | V1 is readable |
| J-02 | Add new Evidence | Import/process later OBJ-A snapshot, explicitly select the reviewed Snapshot/Run as effective, then retrieve Evidence | New Evidence from the selected follow-up generation exists |
| J-03 | Build update Package | Rebuild OBJ-A Package after I-05/I-06 | Current/base Version binding is correct and the applied Relation Type is now available |
| J-04 | Produce Result 2 | External semantic integration using the applied Relation Type and SRC-R1 Evidence | Updated structured Result is valid and contains the supported OBJ-A -> OBJ-B Relation |
| J-05 | Import Result 2 | Validate/review/import | V2 is created |
| J-06 | Current Version | Read OBJ-A | V2 is current |
| J-07 | Historical preservation | Read V1 | V1 remains intact |
| J-08 | Version show | `version show V1`, `version show V2` | Both are individually readable |
| J-09 | Version diff | `version diff V1 V2` | Expected Knowledge changes, including the newly valid Relation where applicable, are displayed |
| J-10 | Historical Object read | `object show --version V1` | Historical state is reconstructed/read correctly |
| J-11 | Version-specific grounding | Inspect V1/V2 Evidence links | Each Version retains appropriate grounding |

Critical invariant:

```text
new accepted knowledge = new immutable Version
not destructive overwrite of prior accepted Version
```

---

# K. Relation

Use the supported OBJ-A -> OBJ-B Relation introduced in V2 after the required Relation Type has been explicitly accepted and applied.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| K-01 | Relation import | Confirm the V2 Result containing the applied Relation Type was imported | Relation is stored in accepted V2, not retroactively inserted into V1 |
| K-02 | Read from OBJ-A | `object relations --object OBJ-A` | OBJ-B relation is visible in current accepted Version |
| K-03 | Read related side | Inspect OBJ-B relation view as defined by relation semantics | Expected relation view is available; do not require an inverse that the Relation Type does not define |
| K-04 | Relation Evidence | Inspect relation with Evidence | SRC-R1-derived grounding is retained |
| K-05 | Version-specific Relation | Read V1 and V2 relations explicitly | Version scope is respected; V1 and V2 may legitimately differ because the type was applied between them |

Do not use a direct ad-hoc relation write path. Accepted Relations must remain inside the Result -> validate/review -> import boundary.

---

# L. Render

| ID | Test | Operation | Expected result |
|---|---|---|---|
| L-01 | Current render | `render --object OBJ-A` | Human-readable current Knowledge is generated |
| L-02 | Version render | `render --version <version-id>` | Selected Version is rendered |
| L-03 | Facet rendering | Inspect output | Facets/statements are represented correctly |
| L-04 | Relation rendering | Inspect output | Accepted relations are represented |
| L-05 | Grounding visibility | Inspect output/detail links | Evidence/provenance can be traced |
| L-06 | V1/V2 render comparison | Render both Versions | Expected Version differences are visible |

---

# M. Lexical Search

Lexical search is the minimum local retrieval path and should pass before semantic runtime tests.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| M-01 | Canonical-name search | Search OBJ-A name | OBJ-A is returned |
| M-02 | Alias search | Search OBJ-A alias | OBJ-A resolves/is returned appropriately |
| M-03 | Knowledge-term search | Search a distinctive accepted statement term | Correct Object is returned |
| M-04 | Multi-object search | Use a term shared by multiple Objects | Relevant Objects are returned |
| M-05 | Current scope | Search after V2 import | Normal retrieval reflects current accepted Knowledge |
| M-06 | Cross-class retrieval | Search terms matching Character/Work/Concept | Appropriate Objects across classes can be found |

---

# N. Semantic Search

Run this section only on the normal fully configured semantic runtime.

Accepted current baseline includes a local Embedding provider and Qdrant-backed vector runtime. The exact model/runtime identity should match the current accepted architecture and local configuration.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| N-01 | Semantic runtime composition | Start/use SGOKB with semantic runtime | Runtime is available without fallback |
| N-02 | Index status | `system index status` | Current derived-state status is healthy |
| N-03 | Index rebuild | `system index rebuild` | Current accepted Knowledge is indexed |
| N-04 | Paraphrase semantic search | Query meaning without exact wording | Intended Object is returned |
| N-05 | Overview retrieval | Query a broad Object characteristic | `object_overview` channel contributes correctly |
| N-06 | Facet retrieval | Query a facet-specific concept | `facet` representation contributes correctly |
| N-07 | Statement retrieval | Query a specific proposition | `statement` representation contributes correctly |
| N-08 | Current Version scope | Query content changed in V2 | Normal search uses current accepted Version |
| N-09 | Cross-class semantic retrieval | Semantic query spanning Object classes | Relevant Character/Work/Concept Objects can be retrieved |

---

# O. Hybrid Search

| ID | Test | Operation | Expected result |
|---|---|---|---|
| O-01 | Name + semantics | Hybrid query mixing identity and concept | Both lexical and semantic evidence contribute |
| O-02 | Exact identity visibility | Query exact name with semantically similar competitors present | Exact identity is not buried incorrectly |
| O-03 | Lexical-heavy query | Use distinctive wording | Lexical signal is reflected |
| O-04 | Semantic-heavy query | Use paraphrase wording | Semantic signal is reflected |
| O-05 | Object aggregation | Inspect result list | Multiple representations of one Object aggregate to bounded Object-level result |

Critical current R2 behavior:

```text
multiple representation/channel hits
  -> bounded aggregation
  -> one Object-level result
```

---

# P. Similarity

| ID | Test | Operation | Expected result |
|---|---|---|---|
| P-01 | Object similarity | `similar --object OBJ-A` | Similar Objects are returned |
| P-02 | Facet-specific similarity | Run similarity for an existing facet | Similarity reflects requested facet |
| P-03 | Human plausibility | Inspect top results | Ranking is semantically plausible for test dataset |
| P-04 | Current scope | Repeat after V2 | Current accepted Knowledge is reflected |
| P-05 | Cross-class behavior | Compare eligible Objects across classes | Results follow current similarity contract |

---

# Q. MCP Read Boundary

Start the MCP server with the same acceptance DB and, where required, the same semantic runtime.

```text
sgokb --db <DB_PATH> mcp serve
```

Invoke every active read capability at least once from an actual MCP client.

| ID | MCP capability | Expected result |
|---|---|---|
| Q-01 | `get_object` | OBJ-A current accepted Knowledge is returned |
| Q-02 | `get_objects` | Multiple requested Objects are returned |
| Q-03 | `search_objects` | Lexical or hybrid search returns expected Objects |
| Q-04 | `find_similar_objects` | Similarity results are returned |
| Q-05 | `get_object_relations` | OBJ-A/OBJ-B accepted Relation from current V2 is returned |
| Q-06 | `get_object_evidence` | Grounding Evidence is returned |
| Q-07 | `search_evidence` | Matching Evidence can be searched |
| Q-08 | `build_context` | Purpose-specific deterministic context subset is returned |
| Q-09 | CLI/MCP consistency | Read same OBJ-A through CLI and MCP | Same current Version identity/content is resolved |
| Q-10 | Comparison context | `build_context` with OBJ-A + OBJ-B and comparison purpose | Useful bounded comparison context is produced |
| Q-11 | Character budget | Run with explicit maximum | Output respects configured size budget |
| Q-12 | Deterministic repeat | Repeat identical request | Same stored Knowledge selection/order behavior is reproduced |

MCP acceptance remains read-only. Do not perform canonical write, Result import, Registry mutation, or Package export through MCP.

---

# R. Derived Index Maintenance

| ID | Test | Operation | Expected result |
|---|---|---|---|
| R-01 | Index status | `system index status` | Derived-state identity/status is readable |
| R-02 | Rebuild | `system index rebuild` | Derived representations/vector state rebuild from canonical Knowledge |
| R-03 | Lexical after rebuild | Repeat lexical query | Canonical read result remains valid |
| R-04 | Semantic after rebuild | Repeat semantic query | Intended Object remains retrievable |
| R-05 | Similarity after rebuild | Repeat similarity query | Similarity remains available |
| R-06 | Reuse observation | Rebuild/update unchanged semantic content | Existing representation/embedding identity is reused where contract permits; unnecessary duplicate state is not created |

Critical invariant:

```text
Derived Search state is rebuildable.
Canonical accepted Knowledge is not replaced by Vector/Embedding state.
```

---

# S. Backup / Restore — Normal Maintenance Path

This is a successful maintenance-path test, not a failure/recovery drill.

Use only acceptance-test assets and restore into an isolated target context.

| ID | Test | Operation | Expected result |
|---|---|---|---|
| S-01 | Backup status | `system backup status` | Backup state is readable |
| S-02 | Create backup | `system backup create` | Complete backup artifact is produced |
| S-03 | Backup integrity | Inspect reported verification | Backup passes integrity verification |
| S-04 | Restore plan | `system restore plan <backup>` | Planned restore actions are displayed |
| S-05 | Restore to isolated target | Apply restore in dedicated acceptance target | Restore succeeds without touching production assets |
| S-06 | Restored integrity | `system integrity` on restored DB | PASS |
| S-07 | Restored Objects | Read OBJ-A/OBJ-B/OBJ-C | Stable IDs and canonical Object data are present |
| S-08 | Restored Versions | Read OBJ-A V1/V2 | Version history is preserved |
| S-09 | Restored Evidence | Inspect Evidence/Provenance | Grounding chain is preserved |
| S-10 | Rebuild derived state | `system index rebuild` on restored environment | Derived state can be reconstructed |
| S-11 | Restored search | Run lexical and semantic retrieval | Expected Objects are retrievable |
| S-12 | Restored render | Render OBJ-A | Accepted Knowledge can be rendered |

---

# T. Final Uninterrupted End-to-End Scenario

After the sectional checks, execute one fresh Object through the complete workflow without shortcutting internal boundaries.

```text
Web page / local capture
  -> source import
  -> source process
  -> object add
  -> association set confirmed
  -> evidence candidates/select
  -> package build
  -> package stage
  -> package preflight
  -> package export
  -> external ChatGPT semantic integration
  -> result.json
  -> result detect
  -> result receive
  -> result validate
  -> result review
  -> result import
  -> accepted Knowledge Version
  -> registry proposal review/accept/apply when the Result legitimately contains one
  -> object show --knowledge
  -> render
  -> lexical search
  -> semantic search
  -> hybrid search
  -> similarity
  -> relation/evidence read when a valid applied Relation Type and supported Relation exist
  -> MCP get_object
  -> MCP search_objects
  -> MCP build_context
  -> backup create
```

## T acceptance conditions

- No raw SQLite manipulation is used.
- No Python REPL shortcut is used.
- No legacy CLI is used.
- Package external export remains explicit.
- External AI uses Package Evidence as grounding.
- Result validation and review are completed before Import.
- Accepted Knowledge is created only through explicit Import.
- Registry proposals are not silently applied; required Relation Types become usable only after explicit accept/apply.
- Stable Object identity is preserved.
- Evidence remains traceable to Source/Snapshot/Raw Artifact.
- CLI and MCP resolve the same current accepted Version.
- Semantic/Vector state remains derived, not canonical.
- Backup can be created from the final accepted state.

---

## 6. Overall acceptance verdict

Use two levels so the minimum local workflow can be distinguished from the fully composed SGOKB environment.

### Core PASS

Require all of the following:

- Sections A through M PASS;
- Section T core chain PASS through lexical retrieval;
- no identity, Version, Evidence, or Provenance inconsistency observed.

This establishes that the canonical local-first SGOKB workflow works with SQLite and the standard human-in-the-loop exchange boundary.

### Full SGOKB PASS

Require all Core PASS conditions plus:

- Sections N through R PASS;
- all eight active MCP read capabilities in Q-01 through Q-08 PASS;
- MCP/CLI consistency checks PASS;
- Section S normal backup/restore path PASS;
- Section T completes through semantic/hybrid/similarity/MCP/backup.

### FAIL

Record FAIL if any normal-path operation completes but violates a canonical invariant, including:

- stable Object identity changes unexpectedly;
- historical accepted Version is lost;
- current/historical Version scope is mixed incorrectly;
- imported Knowledge cannot trace to intended Evidence;
- Evidence cannot trace to Source/Snapshot/Raw Artifact;
- a Registry Proposal is silently applied or a Relation uses a nonexistent/unapplied Relation Type;
- MCP resolves different canonical current Knowledge than CLI;
- derived Vector/Embedding state becomes the only copy of knowledge;
- explicit export/import/review boundaries are bypassed.

A FAIL discovered here should become a separate defect/remediation task. Do not weaken this acceptance plan to make the run pass.

---

## 7. Execution summary

Completed manual run:

```text
Run ID:                              SGOKB-HAPPY-PATH-20261028
Date:                                2026-10-28
Git commit / release:                5eba4629b12cc071dab33d04faa7521a361d6977 / v1.0.0-22-g5eba462
Worktree:                            clean
DB path:                             C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\sgokb-happy-path.sqlite
Semantic runtime:                    local sentence-transformers + Qdrant 1.19.2
Embedding provider/model/revision:   sentence-transformers / microsoft/harrier-oss-v1-0.6b / f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Embedding dimension:                 1024
Embedding Space ID:                  832920052e1d1a6d3bbe2a5ef9d3b0d09785b0e0f26bf3081b8728de2897d591
Qdrant target:                       127.0.0.1:6333 HTTP / 127.0.0.1:6334 gRPC
MCP target:                          sgokb-acceptance acceptance DB

A Environment / CLI:               PASS
B Object Registry:                  PASS
C Source / Snapshot / Raw:          PASS
D Association:                      PASS
E Evidence / Provenance:            PASS
F Evidence Package:                 PASS
G External ChatGPT / Result:        PASS
H Result Validate / Import:         PASS
I Registry Proposal:                PASS
J Knowledge Versioning:             PASS
K Relation:                         PASS
L Render:                           PASS
M Lexical Search:                   PASS
N Semantic Search:                  PASS
O Hybrid Search:                    PASS
P Similarity:                       PASS after remediation
Q MCP Read Boundary:                PASS
R Derived Index:                    PASS
S Backup / Restore:                 PASS
T Final uninterrupted E2E:          PASS

Core verdict:                       PASS
Full SGOKB verdict:                 PASS
Overall verdict:                    FULL SGOKB PASS

T-01 Object:                        フリーザ
T-01 Object ID:                     ca96ae90-3ff6-4c62-83ea-7d1d7c41439a
T-01 current Version ID:            7d7b594b-aea7-45e6-95c5-5f388503568c

Defects / follow-up:
- no blocking defect remains in the happy-path acceptance result
- Section P is retained as PASS after remediation; the original fixture deficiency remains historical evidence
- detailed execution identities and observations are recorded in docs/evaluation/SGOKB_HAPPY_PATH_ACCEPTANCE_20261028.md
```

---

## 8. Relationship to existing acceptance evidence

This document does not supersede Phase N evidence.

Existing automated and formal acceptance assets continue to prove domain correctness, integration wiring, real-data behavior, retrieval/vector quality, performance, and failure/recovery properties. This plan adds a separate **operator-facing real-use smoke/acceptance layer** for the released system.

Its purpose is therefore:

```text
Phase N evidence
  = implementation/evaluation acceptance

this happy-path plan
  = real operator usage acceptance after release
```

Both are useful, but they answer different questions.
