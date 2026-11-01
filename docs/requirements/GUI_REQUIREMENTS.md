# SGOKB GUI Requirements

Updated: 2026-10-28

- Status: **Accepted for Phase P / P-GUI-01**
- Task: `P-GUI-01 [P0] GUI requirements / compatibility contract`
- Baseline: SGOKB `v1.1.0`
- GUI framework direction: PySide6 / Qt for Python
- Companion decision: `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- Capability matrix: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`

---

## 1. Purpose

本書は、SGOKBに追加するDesktop GUIの機能要件を定義する。

GUIの目的は、既存のoperator-facing `sgokb` CLIを廃止することではなく、同じSGOKB Application / Service capabilityを、日常操作に適したDesktop UIから安全に利用できるようにすることである。

GUIはCLIのsubprocess wrapperを主要実装としない。CLIとGUIはtransport / presentationが異なる同格clientとし、canonical behaviorは共有Application / Service boundaryへ集約する。

```text
CLI ---------┐
             │
GUI ---------┼--> Application / Service --> Repository / Retrieval / Exchange
             │
MCP(read) ---┘
```

Phase P後もCLIはfirst-class interfaceとして維持する。

---

## 2. Compatibility definition

### GUI-R-001 Semantic compatibility

GUI互換とは、CLI文字列やstdout表示を模倣することではなく、対応するoperationについて次が成立することを意味する。

1. 同じuse caseを実行できる。
2. 同じcanonical Object / Source / Evidence / Version等を対象にする。
3. 成功時に同じcanonical effectを持つ。
4. 同じprecondition / validation / integrity ruleを適用する。
5. 同じexternal-egress / review / acknowledgement boundaryを維持する。
6. 同じruntime degradation semanticsを維持する。
7. 同じfailure categoryを失わずoperatorへ提示する。
8. GUI固有のpresentation支援がcanonical semanticsを変更しない。

GUIはCLIのJSON envelope `sgokb.cli/1.0`を内部APIとして利用する必要はない。GUIはtransport-neutral Application / Service APIを利用する。

### GUI-R-002 Public CLI parity target

SGOKB `v1.1.0`のpublic `sgokb` surface **67 operations** をGUI capability parity対象とする。

対象domain:

- Source: 6
- Object: 12
- Association: 4
- Evidence: 5
- Registry: 9
- Package: 4
- Result: 7
- Version: 2
- Search: 1
- Similarity: 1
- Render: 1
- MCP: 1
- System / Maintenance: 14

完全な割当は`docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`を正本とする。

`--db`はGUI Workspace / DB selectionへ対応させる。`--format json|text`はCLI transport-only concernであり、GUI parity requirementの対象外とする。

### GUI-R-003 R2 generation operator

`python -m sgokb.cli.generation`はpublic `sgokb` namespaceとは別のoperator entrypointであるため、通常navigationへ露出しない。

Phase Pでは以下の6操作を **Advanced / Search Generation Maintenance** capabilityとして扱う。

- status
- bootstrap
- build
- cutover
- rollback
- recover

これらは67-operation public parity gateとは分離するが、P-GUI-09でAdvanced surfaceとして扱う。通常operatorが誤操作しないようSystem / Maintenance配下へ隔離する。

---

## 3. Identity and selection requirements

### GUI-R-010 Stable identity

canonical writeの対象Identityはstable IDをauthoritativeとする。

Objectの場合、GUI上ではname / alias / search resultを人間向けdiscoverabilityに利用してよいが、WRITE実行時は選択済み`object_id`へ解決してからApplicationへ渡す。

GUIがfuzzy searchやpartial matchを提供すること自体は許可する。ただしfuzzy resultを暗黙にcanonical targetへ変換してwriteしてはならない。

### GUI-R-011 Ambiguity

同名・alias衝突などでtargetが一意でない場合、GUIは候補を表示してoperatorの明示選択を要求する。silent first-matchは禁止する。

### GUI-R-012 Version identity

accepted Knowledge Versionを表示・比較・renderする場合、current Versionとexplicit historical VersionをUI上で区別する。

historical Versionをcurrentとして誤表示しない。

---

## 4. Main navigation requirements

### GUI-R-020 Application shell

最小navigationは次を持つ。

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

Version / Relation / Render等はObject detailから到達可能にし、必要に応じて独立viewへ遷移できる。

### GUI-R-021 Workspace

GUIは1つのactive SQLite DBをWorkspaceとして開く。

最低限:

