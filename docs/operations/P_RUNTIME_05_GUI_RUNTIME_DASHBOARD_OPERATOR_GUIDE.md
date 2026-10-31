# P-RUNTIME-05 — GUI Runtime Dashboard 操作ガイド

日付: 2026-10-31  
タスク: `P-RUNTIME-05 [P1] GUI Runtime Dashboard integration`  
対象GUI画面: `System > Overview`

## 目的

このガイドでは、SGOKB Desktop GUIを起動し、既存の受入用Workspaceを選択し、Runtime Dashboardを確認し、runtime snapshotを更新して、P-RUNTIME-05受入に必要な結果を判定する手順を説明します。

この手順でRuntime Dashboardに対して行う操作は読み取り専用です。Qdrantの起動・停止・再起動は行わず、maintenance操作も必要ありません。

## 前提条件

以下のディレクトリから実行します。

```text
C:\codex\SourceGroundedObjectKnowledgeBase
```

使用するbranch:

```text
phase-p/runtime-05-gui-runtime-dashboard
```

最初にbranchを最新化します。

```powershell
cd C:\codex\SourceGroundedObjectKnowledgeBase
git pull
```

受入で使用するreference Workspaceは以下です。

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\sgokb-happy-path.sqlite
```

Qdrantは、外部所有のWindows runtimeによってすでに起動している必要があります。P-RUNTIME-05はQdrantのlifecycleを管理しません。

## 1. Desktop GUIを起動する

PowerShellから以下を実行します。

```powershell
.\.venv\Scripts\sgokb-gui.exe
```

生成済みentrypointを使用できない場合は、代わりに以下で起動できます。

```powershell
.\.venv\Scripts\python.exe -m sgokb.gui.main
```

期待結果:

- `SGOKB` のdesktop windowが開く;
- 左側navigationに `Home / Dashboard`、`Objects`、`Sources`、`Evidence`、`Associations`、`Search`、`Packages`、`Results`、`Registry`、`System`、`Settings` が表示される;
- Workspaceをまだ開いていない場合、status barに `No workspace` と表示される。

## 2. reference Workspaceを開く

以下のいずれかの方法を使用します。

- メニュー: `File > Open Workspace...`;
- ショートカット: `Ctrl+O`;
- `Home / Dashboard > Open Workspace...`。

ファイル選択画面で以下を選択します。

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\sgokb-happy-path.sqlite
```

その後、`Open` をクリックします。

期待結果:

- window titleにWorkspace名が含まれるようになる;
- status barにWorkspace pathが表示される;
- 一時的に `Workspace ready` メッセージが表示される場合がある;
- Home画面にObject数、current Knowledge、migration summaryなどが表示される。

Workspaceを開けない場合は、受入手順を中止し、表示されたerrorを記録してください。代替として新しいWorkspaceを作成してはいけません。

## 3. Runtime Dashboardを開く

左側navigationで以下をクリックします。

```text
System
```

画面タイトルは以下です。

```text
System / Maintenance
```

最初のtabである以下を選択します。

```text
Overview
```

P-RUNTIME-05受入では、後続のtroubleshooting手順で明示的に必要とされない限り、`Derived`、`Vector Index`、`Backup`、`Restore`、`MCP`、`Advanced Generation` は使用しません。

## 4. runtime snapshotを更新する

`System > Overview` で以下をクリックします。

```text
Refresh system status
```

処理が完了するまで待ちます。DashboardはCLIと同じ `system.status.runtime_health` projectionから更新されます。

画面には以下のsectionがあります。

1. `Runtime health` summary line;
2. `Semantic Search readiness`;
3. `Runtime components`;
4. Qdrant lifecycle ownership note;
5. MCP visibility note;
6. `Runtime issues / troubleshooting`;
7. 最下部のraw `system.status` JSON表示。

通常のP-RUNTIME-05 smoke testでは、`Run integrity check` buttonを使用する必要はありません。

## 5. Runtime health summaryを読む

最上部のsummaryは以下の形式で表示されます。

```text
Runtime health: overall=<status> | Semantic Search=<status>
```

この2つのstatusは意図的に異なる意味を持ちます。

- `overall` はruntime-health snapshot全体の状態を要約する;
- `Semantic Search` はsemantic retrievalに必要な依存関係がready、degraded、blocked、unknownのいずれであるかを示す。

したがって、`overall` が `degraded` でも、それだけでSemantic Searchがblockedであるとは限りません。

## 6. Semantic Search readinessを読む

readiness boxには以下のいずれかが表示されます。

```text
READY
DEGRADED
BLOCKED
UNKNOWN
```

意味:

- `READY`: 必須のsemantic runtime依存関係がhealthy;
- `DEGRADED`: semantic依存関係は利用可能だが、warningが存在する;
- `BLOCKED`: 少なくとも1つの依存関係により、安全にreadyと判定できない;
- `UNKNOWN`: runtime-health schemaまたは必須component dataを解釈できない。

現在のreference Workspaceで期待される結果は以下です。

```text
DEGRADED
```

active Search generationが選択されていないこと、またはrendering由来のstateだけがpendingであることを理由に、`BLOCKED` になってはいけません。

## 7. Runtime componentsを読む

Dashboardでは5つのcomponentが個別に表示されます。

### SQLite

reference状態の期待値:

```text
HEALTHY
journal=wal
```

SQLiteがnon-healthyの場合はsemantic hard blockerです。

