# N-04G-23F — Next Chat Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Authoritative repository state: GitHub `main`
- G-23A-E: **Complete / Architecture Accepted**
- G-23B: **Complete / Contract Accepted**
- G-23C: **Complete / Contract Accepted**
- G-23D: **Complete / Contract Accepted**
- G-23E: **Complete / Contract Accepted**
- Current task: **N-04G-23F — v4 Design Integration / Design Freeze**
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Start here in the next chat

Read in this order:

1. `docs/planning/phases/N/N04/post-g12/N04G23F_NEXT_CHAT_HANDOFF.md`
2. `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`
3. `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
4. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
5. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
6. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
7. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
8. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
9. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
10. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
11. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
12. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

---

## 2. Current v4 architecture

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidates
  ↓
V2-S / V2-P / V2-D
  ↓
V2-R-A / V2-R-C where required
  ↓
V3/V4F source support
  ↓ PASS only
Certification
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
application path assignment / exact fact materialization
  ↓
V2 for model-authored Stage 2 candidates
  ↓
V4I for interpretations
  ↓
Final presentation / Material Requirement
  ↓
Terminal / Render authorization
```

No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE.

---

## 3. G-23B frozen input

Stage 1 model output:

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

Application owns request/context/purpose/stage/path/attempt/proposition identity and retry lineage.

`stage1_fact_candidate -> source_fact` is the authoritative role path.

No Stage 1 presentation role, model-owned role, Atomicity PASS, support PASS, certification status or context-limit authority.

---

## 4. G-23C frozen input

Certification is application/validator-owned.

```text
Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certified `claim_text` and `support_refs[]` exactly copy the immutable Stage 1 candidate.

`certified_fact_id` is scoped to one immutable Certified Content artifact and is not a canonical DB Fact ID.

Stage 2 factual authority is Certified Content, not raw Grounded Context.

---

## 5. G-23D frozen input

Stage 2 model-facing fact projection:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Stage 2 output families:

```text
main
  -> Certified Fact IDs only
  -> application exact materialization

interpretation
  -> claim_text + premise_fact_ids[]
  -> Certified Fact premises only

creative
  -> claim_text only
  -> creative purpose only
```

Source factual rewrite does not inherit certification.

No Stage 2 model-authored context-limit or stylistic-expression path.

---

## 6. G-23E frozen input

Normative Decision:

`docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`

Provider structured output is a structural guard only. Application parse/schema/binding validation is mandatory.

### Stage 1 provider schema

- root `candidates[]`
- candidate = `claim_text + support_refs[]`
- dynamic `allowed_support_refs` enum
- request-owned `maxItems`
- `additionalProperties = false`
- duplicate refs checked by application; do not rely on `uniqueItems`

### Stage 2 provider schema

- root `blocks[]`, max 3
- complete `oneOf` alternatives for `main`, `interpretation`, `creative`
- dynamic active `certified_fact_id` enum
- creative alternative only for creative purpose
- duplicate block kinds checked by application
- duplicate IDs checked by application

### Runtime/provider boundary

- LM Studio structured-output path is already operational in historical Reference Workstation evidence.
- current GGUF structured output uses llama.cpp grammar-based sampling.
- provider support for every JSON Schema keyword is not trusted.
- do not rely on `uniqueItems`, `contains/minContains/maxContains`, conditionals or cross-item uniqueness.
- G-24/G-26 must record exact runtime capability probes.

### Retry

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

- stage counters are independent;
- no Stage 2 -> Stage 1 backward retry;
- retry keeps factual inputs/model/settings/schema fixed;
- only attempt identity, lineage, structured retry feedback and new output change;
- attempt 2 is full replacement, not patch/delta;
- no cross-attempt Stage 1 Certified Fact merge;
- no cross-attempt Stage 2 block/candidate merge;
- no fallback to attempt 1 after attempt 2 is authorized;
- feedback cannot introduce new factual authority or validator-written replacement claims.

---

## 7. G-23F exact responsibility

G-23F is the v4 **integration review / Design Freeze** task.

At minimum:

1. Integrate G-23A-E + G-23B/C/D/E into one authoritative end-to-end v4 design.
2. Verify there is no contradictory ownership/authority between Stage 1, Certification, Stage 2 and validation.
3. Freeze contract/version names and end-to-end artifact flow required by implementation.
4. Freeze stage-local retry ordering and active-attempt semantics.
5. Freeze system-owned context-limit / terminal boundary without reintroducing model authority.
6. Verify Material Requirement interaction with Certified Content / Stage 2 output.
7. Freeze evidence/replay artifact tree and minimum hashes/identity bindings.
8. Verify provider schema constraints are optimization guards only and application safety checks are complete.
9. Preserve mandatory G-25A residual classifier selection gate.
10. Produce an implementation handoff for G-24.

G-23F should not implement production code.

---

## 8. Integration questions G-23F must explicitly close

- Does every model-authored natural-language proposition have exactly one validation path?
- Can any source-world factual text reach render without Stage 1 certification?
- Can a model-declared role/status override application-owned path provenance? It must not.
- Can schema-valid text bypass residual Atomicity/Content-Type? It must not where required.
- Can Stage 2 reopen raw Grounded Context or uncertified candidates? It must not.
- Can Certification rewrite candidate text/support bindings? It must not.
- Can attempt 1 and attempt 2 material be silently merged? It must not.
- Can retry feedback introduce new facts or approved replacement prose? It must not.
- Can provider schema limitations weaken application validation? They must not.
- Can a failed classifier benchmark later be bypassed to reach G-26? It must not.

---

## 9. Protected boundaries

Do not change without concrete new failure evidence:

- Frozen 47 Gold labels / required / critical flags.
- G-14 no-silent-post-hoc-atomization intent.
- G-23 two-stage architecture.
- E2 authority order.
- E3 Semi-structured Proposition contract.
- E4 application-owned role provenance / deterministic compatibility.
- E5 fail-closed residual classifier policy.
- G-23B Stage 1 minimal payload / ownership.
- G-23C Certification / Certified Content contract.
- G-23D Stage 2 contract.
- G-23E provider schema / retry / no-cross-attempt-merge policy.
- Retrieval / Similarity / Context Builder.
- canonical DB.
- Source / Evidence / Provenance.
- Object / Version identity.
- MCP read-only boundary.
- unsupported rendered material prohibition.
- fail-closed semantics.

---

## 10. Residual classifier selection remains later

G-23F freezes the interface/gate but does not select the concrete Residual Atomicity / Content-Type models.

Execution remains:

```text
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

If G-25A yields no acceptable candidate:

```text
VALID_FAIL_NO_SELECTION
```

and G-26 remains blocked.

---

## 11. Current state

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

## 12. Immediate next action

Start **N-04G-23F — v4 Design Integration / Design Freeze** from GitHub `main`.
