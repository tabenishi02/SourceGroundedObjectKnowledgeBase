# Source Grounded Object Knowledge Base — Facet Taxonomy Survey

更新日: 2026-10-12

- Task: `E-02A [P0] 全ClassのFacet taxonomy surveyを実施する`
- Status: Complete
- Inputs:
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
  - `docs/design/OBJECT_SCHEMA.md`
  - `docs/design/SEMANTIC_FACET_SCHEMA.md`
  - `src/sgokb/migrations/003_object_schema.sql`
- Next: `E-02B [P0] Facet vocabularyを横断統合する`

## 1. 目的

E-02 coreでは、全62 Classを初期Class Registryへseedする一方、専用Facet profileはCharacter / Work / Conceptを中心に初期実装した。本書は、残りのClassを`overall`だけへ恒久的に集約して意味幅が膨張することを防ぐため、**初期Registryの全62 Classを同じ観点で横断surveyする。**

各Classについて次を確認する。

- Classの意味境界と、含めるもの / 含めないもの。
- そのClassで長期保存するKnowledgeの主な観点。
- 専用Facet候補、または専用profile不要という判断。
- Facetへ入れず、Object / typed attribute / Relation / Statementへ置くべき情報。
- representative example / counterexample。

本TaskはFacet Registry seedやClass profileを変更しない。候補語彙の重複・近義語統合、shared / class-specific / inherited profileの確定はE-02Bで行う。

---

## 2. Surveyの判定規則

### 2.1 Facetが担当するもの

Facetは、同一Objectについて複数Evidenceから統合・説明する価値がある**意味的観点**を担当する。

例:

- Characterの`personality`
- Organizationの`structure`
- Eventの`causes`
- Processの`mechanism`

### 2.2 Relationへ出すもの

独立Objectとの接続は、Facet本文だけに埋め込まずRelationを正本接続として持てるようにする。

代表例:

- membership / creator / ownership / location / part-of
- Work ↔ Series
- Character ↔ Ability
- Species ↔ Taxon
- Language ↔ WritingSystem

FacetにはRelation群を解釈した要約を置くことはできるが、接続自体の代替にはしない。

### 2.3 typed attributeへ出すもの

短い決定的値・数値・日時・identifier等はtyped attribute候補とする。

代表例:

- birth / release / start / end date
- episode / volume number
- coordinate
- product identifier
- numeric specification

### 2.4 Objectへ分離するもの

stable Identity、独自Source / Evidence、検索・比較価値を持つ対象はFacet内の文字列へ潰さずObject化候補とする。

### 2.5 Structural / Additional-only Class

Structural ClassはPrimary Classとして直接Objectへ割り当てないため、**直接Object用profileは不要**である。ただし、descendantへ継承するfamily-level Facetを置く価値がある場合はE-02Bで検討対象にできる。

`FictionalEntity`はAdditional-onlyの横断分類であり、fictionalityそのものを理由に専用Facetを必須化しない。架空世界・continuity・登場作品等はRelation / temporal context /通常Facetで表現する。

### 2.6 Profile state表記

| 表記 | 意味 |
|---|---|
| `existing` | E-02ですでに直接profileが存在する |
| `inherit-current` | 現行Class hierarchyとE-02 profile inheritanceで専用Facetが解決される |
| `candidate` | 新しい専用profileまたは追加FacetをE-02Bで検討する |
| `family-candidate` | Structural Class上の継承profile候補としてE-02Bで検討する |
| `none` | 専用profileを設ける理由が現時点ではない |

すべてのassignable Classは、上記に関係なくcommon `overall`を利用できる。

---

## 3. 横断的な初期所見

