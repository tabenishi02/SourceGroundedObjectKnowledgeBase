# N-04G-14 Atomic Claim / Semantic-Role Boundary Redesign

更新日: 2026-10-19

- Status: **Complete**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Root cause: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- Existing taxonomy: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- Existing output contract: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- Existing validation design: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- Previous design freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Remediation task master: `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`

---

## 1. Decision

N-04 post-G12 remediationでは、既存G-02/G-04/G-05の「atomic semantic unit」設計意図を維持しつつ、instruction-onlyだった境界を**fail-closedなnormative invariant**へ昇格する。

主要Decisionは次である。

1. **1 validation unit = 1 atomic semantic proposition**を必須とする。
2. Atomicityは文・句読点等の表面的な文法単位ではなく、**support verdictを独立に変え得るmaterial propositionの最小単位**で定義する。
3. material propositionとsupport不要contentを同一unitへ混在させない。異なるgrounding policyを必要とするcontentは別unitへ分離する。
4. `semantic_role`はgeneratorの宣言であり、grounding authorityではない。**content materiality / role boundary判定がmodel-declared roleより優先する。**
5. source-world material propositionを`stylistic_expression` / `context_limit` / `creative_addition`へ逃がすことを禁止する。
6. N-04 v3 formal baselineでは、**model-authored `stylistic_expression`を禁止する。** Roleplayの自然なsurface formはsupported `source_fact`のfirst-person paraphrase等で表現する。
7. `context_limit`は今回供給されたContextの可用性に関するmeta / epistemic propositionだけに限定する。
8. `creative_addition`は新規創作内容だけに限定し、source Object / Concept / Work / Characterについて新しいfactを説明してはならない。
9. `interpretation`はgrounded premiseから導くconclusionに限定し、source factual premiseを同一textへ埋め込まない。premiseの物理参照方式はN-04G-16で確定する。
10. non-atomic / role-ambiguous unitをsemantic judgeへそのまま渡して1 verdictで救済しない。
11. post-hoc atomizerはdebug / audit補助には使用可能だが、唯一のgrounding authorityにはしない。
12. Atomicity / role-boundary Gateが`NON_ATOMIC`または`INDETERMINATE`の場合、後段semantic verifierの`entailed` / `role_valid`はoverrideできない。

概念フロー:

```text
Untrusted generator unit
        ↓
Atomicity / semantic-role boundary gate
  ├─ ATOMIC + ROLE_VALID
  │      ↓
  │   support / derivation validation
  │
  ├─ NON_ATOMIC / ROLE_VIOLATION
  │      ↓
  │   validation failure -> retry candidate
  │
  └─ INDETERMINATE
         ↓
      fail-closed / no grounded PASS
```

本Decisionはproduction codeを変更しない。実装はN-04G-19で行う。

---

## 2. Problem statement

G-12 Case 1では、次の2経路でfalse acceptanceが発生した。

### 2.1 Multi-proposition compression

```text
supported clause
+
unsupported Holy Grail War clause
```

が同一`unit.text`へ混在し、semantic validatorがunit全体へ1つの`entailed` verdictを返した。

既存G-04/G-05はatomic unitを要求していたが、実装上はgenerator instructionだけでありGateではなかった。

### 2.2 Role escape

relationship / duty / loyalty等のmaterial source-world propositionが`stylistic_expression`として宣言され、`support_refs=[]`のまま`role_valid`を通過した。

既存G-02/G-05の意味境界は正しかったが、support-free roleの誤分類をfail-closedに止める第二Gateがなかった。

したがってG-14では、semantic verifierの能力向上より前に、**構造・役割境界で防げるfalse acceptanceをsemantic verifierへ委ねない**設計へ変更する。

---

## 3. Terminology

### 3.1 Proposition

truth / falsity、support / unsupported、derived / not-derived等を独立して評価できる意味内容を`proposition`と呼ぶ。

文法上の1文とpropositionは一致しない。

例:

```text
I am Saber, and I secretly protect Shirou throughout the Holy Grail War.
```

は1文だが、少なくとも次の2 propositionを含む。

```text
P1: I am Saber.
P2: I secretly protect Shirou throughout the Holy Grail War.
```

