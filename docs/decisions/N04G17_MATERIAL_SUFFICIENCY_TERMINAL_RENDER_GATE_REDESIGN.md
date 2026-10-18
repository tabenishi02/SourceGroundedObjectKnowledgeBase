# N-04G-17 Material Sufficiency / Terminal / Render Gate Redesign

更新日: 2026-10-19

- Status: **Complete (design)**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Failure policy: `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`
- Atomicity / role boundary: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- Output / renderer hardening: `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
- Semantic validation redesign: `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- Root cause: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- Remediation task master: `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`

---

## 1. Decision

N-04 post-G12 remediationでは、**Grounding validity、material/use-case sufficiency、workflow terminal outcome、render permissionを4つの独立した責務へ分離する。**

主要Decisionは次である。

1. `Grounding PASS`は「出力中のmaterial semantic unitがgroundedである」ことだけを意味し、user taskを十分に完遂したことまでは意味しない。
2. Grounding PASS後に独立した**Material Requirement Gate**を必須化する。
3. Material Requirement Gateは、outputのsemantic contentを再解釈するLLM judgeではなく、validated unit metadata / support origin / injected requirement profileに基づくdeterministic-first Gateとする。
4. Core SGOKBにはpurpose-levelのgeneric requirementを置き、formal benchmark固有のminimum count / exact conditionは**requirement profileとしてharnessから注入**する。
5. `ACCEPTED`は少なくとも次を全て満たす場合だけ成立する。

```text
Grounding validation = PASS
AND
Material Requirement Gate = PASS
AND
no system failure
AND
terminal policy permits ACCEPTED
```

6. `Grounding PASS`だけで`ACCEPTED`へ進めない。
7. `INSUFFICIENT_CONTEXT`は「material requirementを満たさないoutputの一般的な別名」ではない。**validated context-limit-only safe response**に限定する。
8. `REJECTED` / `SYSTEM_FAILURE`はnormal grounded rendererへ渡さない。
9. normal deterministic rendererは**terminal `ACCEPTED`へbind**する。
10. `INSUFFICIENT_CONTEXT`はnormal rendererとは別の**context-limit-only safe render path**に限定する。
11. rendererはvalidation resultだけでなく、terminal decisionとその対象output identityを確認しなければrenderしてはならない。
12. Comparisonは両Object/Work由来のgrounded source coverageなしにmaterially sufficientとしない。
13. Creativeは両source Concept由来のgrounded source factと、少なくとも1つのvalid `creative_addition`がなければmaterially sufficientとしない。
14. Roleplayはcoreでは「grounded source materialが存在する」ことをgeneric requirementとし、N-04 formal Case 1の「最低2 concrete context facts」等はharness requirement profileへ置く。
15. interpretationやcreative additionの存在だけでsource coverageを満たしたことにはしない。source coverageはvalidated source-fact provenanceから算出する。
16. Material Requirement Gateのfailureはgrounding falsehoodと区別し、独立したfailure/evidenceとして保存する。
17. G-06のbounded single retry原則は維持するが、**Grounding PASS後のmaterial insufficiencyを無条件retry対象にしない。** requirement failure原因がgenerator-repairableかcontext-insufficientかを区別する。
18. G-18ではG-06/G-07との統合関係を明示し、最終contract version / terminal decision shapeをfreezeする。

Target flow:

```text
Generated structured output
        ↓
V0-V5 Grounding Validation
        ↓
Grounding PASS
        ↓
Material Requirement Gate
   ├─ PASS
   │    ↓
   │ Terminal ACCEPTED
   │    ↓
   │ Normal deterministic renderer
   │
   ├─ FAIL: generator can repair requirement
   │    ↓
   │ bounded retry policy (if attempt 1 and retryable)
   │
   ├─ FAIL: context genuinely insufficient
   │    ↓
   │ only validated context-limit-only output may become
   │ INSUFFICIENT_CONTEXT
   │    ↓
   │ safe context-limit renderer
   │
   └─ system/integrity failure
        ↓
      SYSTEM_FAILURE
```

本Decisionはproduction codeを変更しない。実装はN-04G-19で行う。

---

## 2. Problem statement

G-13 desk reviewで、current `GroundingFailureController._infer_material_sufficiency()`は次のroleが1件でもあればmaterially sufficientと推定することを確認した。

```text
source_fact
interpretation
creative_addition
```

これはuse-case completionとして弱すぎる。

