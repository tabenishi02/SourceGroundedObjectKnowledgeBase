# SGOKB 外部分類体系調査

更新日: 2026-10-10

- Task: `B-02A [P0] 外部分類体系を正式調査する`
- Status: Accepted
- Parent: `B-02 [P0] Object要件を定義する`
- Next: `B-02B [P0] SGOKB Object候補を網羅的に整理する`
- Related:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md`

## 1. 目的

本書は、SGOKBで扱うObject候補と分類境界を独自設計だけで決めることを避けるため、既存のWeb schema、Knowledge Graph、語彙分類、Resource Type体系を比較する。

調査対象は次の5体系を中心とする。

1. Schema.org
2. DBpedia Ontology
3. Wikidata
4. WordNet
5. Dublin Core / DCMI Type Vocabulary

目的は、いずれか1体系をSGOKBへそのまま移植することではない。各体系の設計目的の違いを理解した上で、次の後続Taskへ入力を与えることである。

- B-02B: Object候補の網羅化
- B-02C: Object Type / Class階層設計
- B-02D: Object / Facet / Relation / 対象外の境界確定
- B-03: Source / Evidence要件

---

## 2. 調査上の前提

SGOKBでは、少なくとも次を区別する。

```text
Object
  長期的にKnowledgeを蓄積・検索・比較したい意味的対象

Object Type / Class
  Objectを分類する語彙

Facet
  Object Knowledge内部の意味的観点

Relation
  Object間またはObjectと他要素の意味的関係

Source Type
  取得した資料・Resourceが何であるかを表す分類
