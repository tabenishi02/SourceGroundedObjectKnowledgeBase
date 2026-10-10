# SGOKB Object Type / Class Model

更新日: 2026-10-10

- Task: `B-02C [P0] Object Type / Class階層を設計する`
- Status: Accepted
- Parent: `B-02 [P0] Object要件を定義する`
- Inputs:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
  - `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
- Next: `B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する`

---

## 1. 目的

本書は、SGOKBでObjectを分類するための論理モデルを定義する。

B-02Aでは外部分類体系を調査し、B-02BではSGOKBが将来扱い得るObject候補を網羅した。本Taskでは、それらを1階層の固定enumへ並べるのではなく、Object Identityを維持したまま将来拡張できるType / Classモデルへ整理する。

本書で決めるのは論理分類契約であり、SQL table / column、具体的なClass ID形式、migration実装、JSON Schemaの物理形式はE-01 / E-05で決定する。

---

## 2. 結論

SGOKBは、次の方式を採用する。

> **Object IdentityとClassificationを分離し、各Objectに1つのPrimary Classを必須で割り当て、必要に応じて複数のAdditional Classを付与する。Classは拡張可能なClass Registryで管理し、Class間は`subclass_of`相当の階層を持つ。**

重要な点は次である。

1. `Character / Work / Concept / Place / Event / ...` をDBの固定enumへ並べ続けない。
2. Objectの`object_id`はClass変更・追加によって変化しない。
3. Objectには必ず1つのPrimary Classを持たせる。
4. 1 Objectに0件以上のAdditional Classを許容する。
5. ClassはClass Registryで管理する。
6. Class hierarchyは単純な1本のtreeではなく、必要に応じて複数親を許容するDAGとする。
7. Object→Classを`instance_of`相当、Class→Classを`subclass_of`相当として明確に区別する。
8. Class Registry entry自体を通常のSGOKB Objectとして扱うことは要求しない。
9. `instance_of` / `subclass_of`は通常のObject Relationとは別のClassification contractとして扱う。
10. broad typeはObjectごとに別列で重複保持せず、Class hierarchyの祖先Classから導出できる設計を基本とする。

---

## 3. 比較した方式

### 3.1 案A — 1階層固定Type

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

#### 利点

- 実装が単純。
- SQL enumや単一文字列で扱いやすい。
- MVPだけを見ると理解しやすい。

#### 問題

- Type追加のたびに1階層が肥大化する。
- Character / Person / Organizationのような共通上位概念を表しにくい。
- Series / Episode / Software等の複数観点を表現しにくい。
- Classの再整理が物理schema変更へ直結しやすい。

**結論: 不採用。**

---

### 3.2 案B — broad Object Type + 単一subtype

```text
Agent
├─ Character
├─ Person
└─ Organization

CreativeWork
├─ Work
├─ Series
└─ Episode
```

#### 利点

- 案Aより整理される。
- broad type単位でFacetや検索をまとめやすい。
- 人間に理解しやすい。

#### 問題

- Objectが必ず1つの枝だけに所属する前提になりやすい。
- Softwareのように`System`でも`CreativeWork`でもあり得る対象に弱い。
- Fictional / Real、Product / Artifact等の横断分類を追加すると再び例外が増える。
- broad typeを別フィールドへ固定するとClass hierarchyと情報が重複する。

**結論: 単独では不採用。上位Class階層という考え方のみ採用する。**

---

### 3.3 案C — 完全なClass Membership Graph

```text
Object
  ├─ instance_of → Class A
  ├─ instance_of → Class B
  └─ instance_of → Class C

Class A
  └─ subclass_of → Class D
```

#### 利点

- 最も柔軟。
- multiple classificationを自然に扱える。
- Wikidata型の拡張性を持てる。

#### 問題

- どのClassをUI、Facet、validation、標準表示の基準にするか曖昧になる。
- MVPとしては自由度が高すぎる。
- Classification Graph全体の推論機構を必要とすると過剰設計になる。

**結論: そのままは不採用。ただしClass Registry、multiple classification、`instance_of` / `subclass_of`の分離を採用する。**

---

### 3.4 採用案 — Primary Class + Additional Classes + Class Registry

案Bと案Cの利点を組み合わせる。

```text
Object
├─ object_id              # Identity。Classificationから独立
├─ primary_class          # 必須・1件
└─ additional_classes     # 任意・0件以上

