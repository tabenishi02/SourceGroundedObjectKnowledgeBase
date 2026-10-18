# N-04 AI Use Case Acceptance

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Source dataset: `benchmark/n03-real-data-vertical-slice-v1.json`
- Baseline acceptance spec: `benchmark/n04-ai-use-cases-v1.json`
- Current frozen acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Formal harness: `benchmark/n04-v2-formal-harness-v1.json`
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Prerequisite: **N-04P-01〜P-06 Complete**
- Status: **Failed (2026-10-18) — critical grounding failures; not Complete**

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


## 18. Reference Workstation execution — 2026-10-18

### Decision

**N-04 Failed。Completeにしない。** Retrieval / Context / local inference / integrity / automated regressionは成立したが、最終モデルのCase 1 / Case 2にcriticalなContext外factual claimが残った。Case 3もArc outlineの創作範囲の明示要件を満たさなかった。promptやrubricを緩めず、許可された1回のモデル切替を消費した時点で終了した。

N-04P-01〜P-06 Completeは維持する。N-05への移行条件は満たしていない。PR #39はDraftを維持し、PR #36〜#39はmergeしない。

### Environment / frozen model / public boundary

- Windows 11 Home 10.0.26300、Python 3.10.6、RTX 4090。start head: `56d34a4d3e155a01af52b268c3e04240a84da2ec`。
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`。production DBへの操作なし。
- P-06のHarrier model `microsoft/harrier-oss-v1-0.6b` / revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee` / 1024 dimensions / local-onlyを維持。Qdrant 1.19.2、HTTP 6333 / gRPC 6334、collection prefix `sgokb_n03_eval`を再利用した。
- 開始時の6 Object、Search Representation / Embedding / Vector 6/6 ready、missing Embedding=0、Qdrant available、integrity PASSをpublic CLIで確認した。
- LM Studio 0.4.25.0、endpoint `http://127.0.0.1:1234/v1`。cloud inference / Web Searchによる補完なし。新規chat model downloadなし。
- 初回は既存Phi-4 Q4_K_S（`microsoft/phi-4-gguf/phi-4-Q4_K_S.gguf`、identifier `sgokb-n04-phi4`）。context 8192、GPU offload=max。
- 1回だけ既存のより大きいgeneral instruct model Mistral Small 3.2 24B Instruct Q4_K_M（`lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-GGUF/Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf`、identifier `sgokb-n04-mistral32`）へ切替。context 8192、parallel=1、GPU offload=max。
- 初回の基本response contract違反（語数不足、interpretationのラベル不足、creative addition明示不足）を切替理由とし、初回のunsupported claimも別途FAILとして保存した。3ケースすべてを同じ最終モデルで再試験し、case別model選択はしていない。
- benchmark promptは原文のまま。temperature / max_tokensはCase 1=0.2/500、Case 2=0.0/700、Case 3=0.2/900。各requestへseed=20261018を送信した（決定性の品質保証ではない）。3 responseともfinish_reason=stop、非空。
- MCP Python SDK 2.3.0、protocol `2026-07-28`、stdio transport、server sgokb 0.2.0。Local SDK client → `sgokb mcp serve --semantic-runtime` → MCPReadAdapter → KnowledgeReadApplicationの実chainを使用した。
- consumerはSQLiteをqueryせず、AI入力をMCP Toolのstructured Contextだけから構成した。DB before/after読取りはconsumerと分離した検証scriptだけが担当した。

### Initial Phi-4 attempt

3ケースともFAILとしてraw出力、Context、request、claim照合、rubricを`.local/n04/attempt-1-phi4/`へ保全した。

- Case 1: first-personと最低2 factは成立したが、指定100〜180語に不足し、ContextにないShirouの姓や他Servantとの戦闘設定を追加した。
- Case 2: 両Workのfactと限界表示は使えたが、Contextにないmagical servants等を追加し、解釈を明示しなかった。
- Case 3: 概念統合と新規Characterは成立したが、創作detailの明示範囲が不足した。

