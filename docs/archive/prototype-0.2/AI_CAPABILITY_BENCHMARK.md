> [!WARNING]
> **ARCHIVED / LEGACY — Prototype 0.2**
>
> この文書は旧Prototype 0.2の歴史資料です。**現行SGOKBの仕様・設計・運用手順ではありません。**
> 現行仕様は [Current Architecture](../../design/SGOKB_CURRENT_ARCHITECTURE.md) と [root README](../../../README.md) を参照してください。
> 以下の本文は再現性・設計経緯のため当時の内容を保持しています。

# SGOKB ローカルAI能力比較計画

## 1. 目的

本書は、Source Grounded Object Knowledge Base（SGOKB）の文章処理能力を改善するために、**ローカルAIのみを使用してモデル・処理方式・検索構成を比較するためのベンチマーク計画**を定義する。

比較対象は次の3段階とする。

1. Fragment Extraction能力
2. Final Document生成能力
3. Embedding / Retrieval能力

クラウドAIは今回の比較対象に含めない。

本比較の目的は単純に「最も高性能なモデル」を選ぶことではない。

SGOKBでは処理段階ごとに要求される能力が異なるため、

- Fragmentでは高Recallで情報を取りこぼさない能力
- Final Documentでは大量Fragmentを構造化・統合する能力
- Retrievalでは必要なEvidence / Fragmentを高精度で検索する能力

を個別に測定し、最終的に適切な組み合わせを決定する。

本書は `docs/archive/prototype-0.2/PROTOTYPE_CONTENT_REVIEW.md` の改善方針を前提とする。

---

# 2. 基本原則

## 2.1 ローカルAIのみ使用する

今回の比較ではクラウドAPIを使用しない。

比較対象はRTX 4090 24GBを中心としたローカル実行を前提とする。

CPU/RAM Offloadを利用するモデルは比較対象に含めてもよいが、日常運用性が低い場合はその旨を明示する。

---

## 2.2 モデル比較とシステム比較を分離する

同じモデルでもPrompt・処理回数・Reviewer有無によって結果が大きく変わる。

そのため、

```text
モデルA Single Pass
vs
モデルB Multi Pass
```

のような比較だけでは、モデル差とシステム差を区別できない。

原則として、

1. 同一モデルで処理方式を比較する。
2. 勝った処理方式を固定する。
3. 複数モデルを同一条件で比較する。

の順で評価する。

---

## 2.3 入力条件を固定する

同一のEvidence、Fragment、Query、Prompt、Context Budget、出力Schemaを各候補へ与える。

量子化方式やContext Lengthが異なる場合は必ず記録する。

モデル間比較で入力材料が異ならないようにする。

---

## 2.4 実データとGold Setを分ける

`sample/` の実Web Captureを利用するが、全データを毎回すべてモデルへ渡す必要はない。

比較用に代表性のある固定サンプル集合を選び、評価中は変更しない。

可能であれば人間が確認したGold Setを作成する。

Gold Setには少なくとも、

- 抽出されるべきFact
- 抽出されるべきInterpretation
- 抽出されるべきPublic Perception
- 検索Queryと正解Evidence / Fragment
- Final Documentに含めるべき主要情報

を定義する。

実Webページ本文そのものをGitへコミットしない。

Gold Setには必要に応じて匿名化・要約・人工Fixtureを利用する。

---

# 3. Fragment Extraction比較

## 3.1 評価目的

Fragment Extractionでは、文章の自然さよりも**Evidenceに含まれる意味情報をどれだけ漏らさずFragment化できるか**を最重要視する。

評価観点：

- Fragment Recall
- Fragment Precision
- Evidence Coverage
- 1 EvidenceあたりFragment数
- Fact / Interpretation / Public Perception分類精度
- Entity / Facet分類精度
- Unsupported Fragment率
- 重複Fragment率
- JSON / Schema遵守率
- 処理速度
- VRAM使用量

Fragment数そのものを目的にはしない。

