# N-04G-18 Post-G12 Grounded Generation v3 Design Freeze

更新日: 2026-10-19

- Status: **Accepted / Design Frozen**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Root cause: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- G-14: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- G-15: `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
- G-16: `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- G-17: `docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md`
- Previous freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Failure policy baseline: `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`

---

## 1. Freeze decision

N-04G-14〜G-17を統合し、Post-G12 grounded-generation architectureを**v3 acceptance用のP0 Design Freeze**として確定する。

このFreeze以降、N-04G-19〜G-22では本書の意味設計をsilentに変更しない。

変更が必要な場合は:

1. どのFrozen invariantをreopenするか明記する。
2. G-12 failure preventionへ与える影響を説明する。
3. Decision文書を更新する。
4. 再Freezeする。

rubricやcontractを実行後に緩めてPASSさせることは禁止する。

---

## 2. What remains unchanged

次はG-07までの設計を維持する。

- Canonical SGOKB Knowledge ownership
- current accepted Version semantics
- MCP = Knowledge Access / transport adapter
- Context Builder selection / budget semantics
- `sgokb.context-builder.v1`
- `sgokb.grounded-context.v1`
- context-local `K*` reference namespace
- `context_fingerprint`
- no direct SQLite for AI input
- no Web / cloud / external fact supplementation
- local-only formal runtime
- generator = untrusted best-effort component
- one initial generation + maximum one retry
- whole-output regeneration
- no partial salvage of failed output
- no canonical mutation from grounded-generation workflow

Retrieval / Similarity / canonical schemaはG-12 failureの原因ではないため変更しない。

---

## 3. What this Freeze supersedes

G-07はv1/v2 acceptance historyとして保持するが、Post-G12 v3 formal acceptanceでは本書を優先する。

### G-02

基本taxonomyは維持するが、v3 model outputでは:

- `stylistic_expression`を禁止する。
- `context_limit`をfree-form LLM proseとして扱わない。
- `interpretation`はconclusion-onlyとする。

### G-04

`sgokb.grounded-generation-output.v1`は履歴として保持し、v3では`v2`へrevisionする。

### G-05

単一general-purpose V4 semantic judgeを廃止し、Atomicity / Role Gate、V4F source-fact verification、V4I interpretation derivationへ分離する。

### G-06

bounded single retryは維持するが、Material Requirement Gate、strict `INSUFFICIENT_CONTEXT`、render authorizationを加えるためfailure/terminal policyは`v2`へrevisionする。

### G-07

旧End-to-End Freezeはhistorical v2 freezeとする。Post-G12 formal v3では本書が新しいfreeze pointである。

---

## 4. Frozen contract/version set

v3 acceptance architectureでは次をFrozen logical contract identityとする。

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2   revised
sgokb.grounding-validation.v2         revised
sgokb.material-requirement.v1         new
sgokb.grounding-failure-policy.v2     revised
```

`v3`はN-04 acceptance architectureの世代名であり、個々のlogical contract version番号と同一ではない。

---

## 5. Frozen end-to-end sequence

```text
Canonical SGOKB Knowledge
        ↓
KnowledgeReadApplication / Context Builder
        ↓
sgokb.context-builder.v1
        ↓
Grounding Reference Projection
        ↓
sgokb.grounded-context.v1
        ↓
Consumer Orchestrator
        ↓
Untrusted Local Generator
        ↓
sgokb.grounded-generation-output.v2
        ↓
V0 Structural Contract
        ↓
V1 Reference Integrity
        ↓
V2 Atomicity / Semantic Role / Scope
        ↓
V3 Deterministic Source Support
        ↓
V4F Source Fact Verification
   and/or
V4I Interpretation Derivation Verification
        ↓
V5 Grounding Aggregate
        ↓
Grounding PASS
        ↓
sgokb.material-requirement.v1
        ↓
Material PASS
        ↓
sgokb.grounding-failure-policy.v2
        ↓
Terminal ACCEPTED
        ↓
Render authorization binding
        ↓
Deterministic NORMAL renderer
        ↓
