# SGOKB Project Rename — Codex Handoff / Runbook

更新日: 2026-10-09

関連Decision: `docs/SGOKB_RENAME_DECISION.md`

## 1. 目的

本書は、現行 `CharacterPageCollector` を **Source Grounded Object Knowledge Base (SGOKB)** へBreaking Renameするための実施手順を、Codexへそのまま引き渡せる形で定義する。

RenameはB-02以降へ進む前に完了させる。

この作業では、名称・namespace・distribution・CLI・runtime identifier・Repository名・ローカル配置名をSGOKBへ統一する。一方、Entity→Object、Fragment廃止、新DB schema等の再設計ロジック変更は行わない。

---

## 2. 調査時点で確認した旧名称依存

### 2.1 GitHub / Repository

現在のRepositoryは次の状態である。

- Repository: `tabenishi02/CharacterPageCollector`
- Default branch: `main`
- Knowledge Base redesign branch: `docs/knowledge-base-redesign-tasks`
- Rename planning branch: `docs/sgokb-rename-handoff-v3`

最終Repository名は `tabenishi02/SourceGroundedObjectKnowledgeBase` とする。

### 2.2 Python package / distribution / CLI

`pyproject.toml` には現在次が存在する。

- distribution: `character-page-collector`
- console script: `cpc = "cpc.cli:main"`
- package data namespace: `cpc`
- source package: `src/cpc/`

`src/cpc/` 配下には application / repository / domain / CLI / providers / search / importer / extraction / migrations / prompts等の現行実装がある。

### 2.3 Runtime identifier

現行CLI / providerには少なくとも次の旧prefixが存在する。

- `CPC_DB`
- `CPC_PROMPT_DIR`
- `CPC_RUNTIME_METADATA_JSON`
- `CPC_LLM_MODEL`
- `CPC_LLM_PROVIDER`
- `CPC_LLM_BASE_URL`
- `CPC_LLM_REVISION`
- `CPC_LLM_API_KEY`
- `CPC_LLM_MAX_TOKENS`
- `CPC_LLM_EXTRA_JSON`
- `CPC_LLM_FRAGMENT_EXTRA_JSON`
- `CPC_LLM_FINAL_EXTRA_JSON`
- `CPC_API_TIMEOUT`
- `CPC_EMBED_MODEL`
- `CPC_EMBED_PROVIDER`
- `CPC_EMBED_BASE_URL`
- `CPC_EMBED_REVISION`
- `CPC_EMBED_API_KEY`
- `CPC_EMBED_DOCUMENT_PREFIX`
- `CPC_EMBED_QUERY_PREFIX`
- `CPC_EMBED_MAX_CHARS`

既定DB pathは `.local/cpc.sqlite`。

LLM structured output schema nameに `cpc_response` が存在する。

### 2.4 Tests / scripts

`tests/` には6本のPython test moduleがあり、少なくともfixtureでは `from cpc...` を使用している。

`scripts/` には次の補助scriptがあり、Python import・環境変数・コマンド例の旧名称依存を確認対象とする。

- `Use-Strata.ps1`
- `export_upgrade_review.py`
- `inventory_samples.py`
- `run_evaluation.py`
- `run_speed_preflight.py`
- `run_strata_preflight.py`
- `run_strata_speed_preflight.py`
- `run_upgrade_evaluation.py`

### 2.5 Web Page Capture / Native Messaging

Web Page Capture自体の名称は変更不要。

ただしNative Messaging Hostは現在次のidentifierを使用している。

`com.characterpagecollector.web_page_capture`

この値は次の双方に存在する。

- `extensions/web-page-capture/extension/src/background/native.js`
- `extensions/web-page-capture/native-host/Manage-NativeHost.ps1`
- `extensions/web-page-capture/native-host/host.py`

Windows Registryにも同名keyが登録されるため、source置換だけではRenameが完了しない。

新Host nameは次とする。

`com.sgokb.web_page_capture`

### 2.6 Documentation

現行README、旧要件定義、再設計文書、Prototype文書に `CharacterPageCollector` / `CPC` / `cpc` が多数存在する。

扱いを次の2種類に分ける。

1. **Active documentation**
   - README
   - Knowledge Base redesign Decision / Requirements / Tasks / Handoff
   - 今後の設計文書
   - 現行操作手順

   これらはSGOKBへ更新する。

2. **Historical prototype documentation**
   - Prototype時代の評価結果
   - 速度試験
   - 当時の要件・設計を説明する資料

   歴史的事実を示す旧名称は維持してよい。ただし現行仕様と誤認されないようArchived / Historical表示を付ける。機械的な全置換は禁止する。

