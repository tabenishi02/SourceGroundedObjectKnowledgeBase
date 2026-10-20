# N-04G-23E — Provider Schema + Stage-local Retry Design

更新日: 2026-10-21

- Status: **Complete / Contract Accepted**
- Parent: `N-04G-23 — Two-Stage Grounded Generation Architecture`
- Predecessor: `N-04G-23D — Complete / Contract Accepted`
- Next: `N-04G-23F — v4 Design Integration / Design Freeze`
- N-04: **Failed / not Complete**
- N-05: **blocked**

Authority:

- `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
- `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
- `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- historical retry implementation: `src/sgokb/grounding/failure.py`
- historical v3 formal runtime: `benchmark/n04-v3-formal-harness-v1.json`

---

## 1. Decision summary

G-23Eは、G-23B/C/Dで固定したsemantic contractを変更せず、次をfreezeする。

1. Stage 1 provider-facing response schema template。
2. Stage 2 provider-facing response schema template。
3. dynamic allow-list / budgetをschema instanceへ投影する規則。
4. provider-enforced constraintとapplication-enforced invariantの境界。
5. structured-output runtime capabilityについて安全に依存できるsubset。
6. parse / schema / binding failure semantics。
7. Stage 1 / Stage 2の独立したstage-local retry budget。
8. retry trigger / feedback / fixed-input invariants。
9. cross-attempt mergeを禁止するactive-attempt policy。
10. provider/schema/prompt/retry artifact identity requirements。

Normative retry shape:

```text
Stage 1 attempt 1
  ↓ validate / certify / stage-readiness
  ├─ ready -> freeze active Certified Content
  └─ retryable -> Stage 1 attempt 2, full replacement
                    ↓
                  freeze active Certified Content or fail

active Certified Content
  ↓
Stage 2 attempt 1
  ↓ final validation / material readiness
  ├─ ready -> final result
  └─ retryable -> Stage 2 attempt 2, full replacement
                    ↓
                  final result or fail
```

Stage 2 failureからStage 1へ戻るbacktracking loopはv4 baselineでは行わない。

Concrete Residual Atomicity / Content-Type classifierのmodel/checkpoint/thresholdは本Taskでは選定しない。`N-04G-25A`の責務である。

---

## 2. Provider schema is a structural guard, not semantic authority

Provider structured outputは構造エラーを減らすためのguardであり、grounding authorityではない。

Schema-validでも次は証明されない。

```text
Atomicity
Content-Type correctness
support / entailment
interpretation derivability
creative factual safety
certification
material sufficiency
```

Applicationはprovider resultをraw evidenceとして保存した後、必ず独立にparseし、同じinstantiated schemaとdeterministic invariantsを再検証する。

```text
provider constrained generation
  ↓
raw output retained
  ↓
application JSON parse
  ↓
application schema validation
  ↓
application reference/binding/cardinality validation
  ↓