- DB path選択
- recent Workspace
- current Workspaceの明示
- open failure / migration failure表示
- Workspace切替前のrunning operation確認

を提供する。

Phase Pでは1 window内で複数DBを同時mutationすることを必須要件としない。

### GUI-R-022 Dashboard

Dashboardはcanonical Knowledgeの編集画面ではなく、状態確認と主要入口を提供する。

最低限の候補:

- current Workspace
- Source / Object / Evidence等の概数
- pending Result / Registry Proposal
- derived/index state
- runtime warnings
- recent GUI operations

Dashboardの表示のためにcanonical schemaへGUI専用write stateを混入させない。

---

## 5. Object requirements

### GUI-R-030 Object list / detail

Object一覧とdetailをmaster-detail方式で操作できること。

対象capability:

- list
- show registry data
- show current / explicit Knowledge Version
- add
- rename
- active / archived変更
- alias list / add
- primary Class変更
- additional Class add / remove
- events
- relations

### GUI-R-031 Relation write boundary

GUIにaccepted Relationの直接編集機能を追加しない。

Relation writeは既存contractどおり、Package -> Object Result -> Validation / Review -> Import経路でのみ行う。

Relation detailはread-onlyとする。

### GUI-R-032 Canonical mutation preview

Object name / status / Class等のcanonical mutationでは、実行対象Objectと変更内容がoperatorに明確であること。

単純writeでは明示的なApply/Save actionをconfirmationとしてよい。archive、primary Class replacement等の影響が大きい操作では追加confirmationを要求できる。

---

## 6. Source requirements

### GUI-R-040 Source import

Web Capture Bundleをfile dialogからimportできること。

GUI convenienceとしてdrag-and-dropを提供してよい。

Directory batch importをGUIから提供する場合、item単位のsuccess / failureとpartial outcomeを表示する。

### GUI-R-041 Source processing

Snapshot normalizationをGUIから実行できること。

以下を指定可能にする。

- target Snapshot / all applicable Snapshot
- chunk size
- overlap
- auxiliary inclusion

processはcanonical Evidenceを生成するWRITEであるため、完了後に生成run / Evidence数を表示する。

### GUI-R-042 Effective selection

Effective Snapshot / Normalization Run変更ではreason入力を必須とする。

「新しいため自動でeffective化」するGUI shortcutを追加しない。

### GUI-R-043 Raw inspection

Source / Snapshot detailからRaw Artifact metadataへ到達可能にする。

少なくとも次を表示可能にする。

- artifact ID
- logical path
- media type
- byte size
- sha256
- storage referenceの人間向け表示

Raw bytes previewはmedia typeと安全性に応じて後続Taskで設計する。

---

## 7. Evidence and Association requirements

### GUI-R-050 Evidence browsing

Evidenceについて以下を提供する。

- candidate retrieval
- bounded selection
- detail
- provenance
- lexical / semantic / hybrid search

### GUI-R-051 Evidence selection UX

manual include / excludeをmouse / keyboard双方から操作できること。

selection budgetについて最低限:

- selected item count
- estimated tokens
- bytes
- omitted count

を表示する。

Evidence selection自体はcanonical writeではない。

### GUI-R-052 Provenance

Evidence detailからSource / Snapshot / Normalization Run / Raw Artifactへ追跡可能なpresentationを提供する。

Phase P RAW Grounding導入後もこのtraceabilityを維持する。

### GUI-R-053 Association

Object <-> Source associationについてlist / suggest / set / clearを提供する。

status `candidate / confirmed / excluded`、subject relationship、noteを扱えること。

semantic suggestがruntime unavailableの場合、失敗またはdegradationを明示し、silent cloud fallbackしない。

---

## 8. Registry requirements

### GUI-R-060 Registry browse

Class / Relation Typeをbrowse / inspectできること。

### GUI-R-061 Proposal workflow

Registry Proposalは次の状態遷移をUI上でも維持する。

```text
pending
  -> accept / reject
accepted
  -> explicit apply
```

`accept`と`apply`を1 clickのhidden composite writeへ統合してはならない。

Proposal detail、decision note、apply stateを表示する。

---

## 9. Package / Result requirements

### GUI-R-070 Deferred implementation boundary

Package / Result capabilityはGUI parity対象であるが、P-RAWのRaw-grounded contractがPackage / Result schemaを変更する。

したがってP-GUI-01では画面責務を固定し、最終実装はP-RAW完了後のP-GUI-08で行う。

