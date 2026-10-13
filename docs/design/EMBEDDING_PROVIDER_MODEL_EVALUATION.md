# Embedding Provider / Multilingual Model Evaluation — Phase I / I-02

更新日: 2026-10-13

- Status: **Accepted / Implemented**
- Task: `I-02 [P0] Embedding Provider / 多言語Modelを比較する`
- Prerequisite: `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
- Next task: `I-03 [P0] VectorIndexAdapterを設計しBackendを比較決定する`

---

## 1. 結論

Phase Iの共通Embedding Space baselineは次で固定する。

```text
Provider            sentence-transformers
Model               microsoft/harrier-oss-v1-0.6b
Model revision      f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Output dimension    1024
Native dimension    1024
Max sequence length 32768 tokens
Query instruction   Given a query about an object knowledge base,
                    retrieve semantically relevant object knowledge statements.
Query format        Instruct: <instruction>\nQuery: <query>
Document prefix     none
Normalization       L2 normalize = true
Inference dtype     bfloat16 on CUDA
Persisted dtype     float32
Overflow policy     reject
Fallback            none
```

`object_overall / facet / statement / evidence`の4種類は、I-03のbackend比較ではこの**同一Embedding Space**を使う。

ただし、短いStatementだけを対象にした高速profileとして
`intfloat/multilingual-e5-large-instruct`を保持する。I-02の暫定SGOKB corpusではStatement retrievalのRecallでE5が最良だったが、512 token上限のため全representation kind共通の標準にはしない。

---

## 2. I-02で分離したもの

I-02では次を混同しない。

```text
Search Representation      I-01で固定
       ↓
Embedding Provider         I-02で比較
       ↓
Embedding Model / Space    I-02で固定
       ↓
Float32 Exact baseline     I-02で固定
       ↓