Human-readable grounded response
```

`Grounding PASS`だけでは`ACCEPTED`にもrenderにも進めない。

---

## 6. Frozen output contract — `sgokb.grounded-generation-output.v2`

### 6.1 Common envelope

```json
{
  "contract_version": "sgokb.grounded-generation-output.v2",
  "context_fingerprint": "...",
  "purpose": "roleplay | comparison | creative",
  "blocks": []
}
```

Top-level unknown fieldは許可しない。

### 6.2 Presentation roles

```text
main
interpretation
creative
context_limit
```

model-generated free-form `label`は存在しない。

Visible headingはtrusted rendererが`presentation_role`から決定論的に生成する。

### 6.3 `main` block

`source_fact` unit専用。

```json
{
  "block_id": "B1",
  "presentation_role": "main",
  "units": [
    {
      "unit_id": "U1",
      "semantic_role": "source_fact",
      "text": "...",
      "support_refs": ["K1"]
    }
  ]
}
```

Constraints:

- `support_refs`は1件以上。
- 1 unit = 1 atomic source-world proposition。
- multiple K refsが1 propositionを共同supportすることは許容する。

### 6.4 `interpretation` block

`interpretation` unit専用。

```json
{
  "block_id": "B2",
  "presentation_role": "interpretation",
  "units": [
    {
      "unit_id": "U3",
      "semantic_role": "interpretation",
      "text": "...atomic conclusion...",
      "premise_unit_ids": ["U1", "U2"]
    }
  ]
}
```

Constraints:

- direct K `support_refs`を持たない。
- premiseは同一output内のvalidated `source_fact`のみ。
- interpretation chainingは禁止。
- self-reference / cycle / duplicate premise IDは禁止。

### 6.5 `creative` block

`creative_addition` unit専用。

```json
{
  "block_id": "B3",
  "presentation_role": "creative",
  "units": [
    {
      "unit_id": "U4",
      "semantic_role": "creative_addition",
      "text": "..."
    }
  ]
}
```

source factual support fieldを持たない。

Creative text内にsource Object / Conceptについて新しいfactを埋め込んだ場合はG-14 role-boundary failureとなる。

### 6.6 `context_limit` block — final v3 resolution

G-14/G-16/G-17を統合した結果、**free-form model-authored context-limit proseはv3 baselineで採用しない。**

理由:

- `context_limit`は supplied Contextについてのmaterial epistemic propositionである。
- free-form textを`not_applicable`だけで通すと、その真偽を独立検証しない経路が残る。
- G-17 Material Gateが実際の不足をdeterministically確認できるため、LLMに不足理由の自由文を作らせる必要がない。

v3 model outputはstructured limit codeだけを出す。

```json
{
  "block_id": "B1",
  "presentation_role": "context_limit",
  "units": [
    {
      "unit_id": "U1",
      "semantic_role": "context_limit",
      "limit_code": "material_requirements_not_satisfied"
    }
  ]
}
```

Frozen baselineでは`limit_code`は:

```text
material_requirements_not_satisfied
```

のみを必須codeとする。

Human-visible insufficiency proseはLLM textではなく、Material Gateが不足を確認しTerminal `INSUFFICIENT_CONTEXT`を発行した後にtrusted safe rendererが生成する。

### 6.7 Context-limit exclusivity

`context_limit` outputはexclusive shapeとする。

```text
context_limit block exists
-> no main block
-> no interpretation block
-> no creative block
```

normal answerとinsufficiency noticeを同一outputへ混在させない。

### 6.8 Block/role matrix

```text
main           -> source_fact
interpretation -> interpretation
creative       -> creative_addition
context_limit  -> context_limit
```

role pair mismatchはstructural failureである。

### 6.9 Schema source of truth

Canonical logical schemaを単一正本とする。

- providerへ渡すschemaはここから導出する。
- application parserも同じschemaを使用する。
- parser-local hidden structural ruleは禁止する。
- provider unsupported featureはsilent downgradeしない。

provider capabilityはG-19/G-21 preflightで実証する。

---

## 7. Frozen atomicity / semantic-role Gate

Every material text unitは次のverdictを持つ。

```text
atomicity:
  ATOMIC
  NON_ATOMIC
  INDETERMINATE

role_boundary:
  ROLE_VALID
  ROLE_VIOLATION
  INDETERMINATE
