# N-04G-15 Output Schema / Presentation / Renderer Hardening

更新日: 2026-10-19

- Status: **Complete**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- G-14: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- Root cause: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- Existing output contract: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- Existing validation design: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- Previous design freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Remediation task master: `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`

---

## 1. Decision

N-04 post-G12 remediationでは、G-04の「structured semantic units + deterministic rendering」という基本方針を維持しつつ、presentation metadataがsemantic validationを迂回できないようoutput contractをhardeningする。

主要Decisionは次である。

1. **model-generated free-form `label`をnormative output contractから削除する。**
2. human-visible heading / separatorは`presentation_role`からSGOKB側が決定論的に生成する。
3. rendererが追加できる文字列はtrusted fixed presentation textだけとし、LLM生成文字列はvalidated `unit.text`以外renderしない。
4. block roleとunit semantic roleの組合せをcontract上で限定する。
5. `support_refs` cardinality / emptinessをsemantic roleごとにcontractへ可能な限りencodeする。
6. v3 formal baselineではG-14に従い`stylistic_expression`をmodel output enumから除外する。
7. `context_limit`は専用presentation blockへ限定し、`creative_addition`は`creative` block、`interpretation`は`interpretation` blockへ限定する。
8. `main` blockはsource-grounded materialのscopeとし、v3 baselineでは原則`source_fact`のみを許可する。
9. presentation separationをfree-form labelの有無で判定しない。**schema shape + trusted renderer heading**で保証する。
10. provider-native structured outputはsyntax / shape constraintとして使用するが、semantic grounding authorityとはしない。
11. providerへ渡すschemaとapplication parserのnormative schemaを同一正本から導出する。
12. providerが完全なJSON Schema subsetを実装していない場合、unsupported featureをsilent downgradeせず、formal runtime preflightで検出する。
13. contract validation errorはJSON path / block / unit / violated ruleを保存可能な形へする。retry feedbackの物理形式はG-19実装時に確定する。
14. G-12 Case 3の`label=null`問題は、v3 contractでは`label` field自体を削除することで再発経路を除去する。

概念フロー:

```text
Untrusted LLM
   ↓
provider structured-output constraint
   ↓
SGOKB output schema validation
   ↓
G-14 atomicity / role-boundary gate
   ↓
semantic grounding validation
   ↓
terminal gate (G-17)
   ↓
trusted deterministic renderer
   ├─ fixed heading from presentation_role
   └─ validated unit.text only
```

本Decisionはproduction codeを変更しない。実装はN-04G-19で行う。

---

## 2. Problem statement

G-12 Case 3では、providerへ渡したJSON Schemaが:

```text
label = string | null
```

を許可していた一方、application parserは`interpretation` / `creative` blockについてnon-empty `label`を要求していた。

そのためmodelはprovider contract上合法な:

```json
{
  "presentation_role": "creative",
  "label": null
}
```

を2 attempt連続で生成し、application側だけがrejectした。

さらにG-13では、`label`自体がsemantic unit validation対象外なのにrendererがその文字列を表示できることを確認した。

つまり旧contractには2問題がある。

```text
provider schema != application parser rule

and

LLM-generated presentation metadata can become user-visible text
without unit-level grounding validation
```

G-15ではpresentation textをmodel controlから外し、schema / parser / rendererの責務を単純化する。

---

## 3. Preserve from G-04

次のG-04原則は維持する。

- LLM normative outputはstructured envelopeのみ。
- separate final proseを生成しない。
- human-facing semantic contentの唯一のsourceはvalidated `unit.text`。
- deterministic rendererを使用する。
- malformed outputをheuristicでsilent repairしない。
- provider-native schema機能は利用可能だがSGOKB logical contractをprovider固有仕様へ従属させない。

変更するのは主に:

- block presentation metadata
- role/block structural constraints
- role別support_refs constraints
- rendererが追加可能なtrusted text

である。

---

## 4. Contract version policy

G-14/G-15でv1の意味境界とshapeが変わるため、v3 acceptanceで使用するlogical output contractは新versionとする。

推奨version:

```text
sgokb.grounded-generation-output.v2
```

理由:

- `label` field削除はbreaking change。
- `stylistic_expression`削除はenum breaking change。
- block/role combination constraint強化は旧v1 outputの一部をinvalidにする。
- interpretation premise contractはG-16で追加変更される可能性がある。

