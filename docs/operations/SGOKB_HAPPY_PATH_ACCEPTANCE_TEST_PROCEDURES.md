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

## 2. 試験用workspaceと変数

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

Section Cの実施前に、有効なWeb Capture bundleを準備する。次のplaceholderを実際のpathへ置き換える。

```powershell
$CaptureA1   = "C:\path\to\SRC-A1.webcapture.zip"
$CaptureA2   = "C:\path\to\SRC-A2.webcapture.zip"
$CaptureA1V2 = "C:\path\to\SRC-A1-V2.webcapture.zip"
$CaptureB1   = "C:\path\to\SRC-B1.webcapture.zip"
$CaptureC1   = "C:\path\to\SRC-C1.webcapture.zip"
$CaptureR1   = "C:\path\to\SRC-R1.webcapture.zip"
```

識別しやすい試験用Object名を使用する。実際のSourceを使う場合は、実在するObject名を使用してもよい。

```powershell
$ObjectAName = "Acceptance Character A"
$ObjectBName = "Acceptance Work B"
$ObjectCName = "Acceptance Concept C"
```

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

**PASS**: `ok = true`であり、production stateを使用せずstatus dataが返る。

## A-04 Integrity

```powershell
$Integrity = sgokb --db $Db system integrity | ConvertFrom-Json
$Integrity
if ($LASTEXITCODE -ne 0) { throw "A-04 failed" }
```

**確認**: SQLite integrity、foreign-key integrity、migration stateが正常である。

## A-05 Class Registry一覧

```powershell
$Classes = sgokb --db $Db registry class list | ConvertFrom-Json
$Classes.data
```

**PASS**: 登録済みClassが返り、acceptance datasetで使用するClassが含まれる。

## A-06 Class Registry詳細

すべての試験対象Classについて実行する。

```powershell
sgokb --db $Db registry class show character
sgokb --db $Db registry class show work
sgokb --db $Db registry class show concept
```

**PASS**: 選択したすべてのClass定義を読み取れる。

## A-07 Relation type Registry

```powershell
$RelationTypes = sgokb --db $Db registry relation-type list | ConvertFrom-Json
$RelationTypes.data
```

OBJ-A <-> OBJ-Bに適切な既存Relation typeを1件選択し、内容を確認する。

```powershell
sgokb --db $Db registry relation-type show <relation-type-ref>
```

**PASS**: Relation type一覧と選択した定義を読み取れる。

## A-08 JSON contract

```powershell
$JsonProbe = sgokb --db $Db system status | ConvertFrom-Json
$JsonProbe.schema_version
$JsonProbe.ok
$JsonProbe.command
$JsonProbe.warnings
```

**PASS**: `schema_version`が`sgokb.cli/1.0`、`ok`がtrueであり、responseが有効なJSONである。

## A-09 Human-readable output

```powershell
sgokb --db $Db --format text system status
```

**PASS**: 人間可読なtextが表示され、commandが成功する。

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

**PASS B-01..B-03**: 空でなく、相互に異なる3つのstable Object IDが返る。

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

## B-07 Alias追加

```powershell
$ObjectAAlias = "Acceptance Alias A"
sgokb --db $Db object alias add --object $ObjectAId $ObjectAAlias
```

## B-08 Alias一覧

```powershell
sgokb --db $Db object alias list --object $ObjectAId
```

**PASS**: `$ObjectAAlias`が存在する。

## B-09 Aliasで解決

```powershell
$AliasRead = sgokb --db $Db object show --name $ObjectAAlias | ConvertFrom-Json
$AliasRead.data
```

**PASS**: aliasが`$ObjectAId`へ解決される。

## B-10 OBJ-AをRename

後で比較できるよう、旧nameを保持する。

```powershell
$ObjectAOriginalName = $ObjectAName
$ObjectAName = "$ObjectAName Renamed"
sgokb --db $Db object rename --object $ObjectAId --to $ObjectAName
$RenameRead = sgokb --db $Db object show --object $ObjectAId | ConvertFrom-Json
$RenameRead.data
```

**PASS**: canonical nameが変更され、Object IDは`$ObjectAId`のままである。

## B-11 Additional Classを追加

A-05で確認した既存Classのうち、現在のPrimary Classではない互換Classを1つ選ぶ。

```powershell
sgokb --db $Db object class add --object $ObjectAId <additional-class-ref>
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: Additional Classが表示され、Object IDは変わらない。

## B-12 Primary Classを変更して元へ戻す

一時変更用として有効な既存Classを選ぶ。

```powershell
sgokb --db $Db object class set-primary --object $ObjectAId <temporary-class-ref>
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object class set-primary --object $ObjectAId character
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: 両方のmutationが成功し、最終Primary Classは`character`、Object IDは変更されない。

## B-13 Object eventを確認

```powershell
sgokb --db $Db object events --object $ObjectAId
```

**確認**: ここまでに作成されたcreation、alias / name / class / status関連のRegistry eventをevent contractに従って確認できる。

## B-14 Archiveして再Activate

```powershell
sgokb --db $Db object status --object $ObjectAId --set archived
sgokb --db $Db object show --object $ObjectAId
sgokb --db $Db object status --object $ObjectAId --set active
sgokb --db $Db object show --object $ObjectAId
```

