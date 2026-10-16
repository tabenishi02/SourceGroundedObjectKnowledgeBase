# N-04 Prerequisite — Derived Search Pipeline

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Position: `N-03 Complete` と `N-04` の間に置く必須Gate
- Base: N-03 completed commit `da61d287c6ab97ef24e2062344510327a770d65e`
- Status: **Planned / 未着手**
- Origin: N-03 real-data Vertical Sliceで、accepted Knowledgeは作成できたが内容語Lexical Searchが未成立し、`search_representation` derived stateがpendingのまま残ることを確認した。

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

### 2.1 Result Import後のderived state

accepted Version作成時、以下4種類は生成されず、`pending`としてqueueされる。

```text
search_representation
embedding
vector_index
rendering
```

これはVersion acceptanceの意図したcontractであり、canonical Import transaction内で派生物を生成しない設計になっている。

### 2.2 現在のpublic `system index rebuild`

現在のCLIは`sgokb system index rebuild`でsemantic runtimeを構成し、`KnowledgeVectorIndexBuilder(...).rebuild(provider.space)`を呼ぶ。

この処理は、

- Search Representationをmaterializeしない
- 未生成Embeddingを作成しない
- 既存Embeddingを前提にVector Indexを再構築する

ため、freshなaccepted Versionの`search_representation` / `embedding` pendingを解消する入口にはなっていない。

### 2.3 N-03実データでの症状

- exact canonical name / alias検索は成立
- Knowledge本文を使う内容語Lexical Searchは未成立
- Search Representationはpending
- 内部`SearchRepresentationBuilder`を直接呼べば進められるが、公開CLI限定の運用境界を迂回するため実行しなかった

この判断を維持する。

---

# 3. 追加Task

## N-04P-01 [P0] Derived Search lifecycle contractを確定する

**目的:** 実装前に、pending → readyの責務と公開操作境界を確定する。

実施内容:

- `search_representation` / `embedding` / `vector_index`の依存順序を正式化する。
- Result Importはcanonical writeだけを行い、derived generationはtransaction後のlocal maintenanceとする現行方針を維持するか確認する。
- Object単位incremental syncと全体rebuildの責務を分離する。
- current / historical Versionのどこまでを生成対象とするか定義する。
- failure時のderived stateを`pending / ready / failed`のどれへ遷移させるか固定する。
- retry時のidempotencyとrevision競合処理を定義する。
- renderingはN-04検索Gateから分離し、Search pipelineの必須3 stateと混同しない。

推奨Decision:

```text
Import
  → derived states pending
  → public local maintenance command
      1. Search Representation sync
      2. Embedding sync（semantic runtime要求）
      3. Vector Index sync
```

完了条件:

- 公開CLIから内部builderを直接呼ばずに進めるcontractが文書化される。
- Lexical-only maintenanceとSemantic maintenanceを分離できる。
- silent cloud fallbackを禁止する。

---

## N-04P-02 [P0] Search Representation同期経路を実装する

**目的:** accepted KnowledgeをKnowledge本文Lexical Search可能な状態へする。

実施内容:

- accepted current VersionについてObject / Facet / Statement Search Representationを生成するApplication serviceを設ける。
- 既存`SearchRepresentationBuilder`をtransport/CLIから直接扱わず、Application boundary経由で呼ぶ。
- content hashが同一なら既存Representationを再利用する。
- current Version切替後にold membershipを壊さず、新current membershipを作成する。
- 成功時のみ対象Objectの`search_representation` derived stateを該当revisionで`ready`へする。
- failure時はcanonical Knowledgeを変更せず、`failed`または再試行可能な明示状態と`last_error`を記録する。
- semantic runtimeなしで実行可能にする。

必須Test:

```text
accepted Version
→ search_representation pending
→ public sync
→ Object / Facet / Statement representations materialized
→ search_representation ready
→ Knowledge内容語 lexical search hit
```

N-03受入条件:

- N-03で未ヒットだった内容語queryを再実行し、Search Representation不足に起因する未ヒットが解消する。
- ranking品質そのものはN-06へ送る。

---

## N-04P-03 [P0] Incremental Embedding同期経路を実装する

**目的:** Search Representationをlocal semantic runtimeでEmbeddingへ同期する。

実施内容:

- `embedding` pendingかつSearch Representation readyのObjectを処理する。
- frozen Embedding Spaceを明示的に使用する。
- Representation ID / content hashで既存Embeddingを再利用し、同一表現を再計算しない。
- Object / Facet / Statementの全必要Representationを対象にする。
- Embedding Space変更時は別Spaceとして保持し、旧Spaceをsilent overwriteしない。
- local provider failureを明示errorにし、cloudへfallbackしない。
- provider未構成時は既存CLI contractどおりruntime unavailableとして扱う。
- 全必要Embeddingが揃った場合のみ`embedding` stateをreadyへする。

必須Test:

- 同じRepresentationの再同期でEmbedding providerを再呼出ししない。
- Version更新で再利用可能なRepresentationだけreuseされる。
- provider failure時にcanonical SQLite Knowledgeが変化しない。
- partial embeddingをready扱いしない。

---

## N-04P-04 [P0] Vector Index同期 / rebuild経路を完成させる

**目的:** Embedding ready後にSimilarity / Semantic Retrievalで使用できるVector Indexを公開操作で構築する。

実施内容:

- Vector同期はSearch Representation / Embedding readyを前提とする。
- membership単位pointを維持し、同じRepresentationを使うVersion間でもcurrent / historical identityを失わない。
- current Version変更後に`is_current` metadataが正しく更新される。
- incremental updateとfull rebuildの使い分けを定義する。
- `system index rebuild`の既存役割を整理し、Embedding不足時には明示的に失敗させる。
- Vector backend消失時にSQLite + Embeddingから再構築可能であることを維持する。
- 成功時のみ`vector_index` derived stateをreadyへする。

必須Test:

- fresh backend rebuild
- current / historical membership保持
- missing Embedding時の明示failure
- backend再構築後のSemantic Search / Similarity
- stale revisionをreadyへ誤更新しない

---

## N-04P-05 [P0] Public CLI / Status contractを整備する

**目的:** operatorが内部Python APIを使わずにderived pipelineを観測・実行できるようにする。

検討対象:

### 案A — dedicated derived maintenance command（推奨）

```text
sgokb system derived status
sgokb system derived sync [--object <id>] [--semantic-runtime]
```

利点:

- Search Representation / Embedding / Vectorの3段階を明示できる。
- lexical-only syncとsemantic syncを区別できる。
- 既存`system index rebuild`の意味をVector backend rebuildとして維持できる。

### 案B — `system index rebuild`の責務を拡張

Search Representation → Embedding → Vectorまで一括実行する。

欠点:

- semantic runtime不要のSearch Representationまで「index rebuild」に隠れる。
- lexical-only maintenanceがsemantic providerに不要に依存しやすい。
- 既存command semanticsが変化する。

**推奨:** 案Aを採用し、`system index rebuild`はVector Index rebuildとして意味を狭く維持する。

Status出力に最低限含める情報:

```text
object_id
target_version_id
kind
status
revision
last_error
representation count
embedding space / missing embedding count
vector backend / indexed point count
```

CLI要件:

- internal builderをoperatorへ露出しない。
- non-zero exit codeでpartial/runtime failureを表現する。
- semantic runtime未指定時、Search Representation syncまでは実行可能。
- semanticを要求した場合だけlocal embedding/vector runtimeを初期化する。
- external network/cloudをsilent使用しない。

---

## N-04P-06 [P0] N-03実データでDerived Search Gateを受入する

**目的:** synthetic fixtureだけではなくN-03 real-data datasetで公開運用経路を受入する。

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
7. `Fate/stay night` ↔ `BLEACH`のSimilarity経路が利用可能であることを確認する。
8. current Version / Object ID / Evidence groundingが変更されていないことを確認する。
9. `system integrity`とfull pytestを実行する。

Gate:

- 6 Objectすべてで`search_representation = ready`。
- Semanticを使う評価Spaceについて`embedding = ready`。
- Vector backendについて`vector_index = ready`。
- N-03で未ヒットだった内容語queryについて、少なくとも「Representation未生成」が原因の未ヒットは0件。
- Work Similarity API/CLIがN-04 case 2で使用可能。
- canonical Knowledge / Version / Evidence provenanceは不変。
- full suite 0 failed。

検索順位やRecallの正式合否はN-06で評価し、このGateへ混ぜない。

---

# 4. Dependency

```text
N-03 Complete
  ↓
N-04P-01 Contract freeze
  ↓
N-04P-02 Search Representation sync
  ↓
N-04P-03 Embedding sync
  ↓
N-04P-04 Vector sync/rebuild
  ↓
N-04P-05 Public CLI / status
  ↓
N-04P-06 N-03 real-data acceptance
  ↓
N-04 AI use-case acceptance
```

P-02〜P-05は設計上並行検討できるが、受入は上記依存順で行う。

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

- accepted VersionからSearch Representationをpublic CLI経由で生成できる。
- Knowledge内容語Lexical SearchがRepresentation未生成のため失敗しない。
- local semantic runtimeでEmbeddingをincremental生成・reuseできる。
- Vector Indexをpublic CLI経由で同期 / rebuildできる。
- derived stateのpending / ready / failedとerrorがoperatorから観測可能。
- silent cloud fallbackがない。
- N-03 real-data 6 Objectで受入PASS。
- Work SimilarityがN-04 case 2に使用可能。
- canonical Knowledge / Evidence / accepted Versionを変更しない。
- focused tests / full pytest / lintがPASS。

完了後、Phase Nの次Taskを`N-04 [P0] 3つの代表AI利用ケースを受入試験する`へ戻す。
