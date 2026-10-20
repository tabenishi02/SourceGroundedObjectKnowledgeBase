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
- E4 machine-readable matrix: `benchmark/n04g23ae-role-compatibility-v1.json`
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
  ├─ E5 Residual Classifier Evaluation Design       NEXT
  ├─ E6 47-Gold Desk Replay                         Planned
  └─ E7 Integration / Unblock Review                Planned
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

## 2. Task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | Complete / Architecture Accepted | 2-stage LLM generation adopted for v4 |
| N-04G-23A | P0 | Complete / valid benchmark | diagnose Atomicity / Role judge |
| N-04G-23A-R | P0 | Complete / valid FAIL / no candidate selected | evaluate alternate judge candidates |
| N-04G-23A-E | P0 | **In Progress** | decompose Gate responsibilities |
| N-04G-23A-E1 | P0 | Complete | 47 Gold responsibility mapping |
| N-04G-23A-E2 | P0 | Complete | V2 authority/order boundary |
| N-04G-23A-E3 | P0 | Complete | Semi-structured Proposition contract |
| N-04G-23A-E4 | P0 | **Complete** | application-owned role provenance / deterministic compatibility matrix |
| N-04G-23A-E5 | P0 | **NEXT** | residual classifier scope/evaluation |
| N-04G-23A-E6 | P0 | Planned | 47-Gold desk replay / coverage |
| N-04G-23A-E7 | P0 | Planned | integration / G-23B unblock review |
| N-04G-23B | P0 | Blocked by G-23A-E | Stage 1 Content Planner contract |
| N-04G-23C | P0 | Planned | Certified Content contract |
| N-04G-23D | P0 | Planned | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | Planned | provider schema + stage-local retry |
| N-04G-23F | P0 | Planned | v4 Design Freeze |
| N-04G-24 | P0 | Blocked by G-23F | implementation |
| N-04G-25 | P0 | Blocked by G-24 | dev benchmark/regression |
| N-04G-26 | P0 | Blocked by G-25 | Reference Workstation freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. E1 result

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

## 4. E2 result

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

Earlier structural/policy failure cannot be overridden by later semantic/support PASS.

## 5. E3 result

Selected contract family: **Option B — Semi-structured proposition record**.

```text
Application-owned envelope
  + path-discriminated payload
  + one authoritative claim text
  + path-specific support/premise binding
  + optional non-authoritative semantic anchors
```

Candidate / Validation / Certified Contentは別artifact。model-authored free textはschemaだけでatomic PASSとしない。

## 6. E4 result

Application-owned path provenanceをnormalized roleのdeterministic authorityにした。

```text
stage1_fact_candidate
  -> source_fact

certified_fact_materialization
  -> source_fact

stage2_interpretation_candidate
  -> interpretation

stage2_creative_candidate
  -> creative_addition

system_context_limit
  -> context_limit
```

Purpose policy:

- source_fact: roleplay / comparison / creativeで許可
- interpretation: 3用途でdeterministic banしないがResidual semantic + derivation validation必須
- creative_addition: creativeのみ許可
- context_limit: 3用途で許可、system/application-owned and exclusive

Presentation/binding policy:

- Stage 1 fact candidateはpresentationなし
- Certified fact materializationのみ`main`
- Interpretationは`interpretation` presentation + `premise_fact_ids[]`
- Creativeは`creative` presentation、support/premise grounding bindingなし
- Context limitは`context_limit` exclusive
- model-authored `stylistic_expression`は再導入しない

Policy PASSはcontent semantic proofではない。model-authored fact / interpretation / creativeはE5で定義するV2-Rを必要とする。

## 7. E5 immediate scope

E5はE1〜E4でstructural/deterministicへ移せなかった自然言語意味境界だけをV2-Rへ限定する。

Required decisions:

1. residual semantic taxonomy
2. atomicity residual checkとrole/content classifierの分離可否
3. classifier input最小化
4. expected roleをinputへ見せるかcontent-only classification後比較するか
5. dataset expansion beyond 47 Gold
6. minimal pairs / paraphrases / role swaps / purpose swaps / compound-split fixtures
7. pattern-family holdout
8. bounded LLM / encoder / cross-encoder / cascade比較
9. abstention/ambiguity fail-closed semantics
10. zero critical false-pass Gate
11. Reference Workstation runtime候補

Deliverable:

`docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`

## 8. Protected boundaries

Do not change without new evidence:

- frozen 47 Gold labels/flags and G-23A/G-23A-R evidence
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured proposition contract
- E4 application-owned role provenance
- MiniCheck threshold merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 9. Immediate next task

**N-04G-23A-E5 — Residual Classifier Scope / Evaluation Design**
