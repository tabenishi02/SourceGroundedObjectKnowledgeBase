# Phase P — GUI / RAW Grounding / Runtime Modernization Tasks

Updated: 2026-10-28

- Status: **Planned / Not Started**
- Planning authority: `PHASE_P_MODERNIZATION_PLAN.md`
- Priority order: **GUI > RAW Grounding > Runtime**

## 1. Execution policy

Phase Pは3 Workstreamに分ける。

```text
P-GUI      PySide6 Desktop GUI
P-RAW      Evidence-selected / Raw-grounded exchange
P-RUNTIME  Windows / Qdrant runtime operations
```

GUIを最優先する。ただし`Package / Result`画面はRAW Grounding contractを直接表現するため、GUI基盤・主要画面を先行し、P-RAW完了後に完成させる。

各Taskは、設計確定が必要な場合に「設計 → review / approval → implementation → test」の順を維持する。既存current contractを変更するTaskは、実装だけでなくrequirements / decisions / design / operations / migration / compatibility documentationを更新する。

---

# Workstream A — P-GUI

## P-GUI-01 [P0] GUI requirements / compatibility contract

**目的:** CLI互換GUIの意味を正式定義する。

実施内容:

- public `sgokb` command surfaceをGUI capability inventoryへマッピングする。
- Source / Object / Association / Evidence / Registry / Package / Result / Version / Search / Similarity / Render / MCP / Systemを対象とする。
- R2 generation operatorを通常surfaceとAdvanced / Maintenanceのどちらへ置くか確定する。
- GUIでのCLI compatibilityを「同じApplication semantics / same canonical effect / equivalent safety boundary」と定義する。
- GUI-only convenience featureとcanonical operationを区別する。
- READ / DERIVED / WRITE / EXTERNAL / MAINTENANCEのGUI表現を確定する。
- CLI error / warning contractをGUI error modelへマッピングする。

成果物:

- GUI requirement document
- CLI ↔ GUI capability matrix
- GUI safety / compatibility decision

完了条件:

- public CLI operationに未割当GUI capabilityがない。
- GUI-only hidden canonical write pathを禁止するcontractが明記されている。

Dependencies: none

---

## P-GUI-02 [P0] PySide6 application architecture / packaging / license design

**目的:** Desktop applicationの技術基盤を固定する。

実施内容:

- PySide6をformal GUI frameworkとしてDecision化する。
- `QMainWindow` / Model-View / dock / settings / dialogs / status modelの使用境界を決める。
- GUI package/module layoutを決める。
- CLI / GUI共有Application composition rootを設計する。
- GUI main threadとlong-running operationのworker/thread boundaryを設計する。
- packaging方式を比較し、Windows distribution baselineを決める。
- PySide6 / Qt LGPLv3等のOSS配布要件をRelease gateへ追加する。
- `THIRD_PARTY_LICENSES` / notices / library replacement可能性を確認する。

完了条件:

- GUIがCLI subprocess wrapperではなくApplication層を共有する設計でfreezeされている。
- OSS配布時のlicense compliance checklistが存在する。

Dependencies: P-GUI-01

---

## P-GUI-03 [P0] Transport-neutral Application boundary audit / refactor plan

**目的:** CLI専用ロジックをGUIへ複製しないための境界を整える。

実施内容:

- `sgokb.cli.main` dispatch内のbusiness logicを棚卸しする。
- `Application` / `ObjectAdminApplication` / `KnowledgeReadApplication` / exchange / maintenance serviceでGUIから再利用できる範囲を確認する。
- CLIに閉じているcomposition / validation / result formatting処理を抽出すべき箇所を特定する。
- GUI Controller / ViewModelが利用するtransport-neutral APIを定義する。
- raw SQL direct accessをGUI public contractにしない。

完了条件:

- GUI実装でCLI parser / stdout JSONを経由しなくてよいApplication APIが定義されている。

Dependencies: P-GUI-01, P-GUI-02

---

## P-GUI-04 [P0] GUI shell / Workspace / navigation foundation

**目的:** Desktop GUIとして起動・DB選択・画面遷移できる最小基盤を実装する。

実施内容:

- GUI entrypoint追加。
- Workspace / SQLite DB selector。
- recent workspace記録。
- main navigation。
- status bar / global warning area。
- settings persistence。
- basic theme / DPI / font scaling確認。
- safe startup / failed DB open / migration error表示。