### Embedding

reference状態の期待値には以下が含まれます。

```text
HEALTHY
microsoft/harrier-oss-v1-0.6b
configured_not_loaded
```

`configured_not_loaded` はshallow health probeでは正常な状態です。embedding runtimeが利用不能という意味ではありません。

### Qdrant

reference状態の期待値:

```text
HEALTHY
http://localhost:6333
ready
v1.19.2
```

Dashboardはobserver専用です。QdrantのStart / Stop / Restart操作を表示してはいけません。

### Search generation

reference状態の期待値:

```text
DEGRADED
active=none (legacy routing)
Knowledge exists but no active Search generation is selected
```

このreference状態では、legacy vector routingを引き続き利用できるため、これはhard semantic blockerではなくwarningとして扱います。

### Derived state

reference状態の期待値:

```text
DEGRADED
current objects=5
unhealthy states=3
```

現在の3件のunhealthy stateは、想定されている `rendering` pending stateです。semantic kindである `search_representation`、`embedding`、`vector_index` はreadyであるため、この状態はwarningとして表示される必要があり、Semantic Searchのhard blockerとして扱ってはいけません。

## 8. Runtime issues / troubleshootingを確認する

troubleshooting boxには、degradedまたはblockedとなっているcomponentの理由が説明されている必要があります。

現在のreference Workspaceでは、以下に関する案内が含まれていることを確認します。

- inactive Search generation / legacy routing;
- incomplete Derived state;
- 必要に応じて確認する対応System tab。

有用なruntime issueが、理由を示さず単に `degraded` とだけ表示されてはいけません。

## 9. Qdrant lifecycle ownershipを確認する

lifecycle noteに、Qdrantは外部所有であり、SGOKBはruntime healthをobserveするだけであることが記載されていることを確認します。

受入済みlifecycle contractは以下です。

```text
qdrant_owner = external
observe      = true
start        = false
stop         = false
restart      = false
```

Runtime Dashboard上にQdrantのStart / Stop / Restart操作が存在してはいけません。

## 10. MCP noteを確認する

Overview画面が、存在しないMCP health stateを作り出していないことを確認します。

noteには、MCP runtime stateは `sgokb.runtime-health/1.0` の一部ではないことが記載され、stdioの起動/configuration contractを確認するため既存の `MCP` tabへ案内される必要があります。

## 11. raw system.status JSONを確認する

`Refresh system status` 実行後、Overview tab最下部にあるread-only JSON領域までscrollします。

raw outputが引き続き表示され、以下を含んでいることを確認します。

```text
"runtime_health"
```

現在のreference Workspaceでは、authoritativeな値として以下が含まれている必要があります。

```text
overall_status          = degraded
sqlite                  = healthy
embedding               = healthy
qdrant                  = healthy
qdrant.ready            = true
qdrant.version          = 1.19.2
generation              = degraded
generation issue        = generation_not_active
derived                 = degraded
derived issue           = derived_state_incomplete
```

structured dashboardとraw JSONは、同じruntime snapshotを表していなければなりません。

## 12. P-RUNTIME-05受入チェックリスト

各項目についてPASS / FAILを記録します。

```text
[ ] GUIが正常に起動する
[ ] reference Workspaceを正常に開ける
[ ] System > Overviewを開ける
[ ] Refresh system statusが完了する
[ ] Runtime health summaryが表示される
[ ] Semantic Search readinessが表示される
[ ] reference WorkspaceでSemantic Search = DEGRADEDとなり、BLOCKEDではない
[ ] SQLite = HEALTHY
[ ] Embedding = HEALTHY
[ ] Qdrant = HEALTHY / ready / v1.19.2
[ ] Search generation = DEGRADED / inactive generationの案内が表示される
[ ] Derived state = DEGRADED / rendering-only warningが表示される
[ ] troubleshooting textにdegradedとなっている理由が説明されている
[ ] Qdrant lifecycle ownerがexternalである
[ ] Qdrant Start / Stop / Restart操作が存在しない
[ ] MCP noteが架空のhealth stateを作らずMCP tabへ案内している
[ ] refresh後もraw system.status JSONが表示される
[ ] structured dashboardがCLI runtime-health snapshotと一致している
```

すべての項目がPASSした場合、以下を報告します。

```text
GUI reference-workspace smoke = PASS
```

いずれかの項目がFAILした場合は、実際に表示されたtextと、FAILしたchecklist項目を記録してください。別のremediation taskを開始しない限り、canonical dataを変更したりmaintenance操作を実行して補正してはいけません。

## 起動時のみのtroubleshooting

`sgokb-gui.exe` が見つからない場合は、まずvirtual environmentとGUI依存関係を確認します。

```powershell
Test-Path .\.venv\Scripts\python.exe
Test-Path .\.venv\Scripts\sgokb-gui.exe
.\.venv\Scripts\python.exe -c "import PySide6; print(PySide6.__version__)"
```

executableが存在しない一方でPySide6を正常にimportできる場合は、以下を使用します。

```powershell
.\.venv\Scripts\python.exe -m sgokb.gui.main
```

実際に起動が失敗し、その原因を特定できた場合を除き、受入試験の一部としてenvironmentを再installしたり変更したりしないでください。

## 関連文書

- `docs/design/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD.md`
- `docs/evaluation/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_ACCEPTANCE.md`
- `docs/planning/phases/P/PHASE_P_STATUS.md`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