---

## 3. Rename target contract

| Old | New |
|---|---|
| `CharacterPageCollector` | `Source Grounded Object Knowledge Base` |
| `CPC` | `SGOKB` |
| Repository `CharacterPageCollector` | `SourceGroundedObjectKnowledgeBase` |
| distribution `character-page-collector` | `source-grounded-object-knowledge-base` |
| package `cpc` | `sgokb` |
| CLI `cpc` | `sgokb` |
| `python -m cpc` | `python -m sgokb` |
| `CPC_*` | `SGOKB_*` |
| `.local/cpc.sqlite` | `.local/sgokb.sqlite` |
| `cpc_response` | `sgokb_response` |
| `com.characterpagecollector.web_page_capture` | `com.sgokb.web_page_capture` |
| `cpc-prototype-*` example aliases | `sgokb-prototype-*` |
| Local repo candidate `C:\codex\CharacterPageCollector` | `C:\codex\SourceGroundedObjectKnowledgeBase` |

旧CLI・旧package・旧environment prefixのcompatibility aliasは作らない。

---

## 4. 実施順序

### R-00 Preflight / baseline

1. `docs/sgokb-rename-handoff-v3` を取得する。
2. working treeがcleanであることを確認する。
3. Rename実装用branchを作る。推奨: `refactor/sgokb-project-rename`。
4. Rename前のtest結果を記録する。
5. `git status`, `git remote -v`, Python version, active venv, Native Host statusを記録する。
6. repository内の旧名称参照を`rg`でinventoryする。
7. `.local/cpc.sqlite` の存在を確認する。存在する場合は後述のDB migration対象とする。
8. Persistent `CPC_*` environment variableの**名前だけ**を確認する。secret valueをlogへ表示しない。
9. Native Messaging Host旧登録の有無を確認する。

推奨baseline commands:

```powershell
git status --short
git remote -v
python --version
python -m pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
git diff --check
rg -n -i "CharacterPageCollector|character-page-collector|characterpagecollector|\bCPC\b|\bcpc\b|CPC_|cpc_response|cpc-prototype" .
```

`rg`結果は自動置換用ではなく影響範囲inventoryとして利用する。

### R-01 Python package namespace rename

`git mv src/cpc src/sgokb` を基本とする。

以下を更新する。

- package-internal imports
- testsの`from cpc...` / `import cpc...`
- scriptsの`cpc` import
- dynamic importやmodule name文字列があれば更新

この段階ではロジックを変更しない。

### R-02 Packaging / CLI rename

`pyproject.toml` を更新する。

- `[project].name = "source-grounded-object-knowledge-base"`
- `[project.scripts] sgokb = "sgokb.cli:main"`
- `[tool.setuptools.package-data] sgokb = [...]`

旧 `cpc` entry pointは残さない。

Editable installで旧distributionが残留しないよう、使用中venvで次を行う。

```powershell
python -m pip uninstall -y character-page-collector
python -m pip install -e '.[dev]'
```

その後、次を確認する。

```powershell
python -m sgokb --help
sgokb --help
python -m pip show source-grounded-object-knowledge-base
python -m pip show character-page-collector
```

最後の旧distributionは見つからないこと。

`python -m cpc` および `cpc` commandが新venvから提供されないことも確認する。

### R-03 Runtime environment rename

すべての`CPC_*`読込を`SGOKB_*`へ置換する。

旧prefix fallbackは実装しない。

少なくともSection 2.3の環境変数を対象とする。

error messageやREADME exampleも新prefixへ更新する。

`cpc_response` は `sgokb_response` へ変更する。

Example-only local model identifier `cpc-prototype-*` は現行手順内では `sgokb-prototype-*` とする。

Persistent User/Machine environmentに`CPC_*`が存在する場合:

1. valueを画面・logへ表示しない。
2. 同名suffixの`SGOKB_*`へvalueを移す。
3. SGOKB側で動作確認後、旧`CPC_*`を削除する。
4. secretをcommitしない。

### R-04 Default DB rename / local data preservation

code上の既定DBを `.local/sgokb.sqlite` へ変更する。

既存 `.local/cpc.sqlite` が存在する場合、Raw file copyだけで移行せずSQLite backup API等を使用して安全に複製する。

推奨条件:

- CPC/SGOKB processがDBへ書き込み中でないこと。
- `.local/rename-backup/` を作成し、必要ならrename前backupを保持する。
- 新DBに対して `PRAGMA integrity_check` が`ok`。
- `PRAGMA foreign_key_check` が0件。
- 主要table countが一致する。
- 上記確認後に旧active DBを除去する。

