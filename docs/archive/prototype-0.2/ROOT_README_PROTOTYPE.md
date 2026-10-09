# Historical Prototype README

> **Archive:** これはSGOKB再設計前のPrototype運用READMEの保存版です。現行仕様ではありません。現在の文書入口は [`../../README.md`](../../README.md) です。

---

# Source Grounded Object Knowledge Base (SGOKB)

Web Capture Bundleを読み取り、構造化したEvidence、LLMによるFragment、Hybrid Searchを経て、出典付きのEntity文書を生成します。最終製品ではなく、実サンプルで処理を一周させるための暫定実装です。

現在の実装・評価・残課題は[開発状況まとめ（2026-10-06）](DEVELOPMENT_STATUS.md)を参照してください。Prototype Upgradeの実データ工程と8モデルの速度予備試験は終了しています。モデル別の実データ品質比較と速度改善の実装は未実施です。

Rename前のPrototype要件は[歴史資料: 要件定義書 v0.2](CharacterPageCollector%20システム要件定義書%20v0.2.md)です。`docs/cpc-prototype-minimum-requirements` はRename前の履歴ブランチです。既存の[Web Page Capture拡張機能](../../../extensions/web-page-capture/README.md)の取得・保存処理は独立したままです。

名称の正本は[Rename Decision](../../decisions/SGOKB_RENAME_DECISION.md)、実施手順は[Rename Runbook](../rename-2026-10/SGOKB_RENAME_CODEX_HANDOFF.md)です。

## セットアップ

Python 3.10以上、SQLite 3.34以上のFTS5/trigram対応環境が必要です。検証環境はPython 3.10、SQLite 3.37.2です。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m sgokb --help
```

以下では `.venv` を有効化済みの `python` を使用します。有効化しない場合は `.\.venv\Scripts\python.exe` で置き換えてください。`sgokb` コンソールコマンドも同じ処理を呼び出します。

```powershell
.\.venv\Scripts\Activate.ps1
python -m sgokb import sample
python -m sgokb process
python -m sgokb status
python -m sgokb snapshots
```

原ZIPは読み取りだけです。DB・ログ・実データの派生物は既定で `.local/` に保存します。

## 実モデルの設定

LLMはJSON Schema出力が利用できるChat Completions互換API、EmbeddingはEmbeddings互換APIを利用できます。接続先とモデルを個別に交換できます。ローカルLLMを使った検証例：

```powershell
lms server start
lms load openai/gpt-oss-20b --context-length 8192 --identifier sgokb-prototype-llm -y
lms load text-embedding-nomic-embed-text-v1.5 --identifier sgokb-prototype-embedding -y

$env:SGOKB_LLM_BASE_URL = 'http://127.0.0.1:1234/v1'
$env:SGOKB_LLM_MODEL = 'sgokb-prototype-llm'
$env:SGOKB_LLM_REVISION = 'openai/gpt-oss-20b;GGUF-MXFP4;upstream-revision-unknown'
$env:SGOKB_LLM_EXTRA_JSON = '{"reasoning_effort":"low"}'
$env:SGOKB_LLM_FRAGMENT_EXTRA_JSON = '{"response_format":{"type":"text"}}'
$env:SGOKB_EMBED_BASE_URL = 'http://127.0.0.1:1234/v1'
$env:SGOKB_EMBED_MODEL = 'sgokb-prototype-embedding'
$env:SGOKB_EMBED_REVISION = 'nomic-ai/nomic-embed-text-v1.5;GGUF-Q4_K_M;upstream-revision-unknown'
$env:SGOKB_EMBED_DOCUMENT_PREFIX = 'search_document: '
$env:SGOKB_EMBED_QUERY_PREFIX = 'search_query: '
```

このgpt-oss実機ではFragmentの制約付き出力が空配列に偏ったため、Fragment段階だけ `text` 応答へ切り替えています。Core側のJSON parse・Fragment内容・根拠ID検証は常に行います。Final段階はJSON Schema出力を使用します。別モデルでこの回避設定が不要なら `SGOKB_LLM_FRAGMENT_EXTRA_JSON` を解除してください。

既存モデルがある検証環境でNomic v1.5を暫定使用しました。これは英語モデルであり、日本語検索の最適選定ではありません。[モデルカード](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5)のprefixを設定しています。日本語の意味検索品質は今後、多言語モデルで比較してください。モデル自体を同梱・自動ダウンロードしません。

クラウドを選ぶ場合は `SGOKB_LLM_API_KEY` / `SGOKB_EMBED_API_KEY` を環境変数に設定します。選択した接続先にEvidence本文が送られるため、実データを扱える接続先を指定してください。`.env` はGit管理外ですが、自動読み込みは行いません。

SentenceTransformersを使う場合は `pip install -e '.[local-embedding]'` の後、`SGOKB_EMBED_PROVIDER=sentence-transformers`、`SGOKB_EMBED_MODEL` にモデル名、`SGOKB_EMBED_REVISION` にrevisionを指定します。モデルキャッシュは `.local/models/` です。このアダプターの実モデル評価は今回のLM Studio評価とは別です。

## Entityから最終文書まで

少数のEntityはCLIで登録します。評価スクリプトはサンプルのタイトルから対象Captureを選び、Work・Character各1件を登録するため、大量の手入力は不要です。名前・aliasは論理分類であり、Rawの物理名には使いません。

```powershell
python -m sgokb entity add Work 'アイドルマスター シャイニーカラーズ' --alias 'アイドルマスターシャイニーカラーズ'
python -m sgokb entity add Character '櫻木真乃'
python -m sgokb entity list

