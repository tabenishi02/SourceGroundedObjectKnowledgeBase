# N-04 Grounded Generation — Remediation Tasks

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current Status: **N-04 Failed — N-04G-02 Complete / next N-04G-03**
- Branch: `phase-n/n04-prerequisite-derived-search`
- Failure baseline: `benchmark/n04-ai-use-cases-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Design handoff: `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`
- N-04G-01 Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- N-04G-02 Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`

---

## 1. 本書の目的

本書は、N-04で判明したgrounded-generation failureを解消し、N-04を正式にCompleteへ戻すまでの作業を実行可能なTaskへ分解する。

本書は**実施順序とTask completion conditionの正本**として使用する。

N-04自体の最終Completion Gateは既存の以下を変更せず正本とする。

- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- `benchmark/n04-ai-use-cases-v1.json`

本書はrubricを緩めるためのものではない。grounded-generation contractを追加して再受入するための実施計画である。

---

## 2. N-04の完了条件

N-04をCompleteとするには、以下を**すべて**満たす必要がある。

### 2.1 Retrieval / Context Gate

- 3 caseすべてがMCP public read boundaryを通る。
- AI consumerがdirect SQLite queryで入力Knowledgeを構築しない。
- current accepted Versionだけを利用する。
- historical Versionをsilentに混入しない。
- Case 2の比較対象は実Similarity retrieval結果から選択する。
- Context Builderの`purpose`とbudget contractを満たす。

N-04 v1でこの領域のproduction defectは確認されていない。追加設計では、明確なfailure reasonがない限りRetrieval / Similarity / canonical schema / MCP read boundaryを変更しない。

### 2.2 Local LLM Gate

- 同じfrozen local chat modelで3 caseすべてを実行する。
- cloud inferenceへfallbackしない。
- Web Search / external web knowledgeで不足Knowledgeを補完しない。
- SGOKB Context不足時はmodel memoryで事実を穴埋めせず、必要に応じて不足を明示する。

### 2.3 Output Quality Gate

#### Case 1 — Roleplay

- first-person roleplayとして成立する。
- Context内の具体的factを最低2件利用する。
- Contextと矛盾しない。
- Context外の重要franchise / backstory factを既知factとして追加しない。
- personality / backstory coverage不足を勝手に詳細化しない。

#### Case 2 — Comparison

- 両WorkのContextから最低1件ずつfactual materialを使う。
- 最低1つの比較または対比を行う。
- interpretationをstored SGOKB factと区別する。
- Knowledgeが薄い場合は限界を表現できる。
- Context外のfranchise knowledgeをfactとして持ち込まない。
- Similarity scoreをtruth / confidence / preference probabilityとして扱わない。

#### Case 3 — Creative

- Tsundere / Hero's Journeyの両Conceptからgrounded ideaを使用する。
- 両Conceptを新規Character / arcへ実際に統合する。
- 新規name / setting / event / trait等をcreative additionとしてSGOKB factから区別する。
- source ConceptについてContext外のfactをSGOKB由来として追加しない。

### 2.4 Safety / Regression Gate

- canonical Knowledgeが受入前後で不変である。
- current Version pointer / Evidence / Provenanceを変更しない。
- `system integrity`がPASSする。
- full pytestが`0 failed`で完了する。

### 2.5 Evaluation Evidence Gate

- MCP request / response、Context、LLM request / response、model metadata、evaluationを保存する。
- factual responseはatomic claim単位でContext supportを照合できる状態にする。
- creative detailはgrounded factと別分類する。
- LLM自身のself-evaluationだけで最終PASSを決めない。
- v1 failure evidenceを削除・上書きしない。

---

## 3. 設計上の固定境界

以下はN-04対策のためだけには再設計しない。

- Object identity
- current accepted Version semantics
- Statement / Attribute / Relationのcanonical model
- Evidence / Provenance
- Version immutability
- Lexical / Semantic / Similarity retrievalの基本contract
- current / historical scope
- MCPをKnowledge Access Layerとする境界
- silent cloud inference禁止
- Web補完禁止

