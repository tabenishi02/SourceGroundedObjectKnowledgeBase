# Windows 11 + Chrome 手動受入試験

自動テスト成功は実機結合の合格を意味しません。次をユーザー操作で確認し、結果・Chrome/Python/Extensionのversion・日時をPRへ記録してください。実ページやBundleはGit/PRへ添付しません。実機試験完了前にmainへマージしません。

## 準備

READMEのLoad unpacked、Host Install、Statusを実行します。CPCとlocalhost Serverは停止した状態で試験します。Windows/Chrome通知を有効にします。

`tests/fixtures/page.html` は人工Fixtureです。Chrome拡張機能詳細でファイルURLアクセスを有効にし、FixtureをChromeで開きます。ここだけ `example.invalid` のFrameを故意に取得不能にしています。静的/same-origin Frameも確認する場合は、Fixtureの一時コピーをGit管理外に置き、`srcdoc` FrameのDOMをChrome DevToolsで確認してください。

## 試験項目

| 項目 | 操作 | 合格条件 | 結果 |
|---|---|---|---|
| Load unpacked | `extension/` を読み込む | Manifest・Service Workerの読み込みエラーなし。Popup/Options/Side Panelなし | 未記入 |
| 静的ページ | `https://example.com/` を開いて右クリックCapture | 保存成功通知、`local-captures/` にZIPが1つ生成される | 未記入 |
| メニュー対象 | ページ、リンク、画像、選択文字列上から実行 | クリック対象ではなくActive Tab全体のDOMを保存 | 未記入 |
| 動的ページ | Fixtureを開く | Main DOMに `JavaScript content` がある | PENDING（収集済み13 ZIPにFixtureなし。指定markerの実機保存は未確認） |
| 展開後ページ | Fixtureの「もっと見る」を押してCapture | `Expanded content` があり、`hidden` attributeが外れている | PENDING（Fixtureなし。展開前後の操作・DOM比較の証拠がない） |
| フォームproperty | Fixtureの入力欄を変更しCapture | `input` のHTML attributeは `attribute-only` のまま。password propertyを書き戻していない | PENDING（Fixtureのinput/passwordがなく、property変更前後を判断できない） |
| 連続Capture | 同じURLを2回Capture | UUIDの異なる2つのZIPが存在し、1つ目の内容・更新日時は変わらない | 一部確認（同一実URLの5 ZIP、別UUID・日時で共存。最初のファイルの内容・更新日時不変は試験前の記録がなくPENDING） |
| Raw保持 | ZIPの `capture/dom/main.html` をテキストで確認 | DOCTYPE、script、style、nav、aside、footer、UIが残る | OK（ZIP内容確認：全13 ZIPにDOCTYPE・script・style。B02等でnav・aside・footer・buttonも保持） |
| MHTML | ZIPを展開して `capture/archive/page.mhtml` をChromeで開く | 補助Archiveが存在し、開ける。失敗時はmanifestにmhtml=failedと理由があり、空のMHTMLなし | 一部確認（全13 ZIPでmhtml=success、非空Archive・MIMEヘッダー・checksum一致。Chromeでの表示とMHTML失敗時の実機動作はPENDING） |
| iframe | Fixtureまたは同一オリジンFrameを含むページをCapture | アクセス可能FrameのDOM・親子関係を保持。取得不能Frameはframes.jsonにpermission_denied等を記録 | OK（ZIP内容確認：B01・B03・B11で成功FrameのDOMとmetadata、全Frameの親ID対応を確認。取得不能Frameはpermission_denied・理由を記録） |
| Shadow DOM | FixtureをCapture | shadow-dom.jsonにopen/nested shadowとHost位置がある。closed制約warningを記録 | 一部確認（全13 ZIPでopen ShadowのHTML・Host位置とclosed制約warningを確認。Fixtureなし、入れ子open Shadowの実機保存はPENDING） |
| 完全性・checksum | manifestとchecksumsを確認 | format_version=1.0、実URLとcanonicalが別。全Artifact（checksums自身以外）にSHA-256とbyte数がある | OK（全13 ZIPでFormat 1.0、実URLとcanonical別フィールド、全ArtifactのSHA-256・byte数・ZIP CRC一致、partialとwarning整合を確認） |
| Host未登録 | Uninstall → Capture → Installで戻す | 失敗理由の通知、ZIPなし。再Install後に成功 | PENDING（保存成功ZIPから未登録時の通知・非生成・再登録後の動作は判断できない） |
| 保存先失敗 | 以下の可逆な方法で試験 | 失敗通知、一時転送を正式Bundleとして残さない。復旧後に成功 | PENDING（検査時の.tmpは0件だが、書き込み失敗の実機再現・通知・復旧の証拠がない） |

