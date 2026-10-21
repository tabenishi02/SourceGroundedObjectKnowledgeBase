# Knowledge Base Redesign Handoff — N-04 Amendment

更新日: 2026-10-22

- Applies to: `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
- Scope: Current Phase N / N-04 state
- Status: **Accepted amendment — N-04 reconstruction complete**

## 1. Current project state override

既存の全体HandoffはPhase A〜Mの設計背景を引き続き参照できるが、現在地点に関する記述は古い。

2026-10-22時点のcurrent stateは次とする。

```text
Phase A〜M Complete
Phase N Active
N-01 Complete
N-02 Complete
N-03 Complete
N-04 responsibility reconstruction Complete
N-04 Complete / PASS
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

## 3. N-04 reconstruction result

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Complete
N-04R-03 Formal Harness Reconstruction           Complete
N-04R-04 Reference Workstation Re-Acceptance     Complete / PASS
N-04R-05 Grounded Generation Asset Disposition   Complete
```

N-04R-04 formal result:

```text
run_id 20261022T052331+0900
3 / 3 representative cases PASS
canonical invariance PASS
system integrity PASS
post-run focused 32 passed
post-run full 505 passed / 0 failed
Ruff / diff check PASS
```

## 4. Grounded Generation disposition

R-05により、旧Grounded Generation chainはSGOKB coreから正式に分離した。

```text
KEEP_CORE
  Grounded Generation chainから0件

MOVE_CONSUMER_SIDE
  Grounded Generation implementation / verifier / pipeline
  coupled tests
  architecture contracts

KEEP_EXPERIMENTAL
  failure analysis / evaluation evidence
  Frozen 47 / semantic research corpus
  G-25A development corpus / VALID_FAIL_NO_SELECTION

RETIRE
  old generation-quality harnesses
  old verifier / judge / classifier execution tooling
  superseded execution-contract tests
  historical task / handoff documents
```

物理削除は行っていない。historical reproducibilityを保持しつつ、production authorityを解除した。

`src/sgokb/application_grounding.py`、`src/sgokb/application_grounding_v4.py`、`src/sgokb/grounding/**`を今後SGOKB public CLI / MCP / canonical workflowの必須dependencyへ戻してはならない。

Decision:

`docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`

Manifest:

`benchmark/n04r05-grounded-generation-asset-disposition-v1.json`

## 5. Historical remediation

旧N-04 generation-quality specification下でG-01〜G-25AまでGrounded Generation remediationを実施した。

主なhistorical results:

```text
G-12  0/3 formal Case PASS
G-22  0/3 formal Case PASS
G-25A VALID_FAIL_NO_SELECTION
```

これらは有効なhistorical / research evidenceだが、current N-04 Completion prerequisiteではない。

## 6. Current read-first documents

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
3. `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
4. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
5. `docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`
6. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
7. `docs/planning/phases/N/PHASE_N_PREPARATION.md`
8. `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS_N04_AMENDMENT.md`

## 7. Current next work

N-04 reconstruction chainは終了した。

N-05 / N-06は独立して開始可能。順次進める場合:

```text
N-05 — Performance
```

N-04R-04正式結果:

`docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`
