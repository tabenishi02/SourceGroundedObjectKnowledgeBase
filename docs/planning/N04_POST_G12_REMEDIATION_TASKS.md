# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-19

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Formal run: `20261018T213810+0900`
- Branch of record: `main`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Root-cause review: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- G-18 freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- G-19 implementation: `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
- Current parent state: **N-04 Failed / N-05 blocked**

---

## 1. Remediation principles

1. G-12 failed evidenceを削除・上書きしない。
2. N-04をG-22成功前にCompleteへ変更しない。
3. N-05をblockedのまま維持する。
4. v1 / v2 failed acceptance historyを保持する。
5. rubric / contractを実行後に緩めてPASSさせない。
6. generator / verifierをuntrusted or fallible componentとして扱う。
7. deterministicに防げるfailureをLLM judgeへ委ねない。
8. claim / premise / material / terminal / render各境界でfail-closedにする。
9. exact external verifier profileはbenchmark合格前にproduction authority化しない。
10. G-12で正常だったcanonical / MCP / Retrieval / Context Builderを新evidenceなしに変更しない。

---

## 2. Task status

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-13 | P0 | **Complete (2026-10-18)** | Root-cause / desk review / external research |
| N-04G-14 | P0 | **Complete (2026-10-19)** | Atomic claim / semantic-role boundary redesign |
| N-04G-15 | P0 | **Complete (2026-10-19)** | Output schema / presentation / renderer hardening |
| N-04G-16 | P0 | **Complete (2026-10-19, design)** | Semantic validation architecture redesign |
| N-04G-17 | P0 | **Complete (2026-10-19, design)** | Material sufficiency / terminal / render gate redesign |
| N-04G-18 | P0 | **Complete (2026-10-19, Design Frozen)** | Post-G12 v3 Design Freeze |
| N-04G-19 | P0 | **Complete (2026-10-19, implementation)** | Frozen v3 design implementation + verifier adapter boundary |
| N-04G-20 | P0 | **Pending / NEXT** | Adversarial / replay / verifier benchmark / regression |
| N-04G-21 | P0 | Pending | v3 acceptance spec / Reference Workstation harness freeze |
| N-04G-22 | P0 | Pending | Formal v3 re-acceptance |

N-04 CompleteはN-04G-22で全Gate PASS後のみ可能とする。

---

## 3. G-13〜G-17 result summary

### G-13

G-12から次を主要root causeとして確定した。

```text
atomicity instruction-only
support-free role escape
single general semantic judge
schema/parser mismatch
unvalidated free-form label rendering
weak material sufficiency
renderer not bound to terminal outcome
missing multi-object completion gate
```

### G-14

```text
1 unit = 1 atomic semantic proposition
ATOMIC + ROLE_VALID only -> support/derivation path
```

model-authored `stylistic_expression`をv3 baselineから除外し、content-first role boundaryを採用した。

### G-15

- free-form model `label`削除。
- trusted deterministic heading。
- role-specific block/unit schema。
- provider/application schema単一正本。

### G-16

Source fact:

```text
V3 deterministic support
  ↓ unresolved
specialized source-fact verifier
  ↓ SUPPORTED_CANDIDATE
independent bounded judge
  ↓ ENTAILED agreement
supported
```

Interpretation:

```text
validated source_fact
  ↓ premise_unit_ids
Premise Integrity Gate
  ↓
bounded derivation judge
```

### G-17

```text
Grounding PASS
  ↓
Material Requirement PASS
  ↓
Terminal ACCEPTED
  ↓