Class Registry
├─ Class
│  ├─ parent Class 0..N
│  └─ subclass_of
└─ ...
```

Primary ClassによりMVPの決定性を維持し、Additional Classにより複数観点を表現する。

---

## 4. Object Classification Contract

### 4.1 Primary Class

すべてのObjectは、必ず1つのPrimary Classを持つ。

Primary Classは次の用途で利用する。

- Objectの主要な意味分類
- UIでの既定表示分類
- type/class別Facet適用の第一候補
- Validationの第一候補
- Evidence Package / Object Resultでの主要分類
- 検索filterの既定分類

例:

```text
Object: 櫻木真乃
primary_class = Character
```

```text
Object: ある作品タイトル
primary_class = Work
```

```text
Object: 自己犠牲
primary_class = Concept
```

Primary ClassはObject Identityではない。分類訂正によって変更されても`object_id`を変更しない。

---

### 4.2 Additional Classes

Objectは0件以上のAdditional Classを持てる。

Additional Classは、Primary Classだけでは表現できない重要な分類観点を付与するために使う。

例:

```text
Object: Software X
primary_class = Software
additional_classes = [CreativeWork]
```

あるいは将来、fictional / artificial / product等のClassを追加した場合に複数Classで表現できる。

ただし、何でもAdditional Classとして付与することは避ける。Role、状態、属性値、Relationで表現すべき情報をClassへ混在させない。具体的境界はB-02Dで確定する。

---

### 4.3 broad typeをObjectへ重複保持しない

SGOKBでは、原則として次のような重複情報をObjectへ別々に保持しない。

```text
object_type = Agent
object_class = Character
```

CharacterがAgentのsubclassであるなら、AgentはClass hierarchyから導出できる。

```text
Character
  subclass_of → Agent
```

したがって論理モデルでは、broad typeを独立必須fieldとして追加しない。

必要な検索・Facet適用ではAncestor Classを利用する。

---

## 5. Class Registry

### 5.1 Registryを採用する

利用可能ClassをDBの閉じたenumや無制限自由文字列にはしない。

Classは**Class Registry**で管理する。

論理的に最低限、Class Registryは次を表現できることを要求する。

| 概念 | 意味 |
|---|---|
| `class_id` | Classを安定して参照する識別子 |
| `name` | 人間向けClass名 |
| `description` | Classの意味・適用条件 |
| `parent_classes` | 0件以上の上位Class参照 |
| `assignable` | Objectへ直接割当可能か |
| `status` | active / archived等のClass lifecycle |

具体的column名・ID形式はE-01で決定する。

Classの名称変更や階層変更によって`class_id`を再利用・変更しない設計を基本とする。

---

### 5.2 Class Registry entryは通常Objectではない

Class Registryの`Character`や`CreativeWork`を、それだけを理由にSGOKB Objectとして登録しない。

```text
Object Registry
  櫻木真乃
  Fate/stay night
  自己犠牲

Class Registry
  Character
  Work
  Concept
  Agent
  CreativeWork
```

Class自体について独立したKnowledgeを蓄積したい場合は、必要に応じ別のConcept Object等を作成できるが、Classification上のClassとKnowledge Objectを同一Identityとして強制しない。

これによりOntology管理と一般Knowledge管理を分離する。

---

## 6. Class Hierarchy

### 6.1 hierarchyはDAGとする

Class hierarchyは単純な1本のtreeへ限定せず、必要に応じて複数の親Classを許容する。

```text
Software
├─ subclass_of → System
└─ subclass_of → CreativeWork   # 必要と判断した場合
```

ただし、循環は許可しない。

```text
A subclass_of B
B subclass_of A
```

のようなcycleは無効とする。

完全なRDF/OWL推論機構は初期要件としない。最低限必要なのはClass ancestryを追跡できること、Ancestor Classによる検索・validation・Facet適用が可能であることである。

---

### 6.2 Initial Registry Scaffold

B-02Bの候補Familyを基に、Class Registryが少なくとも次の上位領域を表現可能な構造とする。

```text
ObjectClass  # 概念上のroot。Objectへ直接割当しない
├─ Agent
│  ├─ Character
│  ├─ Person
│  └─ Organization
├─ CreativeWork
│  └─ Work
├─ Place
├─ Event
├─ Artifact
├─ Taxon
├─ Concept
├─ Process           # Object/Class境界はB-02Dで確定
├─ TemporalEntity
├─ System
├─ Material
├─ Phenomenon        # Object/Class境界はB-02Dで確定
└─ Language
```

このScaffoldは実装優先順位ではなく、「初期Class Registryで分類可能にすべき領域」の候補を示す。B-02Dで正式なObject Classとして採用されたClassは、利用頻度や専用機能の完成度にかかわらず、原則として初期Class Registryへ登録する。

次の候補の具体的配置はB-02Dで確定する。

- Group / Team / Faction
- Series / Franchise / Episode / Chapter / Arc
- FictionalPlace / Setting / World
- Named Artifact / Product / generic Item
- Species / Race
- Theme / Trait / Feeling / Motivation / State
- Ability / Skill / Action / Process
- Era / Period / Timeline / Continuity
- Software / Service / Rule System
- Natural Phenomenon
- Term / Writing System

B-02Cでは、これらを無理に固定するよりも、B-02DでObject / Class / Facet / Relation境界を確認してから配置する。

---

## 7. `instance_of` / `subclass_of`相当概念

### 7.1 `instance_of`

ObjectがClassに属することを表すClassification edgeである。

```text
櫻木真乃
  instance_of → Character
