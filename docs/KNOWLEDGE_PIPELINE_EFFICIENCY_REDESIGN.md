# Knowledge Pipeline 効率化・再設計調査

更新日: 2026-10-06

この文書は、Prototype 0.2 の実データ評価で顕在化した Fragment 数、LLM 呼び出し回数、出力 token 数、Final Document サイズの増大について、現在の CPC 実装と外部の RAG / Prompt Compression / Long Context 事例を比較し、次の設計見直し候補を整理するための調査・設計メモである。

現行コードとProvider仕様を照合した実装順序・変更箇所・検証・移行の計画は[第11節](#11-実装計画現行コード照合後)に記載する。

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

---

## 11. 実装計画（現行コード照合後）

計画作成日: 2026-10-06。以下は実装予定であり、この文書更新でコード・DB・運用設定を変更したものではない。
対象はPrototype 0.2の既存契約を維持した段階的改善。GraphRAG等への全面置換、全モデル一括評価、クラウド送信は初回実装に含めない。

### 11.1 調査で確認した実装境界

| 現行の箇所 | 確認した動作 | 実装上の判断 |
|---|---|---|
| `capture.py::_extract_window()` | すべてのValueErrorで同一入力を最大2回試し、上限超過も対象 | 出力予算超過だけを即座に外側の分割処理へ渡す |
| `capture.py::extract_window()` | 2種類のエラー文字列で予算超過を判定。再帰分割、最小120文字 | Provider共通の型付きエラーと終端条件を追加する |
| `capture.py::quote_choices()` / `resolve_quotes()` | 本文をchoicesにもコピーし、Coreが引用を復元 | 送信側choicesからtextを除き、Core側の完全な対応表は保持する |
| `application.py::call_llm()` | Promptに完全Schemaを付け、同じSchemaをProviderにも渡す | Prompt/transport/保存Schemaのversionを区別する。Core検証は残す |
| `providers.py` | Compatible/StrataはSchema指定、Nativeはテキスト。Strata 502分類は実装済み | 接続経路ごとの能力を記録し、Schema指定を再実装しない |
| `knowledge_repository.py::record_batch()` | batch単位の結果を保存。途中window成功はbatch完了前に永続化されない | 大きいpacker導入前にwindow単位の再開を追加する |
| `knowledge_repository.py::promote_extraction()` | 未完了Evidenceがあると全体世代を昇格しない | 新しいwindow/checkpointにもこの契約を継承する |
| `final.py::cluster_fragments()` | 非破壊の保守的集約はあるが永続Knowledge Claim世代はない | 現行集約を足場に、派生Claimとsupport参照を追加する |
| `final.py::StructuredFinal.build()` | queryなしは全件。max_charsは局所並べ替え入力の上限 | 出力全体のtoken上限と監査Exportを別のモードにする |
| `application.py::embed()` | 候補全件を再推論し、全件成功後に保存 | 推論済みvectorの再利用と新しい世代への関連付けを分ける |
| `benchmark.py::run_benchmark()` | manifest/config一致の再開とRaw hash確認はある | codec/packer/tokenizer/capabilityもconfigへ入れ、別条件を混ぜない |

外部仕様も再確認した。[LM Studio Structured Output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)は`/v1/chat/completions`のJSON Schema指定とGGUFのgrammar samplingを説明している。したがってNative APIへ未知のパラメータを追加するより、**別条件の互換API経路を比較**する。実際に使うモデル・Schemaの対応は実機probeで確認し、対応保証とは扱わない。

[LM Studio Tokenization](https://lmstudio.ai/docs/python/tokenization)はモデルtokenizerによる計数と、chat template適用後の会話計数を提供する。モデル別TokenCounterの候補にするが、現行CPCはSDKに依存しないため任意依存として追加する。Strataの対応手段は実装時にローカル仕様を確認し、存在未確認のtokenize endpointを前提にしない。

### 11.2 推奨する実装順序と分割単位

各段階を独立コミット・独立比較条件で実装する。既定動作の変更は受入判定後に行う。

| 段階 | 内容 | 依存 | 主な変更先・追加先（予定） | 完了の判断 |
|---|---|---|---|---|
| E0 | 評価条件と観測の固定 | なし | `benchmark.py`、比較設定、評価用runner | 同一manifestで独立条件を記録し、未付与goldを合格扱いしない |
| E1 | 即分割・能力判定・Compact Schema・引用重複除去 | E0 | `providers.py`、`capture.py`、`application.py`、新`transport.py`、version付きPrompt/Schema | 失敗処理とcanonical復元が正しく、各変更のtoken/時間差を測定 |
| E2 | window/checkpoint世代 | E0、E1のversion管理 | `capture.py`、`knowledge_repository.py`、追加migration | 部分成功後の再開が重複・欠落なく動作し、不完全世代を昇格しない |
| E3 | TokenCounter・Adaptive Packer | E1、E2 | 新`budget.py`、`capture.py`、CLI、benchmark条件 | 全入力span coverageを維持し、実測の呼出数/総時間を削減 |
| E4 | 決定論的Knowledge Claim世代 | E0。E3と独立して着手可能 | 新`claims.py`、repository、追加migration、`final.py` | 元Fragment不変、全supportを追跡し、不適切な同一視を防ぐ |
| E5 | 用途別Knowledge View / AI Context | E4、TokenCounter | `final.py`、CLI、document保存設定 | 表示全体が予算内、省略情報を明示、監査Exportは全件保持 |
| E6 | 増分Embedding | E0。E4/E5と独立 | `application.py`、`repository.py`、Embedding設定 | 変更のない推論を再利用し、空間分離と原子的昇格を保持 |
| E7 | 意味集約・階層化・Prompt Compression | E4/E5、品質gold | Claim候補選択、階層representation、context renderer | 個別A/Bで品質を確認。効果がない案は採用しない |

**初回の実装範囲はE0〜E1**を推奨する。続いてE2〜E3で抽出効率を改善する。Finalの可読性改善はE4〜E5として分け、抽出モデルの変化と混同しない。E7を初回標準動作へ組み込まない。

### 11.3 E0: 評価・再現性の準備

1. 代表8Captureのmanifest、Raw SHA256、Normalized/Evidence世代、Entity、Page Context、旧Fragment runを固定する。実データ・DB・生応答はGit管理外に保管する。
2. モデル、revision/量子化、runtime、context、reasoning、projection、Prompt/Schema/codec、packer、tokenizer、出力上限をconfigurationに保存する。未知値はunknown/null。別条件のresumeは拒否する。
3. 基準モデルは現行Qwen3.8-27B構成。Strataは別runtime条件で、変更前後を同じStrata構成内で比較する。旧runと異なるSchema・cache状態の速度差を単一変更の効果としない。
4. 小規模の開発セットは代表8件から、本文・高密度table/list/post・長文・否定/時期/主語曖昧・0件理由を含む2Captureを選ぶ。未使用の保留資料は調整に使わない。
5. 開発セットに原子的gold claimと支持Evidence/spanを付与する。否定・条件・時期・発話者・資料種別・矛盾を含める。代表8件と保留資料のgoldが不足する間は品質を未評価と表示し、既定変更の最終承認を保留する。
6. 試行/再試行/windowごとにstatus、error category、入力/出力token、本文/推論内訳、client総時間、API decode速度、分割深さ、評価Evidence/span、生成Fragment数を記録する。TTFT・ピークメモリが取れない場合は補完しない。

### 11.4 E1: 情報を削らない入出力改善

#### E1a: 予算超過を即分割

- `OutputBudgetExceeded`等のValueError派生型を追加し、Compatible/Native/Strataから同じ型を返す。文字列判定に依存しない。
- `_extract_window()`で予算超過を先に捕捉して再送せずraise。Schema/引用検証エラーの同一入力再試行は現行どおり最大1回とし、validation_errorを添える。
- timeout、認証、接続、一般HTTP障害は内容分割へ分類しない。Strataの構造化出力エラーも打ち切りと形式違反を分ける。
- 最小windowでも打ち切りならfailed。深さ・試行数の上限を設定し、子windowの全成功と全文coverage成立時のみ親をsuccessにする。
- 上限を下げる試験では、モデルの推論tokenが予算に含まれるかも記録する。短いpartial JSONを完成Fragmentとして保存しない。

#### E1b: Structured Outputの能力と経路を明示

- Provider設定へ`structured_mode`（prompt_only / api_schema）と実装上の制約方法（unknown / grammar / prompt_and_validate）を記録する。APIへ指定できることと生成中に制約されることを区別する。
- LM Studio Native controlを維持し、Schema対応の互換APIを別条件としてprobeする。probeは空配列、必須文字列、enum、引用ID、Evidence ID、上限超過を対象にする。
- 推論必須モデルの設定は既存の対応情報を継承し、offを一律指定しない。互換APIで同じ設定を表現できなければ別条件・比較対象外と記録する。
- Unsupported Schemaを黙ってtextへフォールバックせず、理由を記録する。Strataの共有サーバー・依存パッケージはCPC実装から自動変更しない。
- 動的Schemaの入力ID/列挙を保ち、受信後のSchema・主張・引用・assessment検証はすべて実行する。

#### E1c: Compact transportと引用送信を個別導入

- まず**短いkeyのJSON object**を採用候補にする。位置だけで意味が決まるarrayは初回候補から外し、列ずれの診断とSchema対応を容易にする。
- transport-v1の各key/enum codeとcanonical key/値の対応表をversion管理する。subject、facet、statement、atomic_claim、epistemic type、strength、asserted_by、temporal、conflict、Evidence ID、quote IDの意味を削らない。
- 省略を許すのはcanonical Schemaでnull/既定値が同じ意味になる項目だけ。空文字・unknown・null・未提供を勝手に同一化しない。未知code/余分なkeyは拒否する。
- `decode → quote復元 → canonical validate`の順を固定し、保存Schema・既存DB・検索APIは維持する。既存の通常transportも選択可能にする。
- 引用重複除去は別条件で試す。モデルへはEvidence本文と`quote_id → evidence_id`を送り、Coreに現在の完全なchoicesを保持する。任意のspanをモデルに書かせる方式は初回で追加しない。
- サーバーがSchemaを受けてもPrompt内Schemaの除去は別実験にする。意味を説明する短いガイドと厳密Schemaの役割を分け、拒否/検証失敗を観測する。

### 11.5 E2〜E3: 再開可能な抽出単位と予算

**Evidence保存の1000文字chunkは最初に変更しない。** 固定Evidence上の推論単位だけを変更すれば、ID・provenance・評価対象を変えず比較できる。Evidenceを800/1200 tokenで再生成する案は、packer評価後に別Normalized世代で試す。

- 追加migrationでwindow結果とmembershipを保存する。最低限、job、parent window、元Evidence ID、content hash、Evidence内の半開区間[start,end)、順序、codec/packer version、AI run、status、resultを持つ。
- window IDはjobの設定と入力spanから決定する。分割時の子window一覧も保存する。再開は保存済みの計画を使い、同じ入力の成功windowだけを再利用する。
- sibling失敗後も成功windowを再推論しない。assessmentは単一windowから上書きせず、全windowの成功/破棄理由からEvidence単位へ集約する。独立multi-passの結果とAI run参照も保持する。
- 新世代Fragmentの作成・active切替は既存の全体昇格契約を継承する。旧jobは旧batch経路で読めるようにし、途中の旧jobを新packerへ変換しない。
- TokenCounterはモデルtokenizer・chat template・revisionを識別する。SDK等で正確に数える経路と保守的推定値を区別し、計測不能なら固定文字windowへ明示的に戻す。token比較としての採用判定には推定値を使わない。
- 予算式は`formatted_input_tokens + requested_output_tokens + safety_margin <= effective_context`。本文だけでなくPrompt、Schema、Entity、Page Context、neighbor、review既出Fragmentを含める。api_schema部分の計数が不明なら差分校正と余裕を記録する。
- 固定1000/2000/4000 material tokenを順に比較し、その後に密度対応を試す。計画上の初期targetは2000、4000は上限候補。output budgetは4096、control/hard upper candidateは8192。2048はCompact採用後の追加候補にする。
- table/list/postは小さめから開始し、実測output/material比で調整する。調整履歴と算出設定を保存し、同じ構成を再開した時に異なる計画へ変更しない。
- overlapを含むspan集合が元本文全域を覆うことを検証する。改行・Unicode・表の境界を壊すtoken IDの途中decodeは避け、原文文字境界でspanを選ぶ。入力削除や黙った切り捨てはしない。

### 11.6 E4〜E5: Knowledge Claimと人間向けの表示

#### 派生Claimの保存

- 追加migrationでClaim世代、Claim本体、Fragment support、relationを保存する。正本のRaw Fragment、Fragment↔Evidence、AI runを更新・削除しない。
- Claim世代はEntity、対象active Fragment run集合、algorithm/config hashで識別する。Snapshot/Context/Fragment世代変更で再生成し、途中世代を公開しない。
- 決定論的集約から始める。Entity/subject、facet、主張本文、epistemic type、strength、asserted_by、temporal、conflictを一致条件にする。数値・否定・条件を正規化で消さない。
- 同じ主張のsupportは複数資料から保持し、転載/同一sourceの別Snapshotを独立資料の数として数えない。強度の違う主張を勝手に格上げしない。
- `same_claim`以外はrelationとして表現する。`different_time`、`conflict`、`related`は同一Claimへ統合しない。語義が不確かな場合は別Claimのままにする。
- provenance APIの既存応答を維持し、ClaimからFragment/Evidence/Rawへの追加経路を用意する。全support集合とviewで選んだ引用集合を区別する。

#### 用途別View

- 新しい明示モードを追加し、現行の全件Finalは`audit`相当として保持する。既存`generate`の既定・戻り値は初回実装では変更しない。
- まずLLMなしの抽出型Viewを作る。計画上の候補はshort=4k、standard=12k、AI context=12k/16k、detailed=24k/30k。値は実測前の候補で、model contextに収まらない指定はエラーとする。
- query relevance、facet/epistemic type/sourceの多様性、同一主張の反復抑制を決定論的に組み合わせる。LLMによる新事実の補完は行わない。
- 予算は本文だけでなく見出し・注記・引用・timeline・relationships・source notesを含む**最終出力全体**へ適用する。配置が複数になるClaimの反復も計数する。
- Claim/引用ブロックを途中で切らず、入らないブロックは省略ID・理由を残す。必要ならAudit/機械可読manifestから全件へ戻れるようにする。
- AI contextは消費先モデル用に数え、system/query/出力reserveも差し引く。表示用予算とLLMの空きcontextを同一視しない。
- 保存設定へmode、budget、tokenizer、選択/省略Claim ID、元Claim世代、selection algorithmを記録する。既存Finalと比較して情報coverageと人間可読性を測る。

### 11.7 E6〜E7: 後続の最適化

**増分Embedding:** モデル/revision、次元、prefix・max_chars等の前処理、実際にEmbeddingへ渡す文字列のhashを含めて再利用keyを決める。Evidence/Fragment IDだけで再利用しない。現在の`EmbeddingSpace`分離とhash照合・全件保存transactionを足場に、必要な追加migrationで再利用cacheと世代membershipを作る。未変更vectorを再利用、変更分だけ推論し、全件有効になった時点で原子的昇格する。未知revisionの再利用範囲は同じ明示空間内に限定する。途中失敗時は旧検索世代を保持する。

**意味Claim集約:** Embeddingによる候補上限を設定し、全Fragmentペアの総当たりを避ける。候補LLM分類と支持判定を保存する。推移律だけで連鎖統合せず、全memberがsubject・時期・発話者・情報種別の互換条件を満たすことを検証する。信頼度の閾値はgoldで決め、曖昧ならrelationだけにする。

**階層・Prompt Compression:** Facet/Entity summaryはClaim IDを支持として保持した派生物とし、正本にしない。CompressionはRetrieval後のAI Contextだけで比較する。2x/3x/5xを別条件とし、否定・時期・数値・出典を検証する。Evidence抽出前のtoken削除、20xの初期標準化は実施しない。

### 11.8 検証・受入・所要時間

| 範囲 | 既存テストの足場 | 必要な追加確認 |
|---|---|---|
| エラー/Provider | `tests/test_providers.py`、Upgradeのbudget split | 上限時の同一入力再送0回、形式違反再試行、HTTP障害の非分割、終端failed |
| transport/引用 | Upgradeのquote selector・Schema/原子性検証 | 対応表round-trip、null/省略差、未知code拒否、quote/Evidence ID一致 |
| checkpoint/packer | Upgradeの全文window coverage・failure/resume・context変更 | 全span coverage、sibling失敗後の再開、multi-pass保存、config差拒否 |
| Claim/View | Upgradeの非破壊cluster・final完全性・捏造拒否 | 時期/否定/subject/source差の分離、全support追跡、出力全体budget、省略manifest |
| Embedding | `tests/test_core.py`の空間/検索契約 | 無変更時のAPI呼出0、前処理変更時miss、途中失敗時の旧世代維持 |
| migration | Upgradeのv1 migration保存確認 | 既存0.2 DBを複製して移行・整合性・旧job再開を確認 |

比較は「自動の契約検証 → 開発2Capture → 代表8Capture → 保留資料」の順に進める。各変更をcontrolと同じモデル構成で1要素ずつ測り、単体の効果確認後に採用候補だけを組み合わせる。8Capture全量で全factorの総当たりは行わない。

受入条件:

1. Raw hash/更新日時不変、保存済みEvidence/旧Fragment保持、SQLite integrity/foreign key正常、失敗世代非昇格。
2. 全対象Evidenceとspanの処理coverage100%、引用・出典・schema契約違反0。discardedを根拠なくsuccessへ変えない。
3. gold上のRecall/Precision/Atomicityをcontrolより悪化させず、新たなUnsupported・重大な否定/時期/subject誤り0。小標本での同等性は一般品質保証とせず、保留評価を必須とする。
4. 同じruntime内の総時間・token・呼出数の比較で改善を確認する。初回の採用目標は総時間または総tokenの20%以上削減だが、**未実測の目標値**であり保証ではない。速度ばらつきが大きければ3回測定し、中央値と範囲を示す。
5. Viewは全体予算遵守と省略の追跡を満たす。総情報数の減少やFragment数の減少だけで品質合格にしない。

推論時間の計画値は旧Qwen代表8Captureの約5.1時間を参考にする。control再測定＋variant1本で約10.2時間、control1本＋variant4本なら約25.5時間。ただし旧runの失敗・再試行を含む参考値で、新しい実測時間は未確定。開発2件は選んだCaptureの旧時間合計から個別見積もりする。Claim/Viewの決定論的比較はFragment固定で再抽出を不要にする。Strataの所要時間は別実測で更新し、短いS03速度から実Captureの完了時間を断定しない。

試験runnerは独立したhidden processで起動し、status/log/run ID/PIDをGit管理外へ保存する。長時間の自動ポーリングを既定にせず、起動確認と再開手順を示す。失敗時は原因を記録して未完了分を再開し、成功結果を再生成しない。

### 11.9 互換性と移行・戻し方

- 設定追加はopt-inとし、未指定時は現行codec/window/Final経路を保持する。単独採用の段階ごとにconfiguration versionを更新する。
- DB変更は追加migrationで行い、既存カラム/ID/世代を再利用して意味を書き換えない。実DBへ適用する前にDB複製上で移行・旧読取を確認する。
- 変更前のRaw・DBの復元用コピーとhashをGit管理外に保持する。DB migrationのreverse/dropやGit履歴書き換えを通常の戻し方にしない。
- 問題があれば新設定を無効にし、旧Fragment/検索/文書世代を利用する。Schema上互換な旧読取とactive切替を検証し、CLI/APIの破壊的変更を避ける。
- E0〜E1の完了はE2以降や代表8Captureの全モデル品質評価の完了を意味しない。各段階で実装・自動検証・実データ比較・human gold・採用を別々に記録する。

## 12. 計画に基づく実装と確認（2026-10-06）

§1〜11の現状分析は変更前のPrototype 0.2を対象とする。今回、次の経路を追加した。**実装済みと品質上の採用済みは区別する。**

| 段階 | 実装 | 確認範囲 |
|---|---|---|
| E0 評価条件固定 | Providerの`structured_mode`、constraint method、transport対応表hash、抽出設定を台帳・benchmarkへ保存。固定S03の4条件比較runnerを追加 | 同じStrata runtimeで16リクエストを実施。human goldは未付与 |
| E1 出力量・無駄再送削減 | 出力上限を型付きエラーで分類し、新jobは直ちに分割。形式違反は1回再試行。可逆Compact key codec、引用本文の重複送信削減、API Schema／Promptのみの明示切替 | canonical復元、null・未知key・引用契約、自動分割、実Strata比較 |
| E2 window再開 | 成功window・multi-passの成功focusと子分割計画をjob単位で保存。再開時は成功分を再利用 | sibling・focus失敗と再開、失敗した親入力の再送回避 |
| E3 Adaptive Packer | 原文文字spanのtoken packing、表/list/postの密度補正、context全体の予算確認。互換model/revision/provider/codecの成功履歴から最大output/material比＋25%余裕でtargetを縮小し、参照AI IDと計画をjobへ固定 | Unicode全域coverage、予算、履歴参照、再開は固定計画を使用。LM Studio tokenizer経路はSDK mock検証。実機にloaded modelがないため実token経路の接続測定は未実施 |
| E4 Knowledge Claim | 属性・数値・否定・時期を保つ保守的な一致集約、世代・support保存、Claim→Fragment→Evidence→Rawの追跡 | 既存Fragment不変、世代再生成、実評価DB複製で生成 |
| E5 用途別View | LLMなし、query優先とfacet/type分散、本文・引用・文脈を含む全体予算、完全な省略manifest | Markdown／構造JSON両方の予算、context reserve、実評価DB複製で短い表示を出力 |
| E6 増分Embedding | 実際の入力文字列・model/revision/前処理のcache key、変更分だけ推論、全vector確認後に検索世代を保存 | 無変更API呼出0、設定変更時miss、途中失敗時に旧vector維持 |
| E7 意味集約・階層・圧縮 | 上限付きEmbedding候補と任意のLLM relation提案、Claim ID付き抽出的階層、1x/2x/3x/5xの抽出的context選択を実験コマンドとして追加 | 候補上限・出典・非破壊性を自動確認。意味統合の昇格は0。gold未作成のため正式採用は保留 |

E7は評価用の足場である。実装はLLMLingua/RECOMPの学習済みモデルやRAPTORのLLM要約を導入したものではない。属性の異なる`same_claim`提案は`related`へ、時期の異なる`conflict`は`different_time`へ補正し、提案を保存する。曖昧な意味一致を正本へ昇格しない。

### 12.1 使い方と既定値

以下の`<snapshot-id>`等は実環境のIDへ置き換える。実運用設定と生成物はGit管理外へ保存する。

```powershell
# Compactと引用重複削減、成功window再開を有効化
python -m cpc fragment --snapshot '<snapshot-id>' --entity '<entity-id>' `
  --transport compact-keys-v1 --dedup-quotes --window-checkpoint
# 再開は初回と同じ設定に --resume '<job-id>' を追加

# 派生Claim、短いView、省略manifest（view.omitted.json）
python -m cpc claims --entity '<entity-id>'
python -m cpc view --entity '<entity-id>' --mode short --out .local/documents/view.md
python -m cpc provenance claim '<claim-id>'
python -m cpc embed --incremental

# 実験経路。judgeは設定済みローカルLLMを使う追加推論
python -m cpc claim-experiment --entity '<entity-id>' --max-pairs 20 --judge
python -m cpc compression-experiment --entity '<entity-id>' --budget 12000
```

新しい抽出jobは出力上限時に即分割する。その他はopt-inで、未指定ならcanonical／480文字window／従来の全量`generate`を維持する。旧v4 jobの再開は元のretry・Provider条件を維持し、新設定への途中切替を拒否する。互換Providerは`CPC_LLM_STRUCTURED_MODE=api_schema`または`prompt_only`を記録する。LM Studio native経路はPromptのみであり、API Schema比較にはcompatible経路を使う。StrataはSchemaを受け取っても内部制約を保証しないため`prompt_and_validate`と記録する。

Viewの初期予算はshort=4000、standard=12000、detailed=24000、context=12000。`--budget`で変更できる。既定の`utf8-upper-bound`は**UTF-8バイト数による保守的な推定単位で、実token数ではない**。contextモードは消費先の`--context-tokens`を必須とし、query・出力reserve・512単位の余裕を差し引く。消費側のsystem追加文等が大きい場合はその分を予算からさらに引く。

正確なtoken経路は、任意依存を追加し、対象モデルをあらかじめLM Studioへロードして使用する。モデルの自動ロードは行わない。

```powershell
python -m pip install -e '.[token-counting]'
python -m cpc fragment --snapshot '<snapshot-id>' --entity '<entity-id>' `
  --packer token --token-counter lmstudio --material-tokens 2000 `
  --context-tokens 16384 --window-checkpoint
python -m cpc view --entity '<entity-id>' --token-counter lmstudio `
  --model '<loaded-model-key>' --mode context --out .local/documents/context.md
```

token packingの実tokenizerは[LM Studioのtokenize／Prompt template API](https://lmstudio.ai/docs/python/tokenization)を使用し、loaded instanceのcontext上限も確認する。StrataへLM Studioの別モデルのtokenizerを流用しない。`--packer token`で推定counterを選ぶ場合は従来文字windowへ明示的にfallbackし、context確認も推定として記録する。実token pathの実データ測定、1000/2000/4000 token比較は今後の採用試験。

### 12.2 Strataでの実測

固定合成資料S03、Qwen3.8-Flash-Next IQ3_S、同じengine/context/projection設定、APIへSchemaを送る条件。各条件warmup 1回＋本測定3回。台帳全attemptを集計し、再試行込みの使用量を比較した。

| 条件 | 総時間中央値（範囲、秒） | 入力token | 出力token | 時間短縮 |
|---|---:|---:|---:|---:|
| canonical | 17.71（17.66〜17.94） | 2971 | 1498 | control |
| 引用重複削減 | 17.55（17.37〜17.71） | 2657 | 1498 | 0.9% |
| Compact | 15.62（15.55〜16.83） | 3000 | 1357 | 11.8% |
| Compact＋引用重複削減 | 14.98（14.55〜15.00） | 2686 | 1357 | 15.4% |

16/16回でCPC Schema・引用検証成功、各6 Fragment。再試行・失敗0、SQLite integrity正常・外部キーエラー0。Compactは文字出力を2855→1698字に減らすが、token削減は1498→1357（約9.4%）。対応表の説明によりCompact単独の入力tokenは増えた。文字圧縮率を速度・token削減率と同一視しない。

本測定はPrompt cacheが温まった条件で、実CaptureのCold処理や意味品質の改善を示さない。約15.4%短縮は初期目標20%に未達。旧速度試験のPromptのみ条件とは別runである。

runner: `scripts/run_efficiency_preflight.py`。結果: Git管理外の`sample/efficiency-preflight/comparison.txt`、`comparison.json`、個別canonical Fragment、AI台帳。再集計は`python scripts/run_efficiency_preflight.py --summarize`。新測定は新しい`--out`を指定し、停止した場合だけ同じruntime・入力で`--resume`を使用する。共有サーバーがbusyなら推論を開始しない。

### 12.3 既存実データでの派生表示確認

`scripts/run_efficiency_derived.py --source .local/upgrade.sqlite`でSQLite backup APIによる複製へmigrationを適用し、既存5246 Fragmentを対象にClaimとViewを生成した。

| Entity種別 | Fragment | Claim | 4000推定単位Viewに表示 | 省略 | 生成時間 |
|---|---:|---:|---:|---:|---:|
| Character | 524 | 508 | 4 | 504 | 0.19秒 |
| Work | 4722 | 4465 | 4 | 4461 | 2.99秒 |

UTF-8推定量は3098／3820、いずれも予算内。引用・文脈を含む完全なblockを選択するため、表示件数は少ない。全情報の代替ではなく短い入口として使い、省略manifestとClaim provenanceから全件へ戻れる。query・より大きい予算・実token counterの使用を検討する。人間の可読性や選択Recallは未評価。

元DBのSHA256／更新日時と対象Fragmentの内容不変、移行後integrity正常・外部キーエラー0を確認。結果はGit管理外の`sample/efficiency-derived/`へ保存した。正本DBとRawに移行・書き換えは行っていない。

### 12.4 移行・残る採用判定

`003_efficiency.sql`はwindow/split、Claim/support、vector cacheを追加するmigration。旧テーブルを破壊せず、0.2 DB複製と旧読取を確認した。新CLIは指定DBを開くとmigrationを適用するため、正本へ適用する前にSQLite backupで復元用コピーを作る。戻す場合は追加tableをdropせず新オプションを無効にし、既存世代・`generate`を利用する。

関連自動テストは90件成功、lint・差分チェックを実施。残る採用判定は開発2Capture／代表8Captureのcontrol比較、token packの実機測定、human gold・保留資料評価、意味relation／階層／圧縮の品質評価である。今回の合成資料の速度と契約成功から、これらを品質合格へ繰り上げない。

### 12.5 実Captureの変更前後再抽出比較

`scripts/run_efficiency_capture_comparison.py`で代表8Captureを変更前`94f7e9c`／変更後`e95d06e`から再抽出する。両コミットの`src`をGit管理外へ展開し、同一のSQLite backupから別々のDBを作る。正本DBを変更しない。過去のQwen評価と現在のStrata評価を設計変更の速度効果として直接比較しない。

今回の条件は同じロード済みStrata、output8192、batch1、single_pass、固定文字window。変更後はCompact＋引用重複削減＋window checkpointを有効にする。即時分割も変更後コードの挙動に含まれる。実tokenizer・Embedding・Viewは今回の再抽出比較の対象外。変更前後の実行順はCaptureごとに交互にし、Prompt cache使用量を記録する。共有サーバーを再起動したりcacheを消したりせず、各リクエスト前にidle・runtime不変を確認する。

比較出力は総時間、再試行を含むAPI tokenと呼出数、失敗試行、Fragment数、抽出内容の完全一致・追加／削除または変更、Raw hash／更新日時、DB整合性。ID・AI runの違いは内容比較から除外するが、主語・情報種別・強度・時期・Evidence参照などは比較する。重複数の変化も残す。完全一致率は意味Recall/Precisionの代替ではなく、内容差分を人間が評価する入口とする。

```powershell
# 初回は準備・再抽出・比較を順に実行。既存の出力フォルダは上書きしない
python scripts/run_efficiency_capture_comparison.py
# 中断・失敗後、同じruntimeで成功分を保ち再開
python scripts/run_efficiency_capture_comparison.py --resume
# 状態とエラー
Get-Content sample/efficiency-capture-comparison/status.json
Get-Content sample/efficiency-capture-comparison/worker.log -Tail 20
```

処理は独立したhidden processで実行する。各Captureの前後が揃うたび、`sample/efficiency-capture-comparison/comparison.txt`／`comparison.json`／内容差分JSONへ反映する。現時点では起動段階であり、速度・内容比較の結論は結果確認後に記載する。旧Qwen全量約5.1時間と今回のStrata予備速度を参考にすると両条件で十数時間規模が目安だが、実データでの分割・再試行が異なるため未確定。成功条件は16ケース完了、Raw不変、DB整合性正常、元DB不変。失敗や未完了を速度向上・品質合格として扱わない。

### 12.6 分割外本文の混入修正と再試験（2026-10-07）

初回比較は変更後`fragment-07`の1バッチが最小windowでも出力上限に達し、13/16ケースで停止した。途中にサーバー中断もあり、復旧後のcache差と中断試行を台帳へ残した。

原因はLLM入力の`metadata.content`に元のEvidence本文が残ることだった。対象本文84文字・隣接本文120文字のwindowでも、それぞれのmetadataに約1000文字の分割前本文が入り、実質的に分割が効いていなかった。失敗入力をPromptのみ・上限2048の診断条件でcanonical/Compactへ送ると、両方が上限へ到達した。保存した生成本文には、window外の曲名が候補Entityとして多数列挙されていた。Compactに限る不具合ではない。

修正は**新jobのLLM入力からEvidence/neighborのmetadata.contentだけを除去**する。artifact・positions・section・分類は保持し、保存済みEvidence/Rawは変更しない。元本文の全域は引き続きwindowで処理する。引用selector・canonical保存Schema・検証基準は変更しない。algorithmは`full-evidence-v6-scoped-window-input`とし、v5の途中jobへ変更条件を混在させない。旧v4 jobの明示再開は元条件を維持する。

同じ失敗入力について、修正後のAPI Schema・上限8192・同じStrataで確認した結果:

| 形式 | CPC引用/Schema検証 | 出力token | 総応答時間 | Fragment |
|---|---|---:|---:|---:|
| canonical | 成功 | 1056 | 13.96秒 | 3 |
| Compact | 成功 | 1196 | 16.21秒 | 4 |

この表は回復確認であり、変更前2048・Promptのみの診断条件と速度の同条件比較を行ったものではない。形式適合は意味Recall/Precisionの合格を保証しない。診断本文・台帳はGit管理外の`sample/efficiency-failure-probe/`、修正確認は`sample/efficiency-failure-probe-fixed/`へ保存する。

全量再試験は別ディレクトリ`sample/efficiency-capture-comparison-v2/`を使用する。修正後8Captureを全件再測定し、条件一致を確認した変更前の成功済み7Captureを再利用、変更前8件目も実行する。再利用時はmodel/runtime・dataset/normalized generation・batch・output budgetを照合し、条件不一致は拒否する。初回の失敗結果やAI台帳は保持し、修正版の結果で上書きしない。

```powershell
# <fix-commit>は修正コミットへ置換。新しい出力フォルダを使用
python scripts/run_efficiency_capture_comparison.py --after-commit '<fix-commit>' `
  --reuse-before sample/efficiency-capture-comparison `
  --out sample/efficiency-capture-comparison-v2
# 起動後は状態確認。失敗時は同じ --out と --resume で成功分を保持して再開
Get-Content sample/efficiency-capture-comparison-v2/status.json
```

Metadata本文混入の防止・Evidence不変、比較集計、既存Upgradeを含む関連テストを実施した。全量再試験の完了と品質判定は結果確認後に記載する。
