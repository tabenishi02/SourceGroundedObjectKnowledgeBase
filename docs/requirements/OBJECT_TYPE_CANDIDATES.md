# SGOKB Object Type Candidates

更新日: 2026-10-10

- Task: `B-02B [P0] SGOKB Object候補を網羅的に整理する`
- Status: Accepted
- Parent: `B-02 [P0] Object要件を定義する`
- Input:
  - `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
- B-02D result: `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
- Next:
  - `B-02C [P0] Object Type / Class階層を設計する`（完了）
  - `B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する`（完了）

## 1. 目的

本書は、SGOKBが将来Knowledgeとして扱い得る対象を、現在の `Character` / `Work` / `Concept` だけに限定せず網羅的に洗い出し、各候補について独立Object化する価値を評価する。

B-02Aで調査したSchema.org、DBpedia、Wikidata、WordNet、DCMI等の分類体系を候補漏れ防止に利用する。ただし、本書では最終的なObject Type / Class階層を確定しない。

本書の役割は次のとおりである。

1. 将来必要になり得る対象カテゴリを候補として残す。
2. 各候補について独立Object化の価値を比較可能にする。
3. 想定Source、Relation、Facetを先に列挙し、後続設計の漏れを防ぐ。
4. Class Registryへの包含候補と、Class固有機能の実装優先度を区別して後続設計へ渡す。
5. B-02C / B-02DでType / Class / Facet / Relation / 対象外を判断するための入力を作る。

---

## 2. 評価方法

### 2.1 独立Object化の判断基準

`OBJECT_TYPE_REFINEMENT_TASKS.md` の基準に従い、次の6観点を評価する。

| 記号 | 判断基準 |
|---|---|
| I | 独立したIdentityを持つか |
| S | 複数SourceからKnowledgeを蓄積する価値があるか |
| R | 他Objectから参照されるか |
| Q | それ自体を検索・比較したいか |
| V | 独自のKnowledge Versionを持つ価値があるか |
| E | Source / Evidenceを独立して関連付けたいか |

### 2.2 独立Object化価値

- **高**: 6観点の多くを通常満たし、独立Objectとして扱う価値が明確。
- **中**: 対象によって独立Object化の価値が高いが、Facet / Relation / Classとの境界判断が必要。
- **低**: 一般には独立ObjectよりFacet value、Relation、Class、Source metadata等が適する。ただし例外はあり得る。

この評価はB-02B時点の予備評価である。最終配置はB-02D成果物`OBJECT_TYPE_BOUNDARIES.md`を正本とする。

### 2.3 当初の実装優先度評価

B-02Bでは候補比較のため`Core` / `High` / `Future` / `Boundary`を付与した。B-02C後、この評価は**Class Registryへの包含時期ではなく、Class固有機能の実装優先度を示す予備評価**として解釈する。

- **Core**: 専用Facet / UI / validation等を初期から優先的に整備する価値が高い。
- **High**: 早期に専用機能を整備する価値が高い。
- **Future**: 専用機能は後段でもよい。ただしB-02Dで正式Classとして採用された場合は原則として初期Class Registryへ登録する。
- **Boundary**: Object / Classとして採用するか自体をB-02Dで判断するため、採用確定までは初期Registry対象としない。

したがって、`Future`は「Classそのものを後から追加する」という意味ではない。

---

# 3. Candidate Family一覧

B-02Aの調査結果とSGOKBの利用目的から、少なくとも次の候補Familyを検討対象とする。

```text
Object Candidate
├─ Agent / Actor
├─ Creative Work / Media
├─ Place / Setting
├─ Event
├─ Artifact / Item / Product
├─ Biological / Taxonomic
├─ Concept / Abstract
├─ Action / Process / Ability
├─ Time / Period
├─ System / Service / Software
├─ Substance / Material
├─ Natural Phenomenon
└─ Language / Term / Symbolic System
```

これはB-02B時点の候補母集団である。B-02CでClassification modelへ整理済みであり、各候補の最終配置はB-02Dで確定する。

---

# 4. Agent / Actor系

## 4.1 Character / Fictional Character

- **定義:** 物語、ゲーム、漫画、アニメ等に登場し、人格・役割・行動主体として扱われる架空の個体。
- **代表例:** 個別キャラクター、別continuity上の別個体。
- **独立Object化価値:** **高**。I/S/R/Q/V/Eをほぼ常に満たす。
- **想定ユースケース:** 性格・価値観比較、Roleplay Context、Work横断登場関係、Conceptとの関連分析。
- **Source例:** 公式Character紹介、公式設定資料、作品本文、インタビュー、百科事典、Wiki、レビュー・解説。
- **Relation候補:** `appears_in`, `member_of`, `related_to`, `family_of`, `rival_of`, `embodies`, `uses`。
- **Facet候補:** personality, values, motivation, behavior, relationships, role, background, appearance, abilities, themes。
- **実装優先度:** **Core**。既存要件で確定済み。
- **後続論点:** Personと共通上位Typeを持つか。別continuityのIdentity境界。