想定navigation:

```text
Home / Dashboard
Objects
Sources
Evidence
Associations
Search
Packages
Results
Registry
System
Settings
```

完了条件:

- fresh DB / existing DBをGUIから安全に開ける。
- GUI終了後もCLIから同じDBを利用できる。

Dependencies: P-GUI-02, P-GUI-03

---

## P-GUI-05 [P0] Object / Source / Evidence / Association GUI

**目的:** 日常Knowledge収集の主要CLI操作をGUI化する。

実施内容:

### Object

- list / detail / add / rename / archive
- alias管理
- primary / additional Class管理
- events / relations / current Knowledge表示

### Source

- import（file dialog / drag & drop）
- status / snapshot list
- process
- effective snapshot / run selection
- Raw Artifact / metadata / provenance表示

### Evidence

- candidates / selection
- show / provenance
- evidence search
- manual include / exclude
- budget usage表示

### Association

- list / suggest / set / clear
- Object / Source master-detail review

完了条件:

- corresponding CLI operationと同じcanonical effectをGUIで実行できる。
- Evidence selectionをkeyboard / mouseの両方で効率的に行える。

Dependencies: P-GUI-04

---

## P-GUI-06 [P0] Search / Similarity / Registry / Version GUI

**目的:** Knowledge利用・管理系CLIをGUI化する。

実施内容:

- Lexical / Semantic / Hybrid search
- search filters sidebar
- Similarity / Facet-specific Similarity
- Class / Relation Type registry browse
- Registry Proposal list / detail / accept / reject / apply
- Proposal acceptとapplyを別操作として維持
- Version show
- Version diff
- structured / Markdown diff preview
- Render preview / export

完了条件:

- current CLI semanticsと同じscope / degradation / warningを表示できる。
- dangerous Registry mutationはpreview / confirmationを経由する。

Dependencies: P-GUI-04

---

## P-GUI-07 [P0] Progress / error / safety / audit UX

**目的:** CLIでは表現しにくいDesktop operation safetyを追加する。

実施内容:

- long-running operation progress表示。
- cancellation可能 / 不可能なoperationを区別する。
- batch partial failure表示。
- error code category表示。
- warning / degradation center。
- WRITE / EXTERNAL / MAINTENANCE confirmation。
- pre-commit form undo / redo範囲を限定設計する。
- canonical version rollbackをGUI Undoへ混同しない。
- Equivalent CLI command表示。
- GUI operation history / audit surface。

完了条件:

- CLIのblocked / runtime / I/O / integrity / partial等の意味を失わない。
- EXTERNAL / overwrite restoreを誤操作しにくいUIになっている。

Dependencies: P-GUI-04

---

## P-GUI-08 [P0] Package / Result GUI on RAW Grounding contract

**目的:** 新RAW Grounding workflowをGUIで操作可能にする。

実施内容:

- Evidence selection -> Raw resolution preview
- Raw Artifact inclusion list
- Package build / stage / preflight / export wizard
- External Egress confirmation
- Result detect / receive / list / pending
- validate / review / import
- RAW grounding reference表示
- stale / partial / review-required状態表示
- current Knowledgeとのdiff

完了条件:

- P-RAWで確定したPackage / Result contractを完全にGUI表示できる。

Dependencies: P-RAW-01..P-RAW-06, P-GUI-04, P-GUI-07

---

## P-GUI-09 [P1] System / Maintenance / MCP / Advanced GUI

**目的:** operator maintenance CLIをGUIへ統合する。

実施内容:

- system status / integrity
- derived status / sync
- index status / rebuild
- backup status / create
- composite backup create / verify
- restore plan / apply
- composite restore plan / apply
- MCP serve state / configuration support
- R2 generation operatorを採用する場合のAdvanced surface

完了条件:

- destructive maintenance operationはplan / preview / acknowledgementを維持する。

Dependencies: P-GUI-07, P-RUNTIME-03

---

## P-GUI-10 [P0] GUI parity / usability / regression acceptance

**目的:** GUIがCLI互換interfaceとして成立することを受入する。

実施内容:

- CLI ↔ GUI capability matrixを全件再確認。
- representative operationでcanonical state equivalenceを検証。
- GUI-only hidden write pathがないことを確認。
- keyboard / DPI / long operation / error / restart scenariosを検証。
- headless CLI regressionを確認。
- GUI automated tests / smoke testsを整備。

