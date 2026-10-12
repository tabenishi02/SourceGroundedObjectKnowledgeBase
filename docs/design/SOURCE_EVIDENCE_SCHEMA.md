# Source Grounded Object Knowledge Base — Source / Evidence Schema Design

更新日: 2026-10-12

- Task: `E-03 [P0] Source / Evidence / Evidence Link / Provenance schemaを設計する`
- Status: Complete
- Logical authority: `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
- Related result contract: `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- Migration: `src/sgokb/migrations/006_source_evidence_schema.sql`
- Domain contract: `src/sgokb/domain/source.py`
- Persistence: `src/sgokb/storage/source_repository.py`

## 1. 目的

本書は、B-03で確定したSource / Snapshot / Raw Artifact / Normalized Run / Evidence / Provenance契約を、Phase Eで利用するSQLite物理schemaへ具体化した設計正本である。

E-03では次を確定する。

- URL等から独立したstable Source Identity。
- Source 1件に0..N locatorを持たせる物理構造。
- Snapshot / Raw Artifact / Normalization Run / Evidenceの世代・Provenance chain。
- Source classificationとSource↔Object association metadataの分離。
- Source metadataのcaptured / deterministic / inferred / override provenance。
- Source間依存関係。
- Evidence location / extraction mode / content hash。
- Knowledge Statement / structured attribute / RelationからEvidenceへのgrounding link。
- `supports / contradicts / contextualizes` Evidence role。
- Source / Evidence ID存在確認とPackage membership validationへ利用できるstorage contract。

E-03ではeffective Snapshot / Runの選択アルゴリズム、Object Evidence Packageの最終schema、Version lifecycle、Object Result JSON Schemaを先取りしない。

---

## 2. 既存Prototype schemaとの共存方針

Migration 001には既に次のPrototype tableが存在する。

```text
sources
snapshots
artifacts
normalized_runs
evidence
```

ただし旧`sources`は`url UNIQUE`を持ち、B-03の「Source IdentityをURLから独立させる」契約と互換ではない。

SQLiteで既存tableを再構築してこの制約を除去すると、Phase Eのschema設計とPhase Lの実data migrationを同時に実施することになる。このためE-03では既存tableを書き換えない。

新canonical layerは次の別tableをadditiveに追加する。

```text
source_records
source_locators
source_snapshots
raw_artifacts
normalization_runs
normalization_run_artifacts
evidence_records
evidence_locations
```

旧Prototype tableはPhase Lまでreadableなまま残る。

### ID移行契約

新旧table名は異なるが、ID namespaceを意図的に別物とはしない。

Phase Lで旧recordをcanonical tableへ移す際は、可能な限り次をそのまま維持する。

```text
legacy sources.id        -> source_records.id
legacy snapshots.id      -> source_snapshots.id
legacy evidence.id       -> evidence_records.id
```

新schema導入だけを理由に既存IDを再発番しない。

同じTEXT IDが旧tableと新tableに一時的に共存しても、table namespaceが異なるため物理衝突しない。

---

## 3. 採用した全体構造

```text
Source Identity
  source_records
      |
      +-- 0..N source_locators
      +-- source_classifications
      +-- source_metadata_values
      +-- source_object_associations --> objects
      +-- source_relations --> source_records
      |
      +-- 0..N source_snapshots
              |
              +-- 1..N raw_artifacts
              |
              +-- 0..N normalization_runs
                      |
                      +-- normalization_run_artifacts --> raw_artifacts
                      |
                      +-- 0..N evidence_records
                              |
                              +-- 0..N evidence_locations
                              |
                              +-- evidence_links
                                   --> knowledge_statements
                                   --> object_version_attributes
                                   --> object_relations
```

KnowledgeからRawへは次の経路を辿る。

```text
Statement / Attribute / Relation
  -> Evidence Link
  -> Evidence
  -> Normalization Run
  -> Raw Artifact
  -> Snapshot
  -> Source
```

Evidenceは1つのSource chainだけに属し、複数Sourceを1 Evidence recordへ統合しない。

---

## 4. Source Identity

### `source_records`