1. **Classの数とFacetの数は1対1ではない。** 62 Classすべてへ独自Facet集合を作る必要はなく、shared / inherited profileを使う方が意味整合性を保ちやすい。
2. **Structural Classは有力な継承点になり得る。** 特に`WorkComponent`, `Capability`, `SymbolicSystem`はdescendant間の共通観点が比較的明確である。一方、`ObjectClass`は広すぎるため専用Facetを置かない。
3. **Relation-heavyな情報をFacetへ重複正本化しない。** `members`, `works`, `locations`, `owners`, `users`, `components`, `included_works`等はRelationが主要表現となる。
4. **scalar値をFacetへ埋め込みすぎない。** 日付、順序、座標、型番、数値仕様等はtyped attributeが適する。
5. **Concept branchは現行profileの再利用性が高い。** `definition / properties / implications / related_concepts / examples`を基礎に、subclass-specificな観点だけを追加候補とする。
6. **Work branchではWorkとWorkComponentを分ける必要がある。** Episode / Chapter / Arc等には`narrative / themes / characters`等の共有候補があるが、Series / Franchiseは`scope / evolution / continuity`寄りで意味が異なる。
7. **Agent branchは一律profileにしにくい。** Character / Person / Organization / Groupでは有効な観点が異なるため、`Agent`へ多数のFacetを置くよりdescendant profileを中心にする方が安全である。
8. **E-02Bで重点的に統合すべき近義候補が確認された。** `purpose / function / use / usage / application`, `history / evolution`, `structure / architecture / organization`, `properties / characteristics / traits`, `rules / constraints`, `causes / conditions / mechanism`, `effects / outcomes / implications`等である。

---

## 4. Registry / cross-cutting Class

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:object_class` ObjectClass | structural / `none` | 全Class hierarchyのroot。Objectの意味Classとして直接使わない | 専用Facetなし | すべてClassification Registry責務 | 代表: Class tree root / 反例: 不明ObjectをPrimary=`ObjectClass`へ逃がす |
| `class:fictional_entity` FictionalEntity | additional-only / `none` | 架空性を横断付与する補助Class。固有のObject kindではない | 専用Facetなし。fictional contextを必要に応じ通常Facetで説明 | Work / World / Continuityとの接続はRelation。Character / FictionalRaceはancestorから導出 | 代表: 架空OrganizationのAdditional Class / 反例: Characterへ冗長に直接追加、または架空性だけでPrimaryにする |

---

## 5. Agent family

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:agent` Agent | structural / `family-candidate` | 行為主体family。直接Primary assignmentしない | family候補: `background`, `relationships`, `activities`。ただしdescendant差が大きく最小化推奨 | identity/classificationはRegistry、所属等はRelation | 代表: Character / Person等の共通ancestor / 反例: 名前付き人物をPrimary=`Agent` |
| `class:character` Character | primary / `existing` | 物語上の人格主体である架空個体 | 現行: `personality`, `values`, `motivation`, `behavior`, `relationships`, `role`, `themes`, `abilities`。追加候補: `background`, `appearance` | appears_in / member_of / has_ability等はRelation。生年月日等はAttribute | 代表: 架空主人公 / 反例: 実在俳優=`Person` |
| `class:person` Person | primary / `candidate` | 実在・歴史上実在した人物 | `biography`, `career`, `expertise`, `activities`, `relationships` | birth/death等はAttribute。works_for / created / performed等はRelation | 代表: 作者・研究者 / 反例: 作品上のキャラクター |
| `class:organization` Organization | primary / `candidate` | 制度・継続Identity・構造を持つ組織 | `purpose`, `history`, `structure`, `activities`, `culture` | members / owns / produces / located_atはRelation。法人番号等はAttribute | 代表: 出版社・学校・架空機関 / 反例: 非制度的な一時的集団=`Group`または非Object |
| `class:group` Group | primary / `candidate` | 名称・Identityを持つAgent集合。制度化は必須でない | `purpose`, `history`, `dynamics`, `activities`, `identity`候補 | membership / part_ofはRelation | 代表: バンド・名称付きユニット / 反例: 偶然居合わせた3人 |
| `class:team` Team | primary / `candidate` | 共同目的・競技・制作等へ協働するGroup | `purpose`, `coordination`, `history`, `achievements`, `dynamics` | member / competes_with / part_ofはRelation。成績数値はAttribute候補 | 代表: スポーツチーム・制作チーム / 反例: 法人全体=`Organization` |
| `class:faction` Faction | primary / `candidate` | 政治・軍事・思想的な陣営・派閥 | `ideology`, `goals`, `structure`, `history`, `activities`, `conflicts` | members / allied_with / opposes / controls PlaceはRelation | 代表: 作品内政治派閥 / 反例: 単なる作業Team |
| `class:creature` Creature | primary / `candidate` | 固有Identityを持つ非人間個体。人格主体ならCharacterとのmultiple classification可 | `biography`, `traits`, `behavior`, `relationships`, `abilities`候補 | species / owner / habitat / appears_inはRelation | 代表: 固有名の実在動物 / 反例: 猫という種=`Species`。物語人格主体ならPrimary=`Character`も検討 |

