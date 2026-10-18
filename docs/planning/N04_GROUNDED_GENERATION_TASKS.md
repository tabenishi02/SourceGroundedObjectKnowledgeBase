# N-04 Grounded Generation — Remediation Tasks

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current Status: **N-04 Failed — N-04G-01〜G-06 Complete / next N-04G-07 Design Freeze**
- Branch: `phase-n/n04-prerequisite-derived-search`
- Failure baseline: `benchmark/n04-ai-use-cases-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Design handoff: `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`
- N-04G-01 Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- N-04G-02 Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- N-04G-03 Decision: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- N-04G-04 Decision: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- N-04G-05 Decision: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- N-04G-06 Decision: `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`

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

- MCP request / response、Grounded Context / K mapping、LLM request / raw structured response、model metadata、validation、retry履歴、rendered responseを保存する。
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

正しい挙動は、coverage不足をmodel memoryで補うことではなく、必要なら`context_limit` / `INSUFFICIENT_CONTEXT`を表現することである。

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
| N-04G-06 | P0 | **Complete (2026-10-18)** | validation failure時のretry / reject / insufficient policyを設計 |
| N-04G-07 | P0 | Pending | End-to-End designを統合しDesign Freeze |
| N-04G-08 | P0 | Pending | N-04 v2 benchmark / acceptance specを固定 |
| N-04G-09 | P0 | Pending | 採用設計を実装 |
| N-04G-10 | P0 | Pending | automated test / regressionを追加・実施 |
| N-04G-11 | P0 | Pending | formal re-acceptance harness / evidence手順をfreeze |
| N-04G-12 | P0 | Pending | Reference WorkstationでN-04を正式再受入しComplete判定 |

N-05へ進めるのは**N-04G-12でN-04 Completeが確認された後**とする。

N-04G-03〜G-06は相互依存するため設計上の往復を許容した。G-05を先に設計してG-04へvalidator要件を返す往復を完了し、G-06を含めて現在G-01〜G-06は個別Decisionとして揃っている。次のG-07でEnd-to-End整合を確認してDesign Freezeする。

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

- [x] SGOKB / MCP / Consumer / LLMの責務境界が確定している。
- [x] SGOKBが保証する範囲 / 保証しない範囲が確定している。
- [x] G-02以降が責務境界を前提に設計できる。

---

## N-04G-02 [P0] claim taxonomyと用途別意味境界を確定する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`

### Decision summary

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

- `separation_violation`をstored fact / interpretation / creative境界のpresentation failureとして扱う。
- Roleplay / Comparison / Creativeの許容・要分離・禁止境界を固定した。
- Context不足を安全に表す`context_limit`を正常classとして定義した。
- N-04 v1 Case 1〜3を新taxonomyで説明できる。

---

## N-04G-03 [P0] Context grounding / reference contractを設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`

### Decision summary

- **Context-local Grounding Reference + canonical identity metadata**方式を採用する。
- LLM-facing referenceは`K1`, `K2`, ...とし、1 grounded Context内だけで有効とする。
- 各`K*`は`object_id` / `resolved_version_id` / `source_kind` / canonical target identityへ追跡可能にする。
- `context_fingerprint + ref_id`でContext-local namespaceを識別する。
- Evidence IDは一次referenceではなくprovenance / audit用secondary metadataとする。
- J-04 Context Builderのselection後にreference projectionを行い、既存budget selection semanticsを変えない。
- reference存在だけをsemantic supportの証明にしない。
- contract概念名を`sgokb.grounded-context.v1`とする。
- canonical schema変更、新規persistent Fact IDは不要。

---

## N-04G-04 [P0] generation / output contractを設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`

### Decision summary

- **single-pass structured semantic units + deterministic rendering**方式を採用する。
- output contractを`sgokb.grounded-generation-output.v1`とする。
- LLMは`blocks[] -> units[]`のstructured envelopeを生成する。
- 各unitは`unit_id / semantic_role / text / support_refs[]`を持つ。
- `source_fact / interpretation`は`K*`をsupportとして宣言する。
- Grounding DispositionはLLMへ自己申告させず、G-05 validatorが判定する。
- LLMに別の`final_response`を生成させない。
- validated `unit.text`だけをConsumerが決定論的にrenderする。
- `interpretation / creative`はvisible presentation blockで分離する。
- provider-native Structured Outputはoptional optimizationとする。
- malformed outputはV0 failureとしsilent repairしない。
- 2-stage LLM rendererはbaselineとして不採用。
- canonical schema変更不要。

