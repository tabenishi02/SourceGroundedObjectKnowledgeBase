# N-04G-21 v3 Acceptance / Reference Workstation Harness Freeze

更新日: 2026-10-19

- Status: **Prepared / BLOCKED before final Freeze**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Base main SHA: `95145f21f8f3f62ed9cf18d189920c49107a6b06`
- Branch: `phase-n/n04g21-v3-acceptance-harness-freeze`
- Design authority: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- G-20 verifier screening: `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
- G-20R engineering Gate: `docs/evaluation/N04G20R_RUFF_BASELINE_REMEDIATION_AND_GATE_RERUN.md`

---

## 1. Decision

N-04G-21で必要なv3 acceptance spec / Reference Workstation harnessの**freeze candidate**を作成した。

ただし、本Taskを`Complete / Frozen`にはしない。

G-18およびG-20/G-20R handoffは、source-fact verifierのexact local runtime/profileをReference Workstationで確認してからG-21をfreezeすることを要求している。

2026-10-19の本作業時点ではReference Workstation `FNB1Main`はDesktop Commander上でOnlineだったが、Remote Desktop Commanderの月次利用上限によりcommand executionが拒否された。

したがって次の3点を実測できていない。

1. Reference WorkstationのMiniCheck exact local snapshot / model revision解決状態。
2. pinned threshold `0.50`でのG-20 verifier corpus local replay。
3. MiniCheck/Torch/Transformers/Hugging Face/NLTK等のexact installed package versions。

これらを未確認のまま`Frozen`と表記することは、既存Gateのsilent relaxationになるため禁止する。

結論:

```text
G-21 freeze candidate = prepared
G-21 final Reference Workstation verification = blocked by connector quota
G-21 status = Prepared / BLOCKED before final Freeze
G-22 = blocked
N-04 = Failed / not Complete
N-05 = blocked
```

---

## 2. Created freeze-candidate artifacts

```text
benchmark/n04-ai-use-cases-v3.json
benchmark/n04-v3-formal-harness-v1.json
benchmark/n04-v3-material-profiles-v1.json
benchmark/n04-v3-source-fact-verifier-profile-v1.json
tests/test_n04g21_harness_freeze_candidate.py
```

Status fieldはすべて:

```text
freeze_candidate_pending_reference_workstation_verification
```

とし、Reference Workstation確認前のfalse freezeをmachine-testする。

---

## 3. Frozen-semantics compatibility

G-18の論理contractを変更しない。

```text
sgokb.context-builder.v1
sgokb.grounded-context.v1
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

維持する主要invariant:

- generatorはuntrusted best-effort component。
- model outputに`stylistic_expression`を再導入しない。
- model-authored free-form labelを再導入しない。
- interpretationはvalidated source_fact premiseだけを参照する。
- context-limitはexclusive structured safe path。
- Grounding PASSだけでACCEPTEDにしない。
- Material PASSをACCEPTEDに必須とする。
- attempt 1 + retry 1の最大2 generation attempts。
- partial salvage禁止。
- terminal/output/context/attempt identity binding必須。
- REJECTED/SYSTEM_FAILUREはrender不可。

---

## 4. Formal v3 stable Objects / material profiles

### Case 1 — Roleplay

```text
profile: n04-v3-case-1-roleplay
Saber: 326a97cf-47aa-4760-a7f1-07bfe639fcf0
minimum_supported_source_fact_units: 2
```

### Case 2 — Comparison

```text
profile: n04-v3-case-2-comparison
Fate/stay night: d5824d33-7008-4121-9cfe-1f95a19667fd
expected fixed-dataset rank-1 Work: BLEACH
BLEACH: 57db855c-574a-4b38-b474-421c165894f1
minimum_source_fact_per_object: 1
minimum_interpretation_units: 1
require_cross_source_interpretation: true
```

BLEACH IDをLLM input用にhardcodeしてSimilarity retrievalを迂回してはならない。