**PASS**: 最終状態がactiveで、Object IDは`$ObjectAId`のままである。

---

# C. Source / Snapshot / Raw Artifact

各importで返されるSource IDとSnapshot IDをparseして記録する。

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

**PASS**: normalization / evidence processingが成功する。

## C-03 Source status

```powershell
sgokb --db $Db source status
```

**確認**: imported / processed source stateにSRC-A1が含まれる。

## C-04 Snapshot一覧

```powershell
sgokb --db $Db source snapshots
```

**確認**: `$SnapshotA1Id`が存在する。

## C-05 SRC-A2をImport / Process

```powershell
$ImportA2 = sgokb --db $Db source import $CaptureA2 | ConvertFrom-Json
$SourceA2Id   = $ImportA2.data[0].source
$SnapshotA2Id = $ImportA2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA2Id
```

**PASS**: 独立したlogical sourceである場合、`$SourceA2Id`は`$SourceA1Id`と異なる。

## C-06 SRC-B1をImport / Process

```powershell
$ImportB1 = sgokb --db $Db source import $CaptureB1 | ConvertFrom-Json
$SourceB1Id   = $ImportB1.data[0].source
$SnapshotB1Id = $ImportB1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotB1Id
```

## C-07 SRC-C1をImport / Process

```powershell
$ImportC1 = sgokb --db $Db source import $CaptureC1 | ConvertFrom-Json
$SourceC1Id   = $ImportC1.data[0].source
$SnapshotC1Id = $ImportC1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotC1Id
```

## C-08 同一logical Sourceの後続Snapshot

`$CaptureA1V2`は、SRC-A1と同じsource identity / URLを持つ有効な後続captureでなければならない。

```powershell
$ImportA1V2 = sgokb --db $Db source import $CaptureA1V2 | ConvertFrom-Json
$SourceA1V2Id   = $ImportA1V2.data[0].source
$SnapshotA1V2Id = $ImportA1V2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA1V2Id
```

**確認**

- Source identityがcurrent ingestion identity contractに従う。
- 後続captureに対して新しいSnapshot IDが作成される。
- 以前のSnapshotが一覧に残る。

## C-09 Raw Artifact保持

```powershell
sgokb --db $Db source snapshots
```

command outputから公開されるSource / Snapshot詳細を確認し、capture pathが表示される場合は、保持されたraw artifactが試験専用storage内に存在することを確認する。

**PASS**: 以前のRaw / Snapshot履歴がprocessingまたは後続captureによって置換されていない。

---

# D. Source <-> Object Association

D-06の前にSRC-R1をimport / processする。

```powershell
$ImportR1 = sgokb --db $Db source import $CaptureR1 | ConvertFrom-Json
$SourceR1Id   = $ImportR1.data[0].source
$SnapshotR1Id = $ImportR1.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotR1Id
```

## D-01 OBJ-AのAssociationを確認

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

## D-06 SRC-R1を多対多でAssociation

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceR1Id --status confirmed
sgokb --db $Db association set `
  --object $ObjectBId --source $SourceR1Id --status confirmed
```

## D-07 Associationを再確認

```powershell
sgokb --db $Db association list --object $ObjectAId
sgokb --db $Db association list --object $ObjectBId
sgokb --db $Db association list --object $ObjectCId
```

**PASS D-01..D-07**: 各Objectが意図したconfirmed Source集合を持ち、SRC-R1がOBJ-AとOBJ-Bの両方に表示される。

---

# E. Evidence / Provenance

## E-01 OBJ-AのEvidence candidate

```powershell
$CandidatesA = sgokb --db $Db evidence candidates --object $ObjectAId | ConvertFrom-Json
$CandidatesA.data
```

**確認**: confirmed Sourceからcandidate Evidenceが存在する。

## E-02 Evidence選択

```powershell
$SelectedA = sgokb --db $Db evidence select --object $ObjectAId | ConvertFrom-Json
$SelectedA.data
```

返されたEvidence IDを最低1つ`$EvidenceId`として記録する。

## E-03 Evidence詳細

```powershell
sgokb --db $Db evidence show $EvidenceId
```

**PASS**: contentとmetadataを読み取れ、想定したcaptureに対応している。

## E-04 Provenance

```powershell
sgokb --db $Db evidence provenance $EvidenceId
```

**手動確認**: Evidenceがnormalization / snapshot / source identityを経由して想定したRaw captureまで追跡できる。

## E-05 複数Sourceによるgrounding

candidate / selectionを実行し、Source IDを確認する。

