# N-04G-07 End-to-End Grounded Generation Design Freeze

更新日: 2026-10-18

- Status: **Accepted / Design Frozen**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-07 [P0] End-to-End grounded-generation designを統合しDesign Freezeする`
- Responsibility: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- Taxonomy: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- Grounded Context: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- Generation / Output: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- Validation: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- Failure handling: `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04G-01〜G-06を、次のEnd-to-End grounded-generation protocolとして統合し、**P0設計をFreezeする**。

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
  ├─ context_fingerprint
  └─ K1 / K2 / ... + canonical metadata
        ↓
Consumer Orchestrator
  ├─ generation request assembly
  ├─ frozen model/runtime/settings
  └─ no Web / cloud / external fact supplementation
        ↓
Untrusted Local LLM
        ↓
sgokb.grounded-generation-output.v1
  └─ blocks[] / units[]
        ↓
sgokb.grounding-validation.v1
  ├─ V0 Contract / Parse
  ├─ V1 Reference Integrity
  ├─ V2 Taxonomy / Use-case Policy
  ├─ V3 Deterministic Support
  ├─ V4 Bounded Semantic Support
  └─ V5 Aggregate Verdict
        ↓
sgokb.grounding-failure-policy.v1
  ├─ PASS + sufficient → ACCEPTED
  ├─ PASS + valid context limit → INSUFFICIENT_CONTEXT
  ├─ retryable failure → same conditionsで最大1回retry
  ├─ exhausted grounding failure → REJECTED
  └─ infrastructure / integrity failure → SYSTEM_FAILURE
        ↓
ACCEPTEDのみ
        ↓
Deterministic Renderer
        ↓
