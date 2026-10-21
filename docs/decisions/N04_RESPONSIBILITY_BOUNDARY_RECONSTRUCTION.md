# N-04 Responsibility Boundary Reconstruction Decision

更新日: 2026-10-22

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0]`
- Status: **Accepted**
- Decision type: **Acceptance responsibility boundary correction**

## 1. Decision summary

N-04の正式な評価対象を、**SGOKBが外部Consumerへ正しいKnowledgeを提供できる境界まで**に限定する。

```text
Canonical / Derived SGOKB
        ↓
Retrieval / Similarity
        ↓
Context Builder
        ↓
MCP / public read boundary
        ↓
External Consumer boundary  ← N-04 formal acceptance ends here
        ↓
AI / Application inference and generation
```

外部AI / Applicationによる推論・文章生成・創作・解釈・grounding遵守は、SGOKB本体ではなくConsumer側の責務とする。

代表的なAI利用を実際に接続して観測することは維持するが、その生成品質をSGOKBのformal PASS / FAILへ直接変換しない。

## 2. Why this decision is necessary

元のN-04は、SGOKBのread surface / Context Builderと、local LLMの生成品質を同一Completion Gateへ統合していた。

しかし既存要件と実測結果を再確認すると、次が成立する。

1. SGOKBの上位目的は、Source-grounded Object Knowledgeを長期保存し、検索・比較・AI Context等へ再利用可能にすることである。
2. MCPはKnowledge Access Layerであり、推論・創作の主体ではない。
3. N-04自身も「LLM推論そのものはSGOKBの責務外」と定義していた。
4. Phase Nは「モデル性能そのものとSGOKB retrieval defectを混同しない」ことを前提としていた。
5. G-12 / G-22ではContext外claim等が発生した一方、canonical / MCP / Retrieval / Context Builderのproduction defectは確認されなかった。

したがって、Consumer生成失敗を理由としてSGOKB production codeへGrounded Generation Systemを追加し、その成立をN-04完了条件とすることは、元の責務境界を超える。

## 3. Formal SGOKB responsibility in N-04

N-04で正式評価するSGOKB責務は次とする。

### 3.1 Public Knowledge Access

- Consumerが内部SQLite schemaへ直接依存せず、public read boundaryからKnowledgeを取得できる。
- `build_context` / `find_similar_objects`等の正式Application / MCP経路を使用する。

### 3.2 Object / Version correctness

- 指定Objectをstable IDで正しく解決する。
- current accepted Versionを使用する。
- staging / rejected / unintended historical Knowledgeをsilent混入しない。

### 3.3 Context construction

- `roleplay` / `comparison` / `creative` purposeで有効なContextを構築できる。
- Context budget / contract / omission / truncation semanticsを守る。
- Context Builder自身がcanonicalに存在しないObject factを生成しない。

### 3.4 Retrieval integration

- Case 2でSimilarityのpublic経路をContext構築へ接続できる。
- Ranking quality自体はN-06で評価する。

### 3.5 Traceability

- Context内KnowledgeをObject / Version / Statement / Relation / Attribute /必要なEvidence / Sourceへ追跡できる。

### 3.6 Canonical safety

- N-04はread-only acceptanceである。
- 試験前後でcanonical Knowledge / Version / Evidence / Provenanceを変更しない。

## 4. Explicitly outside N-04 formal responsibility

以下をN-04 formal Completion Gateから除外する。

### 4.1 Knowledge coverage sufficiency

特定Objectにpersonality等のKnowledgeが保存されていないこと自体はN-04 failureではない。

ただし、canonicalに存在するKnowledgeをContext Builderが誤って取りこぼした場合はSGOKB defectである。

### 4.2 Consumer inference / generation quality

以下はConsumer側の責務とする。

- Context外factの生成
- hallucination
- 推論品質
- Roleplay品質
- 比較説明品質
- creative synthesis品質
- source fact / interpretation / creative additionの表示上の区別

### 4.3 Grounded Generation certification

以下をN-04必須要件としない。

- Atomicity classifier
- Content-Type classifier
- Source-fact verifier
- Interpretation verifier
- Certified Content
- Grounded Generation pipeline
- Presentation Generator
- model-authored output certification

これらは必要なら独立したConsumer-side / research capabilityとして扱う。

### 4.4 Other Phase N concerns

- processing performance → N-05
- Retrieval / Similarity ranking quality → N-06
- Failure / Recovery → N-07

## 5. Representative use cases retained

N-04の代表3ケースは維持する。

1. Character Knowledge → Roleplay Consumer
2. Similar Work Retrieval → Comparison Consumer
3. Concept A/B Knowledge → Creative Consumer

ただし正式に評価するのは、各Consumerが必要とするKnowledgeをSGOKB boundaryまで正しく提供できることだけである。

実際のAI Consumer実行は`Reference Consumer Demonstration`として記録できるが、結果はSGOKBのformal PASS / FAILを変更しない。

## 6. New formal completion gates

3ケースすべてについて次を満たすこと。

1. Public Boundary: PASS
2. Canonical Scope / current accepted Version: PASS
3. Purpose-specific Context Construction: PASS
4. Retrieval Integration（該当Case）: PASS
5. Traceability: PASS
6. Budget / Contract: PASS
7. Canonical Safety: PASS
8. Integrity / Regression: PASS

正式状態は次とする。

```text
PASS
FAIL
BLOCKED
```

`FAIL`はSGOKB自身のresponsibility defectに限定する。

## 7. Historical N-04 results

過去の結果は削除・改変しない。

- G-12 formal v2 `0/3 PASS`: old specification下のvalid historical result
- G-22 formal v3 `0/3 PASS`: old remediation specification下のvalid historical result
- G-25A `VALID_FAIL_NO_SELECTION`: classifier approachに対するvalid research result

これらは「当時の評価が無効だった」のではない。

**formal N-04 responsibility boundaryそのものを過剰に設定していたため、現在のCompletion Gateからsupersedeする。**

Frozen 47を新N-04完了のために実行しない。

## 8. Grounded Generation disposition

G-13以降に追加したGrounded Generation設計・実装・benchmarkは削除しない。

別Taskで次を分類する。

```text
Keep
Experimental
Move to consumer-side capability
Retire
```

N-04をCompleteにするためにGrounded Generationを完成させてはならない。

## 9. Phase N dependency correction

N-03完了後の本来の構造へ戻す。

```text
N-03 Complete
  ├─ N-04 Knowledge Access Acceptance
  ├─ N-05 Performance
  └─ N-06 Retrieval / Vector Quality
        ↓
      N-07 Failure / Recovery
```

N-04の旧failureを理由にN-05をblockしない。

## 10. Required follow-up

1. N-04 acceptance specificationをこのDecisionに合わせて再構築する。
2. Phase N Preparation / Task stateを更新する。
3. post-G12 remediation文書をhistorical / superseded stateへ整理する。
4. N-04用formal harnessをSGOKB Knowledge Access Boundaryだけを判定する形へ再構築する。
5. Reference Workstationで3代表ケースを再受入する。
6. Grounded Generation assetsの将来処遇をN-04とは別に決定する。

## 11. Current decision

```text
N-04 old acceptance specification = Superseded
N-04 = Pending re-acceptance under corrected boundary
N-05 = Ready / not blocked by N-04
N-06 = Ready after N-03
G-13..G-25 = historical remediation / research chain
G-25A selection = not required for N-04 completion
```
