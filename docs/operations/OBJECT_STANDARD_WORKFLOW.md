# 1 Object Standard Workflow

更新日: 2026-10-16

- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-03 [P1] 1 Object標準手順を1ページで実行可能にする`
- Status: **Complete (2026-10-16)**
- CLI contract: `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`

> 目的: 1 Objectを、内部SQLite操作・Python REPL・旧`sgokb-package`を使わず、Object登録からaccepted Knowledge、検索、MCP read確認まで新しい`sgokb`だけで処理する。

---

## 0. PowerShell変数

実値へ置換する。`$Db`は通常の運用DBを指定する。受入試験では必ず隔離DBを使う。

```powershell
$Db = ".local/sgokb.sqlite"
$Bundle = "C:\path\to\capture.webcapture.zip"
$ObjectName = "Target Object"
$PrimaryClass = "character"
$ExportRoot = "C:\path\to\sgokb-export"
$IncomingRoot = "exchange/incoming"
```

ClassとDB状態を先に確認する。

```powershell
sgokb --db $Db registry class show $PrimaryClass
sgokb --db $Db system integrity
```

以降、exit codeが`0`以外ならその工程で停止する。意味はM-01 contractどおり、`3=not found/ambiguity`、`4=blocked/review-required`、`5=optional runtime unavailable`、`6=I/O/external failure`、`7=integrity failure`、`8=batch partial failure`である。

---

## 1. Object → Source → Evidence

### Object登録

```powershell
$ObjectResult = sgokb --db $Db object add --name $ObjectName --primary-class $PrimaryClass | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "object add failed" }
$ObjectId = $ObjectResult.data.object_id
```

既存Objectを使う場合は`object show --name <exact>`でstable `object_id`を取得する。write操作では以降`$ObjectId`を使う。

### Web Capture import / Normalize

```powershell
$ImportResult = sgokb --db $Db source import $Bundle | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "source import failed" }
$SourceId = $ImportResult.data[0].source
$SnapshotId = $ImportResult.data[0].snapshot

sgokb --db $Db source process --snapshot $SnapshotId
if ($LASTEXITCODE -ne 0) { throw "source process failed" }
```

### Source↔Object association

候補を確認し、対象SourceがこのObjectの根拠であるとoperatorが判断した場合だけ`confirmed`へする。

```powershell
sgokb --db $Db association list --object $ObjectId
sgokb --db $Db association set --object $ObjectId --source $SourceId --status confirmed
```

### Evidence確認

```powershell
sgokb --db $Db evidence candidates --object $ObjectId
sgokb --db $Db evidence select --object $ObjectId
```

必要なEvidenceが不足する場合は、Source追加・association修正・`--include-evidence` / `--exclude-evidence`指定を行い、Package工程へ進まない。

---

## 2. Package → External ChatGPT

### Build / Stage

```powershell
$Build = sgokb --db $Db package build --object $ObjectId | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "package build failed" }
$PackageId = $Build.data.package_id
$BuildPath = $Build.data.path

$Stage = sgokb --db $Db package stage $BuildPath | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "package stage failed" }
$StagedPath = $Stage.data.path
```

### Preflight / explicit Export

```powershell
$Preflight = sgokb --db $Db package preflight $StagedPath --destination $ExportRoot | ConvertFrom-Json
$Preflight.data
```

- `disposition = blocked`: exportしない。
- `disposition = review_required`: 内容・destination・warningを人間が確認し、承認した場合だけ`--acknowledge-review`を付ける。
- その他の正常状態: 通常exportする。

```powershell
$Export = sgokb --db $Db package export $StagedPath --destination $ExportRoot | ConvertFrom-Json
# review_requiredを明示承認した場合のみ:
# $Export = sgokb --db $Db package export $StagedPath --destination $ExportRoot --acknowledge-review | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { throw "package export failed" }
$ExportedPath = $Export.data.path
```

### ChatGPT手動工程

1. `$ExportedPath`のPackageをChatGPTへ渡す。
2. `instructions.md`を分析指示の正本として扱う。
3. Package外の情報をEvidenceとして混入させない。
4. ChatGPTが生成したStructured Object Resultを`result.json`として保存する。
5. Resultを次へ配置する。

```text
<IncomingRoot>/drop/<PackageId>/result.json
```

この工程はSGOKB runtime内で自動化しない。

---

## 3. Result → accepted Version

### Detect / Receive

```powershell
sgokb --db $Db result detect --incoming-root $IncomingRoot