---

## 6. CreativeWork family

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:creative_work` CreativeWork | structural / `family-candidate` | 創作物family。直接Primary assignmentしない | family候補: `themes`, `production`, `reception`は再利用可能性あり。ただし全descendantへ一律継承は要検証 | creator / publisher / part-ofはRelation | 代表: Work / Series等のancestor / 反例: 小説をPrimary=`CreativeWork` |
| `class:work` Work | primary / `existing` | 個別の創作・著作・表現物 | 現行: `themes`, `worldview`, `narrative`, `tone`, `characters`, `relationships`。追加候補: `production`, `reception`, `setting` | creator / publisher / series / adaptationsはRelation。release_date等はAttribute | 代表: 個別小説・映画・ゲーム / 反例: 複数作品を束ねるSeries |
| `class:adaptation` Adaptation | primary / `inherit-current` | 別Workを別media/表現へ翻案した独立Work | Work profile + `adaptation_changes`, `adaptation_approach`候補 | `adaptation_of`はRelation。medium等はAttribute候補 | 代表: 小説原作の映画版 / 反例: 同媒体の改訂版=`WorkEdition` |
| `class:work_edition` WorkEdition | primary / `inherit-current` | edition / remake / revised版として独立Identityを持つWork | Work profile + `edition_changes`, `editorial_context`候補 | `edition_of` / `remake_of`はRelation。版番号・発売日はAttribute | 代表: 改訂版・remake / 反例: SGOKB Knowledge Version |
| `class:series` Series | primary / `candidate` | 複数Work / Componentを継続的まとまりとして束ねる | `scope`, `chronology`, `themes`, `continuity`, `evolution`, `identity` | installments / has_partはRelation | 代表: 小説シリーズ・TVシリーズ / 反例: 単一Work、またはより広いFranchise |
| `class:franchise` Franchise | primary / `candidate` | 複数media・Series・商品展開を跨ぐIP/ブランド的まとまり | `scope`, `history`, `evolution`, `media_mix`, `identity`, `continuity`候補 | owned_by / includes_series / includes_workはRelation | 代表: 複数media展開IP / 反例: 1本のSeriesのみ |
| `class:work_component` WorkComponent | structural / `family-candidate` | Workを構成する独立可能なcomponent family | 継承候補: `narrative`, `themes`, `characters`, `setting`, `significance` | parent Work / order / has_partはRelationまたはAttribute | 代表: Episode等のancestor / 反例: 実ComponentをPrimary=`WorkComponent` |
| `class:episode` Episode | primary / `candidate` | 独立Identityを持つ話・episode | `narrative`, `themes`, `characters`, `tone`, `setting`, `significance` | part_of / features / contains_eventはRelation。episode_numberはAttribute | 代表: 固有タイトル付き第1話 / 反例: Identity不要の単なる番号行 |
| `class:chapter` Chapter | primary / `candidate` | 独立Knowledge対象にする章 | `narrative`, `themes`, `characters`, `setting`, `significance` | part_of / contains_eventはRelation。chapter_numberはAttribute | 代表: 固有タイトル付き章 / 反例: 目次上の順序値だけ |
| `class:volume` Volume | primary / `candidate` | Series/Work内で独立Identityを持つ巻・volume | `scope`, `narrative`, `themes`, `characters`, `production`候補 | chapters / part_ofはRelation。volume_number / release_dateはAttribute | 代表: 漫画第5巻 / 反例: 単巻で完結する独立書籍を機械的にVolume扱い |
| `class:season` Season | primary / `candidate` | 複数episode等を束ねる公式season単位 | `scope`, `narrative`, `themes`, `characters`, `tone`, `evolution` | episodes / part_ofはRelation。season_numberはAttribute | 代表: TV Season 2 / 反例: 歴史上の季節・Period |
| `class:arc` Arc | primary / `candidate` | 名称・意味的まとまりを持つnarrative arc | `narrative`, `themes`, `characters`, `relationships`, `conflicts`, `significance`候補 | component membership / eventsはRelation | 代表: 公式/安定名称を持つ物語編 / 反例: 恣意的に選んだ数話集合 |

---

## 7. Place / Event / Artifact family

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:place` Place | primary / `candidate` | 現実・架空の地理的/施設的位置対象 | `geography`, `environment`, `history`, `culture`, `function`, `notable_features` | located_in / contains / event_atはRelation。座標等はAttribute | 代表: 都市・学校・施設 / 反例: 「学校を舞台とする」というWork setting記述 |
| `class:world` World | primary / `candidate` | 複数Place/Event/Workを包含する世界・宇宙・world-space | `cosmology`, `geography`, `history`, `society`, `culture`, `rules`, `technology_magic`候補 | contains_place / setting_of / continuity関係はRelation | 代表: 架空世界全体 / 反例: 単一都市=`Place` |
| `class:event` Event | primary / `candidate` | 時間的に識別可能な一回/一連の出来事 | `chronology`, `causes`, `participants`, `outcomes`, `significance`, `context` | participant / occurred_at / part_ofはRelation。start/endはTemporal Scope/Attribute | 代表: 戦争・大会・物語上事件 / 反例: 地震という現象類型=`Phenomenon` |
| `class:artifact` Artifact | primary / `candidate` | 固有Identityを持つ人工物・道具・装置 | `design`, `appearance`, `function`, `history`, `capabilities`, `significance` | owner / creator / used_by / made_ofはRelation。寸法等はAttribute | 代表: 固有武器・歴史的遺物 / 反例: 「剣」という一般型=`ArtifactTypeConcept` |
| `class:product` Product | primary / `candidate` | 市場上の製品またはproduct model | `specifications`, `design`, `use`, `variants`, `history`, `reception` | manufacturer / compatible_with / successor_ofはRelation。型番・数値specはAttribute | 代表: RTX 4090製品model / 反例: その1枚の特定個体を研究する場合はArtifact寄り |

