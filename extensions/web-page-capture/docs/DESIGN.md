# Web Page Capture Extension 設計方針

## 1. 位置づけ

本拡張機能はCharacterPageCollector（CPC）のWeb Browser Capture部分を独立させた取得コンポーネントとする。

目的は「現在のCPCが必要とする情報を生成すること」ではなく、ユーザーが確認したWebページ状態を、将来のCPC設計変更後でも再解釈できるRaw Captureとして保存することである。

したがって、CPC固有のSource Type、site分類、Entity、Extractor、Evidence、Fragment、Embedding、DB Schema等をCapture時に確定しない。

## 2. 設計原則

| ID | 原則 |
|---|---|
| CAP-01 | ユーザーが明示的に保存したページだけを取得する。 |
| CAP-02 | HTTP初期HTMLではなく、保存操作時点のRendered DOMを取得する。 |
| CAP-03 | Raw Captureでは本文抽出や不要情報除去を行わない。 |
| CAP-04 | CPC固有の分類・DB Schema・Extractorへ依存しない。 |
| CAP-05 | 同一URLの複数Captureを別Captureとして保持する。 |
| CAP-06 | Capture形式にExtension Versionとは独立したFormat Versionを持たせる。 |
| CAP-07 | 一部取得不能の場合も失敗箇所を明示してCapture自体を保持できる。 |
| CAP-08 | CPC localhost APIを保存の前提条件としない。 |
| CAP-09 | Cookie、認証Token等の認証情報は収集しない。 |
| CAP-10 | Capture後の加工・解釈は後段処理へ委譲する。 |

## 3. 標準Captureフロー

```text
ユーザーがChromeでページを閲覧
        ↓
必要な「もっと見る」・返信・折りたたみ等を展開
        ↓
ExtensionからCaptureを実行
        ↓
Rendered DOM / metadata / structured data等を収集
        ↓
Capture結果・取得不能情報を記録
        ↓
Web Capture Bundleを生成
        ↓
ローカルへ保存
        ↓
後日CPCがImporterで取り込む
```

## 4. Capture対象

### 必須候補

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

### 初期版では必須にしない

- Screenshot
- 画像ファイルの独自Downloader
- CDP/debuggerによる高度なBrowser Snapshot
- network log
- response body archive

## 5. Raw DOM

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

## 6. Metadata

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

## 7. iframe / Shadow DOM

iframeは可能な範囲でFrame単位に保存し、Main Documentとの親子関係をmetadataとして保持する。

取得不能なFrameは削除扱いにせず、`permission_denied` 等のCapture Statusとして記録する。

open Shadow DOMは取得対象とする。closed Shadow DOMは通常方式では完全取得できないため、既知の制約としてCapture Manifestに記録可能とする。

## 8. MHTML

MHTMLはRendered DOMとは別の補助Archiveとして扱う。

役割：

- `dom/main.html`: CPCで直接再解析しやすいRaw DOM
- `archive/page.mhtml`: ページと関連Resourceを含む補助Archive

MHTML単独を正本とはしない。

## 9. Security / Privacy

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

## 10. 保存とExporter

初期ExporterはDownload保存とする。

将来以下へ拡張できるように責務を分離する。

```text
Capture
   ↓
Bundle Builder
   ↓
Exporter
   ├─ DownloadExporter
   └─ CPCExporter
```

CPCExporterを追加してもDownloadExporterは維持し、CPC停止中でもCapture可能とする。

## 11. Chrome Extension構成

Manifest V3を前提とし、常駐Content Script依存を避ける。

基本形：

```text
ユーザー操作
  ↓
activeTab相当の一時的権限
  ↓
Capture処理を実行
  ↓
Bundle生成
  ↓
保存
```

CDP/debugger権限を利用するAdvanced Captureは、権限が強いため初期版の標準方式には含めない。

## 12. MVP境界

MVPでは次を実装対象とする。

- ユーザー明示操作によるCapture
- Main DOM serialization
- URL / title / captured_at
- HTML metadata
- JSON-LD
- open Shadow DOM
- 可能なFrame Capture
- checksum
- completeness / warning
- ZIP Bundle
- Download保存
- Format Version
- optional MHTML

MVPでは次を実装しない。

- CPC Entity判定
- Source Type判定
- Site-specific Extractor
- 本文抽出
- 広告除去
- LLM処理
- Embedding
- 独自画像Downloader
- CPC DB直接更新
- CDP/debugger Capture

## 13. 将来フェーズ

```text
Phase 1: Basic Capture
  DOM / Metadata / JSON-LD / ZIP / Download
        ↓
Phase 2: High Fidelity
  Frame / Shadow DOM / MHTML / Capture診断
        ↓
Phase 3: CPC Integration
  WebCaptureImporter / CPCExporter
        ↓
Phase 4: Advanced Capture
  CDP / DOMSnapshot等を必要性評価後に追加
```
