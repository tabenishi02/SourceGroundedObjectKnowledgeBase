# N-04G-23A-R Codex Judge Candidate Evaluation Handoff

更新日: 2026-10-20

- Branch: `phase-n/n04g23ar-judge-candidate-evaluation`
- Base main: `cfbd7af9663f4cbe5c4acfa9a71d34649b385a48`
- Task: `N-04G-23A-R [P0] Judge Candidate Evaluation`
- State: **Complete / valid FAIL / no candidate selected**
- Run: `20261020T180929+0900`; result: `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`. Original execution procedure below is retained.
- Reference Workstation: Windows 11 / RTX 4090
- Production code change: **禁止**
- G-23A frozen Gold/profile change: **禁止**
- main merge: **禁止**

## 1. Read first

1. `docs/planning/phases/N/N04/post-g12/N04G23AR_JUDGE_CANDIDATE_EVALUATION_PROTOCOL.md`
2. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
3. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
4. `benchmark/n04g23ar-judge-candidates-v1.json`
5. `benchmark/n04g23ar-split-paraphrase-profile-v1.json`
6. `benchmark/n04g23a-atomicity-role-gold-v1.json`
7. `benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json`
8. `benchmark/tools/n04g23ar_preflight.py`
9. `benchmark/tools/n04g23ar_compare_candidates.py`

## 2. Sync / preflight

Branchをfetchし、fast-forward onlyで切り替える。Tracked treeはcleanから開始する。`.local/` ignored evidenceは可。

Gold request前に:

```powershell
python benchmark/tools/n04g23ar_preflight.py `
  --output .local/n04-v4/g23ar/preparation-preflight.json
python -m pytest -q tests/test_n04g23ar_candidate_eval_contract.py
python -m ruff check benchmark/tools/n04g23ar_preflight.py benchmark/tools/n04g23ar_compare_candidates.py tests/test_n04g23ar_candidate_eval_contract.py
git diff --check
```

全PASS必須。

Pure engineering defectをGold request前に発見した場合のみ、Gold / candidate pool / prompts / scoring / selection Gatesを変更せず修正可能。修正後はcommit/pushし、その最新HEADを`benchmark_input_head`とする。

## 3. Frozen candidate pool

Manifestどおり4候補を取得/確認する。代替禁止。

```text
qwen35-9b-q6k
  lmstudio-community/Qwen3.5-9B-GGUF
  Qwen3.5-9B-Q6_K.gguf
  alias sgokb-g23ar-qwen35-9b

ministral3-8b-q6k
  lmstudio-community/Ministral-3-8B-Instruct-2512-GGUF
  Ministral-3-8B-Instruct-2512-Q6_K.gguf
  alias sgokb-g23ar-ministral3-8b

gemma4-12b-q6k
  lmstudio-community/gemma-4-12B-it-GGUF
  gemma-4-12B-it-Q6_K.gguf
  alias sgokb-g23ar-gemma4-12b

mistral32-24b-q4km
  existing G-22 frozen Mistral Small 3.2 24B Q4_K_M
  alias sgokb-n04-mistral32
```

Exact fileが取得/ロードできない候補は`runtime_incompatible`。別quantization/modelで置換しない。

## 4. Neutral smoke and runtime lock

Goldに含まれないneutral textで、各候補を1つずつloadし:

```text
context 8192
GPU offload max
parallel 1
strict json_schema
```

を確認する。Atomicity-only / Role-only response schemaがparse可能であることも確認する。

Qwen3.5は、frozen task semanticsをpromptへ追加せずbounded/non-reasoning structured-outputを確立できなければ`runtime_incompatible`。

Gold request前に全4候補を一つの:

`.local/n04-v4/g23ar/<run_id>/candidate-runtime-lock.json`

へ固定する。各ready候補に最低限:

```text
candidate_id
status=ready
lm_studio_alias
model_path
model_file_size_bytes
model_sha256
quantization
lm_studio_product_version
context_length=8192
gpu_offload=max
parallel=1
reasoning_mode
```

を保存する。Incompatible候補にもcandidate_id/status/reasonを保存する。

さらに`git-start.json`、tracked input hashes、preflight outputを保存する。この境界以降、全benchmark完了までtracked inputs / candidate identity / quantization / prompts / Gatesを変更しない。

## 5. Primary — exact G-23A split-v1

`ready`候補すべてに対し:

```powershell
python benchmark/tools/n04g23a_atomicity_role_benchmark.py `
  --corpus benchmark/n04g23a-atomicity-role-gold-v1.json `
  --profiles benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json `
  --profile-id split-v1 `
  --model <candidate-alias> `
  --repeats 3 `
  --output .local/n04-v4/g23ar/<run_id>/primary/<candidate-id>/result.json
