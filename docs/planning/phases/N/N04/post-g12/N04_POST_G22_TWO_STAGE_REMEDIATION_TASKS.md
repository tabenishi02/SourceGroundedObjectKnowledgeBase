# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-21

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Gate integration decision: `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
- Stage 1 contract: `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
- Certified Content contract: `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
- Stage 2 contract: `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
- Provider/retry contract: `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`
- v4 Design Freeze: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
- G-24 handoff: `docs/planning/phases/N/N04/post-g12/N04G24_NEXT_CHAT_HANDOFF.md`
- G-25 benchmark plan: `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
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
G-23A-E Gate Responsibility Decomposition           Complete / Architecture Accepted
  ├─ E1 47-Gold Responsibility Mapping              Complete
  ├─ E2 v4 V2 Responsibility Boundary               Complete
  ├─ E3 Structured Proposition Contract             Complete
  ├─ E4 Role Provenance / Compatibility Matrix      Complete
  ├─ E5 Residual Classifier Evaluation Design       Complete
  ├─ E6 47-Gold Desk Replay                         Complete / PASS with residual risk
  └─ E7 Integration / Unblock Review                Complete / Accepted
  ↓
G-23B Stage 1 Grounded Content Planner contract     Complete / Contract Accepted
  ↓
G-23C Certification / Certified Content contract    Complete / Contract Accepted
  ↓
G-23D Stage 2 Presentation Generator contract       Complete / Contract Accepted
  ↓
G-23E Provider schema + stage-local retry design    Complete / Contract Accepted
  ↓
G-23F v4 design integration / Design Freeze         Complete / v4 Design Frozen
  ↓
G-24 v4 implementation                              NEXT
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation v4 harness freeze
  ↓
G-27 Formal v4 Re-Acceptance
  ↓ PASS only
N-04 Complete
  ↓
N-05 unblocked
```

Historical G-18/G-21/G-22 artifacts remain immutable evidence.

## 2. Current task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | Complete / Architecture Accepted | two-stage generation architecture |
| N-04G-23A | P0 | Complete / valid benchmark | diagnose Atomicity / Role judge |
| N-04G-23A-R | P0 | Complete / valid FAIL / no candidate selected | alternate judge evaluation |
| N-04G-23A-E | P0 | **Complete / Architecture Accepted** | decompose Gate responsibilities |
| N-04G-23A-E1 | P0 | Complete | 47 Gold responsibility mapping |
| N-04G-23A-E2 | P0 | Complete | V2 authority/order boundary |
| N-04G-23A-E3 | P0 | Complete | Semi-structured Proposition contract |
| N-04G-23A-E4 | P0 | Complete | application-owned role provenance / compatibility matrix |
| N-04G-23A-E5 | P0 | Complete | residual classifier scope/evaluation design |
| N-04G-23A-E6 | P0 | Complete / Gate PASS with residual Atomicity risk | 47-Gold desk replay / coverage |
| N-04G-23A-E7 | P0 | Complete / Architecture Accepted | integration / G-23B unblock |
| N-04G-23B | P0 | Complete / Contract Accepted | Stage 1 Content Planner contract |
| N-04G-23C | P0 | Complete / Contract Accepted | Certification / Certified Content contract |
| N-04G-23D | P0 | Complete / Contract Accepted | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | Complete / Contract Accepted | provider schema + stage-local retry |
| N-04G-23F | P0 | **Complete / v4 Design Frozen** | end-to-end integration / implementation freeze |
| N-04G-24 | P0 | **NEXT** | v4 implementation |
| N-04G-25A | P0 | Blocked by G-24 | Residual classifier benchmark / selection |
| N-04G-25B | P0 | Blocked by G-25A PASS | integrated adversarial regression |
| N-04G-26 | P0 | Blocked by G-25B PASS | Reference Workstation freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. Frozen v4 architecture

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

Universal invariant:

```text
No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE / UNAVAILABLE.
```

## 4. Frozen path / authority map

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

Model-declared role/status is not authority.

No model-authored `context_limit` or `stylistic_expression` path exists in the v4 baseline.

## 5. Frozen contract identities

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

Historical v2/v3 version strings remain historical evidence and must not silently acquire v4 semantics.

## 6. Stage 1 freeze

Provider-facing payload:

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

Key invariants:

- one candidate = one authoritative `claim_text`;
- non-empty candidate requires `support_refs[] >= 1`;
- refs must be request allow-listed/current-context refs;
- schema-valid text does not prove Atomicity;
- application owns stage/path/role/attempt/proposition identity;
- failed candidate is immutable;
- same-attempt eligible candidates may be certified independently;
- no cross-attempt Certified Fact merge.

## 7. Certification freeze

```text
Candidate != Validation Record != Certified Fact != Certified Content
```

Certification requires aggregate V2 PASS + source-support PASS + identity/digest consistency.

Certified Fact `claim_text` and `support_refs[]` are exact Stage 1 copies.

Certification cannot rewrite, atomize, merge support or add source-world facts.

Stage 2 primary factual authority is one active immutable Certified Content artifact.

## 8. Stage 2 freeze

Model-facing facts:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Model output families:

```text
main
  -> Certified Fact IDs only
  -> exact application materialization

interpretation
  -> claim_text + premise_fact_ids[]
  -> active Certified Fact IDs only

creative
  -> claim_text only
  -> creative purpose only
```

