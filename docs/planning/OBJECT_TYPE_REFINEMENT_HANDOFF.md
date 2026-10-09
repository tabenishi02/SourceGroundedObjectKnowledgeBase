# SGOKB Object Type Refinement Handoff

更新日: 2026-10-09

- Scope: B-02 Object要件完了後に追加されたObject Type精緻化作業
- Current next task: `B-02A [P0] 外部分類体系を正式調査する`
- Gate: `B-02A`〜`B-02D`完了まで`B-03 Source / Evidence要件`の詳細確定へ進まない
- Primary references:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`

## 1. 本書の目的

本書は、B-02 Object要件の完了後に行ったObject Typeに関する追加議論を、別チャットへ正確に引き継ぐための専用Handoffである。

全体アーキテクチャやPrototype再設計の背景は`KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`を正本とし、本書ではObject分類の議論だけを集中的に扱う。

次チャットでは、本書と`OBJECT_TYPE_REFINEMENT_TASKS.md`を確認したうえで、B-02Aから作業を継続する。

---

## 2. この追加検討が始まった理由

B-02ではObjectをSource / Document / Knowledge Versionから独立した安定Identityとして定義し、初期Object typeとして`Character` / `Work` / `Concept`を置いた。

その後、ユーザーから次の問題提起があった。

> 必要なObject typeを事前に想定することは、今後どのようなWebページを収集するかの検討につながり、要件を細分化・精緻化できる。その結果、設計漏れのリスクを下げられるのではないか。

この観点を採用した。

Object typeは単なるDB分類ではなく、少なくとも次へ影響する。

- 収集すべきWeb Sourceの種類
- Objectごとに必要なSource coverage
- SourceとObjectの関連付け
- Semantic Facetの種類
- Object間Relation
- 検索・比較・類似検索の単位
- Google Drive / ChatGPTへ渡すObject Evidence Package
- MCPで取得するKnowledgeの単位
- 将来のUPDSから参照する対象

したがって、B-03 Source / Evidence要件へ進む前にObject分類の検討範囲を広げることにした。

---

## 3. B-02で既に確定していること

Object Type精緻化によって、B-02で確定したIdentity要件を不用意に崩してはならない。

### 3.1 ObjectのIdentity

Objectは、長期的にKnowledgeを結び付ける安定した意味上のIdentityである。

`object_id`は少なくとも次から独立する。

- name / aliases
- URL
- Source ID
- file / folder path
- Repository / Project名
- Knowledge Version
- AI model / Prompt / Document

### 3.2 Identityと分類は分離する

Objectの分類が後から変更・精緻化されても、意味対象自体が同一なら`object_id`は維持する。

したがって、B-02CでType/Classモデルを変更しても、Object Identityを再発行することを前提にしない。

### 3.3 Versionとの分離

Object IdentityとObject Knowledge Versionは別ライフサイクルを持つ。

Knowledge未生成のObjectも正常状態として許容する。

### 3.4 同名Object

name / aliasはIdentityではなく、同名の別Objectを許容する。名称一致だけで自動mergeしない。

### 3.5 初期3 typeの位置づけ

`Character` / `Work` / `Concept`は、B-02時点の初期分類として採用した。

ただし、その後の議論により、この3種類を最終的な上位`object_type`として固定することは未確定となった。

B-02A〜B-02Dで分類粒度を再検討し、必要なら`OBJECT_REQUIREMENTS.md`を改訂する。

---

## 4. ユーザーが求めている分類検討の方向

ユーザーは、SGOKB独自の思いつきだけでObject typeを決めるのではなく、既存の実用的な分類体系を参考にすることを希望している。

特に次の2種類を検討対象とする。

1. Web上のEntity / Resource分類
2. 言葉・概念・意味の分類

目的は外部分類体系をそのままコピーすることではない。

既存体系で繰り返し現れる基本カテゴリを利用してSGOKBの見落としを減らし、SGOKBの用途に合わせて簡略化・再構成する。

---

## 5. 予備調査で参照した外部分類体系

ここでの内容はB-02Aの正式成果物ではなく、B-02Aを立ち上げる根拠となった予備調査である。

### 5.1 Schema.org

参照観点:

- Web上で記述される`Thing`のtype hierarchy
- Person / Organization / CreativeWork / Event / Place / Product等
- WebPage等のSource側概念と、そのページが説明するEntityを分離する考え方

重要な示唆:

- `WebPage`, `Article`, `ProfilePage`等をObject typeと混同しない。
- 「ページの形式」と「ページが説明する対象」は別の分類軸である。

参考:
- https://schema.org/docs/full.html
- https://schema.org/Thing

### 5.2 DBpedia Ontology

参照観点:

- Wikipedia由来のcross-domain class hierarchy
- Person / Place / Work / Organisation / Species等
- FictionalCharacterのようなdomain-specific class

重要な示唆:

- `Character`, `Person`, `Organization`を完全に無関係な1階層typeとして置く以外に、より上位classを持つ設計を検討できる。

参考:
- https://www.dbpedia.org/resources/ontology/

### 5.3 Wikidata

参照観点:

- EntityそのものとClassを分離するモデル
- `instance of` / `subclass of`
- 大量の具体Classをcore enumへ固定しない考え方

重要な示唆:

- SGOKBでも`object_type`を巨大な固定enumにする必要はない可能性が高い。
- Object Identityとclassification membershipを分離する設計を比較すべき。

参考:
- https://www.wikidata.org/wiki/Help:Data_model
- https://www.wikidata.org/wiki/Help:Basic_membership_properties/en

### 5.4 WordNet

参照観点:

名詞の意味分類として、person / group / location / artifact / event / cognition / attribute / feeling / motive / relation / state / process等を持つ。

重要な示唆:

- `Concept`内部にはTheme / Attribute / Value / Motive / Feeling / State等の異なる意味カテゴリが存在し得る。
- それらすべてを上位Object Typeにするのではなく、Concept subtype/classやFacetとの境界を検討すべき。

参考:
- https://wordnet.princeton.edu/documentation/lexnames5wn

### 5.5 Dublin Core / DCMI Type Vocabulary

参照観点:

- Collection / Dataset / Event / Image / InteractiveResource / Service / Software / Sound / Text等のResource Type

重要な示唆:

- SGOKBでは主にSource / Resource type検討の参考になる。
- Object typeとSource typeは分離すべき。

参考:
- https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#section-7

---

## 6. 予備調査から得た重要な仮説

以下は有力な方向性だが、B-02A〜B-02Dの正式検討前に確定事項として扱わない。

### 6.1 1階層固定enumは避ける方向が有力

次のような単純な1階層列挙は将来肥大化する可能性がある。

```text
Character
Work
Concept
Person
Organization
Place
Event
Artifact
Species
...
```

代わりに、少なくとも次のモデルを比較する。

```text
案A: 現在のobject_typeを拡張する

