# N-04G-05 Grounding Validation Design

更新日: 2026-10-18

- Status: **Accepted**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-05 [P0] grounding validation方式を設計する`
- Responsibility Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- Claim Taxonomy Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- Grounding Reference Decision: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- Generation / Output Contract: `N-04G-04` — Pending at this Decision time
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 grounded-generationのvalidation方式として、**deterministic validation + bounded semantic validationのHybrid方式**を採用する。

基本原則:

1. **LLM出力を無条件に信用しない。**
2. **構造・reference・taxonomy policyは可能な限りdeterministicに検査する。**
3. **自然言語paraphrase / interpretation等、意味理解が必要な部分だけsemantic validatorへ委ねる。**
4. **same-model self-checkだけを最終grounding Gateにしない。**
5. **semantic validatorも権威ではなく、限定された入力に対する判定器として扱う。**
6. **`unsupported` / `contradictory` / `separation_violation`を明確なvalidation failureとして扱う。**
7. **判定不能はPASSへ倒さない。** `indeterminate`として保持し、`SGOKB-grounded`認定はfail-closedとする。
8. **G-04未完了でもvalidation semanticsは固定する。** G-04は本Decisionが要求するmachine-addressable validation unitを生成可能なoutput contractにする必要がある。

採用フロー:

```text
LLM raw output
    ↓
V0 Contract / parse validation
    ↓
V1 Reference integrity validation
    ↓
V2 Taxonomy / use-case policy validation
    ↓
V3 Deterministic support validation
    ↓ unresolved only
V4 Bounded semantic support validation
    ↓
V5 Aggregate verdict
    ↓
PASS / FAIL / INDETERMINATE
```

Validation結果に基づくRetry / Reject / Insufficient等のworkflow actionはN-04G-06で決める。

---

## 2. なぜHybrid方式か

N-04では次を同時に扱う必要がある。

- direct source fact
- faithful paraphrase
- comparison上のinterpretation
- creative addition
- roleplay style
- context limit

このため、1つのvalidation方式だけでは不足する。

### deterministic-onlyの限界

文字列一致だけでは、例えば次を同義と判定しにくい。

```text
Context: Saber is contracted to Shirou.
Output: I have a contract with Shirou.
```

またComparisonの`interpretation`は、複数premiseからの推論妥当性を確認する必要がある。

### LLM-onlyの限界

LLM validatorだけへ任せると、

- model memory混入
- false positive / false negative
- generatorと同じ誤認
- invalid referenceを見逃す
- schema / namespace違反を曖昧に処理する

危険がある。

したがって、機械的に確定できるものは先にdeterministicに閉じ、意味判定が必要な残差だけをsemantic validationへ渡す。

---

## 3. 比較した方式

### Option A — schema validationのみ

**不採用。**

JSON等が正しい形でも、claim内容がContext外であればgrounding failureを検出できない。

### Option B — `K*` reference presenceのみ

**不採用。**

`K2`を付けながら無関係な事実を書くことが可能である。

```text
K2 = Saber is contracted to Shirou.
claim = Saber secretly rules the world. [K2]
```

reference存在はtraceabilityでありproofではない。

### Option C — exact / normalized matchのみ

**単独方式として不採用。**

明確なdirect matchには有効だが、自然なparaphraseやinterpretationを過剰にrejectする。

### Option D — generatorと同じLLMによるself-check

**最終Gateとして不採用。**

N-04 v1でgenerator自身がinstruction-followingを破った以上、その同一modelの自己申告だけでgroundingを保証しない。

同一modelによるsecond passはdebug / advisory用途には使えるが、唯一のsemantic PASS根拠にはしない。

### Option E — 別local LLM judgeのみ

**単独方式として不採用。**

独立modelでもhallucination /誤判定はあり、reference integrity等をLLMへ任せる必要はない。

### Option F — Hybrid validator

**採用。**

- deterministicな違反はdeterministicに検出
- 意味判定だけsemantic validator
- unresolvedを明示
- claim単位のevidenceを保存可能

という構造が、N-04 failureと既存SGOKB責務境界に最も適合する。

---

## 4. Validator input boundary

Validatorの論理入力は最低限次とする。

```text
grounded_context
  contract_version
  context_fingerprint
  grounding_units[K*]

validation_units[]
  unit_id
  text / semantic content
  declared_semantic_role
  support_refs[]
  presentation_scope / separation metadata

use_case
  roleplay | comparison | creative
