# Object Evidence Retrieval

更新日: 2026-10-12

## 1. 目的

F-03では、Objectに関連するcanonical Evidenceを、旧Fragmentを中間層にせず直接取得する標準Retrievalを定義・実装する。

標準経路は次の通り。

```text
Object
 ↓
Object identity / alias
Source↔Object association
Source metadata
Evidence FTS
Evidence semantic similarity
manual include / exclude
 ↓
Evidence Candidates + Selection Reasons
```

生成LLMは使用しない。Retrieval結果はKnowledgeそのものではなく、後続F-04 / G-01でEvidence Package候補を構築するための入力集合である。

## 2. 既定scope

通常Retrievalでは、Sourceごとに明示選択されたeffective Snapshotと、そのSnapshotで明示選択されたeffective Normalization Runに属するEvidenceだけを対象とする。

最新時刻のSnapshot / Runを自動採用しない。F-01の`source_selection_events`を正本とする。

historical Evidenceは通常候補へ混在させない。operatorが`manual_include`で具体的`evidence_id`を指定した場合のみ、明示overrideとしてhistorical Evidenceを候補へ追加できる。

## 3. Candidate generation signal

### 3.1 explicit Source↔Object association

`source_object_associations`を利用する。

- `confirmed`: 強いcandidate signal
- `candidate`: 高Recall用candidate signal
- `excluded`: 当該Objectの自動candidate生成から除外

`subject_relationship`はselection reason detailとして保持する。

### 3.2 Object name / alias

Objectのcanonical nameまたはaliasがEvidence本文へ直接含まれる場合、それぞれ`name` / `alias` channelとして記録する。

### 3.3 Source metadata

Object name / aliasと、以下のSource側情報の一致をsignalとして使用する。

- Source label
- active locator
- Source classification
- Source metadata
- effective Snapshot title

Snapshot固有classification / metadataはeffective Snapshotの観測値だけを通常検索に使用する。

### 3.4 Evidence FTS

Migration 009でcanonical `evidence_records.content`に対する`evidence_retrieval_fts`を追加する。FTSは再生成可能なderived indexであり、Evidence本体を正本とする。

Object name / aliasをphrase queryとして検索し、`lexical` channelを記録する。

### 3.5 Semantic retrieval

Embedding providerが明示的に設定されている場合だけ`semantic` channelを有効にする。providerが無い状態でsemantic retrievalを要求した場合はerrorとし、cloud等へsilent fallbackしない。

F-03時点では、effective Evidenceをrequest時にEmbeddingしてcosine similarityを計算する単純実装とする。これは正確性を優先した移行実装であり、永続Embedding / Vector backend / incremental reuseはPhase Iの責務とする。

### 3.6 Manual include / exclude

具体的`evidence_id`を明示指定できる。

- `manual_include`: 通常scope外のhistorical Evidenceを含めることもできる明示override
- `manual_exclude`: 他signalで候補になっていても最終候補から除外

manual操作は自動rankingより強いoperator decisionとして扱う。

## 4. Selection reason

各Evidence candidateは複数のselection reasonを保持できる。

```text
explicit_association
name
alias
source_metadata
lexical
semantic
manual
```

reasonには少なくとも`channel`と`detail`を保持し、semantic / lexical等では補助scoreを保持できる。

1 Evidenceが複数channelで取得された場合、reasonを上書きせず併記する。これにより、後続Package BuilderやUIから「なぜこのEvidenceが候補になったか」を追跡できる。

## 5. Retrieval score

F-03の`retrieval_score`はcandidate priorityを決めるためのheuristicであり、以下を意味しない。

- 情報の真偽
- Source trust
- Knowledge confidence
- Objectとの意味的確定関係

複数signalを加算し、confirmed associationやmanual includeを高く扱うが、最終的なKnowledge判断はChatGPT / Human-in-the-loop側へ残す。

高Recallを優先し、False Positiveを完全排除する設計にはしない。

## 6. Output contract

`Application.retrieve_object_evidence()`は概ね次を返す。

```text
object_id
name
aliases
scope = effective_snapshot_and_run
semantic
excluded_source_ids
candidate_count
candidates[]
  evidence_id
  source_id
  snapshot_id
  run_id
  content
  retrieval_score
  reasons[]
  context
```

`context`にはEvidence metadata、location、Source label、Snapshot title、active locator等を含み、Source / Snapshot / Run / Raw ArtifactへのProvenance追跡を維持する。

## 7. F-04との境界

F-03はcandidate retrievalまでを担当する。以下はF-04へ残す。

- token / byte budget
- Source diversity
- Evidence granularity調整
- chunk overlap /近接Evidenceのgrouping
- near-duplicate suppression
- truncation理由
- Packageへ最終採用するEvidence集合

したがってF-03の`max_candidates`は検索暴走防止のcandidate上限であり、Package size budgetではない。

## 8. F-05との境界

F-03は既存`source_object_associations`を読み、`candidate / confirmed / excluded`をRetrievalへ反映する。

associationをoperatorが追加・変更・除外するUI / CLIはF-05で実装する。F-03ではassociation storage contract自体を変更しない。

## 9. Phase Iとの境界

F-03のsemantic channelはon-demand cosine baselineである。Phase Iで以下へ置換・拡張可能にする。

- canonical Evidence Search Representation
- persistent Embedding Space
- VectorIndexAdapter
- Exact / ANN backend
- incremental embedding reuse
- model / revision / preprocessing metadata

F-03のselection reason contractはPhase I移行後も維持し、backend変更でPackage provenanceを失わない。

## 10. 検証条件

F-03完了時に次を満たす。

1. Fragmentを生成せずObject→Evidence candidateを取得できる。
2. confirmed / candidate associationを利用できる。
3. excluded associationを自動候補へ含めない。
4. name / alias / Source metadata / FTSを利用できる。
5. Embedderが明示設定されている場合semantic retrievalを利用できる。
6. effective Snapshot / Runだけを通常検索する。
7. manual includeでhistorical Evidenceを明示選択できる。
8. manual excludeを最終候補へ反映できる。
9. 各Evidenceのselection reasonを追跡できる。
10. Evidence Provenanceを維持する。
11. Generative LLM / Fragment / Final Documentを呼ばない。

次TaskはF-04 `Evidence Selectionのtoken/size budgetを設計する` とする。