## 4.2 Person

- **定義:** 実在する、または歴史上実在した人物。
- **代表例:** 作者、声優、監督、研究者、歴史人物。
- **独立Object化価値:** **高**。複数Source、所属、作品、経歴等とのRelationが豊富。
- **想定ユースケース:** WorkのCreator追跡、インタビュー発言の主体、人物横断比較。
- **Source例:** 公式プロフィール、インタビュー、所属組織ページ、百科事典、論文著者情報。
- **Relation候補:** `created`, `performed`, `member_of`, `works_for`, `influenced`, `related_to`。
- **Facet候補:** biography, career, roles, works, public_statements, expertise。
- **実装優先度:** **High**。Character/Work中心MVPに必須ではないがSource理解に有用。
- **後続論点:** Characterと同じAgent系に置くか。

## 4.3 Organization

- **定義:** 継続的Identityを持つ組織・法人・団体。
- **代表例:** 制作会社、出版社、ゲーム会社、学校、国家機関、架空組織。
- **独立Object化価値:** **高**。
- **Source例:** 公式About、会社情報、作品Credits、百科事典、公式設定ページ。
- **Relation候補:** `employs`, `publishes`, `produces`, `owns`, `member`, `affiliated_with`。
- **Facet候補:** purpose, history, structure, activities, members, works, culture。
- **実装優先度:** **High**。
- **後続論点:** 実在・架空Organizationを同一Class配下にするか。

## 4.4 Group / Team / Unit

- **定義:** 複数Agentから成る集合で、独自名称・Identity・活動を持つ集団。
- **代表例:** アイドルユニット、スポーツチーム、冒険者パーティ、バンド。
- **独立Object化価値:** **高〜中**。単なる一時的集合なら低いが、名称・歴史・関係を持つ場合は高い。
- **Source例:** 公式ユニット紹介、チームページ、作品設定、Wikipedia等。
- **Relation候補:** `has_member`, `belongs_to`, `competes_with`, `part_of`, `appears_in`。
- **Facet候補:** identity, purpose, membership, dynamics, history, achievements。
- **実装優先度:** **Future / High**。
- **後続論点:** Organization subtypeか別Classか。

## 4.5 Faction

- **定義:** 政治的・軍事的・思想的な陣営・派閥。
- **代表例:** 作品世界内の派閥、政党内派閥、対立陣営。
- **独立Object化価値:** **中〜高**。独自目的・構成員・歴史を持つ場合は高い。
- **Source例:** 公式Lore、設定資料、百科事典、解説記事。
- **Relation候補:** `has_member`, `opposes`, `allied_with`, `part_of`, `controls`。
- **Facet候補:** ideology, goals, structure, history, territory, conflicts。
- **実装優先度:** **Future**。
- **後続論点:** Organization / Group subtypeか、Concept的Ideologyとの境界。

## 4.6 Role / Occupation / Title

- **定義:** Agentが担う役割、職業、地位、称号。
- **代表例:** 教師、王、プロデューサー、隊長。
- **独立Object化価値:** **低〜中**。一般にはClass / Concept / Relation valueで十分だが、独自歴史・制度・Evidenceを持つ役職はObject候補になり得る。
- **Source例:** 職業解説、組織規程、設定資料。
- **Relation候補:** `has_role`, `position_in`, `succeeds`。
- **Facet候補:** definition, responsibilities, authority, requirements。
- **実装優先度:** **Boundary**。
- **後続論点:** Class、Concept、Relation valueのいずれに置くか。

---

# 5. Creative Work / Media系

## 5.1 Work / CreativeWork

- **定義:** 創作・著作・表現物として独立してKnowledgeを蓄積する対象。
- **代表例:** 小説、漫画、アニメ、映画、ゲーム、楽曲、アルバム、ソフトウェア作品。
- **独立Object化価値:** **高**。
- **Source例:** 公式作品ページ、出版社・配給元、Store listing、百科事典、レビュー、インタビュー。
- **Relation候補:** `created_by`, `published_by`, `adaptation_of`, `part_of_series`, `features`, `influenced_by`。
- **Facet候補:** summary, themes, worldview, narrative, tone, characters, reception, production。
- **実装優先度:** **Core**。既存要件で確定済み。
- **後続論点:** media subtypeの表現方法。

## 5.2 Series

- **定義:** 複数Workを継続的なまとまりとして束ねる作品系列。
- **代表例:** TVシリーズ、書籍シリーズ、ゲームシリーズ。
- **独立Object化価値:** **高**。シリーズ全体のテーマ・歴史・Relationを個別作品とは別に持つ価値がある。
- **Source例:** 公式シリーズポータル、出版社シリーズページ、百科事典。
- **Relation候補:** `has_part`, `includes_work`, `spin_off`, `adapted_as`。
- **Facet候補:** overall_identity, chronology, themes, continuity, installments, evolution。
- **実装優先度:** **High**。既存OBJ-16と整合。
- **後続論点:** Work subtypeか上位/別Classか。

