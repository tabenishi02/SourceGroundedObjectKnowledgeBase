# Source Grounded Object Knowledge Base — Semantic Facet Schema Design

更新日: 2026-10-12

- Task: `E-02 [P0] Semantic Facet schemaを設計する`
- Status: Complete
- Prerequisite: `docs/design/OBJECT_SCHEMA.md`
- Migration: `src/sgokb/migrations/004_semantic_facets.sql`
- Domain contract: `src/sgokb/domain/knowledge.py`
- Persistence: `src/sgokb/storage/semantic_repository.py`

## 1. 目的

本書は、E-01で確定したStable Object / Class / Knowledge Version骨格の上に、Object Knowledgeの意味内容を保存する物理schemaを定義する。

E-02では次を確定する。

- Facet Registry
- Class-to-Facet profile
- common Facet
- VersionごとのFacet状態
- Knowledge Statement
- typed structured attribute
- Statement / attribute / Relationのtemporal scope
- Object / Facet / Statement Search RepresentationとVersion membership

Evidence groundingはE-03、Version lifecycle / accepted immutability / current promotionはE-04、Object Result JSON Schema最終形はE-05へ残す。

---

## 2. 採用した全体構造

```text
Facet vocabulary
  facet_definitions
  class_facet_profiles

Versioned canonical Knowledge
  object_version_facets
  knowledge_statements
  attribute_definitions
  object_version_attributes
  temporal_scopes
  relation_temporal_scopes

Derived Search Representation
  search_representations
  search_representation_memberships
```

FacetやattributeをCharacter / Work / Concept専用DB列として固定しない。新しいClass / Facet / attributeを追加しても`objects` tableの列追加を要求しない構造とする。

---

## 3. Facet Registry

### `facet_definitions`

Facetは自由文字列ではなくRegistryで管理する。

主要列:

- `id`: stable Facet ID
- `key`: machine-readable stable key
- `name`
- `description`
- `is_common`
- `status`: `active | archived`
- timestamps

初期IDは次の形式とする。

```text
facet:overall
facet:personality
facet:themes
```

Facet名変更でIDを変更しない。

### common Facet

`overall`を初期common Facetとする。

common FacetはClass専用profileが未定義でも利用できる。したがって、初期Class Registryに存在するが専用Facet未実装のClassも共通Object contractを利用できる。

専用Facet未実装を理由に別Classへfallbackしない。

---

## 4. Class-to-Facet profile

`class_facet_profiles`でClassとFacetの対応を管理する。

主要列:

- `class_id`
- `facet_id`
- `position`
- `inherit_to_descendants`

Class hierarchyはE-01でDAGとして定義済みである。profileはancestor Classから継承可能とする。

例えば`WorkEdition subclass_of Work`であり、Work profileの`themes / worldview / narrative / tone / characters / relationships`を継承できる。

Profile解決時は、Result / Validation側が対象時点のPrimary / Additional Class snapshotを入力として利用できる。現在のObject classificationだけを過去Versionの意味契約として固定しない。

---

## 5. 初期Facet seed

初期Registryには18 Facetをseedする。

### Common

```text
overall
```

### Character profile

```text
personality
values
motivation
behavior
relationships
role
themes
abilities
```

### Work profile

```text
themes
worldview
narrative
tone
characters
relationships
```

### Concept profile

```text
definition
properties
implications
related_concepts
examples
```

`themes`や`relationships`のように意味が共有できるFacetは同じRegistry entryを複数Class profileから参照する。これにより将来の明示的cross-class Facet comparisonを可能にする。

Character / Work / Concept以外のClassはE-02 core実装時点で専用profileを必須としない。`overall`と共通Knowledge contractで保持できる。

ただし、この初期18 Facet / 3 profileはVertical Sliceを成立させるための初期seedであり、全ClassのFacet taxonomyが確定したことを意味しない。2026-10-12の設計レビューにより、全62 Classを対象とするE-02A〜E-02Cを追加し、Class意味境界、Facet候補、近義Facetの統合、Object / Facet / Attribute / Relation境界、gold casesを事前検証してからFacet taxonomyをfreezeする方針へ更新した。

