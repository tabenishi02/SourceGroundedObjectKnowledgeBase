# Source Grounded Object Knowledge Base — Phase E Preparation

更新日: 2026-10-12

- Target: `Phase E — Object Knowledgeデータモデル`
- Status: E-01 Complete / E-02 Ready
- Active redesign branch: `integration/knowledge-base-redesign`
- Phase D status: Complete — D-01〜D-07
- Structural prerequisite: Complete — `domain.py -> domain/` package conversion
- Next task: `E-02 [P0] Semantic Facet schemaを設計する`

## 1. 目的

本書は、Phase Dで確定したRepository / Git / module責務境界を、Phase EのObject Knowledge物理データモデル設計へ安全に引き継ぐための開始条件・既存実装・設計入力・禁止事項を整理する。

Phase Eでは、Phase B / Cで定義済みの論理契約をSQLite schema、domain contract、migration方針へ具体化する。

ただし、Phase E開始時点で旧Prototype DBを破壊的に置換しない。既存Prototype dataの実migrationはPhase Lで扱い、Phase Eでは新canonical modelのschemaを先に確定する。

---

## 2. Phase D完了監査

Task masterのPhase Dを再監査し、未完了checkboxが0件であることを確認した。

```text
D-01 [P0] 長期branch strategy                         完了
D-02 [P0] 旧Prototype文書の扱い                      完了
D-03 [P0] docs構造                                   完了
D-04 [P0] src/sgokb責務別設計                        完了
D-05 [P1] module移動方針                             完了
D-06 [P1] runtime data / Git exclusion               完了
D-07 [P1] branch / PR / tag / release cleanup policy 完了
```

Phase D完了条件である次も満たしている。

- 新旧assetの配置ルールが決まっている。
- module migrationの段階実施手順が決まっている。
- runtime / generated / exchange / backupのGit境界が決まっている。
- branch / PR / tag / releaseのcleanup ruleが決まっている。
- 未救済commitを持つarchive branchを削除していない。
- Phase E開始時の正規branchが`integration/knowledge-base-redesign`である。

---

## 3. Phase E直前のstructural prerequisite

D-05 Wave 1では、E-01のschema/domain behavior変更より前に`domain.py`をpackageへ変換することを要求していた。

これをPhase E準備として完了した。

変更後:

```text
src/sgokb/domain/
├─ __init__.py
└─ _prototype.py
```

- 旧`domain.py`の内容は変更せず`_prototype.py`へ100% renameした。
- `domain/__init__.py`で既存public symbolを明示re-exportする。
- `from sgokb.domain import SearchFilter`等の既存import pathを維持する。
- 新Object domain contractを`domain/`内へ追加可能になった。
- 新Object domain codeから`_prototype.py`へ依存してはならない。

GitHub PR: `#11 Phase E prep: convert domain module to package`

Validation:

- `python -m pytest -q` → 71 passed
- `python -m compileall -q src` → passed
- `PYTHONPATH=src python -m sgokb --help` → passed
- existing import compatibility smoke → passed
- move detection → R100

---

## 4. Phase Eの目的

Phase Eは、SGOKBのcanonical Object Knowledge Storeを支える物理データモデルを定義する。

対象:

```text
E-01 Object schema
E-02 Semantic Facet schema
E-03 Source / Evidence / Evidence Link / Provenance schema
E-04 Versioning
E-05 Object Result JSON Schema
```

Phase E完了時には、ChatGPT Result、SQLite canonical store、Search、MCPが共有できるObject modelの物理契約が確定している必要がある。

---

## 5. E-01へ引き継ぐ論理契約

### 5.1 Stable Object Identity

ObjectはSource / Document / Version / name / Classから独立したstable identityを持つ。

必須概念:

- `object_id`
- current display name
- 0..N aliases
- lifecycle status
- Primary Class 1件
- Additional Class 0..N
- nullable current Knowledge Version reference
- registry created / updated time

名称変更、Class訂正、Knowledge Version追加で`object_id`を変更しない。

### 5.2 Class Registry

Classは固定enumや自由文字列ではなくRegistryで管理する。

必要概念:

- stable Class identity
- display name / description
- lifecycle status
- assignment policy
  - `structural`
  - `primary_eligible`
  - `additional_only`
- 0..N parent Class
- DAG / cycle prohibition

B-02Dで採用した全Classを通常Object投入前に決定論的にseedできなければならない。

### 5.3 Object-Class membership

- Primary Classは必須1件。
- Additional Classは0件以上。
- Ancestor ClassをObjectへ重複membershipとして保存することは要求しない。
- Classification edgeと通常Semantic Relationを混同しない。

### 5.4 Object registry metadataとKnowledge Versionを分離する

