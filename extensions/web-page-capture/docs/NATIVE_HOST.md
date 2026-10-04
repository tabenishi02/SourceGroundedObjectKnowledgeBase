# Native Host 設計

## 1. Native Hostとは

Chrome Extensionはセキュリティ上、Windows上の任意のフォルダへ自由にファイルを書き込めない。

本プロジェクトではCapture Bundleを次の場所へ保存する。

```text
CharacterPageCollector/
└─ extensions/
   └─ web-page-capture/
      └─ local-captures/
```

この保存先はChromeの標準Downloadsディレクトリではないため、Chrome Extension単体で直接保存する方式ではなく、Chrome公式の **Native Messaging** を利用する。

Native MessagingでChrome Extensionから呼び出され、Windows側で保存処理を行う小さなプログラムを本書では **Native Host** と呼ぶ。

## 2. 初心者向けの理解

Chrome ExtensionはChromeの中で動作する。

そのため、

```text
C:\...\CharacterPageCollector\extensions\web-page-capture\local-captures\
```

のようなWindows上の好きな場所へ直接書き込むことには制限がある。

Native Hostは、ChromeとWindowsのファイルシステムの間を橋渡しする。

```text
┌──────── Chrome ────────┐
│ Web Page Capture        │
│ Extension               │
└───────────┬─────────────┘
            │
      Native Messaging
            │
            ▼
┌──────── Windows ───────┐
│ Native Host             │
│                         │
│ Capture Bundleを保存    │
└───────────┬─────────────┘
            │
            ▼
local-captures/
```

## 3. localhost Serverとの違い

localhost Server方式では、通常はローカルWeb Serverを起動し、ExtensionからHTTP通信する。

```text
Chrome Extension
      ↓ HTTP
localhost server
      ↓
file save
```

本プロジェクトではCaptureのためだけに常駐Web Serverを必須にしない。

Native MessagingではChromeとNative Hostが直接通信する。

```text
Chrome Extension
      ↓ Native Messaging
Native Host
      ↓
file save
```

Capture処理にTCP port、HTTP API、Firewall設定、常駐CPC Serverを要求しないことを利点とする。

## 4. Native Hostの責務

Native Hostの責務は小さく保つ。

### 行うこと

- Chrome Extensionから保存要求を受け取る。
- Web Capture Bundleを受け取る、またはBundle生成に必要な保存データを受け取る。
- 許可された保存先を決定する。
- `local-captures/` へファイルを書き込む。
- 保存成功・失敗をExtensionへ返す。
- 必要に応じてファイル名・パスの安全性を検証する。

### 行わないこと

- Webページ本文抽出
- 広告除去
- Source Type判定
- Site判定
- Entity判定
- Extractor処理
- Normalization
- Evidence生成
- Fragment生成
- LLM処理
- Embedding
- CPC DB操作
- RAG
- その他CharacterPageCollector本体の処理

Native Hostは**保存用Bridge**であり、CPC Coreではない。

## 5. 通信イメージ

Native MessagingではChromeとNative Hostの間でメッセージをやり取りする。

概念例：

```json
{
  "command": "save_capture",
  "filename": "20261004T182500+0900_abc123.webcapture.zip",
  "data": "..."
}
```

Native Host側からは例えば以下のような結果を返す。

成功：

```json
{
  "success": true,
  "filename": "20261004T182500+0900_abc123.webcapture.zip"
}
```

失敗：

```json
{
  "success": false,
  "error": "write_failed"
}
```

上記は概念例であり、実際のMessage Schema、Binary Dataの渡し方、最大Message Sizeへの対応等は実装設計時に確定する。

## 6. Native Host登録

Chrome ExtensionがWindows上の任意プログラムを無制限に起動するわけではない。

Native Hostとして利用するプログラムは事前登録し、どのChrome Extensionから呼び出し可能かを制限する。

概念的には以下の情報を持つ。

```text
Native Host name
Native Host executable/script path
通信方式
呼び出しを許可するChrome Extension ID
```

WindowsではNative Messaging Host manifestとRegistry登録を利用する方式を前提候補とする。

詳細なインストール・登録方法はNative Host実装時に確定する。

## 7. 実装言語

現段階では確定しない。

CharacterPageCollectorがPython中心であるため、初期候補としてPythonは自然である。

候補：

```text
開発時
Python script
    ↓
必要に応じて
配布用Executable
```

ただし、Python Runtime依存の扱い、Native Messaging起動方法、配布・更新方法を比較した上で最終決定する。

## 8. 保存先

標準保存先：

```text
<repository-root>/
└─ extensions/
   └─ web-page-capture/
      └─ local-captures/
```

Native Hostは、任意のユーザー指定パスへ無制限に保存する汎用ファイル書き込み機能にはしない。

初期実装ではWeb Page Capture専用の保存先へ限定する方向を優先する。

## 9. セキュリティ原則

Native HostはChromeの制限外でWindowsファイルシステムへアクセスできるため、Extension側より強い権限を持つ。

そのため次を原則とする。

- 呼び出し可能なExtensionを限定する。
- 保存先を限定する。
- `..\` 等による保存先脱出を防止する。
- 任意コマンド実行機能を持たせない。
- 任意Executable起動機能を持たせない。
- Webページから渡された文字列をそのままファイルパスとして信用しない。
- エラー時に既存Captureを破壊しない。

## 10. 処理フロー

```text
ユーザー
  ↓
右クリック「このページをキャプチャ」
  ↓
Chrome Extension
  ├─ DOM取得
  ├─ metadata取得
  ├─ Bundle生成
  └─ Native Hostへ保存要求
          ↓
      Native Host
          ├─ 要求検証
          ├─ 保存先決定
          ├─ local-capturesへ保存
          └─ 結果返信
                 ↓
          Chrome Extension
                 ↓
          成功 / 失敗通知
```

## 11. 設計上の境界

Native Hostを導入してもWeb Page Captureの責務は変わらない。

```text
Web Page Capture
  = Webページ情報の取得 + Raw Captureの保存

CharacterPageCollector
  = Raw Captureの解析・整理・検索・生成
```

Native Hostは両者の中間処理エンジンではなく、Web Page Capture側の保存機構の一部として扱う。
