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
- Current task: **N-04G-23A-E2 — v4 V2 Responsibility Boundary Design**
- G-23B: **blocked until G-23A-E is accepted**

## Read first

1. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
2. `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
3. `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
4. `docs/planning/phases/N/N04/post-g12/N04G23AE_GATE_RESPONSIBILITY_DECOMPOSITION_TASKS.md`
5. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
6. `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`
7. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
8. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

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

Atomicity / Role Gate is no longer assumed to be an all-in-one general-purpose LLM judge.

Target responsibility model:

```text
Structured Proposition Record
  ↓
Structural validation
  ↓
Application-owned role provenance
  ↓
Deterministic role/purpose/presentation compatibility
  ↓
Residual semantic classifier only when necessary
  ↓
fail-closed support / certification path
```

## G-23A-E1 result

47 Gold responsibility mapping is complete without changing Gold labels or flags.

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
TOTAL                    47

Required                41
Optional                 6
Critical                33
Critical without owner   0
```

Authority by owner:

### STRUCTURAL

Primary authority is the Structured Proposition contract / structural validator. Residual compound-risk detection may guard free text, but cannot replace the structural authority or use punctuation/conjunction alone as the verdict.

### DETERMINISTIC_POLICY

Known stage/path + purpose + presentation incompatibility must be rejected deterministically before semantic classification. No LLM is needed to rediscover these policy rules.

### RESIDUAL_SEMANTIC

Natural-language content type must be read content-first and compared with application-owned provenance. Truth/support is outside this classifier. `MIXED` / `AMBIGUOUS` remains fail-closed.

### COMBINED

Structural and semantic/policy failures are separate verdicts. Neither may silently override or absorb the other.

### OPTIONAL_AMBIGUOUS

The six optional Gold cases remain explicitly ambiguous. Do not force-label them to improve coverage or metrics.

## Current task: G-23A-E2

Design and freeze the **responsibility boundary**, not the final implementation.

Required decisions:

1. exact validation order;
2. structural hard-fail conditions;
3. compound-risk conditions that escalate rather than decide by themselves;
4. authoritative role provenance source;
5. deterministic compatibility hard-fail matrix boundary;
6. residual classifier invocation conditions;
7. `MIXED_CONTENT` / `AMBIGUOUS` behavior;
8. stage-local failure evidence and retry handoff;
9. downstream support/derivation override prohibition.

Target flow:

```text
Structured Proposition
  ↓
Structural validation
  ↓
Role provenance normalization
  ↓
Deterministic compatibility
  ↓
Residual semantic classification if required
  ↓
Support / derivation validation
```

Expected deliverable:

`docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

Gate:

- every verdict source has exactly one authority;
- earlier deterministic/structural violation cannot be overridden by later semantic/support PASS;
- G-14 fail-closed and no-silent-post-hoc-atomization remain protected;
- E1 mapping remains unchanged unless a documented redesign explicitly reopens E1.

## Following tasks

```text
G-23A-E1 47-Gold Responsibility Mapping             Complete
G-23A-E2 v4 V2 Responsibility Boundary              NEXT
G-23A-E3 Structured Proposition Contract            Planned
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