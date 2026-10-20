# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition Tasks

更新日: 2026-10-20

- Parent: `N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition`
- Decision proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Trigger: `N-04G-23A-R` Complete / valid FAIL / no candidate selected
- Priority: **P0**
- Status: **In Progress**
- Completed: **G-23A-E1, G-23A-E2, G-23A-E3, G-23A-E4**
- Current task: **G-23A-E5 — Residual Classifier Scope / Evaluation Design**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E acceptance**

## 1. Goal

G-23A / G-23A-Rで明らかになったAtomicity / Role Judgeの不安定性に対し、Judge model追加ではなく責務境界そのものを再設計する。

設計作業の完了条件:

1. 47 Gold各caseの責務owner
2. Atomicityのstructural authorityとresidual checkの境界
3. Structured Proposition intermediate contract
4. application-owned role provenance
5. deterministic role/purpose/presentation compatibility matrix
6. residual semantic classifierの必要範囲
7. 47 Gold desk replay
8. G-23Bが参照できる統合Decision

本Taskではproduction実装を行わない。

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
G-23A-E5 Residual Classifier Scope / Evaluation Design  NEXT
  ↓
G-23A-E6 47-Gold Desk Replay / Coverage Analysis
  ↓
G-23A-E7 Integration Decision / G-23B Unblock Review
```

E1〜E6の結果を見て設計を後付けで緩めない。必要な設計変更が生じた場合は変更理由と影響する前工程を明記して再レビューする。

## 3. G-23A-E1 — 47-Gold Responsibility Mapping

Status: **Complete**

Deliverable: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`

Result:

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

## 4. G-23A-E2 — v4 V2 Responsibility Boundary Design

Status: **Complete**

Deliverable: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

Normative decomposition:

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

Hard structural/policy failureは後段classifier/supportでoverride不可。model-authored content typeがconstructionだけで証明できない場合はV2-R必須。

## 5. G-23A-E3 — Structured Proposition Contract Design

Status: **Complete / Option B Semi-structured selected**

Deliverable: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

Decision:

```text
Application-owned envelope
  + path-discriminated candidate payload
  + one authoritative proposition text
  + path-specific support/premise binding
  + optional non-authoritative semantic anchors
```

Candidate / Validation / Certified Contentを分離する。model-authored `semantic_role`、validation status、certification statusはauthority fieldにしない。

V2-S construction states:

```text
PASS_BY_CONSTRUCTION
REVIEW_REQUIRED
FAIL
```

model-authored free textはschemaだけでatomic PASSとせず、原則Residual review対象とする。

## 6. G-23A-E4 — Role Provenance / Compatibility Matrix Design

Status: **Complete**

Deliverables:

- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `benchmark/n04g23ae-role-compatibility-v1.json`

Normative paths:

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

Key decisions:

- path provenanceはapplication-owned。
- unknown/forged pathは`UNRESOLVED_PROVENANCE`。
- `source_fact`はroleplay/comparison/creativeで許容。
- `interpretation`は3用途でdeterministic banしないが、model-authored contentはV2-R/V4I必須。
- `creative_addition`はcreative purposeだけ許可。roleplay/comparisonでは即`POLICY_FAIL`。
- `context_limit`はsystem/application-owned only、terminal responseでexclusive。
- Stage 1 fact candidateはintermediateでpresentationを持たない。
- Certified fact materializationだけ`main` presentationを許可し、modelにsource fact textを再発明させない方向を固定。
- interpretationは`premise_fact_ids[]`必須、raw `support_refs[]`をderivation proofに使わない。
- creative/context-limitはsupport/premise bindingをgrounding proofとして持たない。
- model-authored `stylistic_expression`を再導入しない。
- policy PASSはcontent semantic proofではない。

Deterministic failure categories:

```text
unknown_path_provenance
path_owner_mismatch
path_stage_mismatch
purpose_role_incompatible
presentation_role_incompatible
unexpected_presentation_on_intermediate
missing_support_binding
forbidden_support_binding
missing_premise_binding
forbidden_premise_binding
model_authored_context_limit_forbidden
context_limit_not_exclusive
model_authored_stylistic_expression_forbidden
```

E4 Gate: **PASS**

## 7. G-23A-E5 — Residual Classifier Scope / Evaluation Design

Status: **NEXT**

Purpose:

E1〜E4でstructural/deterministicへ移せなかった自然言語意味境界だけをV2-Rへ限定し、汎用Judge再導入を防ぐ。

Required topics:

1. V2-Rが判定するexact taxonomy
2. residual atomicityとcontent-role classificationを同一classifierにするか分離するか
3. `SOURCE_FACT_CONTENT / INTERPRETATION_CONTENT / CREATIVE_CONTENT / CONTEXT_LIMIT_CONTENT / MIXED_CONTENT / AMBIGUOUS`候補taxonomyの確定
4. classifierへ渡すinput最小化
5. application-owned expected roleをclassifierへ見せるか、content-only classification後に比較するか
6. deterministic policy結果をclassifierがoverrideできない構成
7. datasetを47 Gold以上へ拡張する方法
8. minimal pairs / paraphrase / role-swap / purpose-swap / compound-split fixture
9. pattern-family holdout
10. bounded local LLM / encoder classifier / cross-encoder / deterministic-first cascade比較
11. critical false-pass = 0を維持するevaluation Gate
12. abstention / ambiguityをfail-closedで扱う方法
13. Reference Workstation候補runtimeと再現性

Deliverable:

`docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`

## 8. G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis

Apply E2-E5 model to the same 47 Gold before implementation.

Per case record:

```text
input metadata available?
structural violation detectable?
deterministic policy violation detectable?
residual classifier required?
expected V2 path
historical model error prevented by construction?
remaining uncertainty
```

Deliverable: `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`

## 9. G-23A-E7 — Integration Decision / G-23B Unblock Review

Acceptance checklist:

- [x] 47/47 responsibility mapping complete
- [x] v4 V2 authority/order fixed
- [x] Structured Proposition contract selected
- [x] role provenance model selected
- [x] deterministic compatibility matrix fixed
- [ ] residual classifier scope bounded
- [ ] 47-Gold desk replay complete
- [x] G-14 invariants preserved through E4
- [x] zero-tolerance critical false-pass policy preserved through E4
- [x] historical evidence unchanged
- [x] no silent post-hoc atomization preserved
- [ ] G-23B can consume the integrated contract without duplicate role authority

If accepted:

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

Otherwise G-23B remains blocked.

## 10. Protected boundaries

G-23A-Eでは以下を変更しない。

- G-23A frozen 47 Gold labels/flags
- G-23A-R historical candidate results
- G-14 safety intent
- G-23 two-stage generation decision
- MiniCheck threshold without separate evidence
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 11. Immediate next task

**N-04G-23A-E5 — Residual Classifier Scope / Evaluation Design**

E4でrole provenanceと既知metadata compatibilityをdeterministic化したため、次はそれでも残る自然言語semantic boundaryだけをV2-Rへ限定し、その評価方法を設計する。
