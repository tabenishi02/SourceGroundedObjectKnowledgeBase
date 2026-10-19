# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record after integration: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed remediation task: **N-04G-20R [P0] Repository-wide Ruff baseline remediation + G-20 engineering Gate rerun**
- G-20R result: **PASS**
- Next task: **N-04G-21 [P0] v3 Acceptance / Reference Workstation Harness Freeze**

---

## 1. Historical G-12 failure remains authoritative evidence

Formal v2 run:

```text
run_id: 20261018T213810+0900
Reference Workstation: Windows 11 / Python 3.10.6 / RTX 4090 24GB
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
Overall: 0 / 3 Case PASS
```

Case 1 had Machine ACCEPTED despite unsupported rendered material; Case 2 and Case 3 were REJECTED. G-12 safety/regression was otherwise clean, so canonical / MCP / Retrieval / Context Builder remain protected without new evidence.

---

## 2. Post-G12 chain state

```text
G-13 Root-cause / research                       Complete
G-14 Atomic claim / role boundary                Complete
G-15 Output / presentation hardening             Complete
G-16 Semantic validation architecture            Complete
G-17 Material / terminal / render gate           Complete
G-18 Post-G12 v3 Design Freeze                   Complete / Frozen
G-19 Frozen v3 implementation                    Complete
G-20 Adversarial / verifier regression           Complete / historical Gate FAIL
G-20R Repository-wide Ruff remediation           Complete / PASS
G-21 v3 acceptance / harness freeze              NEXT
G-22 Formal v3 re-acceptance                     Pending
```

G-20 historical FAIL is retained because its original run had repo-wide Ruff 180 errors. G-20R separately proves that blocker has been removed.

N-04 becomes Complete only after G-22 formal acceptance passes all required Gates.

---

## 3. Frozen v3 architecture

Authoritative design:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Frozen contracts:

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

Frozen output:

```text
main           -> source_fact(text, support_refs[])
interpretation -> interpretation(text, premise_unit_ids[])
creative       -> creative_addition(text)
context_limit  -> context_limit(limit_code)
```

Candidate binding:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

Do not reintroduce free-form model labels, `stylistic_expression`, free-form context-limit prose, interpretation direct K support, partial salvage, or unbound rendering.

---

## 4. G-19 implementation

Authoritative record:

```text
docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md
```

Implemented:

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

Verifier interfaces remain adapter boundaries; G-19 did not freeze a concrete checkpoint/threshold.

---

## 5. G-20 authoritative result

Read:

```text
docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md
```

Original G-20 run:

```text
run_id: 39198589270
focused + G-12 replay/adversarial: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
G-20 changed-scope Ruff: PASS
git diff --check: PASS
repository-wide Ruff: FAIL — 180 errors
MiniCheck RoBERTa-large screening: PASS necessary verifier Gate
```

The original Gate remains historical FAIL; do not rewrite that evidence. G-20R resolves its engineering blocker separately.

---

## 6. G-20 provider/application fix

G-20 found a contract defect left by G-19:

```text
provider JSON Schema did not express:
  duplicate_block_id
  duplicate_unit_id
  duplicate_presentation_role

application parser rejected them as hidden rules
```

Fix:

```text
provider JSON Schema == application parse surface
        ↓
Grounding Validation V0
  -> explicit cross-item identity invariants
```

The constraints remain fail-closed; only responsibility placement changed. G-20R preserved this fix.

---

## 7. G-20 replay/adversarial result

Machine coverage includes:

- mixed supported/unsupported unit -> no PASS
- material fact disguised as style -> schema reject
- creative/source Concept role escape -> no PASS
- unsupported interpretation premise -> derivation not invoked
- one-sided comparison -> no Material PASS
- arbitrary label -> reject
- materially incomplete output -> no ACCEPTED
- unjustified context limit -> no INSUFFICIENT_CONTEXT
- justified context limit -> trusted safe render only
- REJECTED / SYSTEM_FAILURE -> no grounded render
- attempt/output digest mismatch -> render denied
- verifier disagreement -> no Grounding PASS
- G-12 Case 3 label mismatch path removed by v2 contract
- provider/application schema preflight

G-20R final focused/replay result remains:

```text
37 passed
```

---

## 8. MiniCheck screening result

Persistent result:

```text
benchmark/results/n04g20-minicheck-roberta-large-github-actions.json
```

Diagnostic candidate:

```text
MiniCheck repo revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model: lytang/MiniCheck-RoBERTa-Large
threshold candidate: 0.50
required negative/replay false-positive: 0
required positive supported: 2/2
negative specificity: 1.0
positive recall: 0.8
```

G-20R did not change verifier semantics, so this screening evidence remains reusable for G-21 candidate selection. It is **not** a production/final verifier freeze.

---

## 9. G-20R authoritative result

Read first:

```text
docs/evaluation/N04G20R_RUFF_BASELINE_REMEDIATION_AND_GATE_RERUN.md
```

Trigger:

```text
repository-wide Ruff = 180 errors
```

Remediation policy:

- Ruff config unchanged.
- ignore / per-file-ignore未追加。
- `noqa`未追加。
- line-length Gate未緩和。
- import order / unused import / formatting / line wrapping中心で修正。
- 日本語固定文字列は値を変えず隣接文字列へ分割。

Final GitHub Actions engineering Gate:

```text
run_id: 39224975505
tested branch SHA: 24b0316aaff2a864c084400f50af920b933c3c24
focused/replay: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
repository-wide Ruff: PASS — All checks passed!
git diff --check: PASS
```

G-20RによりG-20 engineering blockerは解消した。

---

## 10. Reference Workstation limitation carried into G-21

During G-20, Remote Desktop Commander reported monthly usage exhausted. Therefore ChatGPT-side execution could not establish the verifier benchmark on the Windows 11 / RTX 4090 Reference Workstation.

GitHub Actions screening is candidate evidence but not local-only formal runtime proof.

G-21 must resolve and record exact Reference Workstation runtime/profile before claiming the formal harness is frozen.

---

## 11. Next task — N-04G-21

```text
N-04G-21 [P0]
v3 Acceptance / Reference Workstation Harness Freeze
```

G-20R PASSによりengineering dependencyはunblocked。

G-21でfreezeする最低範囲:

- generator exact model/runtime/settings
- source-fact verifier exact checkpoint/revision
- verifier threshold profile/hash
- independent source-fact judge exact model/settings
- interpretation derivation judge exact model/settings
- atomicity/role validator runtime if model-based
- formal Material Requirement profiles + stable Object IDs
- provider structured-output mechanism/schema hash
- retry / terminal policy
- evidence tree
- G-20 verifier benchmark evidence
- G-20R engineering Gate PASS evidence
- formal v3 rubric

G-20 verifier screening必要条件を満たさないprofileはfreezeしない。

---

## 12. Read first in next chat

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/evaluation/N04G20R_RUFF_BASELINE_REMEDIATION_AND_GATE_RERUN.md`
4. `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
5. `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
6. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
7. `benchmark/results/n04g20-minicheck-roberta-large-github-actions.json`
8. `tests/test_n04g20_adversarial_regression.py`
9. `tests/test_n04_grounded_generation.py`

---

## 13. Protected boundaries

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
G-18 Frozen grounded-generation semantics
```

Do not relax the rubric, verifier false-positive Gate, or engineering Gates merely to obtain a PASS.
