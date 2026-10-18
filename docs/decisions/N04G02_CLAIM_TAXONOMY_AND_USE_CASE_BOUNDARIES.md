# N-04G-02 Claim Taxonomy / Use-case Semantic Boundaries

更新日: 2026-10-18

- Status: **Accepted**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-02 [P0] claim taxonomyと用途別意味境界を確定する`
- Responsibility Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- Failure baseline: `benchmark/n04-ai-use-cases-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 grounded-generationでは、生成出力を**単一のflat labelだけで分類せず、次の2軸で扱う**。

1. **Semantic Role** — その出力単位が何を意味するか。
2. **Grounding Disposition** — SGOKB Contextに対してどのような根拠状態にあるか。

この2軸を採用する理由は、N-04の3用途では次が同時に必要だからである。

- source ObjectについてのfactはContext supportが必要。
- Comparisonではstored factではないinterpretationを許容する。
- Creativeでは新規創作を積極的に許容する。
- Roleplayでは事実を増やさないstylistic phrasingを許容する。
- Context不足を正しく表明すること自体はfailureではない。

したがって、`grounded fact / interpretation / creative addition / unsupported claim`を同じ一次元へ並べるのではなく、**意味種別とgrounding状態を分離する**。

本Taskでは意味境界を確定する。Fact ID、Structured Output、validator実装、retry方式はまだ確定しない。

---

## 2. Analysis unit

評価単位は原則として**atomic semantic unit**とする。

ここでいうatomic semantic unitとは、独立して「何を主張・表現しているか」を判定できる最小単位である。

例:

```text
I am Saber, also known as Artoria Pendragon.
```

は概ね1つのsource factとして扱える。

一方、

```text
I am Saber, and I secretly protect Shirou throughout the Holy Grail War.
```

は少なくとも、

- `I am Saber`
- `I secretly protect Shirou throughout the Holy Grail War`

へ分けて評価する。

文・段落・JSON field等の物理形式はN-04G-04で決める。本Taskでは意味上の最小単位だけを定義する。

---

## 3. Axis A — Semantic Role

### 3.1 `source_fact`

SGOKBが対象としているsource Object / Concept / Work / Character等について、事実として読める命題。

対象例:

- identity / alias
- class / category
- state / property
- relationship
- history / event
- backstory
- setting
- stable personality / motive / capability
- source Concept自体の定義・特徴

例:

```text
Saber is also known as Artoria Pendragon.
Saber is contracted to Shirou.
```

`source_fact`は、一般に「本当に正しいか」ではなく、**今回LLMへ供給したSGOKB Contextでsupportされるか**をgrounding判定の基準とする。

モデルの事前学習知識として正しくても、供給Contextに根拠がなければN-04ではgrounded source factではない。

---

### 3.2 `interpretation`

供給されたgrounded factから導く、比較・要約・意味付け・傾向・説明等の推論。

stored SGOKB factそのものではない。

例:

```text
Based on the supplied summaries, both works emphasize conflict.
```

成立条件:

- 前提となるmaterial factがContextでsupportされている。
- 結論が外部知識を新しいpremiseとして持ち込まない。
- source factそのものとして提示しない。
- 読み手がstored factとinterpretationを区別できる。

「解釈」であると名乗れば何でも許容されるわけではない。Context外の事実をpremiseにしたinterpretationはgrounded interpretationではない。

---

### 3.3 `creative_addition`

ユーザーが求めた創作目的のために、新たに発明・提案した内容。

対象例:

- 新規Character名
- 新規setting
- 新規event
- 新規trait
- 新規dialogue situation
- 新規arc / plot

Creative用途では正常なoutput classであり、**新規detailであること自体をhallucination扱いしない**。

ただし、source Object / Conceptについての既存factであるかのように提示してはならない。

創作範囲はsentence単位で毎回ラベル必須とは限らない。section / field / surrounding contract等により、読み手とvalidatorが「ここからは創作」と一意に認識できればよい。具体的表現方式はN-04G-04で決める。

