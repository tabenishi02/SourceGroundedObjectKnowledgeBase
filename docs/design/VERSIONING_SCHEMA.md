# Source Grounded Object Knowledge Base — Versioning Schema Design

更新日: 2026-10-12

- Task: `E-04 [P0] Versioningを設計する`
- Status: Complete
- Logical authority: `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- Prerequisites:
  - `docs/design/OBJECT_SCHEMA.md`
  - `docs/design/SEMANTIC_FACET_SCHEMA.md`
  - `docs/design/SOURCE_EVIDENCE_SCHEMA.md`
- Migration: `src/sgokb/migrations/007_versioning.sql`
- Domain contract: `src/sgokb/domain/version.py`
- Persistence: `src/sgokb/storage/version_repository.py`

## 1. 目的

本書は、E-01で導入した`object_versions`のIdentity skeletonを、SGOKBのcanonical Object Knowledge Version lifecycleへ拡張するE-04の物理設計正本である。

E-04では次を確定する。

- Object Knowledgeを上書きせずVersion追加で更新する方式。
- full Knowledge snapshotを標準Version単位とする方式。
- `candidate / accepted / abandoned` lifecycle。
- accepted Versionとcurrent Versionを分離する契約。
- `base_version_id`によるlineageとstale判定。
- candidate作成時のClassification snapshotとstale判定。
- Version番号とbranch / rollbackの意味。
- accepted / abandoned Version contentのimmutability。
- Statement / known attribute / RelationのEvidence grounding acceptance gate。
- current promotion / rollbackのtransaction boundary。
- process interruption / retry時にincomplete Versionをcurrentへしないrecovery contract。
- Search Representation / Embedding / Vector Index / rendering等のderived artifactをcanonical commitと別failure domainにする契約。
- pre-E-04 Versionを壊さずMigration 007へ移行する契約。

E-04ではObject Result JSON Schema、Package manifest、Result artifact/idempotency、Diff UI、Vector backendそのものは先取りしない。

---

## 2. 基本原則

### 2.1 VersionはObject Knowledgeのimmutable snapshotである

SGOKBのKnowledge更新は既存Versionの上書きではなく、新しいVersionの追加として行う。

```text
Object
  current -> Version 3

新ResultをImport
  -> candidate Version 4
  -> validation / acceptance
  -> current -> Version 4

Version 3は保持
```

accepted Versionの訂正は、そのVersionを書き換えず新Versionを作る。

### 2.2 acceptedとcurrentは別概念である

`accepted`は「canonical Knowledge Versionとして確定済み」であることを表す。

`current`は「そのObjectの通常参照先として現在選ばれているaccepted Version」である。

したがって、Version 1からVersion 3まで全てacceptedでありながら、currentだけVersion 3という状態を正常とする。

```text
v1 accepted historical
v2 accepted historical
v3 accepted current
```

rollbackしてcurrentをv1へ戻しても、v2 / v3を`superseded`や`rejected`へ変更しない。

このためE-04では`superseded` lifecycle stateを導入しない。

### 2.3 ResultとVersionを同一視しない

Object Resultは外部生成されたcandidate artifactである。

E-04の`candidate`は、Validation / Import処理によってSGOKB SQLiteへ構築中の**persisted Knowledge Version candidate**を表す。

```text
result.json
  -> E-05/H-01 validation
  -> H-02 import starts
  -> persisted candidate Version
  -> canonical acceptance
```

Result受領だけでVersionを作成・current化することはしない。

---

## 3. 既存`object_versions`を維持する理由

Migration 003の`object_versions`は次の最小骨格を持つ。

```text
id
object_id
version_number
created_at
```

Migration 004 / 006の多数のFKが既にこのtableを参照しているため、E-04でtable rebuildやrenameを行わない。

E-04は次の補助tableをadditiveに追加する。

```text
object_versions
  1:1 object_version_lifecycle
  1:1 object_version_classification_snapshots
  1:N object_version_additional_class_snapshots
  1:N object_version_events

objects
  1:N object_derived_states
