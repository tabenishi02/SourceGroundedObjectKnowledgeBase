# SGOKB CLI <-> GUI Capability Matrix

Updated: 2026-10-28

- Status: **Accepted / P-GUI-01**
- Baseline parser: `src/sgokb/cli/main.py` on Phase P start baseline
- Public parity target: **67 operations**
- Requirement: `docs/requirements/GUI_REQUIREMENTS.md`
- Decision: `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`

---

## 1. Matrix rules

本表はpublic `sgokb` operationをGUI capabilityへ割り当てるnormative inventoryである。

- `Side effect`はGUI safety表現を決めるprimary classificationである。
- mixed operationは補足でより強いboundaryを記載する。
- `GUI surface`は情報設計上のplacementであり、Qt Widget設計ではない。
- Package / Resultはcurrent v1.1.0 command slotを記録するが、最終GUI semanticsはP-RAW後に更新する。
- `--db`はWorkspace selectorに対応する。
- `--format json|text`はCLI transport-only optionでありmatrix operation countに含めない。

---

## 2. Source — 6 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 1 | `source import <path>` | file / directory | WRITE | Sources / Import | File dialog / drag-drop / batch result。Source/Snapshot/Raw作成結果を表示 |
| 2 | `source process` | snapshot, size, overlap, include-auxiliary | WRITE | Source Detail / Processing | normalization設定、progress、run/Evidence結果、batch partial表示 |
| 3 | `source status` | - | READ | Sources / Dashboard | Source/Snapshot/Raw/Run/Evidence counts |
| 4 | `source snapshots` | - | READ | Sources / Snapshots | Snapshot一覧、effective状態、captured time、completeness |
| 5 | `source select-snapshot` | source, snapshot, reason | WRITE | Source Detail / Snapshot History | targetを明示しreason必須でeffective Snapshot変更 |
| 6 | `source select-run` | snapshot, run, reason | WRITE | Source Detail / Run History | targetを明示しreason必須でeffective Run変更 |

Source parity: **6 / 6 assigned**.

---

## 3. Object — 12 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 7 | `object add` | name, primary-class, aliases | WRITE | Objects / New Object | form validation、Class selector、aliases、explicit Create |
| 8 | `object list` | - | READ | Objects | sortable/filterable Object list |
| 9 | `object show` | object/name, knowledge, version | READ | Object Detail | registry + current/explicit Knowledge Version表示 |
| 10 | `object rename` | object/name, to | WRITE | Object Detail / Identity | stable object_idに対するrename preview / Apply |
| 11 | `object status` | object/name, active/archived | WRITE | Object Detail / Identity | active/archive変更、archive時confirmation |
| 12 | `object alias list` | object/name | READ | Object Detail / Aliases | alias list |
| 13 | `object alias add` | value, language, kind | WRITE | Object Detail / Aliases | alias add form / explicit Add |
| 14 | `object class set-primary` | class-ref | WRITE | Object Detail / Classes | current/new Primary Classを明示してApply |
| 15 | `object class add` | class-ref | WRITE | Object Detail / Classes | Additional Class追加 |
| 16 | `object class remove` | class-ref | WRITE | Object Detail / Classes | Additional Class削除、target明示 |
| 17 | `object events` | object/name | READ | Object Detail / History | Object event timeline |
| 18 | `object relations` | version, include evidence | READ | Object Detail / Relations | Relation一覧、Version scope、evidence refs toggle |

Object parity: **12 / 12 assigned**.

Direct Relation writeはGUI capabilityとして追加しない。

---

## 4. Association — 4 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 19 | `association list` | object | READ | Associations / Object Detail | Objectに対するSource association一覧 |
| 20 | `association suggest` | object, max-candidates, semantic, batch-size | READ | Associations / Suggestions | candidate ranking、semantic runtime state/warning表示 |
| 21 | `association set` | object, source, status, subject-relationship, note | WRITE | Associations / Review | candidate/confirmed/excluded設定、metadata入力 |
| 22 | `association clear` | object, source | WRITE | Associations / Review | association解除、対象pair明示 |

Association parity: **4 / 4 assigned**.

---

## 5. Evidence — 5 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 23 | `evidence candidates` | object, include/exclude, max-candidates, semantic | READ | Evidence / Candidate Review | candidate list、retrieval reasons、manual include/exclude |
| 24 | `evidence select` | candidates + token/byte/item budgets | READ | Evidence / Selection | bounded selection、budget usage、selected/omitted表示 |
| 25 | `evidence show` | evidence-id | READ | Evidence Detail | Evidence content / metadata |
| 26 | `evidence provenance` | evidence-id | READ | Evidence Detail / Provenance | Source/Snapshot/Run/Raw chain表示 |
| 27 | `evidence search` | query, mode, limit, source/object/status/language/history | READ | Evidence Search | lexical/semantic/hybrid、filters、degradation warning |

