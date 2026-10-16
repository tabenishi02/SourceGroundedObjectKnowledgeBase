# N-04 Prerequisite — Derived Search Pipeline

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Position: `N-03 Complete` と `N-04` の間に置く必須Gate
- Base: N-03 completed commit `da61d287c6ab97ef24e2062344510327a770d65e`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Active — N-04P-03 Complete / N-04P-04 Next**
- Origin: N-03 real-data Vertical Sliceで、accepted Knowledgeは作成できたが内容語Lexical Searchが未成立し、`search_representation` derived stateがpendingのまま残ることを確認した。
- Lifecycle contract: `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`

## 1. 目的

N-04の代表AI利用ケース、とくに「Work Dataから意味的に類似する別Workを検索する」ケースを開始する前に、accepted Object Knowledgeから検索用派生物を**公開運用経路だけで**生成・同期できる状態にする。

今回の問題は検索品質ではなく、次のderived artifact lifecycleをpendingからreadyへ進める公開orchestration経路が不足していることにある。

```text
accepted Object Version
  ↓
Search Representation
  ↓
Embedding
  ↓
Vector Index
  ↓
Lexical / Semantic / Hybrid / Similarity Retrieval
```

N-06はこのpipelineが成立した後に検索品質を評価する。N-04前提作業では、まず「生成・同期経路が正しく存在すること」を受入する。

---

## 2. N-03で確認した現状

accepted Version作成時、次のderived kindはartifactを生成せず`pending`としてqueueされる。

```text
search_representation
embedding
vector_index
rendering
```

これはcanonical transaction内で派生物を生成しない意図したVersion lifecycleである。

一方、現在の`sgokb system index rebuild`はsemantic runtimeを構成し、既存EmbeddingからVector Indexを再構築するだけである。

したがって現状では、fresh accepted Versionについて次の入口がpublic workflowに不足している。

- Search Representation materialization
- missing Embedding incremental generation
- Search Representation → Embedding → Vectorの一括orchestration
- derived stateのoperator-visible status / retry

N-03では内部`SearchRepresentationBuilder`を直接呼ばず、公開CLI限定境界を維持した。この判断を継続する。

---

# 3. Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-04P-01 | P0 | **Complete (2026-10-16)** | Derived Search lifecycle / state / orchestration contractを確定 |
| N-04P-02 | P0 | **Complete (2026-10-16)** | Search Representation同期経路を実装 |
| N-04P-03 | P0 | **Complete (2026-10-16)** | Incremental Embedding同期経路を実装 |
| N-04P-04 | P0 | **Next / 未着手** | Vector Index同期 / rebuild経路を完成 |
| N-04P-05 | P0 | Pending | Public CLI / Status contractを実装 |
| N-04P-06 | P0 | Pending | N-03実データでDerived Search Gateを受入 |

---

## N-04P-01 [P0] Derived Search lifecycle contractを確定する — Complete

成果物:

`docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`

確定した主要Decision:

1. Result Import transactionではderived artifact本体を生成せず、Version acceptance時にderived revisionを`pending`としてqueueする。
2. canonical transaction commit後にpost-commit local maintenanceを行う。
3. dependency orderを`Search Representation → Embedding → Vector Index`とする。
4. Search Representationはsemantic runtime不要で、Knowledge本文Lexical Searchを成立させる必須local maintenanceとする。
5. Embedding / Vectorは明示的なlocal semantic runtimeでのみ処理し、silent cloud fallbackを禁止する。
6. derived failureでaccepted Knowledge / current pointerをrollbackしない。
7. `pending / ready / failed / stale`の意味を固定した。
8. completion時には`object_id + kind + target_version_id + revision`のrevision guardを必須とする。
9. representation / embeddingはcontent-addressed reuseを許可し、Version membershipは別に保持する。
10. normal incremental syncはcurrent targetを優先し、historical artifactを破壊しない。full rebuild / backfillではaccepted historical Versionも再生成可能にする。
11. operatorは内部Builderを直接呼ばず、Application service経由のpublic maintenance pathを使用する。
12. `system index rebuild`はVector-only rebuildとして維持し、全pipeline orchestrationは`system derived`側へ分離する。
13. `rendering`は同じderived lifecycleに属するがN-04 Search Gateからは分離する。

N-04P-01完了により、N-04P-02はSearch Representationだけにscopeを限定して実装できる。

---

## N-04P-02 [P0] Search Representation同期経路を実装する — Complete

**目的:** accepted KnowledgeをKnowledge本文Lexical Search可能な状態へする。

