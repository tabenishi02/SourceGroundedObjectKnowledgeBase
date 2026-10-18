# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-19

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Formal run: `20261018T213810+0900`
- Branch of record: `main`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Root-cause / desk review / research: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- G-14 decision: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- G-15 decision: `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
- G-16 decision: `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- G-17 decision: `docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md`
- Current parent state: **N-04 Failed / N-05 blocked**

---

## 1. Purpose

G-12で確認されたfailureを、単なるmodel retryやrubric緩和で回避せず、grounded-generation contract / validation / terminal gateを再点検して修正する。

今回のformal runでは次が正常だった。

- MCP public read boundary
- current Version resolution
- Context Builder / Grounded Context projection
- Similarity retrieval
- canonical read-only safety
- integrity
- focused/full regression

したがって本remediationでは、具体的failure evidenceがない限りRetrieval / MCP / canonical schemaを変更しない。

重点対象は次である。

```text
generation output contract
atomicity
semantic-role boundary
support / premise validation
semantic verifier
retry feedback
material sufficiency
terminal outcome
renderer
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

- K5でsupportされる内容とsupportされないHoly Grail War claimが同一unitに混在した。
- semantic validatorがunit全体を`entailed`と誤判定した。
- material relationship claimが`stylistic_expression`として`role_valid`を通過した。
- unsupported contentがrendered responseへ到達した。

これは最優先のfalse-acceptanceである。

### Case 2 — Comparison

```text
Machine terminal: REJECTED
Formal verdict: FAIL
Retry: 1
```

- Attempt 1でunsupported claim。
- Attempt 2でsupport refs欠落。
- interpretationのmaterial premiseがKに存在しないにもかかわらず、別unitで`derived_supported`相当の誤判定が観測された。

fail-closed terminalは機能したが、semantic validation / premise semanticsは不十分である。

### Case 3 — Creative

```text
Machine terminal: REJECTED
Formal verdict: FAIL
Retry: 1
```

- `creative` blockの`label=null`が2 attempt連続。
- providerへ渡すJSON Schemaでは`label=null`が許可される一方、Python parserはcreative / interpretationでnon-empty labelを追加要求していた。
- retry feedbackは`missing_presentation_label`を返したが、schema自体は同じnull許容のままだった。

これはgenerator qualityだけでなくcontract表現の不一致である。

---

## 3. Remediation principles

1. **G-12 failed evidenceを削除・上書きしない。**
2. **N-04をCompleteへ変更しない。**
3. **N-05をblockedのまま維持する。**
4. **v1 / v2 failed acceptance specを履歴として保持する。**
5. **同じ条件での単純再試行をしない。**
6. **rubricを緩和してPASSさせない。**
7. **untrusted generatorというG-01原則を維持する。**
8. **semantic verifierもuntrusted / fallible componentとして扱う。**
9. **構造で防げるfailureをLLM judgeへ委ねない。**
10. **最終renderへ到達する文字列は全てvalidatorまたはdeterministic rendererの管理下に置く。**
11. **claim-level / premise-level fail-closedを優先する。**
12. **外部libraryは設計参考またはbenchmark candidateとして評価し、即production dependency化しない。**

---

## 4. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-13 | P0 | **Complete (2026-10-18)** | G-12 root-cause、横断desk review、外部repo/library調査、remediation scope定義 |
| N-04G-14 | P0 | **Complete (2026-10-19)** | Atomic claim / semantic-role boundaryを再設計する |
| N-04G-15 | P0 | **Complete (2026-10-19)** | Output schema / presentation / deterministic rendering contractをhardeningする |
| N-04G-16 | P0 | **Complete (2026-10-19, design)** | Source-fact / interpretation semantic validation architectureを再設計する |
| N-04G-17 | P0 | **Complete (2026-10-19, design)** | Material sufficiency / use-case completion / terminal-render gateを再設計する |
| N-04G-18 | P0 | Pending | G-14〜G-17を統合してPost-G12 Design Freezeを行う |
| N-04G-19 | P0 | Pending | Frozen remediation designを実装し、candidate verifierを統合する |
| N-04G-20 | P0 | Pending | Adversarial / replay / verifier benchmark / regression testを実施する |
| N-04G-21 | P0 | Pending | v3 acceptance spec / Reference Workstation harnessをfreezeする |
| N-04G-22 | P0 | Pending | Reference Workstationでformal v3 re-acceptanceを実施する |

N-04 CompleteはN-04G-22で全Gate PASS後のみ可能とする。

---

## 5. N-04G-13 [P0] — Root-cause / Desk Review / External Research

**Status: Complete (2026-10-18)**

正本:

```text
docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
```

実施内容:

- G-12 3 failureを再分類。
- `context.py / request.py / output.py / validation.py / failure.py / render.py / evidence.py / application_grounding.py`を横断レビュー。
- `tests/test_n04_grounded_generation.py`をadversarial coverage観点でレビュー。
- G-04 / G-05 Decisionと実装の差分を確認。
- LM Studio Structured Output、JSON Schema / python-jsonschema、FActScore、Ragas、RAGChecker、MiniCheck、AlignScore、DeepEvalを調査。
- 問題をP0/P1へ分類し、G-14〜G-22へ割当。

---

## 6. N-04G-14 [P0] — Atomic claim / semantic-role boundary redesign

**Status: Complete (2026-10-19)**

正本:

```text
docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
```

### Decisions

- `1 validation unit = 1 atomic semantic proposition`を必須invariantとした。
- Atomicity Gateの結果を`ATOMIC / NON_ATOMIC / INDETERMINATE`とし、`ATOMIC`だけがsupport / derivation validationへ進める。
- mixed-role contentを同一unitへ混在させない。
- content materiality / role boundary判定をmodel-declared `semantic_role`より優先する。
- role mismatchをsilent reclassificationして救済しない。
- post-hoc atomizerを唯一のgrounding authorityにしない。
- v3 formal baselineではmodel-authored `stylistic_expression`を禁止する。
- `context_limit`をsupplied Contextの可用性に関するmeta / epistemic propositionへ限定する。
- `creative_addition`へsource Object / Concept factを混在させない。
- `interpretation`はconclusion-onlyとし、source factual premiseを同一textへ埋め込まない。
- Atomicity / role-boundary failureを後段semantic verifierのpositive verdictでoverrideできない。

### Completion condition

- [x] atomicityのmachine-checkable invariantを定義。
- [x] material propositionのrole逃避対策を定義。
- [x] G-05 `all material propositions supported`を物理実装可能なGate順序へ具体化。
- [x] Case 1保存evidenceで新設計ならFAIL-CLOSEDになることを机上確認。
- [x] production codeは未変更。

---

## 7. N-04G-15 [P0] — Output schema / presentation / renderer hardening

**Status: Complete (2026-10-19)**

正本:

```text
docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
```

### Decisions

- model-generated free-form `label`をv3 normative output contractから削除する。
- heading / separatorは`presentation_role`からtrusted deterministic rendererが生成する。
- visible LLM-authored semantic textをvalidated `unit.text`だけに限定する。
- block role / unit semantic role matrixを定義する。
- G-14に従い`stylistic_expression`をv3 model output enumから除外する。
- role-specific block schemaをv3 baselineの第一候補とする。
- provider schemaとapplication parserを同一canonical logical schemaから導出する。
- schema errorで`json_path / block_id / unit_id / failure_detail / expected_rule`を保持可能にする。
- G-12 Case 3 `label=null`とfree-form label injectionを新contractで構造的に除去する。
- breaking changeのため`sgokb.grounded-generation-output.v2`へのrevisionを予約し、最終version/shapeはG-18でfreezeする。

### Required invariant

```text
rendered semantic content
  = successfully validated unit.text
  + SGOKB-controlled fixed presentation tokens only