またcurrent rendererは`validation.verdict == PASS`だけをnormal renderの主要条件としており、terminal decisionを受け取らない。

そのため、orchestrator misuseがあれば`Grounding PASS`だがterminal policy上ACCEPTすべきでないoutputを表示できる。

G-12 Case 1ではMachine terminal `ACCEPTED`後にunsupported materialがrenderされた。G-14/G-16がgrounding false acceptanceを止める一方、G-17ではさらに**「groundedだが要求未達」もACCEPTEDしない**境界を物理化する。

---

## 3. Four-layer responsibility model

### Layer 1 — Grounding Validation

各material propositionが許可されたgrounding policy上supportされているかを判定する。completeness判定ではない。

### Layer 2 — Material Requirement Gate

grounded outputがpurpose/runで要求される最低限のmaterial構成を満たしているかを判定する。

結果:

```text
PASS
FAIL_REPAIRABLE
FAIL_CONTEXT_INSUFFICIENT
INDETERMINATE
```

### Layer 3 — Terminal Decision

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

retryはterminalではなくactionとする。

### Layer 4 — Render Permission

```text
ACCEPTED             -> normal grounded render
INSUFFICIENT_CONTEXT -> context-limit-only safe render
REJECTED             -> no grounded render
SYSTEM_FAILURE       -> no grounded render
```

---

## 4. Material Requirement Gate contract

概念component名:

```text
MaterialRequirementGate
```

概念contract version候補:

```text
sgokb.material-requirement.v1
```

最終名称/versionはG-18でfreezeする。

### Inputs

```text
purpose
validated output
validation unit results
Grounded Context metadata
requirement profile
```

必要に応じてK ref -> source object mapping、premise unit coverage等を使用する。

### Authority boundary

原則としてWeb、external Knowledge、generator memory、free-form LLM quality judge、raw unvalidated output textをauthorityにしない。

### Output

概念形:

```json
{
  "requirement_contract_version": "sgokb.material-requirement.v1",
  "verdict": "PASS",
  "purpose": "comparison",
  "profile_id": "n04-v3-case-2",
  "checks": [],
  "failures": []
}
```

---

## 5. Generic requirements vs benchmark requirements

### Generic core requirement

#### roleplay
- normal ACCEPTED responseには少なくとも1つのvalidated `source_fact` materialが存在する。
- context-limit-only responseはnormal ACCEPTEDではない。

#### comparison
- comparison対象として要求されたsource object全てからvalidated source fact coverageが存在する。
- comparison/contrast conclusionを要求するprofileでは、validated interpretationが存在する。

#### creative
- 要求されたsource Concept全てからvalidated source fact coverageが存在する。
- 少なくとも1つのvalidated `creative_addition`が存在する。

### Benchmark-specific requirement

N-04 formal harnessが注入する。

Case 1 Roleplay:

```text
minimum_grounded_source_facts = 2
required_source_objects = [Saber]
```

Case 2 Comparison:

```text
required_source_objects = [Work A, Work B]
minimum_source_fact_per_object = 1
minimum_interpretation_units = 1
```

Case 3 Creative:

```text
required_source_objects = [Tsundere, Hero's Journey]
minimum_source_fact_per_object = 1
minimum_creative_addition_units = 1
```

coreへCase固有thresholdをhardcodeせず、`core defines capability / harness profile defines threshold`とする。

---

## 6. Source coverage accounting

source coverageはvalidated `source_fact` unitの`support_refs`からdeterministically算出する。

```text
validated source_fact
 -> K refs
 -> Grounded Context grounding unit
 -> canonical/source object identity
```

interpretation textやcreative_addition textからsource coverageを推測しない。

G-16の`premise_unit_ids`を使い、comparison interpretationがどのsource object premiseに依存するかも追跡可能にする。

---

## 7. Roleplay material sufficiency

Generic production invariant:

```text
normal ACCEPTED roleplay -> supported source_fact >= 1
```

N-04 Case 1 profile:

```text
minimum_supported_source_fact_units >= 2
required source Object = Saber
```

personality coverageが不足していても、それ自体はGrounding FAILではない。available grounded factsでrequirementを満たすか、満たせなければ安全なcontext-limit responseへ収束する。

---

## 8. Comparison material sufficiency

Generic requirement:

```text
all required comparison objects covered by supported source_fact
```

N-04 formal profile:

```text
Work A supported source fact >= 1
Work B supported source fact >= 1
comparison/contrast interpretation >= 1
```