Human-readable response
```

Design Freeze後、G-08〜G-12ではこの意味設計を変更しない。

- G-08: acceptance specへ固定する。
- G-09: 実装する。
- G-10: testする。
- G-11: formal harnessをfreezeする。
- G-12: formal re-acceptanceする。

実装中にP0 contract変更が必要になった場合は、G-07 Freezeを明示的に再openし、理由・影響・再freezeを記録する。silent design driftは禁止する。

---

## 2. Frozen responsibility boundary

### SGOKB Application / Grounding Contract Layer

所有するもの:

- grounded-generationのnormative semantics
- claim taxonomy
- grounded Context / reference semantics
- generation output contract
- validation semantics
- failure handling semantics
- `SGOKB-grounded`と呼べる条件

所有しないもの:

- 特定LLM provider
- model loading / GPU runtime
- provider-specific chat API
- natural-language品質そのもの

### MCP

MCPは引き続き**Knowledge Access / transport adapter**である。

所有しないもの:

- LLM generation
- validator reasoning
- retry orchestration
- provider selection
- canonical semanticsの独自再定義

Grounding-related Application capabilityをMCP経由で公開する場合も、MCPはtransport adapterに限定する。

### Consumer Orchestrator

実行責務を持つ。

- Grounded Context取得
- generation request assembly
- generator invocation
- validation invocation
- retry / terminal outcome実行
- evidence保存
- PASSした内容だけをrender

ConsumerはSGOKB contractを緩和・再定義しない。

### LLM

LLMは**untrusted best-effort generator**であり、grounding authorityではない。

LLM自身のcitation、role、自己評価、`I used only context`等はproofではない。

---

## 3. Frozen semantic model

### Semantic Role

```text
source_fact
interpretation
creative_addition
context_limit
stylistic_expression
```

### Grounding Disposition

```text
supported
derived_supported
not_applicable
unsupported
contradictory
```

Grounding DispositionはLLMが自己申告するfieldではなく、validatorが決定する。

### Separation rule

次はstored SGOKB factと表示上区別する。

- `interpretation`
- `creative_addition`

意味内容が許容されても分離できなければ`SEPARATION_VIOLATION`となる。

---

## 4. Frozen Grounded Context contract

Contract:

```text
sgokb.grounded-context.v1
```

J-04 `sgokb.context-builder.v1`のselected Knowledgeへ、selection完了後にGrounding Reference Projectionを付与する。

### Reference namespace

```text
K1
K2
K3
...
```

`K*`は1 grounded Context内だけで有効なcontext-local referenceである。

各Kは最低限次へ追跡可能である。

```text
object_id
resolved_version_id
source_kind
canonical target identity
```

`source_kind`最低範囲:

```text
object_field
statement
attribute
relation
```

### Context identity

```text
context_fingerprint + K*
```

をsupport reference namespaceとする。

別ContextのKを現在Contextへ流用しない。

### Canonical schema impact

- 新規persistent Fact ID: 不要
- canonical table追加: 不要
- Statement / Attribute / Relation schema変更: 不要
- Evidence schema変更: 不要

EvidenceはKnowledge provenance用secondary metadataであり、generation claimの一次referenceにはしない。

---

## 5. Frozen generation / output contract

Contract:

```text
sgokb.grounded-generation-output.v1
```

### Normative principle

**LLMが生成する唯一のnormative contentはstructured semantic unitsである。**

別のmodel-generated `final_response`は持たない。

概念形:

```json
{
  "contract_version": "sgokb.grounded-generation-output.v1",
  "context_fingerprint": "...",
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
          "text": "...",
          "support_refs": ["K1"]
        }
      ]
    }
  ]
}
```

### Unit invariant

各unit:

```text
unit_id
semantic_role
text
support_refs[]
```

- `source_fact`: support Kを要求
- `interpretation`: material premise Kを要求
- `creative_addition`: source factual supportは原則不要
- `context_limit`: support不要
- `stylistic_expression`: material source-world propositionを含まない限りsupport不要

### Presentation scopes

最低限:

```text
main
interpretation
creative
context_limit
```

`interpretation` / `creative`はhuman-visible separationを持つ。

### Rendering invariant

Human-facing responseは、**validatorがPASSした`unit.text`だけ**を固定順序でrenderする。

Rendererは禁止される:

- paraphrase
- fact追加
- semantic compression
- new transition claim生成
- LLM再生成

したがって、validation対象と表示対象は意味内容として同一である。

---

## 6. Frozen validation pipeline

Contract:

```text
sgokb.grounding-validation.v1
```

### V0 — Contract / Parse

検査:

- contract version
- required fields
- unit uniqueness
- enum
- parseability

Malformed outputをheuristicでsilent repairしない。

### V1 — Reference Integrity

検査:

- context fingerprint
- K存在
- cross-context reference
- canonical mapping integrity

### V2 — Taxonomy / Use-case Policy

検査:

- roleごとのsupport requirement
- Roleplay / Comparison / Creative境界
- interpretation / creative separation

### V3 — Deterministic Support

安全に機械判定可能なものを処理する。

- exact / normalized Statement
- structured Attribute
- structured Relation
- Object field
- 明白なcontradiction

### V4 — Bounded Semantic Support

V3 unresolvedのみを対象にする。

Semantic validatorへ渡す情報は限定する。

```text
対象unit
semantic role
cited K content
必要なtaxonomy / use-case rule
```

Web / external retrieval / model memoryをgrounding根拠として利用しない。

### V5 — Aggregate Verdict

```text
PASS
FAIL
INDETERMINATE
```

`INDETERMINATE`はPASSへ昇格しない。

`SGOKB-grounded`認定はfail-closedとする。

### Same-model self-check

Generator自身のself-checkだけを最終semantic Gateにしない。

Formal N-04でLLM semantic validatorを使う場合、原則generatorから独立した固定local validatorを事前freezeする。

---

## 7. Frozen failure handling

Contract:

```text
sgokb.grounding-failure-policy.v1
```

### Maximum attempts

```text
attempt 1 + retry 1 = maximum 2 generation attempts
```

unlimited retryは禁止する。

### Retry invariants

retry前後で固定する。

```text
Grounded Context
context_fingerprint
purpose
generator model
runtime
generation settings
contract version
```

追加可能なのはvalidatorのstructured failure feedbackだけである。

追加禁止:

- new retrieval
- Web
- external Knowledge
-別generator model
- cloud fallback

### Whole-output regeneration

FAIL outputのsafe-looking unitだけをConsumerが削り出して部分採用しない。

Retry時はstructured output全体を再生成する。

### Terminal outcomes

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

- `ACCEPTED`: validation PASS、要求用途を満たすcandidate
- `INSUFFICIENT_CONTEXT`: valid `context_limit`により安全に不足を表明
- `REJECTED`: retry exhausted等でgrounding contractを満たせない
- `SYSTEM_FAILURE`: validator / mapping / integrity / infrastructure等のsystem-side failure

`INSUFFICIENT_CONTEXT`はgrounding failureではないが、N-04 use-case acceptanceのquality requirementを自動PASSさせない。

---

## 8. End-to-End sequence

### Step 1 — Knowledge retrieval

ConsumerはMCP public read boundary経由でContextを取得する。

- direct SQLiteは禁止
- current accepted Versionを既定とする
- pinned Versionは明示時のみ
- silent historical mixing禁止

### Step 2 — Context selection

J-04 Context Builderがpurpose / budgetにより決定論的にKnowledge subsetを選択する。

Retrieval quality tuningはここでは追加しない。

### Step 3 — Grounding projection

selected KnowledgeへK referenceを決定論的に割り当て、`context_fingerprint`を生成する。

### Step 4 — Generation request

ConsumerはGrounded Contextとoutput contractをgeneratorへ渡す。

Generatorへ外部Web Knowledgeを注入しない。

### Step 5 — Structured generation

Generatorは`blocks[] / units[]`だけを返す。

Free-form final responseを別生成しない。

### Step 6 — Validation

V0〜V5を実行する。

### Step 7 — Failure handling

- PASS → terminal判定
- retryable failure → failure feedback付きで1回だけwhole-output regeneration
- system failure → retryせずSYSTEM_FAILURE
- second attempt FAIL → REJECTED

### Step 8 — Rendering

`ACCEPTED`のvalidated unitsだけを決定論的にrenderする。

`REJECTED / SYSTEM_FAILURE`のfailed generation contentをgrounded responseとして表示しない。

`INSUFFICIENT_CONTEXT`はcontractに従ったcontext-limit responseを表示可能である。

### Step 9 — Evidence retention

最低限保存する。

```text
Git / environment metadata
MCP request / response
source Context
Grounded Context / context_fingerprint / K mapping
generator model / settings
attempt 1 request / response
attempt 1 validation
retry feedback
attempt 2 request / response / validation（存在時）
terminal outcome
rendered response（存在時）
validator model / settings
```

---

## 9. Use-case walkthrough

## 9.1 Case 1 — Roleplay

Context例:

```text
K1: Saber = Artoria Pendragon
K2: Saber is a sword-wielding Servant
K3: Saber is contracted to Shirou
```

正常generation例:

```text
U1 source_fact: "I am Saber, also known as Artoria Pendragon." support=[K1]
U2 source_fact: "I am a sword-wielding Servant." support=[K2]
U3 source_fact: "I am contracted to Shirou." support=[K3]
U4 stylistic_expression: "Very well. Let us proceed." support=[]
```

Context外backstoryを追加した場合:

```text
U5 source_fact: "I secretly protect Shirou throughout the Holy Grail War."
```

→ support不足 / semantic unsupported → retry対象 → 再度FAILならREJECTED。

Roleplay styleを理由にunsupported stable personality / backstoryを許容しない。

---

## 9.2 Case 2 — Comparison

両Workのfactsを`source_fact` unitsとしてgroundし、比較結論は`interpretation` blockへ置く。

```text
Main
  U1 source_fact Work A [K2]
  U2 source_fact Work B [K9]

