# Prototype Upgrade v0.2

知識の取得では高Recall、消費・生成では高Precisionを優先する。初回版の上位Evidence選択と短いFinalを既定動作から外した。Raw ZIPとChrome拡張機能は変更しない。

## Architecture

```text
Raw → Source / Snapshot → Main Content Extraction → Normalized generation
                         └→ Page Context revision ──────────┐
                         Evidence全件 → bounded LLM batches ←┘
                         → assessment / Raw Fragment Store
                         → Search / facet + epistemic grouping / derived clusters
                         → Structured Final Representation → Markdown / JSON / AI context
```

`context.py`は決定的解析、`capture.py`は全Evidenceの抽出と検証、`final.py`は派生Clusterと構造化生成、`benchmark.py`は比較と評価の境界。SQLはRepository層に集約する。LLM / Embedder / VectorIndex / Rerankerは交換可能な既存境界を維持した。

## Evidenceと本文抽出

既存OSSのBeautifulSoupを基盤に、main/article/wiki/article-body/entry-content等の構造と本文量・リンク量のスコアを使う。ナビ、サイドバー、フッター、パンくず、共有ボタン、広告、関連記事・商品推薦・ランキングの明確なwidgetを除く。関連記事見出し配下はリンク優勢の場合だけ除く。関連作品に言及する本文は削除しない。

Trafilatura等への本文置換は今回は採用しない。表・リスト・引用・投稿の境界と元DOM位置を保持するため、既存DOMの構造抽出を拡張した。長大な独自記事判定器は導入しない。サイト全般の完全な本文抽出は保証しない。サイト固有Extractorの追加と実サンプルの欠落確認は継続課題。

位置をDOM削除前に付ける。FragmentからEvidence→Normalized→Snapshot→Source→Raw SHA256 / Artifact / DOM位置へ戻れる。デフォルトChunkは1000文字・100文字overlap。掲示板は投稿境界を維持する。heading単独を実質本文と扱わず、paragraph/table/list/quote/post/codeを実質本文の暫定候補とする。これは機械的な分母定義であり、内容の正しさの判定ではない。

## Page Context

`page_contexts`をNormalized generationとSnapshotへ結び付ける。Evidenceへ複製しない。JSONには次を保持する。

| 属性 | 内容 |
|---|---|
| source_type | official / encyclopedia / wiki / blog / news / bbs / social / commerce / generic等 |
| publisher_type | official / editorial / community / individual / anonymous / commercial / unknown |
| page_purpose | work_introduction / character_profile / concept_explanation / product_description / product_review / news_report / opinion / analysis / discussion / daily_post / fan_creation / guide / unknown等 |
| page_summary | descriptionまたは抽出本文の抜粋。LLMの創作要約ではない |
| subject_candidates | title、見出し、JSON-LD nameから得た未確定候補 |
| source_published_at / source_updated_at | メタ情報の観測値。不明ならnull |
| source_independence | relationshipとdepends_on_sources。既定unknown、出典数を信頼度に換算しない |

`deterministic`、`inferred`、`overrides`、`effective`を分離し、優先順位はoverride > inferred > deterministic。訂正は新しいContext revisionとして保存する。Fragmentは生成時Context IDを固定する。公式判定は小さい明示Host registryで、未登録公式サイトを自動的に公式とはしない。公式判定と個別Fragmentの性質は別軸。taxonomyはJSON / Prompt / registryを変更して拡張できる。

## Fragment

全Evidenceを順序通り処理し、重要度で先頭3〜6件へ限定しない。既定SinglePassは最大4 Evidence / 6000文字の資料予算で分割し、推論時はさらに最大480文字の処理単位へ分ける。長いEvidenceには64文字の重なりを設ける。Evidence・Raw・出典IDは変更せず、全処理単位が成功してから元Evidenceの結果を反映する。Context・Entity・Schemaの固定部分は別予算であり、モデルのContext lengthも十分に確保する。隣接Evidenceは残った予算内で各480文字まで提示する。根拠不足なら理由を残す。

