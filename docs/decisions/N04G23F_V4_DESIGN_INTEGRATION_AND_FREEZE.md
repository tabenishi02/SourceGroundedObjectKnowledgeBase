# N-04G-23F — v4 Design Integration / Design Freeze

更新日: 2026-10-21

- Status: **Complete / v4 Design Frozen**
- Parent: `N-04G-23 — Two-Stage Grounded Generation Architecture`
- Predecessors:
  - `N-04G-23A-E — Complete / Architecture Accepted`
  - `N-04G-23B — Complete / Contract Accepted`
  - `N-04G-23C — Complete / Contract Accepted`
  - `N-04G-23D — Complete / Contract Accepted`
  - `N-04G-23E — Complete / Contract Accepted`
- Next: `N-04G-24 — v4 Implementation`
- N-04: **Failed / not Complete**
- N-05: **blocked**

Authority:

- `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
- `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
- `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
- `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
- `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`
- `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`

---

## 1. Freeze decision

G-23A-EおよびG-23B〜Eを統合レビューした結果、v4 grounded-generation architectureに**未解決のownership / authority / artifact-flow contradictionは確認しない**。

従って、N-04 post-G22 remediationのv4設計を **Design Frozen** とする。

G-24は本書をimplementation authorityとして使用し、G-23B〜Eの個別Decisionを詳細contractとして参照する。

Design Freezeはproduction readinessやN-04 PASSを意味しない。

```text
G-23F Design Frozen
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
```

Concrete Residual Atomicity / Content-Type classifierはまだ選定されていない。G-25Aがmandatory Gateである。

---

## 2. Frozen end-to-end architecture

```text
Canonical Knowledge
  ↓
MCP read boundary / Retrieval / Similarity / Context Builder
  ↓
Grounded Context + context_fingerprint + K refs
  ↓
Stage 1 Grounded Content Planner
  ↓
Stage 1 provider output
  candidates[{claim_text, support_refs[]}]
  ↓
Application-owned Structured Proposition Candidate
  path = stage1_fact_candidate
  role = source_fact
  ↓
Reference Integrity
  ↓
V2-S Structural Proposition Gate
  ↓
V2-P Application-owned Role Provenance
  ↓
V2-D Deterministic Compatibility Gate
  ↓ PASS only
V2-R-A Residual Atomicity if required
  ↓ ATOMIC only
V2-R-C Residual Content Type if required
  ↓ compatible only
V3/V4F Source Fact Support
  ↓ PASS only
Validation Record
  ↓
Application-owned Certification
  ↓
Certified Fact(s)
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
Ordered presentation proposal
  ├─ main: Certified Fact IDs only
  ├─ interpretation: claim_text + premise_fact_ids[]
  └─ creative: claim_text, creative purpose only
  ↓
Application-owned path assignment
  ├─ certified_fact_materialization -> source_fact
  ├─ stage2_interpretation_candidate -> interpretation
  └─ stage2_creative_candidate -> creative_addition
  ↓
Final deterministic + V2 semantic validation
  ↓
V4I derivation for interpretations
  ↓ PASS only
Validated Presentation Plan
  ↓
Material Requirement Gate
  ↓
Terminal Decision
  ↓ ACCEPTED only
Deterministic Render
```

Universal invariant:

> **No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE / UNAVAILABLE.**

---

## 3. Frozen authority map

### 3.1 Model-authored natural-language paths

v4でmodelが新規natural-language propositionを生成できるnormative pathは次だけである。

| Path | Stage | Normalized role | Required validation |
|---|---|---|---|
| `stage1_fact_candidate` | Stage 1 | `source_fact` | V2 + V3/V4F |
| `stage2_interpretation_candidate` | Stage 2 | `interpretation` | V2 + V4I |
| `stage2_creative_candidate` | Stage 2 | `creative_addition` | V2 + purpose/scope policy |

Model-generated role labelはauthorityではない。

### 3.2 Non-model-authored paths

| Path | Owner | Normalized role | Rule |
|---|---|---|---|
| `certified_fact_materialization` | application | `source_fact` | exact Certified Fact text only |
| `system_context_limit` | application/system | `context_limit` | deterministic/system-owned only |

