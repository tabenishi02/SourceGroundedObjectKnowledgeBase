# N-04 AI Knowledge Access Boundary Acceptance

更新日: 2026-10-22

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04 [P0]`
- Status: **Pending re-acceptance under corrected responsibility boundary**
- Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Reconstruction tasks: `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
- Source dataset: `benchmark/n03-real-data-vertical-slice-v1.json`
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`
- Prerequisite: **N-04P-01〜P-06 Complete**

## 1. Purpose

N-04では、SGOKBに保存されたcurrent accepted Object Knowledgeを、**外部AI / Application / MCP Clientが実利用可能な形で正しく取得できること**を確認する。

正式な受入範囲は次で終わる。

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
```

External Consumer以降の推論・生成品質はSGOKBのformal responsibilityではない。

## 2. Responsibility boundary

### N-04で正式評価するもの

- current accepted Knowledgeをpublic read boundaryから取得できること。
- Object / Version identityが正しいこと。
- Context Builderが`roleplay` / `comparison` / `creative` purposeで正常なContextを構築できること。
- Similarity retrievalをComparison Consumer向けContextへ接続できること。
- Context内Knowledgeがcanonical Knowledge /必要なProvenanceへ追跡可能であること。
- budget / omission / truncation等のContext contractを守ること。
- read-only acceptance中にcanonical storeを変更しないこと。
- integrity / regressionが成立すること。

### N-04で正式評価しないもの

- AI Consumerのhallucination / unsupported claim。
- Roleplay品質。
- 比較説明の推論品質。
- Creative outputの品質。
- Consumerがsource fact / interpretation / creative additionを正しく表示するか。
- Objectに保存されているKnowledge量が用途に十分か。
- Recall@K / MRR / nDCG等のranking品質。→ N-06
- Vector backend benchmark。→ N-06
- 1 Object processing time。→ N-05
- Atomicity / Content-Type classifier。
- Source-fact / interpretation verifier。
- Grounded Generation certification pipeline。

Knowledge coverage不足は観測情報として記録してよいが、SGOKB N-04 FAILへ変換しない。

## 3. Public read boundary

AI / Application ConsumerはDB schemaを知る必要がないことを確認する。

主要Tool:

```text
build_context
find_similar_objects
```

必要に応じて確認用に次を使用できる。

```text
get_object
get_objects
get_object_evidence
```

Context Builder contractは現行public contractを使用する。

代表purpose:

```text
Case 1: roleplay
Case 2: comparison
Case 3: creative
```

consumer入力をdirect SQLite queryで作成してはならない。

## 4. Evaluation data

### Case 1 — Character → Roleplay Consumer

Object:

```text
Saber
326a97cf-47aa-4760-a7f1-07bfe639fcf0
```

実行:

```text
build_context(
  object_ids=[Saber],
  purpose="roleplay",
  max_characters=12000,
  include_attributes=true,
  include_relations=true,
  include_evidence_refs=false
)
```

formal PASS条件:

- stable Object IDを正しく解決する。
- current accepted Versionを使用する。
- `purpose=roleplay`のContext contractを満たす。
- budgetを超えない。
- unrelated / rejected / unintended historical Knowledgeを混入しない。
- Context Builder自身がcanonicalにないSaber factを生成しない。
- Context内Knowledgeをcanonical Object / Versionへ追跡できる。

次はformal Gateではない。

- AIがSaberらしく話すか。
- personality / speech pattern等のKnowledge量が十分か。
- Consumer AIがContext外knowledgeを生成するか。

## 5. Case 2 — Similar Work → Comparison Consumer

Source Work:

```text
Fate/stay night
d5824d33-7008-4121-9cfe-1f95a19667fd
```

手順:

1. `find_similar_objects`をpublic pathで実行する。
2. current Workのtop candidateを結果から選択する。
3. candidate IDをhardcodeしてretrievalを迂回しない。
4. source + candidateを`purpose=comparison`で`build_context`へ渡す。

Context:

```text
build_context(
  object_ids=[source, retrieved_candidate],
  purpose="comparison",
  max_characters=24000,
  include_attributes=true,
  include_relations=false,
  include_evidence_refs=true
)
```

formal PASS条件:

- Similarity public pathが利用できる。
- returned candidateをvalid current Objectとして解決できる。
- 両Workを同一Contextへ渡せる。
- current accepted Versionだけを利用する。
- evidence refs要求時にpublic contractで取得できる。
- budget / Context contractを守る。
- unrelated / rejected / unintended historical Knowledgeを混入しない。

次はformal Gateではない。

- candidateが人間評価で最も似ているか。→ N-06
- AI Consumerの比較説明が正しいか。
- AI ConsumerがContext外franchise knowledgeを使用するか。

## 6. Case 3 — Concept A/B → Creative Consumer

Concept A:

```text
Tsundere
8c83f986-f491-41a8-8645-9f71dd5874b9
```

Concept B:

```text
Hero's Journey
fee32007-0f92-449a-ba21-4ec2f78d1cd4
```

Context:

```text
build_context(
  object_ids=[Tsundere, Hero's Journey],
  purpose="creative",
  max_characters=24000,
  include_attributes=true,
  include_relations=true,
  include_evidence_refs=false
)
```

formal PASS条件:

- 両Conceptをstable Object IDで解決できる。
- 両方のcurrent accepted Versionを使用する。
- 同一creative Contextへ両Conceptを含められる。
- Context内でObject境界が識別可能である。
- budget / Context contractを守る。
- unrelated / rejected / unintended historical Knowledgeを混入しない。
- Knowledgeをcanonical Object / Versionへ追跡できる。