| Fragment属性 | 暫定仕様 |
|---|---|
| subject / facet | 自由文字列。Entityのtype/name/aliasesは既存Schemaを維持 |
| original_text | 提示Evidenceに実在する連続引用。原文を変更しない |
| resolved_statement / content | 名前・省略主語を文脈内で補った独立文。contentは検索用の同じ値 |
| atomic_claim | trueを要求する契約。意味上の原子性は人間/Judge評価が必要 |
| epistemic_type | fact / source_interpretation / derived_interpretation / public_perception / promotional_claim |
| evidence_strength | direct_statement / strong_inference / weak_inference。校正確率ではない |
| asserted_by | official / creator / interviewee / article_author / community / anonymous_user / reviewer / cpc_llm / unknown等 |
| temporal_context | story_phase / valid_from / valid_to / work_context / temporal_note、各値はstringまたはnull |
| evidence_ids | 1:N・N:1の引用を許す。未知IDは拒否 |
| conflict_group | 同一論点の矛盾候補。不明はnull。両方の主張を残す |
| context_id / ai_run / extraction_job | 生成時の条件と追跡情報 |

1 Fragmentは一つの独立して評価できる主張。ただし因果・条件を壊す分割はしない。Sourceの考察とCPCが導いた考察を分離し、後者の主張主体はcpc_llmを要求する。公式の宣伝的主張、匿名投稿の事実主張の両方を許す。取得日時、記事公開日時、物語時期は別欄で扱う。

Entity候補は`entity_candidates`のunconfirmedとして保持し、Entityの自動統合は行わない。HighRecallで似たFragmentが増えてもRaw Fragmentを削除しない。

### Coverage・再開・エラー

`extraction_jobs`はSnapshot / Normalized / Entity / Context / モデル・Prompt・Schema・方式・予算を固定する。`evidence_assessments`はpending / success / discarded / failedを区別する。0件ならnavigation_only / metadata_only / unrelated / duplicate / insufficient_context / no_extractable_claimの理由を要求する。

- Evidence total = そのNormalized generationの全Evidence。
- substantive = 構造に基づく実質本文候補。
- Fragment Coverage = Fragmentが参照するsubstantive Evidence数 / substantive全数。
- Average Fragments / Evidence = 保存したRaw Fragment数 / Evidence全数。多対多リンク数の平均とは異なる。
- 0件理由、未処理、失敗は別集計。未処理や失敗を捨てた資料として数えない。

バッチごとの成功結果を保存し、失敗した新世代を既存の正常世代へ昇格しない。全Evidenceの判定が揃ってから一つのトランザクションで昇格する。意図的な全件0結果は完成世代として保存可能。`--resume`は同一条件で未処理・失敗バッチを再実行する。Raw変更やNormalized/Context/モデル/Prompt変更時は新しいJobを作る。

応答Schemaには今回の対象ID集合と許可引用ID集合を動的に入れ、隣接資料をassessmentsへ混入させない。完全性・引用検証に失敗した場合はCPCの診断を添えて1回だけ再要求し、全試行のAI記録を保持する。再試行も失敗した場合はfailedに残し、データの自動補正や根拠検証の省略は行わない。

SinglePassに加え、HighRecallMultiPass（事実・宣伝／考察・評判の2 pass）、Extract+Review（抽出＋漏れ確認）を比較可能。各方式は全Evidenceを処理する。追加passの結果も破壊的統合しない。review材料も予算を超えれば明示的に失敗し、batch縮小で再実行する。

### Prompt Injection

CPCの外部PromptとSchemaだけをsystem命令として使う。ページ、Context、Evidence、Fragmentはuser JSON内の信頼できない資料。資料のrole指定・命令を処理手順として実行しない。Providerもsystem/userを分け、参照ID・Schema・連続引用を検証する。実LLMが注入に絶対従わないという保証とは区別し、代表的な注入への実機評価は継続する。

## Final Document

既定はEntityの**全関連active Fragment集合**を使う。検索上位10件だけの要約を生成しない。任意`--query`は全集合へのlexical filterで、使った条件を記録する。

Facet / epistemic_type / 主張主体 / 根拠形式 / Temporal Contextごとに整理する。空白・句点差の同じ主張だけを派生Clusterへまとめる。代表文は元Fragmentのresolved_statementをそのまま採用し、全member FragmentとEvidenceの引用を保持する。異なる時期や主体は同じClusterへ潰さない。

構造化正本`final-knowledge-v1`はentity、overview、facts、source_interpretations、derived_interpretations、public_perception、promotional_claims、relationships、timeline、conflicts、source_notesを持つ。旧Schemaはunknownへ分ける。根拠のない項目は空配列で、学習済み知識で埋めない。overviewの新しい文章要約は今回は生成しない。

