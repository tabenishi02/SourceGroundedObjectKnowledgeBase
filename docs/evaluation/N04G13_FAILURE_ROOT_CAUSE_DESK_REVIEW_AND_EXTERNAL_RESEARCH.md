# N-04G-13 — G-12 Failure Root-Cause / Desk Review / External Research

更新日: 2026-10-18

- Status: **Complete**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger run: `20261018T213810+0900`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Remediation plan: `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
- Branch: `phase-n/n04-prerequisite-derived-search`

---

## 1. Executive conclusion

G-12のFAILは、Retrieval / MCP / Context Builder / canonical safetyではなく、**grounded-generation output / validation / terminal / rendering layer**に集中している。

今回の最重要結論は次である。

1. **G-04/G-05で設計したatomic semantic unitが実装上は強制されていない。**
2. **single semantic judgeがmulti-proposition unit全体へ1 verdictを返し、部分的unsupported clauseをfalse acceptできる。**
3. **`stylistic_expression`等のsupport不要roleがmaterial claimのescape hatchになり得る。**
4. **interpretationの「premise support → derivation support」というG-05二段階設計が実装では1回のsemantic verdictへ圧縮されている。**
5. **model-generated `label`はunit validation外なのにrendererが表示し得るため、rendering invariantを破る。**
6. **Case 3のlabel failureは、provider schemaとPython parserのcontract不一致である。**
7. **retry feedbackはV0 errorの詳細/pathを失っており、同じcontract failureを再生成しやすい。**
8. **`ACCEPTED`のmaterial sufficiency fallbackが弱く、grounding PASSとuse-case completionを十分に分離できていない。**
9. **rendererがterminal outcomeへbindされておらず、validation PASSだけで呼べる。**
10. **focused testsはlogical branchをcoveredしているが、real failureと同型のadversarial false-positiveを十分に含んでいない。**

したがって、「Phi-4を強いmodelへ交換して再実行」だけでは不十分である。

推奨する方向は:

```text
atomic claim enforcement
+ role-escape prevention
+ deterministic presentation
+ source-fact specialized verification candidate
+ interpretation premise graph
+ explicit material requirement gate
+ terminal-bound renderer
+ G-12 replay/adversarial tests
```

である。

---

# 2. Reviewed implementation

対象:

```text
src/sgokb/grounding/context.py
src/sgokb/grounding/request.py
src/sgokb/grounding/output.py
src/sgokb/grounding/validation.py
src/sgokb/grounding/failure.py
src/sgokb/grounding/render.py
src/sgokb/grounding/evidence.py
src/sgokb/application_grounding.py
tests/test_n04_grounded_generation.py
```

比較したDecision:

```text
docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md
docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md
docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md
docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md
```

---

# 3. G-12 failure root-cause

## 3.1 Case 1 — Multi-proposition false acceptance

Observed:

```text
Machine terminal: ACCEPTED
Formal verdict: FAIL
```

G-12 recordでは、K5がsupportするのはSaberのServant / sword / Shirouとのcontract等であり、同じunitへ追加されたHoly Grail Warのmaterial detailまではsupportしない。

しかしV4 judgeはunit全体へ`entailed`を返した。

### Root cause

`GroundingValidator`は1 `unit.text`を1 semantic judgment単位として扱う。

```text
unit.text
+ cited K units
→ semantic_validator.validate(...)
→ one verdict
```

G-04では`unit.text`を「原則1つのmaterial semantic proposition」として設計し、G-05では「1文に複数factが含まれる場合、atomic unitへ分割して全material propositionを検証する」と定義している。

しかし実装ではatomicityを検査しない。

Request Builderに:

```text
Keep each material semantic proposition atomic enough to validate.
```

というinstructionはあるが、これはgeneratorへのbest-effort要求でありGateではない。

### Classification

```text
Design intent: correct
Implementation enforcement: missing
Severity: P0
```

---

## 3.2 Case 1 — `stylistic_expression` role escape

Observed:

- relationship / duty / loyalty等のmaterial claimが`stylistic_expression`として出力された。
- `support_refs=[]`。
- Phi-4 validatorが`role_valid`を返し、rendered responseへ到達した。

G-05は、`stylistic_expression`はmaterial propositionを含まない場合だけ`not_applicable`とし、material claimなら`source_fact`へ再分類してsupportを要求すると明記している。

### Root cause

実装はroleごとに:

```text
creative_addition / context_limit / stylistic_expression
→ semantic validator returns role_valid
→ not_applicable
```

という単一classificationへ依存する。

`stylistic_expression`にはK supportがなく、validatorがrole mismatchを見逃した場合の第二Gateがない。

### Classification

```text
Design intent: correct
Implementation robustness: insufficient
Severity: P0
```

---

## 3.3 Case 2 — Interpretation premise validation incomplete

G-05はinterpretationについて:

```text
1. premise support
2. derivation support
```

を分離している。

必要条件:

```text
all material premises supported
AND conclusion is reasonable derivation
AND no external factual premise
```

しかし現実装はinterpretation unitに対して、`support_refs`のK unitsを一括でsemantic validatorへ渡し、`reasonable_derivation`が返れば`derived_supported`とする。

つまり:

- premiseを明示的なvalidation unitとして検証しない。
- conclusionの中にhidden external premiseがあっても1 verdictで通過し得る。
- multi-object comparisonで両Objectがpremiseへ寄与したかdeterministicに検査しない。

G-12 Case 2のunsupported interpretation premiseはこのgapと一致する。

### Classification

```text
Design-to-implementation gap: yes
Severity: P0
```

---

## 3.4 Case 3 — JSON Schema / parser mismatch

Current JSON Schema:

```text
label: string | null
```

Current parser:

```text
if presentation_role in {interpretation, creative}:
    require non-empty string label
