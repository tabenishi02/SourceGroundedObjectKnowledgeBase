# K-04 UPDS Context / Profile Evaluation

更新日: 2026-10-14

Status: Accepted

対象Task: `K-04 [P2] UPDS向けContext/Profileを追加するか評価する`

関連正本:

- `docs/decisions/K01_UPDS_OBJECT_REFERENCE_USE_CASE.md`
- `docs/decisions/K02_STABLE_OBJECT_ID_REFERENCE_VERIFICATION.md`
- `docs/decisions/K03_SEMANTIC_INDEX_OWNERSHIP_VERIFICATION.md`
- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`
- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/planning/PHASE_K_PREPARATION.md`

---

## 1. Decision

K-04の結論は次とする。

> **現時点ではUPDS専用Context/ProfileをSGOKBへ追加しない。K-01で確定した`get_objects` + explicit Facet subsetを標準連携経路として維持し、LLM投入用のContext圧縮が必要な場合のみ既存の汎用`build_context`を利用する。**

専用Profileを追加するだけのUPDS固有要件は、K-01〜K-03および現行UPDS構想から確認できなかった。

UPDS runtime / DB schema / Personal Inference algorithmが未実装であるため、将来具体的なconsumer workloadから汎用契約の不足が実証された場合のみ再評価する。

---

## 2. 評価対象

Phase K Preparationで候補とした既存access surfaceを評価した。

```text
get_objects(facets=[...])
build_context(purpose="analysis", facets=[...])
get_object_relations
get_object_evidence
```

K-01の最小ユースケースは次である。

```text
Known Character object_ids
  ↓
get_objects
  facets = [values, personality, themes]
  include_relations = false
  include_evidence_refs = false
  ↓
resolved_version_id + structured Object Knowledge
  ↓
UPDS Personal Inference
```

この経路ではSGOKB側でPersonal Inferenceを行わない。

---

## 3. `get_objects`の評価

### 3.1 適合点

`get_objects`はUPDSの標準Knowledge取得として次を満たす。

- stable `object_id`によるbatch read。
- explicit Facet subset。
- current / pinned Version。
- Objectごとの`resolved_version_id`。
- Relation / Evidence referenceの明示的省略。
- structured responseのため、UPDS側でFacet / Statementを機械的に扱える。
- Context文字数budgetによるKnowledge omissionを受けない。

したがってPersonal Inferenceのcanonical input取得には`build_context`より`get_objects`を優先する。

### 3.2 確認した汎用改善余地

現行`get_object` / `get_objects`はFacetを絞ってもstructured attributes自体を省略するpublic optionを持たない。

したがって、

```text
facets = [values, personality, themes]
```

は「Facet subsetを限定する」という意味であり、wire payload全体がその3 Facetだけになることを意味しない。

将来attributes量が大きくなりUPDSを含むconsumerで転送効率が問題化した場合は、

```text
include_attributes = false
```

相当を**汎用`get_object(s)` contractの改善候補**として評価する。

これはUPDS固有問題ではないため、K-04ではUPDS専用Profile追加理由としない。

---

## 4. `build_context`の評価

既存Context Builderは次を提供する。

- purpose: `general / analysis / comparison / roleplay / creative`
- explicit Facet override
- current / pinned Version
- `include_attributes`
- `include_relations`
- `include_evidence_refs`
- deterministic selection order
- character budget
- multi-object equal-share budget

UPDS向けに例えば次を指定できる。

```json
{
  "purpose": "analysis",
  "object_ids": ["char-A", "char-B", "char-C"],
  "facets": ["values", "personality", "themes"],
  "include_attributes": false,
  "include_relations": false,
  "include_evidence_refs": false,
  "max_characters": 12000
}
```

explicit Facet overrideがpurpose profileを置き換えるため、`analysis` profileに`personality`が既定Facetとして含まれなくても問題にならない。

### 4.1 UPDS標準経路にしない理由

Context BuilderはLLMへ渡す量を決定論的に削減する機能であり、budget超過時にはKnowledge itemをomitする。

Personal Inferenceの入力収集段階でこの省略を標準化すると、

```text
Object Aのvalues Statement 3がbudgetでomit
```

のような状態が分析結果へ影響し得る。

したがって、UPDSのcanonical semantic enrichmentは`get_objects`で行い、`build_context`は取得済みKnowledgeを下流LLMへ投入する必要がある場合の**任意のpresentation / context selection layer**とする。

---

## 5. 専用Profileが不要な理由

Phase K Preparationで示した専用Profile追加候補を評価した。

### 5.1 同一Facet指定が複雑か

K-01ではCharacterについて次の3 Facetだけである。

```text
values
personality
themes
```

これはclient側の定数として十分単純であり、専用server profileへ昇格させる必要はない。