### Final Case 1 — Saber Roleplay

MCP `build_context`はpurpose=roleplay、640/12000 characters、truncated=false、current accepted Versionを返した。summary identity-1とrole grounded-1により、Saber / Artoria Pendragon、Fate/stay nightのfictional character、sword-wielding Servant、Shirouとのcontractを含む。personality等はnot_analyzed。

最終出力はfirst-personでidentity / sword / contractを使ったが、Holy Grail WarでShirouのprotectorとして戦う設定と、Artoriaの正体が作中で広く知られていない設定を追加した。これらは実際に供給したSaber Contextにない。ほかのObject Contextやmodel memoryで補ってよいという契約にはしていない。

atomic claim照合抜粋:

| Claim | Context support | Supported |
|---|---|---|
| Saber = Artoria Pendragon | summary identity-1 | true |
| sword-wielding Servant contracted to Shirou | role grounded-1 | true |
| ShirouのprotectorとしてHoly Grail Warで共闘する | supplied Saber Contextにはない | false |
| Artoriaの正体は作中で広く知られていない | supplied Saber Contextにはない | false |

**Case 1 FAIL / G: critical unsupported franchise/backstory facts。** personalityの薄さ自体はfailureにしていない。

### Final Case 2 — Similar Work → comparison

MCP `find_similar_objects`から最上位current Workを選択した。sourceはFate/stay night、candidateはBLEACH、rank 1、score 0.646960258、score_type `cosine_similarity`。candidateをLLM入力でhardcodeしていない。

両Workはcurrent accepted Version、purpose=comparison、1513/24000 characters、truncated=false、Evidence refsあり、Relationsなし。

出力は指定4 headings、両Workのmedium / author / protagonist / branching等とdata limitationを使った。しかし、Contextにない以下をstored fact同様に述べた。

- magiが歴史上のHeroesを召喚してHoly Grailのため戦うこと。
- Hollowsがmalevolent spiritsであること。
- Soul Reapersがhuman worldとafterlifeのbalanceを維持すること。
- 両protagonistがextraordinary powersを得るという共通化（Shirou側は供給Contextで未支持）。

**Case 2 FAIL / G: critical outside-knowledge claims、E: interpretation labeling不足。** cosine similarityをtruth / confidence / preference probabilityと誤説明してはいない。

### Final Case 3 — Concept combination

両Conceptはcurrent accepted Version、purpose=creative、1299/24000 characters、truncated=false。Tsundereのharsh-to-warmとHero's Journeyのadventure / crisis / changed returnがContextにある。

出力はKaelani Solarisという新規Characterとinterstellar engineerの物語を作り、冷淡さから信頼・温かさへの変化を危機と帰還に統合した。Original characterのname / setting / background / appearance / personalityはCreative additionと明示した。

一方、Arc outline内の新規eventには、それらもSGOKB factではなくcreative additionだという明示がない。benchmark promptが両sectionで要求したexplicit separationには未達だった。十二段階の物語・rogue AI等は意図された創作として分類し、それ自体をhallucinationにはしていない。Concept mappingにunsupportedなsource factを追加したという判定でもない。

**Case 3 FAIL / E: explicit Arc outline labeling contract未達。critical unsupported-source-claimなし。**

### Final model rubric — Codex review

モデル自己採点ではなく、保存されたContext / raw response / 同一benchmark rubricをCodexが照合した。