Interpretation
  U3 interpretation [K2, K9]
```

U3は、

1. premise Kがsupportされること
2. conclusionがpremiseからreasonable derivationであること

の両方を満たす必要がある。

Similarity score自体をtruth / confidence / preference probabilityへ読み替えない。

外部franchise知識をpremiseへ使ったinterpretationはFAILする。

---

## 9.3 Case 3 — Creative

Source Concept knowledge:

```text
Main
  U1 source_fact Concept A [K1]
  U2 source_fact Concept B [K7]
```

New creation:

```text
Creative addition
  U3 creative_addition []
  U4 creative_addition []
  U5 creative_addition []
```

Creative detailそのものにsource supportは要求しない。

ただし、source Conceptに関する新しい事実をcreative blockへ隠して追加することは許容しない。

Creative blockのvisible separationにより、source Knowledgeとnew creationを明示的に区別する。

---

## 10. Invariants across all use cases

以下をDesign Freeze invariantとする。

1. **No direct SQLite for AI input.**
2. **No silent historical Version mixing.**
3. **No Web / external fact supplementation.**
4. **No raw LLM output is automatically grounded.**
5. **No `K*` reference alone proves semantic support.**
6. **No model-generated final prose exists outside validation units.**
7. **No unvalidated unit is rendered as grounded content.**
8. **No unlimited retry.**
9. **No model / cloud fallback inside retry chain.**
10. **No partial salvage of failed output in baseline.**
11. **No canonical mutation from grounded-generation workflow.**
12. **No relaxation of N-04 rubric merely to obtain PASS.**

---

## 11. N-06 boundary

N-04 grounded-generation designは、供給されたContextに対して正しく生成・検証する問題を扱う。

N-06へ残すもの:

- Knowledge coverage quality
- retrieval ranking quality
- similarity quality
- whether the best available Knowledge was retrieved
- semantic retrieval tuning

N-04でContext不足が判明しても、model memoryで補完しない。

正しいoutcomeは必要に応じて`context_limit / INSUFFICIENT_CONTEXT`である。

---

## 12. Model-independent vs model-specific

### SGOKB contractとしてFrozen

- taxonomy
- K reference semantics
- context fingerprint semantics
- structured output logical shape
- presentation separation semantics
- validation stages / verdict semantics
- retry upper bound
- terminal outcome semantics
- rendering invariant
- evidence requirements

### G-08 / G-11でacceptance用にFreezeするruntime details

- generator model ID / quantization
- validator model ID / quantization
- local endpoint
- temperature / top-p等
- provider-native constrained decoding利用有無
- timeout / runtime operational settings

これらはN-04再現性には必要だが、SGOKB一般contractの意味定義にはしない。

---

## 13. Candidate decisions — integrated record

| Candidate | Decision | Reason |
|---|---|---|
| Persistent new Fact ID | **Reject** | existing canonical identity + context-local Kで十分 |
| Canonical Statement ID direct citation | **Reject as primary** | heterogeneous / long / storage coupling |
| Evidence ID direct citation | **Reject as primary** | provenance layerとgeneration support layerが異なる |
| Context-local K + canonical metadata | **Adopt** | short LLM-facing ref + full traceability |
| Natural language only | **Reject** | atomic claim / role / support mappingが不安定 |
| Inline citation only | **Reject as sole contract** | claim scope / roleが曖昧 |
| Separate claim metadata + final prose | **Reject** | validation対象と表示対象が乖離可能 |
| Single-pass structured units | **Adopt** | validation unitとdisplay contentを一致可能 |
| 2-stage LLM renderer | **Reject as baseline** | second stage can reintroduce unsupported content |
| Deterministic renderer | **Adopt** | validation後のsemantic driftを防止 |
| Schema validation only | **Reject** | semantic supportを確認できない |
| Reference presence only | **Reject** | wrong K citationを検出できない |
| Deterministic-only validation | **Reject alone** | paraphrase / interpretationを扱えない |
| Same-model self-check only | **Reject** | generatorの誤りを独立に検証できない |
| Separate semantic LLM judge only | **Reject alone** | deterministic checksまでLLMへ依存する必要なし |
| Hybrid validator | **Adopt** | deterministic + bounded semanticを分離 |
| Unlimited retry | **Reject** | cherry-pick /偶然PASS risk |
| Immediate reject for every correctable failure | **Reject** | structured repair opportunityを捨てる |
| Bounded single retry | **Adopt** | recoveryと再現性のbalance |
| Model/cloud/Web fallback on retry | **Reject** | evaluation条件・grounding sourceが変わる |
| Partial salvage | **Reject as baseline** | semantics / completenessをConsumerが変更する |
| context_limit / INSUFFICIENT_CONTEXT | **Adopt** | Context不足を安全に表現できる |
| Creative additions | **Adopt with separation** | creativity itself is not hallucination |

---

## 14. Architecture impact

### No canonical changes

- DB migration: **不要**
- canonical table change: **不要**
- Evidence / Provenance redesign: **不要**
- Retrieval ranking redesign: **不要**
- MCP responsibility expansion into inference: **不要**

### New logical components required downstream

G-09 implementation scope:

```text
GroundedContextProjector
  Context Builder output → K mapping / fingerprint