Registry metadata:

- identity
- name / alias
- classification
- lifecycle
- current version pointer

Versioned Knowledge:

- summary
- typed attribute
- Facet / Statement
- Relation
- Evidence grounding
- temporal scope

Object registryだけ存在し、Knowledge Versionが0件の正常状態を許容する。

### 5.5 Relation

E-01ではObject Relationの物理骨格とRelation Type vocabulary / Registryの責務境界を設計する。

ただしEvidence Link詳細はE-03、Result JSON表現はE-05で具体化する。

---

## 6. 初期Class Registry seed入力

B-02Dで正式採用したClass hierarchyをE-01のseed正本入力とする。

主要family:

- `ObjectClass` / `FictionalEntity`
- `Agent` → Character / Person / Organization / Group / Team / Faction / Creature
- `CreativeWork` → Work / Adaptation / WorkEdition / Series / Franchise / WorkComponent / Episode / Chapter / Volume / Season / Arc
- Place / World
- Event
- Artifact / Product
- Taxon / Species / FictionalRace
- Concept / Theme / Ideology / Trait / Emotion / Motivation / StateConcept / RoleConcept / ArtifactTypeConcept
- Capability / Ability / Skill
- Process / Action / Activity
- TemporalEntity / Period / Era / Timeline / Continuity
- System / Software / Service / RuleSystem
- Material / Substance
- Phenomenon / NaturalPhenomenon / SocialPhenomenon
- SymbolicSystem / Language / WritingSystem

具体的な階層・assignment policyは`OBJECT_TYPE_BOUNDARIES.md`を正本とし、本書へ重複定義しない。

---

## 7. 現行Prototype DB baseline

E-01開始前に現行migrationを確認した。

### 7.1 `entities`

現在:

```sql
CREATE TABLE entities (
 id TEXT PRIMARY KEY,
 type TEXT NOT NULL,
 name TEXT NOT NULL,
 aliases TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(type,name)
);
```

新Object要件との差分:

- `UNIQUE(type,name)`は同名別Object要件と衝突する。
- `type`は旧1階層分類でClass Registryを表現できない。
- aliasはJSON text 1列で、language / kind等の拡張が難しい。
- lifecycle statusがない。
- `current_version`がない。
- `updated_at`がない。
- multiple classificationがない。

したがって`entities`のrenameだけでE-01を完了しない。

### 7.2 `entity_relations`

現在:

```sql
CREATE TABLE entity_relations (
 subject_id TEXT NOT NULL REFERENCES entities(id),
 predicate TEXT NOT NULL,
 object_id TEXT NOT NULL REFERENCES entities(id),
 metadata TEXT NOT NULL,
 PRIMARY KEY(subject_id,predicate,object_id)
);
```

差分:

- predicateが自由文字列。
- Relation Type Registryがない。
- Knowledge Versionとの所属がない。
- Evidence groundingはRelation自身にbindされていない。
- temporal scopeがない。

Relation骨格は参考にできるが、そのままcanonical Relation schemaにはしない。

### 7.3 `entity_evidence`

現在はEntity↔Evidenceの単純many-to-manyである。

新設計では、Source↔Object association、Versioned Statement / Attribute / Relation grounding、Evidence roleを区別する必要がある。詳細はE-03で決定する。

### 7.4 Fragment / Document

`fragment_runs / fragments / documents / structured_documents`は旧Prototype責務であり、新Object Knowledge schemaの正本として再利用しない。

Phase Lまでlegacy dataとして保持可能だが、E-01で新schemaをこれらへ従属させない。

---

## 8. E-01で決めること

E-01では少なくとも次を具体化する。

1. `object_id`の物理型・生成責務。
2. `objects` table。
3. `object_aliases` table。
4. Class Registry table。
5. Class hierarchy edge table。
6. Object-Class membership表現。
7. Primary / Additional membership制約。
8. Object lifecycle status。
9. current Version referenceの物理境界。
10. Object registry metadata更新監査の最低契約。
11. Relation Type Registryの物理骨格。
12. Object Relationの物理骨格。
13. seedの配置形式と決定論的投入方式。
14. unknown Class / Registry proposal / stagingの最低物理境界。
15. storage responsibilityとmigration fileの配置方針。

---

## 9. E-01で決めすぎないこと

E-01で以下を過剰に先取りしない。

- Facet Registryの詳細 → E-02
- Statement / Attribute / Evidence grounding詳細 → E-02 / E-03
- Source / Snapshot / Evidence schema全面更新 → E-03
- Version commit / rollback / stale Result state machine → E-04
- Object Result JSON field最終形 → E-05
- Google Drive package format → Phase G
- Search representation / Vector backend → Phase I
- MCP Tool schema → Phase J
- Prototype DBから新DBへの実data migration → Phase L
- CLI UX → Phase M

