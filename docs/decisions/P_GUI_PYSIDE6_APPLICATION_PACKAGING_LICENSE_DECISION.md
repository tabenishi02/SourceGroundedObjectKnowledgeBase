# P-GUI PySide6 Application / Packaging / License Decision

Updated: 2026-10-28

- Status: **Accepted / P-GUI-02**
- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-02 [P0] PySide6 application architecture / packaging / license design`
- Requirements: `docs/requirements/GUI_REQUIREMENTS.md`
- Compatibility contract: `docs/decisions/P_GUI_COMPATIBILITY_AND_SAFETY_CONTRACT.md`
- Review basis: `docs/evaluation/P_GUI_02_PYSIDE6_ARCHITECTURE_PACKAGING_LICENSE_REVIEW.md`
- Detailed design: `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`

---

## 1. Decision

SGOKB Desktop GUIの正式baselineを次で固定する。

```text
GUI framework        = PySide6 / Qt for Python
UI technology        = Qt Widgets
Process model        = one SGOKB GUI process
Presentation thread  = Qt main thread
Backend execution    = serialized QObject worker on dedicated QThread
Repository ownership = per-operation Repository, created and closed on worker thread
Business boundary    = CLI / GUI share Application / Service layer
GUI->CLI subprocess  = prohibited as primary business boundary
Direct GUI SQL       = prohibited as public/canonical operation boundary
Windows packaging    = pyside6-deploy / Nuitka
Packaging mode       = standalone directory
Qt linking           = dynamic / separate Qt shared libraries
One-file executable  = not initial baseline
CLI installation     = remains possible without PySide6
```

---

## 2. UI technology

Qt Widgetsをprimary UI technologyとする。

理由:

- SGOKBはtable / tree / list / form / dialog / master-detail中心のDesktop operator applicationである。
- Qt WidgetsはQt公式上、複雑なdesktop application向けのmature / feature-rich UI technologyである。
- Model/View (`QAbstractItemModel`, `QTableView`, `QTreeView`, proxy model等) がSGOKBの大量Object / Source / Evidence表示に適する。
- QML / Qt Quickを追加するとpresentation technologyとdeployment surfaceが増えるが、現時点のSGOKB要件では必要性がない。

Qt Quick / QMLはcore GUI baselineに含めない。

---

## 3. Application boundary

P-GUI-01のsemantic parity contractを維持し、CLIとGUIをpeer presentation adapterとする。

```text
              ┌─ CLI presentation
              │
              ├─ GUI presentation (PySide6)
              │
              └─ MCP read presentation
                       │
                       ▼
              Application / Service
                       │
                       ▼
       Repository / Retrieval / Exchange
```

Rules:

1. domain / storage / retrieval / exchange layerはPySide6をimportしない。
2. GUI controllerはCLI parser / stdout JSONをbusiness APIとして使用しない。
3. GUIからcanonical SQLiteへ独自SQLで書き込まない。
4. CLI-only composition logicが必要ならP-GUI-03でtransport-neutral layerへ抽出する。
5. CLIはPhase P後もfirst-class / headless interfaceとして維持する。

---

## 4. Threading / operation execution

### 4.1 Qt main thread

Qt main threadは次のみを所有する。

- Widgets
- presentation models
- controllers / view state
- navigation
- dialogs
- progress / error rendering

blocking I/O、SQLite operation、embedding、Qdrant、backup/restore等をmain threadで実行しない。

### 4.2 Backend worker

backend executionにはQtのworker-object patternを採用する。

```text
BackendWorker(QObject)
    moveToThread(backend_thread)
```

GUIからoperation requestをqueued signalで渡し、result / progress / warning / errorをsignalsでmain threadへ返す。

### 4.3 Repository ownership

current `Repository`は通常の`sqlite3.connect(path)`でconnectionを作成するため、connectionのthread affinityを維持する。

各operationはbackend thread内で:

```text
open Repository
  -> compose required Application / Service
  -> execute
  -> commit/rollback through existing service semantics
  -> close Repository
```

とする。

`check_same_thread=False`で1 connectionを共有する方式は採用しない。

### 4.4 Serialization

初期GUIではWorkspaceごとにbackend canonical operation laneを1本とし、operationを順序実行する。

parallel readsは将来拡張候補とするが、P0 baselineでは採用しない。

### 4.5 Cancellation

canonical operationを`QThread.terminate()`等で強制中断しない。

cancel可能性はoperation contractに明示し、cooperative cancellation pointを持つserviceだけをcancel可能として表示する。

---

## 5. Runtime lifetime

高コストなEmbedding provider等はbackend worker session内でlazy cache可能とする。

Repository connectionとはlifetimeを分離する。

```text
BackendSession
├─ workspace path / runtime config
├─ lazy embedding provider
├─ lazy vector runtime
└─ per-operation Repository connections
```

Workspace切替時はin-flight operationの終了/中止可能性を処理した後、旧sessionをdisposeする。

P-GUI-03でfactory interfaceを確定する。

---

## 6. Python package surface

planned package surface:

```toml
[project.optional-dependencies]
gui = ["PySide6>=6.12,<6.13"]