Knowledge coverage不足やretrieval ranking品質はN-06との境界を維持する。

正しい挙動は、coverage不足をmodel memoryで補うことではなく、必要なら`insufficient context`を表現することである。

---

## 4. Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-04G-00 | P0 | **Complete (2026-10-18)** | N-04 Completion Gate確認とremediation Task分解 |
| N-04G-01 | P0 | **Complete (2026-10-18)** | grounded-generationの責務所有者と保証レベルを確定 |
| N-04G-02 | P0 | **Complete (2026-10-18)** | claim taxonomyと用途別意味境界を確定 |
| N-04G-03 | P0 | Pending | Context grounding / reference contractを設計 |
| N-04G-04 | P0 | Pending | generation / output contractを設計 |
| N-04G-05 | P0 | Pending | grounding validation方式を設計 |
| N-04G-06 | P0 | Pending | validation failure時のretry / reject / insufficient policyを設計 |
| N-04G-07 | P0 | Pending | End-to-End designを統合しDesign Freeze |
| N-04G-08 | P0 | Pending | N-04 v2 benchmark / acceptance specを固定 |
| N-04G-09 | P0 | Pending | 採用設計を実装 |
| N-04G-10 | P0 | Pending | automated test / regressionを追加・実施 |
| N-04G-11 | P0 | Pending | formal re-acceptance harness / evidence手順をfreeze |
| N-04G-12 | P0 | Pending | Reference WorkstationでN-04を正式再受入しComplete判定 |

N-05へ進めるのは**N-04G-12でN-04 Completeが確認された後**とする。

---

# 5. Design Tasks

## N-04G-01 [P0] grounded-generationの責務所有者と保証レベルを確定する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`

### 目的

最初に「誰がgrounded outputを保証するか」を決める。

比較対象例:

- SGOKB Application capability
- MCP Tool capability
- SGOKB提供consumer library
- 外部client responsibility + contractのみ提供
- 上記のhybrid

同時に保証レベルを比較する。

例:

- Context deliveryまで保証
- generation contractまで保証
- output validationまで保証
- validation failure handlingまで保証

### 必須検討

- MCPはKnowledge Access Layerであり推論主体ではない、という既存方針との整合。
- ChatGPT / local LLM / UPDS / Other Clientsへ適用可能なmodel-independent contractの範囲。
- 特定provider / modelへSGOKB本体を密結合させない方法。
- consumer実装ミスをどこまでSGOKB側が防ぐべきか。

### 完了条件

- [x] 責務境界図または責務表が確定している。
- [x] SGOKB / MCP / consumer / LLMそれぞれの責務が明記されている。
- [x] 「何をSGOKBが保証し、何を保証しないか」が明記されている。
- [x] N-04G-02以降が責務境界を前提に設計できる。

### Decision summary

- **Hybrid方式を採用**: `SGOKB-owned contract + consumer-owned orchestration + untrusted LLM`。
- SGOKB Application側がgrounding contract / conformance semanticsの正本を所有する。
- MCPはtransport/schema adapterのまま維持し、LLM generation主体にしない。
- Consumerがmodel runtime / invocation / workflow enforcementを担当する。
- LLM raw outputはgroundedとみなさず、SGOKB-defined Gateを満たした出力だけを`SGOKB-grounded`として扱える。
- Fact ID / Structured Output / validator実装 / retry方式は本Taskで採用せず、N-04G-02〜G-06へ委ねる。

---

## N-04G-02 [P0] claim taxonomyと用途別意味境界を確定する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`

### 目的

生成文中の情報を、少なくともN-04の3用途で一貫して分類できる意味モデルを決める。

### Decision summary

単純なflat taxonomyではなく、次の**2軸taxonomy**を採用する。

#### Axis A — Semantic Role

```text
source_fact
interpretation
creative_addition
context_limit
stylistic_expression
```

#### Axis B — Grounding Disposition

```text
supported
derived_supported
not_applicable
unsupported
contradictory
```

さらに、semantic role自体が許容されてもstored factとの境界が曖昧な場合を`separation_violation`として扱う。