Formal executionでは実際の`find_similar_objects` rank-1 current Workを使用し、そのIDが固定N-03 dataset上のexpected IDと異なる場合はcandidate substitutionせずCase FAILとして扱う。

### Case 3 — Creative

```text
profile: n04-v3-case-3-creative
Tsundere: 8c83f986-f491-41a8-8645-9f71dd5874b9
Hero's Journey: fee32007-0f92-449a-ba21-4ec2f78d1cd4
minimum_source_fact_per_object: 1
minimum_creative_addition_units: 1
```

---

## 5. Generator freeze candidate

G-12 Reference Workstationで実稼働済みの最終generatorを継続する。

```text
runtime: LM Studio OpenAI-compatible local server
LM Studio: 0.4.25.0
endpoint: http://127.0.0.1:1234/v1
identifier: sgokb-n04-mistral32
model file: lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-GGUF/
            Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf
quantization: Q4_K_M
context length: 8192
GPU offload: max
parallel: 1
seed: 20261018
stream: false
```

Case parameters:

```text
roleplay:   temperature=0.2 / max_tokens=700
comparison: temperature=0.0 / max_tokens=900
creative:   temperature=0.2 / max_tokens=1100
```

同一generatorを3 Caseとretryに固定する。

---

## 6. Bounded semantic model freeze candidate

Generator-independent local bounded modelとして、G-12で実稼働済みPhi-4を継続する。

```text
runtime: LM Studio OpenAI-compatible local server
identifier: sgokb-n04-phi4
model file: microsoft/phi-4-gguf/phi-4-Q4_K_S.gguf
quantization: Q4_K_S
context length: 8192
GPU offload: max
parallel: 1
temperature: 0.0
max_tokens: 64
seed: 20261018
stream: false
```

v3ではstage-specific bounded adapterとして使用する。

```text
AtomicityRoleValidatorAdapter
SourceFactJudgeAdapter
InterpretationDerivationJudgeAdapter
```

各stageは対象propositionと、そのstageに必要なsupplied support/premise/ruleだけを入力する。

禁止:

- Web
- external retrieval
- uncited SGOKB Knowledge
- generator conversation
- source support外のfranchise/world knowledge

同じPhi-4を複数bounded stageに使うことは許容するが、source-fact specialized verifierとは独立componentであり、generator自身のself-checkではない。

---

## 7. Specialized source-fact verifier candidate

G-20 screening必要Gateを満たしたMiniCheck RoBERTa-largeを採用候補として固定する。

```text
MiniCheck source repository: Liyan06/MiniCheck
source revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model alias: roberta-large
model repository: lytang/MiniCheck-RoBERTa-Large
model repository revision candidate:
  74c8919647e61ed0f71bc177d94f10930f090068
max model length: 512
chunk size: 400
formal threshold: 0.50
operator: >=
formal runtime network policy: offline / local-files-only
```

G-20 GitHub Actions screening at0.50:

```text
required negative/replay false-positive: 0
required positive supported: 2 / 2
negative specificity: 1.0
positive recall: 0.8
```

ただしこのGitHub Actions resultはReference Workstation local proofではない。

MiniCheck source code側がmodel loadに`revision=main`を使うため、formal preflightではlocal Hugging Face cacheの`main` refが上記exact model revisionへ解決することを確認し、networkを使わず再実行可能であることを必須にする。

Reference Workstation上でこのidentityが一致しなければ、silent download / alternate revision substitutionを禁止し、G-21をreopenする。

---

## 8. Source-fact composition policy

```text
V3 deterministic exact/structured support
  ↓ unresolved only
MiniCheck specialized verifier
  ↓ SUPPORTED_CANDIDATE only
Phi-4 independent bounded source-fact judge
  ↓ ENTAILED only
supported
```

Fail-closed:

```text
MiniCheck negative                 -> no PASS
MiniCheck positive + Phi-4 negative -> no PASS
verifier disagreement              -> no PASS
indeterminate                      -> no PASS
required component unavailable     -> SYSTEM_FAILURE
```

MiniCheck scoreはtruth probabilityとして扱わない。