[project.scripts]
sgokb = "sgokb.cli:main"

[project.gui-scripts]
sgokb-gui = "sgokb.gui:main"
```

Rules:

- base installにPySide6を強制しない。
- CLI-only environmentは従来どおりQtなしで成立する。
- GUI source installは`.[gui]`を明示する。
- packaged applicationではGUI launcherを`SGOKB`として配布可能だが、Python package entrypoint名は`sgokb-gui`とする。

PySide6 versionはminor lineをbounded rangeとして管理し、packaged releaseではexact versionをmanifestへ記録する。

---

## 7. Windows packaging

Qt公式推奨の`pyside6-deploy`をbaselineとする。

`pyside6-deploy`はNuitka wrapperとして利用し、Windows x64でbuildする。

Baseline:

```text
mode = standalone
```

`onefile`は採用しない。

理由:

- LGPL library replacement / inspectionを説明しやすい。
- bundled component inventoryが明確になる。
- crash / plugin / DLL troubleshootingが容易。
- first OSS releaseに単一EXEの利便性は必須ではない。

initial acceptance artifactはinstallerを必須とせず、standalone directoryをZIP化したportable distributionを正式baselineとする。

Installer / code signing / auto-updateは別Task/Releaseで必要性を判断する。

---

## 8. Build reproducibility

正式distribution buildは次を満たす。

1. clean virtual environment
2. Python version記録
3. exact PySide6 / Qt version記録
4. exact deployment / Nuitka version記録
5. source commit記録
6. output hash記録
7. release build dependenciesを事前installして固定
8. `pyside6-deploy --no-install`相当を使用し、release build中のuncontrolled installを避ける
9. `pysidedeploy.spec` / deployment intentをversion controlする

`pyproject.toml`には高レベルdeployment intentを置くことを許可する。

---

## 9. LGPL / third-party license decision

PySide6 / Qt Community EditionはLGPLv3/GPLv3等のopen-source licenseで提供される。

SGOKBではLGPLv3条件を満たすdynamic-library distributionをbaselineとする。

Release artifactには最低限次を含める。

```text
LICENSES/
THIRD_PARTY_NOTICES.md
BUILD_MANIFEST.json
Qt/PySide6 source availability or written-offer instructions
```

Release gate:

- bundled Qt moduleのlicenseを確認する。
- LGPL license copyを同梱する。
- Qt/PySide6利用を明示する。
- bundled third-party noticesを同梱する。
- corresponding sourceの提供/取得方法をrelease artifactで持続的に案内する。
- LGPL library replacement/relinkingを妨げない。
- Qt/PySide6のmodified sourceがある場合は対応sourceを提供する。
- static Qt linkingを行わない。

新規Qt module追加時はlicense reviewを必須とする。

---

## 10. Project-level OSS license boundary

現時点のrepositoryにはroot `LICENSE` fileが存在しない。

したがって、SGOKB application自身のOSS licenseはP-GUI-02では未確定とする。

```text
private development     = proceed
public OSS distribution = blocked until project license Decision
```

public release前に別Decisionでapplication licenseを選び、root `LICENSE`を追加する。

P-GUI-02はPySide6/Qtの利用可能性と配布要件を確定するTaskであり、SGOKB本体licenseを暗黙にMIT / Apache-2.0 / GPL等へ決めない。

---

## 11. Qt module policy

初期approved baseline:

```text
QtCore
QtGui
QtWidgets
```

必要な標準Qt moduleを追加する場合も、deployment/license inventoryへ明示する。

特にQt WebEngine / Multimedia等の大型optional moduleはconvenienceだけを理由に追加しない。

Markdown / rich text previewの初期baselineはQt Widgets内のtext renderingで実現し、browser engineを要求しない。

---

## 12. GUI settings boundary

QSettings等に保存可能なのはpresentation stateのみとする。

Allowed examples:

- recent DB paths
- window geometry
- dock state
- column size/order
- selected tabs
- presentation-only saved filters

Canonical Knowledge / Source / Evidence / Result / Registry decisionをGUI settingsへ保存して正本化しない。

credential保存は別security designなしでは行わない。

---

## 13. Required implementation follow-up

P-GUI-03:

- CLI composition logicのaudit
- shared Application factories
- operation request/result/error DTO
- semantic runtime composition extraction
- version/show等のCLI-local read logic抽出

P-GUI-04以降:

- `gui` optional dependency
- GUI entrypoint
- Qt shell
- BackendWorker
- Workspace handling
- packaged smoke test

---

## 14. Supersession / change control

このDecisionはP-GUI-02完了時点のPhase P GUI architecture baselineである。

次を変更する場合は明示的なDecision amendmentを要求する。

- Qt Widgets -> Qt Quick primary変更
- subprocess CLI wrapper primary化
- shared SQLite connection跨ぎthread方式
- onefileを正式distribution baseline化
- static Qt linking
- PySide6 major/minor baseline変更（implementation incompatibility等の理由を記録）
- public releaseでのLGPL compliance方式変更
