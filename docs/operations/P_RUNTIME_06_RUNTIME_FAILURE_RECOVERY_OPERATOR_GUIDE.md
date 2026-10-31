# P-RUNTIME-06 — Runtime障害・復旧 受入操作ガイド

日付: 2026-10-31  
タスク: `P-RUNTIME-06 [P1] Runtime failure / recovery acceptance`  
対象環境: supported Windows reference workstation

## 目的

この手順では、native Qdrant runtimeを意図的かつ制御された方法で一時停止し、SGOKBが障害を正しく観測すること、誤ったport occupantをQdrant readyと判定しないこと、Qdrantのpersistent collectionが再起動後も残ること、Vector Indexを再構築できること、そしてcanonical SQLiteが障害前後で正常であることを確認します。

P-RUNTIME-06はQdrant lifecycleをSGOKBへ移しません。Qdrantの停止・復旧はWindows Task Schedulerをoperatorが直接操作します。

## 0. 前提と重要な注意

Repository:

```text
C:\codex\SourceGroundedObjectKnowledgeBase
```

使用branch:

```text
phase-p/runtime-06-failure-recovery-acceptance
```

reference Workspace:

```text
.local\acceptance\sgokb-happy-path.sqlite
```

Qdrant task:

```text
\SGOKB\Qdrant
```

この手順では、故障注入前に必ずTask Scheduler taskを無効化します。無効化せずにQdrantを停止すると、P-RUNTIME-04で導入した60秒recovery pulseが自動復旧し、試験と競合します。

canonical Knowledgeを編集する操作、Result import、Version promotion、Registry変更は行いません。

## 1. local branchを準備する

```powershell
cd C:\codex\SourceGroundedObjectKnowledgeBase

git fetch origin
git switch phase-p/runtime-06-failure-recovery-acceptance
git pull --ff-only

git status
```

working treeがcleanであることを確認します。

## 2. focused testとRuffを実行する

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_p_runtime_06_failure_recovery_acceptance.py `
  tests/test_p_runtime_03_runtime_health_boundary.py `
  tests/test_p_runtime_04_windows_login_autostart.py `
  tests/test_p_runtime_05_gui_runtime_dashboard.py

.\.venv\Scripts\python.exe -m ruff check src tests
```

期待結果:

- focused tests: PASS
- Ruff: `All checks passed!`

## 3. baselineを記録する

```powershell
$Db = ".local/acceptance/sgokb-happy-path.sqlite"
$TaskName = "Qdrant"
$TaskPath = "\SGOKB\"
$ReadyUrl = "http://127.0.0.1:6333/readyz"

$BeforeStatus = .\.venv\Scripts\sgokb.exe --db $Db system status | ConvertFrom-Json
$BeforeIntegrity = .\.venv\Scripts\sgokb.exe --db $Db system integrity | ConvertFrom-Json
$BeforeCollections = @(
    $BeforeStatus.data.runtime_health.components.qdrant.details.available_collections |
    Sort-Object
)
$BeforeObjectCount = $BeforeStatus.data.objects.count
$BeforeCurrentCount = $BeforeStatus.data.objects.with_current_version

$BeforeIntegrity.data
$BeforeStatus.data.runtime_health.components.qdrant
```

必須baseline:

```text
integrity ok                 = true
foreign_key_violations       = []
Qdrant status                = healthy
Qdrant ready                 = true
Qdrant version               = 1.19.2
qdrant_owner                 = external
start / stop / restart       = false / false / false
```

collection一覧は後でpersistence比較に使用します。

## 4. Qdrantをcontrolled unavailable状態にする

まずTask Schedulerを無効化してから停止します。

```powershell
Disable-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath | Out-Null
Stop-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath
Start-Sleep -Seconds 3

Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath |
    Select-Object TaskName, State

Get-Process qdrant -ErrorAction SilentlyContinue
```

`qdrant.exe`がまだ残っている場合のみ、taskがDisabledであることを再確認してから停止します。

```powershell
Get-Process qdrant -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
```

`Invoke-WebRequest`は失敗することが期待値です。

```powershell
try {
    Invoke-WebRequest -Uri $ReadyUrl -UseBasicParsing -TimeoutSec 3
} catch {
    $_.Exception.Message
}
```

## 5. CLI degradationを確認する

```powershell
$DownStatus = .\.venv\Scripts\sgokb.exe --db $Db system status | ConvertFrom-Json
$DownQdrant = $DownStatus.data.runtime_health.components.qdrant

$DownQdrant
$DownStatus.data.runtime_health.lifecycle
```