```

同じ語が体系や文脈によって異なる役割を持つことがある。

例として `Event` は、現実・架空世界で発生する出来事そのものをObjectとして扱う場合もあれば、DCMIでは記述対象ResourceのTypeとして現れる。このため、名称だけで分類先を決めず、SGOKB内での役割を判断する。

---

# 3. Schema.org

## 3.1 体系の目的

Schema.orgは、Webページ内の構造化データで「何について記述しているか」を表現するための語彙である。

最上位は `Thing` であり、主要な直接下位Typeとして次がある。

- Action
- BioChemEntity
- CreativeWork
- Event
- Intangible
- MedicalEntity
- Organization
- Person
- Place
- Product
- Taxon

より具体的なTypeは上位Typeのpropertyを継承し、複数の上位Typeを持つ場合もある。

公式資料:

- https://schema.org/Thing
- https://schema.org/docs/gs.html
- https://schema.org/CreativeWork

## 3.2 SGOKBに有用な分類

SGOKBとの対応候補として特に有用なのは次である。

| Schema.org | SGOKBでの示唆 |
|---|---|
| Person | 実在PersonとCharacter候補を考える基準 |
| Organization | Organization / Group / Faction候補 |
| CreativeWork | Work系の上位分類候補 |
| CreativeWorkSeries / Series | Series / Franchiseの分類検討 |
| Episode / CreativeWorkSeason | Episode / Chapter等の粒度検討 |
| Place | Real / Fictional Place候補 |
| Event | Event Object候補 |
| Product | Item / Artifact / Product境界の参考 |
| Taxon | Species / Race等の分類検討材料 |
| Action | Action / Process / AbilityをObject化する場合の参考 |
| Intangible | 抽象対象を単純な物理Object体系へ押し込まないための参考 |

Schema.orgでは `Person` がfictional personも含むと定義され、`CreativeWork.character` の値もPersonである。したがって、Web Schema上はCharacterをPersonの一種として表現できる。

一方、SGOKBではCharacterと実在Personを同じClassへ統合すべきかは別問題であり、B-02C / B-02Dで判断する。

Seriesについては `CreativeWorkSeries` があり、TVSeries、MovieSeries、BookSeries、VideoGameSeries等の具体型を持つ。EpisodeもCreativeWorkとして独立Typeになっている。この構造は、Series / Episodeを単なるWork属性ではなく独立Object候補として検討する根拠になる。

## 3.3 そのまま採用しない理由

Schema.orgはWeb公開者が検索エンジン等へ意味を伝えるための語彙であり、個人Knowledge Baseの正規化されたontologyを目的としていない。

そのため、次をそのままSGOKBへ持ち込まない。

- E-commerce中心のOffer / Demand等をObject Typeへ大量導入しない。
- MedicalEntity等の専門領域体系をSGOKBの初期Typeへ無条件に導入しない。
- Schema.orgのproperty構成をSGOKB Facet / Relation Schemaとしてコピーしない。
- Schema.orgがPersonにfictional personを含めることだけを理由にCharacterとPersonを同一Classへ固定しない。

Schema.orgは主に「Web上で一般的に独立対象として扱われるカテゴリの漏れ防止」に利用する。

---

# 4. DBpedia Ontology

## 4.1 体系の目的

DBpedia OntologyはWikipedia Infoboxを基に構築されたcross-domain ontologyである。多分野の実Entityを比較的浅いclass hierarchyへ整理する。

公式説明では、Ontologyは数百のClassと多数のPropertyから構成され、代表的な大分類としてPerson、Place、Work、Species、Organisation等を持つ。

公式資料:

- https://www.dbpedia.org/resources/ontology/
- https://dbpedia.org/ontology/FictionalCharacter

## 4.2 SGOKBに有用な分類

SGOKBでは次の観点が特に有用である。

| DBpedia系概念 | SGOKBでの示唆 |
|---|---|
| Agent | Person / Character / Organization等をまとめる上位概念候補 |
| Person | 実在人物候補 |
| FictionalCharacter | CharacterをPersonと別Classとして扱う比較材料 |
| Organisation | Organization / Group / Faction候補 |
| Work | Creative Work系候補 |
| Place | Place / Setting候補 |
| Event | Event候補 |
| Species | Species / Race候補 |

DBpediaでは `FictionalCharacter` が `Agent` のsubclassとして定義されている。これはSchema.orgの「fictional personもPerson」という設計と異なる。

この差は、SGOKBに唯一の外部正解が存在しないことを示している。Character / Personの境界はSGOKBの利用目的から決めるべきである。

## 4.3 そのまま採用しない理由

DBpediaはWikipedia Infoboxと既存Mappingの影響を強く受ける。

したがって、次を避ける。

- DBpedia class hierarchyを完全コピーしない。
- Wikipediaに多い対象であることをSGOKB Object化の十分条件にしない。
- DBpediaのPropertyをRelation / Facetへ機械的に対応させない。

DBpediaは主に「cross-domain Knowledge Graphで実際に独立Class化されているカテゴリ」と「Schema.orgとは異なる分類解」を確認するために利用する。

---

# 5. Wikidata

## 5.1 体系の目的

Wikidataは、固定された少数Typeへ全Entityを押し込むのではなく、ItemとClassを関係で結ぶ方式を採用する。

中心概念は次である。

- `instance of (P31)`
- `subclass of (P279)`
- `subproperty of (P1647)`

WikidataではItemが複数Classのinstanceになれる。また、Entityが文脈によってinstanceとclassの両方になることも可能である。

公式資料:

- https://www.wikidata.org/wiki/Help:Data_model
- https://www.wikidata.org/wiki/Help:Basic_membership_properties/en

## 5.2 SGOKBへの重要な示唆

Wikidataから得る最大の示唆は、個別ObjectのIdentityと分類Classを強く結び付けすぎないことである。

概念的には次の分離が参考になる。

```text
Object Identity
  ↓ classified_as / instance_of
Class
  ↓ subclass_of
