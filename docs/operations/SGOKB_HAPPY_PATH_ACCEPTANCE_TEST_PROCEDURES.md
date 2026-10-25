# SGOKB 正常系運用受入試験 操作手順

更新日: 2026-10-25

- 対象: SGOKB v1.0.0 current accepted architecture
- 試験種別: 手動 / 運用受入試験手順
- 経路: **正常系 / happy path のみ**
- 状態: **手順作成済み / 実行待ち**
- 試験計画: `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md`
- 標準ワークフロー: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Architecture: `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`

---

## 1. 目的

本書は、`SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md` に定義された各正常系受入試験項目について、operatorが実際に実行できる操作手順を示す。

本手順は、正しい入力と正常に成功する運用経路だけを対象とする。不正な入力、stale Result、blocked export、runtime障害、破損、crash recovery、破壊的復旧、performance / quality stress testingには使用しない。

各試験では最低限、次を記録する。

```text
Result: PASS / FAIL / NOT RUN
Observed IDs:
Observed output:
Notes:
```

成功することが期待される操作が0以外のexit codeを返した場合、その時点で現在の試験chainを停止する。試験条件を弱めたり、必須手順をskipしたり、継続のためにcanonical SQLite stateを手動編集してはならない。

---

## 2. 事前環境構築

A-01を開始する前に、repository rootでSGOKBを実行できるPython環境を準備する。

### 2.1 必須要件

Core正常系試験（A〜M）では次を満たすこと。

- Python 3.10以上
- repository rootから実行すること
- SGOKB packageがeditable installされていること

確認例:

```powershell
python --version
```

### 2.2 Core試験用の最小環境

未構築の場合は、repository rootで次を実行する。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

`sgokb` CLIの起動確認:

```powershell
.\.venv\Scripts\sgokb.exe --help
```

この確認が成功したらA-01へ進む。

### 2.3 仮想環境を有効化して実行する場合

本書のコマンドは原則として`sgokb`表記を使用する。PowerShellでそのまま実行する場合は、先に仮想環境を有効化する。

```powershell
.\.venv\Scripts\Activate.ps1
```

以降は次のように実行できる。

```powershell
sgokb --help
```

仮想環境を有効化しない場合は、各`sgokb`を次の形式へ読み替えてもよい。

```powershell
.\.venv\Scripts\sgokb.exe
```

### 2.4 Semantic / MCP試験まで実施する場合

N〜RおよびQのMCP試験まで連続して実施する場合は、追加依存関係を導入してよい。

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,mcp,local-embedding,vector-qdrant]'
```

追加依存関係の用途:

- `mcp`: QのMCP read boundary試験
- `local-embedding`: N/O/P/RのSemantic / Hybrid / Similarity系試験
- `vector-qdrant`: Qdrant vector backendを使用するSemantic系試験

Qdrant server本体はpip installだけでは起動しない。N以降へ進む前に、accepted local Embedding runtimeとQdrant runtimeが別途起動・構成済みであることを確認する。

Core試験A〜Mを開始する段階では、Semantic runtimeやQdrantは必須ではない。

---

## 3. 試験用workspaceと変数

repository rootからPowerShellで実行する。

最初に、試験専用directoryを作成する。

```powershell
$Db           = ".local/acceptance/sgokb-happy-path.sqlite"
$ExportRoot   = ".local/acceptance/export"
$IncomingRoot = ".local/acceptance/incoming"
$BuildRoot    = ".local/acceptance/package-build"
$StagingRoot  = ".local/acceptance/staging"
$RenderRoot   = ".local/acceptance/render"
$BackupRoot   = ".local/acceptance/backups"
$RestoreDb    = ".local/acceptance/restored/sgokb-happy-path.sqlite"

New-Item -ItemType Directory -Force `
  (Split-Path $Db), $ExportRoot, $IncomingRoot, $BuildRoot, `
  $StagingRoot, $RenderRoot, $BackupRoot, (Split-Path $RestoreDb) | Out-Null
```

WebPageCaptureの標準保存先は`extensions/web-page-capture/local-captures/`である。Section Cの実施前に、有効なWeb Capture bundleを準備し、次のplaceholderを実際のpathへ置き換える。

```powershell
$CaptureRoot = ".\extensions\web-page-capture\local-captures"
$CaptureA1   = Join-Path $CaptureRoot "<SRC-A1の実ファイル名>.webcapture.zip"
$CaptureA2   = Join-Path $CaptureRoot "<SRC-A2の実ファイル名>.webcapture.zip"
$CaptureA1V2 = Join-Path $CaptureRoot "<SRC-A1-V2の実ファイル名>.webcapture.zip"
$CaptureB1   = Join-Path $CaptureRoot "<SRC-B1の実ファイル名>.webcapture.zip"
$CaptureC1   = Join-Path $CaptureRoot "<SRC-C1の実ファイル名>.webcapture.zip"
$CaptureR1   = Join-Path $CaptureRoot "<SRC-R1の実ファイル名>.webcapture.zip"
```

今回の受入試験では次の実Objectを使用する。

```powershell
$ObjectAName = "孫悟空"
$ObjectBName = "ドラゴンボール"
$ObjectCName = "ツンデレ"
```

- OBJ-A: 孫悟空 / `character`
- OBJ-B: ドラゴンボール / `work`
- OBJ-C: ツンデレ / `concept`

SRC-R1は、孫悟空とドラゴンボールの関係を本文で明示的に支持するEvidenceを含むこと。

試験の進行に合わせて、次の変数へ値を保持する。

```text
$ObjectAId / $ObjectBId / $ObjectCId
$SourceA1Id / $SourceA2Id / $SourceB1Id / $SourceC1Id / $SourceR1Id
$SnapshotA1Id / ...
$EvidenceId
$PackageId / $BuildPath / $StagedPath / $ExportedPath
$ReceiptId
$Version1Id / $Version2Id
$ProposalRef
$RelationTypeRef
```

---

# A. 環境 / CLI

## A-01 CLI起動

**手順**

```powershell
sgokb --help
if ($LASTEXITCODE -ne 0) { throw "A-01 failed" }
```

**確認**

- Helpが表示される。
- public commandが`sgokb`である。
- Domain commandとして`source`, `object`, `association`, `evidence`, `registry`, `package`, `result`, `version`, `search`, `similar`, `render`, `mcp`, `system`が含まれる。

**PASS**: exit codeが`0`で、想定するcommand surfaceが表示される。

## A-02 隔離DB起動

必ず隔離されたacceptance DBだけを使用する。

```powershell
sgokb --db $Db system status
if ($LASTEXITCODE -ne 0) { throw "A-02 failed" }
```

**確認**: SGOKBがcurrent schema / migration stateで隔離DBをopen / initializeできる。

## A-03 System status

```powershell
$SystemStatus = sgokb --db $Db system status | ConvertFrom-Json
$SystemStatus
```

**PASS**: `ok = true`; production stateを使用せずstatus dataが返る。

## A-04 Integrity

```powershell
$Integrity = sgokb --db $Db system integrity | ConvertFrom-Json
$Integrity
if ($LASTEXITCODE -ne 0) { throw "A-04 failed" }
```

**確認**: SQLite integrity、foreign-key integrity、migration stateがvalidである。

## A-05 Class registry list

```powershell
$Classes = sgokb --db $Db registry class list | ConvertFrom-Json
$Classes.data
```

**PASS**: 登録済みClassが返り、acceptance datasetで使用する`character`, `work`, `concept`を含む。

## A-06 Class registry show

試験対象Classすべてについて実行する。

```powershell
sgokb --db $Db registry class show character
sgokb --db $Db registry class show work
sgokb --db $Db registry class show concept
```

**PASS**: 選択したClass definitionをすべて読み取れる。

## A-07 Relation type registry

```powershell
$RelationTypes = sgokb --db $Db registry relation-type list | ConvertFrom-Json
$RelationTypes.data
$RelationTypes.data.Count
```

fresh acceptance DBでは、Relation Type Registryが空でも正常である。`data = []` / `Count = 0`はCLI failureやDB破損として扱わない。

Relation Typeが1件以上存在する場合だけ、OBJ-A -> OBJ-Bに適した既存typeを選び個別definitionを確認する。

```powershell
sgokb --db $Db registry relation-type show <relation-type-ref>
```

適切な既存typeが存在する場合は、そのrefを`$RelationTypeRef`として記録する。

**PASS**:

- `registry relation-type list`が`ok = true`で正常に読める。
- fresh DBで空配列が返る場合も正常として記録できる。
- 非空の場合は選択したdefinitionを`show`で読み取れる。

Relation Typeが空の場合は、G/Iで`new_relation_type` Registry Proposalを正常系として作成・承認・適用する。SQLiteへ直接Relation Typeを追加してはならない。

## A-08 JSON contract

```powershell
$JsonProbe = sgokb --db $Db system status | ConvertFrom-Json
$JsonProbe.schema_version
$JsonProbe.ok
$JsonProbe.command
$JsonProbe.warnings
```

**PASS**: `schema_version`が`sgokb.cli/1.0`、`ok`がtrueで、responseがvalid JSONである。

## A-09 Human-readable output

```powershell
sgokb --db $Db --format text system status
```

**PASS**: human-readable textが表示され、commandが成功する。

---

# B. Object Registry

## B-01 Character / OBJ-Aを作成

```powershell
$A = sgokb --db $Db object add `
  --name $ObjectAName `
  --primary-class character | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "B-01 failed" }