```

Primary ClassもAdditional Classも論理的にはObject→Class membershipである。

ただし、SGOKB内部で`instance_of`というRelation Typeを通常Relation tableへ保存することを要求しない。物理表現はE-01で決定する。

---

### 7.2 `subclass_of`

Class間の一般化・特殊化を表す。

```text
Character
  subclass_of → Agent
```

```text
Person
  subclass_of → Agent
```

`subclass_of`はClass Registry内部のClassification relationであり、通常のObject Relationと分離する。

---

### 7.3 ClassificationとSemantic Relationを混同しない

次を区別する。

```text
櫻木真乃 instance_of Character
```

と、

```text
櫻木真乃 member_of 283プロダクション
```

は責務が異なる。

前者はClassification、後者はObject Knowledge上のSemantic Relationである。

この分離によりClass hierarchyを変更しても、作品世界・現実世界のRelation graphへ不要な影響を与えない。

---

## 8. Multiple Classification

### 8.1 許容する

SGOKBではmultiple classificationを許容する。

理由は、B-02Bで次のような対象が単一分類だけでは不自然になる可能性が確認されたためである。

- Software: System / CreativeWork / Productの観点を持ち得る。
- Fictional organization: Organizationでありfictionalという横断分類を持ち得る。
- Character: Characterに加えてArtificialIntelligence等のClassを持ち得る。
- Named artifact: Artifactであると同時にProductやWeapon等のClassを持ち得る。

ただし、Primary Classは常に1つに限定し、Additional Classは補助分類として扱う。

---

### 8.2 Class inheritanceと直接membershipを区別する

Objectに祖先Classをすべて直接保存する必要はない。

```text
Object X
  primary_class = Character

Character
  subclass_of = Agent
```

であれば、Object XがAgentとして検索可能であることはhierarchyから導出できる。

`Character`と`Agent`を両方直接membershipとして保存することを要求しない。

これにより重複分類の不整合を減らす。

---

## 9. Initial Registry Coverage / Specialized Support

### 9.1 初期Class Registryは採用Classを原則すべて含む

B-02Dで正式なObject Classとして採用されたClassは、原則として通常のObjectデータを蓄積し始める前にClass Registryへ登録し、Primary ClassまたはAdditional Classとして利用可能にする。

この方針の目的は、Class未実装を理由として初期Objectを少数の広いClassへ集中させないことである。

例えば、本来`Ability`として分類すべき対象を、`Ability` Classが未登録であるという理由だけで一時的に`Concept`へ蓄積すると、次の問題が生じる。

- `Concept`が「抽象概念」以外の意味まで持つcatch-all Classになる。
- 後から`Ability`を追加しても既存Objectの再分類が必要になる。
- 初期Classだけが大量のObjectを持ち、後発Classが狭い意味幅と少数データに偏る。
- 検索、Facet、統計、Embedding評価に歴史的な分類偏りが残る。

したがって、**既に設計上認識しておりB-02Dで採用したClassを、利用頻度が低いという理由だけでFuture ClassとしてRegistry登録から除外しない。**

ただし、Schema.orgやWikidata等の外部Classを無制限に取り込むことは意味しない。初期Registry対象は、SGOKBの用途に照らしてB-02Dで正式採用したClassに限定する。

---

### 9.2 Class Registry包含と専用機能の実装優先度を分離する

Classが初期Registryに存在することと、そのClass専用のFacet、UI、検索、validation、renderer等が初期段階で完成していることは別要件とする。

初期の専用機能は、具体的な利用実績がある次のClassを優先してよい。

- `Character`
- `Work`
- `Concept`

次いでPerson / Organization / Series / Place / Event等の専用機能を優先することもできる。

一方、B-02Dで採用されたArtifact / Product / Taxon / Ability / Era / Software / Material / Phenomenon / Language等は、専用Facetが未整備でも共通Object contractを利用して正しいClassで登録できなければならない。

したがって、以後の文書で`Core` / `High` / `Future`等を使用する場合、それは**専用機能の実装優先度**を意味し、Class Registryへの包含可否を意味しない。

---

### 9.3 Generic Classへの暫定丸め込みを避ける

必要なClassがClass Registryに存在しない場合、実装都合だけを理由に意味的に異なる`Concept` / `Work` / `Character`等へ自動的に丸め込んではならない。

新しいClassが必要であることが判明した場合は、原則として次の順序を取る。

```text
必要Classを識別
  ↓
