# N-04P-04 Vector Index同期 / rebuild

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-04 [P0] Vector Index同期 / rebuild経路を完成させる`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Implementation complete / Reference Workstation verification pending**

## 1. Scope

N-04P-02 / P-03で成立した次の依存をVector backendまで完成させる。

```text
accepted current Version
  ↓
search_representation = ready
  ↓
embedding = ready (selected Embedding Space)
  ↓
Vector Index incremental sync / full rebuild
  ↓
vector_index = ready
  ↓
Semantic / Hybrid / Similarity retrieval
```

P-04はPublic CLI orchestrationを追加しない。CLI / operator-visible statusはP-05で実装する。

## 2. 実装

### 2.1 Application boundary

`DerivedSearchMaintenanceApplication`へ次を追加した。

```text
sync_vector_index(object_id)
rebuild_vector_index()
```

Vector runtimeは明示的に注入された次の2要素から構成する。

```text
Embedding Space
VectorIndexAdapter
```

Embedding ProviderはP-04の必須依存ではない。Providerを注入している場合は`provider.space`を選択Spaceとして利用できるが、Vector sync / rebuild自身はEmbedding生成を行わない。

runtime未構成時は`DerivedMaintenanceRuntimeUnavailableError`とし、`vector_index` stateを変更しない。

### 2.2 Incremental Object sync

`sync_vector_index(object_id)`は以下を要求する。

- Objectにcurrent accepted Versionが存在する。
- `search_representation.target_version_id == current_version_id`。
- `search_representation = ready`。
- `embedding.target_version_id == current_version_id`。
- `embedding = ready`。
- `vector_index.target_version_id == current_version_id`。

対象Objectについて、currentだけでなく**全accepted Versionのmembership point**を再upsertする。

理由:

Version promotion後、旧Versionのpointはmembership ID自体は残す必要があるが、metadataの

```text
is_current=true
```

を

```text
is_current=false
```

へ更新しなければならない。新current Version membershipは`is_current=true`で追加する。

したがってincremental sync単位は「current Versionだけ」ではなく「1 Objectのaccepted membership集合」とする。

### 2.3 Missing Embedding

Object accepted membershipに必要なEmbeddingがselected Spaceで不足している場合、Vector syncは明示的にfailureとする。

```text
Vector Index sync requires embeddings ... missing=N
```

P-04が暗黙にEmbeddingを生成することは禁止する。

同revisionの実attempt failureなので、対象Objectの`vector_index`は`failed + last_error`となる。

canonical Knowledge / accepted Version / current pointerは変更しない。

### 2.4 revision guard

Vector sync開始時に以下をsnapshotする。

- search representation revision
- embedding revision
- vector index revision
- current Version

backend write後にSearch Representation / Embedding依存が同じcurrent target・revision・ready状態であることを再確認する。

途中でVersion promotion等が発生した場合、旧attemptは新revisionを`ready / failed`へ変更できない。`last_error`も新revisionへ持ち越さない。

backend側に旧attemptのpointが残ってもcanonical stateではなく再構築可能derived artifactなので、次回sync/rebuildで修復する。

### 2.5 Full rebuild

`rebuild_vector_index()`はSQLiteに残る全accepted Knowledge membershipと、selected Spaceに保存済みのEmbeddingからbackendを全再構築する。

```text
SQLite Search Representation membership
+
SQLite Embedding cache
→ VectorIndexAdapter.rebuild()
```

Embedding不足は明示failureで、Embedding生成へfallbackしない。

backend rebuild前後でaccepted Object catalog / derived revision snapshotを比較し、途中でVersion promotion等が起きた場合は`DerivedMaintenanceSupersededError`とする。

catalogが安定している場合だけ、次を満たすObjectの`vector_index`をrevision guard付きでreadyへする。

- Search Representation target=current、ready
- Embedding target=current、ready
- Vector target=current

### 2.6 Vector builder responsibility

`KnowledgeVectorMaintenanceBuilder`を追加した。

役割:

- Object accepted membership point生成
- Object単位upsert
- global backend rebuild
- canonical metadata projectionの再利用

既存Phase Iのpoint metadata contractを再利用するため、Class / Facet / Statement / temporal / current-historical metadataの意味を変更しない。

公開`sgokb.retrieval.KnowledgeVectorIndexBuilder`はこのlifecycle-neutral builderを指すよう変更した。

したがって既存

```text
sgokb system index rebuild
```

が呼ぶ`KnowledgeVectorIndexBuilder.rebuild()`は、P-04以降**Vector backendのみをrebuildし、object_derived_statesを直接ready化しない**。

これはP-01で確定した「BuilderではなくApplicationがrevision-guarded lifecycleを所有する」contractに合わせる変更である。

Public CLIから安全にderived stateまで進める経路はP-05で追加する。

## 3. 新しいResult

### `VectorIndexSyncResult`

```text
object_id
version_id
revision
space_id
backend_key
point_count
written_point_count
changed
state
```

### `VectorIndexRebuildResult`

```text
space_id
backend_key
point_count
ready_object_count
state
```

## 4. Failure boundary

P-04でVector backend failureが起きても次は変更しない。

- Object Registry
- accepted Knowledge
- current Version pointer
- Evidence / Provenance
- Search Representation
- Embedding cache

Object incremental syncの実failureだけ対象`vector_index` revisionをfailedへする。

full rebuild failureはglobal recovery operationの失敗として例外を返し、個別Objectを一括failedへ落とさない。

## 5. Focused test

追加:

```text
tests/test_n04p04_vector_index_sync.py
```

主要ケース:

1. Vector runtime未構成 → pending維持。
2. Embedding未ready → backend未書込。
3. current Versionのmembership pointをupsertしてready。
4. v1→v2でv1 historical point保持、`is_current=false`へ更新、v2を`true`で追加。
5. historical Embedding欠落を明示failure。
6. backend upsert failureでcanonical Knowledge不変。
7. superseded成功終了 / 失敗終了の両経路で新revisionを汚染しない。
8. fresh backend full rebuildで全membershipを復元。
9. rebuild後Semantic Search / Similarityが利用可能。
10. full rebuild時のEmbedding不足でreadyへ昇格しない。

## 6. Reference Workstation verification gate

実装完了だけではP-04 Completeにしない。

最低限次を通常venvで実行する。

```powershell
python -m pytest tests/test_n04p04_vector_index_sync.py -q
python -m pytest tests/test_hybrid_search.py tests/test_similarity.py tests/test_vector_backend_evaluation.py -q
python -m pytest tests/test_n04p03_embedding_sync.py tests/test_n04p02_search_representation_sync.py -q
python -m pytest -q
python -m ruff check src/sgokb/application_maintenance.py src/sgokb/retrieval/vector_maintenance.py src/sgokb/retrieval/__init__.py tests/test_n04p04_vector_index_sync.py
python -m ruff format --check src/sgokb/application_maintenance.py src/sgokb/retrieval/vector_maintenance.py src/sgokb/retrieval/__init__.py tests/test_n04p04_vector_index_sync.py
git diff --check
```

リポジトリ内で上記test filenameが異なる場合は、Vector/Similarityに対応する既存testを確認して実行対象を調整し、実際に使ったcommandを記録する。

Gate:

- focused P-04 all pass
- Vector / Semantic / Similarity regression pass
- P-02 / P-03 regression pass
- full pytest 0 failed
- new skip / xfailなし
- Ruff / format / diff-check pass
- fresh backend rebuild pass
- current / historical metadata更新pass
- missing Embedding explicit failure pass
- backend failure時canonical Knowledge保全pass
- revision supersession pass
- rebuild後Semantic / Similarity pass

## 7. P-05への境界

P-04完了時点ではApplication経路までを完成とする。

P-05で以下をPublic CLIとして整備する。

```text
sgokb system derived status [--object <id>]
sgokb system derived sync [--object <id>] [--semantic-runtime]
```

また既存`system index rebuild`と新derived orchestrationのoperator-facing意味をHelp / structured outputで固定する。

P-04 Reference Workstation検証がPASSしたら、状態を

```text
N-04P-04 Complete / N-04P-05 Next
```

へ進める。
