# Source Grounded Object Knowledge Base — Facet Vocabulary Review

更新日: 2026-10-12

- Task: `E-02B [P0] Facet vocabularyを横断統合する`
- Status: Complete
- Inputs:
  - `docs/design/FACET_TAXONOMY_SURVEY.md`
  - `docs/design/SEMANTIC_FACET_SCHEMA.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `src/sgokb/migrations/004_semantic_facets.sql`
- Validated by: `E-02C [P0] Class / Facet境界gold cases` — Complete

## 1. 目的

E-02Aでは初期Class Registryの全62 ClassについてKnowledge観点を列挙した。その結果、Classごとに局所的な名前をそのままFacet Registryへ追加すると、`purpose / function / use / usage / application`、`history / evolution / development`、`structure / architecture / organization / components`等の近義語が別IDとして増殖する危険が確認された。

本書ではE-02Aの候補を横断比較し、次を確定する。

1. Facet vocabularyの命名・再利用原則。
2. 近義候補を統合する場合と、意味差を維持して別Facetにする場合の境界。
3. shared / family-inherited / class-specific profileの使い分け。
4. 初期18 Facetの維持・意味修正・廃止要否。
5. E-02Cでgold case検証する**Facet vocabulary freeze候補**。
6. E-02C後に必要となるRegistry / profile変更案。

本TaskではMigration 004を書き換えず、runtime Facet Registryも変更しない。E-02Cで境界事例を検証してから物理Registryへ反映する。

---

## 2. Vocabulary設計原則

### 2.1 Facetは「Class専用column名」ではない

Facet DefinitionはClassから独立したRegistry entryであり、意味が同じなら異なるClassでも同じFacet IDを再利用する。

例:

```text
Organization.history
Series.history
Place.history
Software.history
Language.history
```

これらは対象Classが異なっても、「そのObjectの時間的な成立・変遷・重要な過去」を説明するという意味契約を共有できるため、同じ`facet:history`を使う。

### 2.2 同じ英単語へ無理に統合しない

語が近くても、検索・比較時に意味を混同すると不利益が大きいものは分離する。

特に次は別Facetとする。

- `purpose`: なぜ存在するか、何を目指すか。
- `function`: 何をするものか、どの機能を果たすか。
- `usage`: 外部主体がどう利用・適用するか。
- `history`: Objectの過去・変遷。
- `chronology`: Object内部の時間順序・出来事配置。
- `effects`: 因果的・実際的な結果。
- `implications`: 論理的・概念的・解釈上の含意。

### 2.3 FacetをRelation一覧の代用品にしない

`members`, `participants`, `users`, `components`, `included_works`, `owners`等をそのままFacet Definitionにしない。

正本接続はRelationで保持し、Facetが存在する場合は、Relation集合についての**意味的な特徴・パターン・解釈**をStatementとして保持する。

既存`characters` / `relationships` / `related_concepts`もこの規則に従う。

### 2.4 FacetをAttribute一覧の代用品にしない

数値仕様、日付、座標、版番号、型番、識別子等はtyped attributeへ置く。

例えば`Product.specifications`という巨大Facetを新設せず、数値specはAttribute、意味的な特徴は`properties` / `design` / `function`へ分離する。

### 2.5 `overall`はcatch-allではない

`overall`は、Object全体にまたがる概要的Knowledgeや複数Facetへ自然に分割できない少量の横断Knowledgeを保持するcommon Facetとする。

次を禁止する。

- 専用profile未設計ClassのKnowledgeを恒久的にすべて`overall`へ入れる。
- 分類可能な内容を「迷ったらoverall」へ送る。
- `overall`をClassごとの非構造化Document置き場にする。

### 2.6 Facet追加基準

新Facet候補は原則として次の複数を満たす場合に採用する。

- 複数Statementをまとめる継続的な意味観点である。
- 複数Objectで繰り返し出現する。
- Relation / Attributeだけでは意味内容を十分表現できない。
- Search / similarity / Context Builderで独立観点として価値がある。
- 既存Facetへ入れると意味幅が過度に広がる。

---

## 3. 初期18 Facetの判定

E-02でseedした18 Facetは**すべて維持**する。ID / keyのrename・archive候補はE-02B時点ではない。

| Facet | 判定 | 意味境界の補足 |
|---|---|---|
| `overall` | keep | Object全体の概要・横断Knowledge。未分類Knowledgeの恒久置き場にはしない |
| `personality` | keep | 人格・性格傾向。一般的`properties`とは分離 |
| `values` | keep | 重視する価値・原則・優先順位。Ideology等でも再利用可能 |
| `motivation` | keep | Agent個体の動機説明。`Motivation` Object Classとは別責務 |
| `behavior` | keep | 行動・応答パターン。Relation一覧や一回のEventではない |
| `relationships` | keep | Relation群の性質・パターン・意味。edge一覧そのものではない |
| `role` | keep | Narrative / social / functional roleの説明。RoleConcept membershipはRelationで保持可能 |
| `themes` | keep | 主題・motifの説明。Theme ObjectとのRelationと併用可能 |
| `abilities` | keep | Agentが持つ能力群の要約・性質。Ability / Skill Object Relationの代替ではない |
| `worldview` | keep | Workが提示・表現する世界観・価値枠組み。`World` Objectの物理設定とは分離 |
| `narrative` | keep | 物語構造・展開・語りの意味観点 |
| `tone` | keep | 表現上の調子・mood・presentation character |
| `characters` | keep | cast一覧ではなく、character ensemble・characterizationの意味的説明 |
| `definition` | keep | Concept / Capability等の意味境界・定義 |
| `properties` | keep | 対象の比較的安定した性質・特徴。数値specはAttributeへ分離 |
| `implications` | keep | 概念的・論理的・解釈上の含意。因果`effects`とは分離 |
| `related_concepts` | keep | Concept間の意味的近傍・関係性の説明。Relation一覧そのものではない |
| `examples` | keep | 意味理解のための代表例。Object instance Relationと併用可能 |

既存Facetを維持することでMigration 004のstable Facet IDを壊さず、E-02Aで見つかった不足は新規shared Facetで補う。

---

## 4. 近義語統合の決定

### 4.1 purpose / function / use / usage / application

**決定: 3つに分離する。**

| Canonical | 意味 | 吸収する候補 |
|---|---|---|
| `purpose` | 存在目的・目標・intended reason | goal（Object全体の目的として扱う場合） |
| `function` | 対象が果たす機能・作用 | functional role, primary function |
| `usage` | 利用方法・適用・運用のされ方 | use, application, practice, operationの利用側説明 |

`purpose`と`function`を統合するとOrganizationの「設立目的」とArtifactの「機能」が同一意味になるため不採用。

### 4.2 history / evolution / development / biography / career

**決定: 基本は`history`へ統合し、biographical contextは`background`を併用する。**

- `history`: 時間的な成立・変遷・重要な過去。
- `background`: 個体・Agent等の成立背景、経歴の前提、文脈。
- `evolution` / `development`: 独立Facetにせず、通常`history`内Statementとする。
- Personのcareerは`history + activities + role`で表現し、`career` Facetを初期vocabularyへ追加しない。

生物学的evolution等、それ自体が独立Knowledge対象ならProcess / Concept / Relationとして扱う余地を残す。

### 4.3 structure / architecture / organization / components / morphology

**決定: canonicalは`structure`。**

- architecture: Software / Systemのtechnical structureとして`structure`へ入れる。
- organization: Organizationの内部構造として`structure`へ入れる。
- components: component edgeはRelation。構成原理・配置の説明を`structure`へ入れる。
- morphology: Taxon等では形態的構造を`properties`または`structure`へ配置し、初期Facetとして独立させない。

### 4.4 properties / characteristics / traits / features / specifications

**決定: descriptive semanticsは`properties`へ統合する。**

- characteristics / descriptive traits / features → `properties`
- numeric specification → typed attribute
-人格的trait → `personality`またはTrait Object Relation
- `Trait` Object自体の性質 → `properties`

### 4.5 rules / constraints / conditions / limits

**決定: 3つに分離する。**

- `rules`: 規範・規則・体系として「どうでなければならないか」。
- `constraints`: 能力・System・Process等の制約・限界。
- `conditions`: 発生・成立・実行に必要な状況・前提。
- `limits` → `constraints`へ統合。

### 4.6 mechanism / procedure / behavior / process

**決定: `mechanism`, `procedure`, `behavior`を分離する。**

- `mechanism`: なぜ・どの原理で作動するか。
- `procedure`: どの順序・手順で実行するか。
- `behavior`: 対象が実際にどのようなパターンで振る舞うか。
- `process`はClass名でありFacet名にはしない。
- `stages`は通常`procedure`へ統合し、独立ObjectとなるstageがあればRelationへ出す。

### 4.7 causes / drivers / triggers / conditions

**決定: `causes`と`conditions`へ整理する。**

- `causes`: 因果的に発生を生む要因。
- `conditions`: 成立を可能・必要にする条件。
- triggers / driversは文脈により`causes`または`conditions`へ配置する。
- Agent固有の心理的driverは既存`motivation`を優先する。

### 4.8 effects / outcomes / implications

**決定: `effects`と既存`implications`を分離し、`outcomes`は`effects`へ統合する。**

- `effects`: 実世界・物語世界で生じる因果的結果。
- outcomes: Event / Process終了後の結果として`effects`へ含める。
- `implications`: 概念的・論理的・解釈上の含意。

### 4.9 relationships / dynamics / interactions

**決定: persistent inter-Object semanticsは既存`relationships`へ寄せる。**

- dynamics: Agent / Group間の関係パターンなら`relationships`。
- System内部の動的挙動なら`behavior` / `mechanism`。
- 個々のinteraction eventはRelation / Event / Statement。
- `interactions`を初期canonical Facetへ追加しない。

### 4.10 chronology / history / timeline

**決定: `chronology`と`history`を分離し、`timeline`はFacetにしない。**

- `chronology`: 内部の出来事・phase・branch等の時間順序。
- `history`: 対象自体の成立・変遷・過去。
- 参照可能な時間系列そのものは`Timeline` Object。

### 4.11 scope / identity / overall

**決定: `scope`を追加し、`identity`はFacet化しない。**

- `scope`: 何を包含し、どこまでを対象とするか。
- Object IdentityはObject Registry責務。
- identityの説明的Knowledgeは`overall`または`history`へ置く。

### 4.12 production / origin / provenance

**決定: `production`を追加し、`provenance`をKnowledge Facet名として使用しない。**

- `production`: Work等の制作過程・制作背景。
- origin: 成立由来が時間的なら`history`、因果なら`causes`、制作なら`production`。
- `provenance`はE-03 Source / Evidence Provenance用語として予約する。

### 4.13 characters / participants / members / users

**決定: 新しいcollection Facetを増やさない。**

- participants / members / users / included worksはRelationが正本。
- 既存`characters`はWork内のcharacter ensemble・characterizationという解釈的観点として維持。
- Relation一覧をそのままFacet本文へ複製しない。

---

## 5. Freeze候補Facet vocabulary

E-02Cで検証するvocabulary freeze候補は、**既存18 + 新規37 = 55 Facet**とする。

### 5.1 Existing 18 — keep

```text
overall
personality
values
motivation
behavior
relationships
role
themes
abilities
worldview
narrative
tone
characters
definition
properties
implications
related_concepts
examples
```

### 5.2 New shared vocabulary — 37

```text
background
appearance
purpose
history
structure
activities
culture
scope
chronology
setting
production
reception
changes
significance
geography
environment
function
usage
design
mechanism
causes
conditions
effects
requirements
constraints
variants
procedure
rules
society
distribution
interpretations
manifestations
measurement
safety
composition
symbols
vocabulary
```

### 5.3 新規Facetの意味契約

| Key | 意味 |
|---|---|
| `background` | Objectの成立背景・個体の前史・文脈 |
| `appearance` | 外観・視覚的特徴。寸法等のscalarはAttribute |
| `purpose` | 存在目的・目標・intended reason |
| `history` | 成立・変遷・重要な過去 |
| `structure` | 内部構造・構成原理・部分間配置 |
| `activities` | 継続・反復する主要活動の意味的説明 |
| `culture` | 文化的慣行・価値・表現・生活様式 |
| `scope` | 包含範囲・対象範囲・境界 |
| `chronology` | 内部出来事・phase等の時間順序 |
| `setting` | Work / Componentの舞台・環境設定の説明 |
| `production` | Creative Work等の制作背景・制作過程 |
| `reception` | 批評・評価・社会的受容のgroundedな説明 |
| `changes` | 版・適応・branch等の意味的差分・変化 |
| `significance` | 歴史的・物語的・機能的な重要性 |
| `geography` | 地理・空間構造・位置的特徴 |
| `environment` | 周辺環境・生息/成立環境・環境条件 |
| `function` | 対象が果たす機能・作用 |
| `usage` | 利用・適用・運用のされ方 |
| `design` | 設計意図・形態・設計上の特徴 |
| `mechanism` | 作動原理・因果機構 |
| `causes` | 発生・成立を生む因果要因 |
| `conditions` | 成立・発生・実行に必要/有利な条件 |
| `effects` | 因果的・実際的な結果・影響 |
| `requirements` | 実行・成立・役割遂行等に要求されるもの |
| `constraints` | 制約・限界・禁止条件 |
| `variants` | variant / subtype / variationの意味的差異 |
| `procedure` | 手順・stage・実行順序 |
| `rules` | 規範・規則・governing rule |
| `society` | 社会構造・制度・集団的構成 |
| `distribution` | 空間的・集団的な分布 |
| `interpretations` | 解釈・読み・意味付けの複数観点 |
| `manifestations` | 概念・性質等が具体的に現れる形 |
| `measurement` | 観測・評価・測定方法と尺度 |
| `safety` | 危険性・安全上の考慮・risk-related Knowledge |
| `composition` | 材料・物質等の組成・構成成分の意味的説明 |
| `symbols` | 記号体系のsymbol inventory / symbol behavior |
| `vocabulary` | Language等のlexical inventory / vocabulary system |

新規FacetはすべてRegistry上ではglobalなDefinitionとする。Class専用columnにはしない。

---

## 6. Vocabularyへ採用しない候補と配置先

| E-02A候補 | 決定 |
|---|---|
| `evolution`, `development` | 原則`history` |
| `biography`, `career` | `background` / `history` / `activities` / `role`へ分解 |
| `architecture`, `organization` | `structure` |
| `components` | Relationを正本、構造説明は`structure` |
| `characteristics`, `traits`, `features` | `properties`。人格traitは`personality` / Trait Object |
| `specifications` | scalarはAttribute、意味説明は`properties` / `design` / `function` |
| `limits` | `constraints` |
| `stages` | `procedure`。独立stageはRelation/Object検討 |
| `drivers`, `triggers` | `causes` / `conditions` / `motivation` |
| `outcomes` | `effects` |
| `dynamics`, `interactions` | `relationships` / `behavior` / `mechanism`へ意味で分解 |
| `timeline` | Timeline Objectまたは`chronology` |
| `identity` | Object Registry / `overall` / `history` |
| `origin` | `history` / `causes` / `production` |
| `provenance` | E-03 Source/Evidence Provenance用語として予約 |
| `members`, `participants`, `users`, `included_works` | Relation |
| `achievements` | `history` / `significance` |
| `goals` | Agent固有なら`motivation`、組織等なら`purpose`、独立概念ならObject/Relation |
| `conflicts` | Relation / Event。関係パターンは`relationships` |
| `technology_magic` | Worldの`properties` / `rules` / 関連System Object |
| `cosmology` | Worldの`structure` / `properties`。必要性がgoldで証明された場合のみ将来追加 |
| `morphology`, `physiology` | `properties` / `structure` |
| `reproduction` | `behavior` / `procedure` / Process Relation |
| `ecology` | `environment` / `behavior` / `relationships` / `distribution`へ分解 |
| `principles` | Ideology等では`values` / `rules` / `properties` |
| `practices` | `activities` / `usage` |
| `dimensions` | `properties` / `measurement` |
| `expression` | `manifestations` |
| `criteria` | `definition` / `conditions` |
| `transitions`, `divergence` | `changes` / `chronology` |
| `responsibilities`, `authority` | `role` / `activities` / `rules` / Relation |
| `training`, `mastery` | `procedure` / `requirements` / `properties` |
| `inputs`, `outputs` | Relation / Attribute。因果説明は`mechanism` / `effects` |
| `controls` | `rules` / `constraints` / Relation |
| `interfaces` | `structure` / Relation |
| `compatibility` | Relation + `constraints` / `properties` |
| `access`, `policy` | `usage` / `rules` / `constraints` |
| `exceptions` | `rules`内Statement |
| `progression` | `chronology` / `rules` |
| `processing` | `procedure` / Process Relation |
| `chemical_properties` | `properties` |
| `reactions` | `behavior` / Relation / Process |
| `occurrence` | `distribution` / `environment` |
| `observation` | `measurement` |
| `hazards` | `safety` / `effects` |
| `grammar`, `orthography_rules` | `structure` + `rules` |
| `phonology` | Languageの`structure` / `properties` |
| `variation` | `variants` |
| `encoding` | `rules` / Attribute / Relation |

この表は「語を捨てる」ことを意味しない。Facet IDとして独立させず、Statementの語彙としては自由に記述できる。

---

## 7. Profile inheritance方針

Facet Definitionを増やすだけではClass意味幅を制御できない。E-02Bでは、同じFacet集合を多数Classへ重複登録せず、Class hierarchy上の自然な共有点にprofileを置く方針を採用する。

### 7.1 family profileを置かないStructural Class

次は意味幅が広すぎるため、原則としてfamily profileを置かない。

- `ObjectClass`
- `Agent`
- `CreativeWork`

`FictionalEntity`もAdditional-onlyであり専用profileを持たない。

### 7.2 family / parent profileを置く候補

| Class | Inherited Facet候補 | 主なdescendant |
|---|---|---|
| `Group` | purpose, history, activities, relationships | Team, Faction |
| `Work` | 既存profile + setting, production, reception | Adaptation, WorkEdition |
| `WorkComponent` | narrative, themes, tone, characters, setting, significance | Episode, Chapter, Volume, Season, Arc |
| `Place` | geography, environment, history, culture, function, significance | World |
| `Artifact` | design, appearance, function, history, significance | Product |
| `Taxon` | properties, behavior, environment, distribution, history | Species, FictionalRace |
| `Concept` | 既存5 Facet | Theme, Ideology, Trait, Emotion, Motivation, StateConcept, RoleConcept, ArtifactTypeConcept |
| `Capability` | definition, mechanism, effects, requirements, constraints, variants | Ability, Skill |
| `Process` | mechanism, conditions, effects, procedure | Action, Activity |
| `TemporalEntity` | scope, chronology | Period, Timeline, Continuity |
| `Period` | scope, chronology, properties, changes | Era |
| `System` | purpose, structure, rules, behavior, constraints | Software, Service, RuleSystem |
| `Material` | properties, composition, behavior, usage, safety | Substance |
| `Phenomenon` | mechanism, causes, conditions, effects, measurement, examples | NaturalPhenomenon, SocialPhenomenon |
| `SymbolicSystem` | structure, rules, usage, history | Language, WritingSystem |

これらはE-02Cのgold caseで「ancestor profileが過剰適用されないか」を検証する。

---

## 8. Class-specific profile差分候補

以下はparent/family profileに加えてClassごとに追加する候補である。

| Class | Direct追加候補 |
|---|---|
| Character | background, appearance（既存8 Facetは維持） |
| Person | background, history, activities, relationships, role, abilities |
| Organization | purpose, history, structure, activities, culture, relationships |
| Faction | values, structure |
| Creature | background, appearance, properties, behavior, relationships, abilities |
| Adaptation | changes |
| WorkEdition | changes |
| Series | scope, chronology, themes, history, production, reception |
| Franchise | scope, history, themes, production, reception |
| Volume | scope, production |
| Season | scope, chronology |
| Arc | relationships |
| World | structure, society, rules |
| Event | chronology, causes, conditions, effects, significance |
| Product | properties, usage, variants, reception |
| FictionalRace | culture, society, abilities |
| Theme | manifestations, interpretations |
| Ideology | values, history, activities |
| Trait | manifestations, measurement |
| Emotion | conditions, manifestations, effects |
| Motivation | conditions, purpose, manifestations, effects |
| StateConcept | conditions, effects, changes |
| RoleConcept | requirements, activities, history |
| ArtifactTypeConcept | function, usage, variants, design |
| Ability | conditions |
| Skill | procedure |
| Action | purpose |
| Activity | purpose |
| Era | culture, society, significance |
| Timeline | rules, changes |
| Continuity | rules, changes |
| Software | properties, usage, history |
| Service | properties, usage, history |
| RuleSystem | mechanism |
| Substance | distribution |
| NaturalPhenomenon | distribution, safety |
| SocialPhenomenon | manifestations, history |
| Language | vocabulary, variants |
| WritingSystem | symbols, variants |

Team / Episode / Chapter / Species等は、E-02B時点ではparent/family profileだけで十分な候補とする。専用Facetを増やす必要がgold caseで示された場合のみ追加する。

---

## 9. Cross-class Facet similarity契約

同じFacet IDを共有する目的の一つはcross-class比較である。ただし、同じ英単語を持つだけで無条件に比較可能とはしない。

### 9.1 比較価値が高いshared Facet

次はcross-class similarityの意味が比較的安定する。

```text
values
themes
behavior
relationships
purpose
history
structure
culture
scope
chronology
significance
properties
function
usage
mechanism
causes
conditions
effects
requirements
constraints
rules
distribution
manifestations
```

例:

- OrganizationとTeamの`purpose`
- WorldとRuleSystemの`rules`
- EventとPhenomenonの`causes` / `effects`
- MaterialとProductの`properties`
- Concept subtype間の`manifestations`

### 9.2 比較scopeを狭くすべきFacet

次はFacet IDはglobalでも、意味比較はPrimary / ancestor Class filterを併用する方が安全である。

```text
personality
motivation
role
abilities
worldview
narrative
tone
characters
appearance
setting
production
reception
design
composition
symbols
vocabulary
```

### 9.3 silent semantic fallbackをしない

`purpose`がないObjectを`function`で代替比較したり、`history`がないObjectを`chronology`へfallbackしたりしない。

将来Query expansionで近縁Facetを横断する場合も、それはexplicitなretrieval strategyとして扱い、Facet Identity自体を同一視しない。

---

## 10. Initial Registry change plan

E-02Bの結論として、E-02C後に次の変更を物理Registryへ適用する案を確定する。

### 維持

- Migration 004でseed済みの18 Facet ID / keyはすべて維持。
- `overall`のみ`is_common=1`という現在の契約を維持。
- Character / Work / Conceptの既存profileを破壊しない。

### 追加候補

- 本書5.2の37 Facet Definitionを追加。
- 本書7〜8のClass profileを追加。
- 既存Work / Concept inheritanceを維持しつつ、より自然なparent/family profileを追加する。

### 削除・rename

- E-02B時点では既存Facetの削除・ID renameなし。
- E-02Aの候補語をそのまま別Facet IDとして追加しない。

### Migration方針

- 既存`004_semantic_facets.sql`は変更しない。
- E-02Cでgold caseを通過したvocabularyだけを**新しいadditive migration**で追加する。
- migration番号は実装時点の次の空き番号を利用し、E-02Bで予約しない。
- Class profile変更は過去Knowledge Versionの意味を現在classificationで再評価しないというE-02契約を維持する。

---

## 11. E-02Cで重点検証する論点

E-02Cでは少なくとも次をgold case化する。

1. `purpose / function / usage`を同じ情報へ誤配置しない。
2. `history / chronology / changes`を区別する。
3. `structure`へarchitecture等を統合しても意味損失がない。
4. `properties`が巨大catch-allにならず、Attribute / personality / design等へ適切に分離される。
5. `rules / constraints / conditions`を区別する。
6. `mechanism / procedure / behavior`を区別する。
7. `causes / effects / implications`を区別する。
8. Relation-derived Facetがedge一覧の複製にならない。
9. `overall`へ分類可能Knowledgeを逃がさない。
10. WorkComponent / Capability / TemporalEntity / SymbolicSystem等のancestor profileが過剰適用されない。
11. Concept subclassがConcept base profileだけで不足する場合にdirect追加Facetが正しく選ばれる。
12. `provenance`をArtifact history等のFacet名として使用せず、E-03 Provenanceと衝突しない。
13. cross-class similarityで同じFacet IDを比較する意味が成立する。
14. narrow Facetのcross-class比較ではClass scopeを併用できる。
15. profileに含まれないFacetを`overall`へsilent fallbackしない。

---

## 12. 完了条件への対応

- [x] E-02Aの全Class候補を横断比較した。
- [x] 近義語群ごとに統合 / 分離判断を記録した。
- [x] shared / inherited / class-specific profileの区別を設計した。
- [x] 初期18 Facetを全件reviewし、すべてkeepと判断した。
- [x] E-02C向けfreeze候補を既存18 + 新規37 = 55 Facetへ整理した。
- [x] Relation / Attributeへ出すべき候補をFacet vocabularyから除外した。
- [x] cross-class Facet similarityの比較境界を定義した。
- [x] Registry / Class profileの変更案を確定した。
- [x] Migration 004とruntime registryを先取り変更していない。

---

## 13. 結論

E-02Aで列挙されたClass固有候補をそのままFacetへ昇格させると、100語を超える局所vocabularyへ膨張し得る。E-02Bではこれを、**既存18 Facetを維持しつつ37の再利用可能なshared Facetを追加する55 Facetのfreeze候補**へ整理した。

重要な方針は、語数を最小にすること自体ではなく、次を同時に満たすことである。

- 同じ意味は同じFacet IDで再利用する。
- 意味が異なる近義語は無理に統合しない。
- Relation / AttributeをFacetへ重複正本化しない。
- Class hierarchy上の自然な共有点でprofile inheritanceを使う。
- `overall`をcatch-allとして利用しない。
- cross-class similarityでFacet IDの意味を安定させる。

この55 FacetはE-02Cの62 Class + 25 boundary gold caseで検証され、修正要求なしでFacet taxonomyとしてfreezeされた。物理Registryは`005_facet_taxonomy_freeze.sql`で55 Facet / 188 profile rowへ反映済みである。E-03 Source / Evidence / Provenance schemaも完了し、現在の次TaskはE-04 Versioning設計である。
