# Knowledge Base Redesign Handoff — N-04 Amendment

更新日: 2026-10-22

- Applies to: `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
- Scope: Current Phase N / N-04 state
- Status: **Accepted amendment — N-04R-03 Complete**

## 1. Current project state override

既存の全体HandoffはPhase A〜Mの設計背景を引き続き参照できるが、現在地点に関する記述は古い。

2026-10-22時点のcurrent stateは次とする。

```text
Phase A〜M Complete
Phase N Active
N-01 Complete
N-02 Complete
N-03 Complete
N-04 responsibility boundary reconstructed
N-04 formal harness reconstructed / frozen
N-04 Pending Reference Workstation re-acceptance
N-05 Ready
N-06 Ready
N-07 Pending
```

## 2. Current N-04 principle

SGOKBはKnowledge Providerであり、MCPはKnowledge Access Layerである。

N-04 formal responsibilityは次まで。

```text
Canonical / Derived SGOKB
  ↓
Retrieval / Similarity
  ↓
Context Builder
  ↓
MCP / public read boundary
  ↓
External Consumer boundary
```

Consumer AI / Applicationの推論・生成品質はSGOKB formal acceptanceから分離する。

## 3. N-04R-03 result

N-04R-03でKnowledge Access Boundary専用Harnessをfreezeした。

Current machine-readable assets:

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
```

Formal HarnessはConsumer generation / classifier / verifierへ依存しない。

Case 2は実Similarity top resultをContextへ渡し、known candidateをhardcodeしない。

Formal evaluatorはraw SGOKB boundary evidence、canonical invariance、integrity、regressionだけから`PASS / FAIL / BLOCKED`を決定する。

Freeze record:

`docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`

## 4. Historical remediation

旧N-04 generation-quality specification下で、G-01〜G-25AまでGrounded Generation remediationを実施した。

主なhistorical results:

```text
G-12  0/3 formal Case PASS
G-22  0/3 formal Case PASS
G-25A VALID_FAIL_NO_SELECTION
```

これらは有効なhistorical evidenceだが、current N-04 Completion prerequisiteではない。

## 5. Current read-first documents

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
3. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
4. `benchmark/n04-knowledge-access-cases-v1.json`
5. `benchmark/n04-knowledge-access-formal-harness-v1.json`
6. `docs/planning/phases/N/N04/execution/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE_HANDOFF.md`
7. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
8. `docs/planning/phases/N/PHASE_N_PREPARATION.md`
9. `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md`

## 6. Current task chain

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Complete
N-04R-03 Formal Harness Reconstruction           Complete
N-04R-04 Reference Workstation Re-Acceptance     Next / Pending
N-04R-05 Grounded Generation Asset Disposition   Pending
```

## 7. Current next task

```text
N-04R-04 — Reference Workstation Re-Acceptance
```

実行正本:

`docs/planning/phases/N/N04/execution/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE_HANDOFF.md`

N-05 / N-06はN-04完了を待たず進行可能。
