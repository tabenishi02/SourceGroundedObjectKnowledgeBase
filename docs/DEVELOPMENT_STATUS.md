# 開発状況まとめ

更新日: 2026-10-06。現在はPrototype 0.2の実装と初回実データ評価が済み、モデル選定・運用負荷の評価へ進んだ段階。最終製品の品質保証や日常運用の完成を意味しない。

## 実装・確認済み

| 範囲 | 状況 |
|---|---|
| Web Page Capture Chrome拡張・Native Host | ZIP取得・ローカル保存を実装。手動確認で成功通知、MHTML表示、既存ZIP非上書き、Host未登録と書き込み不能時の失敗・復旧を確認。MHTML取得失敗は自動テストを根拠とし、実機再現は未実施 |
| Raw Import・Evidence | ZIP/checksum/重複/世代/出典追跡、構造・Page Context処理を実装。106 CaptureをUpgrade Extractorで再処理し、現行Evidenceは5068件 |
| Fragment抽出 | 全Evidence評価・0件理由、分類、主語解決、引用ID、480字から最小120字への適応分割、再開・世代昇格を実装 |
| 検索 | Lexical / Semantic / Hybrid、Embedding空間分離、metadata filter、現行の簡易Rerankerを実装 |
| Final Document | 情報種別を分離した構造、出典・保守的重複集約・矛盾候補・抽出的表示を実装。既定生成はLLMを使わない |
| 評価・比較出力 | 固定manifest、自動の契約検証、人間評価値の未付与表示、Evidence/Fragment/Final比較出力を実装 |
| 速度予備試験 | 8モデル・3条件・ウォームアップと反復・終了時Qwen確認、checkpoint、CSV/日本語集計を実装。モデル対応reasoning設定を選択し、推論条件と本文/推論tokenを区別 |

## 実データ評価

代表8CaptureのFragment抽出、検索6ケース、Final 2ケースがすべて完了した。各工程でRawのSHA256・更新日時不変、SQLite integrity正常、外部キーエラーなし。
代表8件は737 Evidenceから5246 Fragmentを生成。Qwenによる抽出は約5.1時間で、ページごとの幅は約1.6～143分。
意味的な品質goldは未付与で、Recall/Precision、検索Recall@K/MRR/nDCG、Finalの意味上の忠実さは未評価。契約検証の成功を品質合格とは表示しない。

FinalはCharacter約50万字、Work約378万字。根拠全文の反復と主張の重複が多く、人間が毎回全文確認する運用には長すぎる。矛盾候補には異なる時期・論点を混同した例があり、判定改善が必要。

詳細: [Prototype実データ評価](PROTOTYPE_EVALUATION.md)、[Upgrade設計](PROTOTYPE_UPGRADE.md)。

## 速度予備試験

再試験run `33753177-953d-4a1c-89d4-ee56a419ffd6`は99リクエストを完了。8モデルすべての速度を取得し、API拒否・timeoutは0件。CPC抽出条件の本測定3回の中央値は次のとおり。

| モデル | reasoning指定 | API生成tokens/s | CPC形式適合 |
|---|---|---:|---:|
| Qwen3.8-27B | off | 120.09 | 3/3 |
| GPT-OSS 20B | low | 188.52 | 3/3 |
| Gemma 4 26B-A4B QAT | off | 167.19 | 0/3 |
| Mistral Small 3.2 24B | 省略 | 56.62 | 3/3 |
| Ministral 3 14B Reasoning | on | 85.60 | 0/3 |
| Nemotron 3 Nano 30B A3B | off | 61.64 | 3/3 |
| Muse Glimmer | low | 47.62 | 3/3 |
| Gemma 4 31B QAT | off | 40.55 | 3/3 |

推論ありのtokens/sは本文だけの速度とは比較できない。Gemma 26BはJSON後の説明文、Ministralは必須subjectのnullで失敗。全モデルの実データ抽出品質比較はまだ実施していない。
詳細: [予備試験結果](MODEL_SPEED_PREFLIGHT_RESULTS.md)、[モデル比較計画](MODEL_COMPARISON_PLAN.md)、[予備試験計画](MODEL_SPEED_PREFLIGHT_PLAN.md)。

## 運用・速度・費用の調査

- [実運用時間の評価](OPERATION_TIME_ESTIMATE.md): Qwenで数件/日を夜間に抽出し翌日検索する運用は条件付きで可能。大量処理・即時全量解析・Final全文承認は困難。
- [速度ボトルネック調査](PROCESSING_BOTTLENECK_REVIEW.md): 1038推論・約194万出力token、AI応答待ちは全体の99%以上。上限時の不要な再試行、PromptだけのJSON制約、詳細出力の反復、window処理回数が改善対象。
- [クラウド費用試算](CLOUD_AI_COST_ESTIMATE.md): 同じ8件のtoken量を通常料金で処理するとSol約4345円、Opus約8690円（1 USD=150円の仮定、税別）。低価格モデルまたはローカル併用を比較する案。クラウド速度は未測定、外部送信・課金・Provider移行は未実施。

これらは調査と提案。速度改善、Final短縮、変更分Embedding、クラウド経路のコード実装はまだ行っていない。

## 次の作業

1. 出力上限時の即時分割とSchema制約付き生成を独立した変更として比較し、形式失敗・不要再生成を減らす。
2. コンパクトなLLM出力、入力単位の調整、window checkpointを比較する。引用・全文coverage・Raw・DBの契約を維持する。
3. 人間goldを作成し、代表Captureと未使用資料でモデル別の品質・総時間を比較する。予備速度だけで採用モデルを決めない。
4. Finalの短い表示と参照形式、時間文脈を含む矛盾候補、変更分Embeddingを改善する。
5. 多言語Embedding・学習済みReranker・Final並べ替えの実モデル比較を進める。未取得モデルや未実装adapterの条件を先に確認する。
6. クラウド案を採用する場合は、送信対象と予算を明示した別試験を行う。現行benchmarkのローカル限定契約は維持する。

## 検証とGit

Upgrade本体の直近確認はpytest 57件とRuff成功。速度runner追加・修正後は関連pytest 6件、Ruff、差分チェック成功。今回のpush準備では速度runner関連チェックと公開差分確認を行う。過去の実機結果と今回の自動チェックを区別する。
実Capture、DB、生応答、比較の全文、ログ、モデルは`sample/`・`.local/`等のGit管理外に保持し、公開対象へ含めない。
開発ブランチは`feature/cpc-prototype-upgrade`。既存PR #5のbaseは`feature/cpc-prototype`。今回の依頼では現在の開発ブランチをpushし、mainへのmergeやブランチ削除は行わない。