---

## 8. Taxon / Concept / Capability family

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:taxon` Taxon | primary / `candidate` | taxonomy上の分類群をKnowledge Objectとして扱う | `morphology`, `ecology`, `behavior`, `distribution`, `characteristics`, `evolution`候補 | parent/child taxon・habitatはRelation。rank等はAttribute | 代表: 属・科等の分類群 / 反例: 個体Creature |
| `class:species` Species | primary / `candidate` | 実在生物のspecies | Taxon候補 + `physiology`, `reproduction`候補 | taxonomic parent / habitatはRelation。scientific name等はAttribute/alias | 代表: Felis catus / 反例: 作品世界のrace=`FictionalRace` |
| `class:fictional_race` FictionalRace | primary / `candidate` | 作品世界上のspecies/race-like集団 | `biology`, `culture`, `society`, `history`, `abilities`, `distribution` | member / inhabits / appears_in / related_taxonはRelation | 代表: 公式設定された架空種族 / 反例: 思想で集まったFaction |
| `class:concept` Concept | primary / `existing` | 独立定義・比較価値を持つ抽象概念 | 現行: `definition`, `properties`, `implications`, `related_concepts`, `examples`。追加候補: `history`, `interpretations`, `usage` | concrete instances / embodies / theme_of等はRelation | 代表: 自己犠牲 / 反例: 固有能力=`Ability` |
| `class:theme` Theme | primary / `inherit-current` | Work等を横断する主題・motif概念 | Concept profile + `manifestations`, `interpretations`, `functions`候補 | theme_of / embodied_byはRelation | 代表: 成長・自己犠牲という主題 / 反例: あるWorkのテーマ説明そのものはWork `themes` Facet |
| `class:ideology` Ideology | primary / `inherit-current` | 体系化された思想・doctrine・philosophy | Concept profile + `principles`, `values`, `history`, `practices`, `variants` | held_by / influences / opposed_toはRelation | 代表: 思想体系 / 反例: Personの単発の意見Statement |
| `class:trait` Trait | primary / `inherit-current` | 独立概念として扱う比較的持続的な性質 | Concept profile + `dimensions`, `manifestations`, `assessment`候補 | trait_ofはRelationまたは対象Facetで記述 | 代表: 外向性というTrait概念 / 反例: 今怒っているという一時Emotion state |
| `class:emotion` Emotion | primary / `inherit-current` | 感情概念そのもの | Concept profile + `triggers`, `experience`, `expression`, `effects`, `regulation` | experienced_byはRelation/Statement | 代表: 恐怖というEmotion概念 / 反例: Character Aが今恐れている、はCharacter Knowledge |
| `class:motivation` Motivation | primary / `inherit-current` | 行動を方向付ける動機概念 | Concept profile + `drivers`, `goals`, `behavioral_effects`, `manifestations` | motivates / goal_ofはRelation | 代表: 承認欲求という概念 / 反例: Character固有の復讐動機説明はCharacter `motivation` Facet |
| `class:state_concept` StateConcept | primary / `inherit-current` | 定義・原因・結果等を独立Knowledge化する状態概念 | Concept profile + `criteria`, `causes`, `effects`, `transitions`, `manifestations` | Objectのcurrent lifecycle/statusはAttribute/Registry state | 代表: 孤立状態という概念 / 反例: `objects.status=active` |
| `class:role_concept` RoleConcept | primary / `inherit-current` | 職業・役割・地位・称号の概念 | Concept profile + `responsibilities`, `authority`, `requirements`, `context`, `history` | Agentがroleを持つ事実はRelation/value | 代表: 教師という役割概念 / 反例: Aが教師であること自体 |
| `class:artifact_type_concept` ArtifactTypeConcept | primary / `inherit-current` | 一般的な人工物type/categoryの概念 | Concept profile + `function`, `usage`, `variants`, `design_principles` | individual artifacts / productsはRelationまたはinstances | 代表: 剣という一般カテゴリ / 反例: エクスカリバーという固有Artifact |
| `class:capability` Capability | structural / `family-candidate` | Ability / Skill family。直接Primary assignmentしない | 継承候補: `mechanism`, `effects`, `requirements`, `constraints`, `variants` | users / part_of_systemはRelation | 代表: Ability/Skill ancestor / 反例: 固有能力をPrimary=`Capability` |
| `class:ability` Ability | primary / `candidate` | 名称・ルール・制約を独立して持つ能力・power | `definition`, `mechanism`, `effects`, `limits`, `conditions`, `variants` | possessed_by / used_by / part_of_systemはRelation | 代表: 固有特殊能力 / 反例: 習得技法中心ならSkill |
| `class:skill` Skill | primary / `candidate` | 習得・訓練可能な技能/technique | `definition`, `procedure`, `requirements`, `mastery`, `effects`, `training`, `variants` | used_by / requires tool / part_ofはRelation | 代表: 剣術技法 / 反例: 一回の斬撃event/action instance |

---

## 9. Process / Temporal family

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:process` Process | primary / `candidate` | stages / inputs / outputs / conditionsを持つ過程type | `stages`, `inputs`, `outputs`, `mechanism`, `conditions`, `controls` | materials / produced objects / enabling systemsはRelation | 代表: 発酵・製造工程 / 反例: 2026年の特定製造事故=`Event` |
| `class:action` Action | primary / `candidate` | 離散的な行為typeをKnowledge化する | `definition`, `procedure`, `preconditions`, `participants_roles`, `effects`, `purpose` | performer / tool / targetはRelation。単発実行はEvent/Statement | 代表: 投票という行為type / 反例: Relation predicate `uses`をAction Object化 |
| `class:activity` Activity | primary / `candidate` | 継続・反復される活動type | `definition`, `purpose`, `practice`, `participants_roles`, `context`, `outcomes` | performers / locations / equipmentはRelation | 代表: 料理・演奏という活動 / 反例: 2026-10-12のライブ公演=`Event` |
| `class:temporal_entity` TemporalEntity | structural / `family-candidate` | named temporal context family。直接Primary assignmentしない | family候補: `scope`, `chronology`, `transitions`。descendant差を要検証 | start/end等はTemporal Scope/Attribute | 代表: Period/Timeline ancestor / 反例: 任意date rangeをPrimary=`TemporalEntity` |
| `class:period` Period | primary / `candidate` | 名称・Identityを持つ期間 | `scope`, `characteristics`, `chronology`, `events`, `transitions` | start/endはAttribute。contained eventsはRelation | 代表: 名称付き時期 / 反例: 2020-01-01〜2020-02-01という無名区間 |
| `class:era` Era | primary / `candidate` | 歴史的・作品世界上の時代として意味を持つPeriod | Period候補 + `culture`, `society`, `historical_context` | dates / events / placesはAttribute/Relation | 代表: 江戸時代 / 反例: 単なる10年間 |
| `class:timeline` Timeline | primary / `candidate` | Work/Event等を配置する時間系列context | `scope`, `chronology`, `branches`, `divergence`, `ordering_principles` | contained Work/EventはRelation。単なる表示年表はderived view | 代表: 公式timeline / 反例: UI上の年表表示だけ |
| `class:continuity` Continuity | primary / `candidate` | canon・world-line・identityを区別するcontinuity context | `scope`, `canon_rules`, `chronology`, `divergences`, `identity_rules` | included works/worlds/charactersはRelation | 代表: reboot前後を分ける公式continuity / 反例: 単なるSeries分類 |

