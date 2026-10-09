# LLM出力速度の予備試験計画

> **Archived / Historical** — Rename前のPrototypeの記録です。旧名称・コマンド・パスは当時の事実を保持しており、現行操作は[README](../README.md)を参照してください。

作成日・更新日: 2026-10-06。既存8モデルの再試験とStrata追加試験が終了した。[測定結果と制約](MODEL_SPEED_PREFLIGHT_RESULTS.md)を参照。以下の共通条件・手順は元のLM Studio試験を示し、Strataの構成差は追加条件として記録する。

## 目的

本試験前に8モデルの出力速度と応答時間を同じ短い入力で測り、実行可能性と本試験の所要時間を確認する。速度と回答品質は別に判定する。高速でもJSON・引用契約に違反するモデルを、CPCに適したモデルとは評価しない。

## 対象モデル

| ID | モデル |
|---|---|
| L01 | Qwen3.8-27B |
| L02 | GPT-OSS 20B |
| L03 | Gemma 4 26B-A4B |
| L04 | Mistral Small 3.2 24B |
| L05 | Ministral 3 14B |
| L06 | Nemotron 3 Nano 30B-A3B |
| L07 | meta/muse-glimmer |
| L08 | google/gemma-4-31b-qat |
| L09 | Strata / Qwen3.8-Flash-Next IQ3_S（追加runtime条件） |

L09は`run_strata_speed_preflight.py`で同じ固定S01/S02/S03を各ウォームアップ1回＋本測定3回、計12要求測定する。入力・Prompt・出力上限・temperature・条件順を既存試験に合わせ、入力ハッシュ一致を確認する。既存サーバーのcontext65536・projection有効を保持し、engine 0.1.39と共に構成を記録する。互換API、enable_thinking=false、Prompt内Schema指定で実行し、CPC契約検証は共通関数を使用する。ロード・アンロードと終了時Qwen再測定は行わず、既存8モデルの保存済み結果と比較する。StrataのTTFT・推論token内訳はAPIにない場合nullとする。LM Studioと同一runtime条件であるとは扱わない。

本試験で使うGGUF・量子化をそのまま使用する。モデル系列だけでなく量子化とruntimeを含む構成の比較である。未取得・未対応・ロード失敗は未測定として記録する。Phi-4はReviewer速度を確認したい場合の追加枠で、上記8モデルの集計とは分ける。EmbeddingとRerankerは生成token速度を同じ尺度で比べず、別の予備測定で件数/秒・query遅延を測る。

## 共通条件

- 同じPC、LM Studio native API、runtime、GPU設定で、同時に1モデル・1リクエストだけ実行する。
- context 16384、temperature 0、store=false、integrations=[]、会話履歴なしを固定する。初回はreasoning offを共通指定した。再試験では`GET /api/v1/models`の対応設定を確認し、off対応ならoff、設定非公開ならパラメータ省略、推論必須なら対応する最小設定を選ぶ。
- seedは全対象で共通指定できる場合だけ固定する。他のsampling値は指定有無・実効値を記録し、黙ってモデル別に変更しない。
- 他の推論・Embedding・モデルダウンロードを停止または別時間へ分離してから測定する。CPU offloadが発生したモデルはGPU中心のモデルとは別列にし、速度差の原因を示す。
- ファイル名・SHA256、量子化、モデルrevision、runtime version、GPU offload、CPU thread設定、context長を記録する。不明な値はunknown/null。
- Native API非対応は接続不適合とする。reasoning条件は`S01-R-off`、`S01-R-low`、`S01-R-on`、`S01-R-omitted`のように区別し、推論ありの結果をoffと同一条件と扱わない。実行開始時の対応設定を保存し、再開時に変化していれば停止する。
- 入力の本文・Prompt・Schemaと、そのhashをモデル間で固定する。同じ文字列でもtokenizerごとに入力token数が異なるため、実際の入力token数も記録する。

## 入力セット

実ページの機密情報を含まない固定の架空資料を用意し、試験開始前にUTF-8ファイルとして凍結する。モデルごとにPromptを調整しない。