$ObjectAId = $A.data.object_id
$ObjectAId
```

`$ObjectAId`を記録する。

## B-02 Work / OBJ-Bを作成

```powershell
$B = sgokb --db $Db object add `
  --name $ObjectBName `
  --primary-class work | ConvertFrom-Json
$ObjectBId = $B.data.object_id
$ObjectBId
```

## B-03 Concept / OBJ-Cを作成

```powershell
$C = sgokb --db $Db object add `
  --name $ObjectCName `
  --primary-class concept | ConvertFrom-Json
$ObjectCId = $C.data.object_id
$ObjectCId
```

**PASS B-01..B-03**: 空でなく相互に異なる3つのstable Object IDが返る。

## B-04 Object一覧

```powershell
$Objects = sgokb --db $Db object list | ConvertFrom-Json
$Objects.data
```

**確認**: OBJ-A、OBJ-B、OBJ-Cがすべて存在する。

## B-05 IDでOBJ-Aを読む

```powershell
$ById = sgokb --db $Db object show --object $ObjectAId | ConvertFrom-Json
$ById.data
```

**PASS**: 返された`object_id`が`$ObjectAId`と一致する。

## B-06 exact nameでOBJ-Aを読む

```powershell
$ByName = sgokb --db $Db object show --name $ObjectAName | ConvertFrom-Json
$ByName.data
```

**PASS**: 解決されたObject IDが`$ObjectAId`である。

## B-07 aliasを追加

```powershell
$ObjectAAlias = "Son Goku"
sgokb --db $Db object alias add --object $ObjectAId $ObjectAAlias
```

## B-08 alias一覧

```powershell
sgokb --db $Db object alias list --object $ObjectAId
```

**PASS**: `$ObjectAAlias`が存在する。

## B-09 aliasで解決

```powershell
$AliasRead = sgokb --db $Db object show --name $ObjectAAlias | ConvertFrom-Json
$AliasRead.data
```

**PASS**: aliasが`$ObjectAId`へ解決される。

## B-10 OBJ-Aをrename

後の比較用に旧nameを保持する。受入試験で実在Objectのcanonical nameを不要に崩さないため、rename試験後に元へ戻す。

```powershell
$ObjectAOriginalName = $ObjectAName
$ObjectATemporaryName = "$ObjectAName Acceptance Rename"
sgokb --db $Db object rename --object $ObjectAId --to $ObjectATemporaryName
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object rename --object $ObjectAId --to $ObjectAOriginalName
$ObjectAName = $ObjectAOriginalName
$RenameRead = sgokb --db $Db object show --object $ObjectAId | ConvertFrom-Json
$RenameRead.data
```

**PASS**: rename中も復元後もObject IDが`$ObjectAId`のままで、最終canonical nameが`孫悟空`である。

## B-11 additional classを追加

A-05から、現在のprimary classではない互換性のある既存Classを選ぶ。Characterでは`fictional_entity`が候補となる。

```powershell
sgokb --db $Db object class add --object $ObjectAId fictional_entity
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: additional classが表示され、Object IDは変わらない。

## B-12 primary classを変更して復元

一時変更用に有効な`primary_eligible` Classを選ぶ。

```powershell
sgokb --db $Db object class set-primary --object $ObjectAId person
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object class set-primary --object $ObjectAId character
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: 両方のmutationが成功し、最終primary classが`character`で、Object IDは変わらない。

## B-13 Object eventsを確認

```powershell
sgokb --db $Db object events --object $ObjectAId
```

**確認**: ここまでに作られたcreation、alias/name/class/status関連Registry eventsをevent contractに従って確認できる。

## B-14 archiveしてreactivate

```powershell
sgokb --db $Db object status --object $ObjectAId --set archived
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object status --object $ObjectAId --set active
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: 最終stateがactiveで、Object IDは`$ObjectAId`のままである。

---

# C. Source / Snapshot / Raw Artifact

各importで、返されたSource IDとSnapshot IDを解析して記録する。

## C-01 SRC-A1をImport

```powershell
$ImportA1 = sgokb --db $Db source import $CaptureA1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "C-01 failed" }
$SourceA1Id   = $ImportA1.data[0].source
$SnapshotA1Id = $ImportA1.data[0].snapshot
$SourceA1Id
$SnapshotA1Id
```

