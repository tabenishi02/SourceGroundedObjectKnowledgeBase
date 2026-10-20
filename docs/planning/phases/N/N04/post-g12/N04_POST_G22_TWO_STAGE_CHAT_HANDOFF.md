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
- G-23A-E5: **Complete / residual classifier evaluation design fixed**
- Current task: **N-04G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis**
- G-23B: **blocked until G-23A-E is accepted**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
3. `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
4. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
5. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
6. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
7. `benchmark/n04g23ae-role-compatibility-v1.json`
8. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
9. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
10. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
11. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
12. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
13. `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`

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
V2-S Structural Proposition Gate
  ↓
V2-P Role Provenance Normalization
  ↓
V2-D Deterministic Compatibility Gate
  ↓
V2-R-A Residual Atomicity if required
  ↓
V2-R-C Residual Content Type if required
  ↓
V3+ Support / Derivation
```

No downstream component may rescue an earlier structural/policy/semantic failure.

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

## E2-E4 result

- Semi-structured proposition record selected.
- application/stage path owns role provenance.
- model-authored semantic_role is not authority.
- known purpose/presentation/support/premise/ownership mismatch is deterministic hard fail.
- model-authored free text is not considered atomic merely because schema-valid.
- unknown/forged provenance fails closed.
- creative_addition is allowed only for creative purpose.
- interpretation requires certified premise IDs and later derivation validation.
- context_limit is application/system-owned only and exclusive.
- model-authored stylistic_expression remains forbidden.

Path mapping:

```text
stage1_fact_candidate             -> source_fact
certified_fact_materialization    -> source_fact
stage2_interpretation_candidate   -> interpretation
stage2_creative_candidate         -> creative_addition
system_context_limit              -> context_limit
```

## E5 result

Residual probabilistic responsibility is narrowed to two independent tasks.

### V2-R-A Residual Atomicity

Input: normally `claim_text` only.

Labels:

```text
ATOMIC
NON_ATOMIC
AMBIGUOUS
```

Does not judge role, support, truth, purpose, presentation or derivation.

### V2-R-C Residual Content Type

Input: normally `claim_text` only.

Labels:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

Expected role is **not** shown to the classifier. The application compares observed content class with E4 normalized expected role afterward.

Compatibility:

```text
source_fact       <- SOURCE_FACT_CONTENT only
interpretation    <- INTERPRETATION_CONTENT only
creative_addition <- CREATIVE_CONTENT only
context_limit     <- CONTEXT_LIMIT_CONTENT only
```

`MIXED_CONTENT` fails. `AMBIGUOUS/UNAVAILABLE` fail closed.

### Dataset/evaluation policy

- Atomicity and Content Type use separate datasets/tasks.
- Frozen G-23A 47 Gold remains final confirmation control, not repeated threshold-fitting data.
- extend development corpus using paraphrase, minimal pairs, compound/split, role/content swaps and related families.
- group by pattern family and derivation lineage; random row split is not production-selection authority.
- compare encoder sequence classifier, cross-encoder/pair classifier, lightweight/few-shot classifier against historical bounded-LLM baseline.
- deterministic-first E2-E4 cascade is mandatory regardless of classifier family.

Safety Gate:

```text
Atomicity critical false-pass = 0
Content-type critical wrong-compatible false-pass = 0
```

Required-valid false reject target is 0. All-candidate failure is valid `VALID_FAIL_NO_SELECTION`; do not relax Gate to select a best available model.

### Reproducibility

Future runtime evidence must preserve base model/revision/hash, dataset/split manifest hashes, seed, hyperparameters, library/Python/PyTorch/CUDA identity, class mapping and threshold/abstention policy. Formal freeze should be local-only replayable on the Reference Workstation.

## Current task: G-23A-E6

Apply E2-E5 to all Frozen 47 Gold cases as a desk replay before implementation.

For every case record:

```text
input metadata available?
V2-S structural outcome
V2-P normalized role
V2-D deterministic outcome
V2-R-A required? expected Gold atomicity
V2-R-C required? expected Gold content class / compatibility
expected aggregate V2 path
historical broad-judge error prevented by construction?
remaining probabilistic decision?
```

E6 must not assume the future classifier is accurate. Its purpose is to quantify how much responsibility has moved away from the broad joint LLM Judge and whether every critical case has a fail-closed authority path.

Expected deliverable:

`docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`

## Following tasks

```text
G-23A-E1 47-Gold Responsibility Mapping             Complete
G-23A-E2 v4 V2 Responsibility Boundary              Complete
G-23A-E3 Structured Proposition Contract            Complete
G-23A-E4 Role Provenance / Compatibility Matrix     Complete
G-23A-E5 Residual Classifier Evaluation Design      Complete
G-23A-E6 47-Gold Desk Replay                        NEXT
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
- E5 zero-critical-FP / fail-closed classifier selection policy
- MiniCheck threshold merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

G-23B remains blocked until G-23A-E7 explicitly accepts the integrated redesign.
