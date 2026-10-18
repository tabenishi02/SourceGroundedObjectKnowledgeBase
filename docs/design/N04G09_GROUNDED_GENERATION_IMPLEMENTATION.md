# N-04G-09 Grounded Generation Implementation

更新日: 2026-10-18

- Status: **Implemented**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04G-09 [P0] Frozen grounded-generation designを実装する`
- Design Freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Frozen acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Automated verification: **N-04G-10で実施**

## 1. 実装概要

G-07 / G-08でFreezeした意味設計を変更せず、次の実装を追加した。

```text
src/sgokb/grounding/
  context.py
  request.py
  output.py
  validation.py
  failure.py
  render.py
  evidence.py
  __init__.py

src/sgokb/application_grounding.py
```

既存のcanonical schema、Context Builder selection、Retrieval、MCP transport責務は変更していない。

## 2. GroundedContextProjector

`src/sgokb/grounding/context.py`

- `sgokb.context-builder.v1` outputを入力とする。
- selection完了後のKnowledgeへ`K1..Kn`を決定論的に割り当てる。
- `object_field / statement / attribute / relation`を共通Grounding Unitへ投影する。
- 各unitを`object_id / resolved_version_id / canonical_ref`へbindする。
- Evidenceはsecondary `evidence_refs`として保持する。
- canonical JSON + SHA-256で`context_fingerprint`を生成する。
- `verify()`でfingerprint integrityを再検証できる。
- Context Builder budget selectionを変更しない。

## 3. Generation request / output contract

### Request Builder

`src/sgokb/grounding/request.py`

- provider非依存でuser task、Grounded Context、output schema、semantic role/support ruleを組み立てる。
- retry時はG-06のstructured feedbackだけを追加できる。
- provider-specific chat API / model invocationは所有しない。

### Output contract

`src/sgokb/grounding/output.py`

- `sgokb.grounded-generation-output.v1`のexact JSON Schemaを実装した。
- `blocks[] -> units[]`を必須とする。
- unitは`unit_id / semantic_role / text / support_refs[]`を持つ。
- duplicate block/unit ID、unknown field、malformed JSONをV0向けcontract errorにする。
- interpretation / creative blockはvisible labelを必須とする。
- free proseのheuristic repairは行わない。

## 4. Hybrid Grounding Validator

`src/sgokb/grounding/validation.py`

G-05に従い次を実装した。

```text
V0 Contract / Parse
V1 Reference Integrity
V2 Taxonomy / Use-case Policy
V3 Deterministic Support
V4 Bounded Semantic Support
V5 Aggregate Verdict
```

- Grounded Context fingerprint integrityを検査する。
- output fingerprint / purpose bindingを検査する。
- unknown K / broken canonical mappingを検出する。
- role別support requirementとpresentation scopeを検査する。
- exact normalized source factはV3でdeterministic support可能。
- paraphrase / interpretation / semantic-role boundaryは`SemanticValidatorAdapter`へ限定入力で委譲する。
- semantic validator未提供またはruntime failure時は`VALIDATOR_UNAVAILABLE`としてfail-closedにする。
- semantic validatorはG-05 minimum verdictに加え、creative/style/context-limit境界確認用`role_valid`を実装上の拡張として返せる。
- `PASS / FAIL / INDETERMINATE`を返す。

## 5. Failure controller

`src/sgokb/grounding/failure.py`

- `sgokb.grounding-failure-policy.v1`を実装した。
- max retry = 1 / max attempts = 2。
- `ACCEPTED / INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`を分離する。
- system failureはgenerator retryへ流さない。
- retry可能failureだけからstructured repair feedbackを生成する。
- repair feedbackに外部fact、Web、模範解答を含めない。
- whole-output regeneration前提でpartial salvage機能は持たない。

## 6. Deterministic Renderer

`src/sgokb/grounding/render.py`

- validation `PASS`以外をrenderしない。
- validation対象outputとrender対象outputの同一性を要求する。
- 全unitに成功したvalidation resultが存在することを確認する。
- block/unit順序を保持する。
- `unit.text`をparaphraseしない。
- interpretation / creative / context-limitはvisible headingを決定論的にrenderする。
- K / U等のinternal IDは通常responseへ出さない。

## 7. Evidence Logger

`src/sgokb/grounding/evidence.py`

- Git管理外acceptance evidence保存用のJSON writerを実装した。
- attempt 1 / 2のrequest / response / validationを個別保存できる。
- canonical Knowledgeへ書き戻す機能は持たない。

## 8. Application facade

`src/sgokb/application_grounding.py`

Consumerが内部classを独自再構成しなくても、SGOKB-owned contractを次の順に利用できるFacadeを追加した。

```text
project_context
build_request
parse_output
validate
decide
build_retry_feedback
render
```

LLM runtime / provider / endpoint invocationはFacadeへ入れていない。G-01/G-07どおりconsumer orchestration責務に留めている。

## 9. Freezeとのtraceability

| Frozen requirement | Implementation |
|---|---|
| Context-local K + canonical mapping | `grounding/context.py` |
| deterministic context fingerprint | `grounding/context.py` |
| structured semantic units | `grounding/output.py` |
| provider-neutral generation request | `grounding/request.py` |
| no separate model final_response | output schema / renderer boundary |
| Hybrid V0..V5 validation | `grounding/validation.py` |
| bounded semantic validator boundary | `SemanticValidatorAdapter` |
| max one retry | `grounding/failure.py` |
| fail-closed terminal outcomes | `grounding/failure.py` |
| validated units only rendered | `grounding/render.py` |
| evidence preservation helper | `grounding/evidence.py` |
| SGOKB-owned composition | `application_grounding.py` |

## 10. 非変更範囲

次は変更していない。

- canonical DB / 52-table structure
- Object / Version identity
- Statement / Attribute / Relation schema
- Evidence / Provenance schema
- J-04 Context Builder selection / budget contract
- Similarity / Retrieval ranking
- MCPをKnowledge Access / transport layerとする責務
- current / historical semantics

MCP `build_context` responseをConsumerが受けた後、SGOKBの`GroundedGenerationApplication.project_context()`へ渡すことでv2 pathを構成できる。

## 11. G-10への引き渡し

G-09ではproduction codeを実装した。次のN-04G-10で最低限以下をautomated testする。

- deterministic K assignment / fingerprint stability
- output schema / malformed rejection
- supported / unsupported / contradictory / interpretation
- creative/style/context-limit role boundary
- unknown K / fingerprint mismatch
- semantic validator unavailable
- retry once / retry exhausted / system failure
- partial salvageなし
- deterministic rendering equality
- canonical mutationなし
- focused test + full pytest + ruff/compile相当の確認

G-10で設計意味の変更が必要になった場合は、silent fixではなくG-07/G-08 Freeze再open要否を判定する。