### GUI-R-071 Package workflow

最終GUIは少なくとも次を扱う。

```text
selection / grounding preview
  -> build
  -> stage
  -> preflight
  -> export
```

EXTERNAL export前にdestination、Package identity、preflight disposition、送出内容summaryを表示する。

### GUI-R-072 Result workflow

最終GUIは少なくとも次を扱う。

```text
detect / receive
  -> pending / list
  -> validate
  -> review
  -> explicit import
```

Validation failure、stale binding、review-required、import blocking conditionを状態として区別する。

### GUI-R-073 No automatic external AI call

Phase P GUIはExternal AI API自動呼出しを標準機能としない。

Package exportとResult receiveのHuman-in-the-loop boundaryを維持する。

---

## 10. Version and Render requirements

### GUI-R-080 Version show / diff

Version detailとbefore/after diffを表示できること。

JSON構造だけでなく、人間向けstructured / Markdown previewを提供してよい。

### GUI-R-081 Render

Object current Versionまたはexplicit VersionのMarkdown renderを実行できること。

生成物のpathとpreviewを表示可能にする。

Renderはderived artifactでありcanonical Knowledgeを変更しない。

### GUI-R-082 Undo boundary

GUI form内の未commit編集にUndo/Redoを提供してよい。

accepted Version、import済みKnowledge、selection event等のcanonical historyを一般的なCtrl+Zで巻き戻す機能は提供しない。

---

## 11. Search / Similarity requirements

### GUI-R-090 Search modes

Lexical / Semantic / Hybridを明示的に切り替え可能にする。

Search filterとしてCLIのsemantic optionをGUIから設定可能にする。

少なくとも:

- primary Class
- additional Class
- ancestor Class
- Facet
- Version
- temporal scope
- valid-at
- derivation kind
- include archived
- limit / candidate limit

を扱う。

### GUI-R-091 Runtime requirement

Semantic / Hybrid full runtimeではlocal Embedding + Qdrantを使用する。

runtime failureからcloudへsilent fallbackしない。

HybridがLexicalへdegradeした場合、結果そのものとdegraded channel warningを同時表示する。

### GUI-R-092 Similarity

Object / Facet similarityを提供する。

Facet-specific similarityでFacetが利用できない場合、overall similarityへsilent fallbackしない。

---

## 12. MCP requirements

### GUI-R-100 MCP boundary

GUIからMCP runtime state / configuration / serve capabilityへ到達可能にする。

MCP自体のcurrent read-only contractは変更しない。

GUIがMCPを経由してcanonical writeを追加してはならない。

### GUI-R-101 Lifecycle

MCP server lifecycleをGUIで扱う場合、GUI process terminationとserver terminationの関係を明示する。

最終lifecycle designはP-GUI-09で固定する。

---

## 13. System / Maintenance requirements

### GUI-R-110 System operations

GUIはcurrent public CLIに対応して少なくとも以下を扱う。

- system status
- integrity
- derived status / sync
- index status / rebuild
- backup status / create
- composite backup create / verify
- restore plan / apply
- composite restore plan / apply

### GUI-R-111 Restore safety

Restoreはplanとapplyを明確に分離する。

既存target overwrite時のexplicit acknowledgementをGUIでも省略しない。

Apply前に少なくともtarget、backup identity、overwrite対象、recovery上の注意を表示する。

### GUI-R-112 Derived operations

Derived sync / index rebuildはcanonical Knowledgeを変更しないが、時間・GPU・Qdrant等のresourceを消費し得る。

GUIはprogress / statusを提供し、operation中もUI event loopをblockしない。

---

## 14. Safety-class presentation requirements

GUIはoperationを次のclassで認識する。

| Class | GUI baseline |
|---|---|
| READ | 原則即時実行。canonical mutationなし |
| DERIVED | progress / result / replace scopeを明示。高コストrebuildは開始確認可 |
| WRITE | targetとmutationを明示し、明示的Apply/Saveでcommit |
| EXTERNAL | destination / data summary / preflight / acknowledgementを必須表示 |
| MAINTENANCE | plan / recovery information / destructive acknowledgementを強く表示 |

1 operationが複数classを持つ場合、より強いsafety requirementを適用する。例: Package exportはEXTERNALかつaudit write、composite restore applyはMAINTENANCEかつdestructive writeである。

---

## 15. Error / warning requirements

### GUI-R-120 Error taxonomy

CLI exit semanticsをGUIへ次のように写像する。