Evidence parity: **5 / 5 assigned**.

---

## 6. Registry — 9 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 28 | `registry class list` | - | READ | Registry / Classes | Class一覧 |
| 29 | `registry class show` | class-ref | READ | Registry / Class Detail | Class detail / hierarchy information |
| 30 | `registry relation-type list` | - | READ | Registry / Relation Types | Relation Type一覧 |
| 31 | `registry relation-type show` | relation-ref | READ | Registry / Relation Type Detail | Relation Type detail |
| 32 | `registry proposal list` | decision filter | READ | Registry / Proposals | pending/accepted/rejected filter |
| 33 | `registry proposal show` | proposal-ref | READ | Registry / Proposal Detail | proposed change / review/apply state |
| 34 | `registry proposal accept` | proposal-ref, note | WRITE | Registry / Proposal Review | human accept decision記録。Applyとは分離 |
| 35 | `registry proposal reject` | proposal-ref, note | WRITE | Registry / Proposal Review | human reject decision記録 |
| 36 | `registry proposal apply` | proposal-ref | WRITE | Registry / Proposal Apply | accepted proposalのみexplicit Apply、impact preview |

Registry parity: **9 / 9 assigned**.

`accept`と`apply`のhidden compositionは禁止する。

---

## 7. Package — 4 operations

> P-RAW completion後にgrounding-specific controlsを更新する。operation slot自体はGUI parity対象。

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 37 | `package build` | object, build-root, include/exclude, budgets, language | DERIVED | Packages / Build Wizard | grounding selection、budget、build result、artifact preview |
| 38 | `package stage` | source, staging-root | DERIVED + audit WRITE | Packages / Staging | stage target、preflight summary、exchange audit state |
| 39 | `package preflight` | package, destination | READ | Packages / Preflight | disposition allow/review-required/blocked、reasons表示 |
| 40 | `package export` | package, destination, acknowledge-review | EXTERNAL + audit WRITE | Packages / Export | destination、data summary、preflight、required acknowledgement |

Package parity: **4 / 4 assigned**.

---

## 8. Result — 7 operations

> P-RAW completion後にgrounding-specific validation / displayを更新する。

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 41 | `result detect` | incoming-root | READ | Results / Inbox | incoming candidate scan |
| 42 | `result receive` | result path, package-id, incoming-root | WRITE | Results / Receive | Package binding確認、receipt作成結果 |
| 43 | `result list` | optional package-id | READ | Results | receipt一覧 / Package filter |
| 44 | `result pending` | - | READ | Results / Pending | pending receipts |
| 45 | `result validate` | receipt-id, force | WRITE | Result Detail / Validation | validation state / issues。forceはAdvanced confirmation |
| 46 | `result review` | receipt-id, json/markdown | READ | Result Detail / Review | current Knowledgeとのstructured/Markdown review |
| 47 | `result import` | receipt-id, acknowledge-review | WRITE | Result Detail / Import | explicit Import、review acknowledgement、new Version result |

Result parity: **7 / 7 assigned**.

---

## 9. Version — 2 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 48 | `version show` | version-id | READ | Object / Version Detail | immutable accepted Version表示 |
| 49 | `version diff` | before, after, json/markdown | READ | Object / Version Diff | structured / Markdown diff、before/after明示 |

Version parity: **2 / 2 assigned**.

---

## 10. Search — 1 operation

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 50 | `search` | query, lexical/semantic/hybrid, semantic runtime, require-full-runtime, limits, class/facet/version/time/derivation/archive filters | READ | Search | query bar、mode selector、filter sidebar、runtime/degradation state |

Search parity: **1 / 1 assigned**.

`require-full-runtime`相当は「degradation不可」の明示controlとして提供する。

---

## 11. Similarity — 1 operation

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 51 | `similar` | object/name, facet, limit, cross-class, version, archived | READ | Object Detail / Similar | Object / Facet similarity、scope controls、no silent facet fallback |

Similarity parity: **1 / 1 assigned**.

---

## 12. Render — 1 operation

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 52 | `render` | object/version, output-root | DERIVED | Object / Render | render target、output path、Markdown preview |

Render parity: **1 / 1 assigned**.

---

## 13. MCP — 1 operation

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 53 | `mcp serve` | semantic-runtime | READ service / runtime | System / MCP | read-only MCP state、start/stop lifecycle support、semantic mode表示 |

MCP parity: **1 / 1 assigned**.

MCPのcanonical write capabilityは追加しない。

---

