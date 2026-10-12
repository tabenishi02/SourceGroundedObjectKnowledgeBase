# Source Grounded Object Knowledge Base — Object Schema Design

更新日: 2026-10-12

- Task: `E-01 [P0] Object schemaを設計する`
- Status: Complete
- Migration: `src/sgokb/migrations/003_object_schema.sql`
- Domain contract: `src/sgokb/domain/object.py`
- Persistence: `src/sgokb/storage/object_repository.py`

## 1. 目的

本書は、Phase B / Cで確定したObject Identity / Classification契約を、Phase Eで利用するSQLite物理schemaへ具体化した設計正本である。

E-01ではObject Registry、Class Registry、Class hierarchy、Primary / Additional Class membership、Object lifecycle、Knowledge Version参照、Relation Type Registry、Object Relationの物理骨格を確定する。

Facet / Statement / Evidence grounding / Version state machine / Result JSON Schemaは後続Taskへ残し、本Taskで過剰に先取りしない。

---

## 2. 採用した全体構造

```text
Object Registry
  objects
  object_aliases
  object_additional_classes
  object_registry_events

Classification Registry
  object_classes
  object_class_parents
  object_class_proposals

Knowledge skeleton
  object_versions
  relation_types
  object_relations
```

旧Prototypeの`entities / entity_relations / entity_evidence`はこのschemaの正本として再利用しない。Migration 003はadditive migrationであり、旧tableを破壊・renameしない。

---

## 3. ID方針

### Object / runtime record ID

`object_id`を含む新しいruntime persistent record IDはSQLite上では`TEXT`とする。

SGOKBが新規発行するObject IDはlocal UUIDv4文字列を使用する。

```text
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
```

IDはname、Class、Source、Version、path等から生成しない。名称変更・再分類・Knowledge更新でも同一`object_id`を維持する。

既存Prototype dataの実migrationはPhase Lで行うため、E-01では旧Entity IDを変換しない。

### Registry ID

初期Class RegistryはDBごとにIDが変化しないよう固定text IDを使用する。

```text
class:character
class:work
class:concept
```

Relation Type Registryも同じ考え方を採用し、標準的には次の形式を利用する。

```text
relation:<stable-key>
```

Registry表示名を変更しても既存IDを変更・再利用しない。

---

## 4. Object Registry

### `objects`

保持するのはObject Identityとcurrent registry metadataだけとする。

主要列:

- `id`: stable `object_id`
- `name`: current display name。非一意
- `primary_class_id`: 必須1件
- `status`: `active | archived`
- `current_version_id`: nullable Knowledge Version参照
- `created_at`
- `updated_at`

同名Objectを許容するため、`name`にunique constraintを置かない。

`current_version_id = NULL`はKnowledge未生成Objectの正常状態である。

### `object_aliases`

aliasをJSON列ではなく独立tableへ正規化する。

- `id`
- `object_id`
- `value`
- `language`: nullable
- `kind`: 初期default=`alias`
- `created_at`

language / kindを物理的に保持できるようにしたが、最終vocabularyやBCP 47 validationはE-05等で必要に応じて具体化する。

### `object_registry_events`

Object registry metadata変更の最低監査契約としてappend型eventを保存する。

対象例:

- Object作成
- name変更
- alias追加
- Primary Class変更
- Additional Class変更
- lifecycle status変更

Knowledge本文のVersion履歴とRegistry metadata監査を混同しない。

---

## 5. Class Registry / Classification

### `object_classes`

Classを固定enumや自由文字列としてObjectへ埋め込まず、Registry recordとして管理する。

主要列:

- `id`: stable Class ID
- `key`: machine-readable stable key
- `name`: human-readable display name
- `description`
- `assignment_policy`
  - `structural`
  - `primary_eligible`
  - `additional_only`
- `status`: `active | archived`
- `created_at / updated_at`

### `object_class_parents`

Class hierarchyの`subclass_of`相当edgeを保存する。

```text
child_class_id -> parent_class_id
```