実施内容:

- accepted current VersionについてObject / Facet / Statement Search Representationを生成するApplication serviceを設ける。
- 既存`SearchRepresentationBuilder`をtransport / CLIから直接扱わず、Application boundary経由で呼ぶ。
- content hashが同一なら既存Representationを再利用する。
- current Version切替後にold membershipを壊さず、新current membershipを作成する。
- revision guardを実装する。
- 成功時のみ対象Objectの`search_representation`を`ready`へする。
- failure時はcanonical Knowledgeを変更せず`failed`と`last_error`を記録する。
- semantic runtimeなしで実行可能にする。

必須Test:

```text
accepted Version
→ search_representation pending
→ public/Application sync
→ Object / Facet / Statement representations materialized
→ search_representation ready
→ Knowledge内容語 lexical search hit
```

N-03で未ヒットだった内容語queryについて、少なくともRepresentation未生成に起因する未ヒットを解消する。ranking品質はN-06へ送る。

---

## N-04P-03 [P0] Incremental Embedding同期経路を実装する — Complete

**目的:** readyなSearch Representationをlocal semantic runtimeでEmbeddingへ同期する。

実施内容:

- `embedding` pendingかつSearch Representation readyのObjectを処理する。
- active / frozen Embedding Spaceを明示的に使用する。
- Representation identity / content hashで既存Embeddingを再利用する。
- Object / Facet / Statementの必要Representationを対象にする。
- Embedding Space変更時は別Spaceとして保持し、旧Spaceをsilent overwriteしない。
- local provider failureを明示errorにし、cloudへfallbackしない。
- provider未構成時はruntime unavailableとし、未試行対象を単純な`failed`扱いにしない。
- 全必要Embeddingが揃った場合のみ`embedding = ready`とする。
- revision guardを適用する。

必須Test:

- 同じRepresentationの再同期でprovider再呼出しなし。
- Version更新でreuse可能分のみreuse。
- provider failure時にcanonical Knowledge不変。
- partial embeddingをready扱いしない。

---

## N-04P-04 [P0] Vector Index同期 / rebuild経路を完成させる

**目的:** Embedding ready後にSimilarity / Semantic Retrievalで使用できるVector Indexを構築する。

実施内容:

- Vector同期はSearch Representation / Embedding readyを前提とする。
- membership単位pointを維持し、current / historical identityを失わない。
- current Version変更後に`is_current`等のscope metadataを正しく更新する。
- incremental updateとfull rebuildを分離する。
- `system index rebuild`はVector-only rebuildとして維持する。
- missing Embedding時は明示failureまたはblocked扱いとし、暗黙生成しない。
- backend消失時にSQLite + Embeddingから再構築可能とする。
- 成功時のみ`vector_index = ready`とする。
- revision guardを適用する。

必須Test:

- fresh backend rebuild
- current / historical membership保持
- missing Embedding時の明示failure
- rebuild後のSemantic Search / Similarity
- stale revisionをreadyへ誤更新しない

---

## N-04P-05 [P0] Public CLI / Status contractを整備する

**目的:** operatorが内部Python APIを使わずにderived pipelineを観測・実行できるようにする。

推奨public surface:

```text
sgokb system derived status [--object <id>]
sgokb system derived sync [--object <id>] [--semantic-runtime]
```

Exact argument shapeは実装時にCLI整合を確認して固定する。

原則:

- semantic runtime未指定時でもSearch Representation syncまでは実行可能。
- semantic runtimeを明示した場合だけEmbedding / Vectorへ進む。
- `system index rebuild`はVector-only full rebuildとして意味を維持する。
- internal Builderをoperatorへ露出しない。
- partial/runtime failureをexit codeとstructured outputで区別する。
- silent external/cloud processingを行わない。

Status出力に最低限含める候補:

```text
object_id
target_version_id
kind
status
revision
last_error
representation count
active embedding space / missing embedding count
vector backend / indexed point count
```

---

## N-04P-06 [P0] N-03実データでDerived Search Gateを受入する

対象DB:

```text
.local/n03/sgokb-n03.sqlite
```

受入手順:

1. 6 Objectのderived state初期状態を記録する。
2. public CLIだけでSearch Representation syncを実行する。
3. N-03内容語Lexical queryを再実行する。
4. local semantic runtimeを固定する。
5. public CLIだけでEmbedding / Vector syncを実行する。
6. 6 Objectでsemantic search smokeを行う。
7. `Fate/stay night` ↔ `BLEACH`のSimilarity経路を確認する。
8. current Version / Object ID / Evidence groundingが変更されていないことを確認する。
9. `system integrity`とfull pytestを実行する。