GroundedGenerationContract
  logical schema / parser / request requirements

GroundingValidator
  V0..V5

SemanticValidatorAdapter
  bounded semantic judge boundary

GroundingFailureController
  max 1 retry / terminal outcome

DeterministicRenderer
  validated units → human response

GroundingEvidenceLogger
  attempts / validation / outcome artifacts
```

物理module / class名はG-09で調整可能だが、責務境界を変更しない。

---

## 15. Acceptance impact / handoff to G-08

G-08はv1 benchmarkを変更せず、v2 acceptance specを新規freezeする。

G-08へ渡す必須条件:

- same 3 representative use cases
- v1 core quality gatesを維持
- `sgokb.grounded-context.v1`
- `sgokb.grounded-generation-output.v1`
- `sgokb.grounding-validation.v1`
- `sgokb.grounding-failure-policy.v1`
- max generation attempts = 2
- second attemptがPASSした場合、grounded-generation workflow上は`ACCEPTED`になり得る
- attempt countはevidenceへ必ず記録
- `INSUFFICIENT_CONTEXT`はgrounding-safeでもCase quality PASSとは限らない
- `REJECTED / SYSTEM_FAILURE`はCase PASSにしない
- generator / validator runtimeをformal run前にfreeze
- benchmark開始後のmodel / rubric / retry policy cherry-pick禁止
- raw output / validation / rendered responseをすべて保存

G-08はこのDesign Freezeを弱めてPASSしやすくしてはならない。

---

## 16. Open issues after Design Freeze

**P0 semantic / architecture issue: なし。**

後続で決める事項はDesign implementation / acceptance operationalizationであり、本Designの意味変更ではない。

- exact JSON Schema syntax: G-09
- physical module layout: G-09
- generator / validator concrete model: G-08 / G-11
- generation parameters: G-08 / G-11
- evidence file naming: G-11
- formal execution details: G-11

これらがFrozen semanticsと衝突する場合はG-07を再openする。

---

## 17. Definition of Done

- [x] G-01〜G-06の責務・用語・contractを1 sequenceへ統合した。
- [x] Context Builder → Grounded Context → Generation → Validation → Failure handling → Renderingの順序を固定した。
- [x] Case 1 / 2 / 3のEnd-to-End walkthroughを記録した。
- [x] canonical Knowledge / Retrieval / MCPへの影響を確認した。
- [x] N-06との境界を確認した。
- [x] model-independent semanticsとacceptance runtime detailsを分離した。
- [x] logging / evidence retentionを統合した。
- [x] Candidate主要案の採用 / 不採用を統合記録した。
- [x] G-09 implementation scopeを渡せる状態にした。
- [x] G-08 acceptance specへ必要なfreeze条件を引き渡した。
- [x] 未決P0 semantic / architecture issueがないことを確認した。

---

## 18. Next task

```text
N-04G-08 [P0]
N-04 v2 benchmark / acceptance specを固定する
```

G-07でFrozenしたEnd-to-End contractを、formal re-acceptance開始前にv2 benchmark / acceptance specificationへ変換する。
