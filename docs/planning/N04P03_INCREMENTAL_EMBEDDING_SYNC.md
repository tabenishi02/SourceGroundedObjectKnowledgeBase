# N-04P-03 Incremental Embedding Sync

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-03 [P0] Incremental Embedding同期経路を実装する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Complete (2026-10-16)**

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

Reference Workstationでfocused / 回帰 / full suite / lint / format / diff-checkがPASSしたため、N-04P-03をCompleteとした。

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


## 8. Reference Workstation実測結果

- 実行日: 2026-10-16 JST
- 環境: Windows 11 build 26300 / Python 3.10.6 / 通常`.venv`、pytest 9.1.1 / Ruff 0.17.0。
- branch: `phase-n/n04-prerequisite-derived-search` / PR #39。
- 開始head: `f3d6647414479775d42513251c0819a6ee9cd170`。

通常venvのPython（`.venv/Scripts/python.exe`）で実行した。

| Command | 結果 |
|---|---|
| `python -m pytest tests/test_n04p03_embedding_sync.py -q` | **9 passed / 0 failed**（2.03s） |
| `python -m pytest tests/test_embedding_space.py tests/test_search_representation.py tests/test_hybrid_search.py -q` | **23 passed / 1 skipped / 0 failed**（6.17s） |
| `python -m pytest tests/test_n04p02_search_representation_sync.py -q` | **6 passed / 0 failed**（1.29s） |
| `python -m pytest -q` | **322 passed / 3 skipped / 0 failed**（124.85s (0:02:04)） |
| `python -m ruff check src/sgokb/application_maintenance.py tests/test_n04p03_embedding_sync.py` | **PASS** |
| `python -m ruff format --check src/sgokb/application_maintenance.py tests/test_n04p03_embedding_sync.py` | **PASS**（2 files） |
| `git diff --check` | **PASS** |

Embedding/Search回帰の1 skipとfull suiteの3 skipは既存optional Qdrant runtime条件。P-03 focusedは9件すべて実行・成功し、新規skip / xfailは追加していない。format修正後に上記全テストを再実行した。

### Contract確認 / reuse実測

- provider未構成ではDerivedMaintenanceRuntimeUnavailableErrorとなり、embedding stateはbefore/after完全一致（pending維持）。Embedding Space rowも0件で、自動provider構築やcloud fallbackはない。
- Search Representation未readyではprovider呼出し0回、embeddingはpendingを維持。
- readyなcurrent Versionのunique Representation 3件に対し、初回はproviderへ3 documentsを1回渡し、created=3 / reused=0。保存rowsを再照合してembedding=ready、vector_index=pending。
- ready再実行はcreated=0 / reused=3 / changed=false。provider総呼出し回数は1回のまま。
- 同content v1→v2もcreated=0 / reused=3、provider総呼出し回数1回を維持し、新revision=2のembeddingだけreadyになる。
- requested provider.spaceを使い、別Spaceは3 rowsずつ計6 rows、2 Spaceとして共存。旧Spaceのsilent overwriteなし。
- provider failureは同revisionをfailed + last_errorへ変更するが、accepted Version / current pointer / KnowledgeReadApplicationのKnowledge全体は前後一致。Vectorはpendingのまま。
- superseded成功/失敗の両経路で新v2 revision=2はpending、last_error=Noneを維持する。旧attemptはDerivedMaintenanceSupersededErrorとなる。
- 実装確認で、target Versionのcurrent一致、provider Vector数とdocument数の一致、requested Space内の全必要Embedding保存の再確認、persistence errorのrevision-guarded failed記録を確認した。
- focusedは明示注入したdeterministic FakeEmbeddingProviderのみを使い、実Embeddingモデル、network、cloud、Vector backendは不要。P-02のruntime-free同期も6ケースすべてPASS。

### 発見した問題 / 実施した修正

初回focused 9件とRuffはPASS。format checkだけが`application_maintenance.py`のrepresentation_ids式の折返し1か所を検出したため、指定Ruff formatterで整形した。動作変更、fixture/assertion変更、migration変更、production contractの緩和は不要だった。A〜Gに該当する機能的failureは今回の検証では見つからなかった。

**N-04P-03 completion decision: Complete (2026-10-16)。次TaskはN-04P-04。** P-04〜P-06とN-04本体は未完了。N-03評価DBへは適用しておらず、public CLI / real-data受入は後続Taskへ残す。PR #39はDraftを維持し、PR #36 / #37 / #38 / #39はmergeしていない。

ローカル証跡（Git管理外）: `.local/n04p03/focused-initial.log`、`focused-final.log`、`search-regression.log`、`p02-regression.log`、`full.log`。