```

`validation_units[]`の物理形式はN-04G-04で決める。

ただしG-05からG-04へ次を必須要求する。

> **最終出力は、validatorがmachine-addressableなatomic semantic unitとして列挙または復元できるcontractでなければならない。**

Validatorが最終proseだけから全atomic claimを自由推測する方式をnormative baselineにはしない。

理由:

- claim抽出自体が別のLLM推論になる
- claim omissionを検出しにくい
- role / support referenceとの対応が曖昧になる

G-04でhuman-readable final responseとvalidation unitを分離するか同居させるかは未決だが、validation unitへの確実なmappingは必要である。

---

## 5. Validation stages

## V0 — Contract / Parse Validation

目的:

- output contractが解釈可能か確認する。

検査例:

- contract version
- required field presence
- unit ID uniqueness
- semantic role enum
- support reference syntax
- final responseとvalidation metadataの必要な対応

failure例:

```text
malformed_output
unknown_contract_version
missing_required_field
duplicate_unit_id
invalid_semantic_role
```

これはdeterministicに判定する。

---

## V1 — Reference Integrity Validation

N-04G-03の`context_fingerprint + K*`を検査する。

必須検査:

- `context_fingerprint`一致
- support refが現在Contextに存在する
- ref ID重複 / unknown refなし
- refが同じresolved Version namespaceにbindされている
- 別Context由来`K*`の流用なし
- canonical mappingが完全である

failure例:

```text
context_fingerprint_mismatch
unknown_grounding_reference
cross_context_reference
broken_canonical_mapping
```

これはdeterministic hard failureとする。

---

## V2 — Taxonomy / Use-case Policy Validation

N-04G-02のSemantic Role / Grounding Disposition境界を適用する。

### `source_fact`

原則、1個以上のsupport refを要求する。

support refなしの場合:

```text
missing_required_support
```

### `interpretation`

material premiseとなるsupport refを要求する。

また、stored factと区別できるpresentation / metadataが必要である。

### `creative_addition`

source factual supportを必須にしない。

ただしsource Concept / Objectの既存factであるかのように提示してはならない。

### `stylistic_expression`

support不要。

ただしmaterial source-world propositionを含む場合、styleへ逃がさず`source_fact`または`interpretation`として再評価対象にする。

### `context_limit`

support不要。

ただしsource-world factを同時に埋め込まない。

use-case policy violation例:

```text
missing_required_support
role_policy_violation
separation_violation
creative_scope_violation
```

一部はdeterministic、一部はV4 semantic validationで補完する。

---

## V3 — Deterministic Support Validation

semantic modelなしで安全に確定できるsupportだけを判定する。

対象例:

### exact / normalized statement match

- whitespace / punctuation / case等の安全なnormalization
- 意味を変えない既知wrapper除去

### Attribute

claim metadataがstructured attribute valueを直接参照し、値一致を確認できる場合。

### Relation

subject / relation / objectが明示構造として一致する場合。

### Object field

name / alias / class等が直接一致する場合。

結果:

```text
deterministic_supported
deterministic_contradictory
unresolved
```

V3では意味拡張をしない。

例えば、

```text
K4 = Saber is contracted to Shirou.
```

から、

```text
Saber deeply trusts Shirou.
```

をdeterministicにsupport扱いしない。

---

## V4 — Bounded Semantic Support Validation

V3で`unresolved`となったunitだけをsemantic validatorへ渡す。

### 5.4.1 入力制限

semantic validatorへ渡すのは原則として次だけとする。

```text
claim / validation unit
semantic role
cited K* unit content
必要最小限のtaxonomy rule
use-case rule
```

原則として渡さないもの:

- Web
- external retrieval
- canonical Context外Knowledge
- generator conversation全文
- franchise全体の追加情報

目的は「このclaimがcited Contextでsupportされるか」を判定することであり、世界知識として真かどうかを判定することではない。

### 5.4.2 Semantic verdict

semantic validatorは最低限次を返す。

```text
entailed
reasonable_derivation
unsupported
contradictory
role_mismatch
indeterminate
```

意味:

- `entailed`: source_factがcited Knowledgeで十分supportされる
- `reasonable_derivation`: interpretationがcited supported premiseから合理的に導ける
- `unsupported`: cited Knowledgeではmaterial claimをsupportできない
- `contradictory`: cited Knowledgeと矛盾
- `role_mismatch`: declared roleが実際のsemantic contentと不整合
- `indeterminate`: 判定不能

### 5.4.3 Validator model independence

SGOKB contractは特定validator model名を固定しない。

ただしformal N-04 acceptanceでは、validator runtime / model / settingsを事前freezeし、caseごとにcherry-pickしない。

### 5.4.4 Same-model self-check policy

**Generator自身による「このclaimはgroundedです」という自己判定だけではPASSにしない。**

同一base modelを別passで使う場合も、その結果を唯一のsemantic authorityにはしない。

正式なsemantic GateとしてLLM judgeを使う場合は、原則としてgeneratorから独立した固定local validatorを使用する。

独立validatorが利用できない場合、semantic-only claimは`indeterminate`へ落とし、formal acceptanceでは人手 / CodexによるContext照合を最終evidenceに残す。

このfallbackは「manual reviewを恒久production requirementにする」と決めるものではない。N-04 formal acceptanceの評価証跡上、validatorの限界を隠さないためである。

---

## V5 — Aggregate Verdict

claim単位の結果をoutput全体へ集約する。

### PASS

最低条件:

- V0 / V1 hard failureなし
- `source_fact`が`supported`
- `interpretation`が`derived_supported`
- `creative_addition` / `stylistic_expression` / `context_limit`が用途境界内
- `contradictory`なし
- `separation_violation`なし
- unresolved material claimなし

### FAIL

いずれか:

```text
unsupported material source_fact
contradictory claim
unsupported interpretation
invalid / foreign reference
role policy violation
separation_violation
creative_scope_violation
```

### INDETERMINATE

例:

- semantic validatorが判定不能
- validator runtime unavailable
- ambiguous atomic unitで安全に分解できない
- support sufficiencyを確定できない

**INDETERMINATEをPASSへ昇格しない。**

`SGOKB-grounded`認定についてはfail-closedとする。

この後のworkflow actionはG-06で決める。

---

## 6. Semantic Role別のvalidation rule

## 6.1 `source_fact`

必要条件:

```text
valid support ref >= 1
AND
claim is entailed by cited units
AND
no material proposition remains unsupported
```

1文に複数factが含まれる場合、atomic unitへ分割して全material propositionを検証する。

有効なKを1つ付けても、追加のunsupported detailが含まれればFAIL。

---

## 6.2 `interpretation`

二段階で確認する。

1. premise support
2. derivation support

```text
all material premises supported
AND
conclusion is reasonable derivation
AND
no external factual premise
AND
stored factとのseparationが明確
```

このどれかを欠く場合、`derived_supported`にしない。

特にComparisonでは、

> 「interpretation」とラベルしただけで外部knowledgeを持ち込むことを禁止する。

---

## 6.3 `creative_addition`

creative detail自体のfactual entailmentは要求しない。

主に確認するのは:

- creative scope内か
- source Object / Conceptのfactとして偽装していないか
- source Conceptについてunsupported説明を付加していないか

新規Character / event / settingの内容がContextに無いこと自体はFAILではない。

---

## 6.4 `stylistic_expression`

material propositionを含まない限り`not_applicable`。

例えば、

```text
Very well.
```

はvalidation対象外に近い。

しかし、

```text
I have always protected Shirou because of my hidden past.
```

はstyleではなくmaterial source-world claimを含むため、`source_fact`へ再分類しsupportを要求する。

---

## 6.5 `context_limit`

「今回供給されたContextでは確認できない」というmeta statementとして扱う。

Context不足を安全に表明するための正常classであり、原則PASS可能。

ただし、

```text
The context does not say this, but canonically Saber ...
```

のように続けてexternal factを補完する場合、そのexternal partは別atomic unitとして`source_fact / unsupported`になる。

---

## 7. Failure classes

Validatorで最低限次を区別する。

```text
VALIDATION_CONTRACT_ERROR
REFERENCE_INTEGRITY_ERROR
MISSING_REQUIRED_SUPPORT
UNSUPPORTED_CLAIM
CONTRADICTORY_CLAIM
ROLE_MISMATCH
SEPARATION_VIOLATION
CREATIVE_SCOPE_VIOLATION
SEMANTIC_INDETERMINATE
VALIDATOR_UNAVAILABLE
```

N-04G-06で各failure classに対するRetry / Reject / Insufficient等のactionを割り当てる。

---

## 8. Validator result contract

概念結果:

```json
{
  "validation_contract_version": "sgokb.grounding-validation.v1",
  "context_fingerprint": "...",
  "overall_verdict": "pass | fail | indeterminate",
  "units": [
    {
      "unit_id": "C1",
      "semantic_role": "source_fact",
      "support_refs": ["K2"],
      "deterministic_verdict": "unresolved",
      "semantic_verdict": "entailed",
      "final_disposition": "supported",
      "failures": []
    }
  ],
  "failures": [],
  "validator_metadata": {}
}
```

正確なJSON SchemaはG-04 / G-07 / G-09で物理実装へ落とす。

重要なのは、最終overall verdictだけでなく、**各atomic unitがなぜPASS / FAILしたか追跡できること**である。

---

## 9. Case 1〜3 failureへの適用

### Case 1 — Saber Roleplay

Context外の、

- Holy Grail WarでShirouのprotectorとして戦う
- Artoriaの秘密設定

は`source_fact`として検出され、対応Kがなければ`MISSING_REQUIRED_SUPPORT`または`UNSUPPORTED_CLAIM`になる。

LLMが無関係なKを付けてもV4で`unsupported`となる。

したがってv1 critical failureを検出可能である。

### Case 2 — Comparison

Context外のFate / BLEACH設定は`source_fact / unsupported`としてFAIL。

「両protagonistがextraordinary powersを得る」のような比較は、material premiseのK supportがなければ`interpretation / unsupported`となる。

正しいgrounded comparisonでもstored factとの分離がなければ`SEPARATION_VIOLATION`になる。

### Case 3 — Creative

新規Character / event自体は`creative_addition`としてfactual supportを要求しない。

Arc outlineがcreative scopeとして一意に分離されていればPASS可能。

source Concept説明と新規eventを未区分で混ぜる場合のみ`SEPARATION_VIOLATION`または`CREATIVE_SCOPE_VIOLATION`になる。

したがって創作内容そのものをhallucinationと誤検出しない。

---

## 10. Fail-open / Fail-closed policy

Grounding certificationについては**fail-closed**を採用する。

```text
PASS           -> SGOKB-grounded認定候補
FAIL           -> 認定不可
INDETERMINATE  -> 認定不可
```

ただし、これは「失敗時に即ユーザーへ何も返さない」と決めるものではない。

- retry
- partial result
- context_limit
- reject
- human review

等のworkflow behaviorはN-04G-06で決める。

G-05が固定するのは、**不明なものをgroundedと誤認しない**ことだけである。

---

## 11. Architecture responsibility

N-04G-01に従う。

### SGOKB Application / Grounding Contract Layer

Owner:

- validation semantics
- failure classes
- result contract
- deterministic validation rules
- semantic validator input/output contract

### MCP

- validation capabilityを将来公開する場合もtransport adapterのみ
-独自validation semanticsを持たない

### Consumer

- validatorをinvoke
- verdictを保持
- G-06 failure handlingを適用
- raw outputをvalidation前に`SGOKB-grounded`として扱わない

### LLM generator

- validation authorityではない

### Semantic validator

- bounded judge
- canonical truth ownerではない
- external knowledgeをgrounding根拠に使わない

---

## 12. N-04G-04への要求

本TaskはG-04より先に実施したため、次をG-04の必須入力条件として返す。

G-04 output contractは最低限:

1. validation対象のatomic semantic unitをmachine-addressableにできる。
2. 各unitのdeclared semantic roleを識別できる。
3. `source_fact` / `interpretation`についてsupport `K*`を対応付けられる。
4. creative scope / interpretation scopeをseparation判定できる。
5. human-readable final responseとvalidation metadataの対応を失わない。
6. malformed / missing metadataをV0でdeterministicにrejectできる。

G-04が別方式を採用する場合でも、このvalidation requirementを満たす必要がある。

---

## 13. Canonical / Retrieval impact

変更不要:

- canonical schema
- canonical 52 tables
- Statement / Attribute / Relation model
- Evidence / Provenance
- Retrieval ranking
- Similarity semantics
- current / historical Version semantics

Validationはgeneration consumer boundaryの追加capabilityであり、N-06領域のretrieval quality tuningを行わない。

---

## 14. Definition of Done

- [x] validation方式をHybrid方式に確定した。
- [x] deterministic stageとsemantic stageの境界を定義した。
- [x] unsupported claim detection方法を定義した。
- [x] interpretationのpremise / derivation validationを定義した。
- [x] creative additionを誤ってhallucination扱いしないruleを定義した。
- [x] same-model self-checkを唯一の最終Gateとして不採用にした。
- [x] validator自身の不確実性を`indeterminate`として表現した。
- [x] fail-closed grounding certificationを確定した。
- [x] failure classesを定義した。
- [x] validation result contractの概念形を定義した。
- [x] N-04 v1 Case 1〜3のfailureを検出または正しく許容できる理由を示した。
- [x] G-04へ必要なoutput contract要件をフィードバックした。
- [x] canonical / Retrieval変更不要を明記した。

N-04G-05をCompleteとする。