Main DOM / Frame / Shadow / MHTMLがすべて同時点になること、closed ShadowやクロスオリジンFrameを完全取得することは合格条件に含めません。これらの制約がmanifestに記録されることを確認します。

## 収集済みZIPの検査記録（2026-10-04）

対象は `local-captures/` の13 ZIP。Capture日時は2026-10-04 20:14:46〜20:29:12 JST、Capture Tool Versionはすべて0.1.0、実URLは9種類。実ページのURL・title・本文・ローカル絶対パスは本記録へ転記しない。B01〜B13はファイル名の昇順に対応する検査用ラベルで、対応表はGit管理外の `.local/acceptance-inspection.json` に保存した。

- 13 ZIPすべてについてHostのBundle検証を実行し、必須Artifact・Manifest・ファイル名/UUID/日時・ZIP内パス・全ArtifactのSHA-256/byte数・ZIP CRCの検証に成功した。検査は読み取りのみで、既存ZIPは変更していない。
- 最大BundleはB03の56,480,879 bytes。全13 ZIPでMain DOMとMHTMLの成功記録を確認した。MHTMLは非空で `MIME-Version` と `multipart/related` のヘッダーがある。Chromeでの表示可否はこの検査の対象外。
- 同一実URLのB02・B04・B05・B06・B07が、別UUID・日時の5 Captureとして共存している。収集前のhash・更新日時がないため、最初のファイルが後のCaptureで変更されなかったことまでは証明しない。
- Frameは成功7件、permission_denied 35件。成功Frameの対応するHTMLとmetadata、全Frameの親ID対応を確認した。
- 全13 ZIPに合計135件のopen Shadow DOMの記録があり、Host位置・frame ID・mode=open・HTMLを確認した。入れ子Shadow Rootの記録と指定Fixtureはなかった。
- 全体completenessとshadow_domはすべてpartial。全ZIPに `closed_shadow_dom_unobservable`、取得不能FrameがあるZIPには `cross_origin_or_unavailable` が記録されており、既知制約によるpartialを保存失敗とは扱わない。

表中の既存OK/NGはユーザーの操作結果として保持し、追記したOKは明記したZIP内容の検査範囲に限る。「一部確認」は残る合格条件がPENDINGであり、総合合格ではない。通知・障害再現・未確認のFixture試験が残るため、実機受入は完了扱いにしない。

## 保存先失敗を安全に試す方法

処理中のCaptureがないことを確認し、PowerShellで既存 `local-captures/` を同じ親ディレクトリの `local-captures-acceptance-backup/` へ手動で移動します。既存バックアップがある場合はこの操作を開始しません。移動先のフルパスがプロジェクト配下であることを確認します。`local-captures` という名前の空の通常ファイルを代わりに作り、Captureを実行します。Hostのmkdirが失敗し、失敗通知と正式ZIPが作られないことを確認します。

試験後は作成した空ファイルだけを削除し、元のディレクトリを元の名前へ戻します。試験前に保存先がなかった場合は空ファイルを削除するだけです。Captureデータの再帰削除やACL変更は行いません。一時バックアップもGitに追加しません。

## 未観測の状態

この手順を作成しただけでは実機合格にはなりません。未実施項目はPENDINGとして残し、失敗時は通知理由とManifestのstatus（機密内容を含めない）を記録してください。