| Case | Item | Result | Reason |
|---|---|---|---|
| Case 1 | first_person | PASS | Uses I am as Saber. |
| Case 1 | two_concrete_context_facts | PASS | Alias identity, sword-wielding Servant, and Shirou contract are grounded. |
| Case 1 | no_material_context_contradiction | PASS | No direct contradiction; absent support is separately failed. |
| Case 1 | no_outside_franchise_backstory_facts | FAIL | Holy Grail War protection/battle role and secret identity are not in this supplied Saber Context. |
| Case 1 | no_detailed_personality_from_memory | PASS | Explicitly acknowledges missing personality and background details. |
| Case 2 | fact_from_each_Work | PASS | Uses visual novel/Type-Moon and manga/Tite Kubo facts plus both protagonists. |
| Case 2 | comparison_or_contrast | PASS | Contrasts media and route structure and mentions shared Japanese origin. |
| Case 2 | interpretation_separate_from_stored_fact | FAIL | Shared extraordinary-powers framing is not labeled interpretation and is not supported for Shirou. |
| Case 2 | coverage_limits | PASS | Explicitly describes sparse data and not_analyzed themes/relationships. |
| Case 2 | no_outside_franchise_knowledge | FAIL | Adds magi summoning historical Heroes, Grail battle details, Hollows as spirits, and human/afterlife balance not in either Context. |
| Case 2 | cosine_score_semantics | PASS | Does not characterize the score as truth/confidence/preference probability. |
| Case 3 | Tsundere_grounded_idea | PASS | Mapping uses harsh personality gradually revealing warmth. |
| Case 3 | Hero_Journey_grounded_idea | PASS | Mapping uses adventure, decisive crisis, changed return. |
| Case 3 | integrates_both_in_design_and_arc | PASS | Aloof engineer learns trust during crisis and returns warmer. |
| Case 3 | new_original_character | PASS | Invents Kaelani Solaris, setting, engineer/cybernetic arm and quest. |
| Case 3 | explicit_creative_additions_in_both_sections | FAIL | Original character details are labeled Creative addition; Arc outline does not explicitly state its invented events are non-SGOKB creative additions as required by the unchanged prompt. |
| Case 3 | no_unsupported_Concept_fact_attributed_to_SGOKB | PASS | Concept mapping stays within two supplied statements; invented arc stages are not explicitly claimed to be stored Concept facts. |

各caseのatomic claim / creative-vs-grounded分類と短い理由はGit管理外`evaluation.json`へ保存した。

### Safety / regression

- canonical 52 tableとderived tableの全内容はbefore/after完全一致。Object stable IDs / current Version / accepted Knowledge / Facet / Statement / Attribute / Relation / Source / Snapshot / Evidence / grounding / provenanceも不変。
- `system integrity`は前後ともPASS。foreign key違反0件。
- 指定focused regression: **27 passed / 0 failed** (6.74s)。
- full pytest: **361 passed / 0 skipped / 0 failed** (128.28s)。
- production code / test / benchmark prompt / rubricは変更していない。新規skip / xfailなし。`git diff --check` PASS。
- raw request / response / Context / model metadata / logsは`.local/n04/`に保存し、Gitへ追加しない。

### Issues / handoff

- Dは解消: LM Studio起動時に継承された`ELECTRON_RUN_AS_NODE=1`を、service子processだけで外した。親環境は復元した。新規runtime/modelは導入していない。
- I: LM Studio `load`にはfile pathではなくmodel key `phi-4`が必要だった。同じmodelで引数だけ訂正したため、これはmodel切替に数えていない。
- E/G: 同じ固定Contextだけからfactを選ぶというlocal modelの指示追従・groundingが不十分。2モデルのfailureを残し、追加切替やprompt調整で結果を隠していない。
- F: Saberはidentityとroleの2 Statementだけでpersonality未分析。両Workもsummary/overall以外の比較材料が薄い。利用可能性はあるが、このcoverage不足をmodel memoryで埋めることは許容しない。
- N-06へ: P-06未hitの`King of Knights` / `character archetype`、少数Workだけのranking観測、未分析Facet / personality / comparative coverageを引き渡す。今回のSimilarity rank 1を正式ranking品質合格とは扱わない。

**Completion decision: N-04 Failed (2026-10-18)、N-05へは移行しない。** SGOKB transport / Context / Similarity / read-only contractにproduction defectは観測していない。合格には、同じgroundingとcreative-separation条件を満たす再受入が必要である。