E-02C完了後、Migration 005により新規37 Facetを追加し、runtime Facet Registryは合計55 Facetへ拡張した。

---

## 6. VersionごとのFacet状態

`object_version_facets`は、特定Knowledge Versionで特定Facetをどう扱ったかを明示する。

状態:

- `content`: grounded contentを保持するFacet
- `insufficient_evidence`: 分析したが根拠不足
- `not_applicable`: 対象Objectへ適用しない
- `not_analyzed`: Package / process上未分析

Facet行が存在しないこと自体を`not_applicable`や「特徴が存在しない」と解釈しない。

`content`以外のFacetへKnowledge Statementを保存することはDB triggerで拒否する。また、Statementを保持中のFacetを`content`以外へ変更することも拒否する。

Result full snapshotでFacet omissionをどう扱うかはE-04 / E-05で確定する。

---

## 7. Knowledge Statement

`knowledge_statements`は、Object Knowledge Version内部の意味的主張・説明単位である。

主要列:

- row `id`
- `version_id`
- nullable `facet_id`
- `local_key`
- `text`
- `derivation_kind`
- `language`
- nullable `temporal_scope_id`
- `created_at`

`derivation_kind`はB-04の初期語彙を物理化する。

```text
direct_statement
synthesis
interpretation
reported_view
```

`facet_id`があるStatementはそのVersionの`object_version_facets`へ必ず対応する。

`facet_id = NULL`はObject-level summary Statementとして使用できる。これによりB-04の`summary`とFacet内Statementを同じStatement contractで保持しつつ、summaryとcommon `overall` Facetを同一概念へ潰さない。

Statement `id`はDB行参照として一意だが、Versionをまたぐ永続Semantic Identityとはみなさない。`local_key`は1 Version内で一意とし、Result内参照とImport時対応に利用できる。

Evidence grounding / reported-view attributionの最終構造はE-03 / E-05で追加する。

---

## 8. Typed Structured Attribute

### `attribute_definitions`

Attribute keyも無制限自由文字列ではなくRegistry recordとして扱う。

value type:

```text
text
integer
real
boolean
date
datetime
identifier
enum
json
```

E-02ではClass別Attribute extension一覧を固定しない。E-05のClass extension schemaが必要に応じて利用可能keyを制約できる。

### `object_version_attributes`

Attribute valueはKnowledge Versionに属する。

主要列:

- `version_id`
- `attribute_id`
- `ordinal`
- `status`
- typed value columns
- `language`
- nullable `temporal_scope_id`

状態:

```text
known
insufficient_evidence
not_applicable
not_analyzed
```

`known`ではAttribute Definitionの`value_type`と一致する物理value列を1つだけ使用する。DB triggerで型不一致を拒否する。

`known`以外はvalueを保持しない。

同じAttributeを複数保持する場合は`ordinal`でVersion内順序を区別する。`UNIQUE(version_id, attribute_id, ordinal)`により同じslotの二重登録を防ぐ。

---

## 9. Temporal Scope

Versionの`created_at`とKnowledgeが成立する時間を分離する。

`temporal_scopes`はVersion-scoped recordとして次を保持できる。

- `as_of`
- `valid_from`
- `valid_to`
- `context_object_id`
- `label`

`context_object_id`はPeriod / Era / Timeline / Continuity等のObjectを参照できる。Class適合性の最終validationはE-05へ残す。

Statement / attributeはcomposite foreign keyにより同じVersionのTemporal Scopeだけを参照できる。

RelationはE-01 table shapeを壊さないため`relation_temporal_scopes`で0..1 Scopeを関連付ける。RelationとScopeのVersion一致をtriggerで保証する。

```text
Version created_at = 2026-10-12
Statement valid_from = 2024-01-01
```

のような状態を正しく表現できる。

---