```powershell
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: SRC-A1とSRC-A2由来のEvidenceをprovenanceによって区別できる。

## E-06 Evidence検索

capture内に実際に存在する特徴的なphraseを選ぶ。

```powershell
$EvidenceQuery = "<distinctive phrase from a test capture>"
sgokb --db $Db evidence search $EvidenceQuery --mode lexical --object $ObjectAId
```

**PASS**: 想定したEvidenceが返る。

---

# F. Evidence Package

## F-01 Package Build

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

## F-02 manifest確認

```powershell
Get-ChildItem -Recurse $BuildPath
Get-Content (Join-Path $BuildPath "manifest.json") -Raw
```

**確認**: target Object ID、package identity、存在する場合はbase Version state、選択されたEvidence membershipが今回の試験runと一致する。

## F-03 instructions確認

```powershell
Get-Content (Join-Path $BuildPath "instructions.md") -Raw
```

**PASS**: instructionsが存在し、読み取れる。

## F-04 Package内Evidenceを確認

```powershell
Get-ChildItem -Recurse $BuildPath
```

代表的なEvidence payload fileを開き、そのID / contentをE-02 / E-04と比較する。

**PASS**: Package内Evidenceが選択済みのgrounded Evidenceであり、無関係なmaterialではない。

## F-05 Package Stage

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

**PASS**: このhappy-path datasetで想定する通常のexport可能dispositionが返る。選択したdatasetが正当な理由で`review_required`となる場合、その状態を記録し、人間review後にのみ標準の明示acknowledgement経路を使用する。実際のblocked状態をPASSとして扱ってはならない。

## F-07 明示Export

通常のexport可能経路:

```powershell
$Export = sgokb --db $Db package export `
  $StagedPath --destination $ExportRoot | ConvertFrom-Json
$ExportedPath = $Export.data.path
$ExportedPath
```

F-06で正当なhuman acknowledgementが必要となり、operatorが承認した場合のみ`--acknowledge-review`を使用する。

## F-08 Export integrity

```powershell
Get-ChildItem -Recurse $ExportedPath
```

**PASS**: staged Packageから期待されるmanifest、instructions、Evidence payloadが存在し、読み取れる。

---

# G. External ChatGPT / Structured Object Result

## G-01 PackageをChatGPTへ渡す

1. このacceptance Object専用の新しいChatGPT conversationを開く。
2. `$ExportedPath`のexport済みPackageを渡す。
3. この試験では、無関係なWeb上の事実や追加Evidenceを与えない。

**PASS**: ChatGPTがPackage内容を読み取れる。

## G-02 instruction authorityを確立

Package内の`instructions.md`を分析指示の正本として扱い、返却artifactがcurrent SGOKB Structured Object Result contractに従うようChatGPTへ指示する。

**PASS**: 生成結果がfree-form proseだけではなく、Packageのinstruction / schema要件に従う。

## G-03 Grounding確認

何もImportする前に、生成結果を手動確認し、代表的なclaimをPackage内Evidence IDと比較する。

**PASS**: accepted Knowledge候補のclaimがPackage内に実在するEvidenceへgroundingされ、架空のEvidence IDが使用されていない。

## G-04 `result.json`生成

ChatGPTに最終Structured Object Resultを生成させ、正確に次のfilenameで保存する。

```text
result.json
```

**PASS**: artifactが構文上有効なJSONで、current Result schemaに従う。

## G-05 Facet確認

`result.json`を開き、OBJ-Aに対して生成されたFacetを確認する。

**PASS**: Facetが選択したObject / Classとgrounded materialに適切である。

## G-06 Statement確認

生成されたFacet配下の代表的なStatementを確認する。

**PASS**: Statementが構造化され、意味を持ち、有効なPackage Evidenceを参照している。

## G-07 Relation確認

SRC-R1が裏付ける試験用Relationについて、Resultが意図したOBJ-A <-> OBJ-B Relationを、選択したRelation typeと有効なEvidence groundingを用いて表現していることを確認する。

**PASS**: Relation targetが意図したstable Object identityへ解決され、適切なEvidence supportを持つ。

## G-08 Resultをincoming dropへ配置

```powershell
$DropDir = Join-Path $IncomingRoot "drop\$PackageId"
New-Item -ItemType Directory -Force $DropDir | Out-Null
Copy-Item "C:\path\to\generated\result.json" (Join-Path $DropDir "result.json") -Force
$ResultPath = Join-Path $DropDir "result.json"
Test-Path $ResultPath
```

**PASS**: `Test-Path`がtrueを返し、filenameが正確に`result.json`である。

---

# H. Result Intake / Validation / Import

## H-01 Result検出

```powershell
sgokb --db $Db result detect --incoming-root $IncomingRoot
```

**PASS**: `result.json`を含むPackage dropが検出される。

## H-02 Result受信

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

**PASS**: `$ReceiptId`が表示される。

## H-04 Pending Result

```powershell
sgokb --db $Db result pending
```

**PASS**: 受信済みResultが想定するpre-import stateで表示される。

## H-05 Validate

```powershell
sgokb --db $Db result validate $ReceiptId --incoming-root $IncomingRoot
if ($LASTEXITCODE -ne 0) { throw "H-05 failed" }
```

**PASS**: 正常系artifactによりResultがvalid stateへ到達する。

## H-06 Human review

```powershell
sgokb --db $Db result review `
  $ReceiptId --incoming-root $IncomingRoot --review-format markdown
```

続行前にObject identity、base Version、Facet、Statement、Relation、Evidence ID、Registry proposalを確認する。

**PASS**: 提案されたKnowledgeが理解可能で、意図した結果と一致する。

## H-07 明示Import

```powershell
$Imported = sgokb --db $Db result import `
  $ReceiptId --incoming-root $IncomingRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "H-07 failed" }
$Imported.data
```

