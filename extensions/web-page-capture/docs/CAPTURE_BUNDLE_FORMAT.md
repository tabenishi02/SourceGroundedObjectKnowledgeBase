# Web Capture Bundle Format

## 1. 目的

1回のCapture結果を、後段のSource Grounded Object Knowledge Baseや他ツールから再利用できる自己完結した保存単位として扱う。

名称は **Web Capture Bundle** とし、ファイル名は以下とする。

```text
<timestamp>_<capture-id>.webcapture.zip
```

独自バイナリ形式は採用せず、一般的なZIPとJSON/HTMLを中心に構成する。

## 2. 論理構造

```text
capture/
├─ manifest.json
├─ dom/
│  ├─ main.html
│  └─ frames/
│     └─ ...
├─ metadata/
│  ├─ document.json
│  ├─ html-metadata.json
│  ├─ structured-data.json
│  ├─ frames.json
│  ├─ shadow-dom.json
│  └─ resources.json
├─ archive/
│  └─ page.mhtml
└─ checksums.json
```

存在しないOptional Artifactは空ファイルを作るのではなく、manifestで未取得理由を表現する。

## 3. manifest.json

v1.0の基本フィールド例（追加の確定規則は第13節）：

```json
{
  "format": "web-capture-bundle",
  "format_version": "1.0",
  "capture_id": "UUID",
  "captured_at": "RFC3339 timestamp",
  "capture_tool": {
    "name": "WebPageCapture",
    "version": "0.1.0"
  },
  "page": {
    "url": "https://example.com/",
    "title": "Example"
  },
  "components": {
    "main_dom": "success",
    "metadata": "success",
    "structured_data": "success",
    "frames": "partial",
    "shadow_dom": "partial",
    "mhtml": "success"
  },
  "warnings": []
}
```

`format_version` とExtension Versionは別概念とする。

## 4. document.json

基本フィールド例：

```json
{
  "url": "https://example.com/page",
  "canonical_url": "https://example.com/page",
  "title": "Example",
  "base_uri": "https://example.com/page",
  "referrer": "",
  "language": "ja",
  "charset": "UTF-8",
  "content_type": "text/html",
  "ready_state": "complete",
  "viewport": {
    "width": 1920,
    "height": 1080,
    "device_pixel_ratio": 1
  },
  "scroll": {
    "x": 0,
    "y": 0
  }
}
```

実URLとcanonical URLは別々に保持し、canonicalで実URLを上書きしない。

## 5. html-metadata.json

HTML metadataを索引化する。

```json
{
  "meta": [
    {
      "name": "author",
      "content": "..."
    },
    {
      "property": "og:title",
      "content": "..."
    }
  ],
  "links": [
    {
      "rel": "canonical",
      "href": "..."
    }
  ]
}
```

Raw DOMにも元要素を残す。

## 6. structured-data.json

JSON-LD等を保存する。

```json
{
  "json_ld": [
    {
      "index": 0,
      "raw": "{...}"
    }
  ]
}
```

可能な限りraw表現を保持し、後段のParser変更後にも再処理可能とする。

## 7. frames.json

Frame Captureの対応関係と状態を保持する。

```json
[
  {
    "frame_id": "frame-0001",
    "parent_frame_id": "main",
    "url": "https://example.net/embed",
    "capture_status": "success",
    "file": "dom/frames/frame-0001.html"
  },
  {
    "frame_id": "frame-0002",
    "parent_frame_id": "main",
    "url": "https://other.example/",
    "capture_status": "permission_denied"
  }
]
```

## 8. shadow-dom.json

open Shadow RootのHostとの対応を保存する。

```json
[
  {
    "host_path": "html/body/x-app",
    "mode": "open",
    "html": "<div>...</div>"
  }
]
```

closed Shadow DOMは取得不能である可能性をmanifestへ記録する。

## 9. resources.json

DOM中で参照されていたResourceの索引を保存する。

```json
[
  {
    "url": "https://example.com/image.jpg",
    "element": "img",
    "attribute": "src"
  }
]
```

初期版ではResource本体の独自Downloadは必須としない。

## 10. checksums.json

主要ArtifactのSHA-256を保持する。

```json
{
  "dom/main.html": {
    "sha256": "..."
  },
  "archive/page.mhtml": {
    "sha256": "..."
  }
}
```

用途：

- 破損検出
- Capture比較
- 重複調査
- Regression Fixture管理

Hash一致を理由にCapture自体を自動削除・統合しない。

## 11. Capture Status

少なくとも以下を表現できるようにする。

- `success`
- `partial`
- `failed`
- `not_requested`
- `not_supported`
- `permission_denied`

v1.0の確定規則は第13節に記載する。

## 12. Versioning

Formatは後方互換を無条件に要求せず、Importer側で明示的にVersionを判定する。

例：

```text
Extension v0.1 → Format 1.0
Extension v0.8 → Format 1.0
Extension v1.0 → Format 2.0
```

Format変更時には、どのVersionから何が追加・削除・意味変更されたかを本書へ記録する。

