# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed remediation task: **N-04G-18 [P0] Post-G12 Design Freeze**
- Next task: **N-04G-19 [P0] Frozen remediation design implementation**

---

## 1. Purpose

別チャットでN-04 post-G12 remediationを継続するための開始点を固定する。

GitHubは`main`を正本とする。過去のPhase N stacked branchは再利用しない。

G-18までの設計はFreeze済み。G-19以降でsilent design driftしない。

---

## 2. Formal v2 result

Formal run:

```text
run_id: 20261018T213810+0900
Reference Workstation: Windows 11 / Python 3.10.6 / RTX 4090 24GB
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
```

| Case | Machine terminal | Formal verdict | Retry |
|---|---|---|---|
| Saber Roleplay | ACCEPTED | FAIL | 0 |
| Similar Work Comparison | REJECTED | FAIL | 1 |
| Concept Combination Creative | REJECTED | FAIL | 1 |

```text
0 / 3 Case PASS
N-04 = Failed
N-05 = blocked
```

Safety / regressionは正常だった。

```text
canonical SHA-256 before == after
integrity before / after = PASS / PASS
focused grounding = 21 passed
focused read-path = 27 passed
full pytest = 382 passed / 0 skipped / 0 failed
Ruff = PASS
git diff --check = PASS
```

Retrieval / MCP / Context Builder / canonical safetyを今回のfailure原因として扱わない。

---

## 3. G-12 / G-13 failure summary

### Case 1

- supported clause + unsupported Holy Grail War claimが同一unitに混在。
- semantic validatorがunit全体を`entailed`と誤判定。
- material relationship claimが`stylistic_expression`として`role_valid`を通過。
- unsupported contentがMachine `ACCEPTED`後にrenderされた。

### Case 2

- unsupported source claim。
- retryでsupport refs欠落。
- unsupported / hidden interpretation premiseが`derived_supported`相当へ進み得た。

### Case 3

- `label=null`がprovider schemaでは合法、application parserでは違法。
- same mismatchのままretryし、repair不能loopになった。

Additional gaps:

- atomicity instruction-only。
- support-free role escape。
- source fact / interpretationをone general LLM judgeへ圧縮。
- weak material sufficiency fallback。
- renderer not terminal-bound。
- multi-object coverage not machine-gated。

---

## 4. G-14〜G-17 completed decisions

### G-14 — Atomicity / role boundary

```text
docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
```

- `1 unit = 1 atomic semantic proposition`。
- `ATOMIC / NON_ATOMIC / INDETERMINATE` Gate。
- content-first role boundary。
- mixed-role unit禁止。
- v3 model-authored `stylistic_expression`禁止。
- interpretation conclusion-only。
- Gate failureをsemantic judge positiveでoverride不可。

### G-15 — Output / presentation

```text
docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
```

- model free-form `label`削除。
- trusted deterministic headings。
- role-specific block schema。
- provider/application schema single source of truth。
- hidden parser-only structural rules禁止。

### G-16 — Semantic validation

```text
docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md
```

Source fact:

```text
V3 deterministic
  ↓ unresolved
specialized source-fact verifier
  ↓ SUPPORTED_CANDIDATE
independent bounded LLM judge
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

- MiniCheck family primary benchmark candidate。
- AlignScore secondary candidate。
- verifier disagreement / unavailable / indeterminateはPASS不可。
- exact checkpoint/thresholdはG-20 benchmark後G-21でfreeze。

### G-17 — Material / terminal / render

```text
docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md
```

```text
Grounding PASS
   ↓
Material Requirement PASS
   ↓
Terminal ACCEPTED
   ↓
Render authorization
```

- Comparison: required全Object source coverage。
- Creative: required全Concept source coverage + creative addition。
- Roleplay formal minimum factsはharness profile。
- `INSUFFICIENT_CONTEXT` = context-limit-only safe path。
- `REJECTED / SYSTEM_FAILURE`はgrounded render不可。
- output/context/run/attempt identity binding必須。

---

## 5. G-18 — Post-G12 v3 Design Freeze

正本:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Status:

```text
N-04G-18 = Complete
Post-G12 v3 Design = Frozen
```

### Frozen contract versions

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2   revised
sgokb.grounding-validation.v2         revised
sgokb.material-requirement.v1         new
sgokb.grounding-failure-policy.v2     revised
```

### Frozen output v2 shape

```text
main
  -> source_fact(text, support_refs[])

interpretation
  -> interpretation(text, premise_unit_ids[])

creative
  -> creative_addition(text)

context_limit
  -> context_limit(limit_code)
```

Removed:

```text
model free-form label
model-authored stylistic_expression
interpretation direct K support_refs
free-form model-authored context-limit prose
```

### Context-limit clarification

G-14では`context_limit`をsupplied Contextに関するmaterial epistemic propositionと定義していた一方、G-16ではfree-form textのtruth verification pathが独立していなかった。