```

### Completion condition

- [x] Case 3 `label=null` failureをcontract-levelで除去する設計を確定。
- [x] arbitrary model label textがrendered factual content bypassにならない設計を確定。
- [x] schema / parser / rendererのstructural ruleを単一正本から導出する原則を確定。
- [x] production codeは未変更。

---

## 8. N-04G-16 [P0] — Semantic validation architecture redesign

**Status: Complete (2026-10-19, design)**

正本:

```text
docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md
```

### Decisions — Source fact

```text
V3 deterministic support
  ↓ unresolved only
V4F specialized source-fact verifier
  ↓ supported candidate only
independent bounded LLM judge
  ↓
composition / disagreement policy
```

- MiniCheck familyをprimary source-fact verifier benchmark candidateとした。
- AlignScoreをsecondary benchmark candidateとした。
- V3 deterministic-supportedはsemantic verifier不要。
- V3 unresolvedはspecialized fact verifierへ渡す。
- v3 formal baselineではspecialized positive + independent bounded LLM `ENTAILED`のagreementをsemantic support条件とする方向を採用する。
- specialized negativeをgeneral LLMのpositive verdictで救済しない。
- verifier disagreement / ambiguity / unavailableをPASSへ倒さない。
- scoreを校正済みtruth probabilityとして扱わず、SGOKB benchmarkでthresholdをfreezeする。

### Decisions — Interpretation

```text
validated source_fact units
  ↓