Gate:

- 6 Objectすべてで`search_representation = ready`。
- 評価Spaceについて`embedding = ready`。
- Vector backendについて`vector_index = ready`。
- N-03内容語queryで「Representation未生成」が原因の未ヒットが0件。
- Work SimilarityがN-04 case 2で利用可能。
- canonical Knowledge / Version / Evidence provenance不変。
- full suite 0 failed。

検索順位やRecallの正式合否はN-06へ送る。

---

# 4. Dependency

```text
N-03 Complete
  ↓
N-04P-01 Contract freeze                Complete
  ↓
N-04P-02 Search Representation sync     Complete
  ↓
N-04P-03 Embedding sync                 Complete
  ↓
N-04P-04 Vector sync/rebuild            Next
  ↓
N-04P-05 Public CLI / status
  ↓
N-04P-06 N-03 real-data acceptance
  ↓
N-04 AI use-case acceptance
```

P-02〜P-05は設計上並行検討できるが、受入は依存順に行う。

---

# 5. N-04との境界

N-04本体では次の3ケースを評価する。

1. Character Data → local LLM Roleplay
2. similar Work retrieval → AI comparative explanation
3. Concept A/B → local LLM Character creation

Case 1 / 3はObject IDから直接Knowledgeを取得すれば技術的には先行可能である。

しかしPhase Nの評価環境を統一し、Case 2だけ内部APIや特別手順を使う状態を避けるため、**N-04全体の正式開始GateをN-04P-01〜P-06完了後とする。**

N-04PはAI output qualityを評価しない。AI output qualityはN-04本体、Retrieval ranking qualityはN-06が担当する。

---

# 6. Scope外

この前提作業では次を行わない。

- ANN backend品質比較
- Recall / MRR / nDCGの正式評価
- reranker比較
- Roleplay品質評価
- Work比較説明のAI品質評価
- Concept組合せ創作のAI品質評価
- performance p95判定
- Failure / Recovery全シナリオ

これらはN-04〜N-07の既存Taskへ残す。

---

# 7. 完了条件

N-04 prerequisite全体をCompleteとする条件:

- accepted VersionからSearch Representationをpublic経路で生成できる。
- Knowledge内容語Lexical SearchがRepresentation未生成のため失敗しない。
- local semantic runtimeでEmbeddingをincremental生成・reuseできる。
- Vector Indexをpublic経路で同期 / rebuildできる。
- derived stateの`pending / ready / failed / stale`とerrorがoperatorから観測可能。
- revision競合時にstale attemptをreadyへ誤昇格しない。
- silent cloud fallbackがない。
- N-03 real-data 6 Objectで受入PASS。
- Work SimilarityがN-04 case 2に使用可能。
- canonical Knowledge / Evidence / accepted Versionを変更しない。
- focused tests / full pytest / lintがPASS。

完了後、Phase Nの次Taskを`N-04 [P0] 3つの代表AI利用ケースを受入試験する`へ戻す。


## N-04P-02 Reference Workstation acceptance

2026-10-16、Application syncのfocused 6ケース、Search回帰15 passed / 1 skipped、full suite 0 failed、指定Ruff / format / git diff --checkがPASSした。fixtureのStatement groundingを修正し、superseded成功/失敗双方のrevision guardとcanonical Knowledge不変を確認した。実測件数・詳細は`docs/planning/N04P02_SEARCH_REPRESENTATION_SYNC.md`を参照する。

N-04P-02受入時の状態はP-03 Nextだった。現在はN-04P-01〜P-03 Complete / N-04P-04 Next。P-04〜P-06は未着手。N-04 AI use-case acceptanceはprerequisite全体の完了待ちで、PR #39はDraftを維持する。


## N-04P-03 Reference Workstation acceptance

2026-10-16、focused 9 passed、Embedding/Search回帰 23 passed / 1 skipped、P-02回帰 6 passed、full suite 322 passed / 3 skipped / 0 failed、指定Ruff / format / git diff --checkがPASSした。実測は`docs/planning/N04P03_INCREMENTAL_EMBEDDING_SYNC.md`を参照する。

N-04P-01 / P-02 / P-03 Complete、P-04 Next、P-05 / P-06 Pending。N-04 AI use-case acceptanceはprerequisite完了待ちで、PR #39はDraftを維持する。