Object / Source / Snapshot / Evidence等のstable IDは変更しない。

DB schema内にproject-name由来のidentifierがあるか調査し、単なる表示metadataであればSGOKB化するが、Identityを書き換えない。

### R-05 Native Messaging Host rename

新Host name:

`com.sgokb.web_page_capture`

更新対象:

- extension `HOST_NAME`
- native host Python constant
- PowerShell registry key
- generated native host manifest `name`
- docs/tests

旧Windows Registry keyを残さない。

安全な移行手順:

1. Rename前または旧identifierを知っている状態で旧Host `Status` を確認する。
2. 既存 `.local/host-manifest.json` の`allowed_origins`からExtension IDを取得可能なら控える。
3. 旧HostをUninstallする。
4. sourceを新Host nameへ変更する。
5. 最終的なunpacked Extension pathでExtension IDを確認する。
6. 新HostをInstallする。
7. `Status`確認。
8. Chromeから実Captureを1件実施しNative Messagingが成功することを確認する。

注意: unpacked Chrome Extensionは絶対path変更によりExtension IDが変わる可能性がある。ローカルrepository directoryを後でRename/Recloneする場合、**最終pathへ移動後のExtension IDでNative Hostを再登録する**。

### R-06 Tests / scripts / benchmark identifiers

`tests/` 全6 moduleと`scripts/`全8 fileを確認する。

変更対象:

- imports
- subprocess command
- module invocation
- environment variable name
- default path
- expected error text
- fixture / temporary pathに旧project identifierが使われていればSGOKBへ変更

ただしFragment/Final等のPrototypeロジックそのものは今回変更しない。

### R-07 Active documentation rename

次は現行文書としてSGOKB名へ更新する。

- README
- Knowledge Base redesign Decision
- Asset Classification
- Dependency Inventory
- Purpose Requirements
- Redesign Handoff
- Redesign Tasks
- Rename Decision / Handoff
- その他、今後の仕様として扱われている文書

B-01 Purpose Requirementsは、正式名称を`Source Grounded Object Knowledge Base`へ更新する。

`CPC` / `CPC→UPDS` / `CPC Knowledge`等の現行表現はそれぞれ`SGOKB`へ更新する。

Historical Prototype資料では旧名称を保持できるが、現行仕様と誤認しない表示を追加する。

### R-08 Repository-internal old-name scan

変更後、少なくとも以下を実行する。

```powershell
rg -n -i "CharacterPageCollector|character-page-collector|characterpagecollector|\bCPC\b|\bcpc\b|CPC_|cpc_response|cpc-prototype" .
```

ヒットを次の3種へ分類する。

1. **ERROR** — active code/config/docsに残った旧名称
2. **ALLOWED-HISTORICAL** — Prototype資料やRename/Migration説明に必要な旧名称
3. **FALSE POSITIVE** — 一般語等

ERRORは0件にする。

`src/cpc` directoryが存在しないことも確認する。

### R-09 Functional verification

最低限次を実行する。

```powershell
python -m pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
git diff --check
python -m sgokb --help
sgokb --help
python -m sgokb status
```

既存Sample / deterministic evaluationでRename前と同等にImport / Processできることも確認する。

可能ならWeb Page Capture unit testも実行する。

```powershell
Push-Location extensions/web-page-capture
npm test
Pop-Location
```

Native Host実機acceptanceはR-05に従う。

### R-10 GitHub Repository rename

code/doc rename・testsが通った後に実施する。

Repository:

`tabenishi02/CharacterPageCollector`

から

`tabenishi02/SourceGroundedObjectKnowledgeBase`

へRenameする。

GitHub CLIを使用できる場合の候補:

```powershell
gh repo rename SourceGroundedObjectKnowledgeBase --repo tabenishi02/CharacterPageCollector --yes
```

実行後にRepository metadataとbranchが保持されていることを確認する。

GitHubの旧URL redirectだけへ依存せず、local remoteを新URLへ明示的に更新する。

```powershell
git remote set-url origin https://github.com/tabenishi02/SourceGroundedObjectKnowledgeBase.git
git remote -v
git fetch origin
```

README内のGitHub URLやbadge等も新URLへ更新する。

### R-11 Local repository directory migration

推奨最終path:

`C:\codex\SourceGroundedObjectKnowledgeBase`

Windows上でactive VS Code / terminal / Codex processが旧directoryを掴んでいる場合、in-place renameは失敗しやすい。その場合は無理に削除せず次の方式を優先する。