accepted normal flowとして正当なreview acknowledgementが必要な場合、先にhuman reviewを実施し、`--acknowledge-review`を明示的に使用する。

import responseまたはH-08のreadから、新しく作成されたKnowledge Version IDを`$Version1Id`として記録する。

## H-08 Current pointer確認

```powershell
$CurrentA = sgokb --db $Db object show --object $ObjectAId --knowledge | ConvertFrom-Json
$CurrentA.data
```

**PASS**: current accepted KnowledgeがImportしたResultに対応し、`$Version1Id`がcurrentである。

## H-09 Evidence link確認

Knowledge readと代表的なEvidence lookupを使用する。

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
sgokb --db $Db object relations --object $ObjectAId
```

代表的なStatement / Relation Evidence IDについて実行する。

```powershell
sgokb --db $Db evidence show <evidence-id>
sgokb --db $Db evidence provenance <evidence-id>
```

**PASS**: accepted Knowledgeのlinkが、存在する正しいEvidenceへ解決される。

---

# I. Registry Proposal

試験データで裏付けられた、有効かつ安全なproposalを1件含むResultを使用する。適切であればalias proposalが実用的である。

## I-01 Proposal intake確認

proposalを含むResultをImportした後に実行する。

```powershell
sgokb --db $Db registry proposal list --decision pending
```

proposal referenceを`$ProposalRef`として記録する。

**PASS**: proposalがpendingであり、silent applyされていない。

## I-02 Pending proposal一覧

```powershell
sgokb --db $Db registry proposal list --decision pending
```

**PASS**: `$ProposalRef`が存在する。

## I-03 Proposal詳細

```powershell
sgokb --db $Db registry proposal show $ProposalRef
```

**確認**: kind、target / payload、review contextが意図した安全な変更と一致する。

## I-04 Proposal Accept

```powershell
sgokb --db $Db registry proposal accept `
  $ProposalRef --note "happy-path acceptance reviewed"
```

**PASS**: decisionがacceptedになるが、acceptしただけではRegistry mutationは発生していない。

## I-05 Proposal Apply

```powershell
sgokb --db $Db registry proposal apply $ProposalRef
```

**PASS**: applyが成功する。

## I-06 影響を受けたRegistry / Object stateを確認

proposal kindに対応するread commandを使用する。alias proposalの場合:

```powershell
sgokb --db $Db object alias list --object $ObjectAId
```

**PASS**: 期待するRegistry mutationがこの時点で表示される。

---

# J. Knowledge Versioning

## J-01 Version 1 identityを記録

H-07 / H-08の結果から設定・記録する。

```powershell
$Version1Id = "<accepted V1 knowledge_version_id>"
sgokb --db $Db version show $Version1Id
```

**PASS**: V1を読み取れる。

## J-02 後続Evidenceを追加

C-08で作成した後続SRC-A1 Snapshotを使用し、まだ関連付けられていない場合はOBJ-Aへconfirmedする。

```powershell
sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1V2Id --status confirmed
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: 2回目のanalysis cycleに利用できる新しいEvidenceが存在する。

## J-03 Update PackageをBuild

```powershell
$Build2 = sgokb --db $Db package build `
  --object $ObjectAId --build-root $BuildRoot | ConvertFrom-Json
$PackageId2 = $Build2.data.package_id
$BuildPath2 = $Build2.data.path
```

`manifest.json`を確認し、current contractの要件どおりPackageがOBJ-Aとcurrent / base V1へbindingされていることを確認する。

## J-04 Result 2生成

`$PackageId2`についてF-05からG-08を繰り返し、新しく利用可能になったEvidenceを使用して有効な更新版`result.json`を生成する。

2件目のResult pathを`$ResultPath2`として記録する。

## J-05 Result 2をValidate / Review / Import

```powershell
$Receipt2 = sgokb --db $Db result receive `
  $ResultPath2 --package-id $PackageId2 --incoming-root $IncomingRoot | ConvertFrom-Json
$ReceiptId2 = $Receipt2.data.receipt_id

sgokb --db $Db result validate $ReceiptId2 --incoming-root $IncomingRoot
sgokb --db $Db result review $ReceiptId2 --incoming-root $IncomingRoot --review-format markdown
$Imported2 = sgokb --db $Db result import $ReceiptId2 --incoming-root $IncomingRoot | ConvertFrom-Json
```

import / current readから`$Version2Id`を記録する。

## J-06 V2がcurrentであることを確認

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: V2がcurrentである。

## J-07 V1が保持されていることを確認

```powershell
sgokb --db $Db version show $Version1Id
```

**PASS**: V1が存在し続け、読み取れる。

## J-08 両Versionを直接読む

```powershell
sgokb --db $Db version show $Version1Id
sgokb --db $Db version show $Version2Id
```

## J-09 V1 -> V2 Diff

```powershell
sgokb --db $Db version diff $Version1Id $Version2Id --diff-format markdown
```

**PASS**: 想定した追加 / 変更が表現され、無関係な破壊的rewriteが発生していない。

## J-10 Historical Object read

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge --version $Version1Id
```

**PASS**: V2ではなくhistorical V1 stateが返る。

## J-11 Version固有grounding

代表的なV1 / V2のStatement / Relationについて、`evidence show`と`evidence provenance`でEvidence IDを解決する。

