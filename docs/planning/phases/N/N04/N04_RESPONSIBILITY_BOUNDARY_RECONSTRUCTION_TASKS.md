# N-04 Responsibility Boundary Reconstruction Tasks

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Status: **Active — N-04R-03 Complete / Next N-04R-04**

## 1. Purpose

N-04を、外部AIの生成品質ではなく、**SGOKBが外部Consumerへ正しいKnowledgeを提供できることのformal acceptance**として再構築する。

過去のG-12〜G-25は削除せず、old specification下のhistorical remediation / research evidenceとして保持する。

## 2. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04R-01 | P0 | **Complete** | Responsibility Boundary Correctionを正式Decision化する |
| N-04R-02 | P0 | **Complete (2026-10-22)** | N-04 acceptance spec / Phase N docs / handoffを再構築する |
| N-04R-03 | P0 | **Complete (2026-10-22)** | Formal harnessをKnowledge Access Boundary専用に再構築する |
| N-04R-04 | P0 | **Next / Pending** | Reference Workstationで3代表ケースを再受入する |
| N-04R-05 | P1 | Pending | G-13〜G-25 Grounded Generation assetsの将来処遇を決定する |

## 3. N-04R-01 — Responsibility Boundary Correction

Status: **Complete**

Accepted decision:

```text
SGOKB formal responsibility ends at the public Knowledge Access Boundary.
Consumer inference / generation quality is external.
Knowledge coverage sufficiency is external to N-04 formal failure.
Grounded Generation is not an N-04 prerequisite.
```

成果物:

`docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`

## 4. N-04R-02 — Documentation Reconstruction

Status: **Complete (2026-10-22)**

current authorityをResponsibility Boundary Decisionと再構築済みN-04 acceptance specへ一本化した。

主な変更:

- historical formal runs / benchmark resultsを削除しない。
- G-01〜G-25をN-04 Completion prerequisiteから外した。
- N-05 blockedを解除した。
- N-06もN-04と独立してReadyとした。

## 5. N-04R-03 — Harness Reconstruction

Status: **Complete (2026-10-22)**

formal harnessをSGOKB Knowledge Access Boundary専用へ再構築した。

formal Gate:

```text
public read boundary
current accepted version
purpose-specific context contract
retrieval / similarity integration
traceability
budget / omission / truncation semantics
canonical invariance
integrity / regression
```

formal Gateから除外:

```text
consumer output grounding
atomicity classifier
content-type classifier
source-fact verifier
interpretation verifier
grounded-generation certification
creative labeling by consumer
Frozen 47
```

### Deliverables

Machine-readable current spec / harness:

- `benchmark/n04-knowledge-access-cases-v1.json`
- `benchmark/n04-knowledge-access-formal-harness-v1.json`

Harness / evaluator:

- `benchmark/tools/n04r03_harness_preflight.py`
- `benchmark/tools/n04r04_evaluate_evidence.py`

Focused regression:

- `tests/test_n04r03_knowledge_access_harness.py`
- `tests/test_n04r04_evidence_evaluator.py`

Decision / execution handoff:

- `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
- `docs/planning/phases/N/N04/execution/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE_HANDOFF.md`

### Frozen semantics

- 3代表ケースを維持する。
- Case 2 candidateは実Similarity top resultを使い、known BLEACH IDをhardcodeしない。
- Context contractは`sgokb.context-builder.v1`。
- MCP read contractは`sgokb.mcp-read-tools.v1`。
- case spec / deterministic evaluatorをGit blob SHAでHarnessへbindする。
- formal evaluatorはraw SGOKB boundary evidenceだけを読む。
- Consumer outputはformal verdictへ使用しない。
- required evidence不足・読取不能は`BLOCKED`とする。
- SGOKB boundary defectだけを`FAIL`とする。

Reference Workstationでのpreflight / formal runは意図的にR-04へ分離した。R-03では実機PASSを主張しない。

## 6. N-04R-04 — Reference Workstation Re-Acceptance

Status: **Next / Pending**

N-03 real-data evaluation DBを再利用し、次の3ケースをSGOKB boundaryまで実行する。

1. Saber → `purpose=roleplay`
2. Fate/stay night → Similarity candidate → `purpose=comparison`
3. Tsundere + Hero's Journey → `purpose=creative`

開始前にR-03 freeze documentのpreflightをReference Workstationで全PASSさせる。

3ケース + canonical invariance + integrity + regressionがすべてPASSした場合、N-04をCompleteとする。

AI ConsumerによるRoleplay / Comparison / Creative生成結果は、実行する場合でも参考記録としformal resultへ含めない。

実行正本:

`docs/planning/phases/N/N04/execution/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE_HANDOFF.md`

## 7. N-04R-05 — Grounded Generation Asset Disposition

Status: **Pending**

対象:

- v3 / v4 Grounded Generation production code
- verifier adapters
- atomicity / content-type classifier assets
- Frozen 47 benchmark
- G-01〜G-25 design / evaluation documents

分類:

```text
KEEP_CORE
KEEP_EXPERIMENTAL
MOVE_CONSUMER_SIDE
RETIRE
```

処遇判断までは既存code / benchmark / docsを削除しない。

## 8. Current Phase N state

```text
N-01 Complete
N-02 Complete
N-03 Complete
N-04 Pending Reference Workstation re-acceptance
N-05 Ready
N-06 Ready
N-07 Pending
```

## 9. Next task

```text
N-04R-04 — Reference Workstation Re-Acceptance
```