Sourceそのもののstable Identityを保持する。

主要列:

- `id`: stable `source_id`
- `label`: nullableな人間向け表示名
- `status`: `active | archived`
- `created_at / updated_at`

Source recordはURL、path、title、content hash、site、Source classificationをIdentityとして要求しない。

Sourceはlocatorを1件も持たない状態でも存在可能である。例えばphysical referenceやlocator未確定の資料を先に登録できる。

### Source lifecycle

`archived`は通常利用対象から外す状態であり、Snapshot / Evidence履歴の破壊を意味しない。

Hard delete / retention policyはE-03で標準操作として定義しない。

---

## 5. Source Locator

### `source_locators`

取得・参照先はSource Identityから分離して0..Nで保持する。

主要列:

- `id`
- `source_id`
- `kind`
- `value`
- `is_preferred`
- `status`: `active | retired`
- `created_at / retired_at`

`kind`と`value`は閉じたURL専用schemaにしない。

想定例:

```text
kind=url
kind=canonical_url
kind=doi
kind=isbn
kind=repository
kind=local_reference
```

### Locator uniqueness

locator valueにglobal UNIQUEを置かない。

同一URLが異なる論理Source候補に一時的に登録されること、URLが後年別資料へ再利用されることを物理schemaで禁止しない。

同一性判断はURL一致だけで自動確定しない。

### Locator immutability

`source_id / kind / value`は登録後に書き換えず、変更時は旧locatorを`retired`として新locatorを追加する。

---

## 6. Snapshot

### `source_snapshots`

1 Sourceに対する1回の取得・観測を表す。

主要列:

- `id`: `snapshot_id`
- `source_id`
- nullable `observed_locator_id`
- `captured_at`
- `imported_at`
- `capture_method`
- `capture_tool / capture_version`
- `completeness`: `complete | partial | failed`
- `title`
- `manifest_json`
- `metadata_json`
- `warnings_json`
- `created_at`

`observed_locator_id`を指定する場合、そのlocatorは同じSourceへ属さなければならない。

### 時刻分離

`captured_at`と`imported_at`を別列とする。

Source publication / updated timeはSnapshot取得時刻とは別概念であり、Source metadataとして保持する。

### Snapshot不変性

Snapshotは観測履歴であるため、登録後のUPDATEを禁止する。

再取得・訂正されたCaptureは新Snapshotとして追加する。Source metadataの人間overrideはSnapshotそのものを書き換えず、後述metadata recordとして追加する。

同一hashでも別時点のCaptureを自動統合しない。

---

## 7. Source classification / metadata provenance

### `source_classifications`

Source本体に属する分類軸をrow形式で保持する。

初期axis:

```text
resource_type
media_type
document_genre
publisher_kind
site
page_purpose
```

axis集合はSource classificationの意味軸を固定するためのcontractである。一方、各axisの`value`は閉じたDB enumにせず、新しいgenre/provider等をschema変更なしで追加できる。

例:

```text
resource_type = web_page
media_type = text/html
document_genre = interview
publisher_kind = organization
site = wikipedia
page_purpose = character_profile
```

### `origin_kind`

分類値は次の由来を保持する。

```text
captured
deterministic
inferred
override
```

Snapshot由来値ならnullable `snapshot_id`で観測世代へbindできる。

Snapshotを指定したclassificationは同じSourceのSnapshotでなければならない。

### `source_metadata_values`

分類軸以外の書誌・記述metadataをkey + JSON valueで保持する。

想定例:

- creator / author表記
- publisher表記
- language
- published / updated time
- external identifier
- rights / license

こちらも`origin_kind`とnullable `snapshot_id`を持つ。

captured値をoverrideで上書き消去せず、別rowとして履歴を保持する。

`source_classifications`と`source_metadata_values`は観測recordとしてUPDATE禁止とし、訂正は新row追加で行う。

---

## 8. Source ↔ Object association

### `source_object_associations`

SourceがどのObjectに関連する資料かを多対多で保持する。

主要列:

- `source_id`
- `object_id`
- `status`
  - `candidate`
  - `confirmed`
  - `excluded`