comparison claimが2 objectを比較するなら、その`premise_unit_ids`に両object由来supported source_factが含まれることをdeterministically検査できる。

---

## 9. Creative material sufficiency

Generic requirement:

```text
all required source Concepts covered by supported source_fact
AND
creative_addition exists
```

N-04 formal profile:

```text
Tsundere source coverage >= 1
Hero's Journey source coverage >= 1
creative_addition >= 1
```

大量のcreative materialがあってもsource Concept groundingが片側しかなければmaterially sufficientではない。逆に両Concept factだけで新しいcreative additionがなければcreative use case completionではない。

---

## 10. Material Requirement verdict semantics

### PASS
required material structureを満たす。

### FAIL_REPAIRABLE
GroundingはPASSだがgenerator outputがrequirementを満たさず、同じContextで再生成すれば修正可能性がある。

### FAIL_CONTEXT_INSUFFICIENT
requirementを満たすために必要なmaterialがsupplied Contextに存在しないとdeterministically確認できる。

これだけで`INSUFFICIENT_CONTEXT`へ直接変換しない。safe context-limit outputが必要。

### INDETERMINATE
requirement判定自体を安全に確定できない。fail-closed。

---

## 11. Relationship with bounded retry

G-06のmax retry=1を維持する。

- Grounding failureは従来通りfailure classificationに応じretry可能。
- Material `FAIL_REPAIRABLE`かつattempt 1の場合のみretry候補。
- retry feedbackにはmissing requirement ID、covered/missing source objects、minimum counts等の構造化情報を含めてよい。
- new Knowledgeや模範回答は渡さない。

Context側に必要materialがない場合、同一回答の反復では解決しない。ただしAttempt 1がnormal outputを返した場合、1回のretryをcontext-limit-only responseへ収束させるrepair opportunityとして使う余地を残す。最終policyはG-18でG-06と統合freezeする。

---

## 12. `INSUFFICIENT_CONTEXT` redesign

v3 baselineでは最も単純に:

```text
INSUFFICIENT_CONTEXT response = context_limit-only output
```

を採用する方向とする。

Terminal eligibility:

1. output contract valid。
2. Grounding PASS。
3. normal material requirementは満たせない。
4. outputがcontext_limit-only safe shape。
5. context_limit unitがG-14 role-boundary PASS。
6. source_fact / interpretation / creative_additionをnormal answerとして同時renderしない。

partial answer + insufficiency noticeはbaselineでは採用しない。

---

## 13. Terminal decision matrix

### ACCEPTED

```text
Grounding = PASS
Material = PASS
no system failure
```

結果: `render_mode = NORMAL`

### INSUFFICIENT_CONTEXT

```text
Grounding = PASS
Material != PASS
context insufficiency established
output = context_limit-only safe shape
no system failure
```

結果: `render_mode = CONTEXT_LIMIT_ONLY`

### REJECTED

例:
- grounding failure after retry
- material FAIL_REPAIRABLE after retry
- unsafe/mixed output when context insufficient

結果: `render_mode = NONE`

### SYSTEM_FAILURE

例:
- required verifier unavailable
- canonical mapping integrity failure
- material Gate cannot resolve source identity due system defect
- terminal/render contract mismatch

結果: `render_mode = NONE`

---

## 14. Renderer binding

current renderer signature `render(output, validation)`はterminal decisionを知らないため不十分とする。

概念上は:

```text
render(output, validation, material_result, terminal_decision)
```

またはterminal-approved render ticketを使う。

normal rendererは最低限:

```text
terminal_decision.action == ACCEPTED
validation.verdict == PASS
material_result.verdict == PASS
terminal_decision binds same output/context/run
```

を確認する。

output identity bindingとして少なくとも:

```text
context_fingerprint
output contract version
run/attempt identity
validated output identity or digest
```

を保持する方向を採用する。

---

## 15. Render modes

```text
NORMAL
CONTEXT_LIMIT_ONLY
NONE
```

- NORMAL: `ACCEPTED`専用。
- CONTEXT_LIMIT_ONLY: `INSUFFICIENT_CONTEXT`専用。context_limit unit以外が存在すれば拒否。
- NONE: `REJECTED / SYSTEM_FAILURE`。

UI status messageが必要ならtrusted system messageを別系統で生成し、rejected raw LLM textをgrounded responseとして流用しない。

---

## 16. Failure taxonomy additions

G-18統合時に最低限次を検討する。