Stage 2 modelはsource fact本文を生成しない。

Model-authored `context_limit` / `stylistic_expression`専用pathはv4 baselineに存在しない。

### 3.3 Exactly-one-path invariant

すべてのmodel-authored propositionはparse後にapplicationがexactly one pathを割り当てる。

```text
one proposition
-> one path_provenance
-> one normalized role
-> one deterministic compatibility route
-> one required semantic validation route
```

Unknown path、ambiguous path、forged path metadataはfail-closed。

---

## 4. Frozen contract identities

G-24は次をlogical contract identityとして使用する。

```text
Stage 1 request
  sgokb.stage1-grounded-content-request.v1

Stage 1 provider output template
  sgokb.stage1-provider-output.v1

Structured Proposition Candidate envelope
  sgokb.structured-proposition.v1-candidate

v4 Validation Record
  sgokb.v4-validation-record.v1

Certified Content
  sgokb.certified-content.v1

Stage 2 request
  sgokb.stage2-presentation-request.v1

Stage 2 provider output template
  sgokb.stage2-provider-output.v1

Stage-local retry feedback
  sgokb.stage-local-retry-feedback.v1

Validated Presentation Plan
  sgokb.validated-presentation-plan.v1

System Context Limit artifact
  sgokb.system-context-limit.v1

v4 run/evidence manifest
  sgokb.grounded-generation-v4-run.v1
```

`sgokb.v4-validation-record.v1`、`sgokb.validated-presentation-plan.v1`、`sgokb.system-context-limit.v1`、`sgokb.grounded-generation-v4-run.v1`はG-23Fでimplementation identityを明示的にfreezeする名称である。

Contract semanticsを変更する場合は同じversionをsilentに再利用しない。

Provider-specific request wire formatはlogical contractとは分離する。

---

## 5. Stage 1 frozen contract

### 5.1 Model payload

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

Normative rules:

- one authoritative natural-language field = `claim_text`;
- `support_refs[] >= 1` for every non-empty candidate;
- only request allow-listed K refs;
- candidate array may be empty;
- empty candidate array is not context-limit authority;
- no semantic role/status/validation/certification fields;
- no premise IDs;
- no presentation role;
- no optional semantic anchors in v1.

### 5.2 Application envelope

Application binds at minimum:

```text
request contract/version
request_id
context_fingerprint
purpose
stage = stage1
path_provenance = stage1_fact_candidate
attempt / attempt_id
proposition_id
candidate_index
retry lineage
claim_text
support_refs[]
```

Candidate is immutable after construction.

Failed candidate text is never silently rewritten, split, merged or partially certified.

---

## 6. Frozen V2/V3/V4 authority order

For Stage 1 model-authored source facts:

```text
Reference Integrity
  ↓
V2-S
  ↓
V2-P
  ↓
V2-D
  ↓
V2-R-A if required
  ↓
V2-R-C if required
  ↓
V3 deterministic source support
  ↓ unresolved only
V4F source-fact verification
```

For Stage 2 interpretations:

```text
Premise integrity
  ↓
V2-S / V2-P / V2-D
  ↓
V2-R-A if required
  ↓
V2-R-C if required
  ↓
V4I derivation
```

For Stage 2 creative candidates:

```text
V2-S / V2-P / V2-D
  ↓
V2-R-A if required
  ↓
V2-R-C if required
  ↓
creative scope/purpose compatibility
```

`AMBIGUOUS`、`MIXED_CONTENT`、runtime unavailable、malformed classifier outputはPASSへ倒さない。

---

## 7. Certification freeze

Certificationはapplication/validator-owned boundaryである。

Artifact separation:

```text
Candidate
  != Validation Record
  != Certified Fact
  != Certified Content
```

Certified Fact eligibility:

```text
candidate/reference identity valid
AND aggregate V2 PASS
AND source-support aggregate PASS
AND candidate/validation binding match
AND no unresolved FAIL / INDETERMINATE / UNAVAILABLE
```

Certified Fact rules:

- `certified_fact_id` is application-owned;
- ID scope is one immutable Certified Content artifact;
- not a canonical DB Fact identity;
- `claim_text` exact-copies the Stage 1 candidate;
- `support_refs[]` exact-copy the Stage 1 candidate;
- validation authority stays in Validation Record;
- Certification never paraphrases/repairs/atomizes/adds support/adds facts.

One Certified Content artifact contains one context fingerprint only.

Exact duplicate handling may suppress duplicate certification deterministically. Semantic paraphrase merging is not introduced.

---

## 8. Stage 2 frozen contract

### 8.1 Model-facing factual authority

Stage 2 receives a minimal projection from one active Certified Content artifact:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Raw Grounded Context、uncertified Stage 1 candidate、validation score/detailsはnew factual authorityとしてStage 2へ渡さない。

### 8.2 Model output

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

Rules:

- `main` contains Certified Fact IDs only;
- application resolves IDs and materializes exact Certified Fact text;
- model factual paraphrase does not inherit certification;
- interpretation premises resolve only to active Certified Fact IDs;
- creative block exists only when purpose is `creative`;
- each block kind cardinality = 0 or 1;
- duplicate block kind = deterministic FAIL;
- duplicate fact/premise ID = deterministic FAIL;
- `blocks: []` is allowed but is not context-limit;
- Stage 2 output is one ordered plan; order is presentation order only.

### 8.3 Whole-plan validation

Stage 2 presentation attempt is consumed as one plan.

If any included model-authored candidate/block fails required validation:

```text
Stage 2 attempt = not renderable
```

Do not partially render surviving blocks.

---

## 9. No-new-source-fact freeze after Certification

After Certified Content is frozen, a source-world factual proposition may reach normal render only through:

```text
active Certified Fact
  ↓
certified_fact_materialization
  ↓
exact application-owned content
```

Forbidden:

- model paraphrase of Certified Fact rendered as certified source fact;
- interpretation promoted into source fact;
- creative clause promoted into source fact;
- user instruction fact promoted without Stage 1 certification;
- raw Grounded Context reopened by Stage 2;
- validator-written repair prose rendered as fact.

If a new source fact is required, a new top-level orchestration run must return through Stage 1. Stage 2 retry cannot backtrack into Stage 1.

---

## 10. Provider/application validation freeze

Provider structured output is an optimization/structural guard, not safety authority.

Provider-safe subset used by the v4 templates:

```text
type
properties
required
additionalProperties=false
items
minItems/maxItems
enum
const
oneOf with complete alternatives
string minLength
```

Application independently rechecks:

```text
JSON parse
instantiated schema
K / Certified Fact allow-list
reference existence/binding
duplicate refs/IDs
duplicate block kinds
purpose compatibility
context / request / Certified Content binding
```

Do not depend on provider enforcement of:

```text
uniqueItems
contains/minContains/maxContains
conditionals
cross-item uniqueness
semantic regex meaning
```

Provider unavailable/incomplete, schema binding mismatch, or inability to accept the frozen schema is fail-closed. No silent free-prose fallback, alternate provider, alternate model, or weakened schema.

G-24 implements an explicit capability probe. G-26 freezes the exact Reference Workstation provider/runtime capability evidence.

---

## 11. Retry / active-attempt freeze

Retry budgets:

```text
Stage 1 max attempts = 2
Stage 1 max retries  = 1

Stage 2 max attempts = 2
Stage 2 max retries  = 1
```

Counters are independent.

### 11.1 Fixed-input rule

Across a retry, the only things that may change are:

```text
attempt identity
retry lineage
application-owned structured feedback
new provider output
```

Stage 1 keeps fixed:

```text
Grounded Context / context_fingerprint
purpose / user task
K allow-list
candidate budget
model/runtime/load profile/settings
provider schema instance
material requirement profile
```

Stage 2 keeps fixed:

```text
active Certified Content / digest
minimal Certified Fact projection
purpose / presentation instruction
allowed output kinds
model/runtime/load profile/settings
provider schema instance
material requirement profile
```

### 11.2 Active-attempt replacement

If attempt 2 is authorized:

```text
attempt 1 remains evidence only
attempt 2 becomes the sole active attempt
```

Forbidden:

```text
Stage 1 attempt 1 Certified Facts + attempt 2 Certified Facts
Stage 2 attempt 1 blocks + attempt 2 blocks
fallback to attempt 1 after attempt 2 was authorized
```

Multiple eligible candidates from the same active Stage 1 attempt may be certified together.

### 11.3 No Stage 2 -> Stage 1 backtracking

Once active Certified Content is frozen and Stage 2 begins:

```text
Stage 2 failure
-> Stage 2 retry or terminal outcome
```

A new Stage 1 run requires a new top-level orchestration run and is not part of the same retry chain.

---

## 12. Retry feedback freeze

Contract:

```text
sgokb.stage-local-retry-feedback.v1
```

Retry feedback may include:

- failure code/scope/path;
- exact previously generated failed text;
- existing binding IDs;
- expected structural/semantic boundary rule;
- bounded repair directive;
- missing material category/target already defined by request policy.

It must not include:

- new source-world fact;
- new K / Certified Fact ID;
- external support text;
- model-memory/Web correction;
- validator-authored replacement claim;
- post-hoc atomized approved replacement prose.

The retry model must regenerate a complete payload/plan.

---

## 13. Stage 1 readiness and Material Requirement freeze

v4 distinguishes **Stage 1 readiness** from the **final Material Requirement Gate**.

### 13.1 Stage 1 readiness

After validating/certifying one active Stage 1 attempt, application determines whether the active Certified Content has enough factual material to justify Stage 2 under the frozen requirement profile.

This check may authorize Stage 1 retry when:

- Context can still satisfy the required factual material;
- failed/non-certified candidates caused material loss;
- retry budget remains.

It does not declare the final use-case answer acceptable.

### 13.2 Final Material Requirement

After Stage 2 plan validation:

```text
validated exact source-fact materialization
+ validated interpretation
+ validated creative material where required
```

is evaluated against the frozen Material Requirement profile.

Stage 2 model does not declare Material PASS.

Material Requirement cannot rescue validation failure.

### 13.3 Impossible material

If deterministic application policy establishes that the fixed authoritative input cannot satisfy the required material, retry is not used as a hallucination opportunity.

The system proceeds to application-owned context-limit/terminal handling.

---

## 14. System-owned context-limit / terminal freeze

`context_limit` is never model-owned in v4.

Application/system may create:

```text
sgokb.system-context-limit.v1
```

only from deterministic/frozen orchestration evidence that authoritative input cannot satisfy a required material condition.

Minimum logical fields:

```text
contract_version
context_limit_id
reason_code = material_requirements_not_satisfied
stage_at_detection
request_id
context_fingerprint
material_profile_id / hash
missing_requirement_codes[]
authoritative_input_digest
```

No free-form model-authored factual text is part of this artifact.

Important distinctions:

```text
Stage 1 candidates = []
!= automatic context-limit

Certified Content facts = []
!= automatic context-limit

Stage 2 blocks = []
!= automatic context-limit
```

Those states require application policy to determine whether the cause is true input insufficiency, repairable generation failure, exhausted generation failure, or system failure.

Frozen terminal outcomes remain:

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

Semantics:

- `ACCEPTED`: all required validation/material gates PASS; normal deterministic render authorized.
- `INSUFFICIENT_CONTEXT`: deterministic authoritative-input insufficiency; safe terminal but N-04 Case FAIL.
- `REJECTED`: generation/validation/material repair exhausted or invalid without proven authoritative-input insufficiency.
- `SYSTEM_FAILURE`: required runtime/provider/validator/binding unavailable or internally inconsistent.

A system context-limit artifact may be rendered only through a deterministic fixed renderer/template when terminal policy authorizes `INSUFFICIENT_CONTEXT`.

Normal accepted material and context-limit material do not coexist in one terminal output.

---

## 15. Validated Presentation Plan freeze

After Stage 2 deterministic/semantic validation, application constructs:

```text
sgokb.validated-presentation-plan.v1
```

This artifact is application-owned and immutable.

Minimum logical content:

```text
contract_version
validated_plan_id
stage2_request_id
stage2_attempt_id / attempt
certified_content_id / digest
context_fingerprint
purpose
ordered validated blocks
  main -> resolved certified_fact_id + exact claim_text
  interpretation -> proposition_id + claim_text + premise_fact_ids + validation record binding
  creative -> proposition_id + claim_text + validation record binding
plan_digest
```

