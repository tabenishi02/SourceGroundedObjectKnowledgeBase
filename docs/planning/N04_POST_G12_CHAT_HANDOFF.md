# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record: `main` after G-19 merge
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed remediation task: **N-04G-19 [P0] Frozen remediation design implementation**
- Next task: **N-04G-20 [P0] Adversarial / Replay / Verifier Benchmark / Regression**

---

## 1. Formal v2 failure remains historical evidence

Formal run:

```text
run_id: 20261018T213810+0900
Reference Workstation: Windows 11 / Python 3.10.6 / RTX 4090 24GB
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
```

Result:

```text
Saber Roleplay              Machine ACCEPTED / Formal FAIL / Retry 0
Similar Work Comparison     Machine REJECTED / Formal FAIL / Retry 1
Concept Combination Creative Machine REJECTED / Formal FAIL / Retry 1
Overall                     0 / 3 Case PASS
```

Safety/regression in the v2 run was clean, so Retrieval / MCP / Context Builder / canonical schema are not remediation targets without new evidence.

---

## 2. Post-G12 design chain

```text
G-13 Root-cause / desk review / research        Complete
G-14 Atomic claim / semantic-role boundary      Complete
G-15 Output schema / presentation hardening     Complete
G-16 Semantic validation architecture           Complete
G-17 Material / terminal / render gate          Complete
G-18 Post-G12 v3 Design Freeze                  Complete / Frozen
G-19 Frozen remediation implementation          Complete
G-20 Adversarial / replay / verifier benchmark  NEXT
G-21 v3 acceptance / harness freeze             Pending
G-22 Formal v3 re-acceptance                    Pending
```

N-04 becomes Complete only after G-22 passes all formal and regression Gates.

---

## 3. Frozen v3 contract identities

Authoritative design:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Frozen logical contracts:

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

Output shape:

```text
main           -> source_fact(text, support_refs[])
interpretation -> interpretation(text, premise_unit_ids[])
creative       -> creative_addition(text)
context_limit  -> context_limit(limit_code)
```

Removed from v3 model output:

```text
free-form label
stylistic_expression
free-form context-limit prose
interpretation direct K support_refs
```

---

## 4. G-19 implementation record

Authoritative implementation record:

```text
docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md
```

Primary implementation files:

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

Implemented pipeline:

```text
Output v2 / V0
  ↓
Reference Integrity / V1
  ↓
Atomicity + Role Boundary / V2
  ↓
Deterministic support / V3
  ↓
V4F Source Fact Verification
or
V4I Interpretation Derivation
  ↓
V5 Grounding Aggregate
  ↓
MaterialRequirementGate
  ↓
Failure/Terminal policy v2
  ↓
Terminal-bound deterministic renderer
```

---

## 5. Important G-19 behavior

### Atomicity / role

Natural-language material units require an explicit Atomicity/Role Gate result.

```text
ATOMIC + ROLE_VALID -> support/derivation validation may continue
NON_ATOMIC / ROLE_VIOLATION / INDETERMINATE -> no Grounding PASS
```

Missing required validator runtime is fail-closed.

### Source fact

```text
V3 exact deterministic support -> supported

V3 unresolved
  -> specialized source-fact verifier
  -> SUPPORTED_CANDIDATE only
  -> independent bounded source-fact judge
  -> ENTAILED agreement only
  -> supported
```

Specialized negative cannot be rescued by the general judge. Disagreement does not PASS.

### Interpretation

Interpretation references already-supported source facts through `premise_unit_ids[]`.

Unsupported/non-source premise blocks derivation before the derivation judge is called.

### Material Requirement Gate

Grounding PASS is not use-case completion.

The Gate computes source coverage from:

```text
validated source_fact
 -> support_refs
 -> K unit
 -> source object ID
```

It distinguishes generator omission (`FAIL_REPAIRABLE`) from required material absent in supplied Context (`FAIL_CONTEXT_INSUFFICIENT`).

### Context limit

Model output uses only:

```text
limit_code = material_requirements_not_satisfied
```

`INSUFFICIENT_CONTEXT` is allowed only when the Material Gate independently confirms insufficiency. Human-readable text is trusted renderer output.

### Terminal/render binding

Validation / Material / Terminal / Renderer bind the same candidate through:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

`REJECTED` and `SYSTEM_FAILURE` cannot be rendered as grounded output.

---

## 6. Verifier runtime is intentionally not frozen yet

G-19 implements adapter boundaries only:

```text
AtomicityRoleValidatorAdapter
SourceFactVerifierAdapter
SourceFactJudgeAdapter
InterpretationDerivationJudgeAdapter
```

Candidates remain:

```text
MiniCheck family = primary source-fact verifier benchmark candidate
AlignScore       = secondary candidate
```

Do not treat a particular checkpoint/revision/threshold as adopted before G-20 benchmark and G-21 runtime freeze.

---

## 7. G-19 verification status

Focused v3 implementation tests were migrated and executed in an isolated/equivalent environment:

```text
22 passed
```

This confirms the focused contract/pipeline wiring, but it is **not** the G-20 formal regression result.

Still required in G-20:

```text
G-12 replay fixtures
adversarial cases
actual verifier candidate benchmark
provider/application schema preflight
full pytest
Ruff
git diff --check
```

---

## 8. Next task — N-04G-20

```text
N-04G-20 [P0]
Adversarial / Replay / Verifier Benchmark / Regression
```

Minimum required checks from the G-18 Freeze:

1. supported + unsupported clause in one unit -> no PASS.
2. material fact disguised as style -> no PASS.
3. creative block containing source Concept fact -> no role PASS.
4. unsupported interpretation premise -> no derived_supported.
5. one-side-only comparison -> no Material PASS.
6. arbitrary model label -> contract rejection / no render.
7. materially incomplete grounded output -> no ACCEPTED.
8. unjustified context-limit -> no INSUFFICIENT_CONTEXT.
9. justified exclusive context-limit -> CONTEXT_LIMIT_ONLY render only.
10. REJECTED / SYSTEM_FAILURE -> renderer refuses.
11. attempt/output digest mismatch -> renderer refuses.
12. source-fact verifier disagreement -> no Grounding PASS.
13. G-12 Case 1/2/3 replay -> no false acceptance.
14. provider/application schema preflight -> no hidden mismatch.

Verifier candidate eligibility for G-21 requires:

```text
required negative/replay false-positive = 0
```

G-20 must also run full pytest, Ruff, and git diff --check.

---

## 9. Read first in next chat

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
4. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
5. `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
6. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
7. `tests/test_n04_grounded_generation.py`

---

## 10. Protected boundaries

Unless new failure evidence requires reopening them, do not change:

```text
Object identity
current accepted Version semantics
Canonical Statement / Attribute / Relation
Evidence / Provenance
Version immutability
Retrieval / Similarity basic contract
MCP read boundary
Context Builder selection / budget
N-03 dataset
G-12 failed evidence
```

Do not relax the rubric or Frozen v3 contract to obtain a PASS.
