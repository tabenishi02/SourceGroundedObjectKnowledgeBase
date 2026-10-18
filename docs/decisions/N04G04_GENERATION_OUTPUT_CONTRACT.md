# N-04G-04 Generation / Output Contract

更新日: 2026-10-18

- Status: **Accepted**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-04 [P0] generation / output contractを設計する`
- Responsibility Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- Claim Taxonomy Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- Grounding Reference Decision: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- Validation Decision: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 grounded-generationのgeneration / output contractとして、**single-pass structured semantic units + deterministic rendering**方式を採用する。

LLMは人間向け最終文章と検証用claim一覧を別々に生成しない。

LLMが生成するnormative outputは、atomic semantic unitを持つstructured envelopeだけとする。

Consumerはそのstructured envelopeをvalidationへ渡し、PASSしたunitだけを同じ順序・scopeで決定論的にrenderしてhuman-readable responseを得る。

概念フロー:

```text
Grounded Context
  ├─ context_fingerprint
  └─ K1 / K2 / ...
        ↓
Consumer builds generation request
        ↓
LLM
        ↓
sgokb.grounded-generation-output.v1
  ├─ context_fingerprint
  ├─ purpose
  └─ blocks[]
       └─ units[]
            ├─ unit_id
            ├─ semantic_role
            ├─ text
            └─ support_refs[]
        ↓
N-04G-05 Validator
        ↓
validated semantic units
        ↓
Deterministic Renderer
        ↓
