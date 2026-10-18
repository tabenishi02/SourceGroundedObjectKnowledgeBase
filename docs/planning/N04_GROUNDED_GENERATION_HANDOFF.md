# N-04 Grounded Generation — Design Handoff

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current Status: **N-04 Failed (2026-10-18) — grounded-generation対策の追加設計が必要**
- Branch: `phase-n/n04-prerequisite-derived-search`
- N-04 failure commit: `0380d6cd6b927583f12df872ed9eac2226d0c881`
- PR: `#39` — Draft / unmerged
- Primary acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Frozen v1 benchmark: `benchmark/n04-ai-use-cases-v1.json`
- Real-data dataset: `benchmark/n03-real-data-vertical-slice-v1.json`

---

## 1. 本書の目的

本書は、N-04実AI受入で判明したgrounding failureを受け、**grounded-generation対策の追加設計を別チャットへ引き継ぐための専用Handoff**である。

ここでは、すでに確定した事実と、次に設計すべき未決事項を分離する。

次のチャットでは、N-04全体やRetrieval / MCP / Context Builderを最初から再設計しない。本書と既存受入記録を起点に、**SGOKB Contextを下流LLMへ安全に渡し、Context外の事前学習知識混入を抑制・検出するconsumer-side generation contract**を設計する。

---

## 2. Phase Nの現在地点

Phase Nの状態:

| Task | Status |
|---|---|
| N-01 Unit Test | Complete |
| N-02 Integration Test | Complete |
| N-03 real-data Vertical Slice | Complete |
| N-04 prerequisite N-04P-01〜P-06 | Complete |
| N-04 AI use-case acceptance | **Failed** |
| N-05 Performance | Pending |
| N-06 Retrieval / Vector quality | Pending |
| N-07 Failure / Recovery | Pending |

N-04 Failedのため、Task master上はN-05へ進まず、N-04の再受入が必要な状態を維持する。

既存正本:

- `docs/planning/PHASE_N_PREPARATION.md`
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`

---

## 3. N-04で確認済みの正常範囲

N-04では、SGOKBのKnowledge取得側にproduction defectは観測されなかった。

確認済み:

- MCP Python SDK v2 / stdio transport
- `MCPReadAdapter → KnowledgeReadApplication`
- current accepted Version解決
- Context Builder
- `purpose=roleplay / comparison / creative`
- Context budget
- Similarity retrieval
- historical Versionのsilent混入なし
- AI consumerによるSQLite直読みなし
- canonical Knowledge read-only
- canonical 52 table / derived table before-after不変
- `system integrity` PASS
- focused regression PASS
- full pytest `361 passed / 0 skipped / 0 failed`

したがって、今回の追加設計では**失敗理由がない限り、Retrieval / Similarity / canonical schema / MCP read boundaryを変更対象にしない**。

---

## 4. N-04 Failedの直接原因

### Case 1 — Saber Roleplay

Context内でgroundされていた主な情報:

- Saber = Artoria Pendragon
- `Fate/stay night`のfictional character
- sword-wielding Servant
- Shirouとのcontract

最終local LLMは、Contextに存在しない次の情報を事実として追加した。

- Holy Grail WarでShirouのprotectorとして戦う
- Artoriaの正体が作中で広く知られていない

判定:

`critical unsupported franchise/backstory fact`

### Case 2 — Similar Work comparison

Similarity retrieval:

```text
Fate/stay night
→ BLEACH
rank 1
cosine_similarity ≈ 0.646960
```

candidateはhardcodeせず、実Similarity結果から選択した。

しかし最終local LLMはContext外の次を追加した。

- magiが歴史上のHeroesを召喚してHoly Grailのため戦う
- Hollowsがmalevolent spirits
- Soul Reapersがhuman worldとafterlifeのbalanceを維持する
- 両protagonistがextraordinary powersを得るという未支持の共通化

さらに、比較上のinterpretationをstored factと明確に分離しなかった。

判定:

- `critical outside-knowledge factual claim`
- `interpretation labeling不足`

### Case 3 — Concept combination creative Character

Tsundere + Hero's JourneyのConcept統合、新規Character生成自体は成立した。

また、unsupported Concept factの追加は確認されなかった。

一方、`Original character`ではcreative additionと明示したが、`Arc outline`内の新規eventについて「SGOKB factではなくcreative addition」であることを明示しなかった。

判定:

`creative-separation contract未達`

Case 3の創作内容そのものはhallucination扱いしない。

---

## 5. 使用モデルとbaselineの意味

N-04では新規大型modelをdownloadせず、既存local modelだけで評価した。

Attempt 1:

```text
Phi-4 Q4_K_S
```

Final attempt:

```text
Mistral Small 3.2 24B Instruct Q4_K_M
```

許可されたmodel切替は1回だけ使用した。

両modelで、程度の差はあるがContext外knowledge混入またはresponse contract違反が残った。

この結果から、次の結論を固定する。

> 単にpromptへ「SGOKB Contextだけを使う」と書くだけでは、local LLMの事前学習知識混入を十分に防げない。

ただし、これは「local LLMでは不可能」と確定したものではない。次はmodel交換より先に、grounded-generation protocol / output validationの設計を検討する。

---

## 6. 変更してはいけない境界

追加設計のためだけに、次を安易に変更しない。

### Canonical Knowledge

- Object identity
- current accepted Version
- Statement / Attribute / Relation
- Evidence / Provenance
- Version immutability

N-04の生成失敗をcanonical Knowledgeへ書き戻して解決しない。

### Retrieval

- Lexical / Semantic / Similarityの基本contract
- Search score semantics
- current / historical scope

N-06で正式品質評価する領域をN-04対策へ混ぜない。

### MCP

MCPはKnowledge Access Layerであり、推論主体ではない。

Grounded-generation対策のために、MCP Server内部へ特定LLMのgeneration logicを直接埋め込むことを前提にしない。

### Cloud fallback

- silent cloud inference禁止
- Web補完禁止

この原則は維持する。

---

## 7. 次チャットで設計する対象

主対象は次の境界である。

```text
SGOKB current Knowledge
        ↓