```

これによりMigration 001〜006を書き換えず、E-01〜E-03のFK契約を維持する。

---

## 4. Version lifecycle

### `object_version_lifecycle`

主要列:

- `version_id`
- nullable `base_version_id`
- `state`
  - `candidate`
  - `accepted`
  - `abandoned`
- `snapshot_kind`
  - E-04では`full`のみ
- nullable `accepted_at`
- nullable `abandoned_at`
- `created_at`

### candidate

candidateはSQLite内に構築中のVersionである。

- Knowledge contentを追加・修正できる。
- currentにはできない。
- base / Classification preconditionを保持する。
- acceptance前にValidation / Reviewで問題が見つかれば修正またはabandonできる。

### accepted

acceptedはcanonical Knowledge Versionである。

- contentはimmutable。
- historicalでもacceptedのまま。
- current pointerの対象にできる。
- rollback targetにできる。

### abandoned

abandonedはcandidateを採用しないと確定したterminal stateである。

- currentにはできない。
- audit/history用途で保持する。
- contentもterminalとしてimmutableにする。

candidateからの状態遷移は次だけを許可する。

```text
candidate -> accepted
candidate -> abandoned
```

accepted / abandonedから他stateへの遷移は行わない。

---

## 5. Full snapshot semantics

### 5.1 初期標準はfull snapshotのみ

`object_version_lifecycle.snapshot_kind`はMigration 007では`full`だけを許可する。

patch / delta VersionはE-04標準契約に含めない。

Version N+1は、base Versionとの差分だけでなく、そのVersionで採用するKnowledge全体を保持する。

### 5.2 omissionの意味

full snapshotでVersion N+1に存在しないKnowledge要素は、Version N+1ではcarry forwardされていない。

ただし「Resultに書き忘れた」と「意図して削除した」をDBだけで判定することはできないため、silent omissionを安全な削除として自動解釈しない。

E-04の境界は次とする。

- accepted Versionはその時点の完全snapshotとして扱う。
- 過去VersionのKnowledgeは削除しない。
- candidateとbaseの差分からomissionを検出できる。
- FacetについてはE-02の`content / insufficient_evidence / not_applicable / not_analyzed`を利用し、「行がない」ことと意味状態を混同しない。
- 対象Classで期待されるFacet coverageやResult omissionの妥当性はE-05 / H-01でValidationする。
- destructive omissionのReview表示はH-04で行う。

したがって、E-04はfull snapshotの保存意味を確定するが、AI出力の省略を自動削除命令として扱うImporterは実装しない。

### 5.3 Diffは派生比較である

Diffをcanonical deltaとして保存しない。

```text
Diff(v3, v4)
  = immutable snapshot v3 と v4 の比較結果
```

Knowledge Statementのrow IDはVersionをまたぐsemantic identityではないため、Diffでは必要に応じてlocal key、Facet、typed attribute key、Relation endpoint/type、内容等から対応付ける。

最終Diff algorithm / UIはH-04の責務とする。

---

## 6. Version Identity / numbering / lineage

### 6.1 Persistent Version ID

Version IDはSGOKB側で`new_persistent_id()`を利用して発行する。

ChatGPT / Object Resultに永続Version IDを発行させない。

### 6.2 `version_number`

`version_number`はObject内の**Version作成順序を表すmonotonic ordinal**とする。

base Version番号 + 1という意味ではない。

例えば:

```text
v1 accepted
v2 accepted
v3 accepted current
rollback -> current=v1
new candidate -> v4, base=v1
```

となる。

これにより履歴を上書きせず、rollback後のbranchも表現できる。

abandoned candidateが存在すればVersion番号にgapが残ることも正常とする。番号再利用はしない。

### 6.3 `base_version_id`

`base_version_id`はcandidateを構築したときのKnowledge lineage / preconditionである。

- 初回Knowledge生成ではNULLを許容する。
- 更新candidateでは通常、作成時点の`objects.current_version_id`と一致する。
- 同一ObjectのVersionだけを参照できる。
- candidate作成後に変更しない。

baseはparent treeを表現できるため、rollback後に作成した新Versionも元のcurrentではなくrollback targetをbaseとして持てる。

---

## 7. Stale判定

### 7.1 base Version stale

candidate作成時とaccept時の両方でbase preconditionを確認する。

```text
candidate.base_version_id == object.current_version_id
```

候補A/Bを同じbaseから作り、Aを先にacceptした場合、Bはstaleとなる。

```text
base=v1
  candidate A
  candidate B