| CLI | Meaning | GUI requirement |
|---:|---|---|
| 0 | success | success result / completion state |
| 1 | unexpected internal | Unexpected/Internal error。diagnostic detailを保持 |
| 2 | invalid input | field / request validation error |
| 3 | not found / ambiguity | target not found / selection required |
| 4 | blocked / unmet precondition | blocked state。必要action / acknowledgementを表示 |
| 5 | runtime unavailable | Runtime unavailable / degraded capability |
| 6 | I/O / external/provider | I/O / external operation failure |
| 7 | integrity / consistency | Integrity alert。危険な後続mutationを抑止可能にする |
| 8 | partial | batch partial result。success / failure itemを分離表示 |

### GUI-R-121 Warnings

CLIでsuccess + warningsとなるケースをGUIで単純successへ潰してはならない。

Search degradation、Package preflight warning等をoperatorが確認できるwarning surfaceへ表示する。

### GUI-R-122 Details

Exception stack traceを常に一般画面へ露出する必要はないが、error code、human message、structured details、関連operationをdiagnostic viewで確認可能にする。

---

## 16. Progress and cancellation requirements

### GUI-R-130 Responsiveness

Source process、semantic retrieval、index rebuild、backup / restore等のlong-running operation中もmain UIを応答可能に保つ。

thread / worker / process architectureはP-GUI-02で決める。

### GUI-R-131 Cancellation semantics

UIにCancelを表示するのは、安全に中断できるoperationだけとする。

「ボタンを押せるがcanonical commitは既に完了している」のような偽のcancel semanticsを禁止する。

atomic / non-cancellable operationはその旨を表示する。

### GUI-R-132 Partial batch

batch operationではoverall progressだけでなくitem別resultを保持する。

CLI exit 8相当をGUIで「失敗」と一括表示せず、partialとして扱う。

---

## 17. GUI-only convenience requirements

### GUI-R-140 Allowed GUI-only features

以下はcanonical semanticsを変更しない範囲でGUI-only機能として許可する。

- Master-detail
- column sort / local filtering
- saved view
- dock / layout persistence
- recent Workspace
- drag-and-drop
- keyboard shortcuts
- command palette
- Markdown preview
- relation / provenance visualization
- local GUI operation history
- Equivalent CLI表示

### GUI-R-141 No hidden canonical capability

GUI-only convenienceから新しいcanonical write capabilityを作ってはならない。

新しいcanonical operationが必要になった場合、transport-neutral Application / Service capabilityとして設計し、CLIにも同等operationを追加するか、別Decisionでparity policyを明示的に変更する。

### GUI-R-142 GUI operation history

GUI local operation historyはpresentation / convenience logとし、canonical audit logと誤認させない。

既存のcanonical audit / event / proposal review / exchange auditがあるoperationではそれをauthorityとして表示する。

GUIを経由しないCLI操作までGUI local historyが完全に記録していると主張しない。

---

## 18. Equivalent CLI requirement

### GUI-R-150 Equivalent command display

canonical / operator operationについて、対応するpublic CLI commandを表示可能にする。

用途:

- operator学習
- automationへの移行
- GUI / CLI parity確認
- support / debugging

GUIが複数operationを連続実行するworkflowでは、単一commandを偽装せずCLI command sequenceとして表示する。

### GUI-R-151 Not execution backend

Equivalent CLI文字列は説明用であり、GUIのbusiness logic実行backendとしてshell executionしてはならない。

---

## 19. Presentation / usability requirements

### GUI-R-160 Model/View suitability

大量のObject / Source / Evidence / search resultを扱う一覧は、全件Widget生成を前提とせずModel/View方式で実装可能な要件とする。

具体的Qt architectureはP-GUI-02で固定する。

### GUI-R-161 Filtering

一覧画面はdomainに応じてsearch / filter / sortを提供する。

UI filterとcanonical search semanticsを混同しない。例えば現在ロード済み行だけのlocal filterはその旨を区別する。

### GUI-R-162 Keyboard

Evidence review、result review、list navigation等の反復操作はkeyboardだけでも主要操作が可能であることを目標とする。

### GUI-R-163 DPI / scaling

Windows 11の高DPI displayで文字・controlが実用上崩れないこと。

正式なReference Workstation acceptanceはP-GUI-10で行う。

---

## 20. Security requirements

### GUI-R-170 External data

Package / Raw / Result path等、外部由来データをUI表示するだけでcode executionしない。

