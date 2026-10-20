# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition Tasks

更新日: 2026-10-21

- Parent: `N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition`
- Decision proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Final integration decision: `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
- Trigger: `N-04G-23A-R` Complete / valid FAIL / no candidate selected
- Priority: **P0**
- Status: **Complete / Architecture Accepted**
- Completed: **G-23A-E1〜E7**
- Current next task: **G-23B — Stage 1 Grounded Content Planner Contract**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **NEXT**

## 1. Goal

G-23A/G-23A-Rで明らかになったAtomicity / Role Judgeの不安定性に対し、broad joint Judgeへ依存せず、structural / deterministic / residual semanticへ責務を分解する。

本Taskは設計Taskでありproduction実装は行わない。

## 2. Task chain

```text
G-23A-E1 47-Gold Responsibility Mapping                 Complete
  ↓
G-23A-E2 v4 V2 Responsibility Boundary Design           Complete
  ↓
G-23A-E3 Structured Proposition Contract Design          Complete
  ↓
G-23A-E4 Role Provenance / Compatibility Matrix Design  Complete
  ↓
G-23A-E5 Residual Classifier Scope / Evaluation Design  Complete
  ↓
G-23A-E6 47-Gold Desk Replay / Coverage Analysis        Complete
  ↓
G-23A-E7 Integration Decision / G-23B Unblock Review    Complete / Accepted
```

## 3. E1 — Responsibility Mapping

Deliverable: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
TOTAL                    47
Required                 41
Optional                  6
Critical                 33
Critical without owner    0
Gold label changes        0
```

## 4. E2 — v4 V2 Boundary

Deliverable: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

```text
V2-S Structural Proposition Gate
  ↓
V2-P Role Provenance Normalization
  ↓
V2-D Deterministic Compatibility Gate
  ↓ PASS only
V2-R-A Residual Atomicity if required
  ↓ ATOMIC only
V2-R-C Residual Content Type if required
  ↓ compatible only
V3+ Support / Derivation
```

Earlier FAIL/INDETERMINATE cannot be overridden by later positive verdicts.

## 5. E3 — Structured Proposition Contract

Deliverable: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

Selected: **Option B — Semi-structured proposition record**.

Key rules:

- application-owned envelope/path/proposition identity;
- one authoritative `claim_text` per candidate;
- source fact uses `support_refs[]`;
- interpretation uses certified `premise_fact_ids[]`;
- support/premise bindings do not coexist;
- candidate / validation / certification are separate artifacts;
- model-authored free text is not Atomic merely because schema-valid;
- no silent post-hoc atomization.

## 6. E4 — Role Provenance / Compatibility Matrix

Deliverables:

- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `benchmark/n04g23ae-role-compatibility-v1.json`

Path authority:

```text
stage1_fact_candidate             -> source_fact
certified_fact_materialization    -> source_fact
stage2_interpretation_candidate   -> interpretation
stage2_creative_candidate         -> creative_addition
system_context_limit              -> context_limit
```

Known purpose/presentation/binding/ownership mismatch is deterministic `POLICY_FAIL`. Model-authored `semantic_role` is not authority. Model-authored `stylistic_expression` remains forbidden.

## 7. E5 — Residual Classifier Design

Deliverable: `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`

Residual work is split:

```text
V2-R-A Residual Atomicity
  ATOMIC / NON_ATOMIC / AMBIGUOUS

V2-R-C Residual Content Type
  SOURCE_FACT_CONTENT
  INTERPRETATION_CONTENT
  CREATIVE_CONTENT
  CONTEXT_LIMIT_CONTENT
  MIXED_CONTENT
  AMBIGUOUS
```

Expected role/purpose/presentation are hidden from classifier input; observed content type is compared with E4 normalized role afterward.

Safety selection policy:

```text
Atomicity critical false-pass = 0
Content critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS/UNAVAILABLE = fail-closed
all candidates fail -> VALID_FAIL_NO_SELECTION
```

Frozen 47 Gold remains final confirmation control rather than threshold-fitting data.

## 8. E6 — 47-Gold Desk Replay / Coverage Analysis

Status: **Complete / Gate PASS with residual Atomicity risk retained**

Deliverables:

- `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`
- `benchmark/n04g23ae-v4-gate-desk-replay-v1.json`

```text
Total cases                              47
Critical                                 33
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

Broad joint Atomicity/Role Judge is removed from all routes. Content-role classification is narrowed to 11/47 cases, but Atomicity remains the major implementation risk: V2-R-A runs for 42/47 and 25/33 critical invalid fixtures rely on correct Atomicity detection.

## 9. E7 — Integration Decision / G-23B Unblock Review

Status: **Complete / Architecture Accepted / G-23B Unblocked**

Deliverable:

`docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`

Decision:

1. E2-E6 form one coherent authority model without duplicate role authority.
2. Residual Atomicity dependency is a **bounded implementation/benchmark risk**, not an architecture blocker.
3. G-23B can design `stage1_fact_candidate` against the E3/E4 interface without claiming schema proves semantic Atomicity.
4. Concrete Residual classifier selection is mandatory later at `G-25A`.
5. `G-25A = VALID_FAIL_NO_SELECTION` blocks G-26; Gate weakening is prohibited.
6. `G-25B` performs integrated adversarial regression and must PASS before G-26.
7. G-14 no-silent-atomization, fail-closed semantics and zero-critical-FP policy remain protected.

G-23B consumption constraint:

```text
stage1_fact_candidate
  claim_text
  support_refs[] >= 1
  application-owned envelope/path/identity
```

G-23B must not add:

```text
generator-owned authoritative semantic_role
model-owned Atomicity PASS
model-owned certification/support PASS
presentation role on Stage 1 candidate
free-form context_limit path
```

## 10. Downstream classifier execution home

Planning authority:

`docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`

```text
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

The classifier is **not selected by E7**. Architecture acceptance does not imply production readiness.

## 11. Protected boundaries

Do not change without new evidence:

- G-23A Frozen 47 Gold labels/flags
- G-23A-R historical candidate results
- G-14 safety intent
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured contract
- E4 application-owned role provenance
- E5 zero-critical-FP/fail-closed selection policy
- MiniCheck threshold/profile merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 12. Final state

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

## 13. Immediate next task

**N-04G-23B — Stage 1 Grounded Content Planner Contract**
