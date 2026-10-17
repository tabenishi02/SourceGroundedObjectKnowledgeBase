# N-04 AI Use Case Acceptance

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Source dataset: `benchmark/n03-real-data-vertical-slice-v1.json`
- Acceptance spec: `benchmark/n04-ai-use-cases-v1.json`
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Prerequisite: **N-04P-01〜P-06 Complete**
- Status: **Acceptance execution pending / Reference Workstation local LLM required**

## 1. Purpose

N-04では、SGOKBに保存・検索された実データKnowledgeが、単なる検索結果としてではなく、実際のAI利用へ渡したときに役立つかを確認する。

対象はTask masterで固定された3ケースである。

1. Character DataをローカルLLMへ渡してRoleplayする。
2. Work Dataから意味的に類似する別Workを検索し、AIが比較説明する。
3. Concept A/Bを取得し、ローカルLLMが両概念を組み合わせた新Characterを創作する。

N-04は新しいLLM providerをSGOKB本体へ実装するTaskではない。SGOKBのread surfaceとContext BuilderがAI利用に十分かを評価する。

```text
Canonical / Derived SGOKB
        ↓
MCP read Tool
        ↓
Search / Similarity / Context Builder
        ↓
local LLM
        ↓
AI output
```

LLM推論そのものはSGOKBの責務外であり、N-04用のchat client / prompt runnerはGit管理外のacceptance harnessとしてよい。

## 2. Scope boundary

N-04で評価するもの:

- current accepted KnowledgeをAI向けContextとして取得できるか。
- Context Builderのpurpose profileが3用途で実用になるか。
- Similarity retrieval結果を比較AI workflowへ接続できるか。
- local LLMがContext内Knowledgeを使って要求されたAIタスクを実行できるか。
- factual groundingとcreative informationの境界を維持できるか。
- provenance/current Version/canonical storeを壊さないか。

N-04で正式評価しないもの:

- Recall@K / MRR / nDCGなどのretrieval ranking品質。→ N-06
- Vector backend benchmark。→ N-06
- 1 Object processing time。→ N-05
- LLM製品間ランキング。
- 文体の好みや文学的完成度。
- SGOKBに採用されていないKnowledge coverageそのもの。coverage不足は記録し、必要に応じN-06へ送る。

## 3. Public read boundary

AI consumerはDB schemaを知ってはならない。

受入ではMCP stdio read surfaceを使う。

主要Tool:

```text
build_context
find_similar_objects
```

必要に応じて確認用に次を使ってよい。

```text
get_object
get_objects
get_object_evidence
```

Context Builder contractは`sgokb.context-builder.v1`を維持する。

受入caseで使用するpurpose:

```text
Case 1: roleplay
Case 2: comparison
Case 3: creative
```

MCP transportについてはJ-06で受入済みだが、N-04ではN-03実データDBに対して再度実transportを通す。

## 4. Evaluation data

### Case 1 — Roleplay

Object:

```text
Saber
326a97cf-47aa-4760-a7f1-07bfe639fcf0
```

理由:

- N-03で複数Sourceを持つ実Character。
- Saber / Artoria Pendragon identityとFate/stay nightでのroleをaccepted Knowledgeとして持つ。
- roleplay contextにKnowledge coverage不足がある場合も、「不足を創作factで補わない」というContext利用能力を確認できる。

### Case 2 — Similar Work comparison

Source Work:

```text
Fate/stay night
d5824d33-7008-4121-9cfe-1f95a19667fd
```

Comparison targetは手動指定しない。

`find_similar_objects`が返すcurrent Workの最上位candidateを使う。

N-03固定datasetではP-06時点でBLEACHが利用可能である。

```text
BLEACH
57db855c-574a-4b38-b474-421c165894f1
```

ただしAI入力を作る時点ではSimilarity結果からcandidateを決定し、BLEACH IDをhardcodeして検索経路を迂回しない。

### Case 3 — Creative Concept combination

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

両方を`purpose=creative`で同一Contextへ入れ、両conceptのKnowledgeから新しいCharacter案を生成する。

## 5. Local LLM policy

### 5.1 Same model for all cases

3ケースをモデルごとに都合よく切り替えない。

Reference Workstationで既に利用可能なlocal chat/instruct modelを1つ選び、3ケースで固定する。

優先:

1. LM Studio等で現在ロード済みのlocal chat model。
2. 既にインストール済みでRTX 4090上で実用的に動く一般chat/instruct model。

N-04のためだけに新しい大型モデルを無条件でdownloadしない。

モデルを選択した後、次を記録する。