---

### 3.4 `context_limit`

供給Contextでは必要情報を確認できない、または十分な根拠がないことを表すmeta / epistemic statement。

例:

```text
The supplied context does not provide enough personality detail to state that confidently.
```

Context不足をmodel memoryで埋める代わりに使用する、安全な正常出力classである。

`context_limit`は、SGOKB Knowledge自体が世界全体として不足していると断定するものではない。あくまで**今回供給されたContextでの可用情報**について述べる。

---

### 3.5 `stylistic_expression`

source-worldについて新しいmaterial propositionを追加しない、文体・会話・roleplay上の表現。

例:

```text
Very well.
I understand.
Let us proceed.
```

Roleplayでは自然さのため許容する。

ただし、文体に見えてもsource Characterの安定した性格・過去・能力・関係性・出来事を新たに主張する場合は`stylistic_expression`ではなく`source_fact`または`interpretation`として扱う。

例:

```text
I always put Shirou's safety above my own.
```

は単なる口調ではなく、Characterの恒常的な価値観 / motiveを主張しているため、原則`source_fact`または`interpretation`としてsupport判定が必要である。

---

## 4. Axis B — Grounding Disposition

### 4.1 `supported`

該当semantic unitが供給Context内のKnowledgeでsupportされる。

対象:

- direct fact
- faithful paraphrase
- 意味を変えないnormalization / compression

例:

Context:

```text
Saber is a sword-wielding Servant contracted to Shirou.
```

Output:

```text
I am a Servant who wields a sword, and I am contracted to Shirou.
```

はfaithful paraphraseとして`supported`になり得る。

---

### 4.2 `derived_supported`

主に`interpretation`へ適用する。

- material premisesがすべて`supported`
- 推論がそのpremiseから合理的に導出できる
- 新しいexternal factをpremiseとして持ち込まない

場合に使用する。

`derived_supported`は「SGOKB canonical factである」という意味ではない。

---

### 4.3 `not_applicable`

Contextによるsource factual supportを要求しないsemantic unit。

主な対象:

- valid `creative_addition`
- valid `stylistic_expression`
- valid `context_limit`

ただし、それぞれのclass境界を逸脱してsource factを埋め込んだ場合は`not_applicable`に逃がさず、該当部分をatomic unitへ分解してsupport判定する。

---

### 4.4 `unsupported`

source-worldについてfactとして読めるが、供給Contextからsupportできないもの。

例:

```text
Saber fights as Shirou's protector in the Holy Grail War.
```

がContextに存在しない場合、一般知識として真であるかどうかにかかわらずN-04では`unsupported`である。

また、`interpretation`がunsupported external premiseに依存する場合もgrounded interpretationではなく、validation上はunsupportedとして扱う。

---

### 4.5 `contradictory`

供給Contextと明示的に矛盾するもの。

`unsupported`より強いfailure classとして区別する。

例:

Contextが`Saber is contracted to Shirou`と述べているのに、Outputが`Saber has no contract with Shirou`と述べる場合。

---

## 5. Separation / Presentation rule

Semantic Roleが正しくても、**stored SGOKB factとの境界が読み手に分からない提示はcontract違反になり得る**。

特に次の2つはseparationが必要である。

### `interpretation`

Comparison等では、interpretationをcanonical / stored factとして見せない。

許容:

```text
Based on the supplied facts, this suggests ...
```

不十分:

```text
Both works are fundamentally about ...
```

がstored factなのか推論なのか区別できず、かつContextがその命題を直接保持していない場合。

### `creative_addition`

Creative用途では、新規創作をsource Concept knowledgeとして見せない。

許容:

```text
Creative addition — Character arc:
...
```

または同等にscopeが一意なsection / field。

不十分:

source Concept説明と新規eventを同じ未区分の事実列として混ぜること。

具体的なlabel / field / schemaはN-04G-04で決める。本Taskで必須なのは**意味上の分離可能性**である。