HTML / Markdown previewを実装する場合、active content / external resource loadingの扱いをP-GUI-02以降で安全側に固定する。

### GUI-R-171 Secrets

GUI Settingsやdiagnostic outputにcredential / tokenを平文で不用意に表示・exportしない。

Phase P標準runtimeはlocal-firstであり、Semantic failure時にcloud credentialを自動探索してfallbackしない。

---

## 21. Compatibility with RAW Grounding workstream

GUI-R-180として、P-GUI-01時点ではPackage / Resultの**current v1.1.0 capability slot**を67-operation matrixへ割り当てるが、P-GUI-08 implementationはP-RAWで確定するPackage / Result v2 contractに従う。

P-RAWがCLI command nameを維持して内部semanticsを変更する場合、GUIも新contractへ同時追従する。

P-RAWがbreaking CLI surface変更を必要とする場合は、capability matrixを更新してからP-GUI-08を開始する。

---

## 22. Acceptance requirements for P-GUI-01

P-GUI-01は次を満たした時点でCompleteとする。

1. public `sgokb` 67 operationsすべてがGUI capabilityへ割り当て済み。
2. `--db` / `--format`等のtransport / workspace mappingが定義済み。
3. R2 generation operatorのAdvanced / Maintenance placementが確定済み。
4. semantic compatibilityの定義が確定済み。
5. READ / DERIVED / WRITE / EXTERNAL / MAINTENANCEのGUI safety表現が確定済み。
6. CLI error / warning semanticsのGUI mappingが確定済み。
7. Relation direct write禁止、Registry accept/apply分離、Restore acknowledgement等の既存safety boundaryが維持される。
8. GUI-only hidden canonical write pathが明示的に禁止される。
9. Package / Result GUIのP-RAW dependencyが明示される。
10. 次Task P-GUI-02 / P-GUI-03へ渡すarchitecture constraintsが明確である。

---

## 23. Non-goals

P-GUI-01では次を確定しない。

- Qt Widgetごとの具体レイアウト
- threading implementation
- module/package structure
- installer / executable packaging方式
- Qt/PySide6 license compliance implementation
- RAW Grounding schema詳細
- Qdrant Windows lifecycle詳細
- visual theme / icon design
- GUI automated test frameworkの最終選定

これらは後続Taskで決める。

---

## 24. Post-release GUI startup / Runtime-health amendment — 2026-11-01

This section is a post-`v2.0.0` current-state amendment. It does not retroactively change the completed P-GUI-01 acceptance boundary or move the frozen `v2.0.0` tag.

### GUI-PR-001 Consoleless Windows repository launcher

A Windows source checkout with the repository virtual environment MUST provide `scripts\launch-sgokb-gui.vbs` as a normal operator launch path. It MUST launch the GUI through `.venv\Scripts\pythonw.exe` without leaving PowerShell, CMD, or the script host visible for the lifetime of the GUI. The packaged `sgokb-gui` entrypoint remains supported.

### GUI-PR-002 Immediate startup loading surface

After `QApplication` exists, the GUI MUST show and flush a startup Splash before importing the heavier SGOKB runtime/view modules and before semantic native dependency preload. The Splash MUST remain a presentation-only startup surface and MUST NOT create a second backend/runtime path.

### GUI-PR-003 Preload/threading safety preservation

The startup-Splash change MUST preserve the accepted semantic-native safety boundary: PyTorch / Transformers / Sentence Transformers native preload occurs on the Qt main thread before `BackendCoordinator` creates/starts the backend QThread. Splash completion occurs only after the main window is shown.

### GUI-PR-004 Supported legacy Search-generation health

The GUI MUST present the shared `sgokb.runtime-health/1.0` generation component without inventing a warning for the supported no-pointer compatibility route. When current accepted Knowledge exists, no explicit Search generation is active, and the backend reports `routing_mode=legacy`, the expected presentation is:

```text
Search generation = HEALTHY
active=none (legacy routing)
issue = none
```

Opening or refreshing Runtime Dashboard MUST NOT build, activate, cut over, or otherwise mutate Search-generation state. Explicit missing/stale/not-ready generation or Vector binding state remains degraded according to the shared backend contract.

### GUI-PR-005 Post-release acceptance authority

Implementation, regression, documentation audit, and interactive acceptance are recorded in:

`docs/evaluation/POST_RELEASE_GUI_STARTUP_RUNTIME_HEALTH_2026_11_01.md`

Current acceptance state is `Interactive PASS / 15 of 15 OK`.
