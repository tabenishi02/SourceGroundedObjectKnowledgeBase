# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Primary next-chat entry: `docs/planning/phases/N/N04/post-g12/N04G24_NEXT_CHAT_HANDOFF.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23A-E: **Complete / Architecture Accepted**
- G-23B: **Complete / Contract Accepted**
- G-23C: **Complete / Contract Accepted**
- G-23D: **Complete / Contract Accepted**
- G-23E: **Complete / Contract Accepted**
- G-23F: **Complete / v4 Design Frozen**
- Current task: **N-04G-24 — v4 Implementation**

## Read first

0. `docs/planning/phases/N/N04/post-g12/N04G24_NEXT_CHAT_HANDOFF.md`
1. `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
2. `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`
3. `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
4. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
5. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
6. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
7. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
8. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
9. existing production code under `src/sgokb/grounding/`
10. `src/sgokb/application_grounding.py`

GitHub `main` is authoritative.

## Frozen v4 architecture

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidates
  ↓
Reference Integrity
  ↓
V2-S / V2-P / V2-D
  ↓
V2-R-A / V2-R-C where required
  ↓
V3/V4F Source Fact Support
  ↓ PASS only
Validation Record
  ↓
Certification
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
application path assignment / exact Certified Fact materialization
  ↓
V2 for Stage 2 model-authored propositions
  ↓
V4I for interpretations
  ↓
Validated Presentation Plan
  ↓
Material Requirement
  ↓
Terminal Decision
  ↓ ACCEPTED only
Deterministic Render
```

No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE / UNAVAILABLE.

## Frozen authority paths

```text
stage1_fact_candidate
  -> source_fact
  -> model-authored
  -> V2 + V3/V4F

certified_fact_materialization
  -> source_fact
  -> application-owned exact Certified Fact text

stage2_interpretation_candidate
  -> interpretation
  -> model-authored
  -> V2 + V4I

stage2_creative_candidate
  -> creative_addition
  -> model-authored
  -> V2 + creative-purpose/scope policy

system_context_limit
  -> context_limit
  -> application/system-owned only
```

There is no model-owned semantic-role authority, context-limit path, certification status, support PASS or Atomicity PASS.

## Frozen contracts

```text
sgokb.stage1-grounded-content-request.v1
sgokb.stage1-provider-output.v1
sgokb.structured-proposition.v1-candidate
sgokb.v4-validation-record.v1
sgokb.certified-content.v1
sgokb.stage2-presentation-request.v1
sgokb.stage2-provider-output.v1
sgokb.stage-local-retry-feedback.v1
sgokb.validated-presentation-plan.v1
sgokb.system-context-limit.v1
sgokb.grounded-generation-v4-run.v1
```

Historical v2/v3 contracts remain historical evidence and do not acquire v4 semantics.

## Stage 1

Model payload remains:

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

Application owns path, role, identity, attempt and lineage. Schema-valid text still requires residual semantic validation where required. Candidate content is immutable.

## Certification

```text
Candidate != Validation Record != Certified Fact != Certified Content
```

Certified Fact is emitted only after required V2 + source-support PASS and identity consistency.

Certified `claim_text` and `support_refs[]` exactly copy Stage 1. Certification never repairs or adds factual material.

## Stage 2

Model factual input is Certified Content only.

```text
main
  -> Certified Fact IDs only
  -> application exact materialization

interpretation
  -> claim_text + active Certified Fact premise IDs
  -> V2 + V4I

creative
  -> claim_text
  -> creative purpose only
  -> V2 scope/content checks
```

Stage 2 cannot reopen raw Grounded Context or create a new certified source fact.

## Provider / application boundary

Provider structured output is a structural guard only. Application independently revalidates schema, allow-lists, bindings, duplicates, purpose compatibility and all semantic Gates.

Do not depend on provider support for `uniqueItems`, `contains/minContains/maxContains`, conditionals or cross-item uniqueness.

G-24 must implement provider capability probes; G-26 later freezes the exact Reference Workstation runtime evidence.

## Retry

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

Retry is full replacement. Attempt 2 becomes the sole active attempt. No cross-attempt merge, no fallback to attempt 1 after attempt 2 authorization, and no Stage 2 -> Stage 1 backward retry in the same run.

Retry feedback is diagnostic only and cannot add factual authority or validator-written replacement prose.

## Context-limit / terminal

Empty Stage 1 candidates, empty Certified Content or empty Stage 2 blocks are not automatically context insufficiency.

`system_context_limit` is application/system-owned and may be created only from deterministic evidence that authoritative fixed input cannot satisfy required material.

Terminal outcomes remain:

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

Only `ACCEPTED` authorizes normal render and can count toward N-04 Case PASS.

## Evidence / replay

G-24 must implement the frozen evidence tree and exact-byte hashes for request/prompt/schema/runtime/output/validation/certification/retry/final-plan/material/terminal artifacts.

Failed and non-active attempts remain immutable evidence.

## G-24 scope

G-24 implements the frozen v4 architecture, contracts, orchestration, evidence and tests.

It must not redesign:

- Retrieval / Similarity / Context Builder;
- canonical DB;
- Source / Evidence / Provenance;
- Object / Version identity;
- MCP public read boundary;
- Frozen 47 labels/flags;
- G-25A selection Gate.

Concrete Residual Atomicity / Content-Type classifier selection is not G-24 scope. G-24 implements pluggable adapters and fail-closed behavior; G-25A performs benchmark/selection.

## Downstream mandatory Gate

```text
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

If G-25A yields `VALID_FAIL_NO_SELECTION`, G-26 remains blocked and the Gate is not weakened.

## Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = Complete / Contract Accepted
G-23D   = Complete / Contract Accepted
G-23E   = Complete / Contract Accepted
G-23F   = Complete / v4 Design Frozen
G-24    = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## Immediate next task

**N-04G-24 — v4 Implementation**
