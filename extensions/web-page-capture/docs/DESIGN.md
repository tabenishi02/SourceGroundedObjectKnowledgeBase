# Web Page Capture Extension 設計方針

## 1. 位置づけ

本機能はCharacterPageCollector（CPC）のWeb Browser Capture部分を独立させた取得コンポーネントとする。

目的は「現在のCPCが必要とする情報を生成すること」ではなく、ユーザーが確認したWebページ状態を、将来のCPC設計変更後でも再解釈できるRaw Captureとして保存することである。

Web Page Capture側の責務は**取得と保存まで**とする。CPC固有のSource Type、site分類、Entity、Extractor、Normalization、Evidence、Fragment、Embedding、DB Schema等をCapture時に確定しない。

## 2. 設計原則

| ID | 原則 |
|---|---|
| CAP-01 | ユーザーが右クリックメニューから明示的に保存したページだけを取得する。 |
| CAP-02 | HTTP初期HTMLではなく、保存操作時点のRendered DOMを取得する。 |
| CAP-03 | Raw Captureでは本文抽出や不要情報除去を行わない。 |
| CAP-04 | CPC固有の分類・DB Schema・Extractorへ依存しない。 |
| CAP-05 | 同一URLの複数Captureを別Captureとして保持する。 |
| CAP-06 | Capture形式にExtension Versionとは独立したFormat Versionを持たせる。 |
| CAP-07 | 一部取得不能の場合も失敗箇所を明示してCapture自体を保持できる。 |
| CAP-08 | CPC localhost APIやCPC本体の起動をCaptureの前提条件としない。 |
| CAP-09 | Cookie、認証Token等の認証情報は収集しない。 |
| CAP-10 | Capture後の解析・加工・解釈はCPC本体へ委譲する。 |
| CAP-11 | Capture BundleはNative Host経由でプロジェクト内のlocal-capturesへ保存する。 |
| CAP-12 | 常設UIを持たず、右クリックメニューと成功・失敗通知だけをユーザー接点とする。 |
| CAP-13 | CPC本体の解析機能を将来もWeb Page Captureへ取り込まない。 |

## 3. 標準Captureフロー

```text
ユーザーがChromeでページを閲覧
        ↓
必要な「もっと見る」・返信・折りたたみ等を展開
        ↓
右クリック
        ↓
「このページをキャプチャ」
        ↓
ExtensionがRendered DOM / metadata / structured data等を収集
        ↓
Capture結果・取得不能情報を記録
        ↓
Web Capture Bundleを生成
        ↓
Native Messaging
        ↓
Native Host
        ↓
extensions/web-page-capture/local-captures/ へ保存
        ↓
成功 / 失敗通知
        ↓
後日CPCがImporterで取り込む
```

## 4. ユーザーインターフェース

本機能にはPopup、Options画面、Side Panel等の常設UIを設けない。

### 操作

ChromeのContext MenuにCapture項目を追加する。

```text
右クリック
└─ このページをキャプチャ
```

右クリックメニューからの明示操作を、Capture開始の唯一の通常操作とする。

### 結果通知

成功時・失敗時のみ通知を表示する。

成功例：

```text
Web Page Capture
キャプチャを保存しました。
<filename>.webcapture.zip
```

失敗例：

```text
Web Page Capture
キャプチャに失敗しました。
<reason>
```

## 5. Capture対象

### 必須対象

- Capture時点のMain Document DOM
- 実際に表示していたURL
- page title
- capture timestamp
- document metadata
- meta要素
- link要素の主要metadata
- JSON-LD等のstructured metadata
- Capture tool/version
- Capture format version
- Capture completeness / warning
- 各主要Artifactのchecksum

### 取得可能な範囲で保持

- iframe/frame DOM
- open Shadow DOM
- resource reference一覧
- MHTML
- viewport/document size
- scroll position
- canonical URL
- language / charset / content type

### 必須対象外

- Screenshot
- 画像ファイルの独自Downloader
- CDP/debuggerによる高度なBrowser Snapshot
- network log
- response body archive

これらはCapture fidelity上の必要性が明確になった場合のみ、Capture機能として別途検討する。

## 6. Raw DOM

