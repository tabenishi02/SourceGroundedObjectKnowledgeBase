# Source Grounded Object Knowledge Base — Phase N Preparation

## R2-10 closure update (2026-10-24)

This is the current authoritative Phase N state and supersedes older current-state / next-task notes retained below.

```text
N-01 = Complete
N-02 = Complete
N-03 = Complete
N-04 = Complete / PASS
N-05 = Complete / PASS
N-06 = Next / Ready
N-07 = Pending
Phase N = Active / Not Complete
```

R2 closure:

```text
R2-01 ... R2-10 = Complete
N05D-04R2 = Complete
N05D-04   = Complete
N-05      = Complete / PASS
```

N-05 formal acceptance is run `20261024T044506+0900`: 46/46 PASS, Standard warm p95 `12.2832216 s <= 600 s`, Large warm p95 `53.7066947 s <= 1200 s`, zero FAIL/ABORTED/retry, R2-only serving with `object_overall` leakage 0, and canonical/tracked/HEAD plus regression/static safety gates PASS.

Phase N itself is not closed by R2-10. **N-06 — Retrieval / Vector quality** is the next P0 task. R2-08 exercised R2-sensitive quality assets but does not silently complete the broader N-06 task.

Closure authority: `docs/evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md`.

---

## Historical planning/evidence record retained below

## Current acceptance update (2026-10-24)

This update supersedes historical BLOCKED/next-task notes below.
**R2-08 = Complete / PASS; R2-09 = Complete / PASS;
R2-10 = Next / Not Started.** N05D-04R2 remains Active until R2-10 closure;
N05D-04 and N-05 are Not Complete until that separate closure.

Formal run `20261024T044506+0900` measured clean main
`2711d4c389c4d1c722e864e17a7b6afb05af4c62`: exact 3/20/3/20 samples,
46 PASS, 0 FAIL/ABORTED/retry. Standard warm p50/p95/max =
11.3099469 / 12.2832216 / 12.3947986 s; Large =
49.9412004 / 53.7066947 / 54.1282194 s. Evaluator Standard/Large/overall PASS
against unchanged 600/1200 s Gates. Every sample used R2 only, overall leakage 0;
46 namespaces / 34684 live points audited. Original canonical snapshots, measured
HEAD, tracked state and all three R1 asset hashes were unchanged. Post-run evaluator
8 tests / full suite 669 tests / repository-wide Ruff / diff PASS. Accepted Large
resource diagnostic was reused without rerun; source/runtime identity unchanged.
No R2-10 closure, performance tuning or additional benchmark was started.

Formal result: `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`.
Aggregate: `benchmark/results/n05d04r2-r2-09-performance-acceptance.json`.


更新日: 2026-10-23

- Status: **Active — N-01〜N-04 Complete / N-05 Active (R2-09 PASS; R2-10 closure not started) / N-06 Ready**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Previous phase: `Phase M — CLI / 操作フロー` — Complete
- N-04 decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- N-04 asset disposition: `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
- N-04 current spec: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- N-05 plan: `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`
- N-05 blocker diagnostics: `docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`
- N-05 evaluation: `docs/evaluation/N05_PERFORMANCE.md`
- N-05 redesign: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- N-05 redesign tasks: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

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
| N-05 | P0 | **Active / R2-09 PASS; Not Complete until R2-10** | 1 Object local automatic processing性能を評価 |
| N-06 | P0 | **Ready; R2 quality acceptanceで連携** | Retrieval / Vector Backend品質評価 |
| N-07 | P1 | Pending | Failure / Recovery試験 |

## 3. Phase dependency

```text
N-01 Unit Test                         Complete
  ↓
N-02 Integration Test                 Complete
  ↓
N-03 Real-data Vertical Slice         Complete
  ├─→ N-04 Knowledge Access Acceptance   Complete / PASS
  ├─→ N-05 Performance                  Active / BLOCKED
  │       ↓
  │     N05D-04R2 hierarchical Derived Search redesign
  │       ↓
  │     Search-quality acceptance (N-06 assets/resultsと整合確認)
  │       ↓
  │     New formal N-05 rerun
  └─→ N-06 Retrieval / Vector quality   Ready
         ↓
       N-07 Failure / Recovery
         ↓
       Phase N Closure Audit
