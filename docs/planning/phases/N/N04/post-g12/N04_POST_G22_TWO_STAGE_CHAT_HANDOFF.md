# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-20

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23: **Complete / Architecture Accepted**
- G-23A: **Complete / Phi-4 insufficient**
- G-23A-R: **Complete / valid FAIL / no candidate selected**
- G-23A-E: **In Progress**
- G-23A-E1〜E6: **Complete**
- Current task: **N-04G-23A-E7 — Integration Decision / G-23B Unblock Review**
- G-23B: **blocked until G-23A-E7 acceptance**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
3. `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
4. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
5. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
6. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
7. `benchmark/n04g23ae-role-compatibility-v1.json`
8. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
9. `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`
10. `benchmark/n04g23ae-v4-gate-desk-replay-v1.json`
11. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
12. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
13. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`

## Integrated v4 V2 direction

```text
Structured Proposition Candidate
  ↓
V2-S schema / construction
  ↓
V2-P application-owned role provenance
  ↓
V2-D deterministic compatibility
  ↓ PASS only
V2-R-A Residual Atomicity if required
  ↓ ATOMIC only
V2-R-C Residual Content Type if required
  ↓ expected-role compatibility
V3/V4 support / derivation
```

No downstream component may rescue an earlier FAIL/INDETERMINATE.

## E1-E5 fixed decisions

### Structured Proposition

Selected: **Semi-structured proposition record**.

- application owns contract/context/purpose/stage/path/attempt/proposition identity;
- candidate has one authoritative `claim_text`;
- source fact candidate uses `support_refs[]`;
- interpretation uses certified `premise_fact_ids[]`;
- candidate/validation/certification are separate artifacts;
- model-authored role or certification status is never authority;
- schema-valid free text is not automatically Atomic.

### Role provenance / policy

```text
stage1_fact_candidate             -> source_fact
certified_fact_materialization    -> source_fact
stage2_interpretation_candidate   -> interpretation
stage2_creative_candidate         -> creative_addition
system_context_limit              -> context_limit
```

Known purpose/presentation/binding/ownership mismatches are deterministic hard failures. `creative_addition` is creative-purpose only. `context_limit` is application/system-owned and exclusive. Model-authored `stylistic_expression` remains forbidden.

### Residual classifiers

```text
V2-R-A Atomicity
  ATOMIC / NON_ATOMIC / AMBIGUOUS

V2-R-C Content Type
  SOURCE_FACT_CONTENT
  INTERPRETATION_CONTENT
  CREATIVE_CONTENT
  CONTEXT_LIMIT_CONTENT
  MIXED_CONTENT
  AMBIGUOUS
```

Atomicity and Content Type are separate tasks. Expected role/purpose/presentation are hidden from classifier inputs; observed content type is compared with application-owned expected role afterward.

Safety selection Gate remains:

```text
Atomicity critical false-pass = 0
Content critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
all candidates fail -> VALID_FAIL_NO_SELECTION
```

Frozen 47 Gold is a final confirmation control, not repeated threshold-fitting data.

## E6 result

Deliverables:

- `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`
- `benchmark/n04g23ae-v4-gate-desk-replay-v1.json`

Desk replay:

```text
Total                                     47
Required                                  41
Optional                                   6
Critical                                  33

V2-D deterministic POLICY_FAIL             5
V2-R-A invoked                             42
  ATOMIC                                   11
  NON_ATOMIC                               27
  AMBIGUOUS                                 4
V2-R-C invoked                             11
  compatible                                8
  semantic mismatch                         3

Expected V2 PASS                            8
Expected V2 FAIL                           35
Expected V2 INDETERMINATE                   4
```

Critical invalid coverage:

```text
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

E6 Gate: **PASS with residual Atomicity classifier risk retained**.

Interpretation:

- broad joint Atomicity/Role Judge is eliminated from all 47 routes;
- content-role probabilistic classification is needed for only 11/47 and only 3/33 critical invalid fixtures;
- every critical invalid fixture has a fail-closed V2 route before support/derivation;
- however Atomicity remains the main probabilistic risk: 42/47 invoke V2-R-A and 25/33 critical invalid fixtures rely on correct `NON_ATOMIC` detection;
- E6 is architecture coverage only, not classifier performance proof.

## Current task: G-23A-E7

Perform the integrated architecture decision and decide whether G-23B can start.

E7 must explicitly answer:

1. Does E2-E6 form a coherent single authority model without duplicate role authority?
2. Is the remaining V2-R-A dependency a bounded implementation/benchmark risk rather than an architecture blocker?
3. Can G-23B design Stage 1 around `stage1_fact_candidate` without claiming schema proves Atomicity?
4. Is there a mandatory later execution point for classifier dataset construction, benchmark, selection, freeze and regression before G-27?
5. Can G-23C/D use Certified Content without restoring free-form source-fact regeneration in Stage 2?
6. Are G-14 no-silent-atomization, fail-closed semantics and zero-critical-FP policy preserved?

If accepted:

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

Acceptance must not be described as classifier selection, implementation completion, or N-04 acceptance.

If rejected, keep G-23B blocked and create an explicit remediation task.

Expected deliverable:

`docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`

## Protected boundaries

Do not change without new evidence:

- Frozen 47 Gold labels / required / critical flags
- G-23A/G-23A-R historical results
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage generation decision
- E2 authority order
- E3 Semi-structured contract unless E7 explicitly rejects it
- E4 application-owned provenance / deterministic policy
- E5 zero-critical-FP / fail-closed selection policy
- MiniCheck threshold/profile merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

G-23B remains blocked until E7 explicitly accepts the integrated redesign.
