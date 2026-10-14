# L-03 Canonical DB Clean Rebuild Policy

更新日: 2026-10-15

- Status: Accepted
- Task: `L-03 [P1] 既存Prototype DB migrationを設計する`
- Effective interpretation: **existing Prototype DBをdata migrationせず破棄し、canonical DBをclean rebuildする方式を設計する**
- Baseline: `4efebb0`
- Related:
  - `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`
  - `docs/decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md`
  - `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
  - `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`
  - `docs/planning/PHASE_L_PREPARATION.md`

---

## 1. Decision

SGOKBはPrototype DBからcanonical DBへのrow-level data migrationを行わない。

> **2026-10-14のruntime auditでproduction移行対象dataが存在しないことを確認したため、既存Prototype / evaluation DBはcanonical data sourceとして利用せず破棄する。`sample/` Raw Capture corpusは保持する。fresh canonical DBはPrototype migration 001/002を適用せず、canonical migration 003〜016をactive bootstrapとして新規構築する。**

この判断はpre-production段階に限る一度限りのresetであり、production data蓄積後の一般的なmigration policyではない。

---

## 2. 背景

現行`Repository.migrate()`は`src/sgokb/migrations/*.sql`を番号順に全適用する。

現在のmigration chainは次の2層を含む。

```text
001-002  Prototype schema / High Recall Fragment / Final / benchmark
003-016  canonical Object / Facet / Source-Evidence / Version / Exchange / Search
```

001/002を残したままfresh DBを作ると、L-01/L-02でDelete対象と確定したFragment / Final等のlegacy tableが再生成される。

一方、003以降はPhase E〜Iで構築したcanonical schema migrationであり、現在のstandard workflowが依存する。

---

## 3. Runtime auditによる前提

2026-10-14の実機調査で次を確認した。

- `.local/sgokb.sqlite`に保存すべきproduction rowsは存在しない。
- `evaluation.sqlite` / `extraction-fix-verification.sqlite` / `upgrade.sqlite`は`sample/` corpusを使う評価用DBである。
- `i07-search-gold.sqlite`はsynthetic benchmark dataである。
- `sgokb-capture-acceptance.sqlite`はacceptance用dataである。
- production Source / Evidence / Object Knowledgeとしてmigrationすべきrowは確認されなかった。
- `sample/` Raw Capture corpusはDBから独立して保持可能である。

したがって、ID continuity / row conversion / Fragment provenance preservationを目的とするmigrationは不要である。

---

## 4. Active migration chain

### 4.1 001/002をactive bootstrapから除外する

次はactive production bootstrapへ適用しない。

```text
001_initial.sql
002_knowledge_capture.sql
```

これらをclean schema用に書き換えない。

Phase L cleanup時にはactive packageから削除し、必要な歴史的確認はGit historyを使用する。別のruntime-compatible archive migration chainは維持しない。

### 4.2 003〜016をcanonical migration chainとして維持する

active bootstrapは次から開始する。

```text
003_object_schema.sql
004_semantic_facets.sql
005_facet_taxonomy_freeze.sql
006_source_evidence_schema.sql
007_versioning.sql
008_source_effective_selection.sql
009_evidence_retrieval.sql
010_package_exchange_audit.sql
011_result_receipts.sql
012_result_validation.sql
013_object_version_import.sql
014_search_representations.sql
015_embedding_spaces.sql
016_hybrid_search.sql
```

これらは既にPhase E〜Iで実装・検証されたcanonical migrationであるため、L-03では番号を振り直さない。

### 4.3 migration番号は3から始まってよい

fresh canonical DBの`schema_migrations`は原則として、

```text
3, 4, 5, ..., 16
```

を持つ。

`1` / `2`が存在しないことは欠損ではなく、Prototype epochをactive bootstrapから除外したことを表す。

future migrationは既存番号を再利用せず`017_...`以降を使用する。

### 4.4 新しい巨大baseline SQLへsquashしない

L-03では003〜016を1本の巨大な`001_canonical_baseline.sql`へ手作業でsquashしない。

理由:

- trigger / index / seed dataの転記漏れリスクを避ける。
- 005のtaxonomy freeze等、既に検証されたseed処理を維持する。
- 014はE-02時代のderived Search tableを意図的に再構築するmigrationであり、その履歴を保つ方が安全である。
- 既存tests / design docsとの対応関係を維持できる。

将来、正式Release後にschema snapshot / baseline consolidationが必要になった場合は別Taskとして扱う。

---

## 5. Prototype schema exclusion

fresh canonical DBに次の001由来table / FTS / index surfaceを作成しない。

```text
sources
snapshots
artifacts
normalized_runs
evidence
entities
entity_relations
entity_evidence
ai_runs
fragment_runs
fragments
fragment_evidence
search_items
search_fts
embedding_spaces
embeddings
documents
```

次の002由来tableも作成しない。

```text
page_contexts
extraction_jobs
extraction_batches
evidence_assessments
entity_candidates
structured_documents
ai_observations
benchmark_runs
benchmark_cases
```

L-01/L-02のDecisionに従い、Fragment / Final rowsをcanonical tableへ変換しない。

---

## 6. Canonical schema families to preserve

fresh DBは少なくとも次のcanonical familyを持つ。

### Object / classification

```text
object_classes
object_class_parents
objects
object_versions
object_aliases
object_additional_classes
relation_types
object_relations
object_registry_events
object_class_proposals
```

### Facet / semantic Knowledge

```text
facet_definitions
class_facet_profiles
object_version_facets
temporal_scopes
knowledge_statements
attribute_definitions
object_version_attributes
relation_temporal_scopes
```

### Source / Evidence / Provenance

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
```

および006以降で定義されたEvidence Link / Provenance関連canonical tableを保持する。

### Version / import / exchange

007〜013で定義された、

- Object Version lifecycle
- classification snapshot
- derived state
- Package / export audit
- Result receipt
- validation
- Object Version import provenance

を保持する。

### Search / Embedding

```text
search_representations
knowledge_search_representation_memberships
evidence_search_representation_memberships
search_embedding_spaces
search_representation_embeddings
search_representation_fts
```

014で提供するread-only compatibility view `search_representation_memberships`は、canonical Search内部互換surfaceとして現時点では保持する。

---

## 7. Existing DB compatibility policy

### 7.1 in-place upgradeを提供しない

Prototype DBに対し、

```text
001/002 schema
  -> canonical schema
```

のin-place conversion pathは提供しない。

次も作らない。

- legacy ID mapping table
- Fragment → Statement converter
- Entity → Object automatic converter
- Final Document → Object Result parser
- permanent legacy read-only DB adapter

### 7.2 Prototype DBをfail-fastで拒否する

active bootstrap切替時、`Repository`は既存DBの`schema_migrations`に`1`または`2`が存在する場合、silentに継続利用してはならない。

実装時はmigration開始前にPrototype DBを検出し、明示的なerrorで停止する。

例:

```text
LegacyPrototypeDatabaseError:
This database belongs to the pre-canonical Prototype epoch.
Create a fresh canonical database instead of upgrading it in place.
```

このguardはold DBを誤ってproduction DBとして使い続けることを防ぐ。

### 7.3 old DBへcleanup migrationを自動適用しない

Prototype DBを開いた際に自動でDROP TABLEする設計は採用しない。

理由:

- destructive side effectを起動時に隠さない。
- L-04でbenchmark salvageが必要になる可能性がある。
- clean rebuildというDecisionを明確に保つ。

---

## 8. Runtime DB disposal policy

### 8.1 deletion対象

runtime auditでproduction正本ではないと確認したSQLite DBは、L-04のbenchmark salvage gate通過後に削除可能とする。

対象例:

```text
.local/sgokb.sqlite
.local/evaluation.sqlite
.local/extraction-fix-verification.sqlite
.local/upgrade.sqlite
.local/sgokb-capture-acceptance.sqlite
.local/i07-search-gold.sqlite
.local/i03_backend_work/*.sqlite
sample/配下のevaluation / probe SQLite DB
```

実削除時はSQLite本体だけでなく対応する`-wal` / `-shm`も対象にする。

### 8.2 L-04 gate

`evaluation.sqlite` / `upgrade.sqlite`等を物理削除する前に、L-04で歴史資料として具体的価値があるbenchmark結果がDBにしか存在しないか確認する。

保存価値がある場合もDB全体をarchiveせず、必要最小限の結果・条件・manifestを文書または静的artifactとして退避する。

### 8.3 RawはDB cleanupと分離する

L-03ではRaw Captureを削除対象にしない。

特に、

```text
sample/
```

のWeb Capture corpusはExtractor / ingestion回帰試験用として保持する。

DB削除を理由にRaw Artifactを連動削除しない。

---

## 9. Fresh DB bootstrap contract

clean bootstrapは次の手順を標準とする。

```text
1. new empty SQLite pathを用意
2. schema_migrationsを初期化
3. active migration 003〜016を番号順に適用
4. canonical seed / taxonomyを適用
5. integrity checks
6. canonical smoke tests
```

L-03ではphysical runtime pathの全面再設計は行わない。

現在のCLI default `.local/sgokb.sqlite`を`.local/canonical/db/...`へ変更するかはPhase M / operations設計と分離する。

---

## 10. Validation contract

clean rebuild実装時は最低限次を確認する。

### 10.1 schema migration

- `schema_migrations`に`3..16`が存在する。
- `1` / `2`は存在しない。
- 001/002由来legacy tableが存在しない。
- canonical 003〜016 schemaが存在する。

### 10.2 SQLite integrity

```sql
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

期待値:

```text
integrity_check = ok
foreign_key_check = 0 rows
```

### 10.3 canonical workflow smoke test

少なくとも次をfresh DBで確認する。

```text
Sample Raw import
 -> canonical Source / Snapshot
 -> Normalize / Evidence
 -> Object
 -> Object Evidence Package
 -> Result Validation / Import
 -> accepted Object Version
 -> Search Representation / Embedding
 -> Search / Similarity
 -> MCP read
```

外部ChatGPT手動工程そのものはDB bootstrap testに必須ではなく、既存fixture Resultで代替可能とする。

### 10.4 negative test

Prototype DB fixtureを新runtimeで開いた場合、migration継続ではなくfail-fastすることを確認する。

---

## 11. Test / fixture policy

### Keep

- `sample/` Raw corpus
- canonical Source / Evidence fixtures
- Object / Version / Result fixtures
- Search quality gold
- current Embedding / Vector backend benchmark fixture

### Remove or rewrite

- 001/002 table存在を前提にするtests
- Fragment / Final persistence tests
- `documents` / `structured_documents` count assertion
- legacy migration upgrade test
- legacy CLIによるDB生成を前提とするfixture

Prototype historyの再現を目的とするtest suiteはactive CIへ残さない。

---

## 12. Implementation boundary

L-03はclean rebuild方式の設計を確定するTaskである。

実際のcleanupはPhase Lの後続作業と分担する。

### L-04

- legacy benchmarkのarchive / delete判断
- DB削除前のbenchmark salvage gate

### L-05

- 001/002をactive packageから除去
- Prototype DB fail-fast guard実装
- Fragment / Final code / Prompt / CLI / Repository surface削除
- legacy tests / scripts整理
- clean bootstrap regression追加

DBの物理削除はL-04 gate通過後、L-05 cleanupと同じ変更セットまたは直後のoperator cleanupとして実施する。

この順序により、L-03のdestructive designを確定しつつ、歴史的benchmark情報を確認前に失わない。

---

## 13. Rejected alternatives

### A. 017でlegacy tableをDROPする

不採用。

fresh DBで毎回001/002の不要schemaを作成してから削除することになり、active bootstrapにPrototype schemaを残す。

### B. 001/002をclean schemaへ書き換える

不採用。

historical migrationの意味を改変し、過去commit / DBとの対応を不明瞭にする。

### C. 003〜016を新001へsquashする

現時点では不採用。

canonical migrationで検証済みのtrigger / seed / Search再構成を手作業で再構築するリスクが高い。

### D. old DBをread-only archiveとして恒久保持する

不採用。

production移行対象dataがなく、ユーザー方針として不要なlegacy runtime dataを保持しないため。

### E. Sample Rawも同時に削除する

不採用。

DBとは独立したExtractor / ingestion regression valueがあるため。

---

## 14. Consequences

### Positive

- fresh production DBへFragment / Final / Prototype search tableを持ち込まない。
- row migration logicが不要になる。
- current canonical workflowだけを対象にschemaを理解できる。
- Sample Rawは再import可能な回帰資産として維持できる。
- historical Prototype implementationはGitで確認できる。

### Breaking change

- 001/002を適用済みのDBは新runtimeで直接開けない。
- Prototype DBからのautomatic upgradeは存在しない。
- legacy CLI / testsはcleanup後に利用できなくなる。

これはPhase Lで意図したpre-production compatibility breakである。

---

## 15. Definition of Done

- [x] production row migrationを行わないと確定した。
- [x] `sample/` Raw corpusを保持すると確定した。
- [x] 001/002をactive bootstrapから除外すると確定した。
- [x] canonical migration 003〜016を番号変更せずactive chainとして維持すると確定した。
- [x] future migrationは017以降とすると確定した。
- [x] Prototype DBをfail-fastで拒否すると確定した。
- [x] old DBへautomatic destructive migrationを行わないと確定した。
- [x] legacy table absence / SQLite integrity / canonical workflow smoke testをacceptance条件とした。
- [x] physical DB deletion前にL-04 benchmark salvage gateを置いた。
- [x] implementation cleanupをL-05へ引き継いだ。

**L-03 design: Complete.**

Next:

```text
L-04 [P1] 旧benchmarkをarchive / deleteする
```