したがってG-15時点では**v2へのrevisionを予約**するが、最終shapeはG-16/G-17を統合するG-18 Design Freezeで確定する。

G-18までは旧`sgokb.grounded-generation-output.v1`を履歴として保持し、silent reinterpretationしない。

---

## 5. v3 baseline presentation roles

presentation scopeは次を維持する。

```text
main
interpretation
creative
context_limit
```

ただしfree-form `label`は持たない。

### `main`

source-grounded main response scope。

v3 baselineでは原則:

```text
source_fact
```

のみを含む。

G-14でmodel-authored `stylistic_expression`は禁止したため、Roleplayのsurface styleは`source_fact.text`自体のfirst-person paraphrase等で表現する。

### `interpretation`

`interpretation` unit専用scope。

Rendererはtrusted fixed headingを付与する。

### `creative`

`creative_addition` unit専用scope。

Rendererはtrusted fixed headingを付与する。

### `context_limit`

`context_limit` unit専用scope。

Rendererはtrusted fixed headingを付与する。

---

## 6. Model-generated `label` removal

### Decision

`label`をmodel output contractから削除する。

旧:

```json
{
  "block_id": "B2",
  "presentation_role": "creative",
  "label": "Creative addition",
  "units": [...]
}
```

新:

```json
{
  "block_id": "B2",
  "presentation_role": "creative",
  "units": [...]
}
```

visible headingはrendererが:

```text
presentation_role -> trusted label table
```

から生成する。

### Rationale

free-form model labelにはgrounding上の価値がない。

一方で次のriskがある。

- `label=null` schema/parser mismatch
- misleading heading
- material sentence injection
- validation bypass
- localization責務のmodel側流出

これらを全て削除できるため、field自体を廃止する。

---

## 7. Deterministic trusted heading table

v3 baselineの標準headingはSGOKB側trusted tableで管理する。

例:

```text
interpretation -> "Interpretation"
creative       -> "Creative addition"
context_limit  -> "Context limit"
main           -> no heading
```

重要:

- heading textはLLM outputではない。
- headingはsemantic claimとして扱わないfixed UI/presentation textである。
- localized UIが必要ならrenderer/application側のtrusted localization tableを使う。
- modelがheading文字列を指定・overrideできない。

---

## 8. Renderer invariant

G-15で次をnormative invariantとする。

```text
rendered semantic content
  = successfully validated unit.text
  + SGOKB-controlled fixed presentation tokens only
```

SGOKB-controlled fixed presentation tokensとは最低限:

- fixed heading
- newline
- separator
- deterministic whitespace

だけである。

Rendererは禁止:

- unit textのparaphrase
- summary追加
- free-form model label表示
- model metadataの任意表示
- hidden note / rationaleの表示
- validation failure detailの通常response本文への自動混入

Rendererはvalidated `unit.text`の順序を保持し、意味内容を書き換えない。

Terminal outcomeとのbindingはG-17で確定する。

---

## 9. Block-role structural matrix

v3 baselineではblock roleとsemantic roleを可能な限り構造的に限定する。

```text
presentation_role = main
  -> source_fact

presentation_role = interpretation
  -> interpretation

presentation_role = creative
  -> creative_addition

presentation_role = context_limit
  -> context_limit
```

これにより次を禁止する。

```text
creative block + source_fact
main block + creative_addition
context_limit block + source_fact
interpretation block + creative_addition
```

G-14 content-first role validationは引き続き必要であり、このmatrixだけをsemantic proofとはしない。

ただし、generatorが明示的に不整合なrole pairを出した場合はV0/V2前段でdeterministicにrejectできる。

---

## 10. Role-specific `support_refs` constraints

v3 baselineではschemaで可能な範囲まで次をencodeする。

```text
source_fact:
  support_refs minItems >= 1

interpretation:
  G-16でpremise reference contractを確定
  旧K support_refsのまま残すかはG-16で決める

creative_addition:
  support_refs = []

context_limit:
  support_refs = []
```

`stylistic_expression`はv3 baseline enumから削除する。

重要:

schemaで`support_refs >= 1`を保証しても、引用したKがclaimをsupportすることまでは証明しない。

したがって:

```text
schema constraint = structural necessity
semantic verifier = support sufficiency
```

の責務分離を維持する。

---

## 11. Schema shape strategy

### Candidate A — generic block + generic unit + conditional schema

