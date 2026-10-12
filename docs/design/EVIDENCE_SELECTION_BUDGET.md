# Evidence Selection Budget

更新日: 2026-10-12

## 1. 目的

F-04では、F-03のObject Evidence Retrievalが返す高Recall候補集合から、後続のObject Evidence Packageへ渡すEvidence集合を有限サイズに選択する。

F-03の責務は「関連し得るEvidenceを落とし過ぎずに集めること」、F-04の責務は「その候補をbudget内で、関連性とSource多様性を維持しながら選ぶこと」である。

```text
F-03 Evidence Candidates
  ↓
protected/manual selection
  ↓
Source diversity pass
  ↓
relevance fill
  ↓
duplicate / overlap handling
  ↓
token / byte / item budget
  ↓
Bounded Evidence Selection + Omission Reasons
```

Fragmentは使用しない。canonical Evidence ID、F-03 selection reason、Source / Snapshot / Run provenanceをそのまま保持する。

## 2. Budget contract

F-04では3種類のhard limitを同時に使用する。

- `max_estimated_tokens`: Evidence payloadの推定token上限
- `max_bytes`: UTF-8 serialized payloadのbyte上限
- `max_items`: Evidence件数上限

初期defaultは次とする。

```text
max_estimated_tokens = 12,000
max_bytes            = 65,536 bytes
max_items            = 64
```

これは特定ChatGPT modelのcontext上限ではなく、SGOKB側の安全な初期運用値である。すべて呼び出し時に変更可能とする。

G-01以降でPackage manifest、current Knowledge、instructions等を同じcontextへ入れる場合、F-04へ渡すbudgetはそれらの固定overheadを差し引いた残量に設定する。

## 3. Token estimation

F-04はmodel-specific tokenizerへ依存しない。推定方式は`ascii_div4_plus_non_ascii_v1`とし、Evidence candidateのcompact JSON payload全体を対象にする。

- ASCII文字: 約4文字を1 tokenとして見積もる
- 非ASCII文字: 1 code pointを1 tokenとして保守的に見積もる
- contentだけでなく、Evidence ID、selection reasons、context / provenance metadataも見積対象に含める

この値は請求token数や特定modelの正確なtoken数ではない。目的は「Package選択段階で無制限出力を防止する再現可能なbudget metric」を提供することである。

最終export先のmodel tokenizerが確定した場合、G-01以降でTokenEstimator adapterへ置換可能とする。ただしF-04のbudget / omission contractは維持する。

## 4. Selection order

### 4.1 protected Evidence

operatorが`manual_include`したEvidenceはPackage selectionでもprotectedとして扱う。

protected Evidenceは通常ranking・duplicate suppressionより優先する。ただしhard budgetをsilentに超過してはならない。

protected Evidenceを含めるとbudgetを超える場合は自動で捨てず、明示errorとする。operatorはbudgetを増やすかmanual includeを変更する必要がある。

### 4.2 Source diversity pass

protected Evidenceを処理した後、各Sourceの未決定候補のうち最上位Evidenceを1件ずつ試行する。

これにより、単一Sourceの多数chunkが上位を占有して他Sourceを完全に押し出すことを防ぐ。

Source diversityは「Sourceが多いほど真実」という意味ではない。retrieval rankingやSource trustとは独立したPackage構成上の方針である。

### 4.3 relevance fill

Sourceごとの初回候補を処理した後、残りbudgetをF-03のcandidate順で埋める。

この段階では同一Sourceから複数Evidenceを採用できる。Sourceごとのhard quotaは設けない。1 Sourceしかない場合でもbudgetを利用でき、強いEvidenceが多数あるSourceを不必要に切り捨てないためである。

## 5. Structural granularity / nearby Evidence

Evidence Store側のEvidence境界は保持し、F-04で本文を再chunkしない。

`metadata.artifact / positions / section / kinds / run_id / source_id`から`structure_group`を導出し、同一Source構造に由来する近接Evidenceを追跡する。

同じ`structure_group`のEvidenceが複数採用された場合は、後続itemに`related_selected_evidence_ids`を記録する。

これにより次を両立する。

- section / paragraph / table / post等のSource構造を壊さない
- 長い1 blockを分割したchunkの近接関係を失わない
- 近接しているという理由だけで異なる情報をsilent mergeしない

通常の100文字overlap程度では両方のchunkを自動削除しない。重複率が極端に高い場合のみsuppression対象とする。

