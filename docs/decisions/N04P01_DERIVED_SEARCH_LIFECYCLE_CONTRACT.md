# N-04P-01 Derived Search Lifecycle Contract

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-01 [P0] Derived Search lifecycle contractを確定する`
- Status: **Accepted / Complete (2026-10-16)**
- Origin: N-03 real-data Vertical Slice
- Parent plan: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`

## 1. Decision summary

accepted Object Knowledgeから検索用派生物を生成するlifecycleを次で固定する。

```text
validated Result
  ↓ explicit import
accepted Object Version / current pointer
  ↓ queue derived revision (canonical transaction内)
search_representation: pending
embedding:             pending
vector_index:          pending
rendering:             pending
  ↓ canonical transaction commit
post-commit local maintenance
  ↓
Search Representation sync
  ↓
Embedding sync (explicit local semantic runtime only)
  ↓
Vector Index sync
```

主要Decision:

1. **Result Import transactionではderived artifact本体を生成しない。** canonical writeと派生生成を同一transactionへ結合しない。
2. Version promotion / rollbackは対象Versionを`object_derived_states`へqueueし、revisionを進めて`pending`へ戻す。
3. Search Representation → Embedding → Vector Indexを依存順序として固定する。
4. Search Representationはsemantic runtimeに依存せず、Lexical Search成立のためのlocal deterministic maintenanceとする。
5. Embedding / Vectorは、明示的に構成されたlocal semantic runtimeにだけ依存する。silent cloud fallbackは禁止する。
6. derived maintenance failureでaccepted Knowledge / current pointerをrollbackしない。
7. operatorは内部Builderを直接呼ばない。公開CLIはApplication serviceを経由する。
8. incremental syncとfull rebuildを別責務とする。
9. current Objectのderived stateと、historical artifact retentionを分離して扱う。
10. `rendering`は同じderived lifecycleに属するが、N-04 prerequisite Search Gateの依存DAGからは分離する。

---

## 2. Existing contractとの整合

### 2.1 Workflow requirement

`WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`は、explicit Result Import後をLocal Automatic Maintenanceとして次の更新対象を要求している。

- Search Representation
- Lexical Index
- Object / Facet / Statement Embedding
- Vector Index membership
- derived rendering

本Decisionはこの要件を維持する。

ただし「automatic」は、canonical transaction内で派生生成まで完了させることを意味しない。正本commit後に、同一Application orchestrationまたは公開maintenance operationから**人間の意味判断を追加せず**再生成可能であることを意味する。

### 2.2 Search requirement

`SEARCH_REQUIREMENTS.md`の次を維持する。

- accepted current Knowledgeのみを通常検索scopeとする。
- Object / Facet / Statement multi-representationを生成可能にする。
- 同一representation contentではEmbedding / Vector reuseを許可する。
- historical Version membershipを失わない。
- Vector backendはSQLite canonical Knowledgeから再構築可能な派生物とする。

### 2.3 Current implementation

現行Version acceptanceは次を`pending`としてqueueする。

```text
search_representation
embedding
vector_index
rendering
```

このqueue-only contractは維持する。

現行`sgokb system index rebuild`は既存EmbeddingからVector Indexを再構築するoperationであり、Search Representation materializationやmissing Embedding生成を担当しない。この意味も維持する。

---

## 3. Dependency DAG

検索系derived artifactの依存関係を次で固定する。

```text
accepted Version
    │
    ▼
Search Representation
    │
    ├──────────────→ Knowledge Lexical Search
    │
    ▼
Embedding (active Embedding Space)
    │
    ▼
Vector Index membership (active backend / space)
    │
    ├──────────────→ Semantic Search
    ├──────────────→ Hybrid Search
    └──────────────→ Similarity
```

### 3.1 Search Representation

対象:

- Object overall representation
- Facet representation
- searchable Knowledge Statement representation

必要に応じてtextual Attribute等も既存Search contractに従ってmaterializeする。

Search Representation作成と、そのRepresentationを対象とするLexical FTS更新は1つのlogical maintenance単位として扱う。別の`lexical_index` derived kindは追加しない。

### 3.2 Embedding

EmbeddingはSearch Representationに従属する。

`search_representation != ready`の対象についてEmbeddingをreadyへしてはならない。

Embedding readinessは、**現在選択されているactive / frozen Embedding Space**に対する完全性を意味する。別Embedding Spaceの既存rowをsilent overwriteしない。

