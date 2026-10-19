# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-19

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Formal run: `20261018T213810+0900`
- Branch of record: `main`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Root-cause review: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- G-14 decision: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- G-15 decision: `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
- G-16 decision: `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- G-17 decision: `docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md`
- G-18 freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Current parent state: **N-04 Failed / N-05 blocked**

---

## 1. Purpose

G-12で確認されたfailureを、model retryやrubric緩和で隠さず、grounded-generation contract / validation / completion / terminal / rendererをfail-closedに再設計する。

G-12で正常だった以下は、具体的な新failure evidenceがない限り変更しない。

- MCP public read boundary
- current Version resolution
- Context Builder / Grounded Context projection
- Similarity retrieval
- canonical read-only safety
- integrity
- focused/full regression

重点対象:

```text
generation output contract
atomicity
semantic-role boundary
support / premise validation
semantic verifier
material sufficiency
retry / terminal outcome
renderer authorization
adversarial tests
formal harness
```

---

## 2. G-12 failure summary

### Case 1 — Roleplay

```text
Machine terminal: ACCEPTED
Formal verdict: FAIL
Retry: 0
```

- supported clauseとunsupported Holy Grail War claimが同一unitに混在。
- semantic validatorがunit全体を`entailed`と誤判定。
- material relationship claimが`stylistic_expression`として`role_valid`を通過。
- unsupported contentがrendered responseへ到達。

### Case 2 — Comparison

```text
Machine terminal: REJECTED
Formal verdict: FAIL
Retry: 1
```

- unsupported source claim。
- retryでsupport refs欠落。
- unsupported / hidden interpretation premiseが`derived_supported`相当へ進み得た。

### Case 3 — Creative

```text
Machine terminal: REJECTED
Formal verdict: FAIL
Retry: 1
```

- creative / interpretation blockの`label=null`。
- provider JSON Schemaでは合法、Python parserでは違法というcontract mismatch。

---

## 3. Remediation principles

1. **G-12 failed evidenceを削除・上書きしない。**
2. **N-04をCompleteへ変更しない。**
3. **N-05をblockedのまま維持する。**
4. v1 / v2 failed acceptance specを履歴として保持する。
5. 同じ条件での単純再試行をしない。
6. rubricを緩和してPASSさせない。
7. generatorをuntrusted componentとして扱う。
8. semantic verifierもfallible componentとして扱う。
9. 構造で防げるfailureをLLM judgeへ委ねない。
10. rendered semantic contentをvalidation / trusted deterministic rendererの管理下に置く。
11. claim-level / premise-level / terminal-levelでfail-closedにする。
12. external verifier libraryはbenchmark合格前にproduction authority化しない。

---

## 4. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-13 | P0 | **Complete (2026-10-18)** | Root-cause / desk review / external research |
| N-04G-14 | P0 | **Complete (2026-10-19)** | Atomic claim / semantic-role boundary redesign |
| N-04G-15 | P0 | **Complete (2026-10-19)** | Output schema / presentation / renderer hardening |
| N-04G-16 | P0 | **Complete (2026-10-19, design)** | Semantic validation architecture redesign |
| N-04G-17 | P0 | **Complete (2026-10-19, design)** | Material sufficiency / terminal / render gate redesign |
| N-04G-18 | P0 | **Complete (2026-10-19, Design Frozen)** | G-14〜G-17をPost-G12 v3 architectureへ統合 |
| N-04G-19 | P0 | Pending | Frozen remediation designを実装しcandidate verifierを統合 |
| N-04G-20 | P0 | Pending | Adversarial / replay / verifier benchmark / regression |
| N-04G-21 | P0 | Pending | v3 acceptance spec / Reference Workstation harness freeze |
| N-04G-22 | P0 | Pending | Formal v3 re-acceptance |

N-04 CompleteはN-04G-22で全Gate PASS後のみ可能とする。

---

## 5. N-04G-13 — Root-cause / Desk Review / External Research

**Status: Complete (2026-10-18)**

正本:

```text
docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
```

主な結論:

- atomicityがinstruction-only。
- support-free role escapeが存在。
- source fact / interpretationをone general LLM judgeへ圧縮。
- schema/parser presentation rule不一致。
- free-form labelがvalidation外でrender可能。
- material sufficiency fallbackが弱い。
- rendererがterminalへbindされていない。
- multi-object coverageがmachine Gate化されていない。
- adversarial regressionが不足。