Main DOMはCapture時点の `document.documentElement` をserializationしたものを基本とする。

HTTPサーバーが最初に返したHTMLとは区別し、ファイル名も `original.html` ではなく `main.html` または `rendered-dom.html` とする。

DOCTYPEは別途取得し、可能な場合はserialization結果へ保持する。

Raw段階では以下を削除しない。

- script
- style
- navigation
- footer
- sidebar
- advertisement
- related articles
- UI element

これらの不要情報除去はCPC側のExtractor / Normalization段階で行う。

## 7. Metadata

HTML内metadataはRaw DOMにも残した上で、後段から参照しやすい索引として別途JSON化する。

対象例：

- `<meta>`
- canonical link
- Open Graph
- article published/modified time
- author
- site name
- JSON-LD

Structured Dataは解析済み値だけではなく、可能な限り元のraw文字列も保存し、将来再解析できるようにする。

## 8. iframe / Shadow DOM

iframeは可能な範囲でFrame単位に保存し、Main Documentとの親子関係をmetadataとして保持する。

取得不能なFrameは削除扱いにせず、`permission_denied` 等のCapture Statusとして記録する。

open Shadow DOMは取得対象とする。closed Shadow DOMは通常方式では完全取得できないため、既知の制約としてCapture Manifestに記録可能とする。

## 9. MHTML

MHTMLはRendered DOMとは別の補助Archiveとして扱う。

役割：

- `dom/main.html`: CPCで直接再解析しやすいRaw DOM
- `archive/page.mhtml`: ページと関連Resourceを含む補助Archive

MHTML単独を正本とはしない。

## 10. Security / Privacy

Capture目的で以下を積極的に取得しない。

- Cookie
- LocalStorage
- SessionStorage
- IndexedDB
- authentication token
- password
- Browser History

ログイン後ページについては、資格情報ではなく「ブラウザに構築された表示結果」を取得対象とする。

JavaScript propertyとしてのみ存在する入力値を、CaptureのためにDOM attributeへ書き戻す処理も原則行わない。

## 11. 保存方式

### 11.1 保存先

標準保存先は以下とする。

```text
CharacterPageCollector/
└─ extensions/
   └─ web-page-capture/
      └─ local-captures/
         └─ *.webcapture.zip
```

`local-captures/` はGit管理対象外とする。

### 11.2 Chrome Extension単体で直接保存しない理由

Chrome Extensionの標準Downloads APIは、Chromeの既定Downloadディレクトリを基準とした保存を前提とする。

本プロジェクトではプロジェクト配下の固定ディレクトリへ保存するため、保存処理をNative Hostへ委譲する。

### 11.3 Native Host

Chrome公式のNative Messagingを用いる。

```text
Chrome Extension
      ↓
Native Messaging
      ↓
Native Host
      ↓
local-captures/
```

Native HostはWindows上で動作する小さなローカルプログラムとする。

責務：

- ExtensionからCapture Bundleデータまたは保存対象データを受け取る。
- 許可された `local-captures/` へ保存する。
- 成功・失敗結果をExtensionへ返す。

Native Hostへ以下の責務を持たせない。

- 本文抽出
- Source/Site判定
- Entity判定
- Normalization
- CPC DB操作
- LLM処理
- その他CPC本体の処理

Native Hostは保存用の橋渡しに限定する。

### 11.4 localhostサーバーを採用しない

CaptureのためにCPC localhost serverを常時起動する方式は採用しない。

Native Messagingを用いることで、TCP port、HTTP API、常駐Web ServerをCaptureの必須要件にしない。

## 12. Chrome Extension構成

Manifest V3を前提とし、常駐Content Script依存を避ける。

基本形：

```text
右クリックメニュー
  ↓
activeTab相当の一時的権限
  ↓
Capture処理を実行
  ↓
Bundle生成
  ↓
Native Hostへ保存依頼
  ↓
結果通知
```

実装した責務：

- Context Menu登録
- Capture開始
- DOM/metadata等の取得
- Bundle生成
- Native Messaging
- 成功/失敗通知

Popup / Options UI用コードは設けない。

CDP/debugger権限を利用するAdvanced Captureは、権限が強いため標準方式には含めない。必要性が具体化した場合のみCapture fidelity改善として再検討する。

