# N-04G-23C — Next Chat Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Authoritative repository state: GitHub `main`
- G-23A-E: **Complete / Architecture Accepted**
- G-23B: **Complete / Contract Accepted**
- Current task: **N-04G-23C — Certification / Certified Content Contract**
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Start here in the next chat

Read in this order:

1. `docs/planning/phases/N/N04/post-g12/N04G23C_NEXT_CHAT_HANDOFF.md`
2. `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
3. `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
4. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
5. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
6. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
7. `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
8. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
9. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
10. `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`

---

## 2. Current architecture

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidate
  ↓
V2-S / V2-P / V2-D
  ↓
V2-R-A / V2-R-C where required
  ↓ PASS only
V3/V4 support validation
  ↓ PASS only
Certified Content
  ↓
Stage 2 Presentation Generator
```

No downstream authority may rescue an earlier FAIL or INDETERMINATE.

---

## 3. G-23B frozen input to G-23C

Stage 1 model response is minimal:

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

Application wraps each parsed candidate with application-owned metadata:

```text
candidate contract version
request_id
context_fingerprint
purpose
stage = stage1
path_provenance = stage1_fact_candidate
attempt
proposition_id
candidate_index
retry_parent_id
```

Important G-23B decisions:

- model response does not echo application-owned metadata;
- Stage 1 path is `stage1_fact_candidate`;
- role is derived by application as `source_fact`;
- no Stage 1 presentation role;
- every non-empty candidate has `support_refs[] >= 1`;
- support ref presence is not support/entailment proof;
- model-authored free text does not self-prove Atomicity;
- optional semantic anchors are excluded from v1;
- `candidates: []` is allowed and means only "no candidate material produced";
- empty result is not a model-authored `context_limit` verdict;
- failed candidate is immutable; retry creates a new proposition identity with lineage.

---

## 4. G-23C exact responsibility

Design the **Certification / Certified Content contract** between validated Stage 1 candidates and Stage 2.

At minimum G-23C should fix:

1. Validation record vs Certified Content record separation.
2. Exact certification eligibility condition after V2/V3/V4 PASS.
3. Stable `certified_fact_id` semantics and ownership.
4. Binding from certified fact back to immutable Stage 1 candidate identity.
5. Certified claim text semantics: exact candidate text vs deterministic materialization rules.
6. Certified support binding and evidence identity.
7. Context fingerprint / request lineage retained into certification.
8. What validation evidence IDs/digests are required in the Certified Content record.
9. Multiple certified facts representation and ordering semantics.
10. Duplicate/equivalent certified candidate handling, if required for a safe contract.
11. Certified Content versioning / digest / replay identity.
12. How Stage 2 receives certified factual material without reopening raw Grounded Context authority.
13. Failure and non-certification semantics.
14. Evidence fields required by G-23D/G-23E/G-26.

G-23C should produce a normative Decision/contract artifact consumable by G-23D.

---

## 5. G-23C must not reintroduce

Do not add:

```text
model-owned certification status
model-owned support/entailment PASS
generator-declared semantic_role authority
silent rewrite of failed/validated candidate text
post-hoc atomization that preserves compound original text
new source-world fact generation during certification
```

Certification is application/validator-owned.

Candidate, validation evidence, and certification remain separate artifacts.

---

## 6. Existing direction from E3/E4

E3 already fixes the conceptual flow:

```text
Structured Proposition Candidate
  ↓ immutable candidate content
Validation Record
  ↓ PASS only
Certified Content Record
```

Certified source fact should carry a stable `certified_fact_id` for Stage 2.

E4 already reserves:

```text
certified_fact_materialization
  -> normalized role source_fact
  -> application-owned
  -> no new model-authored factual text
```

When materialization is exact/deterministic from Certified Content, residual semantic classification may be `NOT_REQUIRED` under the E4/E5 rules.

G-23C must define the exact Certified Content object that makes this safe.

---

## 7. Protected boundaries

Do not change without new failure evidence:

- Frozen 47 Gold labels / flags
- G-14 no-silent-post-hoc-atomization intent
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured Proposition contract
- E4 application-owned role provenance / compatibility matrix
- E5 fail-closed residual classifier policy
- G-23B minimal Stage 1 model payload and application envelope ownership
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- MiniCheck profile/threshold merely to improve acceptance
- unsupported rendered material prohibition
- fail-closed semantics

---

## 8. Residual classifier selection remains later

G-23C does not select Residual Atomicity / Content-Type models.

Concrete selection remains:

```text
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

If G-25A has no candidate satisfying the zero-tolerance selection gate, result is `VALID_FAIL_NO_SELECTION` and G-26 remains blocked.

---

## 9. Current state

```text
G-23A-E = Complete / Architecture Accepted
G-23B   = Complete / Contract Accepted
G-23C   = NEXT
N-04    = Failed / not Complete
N-05    = blocked
```

## 10. Immediate next action

Start **N-04G-23C — Certification / Certified Content Contract** from GitHub `main`.
