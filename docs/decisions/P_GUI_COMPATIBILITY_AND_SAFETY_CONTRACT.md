# P-GUI Compatibility and Safety Contract

Updated: 2026-10-28

- Status: **Accepted / P-GUI-01**
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-01 [P0] GUI requirements / compatibility contract`
- Requirement authority: `docs/requirements/GUI_REQUIREMENTS.md`
- Capability matrix: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Existing CLI authority: `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`

---

## 1. Decision

SGOKB Desktop GUIは、public `sgokb` CLIと**semantic parity**を持つoperator interfaceとして追加する。

GUI互換性はCLI text / JSON envelopeの再現ではなく、次で判定する。

```text
same use case
+ same target identity
+ same canonical effect
+ same validation / precondition
+ same safety boundary
+ same degradation / warning semantics
+ equivalent failure meaning
```

GUIはCLI commandをsubprocess実行するwrapperとして実装しない。

```text
CLI ─┐
     ├─> Application / Service ─> Repository / Retrieval / Exchange
GUI ─┤
     └─ MCP(read)
```

CLIとGUIが同じApplication / Service boundaryへ依存し、CLI parser / stdout JSONはCLI transport concernとして残す。

---

## 2. Public parity boundary

`v1.1.0` current parser上のpublic `sgokb` surfaceは67 operationsである。

この67 operationsをP-GUI-10 parity acceptanceのminimum gateとする。

```text
Source        6
Object       12
Association   4
Evidence      5
Registry      9
Package       4
Result        7
Version       2
Search        1
Similarity    1
Render        1
MCP           1
System       14
----------------
Total        67
```

`--db`はWorkspace selectionへmapする。

`--format json|text`はCLI transport formattingでありGUI parity capabilityには数えない。

---

## 3. Advanced operator boundary

`python -m sgokb.cli.generation`はpublic `sgokb` namespaceとは異なるexplicit operator entrypointである。

次の6 actionsはnormal navigationへ置かない。

```text
status
bootstrap
build
cutover
rollback
recover
```

Phase Pでは`System -> Advanced -> Search Generation Maintenance`相当へ隔離する。

これらは67-operation public parity gateとは別のAdvanced coverageとして扱う。

---

## 4. Side-effect safety contract

### 4.1 READ

READ operationはcanonical stateを変更しない。

GUI baseline:

- 原則即時実行可能
- destructive confirmation不要
- runtime degradation / warningは表示
- historical / current scopeを誤認させない

### 4.2 DERIVED

DERIVED operationはcanonical sourceから再生成可能なartifact / representation / indexへ作用する。

GUI baseline:

- progress表示
- target scope表示
- resource-costが大きいoperationでは開始確認可
- canonical mutationとして表示しない
- cancellation可否を正確に表示

### 4.3 WRITE

WRITE operationはcanonical / persistent operator stateを変更する。

GUI baseline:

- stable target identityを確定
- mutation内容を明示
- explicit Apply / Save / Import等のcommit action
- impactが大きい場合は追加confirmation
- hidden auto-write禁止

すべてのWRITEでmodal dialogを必須とはしない。明示的なcommit action自体をconfirmationとできるが、archive、effective selection、Registry apply、Result import等は影響に応じて強い確認を設ける。

### 4.4 EXTERNAL

EXTERNAL operationはSGOKB managed boundary外へdataを送出する。

GUI baseline:

- destination表示
- package / artifact identity表示
- preflight disposition表示
- 送出内容summary表示
- required acknowledgementを省略しない
- blocked状態をforce bypassしない

### 4.5 MAINTENANCE

MAINTENANCE operationはbackup / restore / recovery等を扱う。

GUI baseline:

- plan / apply分離を維持
- target / source / overwrite scope表示
- recovery information表示
- destructive applyにはexplicit acknowledgement
- failure時にcanonical integrityを最優先

### 4.6 Mixed classification

operationが複数classを持つ場合、最も強いboundaryを適用する。

例:

- `package export` = EXTERNAL + audit WRITE
- `result import` = WRITE + review acknowledgement
- `composite restore apply` = MAINTENANCE + destructive WRITE
- `index rebuild` = DERIVED + high-resource operation

---

## 5. Stable target contract

GUIはname / alias / fuzzy searchをdiscoverabilityに使ってよい。

ただしcanonical mutationはstable identityへ解決後に実行する。

Object WRITEは最終的に`object_id`をtargetとする。

GUIが曖昧候補からfirst matchを自動選択することを禁止する。

---

## 6. No hidden canonical write rule

GUI-only convenience functionからcanonical DBへ直接writeするpathを禁止する。

禁止例:

```text
GUI Widget
  -> sqlite3.execute(...)
```

または

```text
GUI Widget
  -> CLI text command
  -> subprocess
```

をbusiness logicのprimary routeとして利用する構成を禁止する。

許容されるroute:

```text
GUI Controller / ViewModel
  -> transport-neutral Application / Service
  -> Repository / domain service
```

既存Application boundaryが不足する場合はP-GUI-03で共有Applicationへ抽出する。

---

## 7. Canonical write parity policy

GUIに新しいcanonical capabilityが必要になった場合、次のいずれかを満たす必要がある。

1. 既存CLI operationと同じApplication capabilityとして提供する。
2. shared Application capabilityを新設し、CLIにもpublic operationを追加する。
3. CLI parity policyを変更する明示Decisionを先に承認する。

GUIにだけ存在するcanonical writeを暗黙追加してはならない。

GUI-only featureは原則presentation / navigation / workflow assistance / local preferenceへ限定する。

---

## 8. Existing safety boundaries preserved

### 8.1 Relation write

accepted RelationをGUIから直接編集しない。

```text
Read:
Object Relation view