| 条件 | 入力 | 出力設定 | 主な測定目的 |
|---|---|---|---|
| S01 短い入力 | 同じ日本語資料約300文字＋共通の生成指示 | 最大1024 tokens | 入力が短い場合の出力速度 |
| S02 長い入力 | 同じ日本語資料約2000文字＋S01と同じ生成指示 | 最大1024 tokens | 入力処理量が応答時間に与える影響 |
| S03 CPC形式 | 約480文字の架空Evidence、同じPage Context・Entity・隣接資料、現行Prompt/動的Schema/quote_choices | 最大8192 tokens | 実際の抽出に近い速度と契約適合 |

S01/S02は「資料に基づく説明を番号付きで続ける」同じ長めの出力指示を使う。十分な出力長を狙うが、EOSを抑制して無理に生成を続けさせない。早期終了時は実出力長を残し、token数の異なる応答を同じ所要時間の比較と扱わない。

S03は同じ主張密度の固定Evidenceを使い、引用ID・Schema・原子性の宣言を検証する。適応分割と検証再試行はこの単発測定では起動しない。これらを含む総所要時間は本試験で別に測る。

最大token数到達の扱いを分ける。S01/S02では速度測定用の予算終了として記録できるが、回答完了とはしない。S03では出力上限による不完全応答をCPC不適合として記録する。途中のJSONを修復して採用しない。

## 手順・試行数

1. 保存状況・API対応・実行環境を確認し、各モデルの設定台帳を作る。
2. Qwenで3入力の接続とstats取得を確認する。修正が必要なら全モデル試験前に入力を確定する。
3. L01〜L08の順にモデルを1つずつロードする。ロード開始から完了までを別計測する。
4. 各条件について最初の1回をウォームアップとして実行し、参考値として保存する。
5. 同じ条件を3回測定し、中央値と最小〜最大を集計する。条件順はS01→S02→S03で統一する。
6. 終了後は試験でロードしたモデルだけをアンロードし、次のモデルへ進む。ユーザーが使用中のモデルを無断でアンロードしない。
7. Qwenの3条件を最後に各1回再測定し、負荷・温度・runtime状態の変化が最初との比較に影響していないか確認する。初回の3回集計へ混ぜない。

基本試行数は8モデル×3条件×（ウォームアップ1＋測定3）＝96リクエスト。最後のQwen確認3リクエストと接続確認は別枠。非対応のモデルの試行を自動で別モデルへ置き換えない。

ロード直後の初回とウォームアップ後の値を分離する。store=falseでも内部prefix/KV cacheが無効とは限らない。cacheの状態を記録し、不明ならTTFTを「cold cache性能」と呼ばない。

## 測定する指標

| 指標 | 定義・記録方法 |
|---|---|
| 出力速度 tokens/s | LM Studioが返すstats.tokens_per_second。生成処理の速度として表示 |
| 最初のtokenまでの時間 | stats.time_to_first_token_secondsが取得できる場合のエンジン側TTFT。clientの通信を含む値とは区別 |
| 1リクエストの総時間 | clientで送信直前から全文受信完了まで測る。入力処理・通信等を含む |
| 実出力量 | output tokens、reasoning tokens、本文文字数を別々に記録 |
| 本文文字数/秒 | 本文文字数÷総時間。日本語の実用的な参考値で、純粋なdecode速度とは区別 |
| ロード時間 | モデルロード開始〜完了。リクエスト時間に混ぜない |
| メモリ | ロード後VRAM/RAM、測定中の最大値が取得できれば記録。観測方法・間隔を示し、未取得はnull |
| 応答状態 | 完了、予算到達、空応答、timeout、API不適合、JSON/Schema/引用違反を分離 |

APIの生成tokens/sが得られない場合はnullとし、出力tokens÷総時間を「end-to-end tokens/s」という別指標で表示する。総時間には入力処理も入るので、生成tokens/sと同じ列で順位を付けない。推論tokenの内訳が取得できないモデルは、本文だけのtoken速度を推定しない。

再試験ではtotal_output_tokensとreasoning_output_tokens、その差である本文token数を記録する。内訳が欠ける場合は本文token数をnullとする。APIのtokens/sは推論を含む値として表示し、本文の純粋なdecode速度へ読み替えない。推論あり・内訳不明の測定からoff条件を基準とした本試験時間を自動換算しない。

tokenizerが異なるためtokens/sだけで日本語の実用速度を断定しない。本文文字数/秒・実出力長・総時間を並べて判断する。3回では統計的な優劣を確定せず、速度差が小さい候補は本試験で再確認する。