## 5.3 Franchise / IP

- **定義:** 複数media・Series・商品展開を横断する知的財産・ブランド的まとまり。
- **代表例:** 複数ゲーム・アニメ・漫画を含むメディアミックスIP。
- **独立Object化価値:** **中〜高**。Seriesより広い範囲を束ねる場合に有用。
- **Source例:** 公式ポータル、権利者ページ、企業資料、百科事典。
- **Relation候補:** `includes_series`, `includes_work`, `owned_by`, `licensed_to`。
- **Facet候補:** identity, scope, history, media_mix, ownership, continuity_groups。
- **実装優先度:** **Future**。
- **後続論点:** Seriesとの意味境界。

## 5.4 Episode / Chapter / Installment

- **定義:** Series/Workを構成する個別エピソード・章・話・巻等。
- **代表例:** TV第1話、漫画第10話、小説第3章。
- **独立Object化価値:** **中〜高**。独自タイトル・出来事・Source・Relationを持ち、検索対象にしたい場合は高い。
- **Source例:** 公式episode list、配信ページ、目次、あらすじページ、Wiki。
- **Relation候補:** `part_of`, `precedes`, `follows`, `features`, `contains_event`。
- **Facet候補:** summary, events, characters, themes, location, chronology。
- **実装優先度:** **Future**。
- **後続論点:** Object化閾値。単なる構造要素として保持する場合との境界。

## 5.5 Season / Volume / Arc

- **定義:** Work内の複数installmentを束ねる中間構造。
- **独立Object化価値:** **中**。名称・独立テーマ・公式Identityがある場合に有用。
- **Source例:** 公式season/volumeページ、目次、配信一覧、設定資料。
- **Relation候補:** `part_of`, `has_part`, `precedes`, `covers_arc`。
- **Facet候補:** scope, chronology, themes, cast, major_events。
- **実装優先度:** **Boundary / Future**。
- **後続論点:** Class、Object、単なるordering metadataの境界。

## 5.6 Adaptation / Edition / Version

- **定義:** 同一原作から派生する別media作品、改訂版、remake等。
- **独立Object化価値:** **中〜高**。内容差分がKnowledgeとして重要なら別Objectが適切。
- **Source例:** 公式製品ページ、版情報、出版社、Store、比較記事。
- **Relation候補:** `adaptation_of`, `remake_of`, `edition_of`, `based_on`。
- **Facet候補:** changes, medium, production, scope, reception。
- **実装優先度:** **High / Future**。
- **後続論点:** Object IdentityとWork Versionの区別。Knowledge Versionと作品版を混同しない。

---

# 6. Place / Setting系

## 6.1 Real Place

- **定義:** 現実世界に存在する地理的・施設的対象。
- **代表例:** 国、都市、建物、地域、山、店舗。
- **独立Object化価値:** **高**。
- **Source例:** 公式自治体・施設ページ、地理資料、百科事典、地図説明。
- **Relation候補:** `located_in`, `contains`, `origin_of`, `event_at`, `associated_with`。
- **Facet候補:** geography, history, culture, function, notable_features。
- **実装優先度:** **Future**。

## 6.2 Fictional Place / Setting

- **定義:** 作品世界内の場所、地域、施設、世界。
- **代表例:** 架空都市、学校、惑星、異世界。
- **独立Object化価値:** **高**。複数Character / Event / Workから参照される。
- **Source例:** 公式world guide、設定資料、作品本文、Wiki。
- **Relation候補:** `appears_in`, `located_in`, `home_of`, `event_at`, `controlled_by`。
- **Facet候補:** geography, society, culture, history, atmosphere, rules。
- **実装優先度:** **High / Future**。
- **後続論点:** Real Placeと共通Place配下にするか。

## 6.3 Setting / World

- **定義:** 単一地点ではなく、作品の世界観・宇宙・continuity全体を表す対象。
- **独立Object化価値:** **中〜高**。単なるWork Facetとして十分な場合と、複数Workを跨ぐWorld Objectが必要な場合がある。
- **Source例:** 公式設定集、world guide、シリーズポータル。
- **Relation候補:** `setting_of`, `contains_place`, `contains_faction`, `continuity_of`。
- **Facet候補:** laws, cosmology, society, history, geography, technology/magic。
- **実装優先度:** **Boundary**。

---

# 7. Event系

## 7.1 Historical / Real Event

- **定義:** 現実世界で発生した識別可能な出来事。
- **代表例:** 戦争、災害、選挙、ライブ、公演、競技大会。
- **独立Object化価値:** **高**。
- **Source例:** 公式記録、報道、百科事典、イベント公式ページ。
- **Relation候補:** `occurred_at`, `participant`, `caused_by`, `resulted_in`, `part_of`。
- **Facet候補:** chronology, participants, causes, outcomes, significance, location。
- **実装優先度:** **Future**。