用途別の核心境界:

- **Roleplay**: supported source factと非事実的styleは許容。Context外backstory / stable personality / canonical-looking eventは不可。
- **Comparison**: supported source factとgrounded interpretationを許容。interpretationはstored factから区別し、external premiseを使わない。
- **Creative**: source Concept factはgroundedである必要があるが、新規Character / setting / event等はcreative additionとして許容。source knowledgeとの境界を明示する。

### 完了条件

- [x] claim / output semantic分類と各定義が確定している。
- [x] grounding状態をsemantic roleから分離している。
- [x] 3 use caseそれぞれの許容 / 要分離 / 禁止境界を例示している。
- [x] Roleplayのstyleとunsupported backstoryを区別している。
- [x] Comparisonのstored fact / interpretation / unsupported external factを区別している。
- [x] Creativeのsource Concept knowledge / creative additionを区別している。
- [x] Context不足を安全に表明する`context_limit`を正常classとして定義している。
- [x] Case 1〜3のv1 failureを新taxonomyで一意に説明している。

---

## N-04G-03 [P0] Context grounding / reference contractを設計する

### 目的

LLMへ渡したKnowledgeと生成claimを、必要な強さで追跡できるContext表現を決める。

比較対象例:

- 現行Context本文のみ
- canonical Statement ID
- Context-local Fact ID
- Evidence ID
- Context-local ID + canonical metadata
- 引用可能なnormalized fact representation
- その他のreference方式

Fact ID / Statement ID採用を前提にしない。

### 必須検討

- identityをContext Builder本体が付与するかconsumer側で付与するか。
- canonical internal IDを外部consumerへ露出する必要性。
- claim-level provenanceに必要なmetadata。
- roleplay / comparison / creativeで同じreference contractを使えるか。
- Context budgetへの影響。

### 完了条件

- 採用方式と不採用主要案の理由が記録されている。
- Contextからclaim supportを追跡する方法が定義されている。
- canonical schema変更が必要か不要かが明示されている。

---

## N-04G-04 [P0] generation / output contractを設計する

### 目的

LLMへ何を要求し、どの形で生成結果を返させるかを決める。

比較対象例:

- natural-language responseのみ
- citation付きnatural language
- Structured Output
- claim metadata + final response
- 2-stage generation
- deterministic intermediate representation + final rendering

Structured Outputや2-stage generationを前提にしない。

### 必須検討

- factual claim / interpretation / creative additionをどう表現するか。
- 人間向け最終文章と機械検証用情報を同時に生成するか分離するか。
- 自由なRoleplay / Creative品質を不必要に損なわずgroundingを維持する方法。
- malformed outputの扱い。

### 完了条件

- generation input / output contractが具体化されている。
- 3 use caseへ適用した出力例がある。
- 機械検証可能性と人間向け可読性のtrade-offが評価されている。

---

## N-04G-05 [P0] grounding validation方式を設計する

### 目的

生成後にunsupported factual claimや意味分類違反をどのように検出するかを決める。

比較対象例:

- schema validationのみ
- citation / reference presence validation
- exact / normalized fact comparison
- deterministic rule validator
- local LLM second-pass judge
- 別local model judge
- hybrid validator
- generation contractだけでpost-validationを持たない方式

post-generation validator採用を前提にしない。

### 必須検討

- unsupported claim detectionの精度と限界。
- interpretationのsupport判定。
- creative additionの誤検出回避。
- validator自身のhallucination / false positive / false negative。
- same-model self-checkを最終Gateとして信頼できるか。
- fail-open / fail-closedの境界。

### 完了条件

- validation strengthが確定している。
- 各validation stageの入力 / 出力 / failure classが定義されている。
- N-04のcritical failureを検出または構造的に防止できる理由が説明されている。

---

## N-04G-06 [P0] validation failure時のretry / reject / insufficient policyを設計する

### 目的

生成またはvalidationが失敗した場合の正式挙動を決める。

比較対象例:

- 即Reject
- unsupported claimを除去して再生成
- 同一model retry
- 別local model fallback
- insufficient contextとして終了
- 部分結果を返す

