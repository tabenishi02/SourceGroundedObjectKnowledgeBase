# Reranker / Second-stage Retrieval Evaluation — Phase I / I-06

更新日: 2026-10-14

- Status: **Accepted / Evaluation Complete**
- Task: `I-06 [P1] Reranker / second-stage retrievalを評価する`
- Prerequisites:
  - `docs/design/EMBEDDING_PROVIDER_MODEL_EVALUATION.md`
  - `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
  - `docs/design/OBJECT_SIMILARITY_SEARCH.md`
- Next task: `I-07 [P0] 検索品質gold / Backend benchmarkを作成する`

---

## 1. 結論

I-06ではRerankerをMVP必須機能として即時有効化しない。

I-07の正式Search goldへ持ち込む候補を、balanced / qualityの2 profileへ固定する。

```text
Balanced / default candidate:
  BAAI/bge-reranker-v2-m3
  revision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e

Quality candidate:
  zeroentropy/zerank-2-reranker
  revision 5eae30d5ee3c6b2df2ef6d723bde45172d761c4c

Provisional candidate pool:
  first-stage top 50

Decision:
  both evaluated
  NOT enabled as mandatory production reranker before I-07
```

理由:

1. legacy SGOKB実データ由来の暫定26 Queryでは、Harrier first-stageに対して明確な順位改善があった。
2. `Qwen3-Reranker-4B`と品質差が非常に小さい。
3. 4Bよりlatency / VRAMが大幅に小さい。
4. Apache-2.0で、Jina v3.5のCC BY-NC制約を持たない。
5. 現行Windows / RTX 4090 / sentence-transformers環境で追加custom runtimeなしに動作した。
6. ただし26 QueryはI-07の正式goldではないため、ここでHybrid Search defaultへ組み込むのは早い。

したがってI-06の判断は、

> **BGE v2-m3をbalanced/default候補、zerank-2をquality候補としてI-07へ送り、正式goldで有効性とcostを再確認するまでproduction default化を保留する。**

とする。

---

## 2. Rerankerの責務

Rerankerはfirst-stage retrievalの代替ではない。

```text
Query
  ↓
Lexical / Semantic / Hybrid first-stage
  ↓
Top-N candidate Objects / Statements
  ↓
Reranker
  ↓
同じcandidate集合の順序だけを変更
```

Rerankerは候補集合外のObjectを新しく発見できない。

例えば正解Objectがfirst-stage top 50に存在しなければ、top 50だけを見るRerankerはそのObjectを救えない。

このためPhase Iでは、

```text
first-stage Recall
  ↓
十分なcandidate pool
  ↓
second-stage ranking quality
```

の順に評価する。

---

## 3. I-06評価corpus

I-02で使用したlegacy CPC / SGOKB実データを評価専用corpusとして再利用した。

canonical migrationには使用しない。

```text
Statement-like Search Representations: 4,851
Queries:                            26
Japanese queries:                   16
English -> Japanese queries:        10
```

Search Representation形式:

```text
Object: <entity name>
Primary Class: <legacy entity type>
Facet: <legacy facet>
Statement: <content>
```

relevance labelはI-02と同じ既知target fragmentを使用した。

これはI-07正式goldではない。

用途:

- model間の相対比較
- latency / VRAM比較
- reranking導入価値の初期判定
- candidate pool設計入力

に限定する。

重要な制約として、この暫定benchmarkはI-02由来のStatement Search Representationを直接rerankしており、I-04のHybrid RRF / Object Aggregationをend-to-endで直接評価するものではない。

I-07では少なくとも、

```text
Statement / representation rerank -> Object aggregation
Object aggregation -> Object-level rerank
```

の配置差もgold上で比較し、最終second-stage位置を決定する。

---

## 4. First-stageを固定する

I-06でEmbedding model差を再評価しない。

first-stageはI-02で固定した次の条件を使用した。

```text
Model:
  microsoft/harrier-oss-v1-0.6b

Dimension:
  1024

Normalization:
  L2