Broader Class
```

これにより、将来Class体系を修正してもObject IDを変更せずに済む。

また、multiple classificationを許容すると、単一enumでは表現しづらい対象を扱いやすい。

例:

```text
Object X
├─ class: Character
├─ class: ArtificialIntelligence
└─ class: OrganizationMember
```

ただし、この具体的方式を採用するかはB-02Cで決定する。

## 5.3 そのまま採用しない理由

Wikidataは非常に巨大で柔軟なKnowledge Graphであり、SGOKBの個人利用には過剰になり得る。

そのため、次をそのまま採用しない。

- Class自体をすべてObjectとして管理する設計を前提にしない。
- 無制限なmultiple classificationを許すことを確定しない。
- Wikidataのproperty体系をSGOKB Relation registryとしてコピーしない。
- `instance of` / `subclass of`の完全なRDF推論機構を初期要件としない。

Wikidataは主に「IdentityとClassificationの分離」「instanceとclassの区別」「複数分類可能性」の設計参考として利用する。

---

# 6. WordNet

## 6.1 体系の目的

WordNetは英単語をsynsetとして意味関係で整理するLexical Databaseである。Ontologyというより語彙意味分類として利用する。

WordNetのlexicographer filesには、nounについて次のような意味領域がある。

- act
- animal
- artifact
- attribute
- body
- cognition
- communication
- event
- feeling
- food
- group
- location
- motive
- object
- person
- phenomenon
- plant
- possession
- process
- quantity
- relation
- shape
- state
- substance
- time

公式資料:

- https://wordnet.princeton.edu/documentation/lexnames5wn

## 6.2 SGOKBへの重要な示唆

WordNetは特に `Concept` を1種類の曖昧な箱として扱わないための参考になる。

例えばConcept候補内部には、少なくとも次の異なる意味領域が存在する。

- attribute
- cognition
- feeling
- motive
- relation
- state
- process
- action
- time
- phenomenon

この分類は、B-02BでConcept候補を洗い出す際のチェックリストとして有用である。

また、Action / Process / State / Feeling / Motive等は、SGOKBでは文脈により次のいずれにもなり得る。

- 独立Object
- Object Class
- Facet value
- Relation
- 単なるKnowledge記述

この境界はB-02Dで明示的に判断する必要がある。

## 6.3 そのまま採用しない理由

WordNetの分類単位は語彙意味であり、SGOKBの永続Object Identityとは一致しない。

したがって、`noun.feeling`や`noun.state`等をそのまま上位Object Typeとして採用しない。

WordNetは主に「抽象Concept候補・状態・行為・感情等の見落とし防止」に利用する。

---

# 7. Dublin Core / DCMI Type Vocabulary

## 7.1 体系の目的

DCMI Type Vocabularyは、記述対象Resourceの一般的な性質を表すためのResource Type語彙である。

代表Typeには次がある。

- Collection
- Dataset
- Event
- Image
- InteractiveResource
- MovingImage
- PhysicalObject
- Service
- Software
- Sound
- StillImage
- Text

公式資料:

- https://www.dublincore.org/documents/dcmi-type-vocabulary/
- https://www.dublincore.org/specifications/dublin-core/dcmi-terms/

## 7.2 SGOKBへの重要な示唆

DCMIは主に **Object TypeではなくSource / Resource Type設計** の参考とする。

SGOKBでは例えば次のように分離する。

```text
Source
  source_type = Article / Text / Image / Video / Dataset / Interview / ...

Object
  object_class = Person / Character / Work / Place / Event / ...
```

例:

```text
Source: interview article
  ├─ Person Object A
  ├─ Character Object B
  └─ Work Object C
```

また、同じ語でも役割を分ける必要がある。

```text
Event Object
  「あるライブ公演」という出来事そのもの

Event Resource / Source
  あるEventをResourceとして記述・配信するメタデータ上の分類
