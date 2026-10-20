# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-20

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Adopted architecture: `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- Gate responsibility redesign: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- E1 mapping: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
- E2 boundary: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- E3 proposition contract: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
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
G-23A-E Gate Responsibility Decomposition           In Progress
  ├─ E1 47-Gold Responsibility Mapping              Complete
  ├─ E2 v4 V2 Responsibility Boundary               Complete
  ├─ E3 Structured Proposition Contract             Complete
  ├─ E4 Role Provenance / Compatibility Matrix      NEXT
  ├─ E5 Residual Classifier Evaluation Design       Planned
  ├─ E6 47-Gold Desk Replay                         Planned
  └─ E7 Integration / Unblock Review                Planned
  ↓ ACCEPTED only
G-23B Stage 1 Grounded Content Planner contract     blocked by G-23A-E
  ↓
G-23C Certification / Certified Content contract
  ↓
G-23D Stage 2 Presentation Generator contract
  ↓
G-23E Provider schema + stage-local retry design
  ↓
G-23F v4 design integration / Design Freeze
  ↓
G-24 v4 implementation
  ↓
G-25 dev benchmark / adversarial regression
  ↓
G-26 Reference Workstation v4 harness freeze
  ↓
G-27 Formal v4 Re-Acceptance
  ↓ PASS only
N-04 Complete
  ↓
N-05 unblocked
```

Historical G-18/G-21/G-22 artifacts remain immutable evidence.

## 2. Task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | Complete / Architecture Accepted | 2-stage LLM generation adopted for v4 |
| N-04G-23A | P0 | Complete / valid benchmark | diagnose Atomicity / Role judge |
| N-04G-23A-R | P0 | Complete / valid FAIL / no candidate selected | evaluate alternate judge candidates |
| N-04G-23A-E | P0 | **In Progress** | decompose Gate responsibilities |
| N-04G-23A-E1 | P0 | Complete | 47 Gold responsibility mapping |
| N-04G-23A-E2 | P0 | Complete | V2 authority/order boundary |
| N-04G-23A-E3 | P0 | **Complete** | Structured Proposition contract |
| N-04G-23A-E4 | P0 | **NEXT** | role provenance / deterministic compatibility matrix |
| N-04G-23A-E5 | P0 | Planned | residual classifier scope/evaluation |
| N-04G-23A-E6 | P0 | Planned | 47-Gold desk replay / coverage |
| N-04G-23A-E7 | P0 | Planned | integration / G-23B unblock review |
| N-04G-23B | P0 | Blocked by G-23A-E | Stage 1 Content Planner contract |
| N-04G-23C | P0 | Planned | Certified Content contract |
| N-04G-23D | P0 | Planned | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | Planned | provider schema + stage-local retry |
| N-04G-23F | P0 | Planned | v4 Design Freeze |
| N-04G-24 | P0 | Blocked by G-23F | implementation |
| N-04G-25 | P0 | Blocked by G-24 | dev benchmark/regression |
| N-04G-26 | P0 | Blocked by G-25 | Reference Workstation freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. E1 result

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
Gold label changes        0
```

## 4. E2 result

v4 V2 authorities:

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

Earlier structural/policy failure cannot be overridden by later semantic/support PASS. `MIXED_CONTENT` fails; `AMBIGUOUS/INDETERMINATE` fails closed.

## 5. E3 result

Selected contract family: **Option B — Semi-structured proposition record**.

Core structure:

```text
Application-owned envelope
  ├─ contract/context/purpose
  ├─ stage/path provenance
  ├─ attempt/retry lineage
  └─ proposition identity
        ↓
Path-specific payload
  ├─ one claim_text
  ├─ optional non-authoritative anchors
  └─ support_refs OR premise_fact_ids as allowed by path
```

Key decisions:

- no generator-owned semantic-role authority;
- candidate / validation / certification are separate artifacts;
- Stage 1 source fact uses `support_refs[]`;
- Stage 2 interpretation uses certified `premise_fact_ids[]`, not raw K refs as proof;
- support and premise bindings cannot coexist;
- application/system-owned deterministic records may be `PASS_BY_CONSTRUCTION`;
- model-authored free-text starts as `REVIEW_REQUIRED` unless later construction path proves otherwise;
- residual atomicity resolves review-required records in E5 design;
- no silent post-hoc atomization;
- fully normalized subject/predicate/object ontology is not adopted for the common contract.

## 6. E4 immediate scope

Design exact application-owned role provenance and deterministic compatibility matrix.

Minimum paths:

```text
stage1_fact_candidate
stage2_interpretation_candidate
stage2_creative_candidate
system_context_limit
```

Matrix dimensions:

```text
path / normalized role
purpose
presentation_role
support requirement
premise requirement
model/system ownership
```

Required outputs:

- exact path -> normalized role mapping;
- allowed purpose and presentation mapping;
- required/forbidden support/premise fields;
- system-only restrictions;
- deterministic failure codes;
- explicit construction paths allowed to skip residual semantic classification, if any.

Deliverable:

`docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`

## 7. Protected boundaries

Do not change without new evidence:

- frozen 47 Gold labels/flags and G-23A/G-23A-R evidence
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage architecture
- MiniCheck threshold merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 8. Immediate next task

**N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design**

E3 fixed the candidate structure and field ownership. E4 now makes role provenance and all metadata-known compatibility decisions deterministic before residual semantic classification.