**PASS**: 両immutable Versionが、それぞれ正しいgroundingを保持する。

---

# K. Relation

## K-01 Import済みRelation確認

```powershell
sgokb --db $Db object relations --object $ObjectAId
```

**PASS**: Result Importによって作成されたOBJ-BへのRelationがaccepted Knowledgeに存在する。

## K-02 OBJ-A側から読む

```powershell
$RelationsA = sgokb --db $Db object relations --object $ObjectAId | ConvertFrom-Json
$RelationsA.data
```

**PASS**: targetが想定どおり`$ObjectBId`へ解決される。

## K-03 OBJ-B側の関連stateを読む

```powershell
sgokb --db $Db object relations --object $ObjectBId
```

**PASS**: Relationの可視性 / directionが選択したRelation type contractと一致する。Relation typeがinverse relationを定義していない場合、inverse relationの存在を要求しない。

## K-04 Relation Evidence確認

Evidenceを有効にした通常のrelation outputから引用Evidence IDを1件選択し、次を実行する。

```powershell
sgokb --db $Db evidence show <relation-evidence-id>
sgokb --db $Db evidence provenance <relation-evidence-id>
```

**PASS**: EvidenceがRelationを裏付けている。

## K-05 Version指定Relation read

```powershell
sgokb --db $Db object relations --object $ObjectAId --version $Version1Id
sgokb --db $Db object relations --object $ObjectAId --version $Version2Id
```

**PASS**: 各Versionが自身のRelation stateを返し、current / historical scopeが混在しない。

---

# L. Render

## L-01 Current OBJ-AをRender

```powershell
$RenderCurrent = sgokb --db $Db render `
  --object $ObjectAId --output-root $RenderRoot | ConvertFrom-Json
$RenderCurrent.data
```

生成されたMarkdown fileを開く。

**PASS**: current accepted Knowledgeが人間可読な形で表示される。

## L-02 指定VersionをRender

```powershell
sgokb --db $Db render --version $Version1Id --output-root $RenderRoot
```

**PASS**: historical Versionを独立してRenderできる。

## L-03 Facet確認

current renderを開き、次の結果とFacetを比較する。

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: RenderされたFacetが同じaccepted Knowledgeを表現している。

## L-04 Relation確認

RenderされたRelation内容を次と比較する。

```powershell
sgokb --db $Db object relations --object $ObjectAId
```

**PASS**: Relation情報が一致する。

## L-05 Grounding / Provenance reference確認

read / render surfaceに表示された代表的なEvidence identifierについて次を実行する。

```powershell
sgokb --db $Db evidence provenance <evidence-id>
```

**PASS**: Render / readされたKnowledgeが引き続きtrace可能である。

## L-06 V1 / V2 Render比較

両VersionをRenderし、手動またはPowerShellで比較する。

```powershell
# Substitute the actual output paths returned by render.
Compare-Object `
  (Get-Content "<V1-render-path>") `
  (Get-Content "<V2-render-path>")
```

**PASS**: 想定するVersion差分が反映されている。

---

# M. Lexical Search

## M-01 Canonical name検索

```powershell
sgokb --db $Db search $ObjectAName --mode lexical
```

**PASS**: OBJ-Aが返る。

## M-02 Alias検索

```powershell
sgokb --db $Db search $ObjectAAlias --mode lexical
```

**PASS**: current lexical identity / search contractに従いOBJ-Aを発見できる。

## M-03 特徴的なKnowledge term検索

accepted V2 Knowledgeに存在するtermを選ぶ。

```powershell
$KnowledgeTerm = "<distinctive accepted-knowledge term>"
sgokb --db $Db search $KnowledgeTerm --mode lexical
```

**PASS**: 想定したObjectが返る。

## M-04 Multi-object query

最低2つの試験Objectで共通するtermを選ぶ。

```powershell
sgokb --db $Db search "<shared term>" --mode lexical --limit 10
```

**PASS**: 複数の関連Objectを返せる。同一Object identity由来の重複rowを別Objectとして扱わない。

## M-05 Current scope

V1とV2で変化したtermを使用して比較する。

```powershell
sgokb --db $Db search "<current-specific term>" --mode lexical
sgokb --db $Db search "<historical-specific term>" --mode lexical --version $Version1Id
```

**PASS**: 通常検索がcurrent accepted scopeを使用し、明示Version filterでhistorical scopeを指定できる。

## M-06 Cross-class lexical retrieval

OBJ-A / B / Cに対応するqueryを実行し、必要に応じてClass filterを使用する。

```powershell
sgokb --db $Db search "<character term>" --mode lexical --primary-class character
sgokb --db $Db search "<work term>" --mode lexical --primary-class work
sgokb --db $Db search "<concept term>" --mode lexical --primary-class concept
```

**PASS**: 各Classを正しくretrievalできる。

---

# N. Semantic Search

Nを実施する前に、accepted local Embedding runtimeとQdrant runtimeが起動・構成されていることを確認する。本手順ではfrozen local semantic compositionを使用し、cloud fallbackを有効にしてはならない。

## N-01 Semantic runtime起動 / 確認

```powershell
sgokb --db $Db system index status
```

続いて簡単なfull-runtime semantic queryを実行する。

```powershell
sgokb --db $Db search "<semantic query for OBJ-A>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: runtime-unavailable exitを出さずにcommandが成功する。

