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
- Current task: **N-04G-23A-E3 — Structured Proposition Contract Design**
- G-23B: **blocked until G-23A-E is accepted**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
3. `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
4. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
5. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
6. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
7. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
8. `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`
9. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

## Current architecture direction

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

Atomicity / Role Gate is decomposed into four authorities:

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

Normative order:

```text
Structured Proposition Candidate
  ↓
V2-S
  ↓
V2-P
  ↓
V2-D
  ↓
V2-R if required
  ↓
V3+ Support / Derivation validation
```

## G-23A-E1 result

47 Gold responsibility mapping:

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
TOTAL                    47
Required                 41
Optional                  6
Critical                 33
Critical without owner    0
```

Gold labels / required / critical flags remain unchanged.

## G-23A-E2 result

Authority/order is fixed in:

`docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

### V2-S

- Structured Proposition contract is authority.
- schema/contract violation -> hard structural FAIL.
- schema aloneでsemantic atomicityを証明できない場合は`REVIEW_REQUIRED`へ送る。
- punctuation/conjunction risk aloneは`NON_ATOMIC` verdictにしない。

### V2-P

- application/stage path is role provenance authority.
- generator-declared semantic_role is not authoritative.
- unresolved provenance -> fail-closed.

### V2-D

Known structured policy mismatch is deterministic hard FAIL before classifier.

Examples:

```text
creative path + non-creative purpose
source_fact + interpretation presentation
interpretation + main presentation
interpretation without required premise binding
```

### V2-R

Only residual content-first semantic boundary is classifier scope.

Residual classifier does not decide truth/support/entailment.

Mandatory candidates include:

- E1 RESIDUAL_SEMANTIC cases
- semantic side of COMBINED cases
- V2-S REVIEW_REQUIRED cases
- model-authored content whose content type cannot be proven by construction

`MIXED_CONTENT` -> FAIL.
`AMBIGUOUS / INDETERMINATE` -> fail-closed.

### Override rule

No downstream component may rescue an earlier failure.

```text
Structural FAIL
  cannot be overridden by V2-R or support PASS

Policy FAIL
  cannot be overridden by semantic classifier PASS

V2 FAIL/INDETERMINATE
  cannot enter grounded support/derivation PASS path
```

## Retry boundary

Stage-local failure evidence must include at least:

```text
failed_stage
failed_gate
failure_authority
failure_code
proposition_id
failed text
stage_path
expected role
observed semantic class if available
purpose
presentation_role
support/premise IDs
risk signals
expected rule
repair directive
```

Rules:

- Stage 1 failure -> do not start Stage 2.
- Stage 2 failure -> do not automatically regenerate Certified Content.
- `MIXED_CONTENT` is regenerated as legal separate proposition(s); no hidden post-hoc salvage.
- retry exhaustion remains terminal fail-closed.

## Current task: G-23A-E3

Design the Structured Proposition intermediate contract consumed by V2-S.

Required decisions:

1. Compare:

```text
A Minimal
  id + provenance + text + refs

B Semi-structured
  id + subject/entity refs + predicate hints + text + refs

C Fully normalized
  subject + predicate + object/value + qualifiers
```

2. proposition_id lifetime / uniqueness.
3. stage/path provenance binding.
4. text vs structured semantic fields.
5. support_refs / premise_fact_ids.
6. purpose / object / context fingerprint binding.
7. certification status ownership.
8. retry identity.
9. rejected / ambiguous proposition representation.
10. rendering separation.
11. schema versioning.
12. exact conditions for V2-S `PASS / REVIEW_REQUIRED / FAIL`.
13. which construction paths can legitimately make V2-R `NOT_REQUIRED`.
14. preserve G-14 no-silent-post-hoc-atomization.

Expected deliverable:

`docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

## Following tasks

```text
G-23A-E1 47-Gold Responsibility Mapping             Complete
G-23A-E2 v4 V2 Responsibility Boundary              Complete
G-23A-E3 Structured Proposition Contract            NEXT
G-23A-E4 Role Provenance / Compatibility Matrix     Planned
G-23A-E5 Residual Classifier Evaluation Design      Planned
G-23A-E6 47-Gold Desk Replay                        Planned
G-23A-E7 Integration / G-23B Unblock Review         Planned
G-23B    Stage 1 Content Planner                    blocked
```

## Protected boundaries

Do not change without new evidence:

- frozen 47 Gold labels / required / critical flags
- G-23A-R historical results
- G-14 safety intent
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