semantic validation where required
```

Providerがschemaを受理した事実をPASS evidenceへ昇格させない。

---

## 3. Runtime capability conclusion

### 3.1 Existing SGOKB evidence

G-21/G-22 Reference WorkstationではLM Studio structured outputを使用し、v3 `GENERATION_OUTPUT_SCHEMA`のneutral structured-output smokeをpreflight requirementとして通している。

従って、SGOKB Reference Workstation上で少なくとも:

```text
JSON structured-output path is operational
schema-constrained generation can return parseable conforming JSON
```

ことは既存evidenceで確認済みである。

ただし、positive smokeは**schema keywordのすべてがgrammar engineで厳密に強制されたことを証明しない**。

### 3.2 Current provider/engine research

Current LM Studio documentation states that JSON Schema can be supplied to structured response / OpenAI-compatible `response_format`, and GGUF structured output uses llama.cpp grammar-based sampling.

Current llama.cpp grammar documentation/code identifies a supported subset and documents important limitations. In particular、`uniqueItems`、`contains/minContains`、conditionals等をprovider enforcementとして依存してはならない。

Reference sources reviewed for G-23E:

- LM Studio — Structured Response / Structured Output
- llama.cpp — `grammars/README.md`
- llama.cpp — `common/json-schema.cpp`
- llama.cpp — `common/json-schema-to-grammar.cpp`

Because the exact frozen G-26 runtime may differ from current upstream, G-23E adopts the conservative rule:

> **Provider feature support is optimization evidence; application validation is the safety authority.**

### 3.3 Provider-safe schema subset used by v4

G-23E schemas intentionally rely only on a small structural subset:

```text
type
properties
required
additionalProperties = false
items
minItems / maxItems
enum
const
oneOf using complete alternative object schemas
string minLength
```

Do not rely on provider enforcement of:

```text
uniqueItems
contains / minContains / maxContains
if / then / else
not
dependentSchemas
cross-item uniqueness by property
semantic regex meaning
```

Even for the provider-safe subset, application-side validation remains mandatory.

### 3.4 Required implementation/runtime probe

G-24 implementation and G-26 freeze must record a capability probe for the exact provider/runtime used in v4.

Minimum probe matrix:

```text
Stage 1 valid empty candidates
Stage 1 valid candidate with allow-listed support ref
Stage 1 extra property attempt
Stage 1 out-of-allow-list support ref attempt
Stage 2 valid main block
Stage 2 valid interpretation block
Stage 2 creative block under creative purpose
Stage 2 invalid/out-of-set Certified Fact ID attempt
provider interruption / incomplete generation handling
application rejection of duplicate support/premise IDs
application rejection of duplicate block kinds
```

Safety does not depend on provider preventing the last two cases.

---

## 4. Stage 1 provider-facing schema

Contract/template identity:

```text
sgokb.stage1-provider-output.v1
```

Provider response remains exactly the G-23B payload family:

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

### 4.1 Instantiated schema template

The application deterministically instantiates the provider schema from:

```text
candidate_budget.max_candidates
allowed_support_refs[]
```

Logical template:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["candidates"],
  "properties": {
    "candidates": {
      "type": "array",
      "minItems": 0,
      "maxItems": "<candidate_budget.max_candidates>",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["claim_text", "support_refs"],
        "properties": {
          "claim_text": {
            "type": "string",
            "minLength": 1
          },
          "support_refs": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "enum": ["<allowed K refs>"]
            }
          }
        }
      }
    }
  }
}
```

`maxItems`のplaceholderは実schemaではintegerへ置換する。

### 4.2 Empty allow-list

`allowed_support_refs[]`が空の場合、applicationはStage 1 schemaを:

```text
candidates.maxItems = 0
```

としてinstantiateする。

空`enum`へ依存しない。

### 4.3 Duplicate support refs

`uniqueItems`へ依存しない。

Applicationがparse後に:

```text
support_refs contains duplicate
-> deterministic reference-integrity failure
```

とする。

### 4.4 Dynamic enum is not support proof

Provider enumはunknown K ID生成を減らすstructural guardである。

```text
ref is in enum
!=
claim is supported by ref
```

Support authorityはV3/V4に残る。

---

## 5. Stage 2 provider-facing schema

Contract/template identity:

```text
sgokb.stage2-provider-output.v1
```

Provider response remains G-23D logical output:

```json
{
  "blocks": [
    {
      "block_kind": "main",
      "certified_fact_ids": ["CF1"]
    },
    {
      "block_kind": "interpretation",
      "candidates": [
        {
          "claim_text": "...",
          "premise_fact_ids": ["CF1"]
        }
      ]
    },
    {
      "block_kind": "creative",
      "candidates": [
        {
          "claim_text": "..."
        }
      ]
    }
  ]
}
```

### 5.1 Dynamic inputs

Stage 2 schema instance is deterministically generated from:

```text
purpose
allowed_output_kinds[]
active Certified Content certified_fact_ids[]
```

Main/interpretation alternatives are omitted if there is no active Certified Fact ID to reference.

Creative alternative is present only when:

```text
purpose = creative
AND creative is present in allowed_output_kinds
```

### 5.2 Logical schema shape

