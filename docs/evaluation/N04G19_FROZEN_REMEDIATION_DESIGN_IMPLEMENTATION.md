# N-04G-19 Frozen Remediation Design Implementation

更新日: 2026-10-19

- Status: **Complete (implementation)**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Design Freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Implementation branch: `phase-n/n04g19-v3-grounding-implementation`
- Next Task: `N-04G-20 [P0] Adversarial / Replay / Verifier Benchmark / Regression`

---

## 1. Result

G-18でFreezeしたPost-G12 v3 grounded-generation architectureをproduction codeへ実装した。

実装したlogical contract:

```text
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

`sgokb.context-builder.v1`および`sgokb.grounded-context.v1`は変更していない。

Canonical DB / MCP / Retrieval / Context Builder ownershipにも変更を加えていない。

---

## 2. Implemented components

### `src/sgokb/grounding/output.py`

- output contractを`sgokb.grounded-generation-output.v2`へ更新。
- role-specific block/unit JSON Schemaを実装。
- model-generated `label`を削除。
- `stylistic_expression`を削除。
- interpretationを`premise_unit_ids[]`方式へ変更。
- `context_limit`をstructured `limit_code`方式へ変更。
- context-limit exclusive shapeを実装。
- schema/application parserの正本を`GENERATION_OUTPUT_SCHEMA`へ集約。
- schema violationの`json_path / block_id / unit_id / expected_rule`保持を実装。
- canonical JSON + SHA-256 `output_digest()`を実装。
- validation/material/terminal/render共通の`output_binding()`を実装。
- provider/application schema identity用`generation_output_schema_hash()`を実装。

### `src/sgokb/grounding/verifiers.py`

G-20 benchmark可能なadapter boundaryを追加した。

```text
AtomicityRoleValidatorAdapter
SourceFactVerifierAdapter
SourceFactJudgeAdapter
InterpretationDerivationJudgeAdapter
```

特定model/checkpoint/thresholdはG-19では採用していない。

### `src/sgokb/grounding/validation.py`

`sgokb.grounding-validation.v2`を実装。

```text
V0 Structural Contract
V1 Reference Integrity
V2 Atomicity / Semantic Role / Scope
V3 Deterministic Source Support
V4F Source Fact Verification
V4I Interpretation Derivation
V5 Grounding Aggregate
```

主なfail-closed behavior:

- Atomicity/Role Gate未通過unitはsupport判定へ進めない。
- missing atomicity/role validatorはPASSへ倒さない。
- V3 unresolved source factはspecialized verifierへ送る。
- specialized verifier negativeをLLM judge positiveで救済しない。
- specialized positive + independent judge `ENTAILED`だけをsemantic supportとする。
- verifier disagreement / indeterminate / unavailableをPASSにしない。
- interpretationはsupported source_fact premiseだけを参照可能。
- unsupported premiseがある場合、derivation judgeを呼ばない。

### `src/sgokb/grounding/material_gate.py`

新規`MaterialRequirementGate`を実装。

- Grounding correctnessとuse-case completionを分離。
- generic roleplay/comparison/creative requirementを実装。
- harness requirement profile injectionを実装。
- K ref -> source Object coverageをdeterministically計算。
- comparisonのmulti-object coverage / cross-source interpretationを検査可能にした。
- creativeのmulti-Concept coverage + creative additionを検査可能にした。
- generator omissionとContext不足を`FAIL_REPAIRABLE` / `FAIL_CONTEXT_INSUFFICIENT`へ分離。
- `context_limit`をMaterial Gateで独立に正当化する。

### `src/sgokb/grounding/failure.py`

`sgokb.grounding-failure-policy.v2`を実装。

- bounded single retryを維持。
- Grounding + Material failureを統合してretry/terminalを決定。
- `ACCEPTED / INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`を実装。
- `NORMAL / CONTEXT_LIMIT_ONLY / NONE` render modeを実装。
- context不足時のcontext-limit-only repair pathを実装。
- structured retry feedbackへpremise/material coverage情報を追加。

### `src/sgokb/grounding/render.py`

terminal-bound rendererへ変更。

- validation PASSだけではrender不能。
- Material PASS + Terminal ACCEPTEDだけNORMAL render可能。
- confirmed Context insufficiencyだけCONTEXT_LIMIT_ONLY render可能。
- `REJECTED / SYSTEM_FAILURE`はgrounded render不可。
- output / validation / material / terminal間のcandidate identity bindingを検査。
- `context_limit` human-visible messageはtrusted fixed system textから生成。
- model label / free-form context-limit proseをrenderしない。

### `src/sgokb/application_grounding.py`

Application facadeをv3 pipelineへ配線した。

```text
project_context
build_request
validate
MaterialRequirementGate.evaluate
decide
build_retry_feedback
render
```

### `src/sgokb/grounding/evidence.py`

v3用にMaterial result / Terminal decision / rendered responseを保存できるAPIを追加した。

---

## 3. Focused test migration

`tests/test_n04_grounded_generation.py`をv3 contractへ移行した。

追加/移行した主なcoverage:

- output v2 shape / no label / no stylistic_expression
- context-limit exclusivity
- output digest stability
- schema hash exposure
- Atomicity/Role Gate fail-closed
- source-fact verifier negative / positive agreement / disagreement
- interpretation premise graph
- unsupported premise blocks derivation
- material roleplay minimum
- comparison both-source coverage
- creative both-Concept coverage + creative addition
- justified / unjustified context-limit
- terminal/render binding mismatch
- retry feedback
- Application facade end-to-end wiring

実装相当のisolated focused environmentで実行し:

```text
22 passed
```

を確認した。

これはG-19 implementation smoke/focused verificationであり、正式なG-20 regression resultではない。

---

## 4. Explicitly deferred to G-20 / G-21

G-19では以下をfinal adoptionしていない。

- MiniCheck / AlignScore exact checkpoint/revision
- source-fact verifier threshold / indeterminate band
- independent bounded LLM judge exact model/settings
- interpretation derivation judge exact model/settings
- atomicity/role classifier exact runtime
- provider structured-output compatibility preflight result

G-20でG-12 replay/adversarial/verifier benchmarkを実施し、required negative/replay false-positive = 0を満たすcandidate/profileのみG-21へ進める。

---

## 5. Verification boundary

G-19時点で確認済み:

```text
focused v3 tests: 22 passed (isolated/equivalent environment)
Python syntax: checked for implemented focused modules
```

G-20で必須:

```text
G-12 replay
adversarial tests
real verifier benchmark
provider/application schema preflight
full pytest
Ruff
git diff --check
```

したがってN-04はまだCompleteではない。

---

## 6. Completion assessment

- [x] output v2 schema/parser実装。
- [x] output digest / candidate binding実装。
- [x] atomicity/role adapter boundary実装。
- [x] source-fact verifier + independent judge adapter boundary実装。
- [x] interpretation premise/derivation path実装。
- [x] Material Requirement Gate実装。
- [x] failure policy v2実装。
- [x] terminal-bound renderer実装。
- [x] Application facade配線。
- [x] v3 evidence helper追加。
- [x] focused v3 testsへ移行し22 PASS確認。
- [x] exact verifier checkpoint/thresholdは未freezeのまま維持。
- [x] canonical DB / MCP boundaryを変更していない。

**N-04G-19 = Complete (implementation).**

次Task:

```text
N-04G-20 [P0] — Adversarial / Replay / Verifier Benchmark / Regression
```