## 7.2 Fictional Event

- **定義:** 作品世界内で発生する識別可能な出来事。
- **代表例:** 戦争、事件、祭典、物語上の転換点。
- **独立Object化価値:** **中〜高**。複数Character/Place/Workに跨る重要Eventでは高い。
- **Source例:** 作品本文、公式timeline、設定資料、Wiki。
- **Relation候補:** `occurs_in`, `participant`, `causes`, `affects`, `precedes`。
- **Facet候補:** chronology, cause, participants, outcome, significance。
- **実装優先度:** **Future**。

## 7.3 Release / Publication / Production Event

- **定義:** Workの公開、発売、放送、上演、制作上の出来事。
- **独立Object化価値:** **低〜中**。通常はWork metadataで足りるが、イベント自体を追跡・比較する用途ではObject候補。
- **Source例:** 公式告知、ニュース、release notes。
- **Relation候補:** `releases`, `publishes`, `launch_of`, `held_at`。
- **Facet候補:** date, participants, venue, scope。
- **実装優先度:** **Boundary**。

---

# 8. Artifact / Item / Product系

## 8.1 Artifact / Named Item

- **定義:** 独自Identity・名称・歴史を持つ物理的または架空の物品。
- **代表例:** 固有の武器、車両、衣装、歴史的遺物。
- **独立Object化価値:** **中〜高**。
- **Source例:** 公式商品/設定ページ、博物館資料、作品設定、百科事典。
- **Relation候補:** `owned_by`, `used_by`, `created_by`, `appears_in`, `located_at`。
- **Facet候補:** appearance, function, history, capabilities, provenance。
- **実装優先度:** **Future**。

## 8.2 Product / Product Model

- **定義:** 市販製品または製品model。
- **独立Object化価値:** **中〜高**。SGOKBを一般Knowledgeへ拡張する場合に価値がある。
- **Source例:** メーカー公式、仕様書、販売ページ、レビュー。
- **Relation候補:** `manufactured_by`, `model_of`, `successor_of`, `compatible_with`。
- **Facet候補:** specifications, design, use, variants, reception。
- **実装優先度:** **Future**。

## 8.3 Generic Item Type / Equipment Class

- **定義:** 「剣」「スマートフォン」等の一般カテゴリ。
- **独立Object化価値:** **低〜中**。個体ObjectよりClass / Conceptとして扱う方が自然な場合が多い。
- **Source例:** 辞典、技術資料、分類資料。
- **Relation候補:** `instance_of`, `used_for`, `related_to`。
- **Facet候補:** definition, properties, usage, variants。
- **実装優先度:** **Boundary**。

---

# 9. Biological / Taxonomic系

## 9.1 Species / Taxon

- **定義:** 生物分類上の種・分類群、またはそれに準じる架空生物分類。
- **独立Object化価値:** **高**。複数個体・場所・Conceptから参照され、独自Knowledgeを持つ。
- **Source例:** taxonomy database、学術資料、図鑑、公式設定資料。
- **Relation候補:** `subclass_of`, `habitat`, `related_taxon`, `member`, `appears_in`。
- **Facet候補:** classification, morphology, ecology, behavior, distribution, traits。
- **実装優先度:** **Future**。

## 9.2 Fictional Species / Race

- **定義:** 作品世界内の種族・人種・race・speciesとして定義される集合。
- **独立Object化価値:** **中〜高**。
- **Source例:** 公式world guide、設定資料、Wiki。
- **Relation候補:** `member`, `origin`, `related_to`, `inhabits`, `appears_in`。
- **Facet候補:** biology, culture, abilities, society, history。
- **実装優先度:** **Future**。
- **後続論点:** Taxon、Class、Conceptのどれとして扱うか。

## 9.3 Named Animal / Creature Individual

- **定義:** 個体としてIdentityを持つ非人間生物・Creature。
- **独立Object化価値:** **中〜高**。固有名・経歴・Relationを持つ場合はAgent的Objectとして価値がある。
- **Source例:** 公式プロフィール、動物園/研究機関ページ、作品設定。
- **Relation候補:** `species`, `owner`, `appears_in`, `lives_at`。
- **Facet候補:** biography, traits, behavior, relationships。
- **実装優先度:** **Future**。
- **後続論点:** Agent配下かBiological配下か、複数classificationの要否。

---

# 10. Concept / Abstract系

## 10.1 General Concept

- **定義:** 複数ObjectやSourceを横断して意味・性質・Relationを蓄積する価値がある抽象対象。
- **代表例:** 自己犠牲、復讐、成長、忠誠、孤独。
- **独立Object化価値:** **高**。
- **Source例:** 辞典、論文、評論、作品分析、公式インタビュー。
- **Relation候補:** `related_to`, `opposite_of`, `broader_than`, `embodied_by`, `theme_of`。
- **Facet候補:** definition, properties, implications, examples, related_concepts, interpretations。
- **実装優先度:** **Core**。既存要件で確定済み。

