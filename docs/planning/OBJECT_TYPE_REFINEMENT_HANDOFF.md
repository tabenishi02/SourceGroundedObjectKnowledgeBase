# SGOKB Object Type Refinement Handoff

更新日: 2026-10-10

- Scope: B-02 Object分類精緻化
- Current next task: `B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する`
- Gate: `B-02D`完了まで`B-03 Source / Evidence要件`の詳細確定へ進まない
- Status:
  - B-02A: Complete
  - B-02B: Complete
  - B-02C: Complete
  - B-02D: Next
- Primary references:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
  - `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

## 1. 本書の目的

本書は、B-02A〜B-02Cで確定したObject分類方針と、B-02Dへ引き継ぐ未決事項を別チャットへ正確に渡すための専用Handoffである。

旧版HandoffはB-02A開始前の状態を前提としていたため、2026-10-10時点の決定へ全面更新した。

---

## 2. 変更してはならないIdentity原則

ObjectはSource / Document / Knowledge Version / file path / project nameから独立した安定Identityである。

`object_id`はClassificationからも独立し、Primary ClassやAdditional Classの訂正・追加だけを理由に変更しない。

同名Objectを許容し、名称一致だけで自動mergeしない。

Object Knowledge VersionとObject registry metadataは別ライフサイクルとして扱う。

---

## 3. B-02Aの決定

Schema.org、DBpedia、Wikidata、WordNet、DCMIを調査し、単一の外部分類体系をそのまま採用しないことを決めた。

利用する主な示唆は次のとおり。

- Schema.org: Web上で独立対象になりやすい主要カテゴリの漏れ防止
- DBpedia: cross-domain class hierarchy
- Wikidata: IdentityとClassの分離、`instance of` / `subclass of`
- WordNet: Concept / State / Process / Feeling等の意味領域
- DCMI: 主にSource / Resource Type設計

Source TypeとObject Classは別責務とする。

---

## 4. B-02Bの決定

SGOKBで扱い得る候補をCharacter / Work / Conceptだけに限定せず、少なくとも次のFamilyまで拡張して評価した。

```text
Agent / Actor
Creative Work / Media
Place / Setting
Event
Artifact / Item / Product
Biological / Taxonomic
Concept / Abstract
Action / Process / Ability
Time / Period
System / Service / Software
Substance / Material
Natural Phenomenon
Language / Term / Symbolic System
```

独立Object化価値は、Identity、複数Source、他Object参照、検索比較価値、Version、独立Evidenceの6観点で判断する。

B-02Bで付与したCore / High / Futureは、B-02C後はClass Registryへの包含時期ではなく、Class固有機能の実装優先度を示す予備評価として扱う。

---

## 5. B-02Cで採用したClassification model

SGOKBは次の方式を採用する。

> Object IdentityとClassificationを分離し、各Objectに1つのPrimary Classを必須で割り当て、0件以上のAdditional Classを許容する。Classはhierarchical Class Registryで管理する。

主要ルール:

1. `Character / Work / Concept / ...`を固定enumへ並べ続けない。
2. Primary Classは必須1件、Additional Classは0件以上。
3. Class hierarchyは複数親を許容するDAGとしcycleを禁止する。
4. Object→Classは`instance_of`相当。
5. Class→Classは`subclass_of`相当。
6. Classification edgeは通常のSemantic Relationと分離する。
7. Class Registry entryを通常のKnowledge Objectとして扱うことは要求しない。
8. broad typeをObjectへ重複保存せず、Class ancestryから導出する。
9. Class変更・追加でも同一意味対象なら`object_id`を維持する。

---

## 6. 2026-10-10追加決定 — 初期Class Registryを広く用意する

Classの初期登録方針を次のように変更した。

> **B-02Dで正式なObject Classとして採用されたClassは、利用頻度や専用機能の完成度にかかわらず、原則として初期Class Registryへ登録する。**

理由は、少数Classだけで運用開始すると、本来別Classへ分類すべきObjectが`Concept`等の広いClassへ集中し、そのClassの意味幅と件数が歴史的に肥大化するためである。

後からClassを追加しても、既存データの再分類コストと分類分布の偏りが残る可能性がある。

したがって次を分離する。

```text
初期Class Registryへの包含
  ≠
Class固有Facet / UI / validation / search等の専用機能実装優先度
```

Character / Work / Conceptは主要ユースケースとして専用機能を優先してよい。一方、Artifact / Taxon / Ability / Era / Software / Material / Language等も、B-02DでClassとして採用されれば初期Registryへ登録する。

この方針は外部Ontologyの全Classを取り込むことを意味しない。対象はSGOKB自身がB-02Dで正式採用したClassに限定する。

---

## 7. Generic Classへのfallback方針

必要Classが未登録であるという実装上の理由だけで、意味的に異なる`Concept` / `Work` / `Character`等へObjectを丸め込まない。

原則:

```text
必要Classを識別
  ↓
