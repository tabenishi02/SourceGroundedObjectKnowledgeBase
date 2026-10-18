# N-04 Grounded Generation — Remediation Tasks

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current Status: **N-04 Failed — N-04G-01〜G-11 Complete / next N-04G-12 Formal Re-Acceptance**
- Branch: `phase-n/n04-prerequisite-derived-search`
- Failed baseline: `benchmark/n04-ai-use-cases-v1.json`
- Frozen v2 acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Frozen formal harness: `benchmark/n04-v2-formal-harness-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Design handoff: `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`
- G-01: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- G-02: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- G-03: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- G-04: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- G-05: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- G-06: `docs/decisions/N04G06_VALIDATION_FAILURE_HANDLING_POLICY.md`
- G-07: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- G-08: `docs/decisions/N04G08_N04_V2_ACCEPTANCE_SPEC_FREEZE.md`
- G-08/G-11 clarification: `docs/decisions/N04G08_G11_GENERATION_SETTINGS_CLARIFICATION.md`
- G-09: `docs/design/N04G09_GROUNDED_GENERATION_IMPLEMENTATION.md`
- G-10: `docs/evaluation/N04G10_GROUNDED_GENERATION_REGRESSION.md`
- G-11: `docs/decisions/N04G11_FORMAL_REACCEPTANCE_HARNESS_FREEZE.md`

---

## 1. 本書の目的

N-04で判明したgrounded-generation failureを解消し、N-04を正式Completeへ戻すまでの実施順序とTask completion conditionを管理する。

N-04 v1のFailed baselineは変更しない。

```text
benchmark/n04-ai-use-cases-v1.json
```

G-08以降の正式再受入仕様は次を正本とする。

```text
benchmark/n04-ai-use-cases-v2.json
benchmark/n04-v2-formal-harness-v1.json
```

v2はv1の3代表caseと核心rubricを継承し、G-07 Frozen Designを追加したものである。rubric緩和による見かけのPASSは禁止する。

---

## 2. N-04 Completion Gate

### Retrieval / Context

- 3 caseすべてMCP public read boundaryを通る。
- AI consumerはdirect SQLite Knowledge readを行わない。
- current accepted Versionのみを既定利用する。
- historical Versionをsilentに混入しない。
- Case 2比較対象はactual Similarity retrievalから選ぶ。
- Context Builder purpose / budget contractを満たす。
- Grounded Contextは`context_fingerprint + K*`でtrace可能である。

### Generator / Validation

- formal runでは1つのfrozen local generator model/runtime/load profileを全caseで使用する。
- case別temperature / max_tokensはFrozen v2 benchmark値を使用し、同一caseのretry前後では完全固定する。
- silent cloud / Web / external factual supplementation禁止。
- `sgokb.grounded-generation-output.v1`のstructured semantic unitsを使用する。
- `sgokb.grounding-validation.v1`のHybrid validationを通す。
- `INDETERMINATE`をgrounded PASSへ昇格しない。
- generation retryは各case最大1回、generation attempt最大2回。
- retry中のContext / generator model / settings変更禁止。

### Output Quality

**Case 1 Roleplay**

- first-person roleplay。
- Context内具体factを最低2件利用。
- unsupported / contradictory source-world fact = 0。
- Context外franchise / backstory factを追加しない。

**Case 2 Comparison**

- 両Workから最低1件ずつgrounded factual material。
- comparison / contrastあり。
- interpretationをstored factからvisibleに分離。
- interpretation premiseはgrounded。
- Similarity score semantic misuseなし。

**Case 3 Creative**

- 両Conceptからgrounded ideaを利用。
- 両Conceptを新規Character / arcへ統合。
- creative additionをsource Knowledgeからvisibleに分離。
- source Concept unsupported fact = 0。

### Terminal outcome / Formal Case PASS

formal Case PASSに利用できるterminal outcomeは`ACCEPTED`のみ。

```text
ACCEPTED             -> rubricを全て満たせばCase PASS候補
INSUFFICIENT_CONTEXT -> safe outcomeだがCase FAIL
REJECTED             -> Case FAIL
SYSTEM_FAILURE       -> Case FAIL
```

Attempt 2で`ACCEPTED`になった場合も、Frozen retry policyを満たしAttempt 1を含む全evidenceを保存していればCase PASSを認める。

### Overall PASS

```text
3 / 3 Case PASS required
```

加えて:

- canonical before / after invariance
- system integrity PASS
- focused grounding regression PASS
- full pytest = 0 failed
- new skip / xfailでfailureを隠さない

を要求する。

Retrieval ranking formal metricsはN-06へ残す。

---

## 3. 設計上の固定境界

N-04 remediationだけを理由に次を再設計しない。

- Object identity
- current accepted Version semantics
- Statement / Attribute / Relation canonical model
- Evidence / Provenance
- Version immutability
- Retrieval / Similarity基本contract
- MCPをKnowledge Access Layerとする境界

canonical KnowledgeをN-04 PASS目的で追加・改変しない。

---

## 4. Task一覧

| Task | Priority | Status | 主目的 |
|---|---|---|---|
| N-04G-00 | P0 | **Complete (2026-10-18)** | N-04 Completion Gate確認とremediation Task分解 |
| N-04G-01 | P0 | **Complete (2026-10-18)** | grounded-generation責務 / guarantee boundary |
| N-04G-02 | P0 | **Complete (2026-10-18)** | claim taxonomy / use-case boundary |
| N-04G-03 | P0 | **Complete (2026-10-18)** | Grounded Context / reference contract |
| N-04G-04 | P0 | **Complete (2026-10-18)** | generation / output contract |
| N-04G-05 | P0 | **Complete (2026-10-18)** | grounding validation design |
| N-04G-06 | P0 | **Complete (2026-10-18)** | retry / reject / insufficient policy |
| N-04G-07 | P0 | **Complete (2026-10-18)** | End-to-End Design Freeze |
| N-04G-08 | P0 | **Complete (2026-10-18)** | N-04 v2 benchmark / acceptance freeze |
| N-04G-09 | P0 | **Complete (2026-10-18)** | Frozen grounded-generation designを実装 |
| N-04G-10 | P0 | **Complete (2026-10-18)** | automated test / regression |
| N-04G-11 | P0 | **Complete (2026-10-18)** | formal re-acceptance harness / evidence freeze |
| N-04G-12 | P0 | Pending | Reference Workstation formal re-acceptance |

N-05へ進めるのはN-04G-12でN-04 Completeが確認された後とする。

---

# 5. Completed Design / Acceptance Decisions

## N-04G-01 — Responsibility boundary

**Decision:** `SGOKB-owned contract + consumer-owned orchestration + untrusted LLM`

- SGOKBがgrounding semantics / conformance contractを所有する。
- MCPはKnowledge Access / transport adapterのまま。
- Consumerがruntime invocation / validation / retry / evidence保存を実行する。
- raw LLM outputはgroundedではない。

---

## N-04G-02 — Claim taxonomy

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

Interpretation / creative additionはstored factからvisibleに分離する。

---

## N-04G-03 — Grounded Context / K references

**採用:** Context-local `K*` + canonical identity metadata。

```text
sgokb.grounded-context.v1
context_fingerprint + K1 / K2 / ...
```

新規persistent Fact ID / canonical schema変更は不要。

---

## N-04G-04 — Generation / Output

**採用:** single-pass structured semantic units + deterministic rendering。

```text
sgokb.grounded-generation-output.v1
blocks[] -> units[]
unit_id / semantic_role / text / support_refs[]
```

- model-generated別`final_response`は禁止。
- validated `unit.text`だけをrenderする。
- provider-native Structured Outputはoptional optimization。

---

## N-04G-05 — Validation

**採用:** deterministic + bounded semantic Hybrid validation。

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

Grounding certificationはfail-closed。

---

## N-04G-06 — Failure handling

**採用:** bounded single retry + fail-closed terminal handling。

- max retry = 1
- max generation attempts = 2
- retry中Context / model / settings固定
- validation feedback以外の追加Knowledge禁止
- partial salvage禁止

Terminal outcome:

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

---

## N-04G-07 — End-to-End Design Freeze

**Status:** Accepted / Design Frozen。

Frozen sequence:

```text
Canonical Knowledge
  -> Context Builder
  -> Grounded Context / K*
  -> Consumer
  -> Local LLM
  -> Structured Semantic Units
  -> Hybrid Validation
  -> Failure Policy
  -> ACCEPTED only
  -> Deterministic Rendering