---

## 6. Use-case Boundary — Case 1 Roleplay

### 6.1 許容

- `source_fact + supported`
- `stylistic_expression + not_applicable`
- 必要な場合の`context_limit + not_applicable`
- ごく限定的な`interpretation + derived_supported`（明確に一時的判断・推論として表現され、Characterのcanonical traitへ昇格しないもの）

例:

```text
I am Saber, also known as Artoria Pendragon.
```

→ `source_fact / supported`

```text
Very well. I understand.
```

→ `stylistic_expression / not_applicable`

### 6.2 要注意 / 要分離

現在の会話状況に対する一時的な意志・応答が、Characterの恒常的性格やcanonical motiveに見える場合。

例えば、

```text
I would prefer to proceed cautiously here.
```

が単なる現在会話上のresponseならstylistic / situational expressionとして扱える可能性がある。

一方、

```text
I have always been cautious because of my past.
```

はbackstory / stable personality assertionを含むためsource factとしてsupportが必要である。

### 6.3 禁止

- `source_fact + unsupported`
- `source_fact + contradictory`
- Context外backstory / franchise event / hidden identity / relationship detail
- personality coverage不足を恒常的traitとして補完すること
- creative embellishmentをcanonical eventのように混入すること

Roleplay用途はCreative用途ではないため、source Characterに新しいcanonical-looking eventを自由創作することは許容しない。

---

## 7. Use-case Boundary — Case 2 Comparison

### 7.1 許容

- 両Workの`source_fact + supported`
- `interpretation + derived_supported`
- `context_limit + not_applicable`
- 可読性のための`stylistic_expression + not_applicable`

Comparisonの本質上、interpretation自体は正常かつ必要である。

### 7.2 Interpretationの必須条件

- source Work A / Bのmaterial premiseがContextでsupportされる。
- Similarity score自体をtruth / confidence / preference probabilityへ読み替えない。
- external franchise knowledgeをpremiseに使わない。
- stored factではなく比較上の推論だと区別できる。

### 7.3 禁止

- Context外の設定・登場存在・世界観・event等をfactとして補うこと
- unsupported external factを根拠にcomparisonを成立させること
- interpretationをcanonical SGOKB factとして提示すること
- Similarity scoreから意味上のtruth claimを作ること
- `creative_addition`で不足比較材料を埋めること

---

## 8. Use-case Boundary — Case 3 Creative

### 8.1 許容

- source Conceptについての`source_fact + supported`
- Conceptの組み合わせ方に関する`interpretation + derived_supported`
- 新規Character / setting / event / trait / arc等の`creative_addition + not_applicable`
- `context_limit + not_applicable`
- `stylistic_expression + not_applicable`

### 8.2 Creative separation

新規創作は積極的に許容するが、次を明確に区別する。

```text
SGOKB supplied concept knowledge
vs
new creative material
```

新規name / event / setting等についてSGOKB Context supportを要求しない代わりに、source Concept由来のstored factとして誤認させてはならない。

### 8.3 禁止

- source ConceptについてContext外factを追加すること
- source Conceptに新しいdefinition / history / theoryを付け足し、それをSGOKB factとして扱うこと
- creative additionをSGOKB canonical factのように提示すること

Creative用途では「新しい内容がある」ことはfailureではない。**source knowledgeと創作の境界が壊れること**がfailureである。

---

## 9. v1 Failure Mapping

### Case 1 — Saber Roleplay

Context外で追加された:

- Holy Grail WarでShirouのprotectorとして戦う
- Artoriaのidentityが作中で広く知られていない

分類:

```text
Semantic Role: source_fact
Grounding: unsupported
Result: critical grounding failure
```

単なるroleplay styleではない。source Characterのbackstory / world stateを主張しているためstrict support対象である。

---

### Case 2 — Similar Work Comparison

Context外で追加された:

- magiがhistorical Heroesを召喚する
- Hollowsがmalevolent spirits
- Soul Reapersがhuman worldとafterlifeのbalanceを維持する