G-18でこのgapを閉じた。

v3 baseline:

```text
limit_code = material_requirements_not_satisfied
```

のみをgeneratorが出し、Material Gateが本当に必要materialがContextへ存在しないことを確認した場合だけ`INSUFFICIENT_CONTEXT`へ進む。

Human-visible不足説明はtrusted safe rendererが生成する。

Context-limit outputはexclusiveであり、main / interpretation / creativeと混在できない。

### Frozen Gate sequence

```text
Output v2
  ↓
V0 Structural Contract
  ↓
V1 Reference Integrity
  ↓
V2 Atomicity / Role / Scope
  ↓
V3 Deterministic Source Support
  ↓
V4F Source Fact / V4I Interpretation
  ↓
V5 Grounding Aggregate
  ↓
Material Requirement Gate
  ↓
Failure / Retry / Terminal v2
  ↓
Render authorization
```

`Grounding PASS`だけではACCEPTEDでもrenderableでもない。

### Frozen identity binding

Validation / Material / Terminal / Rendererは同一candidateへ最低限:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

でbindする。

`output_digest`はparsed output canonical JSONのSHA-256。

### Frozen formal requirement profile structure

Case 1:

```text
required_source_objects = [Saber]
minimum_supported_source_fact_units = 2
```

Case 2:

```text
required_source_objects = [Work A, Work B]
minimum_source_fact_per_object = 1
minimum_interpretation_units = 1
require_cross_source_interpretation = true
```

Case 3:

```text
required_source_objects = [Tsundere, Hero's Journey]
minimum_source_fact_per_object = 1
minimum_creative_addition_units = 1
```

concrete stable Object IDsはG-21 harnessでfreezeする。

### Failure taxonomy additions

```text
ATOMICITY_VIOLATION
ATOMICITY_INDETERMINATE
ROLE_BOUNDARY_VIOLATION
ROLE_BOUNDARY_INDETERMINATE
VERIFIER_DISAGREEMENT
PREMISE_INTEGRITY_ERROR
UNSUPPORTED_DERIVATION
SOURCE_COVERAGE_MISSING
COMPARISON_COVERAGE_INCOMPLETE
CREATIVE_SOURCE_COVERAGE_INCOMPLETE
CREATIVE_ADDITION_MISSING
CONTEXT_LIMIT_NOT_JUSTIFIED
MATERIAL_REQUIREMENT_INDETERMINATE
RENDER_AUTHORIZATION_DENIED
OUTPUT_DECISION_BINDING_MISMATCH
```

---

## 6. Current remediation chain

```text
N-04G-13  Root-cause / desk review / research          Complete
N-04G-14  Atomic claim / semantic-role redesign        Complete
N-04G-15  Output / presentation contract hardening     Complete
N-04G-16  Semantic validation architecture             Complete (design)
N-04G-17  Material / terminal / render gate             Complete (design)
N-04G-18  Post-G12 v3 Design Freeze                     Complete / Frozen
N-04G-19  Frozen design implementation                  Pending ← NEXT
N-04G-20  Adversarial / verifier benchmark/regression   Pending
N-04G-21  v3 acceptance / harness freeze                Pending
N-04G-22  Formal v3 re-acceptance                       Pending
```

N-04 CompleteはG-22で3/3 Case PASS + safety/regression Gate全PASS後のみ。

---

## 7. Next task — N-04G-19

```text
N-04G-19 [P0]
Frozen remediation design implementation
```

実装scope最低候補:

```text
src/sgokb/grounding/output.py
src/sgokb/grounding/request.py
src/sgokb/grounding/validation.py
src/sgokb/grounding/failure.py
src/sgokb/grounding/render.py
src/sgokb/application_grounding.py
```

必要に応じて新規:

```text
atomicity.py
material_gate.py
fact_checker.py / semantic_verifier.py
```

G-19 requirements:

- output v2 logical schemaを実装。
- role-specific unit shapesを実装。
- context-limit exclusive structured safe pathを実装。
- output digest utilityを単一化。
- Atomicity / Role Gateを実装。
- V4F source-fact / V4I interpretationを分離。
- Material Requirement Gateを実装。
- failure-policy v2 / render modes / identity bindingを実装。
- provider/application schema single source of truthを維持。
- source-fact verifierはG-20 benchmark可能なadapterとして統合。
- G-20前に特定checkpoint/thresholdをfinal production authorityと宣言しない。
- canonical DB / MCP ownershipは変更しない。

G-19からproduction code変更を開始してよい。

---

## 8. Read first in next chat

1. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
4. `docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md`
5. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
6. `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
7. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
8. `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`
9. `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
10. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`

---

## 9. Protected boundaries

具体的failure evidenceまたはexplicit Freeze reopenなしに変更しない。

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
G-18 Frozen semantic contract
```

rubricを緩和してPASSさせない。