**PASS**: 両方のIDが返る。

## C-02 SRC-A1 SnapshotをProcess

```powershell
sgokb --db $Db source process --snapshot $SnapshotA1Id
if ($LASTEXITCODE -ne 0) { throw "C-02 failed" }
```

**PASS**: normalization/evidence processingが成功する。

## C-03 Source status

```powershell
sgokb --db $Db source status
```

**確認**: imported/processed source stateにSRC-A1が含まれる。

## C-04 Snapshot list

```powershell
sgokb --db $Db source snapshots
```

**確認**: `$SnapshotA1Id`が存在する。

## C-05 SRC-A2をImport/process

```powershell
$ImportA2 = sgokb --db $Db source import $CaptureA2 | ConvertFrom-Json
$SourceA2Id   = $ImportA2.data[0].source
$SnapshotA2Id = $ImportA2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA2Id
```

**PASS**: 独立したlogical sourceについて`$SourceA2Id`が`$SourceA1Id`と異なる。

## C-06 SRC-B1をImport/process

```powershell
$ImportB1 = sgokb --db $Db source import $CaptureB1 | ConvertFrom-Json
$SourceB1Id   = $ImportB1.data[0].source
$SnapshotB1Id = $ImportB1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotB1Id
```

## C-07 SRC-C1をImport/process

```powershell
$ImportC1 = sgokb --db $Db source import $CaptureC1 | ConvertFrom-Json
$SourceC1Id   = $ImportC1.data[0].source
$SnapshotC1Id = $ImportC1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotC1Id
```

## C-08 同じlogical Sourceの後続Snapshot

`$CaptureA1V2`は、SRC-A1と同じsource identity/URLを別時点に取得した有効な後続Captureでなければならない。

```powershell
$ImportA1V2 = sgokb --db $Db source import $CaptureA1V2 | ConvertFrom-Json
$SourceA1V2Id   = $ImportA1V2.data[0].source
$SnapshotA1V2Id = $ImportA1V2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA1V2Id
```

**確認**

- Source identityがcurrent ingestion identity contractに従う。
- 後続Captureについて新しいSnapshot IDが作成される。
- 以前のSnapshotがlistに残る。

## C-09 Raw Artifact保持

```powershell
sgokb --db $Db source snapshots
```

その後、command outputで公開されるSource/Snapshot detailを確認し、Capture pathが報告される場合は、保持されたRaw Artifactが試験専用storage下に存在することを確認する。

**PASS**: 過去のRaw/Snapshot履歴がprocessingや後続Captureによって置換されていない。

---

# D. Source <-> Object Association

D-06の前にSRC-R1をimport/processする。

```powershell
$ImportR1 = sgokb --db $Db source import $CaptureR1 | ConvertFrom-Json
$SourceR1Id   = $ImportR1.data[0].source
$SnapshotR1Id = $ImportR1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotR1Id
```

## D-01 OBJ-A associationを確認

```powershell
sgokb --db $Db association list --object $ObjectAId
```

## D-02 SRC-A1 -> OBJ-Aをconfirmed

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1Id --status confirmed
```

## D-03 SRC-A2 -> OBJ-Aをconfirmed

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA2Id --status confirmed
```

## D-04 SRC-B1 -> OBJ-Bをconfirmed

```powershell
sgokb --db $Db association set `
  --object $ObjectBId --source $SourceB1Id --status confirmed
```

## D-05 SRC-C1 -> OBJ-Cをconfirmed

```powershell
sgokb --db $Db association set `
  --object $ObjectCId --source $SourceC1Id --status confirmed
```

## D-06 many-to-many SRC-R1 association

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceR1Id --status confirmed
sgokb --db $Db association set `
  --object $ObjectBId --source $SourceR1Id --status confirmed
```

## D-07 associationを再読込

```powershell
sgokb --db $Db association list --object $ObjectAId
sgokb --db $Db association list --object $ObjectBId
sgokb --db $Db association list --object $ObjectCId
```

**PASS D-01..D-07**: 各Objectが意図したconfirmed Source setを持ち、SRC-R1がOBJ-AとOBJ-Bの両方で見える。

---

# E. Evidence / Provenance

## E-01 OBJ-AのEvidence candidates

```powershell
$CandidatesA = sgokb --db $Db evidence candidates --object $ObjectAId | ConvertFrom-Json
$CandidatesA.data
```

**確認**: confirmed Sourceからcandidate Evidenceが存在する。

## E-02 Evidence selection

```powershell
$SelectedA = sgokb --db $Db evidence select --object $ObjectAId | ConvertFrom-Json
$SelectedA.data
```

返されたEvidence IDを少なくとも1つ`$EvidenceId`として記録する。

## E-03 Evidence detail

```powershell
sgokb --db $Db evidence show $EvidenceId
```

**PASS**: contentとmetadataを読み取れ、期待するCaptureに対応する。

## E-04 Provenance

```powershell
sgokb --db $Db evidence provenance $EvidenceId
```

**手動確認**: Evidenceがnormalization/snapshot/source identityを通じて期待するRaw captureまで追跡できる。

## E-05 Multi-source grounding

candidates/selectionを実行してSource IDを確認する。

```powershell
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: SRC-A1とSRC-A2のEvidenceをProvenanceから区別できる。

## E-06 Evidence search

Captureの1つに存在する特徴的なphraseを選ぶ。

```powershell
$EvidenceQuery = "<distinctive phrase from a test capture>"
sgokb --db $Db evidence search $EvidenceQuery --mode lexical --object $ObjectAId
```

**PASS**: 期待するEvidenceが返る。

---

# F. Evidence Package

## F-01 PackageをBuild

```powershell
$Build = sgokb --db $Db package build `
  --object $ObjectAId `
  --build-root $BuildRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "F-01 failed" }
$PackageId = $Build.data.package_id
$BuildPath = $Build.data.path
$PackageId
$BuildPath
```

## F-02 manifestを確認

```powershell
Get-ChildItem -Recurse $BuildPath
Get-Content (Join-Path $BuildPath "manifest.json") -Raw
```

**確認**: target Object ID、package identity、base Version state（存在する場合）、selected Evidence membershipが今回のtest runと一致する。

## F-03 instructionsを確認

```powershell
Get-Content (Join-Path $BuildPath "instructions.md") -Raw
```

**PASS**: instructionsが存在し、読み取れる。

## F-04 packaged Evidenceを確認

```powershell
Get-ChildItem -Recurse $BuildPath
```

代表的なEvidence payload fileを開き、ID/contentをE-02/E-04と比較する。

**PASS**: packaged Evidenceが選択されたgrounded Evidenceであり、無関係なmaterialではない。

## F-05 PackageをStage

```powershell
$Stage = sgokb --db $Db package stage `
  $BuildPath --staging-root $StagingRoot | ConvertFrom-Json
$StagedPath = $Stage.data.path
$StagedPath
```

