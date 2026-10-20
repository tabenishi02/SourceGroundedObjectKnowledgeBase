# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-20

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Root-cause investigation: `docs/evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Remediation chain

```text
G-22 valid formal FAIL
  ↓
G-23 Two-stage architecture decision                 Accepted
  ↓
G-23A Atomicity / Role Gold Benchmark               NEXT
  ↓
G-23B Stage 1 Grounded Content Planner contract
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
| N-04G-23A | P0 | **NEXT** | Atomicity / Role Gold Setを作成しPhi-4 prompt/model問題を分離 |
| N-04G-23B | P0 | Planned | Stage 1 `Grounded Content Planner` schema / prompt / responsibility設計 |
| N-04G-23C | P0 | Planned | Certification boundary / `Certified Content` contract設計 |
| N-04G-23D | P0 | Planned | Stage 2 `Presentation Generator` schema / binding / responsibility設計 |
| N-04G-23E | P0 | Planned | presentation-role schema capability + stage-local retry feedback設計 |
| N-04G-23F | P0 | Planned | v4統合設計、migration、evidence、formal acceptance contractをFreeze |
| N-04G-24 | P0 | Blocked by G-23F | Frozen v4 implementation |
| N-04G-25 | P0 | Blocked by G-24 | dev benchmark / adversarial / regression / engineering Gate |
| N-04G-26 | P0 | Blocked by G-25 | Reference Workstation v4 harness/runtime Freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

---

## 3. N-04G-23A — Atomicity / Role Gold Benchmark

### Goal

G-22 Case 2で観測された`role-INDETERMINATE`が、Phi-4 model能力、prompt/task定義、atomicity+role joint callのどこに起因するかを分離する。

### Required corpus

- G-22 actual units
- G-12 / G-20 adversarial units
- franchise knowledge不要のsynthetic neutral controls

### Buckets

Atomicity:

- valid one-proposition direct restatement
- valid faithful paraphrase
- conjunction with two propositions
- supported fact + unsupported addition
- fact + inference

Role:

- valid source_fact
- valid interpretation
- valid creative_addition
- interpretation mislabeled as source_fact
- creative invention mislabeled as source_fact
- source-world assertion smuggled into creative

### Comparison order

1. exact G-22 Phi-4 payload replay
2. same Phi-4 + clarified prompt / examples
3. same Phi-4 + atomicity and role separate calls
4. only if still inadequate: alternative judge candidates

### Metrics

```text
critical false-pass
valid-unit false-reject
INDETERMINATE rate
confusion matrix
same-input repeatability
prompt-paraphrase stability
latency / token cost
```

### Gate

- critical false-pass must remain 0 on frozen critical/adversarial set
- valid-unit false-reject must materially improve over G-22 baseline
- prompt/model identity and exact payload must be reproducible

No Gate relaxation after observing candidate results.

---

## 4. N-04G-23B — Stage 1 Grounded Content Planner

Define:

```text
sgokb.grounded-content-plan.v1
```

Required design topics:

- exact input from Grounded Context
- context fingerprint
- atomic source fact representation
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

## 5. N-04G-23C — Certification / Certified Content

Define:

```text
sgokb.certified-content.v1
```

Required path:

```text
Reference Integrity
→ Atomicity
→ Role Boundary
→ Deterministic Support
→ MiniCheck if unresolved
→ Independent Source Fact Judge
→ Certified Fact
```

Required design topics:

- fact ID stability inside one request
- source/support evidence binding
- verifier/judge provenance
- context fingerprint binding
- rejection/indeterminate representation
- material coverage calculation before Stage 2
- no silent partial salvage that changes proposition meaning

---

## 6. N-04G-23D — Stage 2 Presentation Generator

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

## 7. N-04G-23E — Provider schema / Retry

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

## 8. N-04G-23F — v4 Design Freeze

G-23A〜E完了後にのみFreezeする。

Freeze candidate must define:

- Stage 1 schema/prompt/hash
- Atomicity judge prompt/hash
- Role judge prompt/hash
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

## 9. N-04G-24 — Implementation

Implement only after G-23F Freeze.

Expected implementation boundaries:

- GroundedContentPlanner adapter/application boundary
- ContentPlan parser/schema
- certification orchestrator
- CertifiedContent model
- PresentationGenerator adapter/application boundary
- stage-local failure controller
- final validation integration
- backward/historical v3 test preservation

No implementation-driven redesign without reopening G-23F explicitly.

---

## 10. N-04G-25 — Development verification

Before formal harness Freeze, run:

- Stage 1 gold benchmark
- Atomicity/Role gold benchmark
- unsupported proposition adversarial corpus
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

## 11. N-04G-26 — Reference Workstation v4 Freeze

Prepare exact:

- generator model/load profile
- judge model(s)/load profiles
- MiniCheck runtime
- prompts and hashes
- schema hashes
- corpus hashes
- MCP / Harrier / Qdrant identities
- canonical DB identity
- evidence layout

All required local/offline reproduction Gates must PASS before G-27.

---

## 12. N-04G-27 — Formal v4 Re-Acceptance

Re-run the same three representative AI use cases under Frozen v4 conditions.

Overall PASS requires all three cases to PASS plus all safety/engineering Gates.

A valid formal FAIL remains a FAIL; do not modify prompt, model, schema, threshold or rubric inside the same formal run to obtain PASS.

Only G-27 overall PASS can move:

```text
N-04 -> Complete
N-05 -> unblocked
```

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
- G-12/G-20/G-20R/G-21/G-22 historical evidence
- MiniCheck threshold merely to improve acceptance rate
- unsupported rendered claim prohibition
- accepted role escape prohibition
- fail-closed semantics

---

## 14. Immediate next task

**N-04G-23A — Atomicity / Role Gold Benchmark**

This must be completed before Stage 1/Stage 2 prompt and judge design is Frozen, because the benchmark determines whether Phi-4 can be retained with prompt changes, requires split calls, or must be replaced.