分類:

```text
Semantic Role: source_fact
Grounding: unsupported
Result: critical grounding failure
```

また、

```text
both protagonists gain extraordinary powers
```

は比較上のinterpretationとして扱う余地があるが、そのpremiseが供給Contextでsupportされていなかったため:

```text
Semantic Role: interpretation
Grounding: unsupported
Result: grounding failure
```

さらに、比較上のinterpretationとstored factのpresentation separation不足があったため、**separation contract violation**も併発した。

---

### Case 3 — Concept Creative Character

新規CharacterやArc event自体:

```text
Semantic Role: creative_addition
Grounding: not_applicable
```

であり、hallucinationではない。

一方、`Arc outline`の新規eventについてcreative scopeが明確でなかったため:

```text
Semantic Role: creative_addition
Grounding: not_applicable
Presentation: insufficient separation
Result: creative-separation contract violation
```

source Conceptについてunsupported factは確認されていない。

このためCase 3 failureはCase 1 / 2のgrounding failureとは意味上分離できる。

---

## 10. Normative shorthand

後続Taskでは必要に応じて次の短縮表現を使用してよい。

```text
grounded_fact
  = source_fact + supported

grounded_interpretation
  = interpretation + derived_supported + properly separated

valid_creative_addition
  = creative_addition + not_applicable + properly separated

valid_context_limit
  = context_limit + not_applicable

valid_stylistic_expression
  = stylistic_expression + not_applicable

unsupported_claim
  = source_fact + unsupported
    or interpretation dependent on unsupported premise

contradictory_claim
  = source_fact + contradictory

separation_violation
  = semantic role自体は許容可能だが、stored factとの境界が曖昧
```

このshorthandはcanonical Knowledge schemaのentity / enumを意味しない。Grounded-generation contract上の論理語彙である。

---

## 11. Design implications for later tasks

### N-04G-03 Context grounding / reference contract

少なくとも`source_fact`と`interpretation`のpremiseをContextへ追跡可能にする方式を検討する。

`creative_addition`へcanonical evidenceを捏造して付けない。

### N-04G-04 Generation / output contract

LLM出力でsemantic roleとseparationをどの程度明示させるかを決める。

特に:

- interpretationとstored fact
- creative additionとsource knowledge

の区別を機械検証可能にするかを検討する。

### N-04G-05 Validation

validatorは、少なくとも次を区別できる必要がある。

- supported source fact
- unsupported / contradictory source fact
- grounded interpretation
- unsupported premiseを使うinterpretation
- valid creative addition
- separation violation

### N-04G-06 Failure handling

`unsupported` / `contradictory` / `separation violation` / `insufficient context`を同じfailureとして扱うか、別actionにするかを決める。

---

## 12. Explicit non-decisions

本Taskでは以下をまだ決めない。

- Fact ID / Statement ID方式
- canonical IDをLLMへ見せるか
- Structured Output採用
- JSON schema
- inline citation形式
- validatorのalgorithm
- LLM judge採用
- retry回数
- retry model policy
- automatic repair

これらはN-04G-03〜G-06で決める。

---

## 13. Completion check

N-04G-02の完了条件を次の通り満たした。

- [x] claim / output semantic分類と各定義が確定した。
- [x] grounding状態をsemantic roleから分離した。
- [x] Roleplayの許容styleとunsupported backstoryの境界を定義した。
- [x] Comparisonのstored fact / interpretation / unsupported external factの境界を定義した。
- [x] Creativeのsource Concept knowledge / creative additionの境界を定義した。
- [x] Context不足を安全に表明する`context_limit`を正常classとして定義した。
- [x] Case 1〜3のv1 failureを同一taxonomyで説明した。
- [x] Fact ID / Structured Output / validator / retryを先取り決定していない。

N-04G-02を**Complete**とする。

次Task:

```text
N-04G-03 [P0]
Context grounding / reference contractを設計する
```
