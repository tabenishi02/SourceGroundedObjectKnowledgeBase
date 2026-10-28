# GUI Application Boundary Matrix

Updated: 2026-10-28

- Status: **Accepted / P-GUI-03**
- Baseline: current public `sgokb` surface
- Total public operations: **67**
- Audit: `docs/evaluation/P_GUI_03_APPLICATION_BOUNDARY_AUDIT.md`

## Readiness classes

```text
A = READY
    Existing Application boundary can be reused by GUI.

B = ORCHESTRATION EXTRACTION
    Lower-level reusable service exists, but CLI sequencing/audit/target/batch
    logic must move behind a shared Application facade.

C = APPLICATION GAP
    CLI/direct repository logic must be replaced by a transport-neutral
    Application method/facade before GUI implementation.

D = TRANSPORT-SPECIFIC
    Not a normal synchronous canonical operation.
```

## Summary

| Class | Count |
|---|---:|
| A READY | 25 |
| B ORCHESTRATION EXTRACTION | 26 |
| C APPLICATION GAP | 15 |
| D TRANSPORT-SPECIFIC | 1 |
| **Total** | **67** |

---

## Source — 6

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `source import` | B | `Application.import_source_path` | Move path/directory enumeration + batch partial semantics to `SourceOperatorApplication` |
| `source process` | B | `Application.process_source_snapshot` | Move all-snapshot enumeration + batch partial semantics to `SourceOperatorApplication` |
| `source status` | C | direct `source_store.status()` in CLI | Add `SourceOperatorApplication.status()` |
| `source snapshots` | C | direct SourceRepository reads + effective calculation | Add `SourceOperatorApplication.snapshots()` |
| `source select-snapshot` | C | direct SourceRepository mutation in CLI | Add explicit selection Application method preserving reason/audit semantics |
| `source select-run` | C | direct SourceRepository mutation in CLI | Add explicit selection Application method preserving reason/audit semantics |

Source: A=0, B=2, C=4, D=0.

---

## Object — 12

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `object add` | A | `ObjectAdminApplication.add_object` | none |
| `object list` | A | `ObjectAdminApplication.list_objects` | none |
| `object show` | C | CLI manually combines admin + read app | Add transport-neutral combined object detail query |
| `object rename` | A | `ObjectAdminApplication.rename_object` | none |
| `object status` | A | `ObjectAdminApplication.set_status` | none |
| `object alias list` | A | `ObjectAdminApplication.aliases` | none |
| `object alias add` | A | `ObjectAdminApplication.add_alias` | none |
| `object class set-primary` | A | `ObjectAdminApplication.set_primary_class` | none |
| `object class add` | A | `ObjectAdminApplication.add_class` | none |
| `object class remove` | A | `ObjectAdminApplication.remove_class` | none |
| `object events` | A | `ObjectAdminApplication.events` | none |
| `object relations` | A | selector + `KnowledgeReadApplication.get_object_relations` | keep shared selector/application composition; no GUI SQL |

Object: A=11, B=0, C=1, D=0.

---

## Association — 4

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `association list` | A | `Application.list_source_object_associations` | runtime-independent |
| `association suggest` | A | `Application.suggest_source_associations` | shared semantic runtime factory required |
| `association set` | A | `Application.set_source_object_association` | none |
| `association clear` | A | `Application.clear_source_object_association` | none |

Association: A=4.

---

## Evidence — 5

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `evidence candidates` | A | `Application.retrieve_object_evidence` | shared semantic runtime factory |
| `evidence select` | A | `Application.select_object_evidence` | none |
| `evidence show` | A | `KnowledgeReadApplication.get_evidence` | none |
| `evidence provenance` | C | direct `source_store.evidence_provenance` in CLI | add explicit read application projection |
| `evidence search` | A | `KnowledgeReadApplication.search_evidence` | shared semantic runtime factory |

Evidence: A=4, C=1.

---

## Registry — 9

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `registry class list` | A | `ObjectAdminApplication.classes` | may later move to registry-specific facade |
| `registry class show` | A | `ObjectAdminApplication.class_show` | may later move to registry-specific facade |
| `registry relation-type list` | C | direct SQL inside `ObjectAdminApplication` | move SQL to storage/repository and expose through `RegistryOperatorApplication` |
| `registry relation-type show` | C | direct SQL inside `ObjectAdminApplication` | same |
| `registry proposal list` | C | CLI calls `repository.registry_proposals` | wrap in `RegistryOperatorApplication` |
| `registry proposal show` | C | same | same |
| `registry proposal accept` | C | same | preserve decision-only lifecycle |
| `registry proposal reject` | C | same | preserve decision-only lifecycle |
| `registry proposal apply` | C | same | preserve separate explicit mutation |