Human-readable response
```

主なDecision:

1. output contract名を`sgokb.grounded-generation-output.v1`とする。
2. LLM outputはmachine-readable structured envelopeをnormative形式とする。
3. atomic semantic unitを`units[]`として明示する。
4. 各unitはN-04G-02の`semantic_role`を宣言する。
5. `source_fact` / `interpretation`はN-04G-03の`K*`を`support_refs[]`で宣言する。
6. N-04G-02のGrounding Disposition（`supported`等）はLLMに自己申告させず、N-04G-05 validatorが決定する。
7. human-facing final textをLLMに別fieldで再生成させない。表示文はvalidated `units[].text`からdeterministically renderする。
8. Comparisonのinterpretation、Creativeのcreative additionはvisible scope separationを持つblockへ分ける。
9. provider-native JSON Schema / structured output機能は利用可能なら使用してよいが、SGOKB contract自体は特定provider機能へ依存しない。
10. malformed / unparsable / contract-nonconformant outputを自然言語heuristicでsilent repairしない。V0 validation failureとして扱う。
11. 2-stage LLM generationはbaselineとして採用しない。第2段LLM rendererが新しいunsupported contentを追加する経路を増やすためである。
12. canonical Knowledge / Context Builder / MCP schemaの変更は本Taskでは不要とする。

---

## 2. 解決したい問題

N-04G-05はoutput contractへ次を要求している。

- validatorがatomic semantic unitをmachine-addressableに取得できる。
- 各unitのsemantic roleを取得できる。
- `source_fact / interpretation`と`K*`を対応付けられる。
- creative / interpretation scopeを判定できる。
- human-readable responseとvalidation metadataの対応を失わない。

特に最後の点が重要である。

次の方式は採用しない。

```text
LLM output A = 検証用claim一覧
LLM output B = ユーザー向け最終文章
```

Aが正しくてもBへ新しいfactが追加される可能性があり、Bを再度claim extractionする必要が生じる。

そのため、**検証対象unitそのものを最終表示の唯一のcontent sourceにする**。

---

## 3. 比較した方式

### Option A — Natural language responseのみ

例:

```text
I am Saber, also known as Artoria Pendragon...
```

#### 利点

- modelへの要求が最も単純。
- Roleplay / Creativeの文章自由度が高い。
- provider差が小さい。

#### 欠点

- atomic claim抽出を後段で再推論する必要がある。
- semantic roleを確実に識別できない。
- `K*`との対応が曖昧。
- creative / interpretation separationを機械的に検証しにくい。
- G-05 V0〜V2のdeterministic validationを十分活用できない。

#### Decision

**不採用。**

N-04 v1に近く、G-05のmachine-addressable requirementを満たさない。

---

### Option B — Inline citation付きnatural language

例:

```text
I am Saber [K1], contracted to Shirou [K2].
```

#### 利点

- Contextとの対応が人間にも分かりやすい。
- plain textのままreferenceを付けられる。

#### 欠点

- 1文に複数claimが混在する場合のscopeが曖昧。
- citationの直前だけをsupportするのか文全体か不明確になり得る。
- semantic roleが取れない。
- creative / interpretation separationを十分表現できない。
- user-facing Roleplayへ`[K2]`等が露出し、可読性を損ねる。

#### Decision

**単独方式として不採用。**

`K*`はmachine metadataとして保持し、通常のhuman-facing responseへ直接表示しない。

---

### Option C — Structured claim metadata + 別final response

概念:

```json
{
  "claims": [...],
  "final_response": "..."
}
```

#### 利点

- validation metadataを機械処理できる。
- final responseは自由な文章にできる。

#### 欠点

- `claims[]`と`final_response`が意味的に一致する保証がない。
- final responseだけにunsupported detailが混入できる。
- validatorが再度final responseをclaim extractionする必要がある。
- 二重表現の同期問題が生じる。

#### Decision

**不採用。**

validation対象と表示対象を別生成物にしない。

---

### Option D — 2-stage LLM generation

例:

```text
Stage 1: structured grounded plan / claims
Stage 2: LLMがnatural proseへrender
```

#### 利点

- Stage 1でgroundingを強く制御できる。
- Stage 2でRoleplay / Creative品質を高めやすい。

#### 欠点

- Stage 2が新しいfactを追加できる。
- Stage 2後に再validationが必要。
- latency / runtime / failure pointが増える。
- local modelを2回呼ぶためN-04 formal runの複雑性が増える。
- renderer用model選択という別のmodel policyが発生する。

#### Decision

**baselineとして不採用。**

将来、文体品質のために採用する場合はStage 2 outputも再度同じgrounding Gateへ通す必要がある。N-04 remediationでは不要な複雑性を持ち込まない。

---

### Option E — Structured semantic units + deterministic rendering

#### 利点

- validation対象と表示対象が同じcontentになる。
- atomic unit / semantic role / support refsを直接取得できる。
- LLMが別final responseでfactを追加する経路をなくせる。
- `K*`をuser-visible textから分離できる。
- Roleplay / Creativeの実際の文章は`unit.text`として自然言語のまま保持できる。
- rendererはLLM不要で再現可能。
- provider / modelに依存しないschema contractにできる。

#### 欠点

- LLMへJSON等の構造出力を要求する必要がある。
- 小型modelではmalformed output率が上がる可能性がある。
- atomic unitへ分割しすぎると文章の流れを損なう可能性がある。
- deterministic rendererのseparator / heading ruleを固定する必要がある。

#### Decision

**採用。**

欠点はG-05のV0 failureとして観測可能であり、grounding traceabilityを失う方式より安全である。

---

## 4. Contract boundary

契約名:

```text
sgokb.grounded-generation-output.v1
```

これはLLM provider固有のAPI response schemaではなく、**SGOKB grounded-generation consumerがLLMから受け取るべきlogical output contract**である。

ProviderがJSON Schema constrained decodingを提供する場合は利用してよい。

提供しない場合でも、promptで同じJSON形を要求し、V0でparse / schema validationする。

したがって、次に依存しない。

- OpenAI Structured Outputs
- LM Studio固有API
- llama.cpp grammar
- 特定model family

---

## 5. Normative output shape

概念schema:

```json
{
  "contract_version": "sgokb.grounded-generation-output.v1",
  "context_fingerprint": "...",
  "purpose": "roleplay",
  "blocks": [
    {
      "block_id": "B1",
      "presentation_role": "main",
      "label": null,
      "units": [
        {
          "unit_id": "U1",
          "semantic_role": "source_fact",
          "text": "I am Saber, also known as Artoria Pendragon.",
          "support_refs": ["K1"]
        }
      ]
    }
  ]
}
```

正確なJSON SchemaはN-04G-09実装時にこのDecisionへ従って作成する。

---

## 6. Top-level fields

### `contract_version`

必須。

```text
sgokb.grounded-generation-output.v1
```

unknown versionをsilent acceptしない。

### `context_fingerprint`

必須。

N-04G-03 `sgokb.grounded-context.v1`のfingerprintと完全一致する必要がある。

LLMが別Contextの`K*`を引用することを防ぐnamespace bindingとして使用する。

### `purpose`

必須。

```text
roleplay
comparison
creative
```

N-04のformal 3 caseでは上記のみを使用する。

将来`general / analysis`等へ拡張する場合はcontract revisionまたは明示拡張を行う。

### `blocks[]`

1個以上。

表示順序をそのまま保持する。

---

## 7. Block contract

Blockは**presentation scope**を表す。

各block:

```text
block_id
presentation_role
label
units[]
```

### 7.1 `presentation_role`

N-04 v1では最低限次を定義する。

```text
main
interpretation
creative
context_limit
```

#### `main`

通常のgrounded response本文。

主に:

```text
source_fact
stylistic_expression
```

を含む。

Roleplayでは通常このblockだけで自然な応答を構成できる。

#### `interpretation`

stored SGOKB factではない推論を表示するscope。

Comparisonでは`interpretation` unitを原則このblockへ置く。

human-facing renderingではvisible labelを付ける。

標準表示label:

```text
Interpretation
```

日本語UI等でlocalized labelを使用してよいが、semantic roleは変えない。

#### `creative`

新規創作を表示するscope。

Creative use caseのnew Character / setting / event / arc等をここへ置く。

human-facing renderingではvisible labelを付ける。

標準表示label:

```text
Creative addition
```

これによりsource Concept factとのseparationを明確にする。

#### `context_limit`

供給Context不足を明示するscope。

必要に応じてvisible labelを付ける。

---

### 7.2 `label`

`main`では`null`を許容する。

`interpretation` / `creative`ではhuman-visible separationを成立させるlabelを必須とする。

validatorはlabel文字列そのものの英語表現ではなく、presentation roleとの整合を検査する。

---

## 8. Atomic Unit contract

各`unit`はvalidation対象となるatomic semantic unitである。

必須field:

```text
unit_id
semantic_role
text
support_refs
```

### 8.1 `unit_id`

Context内outputで一意なID。

標準syntax:

```text
U1
U2
U3
...
```

これはoutput-local identityでありcanonical Knowledge IDではない。

### 8.2 `semantic_role`

N-04G-02で定義済みのenumのみを使用する。

```text
source_fact
interpretation
creative_addition
context_limit
stylistic_expression
```

### 8.3 `text`

実際にhuman-facing responseへrenderされる自然言語content。

原則として1つのmaterial semantic proposition、またはsupport不要な1つのstylistic expressionを表す。

重要:

> `text`は単なるhidden metadataではなく、最終表示contentそのものである。

validatorが確認していない別proseを後からLLMに生成しない。

### 8.4 `support_refs[]`

N-04G-03 `K*` reference。

role別rule:

```text
source_fact          >= 1
interpretation       >= 1 material premise
creative_addition    = []
context_limit        = []
stylistic_expression = []
```

creative unitへ`K*`を付けてsource factらしく見せることを標準contractでは認めない。

Conceptからのinspiration traceが将来必要なら`inspired_by_refs`等を別fieldとして設計し、`support_refs`と分離する。

---

## 9. LLMはGrounding Dispositionを宣言しない

N-04G-02では次を定義した。

```text
supported
derived_supported
not_applicable
unsupported
contradictory
```

しかしこれらは**LLM output fieldにしない**。

理由:

- generator自身に「自分はsupported」と自己認定させてもproofにならない。
- N-04G-05 validatorが独立して決定すべきである。
- generated confidence score等をgrounding authorityにしない。

したがってLLMは、

```text
私は何を述べているか = semantic_role
どのContextを根拠にしたか = support_refs
```

だけを宣言する。

実際にsupportされているかはvalidatorが判定する。

---

## 10. Deterministic rendering

Consumer rendererはvalidated block / unitを入力とし、LLMを使用しない。

基本rule:

1. `blocks[]`順を保持する。
2. block内の`units[]`順を保持する。
3. `unit.text`を変更・paraphraseしない。
4. 同一block内unitは用途に応じた固定separatorで連結する。
5. `interpretation` / `creative` blockではvisible labelをrenderする。
6. `K*`, `unit_id`, internal metadataは通常表示しない。
7. debug / audit viewでは必要に応じてreferenceを表示できる。

重要:

```text
rendered response content
=
validated unit.textの集合
```

であり、rendererが新しいmeaningful sentenceを生成してはならない。

---

## 11. Atomicity rule

1 unitへ複数の独立material claimを詰め込まない。

不適切例:

```text
I am Saber, I am contracted to Shirou, and I secretly protect him in the Holy Grail War.
```

これを1 unitへ入れると、一部だけsupportedという状態を扱いにくい。

少なくとも:

```text
U1: I am Saber.
U2: I am contracted to Shirou.
U3: I secretly protect him in the Holy Grail War.
```

のように分離する。

V4 validatorが「1 unit内に複数material propositionがある」と判定した場合は`role_mismatch / malformed semantic unit / indeterminate`等のvalidation結果へ落とす。正確なfailure code統合はG-07でfreezeする。

ただし、

```text
Very well. Let us proceed.
```

のような非material stylistic expressionは、可読性を損なわない範囲で1 unitにまとめてよい。

---

## 12. Generation request contract

ConsumerはLLMへ最低限次を渡す。

```text
1. User task / use-case instruction
2. Grounded Context
   - context_fingerprint
   - K* grounding units
