# N-04 Grounded Generation — Historical Remediation Tasks

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Historical scope: G-01〜G-12 Grounded Generation remediation
- Current status: **Historical / Superseded as N-04 completion path**
- Superseding decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`

## 1. Historical purpose

このTask chainは、旧N-04でConsumer AIの生成品質をSGOKB formal Completion Gateへ含めていた時点に、Context外claim等をSGOKB側で抑止する目的で作成された。

G-01〜G-12でGrounded Generation contract、validation、retry、formal harnessを設計・実装・評価した。

## 2. Current disposition

2026-10-22のresponsibility boundary reconstructionにより、N-04 formal acceptanceはSGOKB public Knowledge Access Boundaryまでに限定された。

したがって次はcurrent N-04 Completion Gateではない。

- structured model-authored semantic units
- Grounded Generation validation
- Consumer output factual grounding
- Consumer output retry
- local generator success
- AI output quality rubric

G-01〜G-12の結果・Decision・benchmarkはhistorical evidenceとして保持する。

## 3. Historical status

```text
G-01〜G-11  Complete
G-12        Complete / valid formal FAIL / 0 of 3 Case PASS
```

G-12 failureを削除・上書きしない。

## 4. Current N-04 authority

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
3. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
4. `docs/planning/phases/N/N04/post-g12/N04_POST_G12_CHAT_HANDOFF.md`

## 5. Future handling

Grounded Generation assetsはN-04R-05で次のいずれかへ分類する。

```text
KEEP_CORE
KEEP_EXPERIMENTAL
MOVE_CONSUMER_SIDE
RETIRE
```

N-04をCompleteにする目的でこのhistorical chainを再開しない。
