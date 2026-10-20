# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-20

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Gate responsibility redesign: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- E1 mapping: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
- E2 boundary: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- E3 proposition contract: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- E4 role matrix: `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- E5 classifier plan: `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
- E6 replay: `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**

## 1. Remediation chain

```text
G-22 valid formal FAIL
  ↓
G-23 Two-stage architecture decision                 Accepted
  ↓
G-23A Atomicity / Role Gold Benchmark               Complete / Phi-4 insufficient
  ↓
G-23A-R Judge Candidate Evaluation                  Complete / valid FAIL / no selection
  ↓
G-23A-E Gate Responsibility Decomposition           In Progress
  ├─ E1 47-Gold Responsibility Mapping              Complete
  ├─ E2 v4 V2 Responsibility Boundary               Complete
  ├─ E3 Structured Proposition Contract             Complete
  ├─ E4 Role Provenance / Compatibility Matrix      Complete
  ├─ E5 Residual Classifier Evaluation Design       Complete
  ├─ E6 47-Gold Desk Replay                         Complete / PASS with residual risk
  └─ E7 Integration / Unblock Review                NEXT
  ↓ ACCEPTED only
G-23B Stage 1 Grounded Content Planner contract     blocked by G-23A-E
  ↓
G-23C Certification / Certified Content contract
  ↓
G-23D Stage 2 Presentation Generator contract
  ↓
G-23E Provider schema + stage-local retry design
  ↓
G-23F v4 design integration / Design Freeze
  ↓
G-24 v4 implementation
  ↓
G-25 dev benchmark / adversarial regression
  ↓
G-26 Reference Workstation v4 harness freeze
  ↓
G-27 Formal v4 Re-Acceptance
  ↓ PASS only
N-04 Complete
  ↓
N-05 unblocked
```

Historical G-18/G-21/G-22 artifacts remain immutable evidence.

## 2. Current task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | Complete / Architecture Accepted | 2-stage generation architecture |
| N-04G-23A | P0 | Complete / valid benchmark | diagnose Atomicity / Role judge |
| N-04G-23A-R | P0 | Complete / valid FAIL / no candidate selected | alternate judge evaluation |
| N-04G-23A-E | P0 | **In Progress** | decompose Gate responsibilities |
| N-04G-23A-E1 | P0 | Complete | 47 Gold responsibility mapping |
| N-04G-23A-E2 | P0 | Complete | V2 authority/order boundary |
| N-04G-23A-E3 | P0 | Complete | Semi-structured Proposition contract |
| N-04G-23A-E4 | P0 | Complete | application-owned role provenance / compatibility matrix |
| N-04G-23A-E5 | P0 | Complete | residual classifier scope/evaluation design |
| N-04G-23A-E6 | P0 | **Complete / Gate PASS with residual Atomicity risk** | 47-Gold desk replay / coverage |
| N-04G-23A-E7 | P0 | **NEXT** | integrated architecture decision / G-23B unblock review |
| N-04G-23B | P0 | Blocked by G-23A-E | Stage 1 Content Planner contract |
| N-04G-23C | P0 | Planned | Certified Content contract |
| N-04G-23D | P0 | Planned | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | Planned | provider schema + stage-local retry |
| N-04G-23F | P0 | Planned | v4 Design Freeze |
| N-04G-24 | P0 | Blocked by G-23F | implementation |
| N-04G-25 | P0 | Blocked by G-24 | dev benchmark/regression |
| N-04G-26 | P0 | Blocked by G-25 | Reference Workstation freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. Integrated E1-E5 architecture

```text
Structured Proposition Candidate
  ↓
V2-S schema/construction
  ↓
V2-P application-owned role provenance
  ↓
V2-D deterministic purpose/presentation/binding compatibility
  ↓ PASS only
V2-R-A narrow Atomicity classification if required
  ↓ ATOMIC only
V2-R-C content-only classification if required
  ↓ role compatibility comparison
V3/V4 support / derivation
```

Key invariants:

- model-authored role is not authority;
- deterministic policy mismatch never goes to an LLM for rescue;
- Atomicity and Content Type are separate tasks;
- expected role/purpose/presentation are not shown to content classifier;
- model-authored free text is not Atomic merely because schema-valid;
- ambiguity/unavailability fail closed;
- support/truth/derivation remain downstream responsibilities;
- no silent post-hoc atomization.

## 4. E6 result

Frozen 47 Gold desk replay:

```text
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

- 33/33 critical invalid fixtures have a fail-closed pre-V3 route.
- broad joint Atomicity/Role Judge is eliminated from the architecture.
- content-role semantic classification is needed for only 11/47 fixtures and 3/33 critical invalid fixtures.
- residual Atomicity remains substantial: V2-R-A runs for 42/47 and 25/33 critical invalid fixtures depend on correct Atomicity classification.
- E6 is architecture coverage, not classifier performance evidence.

Machine-readable replay:

`benchmark/n04g23ae-v4-gate-desk-replay-v1.json`

## 5. E7 immediate scope

E7 must issue a formal integrated design decision.

Review questions:

1. Is the remaining V2-R-A dependency a bounded implementation/benchmark risk, or an architecture blocker?
2. Can G-23B consume the E3 proposition contract without reintroducing generator-owned semantic-role authority?
3. Can Stage 1 target one-proposition candidates while keeping Residual Atomicity mandatory for model-authored free text?
4. Is there an explicit later execution home for E5 classifier dataset construction, benchmark, selection and freeze before G-27?
5. Can G-23C/D preserve Certified Content binding without adding a free-form Stage 2 source-fact regeneration path?
6. Are G-14 and fail-closed/zero-critical-FP policies preserved end to end?

If E7 accepts:

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

Acceptance does not mean a classifier has been selected or N-04 has passed.

If E7 rejects, G-23B remains blocked and an explicit remediation task is required.

## 6. Protected boundaries

Do not change without new evidence:

- Frozen 47 Gold labels/flags and G-23A/G-23A-R evidence
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured proposition contract unless E7 explicitly rejects it
- E4 application-owned role provenance
- E5 zero-critical-FP/fail-closed classifier selection policy
- MiniCheck threshold/profile merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 7. Immediate next task

**N-04G-23A-E7 — Integration Decision / G-23B Unblock Review**
