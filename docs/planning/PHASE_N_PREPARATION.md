# Source Grounded Object Knowledge Base — Phase N Preparation

更新日: 2026-10-16

- Status: **Active — N-01 Complete / N-02 Next**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Previous phase: `Phase M — CLI / 操作フロー` — Complete
- Previous closure: `docs/planning/PHASE_M_CLOSURE_AUDIT.md`
- Baseline: `7b4507ab5a80ebdb687c65d5e4627beb83806f3c`
- Current task: `N-02 [P0] Integration Testを追加する`（Next / 未着手）

---

## 1. Phase Nの目的

Phase Nでは、Phase A〜Mで成立したSGOKBが、新しい目的に対して十分に正しく・実用的に動作するかを評価する。

Phase Mで確認したのは、主として次である。

> 1 Objectのoperator workflowが、内部DB操作なしでpublic `sgokb` CLIとread-only MCPを通して完走できること。

Phase Nでは範囲を広げ、次を評価する。

- domain単位のUnit Test網羅性
- canonical workflow間のIntegration
- 実データVertical Slice
- AI利用ケースの成立
- 1 Object処理性能
- Lexical / Semantic / Hybrid / Similarity / Evidence Search品質
- Vector backend特性
- Failure / Recovery / offline / backup / restore安全性

「Schema適合」や「1本のhappy path成功」だけを品質合格とはみなさない。

---

## 2. Phase Mからの引継ぎ

確定済み:

- public CLIは`sgokb`のみ。
- fresh canonical DBはmigration003〜017から構築する。
- Source / Evidence / Object / Version / Search / MCPのcanonical boundaryが成立している。
- Resultはvalidate / review / explicit importを経由する。
- Package external exportは明示操作である。
- MCPはread-only。
- M-03 isolated workflowとMCP SDK v2 readがPASSした。
- optional Semantic/Similarity runtime不足はexit 5で表現する。

Phase Nへ引き継ぐ既知制約:

1. Package Transferの既知test failureはN-01で同一サイズtamper fixtureにより解消し、Reference WorkstationでPASSした。production validation orderは変更していない。
2. Reference WorkstationではM-03時点でlocal embedding / vector optional runtimeが未構成。
3. M-03ではChatGPT分析品質を評価していない。
4. M-03のResultはdeterministic fixtureであり、実データVertical Sliceではない。
5. repositoryにはPhaseごとのhistorical test名が残っており、N-01では「名前」よりcanonical domain coverageを基準に整理する必要がある。

---

## 3. Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-01 | P0 | **Complete (2026-10-16)** | Unit TestをObject / Relation / Facet / Version / Validation / Retrievalへ整理・補完 |
| N-02 | P0 | **Next / 未着手** | cross-domain Integrationを追加 |
| N-03 | P0 | Pending | Character / Work / Conceptの実データVertical Slice |
| N-04 | P0 | Pending | 代表AI利用ケース3件の受入 |
| N-05 | P0 | Pending | 1 Object自動処理時間の計測 |
| N-06 | P0 | Pending | Retrieval / Vector Backend品質評価 |
| N-07 | P1 | Pending | Failure / Recovery試験 |

Task masterは`docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`を正本とする。

---

## 4. 推奨実施順序

基本順序:

```text
N-01 Unit Test audit / update
  ↓
N-02 Integration Test
  ↓
N-03 Real-data Vertical Slice
  ├─→ N-04 AI use-case acceptance
  ├─→ N-05 Performance
  └─→ N-06 Retrieval / Vector quality
  ↓
N-07 Failure / Recovery
  ↓
Phase N Closure Audit
```

理由:

- N-01でdomain-level correctnessと既知test debtを先に明確化する。
- N-02でcross-domain wiringを固定してから実データへ進む。
- N-03の実データ集合をN-04〜N-06の共通評価資産として再利用する。
- N-07はhappy pathと評価runtimeが安定した後に、破壊・停止・recovery scenarioを系統的に実施する。

N-04〜N-06はN-03完了後、環境準備が独立していれば一部並行してよい。

---

## 5. N-01開始前のTest inventory方針

N-01では「既存testを全部書き直す」ことを目的にしない。まずcanonical domainごとのcoverage表を作る。

最低限の対象domain:

```text
Object Registry / Classification
Facet / Attribute / Relation
Source / Snapshot / Evidence / Provenance
Object Result Schema / Validation
Version lifecycle / stale / rollback / immutability
Evidence Package / Export / Result Receipt
Retrieval: lexical / semantic / hybrid / similarity / evidence
Embedding Space / Representation / Vector lifecycle
MCP read adapter / server
CLI contracts that protect domain boundaries
```

既存testが旧Phase名（例: F-xx / J-xx / M-xx）でも、現行canonical semanticsを直接検証しているなら削除・renameを必須としない。

N-01の成果物として、少なくとも次を作成することを推奨する。

- domain → existing tests → missing casesのcoverage matrix
- redundant / legacy-only / misleading testsの一覧
- 新規Unit Testまたは修正test
- known baseline failureの処遇Decision

### Package Transfer既知failure

N-01開始時に次を再確認する。

```text
tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch
```

開始時はfile size mismatchがhash mismatchより先に検出されるためmessage期待値と差があった。N-01では同一サイズのtamperに修正し、SHA-256 mismatch branchを正規に検証した。既知failureは解消済み。

Phase Nでは、

- 実装のvalidation orderをcontractとするか
- test期待値が過剰にmessage順序へ依存しているか
- security/integrity上hash検証順序を変える必要があるか

を判断する方針とした。N-01ではproduction検証順序とtest期待値を維持し、fixtureだけを修正した。xfail化はしていない。

---

## 6. N-02 Integration scope

