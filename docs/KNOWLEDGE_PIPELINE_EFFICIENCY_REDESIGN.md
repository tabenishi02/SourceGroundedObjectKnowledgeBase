# Knowledge Pipeline 効率化・再設計調査

更新日: 2026-10-06

この文書は、Prototype 0.2 の実データ評価で顕在化した Fragment 数、LLM 呼び出し回数、出力 token 数、Final Document サイズの増大について、現在の CPC 実装と外部の RAG / Prompt Compression / Long Context 事例を比較し、次の設計見直し候補を整理するための調査・設計メモである。

この文書に記載する数値は、次の3種類を区別する。

1. **CPC 実測値**: 現在の Prototype Upgrade で実データを処理して得た値。
2. **外部実装の設定値**: GraphRAG、LightRAG、RAPTOR 等のコードまたは公式文書にあるデフォルト値・実装値。
3. **CPC 再設計案**: 外部事例と CPC 実測を踏まえた比較候補。未採用・未実測の値を含む。

外部事例の値は CPC にそのまま適用可能であることを意味しない。データ種別、モデル、Tokenizer、目的、出力 Schema が異なるため、CPC では固定評価データを用いて Recall / Precision / Unsupported / Atomicity / 所要時間を比較する。

---

## 1. 現在の CPC の状態

### 1.1 Evidence 生成

現在の `src/cpc/extraction.py` は HTML を構造単位へ分解し、既定で次の文字数基準で Evidence を生成する。

- chunk size: 1000 **characters**
- overlap: 100 **characters**
- table / post / quote / list は構造境界を優先
- section、artifact の変更でも区切る

対応実装:

- `src/cpc/extraction.py::chunks()`
- `src/cpc/application.py::Application.process()`

現状は Tokenizer に依存しないという利点がある一方、日本語では「文字数」と LLM が消費する token 数が一致しないため、LLM 入力量の予算管理には直接利用できない。

### 1.2 Fragment 抽出

現在の `src/cpc/capture.py` は High Recall を優先し、全 substantive Evidence を評価する。主な既定値は次のとおり。

- `WINDOW_CHARS = 480`
- `WINDOW_OVERLAP = 64`
- `MIN_WINDOW_CHARS = 120`
- batch size: 4 Evidence
- material budget: 6000 characters 相当の JSON 入力
- 出力上限到達時は window を約半分へ再分割
- 各 Evidence の抽出結果は `evidence_id` / `discard_reason` の assessment を持ち、処理の成功・失敗・未処理は checkpoint 等で追跡する
- 原文引用は quote ID をモデルに選ばせ、Core が exact quote を復元する

このため、Evidence 自体は約1000文字であっても、LLM 推論段階では原則480文字以下へ再分割される。

対応実装:

- `src/cpc/capture.py::extraction_windows()`
- `src/cpc/capture.py::HighRecallCapture.run()`
- `src/cpc/capture.py::HighRecallCapture.extract_window()`

### 1.3 LLM 出力上限

`src/cpc/providers.py` では LLM 出力上限はモデル仕様から自動取得していない。`CPC_LLM_MAX_TOKENS` を API へ渡す方式で、環境変数を設定しない場合の Provider 既定値は 3000 tokens。

速度予備試験と代表8 Capture の比較条件では、モデル間条件を固定するため次を採用した。

- context length: 既存8モデルのLM Studio条件は16384 tokens。追加したStrata L09は65536 tokens
- CPC形式 S03 / 実データ抽出の最大出力予算: 8192 tokens

したがって、**8192 tokens はモデル固有の最大出力能力ではなく、CPC の比較・評価で設定した推論予算**である。再設計後も 8192 を当然の最適値として固定しない。

対応資料:

- `src/cpc/providers.py`
- `docs/MODEL_SPEED_PREFLIGHT_PLAN.md`
- `docs/PROCESSING_BOTTLENECK_REVIEW.md`
- `docs/STRATA_INTEGRATION_REVIEW.md`
- `docs/MODEL_SPEED_PREFLIGHT_RESULTS.md`

