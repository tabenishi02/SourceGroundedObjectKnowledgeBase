# SGOKB Object / Class / Facet / Relation Boundary Requirements

更新日: 2026-10-10

- Task: `B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する`
- Status: Accepted
- Parent: `B-02 [P0] Object要件を定義する`
- Inputs:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
- B-03 result: `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
- Next: `B-04 [P0] Object Result要件を定義する`

---

## 1. 目的

本書は、B-02Bで列挙した候補を、SGOKBで実際にどの責務へ配置するかを確定する。

B-02Cで採用した `Primary Class + Additional Classes + hierarchical Class Registry` を前提とし、次を区別する。

- 独立したKnowledge対象としての **Object**
- Objectの種類を表す **Class**
- 同一Object内部の意味的観点を表す **Facet**
- Object同士の意味的接続を表す **Relation**
- Object内部に保持する単純な **value / metadata**
- SGOKBのObject対象外またはSource側で扱うもの

本書で採用したObject Classは、専用機能の実装優先度にかかわらず、原則として通常のObjectデータ投入前に初期Class Registryへ登録する。

---

## 2. 境界判定の基本原則

### 2.1 Object

独立Objectとするのは、原則として次の複数を満たす意味対象である。

- 長期的に安定したIdentityを持つ。
- 複数SourceからKnowledgeを蓄積する価値がある。
- 他Objectから参照される。
- 単独で検索・比較したい。
- 独自のKnowledge Versionを持つ価値がある。
- Source / Evidenceを独立して関連付けたい。

単に「名前がある」「外部OntologyにTypeがある」だけではObject化しない。

### 2.2 Class

Classは「そのObjectが何の種類か」を表すClassification vocabularyである。

Class Registryは、ドメインに登場するすべての一般名詞を収録する辞書にはしない。

例えば次は異なる。

```text
櫻木真乃      = Object
Character     = Class
教師          = RoleConcept Objectまたはrole value
283プロ       = Organization Object
member_of     = Relation
personality   = Facet
明るい        = Facet valueまたはTrait ObjectへのRelation
```

### 2.3 Facet

Facetは同一ObjectについてKnowledgeを整理する観点であり、独立Identityではない。

例:

- Character: personality / values / motivation / behavior / relationships / abilities
- Work: themes / narrative / tone / worldview / production
- Place: geography / culture / history
- System: rules / components / constraints

Facet名それ自体を通常Objectとして作らない。

### 2.4 Relation

Relationは、独立したObject同士の意味的接続を表す。

例えば「CharacterがWorkへ登場する」はCharacterのClassではなく `appears_in` 相当Relationである。

分類上の `instance_of` / `subclass_of` は通常Semantic Relationとは別契約とする。

### 2.5 value / metadata

日時、順序、数値、短い状態値等、独立Identityを持たせる価値が低いものはvalue / metadataとする。

例:

- release_date
- start_date / end_date
- episode_number
- color value
- 一時的な感情状態

### 2.6 同じ語が複数役割を持つことを許容する

語そのものではなく、SGOKBで何を意味対象として管理するかで決める。

例:

- 「復讐」そのものを定義・比較する → `Motivation`または`Concept` Object
- Character Aが復讐を動機とする → motivation Facet + 必要ならMotivation ObjectへのRelation
- 「教師」という職業概念をKnowledge化する → `RoleConcept` Object
- Character Aが教師である → `has_role` Relationまたはrole value

---

## 3. Class Registryの役割区分

初期Class Registryでは、Classを次の3種類に区別する論理要件を置く。

| 区分 | 意味 |
|---|---|
| Structural | hierarchy整理専用。Objectへ直接Primary Classとして割り当てない |
| Primary-eligible | ObjectのPrimary Classとして割り当て可能 |
| Additional-only | 横断分類用。Primary Classには使わずAdditional Classとして利用 |

物理的にどのfieldで表現するかはE-01で決定する。

---

## 4. 正式Class hierarchy

以下をB-02D時点の正式な初期Class Registry seed集合とする。表記上の`[Primary]`は`Primary-eligible`を意味する。

```text
ObjectClass                                      [Structural]
├─ FictionalEntity                               [Additional-only]
├─ Agent                                         [Structural]
│  ├─ Character                                  [Primary]
│  ├─ Person                                     [Primary]
│  ├─ Organization                               [Primary]
│  ├─ Group                                      [Primary]
│  │  ├─ Team                                    [Primary]
│  │  └─ Faction                                 [Primary]
│  └─ Creature                                   [Primary]
├─ CreativeWork                                  [Structural]
│  ├─ Work                                       [Primary]
│  │  ├─ Adaptation                              [Primary]
│  │  └─ WorkEdition                             [Primary]
│  ├─ Series                                     [Primary]
│  ├─ Franchise                                  [Primary]
│  └─ WorkComponent                              [Structural]
│     ├─ Episode                                 [Primary]
│     ├─ Chapter                                 [Primary]
│     ├─ Volume                                  [Primary]
│     ├─ Season                                  [Primary]
│     └─ Arc                                     [Primary]
├─ Place                                         [Primary]
│  └─ World                                      [Primary]
├─ Event                                         [Primary]
├─ Artifact                                      [Primary]
│  └─ Product                                    [Primary]
├─ Taxon                                         [Primary]
│  ├─ Species                                    [Primary]
│  └─ FictionalRace                              [Primary]
├─ Concept                                       [Primary]
│  ├─ Theme                                      [Primary]
│  ├─ Ideology                                   [Primary]
│  ├─ Trait                                      [Primary]
│  ├─ Emotion                                    [Primary]
│  ├─ Motivation                                 [Primary]
│  ├─ StateConcept                               [Primary]
│  ├─ RoleConcept                                [Primary]
│  └─ ArtifactTypeConcept                        [Primary]
├─ Capability                                    [Structural]
│  ├─ Ability                                    [Primary]
│  └─ Skill                                      [Primary]
├─ Process                                       [Primary]
│  ├─ Action                                     [Primary]
│  └─ Activity                                   [Primary]
├─ TemporalEntity                                [Structural]
│  ├─ Period                                     [Primary]
│  │  └─ Era                                     [Primary]
│  ├─ Timeline                                   [Primary]
│  └─ Continuity                                 [Primary]
├─ System                                        [Primary]
│  ├─ Software                                   [Primary]
│  ├─ Service                                    [Primary]
│  └─ RuleSystem                                 [Primary]
├─ Material                                      [Primary]
│  └─ Substance                                  [Primary]
├─ Phenomenon                                    [Primary]
│  ├─ NaturalPhenomenon                          [Primary]
│  └─ SocialPhenomenon                           [Primary]
└─ SymbolicSystem                                [Structural]
   ├─ Language                                   [Primary]
   └─ WritingSystem                              [Primary]