```

LM Studio structured outputはprovider schemaに従えば`label=null`を合法に生成できる。

その後Python parserがrejectするため、provider constrained decodingとapplication contractが一致しない。

Retryでも同じschemaを渡すため、同じfailureが再発しやすい。

### Classification

```text
Implementation contract mismatch
Severity: P0
```

---

# 4. Additional desk-review findings

G-12で直接観測された3 failure以外に、同種failureへつながる問題を以下で確認した。

---

## P0-01 — Model-generated `label` bypasses unit validation

### Current behavior

`label`はLLM-generated fieldだが、GroundingValidatorのunit validation対象ではない。

Rendererはnon-main blockで:

```text
model labelがnon-emptyならそのlabelを表示
otherwise default label
```

となっている。

### Risk

例えばcreative blockが:

```text
presentation_role = creative
label = "Canonical facts"
```

を返した場合、bodyはcreativeとして正しくvalidationされても、人間向け表示では`Canonical facts`と表示され得る。

さらにlabel自体にmaterial sentenceを入れれば、その文字列は`unit.text`ではないためsemantic validationを通らず表示される。

これはG-04/G-07の:

```text
rendered response content = validated unit.text content
renderer may add fixed headings/separators only
```

に反する。

### Resolution

**model-generated free-form labelをrenderしない。**

推奨:

```text
presentation_role=interpretation -> fixed "Interpretation"
presentation_role=creative       -> fixed "Creative addition"
presentation_role=context_limit  -> fixed "Context limit"
```

localized UI labelが必要ならApplication/renderer側のtrusted tableで管理する。

model fieldとして`label`を残す理由がないならcontractから削除する。

---

## P0-02 — Atomicity is instruction-only

### Current behavior

Generatorへatomicityを要求するが、output schemaにもvalidatorにもatomicity invariantがない。

### Risk

```text
supported proposition + unsupported proposition
```

を1 unitへ入れることで1 semantic verdictに圧縮される。

Case 1で実発生した。

### Resolution

- 1 material proposition / unitをnormative invariantにする。
- obvious compound-riskをGateで検出し、unsafeにsplitせずretry / INDETERMINATEへ落とす。
- optional atomizerはaudit用途に使えるが、atomizer omissionがあるため単独authorityにしない。
- G-12 false-accept exampleをgold adversarial fixture化する。

---

## P0-03 — Support-free roles are semantic escape hatches

対象:

```text
stylistic_expression
context_limit
creative_addition
```

いずれも`support_refs=[]`を要求するため、role classifierがfalse positiveするとmaterial source-world claimがsupportなしでPASSできる。

### Resolution

#### `stylistic_expression`

N-04 v3 baselineでは次のいずれかを選ぶ。

A. model-authored stylistic_expressionを禁止する。

B. `non_propositional_style`相当へ狭め、material proposition検出時は必ずrole mismatch。

Roleplayの自然さはsupported `source_fact.text`のfirst-person paraphraseで維持できるため、Aが最も単純で安全。

#### `context_limit`

free-form model proseではなくstructured reason code + deterministic rendererを検討する。

#### `creative_addition`

新規創作自体は許可するが、source Object / Conceptについて説明するmaterial clauseを含む場合はrole mismatchとする。

---

## P0-04 — Interpretation validates conclusion and premises as one opaque text

### Risk

K refsが存在しても、interpretation text内のhidden premiseがKにない場合がある。

### Resolution

推奨contract:

```json
{
  "semantic_role": "interpretation",
  "premise_unit_ids": ["U1", "U2"],
  "text": "... conclusion ..."
}
```

- premiseは既に`source_fact / supported`になったunitだけを参照する。
- validatorは全premise supportedをdeterministicに確認する。
- semantic judgeは「このconclusionがこれらpremiseからreasonableに導けるか」だけを判定する。
- Comparisonで両Object比較をclaimする場合はpremise sourceが両Objectをcoverすることをdeterministicに検査する。

これによりG-05の二段階validationを物理化できる。

---

## P0-05 — Single general-purpose LLM judge is too strong an authority

G-05自体はsemantic validatorもfallibleと認識しているが、実装ではV4 unresolved unitの最終判定が1 validator verdictへ依存する。

Case 1でfalse acceptanceが実証された。

### Resolution

source_factとinterpretationを同じjudge policyで処理しない。

推奨candidate:

```text
source_fact:
  specialized document-claim fact checker
  + optional independent LLM judge