## F-06 Preflight

```powershell
$Preflight = sgokb --db $Db package preflight `
  $StagedPath --destination $ExportRoot | ConvertFrom-Json
$Preflight.data
```

**PASS**: このhappy-path datasetで期待する通常のexportable dispositionが返る。選択datasetが正当に`review_required`となる場合は、その条件を記録し、人間がreviewした後にだけ標準のexplicit acknowledgement pathを使う。真のblocked conditionをPASSとして扱ってはならない。

## F-07 Explicit export

通常のexportable path:

```powershell
$Export = sgokb --db $Db package export `
  $StagedPath --destination $ExportRoot | ConvertFrom-Json
$ExportedPath = $Export.data.path
$ExportedPath
```

F-06で正当にhuman acknowledgementが必要でoperatorが承認した場合は`--acknowledge-review`を使用する。

## F-08 Export integrity

```powershell
Get-ChildItem -Recurse $ExportedPath
```

**PASS**: staged Packageから期待されるmanifest、instructions、Evidence payloadが存在し、読み取れる。

---

# G. External ChatGPT / Structured Object Result

## G-01 PackageをChatGPTへ渡す

1. このacceptance object専用の新しいChatGPT conversationを開く。
2. `$ExportedPath`のexported Packageを渡す。
3. この試験では無関係なWeb factやsupplementary evidenceを追加しない。

**PASS**: ChatGPTがPackage内容を読み取れる。

## G-02 instruction authorityを確立

Package内の`instructions.md`がauthoritative analysis instructionであり、返却artifactはcurrent SGOKB Structured Object Result contractに従う必要があることをChatGPTへ伝える。

**PASS**: generated resultがfree-form proseだけではなくPackage instruction/schema requirementに従う。

## G-03 groundingを確認

Importする前にresultを手動確認し、代表的claimをPackage Evidence IDと比較する。

**PASS**: accepted Knowledge向けclaimがPackage内に実際に存在するEvidenceでgroundされ、fabricated Evidence IDを使用していない。

## G-04 `result.json`を生成

ChatGPTにfinal Structured Object Resultを生成させ、exact filenameで保存する。

```text
result.json
```

**PASS**: artifactがsyntactically JSONでcurrent Result schemaに従う。

## G-05 Facetsを確認

`result.json`を開き、OBJ-A用に生成されたFacetsを確認する。

**PASS**: Facetsが選択Object/classとgrounded materialに適している。

## G-06 Statementsを確認

generated Facets配下の代表的Statementsを確認する。

**PASS**: Statementsがstructuredで意味があり、有効なpackaged Evidenceを参照する。

## G-07 Relation Type Registryが空の場合のproposalを確認

A-07でOBJ-A -> OBJ-Bに適した既存Relation Typeが存在しなかった場合、初回Resultでは存在しない`relation_type_id`を使用したRelationを生成してはならない。

代わりに、SRC-R1 Evidenceに基づき、孫悟空とドラゴンボールの関係を表現できる`new_relation_type` Registry Proposalを含める。

確認事項:

- `proposal_kind`が`new_relation_type`である。
- rationale/payloadが意図するRelation semanticsを明確に表す。
- proposal自身がPackage内の有効なEvidenceを参照する。
- V1の`knowledge.relations`には、まだ未適用のRelation Typeを使ったRelationを入れない。

**PASS**: unknown Relation Typeを捏造せず、Proposal境界を使って新規typeを提案している。

A-07ですでに適切なRelation Typeが存在した場合は、その既存typeを使用してRelationを生成してよい。その場合Iでは別のbenign proposalを使用できる。

## G-08 Resultをincoming dropへ配置

```powershell
$DropDir = Join-Path $IncomingRoot "drop\$PackageId"
New-Item -ItemType Directory -Force $DropDir | Out-Null
Copy-Item "C:\path\to\generated\result.json" (Join-Path $DropDir "result.json") -Force
$ResultPath = Join-Path $DropDir "result.json"
Test-Path $ResultPath
```

**PASS**: `Test-Path`がtrueを返し、filenameがexactly `result.json`である。

---

# H. Result Intake / Validation / Import

## H-01 ResultをDetect

```powershell
sgokb --db $Db result detect --incoming-root $IncomingRoot
```

**PASS**: `result.json`を含むPackage dropが検出される。

## H-02 ResultをReceive

```powershell
$Receipt = sgokb --db $Db result receive `
  $ResultPath `
  --package-id $PackageId `
  --incoming-root $IncomingRoot | ConvertFrom-Json
$ReceiptId = $Receipt.data.receipt_id
$ReceiptId
```

`$ReceiptId`を記録する。

## H-03 Result一覧

```powershell
sgokb --db $Db result list --package-id $PackageId
```

**PASS**: `$ReceiptId`が見える。

## H-04 Pending Results

```powershell
sgokb --db $Db result pending
```

**PASS**: received Resultが期待するpre-import stateで見える。

## H-05 Validate

```powershell
sgokb --db $Db result validate $ReceiptId --incoming-root $IncomingRoot
if ($LASTEXITCODE -ne 0) { throw "H-05 failed" }
```

**PASS**: normal happy-path artifactでResultがvalid stateへ到達する。

## H-06 Human review

```powershell
sgokb --db $Db result review `
  $ReceiptId --incoming-root $IncomingRoot --review-format markdown
```

続行前にObject identity、base Version、Facets、Statements、Relations、Evidence IDs、Registry proposalsをreviewする。

Relation Type Registryが空だった場合は、初回Resultに未適用typeを使用したRelationがなく、`new_relation_type` proposalとして分離されていることも確認する。

**PASS**: proposed Knowledgeが理解可能で意図したresultと一致する。

## H-07 Explicit Import

```powershell
$Imported = sgokb --db $Db result import `
  $ReceiptId --incoming-root $IncomingRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "H-07 failed" }
$Imported.data
```

accepted normal flowで正当にreview acknowledgementが必要な場合は、先にhuman reviewを行い、`--acknowledge-review`を明示使用する。

import responseまたはH-08 readから新規作成されたKnowledge Version IDを`$Version1Id`として記録する。

## H-08 current pointerを確認

```powershell
$CurrentA = sgokb --db $Db object show --object $ObjectAId --knowledge | ConvertFrom-Json
$CurrentA.data
```

**PASS**: current accepted Knowledgeがimported Resultに対応し、`$Version1Id`がcurrentである。

## H-09 Evidence linkを確認

Knowledge readを使用する。

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
sgokb --db $Db object relations --object $ObjectAId
```

代表的Statement Evidence IDについて:

```powershell
sgokb --db $Db evidence show <evidence-id>
sgokb --db $Db evidence provenance <evidence-id>
```

**PASS**: V1のaccepted Knowledge linkが既存の正しいEvidenceへ解決される。A-07が空だった場合、V1にまだRelationが存在しないこと自体は正常である。

---