```

上記は主要な親子関係を読みやすく示した表示であり、実際のhierarchyはDAGを許容する。横断的な追加`subclass_of` edgeとして最低限次も定義する。

```text
Character      subclass_of FictionalEntity
FictionalRace  subclass_of FictionalEntity
```

これによりCharacter / FictionalRaceの架空性は直接Additional membershipを重複保存しなくてもancestorとして導出できる。架空Organization / Place / Event / Artifact等は、必要に応じて`FictionalEntity`をAdditional Classとして直接付与する。

このhierarchyはClass IDの物理表現ではなく、B-02D時点の論理配置である。具体的`class_id`、seed format、migrationはE-01で定義する。

---

## 5. Agent / Actor境界

### Character vs Person

- `Character`: 架空の人格主体・作品上のキャラクター。
- `Person`: 実在または歴史上実在した人物。
- 同名・モデル関係があっても別意味対象なら別Objectとする。
- CharacterをPersonのsubclassにはしない。両者は`Agent`配下の兄弟Classとする。

### Organization / Group / Team / Faction

- `Organization`: 継続的組織Identity・制度・構造を持つ法人・機関・団体。
- `Group`: 複数Agentから成る名称付き集合で、Organizationほど制度化されていない集団も含む。
- `Team`: 共同活動・競技・制作等の目的を持つGroup。
- `Faction`: 政治・軍事・思想的陣営としてのGroup。

`Organization`と`Group`は`Agent`直下の兄弟Classとする。すべてのGroupをOrganizationとはみなさない。あるTeam / Factionが制度的Organizationでもある場合は、Primary=`Team`または`Faction`、Additional=`Organization`のようなmultiple classificationを許容する。

Group / Team / Factionは独立Objectになり得るが、単なる一時的な「3人組」のようにIdentityがない集合はObject化しない。

### Creature

固有名と独立Identityを持つ非人間個体は`Creature` Objectとする。

- 実在動物個体 → `Creature`
- 架空の個体で物語上Characterとして扱われる → Primary=`Character`、必要に応じAdditional=`Creature`
- 種そのもの → `Taxon` / `Species`

---

## 6. CreativeWork境界

### Work / Series / Franchise

- `Work`: 個別の創作・著作・表現物。
- `Series`: 複数Work / Componentを継続的まとまりとして束ねる系列。
- `Franchise`: media、Series、商品展開等を横断するIP・ブランド的まとまり。

`Series`と`Franchise`を`Work`の単なる属性にはしない。独立Knowledge、Source、Relation、Versionを持てる別Object Classとする。

### Episode / Chapter / Volume / Season / Arc

これらは`WorkComponent`配下のObject Classとする。

ただし、すべての章・話を必ずObject化する必要はない。次のいずれかを満たす場合にObject化する。

- 固有タイトルや公式Identityがある。
- 独自のSource / Evidenceを関連付けたい。
- Event / Character / Theme等のRelationを個別に持たせたい。
- 独立検索・比較したい。

単なる「第3章」という順序情報だけで独立Knowledgeが不要なら、Work内metadataとして保持できる。

### Adaptation / WorkEdition

内容差がKnowledgeとして重要な別版は別Objectとする。

- Adaptation → `Adaptation` + `adaptation_of` Relation
- Edition / remake / revised edition → `WorkEdition` + `edition_of` / `remake_of`等のRelation

SGOKBのKnowledge VersionとWorkEditionを混同しない。

---

## 7. Place / Setting境界

### Place

現実・架空を問わず、地理的または施設的な位置対象は`Place`とする。

架空であることは別Primary Classへ分離せず、必要に応じてAdditional=`FictionalEntity`を付与する。

### World

複数Place / Event / Workを包含し、独立した世界・宇宙・continuity空間としてKnowledgeを持つ対象は`World`とする。

### Setting

「作品の舞台」「現代日本」「学校を舞台とする」のようなSetting記述は原則Work Facetであり、`Setting` Classは作らない。

独立した意味対象が存在する場合は、その実体を`Place` / `World` Objectとして登録し、WorkからRelationで参照する。

---

## 8. Event境界

現実・架空を問わず、時間的に識別可能な出来事で独立Knowledgeを持つものを`Event`とする。

架空EventはAdditional=`FictionalEntity`で表現できる。

### Release / Publication / Production

通常の発売日、公開日、放送日等はWork metadataのscalar valueであり、独立Objectにしない。

一方、名称付きlaunch event、premiere、制作上の歴史的事件等、それ自体を検索・記述・Evidence関連付けしたい場合は通常の`Event` Objectにする。

B-02Dでは`ReleaseEvent`等の専用Classを初期Registryへ追加しない。

---

## 9. Artifact / Product境界

### Artifact

固有Identityを持つ人工物・道具・装置・架空アイテム等を`Artifact`とする。

### Product

市場・製品系統上の製品またはProduct Modelとして管理する対象は`Product`とする。

Softwareが製品でもある場合、Primary=`Software`、Additional=`Product`のようなmultiple classificationを許容する。

### Generic Item Type

「剣」「スマートフォン」「戦車」のような一般カテゴリそのものをClass Registryへ無制限に追加しない。

そのカテゴリ自体をKnowledge化する場合は`ArtifactTypeConcept` Objectとし、個別Artifactとの関係はSemantic Relationで表現する。

---

## 10. Biological / Taxonomic境界

### Taxon / Species / FictionalRace

種・分類群・架空種族等は、Class RegistryのドメインClassそのものではなく、**Taxonomic Knowledge Object**として扱う。

- 一般分類群 → `Taxon`
- 生物種 → `Species`
- 作品世界のrace / species-like group → `FictionalRace`（架空性を含むClass）

Taxon Object同士の上下関係は通常Semantic Relationとして保持し、Class Registryの`subclass_of`と混同しない。

実在人間のrace / ethnicityを生物学的Taxonとして扱わない。社会的・歴史的カテゴリとして独立Knowledge化する必要がある場合は、Concept系Objectとして別途境界を判断する。

### 個体

個体はTaxon Objectではなく`Creature` / `Person` / `Character`等とし、TaxonとのmembershipをRelationで表現する。

---

## 11. Concept / Abstract境界

Concept配下には、独立定義・比較・Evidenceを持つ抽象対象だけをObject化する。

### Theme / Ideology

- Theme / Motif → `Theme`
- Ideology / Doctrine / Philosophy → `Ideology`

WorkやCharacter内の短い記述だけならFacet valueでもよいが、作品横断で参照する場合はObject化しRelationで結ぶ。

### Trait

「勇敢」「内向的」等を独立定義・比較する場合は`Trait` Objectにできる。

ただしCharacterの性格記述をすべてTrait Objectへ分解することは要求しない。通常の性格説明はpersonality Facetのvalueとして保持できる。

### Emotion

感情概念そのものをKnowledge化する場合は`Emotion` Objectとする。

「現在怒っている」のような一時状態はFacet valueであり、通常は新Objectを作らない。

### Motivation

動機概念そのものを作品横断で扱う場合は`Motivation` Objectとする。

Character固有の動機説明はmotivation Facetで保持し、必要ならMotivation ObjectへRelationを張る。

### StateConcept

定義・原因・結果等を独立Knowledgeとして持つ状態概念は`StateConcept`とする。

Objectの現在状態、lifecycle status、短期状態値とは分離する。

### RoleConcept

職業・役割・称号を独立概念としてKnowledge化する場合は`RoleConcept`とする。

Agentへ「教師」「王」等をClassとして直接追加し続けない。Agentとの対応は`has_role`等のRelationまたは簡易valueで表現する。

### ArtifactTypeConcept

一般的な道具・装備カテゴリをKnowledge化する場合に使用する。個別ArtifactのPrimary Classにはしない。

---

## 12. Ability / Skill / Process境界

### Ability / Skill

名称・ルール・制約・使用者・Sourceを独立して持つ能力・技能はObject化する。

- 固有能力、特殊能力 → `Ability`
- 習得可能な技法・技能 → `Skill`

Characterが能力を持つことは`has_ability` / `has_skill` Relationで表現する。

abilities Facetは能力の要約・未Object化情報を保持できるため、Ability ObjectとFacetは排他的ではない。

### Action / Activity / Process

- 行為の種類として独立Knowledgeを持つ → `Action`
- 継続的活動の種類 → `Activity`
- 入力・段階・出力・条件を持つ過程 → `Process`

特定日時に起きた一回の出来事は`Event`であり、Process / Action Objectとは区別する。

Relation predicateとしての「uses」「creates」等をAction Object化しない。

---

## 13. Temporal境界

### Period / Era

名称付きの期間で独立Knowledgeを持つものはObject化する。

- 一般named period → `Period`
- 歴史的・作品世界上の時代 → `Era`

### Date / Time Interval

単なる日時・開始終了時刻・数値期間はscalar valueであり、Object化しない。

### Timeline / Continuity

複数Work / Event / Character Identityを区別する時間系列・世界線のまとまりは`Timeline`または`Continuity` Objectとする。

単なる表示用年表はObjectではなく派生表示にできる。

---

## 14. System / Software / Service境界

### System

独自ルール・構成要素・制約を持つ体系で、他Objectから参照される対象を`System`とする。

### Software

独立名称・機能・Version・Sourceを持つSoftwareは`Software` Objectとする。

Creative Workとしても扱う価値がある場合はAdditional=`Work`、製品として扱う場合はAdditional=`Product`を許容する。

### Service

継続提供されるWeb / 配信 / 公共等のサービスは`Service`とする。

### RuleSystem

魔法体系、ゲームルール、戦闘システム等、複数Objectの挙動を規定する体系は`RuleSystem`とする。

単一の設定説明しかなく独立Identityがない場合はWork Facetに留める。

---

## 15. Material / Substance / Consumable境界

- 材料・物質として独立Knowledgeを持つ → `Material`
- 化学的・物性的な物質Identityを強く持つ → `Substance`
- 特定商品としての飲食物・薬品 → `Product`
- 一般カテゴリとしての「食品」「薬」等 → 原則ConceptまたはMaterialとして意味に応じて扱う

`Food` / `Drug`専用ClassはB-02D初期Registryでは採用しない。

---

## 16. Phenomenon境界

繰り返し生じる現象類型そのものをKnowledge化する場合は`Phenomenon`系Objectとする。

- 自然現象類型 → `NaturalPhenomenon`
- 社会現象類型 → `SocialPhenomenon`

一方、特定日時・場所で発生した個別の地震・台風・流行イベント等は`Event` Objectとする。

したがって「地震という現象」と「202X年の特定地震」は別Objectになり得る。

---

## 17. Language / Term / Writing System境界

### Language / WritingSystem

自然言語・人工言語・架空言語は`Language`、文字体系は`WritingSystem`とする。

### Term

単なる用語文字列は原則Objectにせず、Conceptのname / alias / lexical metadataとして扱う。

用語そのものの語史・用法・表記を独立Knowledgeとして扱う必要が生じた場合は、まず`Concept` Objectとして保持できる。専用Term Classの必要性は実利用が確認されてから追加検討する。

---

## 18. Fictional / Realの扱い

Real / FictionalをPrimary Classの巨大な二重体系にはしない。

架空性が分類上重要な場合はAdditional-only `FictionalEntity`を利用する。

例:

```text
架空組織:
  primary_class = Organization
  additional_classes = [FictionalEntity]