## 10.2 Theme / Motif

- **定義:** WorkやCharacterを横断して現れる主題・モチーフ。
- **独立Object化価値:** **中〜高**。作品横断比較・UPDS連携で価値が高い。
- **Source例:** 評論、作者インタビュー、研究、解説。
- **Relation候補:** `theme_of`, `embodied_by`, `contrasts_with`, `related_to`。
- **Facet候補:** definition, manifestations, interpretations, examples。
- **実装優先度:** **High**。Concept subtype候補。

## 10.3 Ideology / Doctrine / Philosophy

- **定義:** 一定の体系性を持つ思想・価値体系。
- **独立Object化価値:** **高**。
- **Source例:** 原典、辞典、学術資料、解説。
- **Relation候補:** `influences`, `opposed_to`, `held_by`, `derived_from`。
- **Facet候補:** principles, history, values, implications, variants。
- **実装優先度:** **Future / High**。Concept subtype候補。

## 10.4 Attribute / Trait

- **定義:** 対象の性質を表す概念。
- **代表例:** 勇敢、内向的、赤色、脆弱性。
- **独立Object化価値:** **低〜中**。比較・Concept体系化したい場合はObject価値があるが、通常はFacet valueで十分。
- **Source例:** 辞典、心理学資料、専門資料。
- **Relation候補:** `attribute_of`, `opposite_of`, `correlated_with`。
- **Facet候補:** definition, dimensions, examples, implications。
- **実装優先度:** **Boundary**。

## 10.5 Feeling / Emotion

- **定義:** 感情状態・情動概念。
- **代表例:** 喜び、恐怖、嫉妬。
- **独立Object化価値:** **中**。Conceptとして分析・比較する価値はあるがCharacter状態値としても現れる。
- **Source例:** 心理学資料、辞典、評論。
- **Relation候補:** `caused_by`, `contrasts_with`, `experienced_by`, `related_to`。
- **Facet候補:** definition, triggers, expression, effects, related_emotions。
- **実装優先度:** **Boundary**。

## 10.6 Motivation / Goal

- **定義:** 行動を方向付ける動機・目的概念。
- **代表例:** 復讐願望、承認欲求、生存。
- **独立Object化価値:** **低〜中**。Character Facet valueとして使う場合が多いが、作品横断Conceptとして扱う価値もある。
- **Source例:** 心理学資料、評論、作品分析。
- **Relation候補:** `motivates`, `goal_of`, `related_to`。
- **Facet候補:** definition, causes, behavioral_effects, examples。
- **実装優先度:** **Boundary**。

## 10.7 State / Condition

- **定義:** 持続的または一時的な状態を表す概念。
- **代表例:** 孤立、混乱、戦争状態、覚醒状態。
- **独立Object化価値:** **低〜中**。一般にはFacet valueだが、定義・Relationを蓄積する対象ならConcept Object候補。
- **Source例:** 辞典、専門資料、作品設定。
- **実装優先度:** **Boundary**。

## 10.8 Natural / Social Phenomenon

- **定義:** 特定個体ではなく繰り返し観察される現象。
- **代表例:** 雷、インフレーション、流行、社会現象。
- **独立Object化価値:** **中〜高**。
- **Source例:** 科学資料、政府統計、論文、百科事典。
- **Relation候補:** `caused_by`, `affects`, `occurs_at`, `related_to`。
- **Facet候補:** mechanism, causes, effects, examples, measurement。
- **実装優先度:** **Future**。Conceptまたは別Class候補。

---

# 11. Action / Process / Ability系

## 11.1 Ability / Power

- **定義:** Agentが持つ能力・特殊能力・機能で、名称・ルール・Evidenceを独立して持つ対象。
- **代表例:** 固有能力、魔法体系上の能力、特殊技能。
- **独立Object化価値:** **中〜高**。複数Characterが共有し、独自設定を持つ場合に高い。
- **Source例:** 公式能力紹介、設定資料、作品本文、攻略資料。
- **Relation候補:** `possessed_by`, `used_by`, `derived_from`, `countered_by`, `part_of_system`。
- **Facet候補:** definition, mechanism, limits, effects, variants, users。
- **実装優先度:** **Future / Boundary**。

## 11.2 Skill / Technique

- **定義:** 習得可能な技能・技・手法。
- **独立Object化価値:** **中**。固有名と体系を持つ場合はObject候補、一般技能ならConcept/Classで十分。
- **Source例:** 技術資料、設定資料、攻略資料。
- **Relation候補:** `used_by`, `requires`, `part_of`, `derived_from`。
- **Facet候補:** procedure, requirements, effects, mastery, variants。
- **実装優先度:** **Boundary**。