Root:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["blocks"],
  "properties": {
    "blocks": {
      "type": "array",
      "minItems": 0,
      "maxItems": 3,
      "items": {
        "oneOf": [
          "<complete main block schema if allowed>",
          "<complete interpretation block schema if allowed>",
          "<complete creative block schema if allowed>"
        ]
      }
    }
  }
}
```

Main alternative:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["block_kind", "certified_fact_ids"],
  "properties": {
    "block_kind": {"const": "main"},
    "certified_fact_ids": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "enum": ["<active Certified Fact IDs>"]
      }
    }
  }
}
```

Interpretation alternative:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["block_kind", "candidates"],
  "properties": {
    "block_kind": {"const": "interpretation"},
    "candidates": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["claim_text", "premise_fact_ids"],
        "properties": {
          "claim_text": {"type": "string", "minLength": 1},
          "premise_fact_ids": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "enum": ["<active Certified Fact IDs>"]
            }
          }
        }
      }
    }
  }
}
```

Creative alternative:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["block_kind", "candidates"],
  "properties": {
    "block_kind": {"const": "creative"},
    "candidates": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["claim_text"],
        "properties": {
          "claim_text": {"type": "string", "minLength": 1}
        }
      }
    }
  }
}
```

### 5.3 Duplicate block-kind prevention

Provider schemaではduplicate block kindの不存在をauthorityとして証明しない。

`maxItems = 3` only bounds size. It does not imply one-of-each.

Application parse後:

```text
count(block_kind=main) > 1           -> PRESENTATION_DUPLICATE_BLOCK_KIND
count(block_kind=interpretation) > 1 -> PRESENTATION_DUPLICATE_BLOCK_KIND
count(block_kind=creative) > 1       -> PRESENTATION_DUPLICATE_BLOCK_KIND
```

としてdeterministic failする。

`contains/maxContains`は使用しない。

### 5.4 Duplicate IDs

`uniqueItems`はprovider enforcementへ依存しない。

Application checks:

```text
duplicate certified_fact_id in main
-> deterministic failure

duplicate premise_fact_id within one interpretation candidate
-> deterministic failure
```

---

## 6. Provider-enforced vs application-enforced matrix

| Invariant | Provider schema | Application | Semantic authority |
|---|---:|---:|---|
| root/object shape | Guard | Required recheck | No |
| required fields | Guard | Required recheck | No |
| additional fields forbidden | Guard | Required recheck | No |
| block discriminator shape | Guard | Required recheck | No |
| array minimum/maximum structural size | Guard | Required recheck | No |
| K/CF ID allow-list enum | Guard | Required recheck | No |
| duplicate support/premise IDs | Not trusted | **Required** | No |
| duplicate block kind | Not expressively trusted | **Required** | No |
| context / Certified Content binding | No | **Required** | No |
| purpose compatibility | Partial schema narrowing | **Required** | V2-D |
| Atomicity | No | Required semantic Gate | V2-R-A |
| Content Type | No | Required semantic Gate | V2-R-C |
| source support | No | Required | V3/V4F |
| interpretation derivation | No | Required | V4I |
| certification | No | Required | G-23C application boundary |
| material sufficiency | No | Required | Material Gate |

No invariant is allowed to become safer or weaker solely because a provider changes schema support.

---

## 7. Parse / contract failure semantics

Every provider response is first classified into one of the following structural outcomes.

```text
PROVIDER_COMPLETE
PROVIDER_INCOMPLETE
PROVIDER_UNAVAILABLE
```

Only `PROVIDER_COMPLETE` proceeds to JSON parse.

### 7.1 Provider incomplete/unavailable

Examples:

```text
transport failure
model/runtime unavailable
cancellation
context-length termination
max-token termination before complete structured value
missing response payload
```

These are system/runtime failures, not semantic repair opportunities.

```text
-> SYSTEM_FAILURE
-> no alternate model/provider fallback
```

A formal run must not silently retry with changed runtime/settings.

### 7.2 Complete but malformed/schema-invalid output

A complete provider response that is not valid JSON or does not satisfy the instantiated application schema is a retryable generation-contract failure on attempt 1.

Minimum failure codes:

```text
MALFORMED_JSON
PROVIDER_SCHEMA_CONTRACT_VIOLATION
UNEXPECTED_FIELD
MISSING_REQUIRED_FIELD
CARDINALITY_VIOLATION
REFERENCE_ALLOWLIST_VIOLATION
PRESENTATION_DUPLICATE_BLOCK_KIND
DUPLICATE_REFERENCE_ID
```

