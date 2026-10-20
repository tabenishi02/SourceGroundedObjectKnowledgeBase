# N-04G-23B — Next Chat Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Authoritative repository state: GitHub `main`
- Handoff baseline main: `c1174b3fc435e4bbc1ac4203dd2236821d28a26e`
- Current task: **N-04G-23B — Stage 1 Grounded Content Planner Contract**
- G-23A-E: **Complete / Architecture Accepted**
- G-23B: **NEXT**
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Start here in the next chat

Before designing G-23B, read these files from GitHub `main` in this order:

1. `docs/planning/phases/N/N04/post-g12/N04G23B_NEXT_CHAT_HANDOFF.md`
2. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
3. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
4. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
5. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
6. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
7. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
8. `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`
9. `benchmark/n04g23ae-role-compatibility-v1.json`
10. `benchmark/n04g23ae-v4-gate-desk-replay-v1.json`
11. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
12. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

Historical references only when needed:

- `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
- `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`

---

## 2. Current architecture baseline

G-23A-E1〜E7 resolved the Atomicity / Role responsibility problem at the architecture level.

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidate
  ↓
V2-S Structural Proposition Gate
  ↓
V2-P Application-owned Role Provenance
  ↓
V2-D Deterministic Compatibility Gate
  ↓ PASS only
V2-R-A Residual Atomicity if required
  ↓ ATOMIC only
V2-R-C Residual Content Type if required
  ↓ compatible only
V3/V4 Support / Derivation
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
```

No downstream positive verdict may rescue an earlier FAIL or INDETERMINATE.

The old broad joint Atomicity/Role Judge is no longer an authority in v4.

---

## 3. Decisions already fixed

### 3.1 Structured Proposition

Selected contract family: **Semi-structured proposition record**.

Core rules:

- application owns contract/context/purpose/stage/path/attempt/proposition identity;
- one authoritative `claim_text` per candidate;
- Stage 1 source-fact candidate uses `support_refs[]`;
- interpretation uses certified `premise_fact_ids[]` later in Stage 2;
- support and premise bindings do not coexist;
- candidate / validation / certification are separate artifacts;
- model-authored free text is not Atomic merely because schema-valid;
- no silent post-hoc atomization.

### 3.2 Role provenance

Role is derived from application-owned path, not from generator self-declaration.

```text
stage1_fact_candidate             -> source_fact
certified_fact_materialization    -> source_fact
stage2_interpretation_candidate   -> interpretation
stage2_creative_candidate         -> creative_addition
system_context_limit              -> context_limit
```

Unknown/forged path fails closed.

### 3.3 Deterministic policy

Known metadata violations are deterministic hard failures before any residual classifier.

Examples:

- path / owner / stage mismatch
- purpose incompatibility
- presentation mismatch
- missing/forbidden support binding
- missing/forbidden premise binding
- model-authored context limit
- context-limit coexistence
- model-authored stylistic expression

### 3.4 Residual classifiers

Residual semantic work is split into two independent tasks.

```text
V2-R-A Atomicity
  ATOMIC / NON_ATOMIC / AMBIGUOUS

V2-R-C Content Type
  SOURCE_FACT_CONTENT
  INTERPRETATION_CONTENT
  CREATIVE_CONTENT
  CONTEXT_LIMIT_CONTENT
  MIXED_CONTENT
  AMBIGUOUS
```

Expected role/purpose/presentation are hidden from the classifier inputs. The application compares observed content class with the expected role afterward.

`AMBIGUOUS`, unavailable, malformed or unknown output fails closed.

Concrete classifier selection is **not** part of G-23B.

---

## 4. Why G-23B is unblocked

E6 replayed all Frozen 47 Gold fixtures through the proposed v4 authority model.

```text
Critical total                            33
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

Residual Atomicity remains a substantial implementation risk:

```text
V2-R-A invoked                  42 / 47
critical invalid depending A    25 / 33
```

E7 nevertheless accepted the architecture because the remaining uncertainty is component performance, not an undefined responsibility/interface boundary.

This is **not** evidence that the Atomicity classifier already works.

---

## 5. G-23B exact scope

Design the **Stage 1 Grounded Content Planner contract** only.

Primary Stage 1 candidate path:

```text
stage1_fact_candidate
  -> normalized role = source_fact