# IDは上の出力から設定する
$characterId = '<entity-id>'
$workId = '<work-entity-id>'
$snapshotId = '<snapshot-id>'
python -m sgokb entity relate $characterId appears_in $workId
python -m sgokb fragment --snapshot $snapshotId --entity $characterId
python -m sgokb embed
python -m sgokb search '櫻木真乃の性格' --entity $characterId
python -m sgokb generate --entity $characterId --out .local/documents/character.md
python -m sgokb provenance document '<document-id>'
```

`fragment` は入力EvidenceにあるIDだけを受理し、成功した根拠をEntityへ関連付けます。明示的にSnapshotの全Evidenceを対象Entityに関連付けたい場合は `entity link <entity-id> <snapshot-id>` を使用します。

## CLI一覧

グローバルオプション `--db` と `--prompt-dir` はサブコマンドより前に置きます。

| コマンド | 処理 |
|---|---|
| `import <file-or-directory>` | 再帰Import、checksum検証、重複Capture判定 |
| `process` / `extract` | 全Snapshotを正規化・Evidence化。`--snapshot` で限定 |
| `entity add/list/relate/link` | 拡張可能な型・名前・alias、関連・根拠の管理 |
| `fragment --snapshot ID --entity ID` | 実LLMによるFragment抽出 |
| `embed` | Active Evidence/FragmentのEmbedding生成 |
| `search QUERY` | Hybrid検索。`--mode lexical/semantic/hybrid` |
| `generate --entity ID` | 検索・根拠選択・実LLM・Markdown生成 |
| `provenance evidence/fragment/document ID` | 元ZIPまでの参照を表示 |
| `snapshots` / `status` | Snapshot一覧・保存件数 |

`embed` / `search` は `--entity`、`--source`、`--snapshot`、`--site`、`--source-type`、`--facet` で絞れます。Facet指定はFragmentを対象とします。

`process --size 1000 --overlap 100` が既定値です。`--include-auxiliary` を指定した場合だけ、取得成功Frameとopen Shadow DOMも抽出します。広告Frame等を通常検索へ混ぜないため、標準ではMain DOMだけを対象にします。元Artifactは常に参照可能です。

## 再処理

同じ原ZIPから `process` を再実行すると新しいNormalized/Evidence世代が作られます。新しいEvidenceに対して `fragment`、`embed`、`generate` を順に再実行します。旧世代・旧文書とその出典は保持します。

Prompt/LLM変更だけなら `fragment` 以降、Embedding変更だけなら `embed` 以降、Reranker/Final Prompt変更だけなら `generate` を再実行します。未知のrevisionは `unknown` と記録します。別モデル・revision・次元・prefix設定のVectorは混ぜません。

## 実サンプル評価とテスト

```powershell
python scripts/inventory_samples.py
python scripts/run_evaluation.py --phase deterministic
# 上記の実モデル設定を行ってから実行する
python scripts/run_evaluation.py --phase ai
python -m pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
git diff --check
```

評価結果は `.local/evaluation.json`、DBは `.local/evaluation.sqlite`、最終文書は `.local/documents/<document-id>.md` に保存します。`--phase all` は両段階を実行します。既に成功したFragment抽出は再開時に省略します。`--reprocess` は明示的な再実行用です。Import済みCaptureも検証してから重複扱いします。

AI評価は代表8件を選ぶ既定値です。106件すべてのImport/Extractを評価し、少数Captureで実LLMまでのVertical Sliceを評価する構成です。各Captureの段階別結果をレポートで確認できます。AI未選択CaptureをAI合格扱いしません。

長時間処理をWindowsで独立実行する例：

```powershell
$evaluationProcess = Start-Process -FilePath (Resolve-Path .venv/Scripts/python.exe).Path `
  -ArgumentList @('scripts/run_evaluation.py','--phase','all') `
  -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput .local/evaluation.stdout.log `
  -RedirectStandardError .local/evaluation.stderr.log
$evaluationProcess.Id
# 後で状態を確認する
(Get-Content .local/evaluation.json -Raw -Encoding UTF8 | ConvertFrom-Json).status
```

成功は `completed`、失敗を含む場合は `completed_with_failures` / `failed` です。失敗内容を確認して同じphaseを再開できます。

詳細は[暫定設計](PROTOTYPE.md)と[実サンプル評価](PROTOTYPE_EVALUATION.md)に記載します。
