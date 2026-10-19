# N-04P-05 Public CLI / Status contract

更新日: 2026-10-17

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-05 [P0] Public CLI / Status contractを整備する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Complete (2026-10-17)**

## 1. Scope

P-02〜P-04で実装したDerived Search maintenanceをoperatorが内部Python class / Builderを直接呼ばずに利用できる公開CLIへ接続する。

公開surfaceを次で固定する。

```text
sgokb system derived status [--object <object-id>] [--semantic-runtime]
sgokb system derived sync   [--object <object-id>] [--semantic-runtime]
```

`--object`省略時はcurrent accepted Versionを持つ全Objectを対象とする。

`system index rebuild`は既存contractどおり**Vector backend-only full rebuild**のまま維持する。Search Representation / missing Embeddingを暗黙生成せず、derived stateも直接変更しない。

---

## 2. Application boundary

新規`src/sgokb/application_derived.py`の`DerivedSearchOperatorApplication`を公開CLI用Application facadeとする。

責務:

- operator対象Objectの選択
- Derived Search status集約
- dependency orderに従ったstage orchestration
- batch実行時のObject単位failure隔離
- structured result生成

実処理は既存`DerivedSearchMaintenanceApplication`へ委譲し、CLI transportから次の内部要素を直接呼ばない。

- `SearchRepresentationBuilder`
- `KnowledgeVectorMaintenanceBuilder`
- Embedding repositoryの生成処理
- derived state直接更新

---

## 3. `system derived status`

### 3.1 runtimeなし

```text
sgokb system derived status
sgokb system derived status --object <id>
```

この経路はSQLite read-onlyとし、Embedding model / Qdrantを初期化しない。

最低限、Objectごとに次を返す。

```text
object_id
name
current_version_id
derived_states:
  kind
  target_version_id
  status
  revision
  last_error
  updated_at
search_representations:
  membership_count
  unique_representation_count
```

`pending / ready / failed / stale`と`last_error`をoperatorが直接観測可能でなければならない。

### 3.2 semantic runtime指定

```text
sgokb system derived status --semantic-runtime
```

明示指定時だけfrozen local semantic runtimeをcomposition rootから構成する。

追加表示:

```text
runtime.semantic_configured
runtime.embedding_space:
  space_id
  provider_key
  model
  model_revision
  dimension
runtime.vector_backend:
  backend_key
  available
  metadata
  error

objects[].embedding:
  space_id
  representation_count
  embedding_count
  missing_embedding_count
```

Vector backend collectionがまだ存在しない / 到達不能の場合、status command自体は可能な限りread結果を返し、`vector_backend.available=false`とdiagnostic errorを表示する。runtime compositionそのものが不可能な場合はruntime errorとする。

statusはderived/canonical dataを変更してはならない。

---

## 4. `system derived sync`

### 4.1 semantic runtimeなし

```text
sgokb system derived sync
sgokb system derived sync --object <id>
```

実行stage:

```text
Search Representation only
```

Embedding Provider / Vector backendを構成してはならない。

結果としてSearch Representationは`ready`へ進められるが、Embedding / Vector stateは変更しない。

### 4.2 semantic runtime指定

```text
sgokb system derived sync --semantic-runtime
sgokb system derived sync --object <id> --semantic-runtime
```

frozen local semantic runtimeを一度だけ構成し、Applicationへ明示注入する。

Objectごとに次の順序で実行する。

```text
Search Representation
  ↓
Embedding
  ↓
Vector Index
```

前段が失敗したObjectでは後段を実行しない。

cloud / external fallbackは禁止する。

---

## 5. Batch / partial contract

`--object`省略時、current accepted Versionを持つ全ObjectをObject ID順で処理する。

1 Objectのfailureで他Objectを中止しない。

structured result:

```text
semantic_requested
object_count
completed_object_count
partial
objects[]:
  object_id
  current_version_id
  semantic_requested
  complete
  stages[]:
    kind
    status
    result
    error
```

stage statusは少なくとも次を表現可能とする。

```text
ready
pending
failed
stale
blocked
runtime_unavailable
superseded
```