意味のあるEvidenceから十分なFragmentが生成されることを重視する。

---

## 3.2 比較する処理方式

### F-S1: Single Pass

現行方式に近いBaseline。

```text
Evidence + Page Context
        ↓
LLM 1回
        ↓
Fragment[]
```

長所：

- 高速
- 実装が単純

短所：

- LLMが重要情報だけを選択し、細かい情報を捨てる可能性がある

---

### F-S2: High-Recall Multi Pass

情報種別ごとに抽出処理を分ける。

```text
Evidence + Page Context
        ├─ Fact Extraction
        ├─ Interpretation Extraction
        └─ Public Perception Extraction
                ↓
             Merge
```

目的はPrecisionではなくRecallを高めることである。

同一内容の重複は後段で処理可能とし、抽出時点で過剰に削減しない。

---

### F-S3: Extract + Review

```text
Evidence + Page Context
        ↓
Extractor LLM
        ↓
Fragment候補
        ↓
Reviewer LLM
「未抽出の意味情報が残っていないか」
        ↓
追加Fragment
        ↓
Merge
```

Reviewerは既存Fragmentの文章修正を主目的とせず、**取りこぼし検出**を主目的とする。

---

## 3.3 Fragment比較モデル

第一比較対象として次の8モデルを使用する。

| ID | モデル | 位置づけ |
|---|---|---|
| F-M1 | gpt-oss-20b | 現行Baseline |
| F-M2 | Qwen3.8-27B | 高性能Dense基準 |
| F-M3 | Gemma 4 26B-A4B | Google系MoE比較 |
| F-M4 | Mistral Small 3.2 24B | Instruction Following重視比較 |
| F-M5 | Ministral 3 14B | 小型・高速比較 |
| F-M6 | Nemotron 3 Nano 30B-A3B | 高効率MoE比較 |
| F-M8 | meta/muse-glimmer | Meta系比較（Q4_K_M） |
| F-M9 | google/gemma-4-31b-qat | Google系Dense比較（Q4_0） |

追加比較候補：

| ID | モデル | 用途 |
|---|---|---|
| F-M7 | Phi-4 reasoning-plus | Reviewer / epistemic type分類の専門候補 |

Phi系は必ずしも大量Fragment生成の主力とはせず、F-S3のReviewerや `fact / interpretation / public_perception` 分類補助として比較してよい。

正確なModel ID、GGUF、量子化方式は実験開始時に固定し、結果へ記録する。

---

## 3.4 Fragment実験順序

### Phase F1: System comparison

まず現行Baselineモデル `gpt-oss-20b` を固定し、

- F-S1 Single Pass
- F-S2 High-Recall Multi Pass
- F-S3 Extract + Review

を比較する。

目的：Prompt / System構成変更だけでどこまで改善するかを測る。

### Phase F2: Model comparison

Phase F1で最も有望だった処理方式を固定し、F-M1〜F-M6を比較する。

### Phase F3: Specialist comparison

必要に応じてPhi-4 reasoning-plus等をReviewerとして追加し、

- Extractor単独
- Extractor + Reviewer

の費用対効果を比較する。

---

# 4. Final Document比較

## 4.1 評価目的

Final Documentでは、Fragmentの単純要約ではなく、**大量のFragmentを情報の性質を維持したまま構造化・統合する能力**を評価する。

特に、

- Fact
- Interpretation
- Public Perception

を混同せず分離して記述できることを重視する。

評価観点：

- Gold Fragment Coverage
- 重要情報の網羅率
- Unsupported Claim率
- Fragment / Evidenceへの忠実性
- Fact / Interpretation / Public Perception分離精度
- Facet構造の妥当性
- 重複記述率
- 矛盾情報の保持能力
- AIが読みやすい構造
- 固有名詞・関係性の正確性
- 文書量
- 生成速度
- VRAM使用量

文章の華麗さより、情報密度と正確な構造を優先する。

---

## 4.2 比較する生成方式

### D-S1: Flat Top-N

現行Baseline。