```

material support / derivation validationへ進める条件:

```text
atomicity == ATOMIC
AND
role_boundary == ROLE_VALID
```

`NON_ATOMIC` / role violation / indeterminateを後段verifierのpositive verdictでoverrideできない。

Atomicityは文法上のsentence boundaryではなく、独立してgrounding verdictが変わり得るproposition boundaryで判定する。

---

## 8. Frozen source-fact validation

### V3 deterministic path

安全に確定できる場合:

```text
deterministic_supported
-> supported
```

semantic verifierを呼ばない。

### V4F semantic path

V3 unresolved atomic `source_fact`だけを対象にする。

Frozen composition:

```text
specialized source-fact verifier
  ↓
SUPPORTED_CANDIDATE only
  ↓
independent bounded LLM judge
  ↓
ENTAILED agreement
  ↓
supported
```

Fail-closed rules:

- specialized negativeをLLM positiveで救済しない。
- verifier disagreementをPASSへしない。
- indeterminateをPASSへしない。
- required verifier unavailableをPASSへしない。

MiniCheck familyはprimary benchmark candidate、AlignScoreはsecondary candidateとする。

**特定checkpoint / revision / thresholdはDesign Freeze対象外のruntime detailであり、G-20 benchmark成功後G-21でfreezeする。**

---

## 9. Frozen interpretation validation

Grounding chain:

```text
interpretation unit
  ↓ premise_unit_ids
validated source_fact units
  ↓ support_refs
K units
```

Premise Integrity Gate:

1. premise ID >= 1。
2. 同一output内に存在。
3. `source_fact`である。
4. final grounding disposition = `supported`。
5. self-referenceなし。
6. duplicateなし。
7. interpretation chainingなし。
8. cycleなし。

V4I bounded derivation judgeは:

> atomic conclusionがvalidated premise集合だけからreasonableに導けるか

だけを判定する。

Allowed normalized verdict:

```text
REASONABLE_DERIVATION
UNSUPPORTED_DERIVATION
CONTRADICTORY
INDETERMINATE
UNAVAILABLE
```

`REASONABLE_DERIVATION`だけが`derived_supported`へ進める。

external hidden premiseを必要とするconclusionはFAILする。

---

## 10. Frozen Grounding Aggregate — `sgokb.grounding-validation.v2`

Grounding PASS候補は、output内の全unitがroleに応じて成功している場合だけ成立する。

```text
source_fact       -> supported
interpretation    -> derived_supported
creative_addition -> role-valid / not_applicable
context_limit     -> structurally valid limit code
```

ただしcontext-limit outputの`INSUFFICIENT_CONTEXT` eligibilityはGrounding PASSだけで決まらず、Material Gateによる実際のContext insufficiency confirmationを必須とする。

Grounding validationはuse-case completionを判定しない。

---

## 11. Frozen Material Requirement Gate — `sgokb.material-requirement.v1`

Input:

```text
purpose
validated output
validation unit results
Grounded Context metadata
requirement profile
```

Output verdict:

```text
PASS
FAIL_REPAIRABLE
FAIL_CONTEXT_INSUFFICIENT
INDETERMINATE
```

### Generic core requirements

#### roleplay

normal ACCEPTEDにはsupported `source_fact >= 1`。

#### comparison

全required source objectからsupported source fact coverageが必要。

profileがcomparison conclusionを要求する場合、validated interpretationが必要。

#### creative

全required source Conceptからsupported source fact coverageが必要。

valid `creative_addition >= 1`が必要。

### Coverage accounting

source coverageは:

```text
validated source_fact
 -> support_refs
 -> K unit
 -> source object identity
```

からdeterministically算出する。

interpretation / creative textからsource coverageを推測しない。

### Context insufficiency classification

Material Gateはoutput coverageだけでなく、supplied Grounded Context内のavailable source coverageも比較する。

原則:

```text
required material exists in Grounded Context
but generator omitted it
-> FAIL_REPAIRABLE

