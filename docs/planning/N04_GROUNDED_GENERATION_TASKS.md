# N-04 Grounded Generation — Remediation Tasks

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current Status: **N-04 Failed — N-04G-01〜G-07 Complete / next N-04G-08 Acceptance Freeze**
- Branch: `phase-n/n04-prerequisite-derived-search`
- Failure baseline: `benchmark/n04-ai-use-cases-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Design handoff: `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`
- G-01: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- G-02: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- G-03: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- G-04: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- G-05: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- G-06: `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`
- G-07: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`

---

## 1. 本書の目的

N-04で判明したgrounded-generation failureを解消し、N-04を正式Completeへ戻すまでの実施順序とTask completion conditionを管理する。

N-04自体の最終Completion Gateは次を正本とし、rubricを緩めない。

- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- `benchmark/n04-ai-use-cases-v1.json`

v1はFailed baselineとして保持し、G-08でFrozen Designを評価可能なv2 acceptance specを別途作成する。

---

## 2. N-04 Completion Gate

### Retrieval / Context

- 3 caseすべてMCP public read boundaryを通る。
- AI consumerはdirect SQLite queryを使わない。
- current accepted Versionのみを既定利用する。
- historical Versionをsilentに混入しない。
- Case 2比較対象はactual Similarity retrievalから選ぶ。
- Context Builderのpurpose / budget contractを満たす。

### Local LLM

- formal runでは同じfrozen generator modelを3 caseで使う。
- silent cloud fallback禁止。
- Web / external Knowledgeによるfact補完禁止。
- Context不足をmodel memoryで穴埋めしない。

### Output Quality

**Case 1 Roleplay**

- first-person roleplayとして成立。
- Context内具体factを最低2件利用。
- Contextと矛盾しない。
- Context外franchise / backstory factを追加しない。

**Case 2 Comparison**

- 両WorkのContextから最低1件ずつfactual materialを利用。
- 最低1つの比較 / 対比。
- interpretationをstored factから分離。
- Context外franchise fact禁止。
- Similarity scoreのtruth / confidence化禁止。

**Case 3 Creative**

- 両Conceptのgrounded ideaを利用。
- 新規Character / arcへ統合。
- creative additionをSGOKB factから分離。
- source ConceptへContext外factを追加しない。

### Safety / Evidence

- canonical Knowledge不変。
- current pointer / Evidence / Provenance不変。
- system integrity PASS。
- full pytest 0 failed。
- Grounded Context / K mapping、raw structured response、validation、retry、rendered responseを保存。

---

## 3. Fixed boundaries

N-04対策だけを理由に次を再設計しない。

- Object identity
- current accepted Version semantics
- Statement / Attribute / Relation canonical model
- Evidence / Provenance
- Version immutability
- Retrieval / Similarity基本contract
- MCP = Knowledge Access Layer

Knowledge coverage / ranking qualityはN-06へ残す。

Context不足時の正しい挙動はmodel memory補完ではなく、必要に応じて`context_limit / INSUFFICIENT_CONTEXT`とする。

---

## 4. Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-04G-00 | P0 | **Complete (2026-10-18)** | Completion Gate確認 / Task分解 |
| N-04G-01 | P0 | **Complete (2026-10-18)** | 責務所有者 / 保証レベル |
| N-04G-02 | P0 | **Complete (2026-10-18)** | claim taxonomy / use-case境界 |
| N-04G-03 | P0 | **Complete (2026-10-18)** | Context grounding / reference |
| N-04G-04 | P0 | **Complete (2026-10-18)** | generation / output contract |
| N-04G-05 | P0 | **Complete (2026-10-18)** | grounding validation |
| N-04G-06 | P0 | **Complete (2026-10-18)** | retry / reject / insufficient policy |
| N-04G-07 | P0 | **Complete (2026-10-18)** | End-to-End統合 / Design Freeze |
| N-04G-08 | P0 | Pending | v2 benchmark / acceptance spec Freeze |
| N-04G-09 | P0 | Pending | Frozen Design実装 |
| N-04G-10 | P0 | Pending | automated test / regression |
| N-04G-11 | P0 | Pending | formal harness / evidence Freeze |
| N-04G-12 | P0 | Pending | Reference Workstation formal re-acceptance |

N-05へ進むのはG-12でN-04 Completeを確認した後とする。

---

# 5. Frozen Design Summary

## G-01 Responsibility

**SGOKB-owned contract + consumer-owned orchestration + untrusted LLM**を採用。