VectorIndexAdapter         I-03で比較
```

Vector backendを変えてmodel品質を測らない。I-03ではI-02で生成した同一Vectorを使う。

---

## 3. Provider比較

### 3.1 sentence-transformers

採用: **Phase I default**

理由:

- Harrier OSS v1 0.6Bを直接扱える。
- RTX 4090 CUDAを利用できる。
- model固有のquery instructionを明示制御できる。
- model revisionを固定できる。
- query instruction / document textをSGOKB側で明示制御できる。
- normalized dense vectorをそのままFloat32 Exact baselineへ渡せる。
- Windows上で実測済み。

初回I-02ではQwen3-Embedding-0.6Bを約719 documents/sで処理した。2026年追加試験ではHarrier OSS v1 0.6Bを約794 documents/sで処理した。

### 3.2 FastEmbed

位置づけ: **optional local provider / CPU・ONNX profile**

I-02で導入したFastEmbed 0.9.0のruntime registryでは、少なくとも次を確認した。

```text
Qwen/Qwen3-Embedding-0.6B
Qwen/Qwen3-Embedding-0.6B-Q
intfloat/multilingual-e5-large
```

Qwen3-Embedding-4Bは当該registryでは利用できないため、I-02共通標準Providerにはできない。

同一Qwen3-Embedding-0.6BをCPU ONNXで64件処理した実測は約3.06 documents/sだった。RTX 4090上のsentence-transformers CUDA実測約719 documents/sとの差が大きいため、現在のSGOKB実行環境ではdefaultにしない。

FastEmbed GPU profileはI-02では採用判定対象外とした。将来ONNX/GPU運用を主目的とする場合はProvider profileとして再評価できる。

### 3.3 OpenAI-compatible / external HTTP provider

既存prototypeの`CompatibleEmbedder`は互換資産として残すが、Phase I defaultにはしない。

理由:

- SGOKBはlocal-only default。
- external providerへのsilent fallbackは禁止。
- provider outageやmodel revision差でEmbedding Spaceが暗黙変更されてはならない。

外部Providerを使用する場合は別Embedding Spaceとして明示登録する。

---

## 4. Model候補

I-02の主要候補:

| Model | License | Native dim | Context | 特徴 |
|---|---|---:|---:|---|
| Qwen3-Embedding-0.6B | Apache-2.0 | 1024 | 32K | 初回軽量baseline |
| Qwen3-Embedding-4B | Apache-2.0 | 2560 | 32K | 初回共通baseline、MRL対応 |
| multilingual-e5-large-instruct | MIT | 1024 | 512 | 短文Statementで高Recall |
| BGE-M3 | MIT | 1024 | 8K | multilingual、初回環境ではload互換性問題 |
| Microsoft Harrier OSS v1 0.6B | MIT | 1024 | 32K | 2026追加試験、軽量・instruction-aware |
| Jina Embeddings v5 Text Small | CC BY-NC 4.0 | 1024 | 32K | 2026追加試験、`trust_remote_code`必要 |
| NVIDIA Nemotron 3 Embed 1B | OpenMDW-1.1 | 2048 | 32K | 2026追加試験、高Top-1 |
| NVIDIA Nemotron 3 Embed 8B | OpenMDW-1.1 | 4096 | 32K | 2026追加試験、品質上限候補 |
| Google EmbeddingGemma 2 | Apache-2.0 | 768 | 8K | 2026追加試験、高速・multimodal対応 |
| Gemini Embedding 2 | API service | 128-3072 | 8K | 外部API比較対象、local-first標準外 |

公式Qwen3 model cardのMultilingual MTEB Retrieval値では、BGE-M3 54.60、multilingual-e5-large-instruct 57.12、Qwen3-Embedding-0.6B 64.64、Qwen3-Embedding-4B 69.60である。これはI-02のSGOKB暫定評価とは独立した外部参考値として扱う。

参照:

- https://huggingface.co/Qwen/Qwen3-Embedding-4B
- https://huggingface.co/intfloat/multilingual-e5-large-instruct
- https://huggingface.co/BAAI/bge-m3
- https://qdrant.github.io/fastembed/
- https://huggingface.co/microsoft/harrier-oss-v1-0.6b
- https://huggingface.co/jinaai/jina-embeddings-v5-text-small
- https://huggingface.co/nvidia/Nemotron-3-Embed-1B-BF16
- https://huggingface.co/nvidia/Nemotron-3-Embed-8B-BF16
- https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/
- https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2

2026追加試験で固定したHugging Face revision:

```text
Harrier 0.6B       f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Jina v5 small      dd76d535f5447ca3897a9c893fb1e612ead98192
Nemotron 1B        c0c9fea93ea424587517f2c59e20db9f1d6bf615
Nemotron 8B        d1f2f25730bbd775b99b29185134bc86653bf2d1
EmbeddingGemma 2   914f7f89142e33e77833254d9c9b90c3cef7303b
```

---

## 5. SGOKB暫定実測

### 5.1 注意

正式なSearch goldはI-07で作成する。

I-02ではmodel比較を実データ分布上で行うため、旧CPC/SGOKB evaluation DBにあるactive Fragmentを**評価corpusとしてのみ**再利用した。

旧Fragmentをcanonical Knowledgeへ復活させたわけではない。

各項目をI-01 Statement representationに近い次の形式へ変換した。

```text
Object: <entity name>
Primary Class: <legacy entity type>
Facet: <legacy facet>
Statement: <content>
```

条件:

- active legacy Fragment: 5,246件
- representation text重複除去後: 4,851件
- Query: 26件
  - 日本語: 16件
  - English query → Japanese document: 10件
- retrieval: normalized vectorによるFloat32 Exact cosine
- metrics: MRR / Recall@1 / Recall@5 / Recall@10
- Hardware: RTX 4090 24GB
- Provider: 初回 sentence-transformers 5.7.0 / 2026追加試験 sentence-transformers 6.1.0
- 2026追加試験runtime: PyTorch 2.8.0 + CUDA 12.8 / Transformers 5.19.0
- inference: CUDA / BF16 model weights / normalized Float32 output

Queryは、略称、日付、作品設定、関係性、ゲーム性、条件、人物性格、特技、cross-lingual等を含む。

### 5.2 実測結果

| Model | Dim | MRR | R@1 | R@5 | R@10 | JA R@10 | EN→JA R@10 | docs/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-Embedding-0.6B | 1024 | 0.624 | 0.500 | 0.769 | 0.846 | 0.875 | 0.800 | 719 |
| multilingual-e5-large-instruct | 1024 | 0.710 | 0.577 | 0.885 | **1.000** | **1.000** | **1.000** | **1,595** |
| Qwen3-Embedding-4B native | 2560 | **0.718** | **0.654** | 0.808 | 0.808 | 0.813 | 0.800 | 178 |
| Qwen3-Embedding-4B MRL | 1024 | 0.699 | 0.615 | 0.808 | 0.846 | 0.813 | 0.900 | 153 |

この26 Queryだけなら、short Statement first-stage RecallはE5が最良だった。

一方Qwen3-4BはTop-1と一般Multilingual benchmarkに強く、長文representationを扱える。

### 5.3 GPU memory実測

| Model | Model allocated | Peak allocated |
|---|---:|---:|
| Qwen3-Embedding-0.6B | 約1.11 GiB | 約3.17 GiB |
| multilingual-e5-large-instruct | 約1.04 GiB | 約1.38 GiB |
| Qwen3-Embedding-4B | 約7.54 GiB | 約9.19 GiB |

RTX 4090 24GBではQwen3-4Bを十分運用可能だった。

### 5.4 2026年追加候補の実測

2026-10-13時点で新しい有力候補を追加し、同一4,851 representation / 26 Query / Exact cosine条件で再評価した。

| Model | Dim | MRR | R@1 | R@5 | R@10 | JA R@10 | EN→JA R@10 | docs/s | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Harrier OSS v1 0.6B | 1024 | 0.798 | 0.692 | 0.923 | **0.962** | 0.938 | **1.000** | **794** | 1.51 GiB |
| Jina Embeddings v5 Text Small | 1024 | 0.839 | 0.769 | 0.923 | 0.923 | 0.938 | 0.900 | 331 | 3.80 GiB |
| Nemotron 3 Embed 1B | 2048 | 0.927 | **0.923** | 0.923 | 0.923 | 0.938 | 0.900 | 632 | 3.00 GiB |
| Nemotron 3 Embed 8B | 4096 | **0.949** | **0.923** | **0.962** | **1.000** | **1.000** | **1.000** | 99 | 15.30 GiB |
| EmbeddingGemma 2 (text-only) | 768 | 0.720 | 0.654 | 0.808 | 0.885 | 0.813 | **1.000** | 1,017 | 2.09 GiB |

`Gemini Embedding 2`も試験対象へ追加し、同一corpus / Query、768次元、Google推奨retrieval形式のbenchmark harnessを作成した。ただし実行環境に`GEMINI_API_KEY` / `GOOGLE_API_KEY`が設定されていないため、今回は**実測blocked**と記録する。試験対象から除外したわけではない。

追加試験によって初回結論を更新する。I-03の共通baselineは**Harrier OSS v1 0.6B / 1024次元**とする。理由は、32K contextとMIT licenseを維持しながら、Qwen3-4B/1024よりRecall@10、速度、VRAMの全てで今回のSGOKB workload上優位だったためである。

Nemotron 3 Embed 8Bは今回最高精度だったため**quality ceiling / reference profile**として保持する。ただし4096次元、約15.3 GiB peak VRAM、約99 documents/sで、I-03 backend比較の標準vectorとしては重すぎる。Nemotron 1Bは高Top-1の中間profile、EmbeddingGemma 2は高速・compact / future multimodal profile、Jina v5は非商用licenseのためbenchmark/reference profileとする。

---

## 6. Representation kind別の長さ確認

E5 tokenizerで旧実データをI-01相当形式へ変換し、長さ分布を確認した。

| kind | N | p50 | p95 | max | >512 tokens |
|---|---:|---:|---:|---:|---:|
| statement | 5,246 | 55 | 85 | 234 | 0% |
| facet proxy | 1,704 | 60 | 271 | 5,877 | 2.35% |
| evidence | 5,068 | 63 | 596 | 894 | 17.66% |
| object_overall proxy | 2 | 18,746 | - | 165,496 | 100% |

この`object_overall`は旧Fragmentを大量集約した極端なproxyであり、新canonical Object Versionの通常規模を表すものではない。しかし、**512 token modelを全kind共通標準にできない**ことは確認できる。

また、Qwen3の32Kを超えるrepresentationも理論上存在しうるため、Providerはsilent truncationしてはならない。

I-02では標準`overflow_policy = reject`とする。

```text
representation > configured max tokens
  ↓
