# N-04G-22 Formal v3 Failure Root-Cause Investigation

更新日: 2026-10-20

- Status: **Complete (desk review / external research)**
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Formal result: `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md`
- Frozen design: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Current main at investigation start: `b04da99e6538eb34d04e0dbe8c69bb8c90eaea98`
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Executive conclusion

G-22の`0 / 3`は、retrieval / canonical DB / MiniCheck / runtime破損によるFAILではない。

今回の失敗は主に次の3領域へ集中している。

1. **Generatorがsource_factを十分に原子的・保守的に生成できていない。**
2. **Phi-4 Atomicity / Role Gateが、妥当なsource_fact候補まで`INDETERMINATE`へ落としている可能性が高い。**
3. **provider schemaがpresentation-role cardinalityを事前強制できず、Case 3ではretry後に`duplicate_presentation_role`がV0で発生した。**

加えて、retry feedbackはfailure code / unit ID中心で、失敗したunit text自体を返さないため、Generatorにとって修正対象が十分具体的でない。

最重要の優先順位は次とする。

```text
P0-1  Phi-4 Atomicity / Role Gateの診断benchmark
P0-2  Generatorのatomic source_fact / no-extra-fact生成benchmark
P0-3  presentation_role uniquenessをprovider側で強制できるschema capability probe
P1    retry feedbackの情報量改善
```

現時点でMiniCheckの再選定やSimilarity redesignを行う根拠はない。

---

## 2. What G-22 proved

G-22では次がPASSしている。

```text
Preflight / Frozen identity             PASS
Mistral / Phi-4 smoke                   PASS
MCP / Harrier / Qdrant                  PASS
Similarity actual rank-1                PASS
MiniCheck offline reproduction          PASS
Canonical before/after                  identical
Integrity before/after                  PASS
Focused regression                      37 passed
Execution/freeze contracts              10 passed
Full pytest                              408 passed / 0 failed
Repository-wide Ruff                    PASS
git diff --check                        PASS
start HEAD == end HEAD                  PASS
```

3 Caseはすべて:

```text
terminal = REJECTED
render_mode = NONE
formal verdict = FAIL
retry = 1
```

だった。

安全面では:

```text
unsupported rendered material claims = 0
accepted role escape = 0
accepted non-atomic unit = 0
```

であり、**v3はG-12で問題だったfalse acceptanceを防いだ。**

一方で、use-case completionは0/3であり、現在は安全性が高い代わりに**過剰reject / generator contract failure**が実用性を阻害している。

---

## 3. Case-level failure map

### Case 1 — Saber Roleplay

Observed:

- Attempt 1/2ともunsupported franchise additionsを生成。
- Grail War / Excalibur / Shirouへの評価等、supplied Kにないmaterial detailが混入。
- source_fact候補にrole-INDETERMINATE / NON_ATOMICが発生。
- `creative_addition`はroleplay purposeでは許可されずscope violation。
- 2件のcertified supported source_factを確保できずMaterialへ進めない。

Primary classes:

```text
Generator factual leakage
+ claim atomicity failure
+ semantic-role classification indeterminate
```

### Case 2 — Similar Work Comparison

Observed:

- Similarity rank-1はactual retrievalでBLEACHとなり、Frozen expected IDと一致。
- U1-U4はFate/stay night / BLEACH Contextの内容を概ね忠実に言い換えている。
- しかしV2で全unitがrole-INDETERMINATE。
- U2はNON_ATOMIC。
- interpretation U5はShirouの能力という未支持premiseを導入。
- V2を通らないためsource-fact verifier / judgeへ到達しない。

Primary classes:

```text
Atomicity / role judge over-rejection candidate
+ one non-atomic unit
+ unsupported interpretation premise
```

Case 2は**Atomicity / Role Gate診断の最重要evidence**である。

### Case 3 — Concept Creative

Observed:

- Attempt 1はsource facts / creative unitがNON_ATOMIC / role-INDETERMINATE。
- Attempt 2はB2/B3が共に`presentation_role="creative"`となり、V0 `duplicate_presentation_role`。
- provider schemaとしては生成可能だったが、SGOKB V0 identity invariantでreject。

Primary classes:

```text
Atomicity / role judge over-rejection candidate
+ provider-visible schema underconstraint
+ generator output planning failure
```

