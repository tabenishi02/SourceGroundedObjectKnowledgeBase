# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Primary next-chat entry: `docs/planning/phases/N/N04/post-g12/N04G23C_NEXT_CHAT_HANDOFF.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23: **Complete / Architecture Accepted**
- G-23A: **Complete / Phi-4 insufficient**
- G-23A-R: **Complete / valid FAIL / no candidate selected**
- G-23A-E: **Complete / Architecture Accepted**
- G-23A-E1〜E7: **Complete**
- G-23B: **Complete / Contract Accepted**
- Current task: **N-04G-23C — Certification / Certified Content Contract**

## Read first

0. `docs/planning/phases/N/N04/post-g12/N04G23C_NEXT_CHAT_HANDOFF.md`
1. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
2. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
3. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
4. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
5. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
6. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
7. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
8. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
9. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

## Current architecture

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

No downstream positive verdict may rescue an earlier FAIL/INDETERMINATE.

## G-23B result

G-23B is **Complete / Contract Accepted**.

Normative Decision:

`docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`

Stage 1 model response is intentionally minimal:

```json
{
  "candidates": [
    {
      "claim_text": "...",
      "support_refs": ["K3"]
    }
  ]
}
```

Application owns and constructs:

```text
request/candidate contract identity
request_id
context_fingerprint
purpose
stage = stage1
path_provenance = stage1_fact_candidate
attempt
proposition_id
candidate_index
retry lineage
```

Important decisions:

- model-authored `semantic_role` is not present/authoritative;
- Stage 1 has no presentation role;
- non-empty candidate requires `support_refs[] >= 1`;
- model-selected refs are not entailment/support PASS;
- schema-valid free text does not prove Atomicity;
- optional semantic anchors are excluded from v1;
- `candidates: []` is allowed and is not a model-owned context-limit verdict;
- failed candidate content is immutable during validation;
- retry creates a new proposition ID linked by application-owned lineage;
- concrete residual classifier selection remains G-25A.

## G-23C authority boundary

G-23C designs the application/validator-owned **Certification / Certified Content contract** only.

It must preserve:

```text
Candidate artifact
  != Validation artifact
  != Certified Content artifact
```

Certification may occur only after required Gate PASS.

G-23C should define at least:

1. certification eligibility condition;
2. stable `certified_fact_id` ownership/semantics;
3. binding to immutable Stage 1 proposition identity;
4. certified claim/support/evidence binding;
5. context/request lineage;
6. version/digest/replay identity;
7. Stage 2 input boundary;
8. non-certification/failure semantics.

## G-23C must not reintroduce

```text
model-owned certification status
model-owned support/entailment PASS
generator-declared semantic role authority
silent candidate rewrite
new source-world fact generation during certification
```

## Residual classifier execution is later

Concrete V2-R-A/V2-R-C selection is not part of G-23C.

```text
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

If all candidates fail G-25A, result is `VALID_FAIL_NO_SELECTION` and G-26 remains blocked.

## Protected boundaries

Do not change without new evidence:

- Frozen 47 Gold labels / required / critical flags
- G-23A/G-23A-R historical results
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage generation decision
- E2 authority order
- E3 Semi-structured proposition contract
- E4 application-owned provenance / deterministic policy
- E5 zero-critical-FP / fail-closed selection policy
- G-23B minimal Stage 1 payload / application envelope ownership
- MiniCheck threshold/profile merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## Immediate next task

**N-04G-23C — Certification / Certified Content Contract**