- nullable `subject_relationship`
- `origin_kind`
- `note`
- timestamps

`subject_relationship`はSource本体の普遍属性ではなく、**そのSourceと特定Objectの組み合わせに依存するmetadata**である。

例えば同じSourceでも、Object Aに対して`first_party`、Object Bに対して`independent`となり得る。

association statusはPhase Fのretrieval / human confirmationで更新可能なため、Source observation rowとは異なりmutableとする。

Source↔Object associationは「このSourceが対象に関連する」ことを示すだけで、個別Knowledge claimの正しさを意味しない。claim groundingはEvidence Linkで行う。

---

## 9. Raw Artifact

### `raw_artifacts`

Snapshotから得た原資料単位を保持する。

主要列:

- `id`
- `snapshot_id`
- `artifact_kind`
- nullable `logical_path`
- `storage_ref`
- nullable `media_type`
- `sha256`
- `bytes`
- `created_at`

`storage_ref`は保存場所変更に対応する参照でありIdentityではない。このためstorage relocationに伴う`storage_ref`変更は許容する。

一方、Snapshot・artifact kind・logical path・media type・hash・bytes等の内容Identityは登録後に変更しない。

同一Snapshot内で同一logical artifact/hashを二重登録しないunique indexを持つ。

Raw content hashはintegrity / duplicate候補 / change detectionへ利用するが、SnapshotやSource Identityとして利用しない。

---

## 10. Normalization Run

### `normalization_runs`

Raw Artifactから検索・Evidence生成可能な構造へ変換した処理世代を表す。

主要列:

- `id`
- `snapshot_id`
- `extractor_key`
- `extractor_version`
- `configuration_json`
- `output_json`
- `status`: `complete | partial | failed`
- `created_at`

Extractor変更やconfiguration変更で再処理した場合は旧Runを更新せず新Runを追加する。

### `normalization_run_artifacts`

Runと実際に利用したRaw Artifactを明示する。

```text
run_id
artifact_id
role
```

DB triggerでRaw ArtifactがRunと同じSnapshotに属することを保証する。

E-03 canonical EvidenceはRaw Artifactへの実Provenanceを要求するため、Evidence生成時点でRunに最低1件のRaw Artifact linkが必要である。

### active / effective Run

Migration 001の`active_run`のようなselection概念はE-03では新canonical schemaへ固定しない。

最新Runが常に利用可能とは限らないため、effective Snapshot / Run selection policyはPhase Fで決定する。

---

## 11. Evidence

### `evidence_records`

Source中の情報を意味非改変で検索・引用できる単位として保持する。

主要列:

- `id`: stable `evidence_id`
- `run_id`
- `snapshot_id`
- `source_id`
- `ordinal`
- `content`
- `content_hash`
- `extraction_mode`
- nullable `language`
- `metadata_json`
- `created_at`

### Extraction mode

初期語彙:

```text
verbatim
normalized
structured
transcribed
```

LLM synthesis / interpretation / generated summaryはEvidence modeに含めない。

### Provenance consistency

Evidenceは検索filterを効率化するため`run_id / snapshot_id / source_id`を冗長保持するが、DB triggerで次のchain一致を要求する。

```text
evidence.run_id
  -> normalization_runs.snapshot_id
  == evidence.snapshot_id
  -> source_snapshots.source_id
  == evidence.source_id
```

さらにRunにRaw Artifact linkが最低1件存在することを要求する。

これにより、存在するEvidence IDでもRawまで辿れないorphan Evidenceを新canonical layerへ生成できない。

### Evidence identity

`content_hash`はIdentityではない。

同じ文言が異なるSource / Snapshot / locationへ存在する場合は別Evidence IDを保持できる。

Extractor変更でEvidence境界が変わる場合、新Run上で新Evidence IDを発行する。旧Evidence IDを無理に再利用しない。

### Evidence immutability

Evidenceは生成後UPDATE禁止とする。

訂正・再抽出は新Normalization Run / Evidence generationとして追加する。

---

## 12. Evidence location

### `evidence_locations`

Evidenceから原資料内位置へ人間が戻れるよう、Source種別横断のlocation recordを別tableに保持する。

