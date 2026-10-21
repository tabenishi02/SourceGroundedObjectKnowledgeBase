# Source Grounded Object Knowledge Base — Phase N Preparation

更新日: 2026-10-22

- Status: **Active — N-01〜N-04 Complete / N-05 Active (formal measurement BLOCKED) / N-06 Ready**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Previous phase: `Phase M — CLI / 操作フロー` — Complete
- N-04 decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- N-04 harness freeze: `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
- N-04 asset disposition: `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
- N-04 current spec: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- N-04 reconstruction tasks: `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
- N-05 plan: `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`
- N-05 evaluation: `docs/evaluation/N05_PERFORMANCE.md`

## 1. Phase Nの目的

Phase Nでは、Phase A〜Mで成立したSGOKBが、新しい目的に対して十分に正しく・実用的に動作するかを評価する。

Phase Nは「実装した機能が存在する」ことだけを確認するPhaseではない。実データ、実public boundary、性能、検索品質、障害・復旧を含めて、SGOKBがKnowledge Baseとして実利用可能かを検収する。

主な評価対象:

- domain単位のUnit Test網羅性
- canonical workflow間のIntegration
- 実データVertical Slice
- 外部Consumer向けKnowledge Accessの成立
- 1 Object処理性能
- Lexical / Semantic / Hybrid / Similarity / Evidence Search品質
- Vector backend特性
- Failure / Recovery / offline / backup / restore安全性

重要原則:

> SGOKB本体の責務と、SGOKBを利用する外部AI / Application Consumerの責務を混同しない。

## 2. Phase Mからの引継ぎ

確定済み:

- public CLIは`sgokb`のみ。
- Source / Evidence / Object / Version / Search / MCPのcanonical boundaryが成立している。
- Resultはvalidate / review / explicit importを経由する。
- Package external exportは明示操作である。
- MCPはread-only。
- M-03 isolated workflowとMCP SDK v2 readがPASSした。
- optional Semantic/Similarity runtime不足は明示的に表現する。

Phase Nでは、これらをUnit / Integrationだけでなく実データと実運用条件で評価する。

## 3. Current Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-01 | P0 | **Complete (2026-10-16)** | Unit Testをcanonical domainへ整理・補完 |
| N-02 | P0 | **Complete (2026-10-16)** | cross-domain Integrationを確認 |
| N-03 | P0 | **Complete (2026-10-16)** | Character / Work / Conceptの実データVertical Slice |
| N-04 | P0 | **Complete / PASS (2026-10-22)** | SGOKB Knowledge Access Boundaryを代表3用途で受入 |
| N-05 | P0 | **Active / BLOCKED (Reference Workstation execution access)** | 1 Object自動処理時間を計測 |
| N-06 | P0 | **Ready** | Retrieval / Vector Backend品質評価 |
| N-07 | P1 | Pending | Failure / Recovery試験 |

N-04の旧`Failed`はhistorical resultとして保持する。現行statusは責務境界修正後のReference Workstation再受入PASSによるCompleteである。

N-05の`BLOCKED`は性能FAILではない。formal timingを実行するReference Workstation command accessを現在利用できず、required raw evidenceが存在しないためである。

## 4. 推奨実施順序

```text
N-01 Unit Test                         Complete
  ↓
N-02 Integration Test                 Complete
  ↓
N-03 Real-data Vertical Slice         Complete
  ├─→ N-04 Knowledge Access Acceptance   Complete / PASS
  ├─→ N-05 Performance                  Active / formal run BLOCKED
  └─→ N-06 Retrieval / Vector quality   Ready
         ↓
       N-07 Failure / Recovery
         ↓
       Phase N Closure Audit
