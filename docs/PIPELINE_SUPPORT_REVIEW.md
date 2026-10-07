# 支持確認・監査表示の利用方法

実装日：2026-10-08。対象は既存Fragmentからの派生処理。Raw、Fragment本文、Claim本文、従来の完全Finalを修正して意味を合わせる処理ではない。

## 表示と支持判定

Viewの短い`[S番号]`から、同時出力する`.audit.json`の同じキーを参照する。付録にはClaim、支持Fragment、抽出run/job、実引用、引用ハッシュ、Evidence、Snapshot、正規化run、資料URL、帰属、時点、判定runを保持する。引用範囲は正規化Evidence内のUnicode文字位置`[start, end)`であり、元HTMLのバイト位置ではない。空白差を許容した一致でも元文字列の位置を保持する。

支持判定は`ai_runs`に追加し、既存の情報を書き換えない。

| 状態 | 意味 | 支持確認済みView |
|---|---|---|
| supported | 引用が主張の対象・述語・否定・範囲・時点・帰属を支持すると機械判定 | 掲載候補 |
| unsupported | 引用の不在、矛盾、根拠にない断定・帰属変更等 | 除外 |
| uncertain | 複合主張や文脈の不確定、判定入力の上限超過等 | 除外 |
| unreviewed | 現在の入力・判定契約に一致する判定がない | 除外 |

`supported`は資料との整合性判定であり、現実の真実性・公式設定・human goldの認定ではない。本文に隣接して資料筆者・CPCの推論・感想・宣伝等の帰属を表示する。既定Viewは未確認も状態付きで表示し、厳格な利用時は`--supported-only`を指定する。確認済みがゼロの場合も、未確認で穴埋めせず不足項目を返す。

判定前に引用の存在を確認する。入力上限を超える場合は全文を黙って切り詰めず`uncertain`にする。Schema外のフィールドや不正な判定結果は失敗として残し、掲載許可へ変換しない。入力、資料・引用、prompt/Schema、判定モデル・revision・設定、入力上限が同じ場合だけ再利用する。表示では最新の同じ監査入力・判定契約の結果を採用し、使用したモデルとrunを付録へ表示する。異なる判定モデルの結果を人間の承認として扱わない。

## CLI

既存のローカルLLM設定を使用する。Strataの場合は専用PowerShellで`. ./scripts/Use-Strata.ps1`を実行する。実Captureを外部サービスに送る設定変更は、この改修では行っていない。

```powershell
# shortで実際に表示する候補だけを有限件数で判定
cpc --db .local/cpc.sqlite support-review --entity <entity-id> --mode short --limit 10

# 判定がない候補は掲載しない
cpc --db .local/cpc.sqlite view --entity <entity-id> --supported-only --out .local/view.md

# 全Claimを保持する閲覧版。完全Finalも従来どおりDBへ生成・保存
cpc --db .local/cpc.sqlite generate --entity <entity-id> --format reading --out .local/reading.md
```

Viewの監査付録は`.audit.json`、省略理由は`.omitted.json`。閲覧用Finalは`C番号`を監査付録へ対応させ、資料URLとSnapshotの組合せを共有`S番号`で表示する。引用・Evidence・帰属・時点の個別対応は付録へ残す。本文・時系列の重複を省いた閲覧版は、完全Finalの置き換えではない。

Characterは定義・立場/所属・人物像、Workは定義・ジャンル・中心的な仕組み、Conceptは定義・目的・区別する特徴を先に選ぶ。同一項目の候補を繰り返す前に他の必要項目を探し、不足項目を表示する。既知の`conflict_group`に別主張がある場合は、その存在とClaim IDを表示する。一般的な意味矛盾の自動検出は保証しない。

AI入力の予算は本文と構造化Claimを別々に確認する。監査付録はAI入力に自動添付しない。既定counterはUTF-8バイト数による保守的尺度であり、実tokenizerではない。

## 復旧・計測

CompatibleLLM、Strata、LM Studio nativeの接続前エラー・ConnectTimeout・429・503は最大3試行、待機0.25秒/0.5秒。ReadTimeout、502、Schema違反、支持不整合、出力上限を同じ通信再試行で繰り返さない。各試行の時間・HTTP状態・例外分類を観測記録へ保存する。共有GPUサーバーの再起動はしない。抽出windowの既存再開・分割・有限Schema再試行は保持する。

小規模評価は元DBを読み取り専用でコピーし、別の私有ディレクトリへ出力する。

```powershell
. ./scripts/Use-Strata.ps1
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
.venv/Scripts/python.exe scripts/run_support_evaluation.py --live
# 停止後は同じ条件で --resume を追加
Get-Content sample/pipeline-improvement-evaluation/status.json
Get-Content sample/pipeline-improvement-evaluation/report.json
```

既定は表示候補3件、短い同一入力のwarmup 1回＋非キャッシュ3回。View・閲覧版・query例の動作、Fragment/元DB不変、DB整合性を確認する。成功済み工程は再実行しない。入力・runtime・判定契約が違う場合は再開を拒否する。statusの`completed`はこの工程の完了を意味し、品質の全件合格を意味しない。

`--labels <private.json>`には`claim_id`、`expected`、`label_channel`（human/curated_fixture/llm_judge）を持つ配列を指定する。正解ラベル未提供時は`gold_missing`であり、判定の成功数を精度として報告しない。品質の一致率・誤ったsupported数と、warm時間の中央値・範囲・失敗・キャッシュ数を別に集計する。工程時間、API観測のtoken/engine速度、端から端の時間も混同しない。

30〜50件の人手による判定器校正、20〜30質問の検索Recall/MRR評価、長短入力の固定条件比較、スリープ後のGPU復旧確認は、別途ラベル・実機確認を必要とする。この改修だけで完了扱いにしない。

意味判定の最小校正用に`benchmark/support-probes-v1.json`の合成9例（否定・対象・範囲・時点・帰属・曖昧な所属・複合主張等）を用意した。`scripts/run_support_probes.py`はこれらを判定し、前記の小規模評価DBの3候補を最新promptで再判定して表示を再生成する。合成例の参照ラベルは`curated_fixture`であり、人手による実Captureの正解とは区別する。再開は`--resume`。出力は`sample/pipeline-support-probes/`。

初回の実データ工程では表示候補3件の判定が完了し、元DB・Fragment不変、DB整合性`ok`・外部キーエラーなしを確認した。支持確認のwarm 3回は中央値3.95秒、範囲3.40〜4.50秒だった（短い同一入力、Strata、prompt v1、2026-10-08）。これは全Fragmentの処理時間や品質精度を表さない。箇条書きとURLから所属を推定した判定があったため、v2ではURL・共起だけを関係の根拠にしない指示を追加した。v1の判定をv2の確認済みとして再利用しない。

v2の合成9例は参照判定と8例一致し、誤った` supported`は0例だった。残る1例は、曖昧な箇条書きに対して参照は`uncertain`、モデルは`unsupported`と判定したもので、どちらも厳格Viewから除外する。これは小集合の校正結果であり、実Capture全件の精度ではない。実データ3候補はsupported 2件・uncertain 1件となり、曖昧な所属の掲載許可を取り消せた。

最新の通常ViewはCharacterのshort/standard/detailedが5/16/31件、Workが4/14/29件。今回確認した候補だけを許可するViewはCharacter 2件、未判定のWorkは0件で不足項目を表示する。閲覧版はCharacter 530 Claim・65,280文字、Work 4,761 Claim・628,968文字で、全5,291 Claimの本文と支持を保持した。完全Finalの生成・保持は別の経路で維持している。