---

## 10. System / Material / Phenomenon / SymbolicSystem family

| Class | Policy / profile | 意味境界 | 主なKnowledge / Facet候補 | 非Facet境界 | Representative / counterexample |
|---|---|---|---|---|---|
| `class:system` System | primary / `candidate` | 独自ルール・構成要素・制約を持つ体系 | `purpose`, `architecture`, `components`, `rules`, `behavior`, `constraints`, `interfaces` | component / depends_on / governed objectsはRelation | 代表: 情報system・制度的system / 反例: 単純な抽象Concept |
| `class:software` Software | primary / `candidate` | 独立名称・機能・Version・Sourceを持つsoftware | `purpose`, `architecture`, `features`, `compatibility`, `history`, `operation` | developed_by / depends_on / integrates_withはRelation。version番号等はAttribute/edition relation | 代表: VS Code / 反例: softwareを提供する会社=`Organization` |
| `class:service` Service | primary / `candidate` | 継続的に提供されるservice | `purpose`, `features`, `access`, `policy`, `operation`, `history` | provided_by / integrates_with / available_inはRelation | 代表: 配信/Web service / 反例: service provider企業そのもの |
| `class:rule_system` RuleSystem | primary / `candidate` | 複数Objectの挙動を規定するrule-governed system | `rules`, `components`, `constraints`, `exceptions`, `interactions`, `progression`候補 | governed objects / contains_ability / used_inはRelation | 代表: 魔法体系・ゲームルール / 反例: 単一のルールStatement |
| `class:material` Material | primary / `candidate` | 材料として独立性質・用途を持つ対象 | `properties`, `composition`, `processing`, `uses`, `behavior`, `safety`候補 | composed_of / used_to_make / source locationはRelation | 代表: 木材・鋼材 / 反例: その材料で作った製品 |
| `class:substance` Substance | primary / `candidate` | 化学的・物理的identityを強く持つ物質 | Material候補 + `chemical_properties`, `reactions`, `occurrence`候補 | reacts_with / found_at / component_ofはRelation。formula等はAttribute | 代表: 水・エタノール / 反例: 複合構造を用途中心で扱う材料=`Material` |
| `class:phenomenon` Phenomenon | primary / `candidate` | 繰り返し生じる現象type | `mechanism`, `causes`, `conditions`, `effects`, `observation`, `measurement`, `examples` | specific occurrenceはEvent。affected objectsはRelation | 代表: 流行現象というtype / 反例: 特定日時の流行event |
| `class:natural_phenomenon` NaturalPhenomenon | primary / `candidate` | 自然界のphenomenon type | `mechanism`, `conditions`, `effects`, `measurement`, `distribution`, `hazards` | specific earthquake/typhoonはEvent | 代表: 雷・オーロラ / 反例: 2026年の特定台風 |
| `class:social_phenomenon` SocialPhenomenon | primary / `candidate` | 社会に反復・広域的に現れるphenomenon type | `causes`, `dynamics`, `manifestations`, `effects`, `measurement`, `history_context` | organizations / events / affected groupsはRelation | 代表: インフレーション・社会的流行 / 反例: 政党=`Organization`、単発選挙=`Event` |
| `class:symbolic_system` SymbolicSystem | structural / `family-candidate` | Language / WritingSystem等のsymbol system family | 継承候補: `structure`, `rules`, `symbols`, `usage`, `history` | users/languages/scripts間接続はRelation | 代表: Language/WritingSystem ancestor / 反例: 実言語をPrimary=`SymbolicSystem` |
| `class:language` Language | primary / `candidate` | 自然・人工・架空のlanguage | `grammar`, `phonology`, `vocabulary`, `usage`, `history`, `variation` | spoken_by / derived_from / writing_systemはRelation | 代表: 日本語・架空言語 / 反例: Latin alphabet=`WritingSystem` |
| `class:writing_system` WritingSystem | primary / `candidate` | 文字・表記体系 | `structure`, `symbols`, `orthography_rules`, `usage`, `history`, `encoding`候補 | used_by language / derived_fromはRelation | 代表: 漢字体系・Latin alphabet / 反例: 日本語=`Language` |

