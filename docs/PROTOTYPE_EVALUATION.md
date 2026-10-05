# 初回プロトタイプ評価

この節以降の初回評価は履歴として保持する。現行設計は[Prototype Upgrade](PROTOTYPE_UPGRADE.md)、新しい比較の実行手順は[benchmark](../benchmark/README.md)を参照。

## Upgrade評価の進行状態（2026-10-06）

- 初回DBを別の`.local/upgrade.sqlite`へbackupして002へ移行した。初回DBは変更していない。
- 106件の実Captureを新Extractorで再処理した。現行世代のEvidenceは5068件（初回6129件）。件数減少だけで本文選択の品質改善とは判断しない。
- 代表8Captureと2 Entityを`benchmark/sample-v1.json`で固定し、全Evidenceの抽出・0件理由・Coverage、検索3方式、構造化Finalを比較する。比較exportはignored `sample/CPC_Upgrade_評価/`へ生成する。
- 初期のGPT-OSS text-mode試行はSchema違反が多く停止した。Qwen互換APIの空応答を受け、native API・reasoning offで検証した。原文転記の不一致11件と出力上限到達12件を調査し、引用ID選択と480文字から最小120文字までの適応分割を実装した。旧試行記録はDBに保持する。
- 適応分割後の代表8Captureは全件complete。Raw SHA256 / 更新日時不変、integrity_check=ok、外部キーエラーなし。検索・Final Documentの再検証と比較出力は別途進行中。
- human gold未付与の意味評価値はnull。件数・引用率をRecall/Precisionや意味上の正しさへ読み替えない。

実データ比較の完了後に本節へ集計・代表内容レビューを追記する。既存の下記初回結果は置き換えない。

### Fragment再評価（Qwen3.8-27B Q4_K_M、native API）

| Case | Evidence | Fragment | 実質Evidenceの引用Coverage | 失敗 |
|---|---:|---:|---:|---:|
| 01 | 53 | 287 | 69.57% | 0 |
| 02 | 49 | 158 | 63.83% | 0 |
| 03 | 31 | 76 | 31.82% | 0 |
| 04 | 32 | 3 | 9.38% | 0 |
| 05 | 90 | 407 | 78.57% | 0 |
| 06 | 145 | 627 | 84.40% | 0 |
| 07 | 156 | 1338 | 85.04% | 0 |
| 08 | 181 | 2350 | 83.33% | 0 |

合計737 Evidenceから5246 Fragmentを保存した。これは主張数と厳密な引用検証の結果であり、意味上の正しさやRecall/Precisionの評価ではない。重なりのある処理単位による重複を含む。0件理由と分類・主張内容は比較テキストで確認する。複数モデルの比較は未実施。

## 対象と方法

`sample/` を再帰調査し、実Capture 106件（59ドメイン）を使用しました。全件Bundle Format 1.0、Capture日時は各manifestで確認しています。title/実URL/時刻/Artifact/構造の個別一覧はGit管理外の `.local/sample-inventory.json` にあります。実ページ本文・アカウント情報・原ZIP・DB・生成文書をこのレポートへ複製していません。

| 特徴 | Capture数 |
|---|---:|
| JSON-LD索引あり | 56 |
| Frame索引あり | 82 |
| open Shadow索引あり | 106 |
| MHTMLあり | 106 |

Frameの取得不能状態やclosed Shadowの制約はmanifest/metadataのまま保持します。Main DOMを処理対象にし、広告等のFrame/Shadowを標準検索から除外しました。Frame/Shadowを明示追加する動作・位置追跡は人工Fixtureで検証しています。

## 全Captureの決定的処理

| source_type（暫定分類） | Capture数 | Import/Extract/Evidence/FTS |
|---|---:|---|
| encyclopedia | 11 | 11成功 |
| wiki | 21 | 21成功 |
| bbs | 15 | 15成功 |
| blog | 14 | 14成功 |
| news_article | 22 | 22成功 |
| social_post | 3 | 3成功 |
| generic_web | 20 | 20成功 |
| 合計 | 106 | 106成功 |

Source 106、Snapshot 106、Normalized世代106、Evidence 6,129件を保存しました。全件で元ZIPのSHA-256と更新日時が処理前後で不変でした。同一URLの別Capture・同一capture_idの再Importは人工Fixtureで検証しています（この実コーパスの実URLは106種類）。

「抽出成功」は本文候補が空でなくEvidenceへ保存できたことを示します。ページ本文の網羅性や正確な投稿境界の合格を意味しません。本文の短いCaptureや多数のUIを含むサイトは個別評価が必要です。対象ごとの件数・成否は `.local/evaluation.json` に記録しています。

## 実LLM / Embedding / 最終文書

LLMは既存ローカルの `openai/gpt-oss-20b` GGUF MXFP4（API識別子 `cpc-prototype-llm`）、Embeddingは `nomic-embed-text-v1.5` GGUF Q4_K_M（`cpc-prototype-embedding`）を使用しました。LLM context 8192、temperature 0、reasoning_effort lowです。upstreamの正確なrevisionは不明と明記しています。

EntityはCharacter「櫻木真乃」とWork「アイドルマスター シャイニーカラーズ」の2件をスクリプトで登録し、appears_in関係を追加しました。サンプルtitleで対象を選ぶ暫定seedであり、一般的なEntity自動発見を実装したとは扱いません。

代表8件を実LLMへ渡した結果：

