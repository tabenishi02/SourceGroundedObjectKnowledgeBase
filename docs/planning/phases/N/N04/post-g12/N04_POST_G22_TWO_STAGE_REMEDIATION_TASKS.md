# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-21

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Gate integration decision: `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
- Stage 1 contract: `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
- Certified Content contract: `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
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
G-23D Stage 2 Presentation Generator contract       NEXT
  ↓
G-23E Provider schema + stage-local retry design
  ↓
G-23F v4 design integration / Design Freeze
  ↓
G-24 v4 implementation
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
| N-04G-23 | P0 | Complete / Architecture Accepted | 2-stage generation architecture |
| N-04G-23A | P0 | Complete / valid benchmark | diagnose Atomicity / Role judge |
| N-04G-23A-R | P0 | Complete / valid FAIL / no candidate selected | alternate judge evaluation |
| N-04G-23A-E | P0 | **Complete / Architecture Accepted** | decompose Gate responsibilities |
| N-04G-23A-E1 | P0 | Complete | 47 Gold responsibility mapping |
| N-04G-23A-E2 | P0 | Complete | V2 authority/order boundary |
| N-04G-23A-E3 | P0 | Complete | Semi-structured Proposition contract |
| N-04G-23A-E4 | P0 | Complete | application-owned role provenance / compatibility matrix |
| N-04G-23A-E5 | P0 | Complete | residual classifier scope/evaluation design |
| N-04G-23A-E6 | P0 | Complete / Gate PASS with residual Atomicity risk | 47-Gold desk replay / coverage |
| N-04G-23A-E7 | P0 | **Complete / Architecture Accepted** | integration / G-23B unblock |
| N-04G-23B | P0 | **Complete / Contract Accepted** | Stage 1 Content Planner contract |
| N-04G-23C | P0 | **Complete / Contract Accepted** | Certification / Certified Content contract |
| N-04G-23D | P0 | **NEXT** | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | Planned | provider schema + stage-local retry |
| N-04G-23F | P0 | Planned | v4 Design Freeze |
| N-04G-24 | P0 | Blocked by G-23F | implementation |
| N-04G-25A | P0 | Blocked by G-24 | Residual classifier benchmark / selection |
| N-04G-25B | P0 | Blocked by G-25A PASS | integrated adversarial regression |
| N-04G-26 | P0 | Blocked by G-25B PASS | Reference Workstation freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. Integrated v4 V2 architecture

```text
Structured Proposition Candidate
  ↓
V2-S schema/construction
  ↓
V2-P application-owned role provenance
  ↓
V2-D deterministic purpose/presentation/binding compatibility
  ↓ PASS only
V2-R-A narrow Atomicity classification if required
  ↓ ATOMIC only
V2-R-C content-only classification if required
  ↓ role compatibility comparison
V3/V4 support / derivation
```

Key invariants:

- model-authored role is not authority;
- deterministic policy mismatch never goes to a classifier for rescue;
- Atomicity and Content Type are separate tasks;
- expected role/purpose/presentation are not shown to Content-Type classifier;
- model-authored free text is not Atomic merely because schema-valid;
- ambiguity/unavailability fail closed;
- support/truth/derivation remain downstream responsibilities;
- no silent post-hoc atomization.

## 4. E6 coverage result

```text
Critical total                            33
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

Broad joint Atomicity/Role Judge is eliminated. Residual Atomicity remains the largest implementation risk and is not considered solved by desk replay.

## 5. E7 decision

`G-23A-E` is accepted because the remaining unknown is concrete component performance, not unresolved authority ownership.

Residual Atomicity is classified as a bounded implementation/benchmark risk because:

1. V2-R-A has a fixed narrow taxonomy and interface.
2. ambiguity/unavailability fail closed.
3. no earlier structural/policy failure can be overridden.
4. G-23B can consume the candidate contract without concrete classifier identity.
5. concrete classifier selection has an explicit mandatory downstream gate.

Acceptance is not a classifier selection and does not imply N-04 readiness.

## 6. G-23B result

Authority: `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`

G-23B is **Complete / Contract Accepted**.

Stage 1 provider-facing model payload is intentionally minimal:

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