---

## 11. 62 Class coverage結果

Migration 003の初期Registry 62 Classをすべてsurveyした。

分類上の結果:

- Structural Class: 7件。
- Additional-only Class: 1件。
- Primary-eligible Class: 54件。
- 直接Object用専用profile不要と判断: `ObjectClass`, `FictionalEntity`。
- Structural family-level inherited profile候補: `Agent`, `CreativeWork`, `WorkComponent`, `Capability`, `TemporalEntity`, `SymbolicSystem`。ただし実際にprofileを置くかはE-02Bで判断する。
- 現行E-02 profileを直接持つ: `Character`, `Work`, `Concept`。
- 現行profileをClass hierarchyから継承する: `Adaptation`, `WorkEdition`, `Theme`, `Ideology`, `Trait`, `Emotion`, `Motivation`, `StateConcept`, `RoleConcept`, `ArtifactTypeConcept`。
- その他のPrimary-eligible Classには、common `overall`だけで長期運用するより専用候補を検討する価値がある。

### 現行profileで不足が見えた代表点

- Character: `background`, `appearance`候補。
- Work: `production`, `reception`, `setting`候補。
- Concept: `history`, `interpretations`, `usage`候補。
- Adaptation / WorkEdition: 元Workとの差分を記述する専用観点候補。
- Concept subclasses: 現行Concept profileは基礎として有効だが、Ideologyの`principles`、Emotionの`triggers`等の専門観点を追加候補として検討する。

