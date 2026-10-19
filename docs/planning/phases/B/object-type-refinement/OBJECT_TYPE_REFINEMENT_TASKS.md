# SGOKB Object Type Refinement Tasks

更新日: 2026-10-10

- Parent: `B-02 [P0] Object要件を定義する`
- Status: Complete (2026-10-10)
- Gate: Complete — B-03へ進行可能
- Related:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
  - `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md`

## 1. 目的

B-02当初はObjectを安定Identityとして定義し、暫定的な初期分類として `Character` / `Work` / `Concept` を置いた。その後B-02C / B-02DでClass Registry方式へ精緻化した。

しかし、SGOKBが将来どのようなWeb資料を収集し、どの対象をKnowledgeとして独立管理するかを精緻化するには、Object type候補をより広く検討する必要がある。

本タスク群では、既存のWeb schema・Knowledge Graph・語彙分類を参照しながら、SGOKBで扱う対象を網羅的に洗い出し、次を明確化する。

1. 何を独立Objectとして管理するか。
2. 何をObject subtype / classとして扱うか。
3. 何をFacetとして扱うか。
4. 何をRelationとして扱うか。
5. 何をSGOKBのObject対象外とするか。
6. Object分類から逆算して、今後どのようなWeb Sourceを収集すべきか。

目的はObject typeを無制限に増やすことではなく、**将来必要になる対象を想定し、設計漏れを早期に発見すること**である。

---

## 2. 外部分類体系を参照する理由

独自分類だけで設計すると、分野固有の思い込みによって主要カテゴリを見落とす可能性がある。

そのため、少なくとも次の既存体系を参照する。

### Schema.org

Web上で記述される `Thing` を階層的なTypeとして扱う。CreativeWork / Event / Organization / Person / Place / Product等、Webで頻繁に記述される対象分類を確認する。

- https://schema.org/docs/full.html
- https://schema.org/Thing

### DBpedia Ontology

Wikipedia Infobox由来のcross-domain ontology。Person / Place / Work / Organisation / Species等の大分類とsubsumption hierarchyを参考にする。

- https://www.dbpedia.org/resources/ontology/

### Wikidata

固定された少数Typeだけに閉じず、`instance of` / `subclass of` を用いてEntityとClassを分離する考え方を参考にする。

- https://www.wikidata.org/wiki/Help:Data_model
- https://www.wikidata.org/wiki/Help:Basic_membership_properties/en

### WordNet

語の意味領域として person / group / location / artifact / event / cognition / attribute / feeling / motive / relation / state / process等を持つ。特にConcept内部の意味分類を考える参考とする。

- https://wordnet.princeton.edu/documentation/lexnames5wn

### Dublin Core / DCMI Type Vocabulary

Collection / Dataset / Event / Image / InteractiveResource / Service / Software / Sound / Text等のResource Typeを持つ。SGOKBでは主にObject typeではなくSource / Resource typeとの境界確認に用いる。

- https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#section-7

---

## 3. 基本方針

### 3.1 1階層の固定enumにしない

`Character / Work / Concept / Place / Event / ...` を無制限に1階層へ追加する設計は避ける。

候補として、次の二段階以上の分類を検討する。

```text
Object
├─ broad object_type
└─ object_class / subtype
```

例:

```text
Agent
├─ Character
├─ Person
└─ Organization

CreativeWork
├─ Work
├─ Series
├─ Episode
└─ Chapter
```

ただし、この階層をそのまま採用することは本タスク開始時点では確定しない。

### 3.2 Object / Class / Facet / Relationを混同しない

例:

- 「櫻木真乃」→ Object候補
- 「Character」→ Class / Type候補
- 「性格」→ Facet候補
- 「283プロダクションに所属する」→ Relation候補
- 「明るい」→ Knowledge value候補

分類語そのものをすべてObject typeへしない。

### 3.3 Source typeとObject typeを分離する

WebPage / Article / Interview / Dataset / Image等は「何を取得したか」を表すSource type候補であり、「何についてのKnowledgeか」を示すObject typeとは別に扱う。

```text
Source: Interview Article
  ├─ Person Object
  ├─ Character Object
  └─ Work Object
```

この境界はB-03 Source / Evidence要件へ引き継ぐ。

### 3.4 独立Objectとする判断基準

候補項目について、少なくとも次を評価する。

- 独立したIdentityを持つか。
- 複数SourceからKnowledgeを蓄積する価値があるか。
- 他Objectから参照されるか。
- それ自体を検索・比較したいか。
- 独自のVersionを持つ価値があるか。
- Source / Evidenceを独立して関連付けたいか。

複数を満たすほど独立Objectとして扱う価値が高い。

---

# 4. Task一覧

## B-02A [P0] 外部分類体系を正式調査する

- [x] Schema.orgの主要上位TypeとSGOKB関連subtypeを抽出する。
- [x] DBpedia Ontologyの主要cross-domain classを抽出する。
- [x] Wikidataのinstance/class/subclassモデルを整理する。
- [x] WordNet noun categoryをSGOKB観点で整理する。
- [x] Dublin Core等のResource Typeを調査し、Source typeとObject typeを分離する。
- [x] 共通して現れるカテゴリと、体系固有カテゴリを比較表にする。