A accepted -> current=v2
B accept   -> reject stale
```

E-04ではstale candidateを自動merge / rebaseしない。

必要なら新しいcurrentをbaseに新candidateを作る。Result-levelの再分析・review方針はH-02 / H-04へ引き継ぐ。

### 7.2 Classification snapshot stale

E-02のFacet profile validationは「分析時点のClassification snapshot」を必要とするため、candidate作成時に次を固定する。

- Primary Class
- Additional Classes

candidate作成後にObject RegistryのClassificationが変更された場合、通常acceptをstaleとして拒否する。

一方、accepted Version確定後にObject Classificationが後日訂正されても、過去Versionのsnapshotを書き換えず、そのVersionをinvalidにしない。

これにより「現在のClassification訂正が歴史Versionを壊す」問題を防ぐ。

### 7.3 Package bindingとの境界

Package ID / manifest hash / schema version等のstale bindingはE-05 / G-02 / H-01でValidationする。

E-04が所有するpreconditionはcanonical Version側のbase / Classificationである。

---

## 8. Classification snapshot

Migration 007は次を追加する。

```text
object_version_classification_snapshots
object_version_additional_class_snapshots
```

candidate作成時のObject Registry classificationをコピーする。

これらはVersion Knowledgeの解釈条件であり、accepted / abandoned後はimmutable contentとして扱う。

Facet profile validationは現在のObject Registry classificationではなく、このVersion snapshotを利用できる。

---

## 9. Acceptance gate

E-04のDB acceptance gateは、Versionをcanonical current候補へ昇格する最低限の構造integrityを保証する。

### 9.1 current/base precondition

- candidateであること。
- candidate baseが現在のcurrentと一致すること。
- candidate Classification snapshotが現在のObject Classificationと一致すること。

### 9.2 Facet completenessの最低条件

`object_version_facets.status='content'`なら、最低1件のKnowledge Statementを要求する。

「contentなのに内容が0件」という矛盾をacceptedへ昇格させない。

対象Classに必要な全FacetがResultに存在するかはE-05 / H-01で確認する。

### 9.3 Evidence grounding

acceptedへ昇格するcanonical Knowledgeについて次を要求する。

- 全Knowledge Statementに最低1件のEvidence Link。
- `status='known'`のstructured attributeに最低1件のEvidence Link。
- 全Object Relationに最低1件のEvidence Link。

`insufficient_evidence / not_applicable / not_analyzed` Attribute/Facet自体にEvidenceを必須とはしない。

Package membership、Evidence provenance、Evidence roleの妥当性はE-03 storage primitive + E-05/H-01で確認する。

このDB gateは意味的真実性を保証するものではない。

---

## 10. Accepted / abandoned Version content immutability

### 10.1 immutable canonical content

terminal Versionについて、次のinsert / update / deleteをDB triggerで拒否する。

- Version identity / lifecycle metadata。
- Version Classification snapshot。
- Additional Class snapshot。
- `object_version_facets`。
- `temporal_scopes`。
- `knowledge_statements`。
- `object_version_attributes`。
- `object_relations`。
- `relation_temporal_scopes`。
- `evidence_links`。

これにより、accepted後にStatementだけを書き換えたり、Evidence groundingだけを差し替えたりできない。

訂正は新Versionで行う。

### 10.2 Version event

`object_version_events`はappend-only audit logである。

accepted後でもrollback等の後発eventを追加できるが、既存eventのUPDATE / DELETEは禁止する。

### 10.3 derived Search dataはimmutable Version contentではない

次は再生成可能なderived layerであり、accepted後にも生成・再生成可能である。

- `search_representations`
- `search_representation_memberships`
- Embedding
- Vector Index
- Markdown rendering

したがってSearch Representation membershipをVersion content immutability triggerの対象にしない。

canonical Knowledgeの不変性とderived rebuild可能性を分離する。

---

## 11. Current promotion transaction

### 11.1 candidate acceptance

`VersionRepository.accept_candidate()`は`BEGIN IMMEDIATE`を利用し、次を1 SQLite transactionで行う。

1. candidate / base / Classification precondition確認。
2. DB acceptance gate確認。
3. lifecycleを`accepted`へ遷移。
4. `objects.current_version_id`を新Versionへ切替。
5. derived stateを新target Versionの`pending`へ更新。
6. acceptance event追加。
7. COMMIT。

途中で失敗した場合、transaction全体をrollbackする。

したがって、

```text
Versionだけaccepted
currentだけ旧Version
```

または

```text
currentがcandidate/incomplete Versionを指す
```

という半端な状態を通常operationから生成しない。

### 11.2 current pointer制約

`objects.current_version_id`は次だけを指せる。

- 同じObjectに属する。
- lifecycle stateが`accepted`。

candidate / abandoned Versionをcurrentへ直接設定できない。

---

## 12. Rollback

rollbackはKnowledge contentを書き戻す処理ではなく、current pointerを過去のaccepted Versionへ切り替える操作である。

```text
v1 accepted
v2 accepted
v3 accepted current

rollback(v1)