Application constructs the authoritative envelope after parse:

```text
contract/request identity
context_fingerprint
purpose
stage = stage1
path = stage1_fact_candidate
attempt
proposition_id
candidate_index
retry lineage
```

Key decisions:

- application-owned metadata is not echoed by the model;
- `stage1_fact_candidate -> source_fact` remains V2-P authority;
- Stage 1 has no presentation role;
- non-empty candidate requires `support_refs[] >= 1`;
- support-ref presence is not support/entailment proof;
- `claim_text` is one authoritative model-authored content field;
- schema validity does not prove semantic Atomicity;
- optional semantic anchors are excluded from v1;
- `candidates: []` is allowed and does not create model-owned `context_limit` authority;
- validation never silently rewrites a failed candidate;
- retry creates a new proposition identity with application-owned lineage;
- concrete V2-R-A/V2-R-C selection remains G-25A.

## 7. G-23C result

Authority: `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`

G-23C is **Complete / Contract Accepted**.

Certification is application/validator-owned and does not generate or repair factual content.

Artifact separation:

```text
Structured Proposition Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certification eligibility requires:

```text
candidate/reference identity valid
AND aggregate V2 PASS
AND source-support aggregate PASS
AND candidate/validation digest bindings match
AND no unresolved FAIL / INDETERMINATE / UNAVAILABLE
```

Key decisions:

- `certified_fact_id` is application-owned and scoped to one immutable Certified Content artifact;
- it is not a new canonical DB Fact ID;
- certified `claim_text` and `support_refs[]` are exact copies of the immutable Stage 1 candidate;
- Certification cannot rewrite, atomize, merge support or add new source-world facts;
- Validation Record owns validation verdict/evidence; Certified Fact binds it by ID/digest rather than becoming a duplicate validation authority;
- a Certified Content artifact cannot mix different `context_fingerprint` values;
- Stage 2 primary factual authority is Certified Content, not raw Grounded Context;
- Stage 2 interpretation premises must reference `certified_fact_id` values;
- exact duplicate minimum handling prevents trivial material-count inflation without introducing semantic-equivalence judging;
- empty Certified Content is valid audit evidence but is not a `context_limit` verdict;
- cross-attempt salvage/inclusion remains G-23E scope;
- concrete Residual classifier selection remains G-25A.

## 8. G-23D immediate scope

Next task: **N-04G-23D — Stage 2 Presentation Generator Contract**.

G-23D must define at least:

1. Stage 2 request envelope and model-facing Certified Content projection.
2. application-owned `certified_fact_materialization` path.
3. source facts without model-authored factual rewrite.
4. `stage2_interpretation_candidate` with Certified Fact premise IDs.
5. `stage2_creative_candidate` and purpose restriction.
6. presentation-role/block structure and cardinality semantics.
7. purpose-specific output-kind compatibility.
8. duplicate/escaped presentation prevention.
9. Stage 2 output -> V2/V4I/final validation handoff.
10. evidence fields required by G-23E/G-23F/G-26.

Primary handoff:

`docs/planning/phases/N/N04/post-g12/N04G23D_NEXT_CHAT_HANDOFF.md`

## 9. Mandatory downstream classifier gate

Authority: `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`

`G-25A` performs dataset construction, candidate comparison, threshold/abstention freeze, Frozen 47 final confirmation and concrete V2-R-A/V2-R-C selection.

If all candidates fail:

```text
VALID_FAIL_NO_SELECTION
```

and G-26 remains blocked. Gate weakening is prohibited.

`G-25B` then evaluates the selected components in the full v4 pipeline. Only PASS unblocks G-26.

## 10. Protected boundaries

Do not change without new evidence:

- Frozen 47 Gold labels/flags and G-23A/G-23A-R evidence
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured proposition contract
- E4 application-owned role provenance
- E5 zero-critical-FP/fail-closed classifier selection policy
- G-23B Stage 1 minimal payload / application envelope ownership
- G-23C Certification / Certified Content contract
- MiniCheck threshold/profile merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 11. Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = Complete / Contract Accepted
G-23D   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## 12. Immediate next task

**N-04G-23D — Stage 2 Presentation Generator Contract**