### 3.3 Vector Index

Vector IndexはEmbeddingに従属する。

対象Embedding Spaceで必要Embeddingが不足している場合、Vector sync / rebuildは不足を明示し、`ready`へしてはならない。

Vector pointはRepresentationの単純identityではなくVersion membershipを保持し、current / historical scopeを区別できなければならない。

### 3.4 Rendering

`rendering`はaccepted Versionから直接再生成可能なparallel derived artifactとする。

N-04 prerequisiteではSearch pipelineのGateに含めない。Search Representation / Embedding / Vectorがreadyでもrendering pendingを理由にN-04をblockしない。

---

## 4. State semantics

既存`DerivedState`を次の意味で使用する。

### `pending`

最新`target_version_id` / `revision`について、生成・同期が必要だが完全なready状態に到達していない。

次を含む。

- Version promotion / rollback直後
- dependency待ち
- semantic runtime未指定でEmbedding / Vectorをまだ試行していない
- retry待ち

optional semantic runtimeが未構成であることだけを理由に`failed`へしない。

### `ready`

当該`object_id + kind + target_version_id + revision`について必要なderived artifactが完全に同期済みで、通常read pathで利用可能。

`ready`への更新はrevision guard付きで行う。

### `failed`

当該revisionに対する実際のmaintenance attemptがerrorで終了した状態。

例:

- Representation builder error
- local embedding provider execution error
- persistence error
- Vector backend write error

`last_error`へoperatorが診断可能な情報を保存する。canonical Knowledgeをrollbackしない。retry可能とする。

### `stale`

以前readyだったartifactが、Version以外のruntime / configuration invalidation等により現在の要求条件を満たさなくなった状態に使用する。

例:

- Representation Builder contract revision変更
- active Embedding Space変更
- backend/index metadata不整合検出

通常のObject Version promotionでは既存実装どおり`pending`へqueueするため、毎回`stale`を経由させない。

---

## 5. Revision / concurrency contract

Derived maintenanceは開始時に次のtupleをsnapshotする。

```text
(object_id, kind, target_version_id, revision)
```

処理完了時、同じtupleが依然currentである場合だけ`ready` / `failed`へ更新できる。

途中で新しいVersion promotion等によりrevisionが進んだ場合:

- 古いattemptは新revisionを`ready`へしてはならない。
- 古いartifactがcontent-addressedで再利用可能なら保持してよい。
- current membership / state updateは新revision側へ再queueする。
- stale attemptのcompletionはno-opまたは明示的discardとして扱う。

このrevision guardをSearch Representation / Embedding / Vectorの全段階へ適用する。

---

## 6. Idempotency / reuse contract

### Search Representation

同一semantic contentから同一representation hash / identityを生成できる場合、既存Representationを再利用する。

Version membershipは別に保持するため、reuseによってhistorical Version identityを失わない。

### Embedding

次が同一なら既存Embeddingを再利用する。

```text
representation identity/content hash
+ Embedding Space identity
```

同一Representationをsyncするたびにproviderを再呼出ししない。

### Vector

同じEmbedding / Representationを複数Versionが共有しても、Vector backend上ではVersion membership / Object scopeを再構築可能なmetadataとして保持する。

full rebuildを行ってもcanonical Knowledge VersionやEmbedding rowを増やさない。

---

## 7. Current / historical scope

### Incremental sync

通常のincremental maintenanceは`object_derived_states.target_version_id`、すなわち**現在のaccepted target Version**を対象とする。

通常Searchのcurrent scopeを最短でreadyにすることを優先する。

### Historical retention

current切替時に、旧VersionのKnowledge、Search Representation、Embeddingを破壊しない。

旧Versionが以前materialize済みなら、そのartifact / membershipはhistorical retrieval用に保持する。

### Full rebuild / backfill

明示的なfull rebuild / historical backfillでは全accepted Versionを再走査可能にする。

これはcurrent pointerを変更せず、未生成historical representation / embedding / membershipを再構築できるmaintenance operationとする。

`object_derived_states`はcurrent target readinessのoperator stateであり、全historical Versionの完全性を1 rowで表現するものではない。

---

## 8. Trigger / orchestration boundary

Derived pipelineには2種類の公開triggerを認める。

### 8.1 Post-import trigger

explicit Result Importによるcanonical transaction成功後、同じpublic workflowからpost-commit maintenanceを開始可能にする。

