# N-04G-08 N-04 v2 Acceptance Spec Freeze

更新日: 2026-10-18

- Status: **Accepted / Acceptance Frozen**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-08 [P0] N-04 v2 benchmark / acceptance specを固定する`
- Failed baseline: `benchmark/n04-ai-use-cases-v1.json`
- Frozen v2 spec: `benchmark/n04-ai-use-cases-v2.json`
- Design Freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 formal re-acceptanceの評価仕様として、`benchmark/n04-ai-use-cases-v2.json`を**Frozen acceptance spec**として採用する。

v1は2026-10-18に実施済みのFailed baselineとして不変保持し、v2で上書きしない。

v2はv1の3代表use caseと核心quality Gateを継承し、G-07でFreezeしたgrounded-generation protocolを追加評価する。

Formal re-acceptance開始後は、次をcaseごと・結果ごとに変更してはならない。

- case Object / Concept identity
- Context purpose / budget / include policy
- Similarity candidate selection rule
- generator model / runtime / generation settings
- validator implementation / semantic validator policy
- generation output contract
- validation semantics
- retry上限 / retry invariants
- PASS / FAIL criteria
- critical failure criteria

変更が必要になった場合はformal runを停止し、G-07 / G-08 Freezeを必要範囲で明示的にreopenする。

---

## 2. v1は変更しない

次を固定する。

```text
benchmark/n04-ai-use-cases-v1.json
```

位置づけ:

- N-04 initial acceptance spec
- 2026-10-18 Failed baseline
- prompt-only grounding restrictionでは不十分だった証拠
- G-01〜G-07 remediation前の比較基準

v2 PASSのためにv1 result / raw evidence / rubricを削除・改変しない。

---

## 3. v1から継承するもの

### Same three representative use cases

```text
Case 1: Saber Roleplay
Case 2: Fate/stay night -> Similar Work -> comparative explanation
Case 3: Tsundere + Hero's Journey -> creative Character
```

### Same evaluation data identity

Source dataset:

```text
benchmark/n03-real-data-vertical-slice-v1.json
```

Evaluation DB:

```text
.local/n03/sgokb-n03.sqlite
```

### Same core quality gates

#### Case 1

- first-person roleplay
- supplied Contextから最低2 concrete fact
- contradictionなし
- Context外franchise / backstory factなし
- missing personality / backstoryをmodel memoryで補完しない

#### Case 2

- Similarity pathから比較対象を選択
- 両Workからfactual material
- comparison / contrastあり
- interpretationをstored factから分離
- Context外franchise factなし
- Similarity score semanticsを誤解しない

#### Case 3

- 両Conceptからgrounded ideaを利用
- 両Conceptを新規Character / arcへ統合
- creative additionをsource Knowledgeから分離
- source ConceptについてContext外factを追加しない

このためv2はrubric緩和ではない。

---

## 4. v2で追加・変更するもの

### 4.1 Grounded Context

J-04 Context Builder resultへG-03のprojectionを適用する。

```text
sgokb.context-builder.v1
        ↓
sgokb.grounded-context.v1
        ↓
context_fingerprint + K1 / K2 / ...
```

各source factual unitはsupplied Contextへtrace可能でなければならない。

### 4.2 Structured generation output

Natural-language-only responseをnormative outputにしない。

Generatorは:

```text
sgokb.grounded-generation-output.v1
```

に従うstructured semantic unitsを返す。

最低限:

```text
contract_version
context_fingerprint
purpose
blocks[]
  block_id
  presentation_role
  label
  units[]
    unit_id
    semantic_role
    text
    support_refs[]