## 14. System / Maintenance — 14 operations

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 54 | `system status` | - | READ | System / Overview | DB / system state summary |
| 55 | `system integrity` | - | READ | System / Integrity | integrity results、failure severity |
| 56 | `system derived status` | optional object, semantic-runtime | READ | System / Derived | derived generation/status、scope |
| 57 | `system derived sync` | optional object, semantic-runtime | DERIVED | System / Derived | sync scope、progress、partial outcome |
| 58 | `system index status` | - | READ | System / Vector Index | index / embedding-space state |
| 59 | `system index rebuild` | - | DERIVED | System / Vector Index | rebuild confirmation、progress、runtime requirement |
| 60 | `system backup status` | root | READ / MAINTENANCE inspection | System / Backup | backup inventory/status |
| 61 | `system backup create` | output, root | MAINTENANCE | System / Backup | destination、progress、integrity result |
| 62 | `system backup composite create` | incoming-root, output, root | MAINTENANCE | System / Backup / Composite | DB + Raw + incoming scope、destination、completion |
| 63 | `system backup composite verify` | backup | READ / MAINTENANCE verification | System / Backup / Verify | manifest/integrity verification result |
| 64 | `system restore plan` | backup | READ / MAINTENANCE plan | System / Restore | target DBに対するrestore plan、no mutation |
| 65 | `system restore apply` | backup, acknowledge-overwrite | MAINTENANCE + WRITE | System / Restore | plan review後apply、overwrite acknowledgement必須 |
| 66 | `system restore composite plan` | backup, db-target, raw-root, incoming-root | READ / MAINTENANCE plan | System / Restore / Composite | multi-root restore plan |
| 67 | `system restore composite apply` | backup, db-target, raw-root, incoming-root, acknowledge-overwrite | MAINTENANCE + WRITE | System / Restore / Composite | plan review、targets明示、overwrite acknowledgement必須 |

System parity: **14 / 14 assigned**.

---

## 15. Public parity total

| Domain | Operations | Assigned |
|---|---:|---:|
| Source | 6 | 6 |
| Object | 12 | 12 |
| Association | 4 | 4 |
| Evidence | 5 | 5 |
| Registry | 9 | 9 |
| Package | 4 | 4 |
| Result | 7 | 7 |
| Version | 2 | 2 |
| Search | 1 | 1 |
| Similarity | 1 | 1 |
| Render | 1 | 1 |
| MCP | 1 | 1 |
| System | 14 | 14 |
| **Total** | **67** | **67** |

**Unassigned public operation: 0**.

---

## 16. Global CLI controls

| CLI control | GUI mapping | Parity rule |
|---|---|---|
| `--db <path>` | Workspace / DB selector | Required |
| `SGOKB_DB` default | default/recent Workspace resolution候補 | GUI implementation detail。current workspaceを常に表示 |
| `--format json|text` | none | CLI transport-only。GUI parity対象外 |

Environment-backed path / runtime defaultsはSettings / Advancedで表示・override可能にしてよいが、具体設計はP-GUI-02以降で固定する。

---

## 17. Advanced Search Generation operator — 6 actions

これはpublic 67-operation parity gateとは別inventoryである。

Placement: `System -> Advanced -> Search Generation Maintenance`.

| Action | Side effect | GUI requirement |
|---|---|---|
| `status` | READ | generation state表示 |
| `bootstrap` | DERIVED / MAINTENANCE | reason表示・実行確認 |
| `build` | DERIVED / MAINTENANCE | candidate build progress / result |
| `cutover <generation-id>` | MAINTENANCE | target generation、reason、smoke有無を明示して確認 |
| `rollback [generation-id]` | MAINTENANCE | rollback target、reason、smoke有無を強く確認 |
| `recover` | MAINTENANCE | interrupted build recovery result |

これらをnormal Search screenの一般操作へ混在させない。

---

## 18. GUI-only capability inventory

以下はCLI operation countに含めない。

| GUI-only capability | Canonical effect | Rule |
|---|---|---|
| Workspace recent list | none | local GUI state |
| Master-detail layout | none | presentation only |
| local table sort/filter | none | presentation only |
| drag-and-drop import | none by itself | final Importは`source import` semantic capabilityを呼ぶ |
| saved views / dock layout | none | local GUI state |
| command palette | none by itself | existing capability launcher |
| Markdown preview | none | render/display only |
| relation graph | none | read visualization only |
| provenance graph | none | read visualization only |
| GUI local operation history | none | canonical auditと区別 |
| Equivalent CLI display | none | documentation / support only |
| runtime dashboard | none except explicit runtime actions | observationsとactionsを区別 |

GUI-only featureはhidden canonical write pathを作らない。

---

## 19. P-GUI-10 acceptance use

P-GUI-10では本matrixを再利用し、各rowについて最低限次を検証する。

```text
Implemented?
Reachable?
Correct target identity?
Equivalent canonical effect?
Equivalent precondition?
Warnings preserved?
Failure category preserved?
Safety class satisfied?
CLI regression absent?
```

P-RAWでPackage / Result surfaceが変更された場合、P-GUI-08開始前に本matrixの37-47を改訂する。
