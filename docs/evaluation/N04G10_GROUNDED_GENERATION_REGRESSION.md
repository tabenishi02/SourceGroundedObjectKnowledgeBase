# N-04G-10 Grounded Generation Automated Test / Regression

更新日: 2026-10-18

- Status: **Complete / PASS**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-10 [P0] automated test / regressionを追加・実施する`
- Design Freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Frozen acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Implementation record: `docs/design/N04G09_GROUNDED_GENERATION_IMPLEMENTATION.md`
- Focused test: `tests/test_n04_grounded_generation.py`

---

## 1. Result

N-04G-09で実装したgrounded-generation componentに対し、focused automated testとrepository full regressionを実行した。

最終結果:

```text
compileall: PASS
focused N-04 grounding tests: 21 passed / 0 failed
full pytest: 382 passed / 0 failed / 0 skipped
ruff focused check: PASS
git diff --check: PASS
```

Full pytestでは既存Qdrant local-mode由来のwarningが2件出たが、failureではない。

```text
Payload indexes have no effect in the local Qdrant.
Local mode performs exact (brute-force) search, so search_params has no effect except idf.
```

N-04G-09実装に起因するregression failureは確認されなかった。

---

## 2. Execution environment

Automated regressionは、Reference WorkstationのDesktop Commanderが月間利用上限に達していたため、temporary GitHub Actions workflowを使用してisolated CI environmentで実行した。

```text
GitHub Actions hosted runner
OS: Ubuntu 24.04.5 LTS
Python: CPython 3.11.17
pytest: 9.1.1
ruff: 0.17.1
MCP SDK: 2.3.0
fastembed: 0.9.0
qdrant-client: 1.19.1
```

Project runtime requirement `Python >= 3.10`の範囲内である。

このCI runはG-10 automated regression用であり、Reference Workstation上のformal N-04 v2 re-acceptanceを代替しない。Actual generator / semantic validator / LM Studio / N-03 evaluation DBを使用するformal runはG-11 / G-12で実施する。

---

## 3. Test implementation

追加test:

```text
tests/test_n04_grounded_generation.py
```

Test commit:

```text
d02afaa373fbb27bc226dac0d78e68dd1fad500d
```

Focused suiteは外部LLMを使用せず、deterministic fake semantic validatorを用いてG-05/G-06の各branchを再現する。

これによりmodel stochasticityではなく、SGOKB-owned grounding contract implementation自体を検証する。

---

## 4. Covered requirements

### 4.1 Grounded Context / K reference

確認:

- Context projectionがdeterministic。
- `K1`, `K2`, ... assignmentがstable。
- canonical reference mappingが保持される。
- `context_fingerprint`を再計算・verifyできる。
- projection前のContext Builder outputをmutateしない。
- `resolved_version_id`が各K unitへbindingされる。
- current / historical Versionでfingerprintが分離され、silent cross-version identity reuseが起きない。

### 4.2 Generation output contract

確認:

- valid `sgokb.grounded-generation-output.v1`をparse可能。
- free prose / malformed JSONをreject。
- duplicate unit IDをreject。
- output schema / allowed role / Context bindingをrequest builderへ含める。

### 4.3 Supported / unsupported / contradictory

確認:

- exact supported `source_fact`はV3 deterministic supportでPASS。
- valid K referenceを付けてもsemantic supportがなければ`UNSUPPORTED_CLAIM`。
- contradictionは`CONTRADICTORY_CLAIM`として分離。
- reference存在だけではgrounding proofにならない。

### 4.4 Interpretation

確認:

- valid interpretationはmaterial K premise + semantic derivationで`derived_supported`。
- `interpretation`を`main` blockへ混在させると`SEPARATION_VIOLATION`。
- stored factとinterpretationのvisible scope separationを維持。

### 4.5 Creative addition

確認:

- `creative_addition`はcreative block / empty support refsでvalid。
- creative content自体にfactual supportを要求しない。
- main blockへ混入させると`CREATIVE_SCOPE_VIOLATION`。

### 4.6 Context limit / fail-closed

確認:

- valid `context_limit`はvalidation PASS可能。
- material responseがない場合は`INSUFFICIENT_CONTEXT`へterminal classification。
- semantic validator unavailableは`INDETERMINATE` + `SYSTEM_FAILURE`。
- unavailable validatorをgrounded PASSへ昇格しない。

### 4.7 Retry / reject

確認:

- retryable grounding failureはAttempt 1で`RETRY`。
- structured retry feedbackだけを生成。
- feedbackへnew Context / Web Knowledgeを追加しない。
- Attempt 2でもfailureなら`REJECTED`。
- max retry = 1 / max generation attempts = 2を維持。

### 4.8 Deterministic rendering / partial salvage prohibition

確認:

- rendererはvalidated `unit.text`をそのまま表示。
- interpretation labelをvisibleに保持。
- K/U internal identifiersをhuman outputへ混入しない。
- validation FAIL outputをrenderしない。
- validation resultが一部unitを欠く場合もrenderせず、partial salvageを禁止。

### 4.9 Application facade / evidence

確認:

- `GroundedGenerationApplication`がproject -> request -> validate -> decide -> renderのSGOKB-owned部分を一貫してcompositionできる。
- `GroundingEvidenceLogger`がattempt request / response / validationを別artifactとして保存できる。

---

## 5. Regression execution

Temporary workflow:

```text
.github/workflows/n04-g10-regression.yml
```

### Run #1

Commit:

```text
c7e673ca053bb26c98f15dba0e10e5583534a171
```

Result:

```text
compileall: PASS
focused tests: 21 passed
full pytest: 382 passed
ruff: PASS
workflow overall: FAIL
```

Failure reasonはcode/testではなく、checkout `fetch-depth=1`のため`git diff --check HEAD^`がparent commitを参照できなかったこと。

```text
fatal: ambiguous argument 'HEAD^'
```

Regression結果そのものはPASSしていたが、workflow harness defectとして修正した。

### Run #2 — final G-10 result

Workflow fix commit:

```text
fba00b6ba1a1191e6199a1af7485aff5207b3d21
```

GitHub Actions run:

```text
run_id = 39124414421
job_id = 117666427823
```

Result:

```text
compileall: PASS
focused N-04 tests: 21 passed in 0.09s
full pytest: 382 passed, 2 warnings in 87.57s
ruff: All checks passed
git diff --check HEAD^ HEAD: PASS
workflow: SUCCESS
```

Temporary workflowはG-10終了後に削除した。

Removal commit:

```text
6521e892f05c4d06d5d50fe75fb128dd7f853be7
```

Permanent CI導入は本Taskの目的ではないため、test codeだけをrepositoryへ残す。

---

## 6. Canonical / Retrieval safety

G-10でcanonical migration、Knowledge追加、retrieval tuning、MCP inference責務変更は行っていない。

Focused testではContext projectionが入力をmutateしないこと、Version bindingがfingerprint / K mappingへ反映されることを確認した。

Full regression 382件がすべてPASSしたため、既存canonical / ingestion / retrieval / MCP / exchange等のautomated behaviorにregressionは確認されなかった。

ただし、実N-03 evaluation DBのcanonical before / after snapshotはG-10 CIでは実施していない。これはG-11で手順をfreezeし、G-12 Reference Workstation formal re-acceptanceで必須実行する。

---

## 7. Completion decision

N-04G-10 completion conditionを満たす。

- [x] grounded-generation focused testsを追加。
- [x] v2 output parse / malformed outputを検証。
- [x] K reference / fingerprint integrityを検証。
- [x] supported / unsupported / contradictoryを検証。
- [x] interpretation / creative separationを検証。
- [x] context_limit / insufficientを検証。
- [x] retry once / retry exhaustedを検証。
- [x] system failure / fail-closedを検証。
- [x] deterministic rendering / partial salvage禁止を検証。
- [x] canonical input non-mutation / Version binding isolationを検証。
- [x] compileall PASS。
- [x] focused pytest: 21 passed / 0 failed。
- [x] full pytest: 382 passed / 0 failed / 0 skipped。
- [x] ruff PASS。
- [x] git diff --check PASS。
- [x] new skip / xfailでfailureを隠していない。

**N-04G-10 = Complete (2026-10-18)**

次Task:

```text
N-04G-11 [P0]
formal re-acceptance harness / evidence手順をfreezeする
```