## N-02 Index status

```powershell
sgokb --db $Db system index status
```

**PASS**: current index / Embedding Space stateが、この試験構成で利用可能として報告される。

## N-03 Index rebuild

```powershell
sgokb --db $Db system index rebuild
if ($LASTEXITCODE -ne 0) { throw "N-03 failed" }
```

current environmentでindex rebuild前後にsemantic derived synchronizationが必要な場合、次を実行する。

```powershell
sgokb --db $Db system derived sync --semantic-runtime
```

**PASS**: canonical Versionを変更せず、canonical Knowledgeからderived semantic stateを再構築できる。

## N-04 Semantic paraphrase query

Source / Knowledgeの文言をそのままコピーせず、OBJ-Aを説明するqueryを使用する。

```powershell
sgokb --db $Db search `
  "<paraphrased semantic description of OBJ-A>" `
  --mode semantic --semantic-runtime --require-full-runtime --limit 10
```

**PASS**: 小規模acceptance dataset内でOBJ-Aが妥当な順位でretrievalされる。

## N-05 Overview-level semantic retrieval

1つのStatementと完全一致するqueryではなく、Object overviewに対応する広いqueryを使用する。

```powershell
sgokb --db $Db search "<broad OBJ-A description>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: current R2 representation familyを通じてOBJ-Aをretrievalできる。

## N-06 Facet semantic retrieval

OBJ-Aに実在するFacetを選択し、その意味をqueryする。

```powershell
sgokb --db $Db search "<facet semantic query>" `
  --mode semantic --semantic-runtime --require-full-runtime `
  --facet <facet-ref>
```

**PASS**: 意図したFacet contextでOBJ-Aが返る。

## N-07 Statement semantic retrieval

特徴的なStatementをparaphraseしてqueryする。

```powershell
sgokb --db $Db search "<statement paraphrase>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: 文言が異なっていてもOBJ-Aが返る。

## N-08 Current Version scope

V2固有のsemantic conceptを使用し、必要に応じてV1も明示的にqueryする。

```powershell
sgokb --db $Db search "<V2-specific semantic concept>" `
  --mode semantic --semantic-runtime --require-full-runtime

sgokb --db $Db search "<V1-specific semantic concept>" `
  --mode semantic --semantic-runtime --require-full-runtime `
  --version $Version1Id
```

**PASS**: current scopeとhistorical scopeが分離されている。

## N-09 Cross-class semantic retrieval

OBJ-A、OBJ-B、OBJ-Cをそれぞれ識別できる意味的なqueryを実行する。

**PASS**: semantic retrievalが1つの試験Classに限定されない。

---

# O. Hybrid Search

このacceptance sectionで両channelが実際に利用可能であることを証明するため、`--mode hybrid --semantic-runtime --require-full-runtime`を使用する。

## O-01 Name + meaning query

```powershell
sgokb --db $Db search `
  "$ObjectAName <semantic description>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: OBJ-Aが返り、semantic channel不足を示すdegradation warningがない。

## O-02 Exact identityの優先性

```powershell
sgokb --db $Db search $ObjectAName `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: exact identityが容易に発見でき、意味的に類似するObject群の中へ埋没しない。

## O-03 Lexically distinctive Knowledge query

```powershell
sgokb --db $Db search "<distinctive literal knowledge phrase>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: 関連Objectがretrievalされる。

## O-04 Semantically descriptive query

```powershell
sgokb --db $Db search "<paraphrased meaning>" `
  --mode hybrid --semantic-runtime --require-full-runtime
```

**PASS**: semantic contributionによって意図したObjectをretrievalできる。

## O-05 Object aggregation

OBJ-Aの複数Facet / Statementにmatchするqueryを実行する。

```powershell
$Hybrid = sgokb --db $Db search "<multi-aspect OBJ-A query>" `
  --mode hybrid --semantic-runtime --require-full-runtime --limit 10 | ConvertFrom-Json
$Hybrid.data
```

**PASS**: OBJ-Aが1件のObject resultとして表現され、overview / facet / statementごとの別rowとして重複しない。

---

# P. Similarity

Similarityにはsemantic runtime / index stateが構成済みである必要がある。

## P-01 Object Similarity

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

**PASS**: 類似Objectが返り、source Object identityがsimilarity contractどおり扱われる。

## P-02 Facet-specific Similarity

OBJ-Aに実在するFacetを選択する。

```powershell
sgokb --db $Db similar `
  --object $ObjectAId --facet <facet-ref> --limit 10
```

**PASS**: facet-specific比較が成功し、指定したFacetを使用する。

## P-03 Rankingの人間によるsanity check

top resultを、既知のOBJ-B / OBJ-C内容および小規模datasetと比較する。

**PASS**: 運用利用のsanity checkとして意味的に概ね妥当なorderingである。これはPhase Nのformal ANN-quality benchmarkではない。

## P-04 Current Version Similarity

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

続いて、対応している場合はhistorical Versionを明示して比較する。

```powershell
sgokb --db $Db similar --object $ObjectAId --version $Version1Id --limit 10
```

**PASS**: default / current scopeと明示historical scopeを区別できる。

## P-05 Cross-class Similarity

```powershell
sgokb --db $Db similar `
  --object $ObjectAId --cross-class --limit 10
```