Registry: A=2, C=7.

---

## Package — 4

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `package build` | B | `ObjectEvidencePackageBuilder` | wrap in `PackageExchangeApplication`; keep payload adaptable for P-RAW |
| `package stage` | B | `PackageTransferService` | move audit recording + manifest handling behind facade |
| `package preflight` | B | `PackageTransferService.preflight` | expose through facade for consistent outcome mapping |
| `package export` | B | `PackageTransferService.export` | move audit recording / acknowledgement result behind facade |

Package: B=4.

---

## Result — 7

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `result detect` | B | `ResultReceiptService` | compose audit repository behind `ResultExchangeApplication` |
| `result receive` | B | `ResultReceiptService` | same |
| `result list` | B | audit repository | expose through Application facade |
| `result pending` | B | audit repository | expose through Application facade |
| `result validate` | B | `ResultValidationService` | facade owns audit/review state semantics |
| `result review` | B | `DiffReviewService` | structured report from facade; Markdown is presentation |
| `result import` | B | `ObjectVersionImportService` | preserve explicit acknowledgement and import boundary |

Result: B=7.

---

## Version — 2

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `version show` | C | CLI direct SQL + `KnowledgeReadApplication` | add Version ID lookup/read Application method |
| `version diff` | B | `DiffReviewService` | expose structured diff through `VersionReadApplication`; Markdown presentation adapter |

Version: B=1, C=1.

---

## Search — 1

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `search` | A | `KnowledgeReadApplication.search_objects` | move semantic runtime construction out of `sgokb.cli.runtime`; CLI/GUI build same filters |

Search: A=1.

---

## Similarity — 1

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `similar` | A | `KnowledgeReadApplication.find_similar_objects` | shared stable-ID selector + runtime factory |

Similarity: A=1.

---

## Render — 1

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `render` | B | `MarkdownRenderService` | move Object->current Version resolution behind `RenderApplication` |

Render: B=1.

---

## MCP — 1

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `mcp serve` | D | `KnowledgeReadApplication` + MCP transport adapter | keep MCP transport lifecycle separate from synchronous OperatorSession; GUI control deferred to P-GUI-09 |

MCP: D=1.

---

## System — 14

| Operation | Class | Current reusable boundary | Refactor requirement |
|---|---|---|---|
| `system status` | B | `system_status()` | facade under `SystemOperatorApplication` |
| `system integrity` | B | `integrity()` | same |
| `system derived status` | A | `DerivedSearchOperatorApplication.status` | shared runtime factory |
| `system derived sync` | A | `DerivedSearchOperatorApplication.sync` | preserve partial result |
| `system index status` | B | `index_status()` | facade |
| `system index rebuild` | C | runtime + builder constructed in CLI | add Application method with injected runtime |
| `system backup status` | B | `backup_status()` | facade |
| `system backup create` | B | `create_backup()` | facade |
| `system backup composite create` | B | `create_composite_backup()` | facade |
| `system backup composite verify` | B | `verify_composite_backup()` | facade/path-only operation |
| `system restore plan` | B | `restore_plan()` | path-only recovery Application; target Repository need not open |
| `system restore apply` | B | `restore_apply()` | preserve overwrite acknowledgement |
| `system restore composite plan` | B | `composite_restore_plan()` | path-only recovery Application |
| `system restore composite apply` | B | `composite_restore_apply()` | preserve overwrite acknowledgement |

System: A=2, B=11, C=1.

---

## Totals check

```text
Source       A0  B2  C4  D0 = 6
Object       A11 B0  C1  D0 = 12
Association  A4  B0  C0  D0 = 4
Evidence     A4  B0  C1  D0 = 5
Registry     A2  B0  C7  D0 = 9
Package      A0  B4  C0  D0 = 4
Result       A0  B7  C0  D0 = 7
Version      A0  B1  C1  D0 = 2
Search       A1  B0  C0  D0 = 1
Similarity   A1  B0  C0  D0 = 1
Render       A0  B1  C0  D0 = 1
MCP          A0  B0  C0  D1 = 1
System       A2  B11 C1  D0 = 14
---------------------------------
Total        A25 B26 C15 D1 = 67
```

## Gate

P-GUI-04 may build presentation shell components after P-GUI-03, but it must not implement broad canonical operations by calling CLI dispatch. The shared boundary remediation defined by P-GUI-03R is required before the shell is connected to the full operator surface.