初期kind:

```text
dom_path
heading_path
block_order
page
section
time_range
dataset_record
json_path
image_region
metadata_field
other
```

`value_json`でSource種別に応じた構造を保持する。

例:

```json
{"path":"/html/body/main/p[1]"}
```

```json
{"page":42,"section":"3.2"}
```

```json
{"start_ms":120000,"end_ms":126500}
```

1 Evidenceに複数location rowを持てる。

Evidence locationもProvenanceの一部としてUPDATEせず、新Evidence generationで訂正する。

---

## 13. Source dependency

### `source_relation_types`

Source間の依存・再掲載関係をObject Relationとは別Registryで管理する。

初期seed:

```text
cites
quotes
derived_from
mirror_of
syndicated_from
transcript_of
reproduction_of
```

IDは固定Registry IDとする。

```text
source-relation:cites
```

### `source_relations`

Source AがSource Bへ依存していることが判明した場合に保存する。

不明なindependenceを推測で確定しないため`origin_kind`を保持する。

Source relation vocabularyをObject semantic Relation Registryと混同しない。

---

## 14. Evidence Role Registry

### `evidence_roles`

EvidenceがKnowledgeに対して果たす役割をfree textにせずRegistry化する。

初期seed:

```text
supports
contradicts
contextualizes
```

固定ID:

```text
evidence-role:supports
evidence-role:contradicts
evidence-role:contextualizes
```

role追加は既存IDを変更せずadditive migration / explicit Registry operationで行う。

Evidence roleはSource trust scoreではない。`supports`は「このKnowledge要素の根拠として使われている」ことを表し、世界で客観的に真であることを保証しない。

---

## 15. Evidence Link

### `evidence_links`

Versioned Knowledge要素からEvidenceへのgrounding edgeを保存する。

主要列:

- `id`
- `version_id`
- `target_kind`
- `target_id`
- `evidence_id`
- `role_id`
- `origin_kind`
- nullable `origin_ref`
- `created_at`

初期`target_kind`:

```text
statement
attribute
relation
```

DB triggerでtargetが指定`version_id`に実在することを検証する。

```text
statement -> knowledge_statements(id, version_id)
attribute -> object_version_attributes(id, version_id)
relation  -> object_relations(id, version_id)
```

これにより、Version AのStatementへVersion BとしてEvidence Linkを張ることはできない。

### FacetへのEvidence Linkを直接作らない理由

Facet自体は分類・分析状態のcontainerであり、主張単位ではない。

Facet `personality`全体にEvidence一覧を直接持たせると、どのEvidenceがどのStatementを支えるか不明になる。

そのためE-03では次を採用する。

```text
Facet
  -> Knowledge Statement
       -> Evidence Link
```

Object-level summaryもE-02で`facet_id=NULL`のKnowledge Statementとして表現できるため、summary groundingも同じEvidence Link contractを利用できる。

### Attribute / Relation

AI生成structured attributeとObject Relationは自然言語Statementを介さず直接Knowledge要素となるため、それぞれEvidence Link targetとして許可する。

---

## 16. Link生成来歴

Evidence Linkは`origin_kind`を持つ。

初期値:

```text
result_import
manual
migration
system
```

`origin_ref`には、将来Result artifact ID / import run ID等の追跡識別子を保持できる。

E-03ではResult artifact / import state machine自体はまだ設計しない。E-04 / E-05 / H-02からこのfieldを利用できるよう物理余地だけ確保する。

---

## 17. Package membership validation境界

B-04では標準ChatGPT workflowで、Resultが参照するEvidence IDは入力Package manifestに含まれなければならない。

ただしObject Evidence Package table / manifest JSON SchemaはPhase Gの責務であるため、E-03でPackageをcanonical DB tableとして先取りしない。

`SourceRepository`は次のvalidation primitiveを提供する。

```text
validate_source_references(source_ids)
validate_evidence_references(evidence_ids, package_evidence_ids=...)
```

`validate_evidence_references`は次を確認する。