**PASS**: current similarity semanticsに従ってcross-class candidateを返せる。

---

# Q. MCP Read Boundary

MCP clientはproduction DBではなくacceptance DBを起動するよう構成する。

Core / lexical server command:

```text
sgokb --db <ABSOLUTE_ACCEPTANCE_DB_PATH> mcp serve
```

semantic MCP testの場合:

```text
sgokb --db <ABSOLUTE_ACCEPTANCE_DB_PATH> mcp serve --semantic-runtime
```

Q-01..Q-12は接続済みMCP clientのUI / tool inspectorから実行する。

## Q-01 `get_object`

呼出し:

```text
get_object({"object_id":"<OBJ-A-ID>"})
```

**PASS**: Object IDとcurrent accepted VersionがCLIの`object show --knowledge`と一致する。

## Q-02 `get_objects`

公開されているschemaに従ってOBJ-A / B / CのIDを指定して呼び出す。

**PASS**: 要求したすべてのObjectが正しいstable identityで返る。

## Q-03 `search_objects`

まずlexical queryを呼び出す。

```text
search_objects({"query":"<known term>","mode":"lexical","limit":10})
```

次にsemantic-enabled serverでhybrid queryを呼び出す。

**PASS**: 想定ObjectがCLI retrieval semanticsと一致する。

## Q-04 `find_similar_objects`

```text
find_similar_objects({"object_id":"<OBJ-A-ID>","limit":10})
```

**PASS**: MCP経由でSimilarity readが成功する。

## Q-05 `get_object_relations`

```text
get_object_relations({"object_id":"<OBJ-A-ID>"})
```

**PASS**: 想定するOBJ-A -> OBJ-B Relationが、CLIと同じaccepted Version semanticsで返る。

## Q-06 `get_object_evidence`

```text
get_object_evidence({"object_id":"<OBJ-A-ID>"})
```

**PASS**: OBJ-Aのgrounded Evidenceが返る。

## Q-07 `search_evidence`

tool schemaに従い、E-06で使用した特徴的なqueryを指定する。

**PASS**: 想定したEvidenceが見つかる。

## Q-08 `build_context`

```text
build_context({
  "object_ids":["<OBJ-A-ID>","<OBJ-B-ID>"],
  "purpose":"comparison",
  "max_characters":12000
})
```

**PASS**: deterministicなKnowledge subsetが返り、Context Builderによって新しいLLM-authored factが挿入されない。

## Q-09 CLI / MCP整合性

Q-01と次を比較する。

```powershell
sgokb --db $Db object show --object $ObjectAId --knowledge
```

**PASS**: 両方が同じcurrent accepted Knowledge Versionへ解決される。

## Q-10 Comparison context

OBJ-AとOBJ-Bを`purpose = comparison`で使用する。

**PASS**: 返されたsubsetに両Objectの関連する保存済みKnowledgeが含まれる。

## Q-11 Character budget

`max_characters = 6000`など、意図的に小さめだが有効なbudgetで`build_context`を呼び出す。

**PASS**: 返されたcontextが指定budget contract内に収まる。

## Q-12 Determinism

DB stateを変更せず、同一inputでQ-08を再実行する。

**PASS**: deterministic Context Builder contractに従い、選択内容 / 順序が同一である。

---

# R. Derived Index

## R-01 Index status

```powershell
sgokb --db $Db system index status
sgokb --db $Db system derived status --semantic-runtime
```

current derived stateを記録する。

## R-02 Derived / Index state再構築

```powershell
sgokb --db $Db system derived sync --semantic-runtime
sgokb --db $Db system index rebuild
```

**PASS**: canonical accepted Knowledgeを使用してrebuild / syncが成功する。

## R-03 Rebuild後のLexical read

M-01 / M-03を再実行する。

**PASS**: derived maintenance後もcanonical / lexical readが正しい。

## R-04 Rebuild後のSemantic read

N-04を再実行する。

**PASS**: 想定したObjectが返る。

## R-05 Rebuild後のSimilarity

P-01 / P-02を再実行する。

**PASS**: Similarityが引き続き機能する。

## R-06 Representation / Embedding reuse sanity check

canonical Knowledgeを変更せず、derived syncを2回目として実行する。

```powershell
$Before = sgokb --db $Db system derived status --semantic-runtime | ConvertFrom-Json
sgokb --db $Db system derived sync --semantic-runtime
$After = sgokb --db $Db system derived status --semantic-runtime | ConvertFrom-Json
$Before.data
$After.data
```

**PASS**: 未変更のcanonical Knowledgeから意味的に重複したcurrent stateが生成されず、status surfaceが報告するID / countがreuse / idempotent maintenance semanticsと整合する。これは運用上のsanity checkであり、N-02のinternal deterministic fixture assertionではない。

---

# S. Backup / Restore 正常系

acceptance DBと試験専用backup / restore pathのみを使用する。

## S-01 Backup status

```powershell
sgokb --db $Db system backup status --root $BackupRoot
```

**PASS**: backup subsystemのstatusを読み取れる。