### 3.2 Material proposition

grounding / semantic-role判定上、独立して意味評価する必要があるpropositionを`material proposition`と呼ぶ。

最低限次を含む。

- source Object / Concept / Work / Character等についてのfact
- relationship / event / history / capability / personality / motive / state / category等
- comparison / interpretation上の結論
- source Concept等のdefinition / featureに関する説明
- supplied Contextの可用性に関するepistemic claim
- Creative用途で生成する新規Character / setting / event / trait / arc等

単なる句読点、heading、separator、接続表現等はmaterial propositionではない。

### 3.3 Source-world material proposition

対象source Object / Concept / Work / Characterまたはその世界・関係・出来事について、事実として読めるmaterial propositionを指す。

これは原則`source_fact`としてsupport対象となる。

### 3.4 Atomic unit

**1つのvalidation unit内に、独立して異なるgrounding verdictを持ち得るmaterial propositionが2つ以上存在しないunit**をatomic unitとする。

Normative test:

> unitの一部分だけをunsupported / contradictory / role-mismatchedとして判定し、残りをsupported / validとして保持できるなら、そのunitはnon-atomicである。

この定義は句読点や`and`の有無に依存しない。

### 3.5 Homogeneous grounding policy

1 unit内のmaterial contentは、同じsemantic role / grounding policyで評価可能でなければならない。

例えば次は同一unitへ混在させない。

```text
source_fact + context_limit
source_fact + creative_addition
source_fact + interpretation conclusion
creative_addition + source Concept fact
context_limit + source-world fact
```

---

## 4. Normative atomicity invariants

### A1 — One material proposition per unit

各unitは原則1つのmaterial propositionだけを持つ。

```text
1 unit -> 1 material proposition
```

複数K referenceで共同supportされる1 propositionは許容する。

したがって、atomicityは:

```text
1 proposition = 1 support_ref
```

を意味しない。

### A2 — Independent verdict split test

同一text内で部分ごとに異なるgrounding verdictが成立し得る場合はnon-atomicとする。

例:

```text
I am Saber and I protect Shirou throughout the Holy Grail War.
```

`I am Saber`だけsupportされ、後半がunsupportedならnon-atomicである。

### A3 — Grounding-policy homogeneity

同一unitへ異なるgrounding policyを必要とするcontentを混在させない。

例:

```text
The context does not describe her personality, but she always protects Shirou.
```

前半は`context_limit`、後半は`source_fact`であり、1 unitとしてはinvalidである。

### A4 — Surface style is not a second proposition

supported propositionをfirst-person / polite / conversational surface formで表現すること自体は許容する。

例:

```text
I am Saber, also known as Artoria Pendragon.
```

が1 source factのfaithful paraphraseであるなら、Roleplay用の一人称表現であることだけを理由に別`stylistic_expression`へ分離しない。

ただしsurface styleが新しいtruth-apt contentを追加した時点で別material propositionとなる。

### A5 — Atomicity is a gate, not advice

Generator promptでatomicityを要求するだけでは不十分である。

後段validationは、atomicity Gateを通過していないmaterial unitをsupport判定へ進めない。

### A6 — Ambiguity does not PASS

atomicかnon-atomicか安全に確定できないunitは`INDETERMINATE`として扱い、grounded PASSへ昇格させない。

---

## 5. Machine-checkable invariant

自然言語のatomicityを完全にdeterministic ruleだけで判定することは前提にしない。

代わりにpipeline上のmachine-checkable invariantを次で定義する。

```text
Every material unit MUST have an atomicity verdict:
  ATOMIC
  NON_ATOMIC
  INDETERMINATE

Only ATOMIC may enter material support / derivation validation.
NON_ATOMIC and INDETERMINATE may never become grounded PASS.
```

つまり、machine-checkableであるべき対象は「自然言語を完全に機械分解できること」ではなく、**Atomicity Gateを未通過のunitがsupport PASS経路へ入れないこと**である。

実装上の候補検出は後続Taskで次を組み合わせてよい。

- deterministic compound-risk detection
- bounded atomicity classifier
- structured-output constraints
- adversarial fixtureによる回帰検証

ただし、どの実装でも`INDETERMINATE -> PASS`は禁止する。

