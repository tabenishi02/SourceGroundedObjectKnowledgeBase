# N-04P-06 Real-data Derived Search Acceptance

更新日: 2026-10-17

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-06 [P0] N-03実データでDerived Search Gateを受入する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Dataset: `benchmark/n03-real-data-vertical-slice-v1.json`
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Acceptance execution pending / Reference Workstation required**

## 1. Purpose

N-03では6 Objectのcanonical Vertical Sliceは成立したが、Search Representationが未生成だったため内容語Lexical Searchが未成立だった。

N-04P-02〜P-05で次を実装済みである。

```text
accepted Object Version
  ↓
Search Representation sync
  ↓
Embedding sync
  ↓
Vector Index sync / rebuild
  ↓
public CLI: system derived status / sync
```

P-06ではこのpipelineをN-03の実データ評価DBへpublic CLIだけで適用し、Lexical / Semantic / Similarityの利用可能性とcanonical Knowledge不変性を受け入れる。

検索順位、Recall、NDCG等の正式な品質判定はN-06へ送る。P-06では「derived artifact不足のため利用できない」状態を解消したかを判定する。

## 2. Source of truth

評価対象を手作業で再定義しない。

次を正本とする。

```text
benchmark/n03-real-data-vertical-slice-v1.json
```

このbenchmarkに記録された6 Objectについて、最低限以下をDB実体と照合する。

- stable Object ID
- canonical name / aliases
- accepted current Version ID
- Source / Snapshot / Evidence provenance
- N-03 lexical smoke query
- similarity rationale

対象はN-03で確定した次の6 Objectである。

```text
Character:
- Saber
- Ichigo Kurosaki

Work:
- Fate/stay night
- BLEACH

Concept:
- Tsundere
- Hero's Journey
```

## 3. Safety boundary

この受入は評価専用DBだけを変更する。

```text
.local/n03/sgokb-n03.sqlite
```

production DBを変更してはならない。

受入前に次を保存する。

1. DB backup
2. `system integrity`
3. `system derived status`
4. 6 ObjectのObject ID / current Version ID
5. canonical Knowledge / Evidence / provenanceの比較用snapshot

受入で変更を許容するのはderived artifactである。

```text
search_representations
knowledge_search_representation_memberships
search_embedding_spaces
search_representation_embeddings
object_derived_states
外部Vector backend collection / points
```

canonical Object / Version / Statement / Evidence / provenanceの意味内容を変更してはならない。

## 4. Semantic runtime

P-06はfake provider / fake Vector backendではなく標準local semantic runtimeを使う。

