# N-04P-02 Search Representation Sync

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-02 [P0] Search Representation同期経路を実装する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Complete (2026-10-16)**

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
7. sync中にrevisionが進んだ場合、古いattemptは新revisionをready / failedへ変更できず、last_errorも汚染しない。
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


## 8. Reference Workstation verification結果

- 実行日: 2026-10-16 JST
- 環境: Windows 11 build 26300 / Python 3.10.6、通常`.venv`。pytest 9.1.1 / Ruff 0.17.0。
- branch: `phase-n/n04-prerequisite-derived-search`、開始head: `df6a2d30997c0c00c5eda69ad6e94bfff2b9b94f`。
- production Application実装は変更せず、fixture groundingの補完と検証assertion追加のみ実施。

通常venvのPython（`.venv/Scripts/python.exe`）で次を実行した。

| Command | 結果 |
|---|---|
| `python -m pytest tests/test_n04p02_search_representation_sync.py -q` | **6 passed / 0 failed**（1.70秒） |
| `python -m pytest tests/test_search_representation.py tests/test_hybrid_search.py -q` | **15 passed / 1 skipped / 0 failed**（3.73秒） |
| `python -m pytest -q` | **313 passed / 3 skipped / 0 failed**（123.71s (0:02:03)） |
| `python -m ruff check src/sgokb/application_maintenance.py tests/test_n04p02_search_representation_sync.py` | **PASS** |
| `python -m ruff format --check src/sgokb/application_maintenance.py tests/test_n04p02_search_representation_sync.py` | **PASS**（2 files） |
| `git diff --check` | **PASS** |

元の5 test関数を維持し、superseded revisionケースを成功終了 / 失敗終了の2通りにparameterizeしたため実行件数は6。Search回帰の1 skipとfull suiteの3 skipは既存optional Qdrant runtime条件であり、今回skip / xfailは追加していない。

### Contract確認

- accepted current Versionとderived target一致をApplicationで要求。生成は既存BuilderへApplication内部から委譲し、operator/transportがBuilderを直接扱う手順は追加していない。
- pendingからsyncしてObject overall / Facet / Statementの3 membershipsが生成され、同revisionがreadyへ遷移。同じKnowledge内容語`sacrifice`がsync前未hitからsync後hitへ変化した。
- ready再実行はchanged=false、membership IDと件数不変。
- builder failureでは同revisionだけfailedとなりlast_errorを保持。accepted Version / current pointerだけでなく、KnowledgeReadApplicationが返すaccepted Knowledge全体も前後一致。
- 処理中にv2 promotionでrevision=2へ進むと、旧attemptが成功または失敗しても新revisionはpendingのまま、last_error=None。両経路がDerivedMaintenanceSupersededErrorとなる。
- 同contentのv1→v2でRepresentation IDをreuseし、v1 historical membershipを保持。通常Lexical Searchはv2だけを返す。
- Search Representation生成にEmbedding Provider / Vector backend / cloud / networkは不要。local deterministicなApplication/Builderだけを使用し、embedding / vector_indexはpendingのまま。
- 既存Representation hash/reuse、FTS、current/historical、semantic/hybrid filtering、Vector membershipのSearch回帰はPASS（optional Qdrant 1件のみ既存skip）。

### 発見した問題と修正

分類 **B: test fixtureの誤り**。最初は5件すべて、_accepted_versionがEvidenceなしStatementをacceptしようとして`accepted statement requires evidence`で失敗した。fixtureへSource / Snapshot / Raw artifact metadata / Normalization Run / Evidenceを追加し、StatementへEvidence linkを設定してからacceptするよう修正した。test用Raw metadataのSHA-256とbyte数はfixture本文から算出している。

production grounding gateは維持し、revision guardの削除、failureのready扱い、canonical Knowledge変更、historical削除、assertion弱体化はしていない。失敗時のKnowledge全体不変assertionと、superseded失敗終了ケースを追加して保証を補強した。必要なformat後、focused / Search回帰 / full suiteをすべて再実行した。

A/C/D/E/Fに該当するproduction不具合は今回の検証では確認されなかった。N-03評価DBへは適用していない。public CLI / post-import orchestrationはP-05、N-03 real-dataへの正式適用はP-06へ残す。

**N-04P-02 completion decision: Complete。次TaskはN-04P-03。** P-03〜P-06とN-04本体は未完了であり、PR #39はDraftを維持する。PR #36 / #37 / #38 / #39はmergeしない。

ローカル証跡（Git管理外）: `.local/n04p02/focused-initial.log`、`focused-final.log`、`search-regression.log`、`full.log`。