interpretation:
  validated premise units
  + bounded derivation judge
```

Verifier disagreementはPASSへ昇格しない。

---

## P1-01 — V0 retry feedback loses error detail/path

`parse_generation_output()`はValidationError pathをmessageへ含めるが、GroundingValidatorのV0 `_failure()`は`failure_code`しか保存しない。

`build_retry_feedback()`も:

```text
failure_class
failure_code
unit_id
support_refs
```

しか返さない。

Case 3の`missing_presentation_label`ではblock ID / JSON path / required correctionが失われる。

### Resolution

failure resultへ最低限:

```text
json_path
block_id
failure_detail
expected_rule
```

を追加する。

`jsonschema.Draft202012Validator.iter_errors()`を利用し、複数schema errorとinstance pathを保存することも検討する。

---

## P1-02 — Structured schema under-specifies already-known semantic structure

現在schemaは:

- block presentation role
- unit semantic role
- support_refs array

を独立enum/arrayとして持つ。

しかし:

```text
interpretation must be in interpretation block
creative_addition must be in creative block
source_fact requires support_refs >= 1
creative/style/context_limit support_refs = []
```

はschemaへencodeされていない。

### Resolution

LM Studioが対応する範囲でJSON Schemaを強化する。

ただしadvanced schema featureがruntimeで確実にsupportされるとは文書から断定しない。

候補:

1. `oneOf` / `if-then`をpreflight検証して採用。
2. contract shapeを単純化してroleごとの専用array/block schemaにする。
3. `label`をmodel contractから排除し、conditional label rule自体を不要にする。

3を含む単純化が最もrobust。

---

## P1-03 — Material sufficiency fallback is too weak

`GroundingFailureController._infer_material_sufficiency()`は、output内に次のroleが1件でもあればtrueになる。

```text
source_fact
interpretation
creative_addition
```

### Risk

- Comparisonで一方のWorkしか使わなくてもACCEPTED可能。
- Creativeで一方のConceptしか使わなくてもACCEPTED可能。
- Roleplayで必要最低fact数を満たさなくてもACCEPTED可能。

manual formal rubricが後でFAILにできるが、machine terminal `ACCEPTED`の意味が弱い。

### Resolution

`MaterialRequirementGate`を独立させる。

```text
Grounding PASS
+ purpose / case requirement PASS
→ ACCEPTED
```

Generic purpose invariantとbenchmark-specific conditionは分離する。

---

## P1-04 — Renderer is not bound to terminal decision

Application `render()`は:

```text
output + validation
```

だけを受け、failure-controller decisionを受けない。

したがってorchestrator misuseがあれば、validation PASSだがterminal policy上はnormal renderすべきでないoutputをrender可能。

### Resolution

Rendererへterminal decisionを要求する。

```text
ACCEPTED -> normal deterministic render
INSUFFICIENT_CONTEXT -> context-limit-only safe render
REJECTED -> no render
SYSTEM_FAILURE -> no render
```

---

## P1-05 — Multi-object attribution / coverage is implicit

`source_fact` unit自体にtarget `object_id` fieldはない。

object identityはsupport Kから間接的に分かるが、Comparison / Creativeで「両Objectからfactを利用したか」はGroundingValidatorがaggregate検査しない。

### Resolution

- K refからsource object coverageをdeterministically集計する。
- 必要ならunitへ`subject_object_id`を追加する。
- Comparison / Creative purpose invariantへobject coverageを追加する。

---

## P1-06 — Tests mirror intended verdicts but not verifier failure modes

現在focused testは`FakeSemanticValidator`へ期待verdictを直接返させる。

そのため:

- validator false positive
- multi-proposition partial support
- role-escape false positive
- model label injection
- unsupported interpretation premise

を検出できない。

### Resolution

G-12 failure shapeをadversarial testへ追加する。

Fake judgeを使う場合も、「誤ってentailedを返したjudgeを第二Gateが止める」testが必要。

---

## P2-01 — Validation result is less auditable than G-05 conceptual contract

G-05 conceptual resultは:

```text
context_fingerprint
support_refs
deterministic_verdict
semantic_verdict
validator_metadata
```

等を想定していた。

現実装unit resultは最終dispositionとstage中心で、semantic judge metadataはcore resultへ保持しない。

formal harness側で別evidenceは残せるが、production auditabilityは弱い。

### Resolution

次期result contractで:

```text
support_refs
semantic_verdict
validator_id/version
atomicity verdict
premise unit refs
```

等を保持する。

---

# 5. External repository / library research

## 5.1 LM Studio Structured Output

Source:

- https://lmstudio.ai/docs/python/llm-prediction/structured-response
- https://beta.lmstudio.ai/docs/developer/openai-compat/structured-output

Relevant finding:

LM StudioはJSON Schemaを与えることでstructured responseをschemaへconstrainできる。

ただしこれは**schema conformance**の機構であり、「K5がclaim全体をsemanticにsupportする」ことまでは保証しない。

### Applicability

採用継続。

用途:

```text
shape
required fields
enum
array/object constraints
simple structural invariants
```

用途外:

```text
factual entailment
interpretation validity
role semantic validity
```

### Design implication

構造で防げることはStructured Outputへ寄せるが、semantic groundingの代替にはしない。

---

## 5.2 JSON Schema Draft 2020-12 / python-jsonschema

Sources:

- https://json-schema.org/draft/2020-12/
- https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-01
- https://python-jsonschema.readthedocs.io/en/v4.25.1/errors/

Relevant findings:

- Draft 2020-12には`oneOf`, `if`, `then`, `else`等のsubschema mechanismがある。
- projectは既に`jsonschema>=4.18,<5`を依存に持ち、`Draft202012Validator`を使用している。
- `iter_errors()` / ValidationError pathを使えば、単一`schema_violation`より詳細なrepair evidenceを取れる。

### Applicability

**新規dependency不要で改善可能。**

推奨:

- Python-side schema validationのerror path/detailを保持する。
- role-specific structureをJSON Schemaへ寄せる案を試す。

注意:

LM Studio側がDraft 2020-12の全advanced keywordを完全supportするとは、確認した公式Structured Output説明だけでは保証できない。

したがってformal dependencyにする前にReference Workstation preflightでschema subset compatibilityを確認する。

より安全なのは、advanced conditionalを減らせるcontract shapeへ単純化することである。

---

## 5.3 FActScore

Source:

- https://github.com/shmsw25/FActScore
- https://arxiv.org/abs/2305.14251

Relevant finding:

FActScoreはlong-form generationを**atomic factsへ分解し、各atomic factがknowledge sourceでsupportされる割合**を評価する。

FActScoreが解決しようとする「一つの長いgenerationにsupported / unsupported情報が混在するためbinary whole-response判定では粗い」という問題は、G-12 Case 1と同型である。

### Applicability

**設計patternとして強く参考にする。**

ただしFActScore package自体はretrieval / external knowledge sourceを前提とするため、SGOKBのruntimeへそのまま組み込む必要はない。

SGOKBでは既にK refsがあるので:

```text
atomic proposition
→ cited K support
```

だけを利用すればよい。

またFActScore型のpost-hoc atomizerだけをauthorityにすると、atomizerがclaimを取りこぼすリスクがある。

そのためSGOKBでは「generator contract時点でatomic」を第一防御とし、post-hoc atomizationはaudit / adversarial checkへ回すのが望ましい。

---

## 5.4 Ragas Faithfulness

Source:

- https://github.com/vibrantlabsai/ragas/blob/main/src/ragas/metrics/collections/faithfulness/metric.py
- https://github.com/vibrantlabsai/ragas/blob/main/docs/concepts/metrics/available_metrics/faithfulness.md

Relevant finding:

current Faithfulness implementationは:

```text
1. responseをatomic statementsへ分解
2. each statementをretrieved contextに対してNLI的に判定
3. supported statement比率を計算
```

というmulti-step pipelineである。

### Applicability

G-12 Case 1に対して、**statement/claim decomposition → per-claim support**という方向を支持する。

ただしRagasは評価frameworkであり、SGOKB production grounding Gateへ直接依存させる必要はない。

特にstatement extraction自体がLLMであるため、SGOKBではnormative output contractのatomicityを先に強制する方がtraceabilityに優れる。

---

## 5.5 Amazon RAGChecker

Source:

- https://github.com/amazon-science/RAGChecker

Relevant finding:

RAGCheckerはfine-grained diagnosisで**claim-level entailment**を利用し、retrieverとgeneratorのfailureを分離する。

Generator metricsにはfaithfulness / hallucination / self-knowledge等を分けている。

### Applicability

SGOKBでRetrievalが正常、Generation groundingがFAILという今回の切り分け方法と整合する。

特に「retrieval qualityとgenerator faithfulnessを同じmetricへ混ぜない」という考え方は、N-04とN-06の責務分離を支持する。

Package直接導入は不要。

---

## 5.6 MiniCheck

Source:

- https://github.com/Liyan06/MiniCheck

Relevant finding:

MiniCheckはgrounding documentに対してclaimをsentence-levelでfact-checkするための専用model群を提供する。

Repository READMEは:

```text
MiniCheck(document, sentence) -> [0, 1]
```

を基本形とし、multi-sentence claimは先にsentenceへ分割することを推奨している。

公開candidateには:

```text
roberta-large
deberta-v3-large
flan-t5-large
Bespoke-MiniCheck-7B
```

があり、READMEではFlan-T5-Large 770Mを<1B candidateとして案内している。

Repository自体はApache-2.0。

### Applicability

**source_fact verifier candidateとして最も直接的。**

利点:

- general chat LLMより「document -> claim supported?」へ特化。
- local execution可能。
- binary probabilityを取得できる。
- 24B generatorとは独立したfailure modeを期待できる。

注意:

- model licenseはrepository licenseと別に確認する。
- first use auto-downloadを行う実装があるためformal harnessでは事前download / pinned local cacheが必要。
- sentence-level checkerなのでatomicity問題を先に解決する必要がある。
- thresholdはSGOKBのG-12 replay set / adversarial setでcalibrationする必要がある。
- MiniCheck単独judgeを新たな絶対authorityにしない。

### Recommendation

G-16でまず**offline candidate benchmark**を行う。

```text
G-12 supported examples
G-12 unsupported examples
synthetic conjunction examples
contradiction examples
paraphrase examples
```

でfalse-positiveを比較し、採用可否を決める。

---

## 5.7 AlignScore

Source:

- https://github.com/yuh-zha/AlignScore

Relevant finding:

AlignScoreはcontextとclaimのfactual consistencyを評価し、claimをsentence単位、contextをchunk単位へ分ける方式を持つ。

NLI / binary modeを持ち、source textとgenerated claimのalignment用途として設計されている。

### Applicability

source_fact verifierのsecondary benchmark candidateとして有効。

ただし:

- repository READMEはPyTorch 1.12.1を再現推奨しており、現行SGOKB dependencyとの統合コストを要確認。
- score thresholdをSGOKB用途でcalibrateする必要がある。

したがってMiniCheckより優先度は低い。

---

## 5.8 DeepEval Faithfulness

Sources:

- https://deepeval.com/docs/metrics-faithfulness
- https://github.com/confident-ai/deepeval/blob/main/deepeval/metrics/faithfulness/faithfulness.py

Relevant finding:

DeepEvalも:

```text
claims extraction
truth/context extraction
per-claim verdict
```

というfaithfulness architectureを持つ。

current docsにはLLM judge以外にhybrid/system-one判定もある。

### Applicability

「claim extractionとclaim verificationを分離する」「ambiguous verdictを別扱いにする」というarchitecture参考になる。

ただしSGOKBへframework全体を導入するとdependency / abstractionが過大であり、current custom contractとの整合性も低い。

**直接dependency化は現時点で非推奨。**

---

# 6. Solution evaluation

## Option A — Phi-4を別general LLMへ交換するだけ

### Pros

- 実装変更が小さい。
- false-positive率が下がる可能性。

### Cons

- atomicity gapが残る。
- stylistic role escapeが残る。
- interpretation premise gapが残る。
- label bypass / terminal gate問題が残る。
- judgeを単独authorityにする構造が変わらない。

### Decision

**不十分。単独では不採用。**

---

## Option B — Post-hoc LLM atomizerを追加するだけ

### Pros

- FActScore/Ragas型のfine-grained verificationへ近づく。

### Cons

- atomizerがclaimをomitできる。
- output unit/support refとのmappingを再推論する必要。
- normative outputとvalidation対象が再び分離する。

### Decision

**audit補助として採用候補。最終authorityとして不採用。**

---

## Option C — Generator contractでatomicityを要求 + verifierで再確認

### Pros

- support refとのmappingが明示される。
- omissionの余地を減らせる。
- Case 1型のcompound claimをfail-closedにできる。

### Cons

- atomicity判定自体のruleが必要。
- proseの自然さとのtradeoff。

### Decision

**採用推奨。**

---

## Option D — Specialized source-fact verifierを追加

### Pros

- general chat modelとは異なるinductive bias。
- document-claim support問題へ直接最適化されたcandidateがある。

### Cons

- dependency / model cache追加。
- threshold calibration必要。
- interpretationにはそのまま適用しにくい。

### Decision

**G-16でbenchmarkして条件付き採用候補。**

MiniCheckを第一candidate、AlignScoreをsecondary candidateとする。

---

## Option E — Deterministic presentation + fixed headings

### Pros

- Case 3 label failureを根本的に消せる。
- label content validation bypassも消せる。
- renderer invariantが単純になる。
- modelへ不要なpresentation責務を持たせない。

### Cons

- model任意heading表現の自由度がなくなる。

### Decision

**強く採用推奨。**

Grounded workflowでは自由headingよりsemantic separationが重要。

---

## Option F — Interpretation references validated premise units

### Pros

- G-05二段階設計を直接実装できる。
- hidden external premiseを減らす。
- multi-object coverageを機械検査できる。

### Cons

- output contract変更が必要。

### Decision

**採用推奨。**

---

## Option G — Material Requirement Gate

### Pros

- machine ACCEPTEDとformal use-case completionを近づける。
- GroundingとCompletenessを分離したまま合成できる。

### Cons

- benchmark-specific requirementをcoreへhardcodeしない設計が必要。

### Decision

**採用推奨。**

Coreにはgeneric gate interface、formal harnessからcase requirementを注入する。

---

# 7. Recommended target architecture

```text
Grounded Context / K*
        ↓
