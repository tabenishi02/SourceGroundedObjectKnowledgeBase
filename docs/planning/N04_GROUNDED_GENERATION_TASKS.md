# N-04 Grounded Generation — Remediation Tasks

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current Status: **N-04 Failed — N-04G-04 / G-05 Complete / next N-04G-06**
- Branch: `phase-n/n04-prerequisite-derived-search`
- Failure baseline: `benchmark/n04-ai-use-cases-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Design handoff: `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`
- N-04G-01 Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- N-04G-02 Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- N-04G-03 Decision: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- N-04G-04 Decision: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- N-04G-05 Decision: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`

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
| N-04G-03 | P0 | **Complete (2026-10-18)** | Context grounding / reference contractを設計 |
| N-04G-04 | P0 | **Complete (2026-10-18)** | generation / output contractを設計 |
| N-04G-05 | P0 | **Complete (2026-10-18)** | grounding validation方式を設計 |
| N-04G-06 | P0 | Pending | validation failure時のretry / reject / insufficient policyを設計 |
| N-04G-07 | P0 | Pending | End-to-End designを統合しDesign Freeze |
| N-04G-08 | P0 | Pending | N-04 v2 benchmark / acceptance specを固定 |
| N-04G-09 | P0 | Pending | 採用設計を実装 |
| N-04G-10 | P0 | Pending | automated test / regressionを追加・実施 |
| N-04G-11 | P0 | Pending | formal re-acceptance harness / evidence手順をfreeze |
| N-04G-12 | P0 | Pending | Reference WorkstationでN-04を正式再受入しComplete判定 |

N-05へ進めるのは**N-04G-12でN-04 Completeが確認された後**とする。

N-04G-05はN-04G-04より先に設計した。これはG-03〜G-06が相互依存するため許容される設計上の往復である。G-05 requirementsをG-04へ反映し、現在は両Taskが整合した状態でCompleteしている。

---

# 5. Design Tasks

## N-04G-01 [P0] grounded-generationの責務所有者と保証レベルを確定する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`

### Decision summary

- **Hybrid方式を採用**: `SGOKB-owned contract + consumer-owned orchestration + untrusted LLM`。
- SGOKB Application側がgrounding contract / conformance semanticsの正本を所有する。
- MCPはtransport/schema adapterのまま維持し、LLM generation主体にしない。
- Consumerがmodel runtime / invocation / workflow enforcementを担当する。
- LLM raw outputはgroundedとみなさず、SGOKB-defined Gateを満たした出力だけを`SGOKB-grounded`として扱える。

### 完了条件

- [x] 責務境界図または責務表が確定している。
- [x] SGOKB / MCP / consumer / LLMそれぞれの責務が明記されている。
- [x] 「何をSGOKBが保証し、何を保証しないか」が明記されている。
- [x] N-04G-02以降が責務境界を前提に設計できる。

---

## N-04G-02 [P0] claim taxonomyと用途別意味境界を確定する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`

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

### 完了条件

- [x] claim / output semantic分類と各定義が確定している。
- [x] grounding状態をsemantic roleから分離している。
- [x] 3 use caseそれぞれの許容 / 要分離 / 禁止境界を例示している。
- [x] Case 1〜3のv1 failureを新taxonomyで一意に説明している。

---

## N-04G-03 [P0] Context grounding / reference contractを設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`

### Decision summary

- **Context-local Grounding Reference + canonical identity metadata**方式を採用する。
- LLM-facing referenceは`K1`, `K2`, ...とし、1 grounded Context内だけで有効とする。
- 各`K*`は`object_id` / `resolved_version_id` / `source_kind` / canonical target identityへ必ず追跡可能にする。
- `source_kind`は最低限`object_field / statement / attribute / relation`を扱う。
- canonical Statement ID等はbackend metadataとして保持するが、LLMへ直接引用させる標準方式にはしない。
- Evidence IDは一次grounding referenceにせず、provenance / audit用secondary metadataとする。
- `context_fingerprint + ref_id`でContext-local namespaceを識別する。
- J-04 Context Builderのselection後にreference projectionを行い、既存budget selection semanticsを変えない。
- Context-local referenceはtraceabilityであり、reference存在だけをsemantic supportの証明にはしない。
- contract概念名を`sgokb.grounded-context.v1`とする。
- canonical schema変更、新規persistent Fact IDは不要とする。