# I. Registry Proposal

A-07でRelation Type Registryが空だった場合、本SectionではG-07で生成した`new_relation_type` proposalを必ず使用する。

## I-01 proposal intakeを確認

proposalを含むResultをimportした後:

```powershell
sgokb --db $Db registry proposal list --decision pending
```

`new_relation_type` proposal referenceを`$ProposalRef`として記録する。

**PASS**: proposalがpendingで、silent applyされていない。

## I-02 pending proposal一覧

```powershell
sgokb --db $Db registry proposal list --decision pending
```

**PASS**: `$ProposalRef`が存在する。

## I-03 proposalを確認

```powershell
sgokb --db $Db registry proposal show $ProposalRef
```

**確認**:

- `proposal_kind = new_relation_type`
- payload/rationaleが孫悟空 -> ドラゴンボールの関係を表現できる意味を持つ
- Evidence groundingがSRC-R1由来の有効Evidenceに解決される
- まだRelation Type Registryへ適用されていない

## I-04 proposalをAccept

```powershell
sgokb --db $Db registry proposal accept `
  $ProposalRef --note "happy-path acceptance reviewed"
```

**PASS**: decisionがacceptedになるが、acceptanceだけを理由にRelation Type Registry mutationはまだ発生していない。

確認として、必要なら再度listを読む。

```powershell
sgokb --db $Db registry relation-type list
```

## I-05 proposalをApply

```powershell
sgokb --db $Db registry proposal apply $ProposalRef
```

**PASS**: applyが成功する。

## I-06 Relation Type Registryを確認

```powershell
$RelationTypesAfterApply = sgokb --db $Db registry relation-type list | ConvertFrom-Json
$RelationTypesAfterApply.data
```

新しく適用されたRelation Typeを特定し、そのrefを`$RelationTypeRef`として記録して個別に読む。

```powershell
$RelationTypeRef = "<applied relation-type ref>"
sgokb --db $Db registry relation-type show $RelationTypeRef
```

**PASS**:

- A-07で空だったRegistryに、explicit apply後だけ新規Relation Typeが存在する。
- `show`でdefinitionを読み取れる。
- V1自体は書き換えられていない。

Critical invariant:

```text
Result Import
  -> pending new_relation_type proposal
  -> explicit human accept
  -> explicit apply
  -> Relation Type becomes usable
  -> later Result creates a new immutable Knowledge Version containing the Relation
```

---

# J. Knowledge Versioning

## J-01 Version 1 identityを記録

H-07/H-08から設定・記録する。

```powershell
$Version1Id = "<accepted V1 knowledge_version_id>"
sgokb --db $Db version show $Version1Id
```

**PASS**: V1を読み取れる。

## J-02 後続Evidenceを追加

C-08の後続SRC-A1 Snapshotを使用し、まだassociationされていなければOBJ-Aへconfirmedであることを確認する。

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1V2Id --status confirmed
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: 2回目のanalysis cycle向けにnew Evidenceが利用可能である。

## J-03 update PackageをBuild

I-05/I-06でRelation Typeを適用した後に実行する。

```powershell
$Build2 = sgokb --db $Db package build `
  --object $ObjectAId --build-root $BuildRoot | ConvertFrom-Json
$PackageId2 = $Build2.data.package_id
$BuildPath2 = $Build2.data.path
```

`manifest.json`を確認し、current contractが要求する通りPackageがOBJ-Aとcurrent/base V1へbindされていることを確認する。

## J-04 Result 2を生成

newly available Evidenceと、I-06で確認した`$RelationTypeRef`を使用してF-05〜G-08相当を`$PackageId2`について繰り返し、有効なupdated `result.json`を生成する。

このResult 2では、SRC-R1 Evidenceによって支持されるOBJ-A（孫悟空） -> OBJ-B（ドラゴンボール）のRelationを、すでに適用済みのRelation Typeで表現する。

確認事項:

- `relation_type_id`がI-06で実在確認したRelation Typeを参照する。
- `subject_object_id = $ObjectAId`。
- `object_object_id = $ObjectBId`。
- relation EvidenceがSRC-R1由来の有効Evidence IDを参照する。
- 未適用・架空のRelation Type IDを使用しない。

2つ目のResult pathを`$ResultPath2`として記録する。

## J-05 Result 2をValidate/review/import

```powershell
$Receipt2 = sgokb --db $Db result receive `
  $ResultPath2 --package-id $PackageId2 --incoming-root $IncomingRoot | ConvertFrom-Json
$ReceiptId2 = $Receipt2.data.receipt_id

sgokb --db $Db result validate $ReceiptId2 --incoming-root $IncomingRoot
sgokb --db $Db result review $ReceiptId2 --incoming-root $IncomingRoot --review-format markdown
$Imported2 = sgokb --db $Db result import $ReceiptId2 --incoming-root $IncomingRoot | ConvertFrom-Json
```

import/current readから`$Version2Id`を記録する。

## J-06 V2がcurrentであることを確認

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: V2がcurrentである。

## J-07 V1が保持されていることを確認

```powershell
sgokb --db $Db version show $Version1Id
```

**PASS**: V1が依然存在し、読み取れる。

## J-08 両Versionを直接読む

```powershell
sgokb --db $Db version show $Version1Id
sgokb --db $Db version show $Version2Id
```

## J-09 V1 -> V2のDiff

```powershell
sgokb --db $Db version diff $Version1Id $Version2Id --diff-format markdown
```

**PASS**: 期待するaddition/changeが表現され、Relation Type適用後にV2で新規Relationが追加されたことを確認でき、無関係なdestructive rewriteが観測されない。

## J-10 Historical Object read

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge --version $Version1Id
```

**PASS**: V2ではなくhistorical V1 stateが返る。

## J-11 Version-specific grounding

代表的なV1/V2 StatementsとV2 Relationについて、Evidence IDを`evidence show`と`evidence provenance`で解決する。

**PASS**: 両immutable Versionがそれぞれ正しいgroundingを保持する。

---

# K. Relation

KではIでRelation Typeが適用され、Jでそのtypeを使用したRelationを含むV2がimport済みであることを前提とする。

## K-01 imported Relationを確認

```powershell
sgokb --db $Db object relations --object $ObjectAId
```

**PASS**: V2でResult-importされたOBJ-A -> OBJ-B Relationがcurrent accepted Knowledgeに存在する。

## K-02 OBJ-Aから読む

```powershell
$RelationsA = sgokb --db $Db object relations --object $ObjectAId | ConvertFrom-Json
$RelationsA.data
```

**PASS**:

- subjectが`$ObjectAId`。
- targetが`$ObjectBId`。
- Relation Typeが`$RelationTypeRef`と一致する。

## K-03 OBJ-Bからrelated stateを読む

```powershell
sgokb --db $Db object relations --object $ObjectBId
```

