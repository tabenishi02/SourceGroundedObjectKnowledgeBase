# N-04G-03 Context Grounding / Reference Contract

更新日: 2026-10-18

- Status: **Accepted**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-03 [P0] Context grounding / reference contractを設計する`
- Responsibility Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- Claim Taxonomy Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- Existing Context Contract: `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 grounded-generationのContext reference方式として、**Context-local Grounding Reference + canonical identity metadata**を採用する。

概念形:

```text
SGOKB selected Knowledge item
  ├─ context-local reference: K1 / K2 / K3 / ...
  └─ canonical metadata
       ├─ object_id
       ├─ resolved_version_id
       ├─ source_kind
       └─ canonical target identity
```

主なDecision:

1. LLM / Consumerがclaim supportを示すために使用する一次参照は、短い**Context-local Grounding Reference**とする。
2. Context-local referenceは`K1`, `K2`, ...のように、1つのgrounded Context内だけで意味を持つ。
3. 各referenceはSGOKB側でcanonical Object / Version / Knowledge itemへ必ず追跡できるmetadataを保持する。
4. canonical Statement ID / Attribute Value ID / Relation ID等は失わないが、LLMへ直接それだけを引用させることは標準方式にしない。
5. Evidence IDはclaim groundingの一次参照にしない。Evidenceはcanonical Knowledgeのprovenance / audit用secondary metadataとして扱う。
6. Context Builder v1のselection / budget semanticsは変更せず、その**選択後のKnowledge subsetへgrounding reference projectionを付与するApplication-level contract**とする。
7. canonical schema変更、新規canonical table、新規persistent Fact IDは不要とする。
8. Context-local referenceの存在だけではclaimがsupportされたことを証明しない。semantic support判定はN-04G-05のvalidator設計で決める。

この方式はN-04G-01の`SGOKB-owned contract + consumer-owned orchestration + untrusted LLM`と整合し、N-04G-02の`source_fact / interpretation`を供給Contextへ追跡可能にする。

---

## 2. 既存Contextとの整合

J-04でAccepted済みのContext Builderは、保存済みKnowledgeを決定論的に選別するApplication / Retrieval機能であり、LLM推論やKnowledgeの意味的書き換えを行わない。

現行read model / Context Builderは選択されたKnowledge itemについて、すでに次のcanonical identityを保持している。

```text
statement
  statement_id

attribute
  attribute_value_id
  attribute_id

relation
  relation_id
  relation_type_id

object
  object_id
  resolved_version_id
```

したがってN-04G-03ではcanonical Knowledgeへ新しい永続Fact identityを追加しない。

必要なのは、これらの異種canonical identityをLLM / Consumerが一貫して扱える短いContext-local referenceへ投影することである。

---

## 3. 比較した方式

### Option A — 現行Context本文のみ / referenceなし

#### 利点

- 追加payloadがない。
- J-04 v1のまま利用できる。
- 自然言語promptが単純。

#### 欠点

- claimとsupport itemの機械的対応を表現できない。
- 同一Context内のどのKnowledge itemを使ったか追跡しにくい。
- N-04 v1と同様、prompt instructionだけに依存しやすい。

#### Decision

**不採用。**

N-04のfailureを受け、少なくともclaim→Context itemを追跡可能にするreference contractが必要である。

---

### Option B — canonical Statement ID等をそのままLLMへ引用させる

例:

```text
statement: 2fd6...-...
```

#### 利点

- canonical itemへ直接遡れる。
- persistent identityであり、Contextを跨いでも同じKnowledge itemを識別できる。
- 追加alias mappingが不要。

#### 欠点

- Statement / Attribute / RelationでID種別が異なる。
- UUID等の長いinternal IDはLLM outputを冗長にし、誤記しやすい。
- Roleplay / Creativeの自然文へ埋め込みにくい。
- internal storage identityとgeneration-facing citation syntaxを密結合する。
- Object name / alias / class等、canonical item IDがread model上単一でない情報を統一しにくい。

#### Decision

**一次参照としては不採用。**

canonical IDはContext-local referenceのbackend metadataとして保持する。

---

### Option C — Evidence IDを一次referenceにする

#### 利点

- provenanceへ直接遡れる。
- Source-groundedというSGOKBの設計思想と表面的には親和性が高い。

#### 欠点