- SGOKB Application: grounding semanticsのOwner。
- MCP: transport / Knowledge Accessのみ。
- Consumer: model invocation / validation / retry / rendering実行。
- LLM: best-effort generator。raw outputはgroundedではない。

## G-02 Taxonomy

Semantic Role:

```text
source_fact
interpretation
creative_addition
context_limit
stylistic_expression
```

Grounding Disposition:

```text
supported
derived_supported
not_applicable
unsupported
contradictory
```

`interpretation / creative_addition`はstored factからpresentation上分離する。

## G-03 Grounded Context

```text
sgokb.grounded-context.v1
```

- LLM-facing referenceは`K1 / K2 / ...`。
- `context_fingerprint + K*`でnamespaceを識別。
- KはObject / resolved Version / canonical Knowledge itemへtrace可能。
- Evidence IDは一次generation referenceではない。
- canonical schema変更 / persistent Fact ID追加不要。

## G-04 Generation / Output

```text
sgokb.grounded-generation-output.v1
```

**single-pass structured semantic units + deterministic rendering**を採用。

```text
blocks[]
  units[]
    unit_id
    semantic_role
    text
    support_refs[]
```

- 別のmodel-generated `final_response`は禁止。
- Grounding DispositionをLLMに自己申告させない。
- validated `unit.text`だけをrenderする。
- interpretation / creativeはvisible block separation。
- malformed outputをsilent repairしない。

## G-05 Validation

```text
sgokb.grounding-validation.v1
```

Hybrid validation:

```text
V0 Contract / Parse
V1 Reference Integrity
V2 Taxonomy / Use-case Policy
V3 Deterministic Support
V4 Bounded Semantic Support
V5 Aggregate Verdict
```

Verdict:

```text
PASS
FAIL
INDETERMINATE
```

`INDETERMINATE`はPASSへ昇格しない。Same-model self-checkだけを最終Gateにしない。

## G-06 Failure handling

```text
sgokb.grounding-failure-policy.v1
```

**bounded single retry + fail-closed terminal handling**を採用。

- generation attempt最大2回。
- retry時もContext / model / runtime / settings / contract固定。
- retry追加情報はstructured failure feedbackのみ。
- new retrieval / Web /別model / cloud fallback禁止。
- partial salvage禁止。

Terminal outcome:

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

---

# 6. N-04G-07 Design Freeze

**Status: Complete (2026-10-18)**  
**Decision record:** `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`

Frozen End-to-End sequence:

```text
Canonical SGOKB Knowledge
        ↓
MCP / KnowledgeReadApplication / Context Builder
        ↓
sgokb.context-builder.v1
        ↓
Grounding Reference Projection
        ↓
sgokb.grounded-context.v1
        ↓
Consumer Generation Request
        ↓
Untrusted Local LLM
        ↓
sgokb.grounded-generation-output.v1
        ↓
sgokb.grounding-validation.v1
        ↓
sgokb.grounding-failure-policy.v1
  ├─ PASS → ACCEPTED / INSUFFICIENT_CONTEXT
  ├─ retryable → one retry
  ├─ grounding failure → REJECTED
  └─ system failure → SYSTEM_FAILURE
        ↓ ACCEPTED only
Deterministic Rendering
```

### Design Freeze invariants

1. AI inputのdirect SQLite禁止。
2. silent historical Version mixing禁止。
3. Web / external fact supplementation禁止。
4. raw LLM outputをgrounded扱いしない。
5. K reference存在だけをsupport proofにしない。
6. validation外のmodel-generated final proseを持たない。
7. unvalidated unitをgrounded contentとしてrenderしない。
8. unlimited retry禁止。
9. retry chain内のmodel / cloud fallback禁止。
10. failed outputのpartial salvage禁止。
11. grounded-generationからcanonical mutationしない。
12. N-04 rubricをPASS目的で緩和しない。

### Candidate統合採否

```text
Context-local K + canonical metadata: 採用
canonical ID direct citation: primaryとして不採用
Evidence ID direct citation: primaryとして不採用
persistent Fact ID: 不採用
single-pass structured units: 採用
separate final_response: 不採用
2-stage LLM renderer: baseline不採用
deterministic renderer: 採用
Hybrid validator: 採用
same-model self-check only: 不採用
bounded single retry: 採用
unlimited retry: 不採用
model/cloud/Web retry fallback: 不採用
partial salvage: baseline不採用
context_limit / INSUFFICIENT_CONTEXT: 採用
Creative addition: visible separation付きで採用
```

### Architecture impact