## 11.3 Action / Activity

- **定義:** 行為・活動の種類。
- **代表例:** 戦闘、料理、投票、演奏。
- **独立Object化価値:** **低〜中**。一般語としてはClass/Conceptが自然。
- **Source例:** 辞典、手順書、専門資料。
- **Relation候補:** `performed_by`, `uses`, `occurs_at`。
- **Facet候補:** definition, participants, procedure, purpose。
- **実装優先度:** **Boundary**。

## 11.4 Process

- **定義:** 時間的段階を持つ変化・処理・自然/社会過程。
- **代表例:** 発酵、進化、製造工程、選挙過程。
- **独立Object化価値:** **中**。Knowledge対象として独立説明する価値がある場合に有用。
- **Source例:** 教科書、技術資料、論文、規格。
- **Relation候補:** `has_stage`, `causes`, `requires`, `produces`。
- **Facet候補:** stages, inputs, outputs, mechanism, conditions。
- **実装優先度:** **Future / Boundary**。

---

# 12. Time / Period系

## 12.1 Era / Historical Period

- **定義:** 名称・Identityを持つ歴史的期間。
- **代表例:** 江戸時代、ある作品世界の特定時代。
- **独立Object化価値:** **中〜高**。多数Objectから参照され、独自の歴史・文化・Sourceを持つ場合に高い。
- **Source例:** 歴史資料、年表、百科事典、公式timeline。
- **Relation候補:** `precedes`, `follows`, `contains_event`, `period_of`, `associated_with`。
- **Facet候補:** start/end, characteristics, events, culture, transitions。
- **実装優先度:** **Future**。

## 12.2 Date / Time Interval

- **定義:** 単なる日時・期間値。
- **独立Object化価値:** **低**。通常は属性値で十分。
- **Source例:** metadata、timeline。
- **実装優先度:** **Boundary / 非Object有力**。
- **後続論点:** named periodのみObject化する閾値。

## 12.3 Timeline / Continuity

- **定義:** Work群やEvent群を区別する時間的・世界線的まとまり。
- **独立Object化価値:** **中**。複数Work・Character Identity判断に利用する場合は価値がある。
- **Source例:** 公式timeline、設定資料、シリーズ解説。
- **Relation候補:** `contains_event`, `contains_work`, `branch_of`, `parallel_to`。
- **Facet候補:** scope, chronology, divergence, included_works。
- **実装優先度:** **Boundary / Future**。

---

# 13. System / Service / Software系

## 13.1 Software / Application / Game System

- **定義:** 独立名称・Version・機能を持つSoftwareまたは情報システム。
- **独立Object化価値:** **高**。一般Knowledgeを扱う場合に典型的Objectとなる。
- **Source例:** 公式Documentation、GitHub、release notes、製品ページ。
- **Relation候補:** `developed_by`, `depends_on`, `implements`, `compatible_with`, `successor_of`。
- **Facet候補:** purpose, architecture, features, compatibility, history。
- **実装優先度:** **Future**。
- **後続論点:** CreativeWork / Product / Artifactとのmultiple classification。

## 13.2 Service

- **定義:** 継続的に提供されるサービス。
- **代表例:** Web Service、配信サービス、公共サービス。
- **独立Object化価値:** **中〜高**。
- **Source例:** 公式サービスページ、規約、documentation。
- **Relation候補:** `provided_by`, `uses`, `available_in`, `integrates_with`。
- **Facet候補:** purpose, features, access, policy, history。
- **実装優先度:** **Future**。

## 13.3 Rule System / Magic System / Game Mechanic

- **定義:** 複数Objectの行動・能力・状態を規定する体系。
- **代表例:** 魔法体系、戦闘システム、ゲームルール。
- **独立Object化価値:** **中〜高**。体系自体にKnowledgeとRelationがある場合に有用。
- **Source例:** 公式rulebook、manual、設定資料、攻略資料。
- **Relation候補:** `governs`, `contains_ability`, `used_in`, `applies_to`。
- **Facet候補:** rules, components, constraints, exceptions, interactions。
- **実装優先度:** **Future / Boundary**。
- **後続論点:** Concept subtypeかSystem系Objectか。

---

# 14. Substance / Material系

## 14.1 Material / Substance

- **定義:** 物質・材料として独立した性質を持つ対象。
- **代表例:** 鉄、木材、水、架空鉱物。
- **独立Object化価値:** **中**。一般Knowledgeでは有用だが初期SGOKBの中心ではない。
- **Source例:** 技術資料、科学DB、設定資料。
- **Relation候補:** `composed_of`, `used_to_make`, `reacts_with`, `found_at`。
- **Facet候補:** properties, composition, uses, origin, behavior。
- **実装優先度:** **Future**。

## 14.2 Food / Drug / Consumable Category