- N-04でLLMへ渡しているのはaccepted Knowledge Contextであり、Evidence本文そのものではない。
- roleplay / creativeではEvidence refsをJ-04 profile既定で省略する。
- 1 Statementへ複数Evidence、1 Evidenceから複数Knowledge target等があり、generation claim supportの単位と一致しない。
- Evidenceはcanonical Knowledgeを裏付けるprovenanceであり、今回供給したContext itemそのものを識別するものではない。

#### Decision

**一次referenceとして不採用。**

Evidence IDはaudit / provenance用secondary metadataとして必要に応じて保持する。

---

### Option D — Context-local referenceのみ

例:

```text
K1
K2
K3
```

#### 利点

- 短い。
- LLMが扱いやすい。
- Statement / Attribute / Relation等を統一できる。
- natural language / structured outputの双方で使いやすい。

#### 欠点

- `K1`だけでは別Contextからcanonical itemへ遡れない。
- Contextを跨ぐと同じ`K1`が別物を意味する。
- audit evidenceとして単独保存すると弱い。

#### Decision

**単独方式としては不採用。**

canonical metadataとの組み合わせが必要である。

---

### Option E — Context-local reference + canonical identity metadata

#### 利点

- LLM-facing syntaxは短くできる。
- SGOKB側ではcanonical identityへ完全に遡れる。
- Statement / Attribute / Relation / Object identityを同じreference namespaceへ統合できる。
- Context-localなのでpresentation contractをstorage identityから分離できる。
- Consumer / model種類を問わず共通contractにできる。
- canonical schema変更が不要。

#### 欠点

- Contextごとのreference mappingを保持する必要がある。
- `K1`はContext外で意味を持たないため、Context identityと一緒に保存する必要がある。
- 追加metadata分のpayload overheadが発生する。

#### Decision

**採用。**

---

## 4. Grounded Context contract

J-04 `sgokb.context-builder.v1`を置換・破壊せず、その選択結果をgrounded-generation用に投影する論理contractを追加する。

契約名:

```text
sgokb.grounded-context.v1
```

これはN-04G-03時点の設計上のcontract名であり、物理module / API / MCP Tool配置はN-04G-07 / G-09で最終実装へ落とす。

概念構造:

```text
grounded_context_contract_version = sgokb.grounded-context.v1
source_context_contract_version = sgokb.context-builder.v1
context_fingerprint
purpose
objects / selection metadata
grounding_units[]
```

J-04 Context selection policy、purpose、budget、current / pinned Version semanticsは維持する。

---

## 5. Context-local Grounding Reference

### 5.1 Syntax

標準presentation referenceは次とする。

```text
K1
K2
K3
...
```

`K`はKnowledge grounding unitを表す。

以下は使用しない。

- `F1`: interpretationやRelation等まで単純なFactと誤認しやすいため。
- canonical UUIDそのもの: LLM-facing syntaxとして長すぎるため。
- Evidence ID: support layerが異なるため。

### 5.2 Scope

`K1`等は**1 grounded Context内だけで有効**とする。

したがって、次を禁止する。

- 別Contextの`K1`を現在Contextのsupportとして利用する。
- Context fingerprintを失った状態で`K1`だけを長期provenanceとして保存する。
- Context-local referenceをcanonical persistent Fact IDとして扱う。

### 5.3 Determinism

同一のselected Context内容、同一順序、同一grounded-context contract versionであれば、同じ順序で`K1..Kn`を割り当てる。

assignmentは**J-04のKnowledge selection完了後**に行う。

これにより、grounding metadata追加によってJ-04のbudget selection結果を変えない。

---

## 6. Grounding Unit

`grounding_unit`はLLMへ供給された、claim supportの候補になり得る最小Context source unitである。

概念例:

```json
{
  "ref_id": "K7",
  "object_id": "...",
  "resolved_version_id": "...",
  "source_kind": "statement",
  "canonical_ref": {
    "kind": "statement",
    "id": "..."
  },
  "facet": "background",
  "content": {
    "text": "..."
  },
  "evidence_refs": []
}
```

### 6.1 `source_kind`

最低限次を扱う。

```text
object_field
statement
attribute
relation
```

#### `object_field`

Object envelopeに存在し、source-world factとして利用可能な情報。

例:

- name
- alias
- primary class / additional class

canonical targetは`object_id` + `field_path`で表す。

例:

```json
{
  "kind": "object_field",
  "object_id": "char-...",
  "field_path": "aliases[0]"
}
```

#### `statement`