複数親を許容するためtreeではなくDAGとする。SQLite triggerでcycle生成を拒否する。

Ancestor membershipをObjectごとに重複保存しない。検索・validation時にrecursive CTE等で導出する。

### Primary Class

Primary Classは`objects.primary_class_id`として直接保持する。

これにより、Objectは作成時から必ず1件のPrimary Classを持つことをDBレベルで保証できる。

DB triggerで次を要求する。

- Classが存在する。
- Classが`active`である。
- `assignment_policy = primary_eligible`である。

### Additional Class

Additional membershipは`object_additional_classes`へ保存する。

DB triggerで次を要求する。

- Classが存在しactiveである。
- `primary_eligible`または`additional_only`である。
- `structural` Classを直接割り当てない。
- Primary Classと同一Classを重複登録しない。

Primary / Additional Class訂正で`object_id`は変更しない。

---

## 6. 初期Class Registry seed

B-02Dで正式採用した62 ClassをMigration 003内へ固定IDでseedする。

seedの正本はmigration SQLそのものとし、fresh DBと既存DB upgradeで同一Class ID / hierarchyを得る。

代表例:

```text
class:object_class        ObjectClass       structural
class:fictional_entity   FictionalEntity   additional_only
class:agent               Agent             structural
class:character           Character         primary_eligible
class:creative_work       CreativeWork      structural
class:work                Work              primary_eligible
class:concept             Concept           primary_eligible
```

Characterは`Agent`と`FictionalEntity`の2親、FictionalRaceは`Taxon`と`FictionalEntity`の2親を持ち、DAG要件を実際のseedで使用する。

通常Object投入前にseedが存在するため、「Classが未登録だからConcept等へ誤fallbackする」必要をなくす。

将来Classを追加する場合は既存seed IDを書き換えず、additive migrationまたは明示的Registry operationで追加する。

---

## 7. Unknown Class / proposal staging

適切なClassが存在しない場合、Objectを意味的に不正確なClassへ登録しない。

`object_class_proposals`をcanonical Class Registryとは別tableとして設ける。

```text
unknown Class requirement
  -> object_class_proposals (pending)
  -> human/design review
  -> acceptedなら別操作でobject_classesへ追加
```

proposal作成自体は`object_classes`を変更しない。

この分離により、将来のObject ResultにRegistry proposalが含まれても、通常Knowledge Importの副作用でClass Registryをsilent変更しない物理境界を確保する。

proposal reviewの詳細state machine / UI / CLIはE-05 / H / Mで具体化できる。

---

## 8. Knowledge Version参照境界

E-01では`object_versions`をKnowledge Versionの**物理Identity skeleton**として導入する。

保持するのは次だけである。

- `id`
- `object_id`
- `version_number`
- `created_at`

`objects.current_version_id`はnullableであり、triggerによって「そのVersionが同じObjectに属する」ことを保証する。

E-01では以下を決めない。

- accepted / candidate等のVersion state
- Result precondition / stale処理
- commit / rollback algorithm
- current promotion transaction
- immutable enforcementの最終方式
- derived index invalidation

これらはE-04で確定する。

---

## 9. Relation Type / Object Relation

### `relation_types`

Semantic Relation vocabularyをClass Registryから分離したRegistryとして保持する。

主要列:

- stable Relation Type ID
- stable key
- display name
- description
- lifecycle status
- timestamps

Classificationの`instance_of / subclass_of`をこのRegistryへ入れない。

### `object_relations`

Relation edgeの物理骨格は次とする。

```text
version_id
subject_object_id
relation_type_id
object_object_id
```

RelationはObject Registryのmutable metadataではなくVersioned Knowledgeに属するため、`version_id`を必須とする。

ただしE-01ではEvidence groundingを持たせない。Statement / attribute / RelationからEvidenceへ張るLinkとEvidence roleはE-03で追加する。

Relation Typeのdirectionality / inverse / symmetry等の詳細vocabularyも必要性を確認して後続Taskで追加可能とする。

---

## 10. Domain / storage responsibility

`src/sgokb/domain/object.py`はSQLiteへ依存しないObject contractを持つ。

