# Web Page Capture Extension

CharacterPageCollector（CPC）向けのWebページ取得を担うChrome拡張機能用サブプロジェクトです。

## 目的

ユーザーがブラウザで内容を確認し、必要な展開操作やJavaScript実行が完了した時点のWebページ状態を、後からCharacterPageCollectorで再解析できるRaw Captureとして保存します。

この拡張機能はCPC内部のSource分類、Extractor、Evidence、Fragment、DB Schemaなどには依存しません。CPCの設計が将来変更されても、原則として同じWeb Captureを再利用できることを優先します。

## 基本方針

- ユーザーが明示的にCaptureしたページだけを取得する。
- HTTP初期HTMLではなく、Capture時点のRendered DOMを主なRaw資料とする。
- Capture時に本文抽出・広告除去・Entity判定等を行わない。
- 同一URLの複数Captureを許容し、上書きしない。
- Capture形式に独立したFormat Versionを持たせる。
- 取得できなかった情報もCapture結果として記録する。
- CPC localhost APIを必須とせず、拡張機能単体で保存できるようにする。
- Cookie、認証Token、LocalStorage等の資格情報・ブラウザ状態は収集対象にしない。

## ディレクトリ

```text
web-page-capture/
├─ README.md
├─ .gitignore
├─ docs/
│  ├─ DESIGN.md
│  └─ CAPTURE_BUNDLE_FORMAT.md
├─ src/
│  ├─ background/
│  ├─ capture/
│  ├─ export/
│  ├─ options/
│  ├─ popup/
│  └─ shared/
├─ public/
│  └─ icons/
├─ tests/
│  ├─ unit/
│  └─ fixtures/
└─ local-captures/        # Git管理外
```

実装開始時には、このディレクトリ直下へ `package.json`、TypeScript設定、Manifest V3設定、ビルド設定等を追加します。ツールチェーンは実装設計時に確定し、現段階では固定しません。

## 各ディレクトリの責務

- `docs/`: 要件・設計・保存形式仕様。
- `src/background/`: Manifest V3 Service WorkerおよびCapture全体のオーケストレーション。
- `src/capture/`: DOM、metadata、frame、Shadow DOM等の取得処理。
- `src/export/`: ZIP生成、Download保存、将来のCPC Exporter。
- `src/popup/`: 日常Capture用の最小UI。
- `src/options/`: 保存方式等の設定UI。
- `src/shared/`: 型、定数、共通Utility。
- `public/icons/`: Extension icon等の静的資産。
- `tests/unit/`: 決定的処理のUnit Test。
- `tests/fixtures/`: 小さく、再配布可能で、機密情報を含まないTest Fixture。
- `local-captures/`: 実サイトから取得した日常Captureや開発サンプル。Gitへコミットしない。

## CPCとの境界

```text
Chrome
  ↓
Web Page Capture Extension
  ↓
Web Capture Bundle
  ↓
保存
  ↓
CharacterPageCollector
  ↓
Importer → Source / Snapshot → Extractor → Evidence → Fragment
```

CPCとの直接通信は将来のExporterとして追加可能ですが、Capture自体はCPCが停止中でも成立する設計とします。
