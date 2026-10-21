# Knowledge Base Redesign Handoff — N-04 Amendment

更新日: 2026-10-22

- Applies to: `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
- Scope: Current Phase N / N-04 state
- Status: **Accepted amendment**

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
N-04 Pending re-acceptance
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

## 3. Historical remediation

旧N-04 generation-quality specification下で、G-01〜G-25AまでGrounded Generation remediationを実施した。

主なhistorical results:

```text
G-12  0/3 formal Case PASS
G-22  0/3 formal Case PASS
G-25A VALID_FAIL_NO_SELECTION
```

これらは有効なhistorical evidenceだが、current N-04 Completion prerequisiteではない。

## 4. Current read-first documents

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
3. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
4. `docs/planning/phases/N/PHASE_N_PREPARATION.md`
5. `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md`
6. `docs/planning/phases/N/N04/post-g12/N04_POST_G12_CHAT_HANDOFF.md`

## 5. Current next task

```text
N-04R-03 — Formal Harness Reconstruction
```

N-04R-03ではSGOKB Knowledge Access Boundaryのみをformal判定するharnessへ置き換える。

N-05 / N-06はN-04完了を待たず進行可能。