## 13. Web Page Captureの責務外

以下は「初期版では実装しない機能」ではない。

**本機能の責務そのものから除外し、将来的にもWeb Page Captureへ実装しない。**

- 本文抽出
- 広告除去
- navigation / sidebar / footer等の不要情報除去
- Source Type判定
- Site判定
- Wikipedia等の個別サイト判定
- Site-specific Extractor
- Entity判定
- Normalization
- Evidence生成
- Fragment生成
- LLM処理
- Embedding
- RAG
- CPC DB登録・更新

これらはCharacterPageCollector本体の責務とする。

## 14. 初期実装範囲

初期実装では次を対象とする。

- Manifest V3 Chrome Extension
- Context Menuからの明示Capture
- Main DOM serialization
- URL / title / captured_at
- HTML metadata
- JSON-LD
- open Shadow DOM
- 可能なFrame Capture
- checksum
- completeness / warning
- ZIP Bundle
- Format Version
- optional MHTML
- Native Messaging
- Native Hostによる `local-captures/` 保存
- 成功 / 失敗通知

### 14.1 v0.1.0の確定構成

- Chrome 116以降、Manifest V3、ビルド不要のJavaScript ES Modules。
- 権限は `contextMenus`, `activeTab`, `scripting`, `nativeMessaging`, `pageCapture`, `notifications` のみ。常時Host Permission・常駐Content Script・debugger権限なし。
- `scripting.executeScript` のisolated worldでMain Documentを取得し、アクセス可能な子Frameを再帰的に取得する。クロスオリジンFrameは取得不能を記録し、追加権限を要求しない。
- open Shadow DOMのHost位置・HTML・入れ子の対応を別Artifactへ保存。closed Shadow DOMは有無を判定できないため既知の制約としてwarningを保存し、全体をpartialとする。
- MHTMLは毎回 `pageCapture.saveAsMHTML` を試行する。Main DOM取得成功ならMHTML失敗も部分Captureとして保存する。主DOM失敗時はBundleを生成しない。
- UUID v4とUTC日時でファイル名を決定。タイトル・ページ由来パスはファイル名に使用しない。
- ExtensionがZIP（STORE形式）とArtifact SHA-256を生成。`connectNative` をCapture開始時に接続し、ACK付き192 KiB chunkで保存Hostへ転送する。
- Python標準ライブラリのHostが検証、固定ディレクトリ内の一時ファイル、fsync、非上書きAtomic Renameを担当する。Hostはページの意味を解釈しない。
- DOM/MHTMLは逐次取得であり、同時点を保証しない。取得中に実URLが変わった場合は保存を中止する。同一URLの再読み込みは検知を保証しない。

Chrome公式仕様: [activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab)、[scripting](https://developer.chrome.com/docs/extensions/reference/api/scripting)、[pageCapture](https://developer.chrome.com/docs/extensions/reference/api/pageCapture)、[Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)。

## 15. 将来拡張

将来拡張はWeb Captureの取得精度・保存信頼性を高めるものに限定する。

候補：

- Frame取得精度向上
- Shadow DOM取得精度向上
- Capture diagnostics強化
- MHTML取得改善
- CDP / DOMSnapshot等によるHigh Fidelity Capture
- Native Hostの導入・更新手順簡略化
- Capture Bundle検証機能

CPC解析機能の追加は将来拡張に含めない。

## 16. システム境界

```text
Chrome Web Page
      │
      │ 右クリック
      ▼
Web Page Capture Extension
      │
      ├─ Rendered DOM
      ├─ Metadata
      ├─ JSON-LD
      ├─ Frames
      ├─ Open Shadow DOM
      ├─ MHTML
      └─ Capture diagnostics
      │
      ▼
Web Capture Bundle
      │
      ▼
Native Host
      │
      ▼
extensions/web-page-capture/local-captures/
      │
      ▼
========== 責務境界 ==========
      │
      ▼
CharacterPageCollector
      │
      ├─ Import
      ├─ Source / Snapshot
      ├─ Extractor
      ├─ Normalization
      ├─ Evidence
      ├─ Fragment
      └─ その他CPC処理
```