premise_unit_ids integrity gate
  ↓
bounded derivation judge
```

- interpretationはdirect K `support_refs`方式を廃止する。
- `premise_unit_ids[]`で既に`supported`のsource_fact unitを参照する。
- premiseはv3 baselineではsource_factのみ。interpretation chainingは許可しない。
- unsupported / contradictory / indeterminate premiseがあればderivation judgeへ進めない。
- derivation judgeはatomic conclusionがvalidated premisesだけから合理的に導けるかだけを判定する。
- hidden external premiseを必要とするconclusionは`derived_supported`にしない。

### Offline benchmark gate

特定MiniCheck/AlignScore checkpoint・thresholdはG-16時点ではproduction採用していない。G-19/G-20でcandidateを統合し、G-12 replay/adversarial setを使ってoffline benchmarkを実施する。

- required negative/replay caseを1件でもsupport扱いするprofileをformal baselineへ採用しない。
- false-positive最小化を優先する。
- verifier model/revision/cache/threshold profileをG-21前にfreezeする。

### Completion condition

- [x] source fact / interpretation validation architectureを分離。
- [x] MiniCheck familyをprimary candidate、AlignScoreをsecondary candidateとして選定。
- [x] G-12 Case 1 U2/U3をsemantic verifier accuracyに依存せずfalse acceptしないGate順序を維持。
- [x] G-12 Case 2 unsupported interpretationを`derived_supported`へ昇格しないpremise architectureを定義。
- [x] verifier disagreementをPASSへ倒さない。
- [x] local-only / frozen verifier policyを維持可能。
- [x] final verifier adoption前のoffline benchmarkを必須Gate化。
- [x] production codeは未変更。

---

## 9. N-04G-17 [P0] — Material sufficiency / terminal / render gate redesign

**Status: Complete (2026-10-19, design)**

正本:

```text
docs/decisions/N04G17_MATERIAL_SUFFICIENCY_TERMINAL_RENDER_GATE_REDESIGN.md
```

### Goal

`Grounding PASS`と`use-case completion`を分離し、Machine `ACCEPTED`およびrenderer permissionをfail-closedにする。

### Decisions

```text
Grounding Validation PASS
        ↓
Material Requirement Gate PASS
        ↓
Terminal ACCEPTED
        ↓
