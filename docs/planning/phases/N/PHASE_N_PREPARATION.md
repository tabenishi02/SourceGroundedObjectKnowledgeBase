# Source Grounded Object Knowledge Base — Phase N Preparation

更新日: 2026-10-22

- Status: **Active — N-01〜N-04 Complete / Next N-04R-05**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Previous phase: `Phase M — CLI / 操作フロー` — Complete
- N-04 decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- N-04 harness freeze: `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
- N-04 current spec: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- N-04 reconstruction tasks: `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`

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
| N-04 | P0 | **Complete (2026-10-22)** | SGOKB Knowledge Access Boundaryを代表3用途で受入 |
| N-05 | P0 | **Ready** | 1 Object自動処理時間を計測 |
| N-06 | P0 | **Ready** | Retrieval / Vector Backend品質評価 |
| N-07 | P1 | Pending | Failure / Recovery試験 |

N-04の旧`Failed`はhistorical resultとして保持する。現行statusは責務境界修正後のReference Workstation再受入PASSによるCompleteである。

## 4. 推奨実施順序

```text
N-01 Unit Test                         Complete
  ↓
N-02 Integration Test                 Complete
  ↓
N-03 Real-data Vertical Slice         Complete
  ├─→ N-04 Knowledge Access Acceptance   Complete / PASS
  ├─→ N-05 Performance                  Ready
  └─→ N-06 Retrieval / Vector quality   Ready
         ↓
       N-07 Failure / Recovery
         ↓
       Phase N Closure Audit
```

N-04 / N-05 / N-06はN-03完了後の兄弟Taskであり、相互に不要なblock関係を作らない。

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

このdatasetをN-04〜N-06で共通利用する。

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

### 9.1 目的

代表3用途で、SGOKBが外部Consumerへ正しいKnowledgeを提供できることを確認する。

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

### 9.2 formal Gate

評価対象:

- public boundary
- correct Object / current accepted Version
- purpose-specific Context construction
- Similarity → Context integration
- traceability
- budget / omission / truncation contract
- canonical invariance
- integrity / regression

### 9.3 formal Gateから除外

- AI Consumerのhallucination / unsupported claim
- Roleplay / comparison / creative quality
- Consumerのsource fact / interpretation / creative表示品質
- Knowledge coverage sufficiency
- Grounded Generation pipeline
- Atomicity / Content-Type classifiers
- verifier / certification
- Frozen 47

Knowledge coverageは観測記録には残せるが、canonicalに存在しないKnowledgeをSGOKBが補う責務はない。

### 9.4 N-04R-03 Harness Reconstruction

Status: **Complete (2026-10-22)**

Current formal assets:

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
tests/test_n04r03_knowledge_access_harness.py
tests/test_n04r04_evidence_evaluator.py
```

Freeze record:

`docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`

Harnessは旧Generator / Judge / classifier / verifierに依存しない。Case 2は実Similarity responseのtop candidate IDをContextへそのまま渡す。deterministic evaluatorはraw MCP boundary evidenceとcanonical/integrity/regression evidenceだけで`PASS / FAIL / BLOCKED`を判定する。

Reference Workstation実行はR-04へ分離しているため、R-03完了は実機N-04 PASSを意味しない。

詳細正本:

- `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`

## 10. Historical N-04 generation-quality chain

2026-10-18以降、旧N-04ではlocal LLM出力品質をSGOKB Completion Gateへ含めていた。

歴史的結果:

```text
original N-04        Failed under old specification
G-12 formal v2       0 / 3 PASS
G-22 formal v3       0 / 3 PASS
G-25A                 VALID_FAIL_NO_SELECTION
```

同時に、canonical / MCP / Retrieval / Context Builderにはfailure原因となるproduction defectを確認しなかった。

G-01〜G-25でGrounded Generation / verifier / classifier設計・実装を追加したが、2026-10-22のResponsibility Boundary Reconstructionにより、これらをN-04 Completion prerequisiteから外した。

過去evidenceは削除しない。

## 11. N-05 — Performance

Status: **Ready**

B-06で定義したlocal automatic segmentを主要計測対象とする。

含む:

- Package generation
- Validation
- Import
- Object / Facet / Statement Embedding更新
- Vector Index増分更新

分離記録:

- Source探索 / Capture network
- human Package review
- external export / Drive sync
- ChatGPT操作・生成待ち
- Result返却
- review-required判断

Reference Workstation target:

```text
Standard Object: p95 <= 10 min
Large profile:   p95 <= 20 min
```

N-04のConsumer generation resultはN-05開始条件ではない。

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

N-04 reconstruction chain:

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Complete
N-04R-03 Formal Harness Reconstruction           Complete
N-04R-04 Reference Workstation Re-Acceptance     Complete / PASS
N-04R-05 Grounded Generation Asset Disposition   Next
```

次Taskは`N-04R-05 — Grounded Generation Asset Disposition`。

完了したR-04の実行handoff:

`docs/planning/phases/N/N04/execution/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE_HANDOFF.md`

N-05 / N-06はN-04完了を待つ必要はない。

## 2026-10-22 Reference Workstation formal result

Run `20261022T052331+0900`: **PASS (3/3 cases)**. **N-04R-04 = Complete; N-04 = Complete.** Actual MCP stdio/read-only tools, current accepted Versions, purpose/budget/Evidence policies, Similarity rank-1 integration, canonical invariance and system integrity all PASS. Mandatory preflight: focused 20/full 505 passed; post-run focused 32/full 505 passed; Ruff and diff check PASS (2 existing local-Qdrant warnings in each full suite).

正式結果・evidence summary・preflight実装修復記録: `docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`. Case/evaluator frozen blobs, Gates and existing assertions were preserved. No Consumer generation/classifier/verifier/Frozen 47 was executed. Next: **N-04R-05 — Grounded Generation Asset Disposition** (not started); N-05/N-06 remain Ready.