---

## 12. E-02Bへ渡すFacet vocabulary論点

E-02Aでは意図的に候補語彙を統合し切っていない。E-02Bでは少なくとも次を比較する。

| 候補群 | E-02Bで判断する内容 |
|---|---|
| purpose / function / use / usage / application | 同一Facetへ寄せる範囲と、Object familyごとの意味差 |
| history / evolution / development | 時系列変化を共通`history`へ寄せるか、構造的進化を別Facetにするか |
| structure / architecture / organization / components | 組織・System・SymbolicSystem間で共通化できる粒度 |
| properties / characteristics / traits | Concept / Material / Taxonで共有可能か |
| rules / constraints / conditions / limits | RuleSystem / Capability / Processでの境界 |
| mechanism / procedure / process / behavior | 「どう働くか」と「どう実行するか」を分けるか |
| causes / drivers / triggers / conditions | Event / Emotion / Phenomenon等で共通化可能か |
| effects / outcomes / implications | 因果結果と意味的含意を同一視しないための境界 |
| relationships / dynamics / interactions | Object間Relationの要約Facetとして共通化するか |
| chronology / history / timeline | Object内部の時系列説明とTemporalEntity Objectをどう分けるか |
| scope / identity / overall | `overall`との重複を避ける基準 |
| production / origin / provenance | 制作史とSource Provenanceを混同しない命名 |
| characters / participants / members / users | Relation-derived集合をFacetとして保持する場合の責務 |