- **定義:** 摂取物・薬品等の一般カテゴリまたは固有製品。
- **独立Object化価値:** **低〜中**。個別製品ならProduct、一般概念ならMaterial/Conceptに寄る。
- **実装優先度:** **Boundary / Future**。

---

# 15. Natural Phenomenon系

## 15.1 Natural Phenomenon

- **定義:** 自然界で発生する現象・現象類型。
- **代表例:** 台風、地震、雷、オーロラ。
- **独立Object化価値:** **中〜高**。現象類型はConcept的、個別台風・地震はEvent的に扱える。
- **Source例:** 気象機関、研究資料、百科事典。
- **Relation候補:** `causes`, `occurs_at`, `instance_of`, `affects`。
- **Facet候補:** mechanism, conditions, effects, measurement, examples。
- **実装優先度:** **Future / Boundary**。
- **後続論点:** Phenomenon classとEvent instanceの分離。

---

# 16. Language / Term / Symbolic System系

## 16.1 Language

- **定義:** 自然言語・人工言語・架空言語。
- **独立Object化価値:** **中〜高**。独自歴史・構造・使用者・Sourceを持つ。
- **Source例:** 言語資料、辞書、文法書、公式設定。
- **Relation候補:** `spoken_by`, `derived_from`, `related_to`, `used_in`。
- **Facet候補:** grammar, vocabulary, history, speakers, writing_system。
- **実装優先度:** **Future**。

## 16.2 Term / Defined Concept

- **定義:** 明確な定義を持つ用語。
- **独立Object化価値:** **低〜中**。用語の文字列そのものではなく、その背後のConceptをObject化する方が自然な場合が多い。
- **Source例:** glossary、規格、辞典。
- **Relation候補:** `denotes`, `synonym_of`, `broader_than`。
- **Facet候補:** definition, usage, etymology, scope。
- **実装優先度:** **Boundary**。

## 16.3 Writing System / Symbolic System

- **定義:** 文字体系・記号体系・分類記法等。
- **独立Object化価値:** **中**。
- **Source例:** 標準資料、学術資料、辞典。
- **Relation候補:** `used_by`, `represents`, `derived_from`。
- **Facet候補:** structure, symbols, history, usage。
- **実装優先度:** **Future**。

---

# 17. Resource / Sourceと混同しやすい候補

以下は独立Objectになり得る場合もあるが、SGOKBではまずSource Typeとの区別が必要である。

| 候補 | Objectになり得る場合 | Sourceとして扱う場合 |
|---|---|---|
| Article | 記事作品そのものを分析対象にする | Evidenceを提供するWeb記事 |
| Book | WorkとしてKnowledge対象にする | 参考資料として利用する書籍 |
| Dataset | Dataset自体の性質をKnowledge化する | Evidence取得元データ |
| Image | Artwork/CreativeWorkとして扱う | Source内の画像Evidence |
| Video | 映像作品として扱う | Interview/解説Source |
| Software | Software Objectとして扱う | 取得処理・Toolそのもの |
| Event | 出来事そのものをKnowledge化する | DCMI Resource typeとして記述される対象 |

同じ実体が利用文脈によってObjectとSourceの両方の役割を持つことを禁止しない。ただし、Object IdentityとSource recordは別レコード・別責務として扱う。

この詳細契約はB-03へ引き継ぐ。

---

# 18. 独立Object化価値の総括

## 18.1 高価値候補

通常、独立Objectとして扱う価値が高い。

- Character
- Person
- Organization
- Work
- Series
- Place
- Event
- Named Artifact
- Species / Taxon
- General Concept
- Ideology / Doctrine
- Software / System

## 18.2 条件付き高価値候補

Identity・複数Source・Relationが十分ある場合に独立Object化の価値が高い。

- Group / Team
- Faction
- Franchise
- Episode / Chapter
- Season / Arc
- Fictional Setting / World
- Fictional Event
- Product
- Fictional Race
- Named Creature
- Theme / Motif
- Ability / Skill
- Era / Period
- Timeline / Continuity
- Rule / Magic / Game System
- Material / Substance
- Natural Phenomenon
- Language

## 18.3 境界候補

Object Typeとして固定すると過剰設計になりやすく、Class / Concept / Facet / Relation / scalar valueとの比較が必要。

- Role / Occupation / Title
- Generic Item Type
- Attribute / Trait
- Feeling / Emotion
- Motivation / Goal
- State / Condition
- Action / Activity
- Process
- Date / Time Interval
- Release Event metadata
- Term
- Food / Drug category

---

# 19. Class Registry初期登録方針と専用機能優先度

B-02C後の方針では、初期Class Registryの包含範囲と、Class固有機能の実装優先度を分離する。

## 初期Class Registry

B-02Dで正式なObject Classとして採用された候補は、原則として初期Class Registryへ登録する。これは、初期に少数の広いClassへデータが集中し、そのClassが過度に広い意味を持つことを防ぐためである。