## N-04G-12 — Frozen v2 formal re-acceptance (2026-10-18)

**G-12 Complete (formal re-acceptance executed) / N-04 Failed / N-05 blocked.**

### Execution identity and validity

- run_id: `20261018T213810+0900`
- Formal start: `2026-10-18T21:41:05.251722+09:00`, immediately before the first Case 1 MCP request after all preflight/start evidence was saved.
- Start/end HEAD: `843c0332456a7857d567510b4a15162b645293ce` (identical).
- Branch: `phase-n/n04-prerequisite-derived-search`, fast-forward synchronized before preflight; working tree clean at formal start/end.
- Evidence root: `.local/n04-v2/runs/20261018T213810+0900/` (Git-ignored).
- Windows 11 / Python 3.10.6 / RTX 4090 24GB / LM Studio 0.4.25.0; generator `sgokb-n04-mistral32` and semantic validator `sgokb-n04-phi4` used with the exact G-11 load profiles, seeds and case parameters.
- Harrier pinned revision/local-only and Qdrant 1.19.2 used through MCP SDK 2.3.0, protocol 2026-07-28, `python -m sgokb mcp serve --semantic-runtime`.
- No cloud/Web/other-model fallback. Consumer Knowledge inputs came only from MCP public read tools, not direct SQLite reads. Preflight SQL was restricted to dataset identity safety checks and did not supply AI Knowledge.
- All Git-managed files, frozen harness and local execution/review helper hashes remained unchanged throughout formal execution. All required/conditional artifacts exist; `overall-evaluation.json` and `git-end.json` were saved before documentation changes.
- Formal run **valid**. No execution SYSTEM/HARNESS defect invalidated the run; infrastructure does not require G-11 reopening. Product/semantic-validation failures below require separate remediation review, not changes to this frozen run.

A separate preflight-only attempt (`20261018T213643+0900`) failed before any formal Case request: its identity-only read connection left an empty WAL sidecar. SQLite checkpoint/close returned `(0, 0, 0)` and removed the sidecar. The Git-ignored helper connection lifecycle was corrected before repeating preflight; no frozen setting or tracked file changed. Failed preflight evidence remains in its original run directory. The successful formal run passed the complete preflight, including neutral structured-output smoke tests for both frozen models.

### Manual formal rubric and terminal outcomes

Each frozen retrieval/output/critical-failure item was reviewed against the saved Context, K mapping, raw units, validation and rendered output, independently of model verdicts. Each case's `rubric.json` records PASS/FAIL/NOT_APPLICABLE, reasons, unit/K references and evidence paths. Machine ACCEPTED alone does not establish formal PASS.

| Case | Machine terminal | Attempts / retries | Formal verdict | Finding |
|---|---|---|---|---|
| 1 Saber roleplay | ACCEPTED | 1 / 0 | FAIL | Unsupported material facts survived validation and rendering. |
| 2 Similar Work comparison | REJECTED | 2 / 1 | FAIL | Unsupported claim on Attempt 1; missing support refs on Attempt 2; unsupported interpretation premises also observed. |
| 3 Concept combination | REJECTED | 2 / 1 | FAIL | Both attempts failed V0 `missing_presentation_label`; creative block label remained null. |

All retrieval/context gates passed: current accepted Versions, correct purposes, traceable K references and budgets (Case 1: 640/12000; Case 2: 1513/24000; Case 3: 1299/24000), with no truncation or historical fallback.

**Case 1:** U1/K4 is grounded. U2 cites K5, which supports sword-wielding Servant contracted to Shirou, but not the additional Holy Grail War battle claim. Phi-4 nevertheless returned `entailed`. U3 asserts duty/loyalty and a deeper relationship without K support under `stylistic_expression`; Phi-4 returned `role_valid`. These unsupported propositions reached `rendered.txt`. No direct contradiction was required for FAIL: unsupported material facts alone violate the frozen gate. No manual retry was added after the controller returned ACCEPTED.