```

## 7.3 そのまま採用しない理由

DCMI Type VocabularyはResource記述のための広い分類であり、CharacterやPerson、OrganizationのようなSGOKB Knowledge対象を網羅するものではない。

したがってDCMIをObject Type体系の親として採用せず、B-03のSource Type設計へ主に引き継ぐ。

---

# 8. 比較表

| 観点 | Schema.org | DBpedia | Wikidata | WordNet | DCMI |
|---|---|---|---|---|---|
| 主目的 | Web構造化データ | Cross-domain ontology | General Knowledge Graph | 語彙意味分類 | Resource metadata |
| 個別対象Identity | あり | あり | 強い | 主目的ではない | 主目的ではない |
| Class hierarchy | あり | あり | 柔軟 | 意味領域あり | 限定的 |
| Multiple classification | 一部複数継承 | Ontology上可能 | 明示的に可能 | SGOKB用途では非該当 | 主目的ではない |
| Person / Agent | 強い | 強い | 任意Class | person / group | 弱い |
| Creative Work | 強い | Work | 任意Class | communication等のみ | Text/Image等Resource側 |
| Place | 強い | 強い | 任意Class | location | 主対象外 |
| Event | 強い | 強い | 任意Class | event | Resource Typeにも存在 |
| Artifact / Product | Product | 各種Class | 任意Class | artifact | PhysicalObject |
| Species / Taxon | Taxon | Species | 任意Class | animal / plant | 主対象外 |
| Abstract Concept | Intangible等 | 限定的 | 柔軟 | 非常に有用 | 主対象外 |
| Source Type設計への有用性 | CreativeWork系 | 中 | 中 | 低 | 非常に高い |
| SGOKBでの主用途 | Object候補漏れ防止 | Cross-domain候補確認 | 分類モデル設計 | Concept候補整理 | Source Type分離 |

---

# 9. 複数体系に共通して現れるObject候補軸

外部分類体系を横断すると、SGOKBで少なくとも検討すべき候補軸は次のように整理できる。

## 9.1 Agent系

- Person
- Character / FictionalCharacter
- Organization
- Group
- Faction

Schema.org、DBpedia、Wikidata的なEntity/Classモデルのいずれでも重要な領域である。

`Agent`を上位Typeとして採用するかはB-02Cで判断する。

## 9.2 Creative Work系

- Work / CreativeWork
- Series / Franchise
- Episode
- Chapter
- Season
- Game / Movie / Book / Comic等のmedia subtype

Series / Episode等を独立Objectとするか、Work class hierarchy内でどう表すかをB-02B / B-02Cで検討する。

## 9.3 Place系

- Real Place
- Fictional Place / Setting

実在・架空を同じ上位Place配下へ置くかを検討する。

## 9.4 Event系

- Historical Event
- Fictional Event
- Performance / Competition / Ceremony等

Source TypeとしてのEventと区別する。

## 9.5 Artifact / Item / Product系

- Physical Artifact
- Fictional Item
- Product
- Equipment / Weapon等

商取引Productと物語上のArtifactを同一上位型へ置くかは未確定とする。

## 9.6 Biological / Taxonomic系

- Species
- Race
- Taxon
- Animal / Plant

現実分類とfictional speciesを同じ仕組みで扱えるかを検討する。

## 9.7 Concept / Abstract系

- Concept
- Theme
- Attribute
- Cognition
- Feeling
- Motive
- State
- Relation concept
- Phenomenon

すべてを独立Objectにするのではなく、Facet value等との境界をB-02Dで決める。

## 9.8 Action / Process系

- Action
- Process
- Ability
- Skill
- Activity

「火を操る能力」のように長期Identity・Relation・独自Evidenceを持つ対象はObject候補になり得るが、「走る」のような一般行為は通常Object化不要な可能性が高い。

## 9.9 Time / Period系

- Era
- Period
- Historical period
- Fictional era

独立Identityと複数Objectからの参照価値がある場合のみObject候補として検討する。

---

# 10. Source TypeとObject Typeの分離

B-02Aで最も明確になった境界の1つは、Source TypeとObject Typeを独立設計すべきことである。

## Object Typeが答える質問

> このKnowledgeは「何について」蓄積されるか。

例:

- Character
- Person
- Organization
- Work
- Place
- Event
- Concept

## Source Typeが答える質問

> このEvidenceは「どのような資料」から得られたか。

例:

- WebPage
- Article
- Interview
- Wiki page
- Official profile
- Dataset
- Image
- Video
- Audio
- Software / interactive resource

したがって、次のような構造を許容する。

```text
Source A: Official Character Profile
  └─ Character Object X