例えばArtifact / Product / Species / Race / Ability / Skill / Era / Period / Software / Service / Material / Language / Phenomenon等も、B-02DでObject Classとして採用されたなら「Futureだから未登録」とはせず、通常データ投入前から適切な分類先として利用可能にする。

一方、B-02DでFacet / Relation / scalar value / 対象外と判定された候補はClass Registryへ登録しない。

## 専用機能の実装優先度

当初の`Core` / `High` / `Future`評価は、今後はClass固有Facet、UI、validation、検索最適化等の実装優先度として利用する。

### Core support priority

- Character
- Work
- Concept

### High support priority

- Person
- Organization
- Series
- Place
- Event

### Later specialized support

- Franchise
- Episode / Chapter / Season
- Artifact / Product
- Species / Race
- Ability / Skill
- Era / Period
- Software / Service
- Material / Substance
- Language
- Natural Phenomenon

この優先度が低くても、B-02DでClassとして採用されたものは初期Class Registryから除外しない。共通Object contractだけで正しいClassificationを保持できることを優先する。

---

# 20. B-02Cへ渡した主要論点（完了）

B-02BからB-02Cへ渡した論点は次のとおりであり、Classification modelとしての回答は`OBJECT_TYPE_MODEL.md`で確定済みである。

1. `Agent` のような上位Typeを設け、Character / Person / Organization等をsubtype/classにするか。
2. `CreativeWork` のような上位Typeを設け、Work / Series / Episode等を階層化するか。
3. Place / Event / Artifact / Taxonomic / Concept / Action-Process / Time等を同じ階層のbroad typeとするか。
4. 一つのObjectが複数Classを持てるか。
5. Fictional / RealをClass分離するか、属性・multiple classificationで表現するか。
6. Series / Franchise / Episode / Arcの粒度をどう表現するか。
7. Class registryを固定enumより拡張可能にするか。
8. `instance_of` / `subclass_of`相当概念を導入するか。
9. SoftwareのようにCreativeWork / Product / Systemの複数観点を持つ対象をどう扱うか。
10. Class変更時にも既存`object_id`を維持できる論理契約をどう表現するか。

---

# 21. B-02Dで確定した主要境界論点

以下の論点はB-02Dで確定済みである。詳細判断は`OBJECT_TYPE_BOUNDARIES.md`を参照する。

- Character vs Person
- Organization vs Group vs Faction
- Work vs Series vs Franchise vs Episode / Chapter / Arc
- Place vs Setting / World
- Event object vs Work metadata / Source type
- Named Artifact vs Product vs generic Item Class
- Species / Race vs Class
- Concept vs Theme / Trait / Feeling / Motivation / State
- Ability / Skill vs Character Facet
- Action / Process vs Concept / Relation
- Era / Period vs scalar time value
- System / Mechanic vs Concept
- Dataset / Article / Image / VideoのObject roleとSource role
- Role / Occupation / TitleのClass / Concept / Relation value境界

---

# 22. B-03へ渡すSource候補

Object候補から逆算すると、B-03では少なくとも次のSource / Resource typeを検討する価値がある。

- Official profile / official object page
- Official work / series portal
- Official lore / world guide
- Interview
- Article / editorial
- Encyclopedia / Wiki page
- Book / reference material
- Academic paper
- Dataset / database record
- Product specification / manual
- Documentation / repository / release notes
- Timeline / chronology
- Review / criticism
- Image / artwork
- Video / audio
- Store / distribution listing

ただし、これらをそのままSource Type enumにするか、media typeとdocument genreを分離するかはB-03で決定する。

---

# 23. B-02B結論

B-02Bの結論は次のとおりである。

1. `Character` / `Work` / `Concept` は専用機能のCore優先対象として維持するが、初期Class Registryをこの3 Classへ限定しない。
2. Agent、CreativeWork、Place、Event、Artifact、Taxonomic、Concept/Abstract、Action/Process、Time、System/Software、Substance/Material、Natural Phenomenon、Language等まで検討母集団を拡張した。
3. Object候補は「Web上にTypeがある」ことだけで採用せず、安定Identity、複数Source、参照価値、検索比較価値、Version、Evidenceの6観点で評価する。
4. B-02Dで正式なObject Classとして採用された候補は、当初のCore / High / Future評価にかかわらず、原則として初期Class Registryへ登録する。
5. `Role`, `Trait`, `Feeling`, `Motivation`, `State`, `Action`, `Date`等はObject化すると過剰になりやすく、B-02DでFacet / Relation / Class / valueとの境界を重点確認する。
6. Article / Dataset / Image / Video等はObjectになり得る場合もあるが、Evidence取得元としてのSource roleと明確に分離する。
7. B-02Cでは`Primary Class + Additional Classes + hierarchical Class Registry`方式を採用し、Class Registry包含とClass固有機能の実装優先度を分離した。

**Status: Complete (2026-10-10)**