Class Registryへの追加または設計レビュー
  ↓
正しいClassでObject登録
```

既存の上位Classへ一時的に登録できるのは、その上位Class自体が対象の意味分類として正しく、後の再分類を前提としなくても意味を損なわない場合に限る。

物理的なstaging / pending-class状態を用意するかはE-01 / E-05で決定する。

---

### 9.4 稼働後のClass追加は引き続き許容する

初期Registryを広く用意しても、将来未知の領域や新しい要件が発生するためClass追加自体は禁止しない。

新Class追加時も、既存Object ID、Relation、Knowledge Version、Evidence Linkを変更する理由にはならない。必要な場合のみ既存Objectを明示的に再分類し、その変更を監査可能にする。

---

## 10. Validation Requirements

論理上、最低限次をValidation可能とする。

1. Primary Classは必須である。
2. Primary ClassはClass Registryに存在する。
3. Primary Classはactiveかつassignableである。
4. Additional Classは0件以上である。
5. Additional ClassはClass Registryに存在する。
6. 同一ClassをPrimary / Additionalへ重複登録しない。
7. Class hierarchyにcycleを作らない。
8. archived Classを新規Objectへ割り当てない。
9. ObjectのClass変更で`object_id`を変更しない。
10. Class追加時に既存Objectの再採番を要求しない。
11. B-02Dで初期Registry対象として採用されたClassが、本番Object投入前に登録済みであることを検証できる。
12. 専用FacetやUIが未実装であることを理由に、そのClassを別の汎用Classへ自動変換しない。
13. Class固有extensionが未実装でも、共通Object contractだけで正しいClass membershipを保持できる。

具体的なJSON validation / DB constraintはE-01 / E-05で決定する。

---

## 11. Classification変更とVersion

ClassificationはObject Identityに属するregistry metadataとして扱い、Object Knowledge Versionそのものとは分離する。

例:

```text
誤分類:
primary_class = Work

訂正:
primary_class = Series
```

意味対象そのものが同一なら`object_id`を維持する。

Class変更履歴をどの粒度で監査するか、Knowledge Versionと同時変更された場合のtransaction境界はE-01 / E-04で決定する。

ただし、Class変更に伴って適用Facetが変化する場合、必要に応じてObject Knowledgeの再生成対象とすることは許容する。

---

## 12. `object_type`という名称の扱い

既存`OBJECT_REQUIREMENTS.md`では`object_type`を共通Object contractとして定義していた。

B-02C以降、論理的には次の意味へ精緻化する。

```text
旧:
object_type = Character / Work / Concept / ... の1階層分類

新:
primary_class = Class Registry上の主要Class
additional_classes = 0..N Class Registry membership
```

したがって、**`object_type`を独立したbroad type fieldとして新たに維持することは要求しない。**

既存実装との移行互換が必要な場合、一時的に`object_type`をPrimary Class keyの互換表現として扱うことは許容する。ただし、現行要件上の正本概念は`primary_class` / `additional_classes` / Class Registryとする。

物理column名をそのまま`object_type`から変更するかはE-01で決定する。

---

## 13. E-01への論理契約

物理schema設計では、少なくとも次を表現できなければならない。

```text
Object
  stable object_id
  primary Class reference
  zero-or-more Additional Class references