Write:
Package -> Object Result -> validate/review -> import
```

### 8.2 Registry Proposal

`accept / reject`と`apply`を別operationとして維持する。

```text
pending
  -> human decision
accepted
  -> explicit apply
```

GUIがaccept直後にsilent applyしてはならない。

### 8.3 Effective Snapshot / Run

Source selection eventにはreasonを要求する。

新Snapshot / RunをGUI起動時や表示時にsilent effective化しない。

### 8.4 Result Import

Validate / Review / Import境界を維持する。

GUIがvalidでないResultを見た目上のwarningだけでimport可能にしてはならない。

review acknowledgementが必要な場合はexplicit operator actionを要求する。

### 8.5 Restore

Restore planとapplyを分離する。

existing target overwriteのacknowledgementを省略しない。

### 8.6 Semantic runtime

local Embedding / Qdrant failureからcloud providerへsilent fallbackしない。

Hybrid SearchがLexicalへdegradeした場合はwarningを表示する。

---

## 9. CLI error -> GUI error contract

CLI exit categoryはGUI presentationへ次の意味で継承する。

| Exit | CLI meaning | GUI semantic category |
|---:|---|---|
| 0 | success | Success |
| 1 | unexpected internal | Internal / Unexpected |
| 2 | invalid input | Validation / Request Error |
| 3 | not found / ambiguity | Not Found / Selection Required |
| 4 | blocked / unmet precondition | Blocked / Precondition |
| 5 | runtime unavailable | Runtime Unavailable / Degraded |
| 6 | I/O / external/provider | I/O / External Failure |
| 7 | integrity / consistency | Integrity / Consistency Failure |
| 8 | partial batch | Partial Success / Partial Failure |

GUI内部でPython exception hierarchyを直接user contractにしてはならない。

Application / adapter層で意味categoryへ正規化し、GUIはcategory + message + structured detailsとして扱う。

P-GUI-03でCLI専用`_error_exit()`相当のtransport-neutral化必要性を監査する。

---

## 10. Warning contract

success responseにwarningが存在する場合、GUIはwarningを捨てない。

特に:

- Hybrid degradation
- preflight warning
- review-required
- partial sync information

等をsuccessとは独立したwarning surfaceでoperatorに示す。

warningは必ずblockingとは限らない。blocked / warning / errorを別状態として扱う。

---

## 11. GUI-only operation history

GUIはlocal operation historyを持ってよい。

ただしこれはGUI session / convenience logでありcanonical audit authorityではない。

canonical authorityが存在する場合はそちらを優先する。

例:

- Object events
- Source selection events
- Package exchange audit
- Result receipt / validation state
- Registry proposal review / apply audit

CLIから行われたoperationがGUI local historyに存在しない可能性をUI上で誤認させない。

---

## 12. Equivalent CLI display

GUI operationに対応するCLI commandを表示可能にする。

この表示は説明・automation移行・debugging用であり、execution backendではない。

GUI workflowが複数CLI operationを含む場合はcommand sequenceとして表示する。

GUI-only local filtering等、CLI counterpartが存在しないpresentation actionでは`GUI-only`と明示する。

---

## 13. Package / Result RAW Grounding dependency

P-GUI-01のparity matrixはcurrent v1.1.0 command slotsを基準とする。

ただしPackage / Result screenの最終semanticsはP-RAWで更新する。

したがって:

```text
P-GUI-01
  -> capability slot / safety contract確定

P-RAW
  -> Package / Result grounding contract更新

P-GUI-08
  -> updated contractをGUIへ実装
```

とする。

P-RAWによってCLI command name / option / capabilityが変わる場合は、P-GUI-08開始前にmatrixをupdateする。

---

## 14. MCP placement

MCPはnormal Knowledge browsing UIではなく`System / Runtime` operational surfaceへ置く。

current MCP read-only contractは維持する。

GUIがMCP write toolを追加しない。

---

## 15. R2 Search Generation placement

R2 generation operatorはcurrent public CLIとは別のmaintenance toolであるため、normal Search UIへ混在させない。

placement:

```text
System
  -> Advanced
    -> Search Generation Maintenance
```

操作ごとの最低safety:

- status: READ
- bootstrap: DERIVED / MAINTENANCE
- build: DERIVED / MAINTENANCE
- cutover: MAINTENANCE, explicit target / reason / smoke policy
- rollback: MAINTENANCE, explicit target / reason / smoke policy
- recover: MAINTENANCE

---

## 16. GUI state vs canonical state

以下のGUI stateはcanonical SGOKB Knowledgeと分離する。

- window geometry
- dock layout
- recent Workspace
- column widths
- saved view
- theme preference
- local operation history

これらをSQLite canonical domain tableへ混入させない。

保存先・QSettings利用等はP-GUI-02で決める。

---

## 17. Long-running operation contract

GUIはSource processing、semantic operation、index rebuild、backup / restore等でmain event loopをblockしない。

ただしCancellationはUI都合で捏造しない。

operationがsafe cancellationをsupportしない場合、GUIはprogress / busy stateのみ表示しCancel actionを出さない。

worker / connection ownership / thread boundaryはP-GUI-02でDecision化する。

---

## 18. Acceptance gate

P-GUI-01 acceptanceは次で判定する。

- 67 public CLI operationsにGUI capability assignmentが存在する。
- unassigned public operation = 0。
- transport-only optionの扱いが明示される。
- Advanced generation operator placementが決定される。
- semantic parityが定義される。
- side-effect / error / warning contractが定義される。
- hidden canonical writeは禁止される。
- Relation / Proposal / Result / Restore / semantic fallback safetyを維持する。
- Package / ResultのP-RAW dependencyが明示される。

**Decision: Accepted.**

P-GUI-02 / P-GUI-03は本contractを変更せず技術architectureへ落とし込む。