3. Allowed semantic roles
4. Role-specific support rule
5. Use-case presentation rule
6. Required output contract version / schema
7. External knowledge prohibition
8. Context不足時のcontext_limit rule
```

重要なinstruction:

```text
- source_factにはsupport_refsを付与する
- interpretationにはmaterial premise refsを付与する
- creative_addition / style / context_limitにはsupport_refsを付けない
- supplied Context外のfactをsource_factとして追加しない
- insufficientならcontext_limitを使用する
- proseをJSON envelope外へ出力しない
```

Prompt wording自体はN-04G-08 benchmark freeze時に固定する。

---

## 13. Use-case contract — Roleplay

Roleplayでは自然さを保つため、通常は`main` blockを使用する。

例:

```json
{
  "contract_version": "sgokb.grounded-generation-output.v1",
  "context_fingerprint": "ctx-...",
  "purpose": "roleplay",
  "blocks": [
    {
      "block_id": "B1",
      "presentation_role": "main",
      "label": null,
      "units": [
        {
          "unit_id": "U1",
          "semantic_role": "source_fact",
          "text": "I am Saber, also known as Artoria Pendragon.",
          "support_refs": ["K1"]
        },
        {
          "unit_id": "U2",
          "semantic_role": "source_fact",
          "text": "I am contracted to Shirou.",
          "support_refs": ["K2"]
        },
        {
          "unit_id": "U3",
          "semantic_role": "stylistic_expression",
          "text": "Very well. Let us proceed.",
          "support_refs": []
        }
      ]
    }
  ]
}
```

Rendered response:

```text
I am Saber, also known as Artoria Pendragon. I am contracted to Shirou. Very well. Let us proceed.
```

`K1 / K2`は通常表示しない。

Roleplayでinterpretationを使用する場合は、Characterのstable trait / backstoryへ見えないようG-02 / G-05 ruleでsemantic validationする。N-04 Case 1ではinterpretation blockを必須とはしない。

---

## 14. Use-case contract — Comparison

Comparisonではsource factsとinterpretationをvisibleに分離する。

概念例:

```json
{
  "contract_version": "sgokb.grounded-generation-output.v1",
  "context_fingerprint": "ctx-...",
  "purpose": "comparison",
  "blocks": [
    {
      "block_id": "B1",
      "presentation_role": "main",
      "label": null,
      "units": [
        {
          "unit_id": "U1",
          "semantic_role": "source_fact",
          "text": "Work A contains the supplied fact ...",
          "support_refs": ["K3"]
        },
        {
          "unit_id": "U2",
          "semantic_role": "source_fact",
          "text": "Work B contains the supplied fact ...",
          "support_refs": ["K11"]
        }
      ]
    },
    {
      "block_id": "B2",
      "presentation_role": "interpretation",
      "label": "Interpretation",
      "units": [
        {
          "unit_id": "U3",
          "semantic_role": "interpretation",
          "text": "Based on those supplied facts, the two works can be compared as ...",
          "support_refs": ["K3", "K11"]
        }
      ]
    }
  ]
}
```

Rendered responseでは`Interpretation`見出しを表示する。

これにより、stored SGOKB factとcomparison上のderived interpretationを人間にも機械にも分離する。

---

## 15. Use-case contract — Creative

Creativeではsource Concept knowledgeと新規創作をvisibleに分ける。

概念例:

```json
{
  "contract_version": "sgokb.grounded-generation-output.v1",
  "context_fingerprint": "ctx-...",
  "purpose": "creative",
  "blocks": [
    {
      "block_id": "B1",
      "presentation_role": "main",
      "label": null,
      "units": [
        {
          "unit_id": "U1",
          "semantic_role": "source_fact",
          "text": "The supplied Tsundere concept includes ...",
          "support_refs": ["K2"]
        },
        {
          "unit_id": "U2",
          "semantic_role": "source_fact",
          "text": "The supplied Hero's Journey concept includes ...",
          "support_refs": ["K8"]
        }
      ]
    },
    {
      "block_id": "B2",
      "presentation_role": "creative",
      "label": "Creative addition",
      "units": [
        {
          "unit_id": "U3",
          "semantic_role": "creative_addition",
          "text": "A new character named Elia begins her journey ...",
          "support_refs": []
        },
        {
          "unit_id": "U4",
          "semantic_role": "creative_addition",
          "text": "Her arc introduces a newly invented event ...",
          "support_refs": []
        }
      ]
    }
  ]
}
```

Creative blockの内容がContextに存在しないこと自体はfailureではない。

問題になるのは、source Conceptのfactとして提示すること、またはcreative scope外へcanonical-looking source factを混入することである。

---

## 16. Context不足の表現

Context不足をmodel memoryで補わないため、`context_limit`を正式outputとして利用する。

例:

```json
{
  "block_id": "B2",
  "presentation_role": "context_limit",
  "label": "Context limit",
  "units": [
    {
      "unit_id": "U4",
      "semantic_role": "context_limit",
      "text": "The supplied context does not contain enough personality detail to state that confidently.",
      "support_refs": []
    }
  ]
}
```

`context_limit`が存在すること自体をgeneration failureとはみなさない。

その結果を最終answerとして受理するか、partial result / insufficientとしてworkflow終了するかはN-04G-06で決める。

---

## 17. Malformed output policy

次はV0 failureへ送る。

- JSON parse不能
- envelope外の追加natural language
- unknown contract version
- required field欠落
- duplicate `block_id / unit_id`
- unknown semantic role
- invalid support ref syntax
- purpose mismatch
- block / semantic role policy違反

Consumerは次を行わない。

- regexで都合よくJSON片だけ切り出してPASSさせる
- unknown field / unknown roleをsilent ignoreして意味を変える
- missing metadataをmodel outputから推測補完する
- malformed outputをgrounded responseとして直接表示する

retry / rejectの正式actionはN-04G-06で決める。

---

## 18. Provider-native Structured Outputの位置づけ

Provider / runtimeがJSON Schema constrained generationを提供する場合は、V0 malformed率を下げるため利用を推奨する。

ただしSGOKB contract上、

```text
native structured output対応modelだけが利用可能
```

とはしない。

理由:

- local LLM runtime差を吸収する必要がある。
- model-independent contractを維持する。
- JSON syntaxを生成できるmodelなら同じV0 validationへ通せる。

Native constraintは**transport / runtime optimization**であり、grounding semanticsではない。

---

## 19. RenderingとValidationの順序

formal flow:

```text
Raw structured output
    ↓