1. Evidence IDがDBに存在する。
2. EvidenceからSource / Snapshot / Raw ArtifactまでProvenanceが成立する。
3. Package Evidence ID集合が与えられた場合、その集合内に含まれる。

したがってE-05 / H-01は、G-02で確定するmanifestのEvidence ID集合をこのprimitiveへ渡して、存在しないID・Package外IDをrejectできる。

Source IDをResult等で明示参照する場合は`validate_source_references`で存在確認できる。

---

## 18. Domain / storage responsibility

### `src/sgokb/domain/source.py`

SQLiteへ依存しないcontractを持つ。

- Source / locator lifecycle
- metadata origin
- association status
- Snapshot completeness
- Normalization status
- Evidence extraction mode
- Evidence role
- Evidence target kind
- Source / Snapshot / Evidence / Evidence Link / Provenance record

新domain codeは`domain/_prototype.py`へ依存しない。

### `src/sgokb/storage/source_repository.py`

SQLite connectionを受け取り、E-03 canonical Source / Evidence操作を担当する。

代表操作:

- Source作成 / locator追加
- Snapshot / Raw Artifact登録
- Source classification / metadata追加
- Source↔Object association更新
- Normalization Run作成
- Evidence / location登録
- Source dependency登録
- Evidence grounding link作成
- Evidence Provenance解決
- Source / Evidence reference validation

### `repository.py`

移行期間のfaçadeとして`source_store = SourceRepository(self.db)`を公開する。

旧Prototype Source/Evidence APIをE-03で削除・置換しない。

---

## 19. Canonical / derived / legacy境界

### E-03 canonical

```text
source_records
source_locators
source_snapshots
source_classifications
source_metadata_values
raw_artifacts
normalization_runs
normalization_run_artifacts
evidence_records
evidence_locations
source_object_associations
source_relation_types
source_relations
evidence_roles
evidence_links
```

### Legacy coexistence

```text
sources
snapshots
artifacts
normalized_runs
evidence
entity_evidence
page_contexts
```

これらはPhase Lまで旧Prototype compatibility用に残す。

### Derived / later layer

次はE-03 canonical Source/Evidence正本には含めない。

- Evidence FTS / Embedding index
- Object Evidence Package
- Drive export files
- Result JSON
- Markdown citation rendering

Search indexは再生成可能なderived layerとしてPhase I /既存retrieval移行で扱う。

---

## 20. Migration 006 boundary

Migration 006はadditive migrationである。

行うこと:

- canonical Source / locator / Snapshot / Raw / Normalization / Evidence schema追加
- Source classification / metadata provenance schema追加
- Source↔Object association追加
- Source dependency Registry / relation追加
- Evidence Role Registry追加
- Statement / Attribute / Relation -> Evidence Link追加
- Provenance integrity trigger追加
- provenance-bearing observation recordのimmutability guard追加

行わないこと:

- Migration 001 / 002を書き換える
- 旧Source / Snapshot / Evidence dataを自動copyする
- legacy `url UNIQUE`制約を破壊的に除去する
- `entity_evidence`を自動Evidence Linkへ変換する
- current/effective Snapshot / Runを自動選択する
- Evidence FTS / Embeddingを新tableへ移行する
- Object Result / Package tableを作成する

既存Prototype dataの意味migrationはPhase Lで行う。

---

## 21. Integrity contract

E-03でSQLite / storage layerが保証する主なinvariantは次である。

1. Source Identityはlocatorを必須としない。
2. locator valueをSource global identityとしてunique化しない。
3. Snapshotが参照するobserved locatorは同じSourceへ属する。
4. Snapshot-bound classification / metadataは同じSourceのSnapshotへ属する。
5. Snapshot observationは登録後UPDATEしない。
6. Raw Artifactのcontent identityは登録後変更しない。
7. Normalization Runが参照するRaw Artifactは同じSnapshotへ属する。
8. Evidenceのrun / snapshot / sourceは1本のProvenance chainとして一致する。
9. canonical Evidenceは最低1件のRaw Artifactへ辿れる。
10. Evidence content / provenance / locationは登録後UPDATEしない。
11. Source↔Object association statusとsubject relationshipはSource本体metadataから分離する。
12. Source dependency Relation TypeはObject Relation Type Registryから分離する。
13. Evidence roleはactive Registry entryを使用する。
14. Evidence Link targetは指定Knowledge Versionに所属するStatement / Attribute / Relationである。
15. Evidence Linkは存在するEvidence IDだけを参照する。
16. storage validationでEvidenceからRaw / Sourceまで追跡できる。
17. package Evidence集合が与えられた場合、集合外Evidenceをrejectできる。
18. Source ID明示参照の存在確認ができる。