- Assignment policy
- lifecycle status
- Object / alias / Class record
- local persistent ID generation

新domain codeはPrototype実装`domain/_prototype.py`へ依存しない。

`src/sgokb/storage/object_repository.py`は既存SQLite connectionを受け取り、E-01で必要なcanonical Object Registry操作だけを担当する。

既存`repository.py`は移行期間のfaçadeとして残し、`object_store`から新Object persistenceを公開する。旧Repositoryを`storage/repository.py`へwholesale moveしていない。

---

## 11. Migration boundary

Migration 003は次を行う。

- 新canonical Object schema追加
- 初期Class Registry seed
- Classification integrity trigger追加

次は行わない。

- `entities` -> `objects` data migration
- `entity_relations` -> `object_relations` data migration
- Fragment / Document変換
- 旧table削除・rename

したがって既存Prototype DBはMigration 003適用後も従来dataを保持したまま、新schemaとcoexistできる。

実データの意味変換・archiveはPhase Lの責務とする。

---

## 12. Integrity contract

E-01でSQLiteが直接保証する主なinvariantは次である。

1. Objectは必ずPrimary Classを持つ。
2. Primary Classはactive `primary_eligible` Classである。
3. Additional Classへstructural Classを割り当てない。
4. Primary / Additionalへ同じClassを重複登録しない。
5. Class hierarchyにcycleを作らない。
6. Object name / aliasをglobal uniqueにしない。
7. `current_version_id`は同一ObjectのVersionだけを参照し、Version ownerは後から変更しない。
8. Object Relationはactive Relation Typeを使い、そのVersion owner ObjectがRelationのendpointとして参加する。
9. Class proposalはClass Registryとは別tableにstagingされる。

より高位の意味validationはdomain / Result Validator側で行い、SQLite constraintだけを意味品質保証として扱わない。

---

## 13. E-02以降への引き継ぎ

### E-02 — Complete

`docs/design/SEMANTIC_FACET_SCHEMA.md`を正本として、Facet Registry、Class-to-Facet profile、Knowledge Statement、typed attribute、temporal scope、Object / Facet / Statement Search Representation membershipを確定した。

### E-03 — Complete

`docs/design/SOURCE_EVIDENCE_SCHEMA.md`を正本として、canonical Source Identity / locator / Snapshot / Raw Artifact / Normalization Run / Evidence、Source↔Object association、Statement / attribute / Relation -> Evidence Link、Evidence role、Provenance integrityをMigration 006で確定した。

### E-04 — Complete

`docs/design/VERSIONING_SCHEMA.md`を正本としてMigration 007を追加し、candidate / accepted / abandoned lifecycle、full snapshot、base / Classification stale判定、accepted immutability、current promotion / rollback、derived-state failure domainを確定した。

### E-05 — Complete

`docs/design/OBJECT_RESULT_JSON_SCHEMA.md`を正本として、`sgokb.object-result/1.0`のDraft 2020-12 canonical Object Result Schemaを確定した。Registry proposal exchange shape、Class / Relation / Facet / Attributeの参照契約、Package / base Version / Classification binding、Evidence-grounded Knowledge、partial / insufficient evidence等のResult状態を共通Schemaへ反映した。

E-05完了によりPhase EのObject Knowledge data modelは完結した。次の実装段階はPhase Fで既存Capture / Import / Normalize / Evidence pipelineをcanonical Source / Evidence modelへ接続する。

---

## 14. Validation result

E-01実装では次を自動test対象とする。

- 62 Class seedとDAG ancestry
- 同名別Object
- structural ClassのPrimary / Additional assignment拒否
- Primary / Additional重複拒否
- hierarchy cycle拒否
- current Version ownership
- Registry metadata audit
- unknown Class proposal staging
- Relation Type RegistryとClass Registryの分離
- Version-scoped Object Relation
- v1 Prototype DBからMigration 003までのupgrade integrity

E-01完了後の次Taskは `E-02 [P0] Semantic Facet schemaを設計する` とする。