```text
検索Top-N Fragment
        ↓
LLM
        ↓
Final Document
```

---

### D-S2: Hierarchical Generation

推奨候補。

```text
関連Fragment
    ↓
Facet分類
    ↓
Facetごとに
Fact / Interpretation / Public Perception分類
    ↓
各セクション生成
    ↓
全体統合
```

Facet例：

- 基本情報
- 性格
- 外見
- 能力
- 経歴
- 人間関係
- 世界観
- Timeline

---

### D-S3: Writer + Verifier

```text
Fragment集合
    ↓
Writer
    ↓
Draft
    ↓
Verifier
    ├─ Fragment取りこぼし
    ├─ Unsupported Claim
    ├─ Fact / Interpretation混同
    ├─ 重複
    └─ 矛盾情報の消失
    ↓
Revision
```

Verifierには原Fragment / Evidenceを与え、Draftだけを評価させない。

---

## 4.3 Final Document比較モデル

主要候補：

| ID | モデル | 位置づけ |
|---|---|---|
| D-M1 | gpt-oss-20b | 現行Baseline |
| D-M2 | Qwen3.8-27B | 高性能Dense候補 |
| D-M3 | Gemma 4 26B-A4B | MoE候補 |
| D-M4 | google/gemma-4-31b-qat | Final統合重視候補（Q4_0） |
| D-M5 | Mistral Small 3.2 24B | Instruction Following候補 |
| D-M6 | Ministral 3 14B | 高速・小型基準 |
| D-M7 | meta/muse-glimmer | Meta系統合比較（Q4_K_M） |

Fragment ExtractionとFinal Documentで同一モデルを使う必要はない。

---

## 4.4 Final Document実験順序

### Phase D1: System comparison

1つの固定モデルを使用し、D-S1 / D-S2 / D-S3を比較する。

初期候補はgpt-oss-20bまたはFragment比較で最も安定したモデルとする。

### Phase D2: Model comparison

最良のDocument生成方式を固定し、D-M1〜D-M7を比較する。

### Phase D3: Mixed pipeline

Fragmentに高速モデル、Finalに高品質モデルを割り当てた構成を比較する。

---

# 5. Embedding / Retrieval比較

## 5.1 評価目的

RetrievalではFinal Document生成前に、必要なEvidence / Fragmentを適切に候補へ含められるかを評価する。

評価観点：

- Recall@K
- Precision@K
- MRR
- nDCG@K
- Entity Filter適合率
- Facet Filter適合率
- 日本語Semantic Queryへの対応
- 表現の異なる同義Queryへの対応
- 固有名詞Queryへの対応
- 無関係QueryでのFalse Positive
- Query latency
- Index / Embedding生成時間
- VRAM / RAM使用量

---

## 5.2 Embedding候補

| ID | モデル | 位置づけ |
|---|---|---|
| R-E1 | Nomic Embed Text v1.5 | 現行Baseline |
| R-E2 | Qwen3-Embedding-8B | 高品質多言語候補 |
| R-E3 | BGE-M3 | multilingual / hybrid系候補 |
| R-E4 | multilingual-e5-large-instruct | 軽量多言語比較 |
| R-E5 | Jina Embeddings v4 | 長文・将来multimodal候補 |

同一Embedding Modelでも、

- document prefix
- query prefix
- max input length
- quantization

が変われば別設定として記録する。

---

## 5.3 Reranker候補

| ID | モデル | 位置づけ |
|---|---|---|
| R-R1 | 現行Simple Reranker | Baseline |
| R-R2 | bge-reranker-v2-m3 | 軽量multilingual候補 |
| R-R3 | Qwen3-Reranker-4B | 品質・速度バランス候補 |
| R-R4 | Qwen3-Reranker-8B | 高品質候補 |

---

## 5.4 Retrieval実験順序

### Phase R1: Embedding比較

RerankerをSimpleまたは無効に固定し、R-E1〜R-E5を比較する。

FTS5、Metadata Filter、Candidate Merge条件は固定する。