Evidence: `case-1-roleplay/grounded-context.json`, `attempt-1/raw-output.txt`, `attempt-1/semantic-validator/unit-002/`, `unit-003/`, `attempt-1/validation.json`, `rendered.txt`, `rubric.json` beneath the run root.

**Case 2:** actual MCP `find_similar_objects` rank 1 selected BLEACH (current Work), score `0.6469602584838867`, `score_type=cosine_similarity`; the comparison target was not hardcoded. Attempt 1 U2 failed V4 `UNSUPPORTED_CLAIM`. The single permitted retry used unchanged Context/model/settings/task/schema plus only production `build_retry_feedback()`. Attempt 2 U1 had empty support refs and failed V2 `MISSING_REQUIRED_SUPPORT`; its fantasy-genre claim was unsupported. U7's destiny/personal-growth/linear-narrative premises were absent from K5/K10 despite a machine `derived_supported` classification. Interpretation was structurally separated; similarity score semantics were not misrepresented. Neither rejected attempt was rendered.

Evidence: `case-2-comparison/similarity-request.json`, `similarity-response.json`, `candidate-selection.json`, `retry-feedback.json`, both `attempt-*/` trees, `terminal.json`, `rubric.json`.

**Case 3:** both Concepts contributed grounded ideas, and raw candidates combined them in a new fictional character/arc. However, B2 `presentation_role=creative` retained `label=null` in both attempts; Attempt 2 also omitted the interpretation label. Production parsing rejected both at V0 `VALIDATION_CONTRACT_ERROR / missing_presentation_label`, before semantic validation. No repair, partial salvage, further retry or rendering occurred. Invented character events are intentional creative material; they are not classified as unsupported source Concept facts. The failure is the required visible presentation contract, not a lack of source citations for permissible invention.

Evidence: `case-3-creative/attempt-1/raw-output.txt`, `attempt-2/raw-output.txt`, both parse-error/validation/decision records, `retry-feedback.json`, `terminal.json`, `rubric.json`.

### Canonical safety and Reference Workstation regressions

Canonical DB was quiescent without an active WAL at both hash observations:

```text
before SHA-256: 0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d
after SHA-256:  0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d
equal: true
```

`system integrity` before/after: **PASS**, SQLite integrity `ok`, foreign-key violations 0.

| Exact regression command | Reference Workstation result |
|---|---|
| `python -m pytest -q tests/test_n04_grounded_generation.py` | 21 passed / 0 failed (0.55s) |
| `python -m pytest -q tests/test_j06_mcp_client_acceptance.py tests/test_j04_context_builder.py tests/test_j01_similarity_application.py tests/test_n04p05_derived_cli.py` | 27 passed / 0 failed (8.22s) |
| `python -m pytest -q` | 382 passed / 0 skipped / 0 failed (132.68s) |
| `python -m ruff check src/sgokb/grounding src/sgokb/application_grounding.py tests/test_n04_grounded_generation.py` | PASS |
| `git diff --check` | PASS |

All five exit codes were 0; stdout/stderr/results are in `regression/`. Full pytest emitted two local-Qdrant warnings about payload indexes and exact-search parameters; no tests failed, skipped or were weakened to pass. Regression success does not override the real-model formal rubric failures.

### Completion decision and next work

**0/3 formal Case PASS; N-04 remains Failed / not Complete. N-04G-12 is Complete as an executed valid formal re-acceptance; N-05 remains blocked.** P-06 remains Complete.

Separate design/implementation review must address (1) semantic false acceptance of unsupported clauses in multi-proposition source facts, (2) material relationship claims misclassified as stylistic expression, (3) unsupported interpretation premises, and (4) generation/retry adherence to visible-label requirements. This run does not implement those changes or authorize a new acceptance condition. Preserve G-07/G-08/G-11 and all failed attempts; any future changes/re-acceptance require a separately agreed plan. No G-11 infrastructure change was necessary for this execution.