意味品質・Source真実性・Evidence採用判断をこれらのconstraintだけで保証しない。

---

## 22. E-04以降へ残す事項

### E-04 — Complete

`docs/design/VERSIONING_SCHEMA.md`を正本としてMigration 007を追加し、candidate / accepted / abandoned lifecycle、base / Classification stale判定、Evidence Linkを含むaccepted Version contentのimmutability、current promotion / rollback、transaction / recovery、derived-state failure domainを確定した。

### E-05 — Complete

`docs/design/OBJECT_RESULT_JSON_SCHEMA.md`を正本として、Evidence reference + role、Package / base Version / Classification binding、`reported_view` attribution、Class / Facet / Attribute / RelationのResult参照契約を`sgokb.object-result/1.0`へ反映した。`collect_evidence_ids()`によりH-01から本章のEvidence存在 / Package membership / Provenance validation primitiveへ接続できる。

### Phase F

- 既存Capture / Import / Normalize pipelineをcanonical E-03 tablesへ接続
- legacy Source metadata best-effort mapping
- candidate / confirmed / excluded association operation
- effective Snapshot / Run selection
- Evidence chunk budget / overlap
- Evidence retrieval

### Phase G

- Object Evidence Package layout
- manifest schema
- package evidence membership record
- external export

### Phase H

- Result grounding validator
- Evidence reference / Package membership validation integration
- Import transaction

### Phase I

- canonical Evidence Search Representation / Embedding
- active/historical generation search scope

### Phase L

- existing Prototype Source / Snapshot / Raw / Run / Evidence data migration
- legacy ID preservation
- old `entity_evidence` mapping policy

---

## 23. Validation result

E-03では次を自動test対象とする。

- Sourceをlocatorなしで作成可能
- 同一locator valueを異なるSourceに登録可能
- Snapshot locatorのsame-Source constraint
- Source classification axis / metadata origin分離
- Source↔Object association status / subject relationship
- Raw ArtifactのSnapshot ownership
- Normalization Run / Raw Artifact same-Snapshot constraint
- Evidence -> Run -> Snapshot -> Source + Raw Artifact chain
- Snapshot / Evidence provenance immutability
- human-verifiable Evidence location
- Source dependency RegistryとObject Relation Registryの分離
- Statement / Attribute / Relation Evidence Link
- Evidence Link version isolation
- Evidence roles `supports / contradicts / contextualizes`
- Source reference existence validation
- Evidence existence / Package membership validation
- legacy and canonical Source table coexistence
- fresh DB Migration 006 integrity
- v1 Prototype DB upgrade時の既存record preservation

Validation baseline:

```text
schema migrations: 6
source relation types: 7
evidence roles: 3
PRAGMA integrity_check: ok
PRAGMA foreign_key_check: 0 rows
```

---

## 24. 結論

E-03により、Object Knowledgeの根拠をSource / Snapshot / Raw Artifact / Normalization Run / Evidenceへ遡れるcanonical physical contractが成立した。

Source IdentityはURLから分離され、Source classificationとObjectごとのsubject relationshipも別責務となった。Knowledge groundingはStatement / Attribute / Relationから具体的Evidence IDへEvidence Linkを張り、`supports / contradicts / contextualizes`の役割を保持する。

旧Prototype Source/Evidence tableは破壊せず共存させたため、既存IDとRaw履歴を保ったPhase L migrationが可能である。

E-04 / E-05も完了し、Phase Eに未完了Taskはない。次Taskは **`F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する`** とする。Phase F開始条件と既存ingestionとの差分は`docs/planning/PHASE_F_PREPARATION.md`を参照する。