Strata接続と固定S01/S02/S03の追加速度試験は実装・実機確認済み。S03本測定3回の中央値は90.40 tokens/s・16.67秒、CPC契約適合3/3。既存Qwen3.8-27Bは120.09 tokens/s・12.11秒で、この予備試験ではStrataによる高速化を確認していない。runtime・context・量子化・projectionの構成差を含み、代表8CaptureのStrata品質・総時間は未評価。この接続追加を本書の再設計案の実装完了とは扱わない。

### 1.4 実データで確認したボトルネック

代表8 Capture の現行 Qwen run では次を記録した。

| 指標 | 実測値 |
|---|---:|
| Evidence | 737 |
| Fragment | 5246 |
| AI 呼び出し | 1038 |
| 入力 token 合計 | 4,769,210 |
| 出力 token 合計 | 1,942,948 |
| AI 応答待ち | 約18,378秒 / 5.11時間 |
| AI 応答待ちの全体比 | 99%以上 |
| 成功 AI 実行 | 959 |
| 失敗 AI 実行 | 79 |
| JSON 解析エラー | 56 |
| 8192 token 上限到達 | 23 |
| validation error 付き再試行 | 71 |
| 同じ再試行でも8192 token到達 | 8 |
| 本文240文字以下の呼び出し | 529 / 1038 |

詳細は `docs/PROCESSING_BOTTLENECK_REVIEW.md` を正本とする。

ここから、現状の主因は DB や検索処理ではなく、**小さい本文 window に対して Prompt / Schema / Page Context / Entity / neighbors 等の固定情報を繰り返し送り、詳細な JSON を大量生成していること**と判断している。

### 1.5 Final Document

`src/cpc/final.py` の現在の cluster は非常に保守的で、次の属性とほぼ同一の claim text が一致した場合のみ同一 cluster とする。

- facet
- epistemic_type
- asserted_by
- evidence_strength
- temporal_context
- conflict_group
- 空白・一部句読点を除いた content

Raw Fragment を不可逆に統合しない点は設計意図に合う。しかし query 指定なしの Final は active Fragment 全体を読み込み、cluster を原則すべて出力する。そのため代表データでは次のサイズになった。

- Character Final: 約50万文字
- Work Final: 約378万文字

これは通常利用の「最終文書」というより、Knowledge Store の監査用全件 Export に近い。

---

## 2. 外部事例

以下は 2026-10-06 時点で確認した事例。URL と確認した値を併記し、後から再確認可能にする。

### 2.1 Microsoft GraphRAG

参照:

- Defaults: https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/config/defaults.py
- Chunking / configuration: https://github.com/microsoft/graphrag/blob/main/docs/config/yaml.md
- Default dataflow: https://github.com/graphrag/ms-graphrag/blob/main/docs/index/default_dataflow.md

確認値:

| 項目 | 値 | 種別 |
|---|---:|---|
| chunk size | 1200 tokens | 現行デフォルト |
| overlap | 100 tokens | 現行デフォルト |
| Basic Search max context | 12000 tokens | 現行デフォルト |
| Global Search max context | 12000 tokens | 現行デフォルト |
| Global Search map max length | 1000 tokens | 現行デフォルト |
| Global Search reduce max length | 2000 tokens | 現行デフォルト |

GraphRAG の公式 dataflow 文書は、chunk を大きくすると fidelity が下がる可能性がある一方、処理を大幅に高速化できると説明している。

CPC への示唆:

- 保管・抽出対象の単位を数百文字まで細分化することは必須ではない。
- chunk size と最終検索 context budget を別々に管理する。
- Knowledge Store 全体を Final prompt へ入れるのではなく、検索段階で明示的な token budget を設ける。

### 2.2 LightRAG

参照:

- Core documentation: https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md
- Constants: https://github.com/HKUDS/LightRAG/blob/main/lightrag/constants.py

確認値:

| 項目 | 値 | 種別 |
|---|---:|---|
| chunk size | 1200 tokens | 現行デフォルト |
| overlap | 100 tokens | 現行デフォルト |
| entity context | 6000 tokens | query budget default |
| relation context | 8000 tokens | query budget default |
| total query context | 30000 tokens | query budget default |
| chunk top-k | 20 | query default |
| summary input context | 12000 tokens | 現行定数 |
| recommended summary output | 600 tokens | 現行定数 |
| extraction input maximum | 20480 tokens | 現行定数 |

12,000 token の summary input に対して推奨 summary output が 600 token であるため、設定値だけを比較すれば最大約20:1の縮約を想定できる。ただしこれは「常に20倍圧縮される」という実測保証ではなく、入出力予算の上限・推奨値の比較である。

CPC への示唆:

- Extraction input、summary input、query context に別々の token budget を設ける。
- Raw / Evidence を失わず、後段 representation だけを強く圧縮できる。

### 2.3 RAPTOR

参照:

- ICLR 2024 paper: https://openreview.net/pdf?id=GN921JHCRw
- Reference implementation: https://github.com/parthsarthi03/raptor/blob/master/raptor/tree_retriever.py

確認値:

- 論文の collapsed-tree retrieval は **最大2000 tokens** を採用し、約 top-20 nodes に相当すると説明している。
- 現在の reference implementation の `retrieve()` は `max_tokens=3500` を既定値としている。

CPC への示唆:

- 大量の知識を階層化して保持しても、最終利用時に全件を渡す必要はない。
- Claim / Facet / Entity の階層 representation を用意し、用途に応じて数千〜数万 token の budget で展開する構造が候補になる。

### 2.4 Anthropic Contextual Retrieval

参照:

- https://www.anthropic.com/engineering/contextual-retrieval

確認事項:

- 一般的 RAG chunk は「数百 token 程度」と説明。
- コスト例では **800 token chunk**、文書8000 token、context instruction 50 token、追加 context 100 token を仮定。
- 生成される chunk-specific context は通常 50〜100 tokens。
- retrieval では 5 / 10 / 20 chunk を比較し、同評価では 20 chunk が最良。
- reranking では候補 top 150 から top 20 を選ぶ例を使用。
- Contextual Embedding + BM25 + reranking で top-20 retrieval failure rate を 5.7% から 1.9% へ削減したと報告。

CPC への示唆:

- 抽出前に強く圧縮して文脈を失うのではなく、Evidence は十分な文脈を保つ。
- 最終利用時に reranking / selection を行う。
- `Page Context` を Evidence 自体へ重複コピーせず参照可能にしている CPC の方向性は維持できる。

### 2.5 LLMLingua / LongLLMLingua / LLMLingua-2

参照:

- LLMLingua, EMNLP 2023: https://aclanthology.org/2023.emnlp-main.825/
- LongLLMLingua, ACL 2024: https://aclanthology.org/2024.acl-long.91/
- LLMLingua-2, Findings ACL 2024: https://aclanthology.org/2024.findings-acl.57/

確認事項:

- LLMLingua: 最大20x compression を報告。
- LongLLMLingua: 約10k-token prompt を 2x〜6x 圧縮した条件で end-to-end latency を 1.4x〜2.6x 改善。NaturalQuestions では約4x fewer tokens の例も報告。
- LLMLingua-2: compression ratio 2x〜5x で end-to-end latency 1.6x〜2.9x、既存 prompt compression 手法より 3x〜6x 高速と報告。

CPC への示唆:

- token 数を減らせば latency を大きく改善できる余地がある。
- ただし CPC の Evidence → Fragment は根拠抽出工程であり、否定・条件・時期・原文引用の欠落が許されにくい。Token deletion 型 compression をこの段階の既定処理にはしない。
- Prompt Compression は Retrieval 後の AI Context Renderer 等、Raw / Evidence / Fragment を失わない最終消費段で比較するのが安全。

