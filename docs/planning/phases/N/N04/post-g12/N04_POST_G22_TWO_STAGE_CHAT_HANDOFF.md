# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Primary next-chat entry: `docs/planning/phases/N/N04/post-g12/N04G23E_NEXT_CHAT_HANDOFF.md`
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
- Current task: **N-04G-23E — Provider Schema + Stage-local Retry Design**

## Read first

0. `docs/planning/phases/N/N04/post-g12/N04G23E_NEXT_CHAT_HANDOFF.md`
1. `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
2. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
3. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
4. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
5. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
6. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
7. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
8. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
9. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
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

Application owns all request/path/identity/retry metadata. Model-authored role, Atomicity PASS, validation/certification status and support/entailment PASS remain prohibited.

## G-23C result

G-23C is **Complete / Contract Accepted**.

Certification is application/validator-owned.

```text
Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certified Fact is emitted only after aggregate V2 PASS + source-support aggregate PASS + identity/digest consistency.

`certified_fact_id` is scoped to one immutable Certified Content artifact and is not a canonical DB Fact ID.

Certified `claim_text` and `support_refs[]` exactly copy the Stage 1 candidate. Certification cannot rewrite or create facts.

## G-23D result

G-23D is **Complete / Contract Accepted**.

Normative Decision:

`docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`

Stage 2 factual input is a minimal Certified Content projection:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Stage 2 output is an ordered block plan:

```text
main
  -> model selects Certified Fact IDs
  -> application materializes exact certified text

interpretation
  -> model claim_text + premise_fact_ids[]
  -> premise IDs must resolve to active Certified Content

creative
  -> model claim_text
  -> creative purpose only
```

Application assigns path provenance from output slot:

```text
main fact reference
  -> certified_fact_materialization
  -> source_fact

interpretation candidate
  -> stage2_interpretation_candidate
  -> interpretation

creative candidate
  -> stage2_creative_candidate
  -> creative_addition
```

Important decisions:

- Stage 2 model cannot freely rewrite a Certified Fact and inherit certification;
- raw Grounded Context is not reopened as factual authority;
- interpretation uses Certified Fact IDs only;
- creative is denied for roleplay/comparison;
- no model-authored `context_limit` path;
- no model-authored `stylistic_expression` path;
- normal block kinds are `main`, `interpretation`, `creative`;
- each block kind cardinality is 0 or 1;
- duplicate block kind is deterministic failure;
- block order is presentation order only;
- source fact / interpretation / creative remain structurally separate;
- `blocks: []` means no proposal, not context-limit;
- new source facts after certification require returning to Stage 1.

## G-23E authority boundary

G-23E designs **provider schema + stage-local retry integration** only.

It must preserve G-23B/C/D semantic contracts.

At minimum it should define:

1. Stage 1 provider-facing JSON Schema.
2. Stage 2 provider-facing JSON Schema.
3. provider-enforced vs application-enforced invariants.
4. runtime support/probe result for relevant schema features.
5. duplicate Stage 2 block-kind prevention.
6. parse/contract failure semantics.
7. Stage 1 stage-local retry contract.
8. Stage 2 stage-local retry contract.
9. retry identity/lineage and frozen inputs.
10. cross-attempt Stage 1 certification/salvage policy deferred by G-23C.
11. provider request/schema/prompt artifact hashes.

Primary task handoff:

`docs/planning/phases/N/N04/post-g12/N04G23E_NEXT_CHAT_HANDOFF.md`

## Provider schema is not semantic authority

Provider schema may enforce structure, but must not be interpreted as proving:

```text
Atomicity
Content-Type correctness
support / entailment
interpretation derivability
creative factual safety
certification
```

Application deterministic/semantic validation remains authoritative.

## Retry boundary

Retry remains stage-local.

Stage 1 retry may repair Stage 1 candidate/schema/support/Atomicity/content-type/support failures without changing Grounded Context authority.

Stage 2 retry may repair block/schema/binding/interpretation/creative failures without reopening raw Grounded Context or generating new certified facts.

Exact attempt/salvage policy is G-23E scope and must remain fail-closed.

## Residual classifier execution is later

Concrete V2-R-A/V2-R-C selection is not part of G-23E.

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
G-23E   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## Immediate next task

**N-04G-23E — Provider Schema + Stage-local Retry Design**
