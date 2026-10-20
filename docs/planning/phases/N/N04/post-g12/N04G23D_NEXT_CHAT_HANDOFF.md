# N-04G-23D — Next Chat Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Authoritative repository state: GitHub `main`
- G-23A-E: **Complete / Architecture Accepted**
- G-23B: **Complete / Contract Accepted**
- G-23C: **Complete / Contract Accepted**
- Current task: **N-04G-23D — Stage 2 Presentation Generator Contract**
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Start here in the next chat

Read in this order:

1. `docs/planning/phases/N/N04/post-g12/N04G23D_NEXT_CHAT_HANDOFF.md`
2. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
3. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
4. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
5. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
6. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
7. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
8. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
9. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

---

## 2. Current architecture

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidate
  ↓
V2 / V3 / V4 validation
  ↓ PASS only
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
Final validation / Material / Terminal / Render
```

No downstream authority may rescue an earlier FAIL or INDETERMINATE.

---

## 3. G-23C frozen input to G-23D

Certification is application/validator-owned.

Artifact separation:

```text
Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certified Fact is issued only after required V2 + source-support PASS.

Certified source fact logical form:

```text
certified_fact_id
source_proposition_id
source_candidate_digest
claim_text              exact Stage 1 copy
support_refs[]          exact Stage 1 copy
validation_record_id
validation_record_digest
request_id
context_fingerprint
purpose
source_attempt
source_candidate_index
```

Important decisions:

- `certified_fact_id` is application-owned.
- It is stable within one immutable Certified Content artifact, not a new canonical DB Fact ID.
- Certification never rewrites `claim_text` or changes `support_refs`.
- Certified Content cannot mix different `context_fingerprint` values.
- Stage 2 primary factual authority is Certified Content, not raw Grounded Context.
- raw Grounded Context must not be reopened as a new source-fact generation path.
- exact duplicate minimum handling prevents trivial count inflation; semantic paraphrase merging is not performed.
- empty Certified Content is allowed as audit evidence but is not a `context_limit` verdict.
- cross-attempt salvage/inclusion policy is deferred to G-23E.

Reserved E4 path:

```text
certified_fact_materialization
  -> normalized role source_fact
  -> application-owned
  -> no new model-authored factual text
```

Stage 2 interpretation premises must reference `certified_fact_id` values.

---

## 4. G-23D exact responsibility

Design the **Stage 2 Presentation Generator contract** only.

At minimum G-23D should fix:

1. Stage 2 request envelope and application-owned inputs.
2. Minimal model-facing Certified Content projection.
3. Source-fact presentation path using `certified_fact_materialization`.
4. Whether source facts are selected by model ID reference, application planning, or a bounded combination without permitting model-authored factual rewrite.
5. `stage2_interpretation_candidate` response contract.
6. interpretation `premise_fact_ids[] >= 1` rules using Certified Fact IDs only.
7. `stage2_creative_candidate` response contract and creative-purpose restriction.
8. presentation-role/block structure and cardinality semantics.
9. purpose-specific allowed Stage 2 output kinds.
10. prevention of duplicate/escaped presentation roles.
11. final source-fact/interpretation/creative separation.
12. Stage 2 model output -> V2/V4I/final validation handoff.
13. no-new-source-fact rule after certification.
14. evidence fields required by G-23E/G-23F/G-26.

G-23D should produce a normative Decision/contract artifact consumable by G-23E.

---

## 5. G-23D must preserve E4 paths

```text
certified_fact_materialization
  -> source_fact
  -> application-owned
  -> presentation main

stage2_interpretation_candidate
  -> interpretation
  -> model-authored content
  -> premise_fact_ids[] >= 1
  -> support_refs[] forbidden

stage2_creative_candidate
  -> creative_addition
  -> model-authored content
  -> creative purpose only
  -> support_refs[] forbidden
  -> premise_fact_ids[] forbidden as grounding proof

system_context_limit
  -> context_limit
  -> application/system-owned only
```

Stage 2 must not introduce a generator-declared `semantic_role` authority.

---

## 6. Source-fact presentation direction

G-23C preserves E4's safest direction:

```text
Certified Fact exact content
  ↓
application-owned certified_fact_materialization
  ↓
final source-fact material
```

Stage 2 must not gain authority to freely paraphrase a Certified Fact and treat the paraphrase as already-certified factual content.

If G-23D considers any deterministic surface normalization, it must be application-owned, bounded, replayable and unable to add a proposition. A model-authored factual rewrite would create a new proposition and must not inherit certification automatically.

---

## 7. Interpretation boundary

Stage 2 interpretation candidate must use:

```text
claim_text
premise_fact_ids[]
```

Premises must resolve to Certified Facts from the active Certified Content artifact.

Forbidden interpretation proof:

```text
raw K support refs
uncertified Stage 1 candidates
model memory
raw Grounded Context reopened as premise
```

Interpretation remains subject to V2 Atomicity/Content-Type and V4I derivation validation.

---

## 8. Creative boundary

Creative material is allowed only where purpose/material policy permits it.

Creative candidate must not carry Certified Fact support binding as proof that invented content is factual.

Source-world factual assertions hidden inside creative content remain a semantic boundary violation and must fail closed.

---

## 9. Provider schema / retry scope remains later

G-23D defines logical contracts and presentation semantics.

Provider-specific JSON Schema support, exact structured-output feature probes, stage-local retry message layout and cross-attempt salvage are G-23E responsibilities.

Do not weaken acceptance because a provider cannot enforce a desired cardinality rule in-schema; application deterministic validation remains available.

---

## 10. Protected boundaries

Do not change without new failure evidence:

- Frozen 47 Gold labels / flags.
- G-14 no-silent-post-hoc-atomization intent.
- G-23 two-stage architecture.
- E2 authority order.
- E3 Semi-structured Proposition contract.
- E4 application-owned role provenance / deterministic compatibility matrix.
- E5 fail-closed residual classifier policy.
- G-23B Stage 1 minimal payload / ownership.
- G-23C Certification / Certified Content contract.
- Retrieval / Similarity / Context Builder.
- canonical DB.
- Source / Evidence / Provenance.
- Object / Version identity.
- MCP read-only boundary.
- unsupported rendered material prohibition.
- fail-closed semantics.

---

## 11. Residual classifier selection remains later

G-23D does not select Residual Atomicity / Content-Type models.

Concrete selection remains `N-04G-25A` after implementation.

If no candidate satisfies the zero-tolerance selection gate, result is `VALID_FAIL_NO_SELECTION` and G-26 remains blocked.

---

## 12. Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = Complete / Contract Accepted
G-23D   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## 13. Immediate next action

Start **N-04G-23D — Stage 2 Presentation Generator Contract** from GitHub `main`.