## 終了・失敗条件

- 1リクエストは初期timeout 180秒。モデルロードは10分で初期打切りとする。これは運用上の暫定予算で、モデルの性能合格基準ではない。
- 同じ条件でtimeout/OOM/APIエラーが2回続いた場合は、その条件の後続試行を打ち切り、未測定数と理由を残す。負荷原因を確認せず繰り返し再起動しない。
- 推論以外の処理が重なった試行は結果を破棄せず「干渉あり」と記録し、正常条件で再測定した行と分ける。
- 生出力・stats・client時間を保存する。出力上限時も本文を保存し、途中結果の復元やCPCへの昇格は行わない。
- 速度計測は予算到達した応答でも可能だが、CPC適合の成功率はS03の検証結果で別に示す。

## 予想時間と本試験への反映

同じGPU上で実行でき、出力が約1024 tokensに達するS01/S02を20〜120 tokens/sで仮置きすると、1応答の生成部分は約9〜52秒。S03は出力量・Prompt処理によって数十秒〜数分になる。

ロード・ウォームアップ・反復・記録を含め、8モデル全体で約1〜3時間を初期目安にする。20 tokens/sは実測した最低速度ではなく見積もり用の仮定。CPU offload、非対応の調査、ダウンロード、runner実装は別時間。初回Qwenの実測後に見積もりを更新する。

本試験時間は、単純にtokens/sの順位だけで割り算しない。参考値として

`モデル別推定時間 ≈ Qwenの実測5.11時間 ×（モデルのTTFT＋基準出力token数÷モデル生成tokens/s）÷（QwenのTTFT＋同じ基準出力token数÷Qwen生成tokens/s）`

を使い、S03の長さ、モデルごとの出力量・失敗・再試行・適応分割の差を別に加味する。この式は概算であり、8Captureでの時間を保証しない。S03予算到達や契約違反が多いモデルは、本試験の見積もりに追加調査・分割の負荷を明示する。

## 出力と実行方法

`sample/モデル比較/予備速度試験/`へ次を出力する。

- `速度比較.txt`: モデル、量子化、GPU/CPU配置、S01/S02/S03の中央値、時間の幅、CPC適合、未実行理由、所要時間の見積もり。
- `速度比較.csv`: 全試行の条件・統計量・観測方法。ウォームアップと本測定を明示。
- モデル別の生応答・stats・Prompt/input hashと、実行環境・run ID。

表示例（数値は実測後に記入）:

| モデル | 条件 | 生成tokens/s中央値 | TTFT | 総時間 | 出力tokens / 文字数 | CPC適合 |
|---|---|---:|---:|---:|---|---|
| Qwen3.8-27B | S03 | 未測定 | 未測定 | 未測定 | 未測定 | 未測定 |
| その他7モデル | S01〜S03 | 未測定 | 未測定 | 未測定 | 未測定 | 未測定 |

専用runnerは`scripts/run_speed_preflight.py`に実装した。CPC経路では出力上限を失敗として扱うため、S01/S02の速度記録用経路を分けている。モデルの逐次ロード、96試行と最後のQwen確認、timeout・打切り、各試行のcheckpoint、CSV/日本語比較出力を行い、会話や既存benchmark DBを変更しない。Ministralは今回保存済みの`mistralai/ministral-3-14b-reasoning`を使用し、通常版とは区別して記録する。

```powershell
# 独立プロセスで起動し、ログはGit管理外へ保存する。
$job = Start-Process .venv/Scripts/python.exe -ArgumentList 'scripts/run_speed_preflight.py --out sample/speed-preflight-v2' -WindowStyle Hidden -PassThru -RedirectStandardOutput .local/speed-preflight-v2.log -RedirectStandardError .local/speed-preflight-v2.err
$job.Id
Get-Content sample/speed-preflight-v2/status.json -Encoding UTF8
# 中断後は、入力を変更せず--resumeで未測定分を続行する。
# 初回runはrunner_versionが異なるため再開せず、新しい出力先を使用する。
```

runnerは独立したバックグラウンド処理として起動し、PID・状態確認コマンド・成功/失敗条件を提示する。待機目的の自動ポーリングは行わない。status.jsonのcompletedは測定工程の終了を意味し、全モデルのCPC適合ではない。failedは処理全体の停止で、モデル別・条件別の不適合は比較結果に記録する。