---

## 6. N-04G-14 — Atomic claim / semantic-role boundary redesign

**Status: Complete (2026-10-19)**

正本:

```text
docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
```

Frozen direction:

- `1 validation unit = 1 atomic semantic proposition`。
- `ATOMIC / NON_ATOMIC / INDETERMINATE` Gate。
- content-first role boundary。
- mixed-role unit禁止。
- model-authored `stylistic_expression`をv3 baselineから削除。
- creative/source fact境界をfail-closed化。
- interpretationをconclusion-only化。
- Atomicity/Role Gate failureを後段verifierがoverrideできない。

---

## 7. N-04G-15 — Output schema / presentation / renderer hardening

**Status: Complete (2026-10-19)**

正本:

```text
docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
```

Frozen direction:

- free-form model `label`削除。
- trusted deterministic heading。
- role-specific block/unit shape。
- provider schema / application parserを単一logical schemaから導出。
- parser-local hidden structural rule禁止。
- visible model semantic textはvalidated `unit.text`のみ。
- output contract breaking revisionをG-18でfinalize。

---

## 8. N-04G-16 — Semantic validation architecture redesign

**Status: Complete (2026-10-19, design)**

正本:

```text
docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md
```

Source fact:

```text
V3 deterministic support
  ↓ unresolved
specialized source-fact verifier
  ↓ SUPPORTED_CANDIDATE
independent bounded LLM judge
  ↓ ENTAILED agreement
supported
```

- MiniCheck family = primary benchmark candidate。
- AlignScore = secondary candidate。
- specialized negativeをLLM positiveで救済しない。
- disagreement / indeterminate / unavailableをPASSへ倒さない。

Interpretation:

```text
validated source_fact
  ↓ premise_unit_ids
Premise Integrity Gate
  ↓
bounded derivation judge
```

- direct K support方式を廃止。
- premiseはsupported source_factのみ。
- interpretation chaining禁止。
- hidden external premiseは`derived_supported`不可。

特定verifier checkpoint / thresholdはまだ未採用。G-20 empirical Gate後にG-21でfreezeする。

---

## 9. N-04G-17 — Material sufficiency / terminal / render gate redesign

**Status: Complete (2026-10-19, design)**

正本:

```text
docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md
```

Target:

```text
Grounding PASS
   ↓
Material Requirement PASS
   ↓
Terminal ACCEPTED
   ↓
Renderer authorization
   ↓
NORMAL render
```

- Material Requirement Gateを独立化。
- generic core requirementとbenchmark profileを分離。
- comparisonはrequired全Object coverage。
- creativeはrequired全Concept coverage + creative addition。
- roleplay formal minimum factsはharness profileから注入。
- `INSUFFICIENT_CONTEXT`をcontext-limit-only safe pathへ限定。
- `REJECTED / SYSTEM_FAILURE`はgrounded render不可。
- terminal/output/context/run/attempt identity bindingを要求。

---

## 10. N-04G-18 — Post-G12 Design Freeze

**Status: Complete (2026-10-19, Design Frozen)**

正本:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

### Frozen contract identities

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2   revised
sgokb.grounding-validation.v2         revised
sgokb.material-requirement.v1         new
sgokb.grounding-failure-policy.v2     revised
```

### Final output shape

- `main -> source_fact(text, support_refs)`
- `interpretation -> interpretation(text, premise_unit_ids)`
- `creative -> creative_addition(text)`
- `context_limit -> structured limit_code`
- free-form `label`なし。
- `stylistic_expression`なし。
- context-limit outputは他blockとexclusive。

### Context-limit integration clarification

G-14/G-16間に残っていた「free-form epistemic textを誰が真偽検証するか」という曖昧さを解消した。

v3 baselineではLLMはfree-form context-limit proseを生成しない。

```text
limit_code = material_requirements_not_satisfied
```

を出し、Material Gateが実際のContext不足を確認した場合だけ`INSUFFICIENT_CONTEXT`を許可する。Human-visible不足説明はtrusted safe rendererが生成する。

### Final Gate order

```text
Output v2
  ↓
V0 Structural
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
Retry / Terminal Policy v2
  ↓
