# N-04G-23A-R Codex Judge Candidate Evaluation Handoff

更新日: 2026-10-20

- Branch: `phase-n/n04g23ar-judge-candidate-evaluation`
- Base main: `cfbd7af9663f4cbe5c4acfa9a71d34649b385a48`
- Task: `N-04G-23A-R [P0] Judge Candidate Evaluation`
- State: **Reference Workstation execution pending**
- Reference Workstation: Windows 11 / RTX 4090
- Production code changes: **禁止**
- G-23A frozen Gold/profile changes: **禁止**
- main merge: **禁止**; finish by commit/push and PR Ready for review

## Read first

1. `docs/planning/phases/N/N04/post-g12/N04G23AR_JUDGE_CANDIDATE_EVALUATION_PROTOCOL.md`
2. `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
3. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
4. `benchmark/n04g23ar-judge-candidates-v1.json`
5. `benchmark/n04g23ar-split-paraphrase-profile-v1.json`
6. `benchmark/n04g23a-atomicity-role-gold-v1.json`
7. `benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json`
8. `benchmark/tools/n04g23ar_preflight.py`
9. `benchmark/tools/n04g23ar_compare_candidates.py`

## 1. Sync and engineering preflight

Fetch the branch, switch to it, fast-forward only, and begin from a clean tracked tree.
Ignored `.local/` evidence is allowed.

Run:

```powershell
python benchmark/tools/n04g23ar_preflight.py `
  --output .local/n04-v4/g23ar/preparation-preflight.json

python -m pytest -q tests/test_n04g23ar_candidate_eval_contract.py
python -m ruff check benchmark/tools/n04g23ar_preflight.py benchmark/tools/n04g23ar_compare_candidates.py tests/test_n04g23ar_candidate_eval_contract.py
git diff --check
```

All must PASS before model acquisition/scoring continues.

If a pure tracked engineering defect is found before any Gold request, fix it on the branch, rerun these Gates, commit/push, and use the new HEAD as `benchmark_input_head`. Do not change Gold, candidate pool, prompts, scoring or selection Gates.

## 2. Acquire / locate the complete frozen candidate pool

Use the exact candidate manifest. Do not substitute models because one is inconvenient.

Required pool:

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

Model download/acquisition may use the network **only before benchmark identity freeze**.

Do not change Q6_K to Q4/Q8 or choose another repository after seeing any Gold result.

If an exact named file is unavailable or cannot be loaded, record that candidate as `runtime_incompatible`; do not replace it.

## 3. Neutral runtime compatibility smoke

Before any Gold request, load candidates one at a time using:

```text
context 8192
GPU offload max
parallel 1
```

Use neutral smoke text not present in the 47-case Gold set. Confirm:

- local OpenAI-compatible chat request succeeds
- strict json_schema succeeds for Atomicity-only and Role-only shapes
- response can be parsed into the frozen enums
- no Web/tool/retrieval path is active

For Qwen3.5, also establish a bounded non-reasoning mode without altering frozen task semantics. If this cannot be demonstrated, classify it `runtime_incompatible` before Gold execution.

After each smoke, unload the candidate.

Smoke accuracy is not scored and must not influence candidate selection.

## 4. Freeze all candidate runtime identities before scoring

Create one file:

```text
.local/n04-v4/g23ar/<run_id>/candidate-runtime-lock.json
```

Required shape:

```json
{
  "candidates": [
    {
      "candidate_id": "qwen35-9b-q6k",
      "status": "ready",
      "lm_studio_alias": "sgokb-g23ar-qwen35-9b",
      "model_path": "...",
      "model_file_size_bytes": 0,
      "model_sha256": "...",
      "quantization": "Q6_K",
      "lm_studio_product_version": "...",
      "context_length": 8192,
      "gpu_offload": "max",
      "parallel": 1,
      "reasoning_mode": "disabled"
    }
  ]
}
```

For runtime-incompatible candidates, retain the candidate entry with:

```json
{
  "candidate_id": "...",
  "status": "runtime_incompatible",
  "reason": "..."
}
```

The file must cover **all four** candidates.

Also save:

- `git-start.json`
- exact branch HEAD as `benchmark_input_head`
- tracked input SHA-256s
- LM Studio ProductVersion
- preflight output

After this point:

- no tracked input changes until every benchmark result is complete
- no candidate pool/model/quantization changes
- no prompt tuning

## 5. Primary run — frozen G-23A split-v1

For every candidate with runtime status `ready`, load only that candidate with its frozen alias and settings.

Run:

```powershell
python benchmark/tools/n04g23a_atomicity_role_benchmark.py `
  --corpus benchmark/n04g23a-atomicity-role-gold-v1.json `
  --profiles benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json `
  --profile-id split-v1 `
  --model <candidate alias> `
  --repeats 3 `
  --output .local/n04-v4/g23ar/<run_id>/primary/<candidate-id>/result.json
```

Important:

- `--model` is the only model-specific benchmark argument.
- Do not edit `split-v1`.
- Do not change temperature/max_tokens/seed.
- Do not early-stop on bad accuracy.
- Preserve all raw requests/responses in local evidence if the runner/orchestration helper already captures them.
- Unload each model after its complete primary run.