retry採用自体を前提にしない。

### 必須検討

- retryを行う場合の上限。
- retryへ渡してよいvalidation feedback。
- model cherry-pickを防ぐ条件。
- silent cloud / Web fallback禁止の維持。
- retryで偶然PASSするまで繰り返す評価汚染の防止。
- failure evidenceの保存。

### 完了条件

- failure classごとの正式actionが決まっている。
- retryを採用する場合は上限・記録・fallback条件が固定されている。
- retryを採用しない場合も、その理由とReject behaviorが固定されている。

---

## N-04G-07 [P0] End-to-End grounded-generation designを統合しDesign Freezeする

### 目的

N-04G-01〜G-06を1つの実装可能なcontractへ統合する。

対象フロー:

```text
SGOKB current Knowledge
        ↓
MCP / Context Builder
        ↓
Grounded-generation consumer protocol
        ↓
Local LLM
        ↓
Validation / classification
        ↓
Accept / Retry / Reject / Insufficient
```

### 必須検討

- Case 1 / 2 / 3のend-to-end walkthrough。
- canonical Knowledge / Retrieval / MCP境界への影響。
- N-06へ残すKnowledge coverage / retrieval quality課題との分離。
- model-independent部分とmodel-specific tuning部分の分離。
- logging / observability / evidence保存。

### 完了条件

- architecture / sequence / data contractが矛盾なく統合されている。
- 未決P0設計論点が残っていない。
- Candidate A〜Eを含む主要案について採用 / 不採用Decisionが記録されている。
- 実装scopeをN-04G-09へ渡せる。

---

# 6. Acceptance Specification Task

## N-04G-08 [P0] N-04 v2 benchmark / acceptance specを固定する

### 目的

採用したgrounded-generation contractを評価できる再受入仕様を作る。

### 方針

`benchmark/n04-ai-use-cases-v1.json`はFailed baselineとして変更しない。

必要に応じて次を作る。

```text
benchmark/n04-ai-use-cases-v2.json
```

### 必須要件

- v1の核心Gateを緩めない。
- v1→v2で何が変更されたかを明記する。
- generation protocol / output contract / validation / failure handlingの採用仕様を記録する。
- 同じ3代表use caseを継承する。
- model policyを明記する。
- PASS / FAIL判定が再現可能である。

### 完了条件

- v2 acceptance specがDesign Freeze内容と一致している。
- rubric緩和による見かけのPASSになっていない。
- v1とv2の差分理由を説明できる。
- formal re-acceptance開始後に都合よくrubricを変更しない状態へfreezeされている。

---

# 7. Implementation Tasks

## N-04G-09 [P0] 採用したgrounded-generation designを実装する

### 目的

N-04G-07 / G-08でfreezeした仕様だけを実装する。

### Scope

実装場所はN-04G-01で決定した責務境界に従う。

例:

- SGOKB application component
- consumer helper / library
- acceptance harness component
- Context presentation adapter
- validator
- retry controller

上記は候補であり、すべてを実装する前提ではない。

### 禁止

- N-04をPASSさせる目的だけでcanonical Knowledgeへ事実を追加する。
- N-06領域のranking tuningを混在させる。
- benchmark固有文字列をhardcodeしてPASSさせる。
- silent cloud / Web fallbackを追加する。

### 完了条件

- Design Freezeとのtraceabilityがある。
- 3 use caseを扱える共通実装になっている。
- benchmark固有hackがない。
- 既存read boundaryを理由なく破壊していない。

---

## N-04G-10 [P0] automated test / regressionを追加・実施する

### 目的

formal local-LLM再受入の前に、grounded-generation contractの機械的部分をdeterministicに検証する。

### 最低限のtest観点

- supported factual claim
- unsupported factual claim
- contradictory claim
- interpretation classification
- creative addition classification
- insufficient context
- malformed output
- validation failure path
- retry / reject path（採用した場合）
- current / historical isolationを壊していないこと
- canonical mutationが発生しないこと

### 完了条件

