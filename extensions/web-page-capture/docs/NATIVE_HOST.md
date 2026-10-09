# Native Host 設計

## 1. Native Hostとは

Chrome Extensionはセキュリティ上、Windows上の任意のフォルダへ自由にファイルを書き込めない。

本プロジェクトではCapture Bundleを次の場所へ保存する。

```text
Source Grounded Object Knowledge Base/
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
C:\...\Source Grounded Object Knowledge Base\extensions\web-page-capture\local-captures\
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

Capture処理にTCP port、HTTP API、Firewall設定、常駐SGOKB Serverを要求しないことを利点とする。

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
- SGOKB DB操作
- RAG
- その他Source Grounded Object Knowledge Base本体の処理

Native Hostは**保存用Bridge**であり、SGOKB Coreではない。

## 5. 通信プロトコル v1.0

Native MessagingではChromeとNative Hostの間でメッセージをやり取りする。

開始要求：

```json
{
  "command": "begin",
  "transfer_id": "11111111-1111-4111-8111-111111111111",
  "filename": "20261004T092500000Z_11111111-1111-4111-8111-111111111111.webcapture.zip",
  "size": 12345
}
```

Native Host側からは例えば以下のような結果を返す。

成功：

```json
{
  "success": true,
  "filename": "20261004T092500000Z_11111111-1111-4111-8111-111111111111.webcapture.zip",
  "sha256": "<ZIP全体のSHA-256>"
}
```

失敗：

```json
{
  "success": false,
  "error": "write_failed"
}
```

`runtime.connectNative` の1接続につき1転送。各要求へACKが返るまで次を送らない。

| command | 必須フィールド（commandを含む。余分なフィールドは拒否） | 意味 |
|---|---|---|
| hello | command | 保存前の接続確認。protocol_version=1.0を返す |
| begin | command, transfer_id, filename, size | UUID v4、確定ファイル名、ZIP byte数で開始 |
| chunk | command, transfer_id, sequence, data | 0開始の連続sequence、Base64で最大192 KiBのbinaryデータ |
| finish | command, transfer_id, chunks | chunk数と全byte数、ZIP構造、Format、Artifact checksumを検証して確定 |

Chromeの公式上限はExtension→Hostが64 MiB、Host→Extensionが1 MB。実装は受信JSONを300 KiB以下、返信を小さなACKに限定する。Bundleは最大512 MiB、ZIP STORE形式のみ。上限超過は失敗とし、保存成功扱いにしない。要求ごとのExtension側timeoutは60秒。

Hostは各chunkを固定保存先の `.transfer-*.tmp` に書き込む。順序違反・欠落・重複・別transfer ID・不正Base64・サイズ超過を拒否する。完了時に全ArtifactのSHA-256とbyte数を検証し、ストリームで計算したZIP全体のSHA-256を返す。ZIP全体を1つのJSONにしない。

fsync後、Windowsの非上書き `os.rename` で正式ファイルへ変更する。既存Bundleとの衝突は失敗。切断/通常の例外時に一時ファイルを除去する。プロセス強制終了や電源断時には `.tmp` が残る可能性があるが正式Bundleとして扱わず、動作中Hostがないことを確認してから手動削除する。

エラーは `invalid_message`, `invalid_filename`, `invalid_sequence`, `incomplete_transfer`, `checksum_mismatch`, `capture_exists`, `save_or_bundle_validation_failed` 等のコードで返す。ページ本文・資格情報・ローカル絶対パスをエラーへ含めない。

仕様根拠: [Chrome Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)。

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

WindowsではNative Messaging Host manifestと現在ユーザーのRegistry登録を利用する。

`native-host/Manage-NativeHost.ps1` でInstall/Uninstall/Status/Prepareを実行する。HKCUの `Software\Google\Chrome\NativeMessagingHosts\com.sgokb.web_page_capture` に `.local/host-manifest.json` を登録する。allowed_originsは指定Extension IDだけでwildcardなし。HostもChromeから渡されたoriginをmanifestと比較する。実設定・絶対パス・生成Executableは `.local/` に置きGit管理しない。詳細はREADMEを参照。

## 7. 実装言語

Python 3.10以降の標準ライブラリを採用する。SGOKBの依存Packageや解析コードを取り込まない。

既存のPython環境を再利用でき、ZIP/JSON/SHA-256/Native Messagingを外部依存なしで保守できることを選択理由とする。

起動構成：

```text
Chrome → .local/host.exe（C#起動Bridge）→ python.exe -I -u native-host/host.py
```

Install時にWindowsの.NET Framework C# compilerで `Launcher.cs` をコンパイルする。Python/scriptの場所を固定した起動Bridgeだけを生成し、binary stdioを転送する。任意コマンド起動APIは持たない。Pythonはisolated modeで起動する。Python Runtimeが必要であるため、移動・削除後は再Installが必要。将来Python部分をExecutable化する場合も固定保存先・origin検証・同じstdioプロトコルを保持する。

## 8. 保存先

標準保存先：

```text
<repository-root>/
└─ extensions/
   └─ web-page-capture/
      └─ local-captures/
```

Native Hostは、任意のユーザー指定パスへ無制限に保存する汎用ファイル書き込み機能にはしない。

保存先はHost自身の配置から求めた `local-captures/` に固定する。Extensionから保存先を受け取らない。title/URLをファイル名に使用せず、UTC日時とUUID v4の厳格な形式だけを受け付ける。ZIPは展開せず、許可したArtifact名だけを検証する。保存先自体のsymlinkを拒否する。同じWindowsユーザーがリポジトリの親ディレクトリやHostコードを変更できることはOS権限の境界であり、本Hostはそれを防ぐsandboxではない。

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

Source Grounded Object Knowledge Base
  = Raw Captureの解析・整理・検索・生成
```

Native Hostは両者の中間処理エンジンではなく、Web Page Capture側の保存機構の一部として扱う。
