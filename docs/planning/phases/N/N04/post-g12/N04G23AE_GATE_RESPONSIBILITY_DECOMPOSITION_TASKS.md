# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition Tasks

更新日: 2026-10-20

- Parent: `N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition`
- Decision proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Trigger: `N-04G-23A-R` Complete / valid FAIL / no candidate selected
- Priority: **P0**
- Status: **In Progress**
- Completed: **G-23A-E1, E2, E3, E4, E5, E6**
- Current task: **G-23A-E7 — Integration Decision / G-23B Unblock Review**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E7 acceptance**

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
G-23A-E7 Integration Decision / G-23B Unblock Review    NEXT
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
  ↓
V2-R Residual Semantic Gate if required
  ↓
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

Safety selection policy remains zero-tolerance:

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

Aggregate replay:

```text
Total cases                              47
Required                                 41
Optional                                  6
Critical                                 33

V2-D deterministic POLICY_FAIL            5
V2-R-A invoked                            42
  ATOMIC                                  11
  NON_ATOMIC                              27
  AMBIGUOUS                                4
V2-R-C invoked                            11
  compatible                               8
  semantic mismatch                        3

Expected V2 PASS                           8
Expected V2 FAIL                          35
Expected V2 INDETERMINATE                  4
```

Critical coverage:

```text
Critical total                            33
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

Interpretation:

- broad joint Atomicity/Role Judge is removed from all 47 routes;
- content-role probabilistic classification is needed for only 11/47 cases and only 3/33 critical invalid cases;
- all 33 critical invalid fixtures have a pre-V3 fail path;
- however V2-R-A still runs for 42/47 and 25/33 critical invalid fixtures depend on correct Atomicity classification;
- E6 therefore proves responsibility decomposition/coverage, not production classifier accuracy.

E6 Gate: **PASS with residual Atomicity classifier risk retained**.

## 9. G-23A-E7 — Integration Decision / G-23B Unblock Review

Status: **NEXT**

Acceptance checklist:

- [x] 47/47 responsibility mapping complete
- [x] v4 V2 authority/order fixed
- [x] Structured Proposition contract selected
- [x] role provenance model selected
- [x] deterministic compatibility matrix fixed
- [x] residual classifier scope bounded
- [x] 47-Gold desk replay complete
- [x] every critical case has fail-closed authority path in desk replay
- [x] G-14 no-silent-post-hoc-atomization preserved
- [x] zero-tolerance critical false-pass policy preserved
- [x] historical evidence unchanged
- [ ] decide whether residual Atomicity dependency is an architecture blocker or bounded implementation risk
- [ ] confirm G-23B can consume E3/E4 without duplicate role authority
- [ ] confirm classifier benchmark/selection has an explicit later execution home before formal acceptance
- [ ] issue integrated accept/reject decision

If accepted:

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

If rejected, G-23B remains blocked and E7 must create an explicit remediation task.

## 10. Protected boundaries

Do not change without new evidence:

- G-23A Frozen 47 Gold labels/flags
- G-23A-R historical candidate results
- G-14 safety intent
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured contract unless E7 explicitly rejects it
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

## 11. Immediate next task

**N-04G-23A-E7 — Integration Decision / G-23B Unblock Review**
