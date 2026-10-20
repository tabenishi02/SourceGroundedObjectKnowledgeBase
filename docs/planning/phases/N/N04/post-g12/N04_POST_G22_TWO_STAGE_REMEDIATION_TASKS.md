# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-20

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Root-cause investigation: `docs/evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md`
- Gate responsibility redesign proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- G-23A-E task breakdown: `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

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
G-23A-E Gate Responsibility Decomposition           NEXT
  ├─ E1 47-Gold Responsibility Mapping
  ├─ E2 v4 V2 Responsibility Boundary
  ├─ E3 Structured Proposition Contract
  ├─ E4 Role Provenance / Compatibility Matrix
  ├─ E5 Residual Classifier Evaluation Design
  ├─ E6 47-Gold Desk Replay
  └─ E7 Integration / Unblock Review
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

---

## 2. Task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | **Complete / Architecture Accepted** | 2段階LLM生成をv4方針として採用 |
| N-04G-23A | P0 | **Complete / valid benchmark; engineering PASS** | Atomicity / Role Gold SetでPhi-4 prompt/model問題を診断 |
| N-04G-23A-R | P0 | **Complete / valid FAIL / no candidate selected** | frozen Gold/Gateで代替judge候補を評価 |
| N-04G-23A-E | P0 | **Planned / NEXT** | Atomicity / Role Gateをstructural / deterministic / residual semanticへ責務分解 |
| N-04G-23A-E1 | P0 | **NEXT** | 47 Gold全件のresponsibility mapping |
| N-04G-23A-E2 | P0 | Planned | v4 V2責務境界 / validation order / authority設計 |
| N-04G-23A-E3 | P0 | Planned | Structured Proposition intermediate contract設計 |
| N-04G-23A-E4 | P0 | Planned | application-owned role provenance / deterministic compatibility matrix設計 |
| N-04G-23A-E5 | P0 | Planned | residual semantic classifierのscope / dataset / evaluation設計 |
| N-04G-23A-E6 | P0 | Planned | 同じ47 Goldでdesk replay / architecture coverage分析 |
| N-04G-23A-E7 | P0 | Planned | integration decision / G-23B unblock review |
| N-04G-23B | P0 | **Blocked by G-23A-E** | Stage 1 `Grounded Content Planner` schema / prompt / responsibility設計 |
| N-04G-23C | P0 | Planned | Certification boundary / `Certified Content` contract設計 |
| N-04G-23D | P0 | Planned | Stage 2 `Presentation Generator` schema / binding / responsibility設計 |
| N-04G-23E | P0 | Planned | presentation-role schema capability + stage-local retry feedback設計 |
| N-04G-23F | P0 | Planned | v4統合設計、migration、evidence、formal acceptance contractをFreeze |
| N-04G-24 | P0 | Blocked by G-23F | Frozen v4 implementation |
| N-04G-25 | P0 | Blocked by G-24 | dev benchmark / adversarial / regression / engineering Gate |
| N-04G-26 | P0 | Blocked by G-25 | Reference Workstation v4 harness/runtime Freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

---

## 3. G-23A / G-23A-R diagnosis retained

G-23A run `20261020T151126+0900`:

- 47 Gold cases / 41 required / 6 optional
- exact G-22 prompt provenance verified
- prompt clarification / paraphrase / split-call profiles all failed frozen Safety or Required-valid Gates
- Phi-4 insufficient under tested formulations

G-23A-R run `20261020T180929+0900`:

- Qwen3.5 runtime-incompatible before Gold
- Ministral 3 8B Primary FAIL
- Gemma 4 12B Primary FAIL
- Mistral Small 3.2 24B Primary FAIL
- Primary PASS none; Secondary not run
- selector `VALID_FAIL_NO_SELECTION`
- engineering PASS

Conclusion: do not keep adding general-purpose judge candidates under the same old responsibility contract. Redesign the responsibility boundary first.

---

## 4. N-04G-23A-E — Gate Responsibility Decomposition

Authority:

- `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`

Target design direction:

```text
Atomicity
  primary authority -> structured proposition invariant
  residual protection -> compound-risk / bounded semantic check

Semantic Role
  provenance -> application/stage-owned
  compatibility -> deterministic policy matrix
  residual content type -> narrow classifier

Uncertainty
  -> fail closed