- 採用contractの主要branchがautomated testでcoveredされている。
- focused testがPASSする。
- full pytestが`0 failed`で完了する。
- new skip / xfailでfailureを隠していない。

---

## N-04G-11 [P0] formal re-acceptance harness / evidence手順をfreezeする

### 目的

N-04G-12開始後に評価条件を動かさないよう、実行手順とevidence形式を先に固定する。

### 必須固定項目

- evaluation DB / N-03 dataset
- MCP transport / public read route
- semantic runtime
- model selection policy
- generation settings
- v2 prompt / output contract
- validator / retry policy
- raw artifact保存先
- atomic claim evaluation手順
- before / after canonical snapshot
- integrity / pytest実行手順

### 完了条件

- formal runの実行順序が1本に固定されている。
- 失敗時の分類と記録方法が決まっている。
- formal run開始後にcase単位でmodel / rubric / protocolをcherry-pickできない。

---

# 8. Formal Re-Acceptance

## N-04G-12 [P0] Reference WorkstationでN-04を正式再受入する

### 実施

freeze済みv2 acceptance spec / harnessだけを使用し、3ケースをReference Workstationで実行する。

### 必須記録

- Git head / working tree / environment
- model / runtime metadata
- MCP request / response
- Context
- raw LLM request / response
- validation結果
- retry履歴（存在する場合）
- atomic claim support評価
- canonical before / after snapshot
- system integrity
- focused regression
- full pytest

### N-04 Complete条件

本書2章のCompletion Gateをすべて満たすこと。

特に、次を必須とする。

- Case 1: critical unsupported franchise/backstory fact = 0
- Case 2: critical unsupported outside-knowledge fact = 0、interpretationがstored factと区別される
- Case 3: creative additionがSGOKB factと明確に区別される
- canonical mutation = 0
- system integrity = PASS
- full pytest = 0 failed

1件でもcritical Gateを満たさなければN-04はCompleteにしない。

### 完了時の文書更新

- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`へ再受入結果を追記またはv2結果文書を追加する。
- `docs/planning/PHASE_N_PREPARATION.md`のN-04 statusをCompleteへ更新する。
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`のN-04 statusをCompleteへ更新する。
- PR #39の説明を最終状態へ更新する。
- 次TaskとしてN-05へ進行可能であることを明示する。

---

## 9. Task dependency

```text
N-04G-00 Complete
       ↓
N-04G-01 Responsibility / guarantee boundary Complete
       ↓
N-04G-02 Claim taxonomy Complete
       ↓
N-04G-03 Context grounding / reference contract
       ↓
N-04G-04 Generation / output contract
       ↓
N-04G-05 Validation design
       ↓
N-04G-06 Failure handling
       ↓
N-04G-07 Design Freeze
       ↓
N-04G-08 v2 Acceptance Freeze
       ↓
N-04G-09 Implementation
       ↓
N-04G-10 Automated Test / Regression
       ↓
N-04G-11 Formal Harness Freeze
       ↓
N-04G-12 Formal N-04 Re-Acceptance
       ↓
N-04 Complete
       ↓
N-05
```

原則として上から順に実施する。

N-04G-03〜G-06は設計上相互依存するため、検討中の往復は許容する。ただしN-04G-07 Design Freezeまでに矛盾を解消する。

---

## 10. Candidate案の扱い

`docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`にある以下はすべて未採用候補のまま開始する。

- Fact ID / Statement ID引用
- Structured Output
- Post-generation grounding validator
- Retry contract
- Creative mode policy

各Taskで比較対象として扱い、Taskの開始前提にはしない。

特定案を採用する場合は、少なくとも次を記録する。

```text
Decision
Alternatives considered
Why selected
Why alternatives rejected/deferred
Architecture impact
Acceptance impact
```

---

## 11. 次に実施するTask

次のTaskは以下とする。

```text
N-04G-03 [P0]
Context grounding / reference contractを設計する
```

N-04G-02で確定した2軸taxonomyを前提に、source factとinterpretation premiseを供給Contextへ追跡できるreference方式を比較・決定する。
