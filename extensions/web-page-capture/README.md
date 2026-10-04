# Web Page Capture Extension

CharacterPageCollector（CPC）向けのWebページ取得を担うChrome拡張機能用サブプロジェクトです。

## 目的

ユーザーがブラウザで内容を確認し、必要な展開操作やJavaScript実行が完了した時点のWebページ状態を、後からCharacterPageCollectorで再解析できるRaw Captureとして保存します。

本機能の責務は**Webページ情報の収集とRaw Captureの保存だけ**です。CPC内部のSource分類、Extractor、Normalization、Evidence、Fragment、DB Schemaなどには依存しません。CPCの設計が将来変更されても、原則として同じWeb Captureを再利用できることを優先します。

## 基本方針

- ユーザーが右クリックメニューから明示的にCaptureしたページだけを取得する。
- HTTP初期HTMLではなく、Capture時点のRendered DOMを主なRaw資料とする。
- 同一URLの複数Captureを許容し、上書きしない。
- Capture形式にExtension Versionとは独立したFormat Versionを持たせる。
- 取得できなかった情報もCapture結果として記録する。
- Capture結果は `extensions/web-page-capture/local-captures/` に保存する。
- 任意フォルダへの保存はChrome Extension単体では行わず、Native Messagingを利用したNative Hostに委譲する。
- CPC localhost APIやCPC本体の起動をCaptureの前提条件にしない。
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

### CharacterPageCollector側の責務

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
- CPC DB更新

これらはCharacterPageCollector本体で行います。

## 保存先

Capture Bundleの標準保存先は以下とします。

```text
CharacterPageCollector/
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

Native Hostの責務は原則として**Capture Bundleを指定保存先へ書き込むことだけ**とし、CPCの解析処理は持たせません。

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

実装時には次の責務分離を目標とします。

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

実装開始時に `package.json`、TypeScript設定、Manifest V3設定、Native Host実装・登録方式等を追加します。ツールチェーンは実装設計時に確定します。

## CPCとの境界

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
CharacterPageCollector
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

CaptureはCPC本体が停止中でも成立する設計とします。