```

N-04 / N-05 / N-06はN-03完了後の兄弟Taskであり、相互に不要なblock関係を作らない。N-05がexecution accessでBLOCKEDでもN-06は進行可能である。

## 5. N-01 — Unit Test

Status: **Complete**

主な対象:

```text
Object Registry / Classification
Facet / Attribute / Relation
Source / Snapshot / Evidence / Provenance
Object Result Schema / Validation
Version lifecycle / stale / rollback / immutability
Evidence Package / Export / Result Receipt
Retrieval
Embedding / Vector lifecycle
MCP read adapter / server
CLI domain boundaries
```

Reference Workstationで対象test / full suite / Ruffを確認済み。

成果物:

`docs/planning/N01_UNIT_TEST_COVERAGE.md`

## 6. N-02 — Integration Test

Status: **Complete**

主要chain:

```text
Capture → Evidence → Package
Result → Validate → Import → Version
Import → Object / Facet / Statement Embed → Index update → Search
same representation hash → Vector reuse
Version change → current/historical isolation
MCP → KnowledgeReadApplication / Retrieval Core
```

外部AI生成品質はIntegration Testへ混ぜない。

成果物:

`docs/planning/N02_INTEGRATION_TESTS.md`

## 7. N-03 — Real-data Vertical Slice

Status: **Complete**

固定dataset:

- Character: 2 Object以上
- Work: 2 Object以上
- Concept: 2 Object以上
- 複数Source Objectを含む
- 8 real Web Capture
- 6 Object / Package / valid Result / accepted current Version

Provenance / grounding / identity lexical smoke / integrity / regressionを確認済み。

成果物:

- `docs/evaluation/N03_REAL_DATA_VERTICAL_SLICE.md`
- `benchmark/n03-real-data-vertical-slice-v1.json`

このdatasetをN-04〜N-06で共通利用する。N-05ではecological referenceとして利用するが、Standard/Large load envelope自体はisolated deterministic performance fixtureで再現する。

## 8. N-04 prerequisite — Derived Search lifecycle

Status: **N-04P-01〜P-06 Complete**

| Task | Status | 内容 |
|---|---|---|
| N-04P-01 | Complete | lifecycle contract |
| N-04P-02 | Complete | Search Representation Application sync |
| N-04P-03 | Complete | Incremental Embedding sync |
| N-04P-04 | Complete | Vector Index sync / rebuild |
| N-04P-05 | Complete | Public CLI / Status |
| N-04P-06 | Complete | Real model / real Qdrant acceptance |

これらはN-04の責務境界変更後も有効である。Derived Search / public read path自体はSGOKB responsibilityだからである。

## 9. N-04 — Knowledge Access Boundary Acceptance

Status: **Complete / PASS (2026-10-22)**

代表3用途で、SGOKBが外部Consumerへ正しいKnowledgeを提供できることを確認した。

```text
SGOKB canonical Knowledge
  ↓
Retrieval / Similarity
  ↓
Context Builder
  ↓
MCP / public read boundary
  ↓
External Consumer boundary  ← formal N-04 ends here
```

代表ケース:

1. Character → Roleplay Consumer
2. Similar Work → Comparison Consumer
3. Concept A/B → Creative Consumer

formal Gate:

- public boundary
- correct Object / current accepted Version
- purpose-specific Context construction
- Similarity → Context integration
- traceability
- budget / omission / truncation contract
- canonical invariance
- integrity / regression

formal Gateから除外:

- AI Consumerのhallucination / unsupported claim
- Roleplay / comparison / creative quality
- Consumerのsource fact / interpretation / creative表示品質
- Knowledge coverage sufficiency
- Grounded Generation pipeline
- Atomicity / Content-Type classifiers
- verifier / certification
- Frozen 47

Current formal assets:

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
```

Reference Workstation formal result:

```text
run_id: 20261022T052331+0900
3 / 3 cases PASS
canonical invariance PASS
system integrity PASS
post-run focused 32 passed
post-run full 505 passed / 0 failed
Ruff / diff check PASS
```

正式結果:

`docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`

## 10. Historical N-04 generation-quality chain / R-05 disposition

旧N-04ではlocal LLM出力品質をSGOKB Completion Gateへ含めていた。

歴史的結果:

```text
original N-04        Failed under old specification
G-12 formal v2       0 / 3 PASS
G-22 formal v3       0 / 3 PASS
G-25A                 VALID_FAIL_NO_SELECTION
```