Source B: Interview Article
  ├─ Person Object P
  ├─ Character Object X
  └─ Work Object W

Source C: Wiki Article
  ├─ Work Object W
  ├─ Place Object L
  └─ Event Object E
```

この論理境界をB-03へ引き継ぐ。

---

# 11. B-02Cへ引き継ぐ分類モデル上の示唆

本調査だけではSGOKBのType/Classモデルを確定しないが、次の要件候補をB-02Cへ渡す。

1. **1階層固定enumだけで全Objectを表現しない。**
2. Object IdentityとClass membershipを分離できる構造を優先して比較する。
3. 上位Type + subtype/class方式を主要候補とする。
4. multiple classificationの必要性を正式に評価する。
5. `instance_of` / `subclass_of`相当概念を導入する価値を評価する。
6. 外部分類体系のURIやIDを将来mapping metadataとして保持できる余地を残すが、外部体系への依存をIdentity条件にしない。
7. Class体系変更によって既存`object_id`を変更してはならない。

---

# 12. B-02Bへ引き継ぐ候補一覧

B-02Bでは最低限、次を個別評価する。

```text
Agent / Actor-like
├─ Character
├─ Person
├─ Organization
├─ Group
└─ Faction

Creative Work
├─ Work
├─ Series
├─ Franchise
├─ Episode
├─ Chapter
└─ Season

Spatial
├─ Place
├─ Setting
├─ RealPlace
└─ FictionalPlace

Temporal occurrence
└─ Event

Artifact / Material
├─ Artifact
├─ Item
├─ Product
├─ Equipment
└─ Substance

Biological / Taxonomic
├─ Species
├─ Race
└─ Taxon

Abstract / Conceptual
├─ Concept
├─ Theme
├─ Attribute
├─ Cognition
├─ Feeling
├─ Motive
├─ State
├─ Phenomenon
└─ Relation Concept

Dynamic
├─ Action
├─ Process
├─ Ability
└─ Skill

Temporal entity
├─ Time
├─ Era
└─ Period
```

これは採用Type一覧ではなく、B-02Bで独立Object化の価値を評価するための調査母集団である。

---

# 13. 本調査で確定した方針

B-02Aとして次を確定する。

1. **単一の外部分類体系をSGOKBへそのまま採用しない。**
2. Schema.orgはWeb上の主要対象カテゴリとCreativeWork構造の漏れ防止に利用する。
3. DBpediaはcross-domain ClassとCharacter / Person等の代替分類モデル確認に利用する。
4. WikidataはObject IdentityとClassの分離、instance / subclass、multiple classificationの設計参考にする。
5. WordNetはConcept、Action、Process、State、Feeling、Motive等の意味領域の漏れ防止に利用する。
6. Dublin Core / DCMIは主としてSource / Resource Type設計に利用し、Object Type体系とは分離する。
7. 同じ語がObject / Class / Facet / Relation / Source Typeの複数候補になり得るため、名称一致だけで分類しない。
8. 外部体系のClass ID / URIを将来mappingとして保持する余地は有用だが、SGOKB Object Identityを外部IDへ依存させない。

---

# 14. B-02A完了判定

B-02Aの完了条件を確認する。

- [x] Schema.orgの主要上位TypeとSGOKB関連subtypeを抽出した。
- [x] DBpedia Ontologyの主要cross-domain classを整理した。
- [x] Wikidataのinstance / class / subclassモデルを整理した。
- [x] WordNet noun categoryをSGOKB観点で整理した。
- [x] Dublin Core / DCMI Resource Typeを調査し、Source TypeとObject Typeを分離した。
- [x] 共通カテゴリと体系ごとの役割を比較表にした。
- [x] SGOKBへそのまま移植すべきでない点を各体系について明記した。
- [x] B-02Bで再利用可能なObject候補母集団を作成した。

以上により、`B-02A [P0] 外部分類体系を正式調査する` は完了とする。

次のTaskは `B-02B [P0] SGOKB Object候補を網羅的に整理する` とする。