完了条件:

- public CLI capabilityのGUI coverage gateを満たす。
- existing CLI / MCP regressionがない。

Dependencies: P-GUI-05..P-GUI-09

---

# Workstream B — P-RAW

## P-RAW-01 [P0] Current Evidence Package / Result impact survey

**目的:** Evidence本文からRaw Artifactへ切り替える影響範囲を確定する。

実施内容:

- Package Builder
- manifest schema
- instructions
- Object Result schema
- Result Validation
- Review / Diff
- Import / Version / Evidence Link
- accepted Knowledge provenance
- tests / benchmark / operations docs

を横断調査する。

完了条件:

- breaking / compatible / migration-required箇所が一覧化される。

Dependencies: P-GUI-05のEvidence UX要件を参照可能だが実装依存なし

---

## P-RAW-02 [P0] Evidence -> Raw Artifact provenance resolution contract

**目的:** 選択Evidenceから送出対象Rawを決定する規則を固定する。

実施内容:

- Evidence -> run -> `normalization_run_artifacts` -> Raw Artifact traversal
- snapshot / source binding
- multiple Evidenceが同一Rawを指す場合のdedup
- multiple Raw Artifactがrun inputの場合のselection rule
- auxiliary artifact inclusion policy
- logical path / media type / byte size / hash handling
- missing / changed / hash mismatch fail-closed rule
- selected Evidenceとincluded Rawのtraceability

完了条件:

- deterministic Raw resolution algorithmが定義される。

Dependencies: P-RAW-01

---

## P-RAW-03 [P0] RAW-bearing Package v2 design

**目的:** External AIへRawを渡す新Package contractを設計する。

実施内容:

- Package schema versioning
- raw directory layout
- manifest raw artifact entries
- `selected_evidence_ids`とRaw inclusion mapping
- current Object / schema / instructions artifact構成
- budgetの定義見直し
- preflight / secret / size / media type checks
- reproducibility / integrity
- old Package compatibility policy

完了条件:

- Package v2 schema / manifest / instructions designがfreezeされる。

Dependencies: P-RAW-02

---

## P-RAW-04 [P0] Raw-grounded Object Result v2 design

**目的:** AIが実際に読んだRaw materialとResult grounding referenceを一致させる。

実施内容:

- grounding target identityを定義する。
- Raw Artifact / Raw locator / Evidenceとの関係を定義する。
- statement / attribute / relation grounding schemaを更新する。
- Package membership validationをRaw contractへ更新する。
- derivation kind / attribution / temporal semanticsを維持する。
- current Evidence Linkとの保存互換性を設計する。
- v1 Result / v2 Result compatibility / migration方針を決める。

完了条件:

- External AIが参照していないEvidence IDを擬似的にgroundingとして出力する必要がないcontractになる。

Dependencies: P-RAW-03

---

## P-RAW-05 [P0] RAW Grounding implementation

**目的:** P-RAW-02〜04を実装する。

実施内容:

- Raw resolver service
- Package Builder v2
- manifest / instructions / schema
- Result receive / validate
- Review / diff
- Import / provenance persistence
- CLI option / output変更が必要な場合の実装
- old exchange artifact取扱い

完了条件:

- Raw bytesをPackageへ格納し、Resultをvalidate / review / importできる。

Dependencies: P-RAW-02, P-RAW-03, P-RAW-04

---

## P-RAW-06 [P0] RAW Grounding acceptance / compatibility / documentation

**目的:** 新しいexternal AI boundaryを正式受入する。

実施内容:

- deterministic Raw resolution test
- duplicate Raw dedup test
- missing / modified Raw failure test
- manifest hash / package integrity test
- preflight / egress safety test
- Result membership / grounding validation test
- v1/v2 compatibility test where supported
- real Object end-to-end acceptance
- requirements / decisions / design / operations更新

完了条件:

- Raw-based Package -> external AI -> Result -> Importのend-to-endがPASSする。

Dependencies: P-RAW-05

---

# Workstream C — P-RUNTIME

## P-RUNTIME-01 [P1] Windows Qdrant runtime operational design

**目的:** Windows起動後にQdrantを自動利用可能にする標準方式を確定する。

実施内容:

- Docker / Docker Compose baseline確認
- Docker Desktop / Engine startup条件
- Qdrant version pinning
- localhost binding
- named volume
- restart policy
- upgrade / rollback
- no-Docker alternativeをsupportするか判断
- OSS利用者向けinstallation boundary整理

完了条件:

- Reference Windows environmentで採用方式が確定する。

Dependencies: none

---

## P-RUNTIME-02 [P1] Qdrant Compose / configuration assets

**目的:** 再現可能なQdrant runtime構成をrepositoryで管理する。

実施内容:

- Compose file / environment template
- version pin
- named volume
- ports
- health check
- startup / shutdown commands
- persistent storage location説明
- upgrade手順

完了条件:

- fresh Windows environmentでdocumented commandから同じQdrant runtimeを構築できる。

Dependencies: P-RUNTIME-01

---

## P-RUNTIME-03 [P1] Runtime health/status application boundary

**目的:** CLI / GUIからQdrant等のruntime状態を安全に観測する。

実施内容:

- SQLite health
- Embedding provider health
- Qdrant endpoint / version / collection availability
- Vector generation / derived state
- error classification
- GUI/CLI共通health model

完了条件:

- GUIがQdrant lifecycle ownerにならず状態を取得できる。

Dependencies: P-RUNTIME-01

---

## P-RUNTIME-04 [P1] Windows login auto-start integration

**目的:** Windowsログイン後のmanual Qdrant起動を不要にする。

実施内容:

- container runtime auto-start設定
- Qdrant restart policy確認
- startup ordering
- network readiness / retry behavior
- user-visible troubleshooting
- unexpected stop後の復帰確認

完了条件:

- Windows restart / login後、追加手動操作なしでQdrant healthがreadyになる。

Dependencies: P-RUNTIME-02

---

## P-RUNTIME-05 [P1] GUI Runtime Dashboard integration

**目的:** GUIからsemantic runtime状態を可視化する。

実施内容:

- SQLite
- Embedding
- Qdrant
- Vector / generation
- MCP state where available
- degraded / unavailable reason表示
- troubleshooting entrypoints

完了条件:

- Semantic Search実行前にruntime不足をGUIで判断できる。

Dependencies: P-RUNTIME-03, P-GUI-04

---

## P-RUNTIME-06 [P1] Runtime failure / recovery acceptance

**目的:** 自動起動構成がcanonical safetyを損なわないことを確認する。

実施内容:

- Qdrant unavailable
- container runtime unavailable
- port conflict
- volume persistence
- restart after crash
- vector rebuild
- GUI / CLI degradation
- canonical SQLite integrity unaffected確認

完了条件:

- Runtime障害がcanonical Knowledge破壊へ波及しない。
- reboot / crash / rebuildの代表シナリオがPASSする。

Dependencies: P-RUNTIME-02..P-RUNTIME-05

---

# Cross-workstream closure

## P-CLOSE-01 [P0] Full regression / documentation integration

実施内容:

- existing automated regression
- CLI regression
- MCP regression
- GUI acceptance
- RAW Grounding acceptance
- Runtime acceptance
- current architecture update
- requirements / decisions / operations update
- README / docs index update
- release impact / SemVer determination
- third-party license inventory

完了条件:

- Phase P変更がcurrent authority documentsへ統合される。
- Release gateを満たす。

Dependencies: P-GUI-10, P-RAW-06, P-RUNTIME-06

---

# Recommended execution order

```text
P-GUI-01
  ↓
P-GUI-02
  ↓
P-GUI-03
  ↓
P-GUI-04
  ├─ P-GUI-05
  ├─ P-GUI-06
  └─ P-GUI-07
         ↓
P-RAW-01
  ↓
P-RAW-02
  ↓
P-RAW-03
  ↓
P-RAW-04
  ↓
P-RAW-05
  ↓
P-RAW-06
  ↓
P-GUI-08
  ↓
P-RUNTIME-01 → P-RUNTIME-02 → P-RUNTIME-04
       └──────→ P-RUNTIME-03 → P-RUNTIME-05
                              ↓
                         P-RUNTIME-06
                              ↓
P-GUI-09
  ↓
P-GUI-10
  ↓
P-CLOSE-01
```

P-RUNTIME-01は技術的には早期並行可能だが、project priorityとしてGUI / RAW Groundingを先行する。

# Initial next task

```text
P-GUI-01 [P0] GUI requirements / compatibility contract
```

Phase P開始時はこのTaskから実施する。