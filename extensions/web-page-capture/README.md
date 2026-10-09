# Web Page Capture Extension

Source Grounded Object Knowledge Base（SGOKB）向けのWebページ取得を担うChrome拡張機能用サブプロジェクトです。

## 目的

ユーザーがブラウザで内容を確認し、必要な展開操作やJavaScript実行が完了した時点のWebページ状態を、後からSource Grounded Object Knowledge Baseで再解析できるRaw Captureとして保存します。

本機能の責務は**Webページ情報の収集とRaw Captureの保存だけ**です。SGOKB内部のSource分類、Extractor、Normalization、Evidence、Fragment、DB Schemaなどには依存しません。SGOKBの設計が将来変更されても、原則として同じWeb Captureを再利用できることを優先します。

## 基本方針

- ユーザーが右クリックメニューから明示的にCaptureしたページだけを取得する。
- HTTP初期HTMLではなく、Capture時点のRendered DOMを主なRaw資料とする。
- 同一URLの複数Captureを許容し、上書きしない。
- Capture形式にExtension Versionとは独立したFormat Versionを持たせる。
- 取得できなかった情報もCapture結果として記録する。
- Capture結果は `extensions/web-page-capture/local-captures/` に保存する。
- 任意フォルダへの保存はChrome Extension単体では行わず、Native Messagingを利用したNative Hostに委譲する。
- SGOKB localhost APIやSGOKB本体の起動をCaptureの前提条件にしない。
- Cookie、認証Token、LocalStorage等の資格情報・ブラウザ状態は収集対象にしない。
- Popup、Options画面、Side Panel等の常設UIは持たない。
- 成功・失敗は通知のみでユーザーへ返す。

## 操作フロー

```text
Webページを閲覧
      ↓
必要な範囲をユーザーが展開
      ↓
右クリック
      ↓
「このページをキャプチャ」
      ↓
Chrome Extensionが現在ページを取得
      ↓
Web Capture Bundleを生成
      ↓
Native Hostへ保存依頼
      ↓
extensions/web-page-capture/local-captures/
      ↓
成功 / 失敗通知
```

## 責務境界

### Web Page Capture側の責務

- Rendered DOM取得
- URL / title / capture timestamp取得
- HTML metadata取得
- JSON-LD等のstructured metadata取得
- iframe / frame情報の取得
- open Shadow DOM情報の取得
- MHTML等のRaw補助Archive取得
- Capture completeness / warning記録
- Web Capture Bundle生成
- Native Hostを通じた指定ローカルディレクトリへの保存
- 成功 / 失敗通知

### Source Grounded Object Knowledge Base側の責務

以下は初期版だけでなく、**将来的にもWeb Page Capture Extensionの機能領域には含めません**。

- 本文抽出
- 広告・ナビゲーション等の不要情報除去
- Source Type判定
- Site判定
- Wikipedia等のサイト固有判定
- Entity判定
- Normalization
- Evidence生成
- Fragment生成
- LLM処理
- Embedding
- RAG
- SGOKB DB更新

これらはSource Grounded Object Knowledge Base本体で行います。

## 保存先

Capture Bundleの標準保存先は以下とします。

```text
SourceGroundedObjectKnowledgeBase/
└─ extensions/
   └─ web-page-capture/
      └─ local-captures/
         └─ *.webcapture.zip
```

`local-captures/` は実サイトの内容、ログイン後ページ、著作物等を含む可能性があるためGit管理対象外とします。

## Native Host

Chrome Extensionはセキュリティ上、Windows上の任意フォルダへ自由に書き込めません。

そのため、Chrome公式のNative Messagingを利用し、Windows上で動作する小さなNative Hostへ保存処理を委譲します。

```text
Chrome Extension
      ↓ Native Messaging
Native Host
      ↓
local-captures/
```

Native Hostの責務は原則として**Capture Bundleを指定保存先へ書き込むことだけ**とし、SGOKBの解析処理は持たせません。

## UI方針

常設UIは設けません。

```text
User Interaction:
  右クリックメニュー

Feedback:
  成功通知
  失敗通知

Popup UI:
  なし

Options UI:
  なし

Side Panel:
  なし
```

## 目標ディレクトリ構成

次の責務分離で実装しています。

```text
web-page-capture/
├─ README.md
├─ .gitignore
├─ docs/
│  ├─ DESIGN.md
│  ├─ CAPTURE_BUNDLE_FORMAT.md
│  └─ NATIVE_HOST.md
├─ extension/
│  ├─ src/
│  │  ├─ background/
│  │  ├─ capture/
│  │  └─ shared/
│  └─ public/
│     └─ icons/
├─ native-host/
│  └─ ...
├─ tests/
│  ├─ unit/
│  └─ fixtures/
└─ local-captures/        # Git管理外
```