## 10. Search Representation

Search Representationはcanonical Knowledgeではなく再生成可能なderived layerとする。

### `search_representations`

保持する情報:

- `kind`: `object | facet | statement`
- `builder_key`
- `builder_version`
- deterministic representation `content`
- `content_hash`
- `created_at`

同じ`kind + builder + builder version + content hash`は同一representationとして再利用できる。

### `search_representation_memberships`

Representation本体と、どのKnowledge Version / targetへ属するかを分離する。

- `version_id`
- `representation_id`
- `target_kind`
- `target_ref`

`target_ref`の意味:

```text
object    -> object_id
facet     -> facet_id
statement -> statement_id
```

DB triggerでtargetがそのVersionに属することと、Representation kindがtarget kindと一致することを検証する。

これにより同じrepresentation textを別Versionで再利用しても、current / historical membershipを混同しない。

Embedding Space / Vector backend / vector reuse自体はPhase Iで設計する。

---

## 11. Canonical / Derived境界

E-02で正本Knowledgeとして扱うのは次である。

```text
object_version_facets
knowledge_statements
attribute_definitions / object_version_attributes
temporal_scopes
relation_temporal_scopes
```

一方、次はderived dataである。

```text
search_representations
search_representation_memberships
```

Search Representationを失っても、Object Knowledge Versionから再構築できなければならない。

Representation builderを変更してもKnowledge Version自体を書き換えない。

---

## 12. Facet profile validation boundary

Facet Registry / profileは物理schemaとして保持するが、`object_version_facets` insert時に現在のObject classificationへ強くbindするDB triggerは置かない。

理由は、ClassificationがObject Registry metadataとしてVersionとは別に訂正可能だからである。

過去VersionのFacet適合性を現在のPrimary Classだけで再評価すると、後日のClass訂正によって既存Versionが不正扱いになる可能性がある。

したがって、E-02では次の責務分離を採用する。

```text
DB:
  FacetがRegistryに存在しactiveであることを保証

Application / Result Validator:
  Package / Result時点のPrimary / Additional Class snapshotを使い
  common + Class profile + ancestor profileを解決
```

最終referential / profile validationはE-05 / H-01へ引き継ぐ。

---

## 13. E-02 follow-up hardening

E-02の物理schemaはCompleteだが、Facet taxonomyの意味設計は次の追加Taskでhardeningする。

### E-02A — 全Class Facet taxonomy survey — Complete

成果物: `docs/design/FACET_TAXONOMY_SURVEY.md`

- E-01 initial Registryの全62 Classを対象とする。
- Classごとの意味定義、include / exclude、想定Knowledge、Facet候補を整理する。
- Facetへ置く情報とObject / Attribute / Relation / Statementへ置く情報の境界を明示する。
- representative examples / counterexamplesでClass意味幅を検証する。

### E-02B — Facet vocabulary横断統合 — Complete

成果物: `docs/design/FACET_VOCABULARY_REVIEW.md`

- 初期18 Facetを全件維持し、既存stable ID / keyを変更しない。
- E-02A候補を横断統合し、E-02C向けfreeze候補を既存18 + 新規37 = 55 Facetへ整理した。
- shared / class-specific / inherited profileを区別し、Group / WorkComponent / Capability / Process / TemporalEntity / System / Material / Phenomenon / SymbolicSystem等の自然なancestor profile候補を整理した。
- `purpose / function / usage`等、意味差が検索・比較上重要な近義語は別Facetとして維持する。
- Relation / Attributeへ置くべき候補はFacet Definitionへ昇格させない。
- Registry / profileの物理変更はE-02Cのgold case通過後に新規additive migrationで適用する。

### E-02C — Class / Facet境界gold cases — Complete

成果物: `docs/reference/CLASS_FACET_GOLD_CASES.md` / `tests/fixtures/class_facet_gold_cases.json`