### Phase R2: Reranker比較

Phase R1で最も有力だったEmbeddingを固定し、R-R1〜R-R4を比較する。

### Phase R3: Hybrid構成

FTS + Semantic + Metadata + Rerankerの最終構成を比較する。

単一Queryだけで判断せず、Gold Query Set全体で評価する。

---

# 6. 初期比較構成

モデル系列の偏りを避けるため、最初の統合比較では最低限次の構成を比較する。

| 構成 | Fragment | Final Document | Retrieval |
|---|---|---|---|
| A Baseline | gpt-oss-20b | gpt-oss-20b | Nomic v1.5 + Simple |
| B Qwen | Qwen3.8-27B | Qwen3.8-27B | Qwen3-Embedding-8B + Qwen3-Reranker-4B |
| C Gemma | Gemma 4 26B-A4B | Gemma 4 26B-A4B | BGE-M3 + bge-reranker-v2-m3 |
| D Mistral | Mistral Small 3.2 24B | Mistral Small 3.2 24B | BGE-M3 + bge-reranker-v2-m3 |
| E Efficient | Ministral 3 14B | Mistral Small 3.2 24B | BGE-M3 + bge-reranker-v2-m3 |
| F Nemotron Mixed | Nemotron 3 Nano 30B-A3B | Qwen3.8-27B | Qwen3-Embedding-8B + Qwen3-Reranker-4B |
| G Final-heavy | Ministral 3 14B または Nemotron 3 Nano | Gemma 4 31B | Qwen3-Embedding-8B + Qwen3-Reranker-4B |

この表は最終採用構成を意味しない。

各段階の個別比較で性能差の原因を確認した後、統合構成を比較する。

---

# 7. 重点比較系列

最初のLLM比較はQwenだけに偏らせず、少なくとも以下の6系列を含める。

```text
OpenAI   : gpt-oss-20b
Qwen     : Qwen3.8-27B
Google   : Gemma 4 26B-A4B / google/gemma-4-31b-qat
Mistral  : Mistral Small 3.2 24B
NVIDIA   : Nemotron 3 Nano 30B-A3B
Meta     : meta/muse-glimmer
```

速度比較用としてMinistral 3 14Bを追加する。

必要に応じてPhi-4 reasoning-plusをReviewer専門候補として使用する。

---

# 8. 測定する実行性能

品質だけでなく、SGOKBの日常運用可否を判断するため以下も記録する。

- Model file size
- Quantization
- Context length
- Prompt tokens
- Completion tokens
- Prompt evaluation time
- Generation time
- Total time
- Prompt tok/s
- Generation tok/s
- Peak VRAM
- RAM使用量
- CPU Offload量
- Error / Retry回数

可能であれば同一Runtime、同一GPU設定で比較する。

Runtimeが異なる場合は、品質比較と速度比較を分離して解釈する。

---

# 9. Fragment品質指標

今後のSGOKBではFragmentを中心的な知識単位として扱うため、次を特に重視する。

## 9.1 Fragment Recall

Gold Fragmentのうち抽出できた割合。

## 9.2 Fragment Precision

生成FragmentのうちEvidenceから妥当に支持される割合。

## 9.3 Evidence Coverage

意味情報を含むEvidenceのうち、少なくとも1つ有用Fragmentへ変換された割合。

```text
Meaningful Evidence Count
Fragmented Meaningful Evidence Count
Coverage = Fragmented / Meaningful
```

## 9.4 Information Type Accuracy

`fact / interpretation / public_perception` の分類精度。

## 9.5 Unsupported Fragment Rate

Evidenceに存在しない意味を追加したFragmentの割合。

---

# 10. Final Document品質指標

最低限次を測定する。

- Fragment Coverage
- Gold Information Coverage
- Unsupported Claim Rate
- Fact / Interpretation / Public Perception separation accuracy
- Duplicate Claim Rate
- Contradiction Preservation Rate
- Citation Validity
- Citation Semantics Accuracy
- Structure Completeness
- Human readability
- AI usability