Class Registry
  stable class identity
  human-readable metadata
  assignable flag
  lifecycle status
  zero-or-more parent Class references
```

また、次を満たす必要がある。

- Class追加でObject table schemaの列追加を要求しない。
- Class hierarchy変更でObject IDを変更しない。
- multiple classificationを表現できる。
- ancestor classを検索可能にする。
- Class registryとObject registryを別責務として扱える。
- Source Type registryとは別に管理できる。
- B-02Dで採用した初期Class集合を、通常のObjectデータ投入前に決定論的にseedできる。
- Classごとの専用Facet / UI / extensionの実装有無と、Class Registryへの登録有無を独立して管理できる。
- 未登録Classが必要になった際、意味的に不正確な汎用Classへ自動fallbackせず、追加・review・stagingのいずれかへ誘導できる。

---

## 14. B-02Dへ渡す論点

B-02Dでは、本モデルを前提として各候補を具体的に配置する。

特に次を判断する。

1. Group / Team / FactionをOrganization系Classへ置くか。
2. Series / Franchise / Episode / Chapter / ArcをCreativeWork系Classとしてどう配置するか。
3. FictionalPlace / Setting / WorldをPlace系へ統合するか。
4. Product / generic Item / Named ArtifactをArtifact系へどう分離するか。
5. Species / RaceをTaxon Classとして扱うか、Classそのものとして扱うか。
6. Theme / Trait / Feeling / Motivation / StateをConcept Class、Facet、valueのどこへ置くか。
7. Ability / Skill / Action / ProcessをProcess系Objectにする条件をどう定めるか。
8. Era / Period / Timeline / ContinuityをTemporalEntityへ置く条件をどう定めるか。
9. Software / Service / Rule SystemのPrimary ClassとAdditional Classの使い方。
10. Source TypeとObject Classが同名になる場合の境界。
11. 正式なObject Classとして採用したClassを、初期Class Registry対象として一覧化する。
12. Class Registryへの包含とは別に、Class固有Facet / UI / validation / search等の専用機能実装優先度を整理する。
13. 既存の広いClassへ一時的にfallback可能な条件と、意味的な丸め込みとして禁止する条件を明示する。

---

## 15. 非採用事項

B-02Cでは次を採用しない。

- Object Typeの1階層固定enum。
- Objectごとの必須broad type列 + subtype列の二重管理。
- Class名を自由文字列だけで運用する方式。
- Class自体をすべて通常Objectとして登録する方式。
- `instance_of` / `subclass_of`を通常Semantic Relationと完全同一扱いする方式。
- すべての祖先ClassをObjectへ重複保存する方式。
- RDF / OWL相当の完全Ontology reasonerをMVP必須とすること。

---

## 16. 完了条件への対応

### SGOKBの分類方式を一文で説明できる

> SGOKBは、Object IdentityからClassificationを分離し、1つのPrimary Classと0件以上のAdditional ClassをClass Registryから割り当て、Class間の階層を`subclass_of`相当で管理する。

### 初期Registry対象と専用機能優先度が分離されている

- B-02Dで正式採用したObject Classは、原則として初期Class Registryへ登録する。
- Character / Work / Concept等は専用機能の実装優先度を高くできるが、他ClassをRegistryから除外する根拠にはしない。
- 将来新しく発見されたClassは追加可能とするが、既知Classを意図的に後回しにして汎用Classへ集中させない。

### Class追加によってObject Identityが変化しない

Classは`object_id`の構成要素としない。Class変更・追加でも同一意味対象なら同じ`object_id`を維持する。

### E-01へ入力可能な論理契約になっている

Primary Class、Additional Class、Class Registry、Class hierarchy、validation要件を論理契約として定義した。

---

## 17. 結論

B-02Cでは、SGOKBのObject分類を単純な`object_type` enumから、**Primary Class + Additional Classes + hierarchical Class Registry**へ精緻化する。

これにより、Character / Work / Conceptを主要ユースケースとして優先的に機能強化しつつ、B-02Dで正式採用したClassは初期Registryへ広く登録し、データ蓄積開始時点から適切な意味分類を使用できる。

また、multiple classificationを許容しつつPrimary Classを必須とすることで柔軟性と決定性を両立し、Class固有機能の実装優先度とClass Registryの包含範囲を分離する。これにより、初期の少数Classへデータと意味が過度に集中することを防ぐ。

**Status: Complete (2026-10-10)**