- 初期62 Classを62/62 coverageし、positive / negative例と代表Knowledge配置をgold化した。
- 25件のcross-cutting boundary caseで近義Facet、Relation / Attribute境界、inheritance、fallback禁止を検証した。
- E-02Bの55 Facet候補に修正要求がないことを確認し、Facet taxonomyをfreezeした。
- Migration 005で新規37 Facetと169 profile rowを追加し、runtime Registryを55 Facet / 188 profile rowへ更新した。
- `tests/test_class_facet_gold_cases.py`をE-05 / I-07 / N-01 / N-02で再利用可能なregression基盤とした。

---

## 14. E-03以降へ残す事項

### E-03

- Statement / attribute / Relation → Evidence Link
- Evidence role (`supports / contradicts / contextualizes`等)
- Source / Snapshot / Raw Artifact / Normalized Run / Evidenceの新物理schema
- Provenance integrity

### E-04

- Version candidate / accepted state
- accepted Version immutability
- stale Result
- omission / deletion semantics
- current promotion / rollback
- Search Representation invalidation / regeneration transaction境界

### E-05

- Object Result JSON Schema
- Class extension schema
- Facet profile / Attribute key validation
- reported-view attributionの交換形式
- Knowledge language / temporal field formatの最終validation
- partial / insufficient evidence Result status

### Phase I

- Contextual Search Representation Builder
- Embedding Space
- Object / Facet / Statement Embedding
- Vector backend
- current / historical Search Index materialization

---

## 15. Migration boundary

Migration 004 / 005はいずれもadditive migrationである。

次を行う。

- Migration 004: Semantic Facet schema、初期18 Facet、Character / Work / Concept profile、Statement / Attribute / Temporal Scope、Search Representation metadataを追加。
- Migration 005: E-02Cでfreezeした新規37 Facetと169 Class profile rowを追加し、合計55 Facet / 188 profile rowとする。

次は行わない。

- 旧FragmentをKnowledge Statementへ変換する
- 旧DocumentをFacetへ分解する
- Existing ObjectへKnowledge Versionを自動生成する
- Evidence Linkを生成する
- current Versionを変更する

Prototype dataの意味migrationは引き続きPhase Lの責務とする。

---

## 16. Integrity contract

E-02でSQLiteが直接保証する主なinvariantは次である。

1. Facet / Attribute keyはRegistry recordを参照する。
2. 新規Version Facetはactive Facetだけを使用する。
3. Facet-specific Statementは同じVersionのFacet instanceへ属する。
4. `content`以外のFacetへStatementを保存しない。
5. Statementを保持するFacetを非content状態へ変更しない。
6. Attributeのphysical value columnはDefinitionのvalue typeと一致する。
7. `known`以外のAttribute statusはvalueを保持しない。
8. Statement / attributeのTemporal Scopeは同じVersionへ属する。
9. Relation Temporal ScopeはRelationと同じVersionへ属する。
10. Search Representation kindとtarget kindは一致する。
11. Search Representation membership targetは指定Versionへ属する。
12. builder version / content hashとVersion membershipを分離して追跡する。

意味品質やEvidenceの妥当性はこれらのDB constraintだけでは保証しない。

---

## 17. Validation result

E-02実装では次をtest対象とする。

- 55 Facet / 188 Class-profile seed（Migration 004 + 005）
- common `overall` Facet
- Work subclass / Concept subclassへのprofile inheritance
- 専用profileなしClassのcommon contract
- Facet statusとStatement整合
- summary StatementのFacet非依存保存
- typed Attribute value / status
- Temporal ScopeのVersion isolation
- Relation Temporal ScopeのVersion一致
- Object / Facet / Statement Search Representation membership
- builder version / content hash追跡
- Migration 004 / 005適用後の既存回帰
- 62 Class + 25 boundary gold fixture coverage / profile inheritance整合

E-02A / E-02B / E-02Cは完了した。Facet taxonomyは55 FacetでfreezeしMigration 005へ反映済み。次Taskは `E-03 [P0] Source / Evidence / Evidence Link / Provenance schemaを設計する` とする。