---

## N-04G-05 [P0] grounding validation方式を設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`

### Decision summary

- **deterministic validation + bounded semantic validationのHybrid方式**を採用する。
- V0 Contract / Parse、V1 Reference Integrity、V2 Taxonomy / Use-case Policy、V3 Deterministic Support、V4 Bounded Semantic Support、V5 Aggregate Verdictの段階に分ける。
- `K*` reference存在だけをsupport proofにしない。
- exact / structured supportはdeterministicに処理し、paraphrase / interpretation等の未解決部分だけsemantic validatorへ渡す。
- semantic validatorへはclaim / cited K等の必要最小限だけを渡し、Web / external Knowledgeを根拠に使わせない。
- same-model self-checkだけを最終Gateにしない。
- verdictを`PASS / FAIL / INDETERMINATE`で表し、`INDETERMINATE`をgrounded PASSへ昇格しない。
- `SGOKB-grounded`認定はfail-closedとする。
- validation contract概念名を`sgokb.grounding-validation.v1`とする。

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

---

## N-04G-06 [P0] validation failure時のretry / reject / insufficient policyを設計する

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`

### Decision summary

- **bounded single retry + fail-closed terminal handling**を採用する。
- 1 grounded-generation runのLLM再生成retryは**最大1回**とする（generation attemptは最大2回）。
- Retryでは`context_fingerprint / Grounded Context / purpose / generator model / runtime / generation settings / contract version`を固定する。
- Retryへ追加できるのはvalidatorの構造化failure feedbackだけであり、新規retrieval / Web / external Knowledgeを追加しない。
- Retryで別local model / cloud modelへfallbackしない。
- Retryはfailing unit patchではなくstructured output全体を再生成する。
- validation FAIL outputのsafe-looking unitだけをsilentに部分renderしない。
- terminal outcomeを`ACCEPTED / INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`に分ける。
- `context_limit`はvalidation failureではなく、Context不足を安全に表す正常outputとする。
- `INSUFFICIENT_CONTEXT`はproduction上の安全な正常終了になり得るが、N-04 Caseの最低quality Gateを自動的にPASSさせない。
- generator由来で修正可能な`VALIDATION_CONTRACT_ERROR / MISSING_REQUIRED_SUPPORT / UNSUPPORTED_CLAIM / CONTRADICTORY_CLAIM / ROLE_MISMATCH / SEPARATION_VIOLATION / CREATIVE_SCOPE_VIOLATION`等は最大1回retry対象とする。
- stale context / broken canonical mapping / validator unavailable等のsystem failureはgenerator retryせず`SYSTEM_FAILURE`へ分離する。
- semantic indeterminateがgenerator wording由来なら1回retry、validator capability / availability由来ならsystem failureとして扱う。
- attempt 1 / retry request / retry response / validation結果をすべてevidenceとして保存する。
- failure policy概念名を`sgokb.grounding-failure-policy.v1`とする。

### 完了条件

- [x] 即Reject / unlimited retry / model fallback / partial salvage / bounded retryを比較している。
- [x] retry上限を1回に固定している。
- [x] same Context / model / settings invariantを固定している。
- [x] failure class / causeごとのretry eligibilityを定義している。
- [x] retry feedbackへ渡してよい情報 / 禁止情報を定義している。
- [x] silent cloud / Web / model fallbackを禁止している。
- [x] whole-output regenerationとpartial salvage禁止を定義している。
- [x] `INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`の意味境界を定義している。
- [x] evidence保存を必須化している。
- [x] N-04 v1 Case 1〜3への適用を説明している。
- [x] canonical / Retrieval / MCP境界変更不要を確認している。

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
Hybrid Validation
        ↓
Failure Policy
  ├─ PASS → ACCEPTED / INSUFFICIENT_CONTEXT
  ├─ retryable → one retry
  ├─ grounding failure → REJECTED
  └─ system failure → SYSTEM_FAILURE
        ↓ accepted only
Deterministic Rendering
```

