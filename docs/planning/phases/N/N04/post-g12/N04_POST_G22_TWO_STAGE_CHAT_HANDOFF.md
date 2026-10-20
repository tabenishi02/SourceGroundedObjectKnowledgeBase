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
- G-23A-E1: **Complete**
- G-23A-E2: **Complete**
- G-23A-E3: **Complete / Semi-structured contract selected**
- Current task: **N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design**
- G-23B: **blocked until G-23A-E is accepted**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
3. `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
4. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
5. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
6. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
7. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
8. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
9. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
10. `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`

## Architecture direction

v4 retains two-stage generation:

```text
Grounded Context
  ↓
Stage 1: Grounded Content Planner
  ↓
Certification
  ↓
Certified Content
  ↓
Stage 2: Presentation Generator
  ↓
Material / Terminal / Render
```

V2 authorities:

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

No downstream component may rescue an earlier structural/policy failure.

## E1 result

47 Gold mapped with zero label changes:

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
TOTAL                    47
Critical without owner    0
```

## E2 result

Authority/order fixed in:

`docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

Key rules:

- application/stage path owns role provenance;
- known metadata incompatibility is deterministic hard fail;
- model-authored semantic content uses residual classification where construction cannot prove content type;
- `MIXED_CONTENT` fails;
- `AMBIGUOUS/INDETERMINATE` fails closed;
- V2 does not decide truth/support/entailment.

## E3 result

Structured Proposition contract is fixed in:

`docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

Selected: **Option B — Semi-structured proposition record**.

### Candidate layers

```text
Structured Proposition Candidate
  ↓
Validation Record
  ↓ PASS only
Certified Content Record
```

Candidate content is immutable during validation; failed text is retried as a new candidate rather than silently rewritten.

### Application-owned fields

```text
contract_version
context_fingerprint
purpose
stage
path_provenance
attempt
proposition_id
retry lineage
```

Generator does not own semantic-role authority or certification state.

### Path-specific payload direction

```text
stage1_fact_candidate
  claim_text
  support_refs[]

stage2_interpretation_candidate
  claim_text
  premise_fact_ids[]  # certified IDs only

stage2_creative_candidate
  claim_text

system_context_limit
  application/system-owned canonical payload
```

`support_refs[]` and `premise_fact_ids[]` cannot coexist.

Optional `subject_refs[] / predicate_hint / object_refs[]` are diagnostic aids only, not truth/support/role/Atomicity authority.

### V2-S construction state

```text
PASS_BY_CONSTRUCTION
REVIEW_REQUIRED
FAIL
```

Application/system deterministic construction may qualify for `PASS_BY_CONSTRUCTION`.

Model-authored free-text normally starts as `REVIEW_REQUIRED`; schema alone must not pretend it proves semantic Atomicity.

Residual resolution:

```text
REVIEW_REQUIRED + ATOMIC        -> V2-S PASS
REVIEW_REQUIRED + NON_ATOMIC    -> V2-S FAIL
REVIEW_REQUIRED + INDETERMINATE -> V2-S INDETERMINATE
```

Residual mechanism is designed in E5.

### Identity / retry

- proposition_id is application-assigned and unique within an attempt.
- retry generates a new candidate identity.
- application-owned retry lineage links failed and replacement candidates.
- future Certified Content gets a separate certified identity; exact lifecycle is G-23C.

### Not adopted

Fully normalized `subject + predicate + object/value + qualifiers` is not the common v4 contract because it would require a new broad semantic ontology and risks losing arbitrary narrative/interpretive/creative meaning.

## Current task: G-23A-E4

Design the exact role provenance and deterministic compatibility matrix using E3's application-owned path.

Minimum paths:

```text
stage1_fact_candidate
stage2_interpretation_candidate
stage2_creative_candidate
system_context_limit
```

Required matrix dimensions:

```text
path provenance
normalized role
allowed purpose
allowed presentation_role
support_refs required/forbidden
premise_fact_ids required/forbidden
model/system ownership
```

Required decisions:

1. exact path -> normalized role mapping;
2. purpose permissions;
3. presentation-role permissions;
4. support/premise binding requirements;
5. system-only context-limit restrictions;
6. deterministic failure codes;
7. whether any application-owned construction path can legitimately set V2-R `NOT_REQUIRED`;
8. ensure deterministic PASS does not itself prove model-authored text content type.

Expected deliverable:

`docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`

Optional machine-readable artifact:

`benchmark/n04g23ae-role-compatibility-v1.json`

## Following tasks

```text
G-23A-E1 47-Gold Responsibility Mapping             Complete
G-23A-E2 v4 V2 Responsibility Boundary              Complete
G-23A-E3 Structured Proposition Contract            Complete
G-23A-E4 Role Provenance / Compatibility Matrix     NEXT
G-23A-E5 Residual Classifier Evaluation Design      Planned
G-23A-E6 47-Gold Desk Replay                        Planned
G-23A-E7 Integration / G-23B Unblock Review         Planned
G-23B    Stage 1 Content Planner                    blocked
```

## Protected boundaries

Do not change without new evidence:

- frozen 47 Gold labels / required / critical flags
- G-23A-R historical results
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage generation decision
- MiniCheck threshold merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

G-23B remains blocked until G-23A-E7 explicitly accepts the integrated redesign.