架空都市:
  primary_class = Place
  additional_classes = [FictionalEntity]

架空戦争:
  primary_class = Event
  additional_classes = [FictionalEntity]
```

`Character`と`FictionalRace`はClass hierarchy上で`FictionalEntity`もancestorとなるため、直接Additional membershipを重複保存しない。その他の架空Objectは必要に応じてAdditional=`FictionalEntity`を付与する。

---

## 19. Source TypeとObject Classの境界

Source recordは「Evidenceをどの資料から取得したか」を表し、Objectは「何についてKnowledgeを管理するか」を表す。

同じ実体が両方の役割を持つことを許容するが、recordと責務は分離する。

| 実体 | Source role | Object role |
|---|---|---|
| Article | Evidence提供記事 | 記事そのものを研究・比較する場合はWork |
| Book | 参考資料 | 書籍自体をKnowledge対象にする場合はWork |
| Dataset | Evidence取得元 | Dataset自体をKnowledge対象にする場合はWorkまたは将来の専用Class |
| Image | 画像Evidence | ArtworkとしてKnowledge対象ならWork |
| Video | Interview / 解説Evidence | 映像作品としてKnowledge対象ならWork |
| Software | 収集Tool | Software自体をKnowledge対象ならSoftware |
| Event | Resource記述上のEvent | 出来事そのものを管理するならEvent |

Sourceのresource type / media type / document genre / publisher kind / subject relationship / capture境界はB-03で確定済みであり、`SOURCE_EVIDENCE_REQUIREMENTS.md`を正本とする。

---

## 20. Object / Facet / Relation / valueの代表境界

| 情報 | 配置 |
|---|---|
| Characterそのもの | Character Object |
| Characterの性格説明 | personality Facet |
| 「勇敢」という概念 | Trait Object（独立管理する場合） |
| Characterが勇敢である | personality Facet value または Trait ObjectへのRelation |
| Characterの固有能力 | Ability Object + Relation |
| Characterの能力概要 | abilities Facet |
| Workそのもの | Work Object |
| Series全体 | Series Object |
| Workのテーマ説明 | themes Facet |
| 「自己犠牲」という横断テーマ | Theme / Concept Object |
| Workが自己犠牲をテーマに持つ | Relation |
| 発売日 | scalar metadata |
| 発売記念イベント | Event Object（独立Identityがある場合） |
| Characterの職業 | role value または RoleConcept ObjectへのRelation |
| 「教師」という職業概念 | RoleConcept Object |
| Speciesとしての「猫」 | Species / Taxon Object |
| 固有猫個体 | Creature Object |
| 2026-10-10 | scalar date value |
| 江戸時代 | Era Object |

---

## 21. 初期Class Registry seed集合

第4節のClass hierarchyに記載したClassを、B-02D時点の初期Registry seed集合とする。

原則:

1. `Structural` Classもhierarchy解決のためRegistryへseedする。
2. `Primary` ClassはPrimary / Additional membershipへ利用可能にする。
3. `Additional-only` ClassはPrimary assignmentを拒否する。
4. 通常Objectデータ投入前にseed完了をValidationできるようにする。
5. seed漏れを理由に別の広いClassへObjectを自動分類しない。

物理seed file形式・class IDはE-01で決定する。

---

## 22. Class固有機能の実装優先度

Class Registryへの登録とは別に、専用Facet / UI / validation / search最適化の実装順を次のように扱う。

### Core support

- Character
- Work
- Concept

### High support

- Person
- Organization
- Series
- Place
- Event

### Later specialized support

- その他のB-02D採用Class

LaterであってもClass Registryには初期seedする。専用機能がないClassは共通Object contractで利用できなければならない。

---

## 23. fallback / review / stagingルール

### 許可するfallback

既存の上位Classが対象を意味的に正しく表し、そのまま永続保持しても誤分類にならない場合のみ許可する。

例:

- 未知のWork subtype → `Work`
- 未知のConcept subtype → `Concept`
- 未知のSystem subtype → `System`

この場合は「後で必ず再分類するための仮置き」ではなく、上位Class自体が正しいClassificationであることが条件である。

### 禁止するfallback

意味カテゴリが異なるClassへの丸め込みを禁止する。

例:

- Abilityが未登録だから`Concept`へ入れる
- Seriesが未登録だから`Work`へ入れる
- Organizationが未登録だから`Character`へ入れる
- Eraが未登録だからdate stringだけにする

### review / staging

適切なClassが存在せず、既存上位Classでも意味を正しく保持できない場合は、Object本登録を止め、Class追加reviewまたはstagingへ送る。

staging状態・workflow・UIはE-01 / E-05で具体化する。

---

## 24. Character / Work / Conceptの再マッピング

旧B-02の3分類は次のように再解釈する。

```text
Character
  subclass_of Agent

