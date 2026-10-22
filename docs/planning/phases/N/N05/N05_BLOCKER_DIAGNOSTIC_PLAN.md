# N-05 — Formal Benchmark Blocker Diagnostic Plan

更新日: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Current formal verdict: **BLOCKED**
- N-05 completion: **Not Complete**
- Historical formal run: `20261022T130413+0900`
- Historical formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
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

### Blocker B — long-input Harrier resource pressure

Large profile `cold-01`はEmbedding処理中に中断した。

観測:

```text
Object representation tokens: 18,847
embedding batch size: 1
Dedicated VRAM: 約23.2 GiB
Shared GPU memory: 約34.2 GiB
```

当時はAttention kernel / allocator / sequence-length別memory curveを取得していなかったため、別診断とした。

## 3. N05D-01 — Qdrant storage/path diagnosis

### Goal

SGOKB full benchmarkを回さず、Qdrant server側とSGOKB adapter側のどちらに原因があるかを最小再現で切り分ける。

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

### Final outcome

**Complete**。

`QDRANT_ENVIRONMENT_DEFECT`として分類し、workspace-resident storageから`C:\Qdrant\SGOKB`へcutoverした。

50件のcleanup `ACCESS DENIED`は50/50でRust Windows POSIX rename fallbackにより回復した内部eventと相関確認し、未回復rename / delete API failure / surviving source directory / terminal cleanup error / surfaced OS error 3/5はいずれも0だった。

切替後のVector rebuild、real semantic/filtered query、system integrity、canonical invariance、regressionはPASSした。

## 4. N05D-02 — Long-input Harrier memory diagnosis

### Goal

Harrierにおける単一long representationのsequence lengthとGPU/host/shared-memory使用量、wall-clockの関係をformal benchmarkから分離して計測する。

### Frozen conditions

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
device: cuda
batch size: 1
max sequence length: 32768
overflow policy: reject
```

### Prohibited shortcuts

- formal benchmarkだけをPASSさせるためのsilent truncation
- model/revisionの無断変更
- max sequence lengthの無断縮小
- CPU fallbackをformal Reference resultへ混入
- Object representationを意味的根拠なく分割して別仕様にする

### Final outcome

**Complete / VIABLE_FOR_FORMAL_RERUN**。

正式run由来のexact 18,847-token Object representationを再現し、fresh process full-input 3/3 PASS。

```text
full times: 642.830 / 636.118 / 628.092 s
Torch peak allocated: 51.061 GiB
Torch peak reserved:  56.787 GiB
Windows peak shared:  ~34.2 GiB
```

OOM / kill / detected driver reset / CPU fallback / truncation / chunkingなし。

12,278〜16,383 tokens間でWDDM/shared-memory spillが急増する。memory completionは成立するが、performance/host-memory riskは重大であり、formal Gate判定はN05D-04へ残す。

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

### Final outcome

**Complete / READY_FOR_N05D04**。

Evidence reviewで次を確定した。

- Qdrant environment remediationはD01で適用・受入済み。
- current SGOKB adapter/backendに追加production defectは確定していない。
- Harrier/model/representation contractはD02でmemory viabilityを満たす。
- benchmark runner defectを示す残Evidenceはない。
- よって追加production code変更、model変更、representation redesignは行わない。
- batch size 1、max sequence length 32768、overflow reject、formal workload、Gateを維持する。
- truncation / CPU fallback / arbitrary chunkingは導入しない。

正本:

`docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`

## 6. N05D-04 — Formal rerun

N05D-01〜03完了後、新しい`run_id`で最初からformal benchmarkを実行する。

旧run `20261022T130413+0900`のevidenceは削除・上書きしない。

新runでも:

```text
Standard cold 3 + warm 20
Large cold 3 + warm 20
```

を固定し、失敗sampleの置換を行わない。

開始前にremediated Qdrant `C:\Qdrant\SGOKB`、frozen Harrier profile、clean main、競合CUDA workload、host memory state、mandatory preflightを確認する。

Execution handoff:

`docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md`

## 7. Current next task

```text
N05D-01 = Complete
N05D-02 = Complete / VIABLE_FOR_FORMAL_RERUN
N05D-03 = Complete / READY_FOR_N05D04
N05D-04 = Next / Not Started
N-05     = BLOCKED / Not Complete
```

Next: **N05D-04 — Formal benchmark rerun under the frozen contract**.

The historical chronology below is retained only as investigation evidence; final D01/D02/D03 dispositions above supersede their then-current status/next-task wording.

## 8. Historical N05D-01 local result — 2026-10-22

- **N05D-01 = BLOCKED / not Complete** at that time.
- Run: `20261022T161445+0900`; execution HEAD `47d87ae13f621db8f6c6140209749d03d460a26c` plus local diagnostic fixes.
- Isolated short storage passed all direct/adapter indexed/plain paths and indexed repeats.
- Existing-server long-name OS error 3 was independently reproduced; short indexed path still retained intermittent OS error 5.
- Focused tests: 16 PASS; full pytest: 524 PASS; Ruff/diff PASS.

## 9. Historical ProcMon observation — 2026-10-22

Run `20261022T172340+0900` captured a cleanup rename overlapping a `Code.exe` `ShareMode: None` open. This established a concrete external-reader contention candidate for cleanup but did not prove the original index-creation failure or a unique VS Code cause.

## 10. Historical N05D-01C external-storage result — 2026-10-22

Run `20261022T191928+0900` used clean external root `C:\Qdrant\SGOKB`, native Qdrant 1.19.2, temporary 6433/6434.

Four-path smoke and 50/50 indexed cycles completed, client/server surfaced OS error 3/5 was 0, Code.exe external-storage opens 0, but ProcMon showed 50 cleanup rename `ACCESS DENIED` events. The then-current zero-denial Gate therefore left N05D-01C BLOCKED pending semantic interpretation.

## 11. N05D-01D final disposition — 2026-10-22

Correlation source `20261022T191928+0900`; cutover/regression run `20261022T221858+0900`.

All 50 denials were `RECOVERED_FALLBACK`; unrecovered/ambiguous 0, delete API failure 0, source survivors 0, terminal cleanup errors 0. The Gate was corrected to judge unrecovered failure rather than recoverable primary Windows rename attempts.

Controlled cutover to `C:\Qdrant\SGOKB` PASS; approved Vector rebuild 24 points, semantic/filtered query, integrity and canonical invariance PASS. Focused 17 / full 541 passed; Ruff/diff PASS.

## 12. N05D-02 disposition — 2026-10-23

Run `20261022T230242+0900`: **Complete / VIABLE_FOR_FORMAL_RERUN**.

The exact Large representation was 18,847 tokens. Six curve points and all three independent full trials passed. Full trial times were 628–643 seconds with ~34.2 GiB shared GPU memory. Final post-review full regression: 552 passed, 0 failed, 2 warnings; focused 11 passed; Ruff/diff PASS.

Details:

- `docs/evaluation/N05D01_QDRANT_STORAGE_PATH_DIAGNOSIS.md`
- `docs/evaluation/N05D02_HARRIER_MEMORY_DIAGNOSIS.md`
- `docs/evaluation/N05D03_EVIDENCE_BASED_REMEDIATION.md`