### 完了条件

- [x] 採用方式と不採用主要案の理由が記録されている。
- [x] Contextからclaim supportを追跡する方法が定義されている。
- [x] Object / Version / Knowledge itemへのcanonical traceabilityが定義されている。
- [x] Roleplay / Comparison / Creativeで共通reference namespaceを使うことを確定している。
- [x] Evidence / provenanceとの関係を分離している。
- [x] Context budgetへの影響方針を確定している。
- [x] canonical schema変更不要、新規persistent Fact ID不要と明示している。

---

## N-04G-04 [P0] generation / output contractを設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`

### Decision summary

- **single-pass structured semantic units + deterministic rendering**方式を採用する。
- output contractを`sgokb.grounded-generation-output.v1`とする。
- LLMは`blocks[] -> units[]`のstructured envelopeを生成する。
- 各unitは`unit_id / semantic_role / text / support_refs[]`を持つ。
- `source_fact / interpretation`はN-04G-03の`K*`をsupportとして宣言する。
- `creative_addition / context_limit / stylistic_expression`は原則`support_refs=[]`とする。
- Grounding DispositionはLLMへ自己申告させず、G-05 validatorが判定する。
- LLMに検証用claimsと別の`final_response`を生成させない。
- validated `unit.text`だけをConsumerが決定論的にrenderし、human-facing responseとvalidation metadataの乖離を防ぐ。
- `interpretation / creative`はpresentation blockを分離し、人間にも区別可能にする。
- provider-native Structured Outputはoptional optimizationであり、SGOKB contractを特定providerへ依存させない。
- malformed / schema違反outputはG-05 V0 failureとし、heuristicでsilent repairしない。
- 2-stage LLM rendererはbaselineとして不採用とする。
- canonical schema変更は不要。

### 完了条件

- [x] generation input / output contractを具体化している。
- [x] natural language only / inline citation / dual-output / 2-stage / deterministic renderingを比較している。
- [x] atomic semantic unitと`K*` support mappingを定義している。
- [x] LLMにGrounding Dispositionを自己申告させないことを固定している。
- [x] human-facing responseとvalidation metadataの乖離を構造的に防止している。
- [x] Roleplay / Comparison / Creativeの3 use case例を示している。
- [x] interpretation / creative scope separationを機械的かつ人間向けに表現可能にしている。
- [x] malformed outputの扱いをV0 failureとして定義している。
- [x] provider-native Structured Outputをoptional optimizationとして分離している。
- [x] G-05 validator input requirementを満たしている。
- [x] canonical schema変更不要と明示している。

---

## N-04G-05 [P0] grounding validation方式を設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`

### Decision summary

- **deterministic validation + bounded semantic validationのHybrid方式**を採用する。
- V0 Contract / Parse、V1 Reference Integrity、V2 Taxonomy / Use-case Policy、V3 Deterministic Support、V4 Bounded Semantic Support、V5 Aggregate Verdictの段階に分ける。
- `K*` reference存在だけをsupport proofにしない。
- exact / structuredに確定できるsupportはdeterministicに処理し、paraphrase / interpretation等の未解決部分だけsemantic validatorへ渡す。
- semantic validatorへはclaimとcited K内容等の必要最小限だけを渡し、Web / external Knowledgeをgrounding根拠に使わせない。
- generator自身のsame-model self-checkだけを最終Gateにしない。
- formal semantic GateでLLM judgeを使う場合は原則generatorから独立した固定local validatorを使用する。
- validation verdictを`PASS / FAIL / INDETERMINATE`で表し、`INDETERMINATE`をgrounded PASSへ昇格しない。
- `SGOKB-grounded`認定はfail-closedとする。
- Creative detailそのものにはfactual supportを要求せず、source Knowledgeとのseparationを検証する。
- validation contract概念名を`sgokb.grounding-validation.v1`とする。
- canonical / Retrieval変更は不要。