```text
MATERIAL_REQUIREMENT_MISSING
SOURCE_COVERAGE_MISSING
COMPARISON_COVERAGE_INCOMPLETE
CREATIVE_SOURCE_COVERAGE_INCOMPLETE
CREATIVE_ADDITION_MISSING
CONTEXT_LIMIT_SHAPE_VIOLATION
RENDER_AUTHORIZATION_DENIED
OUTPUT_DECISION_BINDING_MISMATCH
```

これらは`UNSUPPORTED_CLAIM`等のgrounding failureと分離する。

---

## 17. Evidence / audit requirements

最低限保存可能にする。

```text
grounding validation result
material requirement profile ID/version
material requirement checks
covered source object IDs
missing source object IDs
terminal decision
render mode
output/context/run binding identity
retry decision and cause
```

formal harnessではprofile自体をfreezeし、run後にthresholdを変更しない。

---

## 18. G-12 desk replay under G-17

### Case 1
G-14/G-16でunsupported unitsはGrounding PASSへ到達しないため、no ACCEPTED / no NORMAL renderとなる。さらにgrounded factが1件だけでもCase 1 formal profileの最低2 factsを満たさずACCEPTEDにならない。

### Case 2
両Workからsource factが必要。一方だけのcoverageではMaterial FAILとなりACCEPTED不可。両Work factがあってもrequired comparison interpretationがなければprofile未達。

### Case 3
Tsundere fact + creative additionだけでHero's Journey factがなければcoverage incomplete。両Concept factだけでcreative_additionがなければcreative completion未達。

---

## 19. Interaction with G-14/G-15/G-16

- G-14: Atomicity / role boundaryがcontent validityを守る。G-17は再semantic判定しない。
- G-15: validated unit.text + trusted fixed tokensのrenderer invariantを維持し、G-17がterminal authorizationを追加する。
- G-16: source coverageは`supported` source_factだけを数え、interpretation coverageはvalidated premise graphから導出する。

---

## 20. Changes required at G-19 implementation

最低候補:

```text
src/sgokb/grounding/material_gate.py        # new candidate
src/sgokb/grounding/failure.py              # terminal composition
src/sgokb/grounding/render.py               # terminal binding / render modes
src/sgokb/application_grounding.py           # facade wiring
src/sgokb/grounding/evidence.py              # requirement/terminal evidence as needed
```

G-17ではproduction codeを変更しない。

---

## 21. Required adversarial tests for G-20

1. Grounding PASS + only one comparison object -> no ACCEPTED.
2. Grounding PASS + both comparison objects + no required comparison interpretation -> no ACCEPTED when profile requires it.
3. Grounding PASS + one creative Concept only + creative addition -> no ACCEPTED.
4. Grounding PASS + both Concepts + no creative addition -> no ACCEPTED.
5. Roleplay Grounding PASS with 1 source fact + formal minimum=2 -> no ACCEPTED.
6. Material requirement FAIL does not become ACCEPTED through fallback inference.
7. REJECTED -> renderer refuses.
8. SYSTEM_FAILURE -> renderer refuses.
9. INSUFFICIENT_CONTEXT + source_fact mixed output -> safe renderer refuses.
10. INSUFFICIENT_CONTEXT + validated context_limit-only output -> safe renderer succeeds.
11. Terminal decision for attempt 1 cannot authorize attempt 2 output.
12. Output digest/context fingerprint mismatch -> render authorization denied.

---

## 22. Completion assessment

- [x] `Grounding PASS`と`use-case completion`を独立Gateへ分離した。
- [x] Material Requirement Gateのinput/output/責務を定義した。
- [x] generic purpose invariantとbenchmark-specific requirement profileを分離した。
- [x] comparisonの両Object source coverageをmachine-check可能な形で定義した。
- [x] creativeの両Concept source coverage + creative addition要件を定義した。
- [x] roleplayのformal minimum fact countをprofile injectionにした。
- [x] `ACCEPTED`条件をGrounding PASS + Material PASSへ強化した。
- [x] `INSUFFICIENT_CONTEXT`をcontext-limit-only safe pathへ限定した。
- [x] `REJECTED / SYSTEM_FAILURE`をnormal rendererへ渡さない設計を確定した。
- [x] rendererをterminal decision / output identityへbindするinvariantを定義した。
- [x] G-12 3 Caseを机上再評価した。
- [x] production codeは未変更。

**N-04G-17 = Complete (design).**

次Task:

```text
N-04G-18 [P0] — Post-G12 Design Freeze
```
