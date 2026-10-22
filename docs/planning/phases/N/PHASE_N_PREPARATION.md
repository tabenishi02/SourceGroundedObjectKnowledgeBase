# Source Grounded Object Knowledge Base — Phase N Preparation

更新日: 2026-10-22

- Status: **Active — N-01〜N-04 Complete / N-05 Active (formal BLOCKED) / N-06 Ready**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Previous phase: `Phase M — CLI / 操作フロー` — Complete
- N-04 decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- N-04 asset disposition: `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
- N-04 current spec: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- N-05 plan: `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`
- N-05 blocker diagnostics: `docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`
- N-05 evaluation: `docs/evaluation/N05_PERFORMANCE.md`

## 1. Phase Nの目的

Phase Nでは、Phase A〜Mで成立したSGOKBが、新しい目的に対して十分に正しく・実用的に動作するかを評価する。

評価対象:

- domain単位のUnit Test網羅性
- canonical workflow間のIntegration
- 実データVertical Slice
- 外部Consumer向けKnowledge Access
- 1 Object処理性能
- Retrieval / Vector品質
- Failure / Recovery / backup / restore安全性

重要原則:

> SGOKB本体の責務と外部AI / Application Consumerの責務を混同しない。また、BLOCKEDをPASS/FAILへ読み替えない。

## 2. Current Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-01 | P0 | **Complete (2026-10-16)** | Unit Testをcanonical domainへ整理・補完 |
| N-02 | P0 | **Complete (2026-10-16)** | cross-domain Integrationを確認 |
| N-03 | P0 | **Complete (2026-10-16)** | Character / Work / Conceptの実データVertical Slice |
| N-04 | P0 | **Complete / PASS (2026-10-22)** | Knowledge Access Boundaryを代表3用途で受入 |
| N-05 | P0 | **Active / BLOCKED** | 1 Object local automatic processing性能を評価 |
| N-06 | P0 | **Ready** | Retrieval / Vector Backend品質評価 |
| N-07 | P1 | Pending | Failure / Recovery試験 |

## 3. Phase dependency

```text
N-01 Unit Test                         Complete
  ↓
N-02 Integration Test                 Complete
  ↓
N-03 Real-data Vertical Slice         Complete
  ├─→ N-04 Knowledge Access Acceptance   Complete / PASS
  ├─→ N-05 Performance                  Active / formal BLOCKED
  └─→ N-06 Retrieval / Vector quality   Ready
         ↓
       N-07 Failure / Recovery
         ↓
       Phase N Closure Audit
```

N-04 / N-05 / N-06は兄弟Taskであり、N-05のblockerを理由にN-06を停止しない。

## 4. N-01 — Unit Test

Status: **Complete**

成果物:

`docs/planning/N01_UNIT_TEST_COVERAGE.md`

## 5. N-02 — Integration Test

Status: **Complete**

主要chain:

```text
Capture → Evidence → Package
Result → Validate → Import → Version
Import → Representation / Embedding / Index update → Search
MCP → KnowledgeReadApplication / Retrieval Core
```

成果物:

`docs/planning/N02_INTEGRATION_TESTS.md`

## 6. N-03 — Real-data Vertical Slice

Status: **Complete**

固定dataset:

- 8 real Web Capture
- 6 Object
- Character / Work / Concept
- valid Result / accepted current Version

成果物:

- `docs/evaluation/N03_REAL_DATA_VERTICAL_SLICE.md`
- `benchmark/n03-real-data-vertical-slice-v1.json`

N-05ではecological referenceとして利用し、性能load shape自体はisolated deterministic fixtureで再現する。

## 7. N-04 — Knowledge Access Boundary Acceptance

Status: **Complete / PASS (2026-10-22)**

formal boundary:

```text
SGOKB canonical Knowledge
→ Retrieval / Similarity
→ Context Builder
→ MCP / public read boundary
→ External Consumer boundary
```

Consumer生成品質、Grounded Generation、Atomicity / Content-Type classifier、Frozen 47はformal Gateではない。

Reference Workstation result:

```text
run_id: 20261022T052331+0900
3 / 3 cases PASS
canonical invariance PASS
system integrity PASS
post-run full 505 passed / 0 failed
```

正式結果:

`docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`

## 8. Historical N-04 remediation / disposition

旧generation-quality chainはhistorical evidenceとして保持する。

```text
G-12 historical formal FAIL
G-22 historical formal FAIL
G-25A VALID_FAIL_NO_SELECTION
```

R-05 disposition:

```text
Grounded Generation KEEP_CORE: 0件
implementation / verifier / pipeline: MOVE_CONSUMER_SIDE
research evidence / Frozen 47: KEEP_EXPERIMENTAL
old harness / execution tooling: RETIRE
```

## 9. N-05 — Performance

Status: **Active / BLOCKED (2026-10-22 formal run)**

Formal target:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

formal run:

```text
run_id: 20261022T130413+0900
HEAD:   a7147f9842f94e96944bc7f67b4c3986970462b0
```

### Standard

```text
Source / Evidence candidates / Package Evidence / Statements
10 / 500 / 120 / 300

planned: cold 3 + warm 20
observed: 23 / 23 terminal sample failure
```

Derived SearchのQdrant payload index作成時にserver-side storage path errorが発生した。観測messageは`gridstore` pathが見つからない旨を示した。Renderへ到達せず全segment evidenceが揃っていない。

### Large

```text
40 / 2000 / 350 / 1200
```

`cold-01`のHarrier Embedding中に中断。

```text
Object representation: 18,847 tokens
batch size: 1
Dedicated VRAM: 約23.2 GiB
Shared GPU memory: 約34.2 GiB
```

後続sampleは未実行。

### Formal evaluator

```text
N-05 verdict = BLOCKED
performance target = Not Judgeable
```

Standard/Largeのformal warm p50 / p95 / maxは算出しない。

Post-run:

```text
Evaluator tests 8 PASS
Full pytest 517 PASS
Ruff PASS
diff check PASS
canonical DB unchanged
tracked files unchanged during run
HEAD unchanged during run
```

次にformal benchmarkを繰り返さず、blockerを分離診断する。

```text
N05D-01 Qdrant storage/path diagnosis
N05D-02 Long-input Harrier memory diagnosis
N05D-03 Evidence-based remediation
N05D-04 Formal benchmark rerun
```

診断計画:

`docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`

## 10. N-06 — Retrieval / Vector quality

Status: **Ready**

評価channel:

```text
Identity / exact lookup
Lexical
Semantic
Hybrid
Overall Similarity
Facet Similarity
Evidence Search
Relation / filter / current-historical isolation
```

主な指標:

- Recall@K
- MRR
- nDCG
- latency
- RAM / VRAM / disk
- index build / incremental update / rebuild

## 11. N-07 — Failure / Recovery

Status: **Pending**

主な対象:

- invalid Result / stale / partial input
- Embedding / Vector Index failure
- backend exchange
- process kill / disk full / partial file
- Raw / provenance corruption
- Internet / provider / MCP停止
- backup / restore / integrity / RPO / RTO

## 12. Current next work

N-05の次Task:

```text
N05D-01 — Qdrant storage/path blocker diagnosis
```

N05D-01 / N05D-02は独立して診断可能。N-05 formal rerunは両blockerのexit conditionを満たすまで開始しない。

N-06は独立して開始可能である。