### 2.6 RECOMP

参照:

- ICLR 2024: https://proceedings.iclr.cc/paper_files/paper/2024/hash/bda88ed2892f5e61c9a9bf215c566913-Abstract-Conference.html

確認事項:

- retrieved documents を query 依存で圧縮する extractive / abstractive compressor を提案。
- retrieved documents の **6%** まで圧縮しても minimal loss の条件を報告。単純比では約16.7x compression。
- 不要な retrieved document については empty string を出力する selective augmentation も採用。

CPC への示唆:

- 「Evidence を保存すること」と「毎回 LLM へ Evidence を渡すこと」を分離する。
- query / purpose に不要な Knowledge Claim を最終 context へ入れない設計が妥当。

### 2.7 Lost in the Middle

参照:

- Liu et al., 2023: https://arxiv.org/abs/2307.03172

確認事項:

- long-context 対応モデルでも、関連情報の位置によって性能が大きく変化することを報告。
- 多くの条件で relevant information が input の先頭または末尾にある場合より、中間にある場合に性能が低下した。

CPC への示唆:

- モデルが大きな context window を持つことは、Knowledge Store 全体を context 上限まで投入すべき根拠にはならない。
- relevant / diverse / source-balanced な情報を選び、明示的な context budget へ詰める方を優先して評価する。

---

## 3. CPC と外部事例の比較

| 論点 | 現在の CPC | 外部事例の傾向 | 再設計上の判断 |
|---|---|---|---|
| Evidence / chunk 単位 | 1000文字 + 100文字 overlap | GraphRAG / LightRAG は1200 token + 100 token | token 基準を比較する |
| Fragment inference unit | 原則480文字、最小120文字 | 数百〜1200+ token、summary/extract はさらに大きい入力も利用 | CPC は小さすぎる可能性が高い |
| 固定 Prompt 費 | 小 window ごとに再送 | 大きい batch / caching / hierarchy を利用 | 固定費削減が重要 |
| Output | 詳細 JSON を Fragment ごとに反復 | representation と保存 Schema を分離する例が多い | LLM transport Schema を compact 化 |
| High Recall | 全 substantive Evidence を LLM 処理 | retrieval / hierarchy / selective augmentation を併用 | Evidence coverage と Fragment 大量生成を分離 |
| Duplicate handling | Final でほぼ完全一致のみ統合 | graph / cluster / hierarchy | Raw Fragment の上に Knowledge Claim 層を追加候補 |
| Final | 全 active Cluster をほぼ全件表示 | 2k〜30k程度の context budget を持つ事例 | Final と Audit Export を分離 |
| Max context | LM Studio比較は16384、Strata追加条件は65536 | 大きな model context を使い切らず独自 budget を設ける | task budget を明示 |
| Max output | 比較条件8192 | task ごとに別 budget | 8192 をモデル能力とみなさない |

---

## 4. 再設計の基本方針

### 4.1 High Recall の保証場所を Evidence 層へ移す

High Recall を「大量の Fragment を生成したこと」で定義せず、次を保証対象とする。

1. 全 substantive Evidence が処理対象として追跡される。
2. 未処理 / failed / zero-fragment reason が明示される。
3. Raw / Normalized / Evidence は不可逆に削除しない。
4. 必要なら後から Evidence へ戻り、再抽出できる。

Fragment は「Evidence の複製」ではなく「独立して評価可能な claim」を担当する。

### 4.2 推奨論理層

```text
Raw
 ↓
Normalized Blocks
 ↓
Evidence                     High Recall / provenance layer
 ↓
Raw Fragment                 atomic claim extraction
 ↓
Knowledge Claim / Cluster    derived consolidation layer
 ↓
Retrieval / Selection
 ↓
Knowledge View               purpose-specific representation
 ↓
AI Context / Markdown / JSON
```