Work
  subclass_of CreativeWork

Concept
  ObjectClass直下の抽象Knowledge Class
```

これらは特権的なIdentity種別ではなく、Class Registry上のPrimary-eligible Classである。

既存の`object_type=Character|Work|Concept`前提は、論理要件上 `primary_class` へ移行する。

---

## 25. B-03へ引き継ぐSource coverage

B-03では少なくとも次のClass familyを根拠としてSource / Evidence要件を設計する。

- Agent: official profile / biography / interview / organization page
- CreativeWork: official work page / series portal / episode guide / store listing / credits
- Place / World: official lore / map / geographic or facility source
- Event: official record / timeline / news / event page
- Artifact / Product: official specification / manual / product page / lore
- Taxon / Creature: taxonomy DB / encyclopedia / official creature guide
- Concept / Capability / Process: dictionary / academic / criticism / rulebook / guide
- Temporal: chronology / historical reference / official timeline
- System / Software / Service: documentation / repository / release notes / official service page
- Material / Phenomenon: scientific / technical / government / reference source
- Language / WritingSystem: dictionary / grammar / linguistic / official setting source

B-03ではこのcoverageを入力としてSource分類をClass hierarchyから独立させ、resource type / media type / document genre / publisher kind / subject relationship / provider / page purpose等へ分離した。詳細は`SOURCE_EVIDENCE_REQUIREMENTS.md`を参照する。

---

## 26. Phase Cへ引き継ぐUPDS境界

SGOKBは外部世界のObject / Conceptを保持する。

次はSGOKBへ保存しない。

- 「ユーザーはこのCharacterを好む」
- 「ユーザーは自己犠牲Themeを好む傾向がある」
- 「この選択群からユーザーの価値観を推測できる」

これらはUPDSのPersonal Inferenceである。

一方、Theme / Trait / Motivation / Ideology等の**概念そのもの**はSGOKB Objectとして保持でき、UPDSはそのObject IDを参照できる。

---

## 27. B-02D完了条件への対応

- B-02Bの主要候補をObject Class / Facet / Relation / value / Source側へ配置した。
- 同一語が文脈によって複数役割を持つ場合の判定規則を定義した。
- Character / Work / Conceptを新Classification modelへ再マッピングした。
- 正式Class hierarchyと初期Class Registry seed集合を確定した。
- Registry包含とClass固有機能の実装優先度を分離した。
- generic fallbackの許可 / 禁止条件を確定した。
- Source Type境界をB-03へ、Personal Inference境界をPhase Cへ引き継げる状態にした。

---

## 28. 結論

SGOKBでは、**「何について長期Knowledgeを持つか」をObject、「そのObjectが何の種類か」をClass、「同一Objectのどの観点か」をFacet、「独立Object同士がどう結び付くか」をRelation、「独立Identityを要しない単純情報」をvalueとして分離する。**

B-02DによりObject分類精緻化B-02A〜B-02Dは完了する。

B-03 Source / Evidence要件は完了済みである。次のタスクは `B-04 [P0] Object Result要件を定義する` とする。

**Status: Complete (2026-10-10)**