## S-02 Backup作成

```powershell
$Backup = sgokb --db $Db system backup create --root $BackupRoot | ConvertFrom-Json
$Backup.data
```

返されたbackup pathを`$BackupPath`として記録する。

## S-03 Backup integrity確認

backup commandがintegrity / verification metadataを返す場合は内容を確認する。加えて次を実行する。

```powershell
Test-Path $BackupPath
```

**PASS**: backupが存在し、通常のintegrity verificationを伴って作成が正常完了している。

## S-04 Restore plan

command output / contractに従い、隔離restore targetへのrestoreをplanする。

```powershell
sgokb --db $RestoreDb system restore plan $BackupPath
```

**PASS**: planが意図した試験専用backupとrestore targetを示す。production stateへ解決される場合は続行してはならない。

## S-05 Restore適用

新規restore targetに対し、通常のrestore apply経路を実行する。

```powershell
sgokb --db $RestoreDb system restore apply $BackupPath
```

current CLIがtarget fileの既存状態によってexplicit overwrite acknowledgementを要求する場合は、試験専用targetを必要に応じて削除 / 再作成するか、targetが破棄可能なacceptance restore DBであることを確認したうえで`--acknowledge-overwrite`を使用する。

**PASS**: restoreが正常完了する。

## S-06 Restore後Integrity

```powershell
sgokb --db $RestoreDb system integrity
```

**PASS**: integrityが成功する。

## S-07 Restore後Object

```powershell
sgokb --db $RestoreDb object show --object $ObjectAId --knowledge
sgokb --db $RestoreDb object show --object $ObjectBId --knowledge
sgokb --db $RestoreDb object show --object $ObjectCId --knowledge
```

**PASS**: Object stable identityが保持されている。

## S-08 Restore後Version

```powershell
sgokb --db $RestoreDb version show $Version1Id
sgokb --db $RestoreDb version show $Version2Id
```

**PASS**: accepted Version履歴が保持されている。

## S-09 Restore後Evidence / Provenance

```powershell
sgokb --db $RestoreDb evidence show $EvidenceId
sgokb --db $RestoreDb evidence provenance $EvidenceId
```

**PASS**: grounded provenanceを引き続き解決できる。

## S-10 Restore後Derived state再構築

restore済み試験環境が試験専用semantic / vector targetを使用するよう構成し、次を実行する。

```powershell
sgokb --db $RestoreDb system derived sync --semantic-runtime
sgokb --db $RestoreDb system index rebuild
```

**PASS**: restoreされたcanonical stateからderived stateを再生成できる。

## S-11 Restore後Knowledge検索

```powershell
sgokb --db $RestoreDb search $ObjectAName --mode lexical
sgokb --db $RestoreDb search "<semantic OBJ-A query>" `
  --mode semantic --semantic-runtime --require-full-runtime
```

**PASS**: restore後もlocal lexical readと構成済みsemantic readの両方が機能する。

## S-12 Restore後Knowledge Render

```powershell
sgokb --db $RestoreDb render --object $ObjectAId --output-root "$RenderRoot/restored"
```

**PASS**: restoreされたcurrent Knowledgeを正常にRenderできる。

---

# T. 最終無中断End-to-End実行

A-Sを個別に理解した後、新しいObjectを1件、SQLiteを手動編集したり境界を迂回したりせず、通常workflow全体へ通す。

## T-01 Full normal operational chain

新しい有効な試験Objectと、1件以上の新しい有効なcapture bundleを使用する。

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
19. object show --knowledge
20. object relations
21. render
22. lexical search
23. semantic search with full runtime
24. hybrid search with full runtime
25. similar
26. MCP get_object
27. MCP search_objects
28. MCP build_context
29. system backup create
30. final system integrity
```

各stepで返されたstable IDを記録し、identity chainが一貫していることを確認する。

**T-01 PASSには次のすべてが必要**:

- 必須stepがskipされていない。
- 成功が期待されるすべてのcommandが正常終了する。
- external exportが明示操作である。
- external AIが架空provenanceではなくPackage Evidenceを使用する。
- Resultが明示Importの前にvalidate / reviewされている。
- accepted Knowledgeがhistorical accepted stateの上書きではなくVersionとして作成される。
- 代表的なKnowledgeをEvidenceおよびRaw Source lineageまで追跡できる。
- lexical、semantic、hybrid、similarity、render、MCP read surfaceが同じcanonical Object / Version semanticsへ解決される。
- workflow完了後にbackup作成が成功する。
- 最後の`system integrity`が成功する。

---

# 3. 完了判定

## Core PASS

local canonical / read workflowまでの該当試験がすべてPASSした場合のみ、**Core PASS**とする。対象は次を含む。

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

Core PASSに加え、optional-runtime / full-system acceptance sectionがすべて完了した場合のみ、**Full SGOKB PASS**とする。

```text
N Semantic Search
O Hybrid Search
P Similarity
Q MCP read boundary
R Derived Index
S Backup / Restore
T full uninterrupted run including semantic/MCP/backup steps
```

最終acceptance recordには、正確なDB path、試験日、repository commit / release identity、使用した場合はsemantic runtime identity、Object / Version ID、overall verdictを記録する。
