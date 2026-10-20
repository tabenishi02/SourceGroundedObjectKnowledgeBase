# N-04G-23A-R Judge Candidate Evaluation Protocol

更新日: 2026-10-20

- Task: `N-04G-23A-R [P0] Judge Candidate Evaluation`
- Status: **Prepared / Reference Workstation execution pending**
- Parent result: `N-04G-23A` Complete / Phi-4 insufficient under tested formulations
- Branch preparation base: `cfbd7af9663f4cbe5c4acfa9a71d34649b385a48`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked pending this task**

## 1. Goal

G-23AでPhi-4 `split-v1`がSafety / Required-valid Gateを通過できなかったため、**Gold、role/atomicity semantics、split prompt、response schema、sampling、scoringを固定したままjudge modelだけを交換**し、v4 V2へ採用可能なbounded local judgeが存在するか判定する。

本Taskはprompt探索ではない。

```text
Frozen Gold + Frozen split-v1 + same runtime semantics
                         ↓
                 alternative model only
                         ↓
             frozen fail-closed scoring
```

## 2. Authorities / protected inputs

Primary authority:

- `benchmark/n04g23a-atomicity-role-gold-v1.json`
  - SHA-256 `347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687`
  - 47 cases / 41 required / 6 optional
- `benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json`
  - SHA-256 `a10b9216d6ead15927c23b015ac3d2863c10dfaa6797f3ede72bef51e58ba89e`
  - Primary profile `split-v1`
- `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`

Do not change:

- Gold text / label / confidence
- `required` / `critical_for_safety`
- Atomicity / Role enum semantics
- `split-v1` prompt or schema
- fail-closed treatment of `INDETERMINATE`
- G-22 / G-23A historical evidence
- MiniCheck or other unrelated pipeline boundaries
- production code

## 3. Frozen candidate pool

Source of truth:

`benchmark/n04g23ar-judge-candidates-v1.json`

Candidates, in frozen order:

1. `qwen35-9b-q6k`
   - Qwen3.5 9B
   - LM Studio Community GGUF
   - Q6_K
2. `ministral3-8b-q6k`
   - Ministral 3 8B Instruct 2512
   - LM Studio Community GGUF
   - Q6_K
3. `gemma4-12b-q6k`
   - Gemma 4 12B IT
   - LM Studio Community GGUF
   - Q6_K
4. `mistral32-24b-q4km`
   - historical G-22 Mistral Small 3.2 24B generator model
   - existing Q4_K_M runtime identity
   - capacity-ceiling/reference candidate

The pool deliberately spans multiple model families and a practical 8B-24B local range. It is not modified after any Gold result is observed.

## 4. Runtime fairness

Common runtime semantics:

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
network        no external inference / retrieval during benchmark
```

Quantization is predeclared per candidate in the manifest. Do not substitute a different quantization after observing a result.

### Qwen3.5 bounded-mode rule

Qwen3.5 may expose reasoning behavior depending on runtime/template. It is eligible only if the Reference Workstation can establish a deterministic non-reasoning/bounded structured-output path **without adding candidate-specific task semantics to the frozen prompt**.

If that cannot be demonstrated before Gold execution, record:

`runtime_incompatible`

and do not silently replace it with another Qwen file or prompt.

## 5. Candidate identity freeze boundary

Before the first Gold request to any candidate:

1. Acquire/locate every candidate model.
2. Load each candidate once only for runtime compatibility checks on neutral non-Gold text.
3. Record for every candidate:
   - exact local path
   - file size
   - SHA-256
   - quantization
   - LM Studio ProductVersion
   - loaded identifier / alias
   - context length
   - GPU offload
   - parallel
   - reasoning mode/template condition if applicable
4. Unload the candidate.
5. Save a single candidate runtime lock under `.local/n04-v4/g23ar/<run_id>/candidate-runtime-lock.json`.
6. Run `n04g23ar_preflight.py` and save its output.
7. Record Git HEAD and tracked-input hashes.

Only after all of the above is complete may any Gold case be sent to a candidate.

Candidate acquisition/download may use the network before this boundary. Model inference after the boundary is local only.

A compatibility smoke must use text not present in the 47-case Gold set and must not be used for candidate scoring.

## 6. Primary experiment — exact frozen split-v1

Every runtime-compatible candidate executes the same complete corpus:

```text
47 cases
x 3 repeats
x 2 calls (Atomicity + Role)
= 282 judge calls / candidate
```

Use the existing frozen G-23A runner and the exact `split-v1` profile. Only the `model` alias changes.

No early stopping based on partial accuracy. A candidate that starts primary scoring must finish all 47 x 3 repeats unless runtime/system failure makes the run invalid; preserve partial evidence in that case.

### Primary Gate

Candidate primary PASS requires all:

```text
critical_atomicity_false_pass_cases == 0
critical_role_false_pass_cases == 0
required_atomicity_false_reject_cases == 0
required_role_false_reject_cases == 0
required_repeatability_failure_cases == 0
```

`INDETERMINATE` on a required valid case is a false reject.

Optional/ambiguous Gold remains diagnostic and cannot be used to relax a required Gate.

## 7. Secondary experiment — pre-registered split paraphrase

Only candidates that satisfy every Primary Gate condition advance.

Profile:

`benchmark/n04g23ar-split-paraphrase-profile-v1.json#split-paraphrase-a`