### 必須検討

- Case 1 / 2 / 3のend-to-end walkthrough。
- G-01〜G-06間の用語 / contract / sequence矛盾解消。
- canonical Knowledge / Retrieval / MCP境界への影響。
- N-06へ残すKnowledge coverage / retrieval quality課題との分離。
- model-independent部分とmodel-specific tuning部分の分離。
- retryを含むlogging / observability / evidence保存。
- retry PASSをformal N-04 v2でどう評価するかをG-08へ引き渡せること。

### 完了条件

- architecture / sequence / data contractが矛盾なく統合されている。
- 未決P0設計論点が残っていない。
- Candidate案の採用 / 不採用Decisionが統合記録されている。
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
- grounded context / generation / output / validation / failure handling contractを記録する。
- 同じ3代表use caseを継承する。
- generator / validator model policyを明記する。
- max generation attempts = 2をfreezeする。
- retry PASSをCase PASSとして認める条件をDesign Freezeと整合させて固定する。
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

### Scope候補

- SGOKB application grounding component
- consumer helper / acceptance harness
- Context presentation adapter / K mapping
- grounded generation output parser / schema
- Hybrid validator
- deterministic renderer
- retry / failure policy controller
- evidence logger

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

### 最低限のtest観点

- supported factual claim
- unsupported factual claim
- contradictory claim
- interpretation classification
- creative addition classification
- context limit / insufficient context
- malformed structured output
- final renderingとvalidated unitの一致
- validation failure path
- retry once / retry exhausted
- non-retryable system failure
- partial salvageが発生しないこと
- current / historical isolationを壊していないこと
- canonical mutationが発生しないこと

### 完了条件

- 採用contractの主要branchがautomated testでcoveredされている。
- focused testがPASSする。
- full pytestが`0 failed`で完了する。
- new skip / xfailでfailureを隠していない。

---

## N-04G-11 [P0] formal re-acceptance harness / evidence手順をfreezeする

### 必須固定項目

- evaluation DB / N-03 dataset
- MCP transport / public read route
- semantic runtime
- generator model / settings
- validator model / settings
- v2 prompt / structured output contract
- retry policy / max attempts
- deterministic rendering rule
- raw artifact保存先
- atomic claim evaluation手順
- before / after canonical snapshot
- integrity / pytest実行手順

### 完了条件

- formal runの実行順序が1本に固定されている。
- 失敗時の分類と記録方法が決まっている。
- formal run開始後にcase単位でmodel / rubric / protocol / retry回数をcherry-pickできない。

---

# 8. Formal Re-Acceptance

## N-04G-12 [P0] Reference WorkstationでN-04を正式再受入する

### 実施

freeze済みv2 acceptance spec / harnessだけを使用し、3ケースをReference Workstationで実行する。

### 必須記録

- Git head / working tree / environment
- generator / validator model / runtime metadata
- MCP request / response
- Grounded Context / K mapping
- attempt 1 request / raw structured response / validation
- retry feedback / attempt 2 request / response / validation（存在する場合）
- terminal outcome
- rendered human response（存在する場合）
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
N-04G-06 Failure handling Complete
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

---

## 10. Candidate案の現在の採否

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
bounded single retry: 採用
unlimited retry: 不採用
retry中の別model / cloud / Web fallback: 不採用
validation FAIL outputのpartial salvage: baselineとして不採用
valid context_limit / INSUFFICIENT_CONTEXT: 採用
Creative presentation: visible creative block separationを採用
```

---

## 11. 次に実施するTask

次のTaskは以下とする。

```text
N-04G-07 [P0]
End-to-End grounded-generation designを統合しDesign Freezeする
```

N-04G-01〜G-06の個別Decisionが揃ったため、次に責務・taxonomy・K* reference・structured generation・Hybrid validation・bounded single retryを1つの実装可能なsequence / data contractへ統合し、P0設計論点をfreezeする。