canonical `statement_id`を保持する。

#### `attribute`

canonical `attribute_value_id`を保持し、必要に応じて`attribute_id`もmetadataとして保持する。

#### `relation`

canonical `relation_id`を保持し、必要に応じて`relation_type_id`もmetadataとして保持する。

### 6.2 Version binding

すべてのgrounding unitは最低限次へbindする。

```text
object_id
resolved_version_id
```

これにより、同じObjectでも別VersionのKnowledgeをsilentに混ぜない。

---

## 7. Context fingerprint

Context-local referenceのnamespaceを識別するため、grounded Contextにはdeterministicな`context_fingerprint`を持たせる。

概念:

```text
SHA-256(
  grounded-context contract version
  + source Context contract version
  + purpose / relevant selection metadata
  + resolved Object / Version identity
  + ordered grounding units / canonical refs / content
)
```

正確なcanonical serialization方式は実装Taskで固定するが、次を満たす。

- 同じgrounded Contextなら同じfingerprint。
- selected Knowledge / Version / ordering / contract semanticsが変わればfingerprintも変わる。
- DBへpersistする必要はない。
- acceptance evidenceではreference mappingと一緒に保存する。

`context_fingerprint + ref_id`の組み合わせで、N-04の1 run内におけるsupport referenceを一意にする。

---

## 8. Claim supportとの関係

N-04G-02 taxonomyとの対応を次とする。

### `source_fact`

claim support候補として1個以上の`K*` referenceを持てる。

ただし、referenceが存在するだけで`supported`とは判定しない。

例:

```text
claim: Saber is contracted to Shirou.
support: [K4]
```

K4が実際にその命題をsupportするかはN-04G-05で検証する。

### `interpretation`

material premiseとなる複数の`K*`をsupport metadataとして持てる。

例:

```text
claim: The two works both emphasize conflict.
role: interpretation
support: [K3, K11]
```

`derived_supported`と認めるには、material premiseがContext内でsupportされ、推論がexternal factual premiseへ依存しない必要がある。

### `creative_addition`

原則としてsource factual support referenceは必須にしない。

必要なら「inspired_by」等の非support metadataを将来設ける余地は残すが、`support`と混同しない。

### `context_limit`

source factual support referenceは原則不要。

### `stylistic_expression`

source-worldのmaterial propositionを含まない限りsupport reference不要。

---

## 9. Reference presenceはproofではない

本Decisionの重要原則:

> **Validな`K*`を出力に付けただけでは、そのclaimがgroundedである証明にはならない。**

LLMは誤ったreferenceを付ける可能性がある。

例:

```text
K4 = Saber is contracted to Shirou.

claim = Saber is secretly the ruler of the world. [K4]
```

このclaimはreference syntax上はvalidでもsemantic supportがない。

したがってN-04G-03は**traceability contract**を定義するTaskであり、grounding truth判定そのものはN-04G-05へ委ねる。

---

## 10. Evidence / Provenanceとの関係

SGOKBのprovenance chainは次のように保持する。

```text
Generated claim
   ↓ support reference
Context-local K*
   ↓ canonical_ref
Statement / Attribute / Relation / Object field
   ↓ optional Evidence link
Evidence
   ↓
Source / Snapshot / Provenance
```

重要な区別:

- `K*` = 今回LLMへ供給されたKnowledge itemを指す。
- canonical ID = SGOKB内でそのKnowledge itemを識別する。
- Evidence ID = そのcanonical Knowledgeを裏付けるprovenanceへ進むための参照。

この3層を同じIDとして扱わない。

Evidence refsがContext profileで省略されていても、`K*`によるgroundingは成立可能である。

必要なauditではcanonical IDを介してEvidenceを別途dereferenceできる。

---

## 11. Context Builder / ownership boundary

### 11.1 Context Builder本体

J-04の責務を維持する。

```text
Knowledge selection
purpose profile
budget control
Version binding
```

Context Builder自身へLLM generation semanticsを入れない。

### 11.2 Grounding reference projection

N-04G-01で定義したSGOKB Grounding Contract LayerのApplication責務とする。

概念フロー:

```text
KnowledgeReadApplication.build_context()
        ↓
sgokb.context-builder.v1
        ↓
Grounding reference projection
        ↓
sgokb.grounded-context.v1
        ↓
MCP / Consumer
```

物理的に同じApplication methodへoptionとして実装するか、別capabilityにするかはN-04G-07 / G-09で決める。