The paraphrase wording is committed before any candidate scoring and cannot be tuned per model.

Run the same 47 cases x 3 repeats x 2 split calls.

Secondary PASS requires:

1. the same Safety / Required-valid / Required-repeatability Gates as Primary, and
2. on all 41 required cases x 3 repeats:
   - Atomicity exact-vs-paraphrase agreement = 100%
   - Role exact-vs-paraphrase agreement = 100%
   - Joint exact-vs-paraphrase agreement = 100%

A candidate that passes the exact prompt but fails this stability test is not selected.

## 8. Selection rule

The rule is fixed in `benchmark/n04g23ar-judge-candidates-v1.json`.

- No Primary PASS -> no judge selected; valid FAIL.
- Primary PASS but no Secondary PASS -> no judge selected; prompt sensitivity remains a blocker.
- Exactly one Secondary PASS -> select it.
- Multiple Secondary PASS -> choose:
  1. lower exact-profile total split-call elapsed time;
  2. if within 5%, lower model-file size / loaded VRAM;
  3. if still tied, earlier frozen manifest order.

Do not use post-hoc prompt tuning or Gold changes as tie-breakers.

## 9. Evidence layout

Raw evidence is local-only:

```text
.local/n04-v4/g23ar/<run_id>/
  run.json
  git-start.json
  tracked-inputs.json
  candidate-runtime-lock.json
  preflight.json
  smoke/
  primary/
    <candidate-id>/
      result.json
      raw/
  secondary/
    <candidate-id>/
      result.json
      raw/
  comparisons/
  engineering/
  git-end.json
```

At minimum retain request payload, response payload/content, parsed verdict, timing and usage per call. No model files or raw HTTP evidence are committed.

## 10. Tracked result projection

After benchmark execution is fully complete, create tracked result JSONs under:

```text
benchmark/results/n04g23ar-<candidate-id>-primary-reference-workstation.json
benchmark/results/n04g23ar-<candidate-id>-secondary-reference-workstation.json   # finalists only
benchmark/results/n04g23ar-selection-reference-workstation.json
```

Each projection must bind:

- run_id
- benchmark input HEAD
- Gold/profile hashes
- candidate manifest/paraphrase hashes
- candidate local model SHA-256 / size / quantization
- exact LM Studio identity/load settings
- scoring metrics
- repeatability
- elapsed time / usage
- primary/secondary verdict

Do not commit raw prompt/response bodies if the existing benchmark result projection convention excludes them.

## 11. Evaluation document

Create after execution:

`docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`

Include:

- run validity
- frozen input hashes
- candidate runtime identities
- compatibility failures
- Primary metrics for every candidate
- Secondary metrics for every finalist
- exact-vs-paraphrase required stability
- latency/model-size comparison
- deterministic selection result
- G-23B implication
- N-04/N-05 unchanged state

## 12. Engineering Gate

Before the model run:

```text
python benchmark/tools/n04g23ar_preflight.py
python -m pytest -q tests/test_n04g23ar_candidate_eval_contract.py
python -m ruff check benchmark/tools/n04g23ar_preflight.py tests/test_n04g23ar_candidate_eval_contract.py

git diff --check
```

After tracked result/doc updates:

```text
python benchmark/tools/n04g23ar_preflight.py
python -m pytest -q tests/test_n04g23a*.py tests/test_n04g23ar_candidate_eval_contract.py
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS. Existing tests may not be weakened because a candidate fails.

## 13. Valid completion states

### Candidate selected

```text
N-04G-23A-R = Complete / PASS / <candidate-id> selected
N-04G-23B   = NEXT
N-04         = Failed / not Complete
N-05         = blocked
```

### No candidate satisfies frozen Gates

```text
N-04G-23A-R = Complete / valid FAIL / no candidate selected
N-04G-23B   = blocked
N-04         = Failed / not Complete
N-05         = blocked
```

A valid FAIL must lead to a new explicit escalation decision; do not relax the frozen Gold/Gates inside this Task.

### Invalid run / system defect

Preserve evidence, do not mark a valid benchmark completion, and repair/re-run only after documenting the defect. No candidate may be selected from a partial/invalid run.