Each block kind cardinality is 0 or 1. Duplicate block kinds/IDs fail deterministically.

Stage 2 attempt is one ordered plan; failed plan is not partially rendered.

After Certification, no new source fact can reach normal render without returning through a new Stage 1 run.

## 9. Provider/application freeze

Provider schema is a structural guard only.

Application always rechecks:

```text
JSON/schema
K/CF allow-list
reference/binding integrity
duplicate IDs
duplicate block kinds
purpose compatibility
context/request/Certified Content binding
```

Do not rely on provider `uniqueItems`, `contains/minContains/maxContains`, conditionals or cross-item uniqueness.

Provider unavailable/incomplete/schema-binding mismatch is fail-closed SYSTEM_FAILURE. No silent provider/model/schema weakening or free-prose fallback.

G-24 and G-26 must record exact provider capability probes.

## 10. Retry freeze

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

- counters are independent;
- retry is full replacement, never patch;
- factual authority/model/settings/schema/material profile stay fixed within a stage retry;
- attempt 2 becomes the sole active attempt;
- attempt 1 remains evidence only;
- no cross-attempt merge;
- no fallback to attempt 1 after attempt 2 authorization;
- no Stage 2 -> Stage 1 backward retry in one run;
- retry feedback is diagnostic only and cannot add new facts or validator-authored replacement prose.

## 11. Material / context-limit / terminal freeze

Stage 1 readiness is distinct from final Material Requirement.

Stage 1 readiness asks whether active Certified Content has enough factual material to justify Stage 2 and whether Stage 1 retry is appropriate.

Final Material Requirement evaluates only validated Stage 2 material.

`candidates: []`, empty Certified Content or `blocks: []` do not automatically mean context insufficiency.

Application/system may create `sgokb.system-context-limit.v1` only from deterministic evidence that authoritative fixed input cannot satisfy the material requirement.

Terminal outcomes:

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

Only `ACCEPTED` authorizes normal render and can count toward N-04 Case PASS.

`INSUFFICIENT_CONTEXT` is safe but formal Case FAIL.

## 12. Evidence / replay freeze

Authority: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`.

Required evidence includes:

```text
run manifest / Git identity
runtime/model/provider/classifier identities
provider capability probe
Grounded Context / fingerprint
Stage 1 request/prompt/schema/raw/parsed/candidate/validation/certification artifacts
active Certified Content + digest
Stage 2 request/projection/prompt/schema/raw/parsed/path/validation/materialization artifacts
retry feedback + lineage for every executed retry
Validated Presentation Plan + digest
Material Requirement result
system context-limit when applicable
terminal decision
rendered output when authorized
```

Exact persisted prompt/schema bytes are hash authorities; historical/non-active attempts remain retained.

## 13. G-23F result

Authority:

`docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`

G-23F is **Complete / v4 Design Frozen**.

Integration review closed the required questions:

- every model-authored natural-language proposition has exactly one application-owned path;
- no uncertified source fact can reach normal render;
- model-declared role/status cannot override provenance;
- schema validity cannot bypass required Residual semantic Gates;
- Stage 2 cannot reopen raw Grounded Context/uncertified candidates;
- Certification cannot rewrite candidate text/support;
- retry attempts cannot be silently merged;
- retry feedback cannot introduce new factual authority;
- provider limitations cannot weaken application validation;
- G-25A failure cannot be bypassed to G-26.

No ownership/authority contradiction requiring architecture reopen was found.

## 14. G-24 immediate scope

Next task: **N-04G-24 — v4 Implementation**.

Primary handoff:

`docs/planning/phases/N/N04/post-g12/N04G24_NEXT_CHAT_HANDOFF.md`

G-24 implements the frozen v4 contracts, orchestration, evidence and automated tests.

G-24 must not select the concrete Residual Atomicity / Content-Type production component. It implements the adapter/interface and fail-closed behavior; selection remains G-25A.

## 15. Mandatory downstream classifier Gate

Authority: `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`.

G-25A remains mandatory:

```text
Atomicity critical NON_ATOMIC false-pass = 0
Content-Type critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
```

All candidates fail:

```text
VALID_FAIL_NO_SELECTION
```

G-26 remains blocked; Gate weakening is prohibited.

G-25B then requires zero critical integrated false-pass classes before G-26.

## 16. Protected boundaries

Do not change during G-24 without reopening G-23F:

- Frozen 47 Gold labels/flags and historical G-23A/G-23A-R evidence;
- G-14 no-silent-post-hoc-atomization intent;
- two-stage architecture;
- E2 authority order;
- E3 proposition contract;
- E4 application-owned provenance;
- E5 fail-closed classifier policy;
- G-23B/C/D/E accepted contracts;
- exact Certified Fact materialization;
- Stage 2 Certified Content factual boundary;
- max one retry per stage / active-attempt replacement;
- no Stage 2 -> Stage 1 backward retry;
- system-owned context-limit;
- provider schema as guard only / application revalidation;
- evidence/replay requirements;
- mandatory G-25A/G-25B Gates;
- Retrieval / Similarity / Context Builder;
- canonical DB;
- Source / Evidence / Provenance;
- Object / Version identity;
- MCP read-only boundary;
- unsupported rendered material prohibition;
- fail-closed semantics.

## 17. Current state

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

## 18. Immediate next task

**N-04G-24 — v4 Implementation**