```

N-04 / N-05 / N-06は兄弟Taskであるが、N05D-04R2はRetrieval semanticsを変更するため、R2-08ではN-06 quality assets/resultsとの再整合が必要になる。

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

Status: **Active / BLOCKED — structural Derived Search remediation selected**

Formal target remains:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

### Historical formal run

```text
run_id: 20261022T130413+0900
HEAD:   a7147f9842f94e96944bc7f67b4c3986970462b0
```

Standard planned cold 3 + warm 20 but reached 23/23 terminal failure at the then-current Qdrant storage path. N05D-01 later repaired the environment by cutover to `C:\Qdrant\SGOKB`.

Large `cold-01` exposed the 18,847-token Harrier Object representation resource problem.

N05D-02 measured the exact old-contract full representation:

```text
full fresh-process 3/3 PASS
Torch peak allocated ~51.1 GiB
Windows Shared GPU memory ~34.2 GiB
full embedding ~628–643 s
```

This proved memory completion, not acceptable performance or design efficiency.

### First N05D-04 rerun

Run `20261023T025413+0900` used the remediated Qdrant runtime. It reached:

```text
Standard cold: 3/3 PASS
Standard warm: 18 PASS / 2 FAIL
```

The two failures were caused by disk exhaustion (`No space left on device` / WAL buffer cannot fit). Large had not completed when the user stopped the run. The attempt is retained as environment BLOCKED / user-aborted evidence, not a formal performance FAIL.

A >=32 GiB free-disk hard start gate was added for future formal runs.

### N05D-04R1 partial VRAM diagnostic

A user-aborted backend diagnostic established partial evidence:

```text
auto SDPA smoke -> math backend observed
forced Flash -> unavailable in current tested Windows build
forced Efficient -> tested GQA shape rejected
full auto trial -> user-aborted
```

R1 is not the selected root remediation.

### Adopted root remediation — N05D-04R2

Current `object_overall` repeats detailed Facet Statements even though the same Knowledge is separately materialized as Facet and Statement representations.

The selected redesign is:

```text
compact object_overview
+ Facet representations
+ Statement representations
+ bounded Object aggregation
+ hierarchical Object Similarity
```

This is semantic hierarchical partitioning, not arbitrary token chunking.

For the first redesign acceptance, Harrier OSS v1 0.6B remains fixed so representation impact can be measured independently. Harrier 270M is a later contingency only.

Design:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`

Tasks:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

### Current N-05 state

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = partial user-aborted evidence
N05D-04R2 = Active
R2-01 = Next / Not Started
N-05 verdict = BLOCKED / Not Complete
performance target = Not Judgeable
```

Do not start another 46-sample formal run before R2-08 Search-quality acceptance and R2-09 authorization.

## 10. N-06 — Retrieval / Vector quality

Status: **Ready; redesign interaction required**

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

N05D-04R2 changes active Object-level semantic representation and overall Object Similarity, so R2-08 must re-run/extend the relevant N-06/search-quality assets before formal N-05 timing is authorized.

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

N-05 current next task:

```text
N05D-04R2 / R2-01 — Impact survey / redesign freeze
```

R2-01 inventories all active `object_overall` dependencies and freezes compatibility/migration boundaries before canonical design documents or code are changed.

Formal N-05 rerun is prohibited until R2-08 quality acceptance and R2-09 authorization.


## R2-09 execution update (2026-10-24)

This execution result supersedes earlier R2-09 next-task notes:
**R2-09 = BLOCKED / Not Complete; N-05 = BLOCKED / Not Complete;
N05D-04R2 = Active; R2-10 = Not Started.** R2-08 quality acceptance is unchanged.

Mandatory preflight PASS (654 pytest passed; repository-wide Ruff/diff PASS;
124.740 GiB free; external Qdrant healthy; no material competing CUDA workload).
Before GPU timing, source inspection established that the frozen performance
workflow uses default v1 `materialize_version` for fresh samples, producing
`object_overall` instead of the required R2 family. No Large diagnostic or formal
sample was started. Runner/model/scoring/gates were not changed. R1 assets remain
byte-identical. A separately reviewed R2 benchmark-wiring change is required
before a new acceptance attempt; no closure or optimization is started here.

Execution record: `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`.