The existing G-23A runner's profile metadata may still mention historical Phi-4 inside the copied `runtime` object. The actual request model is the top-level `model`/API model alias. Do not rewrite the frozen profile to clean up this historical metadata; bind actual candidate identity through `candidate-runtime-lock.json` and tracked result projection.

## 6. Primary Gate

For each candidate, inspect `metrics`.

Primary PASS only if all lists are empty:

```text
critical_atomicity_false_pass_cases
critical_role_false_pass_cases
required_atomicity_false_reject_cases
required_role_false_reject_cases
required_repeatability_failure_cases
```

Do not use lower error count as a PASS. This is a zero-tolerance Safety/Required-valid Gate.

## 7. Secondary run — primary PASS candidates only

For each Primary PASS candidate, run the pre-registered paraphrase:

```powershell
python benchmark/tools/n04g23a_atomicity_role_benchmark.py `
  --corpus benchmark/n04g23a-atomicity-role-gold-v1.json `
  --profiles benchmark/n04g23ar-split-paraphrase-profile-v1.json `
  --profile-id split-paraphrase-a `
  --model <candidate alias> `
  --repeats 3 `
  --output .local/n04-v4/g23ar/<run_id>/secondary/<candidate-id>/result.json
```

Primary FAIL candidates must not receive a secondary run.

## 8. Deterministic selection

Run the tracked selector after all required primary/secondary results exist.

Example with all candidates runtime-compatible and two finalists:

```powershell
python benchmark/tools/n04g23ar_compare_candidates.py `
  --runtime-lock .local/n04-v4/g23ar/<run_id>/candidate-runtime-lock.json `
  --primary qwen35-9b-q6k=.local/n04-v4/g23ar/<run_id>/primary/qwen35-9b-q6k/result.json `
  --primary ministral3-8b-q6k=.local/n04-v4/g23ar/<run_id>/primary/ministral3-8b-q6k/result.json `
  --primary gemma4-12b-q6k=.local/n04-v4/g23ar/<run_id>/primary/gemma4-12b-q6k/result.json `
  --primary mistral32-24b-q4km=.local/n04-v4/g23ar/<run_id>/primary/mistral32-24b-q4km/result.json `
  --secondary <primary-pass-id>=<secondary-result-path> `
  --secondary <primary-pass-id>=<secondary-result-path> `
  --output .local/n04-v4/g23ar/<run_id>/selection.json
```

Omit `--primary` for candidates marked `runtime_incompatible` in the runtime lock.
Add `--secondary` exactly for Primary PASS candidates.

The selector enforces:

- complete frozen candidate coverage through runtime lock
- 47 cases / 41 required / 3 repeats
- candidate alias binding
- zero-tolerance Primary Gate
- zero-tolerance Secondary Gate
- 123/123 required repeat-pair exact-vs-paraphrase stability for Atomicity, Role and Joint
- frozen latency/size/order tie-break

Do not manually override `selected_candidate_id`.

## 9. Post-run tracked projection

Only after `selection.json` exists and all models are unloaded:

Create tracked result projections:

```text
benchmark/results/n04g23ar-<candidate-id>-primary-reference-workstation.json
benchmark/results/n04g23ar-<candidate-id>-secondary-reference-workstation.json  # only if run
benchmark/results/n04g23ar-selection-reference-workstation.json
```

Copy verdicts/metrics/timings and candidate identity binding. Raw HTTP bodies stay under `.local`.

Create:

```text
docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md
```

Update:

```text
docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md
docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_CHAT_HANDOFF.md
```

### If selector outcome = PASS_SELECTED

```text
N-04G-23A-R = Complete / PASS / selected candidate
N-04G-23B   = NEXT
N-04         = Failed / not Complete
N-05         = blocked
```

### If selector outcome = VALID_FAIL_NO_SELECTION

```text
N-04G-23A-R = Complete / valid FAIL / no candidate selected
N-04G-23B   = blocked
N-04         = Failed / not Complete
N-05         = blocked
```

Record that a new explicit escalation decision is required. Do not invent/execute a replacement model in this same run.

## 10. Final engineering Gate

Run:

```powershell
python benchmark/tools/n04g23ar_preflight.py
python -m pytest -q tests/test_n04g23a*.py tests/test_n04g23ar_candidate_eval_contract.py
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS.

Then record `git-end.json`. Tracked benchmark result/doc commits happen after raw execution evidence is complete.

## 11. Git / PR

After valid completion:

- commit tracked result/doc/status changes
- push branch
- update this PR body with run summary
- mark PR Ready for review
- **do not merge main**

Final response must include:

```text
run_id
benchmark_input_head
preflight PASS/FAIL
candidate runtime identities + SHA-256 + size + quantization
runtime-incompatible candidates/reasons
Primary metrics for each ready candidate
Primary PASS candidate IDs
Secondary metrics for each finalist
required exact-vs-paraphrase atomicity / role / joint agreement
selector outcome
selected_candidate_id or none
selected exact elapsed / model size if selected
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