Raw Fragment は保存し、Knowledge Claim / Cluster は再生成可能な派生成果物とする。

### 4.3 Final と Audit Export を分離する

現在の約50万字 / 約378万字の出力は全件監査には利用できるため削除しない。ただし通常利用の Final と同一視しない。

- **Audit Export**: 全 Claim / Fragment / Evidence を追跡可能な形で出力。原則無制限。
- **Standard Knowledge View**: Entity の代表的知識を用途別に構造化。
- **Detailed Knowledge View**: Standard より広いが token budget 内。
- **AI Query Context**: query ごとに retrieval / rerank / diversification した context。

---

## 5. 効率化候補

### P0: 意味情報を削らない I/O 改善

#### 5.1 Output-limit 時の同一 window 再試行をやめる

現在は token budget 到達時にも同じ window で一度再試行する経路があり、代表 run では8回が再度8192 tokenへ到達した。

変更案:

```text
budget reached
  ↓
同一入力再試行を行わず即分割
  ↓
子 window 全成功時のみ親 batch を完了
```

Recall 契約を変えずに無駄な生成を減らせる。

#### 5.2 Provider の Structured Output を利用する

Prompt へ Schema 文を付けるだけでなく、Provider が対応する場合は API の JSON Schema / constrained generation を利用する。Core 側の Schema / quote / Evidence ID 検証は残す。

現行の`CompatibleLLM`および`StrataLLM`はSchema指定時にAPIの`response_format.json_schema`を送る。一方、LM Studio Native経路と既存8モデルに合わせたStrata速度試験はPrompt内Schemaを使う。Strataのサーバー制約は`prompt_and_validate`で、grammarによるconstrained decodingではない。専用Providerの`structured_output_failed`分類は実装済みだが、共通経路での制約付き生成の効果比較は未実施。API指定・生成中制約・生成後検証を区別して評価する。

目的:

- JSON後の余計な文章を抑制
- JSON parse error を削減
- validation retry を削減

#### 5.3 LLM transport Schema と保存 Schema を分離する

LLM に永続化 Schema の全 key を毎 Fragment 出力させず、短い code / positional field / omitted-null を使う transport representation を検討する。Core が canonical Fragment Schema へ復元する。

これは semantic compression ではなく **lossless representation compression** とする。

例:

```text
LLM output
[subject, facet, statement, E, S, A, quote_id, temporal]

Core expansion
E -> epistemic_type
S -> evidence_strength
A -> asserted_by
missing temporal -> canonical null structure
quote_id -> exact original_text + evidence_id
```

現在の約194万 output tokens を削減する第一候補。

#### 5.4 quote text の重複送信を削減する

現在は Evidence content と quote choices の双方に本文を持たせる経路がある。LLM には Evidence 本文を一度だけ渡し、quote ID / span mapping は Core が保持する方式を比較する。

将来候補:

```text
quote_id -> evidence_id + normalized span(start, end)
```

Core は exact source text を再構築し、引用整合性を決定論的に検証する。

### P1: 抽出単位を適応化する

#### 5.5 Character 基準から Token 基準へ

Evidence と LLM batch budget を token 基準でも扱えるようにする。Raw provenance / DOM position / block boundary は維持する。

初期 A/B 候補:

- Evidence target: 800 tokens
- Evidence target: 1200 tokens
- overlap: target の約8〜12%

外部値をそのまま採用するのではなく、現行1000-character方式を control として比較する。

#### 5.6 480文字固定 window を Adaptive Extraction Packer へ置換する

通常時は複数 block / Evidence material をまとめ、**予測 output 量**を基準に1回の LLM 入力を決める。

候補:

- initial material target: 2000 tokens
- normal upper candidate: 4000 tokens
- claim density が高い table / post / list は小さくする
- output limit / validation failure のときのみ再帰分割
- 120文字は通常処理単位ではなく最終 fallback