Attempt 2 failure is terminal for that stage.

### 7.3 Schema identity mismatch

If request evidence says schema hash/version A but the invoked provider adapter used schema B:

```text
SCHEMA_BINDING_MISMATCH
-> SYSTEM_FAILURE
```

Do not treat this as a generator retry.

---

## 8. Retry budget and stage boundaries

v4 uses **one retry per generator stage**.

```text
Stage 1 max attempts = 2
Stage 1 max retries  = 1

Stage 2 max attempts = 2
Stage 2 max retries  = 1
```

The counters are independent because Stage 1 and Stage 2 are different contracts with different factual authorities.

This does not authorize an unbounded loop.

### 8.1 No backward retry after Stage 2 starts

Once active Certified Content is frozen and Stage 2 starts:

```text
Stage 2 failure
-> Stage 2 retry or terminal outcome
```

not:

```text
Stage 2 failure
-> reopen Stage 1
```

If Stage 2 exposes a design-level lack of certified factual material, the run ends fail-closed. A new top-level run may later start under normal orchestration, but it is not the same retry chain.

---

## 9. Stage 1 retry policy

### 9.1 Candidate-local validation within one attempt

G-23B semantics are retained:

- each candidate is independently validated;
- one candidate failure does not automatically invalidate another candidate;
- only eligible candidates can be certified;
- failed candidates are retained as evidence and never rendered/certified.

This is **normative candidate certification**, not cross-attempt partial salvage.

### 9.2 Stage 1 retry trigger

Attempt 1 may retry when:

```text
complete response is malformed/schema-invalid
reference-integrity failure is repairable by regeneration
NON_ATOMIC / AMBIGUOUS candidate loss leaves stage material insufficient
Content-Type mismatch candidate loss leaves stage material insufficient
unsupported candidate loss leaves stage material insufficient
Stage 1 produced no/insufficient certifiable factual material although supplied Context can still satisfy the requirement
```

A candidate-local failure alone does not require retry if the remaining certified set already satisfies Stage 1 readiness/material requirements.

### 9.3 No retry for deterministic insufficiency/system failure

Do not retry Stage 1 when:

```text
application deterministically concludes supplied Context cannot satisfy required factual material
validator/provider/runtime is unavailable
schema/request binding is corrupt
retry budget exhausted
```

Context insufficiency is handled by application/system-owned policy, not by asking the model to emit `context_limit`.

### 9.4 Stage 1 retry output

Attempt 2 returns a **complete new Stage 1 payload**, not a patch/delta.

```text
{"candidates": [...]}
```

All new candidates receive new application-owned proposition identities.

---

## 10. Stage 1 cross-attempt certification policy

G-23C deferred cross-attempt salvage to G-23E. G-23E adopts:

> **active-attempt replacement; no cross-attempt merge.**

If Stage 1 attempt 2 is invoked:

```text
attempt 1 candidates/certifications remain immutable evidence
attempt 1 Certified Facts become non-active for this run
attempt 2 is the sole source of the active Certified Content set
```

Forbidden:

```text
CF from attempt 1 + CF from attempt 2 -> merged active Certified Content
```

If attempt 2 is worse than attempt 1, the system does not fall back to attempt 1 after retry was authorized.

Reason:

- avoids silent partial salvage across generation histories;
- keeps one active factual-generation attempt per Stage 2 run;
- makes replay / provenance / material counting unambiguous;
- preserves fail-closed behavior.

This rule does not prevent multiple eligible candidates from the **same active attempt** from being certified together.

---

## 11. Stage 2 retry policy

Stage 2 output is one ordered presentation plan.

### 11.1 Retry trigger

Attempt 1 may retry for:

```text
malformed/schema-invalid plan
duplicate block kind
invalid/duplicate Certified Fact binding
invalid/duplicate premise binding
purpose-incompatible block
interpretation Atomicity / Content-Type failure
interpretation derivation failure
creative Atomicity / Content-Type / scope failure
repairable Material Requirement failure where the same Certified Content can satisfy the requirement
```