---

## 9. Atomicity / role / interpretation candidates

### Atomicity / role

Phi-4 bounded adapterのallowed verdict:

```text
atomicity:
  ATOMIC
  NON_ATOMIC
  INDETERMINATE

role boundary:
  ROLE_VALID
  ROLE_VIOLATION
  INDETERMINATE
```

`ATOMIC + ROLE_VALID`だけがsupport/derivation stageへ進める。

### Interpretation derivation

Phi-4 bounded derivation judge:

```text
REASONABLE_DERIVATION
UNSUPPORTED_DERIVATION
CONTRADICTORY
INDETERMINATE
```

入力はvalidated `source_fact` premise texts/metadata、atomic conclusion、purposeだけに限定する。

external hidden premiseを許可しない。

---

## 10. Provider structured-output candidate

Provider mechanism:

```text
LM Studio OpenAI-compatible response_format json_schema
strict=true
```

Canonical schema source:

```text
src/sgokb/grounding/output.py::GENERATION_OUTPUT_SCHEMA
```

Schema identity candidate:

```text
sha256: 1fc7674ee9c42ca60feecd1796ec186f970f88e5600f3839d25d851735a1b990
response format name: sgokb_grounded_generation_output_v2
```

Formal preflightで`generation_output_schema_hash()`との一致をmachine-checkする。

provider/application parse surfaceはG-20修正後のshared JSON Schemaを維持し、cross-item identity invariantはGrounding Validation V0で明示判定する。

---

## 11. Retry / terminal / render freeze candidate

```text
max attempts: 2
max retries: 1
retry addition: structured failure/repair feedback only
```

Retry前後で固定:

- Grounded Context
- context_fingerprint
- purpose
- generator/runtime/settings
- output contract/schema
- material requirement profile

Terminal:

```text
ACCEPTED             -> NORMAL
INSUFFICIENT_CONTEXT -> CONTEXT_LIMIT_ONLY
REJECTED             -> NONE
SYSTEM_FAILURE       -> NONE
```

Formal Case PASS terminalは`ACCEPTED`のみ。

`INSUFFICIENT_CONTEXT`は安全なmachine terminalであるが、代表use caseを完遂していないためN-04 formal CaseはFAILとする。

---

## 12. Evidence tree freeze candidate

Root:

```text
.local/n04-v3/runs/<run_id>/
```

Required top-level:

```text
run.json
git-start.json
git-end.json
environment.json
reference-runtime-lock.json
harness.json
acceptance-spec.json
material-profiles.json
verifier-profile.json
schema-identity.json
lm-studio-models.json
minicheck-runtime.json
minicheck-screening.json
mcp-runtime.json
canonical-before.json
canonical-after.json
canonical-compare.json
integrity-before.json
integrity-after.json
regression/focused-replay.log
regression/full-pytest.log
regression/ruff.log
regression/git-diff-check.log
overall-evaluation.json
```

Per Case:

```text
mcp-request.json
mcp-response.json
context-builder.json
grounded-context.json
terminal.json
rubric.json
```

Per Attempt:

```text
request.json
http-request.json
http-response.json
raw-output.txt
parsed-output.json
output-binding.json
validation.json
atomicity-role.json
source-fact-verifier.json
source-fact-judge.json
interpretation-derivation.json
material-result.json
decision.json
```

Failed Attempt 1 evidenceはretry後も削除しない。

---

## 13. Formal v3 rubric freeze candidate

Acceptance spec:

```text
benchmark/n04-ai-use-cases-v3.json
```

Global formal PASS:

```text
3 / 3 Case PASS
unsupported rendered material claims = 0
role escape = 0
canonical before/after equal
integrity before/after PASS
focused/replay regression PASS
repository-wide Ruff PASS
full pytest failed = 0
start/end Git HEAD equal
```

Machine `ACCEPTED`だけではformal PASSにしない。

保存されたContext / K mapping / validation / material / terminal / rendered outputに対してCodex/human evidence reviewを行い、claim-levelでcritical failureがないことを確認する。

