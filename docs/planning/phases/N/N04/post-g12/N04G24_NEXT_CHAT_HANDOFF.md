# N-04G-24 — Next Chat Handoff

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
- G-23F: **Complete / v4 Design Frozen**
- Current task: **N-04G-24 — v4 Implementation**
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Start here

Read in this order:

1. `docs/planning/phases/N/N04/post-g12/N04G24_NEXT_CHAT_HANDOFF.md`
2. `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
3. `docs/decisions/N04G23E_PROVIDER_SCHEMA_AND_STAGE_LOCAL_RETRY_DESIGN.md`
4. `docs/decisions/N04G23D_STAGE2_PRESENTATION_GENERATOR_CONTRACT.md`
5. `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
6. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
7. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
8. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
9. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
10. existing production code under `src/sgokb/grounding/`
11. `src/sgokb/application_grounding.py`

GitHub `main` is the sole source of truth. Do not revive old stacked Phase N branches as design authority.

---

## 2. Frozen v4 architecture

```text
Grounded Context
  ↓
Stage 1 Planner
  ↓
Structured Proposition Candidates
  ↓
Reference Integrity
  ↓
V2-S / V2-P / V2-D
  ↓
V2-R-A / V2-R-C where required
  ↓
V3/V4F source support
  ↓ PASS only
Validation Record
  ↓
Certification
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
application path assignment / exact fact materialization
  ↓
V2 for model-authored Stage 2 propositions
  ↓
V4I for interpretations
  ↓
Validated Presentation Plan
  ↓
Material Requirement
  ↓
Terminal Decision
  ↓ ACCEPTED only
Deterministic Render
```

No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE / UNAVAILABLE.

---

## 3. Frozen contract identities

```text
sgokb.stage1-grounded-content-request.v1
sgokb.stage1-provider-output.v1
sgokb.structured-proposition.v1-candidate
sgokb.v4-validation-record.v1
sgokb.certified-content.v1
sgokb.stage2-presentation-request.v1
sgokb.stage2-provider-output.v1
sgokb.stage-local-retry-feedback.v1
sgokb.validated-presentation-plan.v1
sgokb.system-context-limit.v1
sgokb.grounded-generation-v4-run.v1
```

Historical v2/v3 production contracts remain historical evidence; G-24 must implement v4 explicitly rather than silently changing the meaning of an old version string.

---

## 4. Implementation goals

G-24 must implement the frozen contracts and orchestration without changing architecture.

At minimum:

1. Stage 1 request builder and instantiated provider schema.
2. Stage 1 application-owned candidate envelope / digest / lineage.
3. v4 V2-S/P/D/R dispatch interfaces.
4. source-fact V3/V4F integration boundary.
5. immutable `sgokb.v4-validation-record.v1`.
6. Certification and `sgokb.certified-content.v1`.
7. Stage 1 readiness and active-attempt replacement.
8. Stage 2 request builder and minimal Certified Fact projection.
9. Stage 2 provider schema / parser / application-owned path assignment.
10. exact `certified_fact_materialization`.
11. Stage 2 interpretation V2 + V4I path.
12. Stage 2 creative V2/scope path.
13. whole-plan validation and `sgokb.validated-presentation-plan.v1`.
14. stage-local retry controller: max 2 attempts / 1 retry per stage.
15. system-owned `sgokb.system-context-limit.v1` and terminal mapping.
16. v4 evidence manifest/tree and exact-byte hashes.
17. provider capability probe.
18. deterministic renderer consuming validated plan only.
19. automated unit/integration/regression tests.

---

## 5. Model-authored paths

Only these model-authored proposition paths exist:

```text
stage1_fact_candidate
  -> source_fact
  -> V2 + V3/V4F

stage2_interpretation_candidate
  -> interpretation
  -> V2 + V4I

stage2_creative_candidate
  -> creative_addition
  -> V2 + creative scope policy
```

Non-model paths:

```text
certified_fact_materialization
  -> source_fact
  -> exact application-owned Certified Fact text

system_context_limit
  -> context_limit
  -> application/system-owned only
```

Do not implement model-owned semantic-role authority, model-owned context-limit, model-owned validation/certification status or model-authored factual paraphrase with inherited certification.

---

## 6. Stage 1 implementation invariants

Provider payload:

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

Application must:

- instantiate K allow-list and candidate budget into provider schema;
- independently parse/revalidate provider output;
- reject duplicate/unknown/stale/cross-context refs;
- create application-owned proposition IDs and digests;
- keep candidate immutable;
- validate candidates independently inside one attempt;
- certify only eligible candidates;
- use Stage 1 readiness to decide whether retry is needed;
- never merge Certified Facts across Stage 1 attempts.

Attempt 2, if run, becomes the sole active Stage 1 attempt.

---

## 7. Certification invariants

```text
Candidate != Validation Record != Certified Fact != Certified Content
```

Certification may emit a Certified Fact only after required aggregate V2 PASS + source-support PASS + identity/digest consistency.

Certified Fact:

- application-owned `certified_fact_id`;
- exact candidate `claim_text`;
- exact candidate `support_refs[]`;
- source candidate + Validation Record ID/digest bindings;
- no rewrite/repair/atomization/support replacement.

Certified Content must use a single context fingerprint.

---

## 8. Stage 2 implementation invariants

Model-facing factual projection:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Provider output families:

```text
main
  -> Certified Fact IDs only

interpretation
  -> claim_text + premise_fact_ids[]

creative
  -> claim_text only, creative purpose only
```

