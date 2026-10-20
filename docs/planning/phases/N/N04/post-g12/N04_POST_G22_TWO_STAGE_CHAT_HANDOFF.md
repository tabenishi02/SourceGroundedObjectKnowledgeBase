# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Primary next-chat entry: `docs/planning/phases/N/N04/post-g12/N04G23F_NEXT_CHAT_HANDOFF.md`
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
- G-23D: **Complete / Contract Accepted**
- G-23E: **Complete / Contract Accepted**
- Current task: **N-04G-23F — v4 Design Integration / Design Freeze**

## Read first

0. `docs/planning/phases/N/N04/post-g12/N04G23F_NEXT_CHAT_HANDOFF.md`
1. `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`
2. `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
3. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
4. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
5. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
6. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
7. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
8. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
9. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
10. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
11. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

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
Certification
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
Final validation / Material / Terminal / Render
```

No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE.

## G-23B result

G-23B is **Complete / Contract Accepted**.

Stage 1 model output remains minimal:

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

Application owns request/path/identity/retry metadata. Model-owned role, Atomicity PASS, validation/certification status and support/entailment PASS remain prohibited.

## G-23C result

G-23C is **Complete / Contract Accepted**.

Certification is application/validator-owned.

```text
Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certified `claim_text` and `support_refs[]` exactly copy the immutable Stage 1 candidate. `certified_fact_id` is scoped to one Certified Content artifact and is not a canonical DB Fact ID.

## G-23D result

G-23D is **Complete / Contract Accepted**.

Stage 2 factual input is a minimal Certified Content projection:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Stage 2 blocks:

```text
main
  -> Certified Fact IDs only
  -> application exact materialization

interpretation
  -> model claim_text + premise_fact_ids[]
  -> Certified Fact premises only

creative
  -> model claim_text
  -> creative purpose only
```

No Stage 2 model-authored factual rewrite inherits certification. Raw Grounded Context is not reopened as a factual bypass.

## G-23E result

G-23E is **Complete / Contract Accepted**.

Normative Decision:

`docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`

### Provider schemas

Stage 1 provider response:

```text
candidates[]
  claim_text
  support_refs[]
```

- dynamic K allow-list enum;
- request-owned candidate max;
- additional fields forbidden;
- duplicate refs still checked by application.

Stage 2 provider response:

```text
blocks[] <= 3
  main
  interpretation
  creative where purpose permits
```

- complete `oneOf` block alternatives;
- active Certified Fact IDs projected as enum;
- creative alternative only for creative purpose;
- duplicate block kinds and duplicate IDs checked by application.

### Provider/application boundary

Provider structured output is a structural guard only.

Application must independently:

```text
parse JSON
validate instantiated schema
check duplicate refs/IDs
check duplicate block kinds
check request/context/Certified Content binding
run deterministic/semantic Gates
```

Existing G-21/G-22 evidence shows the LM Studio structured-output path is operational, but schema acceptance does not prove every keyword is enforced. G-23E therefore does not rely on provider `uniqueItems`, `contains/minContains/maxContains`, conditionals or cross-item uniqueness. G-24/G-26 must record exact runtime capability probes.

### Retry

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

- retry is stage-local;
- no Stage 2 -> Stage 1 backward retry in the same run;
- Context/Certified Content, purpose, model, settings and schema remain fixed across a retry;
- attempt 2 is a complete replacement, not a patch;
- no cross-attempt Stage 1 Certified Fact merge;
- no cross-attempt Stage 2 block/candidate merge;
- no fallback to attempt 1 after attempt 2 is authorized;
- retry feedback is structured/application-owned and cannot add new factual authority or validator-written replacement prose.

Stage 1 candidate-level certification within one active attempt remains valid and is not considered cross-attempt salvage.

## G-23F authority boundary

G-23F performs **v4 Design Integration / Design Freeze** only.

It must integrate G-23A-E + G-23B/C/D/E without weakening any accepted boundary.

At minimum:

1. verify end-to-end authority/ownership consistency;
2. freeze contract/version and artifact flow;
3. freeze candidate -> validation -> certification -> Stage 2 -> final validation traceability;
4. freeze stage-local retry ordering and active-attempt semantics;
5. freeze system-owned context-limit / terminal boundary;
6. verify Material Requirement interaction;
7. freeze provider/application validation split;
8. freeze evidence/replay tree and minimum identity/hash bindings;
9. preserve the mandatory G-25A residual classifier Gate;
10. produce the G-24 implementation handoff.

Primary task handoff:

`docs/planning/phases/N/N04/post-g12/N04G23F_NEXT_CHAT_HANDOFF.md`

## Residual classifier execution is later

Concrete V2-R-A/V2-R-C selection is not part of G-23F.

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
- G-23D Stage 2 Presentation Generator contract
- G-23E Provider Schema / Stage-local Retry contract
- source-fact exact materialization after certification
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
G-23D   = Complete / Contract Accepted
G-23E   = Complete / Contract Accepted
G-23F   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## Immediate next task

**N-04G-23F — v4 Design Integration / Design Freeze**