$ResultPath = Join-Path $IncomingRoot "drop\$PackageId\result.json"
$Receipt = sgokb --db $Db result receive $ResultPath --package-id $PackageId --incoming-root $IncomingRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "result receive failed" }
$ReceiptId = $Receipt.data.receipt_id
```

### Validate / Review

```powershell
sgokb --db $Db result validate $ReceiptId --incoming-root $IncomingRoot
if ($LASTEXITCODE -ne 0) { throw "result validation did not reach valid state" }

sgokb --db $Db result review $ReceiptId --incoming-root $IncomingRoot --review-format markdown
```

`blocked` / invalid / staleならImportしない。review-requiredで内容を承認する場合だけ次のImportに`--acknowledge-review`を付ける。

### Explicit Import

```powershell
$Imported = sgokb --db $Db result import $ReceiptId --incoming-root $IncomingRoot | ConvertFrom-Json
# review-requiredを明示承認した場合のみ:
# $Imported = sgokb --db $Db result import $ReceiptId --incoming-root $IncomingRoot --acknowledge-review | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { throw "result import failed" }
```

Registry proposalはResult Importの副作用として適用しない。pendingがある場合だけ個別にreviewする。

```powershell
sgokb --db $Db registry proposal list --decision pending
# 内容確認後、proposal-refごとにどちらかを実行する。
# sgokb --db $Db registry proposal accept <proposal-ref> --note "reviewed"
# sgokb --db $Db registry proposal reject <proposal-ref> --note "reason"
# accepted proposalだけ、別操作として:
# sgokb --db $Db registry proposal apply <proposal-ref>
```

---

## 4. accepted Knowledge確認

### Object / Relation / Render

```powershell
sgokb --db $Db object show --object $ObjectId --knowledge
sgokb --db $Db object relations --object $ObjectId
sgokb --db $Db render --object $ObjectId
```

### Lexical Search — 必須確認

```powershell
sgokb --db $Db search $ObjectName --mode lexical
```

Objectがaccepted current Knowledgeとして検索できれば、Semantic runtimeなしでも標準workflowのlocal read pathは成立している。

### Similarity / Semantic Search — runtime構成済み環境で追加確認

Similarityはlocal Embedding provider + Vector runtimeを必要とする。構成済みなら次を確認する。

```powershell
sgokb --db $Db search $ObjectName --mode semantic --semantic-runtime --require-full-runtime
sgokb --db $Db similar --object $ObjectId
```

optional runtime未構成によるexit `5`は、M-03のLexical workflow失敗とは扱わない。ただしSemantic/Similarityを日常利用する環境では別途runtime受入を完了させる。

### MCP read — 必須確認

MCP clientのstdio server commandを次へ設定する。

```text
sgokb --db <DB_PATH> mcp serve
```

clientから`$ObjectId`を指定してObject readを1回実行し、CLIの`object show --knowledge`と同じaccepted Versionを解決できることを確認する。MCPはread-onlyであり、この確認中にcanonical writeを行わない。

---

## 5. M-03完了条件

次をすべて満たしたらM-03をCompleteとする。

- 新しい`sgokb`だけでObject登録からaccepted Version確認まで完走する。
- SQLite直接操作、Python REPL、`sgokb-package`を使用しない。
- Package ExportとResult ImportのHuman decision boundaryを迂回しない。
- Result Validation / Reviewを経由してaccepted Versionを作成する。
- pending Registry proposalを自動applyしない。
- RenderとLexical Searchでcurrent Knowledgeを確認する。
- read-only MCP clientから同じObject Knowledgeを取得できる。
- focused end-to-end integration testまたはReference Workstationでの同等受入が成功する。

ローカル受入の具体的手順と記録形式は`docs/planning/M03_LOCAL_ACCEPTANCE.md`を正本とする。