Citation IDが実在するだけで合格としない。

Claimの内容が実際のFragment / Evidenceによって支持されているかも評価する。

---

# 11. Retrieval品質指標

QueryごとにGold Evidence / Fragmentを定義し、

- Recall@5
- Recall@10
- Recall@20
- MRR
- nDCG@10

等を比較する。

少なくとも以下のQuery種類を用意する。

1. 固有名詞
2. Facet指定
3. 同義語・言い換え
4. 抽象的意味Query
5. 複数条件
6. 無関係Query

例：

```text
「櫻木真乃」
「櫻木真乃の性格」
「自信がないが成長していく人物」
「周囲を安心させるような性格」
```

---

# 12. ベンチマークデータ管理

結果はGit管理可能な集計値と、Git管理外の実データを分離する。

Git管理可：

- Model / Runtime設定
- Benchmark定義
- 匿名化された評価項目
- 集計Score
- 実行時間
- VRAM等のPerformance値
- Gold ID一覧（実本文を含まない場合）

Git管理外：

- Raw Capture
- Evidence実本文
- Fragment実本文（実ページ由来情報を含む場合）
- Final Document実本文
- DB
- API Key等

候補ディレクトリ：

```text
benchmarks/
├─ ai-capability/
│  ├─ config/
│  ├─ gold/
│  ├─ reports/
│  └─ README.md
└─ ...

.local/
└─ benchmarks/
   └─ ai-capability/
      ├─ raw-results/
      ├─ generated/
      └─ databases/
```

---

# 13. Codex実装時の要求

Codexがベンチマーク機能を実装する際は、以下を守る。

1. 本番Pipelineへモデル固有処理を直接埋め込まない。
2. LLM / Embedder / Rerankerの既存交換境界を利用する。
3. モデル名、revision、quantization、Runtime設定を必ず記録する。
4. PromptとSystem方式をVersion管理する。
5. 同一Benchmark Run内では入力条件を固定する。
6. Runごとに一意なBenchmark IDを付ける。
7. 途中失敗しても既存Benchmark結果を破壊しない。
8. 長時間試験は再開可能にする。
9. Raw / sampleファイルを書き換えない。
10. 実Webページ本文をGitへコミットしない。
11. 評価結果からモデル順位だけでなく、失敗傾向を記録する。
12. モデルの自動ダウンロードを行う場合は、ユーザーが明示的に許可できる構造にする。
13. VRAM不足等で実行不能な候補は無理にCPU Offloadして成功扱いせず、運用適性を別評価する。

---

# 14. ベンチマークの実施順序

推奨順序：

```text
Stage 1
Fragment System Benchmark
F-S1 / F-S2 / F-S3
        ↓
Stage 2
Fragment Model Benchmark
F-M1 ... F-M6
        ↓
Stage 3
Embedding Benchmark
R-E1 ... R-E5
        ↓
Stage 4
Reranker Benchmark
R-R1 ... R-R4
        ↓
Stage 5
Final Document System Benchmark
D-S1 / D-S2 / D-S3
        ↓
Stage 6
Final Document Model Benchmark
D-M1 ... D-M6
        ↓
Stage 7
Integrated Pipeline Benchmark
A ... G
```

モデルをすべて組み合わせた総当たり試験は行わない。

段階評価で候補を絞ってから統合比較する。

---

# 15. 最終判断基準

SGOKBでは単純なBenchmark Score 1位ではなく、用途別に判断する。

Fragment Extraction：

```text
Recall
× Groundedness
× 日本語理解
× Throughput
× VRAM効率
```

Final Document：

```text
Coverage
× Groundedness
× 構造品質
× 長文統合能力
```

Retrieval：

```text
Recall@K
× Ranking Quality
× 日本語Semantic性能
× Latency
```

最終的に、Fragment / Final / Retrievalで異なるモデルを採用してよい。

SGOKB全体を1つのモデル系列へ統一すること自体を目標としない。