Applicationが返す`partial=true`ではCLI exit code `EXIT_PARTIAL (8)`を使用する。

---

## 6. Exit code contract

既存CLI contractを維持する。

| 状況 | Exit |
|---|---:|
| status成功 / sync全Object成功 | `0` |
| batchまたはsingle Objectのderived stage failure | `8` (`EXIT_PARTIAL`) |
| `--semantic-runtime`指定時にlocal semantic runtime構成不可 | `5` (`EXIT_RUNTIME`) |
| unknown Object | `3` (`EXIT_NOT_FOUND`) |
| Objectにaccepted current Versionなし等のprecondition | `4` (`EXIT_BLOCKED`) |
| DB / I/O / integrity error | 既存CLI contract |

semantic runtimeを指定していないこと自体はerrorではない。Search Representation only syncとして正常実行する。

---

## 7. Existing command compatibility

次を変更しない。

```text
sgokb system index status
sgokb system index rebuild
```

`system index rebuild`:

- Vector-only
- existing Embeddingのみ使用
- Search Representationを生成しない
- missing Embeddingを生成しない
- derived lifecycle stateを直接変更しない

N-04P-05で`system derived`を追加しても旧commandの意味を拡張しない。

---

## 8. Required focused tests

最低限次を自動testで固定する。

1. parserが`system derived status/sync`を受理する。
2. `status` runtimeなしでmodel/Qdrant composition rootを呼ばない。
3. `status --object`がderived state / revision / `last_error` / representation countsを返す。
4. `status --semantic-runtime`がactive Space / missing Embedding / Vector backend statusを返す。
5. `sync` runtimeなしでSearch Representationのみready化し、Embedding / Vectorはpending維持。
6. `sync --semantic-runtime`でSearch Representation → Embedding → Vectorが順にready化。
7. ready再実行がidempotent。
8. batchで1 Object failureでも後続Objectを処理し、`partial=true` / exit 8。
9. local semantic runtime composition failureはexit 5で、silent fallbackなし。
10. unknown `--object`はexit 3。
11. accepted current VersionなしObjectはexit 4。
12. `status`がread-onlyでderived/canonical state不変。
13. `system index rebuild`のVector-only / lifecycle-neutral contract回帰。

---

## 9. Regression gate

Reference Workstationで最低限実行する。

```powershell
python -m pytest tests/test_n04p05_derived_cli.py -q
python -m pytest tests/test_n04p04_vector_index_sync.py tests/test_n04p03_embedding_sync.py tests/test_n04p02_search_representation_sync.py -q
python -m pytest tests/test_m01_cli.py tests/test_m03_standard_workflow.py tests/test_k03_semantic_index_boundary.py -q
python -m pytest -q
python -m ruff check src/sgokb/application_derived.py src/sgokb/cli/main.py tests/test_n04p05_derived_cli.py
python -m ruff format --check src/sgokb/application_derived.py src/sgokb/cli/main.py tests/test_n04p05_derived_cli.py
git diff --check
```

条件:

- focused / regressions / full suite: 0 failed
- 新規skip / xfailでfailureを隠さない
- runtime-free focused pathsはnetwork/cloud不要
- semantic focused pathsはdeterministic fake local provider/backendで成立

---

## 10. Completion gate

N-04P-05をCompleteとする条件:

- `system derived status`が公開CLIとして利用可能。
- `system derived sync`が公開CLIとして利用可能。
- runtimeなしでSearch Representationのみ同期可能。
- explicit semantic runtime指定でEmbedding / Vectorまで同期可能。
- statusからstate/revision/error/representation/Embedding/Vector情報を観測可能。
- per-Object failureがstructured partialとして返る。
- exit code contractが固定される。
- internal BuilderがCLIへ露出しない。
- existing `system index rebuild` contract不変。
- silent cloud fallbackなし。
- Reference Workstation全Gate PASS。

PASS後:

```text
N-04P-05 Complete / N-04P-06 Next
```

へ進む。


## 11. Reference Workstation verification — 2026-10-17

