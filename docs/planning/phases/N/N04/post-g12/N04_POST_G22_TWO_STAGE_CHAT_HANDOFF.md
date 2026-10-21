# N-04 Post-G22 Two-Stage Remediation — Historical Handoff

更新日: 2026-10-22

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Historical scope: G-23〜G-25A v4 Grounded Generation / classifier work
- Status: **Historical / Superseded as current handoff**
- Superseding decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`

## 1. Historical state

This handoff previously directed the next chat to continue:

```text
G-23F v4 Design Frozen
G-24 v4 implementation Complete
G-25A Residual Classifier Benchmark / Selection
```

G-25A subsequently completed as:

```text
VALID_FAIL_NO_SELECTION
```

No Residual Atomicity / Content-Type classifier satisfied the historical mandatory selection Gates.

## 2. Responsibility boundary changed

2026-10-22、N-04を上位要件まで遡って再評価し、formal SGOKB responsibilityを次へ修正した。

```text
Canonical / Derived SGOKB
        ↓
Retrieval / Similarity
        ↓
Context Builder
        ↓
MCP / public read boundary
        ↓
External Consumer boundary  ← N-04 formal acceptance ends here
```

Consumer-generated textのAtomicity / Content Type / factual grounding / creative labelingをSGOKB formal Completion Gateにしない。

したがって、このHandoffはcurrent work entryではない。

## 3. Current read-first order

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
3. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
4. `docs/planning/phases/N/N04/post-g12/N04_POST_G12_CHAT_HANDOFF.md`
5. `docs/planning/phases/N/PHASE_N_PREPARATION.md`

## 4. Current task

```text
N-04R-03 — Formal Harness Reconstruction
```

HarnessはSGOKB Knowledge Access Boundaryのみをformal判定する。

## 5. Historical v4 preservation

v4 architecture / implementation / tests / classifier benchmark evidenceは削除しない。

将来の処遇はN-04R-05で次から選ぶ。

```text
KEEP_CORE
KEEP_EXPERIMENTAL
MOVE_CONSUMER_SIDE
RETIRE
```

## 6. Do not continue old chain for N-04

- G-25A candidate追加を行わない。
- classifier threshold / taxonomy tuningを行わない。
- G-25B / G-26 / G-27をN-04目的で進めない。
- Frozen 47をN-04目的で実行しない。
- Consumer output failureを理由にSGOKB coreを修正しない。

## 7. Phase N current relationship

```text
N-03 Complete
  ├─ N-04 Pending re-acceptance
  ├─ N-05 Ready
  └─ N-06 Ready
        ↓
      N-07 Pending
```
