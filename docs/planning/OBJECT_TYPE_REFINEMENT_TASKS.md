# SGOKB Object Type Refinement Tasks

更新日: 2026-10-09

- Parent: `B-02 [P0] Object要件を定義する`
- Status: Planned
- Gate: 本タスク群を完了するまで `B-03 Source / Evidence要件` の詳細確定へ進まない
- Related:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md`

## 1. 目的

B-02ではObjectを安定Identityとして定義し、初期Object typeとして `Character` / `Work` / `Concept` を置いた。

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

- [ ] Schema.orgの主要上位TypeとSGOKB関連subtypeを抽出する。
- [ ] DBpedia Ontologyの主要cross-domain classを抽出する。
- [ ] Wikidataのinstance/class/subclassモデルを整理する。
- [ ] WordNet noun categoryをSGOKB観点で整理する。
- [ ] Dublin Core等のResource Typeを調査し、Source typeとObject typeを分離する。
- [ ] 共通して現れるカテゴリと、体系固有カテゴリを比較表にする。

### 成果物

`docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`

### 完了条件

- 各体系の目的の違いが説明されている。
- SGOKBへそのまま移植すべきでない分類も明記されている。
- Object候補抽出の根拠として再利用可能な比較表がある。

---

## B-02B [P0] SGOKB Object候補を網羅的に整理する

- [ ] B-02Aを基にObject候補を可能な限り列挙する。
- [ ] 少なくとも以下を検討対象に含める。
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
- [ ] 各候補について想定ユースケースを記述する。
- [ ] 各候補について収集対象となり得るWebページ例を記述する。
- [ ] 「独立Objectにする価値」の判断基準で評価する。

### 成果物

`docs/requirements/OBJECT_TYPE_CANDIDATES.md`

### 完了条件

各候補について最低限、次が整理されている。

- 定義
- 代表例
- 独立Object化の価値
- 関連するSource種別
- 主なRelation候補
- 主なFacet候補
- MVP必要性

---

## B-02C [P0] Object Type / Class階層を設計する

- [ ] broad `object_type` と細分類class/subtypeを分ける必要性を判断する。
- [ ] 上位Type候補を決定する。
- [ ] subtype / class hierarchyを決定する。
- [ ] multiple classificationを許容するか判断する。
- [ ] `instance of` / `subclass of`相当の概念をSGOKBへ導入するか判断する。
- [ ] TypeをDB enumへ固定するか、registry方式等へするかの要件を整理する。
- [ ] 新Type追加時に既存Object IDやSchemaを壊さないことを確認する。

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

- SGOKBの分類方式を一文で説明できる。
- 初期実装対象と将来拡張対象が分離されている。
- Class追加によってObject Identityが変化しない。
- E-01物理schema設計へ入力可能な論理契約になっている。

---

## B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する

- [ ] B-02Bの全候補を次のいずれかへ分類する。
  - 上位Object Type
  - Object subtype / Class
  - Facet
  - Relation
  - SGOKB Object対象外
- [ ] 同じ語が文脈によって複数役割になり得るケースを整理する。
- [ ] Character / Work / Conceptの既存要件を新分類モデルへ再マッピングする。
- [ ] Source typeとの境界をB-03へ引き継ぐ。
- [ ] UPDS Personal Inferenceとの境界をPhase Cへ引き継ぐ。

### 重点例

- Series / FranchiseはWork subtypeか独立上位Typeか。
- FactionはOrganization subtypeか。
- FictionalPlaceとRealPlaceは同一Place class配下か。
- AbilityはObjectかCharacter FacetかRelationか。
- Theme / Motivation / Feeling / StateはConcept classかFacet valueか。
- Species / RaceはObjectかClassそのものか。
- Episode / ChapterはCreativeWork Objectか単なる構造要素か。

### 成果物

- `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
- 必要に応じ `docs/requirements/OBJECT_REQUIREMENTS.md` を改訂

### 完了条件

- 主要候補に「なぜObjectか / なぜObjectでないか」の説明がある。
- Type / Class / Facet / Relationの責務重複が解消されている。
- B-03で収集対象Sourceを設計する際に、対象Objectの種類が十分想定されている。

---

## 5. Task間の依存関係

```text
B-02 Object Identity要件（完了）
  ↓
B-02A 外部分類体系調査
  ↓
B-02B Object候補整理
  ↓
B-02C Type / Class階層設計
  ↓
B-02D Object / Facet / Relation境界
  ↓
B-03 Source / Evidence要件
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
- 初期実装Typeと将来拡張候補を区別できる。
- Object / Class / Facet / Relation / Source typeの境界が説明できる。
- Object typeごとに、どのようなWeb Sourceを収集する可能性があるかを列挙できる。
- B-03 Source / Evidence要件を設計するための入力が揃っている。

以上を満たした後、B-03へ進む。
