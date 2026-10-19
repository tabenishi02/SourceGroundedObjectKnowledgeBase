# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record after integration: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed verification task: **N-04G-20 [P0] Adversarial / Replay / Verifier Benchmark / Regression**
- G-20 Gate: **FAIL — repository-wide Ruff 180 errors**
- Next task: **N-04G-20R [P0] Repository-wide Ruff baseline remediation + G-20 engineering Gate rerun**
- N-04G-21: **blocked until G-20R PASS**

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
G-20 Adversarial / verifier regression           Complete (verification) / Gate FAIL
G-20R Repository-wide Ruff remediation           NEXT
G-21 v3 acceptance / harness freeze              BLOCKED
G-22 Formal v3 re-acceptance                     Pending
```

N-04 becomes Complete only after all intervening Gates and G-22 formal acceptance pass.

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

Read first:

```text
docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md
```

Final GitHub Actions run:

```text
run_id: 39198589270
final tested branch SHA: 13248f1f48b0faa232ebaa7c1a76ef052da97d9b
```

Results:

```text
focused + G-12 replay/adversarial: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
G-20 changed-scope Ruff: PASS
git diff --check: PASS
repository-wide Ruff: FAIL — 180 errors
MiniCheck RoBERTa-large screening: PASS necessary verifier Gate
```

Because Task master required `full pytest / Ruff / git diff --check`, repository-wide Ruff failure prevents G-20 Overall PASS. Do not reinterpret the required Ruff Gate as changed-scope-only merely to advance G-21.

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

This could recreate the G-12 Case 3 provider/parser mismatch class.

Fix:

```text
provider JSON Schema == application parse surface
        ↓
Grounding Validation V0
  -> explicit cross-item identity invariants
```

Changed:

```text
src/sgokb/grounding/output.py
src/sgokb/grounding/validation.py
```

The constraints remain fail-closed; only responsibility placement changed.

---

## 7. G-20 replay/adversarial result

New test:

```text
tests/test_n04g20_adversarial_regression.py
```

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

Final focused result:

```text
37 passed
```

---

## 8. MiniCheck screening result

Corpus:

```text
benchmark/n04g20-source-fact-verifier-v1.json
```

Runner:

```text
benchmark/tools/n04g20_minicheck_benchmark.py
```

Persistent result:

```text
benchmark/results/n04g20-minicheck-roberta-large-github-actions.json
```

Diagnostic environment:

```text
GitHub Actions run: 39198589270
MiniCheck repo revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model: lytang/MiniCheck-RoBERTa-Large
threshold candidate: 0.50
required negative/replay false-positive: 0
required positive supported: 2/2
negative specificity: 1.0
positive recall: 0.8
```

This makes MiniCheck RoBERTa-large eligible for later local-runtime evaluation. It is **not** a production/final verifier freeze.

---

## 9. Reference Workstation limitation

During G-20, Remote Desktop Commander reported monthly usage exhausted. Therefore the ChatGPT-side path could not execute the verifier benchmark on the Windows 11 / RTX 4090 Reference Workstation.

GitHub Actions screening is useful candidate evidence but not local-only formal runtime proof.

G-21 must not claim the exact local runtime is frozen until that environment is actually resolved and recorded.

---

## 10. Next task — N-04G-20R

```text
N-04G-20R [P0]
Repository-wide Ruff baseline remediation + G-20 engineering Gate rerun
```

Goal:

Clear the current repo-wide Ruff baseline without changing grounded-generation semantics, then rerun the engineering Gate.

Current baseline:

```text
python -m ruff check .
-> 180 errors
```

Representative locations:

```text
extensions/web-page-capture/native-host/host.py
extensions/web-page-capture/tests/unit/*
src/sgokb/exchange/*
src/sgokb/grounding/render.py
tests/test_n04_grounded_generation.py
other existing tests
```

Required G-20R outcome:

```text
python -m ruff check .                    PASS
focused G19+G20 tests                     PASS
full pytest                               0 failed
git diff --check                          PASS
provider/application V0 fix               preserved
```

Style cleanup must not alter G-18 Frozen semantics. If any lint fix requires behavioral change, isolate and review it rather than hiding it in formatting changes.

After G-20R PASS, update G-20 Overall Gate to PASS and unblock G-21.

---

## 11. Read first in next chat

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
4. `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
5. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
6. `tests/test_n04g20_adversarial_regression.py`
7. `tests/test_n04_grounded_generation.py`

---

## 12. Protected boundaries

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

Do not relax the rubric, verifier false-positive Gate, or repository-wide Ruff Gate merely to obtain a PASS.