| site | Snapshot ID | 対象 | Fragment数 |
|---|---|---|---:|
| dic.pixiv.net | 98cf78b2-2148-469c-a0c0-d9ff5a362c4e | Character | 4 |
| w.atwiki.jp | cc389352-0055-46e0-92d2-3c2453e7e446 | Character | 5 |
| dic.nicovideo.jp | 33ed101c-4925-4790-9712-eb01d2cac69a | Character | 2 |
| dec.2chan.net | 1edddc24-c05c-4741-9b52-1386138fd356 | Character | 0（空結果） |
| dic.pixiv.net | 7cab8e33-5233-45bd-bed7-cdc4e3123370 | Work | 1 |
| w.atwiki.jp | 46c76f15-451d-4f9b-9743-d89da01db71c | Work | 3 |
| dic.nicovideo.jp | fe93f394-c63a-4d62-a7ef-94347dc123c9 | Work | 1 |
| ja.wikipedia.org | dda22047-a761-4aec-ac66-158c051e9dbf | Work | 4 |

7件で20 Fragmentを保存しました。dec.2chan.netの1件では選択した3 Evidence/3000文字から根拠付きFactが得られませんでした。Import/Extractの失敗ではありませんが、このCaptureのFragment段階を有用な出力が得られた合格とは扱いません。専用の投稿選択・対象Entityに対する根拠の確認が次の課題です。残り98件のLLM抽出は今回未評価です。

6,129 Evidenceと20 Fragmentの両方へ実Embedding（768次元、合計6,149件）を保存しました。両EntityについてFTS、Semantic、Entity filter付きHybrid検索で結果が返り、RRF統合・簡易Rerankを経て最終文書を生成しました。検索件数は精度の測定値ではありません。

最終文書は次の2件です（Git管理外）：

- Character: `.local/documents/22e2c0d7-ca26-4710-aa17-20c291a7bf4c.md`
- Work: `.local/documents/ad7aab2c-a92f-40d9-b9bc-a9e03a16932e.md`

Character文書はatwikiのCaptureを引用し、Work文書はNico百科事典とWikipediaのCaptureを引用しました。これらの実ZIPからSource/Snapshot/Evidence/Fragment/Hybrid検索/実LLM/Markdownまで到達しています。各引用についてFragment→Evidence→Snapshot→Source→元ZIPのSHA-256まで照合済みです。

## 実機で見つかった問題と対処

1. LM Studioは最初の `json_object` 指定をHTTP 400で拒否しました。アダプターをJSON Schemaへ修正し、HTTPアダプターテストでその指定を確認しています。
2. gpt-ossのFragment制約出力は8件とも空配列になりました。通常text応答とCoreのJSON/根拠ID検証を組み合わせると7件でFactが得られたため、Fragment段階の応答形式overrideを設定可能にしました。
3. 名前の単純な出現回数でEvidenceを選ぶと関連小説等の一覧が優先されました。Sectionと文書構造を併用し、関連作品UIの優先度を下げました。
4. Finalもtext形式にすると不正JSONの2応答を保存拒否しました。FinalはJSON Schemaへ戻して、2文書とも正常生成できました。失敗履歴と実出力はAI ledgerに残しています。

## 品質に関する観察と次の改善

- Wikipedia/Pixivは本文rootを限定でき、見出し・段落・プロフィール表を保持できました。Genericは投稿/本文/関連一覧の分離が不十分なサイトがあります。短い抽出結果を成功件数だけで評価しないことが必要です。
- 初回のEvidence選択はFactの網羅性が低く、Fragment抽出で対象名を繰り返さない段落や性格・能力等を取りこぼし得ます。次はfacet別の構造選択と、長い表の行単位chunkを評価します。
- Nomic v1.5は英語Embeddingです。日本語の意味検索精度は未定量評価で、多言語モデルへの交換が優先です。600文字より後の情報をEmbeddingが見ない制約も、chunk/入力token設計と併せて見直します。
- 最終出力は概要中心の短い文書でした。生成中の固有名詞に小さな誤記が見られ、実在する引用IDの検証だけでは事実・表記の忠実性を保証できません。次はモデル/Prompt変更、facetごとの材料選択、claimと原文の照合を評価します。
- EntityはWork/Characterの2件のみ評価しました。Concept、alias解決、複数Workとの関係、Facet分類、矛盾したFactの保持・提示は継続課題です。
- Rerankerは簡易方式です。Queryごとの正解候補と評価指標を用意し、語彙が違う検索・関連の薄いQuery・Source優先順位を評価する必要があります。
- Citationは追跡可能ですが、脚注のDOM pathが長いため読みやすさに課題があります。ArtifactビューアとSection単位の表示は今後の候補です。

## 自動検証

人工最小Fixtureによる `pytest` 36件成功、Ruff lint/format成功、`git diff --check` 成功。対象はImporter/Format/checksum/duplicate/Source-Snapshot、Generic/site roots、構造とchunk、Frame/Shadow位置、Fragment validation、provenance、FTS/semantic/model isolation、metadata filter、merge、Final core、再処理、Migration再適用、失敗時の旧世代保護です。Unit TestのLLM/Vectorはテスト専用doubleで、実サンプル評価とは分離しています。

型チェッカーは今回導入していません。SentenceTransformers実モデルアダプター、大規模性能、全サイトの抽出品質、複数更新ジョブの同時実行は未評価です。拡張機能のコードは今回変更していません。