```text
runtime/provider
endpoint
model identifier
model file / quantization if available
context length
GPU offload / device if available
temperature
max_tokens
seed if supported
```

### 5.2 Local-only

禁止:

- OpenAI / Anthropic / Gemini等のcloud inferenceへのfallback。
- Web Searchで不足Knowledgeを補う。
- model自身の既知knowledgeを意図的に使わせるprompt。

LM Studio OpenAI-compatible serverを使う場合の既定候補:

```text
http://127.0.0.1:1234/v1
```

まず`/v1/models`で現在のlocal modelを確認する。

### 5.3 One model retry rule

最初に固定したmodelがchat completion contractを満たせない、context長不足で入力不能、または指示追従が成立しない場合に限り、既存のより強いlocal modelへ1回だけ切替可能。

その場合:

- 1回目のfailureを削除しない。
- 切替理由を記録する。
- 2回目のmodelを3ケースすべてに固定する。

単に出力内容を気に入らないという理由でcase単位にmodel cherry-pickしない。

## 6. AI grounding rule

Case 1 / Case 2のObjectに関する事実主張は、供給したSGOKB Contextだけを正本とする。

```text
Contextにあるfact
  → factual statementとして使用可

Contextから妥当に導ける比較・解釈
  → interpretationと分かる形なら可

Contextにないfranchise knowledge
  → factual statementとして使用不可
```

Case 3はcreative use caseなので新規character detailsの創作を許す。

ただし以下を区別する。

```text
SGOKB Concept knowledge
vs
LLMが今回創作したCharacter detail
```

創作detailを「SGOKBに保存されているfact」のように表現した場合はfailureとする。

## 7. Case 1 acceptance — Character Roleplay

MCP:

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

確認:

- current accepted Version。
- purpose=`roleplay`。
- Context non-empty。
- `used_characters <= max_characters`。
- historical fallbackなし。

LLM promptは`benchmark/n04-ai-use-cases-v1.json`を正本とする。

出力Gate:

1. first-person roleplayとして成立する。
2. Contextから少なくとも2つの具体的factを利用する。
3. Contextのfactと矛盾しない。
4. Context外の重要franchise/backstory factを既知factとして足さない。
5. personality coverageが不足する場合、詳細なpersonalityを勝手に構築しない。

文体が「Saberらしいか」を主観的Gateにはしない。Knowledge coverage以上の人格再現を要求すると、SGOKBよりmodel memoryを評価してしまうためである。

## 8. Case 2 acceptance — Similar Work -> comparison

### 8.1 Similarity retrieval

MCP `find_similar_objects`をFate/stay nightへ実行する。

条件:

```text
cross_class=false
limit=5
current scope
real semantic runtime
```

returned current Workのtop candidateを選択する。

記録:

```text
source object
candidate object
rank
score
score_type
resolved version
```

Similarity scoreはretrieval signalであり、truth/confidence/preference probabilityとして扱わない。

### 8.2 Comparison context

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

出力Gate:

1. 両WorkのContextから最低1件ずつfactual materialを使う。
2. 最低1つの比較または対比を述べる。
3. 比較上の推論をstored factと混同しない。
4. accepted Knowledgeが少ない場合、その限界を明示する。
5. Context外のfranchise knowledgeをfactとして持ち込まない。
6. Similarity score semanticsを誤解しない。

「Fate/stay nightとBLEACHの内容が本当に高品質に似ているか」というranking評価はN-06へ送る。

## 9. Case 3 acceptance — Concept combination creative Character

MCP:

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

出力Gate:

1. Tsundere由来のgrounded ideaを最低1つ使う。
2. Hero's Journey由来のgrounded ideaを最低1つ使う。
3. 両方を実際のCharacter設計 / arcへ統合する。
4. 生成Characterはsource Conceptそのものの言い換えではなく新規創作である。
5. 新規name / setting / events / traitsをcreative additionと明示する。
6. ConceptについてContext外のfactを「SGOKB由来」として追加しない。

Creative outputの新規detailそれ自体はhallucination扱いしない。用途上意図された生成だからである。

## 10. Evaluation method

### 10.1 Retrieval/context layer

これは機械的に判定する。

各caseで保存:

```text
MCP request
MCP response
object/version identity
purpose
selection_policy
used_characters
omitted_items
truncated
warnings
```

### 10.2 LLM output layer

各caseでraw prompt / raw responseを保存する。

rubric itemごとに次で判定する。

```text
PASS
FAIL
NOT_APPLICABLE
```

各判定には短い根拠を付ける。

unsupported claim判定では、responseをatomic claimへ分け、少なくともfactual claimについてContext内supportを照合する。

creative detailはCase 3の`creative addition`として別分類する。

