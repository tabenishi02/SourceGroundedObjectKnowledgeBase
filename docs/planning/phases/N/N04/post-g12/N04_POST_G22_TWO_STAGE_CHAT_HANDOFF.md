# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23: **Complete / Architecture Accepted**
- G-23A: **Complete / Phi-4 insufficient**
- G-23A-R: **Complete / valid FAIL / no candidate selected**
- G-23A-E: **Complete / Architecture Accepted**
- G-23A-E1〜E7: **Complete**
- Current task: **N-04G-23B — Stage 1 Grounded Content Planner Contract**
- G-23B: **NEXT**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
3. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
4. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
5. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
6. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
7. `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`
8. `benchmark/n04g23ae-role-compatibility-v1.json`
9. `benchmark/n04g23ae-v4-gate-desk-replay-v1.json`
10. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
11. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
12. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`

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

## E7 decision

G-23A-E is **Complete / Architecture Accepted**.

Residual Atomicity remains a substantial risk, but is now classified as a bounded implementation/benchmark risk rather than an architecture blocker.

Reason:

- V2-R-A has a fixed narrow interface/taxonomy.
- `AMBIGUOUS/UNAVAILABLE` fails closed.
- concrete classifier identity is not needed to define the Stage 1 candidate contract.
- all-candidate classifier failure later blocks G-26 rather than creating unsafe PASS.

This decision does **not** mean a production Atomicity classifier has been selected or proven.

## G-23B authority boundary

G-23B designs only the Stage 1 Grounded Content Planner contract.

Primary application-owned path:

```text
stage1_fact_candidate
  -> normalized role source_fact
```

Minimum candidate direction:

```text
application-owned envelope
  contract_version
  context_fingerprint
  purpose
  stage = stage1
  path_provenance = stage1_fact_candidate
  attempt
  proposition_id
  retry lineage

model-authored payload
  claim_text
  support_refs[] >= 1
```

Optional diagnostic semantic anchors may exist only if E3 rules are preserved; they are not authority.

## G-23B must not reintroduce

```text
generator-owned authoritative semantic_role
model-owned validation/certification status
model-owned Atomicity PASS
model-owned support/entailment PASS
presentation role on Stage 1 fact candidate
free-form model-authored context_limit path
```

The Stage 1 prompt/schema should reduce non-atomic generation, but schema-valid model-authored text remains `REVIEW_REQUIRED` for semantic Atomicity unless a future deterministic construction exemption is explicitly frozen.

## Stage 1 design goals

G-23B should fix at least:

1. Stage 1 request contract.
2. Stage 1 response/candidate schema.
3. application-owned envelope construction.
4. one-proposition-per-candidate generation policy.
5. `support_refs[]` requirements and reference-integrity expectations.
6. conservative prompt examples / no-extra-proposition rules.
7. candidate identity and retry-lineage semantics.
8. provider structured-output constraints that can be enforced safely.
9. how multiple Stage 1 candidates are represented without assigning final presentation roles.
10. how Stage 1 output enters E7 V2-S/P/D/R without duplicate authority.

## Residual classifier execution is later

Concrete V2-R-A/V2-R-C selection is not part of G-23B.

It has an explicit execution home:

```text
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

G-25A mandatory Gate:

```text
Atomicity critical false-pass = 0
Content critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
```

If all candidates fail, result is `VALID_FAIL_NO_SELECTION` and G-26 remains blocked.

## E6 evidence retained

Frozen 47 Gold desk replay:

```text
Critical total                            33
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

This is architecture coverage only. It is not classifier performance proof.

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
G-23B   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## Immediate next task

**N-04G-23B — Stage 1 Grounded Content Planner Contract**