**PASS**: relation visibility/directionが選択したRelation Type contractに一致する。Relation Typeがinverse relationを定義しない場合はinverseを要求しない。

## K-04 Relation Evidenceを確認

Evidence有効（default）のrelation outputからcited Evidence IDを1つ選び、次を実行する。

```powershell
sgokb --db $Db evidence show <relation-evidence-id>
sgokb --db $Db evidence provenance <relation-evidence-id>
```

**PASS**: Evidenceが孫悟空とドラゴンボールのRelationを明示的に支持し、SRC-R1 lineageへ追跡できる。

## K-05 Version-specific Relation read

```powershell
sgokb --db $Db object relations --object $ObjectAId --version $Version1Id
sgokb --db $Db object relations --object $ObjectAId --version $Version2Id
```

**PASS**:

- V1はRelation Type適用前のhistorical stateを保持するため、当該Relationが存在しなくても正常。
- V2には当該Relationが存在する。
- current/historical scopeが混在しない。

---

# L. Render

## L-01 current OBJ-AをRender

```powershell
$RenderCurrent = sgokb --db $Db render `
  --object $ObjectAId --output-root $RenderRoot | ConvertFrom-Json
$RenderCurrent.data
```

generated Markdown fileを開く。

**PASS**: current accepted Knowledgeがhuman-readableである。

## L-02 特定VersionをRender

```powershell
sgokb --db $Db render --version $Version1Id --output-root $RenderRoot
```

**PASS**: historical Versionを独立してrenderできる。

## L-03 Facetsを確認

current renderを開き、次とFacetsを比較する。

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: rendered Facetsが同じaccepted Knowledgeを表す。

## L-04 Relationsを確認

rendered relation contentを次と比較する。

```powershell
sgokb --db $Db object relations --object $ObjectAId
```

**PASS**: V2 relationship informationがconsistentである。

## L-05 grounding/provenance referenceを確認

read/render surfaceに表示される代表的Evidence identifierについて:

```powershell
sgokb --db $Db evidence provenance <evidence-id>
```

**PASS**: rendered/read Knowledgeがtraceableである。

## L-06 V1/V2 renderを比較

両Versionをrenderし、手動またはPowerShellで比較する。

```powershell
# renderが返した実際のoutput pathへ置き換える。
Compare-Object `
  (Get-Content "<V1-render-path>") `
  (Get-Content "<V2-render-path>")
```

**PASS**: 期待するVersion差分が反映され、V2側だけに新規Relationが現れる場合はその差も確認できる。

---

# M. Lexical Search

## M-01 canonical nameをSearch

```powershell
sgokb --db $Db search $ObjectAName --mode lexical
```

**PASS**: OBJ-Aが返る。

## M-02 aliasをSearch

```powershell
sgokb --db $Db search $ObjectAAlias --mode lexical
```

**PASS**: current lexical identity/search contractに従ってOBJ-Aを発見できる。

## M-03 distinctive Knowledge termをSearch

accepted V2 Knowledgeに存在するtermを選ぶ。

```powershell
$KnowledgeTerm = "<distinctive accepted-knowledge term>"
sgokb --db $Db search $KnowledgeTerm --mode lexical
```

**PASS**: 期待するObjectが返る。

## M-04 Multi-object query

少なくとも2つのtest Objectで共有されるtermを選ぶ。

```powershell
sgokb --db $Db search "<shared term>" --mode lexical --limit 10
```

**PASS**: duplicate Object identity rowを別Objectとして解釈せず、複数のrelevant Objectを返せる。

## M-05 Current scope

V1とV2で変化したtermを使用して比較する。

```powershell
sgokb --db $Db search "<current-specific term>" --mode lexical
sgokb --db $Db search "<historical-specific term>" --mode lexical --version $Version1Id
```

**PASS**: normal searchはcurrent accepted scopeを使用し、explicit Version filterでhistorical scopeを指定できる。

## M-06 Cross-class lexical retrieval

OBJ-A/B/CについてClassに関連するqueryを実行し、必要ならClass filterを使用する。

```powershell
sgokb --db $Db search "<character term>" --mode lexical --primary-class character
sgokb --db $Db search "<work term>" --mode lexical --primary-class work
sgokb --db $Db search "<concept term>" --mode lexical --primary-class concept
```

**PASS**: 各Classを正しくretrievalできる。

---

# N. Semantic Search

Nの前に、accepted local Embedding runtimeとQdrant runtimeが起動・構成済みであることを確認する。この手順ではfrozen local semantic compositionを使用し、cloud fallbackを有効化しない。

## N-01 Semantic runtimeを開始/確認

```powershell
sgokb --db $Db system index status
```

その後、simple full-runtime semantic queryを実行する。

```powershell
sgokb --db $Db search "<semantic query for OBJ-A>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: runtime-unavailable exitなしでcommandが成功する。

## N-02 Index status

```powershell
sgokb --db $Db system index status
```

**PASS**: current index/Embedding Space stateがこのtest compositionでusableと報告される。

## N-03 IndexをRebuild

```powershell
sgokb --db $Db system index rebuild
if ($LASTEXITCODE -ne 0) { throw "N-03 failed" }
```

current environmentでindex rebuild前後にsemantic derived synchronizationが必要な場合は次を実行する。

```powershell
sgokb --db $Db system derived sync --semantic-runtime
```

**PASS**: canonical Versionを変更せず、canonical Knowledgeからderived semantic stateをrebuildできる。

## N-04 Semantic paraphrase query

exact source/Knowledge wordingをコピーせず、OBJ-Aを説明するqueryを使う。

```powershell
sgokb --db $Db search `
  "<paraphrased semantic description of OBJ-A>" `
  --mode semantic --semantic-runtime --require-full-runtime --limit 10
```

**PASS**: small acceptance datasetでOBJ-Aがreasonable rankでretrievedされる。

## N-05 Overview-level semantic retrieval

1つのexact StatementではなくObject overviewに対応するbroad queryを使う。

```powershell
sgokb --db $Db search "<broad OBJ-A description>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: current R2 representation family経由でOBJ-Aをretrievalできる。

## N-06 Facet semantic retrieval

OBJ-Aの実際のFacetを選び、その意味をqueryする。

```powershell
sgokb --db $Db search "<facet semantic query>" `
  --mode semantic --semantic-runtime --require-full-runtime `
  --facet <facet-ref>
```

**PASS**: intended Facet contextでOBJ-Aが返る。

## N-07 Statement semantic retrieval

特徴的なStatement 1つのparaphraseを使う。

```powershell
sgokb --db $Db search "<statement paraphrase>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: wordingが異なってもOBJ-Aが返る。

## N-08 Current Version scope

V2固有のsemantic conceptを使用し、適切な場合はV1をexplicit queryする。

```powershell
sgokb --db $Db search "<V2-specific semantic concept>" `
  --mode semantic --semantic-runtime --require-full-runtime

