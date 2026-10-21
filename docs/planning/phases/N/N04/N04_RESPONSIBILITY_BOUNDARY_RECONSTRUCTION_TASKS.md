# N-04 Responsibility Boundary Reconstruction Tasks

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Status: **Active**

## 1. Purpose

N-04を、外部AIの生成品質ではなく、**SGOKBが外部Consumerへ正しいKnowledgeを提供できることのformal acceptance**として再構築する。

過去のG-12〜G-25は削除せず、old specification下のhistorical remediation / research evidenceとして保持する。

## 2. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04R-01 | P0 | **Complete** | Responsibility Boundary Correctionを正式Decision化する |
| N-04R-02 | P0 | **Active** | N-04 acceptance spec / Phase N docs / handoffを再構築する |
| N-04R-03 | P0 | Pending | Formal harnessをKnowledge Access Boundary専用に再構築する |
| N-04R-04 | P0 | Pending | Reference Workstationで3代表ケースを再受入する |
| N-04R-05 | P1 | Pending | G-13〜G-25 Grounded Generation assetsの将来処遇を決定する |

## 3. N-04R-01 — Responsibility Boundary Correction

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

更新対象:

- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- `docs/planning/phases/N/PHASE_N_PREPARATION.md`
- `docs/planning/phases/N/N04/post-g12/N04_POST_G12_CHAT_HANDOFF.md`
- `docs/planning/phases/N/N04/post-g12/N04_POST_G12_REMEDIATION_TASKS.md`
- `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`

方針:

- current authorityは新Decisionと再構築済みN-04 acceptance specへ一本化する。
- historical formal runs / benchmark resultsを削除しない。
- G-13〜G-25をN-04 Completion prerequisiteから外す。
- N-05 blockedを解除する。

## 5. N-04R-03 — Harness Reconstruction

formal harnessは次だけを判定する。

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

削除するformal Gate:

```text
consumer output grounding
atomicity classifier
content-type classifier
source-fact verifier
interpretation verifier
grounded-generation certification
creative labeling by consumer
```

Reference Consumer実行を残す場合はnon-gating evidenceとして別artifactへ分離する。

## 6. N-04R-04 — Reference Workstation Re-Acceptance

N-03 real-data evaluation DBを再利用し、次の3ケースをSGOKB boundaryまで実行する。

1. Saber → `purpose=roleplay`
2. Fate/stay night → Similarity candidate → `purpose=comparison`
3. Tsundere + Hero's Journey → `purpose=creative`

3ケースすべてでformal GateをPASSした場合、N-04をCompleteとする。

AI ConsumerによるRoleplay / Comparison / Creative生成結果は、実行する場合でも参考記録としformal resultへ含めない。

## 7. N-04R-05 — Grounded Generation Asset Disposition

対象:

- v3 / v4 Grounded Generation production code
- verifier adapters
- atomicity / content-type classifier assets
- Frozen 47 benchmark
- G-13〜G-25 design / evaluation documents

分類:

```text
KEEP_CORE
KEEP_EXPERIMENTAL
MOVE_CONSUMER_SIDE
RETIRE
```

処遇判断までは既存code / benchmark / docsを削除しない。

## 8. Completion state after reconstruction

```text
N-01 Complete
N-02 Complete
N-03 Complete
N-04 Pending re-acceptance under corrected boundary
N-05 Ready
N-06 Ready
N-07 Pending
```