---

# 4. Problem A — Generator source_fact quality

## 4.1 Current request is rule-heavy but example-light

`GroundedGenerationRequestBuilder`はGeneratorへ以下を要求する。

- supplied Grounded Contextだけをsource-world factに使う。
- 1 material text unit = 1 atomic proposition。
- `main -> source_fact`。
- `creative -> creative_addition`。
- creative textへsource-world factを入れない。

しかし、Generatorが実際に見るnormative instructionは抽象ルールの列であり、例えば次のような**positive / negative concrete pattern**はない。

```text
GOOD:
K5: "X is a Servant under contract with Y."
U1: "X is a Servant." support_refs=[K5]
U2: "X is under contract with Y." support_refs=[K5]

BAD:
U1: "X is a Servant who fights to win the Grail War."
```

G-22 Case 1はまさにBAD形状へ戻っている。

### Interpretation

Mistral Small 3.2自体は公式model cardでprecise instruction following改善をうたっているが、それはSGOKB固有のatomic proposition / role boundary / citation disciplineを保証するものではない。

Structured outputはJSON shapeを制約するが、unit textの factual correctness / atomicity / semantic role correctnessまでは保証しない。

したがって:

> 「24Bモデルなのに守れない」

ではなく、

> 「一般instruction modelへ、難しいclaim-decomposition + grounded generationをone-shotで要求している」

と評価する方が適切である。

## 4.2 Claim decomposition is itself a hard task

外部研究でも、long-form responseをatomic/checkworthy claimへ分解する処理は評価結果を大きく左右し、decomposition method自体がerror sourceになることが報告されている。

SGOKBではGeneratorへ:

```text
content generation
+ factual restriction
+ atomic decomposition
+ semantic-role assignment
+ support reference selection
+ presentation planning
```

を同時に行わせている。

これはG-22のfailure patternと整合する。

## 4.3 Retry feedback is too abstract

`GroundingFailureController.build_retry_feedback()`は次を返す。

```text
failure_class
failure_code
unit_id
support_refs
premise_unit_ids
json_path
expected_rule
repair_directives
```

一方、failed unitの**original text**はfeedbackに含めない。

Generatorのretry requestはwhole-output regenerationであり、前attempt本文をnormative inputとして保持する保証はない。

したがって:

```text
U2 = NON_ATOMIC
```

だけでは、Generatorが「U2のどのclauseを分割すべきか」を再構成しづらい。

### Recommended diagnostic

まずformal architectureを変えず、dev benchmarkで以下を比較する。

A. current prompt

B. current + neutral GOOD/BAD atomic examples

C. current + `prefer exact K wording / minimally normalized one proposition per unit`

D. B/C + retry feedbackへfailed unit textをstructured fieldとして追加

E. source_fact generationとpresentation/creative generationを二段階化

評価指標:

```text
unsupported added proposition rate
NON_ATOMIC rate
ROLE_VALID rate
V3 deterministic-supported rate
Material PASS eligibility
schema/V0 failure rate
```

### Recommendation

最初にB/C/Dをdev実験する。

それでも改善しない場合にのみEのarchitecture分離を検討する。

理由は、B/C/Dはlogical acceptance semanticsを変えずにGenerator guidanceを強化できる可能性があるためである。

---

# 5. Problem B — Phi-4 Atomicity / Role Gate

## 5.1 G-22 evidence indicates possible false-negative / over-abstention

Case 2ではContextの内容を概ね忠実に再述したsource_fact候補U1-U4までrole-INDETERMINATEになった。

これは次の2可能性を区別する必要がある。

```text
H1: Phi-4自体がこのclassifier taskに不適切
H2: Prompt / task definition / joint-output designが不十分
```

現時点ではH1とH2を分離できない。

## 5.2 The tracked Freeze pins policy, not a first-class judge-prompt artifact

G-21 harnessは:

- Phi-4 model identity
- temperature / max tokens / seed
- response verdict schema
- high-level Atomicity / Role policy

をfreezeしている。

一方、Generatorには`GroundedGenerationRequestBuilder.to_prompt_text()`というtracked message contractがあるのに対し、Atomicity / Role judgeについては同等の**first-class tracked literal prompt/profile artifact + prompt hash**が見当たらない。

