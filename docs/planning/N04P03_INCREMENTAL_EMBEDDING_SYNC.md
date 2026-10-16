# N-04P-03 Incremental Embedding Sync

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-03 [P0] Incremental Embedding同期経路を実装する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Implementation complete / Reference Workstation verification pending**

## 1. Scope

N-04P-03では、N-04P-02で`ready`になったcurrent accepted VersionのSearch Representationを、明示的に注入されたlocal Embedding ProviderのEmbedding Spaceへincremental同期するApplication経路を追加する。

対象:

```text
accepted current Version
  ↓
search_representation = ready
  ↓
DerivedSearchMaintenanceApplication.sync_embedding(object_id)
  ↓
active/frozen provider.space
  ↓
missing Search Representation only
  ↓
local embed_documents()
  ↓
search_representation_embeddings
  ↓
embedding = ready
```

N-04P-03ではVector Indexを更新しない。`vector_index`はP-04まで`pending`のままとする。

---

## 2. Implementation

`src/sgokb/application_maintenance.py`へ次を追加した。

- `DerivedMaintenanceRuntimeUnavailableError`
- `EmbeddingSyncResult`
- `DerivedSearchMaintenanceApplication(..., embedding_provider=...)`
- `sync_embedding(object_id)`

### 2.1 Explicit local runtime only

Embedding Providerはcomposition rootから明示注入する。

Provider未指定の場合:

- providerを自動構築しない
- network / cloudへfallbackしない
- `embedding`を`failed`へしない
- `pending`のまま`DerivedMaintenanceRuntimeUnavailableError`を返す

これは「runtime未構成」と「実際のprovider execution failure」を区別するためである。

### 2.2 Dependency Gate

Embedding syncは次を要求する。

- Objectにcurrent accepted Versionがある
- `search_representation.target_version_id == current_version_id`
- `search_representation.status == ready`
- `embedding.target_version_id == current_version_id`

Search Representationが未readyならproviderを呼ばず、Embedding stateも変更しない。

### 2.3 Incremental / reuse

current VersionのKnowledge Search Representation membershipからunique `representation_id`を列挙する。

Providerの`EmbeddingSpaceSpec.space_id`をactive/frozen Space identityとして扱い、既存の

```text
(space_id, representation_id)
```

Embeddingを再利用する。

missing Representationだけを`provider.embed_documents()`へ送る。

同一Representationを複数Versionが共有する場合、Version membershipは別のまま、Embeddingはreuseする。

### 2.4 Embedding Space isolation

別のEmbedding Spaceを指定した場合:

- 旧Space rowをoverwriteしない
- 新Spaceに不足Embeddingを生成する
- 両SpaceをSQLite cacheへ共存させる

`search_embedding_spaces` / `search_representation_embeddings`の既存I-02 contractを利用し、新migrationは追加しない。

### 2.5 Completion Gate

Provider call後、current Versionで必要な全Representationについてrequested SpaceのEmbeddingが存在することを再確認する。

完全な場合のみ同revisionを`ready`へする。

providerが文書数と異なるVector数を返す、dimension不一致、persistence failure等は`failed + last_error`とする。

partial cacheが残ってもcanonical Knowledgeは変更しない。retry時は保存済み分をreuseできる。

### 2.6 Revision guard

開始時に少なくとも次をsnapshotする。

```text
embedding: (object_id, target_version_id, revision)
search_representation: (target_version_id, revision, ready)
```

処理中に新Versionがpromotionされ、derived revisionが進んだ場合:

- 旧attemptは新revisionを`ready`へしない
- 旧attempt failureも新revisionを`failed`へしない
- 新revisionの`last_error`を汚染しない
- content-addressedな旧Embedding cacheは保持してよい

---

## 3. Result contract

`EmbeddingSyncResult`は次を返す。

```text
object_id
version_id
revision
space_id
representation_count
reused_embedding_count
created_embedding_count
changed
state
```

`changed=False`は、requested Spaceについて必要Embeddingがすべて既存で、derived stateもすでにreadyだった場合を表す。

---

## 4. Focused tests

追加:

`tests/test_n04p03_embedding_sync.py`

検証対象:

1. Search Representation ready → missing 3件だけEmbedding生成 → embedding ready。
2. provider未構成 → RuntimeUnavailable、pending維持、Spaceも作成しない。
3. Search Representation未ready → providerを呼ばずpending維持。
4. ready再実行 → provider再呼出しなし、全件reuse。
5. v1→v2同一Representation → provider再呼出しなし、既存Embedding reuse。
6. provider failure → embedding failed + last_error、accepted Knowledge不変。
7. 異なるEmbedding Space → 旧Spaceを保持して新Spaceを別保存。
8. revision supersession成功終了 → 新revisionをreadyへしない。
9. revision supersession失敗終了 → 新revisionをfailedへせずlast_errorも汚染しない。

---

## 5. Explicit non-goals

N-04P-03では次を行わない。

- Vector Index upsert / rebuild
- semantic / hybrid / similarityの正式受入
- public CLI追加
- operator-visible derived status UI
- default providerのReference Workstation runtime freeze
- N-03 real-data DBへの正式適用
- ANN / ranking品質評価

これらはP-04〜P-06 / N-06へ残す。

---

## 6. Reference Workstation verification Gate

実行:

```powershell
python -m pytest tests/test_n04p03_embedding_sync.py -q
python -m pytest tests/test_embedding_space.py tests/test_search_representation.py tests/test_hybrid_search.py -q
python -m pytest -q
python -m ruff check src/sgokb/application_maintenance.py tests/test_n04p03_embedding_sync.py
python -m ruff format --check src/sgokb/application_maintenance.py tests/test_n04p03_embedding_sync.py
git diff --check
```

Gate:

- focused: 0 failed
- Embedding / Search regression: 0 failed
- full suite: 0 failed
- Ruff / format / diff-check: PASS
- no new skip / xfail to hide N-04P-03 failures
- no cloud/network requirement for focused tests

Reference Workstation検証がPASSするまでN-04P-03をCompleteにしない。

---

## 7. Completion後

PASS後:

- 本書を`Complete`へ更新
- `N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`を`N-04P-03 Complete / N-04P-04 Next`へ更新
- `PHASE_N_PREPARATION.md`を同状態へ更新
- `KNOWLEDGE_BASE_REDESIGN_TASKS.md`を同状態へ更新
- PR #39本文を更新
- PR #39はP-04〜P-06が残るためDraft維持

次Task:

`N-04P-04 [P0] Vector Index同期 / rebuild経路を完成させる`
