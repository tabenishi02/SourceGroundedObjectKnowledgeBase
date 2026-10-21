# N-04 Grounded Generation — Historical Design Handoff

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Historical scope: G-01〜G-12 design / implementation handoff
- Current status: **Historical / Superseded**
- Superseding decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`

## 1. Historical context

このHandoffは、2026-10-18の旧N-04受入でConsumer AIのContext外claim等が発生した後、SGOKB側へGrounded Generation protectionを追加するために作成された。

当時すでに次は正常と確認されていた。

- MCP stdio / public read path
- current accepted Version resolution
- Context Builder
- `roleplay` / `comparison` / `creative` purpose
- Context budget
- Similarity retrieval
- historical Version isolation
- read-only canonical safety
- integrity / regression

失敗はConsumer-generated output側に集中していた。

## 2. Responsibility correction

2026-10-22、N-04の上位要件と責務境界を再確認し、formal acceptanceを次までに限定した。

```text
SGOKB canonical Knowledge
  ↓
Retrieval / Similarity
  ↓
Context Builder
  ↓
MCP / public read boundary
  ↓
External Consumer boundary
```

External Consumer以降の推論・生成品質はSGOKB formal responsibilityではない。

したがって、このHandoffで開始したGrounded Generation remediationはN-04 Completion prerequisiteではなくなった。

## 3. Historical evidence remains valid

旧N-04 / G-12で観測したConsumer output failureは削除しない。

また、Grounded Generationの設計・実装過程も、Consumer-side grounded generationを将来検討する場合の研究資産として有効である。

## 4. Do not use this as current handoff

現在の作業開始点は次とする。

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
3. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
4. `docs/planning/phases/N/N04/post-g12/N04_POST_G12_CHAT_HANDOFF.md`

Current next task:

```text
N-04R-03 — Formal Harness Reconstruction
```

## 5. Future disposition

N-04R-05でGrounded Generation assetsを`KEEP_CORE / KEEP_EXPERIMENTAL / MOVE_CONSUMER_SIDE / RETIRE`へ分類するまでは、既存code / docs / benchmarkを削除しない。