特に`provenance`という語はE-03のSource / Evidence Provenanceと衝突しやすいため、Artifact等の「来歴」Facet名としてそのまま採用しない方が安全である。

---

## 13. E-02Cへ渡すClass / Facet境界論点

E-02Cのgold casesには、少なくとも次を含める。

1. `Character`と`Person`を同名・モデル関係でも混同しない。
2. `Organization` / `Group` / `Team` / `Faction`を制度性・目的・陣営性で区別する。
3. `Work` / `Series` / `Franchise` / `WorkComponent`をpart-of関係だけで丸めない。
4. `Adaptation` / `WorkEdition` / SGOKB Knowledge Versionを区別する。
5. `Place`とWorkのsetting Facet、`World`と`Continuity`を区別する。
6. `Event`と`Phenomenon`、`Process`をspecific occurrenceかtype/processかで区別する。
7. `Artifact` / `Product` / `ArtifactTypeConcept`を個体・product model・一般typeで区別する。
8. `Taxon` / `Species` / `FictionalRace` / `Creature`を分類群・種・架空種族・個体で区別する。
9. Concept subclassesと対象Object内Facet valueを区別する。
10. `Ability` / `Skill`とCharacter `abilities` Facetを併用できることを確認する。
11. `Period` / `Era`とscalar date interval、`Timeline` / `Continuity`とderived chronologyを区別する。
12. `System` / `RuleSystem` / `Software` / `Service`を目的と責務で区別する。
13. `Material` / `Substance` / `Product`を物性identityと製品identityで区別する。
14. `Language`と`WritingSystem`を分離しRelationで接続する。
15. Structural ClassへObjectを直接assignしない。
16. `FictionalEntity`をPrimaryにせず、必要なObjectへAdditional分類として使う。

---

## 14. Schema / Registryへの影響

E-02AではMigration 003 / 004、Facet Registry seed、Class-to-Facet profileを変更しない。

理由:

- 本Taskの目的は候補と境界の網羅確認である。
- 近義Facetをここで個別にseedすると、Classごとの局所設計が先行しFacet vocabularyが肥大化する。
- E-02Bで全候補を横断比較してからshared / class-specific / inherited profileを確定する方が安全である。

したがってE-02A完了時点のruntime behaviorはE-02 core完了時と同一である。

---

## 15. 完了条件への対応

- [x] Migration 003の62 Classを全件surveyした。
- [x] 各Classの意味境界を記述した。
- [x] 含めるもの / 含めないものをrepresentative / counterexampleで確認可能にした。
- [x] 専用Facet候補または専用profile不要判断を記録した。
- [x] Object / Attribute / Relation / Statementとの主要境界を記録した。
- [x] `overall`を恒久catch-allにしないため、未整備ClassのFacet候補を明示した。
- [x] 近義FacetをE-02Bで統合すべき論点として抽出した。
- [x] E-02Cのgold case作成へ必要な境界論点を抽出した。
- [x] 物理schema / Registry seedを先取り変更していない。

---

## 16. 結論

全62 Classを横断すると、**「すべてのClassへ独自Facet集合を作る」ことも、「Character / Work / Concept以外を`overall`だけで運用し続ける」ことも適切ではない。**

採るべき方向は、ClassごとのKnowledge観点を一度すべて列挙したうえで、E-02Bで近義語を統合し、shared Facet・Structural Classからの継承Facet・Class-specific Facetを最小限のvocabularyへ整理することである。

E-02Aではそのためのsurvey母集団とClass境界を確定した。次Taskは **`E-02B [P0] Facet vocabularyを横断統合する`** とする。