G-22 raw evidenceには実request payloadが残るため監査は可能だが、post-failure diagnosisでは:

```text
model capability
vs
prompt wording
```

の切り分けが弱い。

これは次回remediationで改善すべきreproducibility gapである。

## 5.3 Joint atomicity + role classification can couple two tasks

現在のAdapterは1 callで:

```text
atomicity_verdict
role_boundary_verdict
```

を返す。

しかしatomicityとrole boundaryは別問題である。

例:

```text
"BLEACH is a manga series."
```

はatomicity判定と、`source_fact`としてcontent-typeが妥当かの判定を独立に扱える。

一方の曖昧さがもう一方の`INDETERMINATE`へ波及している可能性をG-22だけでは排除できない。

## 5.4 External research supports prompt-sensitivity concern

LLM-as-a-Judge研究では、semantic-equivalentなprompt variationでもjudge verdictが変化し得ることが繰り返し報告されている。

2025のrelevance-judgment研究ではprompt templateがagreementへ大きく影響し、2026 JudgeSenseでもjudge consistencyがprompt paraphraseへ敏感であることが示されている。

Phi-4 model card自体も、特定downstream classifier/judge用途への適合を保証しておらず、use-case-specific evaluationを求めている。

したがって、Case 2の結果だけで即座に「Phi-4を交換する」のではなく、まずSGOKB-specific gold benchmarkでprompt/modelを分離評価するべきである。

## 5.5 Required diagnostic benchmark

G-22 actual unitsを中心に`Atomicity / Role Gold Set v1`を作る。

最低bucket:

### Atomicity positive

- direct one-proposition K restatement
- faithful one-proposition paraphrase
- one proposition supported by multiple K refs

### Atomicity negative

- supported proposition + unsupported addition
- two independently judgeable facts joined by conjunction
- fact + causal inference
- fact + temporal inference

### Role positive

- legitimate `source_fact`
- legitimate `interpretation`
- legitimate `creative_addition`

### Role negative

- interpretation mislabeled source_fact
- source Concept fact smuggled into creative_addition
- creative invention mislabeled source_fact
- material source-world claim in disallowed purpose/role

### Gold origin

1. G-22 actual U1-U*.
2. G-12/G-20 adversarial units.
3. synthetic neutral controls that do not depend on franchise knowledge.

### Metrics

Atomicity and Roleを別々に測る。

```text
critical false-pass count
valid-unit false-reject count
INDETERMINATE rate
confusion matrix
same-input repeatability
prompt-paraphrase stability
```

### Experiment order

```text
1. exact G-22 prompt/payload replay on Phi-4
2. same model + clarified definitions/examples
3. split atomicity and role into separate calls
4. only if still inadequate: alternative judge candidates
```

### Decision rule

- Prompt改善だけでvalid source_fact recallが回復し、critical false-pass=0を維持するならPhi-4継続候補。
- Split-callでのみ改善するならV2 implementation/runtime profileを再設計。
- Prompt/splitでも過剰rejectまたはfalse-passが残るならjudge candidate selectionを再開。

**model replacementを最初の手段にしない。**

---

# 6. Problem C — presentation_role uniqueness / structured output

## 6.1 Current mechanism

Provider/application JSON Schemaの`blocks`は:

```text
array
minItems=1
maxItems=3
items = oneOf(main, interpretation, creative)
```

である。

このshapeは:

```json
[
  {"presentation_role":"creative", ...},
  {"presentation_role":"creative", ...}
]
```

をprovider schema上では許す。

SGOKBは後段V0 `_cross_item_contract_failures()`で`duplicate_presentation_role`としてrejectする。

G-20でこれはprovider/parser hidden mismatchを避けるため意図的にV0へ移された。

### G-22 impact

Case 3 Attempt 2ではstructured output自体は成功したが、V0でduplicate creative blockをrejectした。

つまり:

> schema adherenceは成功しているが、SGOKB invariant adherenceは失敗している。

## 6.2 JSON Schema can express cardinality more strongly

Draft 2020-12では`contains`と`minContains/maxContains`により、特定subschemaへ一致するarray item数を制約できる。

例えば概念上:

```json
{
  "type": "array",
  "contains": {"$ref": "#/$defs/creative_block"},
  "maxContains": 1
}
```