sgokb --db $Db search "<V1-specific semantic concept>" `
  --mode semantic --semantic-runtime --require-full-runtime `
  --version $Version1Id
```

**PASS**: current scopeとhistorical scopeが区別されたままである。

## N-09 Cross-class semantic retrieval

OBJ-A、OBJ-B、OBJ-Cをそれぞれ識別すべき意味のあるsemantic queryを実行する。

**PASS**: semantic retrievalが1つのtest classだけに限定されない。

---

# O. Hybrid Search

このacceptance sectionで両channelが実際に利用可能であることを証明するため、`--mode hybrid --semantic-runtime --require-full-runtime`を使用する。

## O-01 Name + meaning query

```powershell
sgokb --db $Db search `
  "$ObjectAName <semantic description>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: OBJ-Aが返り、semantic channel欠如を示すdegradation warningがない。

## O-02 Exact identity prominence

```powershell
sgokb --db $Db search $ObjectAName `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: exact identityが容易に見つかり、semantically similar Objectの中に埋没しない。

## O-03 Lexically distinctive Knowledge query

```powershell
sgokb --db $Db search "<distinctive literal knowledge phrase>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: relevant Objectがretrievedされる。

## O-04 Semantically descriptive query

```powershell
sgokb --db $Db search "<paraphrased meaning>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: semantic contributionによってintended Objectをretrievalできる。

## O-05 Object aggregation

OBJ-Aの複数Facets/Statementsにmatchするqueryを実行する。

```powershell
$Hybrid = sgokb --db $Db search "<multi-aspect OBJ-A query>" `
  --mode hybrid --semantic-runtime --require-full-runtime --limit 10 | ConvertFrom-Json
$Hybrid.data
```

**PASS**: OBJ-Aがseparate overview/facet/statement result rowとして繰り返されず、1つのObject resultとして表現される。

---

# P. Similarity

Similarityにはconfigured semantic runtime/index stateが必要である。

## P-01 Object similarity

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

**PASS**: similar Objectが返り、source Object identityがsimilarity contractに従って扱われる。

## P-02 Facet-specific similarity

OBJ-Aに実在するFacetを選ぶ。

```powershell
sgokb --db $Db similar `
  --object $ObjectAId --facet <facet-ref> --limit 10
```

**PASS**: facet-specific comparisonが成功し、requested Facetを使用する。

## P-03 rankingのHuman sanity check

上位resultをOBJ-B/OBJ-Cの既知contentとselected small datasetに照らして比較する。

**PASS**: orderingがoperational useとしてsemantically plausibleである。これはsanity checkでありPhase N formal ANN-quality benchmarkではない。

## P-04 Current Version similarity

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

その後、supportedな場合はhistorical Versionをexplicit compareする。

```powershell
sgokb --db $Db similar --object $ObjectAId --version $Version1Id --limit 10
```

**PASS**: default/current scopeとexplicit historical scopeを区別できる。

## P-05 Cross-class similarity

```powershell
sgokb --db $Db similar `
  --object $ObjectAId --cross-class --limit 10
```

**PASS**: current similarity semanticsに従いcross-class candidateを返せる。

---

# Q. MCP Read Boundary

MCP clientはproduction DBではなくacceptance DBをlaunchするよう構成する。

Core/lexical server command:

```text
sgokb --db <ABSOLUTE_ACCEPTANCE_DB_PATH> mcp serve
```

Semantic MCP test:

```text
sgokb --db <ABSOLUTE_ACCEPTANCE_DB_PATH> mcp serve --semantic-runtime
```

Q-01..Q-12はconnected MCP client UI/tool inspectorを使用する。

## Q-01 `get_object`

Call:

```text
get_object({"object_id":"<OBJ-A-ID>"})
```

**PASS**: Object IDとcurrent accepted VersionがCLI `object show --knowledge`と一致する。

## Q-02 `get_objects`

exposed schemaに従ってOBJ-A/B/C IDを指定してCallする。

**PASS**: requested Objectがすべて正しいstable identityで返る。

## Q-03 `search_objects`

まずlexical queryをCallする。

```text
search_objects({"query":"<known term>","mode":"lexical","limit":10})
```

次にsemantic-enabled serverでhybrid queryをCallする。

**PASS**: 期待するObjectがCLI retrieval semanticsと一致する。

## Q-04 `find_similar_objects`

```text
find_similar_objects({"object_id":"<OBJ-A-ID>","limit":10})
```

**PASS**: MCP経由のsimilarity readが成功する。

## Q-05 `get_object_relations`

```text
get_object_relations({"object_id":"<OBJ-A-ID>"})
```

**PASS**: V2でacceptedされたOBJ-A -> OBJ-B RelationがCLIと同じcurrent Version semanticsで返る。

## Q-06 `get_object_evidence`

```text
get_object_evidence({"object_id":"<OBJ-A-ID>"})
```

**PASS**: OBJ-Aのgrounded Evidenceが返る。

## Q-07 `search_evidence`

Tool schemaに従いE-06のdistinctive queryでCallする。

**PASS**: 期待するEvidenceが見つかる。

## Q-08 `build_context`

```text
build_context({
  "object_ids":["<OBJ-A-ID>","<OBJ-B-ID>"],
  "purpose":"comparison",
  "max_characters":12000
})
```

**PASS**: deterministic Knowledge subsetが返り、Context Builderが新しいLLM-authored factを挿入しない。

## Q-09 CLI/MCP consistency

Q-01を次と比較する。

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: 両方が同じcurrent accepted Knowledge Versionへ解決される。

## Q-10 Comparison context

OBJ-AとOBJ-Bを`purpose = comparison`で使用する。

**PASS**: returned subsetに両Objectのrelevant stored Knowledgeが含まれる。

## Q-11 Character budget

`build_context`を`max_characters = 6000`など意図的に控えめだが有効なbudgetでCallする。

**PASS**: returned contextがrequested budget contract内に収まる。

## Q-12 Determinism

DB stateを変更せず、identical inputでQ-08を繰り返す。

**PASS**: deterministic Context Builder contractに従ってselected content/orderが同一である。

---

# R. Derived Index

## R-01 Index status

```powershell
sgokb --db $Db system index status
sgokb --db $Db system derived status --semantic-runtime
```

current derived stateを記録する。

## R-02 derived/index stateをRebuild

```powershell
sgokb --db $Db system derived sync --semantic-runtime
sgokb --db $Db system index rebuild
```

**PASS**: canonical accepted Knowledgeを使ってrebuild/syncが成功する。

## R-03 rebuild後のLexical read

M-01/M-03を繰り返す。

**PASS**: derived maintenance後もcanonical/lexical readが正しい。

## R-04 rebuild後のSemantic read

N-04を繰り返す。

**PASS**: 期待するObjectが返る。

## R-05 rebuild後のSimilarity

P-01/P-02を繰り返す。

**PASS**: similarityが引き続き機能する。

## R-06 Representation/Embedding reuse sanity check