embedding build failure
  ↓
object_derived_states = failed
  ↓
canonical accepted Versionは維持
```

必要ならSearch Representation自体を後続設計で再分割・再構築する。末尾を黙って切って「ready」にしてはならない。

---

## 7. Representation kindごとの判定

### Statement

暫定実測では`multilingual-e5-large-instruct`が最良。

すべてのlegacy Statement proxyが512 token以内だったため、Statement-only workloadならE5は非常に有力である。

### Facet

大部分はE5でも収まるが、長いFacetが存在する。

共通baselineではHarrier OSS v1 0.6Bを使用する。

### Evidence

legacy effective Evidenceの約17.7%がE5 512 tokenを超えた。

Evidence Searchを全文意味検索するため、Harrier OSS v1 0.6Bを共通baselineとする。

### Object overall

長文になりやすく、E5は不適切。

Harrier OSS v1 0.6Bを使用する。ただし32Kを超える場合はrejectし、representation設計を修正する。

### 同一modelを使うか

**数値上、各kindで常に同一modelが最適とは判断しない。**

しかしI-03/I-04のbaselineでは、次の理由からHarrier OSS v1 0.6B / 1024-dimを4kind共通で使用する。

- Embedding Spaceを統一できる。
- 32K contextでFacet/Evidence/Objectを扱いやすい。
- native 1024次元でVectorサイズを抑えられる。
- cross-lingual能力が高い。
- MIT license。
- RTX 4090で高速・低VRAM運用できる。
- 2026追加試験でQwen3-4B/1024をRecall・速度・VRAMで上回った。

Statement専用E5 profileの正式採否はI-07 goldで再評価する。

---

## 8. 1024次元を採用する理由

更新後baselineのHarrier OSS v1 0.6Bはnative 1024次元であり、MRL truncationなしでそのまま使用する。

Float32 vector本体の概算:

```text
1024 dim = 4,096 bytes / vector
2048 dim = 8,192 bytes / vector
4096 dim = 16,384 bytes / vector