期待結果:

```text
Qdrant status        = unavailable
ready                = false
issue                = qdrant_endpoint_unavailable または qdrant_readiness_failed
qdrant_owner         = external
observe              = true
start/stop/restart   = false/false/false
```

`system status`自体はRuntime障害をcomponent状態として返し、canonical DBを壊してはいけません。

## 6. GUI degradationを確認する

別PowerShellからGUIを起動します。

```powershell
.\.venv\Scripts\sgokb-gui.exe
```

reference Workspaceを開き、`System > Overview` で `Refresh system status` を実行します。

確認項目:

```text
[ ] QdrantがHEALTHYではなくunavailable/not readyとして表示される
[ ] Semantic Search readiness = BLOCKED
[ ] blocker/troubleshootingにQdrantまたは/readyzが示される
[ ] Qdrant lifecycle owner = external
[ ] Start / Stop / Restart操作が存在しない
[ ] raw system.status JSONにも同じ障害状態が表示される
```

確認後、GUIは閉じても構いません。

## 7. port conflict / wrong-serviceを注入する

Qdrant taskがDisabledで、real `qdrant.exe`が停止している状態でのみ実行します。

fake server用scriptを作成します。

```powershell
$FakeScript = Join-Path $env:TEMP "sgokb-p06-port-conflict.py"

@'
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"not qdrant"
        self.send_response(503 if self.path == "/readyz" else 404)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

ThreadingHTTPServer(("127.0.0.1", 6333), Handler).serve_forever()
'@ | Set-Content -LiteralPath $FakeScript -Encoding UTF8

$FakeProcess = Start-Process `
    -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList $FakeScript `
    -PassThru

Start-Sleep -Seconds 2
```

fake port occupantを確認します。

```powershell
try {
    Invoke-WebRequest -Uri $ReadyUrl -UseBasicParsing -TimeoutSec 3
} catch {
    $_.Exception.Message
}
```

次にSGOKB statusを確認します。

```powershell
$ConflictStatus = .\.venv\Scripts\sgokb.exe --db $Db system status | ConvertFrom-Json
$ConflictStatus.data.runtime_health.components.qdrant
```

必須結果:

```text
status = unavailable
ready  = false
issue  = qdrant_readiness_failed または同等の明示的endpoint failure
```

**port 6333がopenであるだけでhealthyになってはいけません。**

SGOKBがfake processを終了したり、lifecycle ownershipを取得したりしてもいけません。

## 8. fake port occupantを削除する

```powershell
if ($FakeProcess -and -not $FakeProcess.HasExited) {
    Stop-Process -Id $FakeProcess.Id -Force
}
Remove-Item -LiteralPath $FakeScript -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
```

6333が解放されたことを確認します。

```powershell
Get-NetTCPConnection -LocalPort 6333 -ErrorAction SilentlyContinue
```

## 9. native Qdrantを復旧する

```powershell
Enable-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath | Out-Null
Start-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath

$Deadline = (Get-Date).AddSeconds(120)
$Ready = $false
while ((Get-Date) -lt $Deadline) {
    try {
        $Response = Invoke-WebRequest -Uri $ReadyUrl -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            $Ready = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}

if (-not $Ready) {
    throw "Qdrant did not recover within 120 seconds"
}

$Response.StatusCode
$Response.Content
```

期待値:

```text
200
all shards are ready
```

## 10. persistent collectionを確認する

```powershell
$RecoveredStatus = .\.venv\Scripts\sgokb.exe --db $Db system status | ConvertFrom-Json
$AfterCollections = @(
    $RecoveredStatus.data.runtime_health.components.qdrant.details.available_collections |
    Sort-Object
)

$CollectionDiff = Compare-Object $BeforeCollections $AfterCollections
$CollectionDiff
```

`$CollectionDiff`が何も出力しなければPASSです。

```text
native Qdrant collection persistence across restart = PASS
```

差分がある場合は、そのままFAIL証跡として保存し、Vector rebuildへ進む前に原因を確認します。

## 11. recovered CLI / GUI状態を確認する

CLI:

```powershell
$RecoveredStatus.data.runtime_health.components.qdrant
```

必須:

```text
status  = healthy
ready   = true
version = 1.19.2
```

GUIを再度開いて `System > Overview > Refresh system status` を実行します。

現在のreference Workspaceでは、P-RUNTIME-05 baselineと同様に以下へ戻ることが期待値です。

```text
Qdrant                 = HEALTHY / ready / v1.19.2
Semantic Search        = DEGRADED, not BLOCKED
Search generation      = DEGRADED / generation_not_active
Derived                = DEGRADED / rendering-only warning
```