LLM自身に自己採点させた結果だけで合否を決めない。CodexがContextとraw responseを照合して最終rubricを記録する。

## 11. Evidence preservation

Git管理外:

```text
.local/n04/
  environment.json
  model.json
  mcp/
  case-1-roleplay/
    context.json
    request.json
    response.json
    evaluation.json
  case-2-comparison/
    similarity.json
    context.json
    request.json
    response.json
    evaluation.json
  case-3-creative/
    context.json
    request.json
    response.json
    evaluation.json
  canonical-before.json
  canonical-after.json
  integrity.json
  pytest.log
```

raw LLM responseはGitへcommitしない。受入文書には必要な要約・短い抜粋・評価だけ記録する。

## 12. Canonical safety

N-04はread-only AI利用試験である。

N-04開始前後で以下が不変であること。

```text
Object stable IDs
current Version IDs
accepted Knowledge
Facet / Statement / Attribute / Relation
Source / Snapshot / Evidence
Statement-Evidence grounding
provenance
```

N-04ではResult Import、Version promotion、Source mutationを行わない。

P-06ですでに生成済みのSearch Representation / Embedding / Vectorはreadに利用してよい。

## 13. Runtime sequence

1. Git head / working tree / environmentを記録。
2. `.local/n03/sgokb-n03.sqlite`とN-03 6 Objectを確認。
3. Qdrant / Harrier semantic runtimeをP-06 profileで再利用可能にする。
4. `system integrity` PASS。
5. canonical before snapshot。
6. local chat modelをinventoryし、1モデルをfreeze。
7. MCP stdio serverをN-03 DBで起動。
8. Case 1を実施・rubric評価。
9. Case 2をSimilarity→Context→LLMの順で実施・rubric評価。
10. Case 3を実施・rubric評価。
11. canonical after snapshot比較。
12. `system integrity` PASS。
13. full pytest。
14. N-04 completion判定。

## 14. Completion Gate

N-04をCompleteとする条件:

### Retrieval / Context

- 3 caseすべてMCP public read boundaryを通る。
- direct consumer-side SQLite queryでAI入力を作らない。
- current accepted Versionのみ。
- Case 2 candidateはSimilarity経由で選ばれる。
- Context budget / purpose contractを満たす。

### Local LLM

- 同じfrozen local chat modelで3 caseすべてresponseを生成。
- cloud inferenceなし。
- external web knowledge注入なし。

### Output quality

- 3 caseすべてcritical failureなし。
- Case 1はgrounded roleplayとして成立。
- Case 2はgrounded comparative explanationとして成立。
- Case 3は両Conceptを使ったcreative synthesisとして成立し、創作factを区別する。

### Safety / regression

- canonical Knowledge不変。
- `system integrity` PASS。
- full pytest 0 failed。

## 15. Failure classification

```text
A. MCP transport / Tool contract defect
B. Context Builder selection defect
C. Semantic Similarity retrieval defect
D. local LLM runtime unavailable
E. selected local model instruction-following / quality failure
F. Knowledge coverage不足
G. grounding / hallucination failure
H. canonical mutation regression
I. test / acceptance harness defect
```

判断:

- A〜C/H: SGOKB defect。N-04内で修正し再受入。
- D: runtimeを整備できなければBlocked。
- E: model selection policyの1回だけのretryを適用可。結果は両方残す。
- F: use case成立を妨げるならN-04 failure。成立するが品質余地の話ならN-06/将来coverage課題へ送る。
- G: prompt/contextを不当に緩めず、同じrubricで評価する。重大ならN-04 failure。
- I: harnessだけ修正し再実行。

## 16. Regression

最低限:

```powershell
python -m pytest `
  tests/test_j06_mcp_client_acceptance.py `
  tests/test_j04_context_builder.py `
  tests/test_j01_similarity_application.py `
  tests/test_n04p05_derived_cli.py `
  -q

python -m pytest -q
```

Production codeを変更した場合は対象focused testsとRuff / format / `git diff --check`も必須。

## 17. Completion record

PASS後、本書へ以下を追記する。

```text
Reference Workstation environment
start/end head
Qdrant / Embedding runtime
local chat model/runtime
MCP transport/version
caseごとのretrieval/context summary
caseごとのLLM output rubric
unsupported claims / coverage limitations
canonical invariance
integrity
focused/full pytest
issues/fixes
completion decision
```

Task master / Phase N preparationを次へ更新する。

```text
N-04 Complete
Next: N-05 [P0] 1 Object自動処理時間を測定する
```

N-05とN-06はN-03完了後に一部並行可能だが、Task master上の次Taskは基本順序に従いN-05とする。
