# Strataの利用可能性調査

> **Archived / Historical** — Rename前のPrototypeの記録です。旧名称・コマンド・パスは当時の事実を保持しており、現行操作は[README](../../../README.md)を参照してください。

調査日: 2026-10-06。対象は既存のStrata checkoutと分離されたStrata-data。Strataのファイル・設定・モデルを変更せず、起動・停止・アンロードを行わなかった。
上流: [Niko1221/Strata](https://github.com/Niko1221/Strata)。これはQwen3.8-Flash-Nextのローカル推論環境で、クラウドAPI費用は発生しない。電力・メモリ・GPU等の資源は使用する。

## 結論

### CPC用動作環境の追加（2026-10-06）

比較候補に **L09: Strata / Qwen3.8-Flash-Next IQ3_S** を追加した。
`StrataLLM`はCPCの通常経路で選択でき、HTTP 502の`structured_output_failed`を
検証再試行へ渡す。`finish_reason=length`の場合のみ出力予算超過へ分類し、
既存の適応分割を使用する。他のHTTP障害はHTTPエラーのまま保持する。

リポジトリ直下の専用PowerShellセッションで、次の設定を読み込む。
既にロード済みのサーバーを確認し、engine・context・control vectorを実測設定へ記録する。
Embeddingの接続設定は別途必要で、StrataにはテキストEmbedding APIがない。

```powershell
. ./scripts/Use-Strata.ps1
./.venv/Scripts/python.exe scripts/run_strata_preflight.py --trials 3
Get-Content .local/strata-preflight/status.json
```

再実行時は`--out .local/strata-preflight-02`のように新しい出力先を指定する。
既存結果の上書きは拒否する。

このrunnerは既存予備試験の固定S03入力・Prompt・Schema・8192 token上限を使う。
ウォームアップ1回と測定3回を逐次実行し、CPCの引用選択Schema・引用一致・全Evidence評価を検証する。
総所要時間とengineのdecode速度を別々に記録し、入力ハッシュ・構成・生成JSON・復元Fragmentを
Git管理外の`.local/strata-preflight/`に保存する。既存CPC DBやRawは変更しない。
サーバーが他の要求を処理中なら停止する。S01/S02の速度試験、代表8Captureの主比較、
人間goldによる品質評価はこの短い動作試験に含めない。

実機結果: ウォームアップと測定3回のすべてで契約検証に成功し、毎回6件のFragmentを抽出した。
engine=0.1.39、context=65536、control vector=`project:4-44`、projection有効。

| 回 | 総所要時間 | engine decode速度 | CPC検証 | Fragment数 |
|---|---:|---:|---|---:|
| ウォームアップ | 31.45秒 | 55.4 tokens/s | 成功 | 6 |
| 測定1 | 28.66秒 | 52.6 tokens/s | 成功 | 6 |
| 測定2 | 27.09秒 | 56.3 tokens/s | 成功 | 6 |
| 測定3 | 24.69秒 | 61.2 tokens/s | 成功 | 6 |
| 測定中央値 | 27.09秒 | 56.3 tokens/s | 3/3成功 | 6 |

固定入力ハッシュ: `cdf0973526880ce04becfe7aae40a1e9e7b50f0f275d7d125cbc8b27a80b21dd`。
これは出力形式・引用・網羅性の動作確認であり、抽出内容の正確性や取りこぼしを人間goldで評価した結果ではない。
測定は既にロード済みの同一モデルに対する逐次要求であり、後続回のキャッシュ効果を含む。
詳細は`.local/strata-preflight/status.json`、生成結果は`fragments-0.json`〜`fragments-3.json`。

### 既存8モデルと同じ速度予備試験

`scripts/run_strata_speed_preflight.py`は固定S01/S02/S03を各ウォームアップ1回＋測定3回、
計12要求で実行する。初期動作試験とは別runで、S03のサーバー側`response_format`指定を
省略し、既存LM Studio Native試験と同じPrompt内Schema・入力文字列・出力上限を使用する。
応答は既存の`response_record()`でCPC契約検証し、打ち切り応答も速度測定として保持する。

```powershell
./.venv/Scripts/python.exe scripts/run_strata_speed_preflight.py
Get-Content sample/strata-speed-preflight/status.json
# 中断した場合の未測定分の再開
./.venv/Scripts/python.exe scripts/run_strata_speed_preflight.py --resume
```

出力はGit管理外の`sample/strata-speed-preflight/`。`速度比較.txt`は既存8モデルの保存済み
runとStrataを並べ、条件ごとの生成tokens/s、S03本文文字/秒・総時間・CPC適合率を表示する。
`速度比較.csv`には試行別値、生応答JSONにはusage・timings・本文を保存する。
入力ハッシュが既存runと一致しない場合は比較を拒否する。
completedは12要求の速度試験終了を示し、S03契約違反やS01/S02予算到達は行ごとに区別する。
API障害・共有サーバー使用中・構成変更はfailedとして残す。
`--resume`は既に記録済みの試行を保持し、未記録分だけを実行する。

Strataの既存context65536とprojection設定を保持し、runtime.jsonへ記録する。
LM Studioのcontext16384とは異なるruntime条件として比較する。Strataの非streaming APIから
TTFTは取得できないためnullとし、入力処理時間から推測しない。推論token内訳もAPIにない場合はnull。
既存8モデルの再ロード・再実行や、代表8Captureの品質評価は行わない。

追加速度試験は全12要求completed、S03適合3/3。S01/S02/S03中央値は77.90 / 89.50 / 90.40 tokens/s、S03総時間16.67秒。初期動作試験とはSchemaの渡し方も異なるため、比較には[追加予備試験結果](MODEL_SPEED_PREFLIGHT_RESULTS.md)を使用する。

## 実装前の調査記録

以下はStrata接続追加前の調査記録である。エラー分類・専用runnerの課題は上記で対応済み。jsonschema依存追加、Embedding併用、代表8Captureの品質評価は完了していない。下記の設定案は当時の互換接続例で、現在の推奨設定は`Use-Strata.ps1`と専用Providerである。

このプロジェクトのLLMとして利用可能。既存の`CompatibleLLM`で通常のOpenAI互換接続ができ、架空資料による最小JSON抽出を実機で確認した。
ただしCPCの全Schema・長い実ページ・中断再開まで確認したものではない。出力上限等のエラー処理と、既存プロジェクトとの資源共有を整えてから、別構成として実データ比較するのが妥当。速度改善や採用モデルの確定はまだ判断できない。

## 現在の環境と確認結果

| 項目 | 確認した状態 |
|---|---|
| Strata checkout | commit `7a3ad6a` |
| 稼働API | `http://127.0.0.1:8080` |
| `/health` | status=ok、loaded=true |
| `/v1/models` | `qwen3.8-flash-next-iq3_s`、text入出力 |
| エンジン | 0.1.39 |
| context | 65536 token |
| 同時処理 | serving=1。待機中の他要求は順番待ちになる |
| Vision | 無効。CPCの本文抽出には不要 |
| structured output | json_object / json_schema、prompt_and_validate、constrained_decoding=false |
| 既存設定 | experimental speed projectionが有効。設定・実行中エンジン情報にprojectionの使用を確認 |

CPC側`CompatibleLLM.complete()`から、system/user messages、temperature=0、max_tokens=256、`chat_template_kwargs.enable_thinking=false`、小さな`response_format.json_schema`を送った。
subject / statement / evidence_idの3項目を持つJSONを受信し、CPC側でSchema検証に成功。架空の資料のみ使用し、DBに書き込んでいない。
観測は入力181 token・出力30 token・総時間約2.30秒。この短い1回から生成速度を評価しない。現行CompatibleLLMのtokens_per_secondは通信・prefill込みの出力token/総時間であり、LM Studioのdecode速度とは直接比較できない。
詳細な確認記録はGit管理外の`.local/strata-compatibility-check.json`へ保存した。

## 接続設定案

新しいPowerShellセッションで使う例。既存設定を共有するセッションへ無条件に上書きしない。

```powershell
$env:CPC_LLM_PROVIDER = 'compatible'
$env:CPC_LLM_BASE_URL = 'http://127.0.0.1:8080/v1'
$env:CPC_LLM_MODEL = 'qwen3.8-flash-next-iq3_s'
$env:CPC_LLM_REVISION = 'Strata-7a3ad6a;engine-0.1.39;IQ3_S;upstream-model-revision-unknown'
$env:CPC_LLM_MAX_TOKENS = '8192'
$env:CPC_API_TIMEOUT = '180'
$env:CPC_LLM_EXTRA_JSON = '{"chat_template_kwargs":{"enable_thinking":false}}'
# 過去のLM Studio専用設定やresponse_format=textへの回避設定を混ぜない。
Remove-Item Env:CPC_LLM_FRAGMENT_EXTRA_JSON -ErrorAction SilentlyContinue
Remove-Item Env:CPC_LLM_FINAL_EXTRA_JSON -ErrorAction SilentlyContinue
```

これは設定案。永続設定や既存プロジェクトの設定は変更していない。max_tokens=8192は現行比較の基準で、Schema失敗やtimeoutを防ぐ保証ではない。Strata側の共有samplingやprojection設定も構成台帳へ記録する。
`CPC_LLM_PROVIDER=lmstudio`は`/api/v1/chat`を使うため、Strataへはそのまま接続しない。

## 統合上の課題

1. **Schema制約の意味。** StrataはPromptで形式を指定し、生成後に検証する。grammarによる生成中の制約はない。さらに今回、Strataの`.venv`でjsonschemaパッケージを確認できなかった。実装はこの依存がない場合、JSON objectであることだけを検証するfallbackを持つため、現行環境でサーバー側の完全なSchema検証を前提にしない。最小テストのSchema検証はCPC側で行ったもの。CPC側の引用・全Evidence評価・主張契約検証は引き続き必要。依存追加は既存プロジェクトへの変更となるため本調査では行っていない。
2. **エラーの整合。** Strataは`finish_reason != stop`やJSON/Schema違反を`structured_output_failed`としてHTTPエラーにする。通常の非streaming経路では502。現行CPCは`raise_for_status()`によるHTTPStatusErrorをValueErrorへ分類しないため、引用検証再試行や出力上限時の適応分割へ進まず、該当バッチが失敗する可能性がある。上限を表すエラーだけを既存の分割理由へ対応させ、形式違反・通信障害・推論障害を分離する必要がある。すべての502を再分割しない。
3. **Embeddingは別。** 調査したサーバーは生成モデルと画像入力用処理を持つが、テキスト検索用`/v1/embeddings`の提供経路は確認できなかった。Nomic等の既存Embedding接続先を維持する。LLMとEmbeddingはこのプロジェクトで別々に設定できる。
4. **既存プロジェクトと共有。** parallel=1の同じサーバーを使えば処理待ちとcacheの影響が出る。StrataはGPUと大量のRAMを使用するため、LM Studioの大型モデルと同時ロードして速度・空きVRAMを悪化させない計画が必要。利用時間を分ける案を先に検討する。既存サーバーは本調査で変更していない。
5. **実験的projection。** 現在有効なprojectionはモデル挙動を変える構成で、単なる速度設定として扱わない。CPCの抽出忠実さ・取りこぼしへの影響は未評価。projection有無を別条件にし、既存プロジェクトを動かしたままグローバル設定を変更しない。
6. **既存速度runnerはLM Studio専用。** `run_speed_preflight.py`はlms CLI・Native API・GGUF inventoryを前提にするため、URLだけ変更してStrataを測定できない。Strata用の実行経路と、timings.predicted_per_second / usage /総時間を取得する比較が必要。通常benchmarkはloopback接続を許可するので、Strataはローカル限定方針に合う。

エラー処理とstructured outputの根拠は、ローカル`serve/server.py`・`serve/structured.py`・`src/cpc/providers.py`・`src/cpc/capture.py`の照合。上流の説明だけでローカル版の対応を断定していない。

## 速度の判断と次の確認

既存Strata-dataの別用途試験では、512出力tokenの日本語でdecode約73.1 tokens/s、projection比較で平均約91.6（無効）/103.1（有効）tokens/sの記録がある。条件・Prompt・出力量がCPCと違うため、Qwen3.8-27BのCPC予備試験約120 tokens/sから単純な倍率換算はしない。
これらの記録からStrataがCPCを必ず高速化するとはいえない。一方、モデルの抽出品質が改善し再試行・分割回数を減らせる可能性はあり、実データで評価する価値がある。

推奨順序は、エラー分類の整合→固定CPC入力で3回の形式・引用・速度確認→軽い/中規模/重いCaptureの比較→代表8Capture。入力・Prompt・Schema、reasoningとprojection設定、全実行時間、出力token、分割・再試行数を記録し、人間goldで品質を比較する。
本調査で確認済みなのは稼働状態と最小JSON接続。完全なCPC抽出、Embedding併用、実ページ性能、projectionによる品質差は未確認。
