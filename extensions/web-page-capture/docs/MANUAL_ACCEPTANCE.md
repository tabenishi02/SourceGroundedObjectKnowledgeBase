# Windows 11 + Chrome 手動受入試験

自動テスト成功は実機結合の合格を意味しません。次をユーザー操作で確認し、結果・Chrome/Python/Extensionのversion・日時をPRへ記録してください。実ページやBundleはGit/PRへ添付しません。実機試験完了前にmainへマージしません。

## 準備

READMEのLoad unpacked、Host Install、Statusを実行します。CPCとlocalhost Serverは停止した状態で試験します。Windows/Chrome通知を有効にします。

`tests/fixtures/page.html` は人工Fixtureです。Chrome拡張機能詳細でファイルURLアクセスを有効にし、FixtureをChromeで開きます。ここだけ `example.invalid` のFrameを故意に取得不能にしています。静的/same-origin Frameも確認する場合は、Fixtureの一時コピーをGit管理外に置き、`srcdoc` FrameのDOMをChrome DevToolsで確認してください。

## 試験項目

| 項目 | 操作 | 合格条件 |
|---|---|---|
| Load unpacked | `extension/` を読み込む | Manifest・Service Workerの読み込みエラーなし。Popup/Options/Side Panelなし |
| 静的ページ | `https://example.com/` を開いて右クリックCapture | 保存成功通知、`local-captures/` にZIPが1つ生成される |
| メニュー対象 | ページ、リンク、画像、選択文字列上から実行 | クリック対象ではなくActive Tab全体のDOMを保存 |
| 動的ページ | Fixtureを開く | Main DOMに `JavaScript content` がある |
| 展開後ページ | Fixtureの「もっと見る」を押してCapture | `Expanded content` があり、`hidden` attributeが外れている |
| フォームproperty | Fixtureの入力欄を変更しCapture | `input` のHTML attributeは `attribute-only` のまま。password propertyを書き戻していない |
| 連続Capture | 同じURLを2回Capture | UUIDの異なる2つのZIPが存在し、1つ目の内容・更新日時は変わらない |
| Raw保持 | ZIPの `capture/dom/main.html` をテキストで確認 | DOCTYPE、script、style、nav、aside、footer、UIが残る |
| MHTML | ZIPを展開して `capture/archive/page.mhtml` をChromeで開く | 補助Archiveが存在し、開ける。失敗時はmanifestにmhtml=failedと理由があり、空のMHTMLなし |
| iframe | Fixtureまたは同一オリジンFrameを含むページをCapture | アクセス可能FrameのDOM・親子関係を保持。取得不能Frameはframes.jsonにpermission_denied等を記録 |
| Shadow DOM | FixtureをCapture | shadow-dom.jsonにopen/nested shadowとHost位置がある。closed制約warningを記録 |
| 完全性・checksum | manifestとchecksumsを確認 | format_version=1.0、実URLとcanonicalが別。全Artifact（checksums自身以外）にSHA-256とbyte数がある |
| Host未登録 | Uninstall → Capture → Installで戻す | 失敗理由の通知、ZIPなし。再Install後に成功 |
| 保存先失敗 | 以下の可逆な方法で試験 | 失敗通知、一時転送を正式Bundleとして残さない。復旧後に成功 |

Main DOM / Frame / Shadow / MHTMLがすべて同時点になること、closed ShadowやクロスオリジンFrameを完全取得することは合格条件に含めません。これらの制約がmanifestに記録されることを確認します。

## 保存先失敗を安全に試す方法

処理中のCaptureがないことを確認し、PowerShellで既存 `local-captures/` を同じ親ディレクトリの `local-captures-acceptance-backup/` へ手動で移動します。既存バックアップがある場合はこの操作を開始しません。移動先のフルパスがプロジェクト配下であることを確認します。`local-captures` という名前の空の通常ファイルを代わりに作り、Captureを実行します。Hostのmkdirが失敗し、失敗通知と正式ZIPが作られないことを確認します。

試験後は作成した空ファイルだけを削除し、元のディレクトリを元の名前へ戻します。試験前に保存先がなかった場合は空ファイルを削除するだけです。Captureデータの再帰削除やACL変更は行いません。一時バックアップもGitに追加しません。

## 未観測の状態

この手順を作成しただけでは実機合格にはなりません。未実施項目はPENDINGとして残し、失敗時は通知理由とManifestのstatus（機密内容を含めない）を記録してください。