```

を論理contractとして扱う。

### 4.3 Validation

次を使用する。

```text
sgokb.grounding-validation.v1
```

Stage:

```text
V0 Contract / Parse
V1 Reference Integrity
V2 Taxonomy / Use-case Policy
V3 Deterministic Support
V4 Bounded Semantic Support
V5 Aggregate Verdict
```

`K*`が存在するだけではgrounded PASSにしない。

### 4.4 Deterministic rendering

Human-readable responseはvalidated `unit.text`だけからrenderする。

別model-generated `final_response`はformal acceptance pathで使用しない。

### 4.5 Retry

G-06をそのまま採用する。

```text
max generation attempts per case = 2
max retry = 1
```

retry中に固定する:

- `context_fingerprint`
- Grounded Context / K mapping
- generator model
- runtime / endpoint
- generation settings
- output contract
- user task / case rubric

追加可能なのはstructured validation feedbackだけである。

禁止:

- new retrieval
- Web Search
- external factual supplementation
- another local generator model
- cloud model
- case-specific settings変更

### 4.6 v1 model-switch retryを廃止

v1には「response contractを満たさない場合に、より強いalready-installed local modelへ1回切替可能」というpolicyがあった。

これはG-06 / G-07のretry invariantと整合しないため、v2 formal runでは採用しない。

v2ではformal run開始前にgeneratorを1 modelへfreezeする。

もし選択modelがformal run開始前のpreflightでcontract実行不能と判明した場合は、formal runを開始せずG-11 harness freeze前にmodel selectionをやり直す。

formal run開始後はmodel switchingしない。

---

## 5. Generator / Validator model policy

### Generator

Formal run前に次をfreezeする。

```text
runtime
endpoint
model identifier
model file / quantization if applicable
context configuration
GPU/device configuration if material
temperature
max_tokens
seed if supported
```

同じ設定を全3 case / retry attemptで使用する。

### Validator

V0〜V3はdeterministic validationを優先する。

V4でLLM semantic judgeが必要な場合は、formal run前に**generator-independentなfixed local validator**をfreezeする。

禁止:

- caseごとのvalidator切替
- generator self-checkだけによるgrounding certification
- cloud validator
- Web / external Knowledgeをvalidatorへ与えること

exact validator identifier/settingsはG-11 formal harness freezeで記録する。

---

## 6. Formal Case verdict

### Case PASS

Case PASSには次をすべて要求する。

1. terminal outcome = `ACCEPTED`
2. Retrieval / Context Gate PASS
3. case-specific output Gate PASS
4. critical failure = 0
5. rendered responseはvalidated unit textだけで構成
6. canonical mutationなし

### Retry PASS

Attempt 1が失敗してAttempt 2が`ACCEPTED`になった場合も、次をすべて満たせばCase PASSとして認める。

- retry回数 <= 1
- frozen retry invariants維持
- attempt 1 evidenceを削除しない
- retry feedbackを保存
- attempt 2が全case rubricを満たす
- critical failureがrendered responseへ残らない

これはcherry-pickではなく、Design Freezeで定義されたworkflowの正式pathである。

### `INSUFFICIENT_CONTEXT`

`INSUFFICIENT_CONTEXT`は安全なterminal outcomeであり、hallucination failureとは区別する。

しかしN-04は代表AI workflowを実用完遂できることの受入であるため、**Case PASSには数えない**。

したがってformal verdictはFAILとなるが、failure reasonはgrounding violationではなくKnowledge / Context sufficiencyとして記録できる。

### `REJECTED`

Case FAIL。

### `SYSTEM_FAILURE`

Case FAIL。

generator quality failureとは分けて記録する。

---

## 7. Overall N-04 v2 PASS Gate

N-04 v2 PASSには3 caseすべてのCase PASSが必要である。

```text
3 / 3 Case PASS required
```

多数決 / 2 of 3 / partial passは認めない。

さらに:

- canonical before / after invariance
- system integrity PASS
- focused grounding regression PASS
- full pytest = 0 failed
- new skip / xfailでfailureを隠さない

を要求する。

N-06領域のRecall@K / MRR / nDCG等はこのGateへ混在させない。

---

## 8. Formal evidence requirement

G-11で具体ファイル名をfreezeするが、v2 specとして最低限次を保存する。

```text
Git head / working tree / environment
generator model/runtime/settings
validator model/runtime/settings if used
MCP request / response
Similarity result for Case 2
Grounded Context / K mapping
context_fingerprint
Attempt 1 generation request
Attempt 1 raw structured output
Attempt 1 validation
Retry feedback if used
Attempt 2 request/output/validation if used
terminal outcome
rendered response if ACCEPTED
case rubric evaluation
canonical before / after
system integrity
focused regression
full pytest result
```

raw artifactsはGitへcommitしなくてよい。

---

## 9. Case-specific freeze summary

### Case 1 — Roleplay

Context:

```text
Saber
purpose=roleplay
max_characters=12000
attributes=true
relations=true
evidence refs=false
```

Formal PASS requires:

- `ACCEPTED`
- supported source facts >= 2
- first-person roleplay
- unsupported / contradictory material source fact = 0
- no fabricated detailed personality/backstory

### Case 2 — Comparison

Source:

```text
Fate/stay night
```

Candidate:

```text
actual current Work top candidate from find_similar_objects
```

Context:

```text
purpose=comparison
max_characters=24000
attributes=true
relations=false
evidence refs=true
```

Formal PASS requires:

- `ACCEPTED`
- grounded fact from each Work >= 1
- comparison / contrast >= 1
- interpretation visibly separated
- interpretation premises grounded
- outside Knowledge facts = 0
- similarity score semantic misuse = 0

### Case 3 — Creative

Context:

```text
Tsundere + Hero's Journey
purpose=creative
max_characters=24000
attributes=true
relations=true
evidence refs=false
```

Formal PASS requires:

- `ACCEPTED`
- grounded source idea from both Concepts
- both Concepts meaningfully integrated
- new Character / setting / event / trait / arc are creative scope
- source Concept unsupported fact = 0

---

## 10. G-09 / G-10 / G-11への引き渡し

### G-09 Implementation

実装はFrozen v2 contractへ従う。

benchmark固有hardcodeでPASSさせない。

### G-10 Automated Test

最低限:

- v2 output contract parse
- K reference integrity
- supported / unsupported / contradictory
- interpretation
- creative separation
- context_limit
- attempt 1 / retry 1
- retry exhausted
- system failure
- deterministic rendering
- canonical non-mutation

をtestする。

### G-11 Formal Harness Freeze

次を具体値へfreezeする。

- actual generator identifier/settings
- actual semantic validator identifier/settings
- exact implementation command / sequence
- exact evidence paths / filenames
- preflight conditions

G-11はrubricやretry semanticsを変更してはならない。

---

## 11. Definition of Done

- [x] v1 Failed baselineを不変保持した。
- [x] `benchmark/n04-ai-use-cases-v2.json`を作成した。
- [x] 同じ3代表caseを継承した。
- [x] v1核心quality Gateを緩和していない。
- [x] G-07 Grounded Context / structured output / Hybrid validation / failure policyをv2へ反映した。
- [x] generator / validator model policyを固定した。
- [x] max generation attempts = 2を固定した。
- [x] retry PASSを認める条件を固定した。
- [x] `INSUFFICIENT_CONTEXT`はsafe outcomeだがCase PASSではないと固定した。
- [x] 3 / 3 Case PASSをOverall PASS条件に固定した。
- [x] formal run開始後のrubric / model / protocol cherry-pickを禁止した。
- [x] G-09〜G-11へ必要な引き渡し事項を定義した。

---

## 12. Next task

次は:

```text
N-04G-09 [P0]
採用したgrounded-generation designを実装する
```

とする。