### 成果物

`docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`

### 完了条件

- [x] 各体系の目的の違いが説明されている。
- [x] SGOKBへそのまま移植すべきでない分類も明記されている。
- [x] Object候補抽出の根拠として再利用可能な比較表がある。

### 結果概要

- 単一の外部分類体系をSGOKBへそのまま採用しない。
- Schema.orgは主要Web対象カテゴリ、DBpediaはcross-domain class、WikidataはIdentityとClassの分離、WordNetはConcept意味領域、DCMIはSource / Resource Type設計の参考として利用する。
- B-02Bへ、Agent / CreativeWork / Place / Event / Artifact / Taxonomic / Concept / Action-Process / Time-Period系の候補母集団を引き継ぐ。
- Source TypeとObject Typeは独立設計する。

**Status: Complete (2026-10-10)**

---

## B-02B [P0] SGOKB Object候補を網羅的に整理する

- [x] B-02Aを基にObject候補を可能な限り列挙する。
- [x] 少なくとも以下を検討対象に含める。
  - Character
  - Person
  - Organization / Group / Faction
  - Work / CreativeWork
  - Series / Franchise
  - Episode / Chapter
  - Place / Setting
  - Event
  - Artifact / Item / Product
  - Species / Race
  - Concept
  - Action / Process / Ability
  - Time / Period
- [x] 各候補について想定ユースケースを記述する。
- [x] 各候補について収集対象となり得るWebページ例を記述する。
- [x] 「独立Objectにする価値」の判断基準で評価する。

### 成果物

`docs/requirements/OBJECT_TYPE_CANDIDATES.md`

### 完了条件

各候補について最低限、次が整理されている。

- [x] 定義
- [x] 代表例
- [x] 独立Object化の価値
- [x] 関連するSource種別
- [x] 主なRelation候補
- [x] 主なFacet候補
- [x] 実装優先度（後にClass Registry包含とは分離）

### 結果概要

- Candidate Familyを Agent / CreativeWork / Place / Event / Artifact / Taxonomic / Concept-Abstract / Action-Process / Time に加え、System-Software / Substance-Material / Natural Phenomenon / Languageまで拡張した。
- 各候補を、安定Identity・複数Source・他Object参照・検索比較価値・Version・独立Evidenceの6観点で評価した。
- `Character` / `Work` / `Concept` はClass固有機能のCore優先候補、`Person` / `Organization` / `Series` / `Place` / `Event` はHigh優先候補として評価した。
- B-02C後、Core / High / FutureはClass Registryへの包含時期ではなく、Class固有機能の実装優先度として扱う。B-02Dで正式Classとして採用されたものは原則として初期Registry対象とする。
- Role / Trait / Feeling / Motivation / State / Action / Date等はObject化すると過剰になりやすく、B-02DでClass / Facet / Relation / valueとの境界を重点判断する。
- Article / Dataset / Image / Video等はObject roleとSource roleを分離して扱う。

**Status: Complete (2026-10-10)**

---

## B-02C [P0] Object Type / Class階層を設計する

- [x] broad `object_type` と細分類class/subtypeを分ける必要性を判断する。
- [x] 上位Type候補を決定する。
- [x] subtype / class hierarchyを決定する。
- [x] multiple classificationを許容するか判断する。
- [x] `instance of` / `subclass of`相当の概念をSGOKBへ導入するか判断する。
- [x] TypeをDB enumへ固定するか、registry方式等へするかの要件を整理する。
- [x] 新Class追加時に既存Object IDやSchemaを壊さないことを確認する。

### 重要論点

候補として、例えば次のような上位構造を比較する。

```text
案A: 現行型を拡張
Character / Work / Concept / Place / Event / ...

案B: 上位Type + subtype
Agent / CreativeWork / Place / Event / Artifact / Concept / ...
  ↓
Character / Person / Organization / Work / Series / ...

案C: Objectは単一でclass membershipをRelation的に持つ
Object
  └─ instance_of → Class Object / Class Registry
```

### 成果物

`docs/requirements/OBJECT_TYPE_MODEL.md`

### 完了条件

- [x] SGOKBの分類方式を一文で説明できる。
- [x] 初期Class Registryの包含範囲と、Class固有機能の実装優先度が分離されている。
- [x] Class追加によってObject Identityが変化しない。
- [x] E-01物理schema設計へ入力可能な論理契約になっている。

### 結果概要