案B: broad object_type + subtype/class

案C: Objectは単一Identityとし、class membershipを別に持つ
```

採用方式はB-02Cで決定する。

### 6.2 上位カテゴリ候補

予備調査では、次のカテゴリは複数の既存体系に現れ、SGOKBでも検討価値が高いと判断した。

- Agent相当
  - Character
  - Person
  - Organization / Group / Faction
- CreativeWork相当
  - Work
  - Series / Franchise
  - Episode / Chapter
- Place / Setting
- Event
- Artifact / Item / Product
- Concept
- Species / Race

追加検討候補:

- Action / Process / Ability
- Time / Period

これらを最終`object_type`とすることはまだ決めていない。

### 6.3 Objectとする判断基準

独立Object候補について、少なくとも次を評価する。

- 独立したIdentityを持つか
- 複数SourceからKnowledgeを蓄積する価値があるか
- 他Objectから参照されるか
- それ自体を検索・比較したいか
- 独自Versionを持つ価値があるか
- Source / Evidenceを独立して関連付けたいか

複数条件を満たすほど独立Object化の価値が高い。

---

## 7. Object / Facet / Relationを分ける考え方

分類作業では、概念を何でもObject typeへ昇格させない。

例:

```text
「櫻木真乃」
→ Object候補

「Character」
→ Type / Class候補

「性格」
→ Facet候補

「283プロダクションに所属する」
→ Relation候補

「明るい」
→ Knowledge value候補
```

特に判断が必要な境界例:

- Series / FranchiseはWork subtypeか独立上位Typeか
- FactionはOrganization subtypeか
- FictionalPlace / RealPlaceを同じPlace配下にするか
- Abilityは独立ObjectかCharacter FacetかRelationか
- Theme / Motivation / Feeling / StateはConcept classかFacet valueか
- Species / RaceはObjectかClassか
- Episode / ChapterはCreativeWork Objectか構造要素か

これらはB-02Dで最終的に整理する。

---

## 8. Source typeとの分離

今回の議論で重要になった原則の1つが次である。

```text
Source Type
= 何を取得したか / どのような資料か

Object Type / Class
= その資料が何について述べているか
```

例:

```text
Source: Interview Article
  ├─ Person Object
  ├─ Character Object
  └─ Work Object