```

47 x 3 x 2 callsを完走する。Accuracyが悪くてもearly stopしない。Candidateごとに完了後unloadする。

Primary PASSは次の5 listがすべてemptyの場合だけ:

```text
critical_atomicity_false_pass_cases
critical_role_false_pass_cases
required_atomicity_false_reject_cases
required_role_false_reject_cases
required_repeatability_failure_cases
```

## 6. Secondary — Primary PASS only

Primary PASS候補だけに:

```powershell
python benchmark/tools/n04g23a_atomicity_role_benchmark.py `
  --corpus benchmark/n04g23a-atomicity-role-gold-v1.json `
  --profiles benchmark/n04g23ar-split-paraphrase-profile-v1.json `
  --profile-id split-paraphrase-a `
  --model <candidate-alias> `
  --repeats 3 `
  --output .local/n04-v4/g23ar/<run_id>/secondary/<candidate-id>/result.json
```

を実行する。Primary FAIL候補にSecondaryを実行しない。

## 7. Deterministic selector

全required result作成後:

```powershell
python benchmark/tools/n04g23ar_compare_candidates.py `
  --runtime-lock .local/n04-v4/g23ar/<run_id>/candidate-runtime-lock.json `
  --primary <ready-id>=<primary-result-path> `
  --primary <ready-id>=<primary-result-path> `
  --secondary <primary-pass-id>=<secondary-result-path> `
  --output .local/n04-v4/g23ar/<run_id>/selection.json
```

- `--primary`: ready候補すべて、runtime_incompatibleは省略
- `--secondary`: Primary PASS候補だけ

Selectorは47 cases / 41 required / 3 repeats / alias / zero-tolerance Gates / 123-of-123 stability / frozen tie-breakを強制する。`selected_candidate_id`を手動overrideしない。

## 8. Post-run tracked outputs

Raw run完了・全model unload・`selection.json`確定後のみtracked result/docを作成する。

```text
benchmark/results/n04g23ar-<candidate-id>-primary-reference-workstation.json
benchmark/results/n04g23ar-<candidate-id>-secondary-reference-workstation.json
benchmark/results/n04g23ar-selection-reference-workstation.json
docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md
```

Secondary resultは実行候補のみ。Raw HTTP/log/model filesは`.local`に保持しcommitしない。

Planning更新:

- `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md`
- `docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_CHAT_HANDOFF.md`

Selectorが`PASS_SELECTED`なら:

```text
N-04G-23A-R = Complete / PASS / selected candidate
N-04G-23B   = NEXT
N-04         = Failed / not Complete
N-05         = blocked
```

`VALID_FAIL_NO_SELECTION`なら:

```text
N-04G-23A-R = Complete / valid FAIL / no candidate selected
N-04G-23B   = blocked
N-04         = Failed / not Complete
N-05         = blocked
```

後者では同一run内で別modelを追加せず、新しいexplicit escalation taskが必要と記録する。

## 9. Final engineering Gate

Windowsではpytest wildcardに依存しない。明示列挙する:

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

全PASS必須。終了後`git-end.json`を保存する。

## 10. Git / PR #55

Valid completion後:

- tracked result/doc/statusをcommit
- branchをpush
- PR #55本文をrun summaryで更新
- PR #55をReady for reviewへ変更
- **mainへmergeしない**

最終報告:

```text
run_id
benchmark_input_head
preflight
candidate identities + SHA-256 + size + quantization
runtime-incompatible candidates/reasons
Primary metrics / PASS IDs
Secondary metrics
required exact-vs-paraphrase atomicity/role/joint agreement
selector outcome
selected_candidate_id or none
G-23A-R state
G-23B state
N-04 / N-05 state
G-23A-R tests
full pytest
Ruff
git diff --check
final commit SHA
PR status
raw evidence root
```