Work等で別Facet集合を利用する場合もexplicit Facet listで表現できる。

### 5.2 汎用Contextに不要情報が多いか

`build_context`ではexplicit Facet overrideおよびattributes / relations / evidence refsのboolean overrideがある。

不要情報の多くは既存optionで除外可能である。

Context Builderはsummaryを常に候補に含めるため、将来summary overheadが明確な問題になれば汎用`include_summary`相当を検討できる。

これもUPDS専用ProfileではなくContext Builder一般の改善として扱う。

### 5.3 UPDS側でdeterministic selection再実装が必要か

LLM用Context selectionが必要なら既存`build_context`を利用できる。

UPDSが独自にFacet priority / character budget / omission policyを再実装する必要はない。

### 5.4 Personal semanticsが必要か

不要であり、導入してはならない。

次を専用Profile追加理由としない。

```text
User ProfileによるFacet順位変更
Preference HypothesisによるKnowledge ranking
Selection historyによるObject ranking personalization
Personal embeddingによるSGOKB Knowledge selection
```

これらはK-03で分離したPersonal Inference ownershipを破る。

---

## 6. 標準利用規則

### 6.1 Semantic enrichment

標準:

```text
get_objects
```

用途:

- Selection Eventに対応するObject Knowledge取得。
- Semantic Observation生成前のstructured input。
- current / pinned Versionの再現。

### 6.2 Relationが必要な場合

```text
get_object_relations
```

Relation patternをPersonal Inference材料に使う場合だけ追加取得する。

### 6.3 Evidenceが必要な場合

```text
get_object_evidence
```

通常分析ではaccepted Knowledgeを使用し、監査・説明・再確認で必要な場合に限る。

### 6.4 LLM Contextが必要な場合

```text
build_context
```

既定purposeに意味を依存せず、UPDS用途では必要Facetを明示指定することを推奨する。

---

## 7. 専用Profile再評価のtrigger

次のいずれかが実UPDS実装後に測定・実証された場合に再評価する。

1. 複数のUPDS use caseで同一の10個以上の引数組合せが反復し、client実装の不整合が実際に発生する。
2. 汎用`build_context`のselection policyではPersonal Inference用LLM入力の再現性を満たせない。
3. 汎用Facet overrideでは表現できない、World/Object Knowledge側の新しいdeterministic selection semanticsが必要になる。
4. payload / latency測定で汎用contractが明確なボトルネックとなり、generic option追加よりprofile化の方が契約を単純化できる。
5. 複数consumerでも再利用できる一般的な分析profileとして昇格できる。

次はtriggerとしない。

- UPDSだからという理由だけ。
- ユーザー嗜好をSGOKB側で推論したい。
- User ProfileでSGOKB rankingをpersonalizeしたい。
- Preference HypothesisをSGOKB側Contextへ保存したい。

---

## 8. UPDS未実装による留保

現時点のUPDSは構想段階であり、実traffic / payload / LLM workflowが存在しない。

したがってK-04の判断は、

```text
専用Profileは永久に不要
```

ではなく、

```text
現時点では追加を正当化する実証的不足がないため追加しない
```

である。

UPDS実装後のcross-repository integrationでは、K-01で定義した標準経路から開始し、必要性を測定してから拡張する。

---

## 9. Acceptance result

評価結果:

| 観点 | 判定 |
|---|---|
| Character最小Facet取得 | 汎用`get_objects`で成立 |
| batch | 成立 |
| current / pinned Version | 成立 |
| Relation optional retrieval | 成立 |
| Evidence optional retrieval | 成立 |
| deterministic LLM context | 汎用`build_context`で成立 |
| explicit Facet selection | 成立 |
| attributes省略 | `build_context`では成立、`get_objects`は汎用改善余地あり |
| Personal inference separation | K-03契約で成立 |
| UPDS専用Profile必須性 | **認められない** |

**K-04 Acceptance: PASS — UPDS専用Context/Profileは追加しない。**

---

## 10. Definition of Done

- [x] K-01の標準`get_objects`経路を再評価した。
- [x] J-04 Context Builder capabilitiesを照合した。
- [x] explicit Facet overrideでUPDS候補Facetを表現できることを確認した。
- [x] Relation / Evidence / attributesのoptional boundaryを評価した。
- [x] 専用Profileを正当化する不足がないことを確認した。
- [x] `get_objects`のattributes省略不可を汎用改善候補として分離した。
- [x] Context Builderのsummary常時候補を汎用改善候補として分離した。
- [x] Personal Profile / PreferenceをSGOKBへ持ち込まないことを再確認した。
- [x] 将来の再評価triggerを定義した。
- [x] Phase KのK-01〜K-04を完了可能な状態にした。