`if/then`, `oneOf`等でrole combinationを制約する。

利点:

- logical modelがcompact。
- Python jsonschemaでは表現しやすい。

欠点:

- provider structured-output implementationが高度なconditional schema subsetを完全supportする保証がない。
- runtime incompatibilityがG-12 Case 3と同型のprovider/application mismatchを再発させ得る。

### Candidate B — role-specific block schemas

例:

```text
main_block
interpretation_block
creative_block
context_limit_block
```

各blockの`presentation_role`を`const`で固定し、units側のsemantic roleも対応roleへ固定する。

利点:

- conditional semantic relationをshapeそのものへ落とせる。
- provider側で解釈しやすい。
- parserとの一貫性を作りやすい。
- failure pathが明確。

欠点:

- schemaが冗長になる。
- G-16 interpretation premise field追加時に専用schema更新が必要。

### Decision

**Candidate Bをv3 baselineの第一候補とする。**

ただし実runtimeのLM Studio structured-output subsetで`oneOf`等が必要になる場合はpreflightで確認する。

最終JSON SchemaはG-18でfreezeし、G-19で実装する。

---

## 12. Provider schema / application schema single source of truth

旧実装では同じPython moduleにschema自体は存在したが、parserがschema外追加ruleを持ち、実質的に二重contractになった。

v3では次を禁止する。

```text
provider schema allows X
but
parser silently has a stricter undocumented rule Y
```

Normative rule:

1. structural requirementはcanonical logical schemaへencodeする。
2. providerへ渡すschemaはそのcanonical schemaから導出する。
3. application parserも同じcanonical schemaを使用する。
4. semantic / cross-unit ruleでschema表現困難なものは、schemaとは別のnamed validation stageとして明示する。
5. parser-local hidden ruleを作らない。

これにより「schemaでは合法、parserでは違法」を回避する。

---

## 13. Provider capability preflight

Structured output providerがJSON Schema Draft 2020-12全体をsupportすると仮定しない。

formal v3 runtimeでは、acceptance前に使用schemaがproviderで正しくconstraintされることをpreflightする。

最低確認:

- required
- additionalProperties=false
- enum / const
- array minItems / maxItems相当
- string pattern
- nested object / array
- role-specific branch structureに必要なschema feature

providerが必要featureをsupportしない場合:

- silentにconstraintを削らない。
- contract shapeをprovider-compatibleなより単純な形へ変更するか、provider-native constraintを補助扱いにしてapplication V0でfail-closedにする。
- formal harnessには実際にproviderへ渡したschema identity/hashを保存する方向とする。

このpreflightの実装/acceptance固定はG-19〜G-21で扱う。

---

## 14. Contract error reporting requirement

G-13で、schema ValidationErrorが持つpath/detailがretry feedbackまで保持されない問題を確認した。

G-15ではpresentation/schema failureについて最低限次を保持できる設計を要求する。

```text
failure_code
json_path
block_id (if known)
unit_id (if known)
failure_detail
expected_rule
```

例:

```text
failure_code: invalid_block_role_pair
json_path: blocks[1].units[0].semantic_role
block_id: B2
unit_id: U3
expected_rule: creative block may contain creative_addition only
```

G-12 Case 3型のrepair不能retryを減らすため、retry feedbackは「何が違反か」だけでなく「どのpathをどう直すか」を保持する。

物理data class / failure schemaはG-19実装時に確定する。

---

## 15. G-14 interaction

G-15のstructural schemaはG-14 semantic boundaryを補助するが、代替しない。

例えば:

```json
{
  "presentation_role": "creative",
  "units": [
    {
      "semantic_role": "creative_addition",
      "text": "Tsundere is historically defined as ...",
      "support_refs": []
    }
  ]
}
```

はshape上はcreative block / creative_additionで整合していても、内容はsource Concept factである。

したがってG-14 content-first role gateで`ROLE_BOUNDARY_VIOLATION`になる。

責務:

```text
G-15 schema
  -> declared structural consistency

G-14 role boundary gate
  -> actual content semantic consistency
```

---

## 16. G-12 Case 3 desk replay

Observed shape:

```text
presentation_role = creative
label = null
```

旧provider schema:

```text
label: string | null
```

旧application parser:

```text
creative -> non-empty label required
```

結果:

```text
provider accepts
application rejects
retry uses same provider schema
same failure repeats
```

