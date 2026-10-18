# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed remediation task: **N-04G-17 [P0] Material sufficiency / terminal / render gate redesign**
- Next task: **N-04G-18 [P0] Post-G12 Design Freeze**

---

## 1. このhandoffの目的

別チャットでN-04 post-G12 remediationを継続するための開始点を固定する。

GitHubは`main`を正本とする。過去のPhase N stacked branchは再利用しない。

---

## 2. Formal v2 result

Formal run:

```text
run_id: 20261018T213810+0900
Reference Workstation: Windows 11 / Python 3.10.6 / RTX 4090 24GB
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
```

結果:

| Case | Machine terminal | Formal verdict | Retry |
|---|---|---|---|
| Saber Roleplay | ACCEPTED | FAIL | 0 |
| Similar Work Comparison | REJECTED | FAIL | 1 |
| Concept Combination Creative | REJECTED | FAIL | 1 |

Overall:

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

## 3. G-12 / G-13で確定した主要failure

### Case 1

- supported clause + unsupported Holy Grail War claimが同一unitに混在。
- semantic validatorがunit全体を`entailed`と誤判定。
- material relationship claimが`stylistic_expression`として`role_valid`を通過。
- unsupported contentがMachine `ACCEPTED`後にrenderされた。

### Case 2

- unsupported source claim。
- retryではsupport refs欠落。
- unsupported / hidden interpretation premiseが`derived_supported`相当へ進み得た。

### Case 3

- creative / interpretation blockの`label=null`。
- provider JSON Schemaでは合法、Python parserでは違法というcontract mismatch。

### Additional gaps

- atomicityがinstruction-only。
- support-free role escape。
- one general LLM judgeへsource fact / interpretation責務を圧縮。
- material sufficiency fallbackが弱い。
- rendererがterminal decisionへbindされていない。
- multi-object use-case coverageがmachine Gate化されていない。

---

## 4. G-14 — Atomic claim / semantic-role boundary

正本:

```text
docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
```

主要Decision:

- `1 validation unit = 1 atomic semantic proposition`。
- `ATOMIC / NON_ATOMIC / INDETERMINATE` Gate。
- `ATOMIC`だけsupport / derivation validationへ進める。
- content materialityをmodel-declared semantic roleより優先。
- mixed-role unit禁止。
- silent reclassification禁止。
- post-hoc atomizerをgrounding sole authorityにしない。
- v3 model-authored `stylistic_expression`禁止。
- `context_limit` / `creative_addition`境界を狭くする。
- interpretationはconclusion-only。

---

## 5. G-15 — Output schema / presentation / renderer hardening

正本:

```text
docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
```

主要Decision:

- model-generated free-form `label`削除。
- headingはtrusted rendererが`presentation_role`から生成。
- visible LLM semantic textはvalidated `unit.text`のみ。
- role-specific block schemaを第一候補。
- provider schemaとapplication parserを同一canonical logical schemaから導出。
- v3 output contractはbreaking revisionとして`sgokb.grounded-generation-output.v2`候補。
- final version/shapeはG-18でfreeze。

---

## 6. G-16 — Semantic validation architecture

正本:

```text
docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md
```

Source fact path:

```text
V3 deterministic support
  ↓ unresolved
specialized source-fact verifier
  ↓ supported candidate
independent bounded LLM judge
  ↓
composition / disagreement policy
```

- MiniCheck familyをprimary benchmark candidate。
- AlignScoreをsecondary candidate。
- specialized negativeをgeneral LLMで救済しない。
- disagreement / ambiguity / unavailableはPASS不可。
- final checkpoint / thresholdはまだproduction採用していない。
- G-19/G-20 offline benchmarkを必須Gateとする。

Interpretation path:

```text
validated source_fact units
  ↓
premise_unit_ids integrity gate
  ↓
bounded derivation judge
```

- direct K `support_refs`をinterpretation grounding proofとして使わない。
- premiseはsupported source_factのみ。
- interpretation chainingはv3 baselineでは禁止。
- hidden external premiseは`derived_supported`不可。

---

## 7. G-17 — Material sufficiency / terminal / render gate

正本:

```text
docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md
```

主要Decision:

```text
Grounding PASS
   ↓
Material Requirement Gate PASS
   ↓
Terminal ACCEPTED
   ↓
NORMAL deterministic renderer
```

### Material Requirement Gate

- Grounding correctnessとuse-case completionを分離。
- validated metadata / source coverage / requirement profileからdeterministic-firstに判定。
- generic production requirementとN-04 benchmark-specific thresholdを分離。

### Roleplay

- core: supported source materialが必要。
- N-04 Case 1:最低2 grounded source facts等をharness profileから注入。

### Comparison

- required両Object/Workからsupported source fact coverageが必要。
- required comparison interpretationがあるprofileではinterpretationも必要。
- interpretation premise coverageはG-16 `premise_unit_ids`から追跡。

### Creative

- required両Conceptからsupported source fact coverageが必要。
- `creative_addition`が最低1件必要。

### Terminal / render

```text
ACCEPTED             -> NORMAL render
INSUFFICIENT_CONTEXT -> CONTEXT_LIMIT_ONLY safe render
REJECTED             -> no grounded render
SYSTEM_FAILURE       -> no grounded render
```

- `Grounding PASS`だけではACCEPTED不可。
- `INSUFFICIENT_CONTEXT`はv3 baselineでvalidated `context_limit`-only outputに限定。
- partial normal answer + insufficiency noticeは不採用。
- rendererはterminal decision / same output / context / run / attempt identityへbindする。
- current `render(output, validation)`だけでは不十分。

G-17ではproduction codeを変更していない。

---

## 8. Current remediation chain

```text
N-04G-13  Root-cause / desk review / research         Complete
N-04G-14  Atomic claim / semantic-role redesign       Complete
N-04G-15  Output / presentation contract hardening    Complete
N-04G-16  Semantic validation architecture            Complete (design)
N-04G-17  Material / terminal / render gate            Complete (design)
N-04G-18  Post-G12 Design Freeze                       Pending
N-04G-19  Implementation + verifier candidate          Pending
N-04G-20  Adversarial / verifier benchmark/regression  Pending
N-04G-21  v3 acceptance / harness freeze               Pending
N-04G-22  Formal v3 re-acceptance                      Pending
```

N-04 CompleteはG-22で3/3 Case PASS + safety/regression Gate全PASS後のみ。

---

## 9. Next task — N-04G-18

```text
N-04G-18 [P0]
Post-G12 Design Freeze
```

目的:

G-14〜G-17の個別Decisionを1つの実装可能なend-to-end contractへ統合し、旧G-02/G-04/G-05/G-06/G-07とのreopen / override / preserve関係を明示する。

最低freeze対象:

- atomicity contract
- semantic-role boundary
- final structured output contract version / shape
- role-specific block schema
- interpretation `premise_unit_ids`
- source-fact verifier composition
- verifier disagreement policy
- material requirement contract/profile
- bounded retryとの統合
- terminal outcome mapping
- context-limit-only safe path
- renderer authorization / render mode
- output/context/run/attempt identity binding
- failure taxonomy / retry feedback fields
- G-19 implementation scope

G-18も設計Taskであり、freeze完了まではproduction codeを変更しない。

---

## 10. Read first in next chat

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md`
4. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
5. `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
6. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
7. `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`
8. `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
9. `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
10. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`

---

## 11. Protected boundaries

具体的failure evidenceがない限り次を変更しない。

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

rubricを緩和してPASSさせない。