Query instruction:
  Given a query about an object knowledge base,
  retrieve semantically relevant object knowledge statements.
```

4,851件全体からExact cosineで順位を作り、各Queryのtop 50を固定candidate setとして保存した。

Rerankerはこの同一50候補だけを再順位付けした。

これにより、

```text
Embedding差
Vector backend差
Reranker差
```

を混同しない。

---

## 5. First-stage baseline

Harrier単独:

| Metric | Result |
|---|---:|
| MRR | 0.797543 |
| Recall@1 | 69.23% |
| Recall@5 | 92.31% |
| Recall@10 | 96.15% |
| nDCG@10 | 0.786495 |

candidate pool内に少なくとも1 relevant targetが存在するQuery比率:

| Candidate depth | Recall |
|---|---:|
| top 10 | 96.15% |
| top 20 | 96.15% |
| top 30 | 96.15% |
| top 40 | 100% |
| top 50 | 100% |

暫定corpusにはfirst-stage rank 36のtargetが1件存在した。

そのためtop 10〜30だけをRerankerへ渡すと、このQueryは原理的に救えない。

I-06では余裕を持たせてtop 50を共通評価条件とした。

---

## 6. 評価candidate

### 6.1 BAAI/bge-reranker-v2-m3

```text
Revision:
953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e

License:
Apache-2.0

Runtime:
sentence-transformers CrossEncoder
```

pairwise Cross Encoderとして評価した。

### 6.2 Qwen/Qwen3-Reranker-0.6B

```text
Revision:
e61197ed45024b0ed8a2d74b80b4d909f1255473

License:
Apache-2.0

Runtime:
sentence-transformers CrossEncoder
```

SGOKB retrieval instructionを明示して評価した。

### 6.3 Qwen/Qwen3-Reranker-4B

```text
Revision:
22e683669bc0f0bd69640a1354a6d0aebcfeede5

License:
Apache-2.0
```

品質上限寄りcandidateとして評価した。

### 6.4 jinaai/jina-reranker-v3.5

```text
Revision:
e8a93f33f0b22108f8c2364f8484ce3422552fbc

License:
CC BY-NC 4.0
```

2026年の新しい0.6B multilingual listwise rerankerとして比較した。

license制約のため、品質が高くても汎用標準profileにはしない。

### 6.5 Alibaba-NLP/gte-multilingual-reranker-base

```text
Revision:
8215cf04918ba6f7b6a62bb44238ce2953d8831c