## 13. 確定Schema v1.0（初回実装）

本節をv1.0の規範とする。上のJSON例は主要フィールドの説明であり、全フィールドを示すものではない。JSONはUTF-8、HTMLはRendered DOMをUTF-8で保存する。MHTMLはChromeが返したbyte列を変換せずに保存する。ZIPは標準STORE形式、各entryは `capture/` から始まる。

### ファイル名と必須Artifact

ファイル名は `YYYYMMDDTHHMMSSmmmZ_<UUID-v4>.webcapture.zip`。日時はUTC、ミリ秒3桁。Capture IDは小文字UUID v4。page title/URLはファイル名に使用しない。同一URLでも新しいCapture IDを生成し、上書き・重複統合しない。

必須Artifactは `manifest.json`, `dom/main.html`, `metadata/document.json`, `metadata/html-metadata.json`, `metadata/structured-data.json`, `metadata/frames.json`, `metadata/shadow-dom.json`, `metadata/resources.json`, `checksums.json`。取得できたFrameだけ `dom/frames/frame-NNNN.html` を追加する。MHTML成功時だけ `archive/page.mhtml` を追加する。

### Manifest

- `format`: `web-capture-bundle`、`format_version`: `1.0`。
- `capture_id`: UUID v4。`captured_at`: Main DOM取得時の `YYYY-MM-DDTHH:mm:ss.sssZ`。
- `capture_tool`: `name=WebPageCapture`, `version=Extension version`。
- `page`: 実際にDOMから取得した `url`, `title`。canonicalで置き換えない。
- `components`: `main_dom`, `metadata`, `structured_data`, `frames`, `shadow_dom`, `mhtml` の状態。
- `completeness`: 全取得対象が成功ならsuccess、取得不能・失敗・既知の完全性制約があればpartial。初回実装はclosed Shadow DOMを判定できず、常にpartialとする。
- `warnings`: `{code, component, reason?, frame_id?}` の配列。機密ページ情報や例外stackは含めない。

Main DOMは必須でsuccessのみ保存可能。Main DOM失敗はCapture全体のfailedとして失敗通知し、正式Bundleを生成しない。MHTML失敗時はmhtml=failedとwarningを保存し、空Artifactを作らない。framesは取得不能Frameがあるとpartial、shadow_domはclosed制約によりpartial。未検出Frame/open Shadow/Structured Dataの索引は空配列で成功を示す。not_requested/not_supported/permission_deniedはSchema上有効な状態だが、毎回MHTMLを試す初回実装のmhtmlはsuccessまたはfailed。

### Documentと索引

`document.json` は第4節の全フィールドに加え `doctype`, `captured_at`, `size={width,height}` を持つ。canonicalがない場合はnull、doctypeがない場合は空文字列。DOCTYPEはHTML先頭にも保存する。propertyとしてのみ存在するフォーム値はattributeへ書き戻さない。

`html-metadata.json` はmeta/link要素の全attributeを文字列辞書として保持する。重複要素と順序を保持する。raw hrefとresolved canonical_urlを区別する。

`structured-data.json` は `json_ld=[{index,raw}]`（不正JSONもrawのまま）、`microdata=[attribute辞書]`, `rdfa=[attribute辞書]`。意味の解釈・分類は行わず、本文を含む元要素はRaw DOMにも残す。

`frames.json` は配列。各項目に `frame_id`, `parent_frame_id`, `element_path`, `url`, `attributes`, `capture_status` を持つ。成功時は `file`, `metadata`（子document情報）, `html_metadata`, `structured_data` を追加する。取得不能時はreasonを記録し、metadata索引はnull、fileは存在しない。frame IDはDOM走査順のframe-0001等。クロスオリジン/sandbox等で読めない場合はpermission_denied、読み取り中の例外はfailed。その内部のFrameは列挙できない。

`shadow-dom.json` は `{frame_id, host_path, mode=open, html}` の配列。位置は `/html[0]/body[1]/x-fixture[5]` のように各親のchildren内の0始まりindexを使い、Shadow Root境界は `/#shadow-root`。入れ子open Shadow Rootも別項目として保持する。Main DOMのouterHTMLにShadow内容を人工的に追加しない。closedは存在判定不能というwarningで表現する。

`resources.json` は `{frame_id, element_path, element, attribute, raw, url}` の配列。src/href/poster/srcset/data attributeを索引化する。srcsetは複数URLなのでurl=null、raw文字列をそのまま保存。CSS内のURLやResource本体を独自取得しない。

### Checksumと保存失敗

`checksums.json` は、自身以外の全Artifact（manifestと各metadataも含む）の相対パスをキーに `{sha256: 小文字hex64桁, bytes: byte数}` を持つ。キーに `capture/` は含めない。Native Hostは全checksumとZIP CRCを検証してから正式ファイルへ確定する。

転送・検証・書き込み失敗は保存全体のfailed。正式Bundleを残さず失敗通知する。一時ファイルはBundleではない。電源断等による残存一時ファイルの扱いと転送上限はNATIVE_HOST.mdに記載する。