のようなconstraintをroleごとに組み合わせれば、同一presentation roleの複数blockをschema側で禁止可能である。

ただし、LM StudioのGGUF structured outputはllama.cpp grammar-based samplingを使用するため、**実際のLM Studio 0.4.25.0 / frozen runtimeが`contains/maxContains`をprovider grammarへ正しく反映できるかは別途preflight実証が必要**である。

LM Studio docsはJSON Schema structured outputをサポートするとするが、全Draft keywordの完全supportまでは今回確認できない。

## 6.3 Candidate fixes

### Option A — current shape + `contains/maxContains`

Pros:

- output contract shapeを維持しやすい。
- duplicate roleをgeneration時点で禁止できる可能性。

Cons:

- LM Studio / llama.cpp support確認が必要。
- schema complexity増加。

### Option B — fixed role properties

例:

```json
{
  "main": {...} | null,
  "interpretation": {...} | null,
  "creative": {...} | null
}
```

Pros:

- uniquenessが構造上自明。
- modelが同role blockを2個生成できない。

Cons:

- output contract revisionが必要。
- G-15/G-18/G-21の再Freeze対象。

### Option C — prompt instruction only

```text
Emit at most one block for each presentation_role.
```

Pros:

- 最小変更。

Cons:

- best-effortでしかない。
- G-22と同型failureを構造的に防止しない。

### Recommendation

まずOption Aのprovider capability probeを実施する。

PASSならAを第一候補。

unsupportedならBを設計候補とする。

C単独は正式remediationとしては弱いが、A/Bと併用するgenerator guidanceとしては有効。

---

# 7. What is NOT currently implicated

## MiniCheck

G-21V/G-21R/G-22 preflightで:

```text
required negative FP = 0/11
required positive = 2/2
positive recall = 0.8
specificity = 1.0
G-21V 17 verdicts/scores identical
network attempt = 0/0
```

G-22 case executionではV0/V2で停止し、MiniCheckへ到達していない。

したがって今回のformal FAILはMiniCheckのfailure evidenceではない。

## Similarity / Retrieval

Case 2 actual rank-1はBLEACHでFrozen expected IDと一致。

retrieval redesignの根拠はない。

## Canonical / MCP / Harrier / Qdrant

identity/integrity/canonical invarianceはPASS。

今回のremediation scopeから除外する。

---

# 8. Recommended remediation sequence

新しいFrozen条件を即決せず、次のdiagnostic-first sequenceを推奨する。

## Stage A — Evidence-preserving diagnostics

### A1. Atomicity / Role Gold Benchmark

G-22 actual units + G-12/G-20 adversarial + synthetic controlsでgold setを作成する。

目的:

```text
Phi-4 model issue
vs prompt issue
vs joint-classification issue
```

を切り分ける。

### A2. Exact judge prompt artifactization

Atomicity / Role / SourceFactJudge / InterpretationJudgeについて:

```text
prompt template
response schema
settings
prompt SHA-256
```

をtracked profileとして保存可能にする。

### A3. Provider schema capability probe

LM Studio 0.4.25.0で:

```text
contains
minContains
maxContains
```

がstrict structured outputで実際にenforceされるかneutral fixtureで確認する。

### A4. Generator atomic-output benchmark

Frozen G-22 Contextをdev-only fixtureとして使用し、以下を比較する。

```text
current
+ atomic GOOD/BAD examples
+ exact/minimal K paraphrase preference
+ explicit one-block-per-role rule
+ richer structured retry feedback
```

Formal rubricを変更せず、出力品質だけ比較する。

---

## Stage B — Decision after diagnostics

### If Phi-4 prompt-only fix succeeds

- logical V2 semantics維持。
- exact promptをfreeze対象化。
- G-21 runtime/harness revision後、new formal run。

### If split atomicity/role calls are required

- V2 implementation/runtime designをreopen。
- false-pass regressionを維持。
- G-21 re-freeze。

### If Phi-4 itself remains unsuitable

- bounded judge candidate comparisonを行う。
- public benchmarkよりSGOKB gold setを優先。

### If generator prompt-only fix succeeds

- source/test/request behaviorをrevision。
- G-18 logical semanticsを変えない範囲か確認。
- execution behaviorが変わるためG-21再Freezeは必須。

### If generator still fails

次を検討する。