License:
Apache-2.0
```

306M級の効率候補として試験した。

ただし現行benchmark環境、

```text
transformers 5.19.0
PyTorch 2.8.0+cu128
CUDA
```

ではremote custom modeling code内でCUDA device-side index assertionが発生し、品質benchmarkまで到達しなかった。

これはモデル自体を不適格と断定する結果ではない。

現行SGOKB runtimeとの運用互換性リスクとして記録する。

---

## 7. 実測結果

全candidateはHarrier top 50を同一入力として使用した。

| Model | MRR | R@1 | R@5 | R@10 | nDCG@10 | p50 / 50 candidates | p95 | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Harrier first-stage only | 0.798 | 69.2% | 92.3% | 96.2% | 0.786 | - | - | - |
| **BGE reranker v2-m3** | **0.944** | **92.3%** | **100%** | **100%** | **0.921** | **35.2 ms** | **55.9 ms** | **1.21 GiB** |
| Qwen3 Reranker 0.6B | 0.904 | 84.6% | 100% | 100% | 0.876 | 138.9 ms | 163.3 ms | 1.75 GiB |
| Qwen3 Reranker 4B | **0.949** | 92.3% | 100% | 100% | **0.925** | 606.7 ms | 657.6 ms | 8.06 GiB |
| Jina Reranker v3.5 | 0.910 | 84.6% | 100% | 100% | 0.906 | 316.8 ms | 414.7 ms | 4.63 GiB |
| GTE multilingual reranker | blocked | - | - | - | - | - | - | - |

注意:

- latencyはwarm modelで1 Queryあたり50 candidateをrerankした時間。
- model初回download時間は比較対象外。
- candidate passageはI-01形式の短いStatement Search Representation中心である。
- 正式production corpus latencyはI-07 / N-06で再測定する。

### 7.1 2026-10-14 追加候補実測

I-06完了後の最新model surveyで見つかった4候補を、同じHarrier top-50 fixtureで追加実測した。
KaLM R2の公式要件に合わせ、追加評価runtimeは `sentence-transformers 5.6.0 / transformers 5.19.0 / PyTorch 2.8.0+cu128 / CUDA BF16` とした。比較基準のBGEも同runtimeで再実測し、品質値が初回評価と一致することを確認した。

| Model | MRR | R@1 | R@5 | R@10 | nDCG@10 | p50 / 50 candidates | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| Harrier first-stage only | 0.798 | 69.2% | 92.3% | 96.2% | 0.786 | - | - |
| **BGE v2-m3 (ST 5.6 retest)** | **0.944** | 92.3% | 100% | 100% | 0.921 | **55.5 ms** | **1.21 GiB** |
| KaLM-Reranker-V1-Nano-R2 | 0.721 | 61.5% | 92.3% | 92.3% | 0.740 | 393.4 ms | 2.22 GiB |
| KaLM-Reranker-V1-Small-R2 | 0.907 | 84.6% | 96.2% | 96.2% | 0.870 | 949.6 ms | 4.44 GiB |
| Qwen3-VL-Reranker-2B | 0.890 | 84.6% | 96.2% | 96.2% | 0.873 | 373.3 ms | 4.09 GiB |
| **ZeroEntropy zerank-2** | **0.971** | **96.2%** | **100%** | **100%** | **0.953** | 411.8 ms | 9.14 GiB |

追加候補のrevision:

```text
KaLM Nano R2:   32b242bb7fd7ad6fd404154c09560d249ffe017f
KaLM Small R2:  68b74f09ff2ab5df9b9a9a48c812a81aaff8815e
Qwen3-VL 2B:    4bd860ac4f15ad1897a214615cccc700f8f71818
zerank-2:       5eae30d5ee3c6b2df2ef6d723bde45172d761c4c
```

KaLMは公式defaultの `chunk_size=4` とSGOKB retrieval instructionを使用した。Qwen3-VL 2BもSGOKB retrieval instructionを与えた。zerank-2は公式Sentence Transformers CrossEncoder形式で実行した。

重要な結果:

- zerank-2が暫定corpusの総合品質1位となった。
- zerank-2のJapanese sliceはMRR 1.000、English -> Japanese sliceはMRR 0.925だった。
- BGEのEnglish -> Japanese sliceはMRR 1.000であり、cross-lingualでは依然BGEが強い。
- zerank-2はBGEよりMRRが約0.028高い一方、p50は約7.4倍、Peak VRAMは約7.6倍である。
- KaLM Nano R2はこのSGOKB workloadではfirst-stageより悪化した。
- KaLM Small R2は改善したがBGEより低品質かつ大幅に高latencyだった。
- Qwen3-VL 2Bは日本語sliceでは強いが、text-only総合ではBGEを上回らなかった。

したがってI-07では単一候補ではなく、

```text
Balanced / default candidate:
  BAAI/bge-reranker-v2-m3

Quality candidate:
  zeroentropy/zerank-2-reranker
```

の2 profileを正式goldで比較する。

---

## 8. BGEとQwen 4Bの比較

品質差:

```text
MRR
BGE:       0.943590
Qwen 4B:   0.948718
Difference 0.005128

nDCG@10
BGE:       0.921141
Qwen 4B:   0.925176
Difference 0.004035
```

一方、runtime cost:

```text
p50 latency
BGE:      35.2 ms
Qwen 4B: 606.7 ms

