# N-05 — Formal Benchmark Blocker Diagnostic Plan

更新日: 2026-10-22

- Parent: `N-05 [P0] — Performance`
- Current formal verdict: **BLOCKED**
- N-05 completion: **Not Complete**
- Formal run: `20261022T130413+0900`
- Formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- Performance contract: `benchmark/n05-performance-contract-v1.json`
- Evaluation: `docs/evaluation/N05_PERFORMANCE.md`

## 1. Purpose

N-05 formal benchmarkは性能target判定へ到達する前に2つの独立したruntime blockerで停止した。

したがって、正式Gateやworkloadを変更せず、formal benchmarkとは分離した診断を行う。

```text
N05D-01 Qdrant storage/path blocker diagnosis
N05D-02 Long-input Harrier memory diagnosis
        ↓
N05D-03 Evidence-based remediation
        ↓
N05D-04 Formal benchmark rerun under the frozen contract
```

診断値はN-05 p95 formal sampleへ混ぜない。

## 2. Observed blockers

### Blocker A — Qdrant storage/path

Standard profileはcold 3 + warm 20、計23 sampleすべてでterminal sample failureとなった。

失敗地点:

```text
Derived Search sync
→ Qdrant collection / payload index preparation
→ server-side storage error
```

観測エラーは`gridstore`の保存先pathが見つからない旨を示した。

現時点で以下は未確定である。

- Qdrant server storage directory/configuration defect
- Windows filesystem / permission / lifecycle defect
- sample固有collection大量生成との相互作用
- SGOKB Qdrant adapter側のtrigger条件
- その他のbackend defect

pytest PASSだけを根拠に実Qdrant経路を正常と判断してはならない。

### Blocker B — long-input Harrier resource pressure

Large profile `cold-01`はEmbedding処理中に中断した。

観測:

```text
Object representation tokens: 18,847
embedding batch size: 1
Dedicated VRAM: 約23.2 GiB
Shared GPU memory: 約34.2 GiB
```

単一長文入力の中間memoryが主要候補だが、Attention kernel / allocator / sequence-length別memory curveをまだ計測していないため、root causeを断定しない。

## 3. N05D-01 — Qdrant storage/path diagnosis

### Goal

SGOKB full benchmarkを回さず、Qdrant server側とSGOKB adapter側のどちらに原因があるかを最小再現で切り分ける。

### Required checks

1. Qdrant process/version/start command/configurationを記録する。
2. storage root / snapshots / temp / gridstore関連directoryの実pathと存在・権限を確認する。
3. disk free spaceとvolume状態を確認する。
4. Qdrant単体clientから次を実行する。
   - collection create
   - payload index create
   - point upload
   - query
   - collection delete
5. SGOKB `QdrantVectorIndexAdapter`から同等の最小upsertを実行する。
6. sample-specific collection prefixで連続create/deleteした場合も確認する。
7. server logとclient exceptionをraw evidenceとして保存する。

### Exit condition

次のいずれかをevidence付きで確定する。

```text
QDRANT_ENVIRONMENT_DEFECT
SGOKB_ADAPTER_DEFECT
BENCHMARK_RUNNER_DEFECT
BACKEND_PRODUCT_DEFECT
OTHER_IDENTIFIED_CAUSE
```

修復後、最小real-Qdrant smokeが繰り返しPASSすること。

## 4. N05D-02 — Long-input Harrier memory diagnosis

### Goal

Harrierにおける単一long representationのsequence lengthとGPU/host/shared-memory使用量、wall-clockの関係をformal benchmarkから分離して計測する。

### Required checks

同一model/revision/dtype/deviceで、batch size 1を固定する。

最低限、複数sequence lengthで段階的に計測する。

例:

```text
~2k tokens
~4k tokens
~8k tokens
~12k tokens
~16k tokens
actual Large representation (~18,847 tokens)
```

各ケースで最低限記録する。

```text
token count
wall-clock
torch.cuda.memory_allocated peak
torch.cuda.memory_reserved peak
nvidia-smi dedicated VRAM
shared GPU memory / system memory observation
success / failure
```

可能なら使用Attention implementation / dtype / model configも記録する。

### Prohibited shortcuts

- formal benchmarkだけをPASSさせるためのsilent truncation
- model/revisionの無断変更
- max sequence lengthの無断縮小
- CPU fallbackをformal Reference resultへ混入
- Object representationを意味的根拠なく分割して別仕様にする

### Exit condition

少なくとも次を判定できること。

```text
18,847-token input is operationally viable on the Reference Workstation
```

または

```text
current representation/model contract is not operationally viable and requires explicit design remediation
```

## 5. N05D-03 — Evidence-based remediation

診断結果に応じて必要な最小修正を行う。

優先順位:

1. environment/configuration defectならenvironmentを修復する。
2. benchmark runner defectならrunnerだけを修復する。
3. SGOKB production defectならproduction codeを修復しregressionを追加する。
4. representation/model design issueなら、N-05だけの小細工にせずDerived Search設計として明示的に再検討する。

正式Gate:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

はこの診断を理由に変更しない。

## 6. N05D-04 — Formal rerun

両blockerが解消した後、新しい`run_id`で最初からformal benchmarkを実行する。

旧run `20261022T130413+0900`のevidenceは削除・上書きしない。

新runでも:

```text
Standard cold 3 + warm 20
Large cold 3 + warm 20
```

を固定し、失敗sampleの置換を行わない。

## 7. Current next task

最初に実施するTask:

```text
N05D-01 — Qdrant storage/path blocker diagnosis
```

N05D-01とN05D-02は独立して調査可能だが、formal rerunは両方のexit conditionを満たすまで開始しない。
