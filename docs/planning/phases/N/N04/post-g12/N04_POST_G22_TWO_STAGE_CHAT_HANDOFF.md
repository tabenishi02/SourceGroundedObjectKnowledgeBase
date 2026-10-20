# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Primary next-chat entry: `docs/planning/phases/N/N04/post-g12/N04G23D_NEXT_CHAT_HANDOFF.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23: **Complete / Architecture Accepted**
- G-23A: **Complete / Phi-4 insufficient**
- G-23A-R: **Complete / valid FAIL / no candidate selected**
- G-23A-E: **Complete / Architecture Accepted**
- G-23A-E1〜E7: **Complete**
- G-23B: **Complete / Contract Accepted**
- G-23C: **Complete / Contract Accepted**
- Current task: **N-04G-23D — Stage 2 Presentation Generator Contract**

## Read first

0. `docs/planning/phases/N/N04/post-g12/N04G23D_NEXT_CHAT_HANDOFF.md`
1. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
2. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
3. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
4. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
5. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
6. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
7. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
8. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
9. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
10. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

## Current architecture

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidate
  ↓
V2 / V3 / V4 validation
  ↓ PASS only
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
Final validation / Material / Terminal / Render
```

No downstream positive verdict may rescue an earlier FAIL/INDETERMINATE.

## G-23B result

G-23B is **Complete / Contract Accepted**.

Normative Decision:

`docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`

Stage 1 model response remains minimal:

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

Application owns request/candidate metadata, path provenance, identity and retry lineage.

Model-authored role, validation/certification status, Atomicity PASS, support/entailment PASS and Stage 1 presentation role remain prohibited.

## G-23C result

G-23C is **Complete / Contract Accepted**.

Normative Decision:

`docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`

Artifact separation:

```text
Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certification eligibility:

```text
candidate/reference identity valid
AND aggregate V2 PASS
AND source-support aggregate PASS
AND candidate/validation digest bindings match
AND no unresolved FAIL / INDETERMINATE / UNAVAILABLE
```

Important decisions:

- certification is application/validator-owned;
- `certified_fact_id` is application-owned and scoped to one immutable Certified Content artifact;
- it is not a canonical DB Fact identity;
- certified `claim_text` and `support_refs[]` exactly copy the Stage 1 candidate;
- Certification cannot rewrite, atomize, merge support or create new source-world facts;
- Validation Record owns validation verdict/evidence and is referenced by ID/digest;
- one Certified Content artifact cannot mix context fingerprints;
- Stage 2 primary factual authority is Certified Content, not raw Grounded Context;
- Stage 2 interpretation premises reference `certified_fact_id` values;
- exact duplicate minimum handling prevents trivial count inflation without semantic equivalence judging;
- empty Certified Content is audit evidence only, not a model/system context-limit verdict;
- cross-attempt salvage/inclusion is explicitly deferred to G-23E.

## G-23D authority boundary

G-23D designs only the **Stage 2 Presentation Generator contract**.

It must preserve E4 paths:

```text
certified_fact_materialization
  -> source_fact
  -> application-owned
  -> main presentation

stage2_interpretation_candidate
  -> interpretation
  -> model-authored
  -> premise_fact_ids[] >= 1

stage2_creative_candidate
  -> creative_addition
  -> model-authored
  -> creative purpose only

system_context_limit
  -> context_limit
  -> application/system-owned only
```

G-23D must not give the model authority to freely rewrite a Certified Fact and inherit its certification.

Source-fact presentation should use application-owned exact Certified Fact materialization unless an explicitly bounded deterministic surface rule is justified and frozen.

Interpretation may use Certified Fact IDs only as factual premises. Raw K refs or raw Grounded Context must not reopen a factual bypass.

Creative content remains purpose-restricted and may not hide source-world factual claims.

## G-23D should define

At minimum:

1. Stage 2 request envelope.
2. minimal model-facing Certified Content projection.
3. source-fact selection/materialization path.
4. interpretation candidate schema and Certified Fact premise binding.
5. creative candidate schema and purpose restriction.
6. presentation-role/block structure and cardinality.
7. purpose-specific output-kind compatibility.
8. duplicate/escaped presentation prevention.
9. Stage 2 output -> V2/V4I/final-validation handoff.
10. evidence fields needed by G-23E/G-23F/G-26.

Primary task handoff:

`docs/planning/phases/N/N04/post-g12/N04G23D_NEXT_CHAT_HANDOFF.md`

## Residual classifier execution is later

Concrete V2-R-A/V2-R-C selection is not part of G-23D.

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
- G-23B Stage 1 contract
- G-23C Certification / Certified Content contract
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
G-23C   = Complete / Contract Accepted
G-23D   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## Immediate next task

**N-04G-23D — Stage 2 Presentation Generator Contract**