1. 新GitHub URLから新pathへclone。
2. Git管理外の必要データを安全に移行する。
3. `.local` DBはR-04の検証済みSGOKB DBを利用する。
4. unpacked Extensionを新pathから読み直す。
5. 新Extension IDに合わせNative Hostを再登録する。
6. tests / capture acceptanceを再実行する。
7. 新pathで問題ないことを確認してから旧cloneを削除する。

Codex実行環境自身が旧workspaceに固定されていて最終folder削除だけ不可能な場合は、そこで作業を失敗扱いにせず、残り1手として正確なcommandを報告する。

### R-12 External reference check

Repository外の既知integrationについて、旧URL/path/identifierが残っていないか確認する。

対象例:

- VS Code workspace / recent project configuration
- PowerShell profileやプロジェクト用script
- `C:\codex` 配下の他Repositoryからの直接参照
- Task Scheduler等に旧local pathが登録されている場合
- ChatGPT Project等の表示名（Codexから変更できない場合は手動項目として報告）

無関係なUser directory全体を無差別検索しない。既知の開発領域・integrationだけを対象とする。

---

## 5. Commit / PR strategy

Renameと再設計ロジック変更を混在させない。

推奨commit分割:

1. `docs: record SGOKB rename decision and handoff`
2. `refactor: rename Python package cpc to sgokb`
3. `refactor: rename SGOKB runtime identifiers and CLI`
4. `refactor: rename native messaging host`
5. `docs: rename active project documentation to SGOKB`
6. `test: verify SGOKB rename baseline`

`git mv`主体のmoveと内容変更を可能な範囲で分け、Git historyを追跡しやすくする。

GitHub Repository Renameはtests通過・push完了後に行う。

---

## 6. 明示的に今回行わないこと

次はRename作業へ混ぜない。

- Entity → Object実装変更
- Fragment table/code削除
- Final Document廃止
- Object schema新設
- Google Drive exchange実装
- MCP実装
- Embedding backend変更
- 新Retrieval algorithm実装
- Prototype architectureの機能的改修

これらはRename完了後のB-02以降または該当Phaseで扱う。

---

## 7. Acceptance criteria

以下をすべて満たした時点でRename完了とする。

- [x] 正式名称が`Source Grounded Object Knowledge Base`、略称が`SGOKB`。
- [x] GitHub Repositoryが`SourceGroundedObjectKnowledgeBase`。
- [x] `src/sgokb`が正本packageであり`src/cpc`が存在しない。
- [x] distributionが`source-grounded-object-knowledge-base`。
- [x] `sgokb` CLIと`python -m sgokb`が動作する。
- [x] 旧`cpc` CLI/package互換aliasを提供していない。
- [x] active runtime environment prefixが`SGOKB_*`のみ。
- [x] default DBが`.local/sgokb.sqlite`。
- [x] 既存DBがある場合、内容・stable IDsを保持して安全に移行済み。
- [x] Native Hostが`com.sgokb.web_page_capture`。
- [x] 旧Native Host registry keyが残っていない。
- [x] Web Page CaptureからNative Messaging実Captureが成功する。
- [x] active docsがSGOKB表記へ更新済み。
- [x] historical docs以外の旧名称scan ERRORが0件。
- [x] Python tests成功。
- [x] Ruff / `git diff --check`成功。
- [x] Web Page Capture tests成功。
- [x] `origin`が新GitHub URL。
- [x] local working pathを移す場合、新pathで再検証済み。
- [x] Renameに無関係な再設計ロジック変更が混入していない。

---

## 8. Codex完了報告フォーマット

Codexは作業完了時に次を報告する。

```text
SGOKB Rename Result

1. Repository
- old:
- new:
- branch:
- PR/commit:

2. Source rename
- package:
- distribution:
- CLI:
- environment prefix:
- DB default:
- Native Host:

3. Data migration
- existing DB found: yes/no
- migration method:
- integrity_check:
- foreign_key_check:
- stable ID preservation:

4. Verification
- pytest:
- ruff:
- format check:
- git diff --check:
- web-page-capture tests:
- native host acceptance:
- old-name scan ERROR count:

5. External/local migration
- origin URL:
- local directory:
- Extension ID:
- remaining manual action:

6. Out-of-scope confirmation
- Entity/Object redesign performed: no
- Fragment/Final redesign performed: no

7. Remaining issues
- none / details
```

残作業がある場合、「完了」とせず、何が自動実行できなかったかと次の1手を具体的に記述する。

## 9. 実施記録（2026-10-09）

実装branch: `refactor/sgokb-project-rename`。R-00〜R-12の名称変更と新配置での受入確認を実施した。B-02以降には進んでいない。

### Source / runtime

