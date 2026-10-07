# 代表8CaptureのFragmentを使う後段試験計画

作成日：2026-10-07。対象は完了済みの再抽出比較V2。ユーザーはFragmentの内容を確認し、致命的な問題は見つからなかったと報告している。この入力受入を前提として後段を試験する。ただし、網羅的な意味品質の正解ラベルが作成されたとは扱わない。

## 目的と固定条件

変更前5,337件、変更後5,356件の有効なFragmentから、Claims・用途別View・Final Documentを作成し、実Embeddingと検索まで動作を確認する。両方に同じ現在の後段実装を適用するため、これは「入力Fragmentの差による下流出力比較」であり、旧後段実装と新後段実装の性能比較ではない。

- 入力：Git管理外の `sample/efficiency-capture-comparison-v2/{before,after}/captures.sqlite`。
- 試験DB：SQLite backup APIによる別コピー。入力DB・Fragment・Rawを変更しない。
- 対象：代表8Captureに対応する2 Entity。有効Fragment数を元のケース結果と照合する。
- Embedding：保存済みNomic Embed Text v1.5、LM Studio、CPUのみ。document/query prefixと600文字入力上限を両条件で固定する。実ファイルのmodel ID・ロード設定はローカルのsetupログへ保存する。
- 検索：既存manifestの6ケース、lexical/semantic/hybridを各Entityに実施、上位10件。rerankerは既存の `rrf60-literal-v1`。
- Final Document：既定の抽出型生成。LLMによる並べ替えは使わない。これは生成LLMの速度・品質試験ではない。既存Strataの設定を変更しない。
- View予算：short 4000、standard 12000、detailed 24000、context 12000。context長65536。既定counterはUTF-8バイト数の保守的尺度であり、実token計測とは表記を分ける。

## 試験項目と受入条件

| 工程 | 実施内容 | 合格条件 |
|---|---|---|
| 入力固定 | active Fragment数、入力DB指紋、Raw hash・更新日時確認 | 件数一致、試験後も入力DB・Fragment・Raw不変 |
| Knowledge Claim | 全有効Fragmentから生成 | 元Fragment全件がClaimの支持に残り、正規化以外の本文変更・帰属/時期/強度の変更がない |
| 用途別View | 2 Entity × 4 mode × 前後 | 予算内、選択と省略が全Claimを漏れ・重複なく分割、省略manifest出力 |
| Final Document | 2 Entity × 前後 | 全Fragmentの支持を保持、全件引用可能、情報種別の分類と帰属/時期/強度を保持 |
| 実Embedding | 前後それぞれの有効検索対象をCPUで処理 | APIによる実ベクトル、件数・次元整合、処理完了 |
| 増分Embedding | 同じDB・モデル設定で再実行 | inferred=0、全対象を再利用 |
| 検索 | 既存6ケース × 前後 | 非空、上位件数上限内、各結果から元Evidenceへ参照可能 |
| DB整合性 | 全工程の終了時 | integrity=ok、外部キーエラー0 |

検索Recall/MRR/nDCGは正解ラベルがないため未評価とする。非空の検索結果だけで意味的な検索品質を合格としない。生成資料の読みやすさ・意味的な支持の十分さは、人間が出力を確認する別項目とする。

## 予想時間と進め方

初回起動を含む暫定の予想は10〜60分。Claims/View/Finalの前後合計2〜15分、CPU Embedding・再利用・検索5〜30分、サービス起動と確認は数分〜15分を見込む。これは今回の実測前の幅のある見積もりであり、GPU LLMの予備試験速度から換算した値ではない。実測は工程別のsecondsへ記録する。

Embeddingサービス起動と独立して派生処理を先行試験できる。長時間処理はhidden processとして起動し、状態と工程結果をファイルへ保存する。完了済み工程を保持して再開する。

```powershell
# インストール済みPython環境で実行。Embeddingモデルは事前にCPUロードする
python scripts/run_fragment_downstream.py --revision nomic-v1.5-local-cpu --derived-only
# Embedding・検索へ続行
python scripts/run_fragment_downstream.py --revision nomic-v1.5-local-cpu --resume
# 状態確認
Get-Content sample/fragment-downstream/status.json
```

`derived_completed` は派生処理のみ完了、`completed` は全工程完了、`failed` は当該工程を調査する。失敗時は同一条件の `--resume` で成功済み工程を保持する。

## 成果物と公開範囲

`sample/fragment-downstream/` に前後のClaims、各Viewと省略manifest、Final Document、Embedding・検索結果、工程別時間、status.json、result.jsonを保存する。実データを含むためGit管理外で保持する。計画と試験ランナーのみをコミットする。評価結果を確認後、ユーザーが読める比較・評価を作成する。
