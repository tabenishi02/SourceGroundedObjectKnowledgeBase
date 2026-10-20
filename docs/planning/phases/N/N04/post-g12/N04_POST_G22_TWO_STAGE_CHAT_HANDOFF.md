# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-20

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23: **Complete / Architecture Accepted**
- Current task: **N-04G-23A — Atomicity / Role Gold Benchmark**

## Read first

1. `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md`
2. `docs/evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md`
3. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
4. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`
5. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
6. `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`

---

## Current architecture decision

次期v4ではLLM生成責務を2段階化する。

```text
Grounded Context
  ↓
Stage 1: Grounded Content Planner
  ↓
Atomicity / Role / Support / MiniCheck / Fact Judge
  ↓
Certified Content
  ↓
Stage 2: Presentation Generator
  ↓
Final V0-V5 / Material / Terminal / Render
```

目的は「何が言えるか」と「どう表現するか」を別のLLM generation responsibilityとして扱うこと。

Stage 1はfinal proseを作らない。
Stage 2はuncertified source factを新規生成しない。

---

## Historical v3 rule

G-18/G-21のFrozen v3 artifactは書き換えない。
G-22の0/3 FAILは有効なformal evidenceとして保持する。

v4はnew schema/profile/harnessとして作る。

---

## Why this was chosen

G-22で確認された主failure:

- unsupported source-world additions
- NON_ATOMIC units
- role-INDETERMINATE
- unsupported interpretation premise
- duplicate_presentation_role

一方、次は正常だった。

- Retrieval / Similarity
- canonical DB / integrity
- MiniCheck offline reproduction
- runtime identity
- engineering Gates

そのためMiniCheckやRetrievalを先に変更せず、Generator責務の分離を優先する。

---

## Immediate next task — G-23A

`Atomicity / Role Gold Set v1`を作成する。

Gold origin:

- G-22 actual units
- G-12/G-20 adversarial units
- synthetic neutral controls

Comparison:

1. exact G-22 Phi-4 prompt replay
2. clarified prompt/examples
3. atomicity / role separate calls
4. only if still inadequate: alternative judge model

Critical rule:

- critical false-pass = 0を維持
- valid-unit false-reject / INDETERMINATEを改善
- model replacementを最初の手段にしない

---

## Following tasks

```text
G-23A Atomicity / Role Gold Benchmark
G-23B Stage 1 Content Planner contract
G-23C Certification / Certified Content contract
G-23D Stage 2 Presentation Generator contract
G-23E Provider schema + stage-local retry
G-23F v4 Design Freeze
G-24  Implementation
G-25  Dev benchmark / regression
G-26  Reference Workstation v4 Freeze
G-27  Formal v4 Re-Acceptance
```

G-27で3/3 formal PASSした場合のみN-04をComplete、N-05をunblockする。

---

## Protected boundaries

新しいfailure evidenceなしに変更しない。

- Object / Version identity
- Source / Evidence / Provenance
- canonical DB
- MCP read-only boundary
- Retrieval / Similarity
- Context Builder selection/budget
- N-03 dataset
- MiniCheck threshold merely to increase acceptance
- historical G-12/G-20/G-21/G-22 evidence
- fail-closed principle

---

## Design preference to preserve

Stage 2 source_factは自由な再作文より、`certified_fact_id`を参照しapplicationがdeterministicにtext/support refsをmaterializeする方式を第一候補とする。

3段階以上への分割は将来拡張可能にするが、Stage 2で新しい責務衝突が実測されるまで採用しない。