canonical DB migration、Evidence / Provenance redesign、Retrieval ranking redesign、MCP推論主体化はいずれも不要。

G-09 implementation scopeとして以下を想定する。

```text
GroundedContextProjector
GroundedGenerationContract / parser
GroundingValidator
SemanticValidatorAdapter
GroundingFailureController
DeterministicRenderer
GroundingEvidenceLogger
```

物理class / module名は変更可能だが、Frozen responsibility / semanticsは変更しない。

### Open P0 issue

**なし。**

exact JSON Schema、物理module配置、具体generator / validator model、generation parameters、formal evidence naming等は後続Taskで固定するoperation / implementation detailである。

Frozen semanticsと衝突する変更が必要になった場合、G-07を明示的にreopenして再Decisionする。

---

# 7. N-04G-08 [P0] v2 benchmark / acceptance specを固定する

### 方針

`benchmark/n04-ai-use-cases-v1.json`はFailed baselineとして変更しない。

新規v2 specでG-07 Frozen Designを評価可能にする。

最低限freezeする項目:

- same 3 use cases
- v1 core quality Gate維持
- four grounded-generation contract versions
- generator / validator model policy
- generation / validator settings
- max generation attempts = 2
- retry PASSの扱い
- `INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`のCase評価
- artifact / evidence requirement
- formal run開始後のrubric / model / retry policy変更禁止

Retry attempt 2がvalidation PASSしuse-case quality Gateも満たす場合、workflow上は`ACCEPTED`になり得る。attempt countは必ず記録する。

`INSUFFICIENT_CONTEXT`はgrounding-safeな終了になり得るが、Case quality Gateを自動PASSさせない。

---

# 8. N-04G-09 [P0] Frozen Designを実装する

実装候補:

- Grounded Context projection / K mapping
- context fingerprint
- generation request / output schema
- Hybrid validator
- bounded semantic validator adapter
- deterministic renderer
- retry / terminal outcome controller
- evidence logging

禁止:

- benchmark固有hardcode
- N-06 ranking tuning混在
- silent cloud / Web fallback
- canonical Knowledge追加で見かけのPASSを作ること

---

# 9. N-04G-10 [P0] automated test / regression

最低観点:

- supported / unsupported / contradictory source fact
- interpretation support
- creative addition separation
- context limit
- malformed structured output
- K / fingerprint integrity
- deterministic rendering一致
- retry once / exhausted
- non-retryable system failure
- partial salvageなし
- current / historical isolation
- canonical mutationなし

full pytestは`0 failed`必須。

---

# 10. N-04G-11 [P0] formal harness / evidence Freeze

formal run前に固定する。

- evaluation DB / N-03 dataset
- MCP public read route
- generator model / runtime / settings
- validator model / runtime / settings
- prompt / structured output schema
- retry policy
- deterministic rendering
- artifact保存先 / naming
- before / after canonical snapshot
- integrity / pytest手順

Caseごとのmodel / rubric / protocol / retry回数cherry-pickは禁止。

---

# 11. N-04G-12 [P0] Formal Re-Acceptance

3 caseをfreeze済みv2 spec / harnessだけで実行する。

必須evidence:

- Git / environment
- generator / validator metadata
- MCP request / response
- Grounded Context / K mapping
- attempt 1 request / response / validation
- retry attempt artifacts（存在時）
- terminal outcome
- rendered response
- atomic claim support evaluation
- canonical before / after
- integrity
- focused regression
- full pytest

Critical Gateを1件でも満たさなければN-04 Completeにしない。

---

## 12. Task dependency

```text
N-04G-00 Complete
       ↓
N-04G-01 Complete
       ↓
N-04G-02 Complete
       ↓
N-04G-03 Complete
       ↓
N-04G-04 Complete
       ↓
N-04G-05 Complete
       ↓
N-04G-06 Complete
       ↓
N-04G-07 Design Freeze Complete
       ↓
N-04G-08 v2 Acceptance Freeze
       ↓
N-04G-09 Implementation
       ↓
N-04G-10 Automated Test / Regression
       ↓
N-04G-11 Formal Harness Freeze
       ↓
N-04G-12 Formal Re-Acceptance
       ↓
N-04 Complete
       ↓
N-05
```

---

## 13. 次に実施するTask

```text
N-04G-08 [P0]
N-04 v2 benchmark / acceptance specを固定する
```

G-07でFrozenしたEnd-to-End contractを、formal run開始前に再現可能なv2 benchmark / acceptance specificationへ変換する。