Only this validated plan may feed final Material Requirement and normal render.

Raw Stage 2 output is never rendered directly.

---

## 16. Evidence / replay freeze

Top-level run manifest:

```text
sgokb.grounded-generation-v4-run.v1
```

Minimum evidence tree:

```text
run/
  manifest.json
  runtime/
    provider-runtime.json
    model-runtime.json
    validator-runtime.json
    provider-capability-probe.json

  context/
    request-input.json
    grounded-context.json
    grounded-context.sha256

  stage1/
    attempt-1/
      request.json
      prompt.txt
      provider-schema.json
      provider-status.json
      raw-output.txt
      parsed-output.json
      candidate-envelopes.json
      validation-records.json
      certification-decisions.json
      certified-content.json          # if active/ready
      retry-feedback.json             # if retry authorized
    attempt-2/                        # if executed
      ...same classes...

  certification/
    active-certified-content.json
    active-certified-content.sha256

  stage2/
    attempt-1/
      request.json
      model-facing-projection.json
      prompt.txt
      provider-schema.json
      provider-status.json
      raw-output.txt
      parsed-output.json
      candidate-envelopes.json
      validation-records.json
      materialization-map.json
      retry-feedback.json             # if retry authorized
    attempt-2/                        # if executed
      ...same classes...

  final/
    validated-presentation-plan.json
    material-result.json
    system-context-limit.json         # only when applicable
    terminal-decision.json
    rendered-output.txt               # only when authorized
```

Minimum identity/hash binding:

```text
Git commit / code identity
contract versions
schema template + instantiated schema exact-byte SHA-256
prompt template + attempt prompt exact-byte SHA-256
request payload digest
context_fingerprint
model/runtime/settings identity
provider adapter/runtime identity
classifier/verifier profile identity where invoked
attempt IDs / lineage
raw/parsed output digests
candidate digests
validation record IDs/digests
Certified Content ID/digest
Validated Presentation Plan ID/digest
material profile ID/hash
terminal decision binding
```

Historical/failure attempt artifacts are never deleted merely because a later attempt becomes active.

---

## 17. Render freeze

Normal render consumes only `sgokb.validated-presentation-plan.v1` under `ACCEPTED`.

Renderer must preserve semantic separation:

```text
source fact material
!= interpretation material
!= creative material
```

Application-owned deterministic wrappers may provide fixed headings, bullet markers, numbering and separators.

Renderer must not:

- paraphrase factual content;
- merge interpretation/creative into main;
- invent headings that carry source-world propositions;
- render unvalidated raw model output;
- render failed/non-active attempt material.

Exact human-facing template can be implemented in G-24 so long as these frozen invariants hold and its bytes/version are replayable.

---

## 18. Implementation boundary for G-24

G-24 may implement/refactor the grounded-generation package to realize this design.

Expected implementation areas include:

```text
Stage 1 request/provider schema builder
Structured Proposition Candidate envelope/digest
v4 V2 orchestration
Validation Record
Certification / Certified Content
Stage 2 request/provider schema builder
Stage 2 parser/path assignment
Certified Fact exact materialization
Stage 2 validation / V4I integration
stage-local retry controller
system context-limit / terminal controller
Validated Presentation Plan
v4 evidence logger / manifest
renderer integration
provider capability probes
unit/integration tests
```

G-24 must not redesign:

```text
Retrieval / Similarity / Context Builder
canonical DB
Source / Evidence / Provenance
Object / Version identity
MCP public read boundary
Frozen 47 Gold labels/flags
G-25A selection Gate
```

Concrete Residual classifier selection remains G-25A. G-24 should implement pluggable interfaces/adapters and fail-closed behavior when a required component is not configured/available.

---

## 19. Integration questions — closed

### Q1. Does every model-authored natural-language proposition have exactly one validation path?

**YES.** Stage 1 fact, Stage 2 interpretation, Stage 2 creative each have one application-owned path and required validator route.

### Q2. Can source-world factual text reach normal render without Stage 1 certification?