拡張機能はES ModulesのJavaScriptで実装し、ビルドは不要です。Python 3.10以降の標準ライブラリで保存Hostを実装し、Windows標準の.NET Framework C# compilerで小さな起動用Executableを生成します。SGOKB、localhost Server、管理者権限は不要です。Node.js 22.13以降とnpmは自動テスト時のみ必要です。jsdomはテスト専用依存です。

## 導入・利用（Windows 11 / Chrome 116以降）

1. `chrome://extensions` でデベロッパーモードを有効にする。
2. 「パッケージ化されていない拡張機能を読み込む」で、このディレクトリ内の `extension/` を選択する。
3. 表示された32文字の拡張機能IDを控える。
4. このディレクトリをカレントディレクトリにして、PowerShellで次を実行する。

```powershell
.\native-host\Manage-NativeHost.ps1 -Action Install -ExtensionId <拡張機能ID>
.\native-host\Manage-NativeHost.ps1 -Action Status
```

必要なら `-PythonPath <python.exeのパス>` を指定します。実行ポリシーでブロックされる場合は、内容を確認したうえで `powershell -NoProfile -ExecutionPolicy Bypass -File .\native-host\Manage-NativeHost.ps1 -Action Install -ExtensionId <拡張機能ID>` を使用してください。

5. 通常のWebページを開き、必要な内容を展開してから右クリック →「このページをキャプチャ」。画像・リンク上からでもページ全体を対象にする。
6. 通知を確認し、`local-captures/` のZIPを展開して `capture/manifest.json` を確認する。

ファイルページのFixtureを試す場合はChromeの拡張機能詳細で「ファイルのURLへのアクセスを許可する」を有効にしてください。通常のHTTP/HTTPSページでは不要です。通知が出ない場合はWindowsとChromeの通知設定を確認します。リポジトリの移動、Pythonの移動、Extension IDの変更後はInstallを再実行します。

```powershell
.\native-host\Manage-NativeHost.ps1 -Action Uninstall
```

アンインストールは現在ユーザーのRegistry登録だけを解除し、Captureは保持します。拡張機能は `chrome://extensions` から削除できます。`.local/` は実設定・生成Executableを含むGit管理外のディレクトリです。PrepareはRegistryを変更せずにHostの準備だけを行います。

## テストと受入

このディレクトリで実行します。

```powershell
npm ci --cache .local/npm-cache
npm test
python -m unittest discover -s tests/unit -p "test_*.py"
```

ChromeとNative Hostの実機結合は自動テストのみでは確認できません。[手動受入試験](docs/MANUAL_ACCEPTANCE.md)に従ってWindows 11 + Chromeで確認してください。実機試験が終わるまでmainへマージしません。

## 保存範囲と制約

MHTMLは毎回取得を試み、失敗時もMain DOMが取得済みなら部分Captureとして保存します。Main DOM取得失敗、途中のページ遷移、Host接続失敗、保存失敗は失敗通知となり、正式Bundleを保存しません。

同一オリジンでアクセス可能なFrameを再帰的に保存します。クロスオリジンやsandboxで取得できないFrameはその要素・URL・親子関係と状態を保持します。その内部のFrame構造は不明です。open Shadow DOMは入れ子を含めて別Artifactに保持します。closed Shadow DOMの有無は判定できないため、完全取得は保証せず `shadow_dom` と全体のcompletenessは `partial` です。

DOMとMHTMLは順に取得するため完全に同時ではありません。取得中の動的変更、同一URLへの再読み込み、canvas等の描画状態は完全には再現できません。Raw DOMとMHTMLに既に埋め込まれた機密情報は保存され得るため、Bundleは公開しないでください。ブラウザの資格情報・ストレージAPIにはアクセスせず、フォームのproperty値を書き戻しません。

## SGOKBとの境界

```text
Chrome
  ↓
右クリックCapture
  ↓
Web Page Capture Extension
  ↓
Web Capture Bundle
  ↓
Native Host
  ↓
local-captures/
  ↓
──────── 責務境界 ────────
  ↓
Source Grounded Object Knowledge Base
  ↓
Importer
  ↓
Source / Snapshot
  ↓
Extractor / Normalization
  ↓
Evidence
  ↓
Fragment
```

CaptureはSGOKB本体が停止中でも成立する設計とします。