M-03で追加した1 Object public CLI end-to-end testは有用だが、N-02全体を満たしたとはみなさない。

追加・確認すべき主要chain:

```text
Capture → Evidence → Package
Result → Validate → Import → Version
Import → Object / Facet / Statement Embed → Index update → Search
same representation hash → Vector reuse
Version change → current/historical scope isolation
MCP → KnowledgeReadApplication / Retrieval Core
```

Integration Testは可能な限りdeterministic / offlineとし、外部AI品質試験はN-04へ分離する。

---

## 7. N-03 Real-data Vertical Slice

最低構成:

- Character: 2 Object以上
- Work: 2 Object以上
- Concept: 2 Object以上
- うち1 Object以上は複数Sourceを持つ

Synthetic fixtureではなく、実際のWeb Capture / Evidenceを使う。

Vertical SliceはN-04〜N-06で再利用できるよう、次を固定して記録する。

- Object stable ID
- Class / aliases
- Source / Snapshot / Evidence
- Package / Result / accepted Version
- ground truthまたは人間評価メモ
- Search query / expected relation / similarity rationale

production canonical DBへ直接投入するか、評価専用DBへ保持するかはN-03開始時に明示Decisionする。評価のために本番dataを無断変更しない。

---

## 8. N-04 AI use-case acceptance

Task masterの3ケースを別々に評価する。

1. Character Data → local LLM Roleplay
2. similar Work retrieval → AI comparative explanation
3. Concept A/B → local LLMによる新Character創作

評価を二層に分ける。

### Retrieval / context delivery

- 正しいObject / Facet / Relation / Evidenceが取得できるか
- MCP/context payloadが十分か
- 不要・矛盾・historical dataが混入しないか

### AI output quality

- factual grounding
- requested use-caseへの適合
- hallucination / unsupported claim
- provenance説明可能性

モデル性能そのものとSGOKB retrieval欠陥を混同しない。

---

## 9. N-05 Performance measurement

B-06で定義したlocal automatic segmentだけを主要計測対象とする。

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
Large profile:   p95 <= 20 min（別集計）
```

cold / warm、model load、GPU/CPU、storage、Embedding Space、vector backend、retry等をbenchmark metadataへ保存する。

---

## 10. N-06 Retrieval / Vector quality

既存資産:

- `benchmark/search-quality-gold-v1.json`
- `scripts/run_search_quality_gold.py`
- `scripts/run_search_gold_reranker_benchmark.py`
- `scripts/run_vector_backend_benchmark.py`

評価channelを混ぜない。

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

必要な指標:

- Recall@K
- MRR
- nDCG（適切なgraded relevanceがある場合）
- latency
- RAM / VRAM
- disk
- index build / incremental update / rebuild

ANN backendはExact baselineと比較する。Statement数の多いObjectがaggregationで不当にboostされないことも確認する。

Semantic runtime構成はN-06開始時にReference Workstation用の再現可能な設定として固定し、silent cloud fallbackを禁止する。

---

## 11. N-07 Failure / Recovery

最低限、Task masterにある次のfailure domainを分類して試験する。

### Input / Result

- invalid JSON / schema version
- unknown Evidence
- stale / partial Result
- Result受領済み・Import未承認

### Derived runtime

- embedding model / representation change
- Vector Index消失・破損
- backend exchange
- Derived Index update failure

### Process / storage

- process kill / partial Import
- disk full / partial file
- Raw欠損 / checksum mismatch / broken provenance

### External / offline

- Internet / provider停止
- MCP停止
- local provider failure
- external export blocked / credential finding

### Recovery

- full index rebuild from SQLite
- backup create
- restore to別path
- integrity validation
- RPO / RTO記録

canonical SQLite Knowledgeを壊さないこと、silent promotion / silent fallback / silent exportを起こさないことを最重要Gateとする。

---

## 12. Phase N evidence / completion policy

各Taskは「実行した」だけでなく、再現可能なEvidenceを残す。

推奨:

```text
docs/evaluation/          人間が読む評価結果
benchmark/                frozen gold / machine-readable input
.local/nXX/               machine-local logs/results（Git管理外）
tests/                    deterministic regression
```

Phase N closure時には`docs/planning/PHASE_N_CLOSURE_AUDIT.md`を作成し、少なくとも次をまとめる。

- N-01〜N-07 status
- full test結果
- known unresolved failures
- real-data Vertical Slice一覧
- AI use-case acceptance
- performance result
- Retrieval / Vector quality result
- Failure / Recovery result
- optional runtime / hardware metadata
- Phase Oへの残課題

Phase N完了条件:

> 新しいSGOKBの目的に対する受入条件を満たし、Schema適合・単一happy path・LLMの見た目の良い出力だけを品質合格と誤認しない。

---

## 13. Phase N開始Gate

Phase Nへ移行可能。

開始時点（履歴。N-01完了後の現在状態はsection 14を参照）:

- Phase M正式Task残件: **0**
- public CLI / standard workflow: **accepted**
- first task: **N-01 [P0] Unit Testを新ドメインへ更新する**
- Phase N implementation: **未着手**

N-01ではまずTest inventoryとcoverage gapを確定し、その後にtest変更へ進む。


## 14. N-01 runtime verification完了

2026-10-16、Reference Workstationで対象test 11件とfull suite、指定RuffがPASSし、N-01をCompleteとした。Relationのgrounding / accepted immutabilityが現行contractと一致し、Package Transfer既知failureも解消した。詳細と件数は`docs/planning/N01_UNIT_TEST_COVERAGE.md`を参照する。

次TaskはN-02（未着手）。Phase N全体のComplete判定はN-02〜N-07とclosure auditの完了後に行う。
