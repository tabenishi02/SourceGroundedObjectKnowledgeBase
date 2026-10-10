# SGOKB Object Type Refinement Handoff

更新日: 2026-10-10

- Scope: B-02 Object分類精緻化
- Status: Complete
- Completed: B-02A / B-02B / B-02C / B-02D
- B-03 result: `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
- B-04 result: `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- B-05 result: `docs/requirements/SEARCH_REQUIREMENTS.md`
- Downstream next task: `B-06 [P0] 人間工程と自動工程を要件として分離する`
- Primary references:
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/reference/OBJECT_CLASSIFICATION_SURVEY.md`
  - `docs/requirements/OBJECT_TYPE_CANDIDATES.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/planning/OBJECT_TYPE_REFINEMENT_TASKS.md`

## 1. 完了したClassification model

SGOKBは、Object IdentityとClassificationを分離し、各Objectに1件のPrimary Classと0件以上のAdditional Classを割り当てる。Classはhierarchical Class Registryで管理し、hierarchyはDAGとする。

`object_id`はClass変更・追加で変更しない。

Classification edge (`instance_of` / `subclass_of`) と通常Semantic Relationは分離する。

## 2. B-02Dで確定した境界

- Object = 長期的に独立Identity / Knowledge / Evidence / Versionを持つ意味対象。
- Class = Objectの種類。
- Facet = 同一Object内部の意味的観点。
- Relation = 独立Object同士の意味的接続。
- value / metadata = 独立Identityを必要としない日時・数値・短い状態等。
- Source record = Evidenceをどの資料から取得したかを表し、Objectとは別責務。

詳細は `OBJECT_TYPE_BOUNDARIES.md` を正本とする。

## 3. 初期Class Registry方針

B-02Dで正式採用したClassは、専用機能の実装優先度にかかわらず、原則として通常Objectデータ投入前に初期Class Registryへseedする。

Class Registry包含とClass固有Facet / UI / validation / search等の実装優先度は分離する。

専用機能優先度は次を基準とする。

- Core: Character / Work / Concept
- High: Person / Organization / Series / Place / Event
- Later: その他の採用Class

## 4. 主要な境界決定

- CharacterとPersonはAgent配下の兄弟Class。
- OrganizationとGroupはAgent配下の兄弟Classとし、Team / FactionをGroup配下へ置く。制度的Organizationでもある対象はmultiple classificationを利用する。
- Series / FranchiseはWork属性ではなくCreativeWork系の独立Class。
- Episode / Chapter / Volume / Season / ArcはWorkComponent系Object Class。ただし独立Knowledge価値がない単なる構造要素はmetadataでもよい。
- Settingは原則Facet。独立世界はWorld / Place Object。
- 架空性は横断`FictionalEntity`分類で表し、Real/Fictionalの二重Primary hierarchyを作らない。
- Taxon / Species / FictionalRaceはKnowledge Objectであり、Class Registry taxonomyとは別。
- Theme / Trait / Emotion / Motivation / Role等はConcept系Objectとして独立管理できるが、Object固有記述ではFacet valueにもできる。
- named Ability / SkillはObject + Relation。能力概要はFacetにも保持可能。
- Date / Time Interval、通常のrelease dateはscalar metadata。
- Natural / Social Phenomenon類型はPhenomenon Object、個別発生はEvent Object。
- Termは原則lexical metadata。専用Term Classは初期採用しない。

## 5. fallback rule

既存上位Classが対象を意味的に正しく表す場合だけfallbackを許可する。

例: 未知のWork subtype → Work は可。

意味カテゴリが異なるClassへの丸め込みは不可。

例: Ability未登録 → Concept、Series未登録 → Work のような「実装都合の仮置き」は禁止する。

適切なClassがない場合はClass追加review / stagingへ送る。物理workflowはE-01 / E-05で決定する。

## 6. B-03へ引き継いだ入力と反映結果

B-03ではClass family別に必要Source coverageを検討する。

- Agent: profile / biography / interview / organization page
- CreativeWork: official work / series portal / episode guide / credits / store
- Place / World: lore / map / geographic / facility source
- Event: official record / timeline / news
- Artifact / Product: specification / manual / product / lore
- Taxon / Creature: taxonomy DB / encyclopedia / guide
- Concept / Capability / Process: dictionary / academic / criticism / rulebook
- Temporal: chronology / history / official timeline
- System / Software / Service: documentation / repository / release notes
- Material / Phenomenon: scientific / technical / government source
- Language / WritingSystem: dictionary / grammar / linguistic / setting source

B-03ではこの入力を反映し、Source IdentityをURLから独立させ、Source classificationをresource type / media type / document genre / publisher kind / subject relationship / provider / page purpose等へ分解した。またEvidenceを単一Snapshotへ遡れる意味非改変の検索・引用単位として確定した。正本は`docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`とする。

## 7. Phase Eへの入力

E-01:
- Class Registry / hierarchy / Object-Class membership schema
- Structural / Primary-eligible / Additional-onlyの表現
- B-02D seed集合の決定論的投入
- class review / staging

E-02:
- 専用Facet未実装Classでも共通Object contractで保持可能にする

E-05:
- Registry存在 / assignability validation
- semanticに不正確なfallbackを拒否

## 8. 現在地点

```text
B-02A 外部分類体系調査        Complete
B-02B Object候補整理           Complete
B-02C Classification model     Complete
B-02D Boundary確定             Complete
  ↓
B-03 Source / Evidence要件      Complete
B-04 Object Result要件              Complete
B-05 Search要件                     Complete
B-06 Workflow要件                   Next
```

Object Type Refinement seriesは完了した。
