# N-04G-23A-R Judge Candidate Evaluation Protocol

更新日: 2026-10-20

- Task: `N-04G-23A-R [P0] Judge Candidate Evaluation`
- Status: **Complete / valid FAIL / no candidate selected**
- Run: `20261020T180929+0900`; result: `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`. Fixed protocol and Gates below are unchanged.
- Parent: `N-04G-23A` Complete / Phi-4 insufficient under tested formulations
- Preparation base main: `cfbd7af9663f4cbe5c4acfa9a71d34649b385a48`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked; no viable judge selected; new explicit escalation required**

## 1. Goal

G-23AでPhi-4 `split-v1`がSafety / Required-valid Gateを通過できなかったため、**Gold、Atomicity/Role semantics、split prompt、response schema、sampling、scoringを固定したままjudge modelだけを交換**し、v4 V2へ採用可能なbounded local judgeが存在するか判定する。

本Taskはprompt探索ではない。

```text
Frozen Gold + frozen split-v1 + same runtime semantics
                         ↓
                 alternative model only
                         ↓
             frozen fail-closed scoring
```

## 2. Protected authority

変更禁止:

- `benchmark/n04g23a-atomicity-role-gold-v1.json`
  - SHA-256 `347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687`
  - 47 cases / 41 required / 6 optional
- `benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json`
  - SHA-256 `a10b9216d6ead15927c23b015ac3d2863c10dfaa6797f3ede72bef51e58ba89e`
  - Primary profile `split-v1`
- Gold labels / confidence / `required` / `critical_for_safety`
- Atomicity / Role enum semantics
- fail-closed `INDETERMINATE`
- G-22 / G-23A historical evidence
- production code / MiniCheck / unrelated pipeline boundaries

Semantic authority:

- `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`

## 3. Frozen candidate pool

Source of truth:

`benchmark/n04g23ar-judge-candidates-v1.json`

Order:

1. `qwen35-9b-q6k` — Qwen3.5 9B / Q6_K
2. `ministral3-8b-q6k` — Ministral 3 8B Instruct 2512 / Q6_K
3. `gemma4-12b-q6k` — Gemma 4 12B IT / Q6_K
4. `mistral32-24b-q4km` — historical G-22 Mistral Small 3.2 24B / Q4_K_M

候補集合、model family、quantizationはGold結果を見た後に変更しない。

Qwen3.5は、frozen task promptへcandidate固有の意味規則を追加せず、deterministicなbounded/non-reasoning structured-output pathを事前確認できた場合だけ`ready`とする。確認不能なら`runtime_incompatible`とする。

## 4. Common runtime

```text
provider       LM Studio local OpenAI-compatible endpoint
context        8192
GPU offload    max
parallel       1
temperature    0
max_tokens     64
seed           20261018
stream         false
repeats        3
structured     strict json_schema
```

Candidate acquisition/downloadはidentity freeze前のみnetwork利用可。Benchmark inference開始後はlocal only。

## 5. Identity freeze before any Gold request

全候補についてGoldを一度も送信する前に:

1. exact modelを取得/確認する。
2. Goldに含まれないneutral textでstrict JSON smokeを行う。
3. exact local path / file size / SHA-256 / quantization / LM Studio ProductVersion / alias / context / GPU / parallel / reasoning modeを記録する。
4. 各modelをunloadする。
5. `.local/n04-v4/g23ar/<run_id>/candidate-runtime-lock.json`へ全4候補を保存する。
6. `n04g23ar_preflight.py`をPASSさせる。
7. `benchmark_input_head`とtracked input hashを保存する。

Runtime lockの各候補statusは`ready`または`runtime_incompatible`のみ。

この境界以降、全benchmark完了までtracked inputs / candidate pool / quantization / prompt / Gateを変更しない。

## 6. Primary experiment

Runtime-compatibleな全候補へ、G-23Aの**exact `split-v1`**を実行する。

```text
47 cases x 3 repeats x 2 calls = 282 judge calls / candidate
```

Model alias以外のbenchmark意味条件を変更しない。Partial accuracyによるearly stopは禁止。

Primary PASSは次がすべて0件の場合のみ:

```text
critical_atomicity_false_pass_cases
critical_role_false_pass_cases
required_atomicity_false_reject_cases
required_role_false_reject_cases
required_repeatability_failure_cases
```

Required valid caseへの`INDETERMINATE`はfalse reject。

## 7. Secondary experiment

Primary PASS候補だけを対象に、事前固定した:

`benchmark/n04g23ar-split-paraphrase-profile-v1.json#split-paraphrase-a`

を同じ47 cases x 3 repeats x 2 callsで実行する。

Secondary PASSにはPrimaryと同じzero-tolerance Gateに加え、41 required x 3 repeats = 123 pairsで:

```text
Atomicity exact-vs-paraphrase agreement = 123/123
Role exact-vs-paraphrase agreement      = 123/123
Joint exact-vs-paraphrase agreement     = 123/123
```

を必須とする。

## 8. Deterministic selection

`benchmark/tools/n04g23ar_compare_candidates.py`を唯一のselection authorityとする。

- Primary PASSなし -> no selection / valid FAIL
- Primary PASSはあるがSecondary PASSなし -> no selection / valid FAIL
- Secondary PASS 1候補 -> select
- Secondary PASS複数 -> exact-profile elapsed timeが短い候補
- fastestから5%以内に複数 -> model file size / loaded VRAMが小さい候補
- なおtie -> frozen manifest order

Manual override、Gold変更、candidate固有prompt tuningは禁止。

## 9. Evidence / tracked output

Raw evidence:

`.local/n04-v4/g23ar/<run_id>/`

最低限:

```text
run.json
git-start.json
tracked-inputs.json
candidate-runtime-lock.json
preflight.json
smoke/
primary/<candidate-id>/
secondary/<candidate-id>/
comparisons/
engineering/
git-end.json
```

Tracked result:

```text
benchmark/results/n04g23ar-<candidate-id>-primary-reference-workstation.json
benchmark/results/n04g23ar-<candidate-id>-secondary-reference-workstation.json
benchmark/results/n04g23ar-selection-reference-workstation.json
```

Secondary resultは実行候補のみ。Raw HTTP/model filesはcommitしない。

評価文書:

`docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`

## 10. Engineering Gates

Before any Gold request:

```powershell
python benchmark/tools/n04g23ar_preflight.py
python -m pytest -q tests/test_n04g23ar_candidate_eval_contract.py
python -m ruff check benchmark/tools/n04g23ar_preflight.py benchmark/tools/n04g23ar_compare_candidates.py tests/test_n04g23ar_candidate_eval_contract.py
git diff --check
```

After tracked result/doc updates, Windowsではwildcardに依存せず明示列挙する:

```powershell
python benchmark/tools/n04g23ar_preflight.py
python -m pytest -q `
  tests/test_n04g23a_atomicity_role_benchmark_contract.py `
  tests/test_n04g23a_required_repeatability_gate.py `
  tests/test_n04g23ar_candidate_eval_contract.py
python -m pytest -q
python -m ruff check .
git diff --check
```

すべてPASS必須。Candidate failureを理由に既存testを弱めない。

## 11. Completion states

Candidate selected:

```text
N-04G-23A-R = Complete / PASS / <candidate-id> selected
N-04G-23B   = NEXT
N-04         = Failed / not Complete
N-05         = blocked
```

No candidate selected:

```text
N-04G-23A-R = Complete / valid FAIL / no candidate selected
N-04G-23B   = blocked
N-04         = Failed / not Complete
N-05         = blocked
```

Invalid/system-defect runではvalid completionにしない。Partial resultからcandidateを選定しない。