v1 accepted current
v2 accepted historical
v3 accepted historical
```

`VersionRepository.rollback_current()`は次を1 transactionで行う。

- targetが同一Objectのaccepted Versionであることを確認。
- current pointerをtargetへ変更。
- derived stateをtarget Versionのpendingへ更新。
- rollback eventをappend。

Version content / lifecycle stateは変更しない。

rollback後に新Knowledgeを作る場合は、rollback targetをbaseとした新しいVersionを発行する。

---

## 13. Candidate abandon / retry / interruption

### 13.1 candidate構築中のprocess interruption

candidate作成後にprocessが停止しても、candidateはcurrentではない。

そのためcanonical current Knowledgeは失われない。

再起動後はcandidateを検査して、次のいずれかを行える。

- resume / continue construction。
- abandon。
- 新candidateを作る。

candidate自動削除はE-04標準operationにしない。

### 13.2 acceptance transaction中のinterruption

SQLite transactionがcommit前に失敗すれば、acceptance / current pointer変更 / derived state更新をrollbackする。

currentがincomplete Versionを指す状態を残さない。

### 13.3 retry

Version lifecycle operationは自分でtransaction boundaryを所有する。

既に外側transactionが開いている状態で呼び出すことを拒否し、partial nested transaction semanticsを避ける。

Result artifactのduplicate Import/idempotency keyはH-02で確定する。

---

## 14. Derived artifact failure domain

### `object_derived_states`

canonical Version acceptanceと、後続のSearch / Embedding / Vector / rendering生成を同一transactionへ含めない。

E-04ではObjectごとのderived target状態を次のtableで管理する。

```text
object_id
kind
target_version_id
status
revision
last_error
updated_at
```

初期status:

- `pending`
- `ready`
- `failed`
- `stale`

初期kind contract:

- `search_representation`
- `embedding`
- `vector_index`
- `rendering`

### 14.1 canonical commitとderived generationの分離

acceptance transactionでは実際のEmbedding計算やVector Index更新を実行しない。

新currentへ切り替えたらderived stateだけを`pending`へ更新し、実処理はcommit後の別failure domainで行う。

したがってVector backend障害が起きてもaccepted canonical Knowledgeをrollbackしない。

### 14.2 revision token

同じObject/kindが新しいVersionへretargetされるたび`revision`を増やす。

workerが処理開始時のrevisionを保持し、完了報告時にcompare-and-setする。

これにより古いVersion向けworkerが後から完了しても、新currentのstateを誤って`ready`へできない。

```text
revision 1 -> v1 processing
accept v2
revision 2 -> v2 pending
late worker(revision 1) -> update rejected
```

### 14.3 stale / fallback

derived stateが`pending / failed / stale`の場合にSearch / MCPがどうfallbackするかはPhase I / J / Nで具体化する。

少なくともcanonical current Versionとderived target Versionを比較できるため、古いIndexをsilent currentとして扱わない設計が可能である。

---

## 15. Search Representation / Vector reuse境界

E-02で`search_representations`本体とVersion membershipを分離済みである。

同じbuilder / builder version / content hashならrepresentation本体を再利用できる。

E-04では次を維持する。

```text
representation content identity
  !=