E-01は後続schemaが乗る安定したObject / Classification / Relation / Version参照の骨格を作る。

---

## 10. Migration boundary

Phase Eでは新schema migrationを設計・実装できるが、旧Prototype dataの意味変換migrationを同時に行わない。

区別:

```text
Phase E:
  new canonical schema definition
  fresh DB migration
  schema-level coexistence / compatibility

Phase L:
  existing Prototype entity / fragment / document data
  -> new Object modelへの実data migration / archive
```

既存migration `001_initial.sql` / `002_knowledge_capture.sql`の内容を書き換えない。

新schemaは新しいmigration versionとして追加し、既存DBのmigration historyを保持する。

migration directory自体の`storage/migrations/`への物理moveは、D-05条件を満たす独立structural PRとして扱う。E-01 schema追加と無理に同一moveにしない。

---

## 11. Repository / domain責務

D-04 / D-05により次を維持する。

### `domain/`

- persistence-independent Object / Class / Relation contract
- domain validation
- SQLiteやSQLをimportしない
- `_prototype.py`へ新Object contractを依存させない

### `storage/`

- SQLite schema / migration / repository
- transaction / persistence integrity
- canonical Object persistence

現行`repository.py`を`storage/repository.py`へ丸ごとmoveしない。新Object persistenceをPhase E schemaに基づいて追加し、旧Repositoryは移行期間のfaçadeとする。

---

## 12. Git / PR実施方針

Phase Eの正規baseは`integration/knowledge-base-redesign`。

E-01実施branch:

```text
task/e01-object-schema
```

推奨分割:

```text
PR #11  domain module -> package structural conversion     完了

E-01 PR A  Object / Class domain contracts
E-01 PR B  SQLite schema / migration / storage implementation
E-01 PR C  seed / constraint / migration tests
```

実装量が小さければB/Cを統合できるが、domain設計変更と大規模repository refactorを同一PRへ混ぜない。

---

## 13. E-01 Definition of Ready

- [x] Phase A完了。
- [x] Phase B完了。
- [x] Phase C完了。
- [x] Phase D完了。
- [x] Object logical requirements accepted。
- [x] Class hierarchy / initial Registry seed accepted。
- [x] Object Result logical boundary accepted。
- [x] module responsibility design accepted。
- [x] module migration policy accepted。
- [x] `domain.py -> domain/` structural prerequisite完了。
- [x] integration branch clean / synced。
- [x] current Prototype entity / relation schemaを棚卸し済み。
- [x] Prototype data migrationをPhase Lへ分離済み。

以上によりE-01は開始可能である。

---

## 14. E-01開始時に読む文書

必須:

1. `docs/planning/PHASE_E_PREPARATION.md`
2. `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
3. `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
4. `docs/requirements/OBJECT_REQUIREMENTS.md`
5. `docs/requirements/OBJECT_TYPE_MODEL.md`
6. `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
7. `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
8. `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
9. `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`

E-01中に必要に応じ参照:

- `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
- `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`
- `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
- `docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`

---

## 15. 次チャット用指示文

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。
Phase A〜Dは完了し、Phase E開始準備も完了しています。

再設計の正規作業基盤はintegration/knowledge-base-redesignです。
D-05 Wave 1のdomain package conversionも完了済みです。

まず以下を確認してください。
- docs/planning/PHASE_E_PREPARATION.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md
- docs/requirements/OBJECT_REQUIREMENTS.md
- docs/requirements/OBJECT_TYPE_MODEL.md
- docs/requirements/OBJECT_TYPE_BOUNDARIES.md
- docs/requirements/OBJECT_RESULT_REQUIREMENTS.md
- docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md
- docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md

今回実施するタスク:
E-02 [P0] Semantic Facet schemaを設計する

E-01は`docs/design/OBJECT_SCHEMA.md`を正本として完了しています。E-01で確定したObject / Class / Version / Relation骨格を維持し、Facet Registry、Class-to-Facet profile、Knowledge Statement、typed attribute、temporal scope、Search Representation membershipを設計してください。Evidence Link詳細はE-03、Version state machineはE-04、JSON Schema最終形はE-05へ残してください。
```

---

## 16. 結論

Phase Dには残Taskはない。

D-05でPhase E開始前に要求されていたdomain package conversionも完了したため、Repository / Git / physical module boundaryの観点からPhase Eへ移行可能である。

E-01は`docs/design/OBJECT_SCHEMA.md`を正本として完了した。次Taskは`E-02 [P0] Semantic Facet schemaを設計する`。