- 1階層固定enum、単純なbroad type + subtype、完全自由Class Graphを比較した。
- `Primary Class + Additional Classes + hierarchical Class Registry`方式を採用した。
- Primary Classを1件必須、Additional Classを0件以上としmultiple classificationを許容する。
- broad typeは別必須fieldとして重複保持せず、Class hierarchyの祖先から導出する。
- Object→Classを`instance_of`相当、Class→Classを`subclass_of`相当として通常のSemantic Relationと分離する。
- Class hierarchyは複数親を許容するDAGとしcycleを禁止する。
- Class Registry entry自体を通常Objectとして扱うことは要求しない。
- 既存`object_type`概念は現行要件上`primary_class` / `additional_classes`へ精緻化した。
- B-02Dで正式なObject Classとして採用したClassは、原則として初期Class Registryへすべて登録する方針とした。
- `Character` / `Work` / `Concept`等の優先度はClass固有Facet / UI / validation等の専用機能実装優先度として扱い、Registry包含とは分離した。
- Class未登録を理由に`Concept`等の汎用Classへ意味的に不正確なfallbackを行わない方針とした。

**Status: Complete (2026-10-10)**

---

## B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する

- [x] B-02Bの全候補をObject Class / Facet / Relation / value / Source側 / 対象外へ分類する。
- [x] 同じ語が文脈によって複数役割になり得るケースを整理する。
- [x] Character / Work / Conceptの既存要件を新分類モデルへ再マッピングする。
- [x] Object Classとして正式採用した候補を初期Class Registry seed集合として確定する。
- [x] Class Registryへの包含とは別に、Class固有Facet / UI / validation / search等の専用機能実装優先度を記録する。
- [x] 未登録Classが必要になった場合のfallback / review / staging境界を定義する。
- [x] Source typeとの境界をB-03へ引き継ぐ。
- [x] UPDS Personal Inferenceとの境界をPhase Cへ引き継ぐ。

### 主な決定

- Agent配下にCharacter / Person / Organization / Group / Creatureを置き、Team / FactionをGroup配下へ配置した。OrganizationとGroupは兄弟Classとする。
- CreativeWork配下にWork / Series / Franchise / WorkComponent系を配置し、SeriesをWork属性として扱わない。
- Fictional / RealはPrimary Class二重体系にせず、横断`FictionalEntity`分類を利用する。
- Taxon / Species / FictionalRaceはKnowledge Objectとして扱い、Class Registryの`subclass_of`とtaxonomic relationを分離する。
- Theme / Trait / Emotion / Motivation / Role等はConcept系Objectとして独立管理できる一方、Object固有記述ではFacet valueとしても利用できる。
- named Ability / SkillはObject + Relation、単純な能力説明はFacetで保持できる。
- Date / Time Interval、通常のrelease date等はscalar metadataとする。
- Settingは原則Work Facet、独立した世界はWorld / Place Objectとする。
- Termは原則name / alias / lexical metadataとし、専用Term Classは初期採用しない。
- Food / Drug専用Class、ReleaseEvent専用Classは初期採用しない。

### 成果物

- `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
- `docs/requirements/OBJECT_REQUIREMENTS.md` 同期更新
- `docs/requirements/OBJECT_TYPE_MODEL.md` 同期更新

### 完了条件

- [x] 主要候補に「なぜObjectか / なぜObjectでないか」の説明がある。
- [x] Type / Class / Facet / Relationの責務重複が解消されている。
- [x] 初期Class RegistryへseedするClass集合が確定している。
- [x] Class Registry包含とClass固有機能の実装優先度が明確に分離されている。
- [x] B-03で収集対象Sourceを設計するためのClass familyとSource候補が整理されている。

**Status: Complete (2026-10-10)**

---

## 5. Task間の依存関係

```text
B-02 Object Identity要件（完了）
  ↓
B-02A 外部分類体系調査（完了）
  ↓
B-02B Object候補整理（完了）
  ↓
B-02C Type / Class階層設計（完了）
  ↓
B-02D Object / Facet / Relation境界（完了）
  ↓
B-03 Source / Evidence要件（次）
```

原則として順番に実施する。

B-02CとB-02DでB-02本体の前提を変更する必要が生じた場合は、`OBJECT_REQUIREMENTS.md`を改訂し、変更理由を記録する。

---

## 6. 本タスク群で決めないこと

次はObject分類の結果に影響されるが、このタスク群では物理実装まで確定しない。

- SQL table / column
- `object_id`形式
- Facetの物理schema
- Relation table schema
- JSON Schema詳細
- Search scoring
- Embedding model
- MCP Tool schema
- Source / Evidence schema詳細

これらはPhase E以降または各対応Taskで決定する。

---

## 7. 全体完了条件

B-02A〜B-02Dを完了した時点で、次を満たすこと。

- SGOKBが扱い得る主要対象カテゴリを、既存分類体系を根拠に説明できる。
- Object分類が1階層固定enumへ過度に依存していない。
- B-02Dで正式採用したObject Classを初期Registryへ原則すべて登録する方針と、Class固有機能の実装優先度を区別できる。
- Object / Class / Facet / Relation / Source typeの境界が説明できる。
- Object Class / 対象カテゴリごとに、どのようなWeb Sourceを収集する可能性があるかを列挙できる。
- B-03 Source / Evidence要件を設計するための入力が揃っている。

以上を満たしたため、Object Type Refinement task seriesは完了とし、B-03へ進む。