Frozen Embedding profile:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dimension: 1024
provider: sentence-transformers
output dtype: float32
model load dtype: bfloat16
```

Vector backend:

```text
Qdrant
default URL: http://localhost:6333
default gRPC port: 6334
```

必須原則:

- cloud inferenceへfallbackしない。
- provider / model / revision / Embedding Space IDを記録する。
- Qdrant server versionとcollection名を記録する。
- 実行時の環境変数を記録する。
- model artifact downloadが必要な場合、それはlocal runtime準備として記録し、cloud inferenceとは区別する。
- 可能ならmodelを一度cacheした後、`SGOKB_MODEL_LOCAL_ONLY=1`で本受入を再実行する。

QdrantがReference Workstation上に存在しない場合、production実装をfake/local-modeへ変更してGateを通してはならない。既存Qdrant service / executable / approved temporary local serverを使用する。runtimeを用意できない場合はP-06をBlockedとして記録し、Completeにしない。

## 5. Acceptance sequence

### A. Baseline integrity / dataset identity

1. branch / head / working treeを記録する。
2. `.local/n03/sgokb-n03.sqlite`の存在を確認する。
3. benchmark JSONとDBの6 Object stable IDを照合する。
4. benchmark記録のaccepted current Version IDとDBを照合する。
5. canonical Knowledge / Evidence / provenance snapshotを保存する。
6. `sgokb system integrity`を実行しPASSを確認する。
7. runtime-free `sgokb system derived status`を保存する。

N-03由来DBであることを確認できない場合は中止する。

### B. Search Representation acceptance

public CLIのみを使う。

```text
sgokb --db .local/n03/sgokb-n03.sqlite system derived sync
```

semantic runtimeは付けない。

Gate:

- 6 Objectすべて`search_representation = ready`
- `embedding` / `vector_index`はこの段階で勝手にreadyへ進まない
- canonical Knowledge不変

### C. Lexical re-check

N-03 benchmarkに記録されたlexical smoke queryを再実行する。

特にN-03で内容語由来の未ヒットとなったqueryを再評価する。

判定:

- 「Search Representation未生成」が原因の未ヒットが0件になること。
- canonical name / aliasの既存rank-1成立を壊さないこと。
- 正式なranking quality合否はN-06へ送る。

queryごとに次を記録する。

```text
query
target object
target found
target rank
search channel
N-03 result
P-06 result
```

### D. Real semantic runtime preflight

1. `local-embedding` / `vector-qdrant` dependency確認。
2. frozen model revisionをload可能か確認。
3. Qdrantへ接続できることを確認。
4. `system derived status --semantic-runtime`を実行。
5. active Embedding Space ID / model / revision / Qdrant metadataを記録。

このpreflightはstatusなのでDBのderived/canonical dataを変更しないことを確認する。

### E. Embedding + Vector acceptance

public CLIのみを使う。

```text
sgokb --db .local/n03/sgokb-n03.sqlite system derived sync --semantic-runtime
```

Gate:

- 6 Objectすべて`search_representation = ready`
- 6 Objectすべて評価Spaceで`embedding = ready`
- 6 Objectすべて対象backendで`vector_index = ready`
- status上`missing_embedding_count = 0`
- partial=false / exit 0
- cloud fallbackなし

実行後に同じcommandを再実行し、Embedding reuse / lifecycle idempotencyも確認する。

### F. Semantic search smoke

6 Objectについて少なくとも1 queryずつsemantic searchを実行する。

queryはbenchmarkのexpected search query / grounded contentから選ぶ。

P-06のGateは品質順位そのものではなく、次である。

- semantic channelがdegradedせず実行できる。
- Vector backendからcurrent Object resultが返る。
- target Objectが合理的なcandidate集合に入る。
- current/historical scopeが破壊されていない。

詳細ranking qualityはN-06で評価する。

### G. Work Similarity smoke

N-04 case 2の前提として、少なくとも次を実行する。

```text
Fate/stay night → similar objects
BLEACH → similar objects
```

確認事項:

- Similarity operationがruntime errorなしで成立する。
- score typeは既存contractどおりsemantic similarityである。
- Work class / cross-class optionの既存contractに従う。
- 取得結果を保存する。

「Fate/stay nightとBLEACHが必ず相互rank 1」はP-06 Gateにしない。順位・品質はN-06で判定する。

### H. Canonical invariance

受入後、事前snapshotと比較する。

次が不変であること。

```text
Object stable IDs
current Version IDs
accepted Version content
Facet / Statement / Attribute / Relation canonical Knowledge
Source / Snapshot / Evidence
Statement-Evidence grounding
provenance
```

Search Representation / Embedding / Vector derived artifactの追加は許容する。

### I. Final system gate

```text
sgokb system integrity
python -m pytest -q
```

Gate:

- integrity PASS
- full suite 0 failed
- 新規skip / xfailなし
- working tree clean（受入記録更新前の意図したdoc差分を除く）

## 6. Completion Gate

N-04P-06をCompleteにできるのは、すべて満たす場合だけである。

- benchmarkと評価DBの6 Object identity整合。
- 6 Objectすべて`search_representation = ready`。
- frozen評価Spaceについて6 Objectすべて`embedding = ready`。
- 実Qdrant backendについて6 Objectすべて`vector_index = ready`。
- `missing_embedding_count = 0`。
- N-03内容語queryでRepresentation未生成原因の未ヒット0件。
- semantic search smokeが実runtimeで成立。
- Work Similarity経路が実runtimeで成立。
- canonical Knowledge / Version / Evidence provenance不変。
- `system integrity` PASS。
- full pytest 0 failed。

受入中にproduction defectが見つかった場合はP-06 scopeで修正し、P-02〜P-05回帰とfull suiteを再実行する。

環境不足だけの場合はproduction contractを弱めず、Blockedとして環境条件を記録する。

## 7. Evidence to record

Complete時はこの文書へ少なくとも以下を追記する。

```text
Reference Workstation OS / Python / GPU
branch / start head / final head
DB path / backup path / DB hash before-after
6 Object ID / current Version verification
initial/final derived states
representation counts per Object
Embedding model / exact revision / space_id
Embedding count / reuse count
Qdrant server/client version / collection
Vector point count
lexical query before/after table
semantic smoke result table
Work Similarity result
canonical invariance comparison
system integrity result
full pytest result
Ruff / diff-check if code changes occurred
issues / fixes / blockers
```

Local runtime logs belong under `.local/n04p06/` and are not committed unless intentionally converted into summarized acceptance evidence.

## 8. Completion transition

PASS後:

```text
N-04P-01 Complete
N-04P-02 Complete
N-04P-03 Complete
N-04P-04 Complete
N-04P-05 Complete
N-04P-06 Complete
```

としてN-04 prerequisite全体をCompleteにする。

次TaskはPhase N本体の:

```text
N-04 [P0] 3つの代表AI利用ケースを受入試験する
```

PR #39はP-06完了記録を反映した後にprerequisite completionとしてReady化可否を判断する。PR #36〜#39を勝手にmergeしない。
