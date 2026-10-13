# Current SGOKB Search benchmark

Phase Iの現行Search評価正本は`search-quality-gold-v1.json`。外部Web内容に依存しないfrozen synthetic canonical Knowledgeで、Search contract / Similarity / Evidence / ANN / Reranker regressionに使用する。

```powershell
python scripts/run_search_quality_gold.py --local-files-only
python scripts/run_vector_backend_benchmark.py --count 100000 --hnsw-ef 768
python scripts/run_search_gold_reranker_benchmark.py
```

設計・結果: [`docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`](../docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md)

---

# Local AI comparison

次回のモデル比較は[モデル比較の実行計画](../docs/archive/prototype-0.2/MODEL_COMPARISON_PLAN.md)に従う。現行の8CaptureはPrompt修正にも使用済みのため、独立した未知データのtestとは扱わず、モデル比較用manifestと保留データを別に用意する。

`sample-v1.json`は代表8CaptureのFragment比較、2 Entity × 3検索方式、2 Finalの固定manifest。Raw UUID / SHA256で同一入力を確認し、本文はignored DBから解決する。validationとtestを分ける。現在human goldは未付与。自動引用率や件数をRecall/Precisionと呼ばない。

`configurations.example.json`は比較候補の一覧で、全モデルの取得・実行を意味しない。LLM・抽出方式・Embedding・Rerankerを一度に変更せず、同じmanifest、Prompt、Schema、予算の条件で比較する。LLM / embeddingのAPIはloopbackに限定する。Coreの一般Provider機能とbenchmarkのローカル限定を分離した。

```powershell
# 既存DBを破壊しない別DBで準備。初回評価DBが必要。
.venv/Scripts/python.exe scripts/run_upgrade_evaluation.py --phase prepare
# SGOKB_LLM_MODEL等を設定後、SinglePass / MultiPass / Extract+Reviewを別runに記録。
.venv/Scripts/python.exe -m sgokb --db .local/upgrade.sqlite benchmark benchmark/sample-v1.json --phase fragment --strategy single_pass
.venv/Scripts/python.exe -m sgokb --db .local/upgrade.sqlite benchmark benchmark/sample-v1.json --phase fragment --strategy high_recall_multi_pass
.venv/Scripts/python.exe -m sgokb --db .local/upgrade.sqlite benchmark benchmark/sample-v1.json --phase fragment --strategy extract_review
.venv/Scripts/python.exe -m sgokb --db .local/upgrade.sqlite embed
.venv/Scripts/python.exe -m sgokb --db .local/upgrade.sqlite benchmark benchmark/sample-v1.json --phase retrieval
.venv/Scripts/python.exe -m sgokb --db .local/upgrade.sqlite benchmark benchmark/sample-v1.json --phase final
.venv/Scripts/python.exe scripts/export_upgrade_review.py
.venv/Scripts/python.exe -m sgokb benchmark-score .local/human-labels.json
```

runは毎回UUIDを作り、旧runを上書きしない。`--resume <run-id>`は同じmanifest/hash/configurationで失敗・未処理caseだけ再開する。成功caseは再実行しない。datasetを編集した場合はbenchmark_versionも更新する。調整はvalidationを用い、testの採点結果で無断に調整しない。旧manifestをGit履歴に保持する。

Fragment方式3種類を実装した。Finalは既定のextractive hierarchyとcaseの`llm_order:true`による階層順列を比較できる。従来flat writerは`generate --legacy`で再現する。writer+reviewer等の新しい方式はApplication/LLM境界へ追加可能だが今回実装しない。RerankerはApplicationの注入引数で交換できる。BGE/Qwen専用モデルadapterの準備・実行は別評価作業。

## 記録

LM Studio native APIを使う場合は`SGOKB_LLM_PROVIDER=lmstudio`と`SGOKB_LLM_EXTRA_JSON={"reasoning":"off"}`を指定する。[公式API](https://lmstudio.ai/docs/developer/rest/chat)のsystem_promptとinputを分け、store=false・integrations=[]で呼ぶ。JSON grammarを強制する互換APIとは異なり、Schemaはsystem命令と応答検証で適用する。Providerを変えたrunは別条件として扱う。native adapterは対応パラメータ以外を拒否する。

benchmark runにモデル名/revision/configuration、Embedding model/revision/prefix/truncation、Reranker version、Prompt/Schema hash、dataset versionを記録する。Fragment jobにはNormalized IDとEvidence入力hash、AI runには実Prompt/Schema/input/output/実行日時を保持する。Provider応答からtoken数、秒数、tok/sを記録する。推論tokenと生成tokenの内訳はProviderが返すusageに依存する。

`SGOKB_RUNTIME_METADATA_JSON`でGGUF filename、quantization、runtime/version、context_length、GPU/VRAM/RAM条件を明示できる。temperature、reasoning_effort、seedはProvider configurationへ保存する。特定値が取得できない場合はnull / unknownとし、CLI commitと推論runtime versionを同一視しない。モデル名が同じでもrevision/量子化/runtime/Prompt/Schemaが違えば別条件。実行時のVRAM/RAM使用量は未計測ならnullで、搭載容量と区別する。

## Metricと判定経路

| 対象 | 自動集計 | 意味評価・goldが必要な項目 |
|---|---|---|
| Fragment | Evidence総数/実質本文数/引用数/0理由/件数/Coverage/平均 | Recall、Precision、Unsupported率、Epistemic分類精度、原子性 |
| Retrieval | 有効ID、rank。relevanceがあればRecall@K/MRR/nDCG | 関連性goldの付与 |
| Final | 文字数、Section数、分類ごとのCluster数、引用数、矛盾候補数 | 情報Coverage、Unsupported率、分類分離、構造、冗長性、矛盾保持、引用内容の妥当性 |

`retrieval_metrics`はcaseの`relevance:{target_id:grade}`を使う。未付与なら各値nullでgold_missing。意味評価は`labels.example.json`をコピーしignored `.local/`で付与して`benchmark-score`へ渡す。matched_gold_claim_idsによるRecall、supportedによるPrecision/Unsupported率、epistemic_correct、atomicを計算する。サンプルに含めたlabelは記入例で、実データ採点ではない。

channelはhumanまたはllm_judgeを明示する。自動値とは別結果として保存・比較し、Judgeの採点を正解データと同一視しない。Finalの意味評価値は付与値を取り込み、未付与はnull。意味の似たgold主張の自動照合はしない。部分annotationで得たPrecisionはそのannotation集合に対する値で、全件精度ではない。

## 長時間処理

```powershell
$job = Start-Process .venv/Scripts/python.exe -ArgumentList 'scripts/run_upgrade_evaluation.py','--phase','all' -WindowStyle Hidden -PassThru -RedirectStandardOutput .local/upgrade-job.log -RedirectStandardError .local/upgrade-job.err
$job.Id
Get-Process -Id <pid> -ErrorAction SilentlyContinue
Get-Content .local/upgrade-job.log -Tail 5
Get-Content .local/upgrade-job.err -Tail 10
```

起動確認後は待機のためだけの自動ポーリングをしない。ログのrun_idと`.local/upgrade-evaluation.json`でcase進捗を確認する。成功はbenchmark complete、Raw不変、integrity ok、foreign key errorなし。失敗はfailed/incomplete caseまたはerrの例外。再開は同一envで`--resume <run-id>`。新しいPrompt/modelの場合はresumeせず新規runにする。