Application must:

- validate active Certified Fact ID allow-list;
- reject duplicate block kind / duplicate IDs;
- assign path from schema slot, not model role declaration;
- materialize `main` using exact Certified Fact text;
- run V2 on interpretation/creative model text;
- run V4I on interpretation;
- reject entire Stage 2 attempt when any included model-authored candidate/block fails;
- never partially render a failed plan;
- never merge Stage 2 attempts.

---

## 9. Provider/application boundary

Provider structured output is only a guard.

Application revalidation is mandatory even when provider reports schema-conforming output.

Do not rely on provider enforcement of:

```text
uniqueItems
contains/minContains/maxContains
conditionals
cross-item uniqueness
```

G-24 must add a provider capability probe covering at least:

```text
Stage 1 empty candidate set
Stage 1 valid candidate
Stage 1 extra property
Stage 1 invalid K ref
Stage 2 valid main
Stage 2 valid interpretation
Stage 2 creative under creative purpose
Stage 2 invalid Certified Fact ID
duplicate support/premise IDs -> application reject
duplicate block kind -> application reject
provider incomplete/interrupted response
```

Safety must not depend on provider preventing invalid cases.

---

## 10. Retry invariants

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

Retry is full replacement, never patch/delta.

Fixed across Stage 1 retry:

```text
Grounded Context/fingerprint
purpose/task
K allow-list
candidate budget
model/runtime/settings
provider schema instance
material profile
```

Fixed across Stage 2 retry:

```text
active Certified Content/digest
model-facing projection
purpose/presentation instruction
allowed output kinds
model/runtime/settings
provider schema instance
material profile
```

Retry feedback is diagnostic only and cannot add facts, IDs, support text or validator-written replacement claims.

No Stage 2 -> Stage 1 retry inside the same run.

---

## 11. Context-limit / terminal invariants

Empty candidates/facts/blocks do not by themselves prove context insufficiency.

`sgokb.system-context-limit.v1` may be created only by deterministic application policy when authoritative fixed input cannot satisfy required material.

Terminal outcomes:

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

Only `ACCEPTED` authorizes normal render and can be N-04 Case PASS candidate.

`INSUFFICIENT_CONTEXT` is safe but remains formal Case FAIL.

---

## 12. Evidence requirements

Implement `sgokb.grounded-generation-v4-run.v1` and retain, at minimum:

- Git/code identity;
- Grounded Context + fingerprint;
- request/prompt/schema artifacts and exact-byte hashes;
- provider/model/settings/runtime identity;
- provider capability probe;
- each Stage 1/2 attempt raw + parsed output;
- candidate envelopes/digests;
- Validation Records and component evidence refs;
- certification decisions / Certified Content;
- retry feedback + lineage;
- Stage 2 materialization map;
- Validated Presentation Plan;
- Material Requirement result;
- system context-limit when applicable;
- terminal decision;
- rendered output when authorized.

Failed/non-active attempts are evidence and must not be deleted.

---

## 13. Required tests

G-24 should add automated coverage for at least:

- schema-valid non-atomic text still routes to V2-R-A;
- forged model role/status cannot alter path;
- invalid K/CF binding fails closed;
- Certification exact-copy invariant;
- certification cannot rescue earlier V2 failure;
- no model-authored source fact path after Certification;
- Stage 2 factual paraphrase cannot inherit certification;
- interpretation premise must be active Certified Fact ID;
- creative denied outside creative purpose;
- duplicate Stage 2 block kinds fail;
- application rejects duplicates even if provider accepts them;
- Stage 1 attempt replacement / no cross-attempt merge;
- Stage 2 whole-plan invalidation / no partial render;
- no attempt-1 fallback after attempt 2 authorization;
- no Stage 2 -> Stage 1 backtracking;
- context-limit is system-owned only;
- raw Stage 2 output never feeds render;
- only Validated Presentation Plan + ACCEPTED terminal can render;
- evidence hashes/lineage bind correctly.

Do not hide failures with new skip/xfail.

---

## 14. Protected boundaries

G-24 must not change without reopening G-23F:

- two-stage architecture;
- E2 V2 authority order;
- application-owned path provenance;
- Residual Atomicity / Content-Type split;
- candidate/validation/certification separation;
- no silent atomization;
- exact Certified Fact materialization;
- Stage 2 Certified Content boundary;
- interpretation Certified Fact premise boundary;
- creative purpose restriction;
- provider schema as guard only;
- application revalidation;
- one retry per stage;
- active-attempt replacement;
- no Stage 2 -> Stage 1 retry;
- system-owned context-limit;
- evidence/replay requirements;
- mandatory G-25A/G-25B Gates.

Retrieval, Similarity, Context Builder, canonical DB, Source/Evidence/Provenance, Object/Version identity and MCP read-only boundary remain outside G-24 redesign scope.

---

## 15. Residual classifier execution remains G-25A

G-24 implements adapter/interfaces and fail-closed behavior only.

It must not select/tune the production V2-R-A/V2-R-C component using Frozen 47 Gold.

After G-24:

```text
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

`VALID_FAIL_NO_SELECTION` keeps G-26 blocked.

---

## 16. Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = Complete / Contract Accepted
G-23D   = Complete / Contract Accepted
G-23E   = Complete / Contract Accepted
G-23F   = Complete / v4 Design Frozen
G-24    = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## 17. Immediate next action

Start **N-04G-24 — v4 Implementation** from GitHub `main`.