**NO.** Main source facts are exact Certified Fact materializations only.

### Q3. Can model-declared role/status override path provenance?

**NO.** Role/status fields are absent or non-authoritative; path is application-owned.

### Q4. Can schema-valid text bypass Residual Atomicity/Content-Type where required?

**NO.** Provider/application schema validity is structural only.

### Q5. Can Stage 2 reopen raw Grounded Context or uncertified candidates?

**NO.** Stage 2 factual authority is one active Certified Content artifact.

### Q6. Can Certification rewrite candidate text/support bindings?

**NO.** Exact-copy only.

### Q7. Can attempt 1 and attempt 2 material be silently merged?

**NO.** Active-attempt replacement is frozen.

### Q8. Can retry feedback introduce new facts or approved replacement prose?

**NO.** Diagnostic bounded feedback only.

### Q9. Can provider schema limitations weaken application safety checks?

**NO.** Application validation is mandatory and authoritative.

### Q10. Can a failed G-25A classifier benchmark be bypassed to G-26?

**NO.** `VALID_FAIL_NO_SELECTION` keeps G-26 blocked.

---

## 20. Mandatory downstream Gate freeze

G-25A remains mandatory before G-26.

Selection Gate:

```text
Atomicity critical NON_ATOMIC false-pass = 0
Content-Type critical wrong-compatible false-pass = 0
required-valid false-reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
repeatability = exact / 100% as applicable
```

All candidates fail:

```text
VALID_FAIL_NO_SELECTION
```

No threshold/rubric/Gate weakening is permitted to advance the schedule.

G-25B then requires at minimum:

```text
critical Atomicity false-pass = 0
critical content-role false-pass = 0
unsupported rendered material claim = 0
accepted role escape = 0
invalid certified binding acceptance = 0
invalid interpretation premise acceptance = 0
creative scope violation acceptance = 0
```

Only G-25A PASS + G-25B PASS can unblock G-26.

---

## 21. Design Freeze protected boundaries

After G-23F, G-24 implementation must not silently alter:

- two-stage architecture;
- application-owned role provenance;
- candidate/validation/certification artifact separation;
- one-authoritative-`claim_text` proposition contract;
- no silent post-hoc atomization;
- Stage 1 support-ref contract;
- V2 authority order;
- Residual Atomicity / Content-Type split;
- fail-closed ambiguity/unavailability;
- exact Certified Fact materialization;
- Stage 2 Certified Content factual boundary;
- interpretation Certified Fact premise boundary;
- creative purpose restriction;
- no model-owned context-limit/stylistic-expression path;
- provider schema as guard only;
- application revalidation;
- max 1 retry per stage;
- active-attempt replacement / no cross-attempt merge;
- no Stage 2 -> Stage 1 backward retry;
- system-owned context-limit semantics;
- unsupported rendered material prohibition;
- evidence/replay requirements;
- mandatory G-25A/G-25B Gates.

Any implementation-discovered contradiction that requires changing one of these is a **Design Freeze reopen / architecture escalation**, not an implementation convenience change.

---

## 22. Acceptance checklist

- [x] G-23A-E + G-23B/C/D/E integrated.
- [x] End-to-end ownership/authority is non-contradictory.
- [x] Every model-authored proposition has one application-owned path.
- [x] No uncertified source fact can reach normal render.
- [x] Contract identities needed by implementation are frozen.
- [x] Candidate -> Validation -> Certification traceability is frozen.
- [x] Stage 2 Certified Content boundary is frozen.
- [x] Provider/application validation split is frozen.
- [x] Stage-local retry ordering and active-attempt semantics are frozen.
- [x] System-owned context-limit / terminal boundary is frozen.
- [x] Stage 1 readiness vs final Material Requirement is distinguished.
- [x] Validated Presentation Plan and render boundary are frozen.
- [x] Evidence/replay tree and minimum hash bindings are frozen.
- [x] G-25A/G-25B mandatory downstream Gates are preserved.
- [x] G-24 implementation scope is defined.

Result:

```text
N-04G-23F = Complete / v4 Design Frozen
N-04G-24  = NEXT
N-04      = Failed / not Complete
N-05      = blocked
```