rubric / threshold / requirementを実行後に緩めることは禁止する。

---

## 14. Formal preflight Gate

G-22 formal Case 1を開始する前に全てPASS必須。

1. Git working tree clean（ignored `.local`除く）。
2. 全tracked freeze file hash一致。
3. output v2 provider schema hash一致。
4. evaluation DB存在、active WALなし、N-03 six Object identity一致。
5. Harrier/Qdrant/MCP runtime identity一致、integrity PASS。
6. LM Studio version/endpoint一致。
7. Mistral/Phi-4 model file/load profile一致。
8. generator/Phi-4 neutral output-v2 structured-output smoke PASS。
9. MiniCheck source revision一致。
10. MiniCheck model local cache revision一致。
11. MiniCheck offline scoring可能。
12. Reference WorkstationでG-20 verifier corpusを0.50 thresholdで再runし、required negative FP=0 / required positive=2/2。
13. MiniCheck/Torch/Transformers/Hugging Face/NLTK等exact package versionsを`reference-runtime-lock.json`へ保存。
14. MCP stdio initialization PASS。

1件でも不一致ならformal run開始前にBLOCKし、runtime/model/revision/threshold/schemaを代替しない。

---

## 15. Engineering validation for this candidate

New machine check:

```text
tests/test_n04g21_harness_freeze_candidate.py
```

確認対象:

- freeze candidate file identities
- canonical profile hashes
- output schema hash binding
- G-18 contract version set
- stable Object IDs
- material requirements
- generator/Phi-4 identities
- MiniCheck source/model revision candidate
- threshold 0.50
- G-20 false-positive Gate保持
- retry upper bound
- ACCEPTED-only formal Case PASS
- candidate statusがReference Workstation確認前に`frozen`へ変わっていないこと

Repository regressionはPR上でfocused/replay / full pytest / repo-wide Ruff / diff checkを実行する。

---

## 16. Remaining unblock work

Reference Workstation accessが再びcommand execution可能になった時点で、**候補を変更せず**次を実行する。

```text
A. runtime inventory / exact package lock
B. MiniCheck source+model cache exact revision verification
C. network-disabled/offline verifier corpus replay
D. threshold 0.50:
     required negative false-positive = 0
     required positive supported = 2/2
E. neutral structured-output smoke for Mistral/Phi-4 against output v2
F. MCP / Harrier / Qdrant / integrity preflight
```

全PASS時のみ:

1. `reference-runtime-lock.json`相当のfreeze値をharnessへ反映。
2. 4 candidate JSONのstatusを`frozen`へ変更。
3. `unresolved_before_freeze`を0件にする。
4. freeze file hashesを再計算。
5. G-21 regression Gateを再実行。
6. 本書Statusを`Complete / Frozen`へ変更。
7. G-22をunblockする。

候補と異なるmodel/revision/runtimeが必要ならsilent substitutionせずG-21 decisionをreopenする。

---

## 17. Completion assessment

- [x] v3 acceptance spec candidateを作成。
- [x] stable Object IDs / Material profilesを固定。
- [x] generator profile candidateを固定。
- [x] bounded Phi-4 judges candidateを固定。
- [x] MiniCheck source/model revision + threshold candidateを固定。
- [x] source-fact composition policyを固定。
- [x] output-v2 provider schema hash candidateを固定。
- [x] retry/terminal/render policyを固定。
- [x] physical evidence tree candidateを固定。
- [x] formal v3 rubric candidateを固定。
- [x] Reference Workstation preflight Gateをfail-closedに定義。
- [x] freeze candidate machine testsを追加。
- [ ] Reference Workstation MiniCheck exact local runtime verification。
- [ ] Reference Workstation verifier corpus offline replay。
- [ ] exact MiniCheck runtime package lock。
- [ ] final status `frozen`。

**N-04G-21 is not Complete yet. Freeze candidate preparation is complete, but final Reference Workstation verification is blocked by the Desktop Commander monthly usage limit.**

G-22はunblockしない。