重要なのは input token を常に最大化することではなく、**1回の生成が安全な output budget 内へ収まるよう入力を動かすこと**である。

予測には次を利用できる。

- block kind
- text token 数
- table/list item 数
- 同じ site / page purpose で過去に観測した Fragment/token 密度
- 過去の output/input ratio

### P1: Knowledge Claim 層

#### 5.7 overlap / exact duplicate を決定論的に整理する

同一 Evidence / source span / normalized statement 等から生じた重複は、semantic LLM 判定より前に deterministic に関連付ける。

Raw Fragment 自体は削除しない。

#### 5.8 Semantic Claim Cluster を派生層として追加する

例:

```text
F101: Aは17歳である。
F285: Aの年齢は17歳。
F397: プロフィールではAは17歳とされる。
            ↓
K123: Aは17歳である
support = [F101, F285, F397]
```

判定は次の段階構成を候補とする。

1. deterministic exact / normalized match
2. Embedding による candidate generation
3. 候補だけ LLM で `same_claim / related / different_time / conflict / unrelated` 判定

`asserted_by`、`epistemic_type`、`temporal_context`、Source independence を統合条件から落とさない。

### P1: Final / AI Context Token Budget

外部事例の 2k〜30k を参考にするが、CPC の初期比較値として次を仮置きする。

| 用途 | CPC比較候補 | 状態 |
|---|---:|---|
| Short Summary | 2000〜4000 tokens | 未評価 |
| Standard Knowledge View | 12000 tokens | 未評価 |
| AI Query Context | 12000〜16000 tokens | 未評価 |
| Detailed Knowledge View | 24000〜30000 tokens | 未評価 |
| Audit Export | 原則無制限 | 現行全件出力を再利用可能 |

これらはモデルの最大 context ではない。CPC が用途ごとに設ける **task context budget** である。

Selection では relevance だけでなく、同一 claim の反復を抑え、facet / source / epistemic type の多様性を確保する。

### P2: Hierarchical Representation

RAPTOR / GraphRAG / LightRAG の考え方を参考に、次の階層を比較する。

```text
Raw Fragment
 ↓
Knowledge Claim
 ↓
Facet Knowledge
 ↓
Entity Overview
```

各 summary / overview から元 Claim ID / Fragment ID / Evidence ID へ戻れることを必須とし、LLM summary を正本にしない。

### P2: Prompt Compression

LLMLingua 系や RECOMP 型 compression は、Evidence → Fragment の既定処理では使用せず、Retrieval 後の AI Context で比較する。

理由:

- Evidence 抽出時に token deletion を行うと、否定、時期、条件、固有名詞等を落とす危険がある。
- CPC の正本は Raw / Evidence / Fragment であり、最終 Prompt は再生成可能である。

---

## 6. 出力 token budget の扱い

8192 tokens は現在のモデル比較・Prototype評価条件であり、モデル固有の最大値ではない。今後は次を概念上分離する。

```text
Model / Runtime output capability
        ↓
CPC hard output cap
        ↓
Task output budget
        ↓
Expected / target output size
```

Fragment Extraction の初期比較では、次を候補とする。

- task output budget: 2048
- task output budget: 4096
- hard cap / control: 8192

ただし output budget だけを小さくして途中打切りを増やしてはならない。Adaptive Packer と組み合わせ、**正常な batch は hard cap に到達しない**ことを目標とする。

評価時には reasoning token と response/body token を区別し、Provider が内訳を返さない場合は不明として扱う。

---

## 7. 推奨する比較実験

設計変更は一度にまとめず、固定データで1要素ずつ変更する。

### Experiment A: Lossless I/O optimization

Control:

- 現行480字 window
- 現行 Schema
- 現行8192 output budget

Variant:

- output-limit 即分割
- Structured Output
- compact transport Schema
- quote text 重複除去

測定:

- AI call count
- input/output tokens
- JSON/Schema failures
- retry count
- total duration
- Fragment count
- human gold Recall / Precision / Unsupported / Atomicity