```text
source-fact planning/decomposition stage
  ↓ validated atomic facts
presentation / interpretation / creative generation
```

これはarchitecture変更なのでG-18 reopen候補。

### If `maxContains` works

provider schemaへuniquenessを前倒しし、V0 checkはdefense-in-depthとして残す。

### If `maxContains` unsupported

role-keyed output structure等のschema revisionを検討する。

---

# 9. Proposed follow-up task set

まだ正式task番号として採番せず、次の順序で作業化することを推奨する。

```text
[P0] Atomicity / Role Gold Benchmark + exact G-22 prompt replay
[P0] Phi-4 prompt/split-call diagnostic
[P0] Generator atomic source_fact benchmark
[P0] LM Studio structured schema cardinality capability probe
[P1] Structured retry feedback redesign experiment
[P0] Diagnostic resultに基づくremediation decision / re-freeze plan
```

最初に行うべき作業は:

> **Atomicity / Role Gold Benchmark + exact G-22 prompt replay**

である。

Case 2のverbatim/faithful source fact候補がrole-INDETERMINATEになった原因を確定しないままGeneratorだけを修正すると、Generator品質が向上してもV2で引き続きrejectされる可能性があるためである。

---

# 10. External research reviewed

1. Wanner et al., **A Closer Look at Claim Decomposition** (2024) — claim decomposition method itself materially affects factual-support evaluation and is an independent error source.  
   https://arxiv.org/abs/2403.11903

2. Zhang et al., **A Claim Decomposition Benchmark for Long-form Answer Verification** (2024) — atomic/checkworthy claim decomposition remains challenging even for LLMs.  
   https://arxiv.org/abs/2410.12558

3. Arabzadeh & Clarke, **A Human-AI Comparative Analysis of Prompt Sensitivity in LLM-Based Relevance Judgment** (2025) — LLM judge labels depend materially on prompt templates.  
   https://arxiv.org/abs/2504.12408

4. Bellibatlu, **JudgeSense: A Benchmark for Prompt Sensitivity in LLM-as-a-Judge Systems** (2026) — semantically equivalent judge prompts can change verdict consistency; factuality judgments are also prompt-sensitive.  
   https://arxiv.org/abs/2604.23478

5. Microsoft, **Phi-4 Model Card** — Phi-4 is a general-purpose reasoning model, not a task-specific semantic-role classifier; downstream use requires use-case-specific evaluation.  
   https://huggingface.co/microsoft/phi-4

6. Mistral AI, **Mistral-Small-3.2-24B-Instruct-2506 Model Card** — 3.2 improves precise instruction following but remains a general instruct model.  
   https://huggingface.co/mistralai/Mistral-Small-3.2-24B-Instruct-2506

7. LM Studio, **Structured Output documentation** — GGUF structured outputs use llama.cpp grammar-based sampling; successful complete generation is constrained to the supplied JSON schema.  
   https://lmstudio.ai/docs/developer/openai-compat/structured-output

8. JSON Schema, **Array / contains / maxContains / uniqueItems** — `uniqueItems` compares whole array items; `contains` with `maxContains` can constrain how many items match a subschema.  
   https://json-schema.org/understanding-json-schema/reference/array

---

# 11. Final assessment

Current evidence supports the following confidence levels.

| Finding | Confidence |
|---|---|
| Retrieval / MiniCheck / canonical layer is not the cause of G-22 0/3 | **High** |
| Generator produces unsupported / non-atomic material under current prompt | **High** |
| Current provider schema permits duplicate presentation roles before V0 | **Certain from implementation + G-22** |
| Phi-4 V2 behavior is over-rejecting some valid source_fact candidates | **High suspicion; requires gold replay confirmation** |
| Phi-4 model itself, rather than prompt/task definition, is the root cause | **Not established** |
| Retry feedback lacks enough local repair context | **Medium-High** |

Therefore the correct next move is not acceptance-rule relaxation and not immediate model replacement.

```text
G-22 failure evidence
  ↓
Atomicity / Role diagnostic benchmark
  + Generator atomic-output benchmark
  + structured-schema capability probe
  ↓
root cause isolation
  ↓
minimal remediation
  ↓
re-freeze
  ↓
new formal acceptance
```

G-21 Frozen evidence and G-22 FAIL evidence must remain immutable historical records throughout remediation.
