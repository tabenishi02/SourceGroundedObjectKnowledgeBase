# Web Capture Bundle Format

## 1. 目的

1回のCapture結果を、後段のCharacterPageCollectorや他ツールから再利用できる自己完結した保存単位として扱う。

初期名称は **Web Capture Bundle** とし、ファイル名は以下を候補とする。

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

最低限の候補：

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
    "shadow_dom": "success",
    "mhtml": "not_requested"
  },
  "warnings": []
}
```

`format_version` とExtension Versionは別概念とする。

## 4. document.json

候補：

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

DOM中で参照されていたResourceの索引を保存する候補。

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

具体的なSchemaは実装前に確定する。

## 12. Versioning

Formatは後方互換を無条件に要求せず、Importer側で明示的にVersionを判定する。

例：

```text
Extension v0.1 → Format 1.0
Extension v0.8 → Format 1.0
Extension v1.0 → Format 2.0
```

Format変更時には、どのVersionから何が追加・削除・意味変更されたかを本書へ記録する。