Generation Request
  + atomic unit rule
  + simple structured contract
        ↓
Local Generator
        ↓
V0 Structural Gate
  + exact schema
  + detailed error path
        ↓
V1 Reference Integrity
        ↓
V2 Role / Atomicity / Scope Gate
  + no unvalidated free-form label
  + no role escape
        ↓
V3 Deterministic Support
        ↓
V4a Source Fact Verification
  + specialized fact checker candidate
  + optional independent judge
        ↓
V4b Interpretation Verification
  + all premise unit IDs already supported
  + derivation judge only
        ↓
V5 Grounding Aggregate
        ↓
Material Requirement Gate
        ↓
Failure Controller
        ↓
ACCEPTED / INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE
        ↓
Terminal-bound Deterministic Renderer
  + fixed trusted headings only
```

---

# 8. Reopen impact assessment

## G-02 Claim taxonomy

Potential reopen: **limited**。

- `stylistic_expression`をformal baselineで禁止/狭義化する場合に必要。
- semantic role enum自体を削除しないならclarificationで済む可能性。

## G-04 Output contract

Reopen: **required**。

- atomicity physical invariant
- interpretation premise-unit references
- label/presentation contract
- optional object attribution

を更新する必要がある。

## G-05 Validation design

Reopen: **required**。

G-12でG-05 intended semanticsが物理実装されていない点が実証された。

- atomicity
- role escape
- premise support
- validator composition

を明示する。

## G-06 Failure policy

Potential reopen: **small**。

max retry=1は維持可能。

ただしV0 retry feedback detail、validator disagreement / atomicity failureのretryabilityを追記する必要がある。

## G-07 End-to-End Freeze

Reopen/re-freeze: **required after G-14〜G-17**。

Responsibility boundary、MCP/canonical境界は維持する。

## G-08 / G-11

v2 Failed historyとして保持。

新設計後は**v3 acceptance / harnessを別versionで作る**。

既存v2を上書きしない。

---

# 9. Test gap matrix

| Failure shape | Existing focused test | Required new test |
|---|---|---|
| unsupported source fact with judge correctly saying unsupported | Yes | retain |
| supported + unsupported clause, judge says entailed | No | P0 |
| material claim disguised as stylistic_expression | No | P0 |
| context_limit mixed with source fact | No | P0 |
| creative block makes unsupported source Concept claim | weak | P0 |
| interpretation hidden unsupported premise | No | P0 |
| interpretation only one comparison side cited | No | P1 |
| arbitrary model label rendered | No | P0 |
| label=null provider-schema mismatch | formal only | P0 |
| V0 retry feedback path/detail | No | P1 |
| materially incomplete output becomes ACCEPTED | No | P0/P1 |
| validation PASS but terminal non-ACCEPTED renderer call | No | P1 |
| verifier disagreement | No | P0 |
| G-12 exact failure shapes replay | No | P0 |

---

# 10. Final recommendation

次はN-04G-14へ進む。

優先順:

```text
1. atomic claim / role escape
2. presentation contract / deterministic headings
3. source-fact verifier + interpretation premise architecture
4. material/terminal/render gate
5. integrated design freeze
6. implementation
7. adversarial regression
8. v3 formal acceptance
```

現時点でRetrieval / MCP / canonical data modelへ戻る根拠はない。

また、単純なvalidator model replacementだけを先行させない。

G-12は、generator hallucinationだけでなく**grounding Gate自体のfalse-positive path**を発見したformal evidenceとして保持する。
