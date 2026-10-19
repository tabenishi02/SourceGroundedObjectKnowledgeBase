# N-04P-04 Vector Index同期 / rebuild

更新日: 2026-10-17

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-04 [P0] Vector Index同期 / rebuild経路を完成させる`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Complete (2026-10-17)**

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
python -m pytest tests/test_hybrid_search.py tests/test_object_similarity.py tests/test_vector_index.py tests/test_j01_similarity_application.py tests/test_k03_semantic_index_boundary.py -q
python -m pytest tests/test_n04p03_embedding_sync.py tests/test_n04p02_search_representation_sync.py -q
python -m pytest tests/test_n02_integration.py -q
python -m pytest tests/test_m01_cli.py tests/test_m03_standard_workflow.py -q
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


## 8. Reference Workstation検証結果

- 実行日: **2026-10-17 JST**（実測日で記録）。
- 環境: Windows 11 build 26300 / Python 3.10.6 / 通常`.venv`、pytest 9.1.1 / Ruff 0.17.0。
- branch: `phase-n/n04-prerequisite-derived-search` / 開始head: `b31f1857b094cd8df52f202aabfc48df651121d3`。

通常venvのPython（`.venv/Scripts/python.exe`）で、修正・format後に以下をすべて実行した。

| Command | 結果 |
|---|---|
| `python -m pytest tests/test_n04p04_vector_index_sync.py -q` | **14 passed / 0 failed**（3.62s） |
| `python -m pytest tests/test_hybrid_search.py tests/test_object_similarity.py tests/test_vector_index.py tests/test_j01_similarity_application.py tests/test_k03_semantic_index_boundary.py -q` | **23 passed / 3 skipped / 0 failed**（6.95s） |
| `python -m pytest tests/test_n04p03_embedding_sync.py tests/test_n04p02_search_representation_sync.py -q` | **15 passed / 0 failed**（4.59s） |
| `python -m pytest tests/test_n02_integration.py -q` | **3 passed / 0 failed**（4.70s） |
| `python -m pytest tests/test_m01_cli.py tests/test_m03_standard_workflow.py -q` | **14 passed / 0 failed**（33.01s） |
| `python -m pytest -q` | **336 passed / 3 skipped / 0 failed**（134.07s (0:02:14)） |
| 指定4 Python filesの`ruff check` / `ruff format --check` | **PASS** |
| `git diff --check` | **PASS** |

3 skipは既存optional Qdrant依存条件（adapter test moduleとHybrid/Similarityのoptional実backendケース）。実Qdrant adapterのruntime受入をPASSと主張しない。新しいskip / xfailは追加していない。focusedはdeterministic provider + local fake exact backendでnetwork/cloud不要。

### Contract / 動作確認

- 明示runtime未構成はvector stateを変更せずpending維持。Embedding未readyならupsert 0回。
- 初回incremental syncはmembership point 3件をupsertしてready。v1→v2同contentでもmembership identityを共有せず、旧3点のis_current=false / 新3点=trueへ更新し、計6点を保持した。
- historicalにだけ必要なEmbeddingを1件欠損させるとmissing=1で明示failure、同revisionのみfailed + last_error。Embeddingを暗黙生成しない。
- backend upsert failureでもaccepted Knowledge全体とcurrent pointerを維持。
- superseded成功/失敗の両経路で新revisionはpending、last_error=None。旧attemptは新revisionをready/failedにしない。
- fresh backend full rebuildで保存済みEmbeddingとSQLite membershipから2 Object / 6点を復元。Search Representation未準備の別current Objectはvector pendingのまま、ready_object_count=2。再構築後Semantic Searchで対象2 Objectが返り、SimilarityでAlpha→Betaが成立した。
- full rebuildでEmbedding 3件欠損ならfailure、readyへの昇格なし。
- rebuild中のaccepted Object新規追加 / v2 promotionをそれぞれ検証し、catalogまたはrevision変化でDerivedMaintenanceSupersededError。新旧Objectのvector stateをreadyへ進めず、新revisionのlast_errorも汚染しない。
- full backend rebuild failureを2 Objectで検証し、双方のKnowledge・全derived statesが前後一致。複数Objectを一括failedへ落とさず、providerのdocument呼出しも増えない。
- **公開KnowledgeVectorIndexBuilderがKnowledgeVectorMaintenanceBuilderを指すことを直接assertし、直接rebuildでbackend 3点を構築しても全derived statesが前後一致、vector_indexはpendingのままであることを追加testで保証した。** 同じtestで既存`system index rebuild`も実CLI dispatchを通し、別backend 3点の構築・state不変・Embedding provider再呼出しなしを確認した。
- P-02 / P-03とN-02 / CLI回帰はPASS。P-03のEmbedding ready / Vector pending境界を維持し、P-05のsystem derived CLIは先行実装していない。

### 発見した問題 / 修正

初回focusedは10 passedで機能的failureなし。指定Ruffは`retrieval/__init__.py`のE402と`vector_maintenance.py`のE501を検出し、formatはBuilder/testの2ファイルに差分があった。import blockを上部へ移動し、指定formatterで整形した。公開exportの参照先やproductionの判定・例外・revision guardは変更していない。

既存testに公開Builder rebuildのlifecycle-neutral保証がなかったため、依頼に従い直接Builder + 実CLI boundary testを追加した。さらにcatalog変更2経路とfull rebuild failureの複数Object保全を追加し、既存rebuild testへ未準備Objectのready非昇格assertionを補完した。最終focusedは実測14ケース。assertion弱体化、historical削除、missing Embedding暗黙生成、cloud fallbackは行っていない。

A〜Hに該当する機能的production failureは今回の検証では確認されなかった。既存候補名の存在しないtest filenameは実在する上記test群へ訂正した。

**N-04P-04 completion decision: Complete (2026-10-17)。次TaskはN-04P-05。** N-03評価DBへの適用や実semantic runtime受入はP-06へ残す。PR #39はDraft、PR #36 / #37 / #38 / #39はmergeしていない。

ローカル証跡（Git管理外）: `.local/n04p04/`のfocused-initial / focused-final / vector-regression / p02-p03-regression / n02-integration / cli-regression / full各log。