### 11.2 Whole-plan invalidation

Unlike Stage 1 candidate certification, Stage 2 presentation attempt is consumed as one ordered plan.

If any included Stage 2 model-authored candidate/block fails required final validation:

```text
Stage 2 attempt = not renderable
```

Do not render only the surviving blocks from that failed attempt.

Attempt 2, when authorized, is a complete new `blocks[]` plan.

### 11.3 No retry for impossible material/system failure

Do not retry Stage 2 when:

```text
active Certified Content cannot satisfy required material by construction
provider/validator/runtime unavailable
Certified Content/schema/request binding corrupt
retry budget exhausted
```

Stage 2 may not reopen raw Grounded Context or request new source facts.

---

## 12. Stage 2 cross-attempt policy

Stage 2 uses the same active-attempt replacement principle.

If attempt 2 occurs:

```text
attempt 1 plan remains evidence only
attempt 2 is the sole candidate final presentation plan
```

Forbidden:

```text
main block from attempt 1
+ interpretation block from attempt 2
+ creative block from either
-> merged final plan
```

If attempt 2 fails, do not fall back to attempt 1.

---

## 13. Retry fixed-input invariants

The only permitted retry changes are:

```text
attempt number / attempt identity
retry lineage metadata
structured retry feedback
new model output
```

### Stage 1 fixed across retry

```text
Grounded Context payload
context_fingerprint
purpose
user task / Stage 1 base instruction
allowed_support_refs
candidate budget
provider schema instance
model identity / revision
load profile
inference settings including temperature/max tokens/seed policy
material requirement profile
```

### Stage 2 fixed across retry

```text
active Certified Content payload/digest
minimal Certified Fact projection
context_fingerprint
purpose
presentation instruction
allowed_output_kinds
provider schema instance
model identity / revision
load profile
inference settings
material requirement profile
```

No new Web retrieval, external factual text, alternate provider, extra Grounded Context, new K IDs, or new Certified Facts may be added through retry feedback.

---

## 14. Retry feedback contract

Retry feedback is application-owned and machine-addressable.

Contract identity:

```text
sgokb.stage-local-retry-feedback.v1
```

Logical envelope:

```json
{
  "retry_contract_version": "sgokb.stage-local-retry-feedback.v1",
  "stage": "stage1",
  "previous_attempt": 1,
  "next_attempt": 2,
  "previous_attempt_id": "...",
  "previous_output_digest": "...",
  "failures": [
    {
      "failure_scope": "candidate",
      "failure_code": "...",
      "json_path": "...",
      "proposition_id": "...",
      "claim_text": "<exact failed candidate text when available>",
      "support_refs": ["K3"],
      "premise_fact_ids": [],
      "expected_rule": "...",
      "repair_directive": "..."
    }
  ]
}
```

Stage 2 feedback uses the same envelope with Stage 2 IDs/bindings.

### 14.1 Feedback content rules

Feedback may contain:

```text
exact failed model text already produced
failure code / path / binding IDs
expected structural or semantic boundary rule
bounded repair directive
missing material category/target identity already present in request policy
```

Feedback must not contain:

```text
new source-world fact
new support text not present in fixed input
new K/Certified Fact ID
Web/model-memory factual correction
validator-authored replacement claim
post-hoc atomized replacement text presented as approved answer
```

### 14.2 Repair directives

Safe examples:

```text
return a complete schema-conforming output
use only allow-listed support refs
make each candidate one independently judgeable proposition
remove unsupported extra proposition
use only active Certified Fact IDs
return at most one block per block_kind
remove source-world factual assertion from creative content
make interpretation depend only on listed Certified Fact premises
```

The validator does not write the replacement proposition for the model.

---

## 15. Retry identity / lineage

Every stage generation has an application-owned attempt identity.

Minimum lineage:

```text
stage_run_id
stage
attempt
attempt_id
previous_attempt_id
request identity
schema instance hash
base prompt/template hash
retry feedback hash when present
raw output digest
parsed output digest when parse succeeds
```

Stage 1 proposition IDs and Stage 2 proposition IDs are never reused for changed text.