次はformal Gateではない。

- AI Consumerが両Conceptを上手く統合するか。
- 新Characterが魅力的か。
- Consumerが創作detailを明示的にlabelするか。

## 7. Knowledge coverage handling

Knowledge coverageはN-04 formal failureではない。

例:

```text
Saber
  identity      available
  role          available
  personality   not available
```

これは`coverage observation`として記録する。

一方、canonical DBに存在するKnowledgeをContext Builderが誤って返さない場合はSGOKB defectである。

判定基準:

```text
Knowledge does not exist in canonical store
  -> not N-04 failure

Knowledge exists but public Context path loses / corrupts it
  -> N-04 failure
```

## 8. Reference Consumer Demonstration

代表AI利用を実際に確認するため、任意でlocal LLM等へ3 Contextを渡してよい。

結果例:

```text
consumer: <runtime/model>
roleplay: PASS / FAIL
comparison: PASS / FAIL
creative: PASS / FAIL
```

この結果は参考情報であり、N-04 formal PASS / FAILを変更しない。

Consumer側のfailureは必要に応じて次へ分類する。

```text
consumer model capability
prompt / orchestration
consumer grounding policy
consumer presentation policy
knowledge coverage observation
```

N-04の修正理由にはしない。

## 9. Evidence preservation

formal runでは最低限次を保存する。

```text
.local/n04/
  environment.json
  mcp/
  case-1-roleplay/
    context.json
    request.json
    evaluation.json
  case-2-comparison/
    similarity.json
    context.json
    request.json
    evaluation.json
  case-3-creative/
    context.json
    request.json
    evaluation.json
  canonical-before.json
  canonical-after.json
  integrity.json
  pytest.log
```

Reference Consumer Demonstrationを行う場合、そのprompt / response / evaluationはformal boundary evidenceとは別directoryに保存する。

## 10. Canonical safety

N-04はread-only acceptanceである。

試験前後で少なくとも次が不変であること。

```text
Object stable IDs
current Version IDs
accepted Knowledge
Facet / Statement / Attribute / Relation
Source / Snapshot / Evidence
Statement-Evidence grounding
provenance
```

Result Import、Version promotion、Source mutationをN-04 formal run中に行わない。

## 11. Formal completion gates

N-04をCompleteとする条件:

### Gate 1 — Public Boundary

3 caseすべてpublic read boundaryを使用し、direct consumer-side SQLite queryを行わない。

### Gate 2 — Canonical Scope

current accepted Versionだけを利用し、unintended historical / rejected / staging dataを混入しない。

### Gate 3 — Context Construction

`roleplay` / `comparison` / `creative`の3 purposeでvalid Contextを構築できる。

### Gate 4 — Retrieval Integration

Case 2でSimilarity結果をpublic pathからComparison Contextへ接続できる。

### Gate 5 — Traceability

Context内KnowledgeのObject / Version /必要なProvenanceを確認できる。

### Gate 6 — Budget / Contract

Context budget、required metadata、omission / truncation semanticsを満たす。

### Gate 7 — Canonical Safety

before / after canonical snapshotが不変。

### Gate 8 — Integrity / Regression

`system integrity`と関連focused tests / full pytestがPASSする。

## 12. Result states

```text
PASS
FAIL
BLOCKED
```

### PASS

SGOKB Knowledge Access Boundaryが全formal Gateを満たした。

### FAIL

SGOKB自身の責務にdefectがある。

例:

- wrong Object / Version
- unintended historical Knowledge混入
- Context Builderによるcanonicalにないfact生成
- public MCP/Application contract破損
- Similarity resultをContextへ接続不能
- read acceptanceによるcanonical mutation

### BLOCKED

formal evaluationに必要なSGOKB runtimeが利用できず判定不能。

## 13. Historical acceptance results

### Original N-04 run — 2026-10-18

実MCP / local LLMで3ケースを実施し、Consumer outputにContext外claim等が発生したため、旧仕様ではN-04 Failedと判定した。

同runではcanonical invariance / integrity / regressionはPASSし、SGOKB transport / Context / Similarity / read-only contractにproduction defectは観測されなかった。

この結果は旧仕様下のvalid historical evidenceとして保持する。

### G-12 formal v2 re-acceptance

```text
run_id: 20261018T213810+0900
0 / 3 Case PASS
```

old generation-quality Gate下のvalid historical result。

### G-22 formal v3 re-acceptance

```text
0 / 3 Case PASS
```

post-G12 Grounded Generation remediation specification下のvalid historical result。

### G-25A classifier selection

```text
VALID_FAIL_NO_SELECTION
```

Residual Atomicity / Content-Type classifier selection approachに対するvalid research result。

これらは削除しないが、現行N-04 Completion prerequisiteではない。

## 14. Superseded requirements

次は現行N-04 formal Gateとしてsupersededとする。

```text
same local LLM must generate 3 successful outputs
consumer unsupported claim = SGOKB formal failure
consumer creative labeling = SGOKB formal failure
Atomicity classifier required
Content-Type classifier required
source-fact verifier required
Grounded Generation v3/v4 completion required
Frozen 47 confirmation required for N-04 completion
```

## 15. Current state

```text
N-04 prerequisite N-04P-01..P-06 = Complete
N-04 old acceptance = Historical Failed
N-04 current acceptance = Pending re-execution
N-05 = Ready / not blocked by N-04
N-06 = Ready
```

Next work:

`N-04R-03 — formal harness reconstruction`