Class Registryへ追加 / review / staging
  ↓
正しいClassでObject登録
```

既存上位Classへの一時登録を許すのは、その上位Class自体が対象を正しく表し、後の再分類を前提としなくても意味を損なわない場合に限る。

stagingやpending-classの物理方式はE-01 / E-05で決定する。

---

## 8. B-02Dで決めること

B-02DではB-02Bの全候補を、Object Class / Facet / Relation / value / SGOKB Object対象外へ具体的に配置する。

重点境界:

- Character vs Person
- Organization vs Group / Faction
- Work vs Series / Franchise / Episode / Chapter / Arc
- Place vs Setting / World
- Event Object vs Work metadata / Source Type
- Named Artifact vs Product vs generic Item Class
- Species / Race vs Class
- Concept vs Theme / Trait / Feeling / Motivation / State
- Ability / Skill vs Character Facet
- Action / Process vs Concept / Relation
- Era / Period vs scalar time value
- System / Mechanic vs Concept
- Dataset / Article / Image / VideoのObject roleとSource role
- Role / Occupation / TitleのClass / Concept / Relation value境界

さらに今回の方針変更により、B-02Dは次も必須成果とする。

1. 正式採用したObject Classの一覧。
2. そのうち初期Class Registryへseedする集合。原則は正式採用Classすべて。
3. Registry包含とは別のClass固有機能実装優先度。
4. 既存の広いClassへのfallbackを許す条件 / 禁止する条件。

---

## 9. Phase Eへの影響

E-01ではClass Registry、Class hierarchy、Object-Class membershipを物理schemaへ落とし込む。

通常のObjectデータ投入前に、B-02Dで採用した初期Class集合を決定論的にseedできなければならない。

E-02では、専用Facetが未定義のClassでも共通Object contractで保持できるようにする。

E-05では、Primary / Additional ClassのRegistry存在確認を行い、専用extension未実装を理由に別Classへ自動fallbackさせない。

---

## 10. 現在の進行順

```text
B-02 Object Identity要件              完了
  ↓
B-02A 外部分類体系調査               完了
  ↓
B-02B Object候補整理                  完了
  ↓
B-02C Type / Class hierarchy          完了
  ↓
B-02D Object / Facet / Relation境界   次に実施
  ↓
B-03 Source / Evidence要件
```

---

## 11. B-02Dの成果物

主成果物:

- `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`

必要に応じて更新:

- `docs/requirements/OBJECT_REQUIREMENTS.md`
- `docs/requirements/OBJECT_TYPE_MODEL.md`
- `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
- `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

---

## 12. 次チャットが読む順序

1. `docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md`
2. `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`
3. `docs/requirements/OBJECT_TYPE_MODEL.md`
4. `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
5. `docs/requirements/OBJECT_REQUIREMENTS.md`
6. `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`

---

## 13. 次チャット開始用プロンプト

```text
Source Grounded Object Knowledge Base（SGOKB）のObject分類設計を続けます。

今回実施するタスクは、
B-02D [P0] Object / Facet / Relation / 対象外の境界を確定する
です。

最初に以下を確認し、B-02A〜B-02Cの決定と最新の初期Class Registry方針を把握してください。

- docs/planning/OBJECT_TYPE_REFINEMENT_HANDOFF.md
- docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md
- docs/requirements/OBJECT_TYPE_MODEL.md
- docs/requirements/OBJECT_TYPE_CANDIDATES.md
- docs/requirements/OBJECT_REQUIREMENTS.md
- docs/reference/OBJECT_CLASSIFICATION_SURVEY.md

特に、B-02Dで正式なObject Classとして採用したClassは、利用頻度や専用機能の実装優先度にかかわらず、原則として初期Class Registryへ登録する方針を維持してください。

B-02Bの全候補をObject Class / Facet / Relation / value / 対象外へ分類し、なぜその配置にするか説明してください。

また、次を別々に確定してください。
1. 正式採用Object Class一覧とClass hierarchy。
2. 初期Class RegistryへseedするClass集合。
3. Class固有Facet / UI / validation / search等の実装優先度。
4. 未登録Classが必要な場合のfallback / review / stagingルール。

成果物として `docs/requirements/OBJECT_TYPE_BOUNDARIES.md` を作成し、必要な関連文書を同期してください。
```

---

## 14. 現在地点

- SGOKB Rename: 完了
- 旧Prototype docs整理: 完了
- Phase A: 完了
- B-01: 完了
- B-02 Object Identity: 完了
- B-02A: 完了
- B-02B: 完了
- B-02C: 完了
- 初期Class Registry方針変更: 反映済み
- B-02D: 次に実施
- B-03: Gateにより保留

この状態を次チャットへの開始点とする。