通常のproject venvで以下を実行した。semantic focused testsはdeterministic fake local provider / fake exact Vector backendのみを使用し、network/cloudおよび実SentenceTransformer/Qdrantを必要としない。

| Command | 実測結果 |
|---|---|
| `python -m pytest tests/test_n04p05_derived_cli.py -q` | 17 passed / 0 failed |
| `python -m pytest tests/test_n04p04_vector_index_sync.py tests/test_n04p03_embedding_sync.py tests/test_n04p02_search_representation_sync.py -q` | 29 passed / 0 failed |
| `python -m pytest tests/test_m01_cli.py tests/test_m03_standard_workflow.py tests/test_k03_semantic_index_boundary.py -q` | 20 passed / 0 failed |
| `python -m pytest -q` | 353 passed / 3 skipped / 0 failed (132.73s) |
| `python -m ruff check src/sgokb/application_derived.py src/sgokb/cli/main.py tests/test_n04p05_derived_cli.py` | PASS |
| `python -m ruff format --check src/sgokb/application_derived.py src/sgokb/cli/main.py tests/test_n04p05_derived_cli.py` | PASS (3 files) |
| `git diff --check` | PASS |

3 skippedは既存optional Qdrant依存条件。新しいskip / xfailは追加していない。実Qdrantの動作・品質受入を今回の結果へ含めない。

### 確認済みcontract

- parserが両commandとoptional Object / semantic runtimeを受理する。
- runtime-free status/syncはcomposition rootを呼ばない。statusはstate / revision / last_error / updated_at / current VersionとRepresentation countを返す。
- runtime-free syncはSearch Representationのみready、Embedding / Vector / renderingはpendingを維持する。current accepted VersionのないObjectはbatch対象外。
- explicit semantic syncはSearch Representation → Embedding → Vectorの順でready。再実行でもKnowledge、revision、membership Vector pointは同じで、Embeddingは再生成されない。既存契約上、Vector再upsertと同期確認時刻更新は許容する。
- semantic statusはSpaceの全指定field、Embedding充足数、Vector metadataを返す。未作成/到達不能backendはavailable=false / diagnostic errorを返し、SQLite statusを維持する。
- status前後のSQLite全table dump一致をruntime-free / semantic / backend diagnosticで確認した。providerのdocument生成も呼ばれない。
- batchの先頭ObjectのVector failureでも後続Objectはready。通常success envelope内にpartial=trueとObject/stage errorを返し、exit 8。失敗してもcanonical Knowledgeは不変。
- runtime composition不可はexit 5、unknown Objectはexit 3、accepted current Versionなしはexit 4。status/syncの双方で確認した。
- `system index status`と`system index rebuild`の意味は変更していない。rebuildは既存EmbeddingのVector-only処理で、SQLite全table dumpとderived lifecycleが不変。P-04回帰でも公開Builderのlifecycle-neutral境界・missing Embedding拒否を確認した。
- P-02〜P-04回帰はrevision guard、missing-only / reuse、Space isolation、membership identity、current/historical scopeを保持した。

### 発見した問題と修正

- 公開CLI parser/dispatch未接続: `DerivedSearchOperatorApplication`を呼ぶ経路を実装。semantic指定時のみruntimeを一度構成し、partialと既存exit contractへ接続した。
- facadeのprivate maintenance helper依存: public `version_store.derived_states()`から対象kindを取得する形へ変更した。
- focused test作成中の既存API名の誤りをpublic Read Applicationへ修正。冪等性を「upsertや確認時刻更新も起きない」とした過剰な期待は、canonical Knowledge / lifecycle revision / Vector identityの不変性とEmbedding reuseの検証へ修正した。productionの同期・revision契約は変更していない。
- import順序と既存format差分をRuffで修正し、その後すべての指定testを実行した。

### Completion decision

全Gate PASSにより **N-04P-05 Complete (2026-10-17)**。次Taskは **N-04P-06 [P0] N-03実データでDerived Search Gateを受入する**。

N-03実データへの正式適用は未実施。PR #39はDraftを維持し、PR #36〜#39はmergeしない。