```

At minimum G-23B should fix:

1. Stage 1 request contract.
2. Stage 1 response / candidate schema.
3. Application-owned envelope construction.
4. One-proposition-per-candidate generation policy.
5. `claim_text` semantics.
6. `support_refs[] >= 1` requirements.
7. Reference-integrity expectations before support validation.
8. Candidate identity and retry lineage.
9. Representation of multiple Stage 1 candidates.
10. Conservative prompt policy and GOOD/BAD examples.
11. Provider structured-output constraints that are safe to enforce.
12. How Stage 1 output enters V2-S/P/D/R without duplicate authority.
13. Stage-local retry inputs/outputs only to the extent necessary to define the Stage 1 contract; detailed retry integration remains G-23E.
14. Evidence / artifact fields that later G-23C/G-23E/G-26 need to freeze and replay Stage 1.

G-23B should produce a normative Decision/contract artifact suitable for G-23C consumption.

---

## 6. G-23B must not reintroduce

Do not add any of the following authority back into the Stage 1 model output:

```text
generator-owned authoritative semantic_role
model-owned Atomicity PASS
model-owned validation status
model-owned certification status
model-owned support/entailment PASS
presentation role on stage1_fact_candidate
free-form model-authored context_limit path
```

Do not claim schema validity proves semantic Atomicity.

Do not add a post-hoc atomizer that splits an already generated non-atomic proposition and silently preserves/render the original compound text.

Do not redesign Retrieval, Similarity, Context Builder, canonical DB, Source/Evidence/Provenance, Object/Version identity or MCP boundaries.

---

## 7. Stage 1 design direction

The existing architecture decision already requires Stage 1 to be conservative.

Prompt/schema direction:

```text
prefer supplied Grounded Context wording
minimally normalize wording
one independently judgeable proposition per candidate
no extra proposition
no model-memory source-world additions
bind every fact candidate to explicit support refs
```

Structured output should reduce obvious structural errors, but model-authored `claim_text` remains subject to V2-R-A unless a later, explicit deterministic-construction exemption is frozen.

Stage 1 has no final presentation role.

---

## 8. Downstream work already reserved

After G-23B:

```text
G-23C Certified Content contract
G-23D Stage 2 Presentation Generator contract
G-23E Provider schema + stage-local retry design
G-23F v4 integration / Design Freeze
G-24 implementation
G-25A Residual Classifier Benchmark / Selection
G-25B Integrated v4 Adversarial Regression
G-26 Reference Workstation Freeze
G-27 Formal v4 Re-Acceptance
```

G-25A is mandatory before G-26.

```text
Atomicity critical false-pass = 0
Content critical wrong-compatible false-pass = 0
required-valid false reject target = 0
```

If every classifier candidate fails:

```text
VALID_FAIL_NO_SELECTION
```

G-26 stays blocked and the Gate must not be weakened.

---

## 9. Protected boundaries

Do not change without concrete new failure evidence:

- Frozen 47 Gold labels / required / critical flags
- G-23A/G-23A-R historical evidence
- G-14 no-silent-post-hoc-atomization safety intent
- G-23 two-stage generation architecture
- E2 authority order
- E3 Semi-structured proposition contract
- E4 application-owned role provenance / deterministic policy
- E5 zero-critical-FP / fail-closed selection policy
- MiniCheck selection / threshold merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered material claim prohibition
- fail-closed semantics

---

## 10. Current state

```text
G-23A-E1〜E7 = Complete
G-23A-E       = Complete / Architecture Accepted
G-23B         = NEXT
N-04          = Failed / not Complete
N-05          = blocked
```

## 11. Immediate next action

Start **N-04G-23B — Stage 1 Grounded Content Planner Contract** from GitHub `main`.

First, summarize the constraints above and identify the Stage 1 contract decisions that still require explicit design choices. Then perform G-23B without modifying protected historical/frozen evidence.