```

This task does not implement production code and does not change the frozen 47 Gold labels/Gates.

### Required subtask sequence

1. `G-23A-E1` — 47-Gold Responsibility Mapping
2. `G-23A-E2` — v4 V2 Responsibility Boundary Design
3. `G-23A-E3` — Structured Proposition Contract Design
4. `G-23A-E4` — Role Provenance / Compatibility Matrix Design
5. `G-23A-E5` — Residual Classifier Scope / Evaluation Design
6. `G-23A-E6` — 47-Gold Desk Replay / Coverage Analysis
7. `G-23A-E7` — Integration Decision / G-23B Unblock Review

G-23A-E7でArchitecture Acceptedになった場合のみG-23BをNEXTへ移す。

---

## 5. N-04G-23B — Stage 1 Grounded Content Planner

Blocked until G-23A-E acceptance.

After unblock, define:

```text
sgokb.grounded-content-plan.v1
```

Required design topics:

- exact input from Grounded Context
- context fingerprint
- G-23A-Eで選定したStructured Proposition representation
- support_refs
- interpretation premise slots
- presentation allowance
- material-awareness without final prose generation
- GOOD/BAD prompt examples
- exact/minimal Context wording preference
- Stage 1 retry contract
- Stage 1 evidence tree

Stage 1 must not produce final rendered prose.

---

## 6. N-04G-23C — Certification / Certified Content

Define:

```text
sgokb.certified-content.v1
```

Certification path must consume the G-23A-E responsibility model rather than restoring the old all-in-one judge.

Required design topics:

- fact/proposition ID stability
- source/support evidence binding
- structural/deterministic/residual verdict provenance
- context fingerprint binding
- rejection/indeterminate representation
- material coverage calculation before Stage 2
- no silent partial salvage that changes proposition meaning

---

## 7. N-04G-23D — Stage 2 Presentation Generator

Stage 2 primary input is `Certified Content`, not raw Grounded Context.

Required design topics:

- certified fact selection/order
- source_fact binding method
- interpretation premise binding
- creative allowance
- block/presentation planning
- final output schema compatibility/versioning
- deterministic text materialization candidate
- Stage 2 retry contract
- no new source-world fact generation

Preferred source-fact binding candidate:

```text
Stage 2 emits certified_fact_id
  ↓
application deterministically materializes fact text/support refs
```

Compare against free-text copy + deterministic equality/binding validation before Freeze.

---

## 8. N-04G-23E — Provider schema / Retry

### Schema probe

Reference WorkstationでLM Studio / llama.cpp structured outputが以下を実際に強制できるか確認する。

- contains
- minContains
- maxContains
- role cardinality

If supported:
- duplicate presentation roleをprovider schema側でも禁止する。

If unsupported:
- Acceptanceを緩めずStage 2 planning + V0 deterministic validationでrejectする。

### Retry feedback

Stage-local feedbackへ最低限追加する。

```text
failed_stage
failure_code
unit/fact ID
failed unit text
support/certified IDs
expected_rule
repair_directive
```

Stage 1 failureでStage 2をretryしない。
Stage 2 presentation failureでStage 1 certified contentを再生成しない。

---

## 9. N-04G-23F — v4 Design Freeze

G-23A-E〜G-23E完了後にのみFreezeする。

Freeze candidate must define:

- Stage 1 schema/prompt/hash
- Structured Proposition schema/hash
- role provenance / deterministic policy artifact/hash
- residual classifier contract/model identity if used
- certification composition
- MiniCheck identity/threshold or justified replacement evidence
- Certified Content schema
- Stage 2 schema/prompt/hash
- provider structured-output profile
- retry policy
- Material / terminal / render contract
- evidence tree
- runtime identities
- Reference Workstation acceptance procedure

Historical v3 artifacts are not mutated.

---

## 10. N-04G-24 — Implementation

Implement only after G-23F Freeze.

Expected implementation boundaries:

- GroundedContentPlanner adapter/application boundary
- Structured Proposition parser/schema
- structural/deterministic Gate
- residual classifier boundary if selected
- certification orchestrator
- CertifiedContent model
- PresentationGenerator adapter/application boundary
- stage-local failure controller
- final validation integration
- backward/historical v3 test preservation

No implementation-driven redesign without reopening G-23F explicitly.

---

## 11. N-04G-25 — Development verification

Before formal harness Freeze, run:

- Stage 1 proposition benchmark
- G-23A 47-Gold regression under new responsibility mapping
- unsupported proposition adversarial corpus
- deterministic role-policy regression
- residual classifier family-holdout evaluation if used
- Stage 2 no-new-fact regression
- duplicate role regression
- interpretation premise regression
- retry localization regression
- Material coverage regression
- G-12 historical replay
- G-20 verifier regression
- full pytest
- repository-wide Ruff
- git diff --check

Formal rubric must be predetermined before Reference Workstation acceptance.

---

## 12. N-04G-26 / G-27

G-26 freezes exact v4 Reference Workstation identities, prompts/schemas/policies/corpora/evidence layout.

G-27 re-runs the same three representative AI use cases under Frozen v4 conditions.

Only G-27 overall PASS may move:

```text
N-04 -> Complete
N-05 -> unblocked
```

A valid formal FAIL remains a FAIL; do not tune prompt/model/schema/policy/rubric inside the formal run.

---

## 13. Protected boundaries

Without new failure evidence, do not change:

- Object / Version identity
- Source / Evidence / Provenance
- canonical DB
- MCP read-only boundary
- Retrieval / Similarity
- Context Builder selection/budget
- N-03 dataset
- G-12/G-20/G-20R/G-21/G-22/G-23A/G-23A-R historical evidence
- G-23A 47 Gold labels/required/critical flags merely to improve acceptance
- MiniCheck threshold merely to improve acceptance rate
- unsupported rendered claim prohibition
- accepted role escape prohibition
- fail-closed semantics
- G-23 two-stage architecture unless new evidence explicitly requires reopening it

---

## 14. Immediate next task

**N-04G-23A-E1 — 47-Gold Responsibility Mapping**

全47 caseを `STRUCTURAL / DETERMINISTIC_POLICY / RESIDUAL_SEMANTIC / COMBINED / OPTIONAL_AMBIGUOUS` に分類し、primary owner / secondary guard / expected v4 actionを定義する。

このmappingを先に行うことで、後続E2〜E5の設計が特定の都合の良いexampleだけに最適化されることを防ぐ。