canonical Knowledgeを変更せずderived syncを2回目実行する。

```powershell
$Before = sgokb --db $Db system derived status --semantic-runtime | ConvertFrom-Json
sgokb --db $Db system derived sync --semantic-runtime
$After = sgokb --db $Db system derived status --semantic-runtime | ConvertFrom-Json
$Before.data
$After.data
```

**PASS**: unchanged canonical Knowledgeからsemantically duplicated current stateが生成されず、status surfaceが報告するID/countがreuse/idempotent maintenance semanticsと整合する。これはoperational sanity checkであり、internal N-02 deterministic fixture assertionではない。

---

# S. Backup / Restore Happy Path

acceptance DBとtest-owned backup/restore pathだけを使用する。

## S-01 Backup status

```powershell
sgokb --db $Db system backup status --root $BackupRoot
```

**PASS**: backup subsystem statusを読み取れる。

## S-02 Backupを作成

```powershell
$Backup = sgokb --db $Db system backup create --root $BackupRoot | ConvertFrom-Json
$Backup.data
```

返されたbackup pathを`$BackupPath`として記録する。

## S-03 Backup integrityを確認

backup commandがintegrity/verification metadataを返す場合は確認する。また、次を実行する。

```powershell
Test-Path $BackupPath
```

**PASS**: backupが存在し、通常のintegrity verificationを伴ってcreationが成功している。

## S-04 Restore plan

command output/contractに従い、隔離restore targetへのrestoreをplanする。

```powershell
sgokb --db $RestoreDb system restore plan $BackupPath
```

**PASS**: planが意図したtest-owned backupとrestore targetを示す。production stateへ解決される場合は続行しない。

## S-05 RestoreをApply

fresh restore targetについてnormal restore apply pathを実行する。

```powershell
sgokb --db $RestoreDb system restore apply $BackupPath
```

current CLIがtarget fileの既存時にexplicit overwrite acknowledgementを要求する場合は、test-owned targetを適切に削除/再作成するか、targetがdisposable acceptance restore DBであることを確認した後にだけ`--acknowledge-overwrite`を使用する。

**PASS**: restoreが正常完了する。

## S-06 Restored integrity

```powershell
sgokb --db $RestoreDb system integrity
```

**PASS**: integrityが成功する。

## S-07 Restored Objects

```powershell
sgokb --db $RestoreDb object show --object $ObjectAId --knowledge
sgokb --db $RestoreDb object show --object $ObjectBId --knowledge
sgokb --db $RestoreDb object show --object $ObjectCId --knowledge
```

**PASS**: Object stable identityが保持される。

## S-08 Restored Versions

```powershell
sgokb --db $RestoreDb version show $Version1Id
sgokb --db $RestoreDb version show $Version2Id
```

**PASS**: accepted Version historyが保持される。

## S-09 Restored Evidence / Provenance

```powershell
sgokb --db $RestoreDb evidence show $EvidenceId
sgokb --db $RestoreDb evidence provenance $EvidenceId
```

**PASS**: grounded provenanceを解決できる。

## S-10 restore後にderived stateをRebuild

restored test environmentをtest-owned semantic/vector targetへ構成し、次を実行する。

```powershell
sgokb --db $RestoreDb system derived sync --semantic-runtime
sgokb --db $RestoreDb system index rebuild
```

**PASS**: restored canonical stateからderived stateを再生成できる。

## S-11 restored KnowledgeをSearch

```powershell
sgokb --db $RestoreDb search $ObjectAName --mode lexical
sgokb --db $RestoreDb search "<semantic OBJ-A query>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: restore後にlocal lexicalとconfigured semantic read pathの両方が機能する。

## S-12 restored KnowledgeをRender

```powershell
sgokb --db $RestoreDb render --object $ObjectAId --output-root "$RenderRoot/restored"
```

**PASS**: current restored Knowledgeが正常にrenderされる。

---

# T. Final uninterrupted end-to-end run

A-Sを個別に理解した後、SQLiteを手動編集したりboundaryをbypassしたりせず、fresh Objectをnormal workflow全体へ通す。

## T-01 Full normal operational chain

新しい有効なtest Objectと1つ以上の新しい有効なcapture bundleを使用する。

次の順序で実行する。

```text
1.  system integrity
2.  object add
3.  source import
4.  source process
5.  association set --status confirmed
6.  evidence candidates
7.  evidence select
8.  package build
9.  package stage
10. package preflight
11. package export
12. external ChatGPT analysis under instructions.md
13. save exact result.json
14. result detect
15. result receive
16. result validate
17. result review
18. result import
19. registry proposal review/accept/apply when the Result legitimately contains one
20. object show --knowledge
21. object relations when a valid applied Relation Type and supported Relation exist
22. render
23. lexical search
24. semantic search with full runtime
25. hybrid search with full runtime
26. similar
27. MCP get_object
28. MCP search_objects
29. MCP build_context
30. system backup create
31. final system integrity
```

各stepで返されたstable IDを記録し、identity chainが内部でconsistentなままであることを確認する。

**T-01 PASSには次のすべてが必要**:

- 必須stepをskipしていない。
- 成功が期待されるすべてのcommandが正常exitする。
- external exportがexplicitである。
- external AIがfabricated provenanceではなくPackage Evidenceを使用する。
- Resultがexplicit Import前にvalidateおよびreviewされる。
- Registry Proposalがsilent applyされず、必要な場合はexplicit accept/applyを経る。
- accepted Knowledgeがhistorical accepted stateのoverwriteではなくVersionである。
- 代表的KnowledgeがEvidenceおよびRaw Source lineageまでtraceableである。
- lexical、semantic、hybrid、similarity、render、MCP read surfaceが同じcanonical Object/Version semanticsへ解決される。
- Relationを使用する場合、実在・適用済みのRelation Typeだけを参照する。
- completed workflow後にbackup creationが成功する。
- 最終`system integrity`が成功する。

---

# 4. 完了判定

## Core PASS

local canonical/read workflowを通る適用可能な試験がすべてPASSした場合のみ**Core PASS**とする。最低限、次を含む。

```text
A Environment / CLI
B Object Registry
C Source / Snapshot / Raw
D Association
E Evidence / Provenance
F Evidence Package
G External semantic integration
H Result intake / validation / review / import
I Registry Proposal
J Versioning
K Relation
L Render
M Lexical Search
T end-to-end core chain
```

## Full SGOKB PASS

Core PASSに加え、optional-runtime/full-system acceptance sectionがすべて完了した場合のみ**Full SGOKB PASS**とする。

```text
N Semantic Search
O Hybrid Search
P Similarity
Q MCP read boundary
R Derived Index
S Backup / Restore
T full uninterrupted run including semantic/MCP/backup steps
```

final acceptance recordには、exact DB path、test date、repository commit/release identity、使用したsemantic runtime identity、Object/Version ID、overall verdictを含める。