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
G-23F v4 design integration / Design Freeze         NEXT
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
| N-04G-23D | P0 | **Complete / Contract Accepted** | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | **Complete / Contract Accepted** | provider schema + stage-local retry |
| N-04G-23F | P0 | **NEXT** | v4 Design Freeze |
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

Stage 1 model payload is intentionally minimal:

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

Application owns contract/context/purpose/stage/path/attempt/proposition identity and retry lineage.

Key decisions:

- `stage1_fact_candidate -> source_fact` is application-owned authority;
- no Stage 1 presentation role;
- non-empty candidate requires `support_refs[] >= 1`;
- support-ref presence is not support/entailment proof;
- schema validity does not prove Atomicity;
- optional semantic anchors are excluded from v1;
- `candidates: []` is not a model-owned context-limit verdict;
- failed candidate is immutable;
- concrete V2-R-A/V2-R-C selection remains G-25A.

## 7. G-23C result

Authority: `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`

G-23C is **Complete / Contract Accepted**.

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

- certification is application/validator-owned;
- `certified_fact_id` is scoped to one immutable Certified Content artifact and is not a canonical DB Fact ID;
- certified `claim_text` and `support_refs[]` exactly copy the Stage 1 candidate;
- certification cannot rewrite, atomize, merge support or create new source-world facts;
- Validation Record owns validation verdict/evidence;
- one Certified Content artifact cannot mix context fingerprints;
- Stage 2 factual authority is Certified Content, not raw Grounded Context;
- interpretation premises use `certified_fact_id` values;
- exact duplicate minimum handling prevents trivial count inflation;
- empty Certified Content is audit evidence only, not context-limit;
- cross-attempt salvage/inclusion was deferred to G-23E and is now closed by active-attempt replacement.

## 8. G-23D result

Authority: `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`

G-23D is **Complete / Contract Accepted**.

Stage 2 model-facing factual projection is intentionally minimal:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Stage 2 logical output uses ordered blocks:

```text
main
  -> Certified Fact IDs only
  -> application exact materialization

interpretation
  -> model claim_text + premise_fact_ids[]
  -> Certified Fact IDs only as premises

creative
  -> model claim_text
  -> creative purpose only
```

Key decisions:

- model may select Certified Fact IDs, but cannot rewrite source factual text and inherit certification;
- `certified_fact_materialization` is application-owned and exact;
- Stage 2 model does not receive raw Grounded Context as a new factual authority;
- interpretation path is `stage2_interpretation_candidate` and requires V2 + V4I;
- creative path is `stage2_creative_candidate`, allowed only for `purpose = creative`, and remains subject to V2 semantic boundary checks;
- no model-authored `context_limit` or `stylistic_expression` path is reintroduced;
- normal block kinds are `main`, `interpretation`, `creative`;
- each block kind has cardinality 0 or 1; duplicate kind is deterministic failure;
- block order is presentation order, not semantic authority;
- `blocks: []` is allowed as no proposal and is not context-limit;
- source fact / interpretation / creative remain structurally separate through final rendering;
- no-new-source-fact rule applies after Certification.

## 9. G-23E result

Authority: `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`

G-23E is **Complete / Contract Accepted**.

Provider structured output is a structural guard only. Application-side parse/schema/reference/binding validation remains mandatory.

Provider schema decisions:

```text
Stage 1
  candidates[]
    claim_text
    support_refs[]
  dynamic K allow-list enum
  request-owned candidate max

Stage 2
  blocks[] max 3
  complete oneOf alternatives:
    main
    interpretation
    creative where purpose permits
  dynamic active Certified Fact enum
```

Runtime/schema safety decisions:

- existing Reference Workstation evidence proves the LM Studio structured-output path is operational;
- provider acceptance of a schema does not prove every JSON Schema keyword is enforced;
- do not rely on provider `uniqueItems`, `contains/minContains/maxContains`, conditionals or cross-item property uniqueness;
- duplicate support/premise IDs and duplicate Stage 2 block kinds are application-enforced;
- application revalidates complete provider output against the instantiated schema;
- provider/schema binding mismatch or provider unavailability is fail-closed SYSTEM_FAILURE;
- G-24/G-26 must record exact runtime capability probes.

Retry decisions:

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

- counters are stage-local and independent;
- no Stage 2 -> Stage 1 backward retry in the same run;
- retry inputs keep Context/Certified Content, purpose, model, settings and schema fixed;
- only attempt identity, lineage, structured feedback and new output may change;
- Stage 1 candidate-level certification inside one attempt is allowed by design;
- if Stage 1 attempt 2 is invoked, attempt 2 fully replaces attempt 1 as the active factual attempt;
- no cross-attempt Certified Fact merge and no fallback to attempt 1;
- Stage 2 failed plan is not partially rendered;
- if Stage 2 attempt 2 is invoked, attempt 2 fully replaces attempt 1 as the active plan;
- retry feedback is diagnostic only and cannot introduce new facts or validator-written replacement claims.

## 10. G-23F immediate scope

Next task: **N-04G-23F — v4 Design Integration / Design Freeze**.

G-23F must integrate the accepted G-23A-E + G-23B/C/D/E decisions into one authoritative implementation-ready v4 design.

At minimum:

1. End-to-end authority/ownership consistency review.
2. Contract/version and artifact-flow integration.
3. Candidate -> Validation -> Certification -> Stage 2 -> final validation traceability.
4. stage-local retry ordering and active-attempt semantics.
5. system-owned context-limit / terminal boundary.
6. Material Requirement interaction.
7. provider/application validation split.
8. evidence/replay artifact tree and identity bindings.
9. preservation of mandatory G-25A residual classifier Gate.
10. G-24 implementation handoff.

Primary handoff:

`docs/planning/phases/N/N04/post-g12/N04G23F_NEXT_CHAT_HANDOFF.md`

## 11. Mandatory downstream classifier gate

Authority: `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`

`G-25A` performs dataset construction, candidate comparison, threshold/abstention freeze, Frozen 47 final confirmation and concrete V2-R-A/V2-R-C selection.

If all candidates fail:

```text
VALID_FAIL_NO_SELECTION
```

and G-26 remains blocked. Gate weakening is prohibited.

`G-25B` evaluates selected components in the full v4 pipeline. Only PASS unblocks G-26.

## 12. Protected boundaries

Do not change without new evidence:

- Frozen 47 Gold labels/flags and G-23A/G-23A-R evidence
- G-14 safety intent / no silent post-hoc atomization
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured proposition contract
- E4 application-owned role provenance
- E5 zero-critical-FP/fail-closed classifier selection policy
- G-23B Stage 1 contract
- G-23C Certification / Certified Content contract
- G-23D Stage 2 Presentation Generator contract
- G-23E Provider Schema / Stage-local Retry contract
- MiniCheck threshold/profile merely to improve acceptance
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 13. Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = Complete / Contract Accepted
G-23D   = Complete / Contract Accepted
G-23E   = Complete / Contract Accepted
G-23F   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## 14. Immediate next task

**N-04G-23F — v4 Design Integration / Design Freeze**