1,000,000 vectors:
1024 dim ≈ 3.81 GiB
2048 dim ≈ 7.63 GiB
4096 dim ≈ 15.26 GiB
```

Nemotron 8Bは品質上限として優秀だが4096次元で、Harrier baselineの約4倍のvector本体容量を必要とする。I-03はbackend差を比較するため、品質・速度・容量の均衡が良い1024次元Harrier spaceを固定baselineとする。

初回Qwen3-Embedding-4Bでは2560→1024 MRLも評価しており、Recall@10 0.808→0.846だった。この結果は履歴比較として保持するが、I-03の現行baselineではない。

---

## 9. Embedding Space identity

I-02ではEmbedding Spaceを単なる`model + dimension`ではなく、次の組で識別する。

```text
provider_key
provider_version
model
model_revision
dimension
native_dimension
preprocessing_key
preprocessing_version
query_instruction
document_instruction
normalize_embeddings
max_sequence_length
overflow_policy
output_dtype
provider_configuration
```

これらをcanonical JSON化しSHA-256した値を`space_id / configuration_hash`とする。

つまり、同じmodelでも、

- revisionが違う
- dimensionが違う
- instructionが違う
- normalizationが違う
- preprocessingが違う

場合は別Embedding Spaceである。

Vectorを異なるEmbedding Space間で比較してはならない。

---

## 10. SQLite persistence

Migration 015でPhase I用の次を追加する。

```text
search_embedding_spaces
search_representation_embeddings
```

旧prototypeの`embedding_spaces / embeddings`はPhase L互換のため破壊しない。

### search_embedding_spaces

Embedding Space metadataの正本ではなく、再構築可能なderived configuration recordである。

### search_representation_embeddings

```text
Embedding Space
+ Search Representation
+ representation content_hash
+ Float32 vector BLOB
```

を保存する。

Vector cacheはSearch Representation content hashと一致する場合だけ有効である。

I-02ではこのSQLite Float32 cache + Python Exact cosineを**品質比較の基準**とする。

I-03でANN backendを選ぶ際も、このExact結果をreferenceにする。

---

## 11. Failure boundary

Embedding生成失敗はcanonical Version lifecycleから独立させる。

```text
accepted Object Version = canonical
Search Representation   = derived
Embedding               = derived
Vector Index             = derived
```

したがって、

- model fileがない
- CUDAが使えない
- inputがmax token超過
- Providerが例外
- Vector cache書込失敗

でもaccepted Versionをrollbackしない。

`object_derived_states`の`embedding`を`failed`として再試行可能にする。

external providerへのsilent fallbackは禁止する。

---

## 12. I-03へ固定して渡す条件

I-03 Vector backend benchmarkでは、原則として次を変更しない。

```text
Provider: sentence-transformers
Provider/runtime benchmark: sentence-transformers 6.1.0 / PyTorch 2.8.0
Model: microsoft/harrier-oss-v1-0.6b
Revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Output dimension: 1024
Normalization: L2
Query instruction: I-02 fixed instruction
Query format: Instruct: <instruction>\nQuery: <query>
Document prefix: none
Max sequence length: 32768
Overflow policy: reject
Exact reference: SQLite Float32 representation cache
```

Backend比較中にEmbedding modelやdimensionを変更すると、ANN差とmodel差を分離できなくなるため禁止する。

---

## 13. I-07へ残す事項

I-02の26 Queryは正式goldではない。

I-07では、

- Object / Facet / Statement / Evidence別gold
- Character / Work / Concept以外のClass
- Japanese / English / cross-lingual
- temporal / exception / fine-grained semantic query
- actual accepted canonical Knowledge

を増やし、Harrier共通space、Nemotron 8B quality ceiling、E5 Statement profileを再比較する。

I-07で明確な改善が確認された場合だけ、representation kindごとの複数Embedding Space採用を検討する。