```

Source type候補:

- WebPage
- Article
- Interview
- Profile
- Wiki / Encyclopedia page
- Dataset
- Image
- Video
- InteractiveResource

この一覧自体はB-03で正式決定する。

B-02AではObject分類とSource分類を混同しないための境界として整理する。

---

## 9. 現在の正式タスク構成

```text
B-02 Object Identity要件            完了
  ↓
B-02A 外部分類体系を正式調査       未着手
  ↓
B-02B SGOKB Object候補整理          未着手
  ↓
B-02C Object Type / Class階層設計   未着手
  ↓
B-02D Object / Facet / Relation境界 未着手
  ↓
B-03 Source / Evidence要件
```

### B-02A 成果物

`docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`

### B-02B 成果物

`docs/requirements/OBJECT_TYPE_CANDIDATES.md`

### B-02C 成果物

`docs/requirements/OBJECT_TYPE_MODEL.md`

### B-02D 成果物

`docs/requirements/OBJECT_TYPE_BOUNDARIES.md`

必要であればB-02Dで`OBJECT_REQUIREMENTS.md`を改訂する。

---

## 10. B-02Aで実施すべきこと

次チャットではB-02Aだけを対象とする。

最低限、次を行う。

1. Schema.orgの主要上位TypeとSGOKB関連subtypeを正式に確認する。
2. DBpedia Ontologyの主要cross-domain classを確認する。
3. WikidataのEntity / Class / instance / subclassモデルを整理する。
4. WordNet noun categoryをSGOKB用途の観点で整理する。
5. Dublin Core等のResource Typeを確認し、Source typeとObject typeの境界を整理する。
6. 各体系の目的の違いを明記する。
7. 各体系に共通して現れるカテゴリを比較表にする。
8. SGOKBへそのまま採用すべきでない分類も記録する。
9. B-02Bで利用できるObject候補抽出ルールを作る。

Web上の現在の公式資料を確認し、一次資料を優先する。

B-02AではSGOKBの最終Object Type一覧を確定しない。最終分類決定はB-02B〜Dで行う。

---

## 11. B-02Aで変更してよい文書

最低限:

- 新規 `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
- `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md` のB-02A状態
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md` のB-02A状態
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md` の現在地点
- 本Handoffの現在地点

必要な場合のみ:

- `docs/requirements/OBJECT_REQUIREMENTS.md`

ただし、B-02Aは調査Taskなので、Object Identity要件を理由なく変更しない。

---

## 12. この時点で決めないこと

次をB-02Aで先回りして確定しない。

- SQL table / column
- UUID / ULID等の`object_id`形式
- Type registryの物理schema
- Facet table schema
- Relation table schema
- JSON Schema
- Search scoring
- Embedding model
- MCP Tool schema
- Source / Evidenceの詳細schema
- Google Drive交換形式

Object分類の論理要件を先に固める。

---

## 13. 次チャットが読む順序

1. `docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md`（本書）
2. `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`
3. `docs/requirements/OBJECT_REQUIREMENTS.md`
4. `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
5. `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

必要に応じて:

- `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
- `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`

---

## 14. 次チャット開始用プロンプト

```text
Source Grounded Object Knowledge Base（SGOKB）のKnowledge Base再設計を続けます。

今回実施するタスクは、
B-02A [P0] 外部分類体系を正式調査する
です。

最初にGitHubリポジトリの以下の文書を確認し、ここまでの決定事項とObject Type精緻化の目的を把握してください。

- docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md
- docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md
- docs/requirements/OBJECT_REQUIREMENTS.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md

B-02で確定したObject Identity要件は維持してください。

Schema.org、DBpedia Ontology、Wikidata、WordNet、Dublin Core / DCMI Type Vocabulary等の現在の公式資料を調査し、それぞれの分類体系の目的、主要分類、階層構造、SGOKBへ応用できる考え方、応用すべきでない部分を整理してください。

特に以下を重視してください。
- Object typeとSource typeを混同しないこと
- 1階層の固定enumを前提にしないこと
- 各体系に共通して現れる基本カテゴリを抽出すること
- Object / Class / Facet / Relationの違いを意識すること
- B-02BのObject候補整理に再利用できる比較表を作ること

成果物として、
docs/reference/OBJECT_CLASSIFICATION_SURVEY.md
を作成してください。

必要な関連ドキュメントの更新、リンク確認、Git反映まで実施してください。
B-02Aでは最終Object Type一覧や物理DB Schemaまでは確定しないでください。
```

---

## 15. 現在地点

- SGOKB Rename: 完了
- 旧Prototype docs整理: 完了
- A-01〜A-03: 完了
- B-01: 完了
- B-02 Object Identity要件: 完了
- Object Type refinement task series: 作成済み
- B-02A: 次に実施
- B-03: Gateにより保留

この状態を次チャットへの開始点とする。