Version membership/currentness
```

同じrepresentationや将来同じEmbedding vectorを再利用しても、各Versionのmembershipを保持し、通常Searchのcurrent/historical scopeは`objects.current_version_id`を基準に判定する。

Vector reuse条件の最終定義はPhase IでEmbedding Spaceを含めて確定する。

---

## 16. Migration 007 compatibility / backfill

Migration 007はadditive migrationである。

既存Migration 001〜006を書き換えない。

### 16.1 pre-E-04 Version

Migration 007適用前に存在した`object_versions`は、既に永続Knowledgeとして利用されていた可能性があるためcandidateへ降格しない。

全て`accepted`としてbackfillする。

- `accepted_at = object_versions.created_at`
- `snapshot_kind = full`
- baseは同一Objectで直前の`version_number`をbest-effort lineageとして設定。
- Classification snapshotはmigration時点のObject Registry classificationを記録。

これはE-04以前に存在しなかった履歴情報を完全再現するものではなく、既存dataを壊さないcompatibility migrationである。

### 16.2 E-01〜E-03 low-level insert compatibility

既存test / migration helperが4列`object_versions`へ直接INSERTしても、Migration 007のAFTER INSERT triggerがcandidate lifecycle / base / Classification snapshotを自動作成する。

新しいapplication codeでは`VersionRepository.begin_candidate()`を使用する。

---

## 17. Domain / storage responsibility

### `src/sgokb/domain/version.py`

SQLite非依存contract:

- `VersionState`
- `DerivedState`
- `StaleVersionError`
- Version Classification snapshot
- Object Version record
- Derived state record

### `src/sgokb/storage/version_repository.py`

Version lifecycle operationを担当する。

代表操作:

- `begin_candidate()`
- `version_by_id()`
- `versions_for_object()`
- `accept_candidate()`
- `abandon_candidate()`
- `rollback_current()`
- `derived_states()`
- revision付き`mark_derived_state()`

既存`Repository`は移行期間façadeとして`version_store`を公開する。

---

## 18. E-04で意図的に決めない事項

### E-05 — Complete

`docs/design/OBJECT_RESULT_JSON_SCHEMA.md`で`sgokb.object-result/1.0`のObject Result最終JSON Schemaを確定した。Package / base Version / Classification binding、Facet profile completeness、Evidence reference、reported-view attribution、conflict / gap / unresolved reference / Registry proposal、partial / insufficient evidenceのexchange shapeをSchema化済みである。

### H-01

- Schema validation後のObject / Class / Facet / Attribute / Relation Type実在確認。
- Package manifestとのbinding / hash / Evidence membership照合。
- E-03 storage primitiveを利用したEvidence Provenance integrity確認。
- schema適合と意味品質を分離したResult Validator orchestration。

### H-02

- original Result artifact保存table/hashの最終形。
- duplicate Result Import / idempotency key。
- Result artifactからcandidateを構築するImporter orchestration。
- partial Result explicit acceptance workflow。

### H-04

- semantic Diff algorithm。
- destructive omission Review UI。
- stale / Registry proposal表示。

### Phase I

- Search Representation builder実装。
- Embedding Space。
- Vector backend。
- actual background job implementation。
- derived fallback policy。

---

## 19. Integrity contract

Migration 007 / VersionRepositoryが保証する主なinvariantは次である。

1. Versionは1 Objectへ属し、ownerを後から変更しない。
2. Version番号はObject内で一意。
3. base Versionは同一Objectへ属する。
4. baseはcandidate作成後に変更しない。
5. current pointerは同一Objectのaccepted Versionだけを指す。
6. candidateだけがaccepted / abandonedへ遷移できる。
7. accepted / abandoned lifecycleはterminal immutable。
8. accepted / abandoned Version contentを後から変更しない。
9. Version Classification snapshotをterminal後に変更しない。
10. accept時にbaseがcurrentと一致する。
11. accept時にClassification snapshotがcurrent Registry classificationと一致する。
12. `content` Facetは最低1 Statementを持つ。
13. accepted Statement / known Attribute / RelationはEvidence Linkを持つ。
14. acceptance + current promotion + derived target updateは1 transaction。
15. rollbackはaccepted targetへのcurrent pointer移動だけであり、Version content/stateを変更しない。
16. derived generation failureはcanonical acceptanceを無効化しない。
17. derived workerはrevision tokenで旧targetのlate completionを上書きできない。
18. pre-E-04 VersionはMigration 007でacceptedとして保全する。

---

## 20. Validation result

E-04で追加した主なtest:

- initial candidate / first acceptance。
- current pointerのaccepted-only制約。
- concurrent candidate stale rejection。
- Classification変更によるcandidate stale rejection。
- ungrounded Statement / known Attribute rejection。
- content Facet without Statement rejection。
- accepted Statement / Evidence Link immutability。
- v1→v2→v3後のv1 rollback。
- rollback後の`v4 / base=v1` branch。
- derived state pending / ready / failedとrevision CAS。
- abandoned candidate terminal behavior。
- Migration 001〜006 DBからMigration 007へのbackfill。

Validation baseline:

```text
schema migrations: 7
PRAGMA integrity_check: ok
PRAGMA foreign_key_check: 0 rows
E-04 focused regression: 47 passed
full test suite: 122 passed
ruff: passed
compileall: passed
CLI help smoke: passed
```

---

## 21. 結論

E-04により、SGOKBのObject Knowledgeは**full immutable Version snapshot + explicit current pointer**として管理できるようになった。

重要な決定は、acceptedとcurrentを分離したことである。過去Versionはaccepted履歴として残り、rollbackはKnowledgeを書き換えずcurrent pointerだけを戻す。新Versionのlineageは`base_version_id`で追跡し、Version番号はObject内の作成順序とするため、rollback後のbranchも履歴破壊なしで表現できる。

accepted VersionはStatement / Attribute / Relation / temporal scope / Evidence Link / Classification snapshotを含めてimmutableとなり、canonical acceptanceとcurrent切替は1 SQLite transactionで行う。一方、Search Representation / Embedding / Vector Index / renderingは独立したderived failure domainとし、失敗してもcanonical Knowledgeを失わない。

E-05も完了し、Phase Eに未完了Taskはない。次Taskは **`F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する`** とする。Phase F開始準備は`docs/planning/PHASE_F_PREPARATION.md`を正本とする。