### v3 design

`label` fieldをcontractから削除する。

```json
{
  "presentation_role": "creative",
  "units": [...]
}
```

Rendererはtrusted tableから:

```text
Creative addition
```

を付与する。

したがって:

```text
label=null
missing label
malicious free-form label
```

というfailure class自体がgeneration contractから消える。

Case 3のpresentation separationは、creative block shape + deterministic headingで成立する。

---

## 17. Label injection desk replay

仮に旧contractでmodelが:

```json
{
  "presentation_role": "creative",
  "label": "Canonical fact: Saber won the war",
  "units": [
    {
      "semantic_role": "creative_addition",
      "text": "A new character named X is created.",
      "support_refs": []
    }
  ]
}
```

を返した場合、旧rendererではlabelがuser-visibleになり得る。

v3では`label` fieldが存在しないためV0 contract violationとなり、rendererへ到達しない。

仮にunknown fieldを追加しても`additionalProperties=false`でrejectする。

これにより:

```text
all LLM-authored visible semantic text
  -> unit.text
  -> validation target
```

を維持できる。

---

## 18. Rendering examples

### Roleplay / main

Structured:

```json
{
  "presentation_role": "main",
  "units": [
    {
      "semantic_role": "source_fact",
      "text": "I am Saber, also known as Artoria Pendragon.",
      "support_refs": ["K1"]
    }
  ]
}
```

Rendered:

```text
I am Saber, also known as Artoria Pendragon.
```

### Comparison interpretation

Structured conceptually:

```json
{
  "presentation_role": "interpretation",
  "units": [
    {
      "semantic_role": "interpretation",
      "text": "This creates a contrast in how the two works frame conflict."
    }
  ]
}
```

Rendered:

```text
Interpretation
This creates a contrast in how the two works frame conflict.
```

Premise reference fields are deferred to G-16.

### Creative

Structured:

```json
{
  "presentation_role": "creative",
  "units": [
    {
      "semantic_role": "creative_addition",
      "text": "The new character begins as an aloof rival who gradually accepts help.",
      "support_refs": []
    }
  ]
}
```

Rendered:

```text
Creative addition
The new character begins as an aloof rival who gradually accepts help.
```

---

## 19. Explicit non-decisions / handoff

### G-16へ送る

- interpretationの`premise_unit_ids`等の物理field
- source-fact verifier architecture
- semantic validator disagreement policy
- interpretation derivation judge
- atomicity classifierのsemantic component

### G-17へ送る

- validation PASSとterminal ACCEPTEDの関係
- materially sufficient response判定
- rendererのterminal decision binding
- INSUFFICIENT_CONTEXTのsafe render path

### G-18へ送る

- logical contract version最終確定
- complete JSON Schema freeze
- G-14〜G-17統合後のfield set

### G-19へ送る

- production schema/parser/renderer実装
- failure detail/path保持
- provider preflight実装

---

## 20. Impact on existing decisions

### G-04

基本方式は維持するが、次をsupersedeする。

- model-generated `label`
- `stylistic_expression`をv3 output roleとして許可する部分
- free-form labelによるpresentation separation

### G-05

validation semanticsは維持するが、schemaでdeterministically閉じられるrole/block mismatchを前段化する。

### G-07

旧v1 design freezeはv1/v2 formal historyとして保持する。

G-14〜G-17完了後、G-18でpost-G12 designを明示的に再freezeする。

---

## 21. Completion check

N-04G-15のcompletion conditionを次の通り満たした。

- [x] G-12 Case 3 `label=null` failureをcontract-levelで除去する設計を確定した。
- [x] model-generated arbitrary labelをuser-visible semantic contentへ到達させない設計を確定した。
- [x] schema / parser / rendererのstructural ruleを単一正本から導出する原則を確定した。
- [x] deterministic trusted heading / separatorだけをrenderer追加textとして許可した。
- [x] block role / unit semantic role matrixを定義した。
- [x] role別`support_refs` structural constraint方針を定義した。
- [x] provider structured-output capability preflight要件を定義した。
- [x] schema errorのpath/detail保持要件を定義した。
- [x] G-14 content-first semantic boundaryとの責務分離を定義した。
- [x] production codeを変更していない。

N-04G-15を**Complete**とする。

次Task:

```text
N-04G-16 [P0]
Semantic validation architecture redesign
```