既定の抽出的生成は新しい主張を書かない。`--llm-order`ではFacet・情報種別ごとに最大24 Cluster / 8000文字の局所batchを並べ替える。LLMは既存Cluster IDの完全な順列だけを返せる。最終mergeは決定的に行う。大量のFragmentを一度にLLMへ送らず、引用ID一覧は局所Promptへ展開しない。

明示conflict_groupと、同一文脈・同一文型の数値差を未解決の矛盾候補として残す。数値差の自動検出は限定的で、真偽判定や一般的な矛盾検出ではない。Final自体が新しい情報を捏造しなくても、元Fragmentの根拠忠実性は別途評価する。

## CLI

```powershell
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite process
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite context --snapshot <snapshot-id>
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite context --snapshot <snapshot-id> --override .local/context-patch.json
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite fragment --snapshot <snapshot-id> --entity <entity-id> --batch-size 1
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite coverage <job-id>
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite fragment --snapshot <snapshot-id> --entity <entity-id> --batch-size 1 --resume <job-id>
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite embed
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite generate --entity <entity-id> --out .local/final.md
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite generate --entity <entity-id> --format json --out .local/final.json
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite generate --entity <entity-id> --format context --out .local/final-context.txt
.venv/Scripts/python.exe -m cpc --db .local/cpc.sqlite generate --entity <entity-id> --llm-order
```

旧方式の比較用入口はfragment / generateの`--legacy`。初回と同一の実装で再現する場合は初回commitを別checkoutで使用する。既定generateにはLLMもEmbeddingも不要。`--llm-order`はLLMだけ必要。fragment、embed、hybrid/semantic検索はそれぞれ実Providerが必要。

## Migrationと保存

Repository初期化時に`002_knowledge_capture.sql`をトランザクションで追加適用する。001は変更しない。既存Source/Snapshot/Evidence/Fragment/AI記録/Documents/Embeddingsは保持する。旧Normalized generationにはContextがないため、HighRecall開始前にprocessする。旧文書へ架空の構造化表現をバックフィルしない。

実評価はbaseline DBをSQLite backup APIで別DBへ複製して移行する。初回DBと評価ファイルを保持する。実本文、生成文書、Vector、DB、ログ、比較exportは`.local/`または`sample/`でGit管理外。追跡するbenchmark manifestはUUID・Raw hash・query・評価定義だけで、本文は含めない。

## 暫定判断と残課題

今回の独自判断は、保守的な本文root選択、構造によるsubstantive判定、上記分類とNullable Temporal Context、4件/6000文字batch、厳密引用検証、抽出的Final、空白・句点同一Cluster、限定数値矛盾候補、局所24件/8000文字の順列生成である。いずれも完成分類・完成アルゴリズムではない。

優先順に、(1) human goldによる本文欠落・重要主張Recall/Precisionの確認、(2) 主語解決と原子性・分類精度、(3) 汎用本文抽出の取りこぼし、(4) semantic類似Clusterと矛盾検出、(5) 出典依存関係とEntity候補確認、(6) multilingual Embedding / Reranker / model比較、(7) writer+verifier型Finalの検証を進める。完全な信頼性判定、引用ネットワーク、Entity自動統合、GUI、大規模運用は今回の完成条件にしない。

## 抽出失敗への対策

出力上限への到達が再試行後も続く場合、その処理単位だけを半分の幅へ再分割する。最小120文字まで縮小し、重なりは最大64文字・幅の1/4とする。全ての子処理が成功した場合だけ結果を採用する。最小幅でも上限へ達する場合はfailedに残し、主張数の制限や不完全JSONの取り込みはしない。旧条件のrunは変更せず、適応分割を含む新しい条件で評価する。

LLMはCoreが原文から作成したquote_choicesのquote_idを選択する。original_textは選択した原文からCoreが復元し、不明なIDや引用先Evidenceに属さない候補は拒否する。保存するFragmentのSchemaと厳密な原文照合は維持する。処理単位を小さくし、主張数を制限せずに出力予算への負荷を抑える。分割条件・引用選択方式はjob設定とPrompt versionに記録し、旧条件のjobを再開せず新しいbenchmark runで比較する。480文字・64文字重なりは暫定値で、境界をまたぐ主張の扱いは実データで確認する。