同時に、canonical / MCP / Retrieval / Context Builderにはfailure原因となるproduction defectを確認しなかった。

R-05でGrounded Generation資産のfuture ownerを確定した。

```text
Grounded Generation core assets      KEEP_CORE 0件
implementation / verifier / pipeline MOVE_CONSUMER_SIDE
research evidence / Frozen 47        KEEP_EXPERIMENTAL
old harness / execution tooling      RETIRE
```

物理削除はhistorical reproducibilityのため行わない。ただしGrounded Generation資産はSGOKB public CLI / MCP / canonical workflowへ再接続してはならない。

Decision:

`docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`

Manifest:

`benchmark/n04r05-grounded-generation-asset-disposition-v1.json`

## 11. N-05 — Performance

Status: **Active / formal measurement BLOCKED (2026-10-22)**

B-06 / NFR-PERFで定義したlocal automatic segmentを計測する。

Formal target:

```text
Standard Object warm p95 <= 600 s
Large profile warm p95   <= 1200 s
```

含む:

- Package build / Evidence retrieval-selection
- Package stage / preflight
- Result Validation
- Diff review
- Result Import
- Search Representation / Embedding / Vector Index増分更新
- Render

除外:

- Source探索 / Capture network
- human Package review
- external export / Drive sync
- ChatGPT / external AI操作・生成待ち
- Result返却transport
- human approval wait
- full Vector Index rebuild

Coldは各profile最低3回を診断用、Warmは各profile最低20回をformal Gate用とする。Warm p95はnearest-rankで算出し、formal warm sampleのterminal failureを成功run追加で隠してはならない。

Current assets:

```text
benchmark/n05-performance-contract-v1.json
benchmark/n05-performance-evidence-template-v1.json
benchmark/tools/n05_evaluate_performance.py
tests/test_n05_performance_evaluator.py
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/execution/N05_REFERENCE_WORKSTATION_HANDOFF.md
docs/evaluation/N05_PERFORMANCE.md
```

Reference Workstationへの接続は確認したが、Remote Desktop Commanderのcurrent monthly execution limitによりcommand実行が拒否された。このためformal raw timing evidenceは0件であり、Standard/Large p95は未測定。

```text
N-05 formal verdict = BLOCKED (execution access)
N-05 task status    = Active / not Complete
```

これはperformance requirement failureではない。実測値を推定してPASS/FAILを付けない。

## 12. N-06 — Retrieval / Vector quality

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

N-04 Case 2はSimilarity pathが利用できることだけを確認し、ranking品質はN-06で正式評価する。

## 13. N-07 — Failure / Recovery

Status: **Pending**

主な対象:

- invalid JSON / schema mismatch / unknown Evidence
- stale / partial Result
- Embedding / Vector Index failure
- backend exchange
- process kill / partial Import
- disk full / partial file
- Raw / provenance corruption
- Internet / external provider停止
- MCP停止
- local provider failure
- backup / restore / integrity / RPO / RTO

canonical SQLite Knowledgeを壊さないこと、silent promotion / fallback / exportを起こさないことを最重要Gateとする。

## 14. Phase N evidence / completion policy

推奨保存先:

```text
docs/evaluation/   human-readable evaluation
benchmark/         frozen machine-readable inputs
.local/nXX/        machine-local runtime evidence
tests/             deterministic regression
```

Phase N closureでは、各Taskが**自分の責務範囲だけを評価していること**を確認する。

特に、外部AIの品質問題をSGOKB defectとして扱わない一方、SGOKB public boundaryの欠陥をConsumer側へ押し付けてもならない。

## 15. Current next work

N-05はformal execution access待ちでActive / BLOCKED。N-06は独立してReadyであり、N-05 blockerを理由に停止させない。

```text
N-05: Reference Workstation formal measurement pending
N-06: Ready and may proceed independently
```

N-05再開時の正本:

`docs/planning/phases/N/N05/execution/N05_REFERENCE_WORKSTATION_HANDOFF.md`