MCP / Context Builder
        ↓
Grounded-generation consumer protocol
        ↓
Local LLM
        ↓
Output validation
        ↓
Accept / Retry / Reject
```

今回の追加設計では、少なくとも次を検討する。

1. LLMへ渡すgrounded context format
2. Context中のFact / Statement identityの表現
3. factual claimとinterpretationの分離
4. creative additionの分離
5. output schema
6. claim-level provenance / citation contract
7. unsupported claim検出
8. validation failure時のretry / reject policy
9. model-independent contractにできる範囲
10. N-04再受入benchmarkのversioning

---

## 8. 検討候補 — 未採用

以下は**採用済みDecisionではない**。次チャットで比較・評価する候補である。

### Candidate A — Fact ID / Statement ID引用

Context中の利用可能Factへ、例えば次のような安定した参照ラベルを付ける。

```text
F1: Saber is also known as Artoria Pendragon.
F2: Saber is a sword-wielding Servant contracted to Shirou.
```

LLMへ、source Objectについてのfactual claimには対応Fact IDを付けるよう要求する。

利点候補:

- claimとContext supportを機械的に照合しやすい
- post-validationしやすい

論点:

- Fact IDをContext Builder contractへ含めるかconsumer側で付与するか
- Statement IDをそのまま公開するかpresentation-only IDを使うか

### Candidate B — Structured output

出力を例えば次へ分離する。

```text
facts_used
interpretations
creative_additions
final_response
```

またはclaim単位に、

```text
type = grounded_fact | interpretation | creative_addition
support = [F1, F2]
```

を持たせる。

論点:

- 人間向け文章と検証用構造を同時に生成させるか
- 2-stage generationに分けるか

### Candidate C — Post-generation grounding validator

生成結果をatomic claimへ分解し、Context supportのないsource-object factual claimをrejectする。

論点:

- deterministic validatorでどこまで可能か
- validatorにもLLMを使う場合、同一model self-checkを信頼してよいか
- local second-pass modelを使うか

### Candidate D — Retry contract

Validation failure時に、unsupported claim一覧を付けて再生成する。

論点:

- retry上限
- 同一modelでのretryと別model fallbackの境界
- failureを隠すためのprompt tuningにならないようどう記録するか

### Candidate E — Creative mode policy

Creative use caseでは、

```text
SGOKB grounded concept
vs
new creative material
```

を明示的な別section / fieldとして扱う。

Case 3のような「創作自体は成功しているがラベルが不足」というfailureを構造的に防ぐことを狙う。

---

## 9. 未決の設計論点

別チャットでは特に次を個別検討する。

### 9.1 Grounded generationはSGOKB本体の責務かconsumerの責務か

候補:

- SGOKB Application capabilityとして提供
- MCP Toolとして提供
- consumer libraryとして提供
- 外部client responsibilityとして契約だけ定義

MCPが推論主体ではない既存方針との整合が必要。

### 9.2 Fact identity

候補:

- canonical Statement ID
- Context-local Fact ID
- Evidence ID
- Context-local Fact ID + canonical ID metadata

### 9.3 Validation strength

候補:

- schema validationのみ
- citation presence validation
- quoted/normalized fact comparison
- deterministic claim support rules
- second-pass local LLM judge
- hybrid

### 9.4 Roleplayへの適用

Roleplay文章は自然言語として事実と演出が混ざりやすい。

次を区別する必要がある。

- factual backstory
- speech style / harmless phrasing
- unsupported fictional event
- creative embellishment

### 9.5 Comparisonへの適用

比較では、stored factそのものではない推論が必要になる。

したがって、

```text
grounded fact
interpretation derived from grounded facts
unsupported external fact
```

の3分類が必要。

### 9.6 Creative generationへの適用

創作を禁止せず、

```text
source Concept knowledge
creative addition
```

の境界だけを明確化する。

---

## 10. Benchmark versioning方針

### v1は変更しない

次をbaselineとして保存する。

```text
benchmark/n04-ai-use-cases-v1.json
```

v1は、grounded-generation追加対策なしの条件で実施し、Phi-4 / Mistral Small 3.2でFAILした履歴を表す。

次の再設計でprompt / context protocol / output schema / validator等を変更する場合、v1を上書きしない。

推奨:

```text
benchmark/n04-ai-use-cases-v2.json
```

v2には、採用したgrounded-generation contractを明示する。

v1とv2の差分が追跡できるようにし、rubricを単純に緩めてPASSへ変更しない。

---

## 11. 再受入で維持する核心Gate

grounded-generation対策を導入した後も、少なくとも次は維持する。

### Common

- current accepted Versionだけを使用
- consumer-side direct SQLite query禁止
- cloud inference禁止
- Web補完禁止
- canonical Knowledge不変
- `system integrity` PASS
- full pytest 0 failed

### Factual grounding

Case 1 / Case 2では、source Objectについてのmaterial factual claimが供給Contextでsupportされること。

Context外のfranchise knowledgeを、model memoryから既知factとして追加しないこと。

### Interpretation

Case 2では、比較上のinterpretationをstored factと区別すること。

### Creative separation

Case 3では、creative additionをSGOKB factとして表現しないこと。

創作内容そのものの豊かさはhallucination判定対象にしない。

---

## 12. Knowledge coverageとの境界

N-04では、Contextが薄いこと自体も観測された。

例:

- Saber personality未分析
- Work比較材料がsummary / overall中心
- P-06 lexical未hit: `King of Knights`, `character archetype`

これらはN-06等へcoverage課題として引き継ぐ。

Grounded-generation対策で、coverage不足をmodel memoryから補ってはいけない。

必要なKnowledgeがない場合の正しい挙動は、

```text
insufficient context
```

を明示することであり、外部知識で穴埋めすることではない。

---

## 13. Raw evidenceの場所

Git管理外のReference Workstation evidence:

```text
.local/n04/
```

含む:

- attempt-1 Phi-4 Context / request / response / evaluation
- final Mistral Small 3.2 Context / request / response / evaluation
- atomic claim support照合
- model metadata
- runtime logs
- before / after canonical snapshot

GitHub側には完全raw responseを保存していない。

次チャットで実際の生成文を詳細分析する必要がある場合は、Codexへ`.local/n04/`を確認させる。

通常の設計開始には、`docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`のclaim照合結果で十分である。

---

## 14. 参照すべき文書

次チャットでは最低限以下を読む。

### Current Phase / Task

- `docs/planning/PHASE_N_PREPARATION.md`
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

### N-04

- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- `benchmark/n04-ai-use-cases-v1.json`
- 本書 `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`

### Dataset

- `docs/evaluation/N03_REAL_DATA_VERTICAL_SLICE.md`
- `benchmark/n03-real-data-vertical-slice-v1.json`

### Retrieval prerequisite

- `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md`

### MCP / Context

- `docs/decisions/J06_LOCAL_MCP_CLIENT_ACCEPTANCE.md`
- Context Builder関連test / contract

---

## 15. 次チャットの開始地点

次の作業は実装ではなく、まず**grounded-generation design optionsの比較と責務境界の確定**から開始する。

推奨開始順序:

1. failureを再確認する
2. grounded-generationの責務所有者を決める
3. Fact identity / citation contractを決める
4. output schemaを決める
5. validation / retry policyを決める
6. Roleplay / Comparison / Creativeそれぞれへの適用差を決める
7. v2 benchmarkを設計する
8. 実装Taskへ分解する
9. 実装後にN-04再受入する

この段階では、Candidate A〜Eのいずれも未採用である。

---

## 16. 次チャットへ渡す最小プロンプト

```text
Phase NのN-04で、SGOKBからのRetrieval / MCP / Context deliveryは正常でしたが、
local LLMがContext外の事前学習知識を事実として混入し、N-04はFailedとなりました。

grounded-generation対策を追加設計します。
まず以下を確認してください。

- docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md
- docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md
- benchmark/n04-ai-use-cases-v1.json

既存のRetrieval / MCP / canonical Knowledgeを理由なく再設計せず、
SGOKB Context → local LLM → output validation間のgrounding contractを中心に検討してください。

最初に、設計上の主要論点と実現案を複数提示し、
各案のメリット・デメリット・既存architectureへの影響を比較してください。
まだ実装は開始しないでください。
```

---

## 17. Handoff completion

本書追加時点では、grounded-generation対策の設計・実装は未開始である。

確定しているのは次だけである。

- N-04 v1 acceptanceはFailed。
- SGOKB retrieval / MCP / Context側のproduction defectは観測されていない。
- local LLMのgrounding / instruction-following failureが主要原因。
- v1 benchmarkはfailed baselineとして保存する。
- 次作業はgrounded-generation protocol / validationの追加設計。
- N-05へはまだ移行しない。

以上を次チャットの開始状態とする。