- `git mv`でpackageを移動し、imports・distribution・CLI・環境変数・既定DB・structured-output名・Native Hostを更新した。互換aliasと旧prefix fallbackは提供していない。
- 使用中venvから旧distributionをuninstallし、残った旧egg-infoを除去した。新配置にはvenvを再作成し、新distributionをeditable installした。両環境で旧package/CLI/distributionが提供されないことを確認した。
- 旧venv内の追加依存`lmstudio==1.5.0`、`httpx-ws==0.9.0`、`msgspec==0.22.0`も新venvへ同版で導入した。両環境に共通するAnyIO 4.8.0との既存SDK import不整合（`AsyncContextManagerMixin`不足）を確認した。この依存不整合の修正は名称変更対象外であり、provider testsは8件成功している。
- 実User/Machine environmentに旧prefixは存在しなかった。値をログに表示していない。
- 名称を逆変換したPython ASTの比較で、28ファイルに名称以外の差分がないことを確認した。既存SQL migrationは不変。

### Data / local placement

- 旧既定DBは存在しなかった。新既定DBをstatusコマンドで作成・確認した。
- Git管理外の約11.48 GB・4,374ファイルを新cloneへ移行した。既存20 SQLite DBはbackup APIで複製し、全table件数・全primary keyのdigest一致、`integrity_check=ok`、FK違反0件を確認した。
- 新cloneのDBでは、旧clone配下の絶対Raw pathだけを新配置へ移した。永続ID・Raw・Fragment・Final等の内容は変更していない。主要DBの106 Raw参照は実ファイルのchecksumと一致した。
- 既存SampleのRename前後比較では、1 Source / 1 Snapshot / 1 normalization / 57 Evidence / 1 Page Contextが一致し、Evidence本文・metadata、Capture由来Snapshot ID、Rawの不変を確認した。
- 旧ローカルmainに存在する未push 11 commitsは、新cloneの`archive/pre-rename-local-main`に保全した。旧feature branchesもローカルに保全した。

### Verification

- 新配置で`python -m pytest -q`: **71 passed**。
- `ruff check src tests scripts`、`ruff format --check src tests scripts`、`git diff --check`: **成功**。
- `python -m sgokb --help`、`sgokb --help`、`python -m sgokb status`: **成功**。
- Web Capture `npm test`: **8 passed**。Native Host Python tests: **22 passed / 8 subtests passed**。
- 最終pathからChrome Extensionを読み込み、そのExtension IDでNative Hostを登録した。実ユーザーRegistryで新Hostの登録・manifest・launcherを確認し、旧keyを削除した。
- Chrome 154で実DOM/MHTMLを本番context-menu handlerとNative Messagingを通して保存し、ZIP検証と別受入DBへのImport/Processに成功した。この自動確認では物理的な右クリックは未観測だった。
- 続いてユーザーが普段使うChromeで新pathから再読込し、右クリックCaptureの成功を報告した。追加ZIPをHost/Importer双方で検証し、Main DOM/MHTMLの成功を確認した。
- 旧名称scanは**ERROR 0件**。Rename説明・明示したHistorical資料・過去のbranch名だけをALLOWED-HISTORICALとした。FALSE POSITIVEは0件。分類一覧と実データ受入記録はGit管理外`.local/`に保持した。

### Repository / external check

- Repositoryを`tabenishi02/SourceGroundedObjectKnowledgeBase`へRenameした。Repository ID・default branchと既存branchのcommit SHAを保持し、originを新URLへ明示更新した。実装branchをpush済み。
- 中間handoff / handoff-v2にはv3に未包含のcommitが0件だったため、両remote branchを削除した。
- 旧path/identifierを参照するScheduled Taskと既知PowerShell profileはなかった。他RepositoryではUPDSの2文書に旧表示名、Backfill/Numpadの過去記録に旧名称があるが、今回の運用URL/path登録の参照ではない。別Repositoryの文書・履歴は変更していない。
- VS Code / Codexの現在のworkspaceは旧cloneを使用中。ChatGPT Project表示名は確認・変更できていない。

### 最後の手動作業

新配置でのtests・データ移行・Native Host・ユーザー実Captureは確認済み。使用中workspaceの削除は実施しない。セッションを閉じ、新配置を開いた後で、別のPowerShellから次を実行する。

```powershell
Set-Location C:\codex
$legacyClone = (Resolve-Path -LiteralPath 'C:\codex\CharacterPageCollector').Path
if ($legacyClone -ne 'C:\codex\CharacterPageCollector') { throw 'Unexpected legacy clone path' }
Remove-Item -LiteralPath $legacyClone -Recurse -Force
```

旧cloneの片付けまで含めた全作業の終了は、この最後の1手の後となる。