Retry feedback refers to old IDs only as failure lineage; attempt 2 receives new proposition IDs after parse.

---

## 16. Provider request / schema / prompt evidence

G-23F/G-24/G-26 must preserve at least:

```text
provider adapter identity/version
provider runtime identity/version
model identity / revision / load profile
inference settings
stage request contract version
logical request payload/digest
base prompt/template artifact + exact bytes hash
attempt prompt artifact + exact bytes hash
provider schema template version
instantiated provider schema artifact + exact bytes SHA-256
provider response status/stop reason
raw provider output + digest
application parser/schema-validator version
parsed output + digest
retry feedback artifact + digest when used
attempt lineage
```

For hashes, the persisted UTF-8 artifact bytes are authoritative. G-24 may also define canonical-object digests, but replay must not depend on reconstructing a schema/prompt from memory.

---

## 17. Provider adapter failure policy

If the selected provider/runtime cannot accept the frozen schema instance:

```text
-> SYSTEM_FAILURE
```

Do not silently:

```text
drop structured output
switch to JSON-only mode
remove required schema constraints
switch provider/model
post-process free prose into the contract
```

A future explicitly frozen fallback would require a new design decision and acceptance evidence.

---

## 18. G-23E explicit decisions

### E1 — Stage 1 schema

**Adopted:** minimal `candidates[{claim_text,support_refs[]}]`, dynamic K enum, request-owned candidate max.

### E2 — Stage 2 schema

**Adopted:** `blocks[]` with complete `oneOf` block alternatives, dynamic Certified Fact enum, purpose-based creative alternative.

### E3 — Unsupported schema keywords

**Do not rely on provider `uniqueItems` / `contains` / conditionals.** Application performs duplicate/cardinality/binding checks.

### E4 — Duplicate block kinds

**Application deterministic failure.** Provider schema is only a guard.

### E5 — Retry budget

**One retry per stage, max two attempts per stage.** No backward Stage 2 -> Stage 1 retry.

### E6 — Stage 1 cross-attempt salvage

**No merge. Attempt 2 fully replaces attempt 1 as active factual attempt.**

### E7 — Stage 2 cross-attempt salvage

**No merge. Attempt 2 fully replaces attempt 1 as active presentation plan.**

### E8 — Retry feedback

**Structured, application-owned, diagnostic only; no new factual authority or validator-written replacement claims.**

### E9 — Provider/app authority

**Application revalidation is mandatory even when provider reports structured success.**

---

## 19. What G-23E does not decide

G-23E does not freeze:

- concrete Residual Atomicity classifier/model/checkpoint/threshold;
- concrete Residual Content-Type classifier/model/checkpoint/threshold;
- Stage 1/Stage 2 production generator checkpoint for v4;
- final G-26 Reference Workstation runtime/version;
- G-24 code organization;
- G-25A benchmark outcome;
- G-27 acceptance result.

G-23F integrates B/C/D/E into one v4 frozen design before implementation.

---

## 20. Acceptance checklist

- [x] Stage 1 provider schema is fixed.
- [x] Stage 2 provider schema is fixed.
- [x] dynamic K / Certified Fact allow-list projection is fixed.
- [x] provider vs application enforcement boundary is explicit.
- [x] runtime capability limitations are accounted for conservatively.
- [x] duplicate block kind is application-enforced.
- [x] parse/schema/system failure semantics are defined.
- [x] Stage 1 retry trigger and output replacement semantics are fixed.
- [x] Stage 2 retry trigger and whole-plan replacement semantics are fixed.
- [x] one retry per stage is fixed.
- [x] Stage 2 cannot reopen Stage 1 in the same retry chain.
- [x] cross-attempt Stage 1 merge/salvage is prohibited.
- [x] cross-attempt Stage 2 plan merge/salvage is prohibited.
- [x] retry feedback cannot introduce factual authority.
- [x] request/schema/prompt/output evidence identities are defined.
- [x] G-23B/C/D protected semantic boundaries remain unchanged.
- [x] concrete residual classifier selection remains G-25A.

Result:

```text
N-04G-23E = Complete / Contract Accepted
N-04G-23F = NEXT
N-04       = Failed / not Complete
N-05       = blocked
```
