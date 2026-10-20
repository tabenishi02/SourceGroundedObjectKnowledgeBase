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
- G-23A-E4: **Complete / deterministic role matrix fixed**
- Current task: **N-04G-23A-E5 — Residual Classifier Scope / Evaluation Design**
- G-23B: **blocked until G-23A-E is accepted**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
3. `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
4. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
5. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
6. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
7. `benchmark/n04g23ae-role-compatibility-v1.json`
8. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
9. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
10. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
11. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
12. `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`

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

47 Gold mapping:

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

- application/stage path owns role provenance;
- known metadata incompatibility is deterministic hard fail;
- model-authored semantic content uses residual classification where construction cannot prove content type;
- `MIXED_CONTENT` fails;
- `AMBIGUOUS/INDETERMINATE` fails closed;
- V2 does not decide truth/support/entailment.

## E3 result

Selected: **Option B — Semi-structured proposition record**.

```text
Application-owned envelope
  + path-discriminated payload
  + one authoritative claim_text
  + path-specific support/premise binding
  + optional non-authoritative semantic anchors
```

Candidate / Validation / Certified Content are separate artifacts. Model-authored free text is not considered atomic merely because it satisfies JSON Schema.

## E4 result

Role provenance and metadata compatibility are fixed in:

`docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`

Machine-readable mirror:

`benchmark/n04g23ae-role-compatibility-v1.json`

### Path -> normalized role

```text
stage1_fact_candidate
  -> source_fact

certified_fact_materialization
  -> source_fact

stage2_interpretation_candidate
  -> interpretation

stage2_creative_candidate
  -> creative_addition

system_context_limit
  -> context_limit
```

Unknown/forged path does not fall back to generator label:

```text
UNRESOLVED_PROVENANCE
```

### Purpose policy

```text
source_fact
  roleplay / comparison / creative = allow

interpretation
  roleplay / comparison / creative = deterministic allow
  but V2-R + V4I remain required for model-authored content

creative_addition
  creative = allow
  roleplay / comparison = POLICY_FAIL

context_limit
  all three purposes = allow
  application/system-owned only
```

Roleplay interpretation remains possible only to preserve G-02's narrow transient inference allowance. This is not a semantic PASS; classifier/derivation still decides whether actual content is legal.

### Presentation policy

```text
stage1_fact_candidate
  presentation = none

certified_fact_materialization
  presentation = main

stage2_interpretation_candidate
  presentation = interpretation

stage2_creative_candidate
  presentation = creative

system_context_limit
  presentation = context_limit
  exclusive terminal response
```

Known mismatch is deterministic `POLICY_FAIL`.

### Binding policy

```text
stage1_fact_candidate
  support_refs[] >= 1
  premise_fact_ids[] forbidden

certified_fact_materialization
  support provenance inherited from Certified Content
  no new model-authored support/premise binding

stage2_interpretation_candidate
  premise_fact_ids[] >= 1
  raw support_refs[] forbidden as derivation proof

stage2_creative_candidate
  support_refs[] / premise_fact_ids[] forbidden as grounding proof

system_context_limit
  support_refs[] / premise_fact_ids[] forbidden
```

### Other fixed rules

- model-authored `semantic_role` is not authority;
- model-authored `stylistic_expression` remains forbidden;
- Stage 2 does not regain a free-form source-fact generation slot;
- Certified source fact materialization is application-owned and is the preferred source-fact presentation path;
- deterministic policy PASS does not prove natural-language content type;
- V2-D failure cannot be overridden by V2-R/V3/V4 positive verdicts.

## Current task: G-23A-E5

Design the residual classifier scope and evaluation protocol after E1-E4 have removed structural/policy decisions from the broad probabilistic judge.

Required decisions:

1. exact V2-R taxonomy;
2. whether residual atomicity and content-role classification are separate models/tasks;
3. minimum classifier inputs;
4. whether expected role is hidden from classifier until after content-only classification;
5. dataset expansion beyond the 47 Gold cases;
6. minimal pairs, paraphrases, role swaps, purpose swaps, compound/split fixtures;
7. pattern-family holdout to prevent template leakage;
8. candidate families: bounded LLM, encoder classifier, cross-encoder, deterministic-first cascade;
9. ambiguity/abstention fail-closed policy;
10. critical false-pass zero-tolerance Gate;
11. Reference Workstation reproducibility/runtime requirements.

Expected deliverable:

`docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`

## Following tasks

```text
G-23A-E1 47-Gold Responsibility Mapping             Complete
G-23A-E2 v4 V2 Responsibility Boundary              Complete
G-23A-E3 Structured Proposition Contract            Complete
G-23A-E4 Role Provenance / Compatibility Matrix     Complete
G-23A-E5 Residual Classifier Evaluation Design      NEXT
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
- E2 authority order
- E3 Semi-structured contract
- E4 application-owned provenance and deterministic policy matrix
- MiniCheck threshold merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

G-23B remains blocked until G-23A-E7 explicitly accepts the integrated redesign.