Peak VRAM
BGE:      1.21 GiB
Qwen 4B:  8.06 GiB
```

今回のworkloadではQwen 4Bの品質差は小さい。

BGEに対して、概ね、

```text
~17x p50 latency
~6.7x peak VRAM
```

を必要とする。

したがってQwen 4Bはquality referenceとして保持するが、標準candidateにはしない。

---

## 9. Query別改善 / 悪化

first-stageに対するfirst relevant rankの変化:

| Model | Improved | Degraded | Unchanged |
|---|---:|---:|---:|
| BGE v2-m3 | 8 | 1 | 17 |
| Qwen3 0.6B | 7 | 2 | 17 |
| Qwen3 4B | 8 | 1 | 17 |
| Jina v3.5 | 7 | 4 | 15 |

BGEで悪化した暫定Query:

```text
ja_mano_scout
```

つまりRerankerは常に改善するわけではない。

平均指標だけでdefault化せず、I-07ではQuery category別regressionを確認する。

---

## 10. Japanese / cross-lingual傾向

BGE:

```text
Japanese MRR:            0.9083
English -> Japanese MRR: 1.0000
```

Qwen 4B:

```text
Japanese MRR:            0.9583
English -> Japanese MRR: 0.9333
```

暫定corpusでは、

- Qwen 4Bは日本語Queryで強い
- BGEはcross-lingual Queryで特に安定した

という差が見えた。

26 Queryでは一般化できないため、I-07で日本語 / cross-lingualを別sliceとして評価する。

---

## 11. FastEmbed評価

FastEmbedは軽量ONNX runtimeとして有用である。

ただしI-06時点の公式Cross Encoder catalogでは、主に、

```text
MiniLM rerankers
BAAI/bge-reranker-base
Jina reranker v1 English
Jina reranker v2 multilingual
```

が公開されている。

I-06で実測上有力だった、

```text
BAAI/bge-reranker-v2-m3
Qwen3-Reranker
jina-reranker-v3.5
```

を同じFastEmbed contractでそのまま使用する構成ではない。

また公式multilingual Jina v2 profileはCC BY-NC 4.0である。

そのため、I-06の標準Reranker runtimeとしてFastEmbedを固定しない。

将来FastEmbed catalogが更新された場合はProvider候補として再評価できる。

---

## 12. Second-stage contract

I-07でRerankerを有効化する場合も、first-stage contractを壊さない。

概念contract:

```text
RerankerProvider.rerank(
    query,
    candidates,
    limit,
) -> ordered candidates + reranker scores
```

入力candidateには最低限、

```text
object_id
version_id
representation_id / statement_id
representation text
first-stage rank
first-stage channel / reason
```

を保持する。

Reranker後もfirst-stage match reasonを失わない。

---

## 13. Score semantics

Reranker scoreは検索関連度signalである。

禁止:

```text
reranker score
  != truth probability
  != Knowledge confidence
  != Source trust
  != Evidence strength