---

## 6. Post-hoc atomizer policy

LLM / NLPによるpost-hoc atomizerで、generatorのunitを後段分解する方式を唯一のgrounding proofにはしない。

理由:

- atomizer自身がclaimを落とす可能性がある。
- unsupported clauseのomissionがfalse acceptanceにつながる。
- original rendered textとのmappingが曖昧になる。
- generator contract違反をsilent repairしてしまう。

許容用途:

```text
debug
failure explanation
audit
adversarial analysis
candidate split suggestion for retry feedback
```

禁止用途:

```text
original non-atomic unit
  ↓ silent atomization
subsetだけ検証
  ↓ original full textをrender
```

Atomicity violationは原則generatorへ明示的に返し、再生成させる。

---

## 7. Content-first semantic-role rule

`semantic_role`はgeneratorが宣言するmetadataであり、grounding authorityではない。

Normative priority:

```text
unit.text content semantics
        ↓
materiality / source-world proposition判定
        ↓
role boundary判定
        ↓
declared semantic_roleとの整合
```

次は禁止する。

```text
model declares support-free role
        ↓
therefore support not required
```

正しくは:

```text
content contains source-world material proposition
        ↓
source_fact-compatible support path required
        ↓
support-free declared roleなら ROLE_BOUNDARY_VIOLATION
```

Validatorはrole mismatchをsilentに`source_fact`へreclassifyして救済しない。

理由:

- support refsが不足している可能性が高い。
- mixed-role unitを隠す。
- generator contract違反を見えなくする。

role mismatchは明示failureとしてretry対象にする。

---

## 8. Role boundary redesign

## 8.1 `source_fact`

対象:

- source Object / Concept / Work / Character等について事実として読めるproposition
- identity / alias / class / property / state
- relationship
- history / event / backstory
- capability
- stable personality / motive / value
- source Conceptのdefinition / feature

Normative rules:

1. 1 unit = 1 atomic source-world proposition。
2. support refを必要とする。
3. multiple support refsは、1 propositionを共同supportする場合に許容する。
4. first-person / roleplay phrasingは許容するが、新しいmaterial propositionを追加しない。
5. unsupported detailが同居すればunit全体をatomic source factとして扱わない。

---

## 8.2 `interpretation`

`interpretation`はgrounded source factから導く**conclusion**を表す。

N-04G-14では次を固定する。

1. interpretation unit自身は1 atomic conclusionとする。
2. source factual premiseをinterpretation textへ再埋め込みしない。
3. premiseは別のvalidated source fact unitとして存在することを前提とする。
4. hidden external premiseを持ち込まない。
5. premiseとの物理的参照方式、derivation verifier policyはN-04G-16で確定する。

許容イメージ:

```text
U1 source_fact: Work A has X.
U2 source_fact: Work B has Y.
U3 interpretation: This creates a contrast in how the two works frame conflict.
```

避ける形:

```text
Because Work A has X and Work B has Y, and both protagonists gain hidden powers,
these works are similar in ...
```

後者はsource premise、外部premise、interpretation conclusionが同一textへ混在し得る。

---

## 8.3 `creative_addition`

Creative用途で新しく発明する内容を表す。

許容:

- new Character name
- new setting
- new event
- new trait
- new arc / plot
- new dialogue situation

Normative rules:

1. source Object / Concept / Work / Characterについて新しいfactを説明しない。
2. source Concept名を入力由来の参照ラベルとして言及すること自体は可能だが、そのdefinition / featureを新たに断定しない。
3. source knowledgeの説明が必要なら別`source_fact` unitへ分離する。
4. creative addition自体も、role boundaryを明確にするため原則atomic unitとして表現する。
5. source factとcreative propositionの混在unitは禁止する。

例:

許容:

```text
Creative addition: The new character is named Rina.
```

不許可:

```text
Tsundere means she must secretly be affectionate, so Rina always hides her love.
```

source Conceptのdefinition claimとnew Character factが混在している。

---

## 8.4 `context_limit`

今回供給されたContextで確認できる情報の限界を表すmeta / epistemic propositionである。

Normative scope:

```text
what the supplied context does / does not establish
```

許容:

```text
The supplied context does not provide enough personality detail to state that confidently.
```

禁止:

```text
The supplied context does not say much about her personality,
but she is deeply loyal to Shirou.
```

後半はsource-world propositionであり、同一unitへ混在させない。

G-15では、free-form textを残すかstructured reason code + deterministic rendererへ変更するかを決める。

---

## 8.5 `stylistic_expression`

### v3 formal baseline decision

**model-authored `stylistic_expression`を禁止する。**

理由:

1. G-12でmaterial relationship / duty / loyalty claimのescape hatchとして実際にfalse acceptした。
2. Roleplayの自然さはsupported `source_fact`のfirst-person / conversational paraphraseで維持できる。
3. `Very well.`等のpure styleを独立semantic roleとしてmodelに生成させるacceptance上の必要性が低い。
4. support-free roleを減らすことでrole classifierのfalse positive surfaceを縮小できる。

扱い:

- historical v1/v2 evidenceのtaxonomy語彙としては保持する。
- N-04 v3 generation contractではgeneratorが出力できないroleとする。
- rendererが追加できるのはG-04/G-15で許可されたdeterministic fixed headings / separators等だけであり、任意のroleplay proseを追加しない。

将来、production use caseで純粋なstylistic unitが必要になった場合は、N-04 v3 acceptance後に別Decisionとして再導入を検討する。

---

## 9. Mixed-role unit policy

1 unit内へ複数role相当のmaterial contentを混ぜない。

特に禁止する組合せ:

```text
source_fact + interpretation
source_fact + creative_addition
source_fact + context_limit
creative_addition + source Concept fact
context_limit + source-world fact
```

unitがmixed-roleか安全に判定できない場合も`INDETERMINATE`へ倒す。

separationはpresentationだけの問題ではない。

```text
visible headingで分かれている
```

だけでは、1 unit内部のsemantic mixingを救済しない。

---

## 10. Atomicity / role Gate result model

論理結果を最低限次で扱う。

```text
atomicity:
  ATOMIC
  NON_ATOMIC
  INDETERMINATE

role_boundary:
  ROLE_VALID
  ROLE_VIOLATION
  INDETERMINATE
```

support / derivation validationへ進める最低条件:

```text
atomicity == ATOMIC
AND
role_boundary == ROLE_VALID
```

禁止:

```text
NON_ATOMIC + semantic judge entailed -> PASS
ROLE_VIOLATION + semantic judge role_valid -> PASS
INDETERMINATE + downstream positive verdict -> PASS
```

後段validatorは前段structural / semantic-boundary failureをoverrideしない。

---

## 11. Detection policy boundary

G-14ではnormative semanticsを確定し、production algorithmの詳細はまだ実装しない。

実装時は少なくとも次の二層を想定する。

```text
Layer 1: deterministic compound / role-risk checks
Layer 2: bounded atomicity / role classifier for unresolved cases
```

Layer 1 candidate:

- multi-sentence / list-like unit
- explicit multiple independent clauses
- role-specific forbidden field combinations
- support-free role with support refs
- source_fact without support refs
- v3で禁止された`stylistic_expression`

ただし単純な`and`文字列検出だけをatomicity proofにしない。

Layer 2はfalse positive / false negativeを持つfallible componentとして扱い、判定不能をPASSへ倒さない。

具体的model / library / verifier構成はG-16/G-19へ送る。

---

## 12. Relationship with G-02 / G-04 / G-05 / G-07

### G-02

基本taxonomyの意味意図は維持する。

ただしv3 formal baselineでは次を強化する。

- content-first role validation
- support-free role escape禁止
- `stylistic_expression` model-authored出力禁止
- mixed-role unit禁止

### G-04

`units[]`をvalidation対象かつrender sourceとする基本方針は維持する。

ただし「原則1つのmaterial semantic proposition」は、v3では**必須invariant**へ変更する。

具体的schema version / shapeはG-15で決める。

### G-05

次の既存原則を物理化する。

```text
all material propositions must be supported
```

v3では:

```text
all rendered material propositions
  -> explicit unit boundary
  -> atomicity PASS
  -> role boundary PASS
  -> applicable support / derivation validation PASS
```

とする。

### G-07