最低限、semantic runtime不要のSearch Representation syncは標準local workflowとして自動開始可能にする。

Embedding / Vectorは、local semantic runtimeが明示的に有効な環境でのみ続行してよい。runtimeを見つけるためにcloudへfallbackしてはならない。

派生処理失敗はImport成功そのものを取り消さない。command / statusは「canonical import succeeded / derived maintenance incomplete」を区別できなければならない。

### 8.2 Explicit maintenance trigger

retry、backfill、runtime後付け、rebuildのために、operatorがpublic CLIからderived maintenanceを明示実行できるようにする。

exact command shapeはN-04P-05で確定するが、logical surfaceは次とする。

```text
system derived status
system derived sync
```

operatorに`SearchRepresentationBuilder`等の内部classを直接呼ばせない。

---

## 9. Incremental sync と full rebuild

### Incremental sync

用途:

- Result Import後
- rollback後
- failed / pending retry
- active runtime設定後

特徴:

- current targetを優先
- content-addressed reuse
-不足分だけ生成
- canonical Knowledge不変

### Full rebuild

用途:

- Vector backend消失 /交換
- Search Representation schema変更
- Embedding Space追加後のbackfill
- derived integrity recovery

特徴:

- canonical SQLiteをsource of truthとする
- accepted Versionを再走査可能
- current / historical membership再構築可能
- rebuild自体で新Knowledge Versionを作成しない

既存`system index rebuild`は**Vector-only rebuild**として維持し、Search Representation / missing Embeddingを暗黙生成するcommandへ拡張しない。

全pipeline rebuildが必要な場合は`system derived`側のorchestrationから各段階を明示的に実行する。

---

## 10. Runtime / egress contract

- Search Representation生成はlocal deterministic処理。
- 標準Embeddingはlocal providerを使用する。
- `--semantic-runtime`相当の明示指定または明示local configurationなしにEmbedding / Vector runtimeを起動しない。
- cloud Embedding / remote reranker等へsilent fallbackしない。
- 将来external semantic providerを利用する場合はB-06/B-07のExternal Processing / egress boundaryへ従い、N-04Pの標準local pathとは分離する。

---

## 11. Failure contract

Derived maintenance failure時:

1. accepted Object Versionは維持する。
2. current pointerをrollbackしない。
3. Knowledge / Evidence groundingを変更しない。
4. 該当kindを`failed`またはretry可能な`pending`として可視化する。
5. downstream dependencyを`ready`にしない。
6. Lexical-only pathが成立している場合、semantic failureでIdentity / Lexical readを禁止しない。
7. public statusから対象Object、kind、target Version、revision、errorを確認可能にする。

canonical integrity failureとoptional runtime failureを同じerror categoryへ潰さない。

---

## 12. Public Application boundary

N-04P-02〜P-05では、Derived Search maintenanceをApplication serviceとして実装する。

推奨logical API:

```text
DerivedSearchMaintenanceApplication
  status(...)
  sync_search_representations(...)
  sync_embeddings(...)
  sync_vector_index(...)
  sync(...)
```

CLIはこのApplication boundaryを呼び、storage repository / builder / provider / vector adapterを直接組み立てる処理を可能な限りCLI command bodyへ持ち込まない。

同じApplication serviceを将来のscheduler / GUI等から再利用可能にする。

---

## 13. N-04P-02への実装契約

N-04P-02は本Decisionに従い、まずSearch Representationのみを完成させる。

必須条件:

- semantic runtime不要
- accepted current Versionのみをincremental対象にできる
- Object / Facet / Statement Representationをmaterialize
- content reuse
- current/historical membership保持
- revision guard
- 成功時`search_representation = ready`
- failure時canonical Knowledge不変
- 内容語Lexical SearchがRepresentation未生成のため失敗しない
- public/Application pathを用意し、内部Builder直呼びをoperator手順にしない

Embedding / Vector実装はP-03 / P-04へ分離する。

---

## 14. Acceptance decision

N-04P-01の目的である以下を確定した。

- derived dependency order
- canonical transactionとの境界
- current / historical scope
- state semantics
- failure / retry semantics
- revision concurrency guard
- idempotency / reuse
- incremental / rebuild責務
- runtime / no-silent-cloud boundary
- public Application / CLI orchestration boundary

**N-04P-01: Complete。次TaskはN-04P-02 [P0] Search Representation同期経路を実装する。**