```

Hybrid SearchのRRF scoreとも別尺度である。

結果を返す場合は、

```text
first_stage_score / rank
reranker_score / rank
score_type
```

を明示的に分離する。

---

## 14. Failure behavior

RerankerはDerived Search dependencyである。

将来optionalに有効化した場合、failure時にcanonical Knowledgeへ影響させない。

禁止:

- current Version rollback
- Vector Index変更
- external rerankerへのsilent fallback
- 別local modelへのsilent fallback

Rerankerがoptional enhancementとして設定されている場合のfallback policyはI-07で明示する。

少なくとも障害を隠して「reranked」と表示してはならない。

---

## 15. I-06でproduction codeへ入れないもの

I-06はevaluation Taskである。

そのため次はまだ実装しない。

```text
mandatory RerankerProvider
HybridObjectSearchへの自動second-stage挿入
BGE modelのproduction dependency固定
reranker result persistence
reranker cache
```

理由は、正式goldなしに暫定26 Queryだけでranking pipelineを固定しないためである。

I-07通過後に必要なら実装Taskへ昇格する。

---

## 16. I-07へ引き継ぐ評価条件

I-07では少なくとも次を比較する。

```text
A. no reranker
B. BGE reranker v2-m3
C. Qwen3-Reranker-4B quality reference
```

candidate depth:

```text
20
40
50
100
```

主指標:

```text
Statement Recall@K
Object Recall@K
MRR
nDCG@10
category-level regression
p50 / p95 latency
Peak VRAM
```

特に、

- exact name / alias
- fine-grained Statement
- conditional / exception
- temporal
- Japanese
- cross-lingual
- Facet-specific

を別sliceで確認する。

first-stageで取得できなかったObjectはReranker評価から救済されたことにしない。

---

## 17. Model selection decision

### Balanced / default candidate for I-07

```text
BAAI/bge-reranker-v2-m3
```

理由:

- 暫定品質が高い
- top-50 rerankが50ms前後で軽量
- Peak VRAM約1.21 GiB
- cross-lingual sliceが非常に強い
- Apache-2.0
- current SGOKB runtimeで安定動作

### Quality candidate for I-07

```text
zeroentropy/zerank-2-reranker
```

理由:

- 追加評価でMRR 0.971 / Recall@1 96.2%と総合1位
- Japanese slice MRR 1.000
- Qwen3-Reranker-4Bより高品質かつ低latency
- Apache-2.0

ただしmodel card metadataはEnglishであり、約9 GiB VRAM / 約0.4 s p50を要するため、正式goldで日本語・cross-lingual generalizationを再確認する。

### Secondary quality reference

```text
Qwen/Qwen3-Reranker-4B
```

### Research references

```text
jinaai/jina-reranker-v3.5
KaLM-Embedding/KaLM-Reranker-V1-Nano-R2
KaLM-Embedding/KaLM-Reranker-V1-Small-R2
Qwen/Qwen3-VL-Reranker-2B
```

### Runtime compatibility follow-up only

```text
Alibaba-NLP/gte-multilingual-reranker-base
```

---

## 18. Final decision

```text
I-06 status:
  Complete

Production mandatory reranker:
  No

I-07 balanced/default candidate:
  BAAI/bge-reranker-v2-m3

I-07 quality candidate:
  zeroentropy/zerank-2-reranker

Provisional rerank depth:
  top 50

Secondary quality reference:
  Qwen3-Reranker-4B

Next:
  I-07 formal Search gold / end-to-end benchmark
```

**Status: I-06 Complete / I-07 Ready**


---

## 19. Official references

- BGE reranker v2-m3: https://huggingface.co/BAAI/bge-reranker-v2-m3
- Qwen3 Reranker: https://huggingface.co/Qwen/Qwen3-Reranker-0.6B
- Jina Reranker v3.5: https://huggingface.co/jinaai/jina-reranker-v3.5
- GTE multilingual reranker: https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base
- KaLM Reranker Nano R2: https://huggingface.co/KaLM-Embedding/KaLM-Reranker-V1-Nano-R2
- KaLM Reranker Small R2: https://huggingface.co/KaLM-Embedding/KaLM-Reranker-V1-Small-R2
- Qwen3-VL-Reranker-2B: https://huggingface.co/Qwen/Qwen3-VL-Reranker-2B
- ZeroEntropy zerank-2: https://huggingface.co/zeroentropy/zerank-2-reranker
- FastEmbed rerankers: https://qdrant.tech/documentation/fastembed/fastembed-rerankers/


---

## 20. I-07 formal gold follow-up

I-07のfrozen Search goldでBGE v2-m3とzerank-2を再比較した。Harrier Statement top-50 candidate Recallは両者とも100%。Statement単位ではBGE MRR 0.970、zerank-2 MRR 1.000だったが、Statement→Object aggregation後およびObject-level rerankでは両者ともObject MRR 1.000 / Recall@10 100%となり、品質差はほぼ消えた。BGEはStatement rerank p50約19 ms / peak約2.24 GiB、zerank-2は約48 ms / 9.43 GiBだった。

したがってI-06の最終位置づけは維持する。

```text
Balanced / default candidate: BAAI/bge-reranker-v2-m3
Quality candidate: zeroentropy/zerank-2-reranker
Production mandatory reranker: No
```

正式goldと100k backend結果の正本は`docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`。