```

P0意味設計のsilent driftは禁止。変更にはG-07 reopenが必要。

---

## N-04G-08 — v2 Acceptance Freeze

**Status: Complete (2026-10-18)**  
**Decision:** `docs/decisions/N04G08_N04_V2_ACCEPTANCE_SPEC_FREEZE.md`  
**Machine spec:** `benchmark/n04-ai-use-cases-v2.json`  
**G-11 clarification:** `docs/decisions/N04G08_G11_GENERATION_SETTINGS_CLARIFICATION.md`

### Decision summary

- v1をFailed baselineとして不変保持する。
- v2は同じ3代表case / 同じ核心quality Gateを継承する。
- Grounded Context / K mappingをformal evidenceへ追加する。
- structured semantic units + deterministic renderingを必須化する。
- Hybrid validationを必須化する。
- generator model/runtime/load profileはformal run前に1つへfreezeし、formal run中のmodel switchを禁止する。
- case別temperature / max_tokensはv2 machine spec値を固定し、同一caseのretry前後で変更しない。
- v1のmodel-switch retry ruleはv2では廃止する。
- semantic validatorは必要時にgenerator-independentなfixed local validator policyを使用する。
- max generation attempts = 2 / max retry = 1をfreezeする。
- retry PASSはFrozen retry invariantと完全evidenceを満たす場合に限りCase PASSを認める。
- `INSUFFICIENT_CONTEXT`はsafe terminal outcomeだがN-04 Case PASSには数えない。
- formal Case PASSは`ACCEPTED + all case gates + critical failure 0`を要求する。
- Overall N-04 v2 PASSは3 / 3 Case PASSを要求する。
- formal run開始後のrubric / model / protocol / retry policy cherry-pickを禁止する。

### Completion condition

- [x] v1 Failed baseline不変。
- [x] `benchmark/n04-ai-use-cases-v2.json`作成。
- [x] G-07 Frozen Designと一致。
- [x] generator / validator policy定義。
- [x] retry PASS / insufficient / terminal outcomeのCase判定を固定。
- [x] 3 / 3 Overall PASSを固定。
- [x] G-09〜G-11への引き渡しを定義。
- [x] G-11でgeneration-settings wording ambiguityをbinding clarificationした。

---

# 6. Implementation / Formal Acceptance Tasks

## N-04G-09 [P0] Frozen grounded-generation designを実装する

**Status: Complete (2026-10-18)**  
**Implementation record:** `docs/design/N04G09_GROUNDED_GENERATION_IMPLEMENTATION.md`

### Implemented components

```text
src/sgokb/grounding/context.py
src/sgokb/grounding/request.py
src/sgokb/grounding/output.py
src/sgokb/grounding/validation.py
src/sgokb/grounding/failure.py
src/sgokb/grounding/render.py
src/sgokb/grounding/evidence.py
src/sgokb/grounding/__init__.py
src/sgokb/application_grounding.py
```

### Implementation summary

- `GroundedContextProjector`: Context Builder outputからdeterministic K mapping / SHA-256 context fingerprintを生成。
- `GroundedGenerationRequestBuilder`: provider-neutral generation request / exact output schema / retry feedbackを構成。
- `sgokb.grounded-generation-output.v1`: strict JSON Schema / parserを実装。
- `GroundingValidator`: V0〜V5 Hybrid validationとfail-closed semantic adapter boundaryを実装。
- `GroundingFailureController`: max 1 retry、4 terminal outcomes、structured retry feedbackを実装。
- `DeterministicRenderer`: validation PASSしたunit textだけを決定論的にrender。
- `GroundingEvidenceLogger`: attempt artifact保存helperを実装。
- `GroundedGenerationApplication`: SGOKB-owned contract componentをFacadeとして統合。
- canonical DB / Retrieval / Context Builder selection / MCP inference責務は変更していない。
- benchmark case固有hardcode、Web/cloud fallback、partial salvageは追加していない。

### Completion

- [x] Frozen Design / v2 specとのtraceabilityを文書化。
- [x] 3 use caseに依存しない共通componentとして実装。
- [x] existing MCP / Knowledge read boundaryを維持。
- [x] canonical schema migrationなし。
- [x] provider / model-specific runtimeをSGOKB contract層へ混入させていない。
- [x] G-10へautomated verification観点を引き渡した。

---

## N-04G-10 [P0] Automated Test / Regression

**Status: Complete (2026-10-18)**  
**Evaluation record:** `docs/evaluation/N04G10_GROUNDED_GENERATION_REGRESSION.md`

### Added focused test

```text
tests/test_n04_grounded_generation.py
```

### Final automated result

```text
compileall: PASS
focused pytest: 21 passed / 0 failed
full pytest: 382 passed / 0 failed / 0 skipped
ruff: PASS
git diff --check: PASS
```

Temporary GitHub Actions workflowは実行後に削除した。Formal Reference Workstation acceptanceはG-11/G-12へ残す。

### Completion

- [x] focused grounded-generation tests追加。
- [x] G-10最低test観点をcovered。
- [x] compileall PASS。
- [x] focused test PASS。
- [x] full pytest 0 failed / 0 skipped。
- [x] ruff PASS。
- [x] git diff --check PASS。
- [x] new skip / xfailでfailureを隠していない。
- [x] G-11へformal harness freezeを引き渡せる。

---

## N-04G-11 [P0] Formal Harness Freeze

**Status: Complete (2026-10-18)**  
**Decision:** `docs/decisions/N04G11_FORMAL_REACCEPTANCE_HARNESS_FREEZE.md`  
**Machine harness:** `benchmark/n04-v2-formal-harness-v1.json`

### Frozen actual runtime

Generator:

```text
LM Studio 0.4.25.0
http://127.0.0.1:1234/v1
sgokb-n04-mistral32
Mistral Small 3.2 24B Instruct Q4_K_M
context 8192 / GPU offload=max / parallel=1 / seed=20261018
```

Semantic validator:

```text
LM Studio 0.4.25.0
sgokb-n04-phi4
Phi-4 Q4_K_S
context 8192 / GPU offload=max / parallel=1
temperature=0.0 / max_tokens=64 / seed=20261018
```

GeneratorとvalidatorはVRAM上必要ならsequential load/unload可。ただしidentifier / model file / load config / inference settings変更禁止。

### Frozen case settings

```text
Case 1: temperature=0.2 / max_tokens=700
Case 2: temperature=0.0 / max_tokens=900
Case 3: temperature=0.2 / max_tokens=1100
```

同一caseのAttempt 1 / Attempt 2で完全一致させる。

### Frozen harness boundary

- N-03 evaluation DB / Harrier / Qdrant profileを固定。
- MCP stdio command / environmentを固定。
- LM Studio structured JSON Schema outputをformal pathで使用。
- V4 semantic judge prompt / verdict enumを固定。
- preflight完了後のCase 1最初のMCP requestをformal startと定義。
- case orderをRoleplay -> Comparison -> Creativeに固定。
- max retry=1 / max attempts=2を維持。
- evidence rootを`.local/n04-v2/runs/<run_id>/`へ固定。
- canonical safetyはevaluation DB SHA-256 before/after一致 + integrity before/after PASSを要求。
- G-12後にReference Workstation focused/full regressionを再実行する。
- final rubric authorityはbenchmark rubricに対するCodex/human evidence reviewとし、model self-scoreを採用しない。

### Completion

- [x] actual generatorをFreeze。
- [x] actual generator-independent semantic validatorをFreeze。
- [x] case-specific generation settingsをFreeze。
- [x] exact MCP / retrieval runtimeをFreeze。
- [x] structured-output / validator protocolをFreeze。
- [x] preflight / formal-start boundaryをFreeze。
- [x] exact evidence treeをFreeze。
- [x] canonical before/after procedureをFreeze。
- [x] Reference Workstation regression procedureをFreeze。
- [x] formal run prohibited actionsをFreeze。
- [x] G-12へ引き渡し可能。

---

## N-04G-12 [P0] Formal N-04 Re-Acceptance

Frozen v2 spec / G-11 harnessだけを使用する。

必須evidence:

```text
Git/environment
generator/validator metadata
MCP request/response
Grounded Context / K mapping
attempt 1 request/output/validation
retry artifacts if used
terminal outcome
rendered response if ACCEPTED
atomic claim evaluation
canonical before/after
system integrity
focused regression
full pytest
```

N-04 Completeには3 / 3 Case PASS + safety/regression Gate全PASSが必要。

完了後:

- N-04 acceptance recordをv2 resultで更新。
- `PHASE_N_PREPARATION.md` N-04 Complete。
- `KNOWLEDGE_BASE_REDESIGN_TASKS.md` N-04 Complete。
- PR #39最終状態更新。
- N-05へ進行可能とする。

---

## 7. Task dependency

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
N-04G-08 Acceptance Freeze Complete
       ↓
N-04G-09 Implementation Complete
       ↓
N-04G-10 Automated Test / Regression Complete
       ↓
N-04G-11 Formal Harness Freeze Complete
       ↓
N-04G-12 Formal N-04 Re-Acceptance
       ↓
N-04 Complete
       ↓
N-05
```

---

## 8. Candidate採否 — Frozen

```text
Context-local K* + canonical metadata: 採用
persistent new Fact ID: 不採用
canonical ID direct citation: 一次referenceとして不採用
Evidence ID direct citation: 一次referenceとして不採用
single-pass structured semantic units: 採用
deterministic renderer: 採用
separate model-generated final_response: 不採用
2-stage LLM renderer: baseline不採用
Hybrid post-generation validator: 採用
same-model self-check only: 最終Gateとして不採用
bounded single retry: 採用
unlimited retry: 不採用
retry中のmodel/cloud/Web fallback: 不採用
partial salvage: baseline不採用
valid context_limit / INSUFFICIENT_CONTEXT: 採用
INSUFFICIENT_CONTEXTをN-04 Case PASSに数える: 不採用
retry後ACCEPTEDをCase PASS候補にする: 条件付き採用
Creative visible scope separation: 採用
```

---

## 9. 次に実施するTask

```text
N-04G-12 [P0]
Reference Workstation formal N-04 v2 re-acceptanceを実施し、N-04 Complete判定を行う
```