G-07はv2以前のDesign Freezeとして履歴保持する。

本DecisionはG-07をsilent rewriteしない。

G-14〜G-17の変更はG-18 Post-G12 Design Freezeで統合し、v3 contractとして再freezeする。

---

## 13. G-12 Case 1 desk replay

保存済みG-12 Case 1 failure shapeへ本Decisionを机上適用する。

### Failure shape A — supported + unsupported in one unit

Observed shape:

```text
K5-supported Saber clause
+
unsupported Holy Grail War material detail
```

v3 desk result:

```text
Independent verdict split possible
-> NON_ATOMIC
-> support validationへ進めない
-> no grounded PASS
```

Phi-4等がunit全体へ`entailed`を返す経路自体を前段で閉じる。

### Failure shape B — material claim disguised as `stylistic_expression`

Observed shape:

```text
semantic_role = stylistic_expression
support_refs = []
text = relationship / duty / loyaltyについてのmaterial source-world claim
```

v3 desk result:

```text
stylistic_expression is forbidden in v3 model output
AND
content contains source-world material proposition
-> ROLE_VIOLATION
-> no support-free path
-> no grounded PASS
```

semantic judgeが`role_valid`を誤返却しても前段Gateをoverrideできない。

### Desk replay conclusion

G-12 Case 1の主要2 false-accept経路は、本Decisionのatomicity / role boundaryでいずれもFAIL-CLOSEDになる。

したがってG-14の目的:

```text
supported clause + unsupported clause
```

を1 verdictでPASSさせないことは、設計上満たす。

---

## 14. Required downstream work

### N-04G-15 — Output / presentation contract hardening

引き渡すDecision:

- v3 schemaから`stylistic_expression`をmodel output roleとして除外する。
- 1 unit = 1 atomic propositionをschema / parser / validator contractへ反映する。
- roleごとのshapeを可能な限りschemaへencodeする。
- `context_limit`のfree-form text vs reason codeを決定する。
- arbitrary labelをsemantic bypassにしない。

### N-04G-16 — Semantic validation architecture

引き渡すDecision:

- Atomicity / role-boundary PASS後だけsemantic supportへ進む。
- interpretation textはconclusion-onlyとし、premiseを別validated unitへ物理化する。
- atomicity / role classifier自体もfallibleとして扱う。
- validator disagreement / indeterminateをPASSへ倒さない。

### N-04G-17 — Material / terminal / render gate

引き渡すDecision:

- rendered material propositionはすべてatomic + role-valid + applicable grounding PASSでなければならない。
- support-free roleの存在だけをmaterial sufficiencyとみなさない。

### N-04G-18 — Post-G12 Design Freeze

G-14〜G-17を統合し、v3 contract versionと旧G-07との変更関係を明示する。

---

## 15. Explicit non-decisions

本Taskでは次をまだ確定しない。

- v3 JSON Schemaの具体形
- output contract version名
- provider-specific Structured Output設定
- atomicity classifierの具体model
- MiniCheck / AlignScore等のproduction採用
- source-fact verifier ensemble
- interpretation `premise_unit_ids`の具体schema
- retry feedback JSON shape
- material sufficiency rule
- terminal / renderer binding
- v3 formal harness

これらはG-15〜G-21で扱う。

---

## 16. Completion check

N-04G-14完了条件を次の通り満たした。

- [x] atomicityのmachine-checkable invariantを定義した。
- [x] material propositionのrole逃避対策を定義した。
- [x] G-05 `all material propositions supported`を物理実装可能なGate順序へ具体化した。
- [x] non-atomic / ambiguous unitのfail-closed方針を定義した。
- [x] post-hoc atomizerを唯一authorityにしない方針を確定した。
- [x] `stylistic_expression`をv3 formal baselineでmodel-authored禁止とした。
- [x] `context_limit` / `creative_addition` / `interpretation`の境界を強化した。
- [x] G-12 Case 1保存failure shapeへ机上適用し、新設計ならgrounded PASSしないことを確認した。
- [x] production codeを変更していない。

N-04G-14を**Complete**とする。

次Task:

```text
N-04G-15 [P0]
Output schema / presentation / deterministic rendering contractをhardeningする
```