### Experiment B: Extraction unit

比較候補:

- 現行480 characters
- token pack target 1000
- token pack target 2000
- token pack target 4000
- adaptive density-based packing

8192 を使い切った件数ではなく、**完全な出力を得るための総 token / 総時間**で比較する。

### Experiment C: Knowledge Claim clustering

比較:

1. exact normalized only
2. exact + Embedding candidates
3. exact + Embedding + LLM pair classification

Raw Fragment を固定して実施できるため、Fragment 抽出モデルの差と分離して評価する。

### Experiment D: Knowledge View budget

同一 Knowledge Claim Store から、

- 4k
- 12k
- 16k
- 24k
- 30k

の context を生成し、情報 Coverage、重複率、unsupported、質問回答性能、人間可読性を比較する。

### Experiment E: Prompt Compression

Retrieval結果を固定し、

- compressionなし
- 2x
- 3x
- 5x

程度から比較する。20x等の高圧縮は初期標準値にしない。

---

## 8. 採用判断の原則

効率化によって Fragment 数または token 数が減っただけでは成功と判定しない。

採用条件:

1. Raw が不変。
2. Evidence provenance が維持される。
3. 全 substantive Evidence の処理状態が追跡可能。
4. quote は Evidence へ厳密に遡れる。
5. human gold Recall を悪化させない、または許容差を事前定義する。
6. Unsupported率を悪化させない。
7. Atomicity / subject resolution / temporal qualifier の品質を悪化させない。
8. total LLM call、input token、output token、総時間の少なくとも1つで明確な改善がある。
9. 改善値はモデル・Prompt・Schema・runtime・dataset version を固定して比較する。

---

## 9. 現時点の推奨順位

| 優先 | 変更 | High Recallへの危険 | 期待効果 |
|---|---|---|---|
| P0 | output-limit 即分割 | 低 | 小〜中 |
| P0 | API Structured Output | 低 | 中 |
| P0 | compact transport Schema | 低 | 大 |
| P0 | quote / context の重複送信削減 | 低 | 中 |
| P1 | token 基準の Evidence / packing | 要比較 | 中〜大 |
| P1 | Adaptive Extraction Packer | 要比較 | 非常に大 |
| P1 | deterministic overlap dedup | 低 | 中 |
| P1 | Knowledge Claim 層 | Raw保持なら低 | 非常に大 |
| P1 | Final / AI Context budget | Raw保持なら低 | 非常に大 |
| P2 | semantic cluster LLM 判定 | 要評価 | 大 |
| P2 | hierarchical summary | 要評価 | 大 |
| P2 | incremental embedding | 低 | 中 |
| P3 | LLMLingua / RECOMP型 prompt compression | 最終context限定なら低 | 中〜大 |

---

## 10. 設計上の暫定結論

今回の調査から、CPC の High Recall 方針自体を撤回する根拠はない。一方で、High Recall を「全 Evidence を非常に小さな window へ分割し、大量の詳細 Fragment JSON を生成し、それをほぼ全件 Final に出力すること」と結び付ける必要もない。

再設計の中心は次の分離とする。

> **Evidence では情報到達可能性と追跡性を保証する。Raw Fragment では原子的主張を保存する。Knowledge Claim では重複・関係を派生的に整理する。Knowledge View / AI Context では用途ごとの token budget 内に選択・圧縮する。**

この構造であれば、Raw / Evidence / Raw Fragment を保持したまま、LLM 呼び出し回数、反復 Prompt、重複 Claim、数百万文字 Final をそれぞれ異なる層で削減できる。

現時点では上記を**設計候補**とし、Prototype 0.2 の既存実装を即座に置換したとは扱わない。次の工程は、まず P0 の lossless I/O 改善と Adaptive Extraction Packer の比較実験を固定データで行い、人間 gold を含む品質評価を通過した変更だけを正式設計へ昇格することである。
