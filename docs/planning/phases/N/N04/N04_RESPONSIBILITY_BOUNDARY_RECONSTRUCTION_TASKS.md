# N-04 Responsibility Boundary Reconstruction Tasks

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Asset disposition: `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
- Status: **Complete — N-04R-01〜R-05 Complete / N-04 Complete PASS**

## 1. Purpose

N-04を、外部AIの生成品質ではなく、**SGOKBが外部Consumerへ正しいKnowledgeを提供できることのformal acceptance**として再構築する。

過去のG-12〜G-25は削除せず、old specification下のhistorical remediation / research evidenceとして保持する。

## 2. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04R-01 | P0 | **Complete** | Responsibility Boundary Correctionを正式Decision化する |
| N-04R-02 | P0 | **Complete (2026-10-22)** | N-04 acceptance spec / Phase N docs / handoffを再構築する |
| N-04R-03 | P0 | **Complete (2026-10-22)** | Formal harnessをKnowledge Access Boundary専用に再構築する |
| N-04R-04 | P0 | **Complete / PASS (2026-10-22)** | Reference Workstationで3代表ケースを再受入する |
| N-04R-05 | P1 | **Complete (2026-10-22)** | G-01〜G-25 Grounded Generation assetsの将来処遇を決定する |

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

Current machine-readable spec / harness:

- `benchmark/n04-knowledge-access-cases-v1.json`
- `benchmark/n04-knowledge-access-formal-harness-v1.json`
- `benchmark/tools/n04r03_harness_preflight.py`
- `benchmark/tools/n04r04_evaluate_evidence.py`

Decision:

`docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`

## 6. N-04R-04 — Reference Workstation Re-Acceptance

Status: **Complete / PASS (2026-10-22)**

Run:

```text
20261022T052331+0900
```

結果:

```text
Case 1 Saber / roleplay                            PASS
Case 2 Fate/stay night / Similarity / comparison  PASS
Case 3 Tsundere + Hero's Journey / creative       PASS
Canonical invariance                              PASS
System integrity                                  PASS
Post-run focused pytest                            32 passed
Post-run full pytest                               505 passed / 0 failed
Ruff / diff check                                  PASS
Formal overall                                    PASS
```

Case 2は実Similarity rank 1で返ったBLEACHをそのままComparison Contextへ使用した。

正式結果:

`docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`

これにより`N-04 = Complete / PASS`とする。

## 7. N-04R-05 — Grounded Generation Asset Disposition

Status: **Complete (2026-10-22)**

Decision:

`docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`

Machine-readable manifest:

`benchmark/n04r05-grounded-generation-asset-disposition-v1.json`

確定した分類:

```text
KEEP_CORE
  Grounded Generation chainからは0件
  current N-04 Knowledge Access assetsは引き続きcore

MOVE_CONSUMER_SIDE
  src/sgokb/application_grounding.py
  src/sgokb/application_grounding_v4.py
  src/sgokb/grounding/**
  coupled implementation tests
  Grounded Generation architecture / implementation contracts

KEEP_EXPERIMENTAL
  G-13以降のfailure analysis / evaluation evidence
  Frozen 47 / semantic research corpus
  G-25A development corpus / VALID_FAIL_NO_SELECTION result

RETIRE
  old N-04 v1/v2/v3 generation-quality harnesses
  old verifier/judge/classifier execution tooling
  superseded execution-contract tests
  historical Grounded Generation task/handoff documents
```

重要:

- R-05ではhistorical reproducibility維持のため物理削除を行わない。
- `MOVE_CONSUMER_SIDE`資産は今後SGOKB public CLI / MCP / canonical workflowへ接続しない。
- Consumer-side capabilityとして再開する場合は新しい責務・要件を先に定義する。
- G-25A classifier selectionをN-04目的で再開しない。
- Frozen 47をcurrent N-04 Gateとして実行しない。

## 8. N-04 reconstruction closure

```text
N-04R-01 Complete
N-04R-02 Complete
N-04R-03 Complete
N-04R-04 Complete / PASS
N-04R-05 Complete
```

**N-04 responsibility reconstruction chain = Complete.**

過去のG-12 / G-22 / G-25A resultは削除せずhistorical evidenceとして保持する。

## 9. Current Phase N state

```text
N-01 Complete
N-02 Complete
N-03 Complete
N-04 Complete / PASS
N-05 Ready
N-06 Ready
N-07 Pending
```

## 10. Next task

N-05 / N-06は独立して開始可能。

順次進める場合の次Task:

```text
N-05 — Performance
```