## 6. Duplicate / overlap suppression

F-04のsuppressionはPackage-localであり、Evidence Storeからrecordを削除しない。

採用済みEvidenceとの比較で次を除外できる。

- `duplicate`: whitespace/case正規化後の本文が同一
- `near_duplicate`: 同一Source内で本文similarityが0.92以上
- `overlapping_chunk`: 同一structure groupでrange overlapが0.85以上

異なるSourceのnear-duplicateは、exact duplicateでない限り一律削除しない。独立Sourceによる類似記述まで失うことを避けるためである。

通常chunk overlapはrange情報と`structure_group`で追跡し、単なる近接だけを理由に削除しない。

## 7. Omission / truncation reason

Packageへ採用されなかったretrieval candidateには、少なくとも以下のreasonを記録する。

```text
max_items
token_budget
byte_budget
duplicate
near_duplicate
overlapping_chunk
```

各omissionには以下を保持する。

- `evidence_id`
- `source_id`
- `reason`
- budget / duplicate判定のdetail
- candidateの推定token数
- candidateのbyte数

これにより「検索されなかった」のか「検索されたがbudget等で採用されなかった」のかを区別できる。

`manual_exclude`はF-03で候補集合から除外されるoperator controlであり、Application layerではmanual include / exclude設定自体をselection controlとして保持する。F-04のbudget omissionとは区別する。

## 8. Selected item contract

採用EvidenceはF-03 candidate全体を保持したまま、Package selection metadataを追加する。

```text
candidate
  evidence_id
  source_id / snapshot_id / run_id
  content
  retrieval_score
  reasons[]
  context / provenance
selected_by
  protected | source_diversity | relevance_fill
estimated_tokens
byte_size
structure_group
related_selected_evidence_ids[]
```

`selected_by`はF-03のselection reasonを置き換えない。前者は「Packageに採用した段階」、後者は「F-03が候補にした根拠」であり、両方を保持する。

## 9. Budget semantics

budgetはhard limitとする。通常candidateはlimitを超える場合にomitし、後続のより小さいcandidateが収まる可能性を残してselectionを継続する。

protected Evidenceだけはsilent omissionしない。protected集合がlimitを超える場合はerrorにしてoperator判断へ戻す。

F-04はEvidence本文を途中で切断してbudgetへ押し込まない。Evidence IDとProvenanceを維持するため、採用単位は常に既存canonical Evidence全体とする。

## 10. F-03 / G-01との境界

F-03:
- 高Recall candidate generation
- retrieval score
- retrieval selection reason

F-04:
- bounded selection
- Source diversity
- duplicate / overlap handling
- budget usage
- omission reason

G-01以降:
- Package identity / manifest / hash
- current Knowledge carry-forwardの具体的な組込み
- export serialization
- ChatGPT向けinstructionsとの全体context配分

current Knowledge carry-forward EvidenceはG-01でF-04のprotected inputとして渡せる構造とする。F-04自体はKnowledge Versionの意味判断を行わない。

## 11. 実装

実装箇所:

- `src/sgokb/retrieval/package.py`
  - `EvidenceBudget`
  - `EvidencePackageSelector`
  - `SelectedEvidence`
  - `OmittedEvidence`
  - `estimate_tokens()`
- `Application.select_object_evidence()`

`Application.select_object_evidence()`はF-03 retrievalを内部実行し、`manual_include`をprotected Evidenceとして扱った上でbudget selectionを返す。

## 12. 検証条件

F-04完了には次を満たす。

1. token / byte / itemの3 hard limitを設定できる。
2. 1 Objectの全Evidenceを無制限に出力しない。
3. Source diversity passにより複数Sourceを可能な範囲で保持する。
4. relevance fillにより残余budgetを有効利用する。
5. manual includeをsilentに捨てない。
6. exact / near duplicateをPackage-localに抑制できる。
7. 高overlap chunkを識別できる。
8. 通常の近接chunkはSource構造groupを維持して追跡できる。
9. Evidence本文をbudget都合で途中切断しない。
10. omission reasonをcandidate単位で監査できる。
11. F-03 selection reasonとEvidence provenanceを保持する。
12. Generative LLM / Fragmentを使用しない。

次TaskはF-05 `ObjectとSource/Evidenceの明示linkを維持できるUI/CLIを設計する` とする。