### Failure classes

```text
VALIDATION_CONTRACT_ERROR
REFERENCE_INTEGRITY_ERROR
MISSING_REQUIRED_SUPPORT
UNSUPPORTED_CLAIM
CONTRADICTORY_CLAIM
ROLE_MISMATCH
SEPARATION_VIOLATION
CREATIVE_SCOPE_VIOLATION
SEMANTIC_INDETERMINATE
VALIDATOR_UNAVAILABLE
```

### 完了条件

- [x] validation strengthをHybrid方式に確定している。
- [x] deterministic / semantic validation stageの入力・出力境界を定義している。
- [x] unsupported factual claim detectionを定義している。
- [x] interpretationのpremise / derivation support判定を定義している。
- [x] creative additionの誤検出を避けるruleを定義している。
- [x] same-model self-checkを唯一の最終Gateとして不採用にしている。
- [x] validator uncertaintyを`indeterminate`として表現している。
- [x] grounding certificationをfail-closedにしている。
- [x] failure classesとvalidator result contractの概念形を定義している。
- [x] N-04 v1 Case 1〜3を検出または正しく許容できる理由を説明している。
- [x] G-04 output contractと整合している。

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
- G-05の`PASS / FAIL / INDETERMINATE`とfailure classごとのaction対応。
- G-04 malformed output / structured contract failure時のaction。
- `context_limit`を正常終了、partial result、insufficientのどれとして扱うか。

### 完了条件

- failure classごとの正式actionが決まっている。
- retryを採用する場合は上限・記録・fallback条件が固定されている。
- retryを採用しない場合も、その理由とReject behaviorが固定されている。
- structured generation / validation / rendering flowとの整合が確認されている。

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
Grounded Context / K* references
        ↓
Consumer Generation Request
        ↓
Local LLM
        ↓
Structured Semantic Units
        ↓
Validation / classification
        ↓
Accept / Retry / Reject / Insufficient
        ↓ PASS only
Deterministic Rendering
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
- grounded generation output parser / schema
- validator
- deterministic renderer
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
- malformed structured output
- final renderingとvalidated unitの一致
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
- v2 prompt / structured output contract
- validator / retry policy
- deterministic rendering rule
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
- Grounded Context / K mapping
- raw LLM structured response
- validation結果
- rendered human response
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
N-04G-03 Context grounding / reference contract Complete
       ↓
N-04G-04 Generation / output contract Complete
       ↓
N-04G-05 Validation design Complete
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

N-04G-03〜G-06は設計上相互依存するため、検討中の往復は許容する。G-05を先に設計してG-04へrequirementsを返す往復は完了した。次はG-06を実施し、G-07 Design FreezeでG-01〜G-06を統合する。

---

## 10. Candidate案の扱い

`docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`にある候補は、各Taskで比較して採否を決める。

現時点のDecision:

```text
Context-local K* reference + canonical identity metadata: 採用
canonical ID direct citation: 一次referenceとして不採用
Evidence ID direct citation: 一次referenceとして不採用
persistent new Fact ID: 不採用
single-pass structured semantic units + deterministic rendering: 採用
separate model-generated final_response: 不採用
2-stage LLM renderer: baselineとして不採用
provider-native Structured Output: optional optimization
Hybrid post-generation grounding validator: 採用
same-model self-check only: 最終Gateとして不採用
Retry contract: G-06で決定
Creative presentation: visible creative block separationを採用
```

---

## 11. 次に実施するTask

次のTaskは以下とする。

```text
N-04G-06 [P0]
validation failure時のretry / reject / insufficient policyを設計する
```

G-04 structured generation contractとG-05 Hybrid validationが揃ったため、次に`PASS / FAIL / INDETERMINATE`およびfailure classごとの正式なworkflow action、retry上限、insufficient behaviorを確定する。