required material itself is absent from Grounded Context
-> FAIL_CONTEXT_INSUFFICIENT
```

これによりgenerator omissionとKnowledge/Context不足を分離する。

---

## 12. Frozen N-04 v3 requirement profiles

Formal harnessはcoreへthresholdをhardcodeせずprofileとして注入する。

### Case 1 — Roleplay

```text
profile_id = n04-v3-case-1-roleplay
required_source_objects = [Saber]
minimum_supported_source_fact_units = 2
```

### Case 2 — Comparison

```text
profile_id = n04-v3-case-2-comparison
required_source_objects = [Work A, Work B]
minimum_source_fact_per_object = 1
minimum_interpretation_units = 1
require_cross_source_interpretation = true
```

required comparison interpretationのpremise graphには両Work由来source factが必要。

### Case 3 — Creative

```text
profile_id = n04-v3-case-3-creative
required_source_objects = [Tsundere, Hero's Journey]
minimum_source_fact_per_object = 1
minimum_creative_addition_units = 1
```

具体的stable Object IDはG-21 harnessでfreezeする。

---

## 13. Frozen retry / terminal policy — `sgokb.grounding-failure-policy.v2`

Maximum attempts:

```text
attempt 1 + retry 1 = maximum 2 generation attempts
```

Retry前後で固定:

- Grounded Context
- context fingerprint
- purpose
- generator model/runtime/settings
- output contract version
- requirement profile

追加可能なのはstructured failure/repair feedbackだけ。

### Retryable generator/output causes

attempt 1で次は1回retry可能:

- structural contract error
- unknown/missing model-authored reference
- non-atomic / role-boundary violation
- atomicity/role ambiguity caused by wording
- unsupported / contradictory generated claim
- invalid interpretation premise selection
- unsupported derivation
- verifier disagreement where clearer regeneration may resolve wording
- Material `FAIL_REPAIRABLE`
- unjustified context-limit output while usable material exists

Attempt 2で未解消なら原則`REJECTED`。

### Non-retry system causes

次はgenerator retryしない。

- canonical mapping integrity failure
- context fingerprint system mismatch
- required verifier unavailable
- verifier model/revision identity mismatch
- material requirement profile invalid
- source identity resolution system defect
- terminal/render binding defect

→ `SYSTEM_FAILURE`

### Context insufficient path

If normal attempt 1 reaches `FAIL_CONTEXT_INSUFFICIENT`:

- one retryをcontext-limit-only shapeへ収束させるrepair opportunityとして使用してよい。

If context-limit-only attempt is structurally valid and Material Gate independently confirms required material is absent:

- `INSUFFICIENT_CONTEXT`。

If model claims context insufficiency while required material is available:

- attempt 1: repairable retry candidate。
- attempt 2: `REJECTED`。

---

## 14. Frozen terminal outcomes

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

### ACCEPTED

```text
Grounding = PASS
Material = PASS
no system failure
```

`render_mode = NORMAL`

### INSUFFICIENT_CONTEXT

```text
Grounding = PASS
Material = FAIL_CONTEXT_INSUFFICIENT
output = exclusive context_limit shape
Material Gate confirms insufficiency
no system failure
```

`render_mode = CONTEXT_LIMIT_ONLY`

### REJECTED

- exhausted generator/grounding failure
- exhausted Material `FAIL_REPAIRABLE`
- unsafe/mixed insufficiency output
- persistent verifier disagreement/semantic ambiguity that cannot be certified

`render_mode = NONE`

### SYSTEM_FAILURE

- required validation component unavailable
- integrity defect
- contract/profile identity defect
- terminal/render binding defect

`render_mode = NONE`

---

## 15. Frozen render authorization

Normal rendererはvalidation resultだけでは実行できない。

最低入力:

```text
parsed output
validation result
material result
terminal decision
```

Normal render authorization:

```text
terminal.action == ACCEPTED
AND terminal.render_mode == NORMAL
AND validation.verdict == PASS
AND material.verdict == PASS
AND all identities bind to the same output/context/attempt
```

Context-limit render authorization:

```text
terminal.action == INSUFFICIENT_CONTEXT
AND terminal.render_mode == CONTEXT_LIMIT_ONLY
AND output has context_limit role only
AND material.verdict == FAIL_CONTEXT_INSUFFICIENT
AND same output/context/attempt binding
```

`REJECTED / SYSTEM_FAILURE`はgrounded rendererへ渡せない。

---

## 16. Frozen output identity binding

Validation、Material Gate、Terminal Decision、Rendererが同一candidateを扱っていることを明示的にbindする。

最低identity:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

`output_digest`はparsed output envelopeのcanonical JSON bytesに対するSHA-256とする。

Canonicalization invariant:

- UTF-8
- object keyを再帰的にstable sort
- insignificant whitespaceなし
- semantic valueを変更しない

実装詳細はG-19で1つのutilityへ集約する。

Attempt 1 terminal decisionでAttempt 2 outputをrenderすることは禁止する。

---

## 17. Frozen rendering semantics

### NORMAL

Human-visible semantic content:

```text
successfully validated unit.text
+ trusted fixed headings/separators/whitespace
```

Rendererは禁止:

- paraphrase
- summary
- transition claim生成
- arbitrary model label
- hidden rationale表示
- failed unit salvage

### CONTEXT_LIMIT_ONLY

free-form LLM proseをrenderしない。

Material Gate / requirement profileからtrusted system messageを決定論的に生成する。

最低意味:

> supplied Contextだけでは、要求されたgrounded material requirementを安全に満たせない。

Localizationはtrusted application tableで行ってよい。

### NONE

Grounded responseを生成しない。

UIがstatusを表示する場合はtrusted system statusとして別系統にする。

---

## 18. Frozen failure taxonomy

最低failure classを次へ整理する。

### Structural / reference

```text
VALIDATION_CONTRACT_ERROR
REFERENCE_INTEGRITY_ERROR
```

代表code:

```text
malformed_output
unknown_contract_version
missing_required_field
unexpected_field
duplicate_block_id
duplicate_unit_id
duplicate_presentation_role
invalid_block_role_pair
context_limit_mixed_output
unknown_grounding_reference
output_context_fingerprint_mismatch
broken_canonical_mapping
```

### Atomicity / role / scope

```text
ATOMICITY_VIOLATION
ATOMICITY_INDETERMINATE
ROLE_BOUNDARY_VIOLATION
ROLE_BOUNDARY_INDETERMINATE
CREATIVE_SCOPE_VIOLATION
```

### Source fact / verifier

```text
MISSING_REQUIRED_SUPPORT
UNSUPPORTED_CLAIM
CONTRADICTORY_CLAIM
VERIFIER_DISAGREEMENT
VALIDATOR_UNAVAILABLE
```

### Interpretation

```text
PREMISE_INTEGRITY_ERROR
UNSUPPORTED_DERIVATION
DERIVATION_CONTRADICTORY
DERIVATION_INDETERMINATE
```

### Material requirement

```text
MATERIAL_REQUIREMENT_MISSING
SOURCE_COVERAGE_MISSING
COMPARISON_COVERAGE_INCOMPLETE
CREATIVE_SOURCE_COVERAGE_INCOMPLETE
CREATIVE_ADDITION_MISSING
CONTEXT_LIMIT_NOT_JUSTIFIED
MATERIAL_REQUIREMENT_INDETERMINATE
```

### Terminal / render

```text
RENDER_AUTHORIZATION_DENIED
OUTPUT_DECISION_BINDING_MISMATCH
```

Failure classと`failure_code`を分離し、retryability/system-failure classificationはcause単位で保持する。

---

## 19. Frozen evidence requirements

1 runで最低限保存可能にする。

```text
Git head / environment
Grounded Context
context_fingerprint / K mapping
output contract identity/schema hash
requirement profile identity/hash
generator runtime/settings
attempt raw output
parsed output/output_digest
atomicity/role results
source-fact verifier results
verifier threshold profile
independent LLM judge result
interpretation premise graph/derivation result
grounding aggregate
material checks/covered+missing source IDs
retry decision/feedback
terminal decision/render mode
render authorization identity
rendered output if any
```

Formal evidenceはG-21 harnessで物理treeをfreezeする。

---

## 20. G-12 failure replay under Frozen v3 design

### Case 1

- supported + unsupported Holy Grail War clause in one unit → `NON_ATOMIC` → no V4F → no Grounding PASS。
- duty/loyalty claim disguised as style → `stylistic_expression` not in v2 output enum + content-first role failure。
- even grounded output with only1 fact cannot meet formal profile minimum=2。
- no `ACCEPTED`, no NORMAL render。

### Case 2

- unsupported source claim → V3/V4F failure。
- interpretation hidden premise → premise must first exist as validated source fact; unsupported premise cannot enter V4I。
- interpretation lacking both Work provenance cannot meet cross-source Material Gate。
- no false `derived_supported` based only on K presence。

### Case 3

- model `label` field does not exist; `label=null` failure path is removed。
- headings are trusted renderer output。
- both Concepts require source coverage and creative addition is required。
- creative/source boundary remains G-14 content-first validation responsibility。

---

## 21. Required implementation components for G-19

Minimum:

```text
output.py
  -> output v2 schema/parser
  -> role-specific unit shapes
  -> context-limit exclusive shape
  -> canonical output digest

request.py
  -> output v2 instructions
  -> requirement profile exposure needed for repair/context-limit

atomicity.py (new candidate)
  -> atomicity/role Gate adapter

validation.py
  -> grounding-validation.v2
  -> V4F / V4I separation

fact_checker.py / semantic_verifier.py (new candidate)
  -> specialized source fact verifier adapter
  -> bounded LLM judge adapters

material_gate.py (new)
  -> sgokb.material-requirement.v1

failure.py
  -> sgokb.grounding-failure-policy.v2
  -> material/terminal composition

render.py
  -> NORMAL / CONTEXT_LIMIT_ONLY / NONE
  -> terminal/output identity binding

application_grounding.py
  -> new facade wiring

evidence.py
  -> v3 evidence fields as needed
```

Physical class/module names may be adjusted, but responsibility boundaries may not change silently。

---

## 22. Required G-20 adversarial/replay Gates

At minimum:

1. supported + unsupported clause in one unit -> no PASS。
2. material claim disguised as style -> no PASS。
3. creative block with source Concept fact -> no role PASS。
4. unsupported interpretation premise -> no derived_supported。
5. one-sided comparison premise graph -> no Material PASS。
6. arbitrary model label -> contract rejection / no render。
7. materially incomplete grounded output -> no ACCEPTED。
8. unjustified context-limit output when Context is sufficient -> no INSUFFICIENT_CONTEXT。
9. justified exclusive context-limit output -> safe render only。
10. REJECTED / SYSTEM_FAILURE -> renderer refuses。
11. attempt/output digest mismatch -> renderer refuses。
12. source-fact verifier disagreement -> no Grounding PASS。
13. G-12 exact failure shapes replay -> no false acceptance。
14. provider/application schema preflight -> no hidden mismatch。

Source-fact verifier profile cannot be selected for G-21 if any required negative/replay case is false-positive supported。

---

## 23. Frozen vs runtime-specific decisions

### Frozen here

- semantic roles available to v3 output
- atomicity/role Gate semantics
- output v2 logical shape
- interpretation premise graph
- context-limit structured safe path
- source-fact verifier composition policy
- verifier disagreement fail-closed policy
- Material Requirement Gate semantics
- formal requirement profile structure
- retry upper bound
- terminal semantics
- render authorization/binding
- failure class taxonomy

### Frozen later in G-21

- generator model/revision/quantization
- specialized verifier exact checkpoint/revision
- verifier threshold values/profile hash
- independent LLM judge exact model/settings
- derivation judge exact model/settings
- atomicity/role classifier exact runtime if model-based
- LM Studio/provider version
- timeout/GPU/runtime operational settings
- physical acceptance evidence tree

---

## 24. Explicit non-goals

G-18だけを理由に変更しない。

- canonical 52-table model
- Object / Version identity
- Source / Evidence / Provenance
- Context Builder ranking/budget
- Similarity algorithm
- N-06 retrieval quality work
- canonical write path
- MCP ownership boundary

---

## 25. Completion assessment

- [x] G-14〜G-17を1 End-to-End architectureへ統合した。
- [x] G-02/G-04/G-05/G-06/G-07とのsupersession/compatibilityを明記した。
- [x] output contractを`sgokb.grounded-generation-output.v2`としてfreezeした。
- [x] interpretation `premise_unit_ids` shapeをfreezeした。
- [x] context-limit free-form semantic gapをstructured safe pathで解消した。
- [x] grounding validationを`sgokb.grounding-validation.v2`としてfreezeした。
- [x] Material Requirement Gateを`sgokb.material-requirement.v1`としてfreezeした。
- [x] retry/terminalを`sgokb.grounding-failure-policy.v2`としてfreezeした。
- [x] rendererをterminal/output identityへbindした。
- [x] failure taxonomyを統合した。
- [x] G-12 3 Caseを新設計で机上再評価した。
- [x] G-19 implementation boundaryを確定した。
- [x] production codeは変更していない。

**N-04G-18 = Complete / Post-G12 v3 Design Frozen.**

Next:

```text
N-04G-19 [P0] — Frozen remediation design implementation
```
