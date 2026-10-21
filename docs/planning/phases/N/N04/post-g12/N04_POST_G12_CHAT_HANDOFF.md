# N-04 Current Chat Handoff — Reconstruction Complete

更新日: 2026-10-22

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Branch of record: `main`
- Parent Task: `N-04 [P0]`
- Current status: **Complete / PASS under corrected SGOKB responsibility boundary**
- N-04 reconstruction: **R-01〜R-05 Complete**
- N-05: **Ready**
- N-06: **Ready**
- N-07: **Pending**
- Recommended next task: **N-05 — Performance**

## 1. Read first

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
3. `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
4. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
5. `docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`
6. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
7. `docs/planning/phases/N/PHASE_N_PREPARATION.md`

GitHub `main`を正本とする。

## 2. Current responsibility boundary

N-04 formal acceptanceは次で終了する。

```text
Canonical / Derived SGOKB
        ↓
Retrieval / Similarity
        ↓
Context Builder
        ↓
MCP / public read boundary
        ↓
External Consumer boundary  ← formal N-04 ends here
```

外部Consumerの推論・生成・Roleplay・比較・創作品質はSGOKB formal Gateではない。

## 3. Formal result

Reference Workstation run:

```text
run_id: 20261022T052331+0900
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

Case 2は実Similarity rank 1で返ったBLEACHをhardcodeせず、そのID / VersionをContextへ使用した。

## 4. Current formal assets

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
```

これらはKnowledge Access Boundaryだけを評価し、Consumer outputを入力にしない。

## 5. R-05 Grounded Generation disposition

旧G-01〜G-25資産の将来処遇は確定済み。

```text
KEEP_CORE
  Grounded Generation chainから0件

MOVE_CONSUMER_SIDE
  Grounded Generation implementation / verifier / pipeline
  coupled implementation tests
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

Decision:

`docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`

Manifest:

`benchmark/n04r05-grounded-generation-asset-disposition-v1.json`

Physical deletion / repository extractionは今回行っていない。historical reproducibilityを保持しつつ、Grounded GenerationのSGOKB production authorityを解除した。

## 6. Historical chain

```text
Original N-04         Historical FAIL under old specification
G-12                  Historical valid formal FAIL / 0 of 3 PASS
G-22                  Historical valid formal FAIL / 0 of 3 PASS
G-25A                 Historical valid VALID_FAIL_NO_SELECTION
```

これらの結果は削除・改変しないが、current N-04 Completion prerequisiteではない。

## 7. Closed N-04 reconstruction chain

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Complete
N-04R-03 Formal Harness Reconstruction           Complete
N-04R-04 Reference Workstation Re-Acceptance     Complete / PASS
N-04R-05 Grounded Generation Asset Disposition   Complete
```

**N-04 = Complete / PASS.**

## 8. Phase N relationship

```text
N-03 Complete
  ├─ N-04 Complete / PASS
  ├─ N-05 Ready
  └─ N-06 Ready
        ↓
      N-07 Pending
```

N-05 / N-06は独立して開始可能。順次進める場合は`N-05 — Performance`へ進む。