MCPが独自に`K*`を採番してはならない。
Consumerが独自にnormative referenceを付与してもならない。

SGOKB Application contractがmappingの正本を所有する。

---

## 12. Roleplay / Comparison / Creativeでの共通利用

reference syntax自体は3用途で共通とする。

### Roleplay

- source Character factへ`K*`を利用可能。
- stylistic expressionは通常reference不要。
- unsupported backstoryへ適当な`K*`を付けてもsupportにはならない。

### Comparison

- 両Objectのsource factsとinterpretation premisesを`K*`で追跡する。
- 1 interpretationへ複数Object由来referenceを付与できる。

### Creative

- source Concept factだけを`K*`で追跡する。
- 新規Character / event等のcreative additionにsupport referenceを必須化しない。
- creative additionへsource fact用`support`を付けてcanonical factのように見せない。

したがって、3用途でreference syntaxを分岐させない。
用途差はN-04G-02のsemantic roleとN-04G-04 output contractで表現する。

---

## 13. Budget / payload policy

J-04の`max_characters`は引き続き**selected Knowledge item本体のbudget**であり、wire payload全体や最終LLM prompt総量の上限ではない。

Grounding referenceはselection後に付与するため、`K*`やcanonical mapping metadataを追加してもJ-04のKnowledge subsetを変えない。

ただし、実際のLLM Contextにはreference syntax分のoverheadが増える。

そのためConsumer / N-04G-04 generation contractでは、model context windowに対して次を別途考慮する。

```text
selected Knowledge
+ grounding reference overhead
+ generation instruction / schema
+ output reserve
```

N-04G-03ではJ-04 budget metricを変更しない。

---

## 14. Canonical schema impact

### 変更不要

- Object identity
- Knowledge Version
- Statement
- Attribute
- Relation
- Evidence
- Provenance
- Evidence Link
- current Version pointer

新規persistent Fact ID tableも作成しない。

Context-local `K*`と`context_fingerprint`はderived / ephemeral representationであり、canonical Knowledgeではない。

したがってN-04対策でcanonical 52 table構成を変更しない。

---

## 15. Failure / invalid reference semantics

少なくとも次を区別可能にする。

```text
unknown_reference
cross_context_reference
version_mismatch
reference_kind_mismatch
reference_present_but_semantically_unsupported
```

具体的validator result schemaはN-04G-05で定義する。

Consumerはunknown / cross-context referenceをsilentに無視してgrounded扱いしてはならない。

---

## 16. N-04G-04 / G-05への引き渡し

### N-04G-04 Generation / Output Contract

次を決める。

- `K*`をどのoutput field / citation syntaxでLLMへ要求するか。
- human-facing responseとvalidation metadataを分離するか。
- source_fact / interpretationでreferenceを必須にする範囲。
- creative / style / context_limitの表現方法。

### N-04G-05 Validation

次を決める。

- claim→`K*` mappingのpresence validation。
- `K*`→canonical itemのexistence / Context binding検証。
- claimとreferenced content間のsemantic support検証。
- contradictory / unsupported / separation violation判定。

---

## 17. Definition of Done

- [x] 現行Context本文のみ方式を不採用とした。
- [x] canonical ID直接引用方式を一次referenceとして不採用とした。
- [x] Evidence IDをgeneration claimの一次referenceとして不採用とした。
- [x] Context-local reference + canonical identity metadata方式を採用した。
- [x] `K1..Kn`のscope / determinism / non-persistenceを定義した。
- [x] Object field / Statement / Attribute / Relationを共通reference namespaceで扱えるようにした。
- [x] Object / resolved Version bindingを必須化した。
- [x] `context_fingerprint`でContext-local namespaceを識別する方針を固定した。
- [x] claim support referenceとsemantic proofを分離した。
- [x] Evidence / provenanceとの3層関係を定義した。
- [x] Roleplay / Comparison / Creativeで同じreference contractを使うことを固定した。
- [x] J-04 Context Builderのselection / budget semanticsを維持した。
- [x] canonical schema変更不要、新規persistent Fact ID不要と明記した。

N-04G-03をCompleteとする。

---

## 18. Next Task

次のTask:

```text
N-04G-04 [P0]
generation / output contractを設計する
```

N-04G-04では、本Taskで採用した`K*` referenceを、LLM outputのどの部分へどの形式で要求するかを決定する。