Render authorization
```

Comparison/Creativeのmulti-source coverageとRoleplay formal minimumをmachine-check可能なprofileへ分離した。

---

## 4. G-18 — Post-G12 Design Freeze

**Status: Complete / Design Frozen**

正本:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Frozen contract identities:

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

Frozen output shape:

```text
main           -> source_fact(text, support_refs[])
interpretation -> interpretation(text, premise_unit_ids[])
creative       -> creative_addition(text)
context_limit  -> context_limit(limit_code)
```

Validation / Material / Terminal / Renderer candidate identity:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

---

## 5. G-19 — Frozen remediation implementation

**Status: Complete (2026-10-19, implementation)**

正本:

```text
docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md
```

Implemented:

```text
src/sgokb/grounding/output.py
src/sgokb/grounding/request.py
src/sgokb/grounding/verifiers.py
src/sgokb/grounding/validation.py
src/sgokb/grounding/material_gate.py
src/sgokb/grounding/failure.py
src/sgokb/grounding/render.py
src/sgokb/grounding/evidence.py
src/sgokb/grounding/__init__.py
src/sgokb/application_grounding.py
tests/test_n04_grounded_generation.py
```

Key results:

- output v2 schema/parser implemented。
- canonical output digest + binding implemented。
- Atomicity/Role adapter boundary implemented。
- V4F specialized verifier + independent judge composition implemented。
- V4I premise graph / derivation path implemented。
- `MaterialRequirementGate` implemented。
- failure policy v2 + render modes implemented。
- terminal-bound renderer implemented。
- exclusive structured context-limit path implemented。
- application facade / evidence helper wired。
- focused v3 tests migrated。

Focused isolated/equivalent verification:

```text
22 passed
```

This does **not** replace G-20 full regression / real verifier benchmark.

Exact MiniCheck/AlignScore checkpoint/revision/threshold and exact model runtimes remain unfrozen.

---

## 6. N-04G-20 — Adversarial / Replay / Verifier Benchmark / Regression

**Status: Pending / NEXT**

Required functional/adversarial checks:

1. supported + unsupported clause in one unit -> no PASS。
2. material fact disguised as style -> no PASS。
3. creative block containing source Concept fact -> no role PASS。
4. unsupported interpretation premise -> no derived_supported。
5. one-side-only comparison -> no Material PASS。
6. arbitrary model label -> contract rejection / no unvalidated render。
7. materially incomplete grounded output -> no ACCEPTED。
8. unjustified context-limit -> no INSUFFICIENT_CONTEXT。
9. justified exclusive context-limit -> CONTEXT_LIMIT_ONLY render only。
10. REJECTED / SYSTEM_FAILURE -> renderer refuses。
11. attempt/output digest mismatch -> renderer refuses。
12. source-fact verifier disagreement -> no Grounding PASS。
13. G-12 Case 1/2/3 replay -> no false acceptance。
14. provider/application schema preflight -> no hidden mismatch。

Verifier benchmark must include at least:

```text
supported direct claim
supported paraphrase
unsupported material extra detail
G-12 unsupported atomic claims
high-overlap unsupported relation/event
contradiction / negation flip
threshold indeterminate-band cases
```

Candidate eligibility for G-21:

```text
required negative/replay false-positive = 0
```

Required engineering checks:

```text
full pytest
Ruff
git diff --check
```

G-20 may fix implementation/test defects found by these checks, but must not silently relax the G-18 Frozen semantics.

---

## 7. N-04G-21 — v3 Acceptance / Harness Freeze

**Status: Pending**

Formal run前にfreeze:

- generator model/runtime/settings
- source-fact verifier exact checkpoint/revision
- verifier threshold profile/hash
- independent source-fact judge exact model/settings
- interpretation derivation judge exact model/settings
- atomicity/role classifier runtime if model-based
- material requirement profiles + stable Object IDs
- provider structured-output mechanism/schema hash
- retry/terminal policy
- evidence tree
- G-20 adversarial/verifier preflight result
- formal rubric

G-20 empirical Gate未達profileをfreezeしない。

---

## 8. N-04G-22 — Formal v3 Re-Acceptance

**Status: Pending**

Same three representative use cases are retained.

N-04 Complete requires:

```text
3 / 3 formal Case PASS
+ no unsupported rendered material claim
+ no role escape
+ material requirement PASS
+ terminal/render authorization PASS
+ canonical invariance
+ integrity PASS
+ focused/adversarial/verifier regression PASS
+ full pytest 0 failed
```

---

## 9. Dependency

```text
G-12 valid formal FAIL
  ↓
G-13 Root-cause / Research Complete
  ↓
G-14 Atomicity / Role Boundary Complete
  ↓
G-15 Output / Presentation Complete
  ↓
G-16 Semantic Validation Complete
  ↓
G-17 Material / Terminal / Render Complete
  ↓
G-18 Post-G12 Design Freeze Complete
  ↓
G-19 Implementation Complete
  ↓
G-20 Adversarial / Verifier Benchmark / Regression  ← NEXT
  ↓
G-21 v3 Acceptance + Harness Freeze
  ↓
G-22 Formal v3 Re-Acceptance
  ↓
N-04 Complete only if PASS
  ↓
N-05
```

---

## 10. Explicit non-goals / protected boundaries

Without new failure evidence, do not change:

- canonical 52-table model
- Object ID / Version identity
- Source / Evidence / Provenance
- MCP read-only boundary
- Context Builder budget / purpose selection
- Similarity ranking algorithm
- N-06 retrieval-quality metrics
- G-12 historical failed evidence

Do not relax G-18 Frozen semantics merely to obtain PASS.