## 12. Vector Indexを再構築する

Qdrantが完全復旧してから実行します。

まず状態を確認します。

```powershell
.\.venv\Scripts\sgokb.exe --db $Db system index status
```

次に公開recovery operationを実行します。

```powershell
.\.venv\Scripts\sgokb.exe --db $Db system index rebuild
```

この操作はreplaceable Vector IndexをSQLite membership + persisted Embeddingから再構築します。accepted canonical Knowledgeを生成・変更する操作ではありません。

期待結果:

```text
command = system.index.rebuild
ok      = true
```

再度statusを確認します。

```powershell
.\.venv\Scripts\sgokb.exe --db $Db system index status
```

## 13. canonical SQLite不変条件を確認する

```powershell
$AfterStatus = .\.venv\Scripts\sgokb.exe --db $Db system status | ConvertFrom-Json
$AfterIntegrity = .\.venv\Scripts\sgokb.exe --db $Db system integrity | ConvertFrom-Json

$AfterIntegrity.data

[pscustomobject]@{
    BeforeObjectCount  = $BeforeObjectCount
    AfterObjectCount   = $AfterStatus.data.objects.count
    BeforeCurrentCount = $BeforeCurrentCount
    AfterCurrentCount  = $AfterStatus.data.objects.with_current_version
}
```

必須結果:

```text
integrity ok                 = true
sqlite_integrity             = ["ok"]
foreign_key_violations       = []
BeforeObjectCount            = AfterObjectCount
BeforeCurrentCount           = AfterCurrentCount
```

Vector rebuildによってderived-state metadataが更新される可能性はあります。これはcanonical Knowledge破壊ではありません。Object数/current Version数の変化やintegrity failureはFAILです。

## 14. crash restart sub-gate

この項目はP-RUNTIME-04のsupported workstation acceptanceを再利用します。

既存証跡:

```text
forced qdrant.exe termination          = performed
manual Start-ScheduledTask after crash = none
replacement qdrant.exe                 = PASS
recovered /readyz                      = HTTP 200
SGOKB Qdrant health                    = healthy
```

したがって、P-RUNTIME-06で同じforced crashを再度行う必要はありません。

## 15. 最終チェックリスト

以下をPASS / FAILで報告してください。

```text
[ ] focused P-RUNTIME tests PASS
[ ] Ruff PASS
[ ] baseline system integrity PASS
[ ] controlled Qdrant unavailableをCLIが検出
[ ] unavailable中のGUI Semantic Search = BLOCKED
[ ] unavailable中もQdrant lifecycle owner = external
[ ] port 6333 wrong-serviceをreadyと誤認しない
[ ] wrong-service時に明示的なQdrant issueが表示される
[ ] native Qdrantを正常に復旧できる
[ ] /readyz = HTTP 200へ復帰
[ ] Qdrant collection inventoryがrestart前後で一致
[ ] recovered CLI Qdrant = healthy / ready / v1.19.2
[ ] recovered GUIがP-RUNTIME-05 baselineへ戻る
[ ] system index rebuildがPASS
[ ] rebuild後のsystem index statusを取得できる
[ ] final system integrity PASS
[ ] Object countが前後一致
[ ] current Version countが前後一致
[ ] P-RUNTIME-04 crash-restart evidenceを再利用可能
```

すべてPASSの場合:

```text
P-RUNTIME-06 reference-host failure/recovery acceptance = PASS
```

FAILした場合は、その項目の出力をそのまま保存し、無理に復旧結果をPASSへ読み替えないでください。

## 緊急復旧

試験途中で中断した場合、fake listenerを停止し、Task Schedulerを通常状態へ戻します。

```powershell
Get-Process python -ErrorAction SilentlyContinue

if ($FakeProcess -and -not $FakeProcess.HasExited) {
    Stop-Process -Id $FakeProcess.Id -Force
}
Remove-Item -LiteralPath $FakeScript -Force -ErrorAction SilentlyContinue

Enable-ScheduledTask -TaskName "Qdrant" -TaskPath "\SGOKB\" | Out-Null
Start-ScheduledTask -TaskName "Qdrant" -TaskPath "\SGOKB\"
```

その後、必ず以下を確認します。

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:6333/readyz" -UseBasicParsing
.\.venv\Scripts\sgokb.exe --db ".local/acceptance/sgokb-happy-path.sqlite" system status
.\.venv\Scripts\sgokb.exe --db ".local/acceptance/sgokb-happy-path.sqlite" system integrity
```
