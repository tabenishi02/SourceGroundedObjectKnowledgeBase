# N-04P-02 Search Representation Sync

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-02 [P0] Search Representation同期経路を実装する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Implementation complete / Reference Workstation verification pending**

## 1. Scope

N-04P-02では、accepted current Object VersionからSearch Representationを生成し、Knowledge本文Lexical Searchを利用可能にするApplication境界を実装する。

このTaskではEmbedding / Vector Indexは生成しない。

```text
accepted current Version
  ↓
search_representation: pending / failed / stale
  ↓
DerivedSearchMaintenanceApplication
  ↓
SearchRepresentationBuilder
  ↓
Object overall / Facet / Statement representation + membership
  ↓
FTS trigger / lexical retrieval
  ↓
search_representation: ready
```

## 2. Implementation

追加:

- `src/sgokb/application_maintenance.py`
  - `DerivedSearchMaintenanceApplication`
  - `SearchRepresentationSyncResult`
  - `DerivedMaintenanceError`
  - `DerivedMaintenanceSupersededError`

公開transportやCLIが`SearchRepresentationBuilder`を直接呼ばないよう、Application boundaryを設けた。

### `sync_search_representation(object_id)`

1 Objectのcurrent accepted Versionを対象にする。

実行条件:

- `search_representation` derived stateが存在する。
- Objectにaccepted current Versionが存在する。
- derived state's `target_version_id`がcurrent Versionと一致する。

処理:

1. `(object_id, target_version_id, revision)`をsnapshotする。
2. すでに同revisionが`ready`ならidempotent no-opとして返す。
3. `SearchRepresentationBuilder.materialize_version()`でObject / Facet / Statement RepresentationとVersion membershipをmaterializeする。
4. 同revisionが依然currentの場合だけ`ready`へ遷移する。
5. builder失敗時は同revisionだけ`failed`へ遷移し、`last_error`を記録する。
6. 処理中にVersion promotion等でrevisionが進んだ場合、古いattemptは新revisionを`ready` / `failed`へ変更せず`DerivedMaintenanceSupersededError`とする。

Search Representation生成はsemantic runtimeを初期化しない。

## 3. Canonical / derived boundary

このserviceが変更してよいもの:

- `search_representations`
- `search_representation_fts`
- `knowledge_search_representation_memberships`
- `object_derived_states.search_representation`

変更してはならないもの:

- accepted Object Knowledge Version内容
- Object current pointer（service自身はpromotionしない）
- Evidence / Provenance
- `embedding` / `vector_index` derived artifact

Builder途中失敗で一部derived rowが生成されてもcanonical Knowledgeは変更しない。retryは既存content-addressed Representation / membershipを再利用する。

## 4. Current / historical behavior

新VersionがacceptedになるとVersion lifecycleが`search_representation` revisionを進め、new current Versionを`pending`へする。

その後syncすると:

- old accepted VersionのRepresentation membershipは保持する。
- new current Version用membershipを追加する。
- representation contentが同一なら既存Representation IDを再利用する。
-通常検索のcurrent scopeはnew Versionだけを対象とする。
- historical Version指定ではold membershipを引き続き利用できる。

## 5. Tests

追加:

`tests/test_n04p02_search_representation_sync.py`

必須ケース:

1. accepted Version直後は`pending`で、内容語Lexical Searchは未hit。
2. Application sync後、Object / Facet / Statement Representationが生成され`ready`になる。
3. 同じ内容語Lexical Searchが対象Objectへhitする。
4. `embedding` / `vector_index`はN-04P-02では`pending`のまま。
5. ready後の再実行はduplicate membershipを作らない。
6. builder failureは`failed + last_error`を記録し、accepted Knowledge/current Versionを維持する。
7. sync中にrevisionが進んだ場合、古いattemptは新revisionをreadyへできない。
8. v1→v2 current切替後もv1 historical membershipを保持し、同一contentのRepresentationをreuseする。

## 6. Reference Workstation verification

通常venvで実行する。

```powershell
python -m pytest tests/test_n04p02_search_representation_sync.py -q
python -m pytest tests/test_search_representation.py tests/test_hybrid_search.py -q
python -m pytest -q
python -m ruff check src/sgokb/application_maintenance.py tests/test_n04p02_search_representation_sync.py
python -m ruff format --check src/sgokb/application_maintenance.py tests/test_n04p02_search_representation_sync.py
git diff --check
```

Gate:

- N-04P-02 focused tests: 0 failed
- existing Search Representation / Hybrid Search regression: 0 failed
- full suite: 0 failed
- Ruff / format / diff check: PASS
- production canonical Knowledge contractを弱めない
- semantic runtime / network / cloudを要求しない

## 7. Completion update

Reference Workstation verificationがPASSしたら:

- 本書へ実測test結果を追記する。
- `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`を`N-04P-02 Complete / N-04P-03 Next`へ更新する。
- PR #39へ結果を反映する。

次Task:

`N-04P-03 [P0] Incremental Embedding同期経路を実装する`