G-05 V0〜V5 validation
    ↓
PASSしたstructured output
    ↓
Deterministic rendering
    ↓
Human-facing response
```

FAIL / INDETERMINATE outputを通常human responseとしてrenderしてからgrounded扱いしない。

Debug / evaluation evidenceとしてraw contentを保存・表示することはできる。

---

## 20. Contract ownership

N-04G-01に従う。

### SGOKB Application / Grounding Contract Layer

所有:

- output contract version
- field semantics
- semantic role rule
- support reference semantics
- deterministic rendering semantics
- validatorとの接続条件

### MCP

必要に応じてApplication capabilityをtransportするだけで、独自output semanticsを持たない。

### Consumer

- request assembly
- provider / model invocation
- raw structured output保存
- validation invocation
- deterministic rendering
- G-06 failure handling

### LLM

- required schemaへ従うbest-effort generation
- semantic role / support refsの宣言

ただしgrounding PASSを自己決定しない。

---

## 21. Architecture impact

今回のDecisionにより必要になる実装候補:

```text
GroundedGenerationOutput schema / parser
Output contract validator (V0)
Deterministic renderer
Generation request builder / prompt template
N-04 acceptance harness integration
```

N-04G-09で実装場所を最終決定する。

不要:

- canonical DB schema変更
- persistent Fact ID
- MCP内LLM generation
- second-stage LLM renderer
- Web / cloud fallback

---

## 22. Acceptance impact

N-04 v2では少なくとも次を確認する。

### 共通

- model outputが`sgokb.grounded-generation-output.v1`へ適合する。
- context fingerprintが一致する。
- source fact / interpretation support refsがmachine-addressable。
- raw structured outputとrendered contentの意味差分がない。

### Case 1

- first-person Roleplayをstructured unitから自然にrenderできる。
- source facts最低2件がsupport refsを持つ。
- unsupported backstoryがunitとして生成された場合validatorでFAILできる。

### Case 2

- 両Workのsource factsが個別unitとして存在する。
- interpretationがseparate blockへ置かれる。
- interpretation premise `K*`を追跡できる。

### Case 3

- source Concept factsとcreative blockが分離される。
- new Character / setting / event / arcがcreative additionとして明示される。
- creative contentへsource support refを偽装しない。

---

## 23. Deferred decisions

本Taskでは次を確定しない。

- retry回数 / reject / partial return policy — N-04G-06
- semantic validator具体model — G-07 / G-08でfreeze
- exact JSON Schema implementation — N-04G-09
- exact prompt wording / temperature / sampler — N-04G-08 / G-11
- localized human-facing labels — implementation detail

---

## 24. Definition of Done

- [x] generation input / output contractを具体化した。
- [x] natural language only / inline citation / dual-output / 2-stage / deterministic rendering方式を比較した。
- [x] `single-pass structured semantic units + deterministic rendering`を採用した。
- [x] atomic semantic unitと`K*` support mappingを定義した。
- [x] LLMにGrounding Dispositionを自己申告させないことを固定した。
- [x] final human-readable responseとvalidation metadataの乖離を構造的に防止した。
- [x] Roleplay / Comparison / Creativeの3 use case例を示した。
- [x] interpretation / creative separationをpresentation blockで表現可能にした。
- [x] malformed outputの扱いをV0 failureとして定義した。
- [x] provider-native Structured Outputをoptional optimizationとして分離した。
- [x] canonical schema変更不要を確認した。
- [x] N-04G-05 validation designと整合した。

---

## 25. Next Task

次は以下とする。

```text
N-04G-06 [P0]
validation failure時のretry / reject / insufficient policyを設計する
```

N-04G-04 / G-05の往復設計が揃ったため、次に各validation failureへ正式なworkflow actionを割り当てる。