Render authorization
```

### Identity binding

Validation / Material / Terminal / Rendererは最低限:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

で同一candidateへbindする。

### Failure taxonomy

Grounding failureとMaterial/Terminal failureを分離し、少なくとも:

```text
ATOMICITY_VIOLATION
ROLE_BOUNDARY_VIOLATION
VERIFIER_DISAGREEMENT
PREMISE_INTEGRITY_ERROR
UNSUPPORTED_DERIVATION
SOURCE_COVERAGE_MISSING
COMPARISON_COVERAGE_INCOMPLETE
CREATIVE_SOURCE_COVERAGE_INCOMPLETE
CREATIVE_ADDITION_MISSING
CONTEXT_LIMIT_NOT_JUSTIFIED
RENDER_AUTHORIZATION_DENIED
OUTPUT_DECISION_BINDING_MISMATCH
```

を明示的に扱う。

### Completion condition

- [x] G-14〜G-17統合。
- [x] G-02/G-04/G-05/G-06/G-07とのsupersession関係明示。
- [x] output v2 shape/version freeze。
- [x] validation v2 freeze。
- [x] material-requirement v1 freeze。
- [x] failure-policy v2 freeze。
- [x] context-limit safe path freeze。
- [x] terminal/render authorization freeze。
- [x] failure taxonomy統合。
- [x] G-19 implementation boundary確定。
- [x] production code未変更。

---

## 11. N-04G-19 — Implementation

**Status: Pending**

Freezeをそのまま実装する。最低対象:

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

追加要件:

- output digest utilityを単一実装へ集約。
- provider/application schemaを単一正本から導出。
- source-fact verifierはbenchmark可能なadapterとして統合。
- particular checkpoint/thresholdをG-19だけでfinal adoptionしない。
- canonical DB / MCP ownershipを変更しない。

---

## 12. N-04G-20 — Adversarial / Replay / Verifier Benchmark / Regression

**Status: Pending**

必須test:

1. supported + unsupported clause in one unit -> no PASS。
2. material fact disguised as style -> no PASS。
3. creative block containing source Concept fact -> no role PASS。
4. unsupported interpretation premise -> no derived_supported。
5. one-side-only comparison -> no Material PASS。
6. arbitrary model label -> no unvalidated render。
7. materially incomplete grounded output -> no ACCEPTED。
8. unjustified context-limit -> no INSUFFICIENT_CONTEXT。
9. justified exclusive context-limit -> safe render only。
10. REJECTED / SYSTEM_FAILURE -> renderer refuses。
11. attempt/output digest mismatch -> renderer refuses。
12. verifier disagreement -> no Grounding PASS。
13. G-12 Case 1/2/3 replay -> no false acceptance。
14. provider/application schema preflight -> no hidden mismatch。

Verifier benchmark candidate acceptance:

```text
required negative/replay false-positive = 0
```

Full pytest / Ruff / diff check required。

---

## 13. N-04G-21 — v3 Acceptance / Harness Freeze

**Status: Pending**

Formal run前にfreeze:

- generator model/runtime/settings
- source-fact verifier exact checkpoint/revision
- verifier threshold profile/hash
- independent source-fact LLM judge
- interpretation derivation judge
- atomicity/role classifier runtime if model-based
- material requirement profiles + concrete stable Object IDs
- provider structured-output mechanism/schema hash
- retry/terminal policy
- evidence tree
- adversarial/verifier preflight result
- formal rubric

G-20 empirical Gate未達profileはfreezeしない。

---

## 14. N-04G-22 — Formal v3 Re-Acceptance

**Status: Pending**

同じ3代表use caseを維持する。

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

## 15. Dependency

```text
G-12 valid formal FAIL
  ↓
G-13 Root-cause / Desk review / Research Complete
  ↓
G-14 Atomicity / Role Boundary Complete
  ↓
G-15 Output / Presentation Contract Complete
  ↓
G-16 Semantic Validation Architecture Complete
  ↓
G-17 Material / Terminal / Render Gate Complete
  ↓
G-18 Post-G12 Design Freeze Complete
  ↓
G-19 Implementation + verifier candidate integration  ← NEXT
  ↓
G-20 Adversarial / Verifier Benchmark / Regression
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

## 16. Explicit non-goals

本remediationだけを理由に次を変更しない。

- canonical 52-table model
- Object ID / Version identity
- Source / Evidence / Provenance
- MCP read-only boundary
- Context Builder budget / purpose selection
- Similarity ranking algorithm
- N-06 retrieval-quality metrics

新しいfailure evidenceが出た場合のみ別Taskとして扱う。
