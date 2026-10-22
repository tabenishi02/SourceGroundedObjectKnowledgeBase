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


## 8. N05D-01 local result — 2026-10-22

- **N05D-01 = BLOCKED / not Complete**; it remains the current task.
- Latest run: `20261022T161445+0900`; execution HEAD:
  `47d87ae13f621db8f6c6140209749d03d460a26c` plus local diagnostic fixes.
- Isolated short storage passed all four direct/adapter indexed/plain paths and
  5/5 indexed repeats. Existing-server long-name OS error 3 is independently
  reproduced by direct client. Short indexed adapter controls passed 2/3;
  the retained failure is OS error 5 (access denied). Direct indexed also
  exhibited OS error 5. Root cause is not fully classified or repaired.
- Path-shortening and explicit-empty-schema fixes are validated by tests but
  are not sufficient evidence to declare runtime recovery.
- Focused tests: 16 PASS; full pytest: 524 PASS, 0 failed; Ruff/diff PASS.
- Result/evidence details:
  `docs/evaluation/N05D01_QDRANT_STORAGE_PATH_DIAGNOSIS.md`.
- Additional file-operation tracing is needed; no security disable/exclusion or
  existing-server restart is authorized by this result. Previous evidence and
  failed collections are retained.
- N-05 remains BLOCKED / not Complete. N05D-02 and the formal rerun were not started.


## 9. ProcMon observation progress — 2026-10-22

- Run `20261022T172340+0900`: official signed ProcMon 4.12, user-authorized ProcMon-only
  elevation, local PML/CSV retained. Existing storage remained
  `.local/n04p06/qdrant/storage`; server/security settings were not changed.
- Short indexed diagnosis probes: 10/10 PASS;
  client OS error 5: 0. Storage trace contains
  9 ACCESS DENIED/SHARING VIOLATION events, requiring evidence review.
- One cleanup rename overlaps a Code.exe ShareMode: None open on a descendant
  index file (open 0.2844 ms before denial; close 0.2522 ms after). This is a
  concrete external-reader contention candidate for cleanup, not proof of the
  original index-creation error. Raw PML stacks/handle identity need review.
- Root-cause attribution and safe full remediation remain unproven.
  **N05D-01 = BLOCKED / Not Complete**; it stays the current task.
- Focused tests 10 PASS; full pytest 529 PASS; Ruff/diff PASS.
- Diagnostic tools and documented observations may be committed/pushed as
  progress under the user's updated policy; this does not grant acceptance.
- Next: correlate a reproduced access-denied operation with exact file/handle
  and PML stack evidence. N05D-02/formal rerun were not executed.


## 10. N05D-01C external-storage remediation result — 2026-10-22

- Run `20261022T191928+0900`, HEAD `a2e2a48fdc04ec730fc14b655dc00e0a4fd1a4a1`.
- Clean external root `C:\Qdrant\SGOKB`, native Qdrant 1.19.2, non-admin,
  temporary HTTP/gRPC 6433/6434. Old storage/state was not copied or removed.
- Four-path minimal smoke PASS. 50/50 indexed cycles completed (25 direct,
  25 adapter); terminal API failures 0; exception-string OS error 3/5 counts 0.
- Full stress ProcMon coverage confirmed: Code.exe external-storage accesses
  and opens 0, SHARING VIOLATION 0, **Qdrant ACCESS DENIED 50** during cleanup
  rename. Native denials remain failures even when API responses report success.
- **N05D-01C BLOCKED; N05D-01 BLOCKED / Not Complete.** Root cause unresolved;
  isolation effectiveness is observed but the remediation acceptance gate failed.
- 6333/6334 were not cut over; old PID/config/storage/31 collections preserved.
  Post-switch smoke and vector rebuild were NOT RUN. Existing evaluation DB
  system integrity PASS. Security settings and production canonical DB unchanged.
- Full result: `docs/evaluation/N05D01_QDRANT_STORAGE_PATH_DIAGNOSIS.md` and
  `docs/planning/phases/N/N05/N05D01C_QDRANT_STORAGE_ISOLATION_REMEDIATION.md`.
- Focused: 10 PASS / 0 failed; full pytest: 529 PASS / 0 failed;
  Ruff: PASS; diff: PASS.
- Next candidate: separately authorized WSL2/Linux-filesystem Qdrant remediation.
  N05D-02 and formal N-05 rerun remain unstarted; do not disable security to pass.