NORMAL Renderer
```

- `MaterialRequirementGate`を独立componentとして導入する設計を確定。
- `Grounding PASS`だけでは`ACCEPTED`にしない。
- purpose-level generic requirementとN-04 benchmark-specific requirement profileを分離する。
- source coverageはvalidated `source_fact`のK ref / source-object mappingからdeterministically算出する。
- Comparisonはrequired両Object/Workのsource coverageを要求する。
- Creativeはrequired両Conceptのsource coverage + `creative_addition`存在を要求する。
- Roleplayのgeneric coreはsupported source material存在、formal Case 1の最低2 facts等はharness profileから注入する。
- Material verdictを`PASS / FAIL_REPAIRABLE / FAIL_CONTEXT_INSUFFICIENT / INDETERMINATE`へ分離する方向を採用。
- `INSUFFICIENT_CONTEXT`はvalidated `context_limit`-only safe responseへ限定する。
- partial normal answer + insufficiency noticeはv3 baselineでは不採用。
- rendererをterminal decision / output identityへbindする。
- `REJECTED / SYSTEM_FAILURE`はnormal render不可。
- render modeを`NORMAL / CONTEXT_LIMIT_ONLY / NONE`へ分離する。
- output/context/run/attempt binding identityをterminal/render authorizationに保持する方向を採用。

### G-12 replay consequence

```text
Case 1 grounding false acceptance
-> G-14/G-16でGrounding PASS不可
-> Material Gateへ進まない
-> no ACCEPTED / no NORMAL render
```

```text
Case 2 one-side-only grounded comparison
-> source coverage incomplete
-> Material FAIL
-> no ACCEPTED
```

```text
Case 3 one-Concept-only grounding or no creative addition
-> Material FAIL
-> no ACCEPTED
```

### Completion condition

- [x] ACCEPTED条件をG-06の意味と整合する形でGrounding PASS + Material PASSへ強化。
- [x] materially insufficient outputをACCEPTEDにしない。
- [x] generic purpose invariantとbenchmark-specific profileを分離。
- [x] comparison / creative source coverageをmachine-check可能にした。
- [x] REJECTED / SYSTEM_FAILUREをrender不能とした。
- [x] INSUFFICIENT_CONTEXTをcontext-limit-only safe render pathへ限定。
- [x] terminal/output identity renderer bindingを定義。
- [x] production codeは未変更。

---

## 10. N-04G-18 [P0] — Post-G12 Design Freeze

G-14〜G-17を統合し、必要範囲でG-02/G-04/G-05/G-06/G-07の変更関係を明示する。

Silent design driftは禁止する。

Freeze対象:

- atomic claim contract
- role boundary
- structured output contract version
- deterministic presentation
- source-fact verifier policy
- interpretation premise policy
- validator disagreement policy
- material requirement gate
- terminal/render relationship
- retry feedback structure
- context-limit-only safe terminal path
- output/terminal/render identity binding

---

## 11. N-04G-19 [P0] — Implementation

最低対象:

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

G-16 source-fact verifier candidate integrationでは、特定checkpointをfinal adoptionしたとみなさず、G-20 benchmark可能なadapter boundaryを実装する。

canonical DB / MCP ownershipは変更しない。

---

## 12. N-04G-20 [P0] — Adversarial / Replay / Verifier Benchmark / Regression

G-12 evidenceをgold regression fixtureへ変換可能な最小synthetic testcaseとして再現する。

必須test:

1. supported clause + unsupported clause in one unit -> no PASS
2. material fact disguised as stylistic_expression -> no PASS
3. context_limit with appended external fact -> no PASS
4. creative block containing source Concept claim -> role/scope failure
5. interpretation with unsupported premise -> no derived_supported
6. interpretation referencing only one side of a two-object comparison -> no comparison PASS
7. arbitrary model label cannot appear as unvalidated rendered content
8. null/missing presentation metadata cannot cause repeated useless retry under the new contract
9. schema error feedback contains path/detail sufficient for repair
10. materially incomplete but grounded response -> not ACCEPTED
11. validation PASS but terminal REJECTED/SYSTEM_FAILURE -> renderer refuses
12. source fact verifier disagreement -> INDETERMINATE/FAIL-CLOSED
13. INSUFFICIENT_CONTEXT + mixed normal material -> safe renderer refuses
14. attempt/output binding mismatch -> render authorization denied
15. G-12 Case 1/2/3 failure shapes all regress correctly
16. existing G-10 tests remain PASS or are deliberately migrated with documented reason

Verifier benchmark must additionally include:

- supported direct claim
- supported paraphrase
- unsupported material extra detail
- G-12 unsupported atomic claims
- high-overlap unsupported relation/event
- contradiction / negation flip
- threshold indeterminate-band cases

Candidate/profile acceptance:

```text
required negative/replay false-positive = 0
```

をformal baseline採用の必要条件とする。

Full pytest / Ruff / diff check required。

---

## 13. N-04G-21 [P0] — v3 Acceptance / Harness Freeze

v2 Failed historyを保持し、新しいcontract / verifierを使うv3 acceptance specを作る。

Formal run前にfreeze:

- generator
- source-fact verifier + checkpoint/revision
- source-fact verifier threshold profile
- independent source-fact LLM judge
- interpretation derivation judge
- material requirement profiles
- terminal/render policy
- runtime/settings
- structured-output mechanism
- retry policy
- evidence tree
- adversarial/verifier benchmark preflight
- formal rubric

G-20 verifier empirical Gate未達のprofileをfreezeしない。

G-12のFAILを「なかったこと」にしない。

---

## 14. N-04G-22 [P0] — Formal v3 Re-Acceptance

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
G-18 Post-G12 Design Freeze
  ↓
G-19 Implementation + verifier candidate integration
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

これらに新しいfailure evidenceが出た場合のみ別Taskとして扱う。