# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-20

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23: **Complete / Architecture Accepted**
- G-23A: **Complete / valid benchmark; Phi-4 insufficient**
- G-23A-R: **Complete / valid FAIL / no candidate selected**
- G-23A-E: **Planned / NEXT**
- Current task: **N-04G-23A-E1 — 47-Gold Responsibility Mapping**
- G-23B: **blocked until G-23A-E is accepted**

## Read first

1. `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md`
2. `docs/evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md`
3. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
4. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
5. `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`
6. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
7. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
8. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`
9. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`

---

## Current architecture decision

次期v4ではLLM生成責務を2段階化する。

```text
Grounded Context
  ↓
Stage 1: Grounded Content Planner
  ↓
Certification
  ↓
Certified Content
  ↓
Stage 2: Presentation Generator
  ↓
Final Material / Terminal / Render
```

G-23A/G-23A-Rの結果を受け、Stage間のAtomicity / Role Gateはv3のall-in-one general-purpose LLM judge方式をそのまま再利用しない。

新しい設計方向:

```text
Structured Proposition Record
  ↓
Structural validation
  ↓
Application-owned role provenance
  ↓
Deterministic role/purpose/presentation compatibility
  ↓
Residual semantic classifier only when necessary
  ↓
fail-closed support / certification path
```

---

## Why G-23A-E is required

G-23A:

- 47 Gold cases
- exact G-22 replay reproduced
- clarified joint / paraphrase / split-call formulations all failed frozen Safety or Required-valid Gates
- Phi-4 not viable under tested formulations

G-23A-R:

- Qwen3.5 runtime-incompatible before Gold
- Ministral 3 8B Primary FAIL
- Gemma 4 12B Primary FAIL
- Mistral Small 3.2 24B Primary FAIL
- no Primary PASS / no Secondary
- deterministic selector `VALID_FAIL_NO_SELECTION`

The failure pattern is not explained by model size alone. More importantly, current Role Judge includes deterministic policy rules such as purpose/presentation compatibility that should not require an LLM.

Therefore do not continue by simply adding more general-purpose judge models under the same responsibility contract.

---

## G-23A-E target responsibility model

### Atomicity

```text
Primary authority:
  structured proposition invariant

Residual protection:
  compound-risk detection / bounded semantic check
```

Do not silently post-hoc split non-atomic text and then render the original text.

### Semantic Role

```text
Role provenance:
  application/stage path

Compatibility:
  deterministic policy matrix

Residual natural-language content type:
  narrow classifier only when needed
```

Generator self-declared role is not grounding authority.

### Uncertainty

```text
MIXED / AMBIGUOUS / unresolved
  -> fail closed
```

---

## G-23A-E task order

```text
G-23A-E1 47-Gold Responsibility Mapping              NEXT
  ↓
G-23A-E2 v4 V2 Responsibility Boundary Design
  ↓
G-23A-E3 Structured Proposition Contract Design
  ↓
G-23A-E4 Role Provenance / Compatibility Matrix
  ↓
G-23A-E5 Residual Classifier Scope / Evaluation Plan
  ↓
G-23A-E6 47-Gold Desk Replay / Coverage Analysis
  ↓
G-23A-E7 Integration Decision / Unblock Review
  ↓ ACCEPTED only
G-23B Stage 1 Content Planner contract
```

Task detail authority:

`docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`

---

## Immediate task: G-23A-E1

Use the frozen corpus:

`benchmark/n04g23a-atomicity-role-gold-v1.json`

Map all 47 cases into:

```text
STRUCTURAL
DETERMINISTIC_POLICY
RESIDUAL_SEMANTIC
COMBINED
OPTIONAL_AMBIGUOUS
```

For every case define:

- primary owner
- secondary guard if needed
- structured inputs available
- semantic classification still required or not
- expected v4 path
- whether historical judge failure becomes impossible by construction
- retained regression assertion

Do not change Gold labels/required/critical flags during this task.

Expected deliverable:

`docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`

---

## Protected historical / safety boundaries

Do not change without new explicit failure evidence:

- G-14 atomicity / role safety intent
- G-18/G-21 Frozen v3 history
- G-22 valid formal FAIL
- G-23A frozen Gold and results
- G-23A-R valid no-selection result
- Object / Version identity
- Source / Evidence / Provenance
- canonical DB
- MCP read-only boundary
- Retrieval / Similarity
- Context Builder
- MiniCheck threshold merely to improve acceptance
- unsupported rendered claim prohibition
- accepted role escape prohibition
- fail-closed semantics

---

## Current state

```text
G-23A     Complete
G-23A-R   Complete / valid FAIL / no selection
G-23A-E   Planned / NEXT
G-23A-E1  NEXT
G-23B     blocked by G-23A-E

N-04      Failed / not Complete
N-05      blocked
```

Only after G-23A-E7 accepts the new responsibility model may G-23B become NEXT.
