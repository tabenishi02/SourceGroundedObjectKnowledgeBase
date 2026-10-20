# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-20

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Gate responsibility redesign: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- G-23A-E tasks: `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
- E1 mapping: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
- E2 boundary: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
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
  ├─ E3 Structured Proposition Contract             NEXT
  ├─ E4 Role Provenance / Compatibility Matrix      Planned
  ├─ E5 Residual Classifier Evaluation Design       Planned
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

G-18/G-21/G-22のv3 artifact/evidenceはhistorical authorityとして保持し、直接書き換えない。

## 2. Task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | **Complete / Architecture Accepted** | 2段階LLM生成をv4方針として採用 |
| N-04G-23A | P0 | **Complete / valid benchmark** | Atomicity / Role GoldでPhi-4を診断 |
| N-04G-23A-R | P0 | **Complete / valid FAIL / no candidate selected** | frozen Gold/Gateで代替judge候補評価 |
| N-04G-23A-E | P0 | **In Progress** | Gateをstructural / deterministic / residual semanticへ責務分解 |
| N-04G-23A-E1 | P0 | **Complete** | 47 Gold全件のresponsibility mapping |
| N-04G-23A-E2 | P0 | **Complete** | v4 V2 responsibility boundary / authority / order |
| N-04G-23A-E3 | P0 | **NEXT** | Structured Proposition intermediate contract設計 |
| N-04G-23A-E4 | P0 | Planned | application-owned role provenance / deterministic compatibility matrix設計 |
| N-04G-23A-E5 | P0 | Planned | residual semantic classifier scope / dataset / evaluation設計 |
| N-04G-23A-E6 | P0 | Planned | 同じ47 Goldでdesk replay / coverage分析 |
| N-04G-23A-E7 | P0 | Planned | integration decision / G-23B unblock review |
| N-04G-23B | P0 | **Blocked by G-23A-E** | Stage 1 `Grounded Content Planner` contract |
| N-04G-23C | P0 | Planned | Certification / `Certified Content` contract |
| N-04G-23D | P0 | Planned | Stage 2 `Presentation Generator` contract |
| N-04G-23E | P0 | Planned | provider schema capability + stage-local retry |
| N-04G-23F | P0 | Planned | v4 integrated Design Freeze |
| N-04G-24 | P0 | Blocked by G-23F | Frozen v4 implementation |
| N-04G-25 | P0 | Blocked by G-24 | dev benchmark / regression |
| N-04G-26 | P0 | Blocked by G-25 | Reference Workstation v4 Freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. G-23A-E1 result

47 Gold全部を既存Gold変更なしで分類した。

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

## 4. G-23A-E2 result

E2でv4 V2のauthority/orderを固定した。

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

Order:

```text
Structured Proposition Candidate
  ↓
V2-S
  ↓
V2-P
  ↓
V2-D
  ↓
V2-R if required
  ↓
V3+ Support / Derivation
```

Normative rules:

- structural/policy failureは後段classifier/supportでoverride不可。
- role provenanceはapplication/stage pathがauthority。
- known stage/purpose/presentation/premise/support mismatchはdeterministic hard reject。
- compound-risk signalは単独verdictではなくResidual review/retryのtrigger。
- model-authored content typeがconstructionだけで証明できない場合はResidual Semantic必須。
- `MIXED_CONTENT`はFAIL。
- `AMBIGUOUS/INDETERMINATE`はfail-closed。
- V2はtruth/support/entailmentを判定しない。
- retryはfailed proposition本文とauthorityを含むstage-local evidenceを使う。

Deliverable:

`docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

## 5. G-23A-E3 immediate scope

E3はE2の`V2-S`を実体化するStructured Proposition intermediate contractを設計する。

Required decisions:

1. minimal / semi-structured / fully normalizedの比較
2. proposition ID / lifetime / uniqueness
3. stage/path provenance binding
4. text / subject/entity / predicate hint等のrepresentation
5. support_refs / premise_fact_ids
6. purpose / context fingerprint binding
7. certification ownership
8. rejected / ambiguous representation
9. renderingとの分離
10. `V2-S PASS / REVIEW_REQUIRED / FAIL` construction rule
11. どのpathなら`V2-R = NOT_REQUIRED`を許せるか
12. G-14 no-silent-post-hoc-atomizationとの整合

Deliverable:

`docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

## 6. Following G-23A-E tasks

E4: Role Provenance / Compatibility Matrix

- stage1 fact / stage2 interpretation / stage2 creative / system context-limit paths
- normalized role, purpose, presentation, premise/support requirements
- deterministic violations never delegated to classifier merely for convenience

E5: Residual Classifier Evaluation Design

- bounded semantic taxonomy
- dataset expansion beyond 47 Gold
- pattern-family holdout
- compare bounded LLM, encoder/sequence classifier, cross-encoder and deterministic-first cascade

E6: 47-Gold Desk Replay

- apply new responsibility model to same Gold
- measure how many critical decisions are removed from broad probabilistic judge dependence

E7: Integration Decision

- accept/reject G-23A-E
- unblock G-23B only if accepted

## 7. Protected boundaries

Without new evidence, do not change:

- Object / Version identity
- Source / Evidence / Provenance
- canonical DB
- MCP read-only boundary
- Retrieval / Similarity
- Context Builder selection/budget
- N-03 dataset
- G-12/G-20/G-21/G-22/G-23A/G-23A-R historical evidence
- frozen 47 Gold labels/required/critical flags
- MiniCheck threshold merely to improve acceptance
- unsupported rendered claim prohibition
- fail-closed semantics

## 8. Immediate next task

**N-04G-23A-E3 — Structured Proposition Contract Design**

E2でresponsibility boundaryは固定された。次はV2-Sのinput contractとconstruction proofを設計し、どのrecordを機械的にPASS/REVIEW_REQUIRED/FAILへ送るかを確定する。