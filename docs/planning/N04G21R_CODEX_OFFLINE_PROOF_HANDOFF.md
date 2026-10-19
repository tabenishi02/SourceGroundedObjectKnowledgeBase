# N-04G-21R Codex Handoff — Selected Verifier Runtime Preparation / Local Proof

更新日: 2026-10-19

- Task: `N-04G-21R [P0]`
- Status before execution: **NEXT / unblocked**
- Selected verifier: **MiniCheck RoBERTa-large**
- Branch: `phase-n/n04g21r-offline-proof`
- Base main at preparation: `92a5d271e030f0da2e912adc460f3b954a803793`
- G-21V authority: `docs/evaluation/N04G21V_VERIFIER_CANDIDATE_EVALUATION.md`
- G-21 freeze candidate: `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`

## Goal

G-21Vで選定したMiniCheckをReference Workstationのformal verifier runtimeとして隔離・固定し、**ネットワークを使用せず**同一G-20 corpusを再生して、G-21 final Freezeに必要なlocal proofを取得する。

G-21Vのdownload-enabled比較結果はこのproofの代用ではない。

## Frozen identities

変更禁止:

```text
MiniCheck source repo: Liyan06/MiniCheck
source revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model repo: lytang/MiniCheck-RoBERTa-Large
model revision: 74c8919647e61ed0f71bc177d94f10930f090068
threshold: >= 0.50
max model length: 512
chunk size: 400
batch size: 16
device: cuda:0
```

Reference Workstation selected runtime from G-21V:

```text
Python 3.10.6
PyTorch 2.6.0+cu124 / CUDA build 12.4
Transformers 5.20.1
huggingface_hub 1.33.0
tokenizers 0.23.3
MiniCheck 0.1.0
NLTK 3.10.3
accelerate 1.4.0
GPU RTX 4090
```

Do not alter versions merely to obtain PASS.

## Isolation

Do not modify the standard SGOKB venv.

Formal runtime root:

```text
.local/n04-v3/runtime/verifier/
  venv/
  source/minicheck/
  hf-cache/
  nltk-data/
  lock/
  runs/<run_id>/
```

The G-21V runtime under `.local/n04-v3/runtime/g21v/` may be used as preparation input, but formal proof must run from the verifier runtime paths above.

Preparation may use network only if an exact required artifact is genuinely missing. Prefer copying/verifying the already downloaded G-21V exact source/model/NLTK assets. Once preparation is complete, switch to the offline proof boundary. No download or dependency change is allowed after that boundary.

## Required preparation evidence

Save under `.local/n04-v3/runtime/verifier/lock/` and the run evidence directory:

- full `pip freeze`
- Python/platform/GPU/CUDA inventory
- MiniCheck source `git rev-parse HEAD` and clean status
- Hugging Face `refs/main` content
- pinned snapshot existence/file inventory
- NLTK `punkt` and `punkt_tab` local resource paths
- standard SGOKB venv before/after package inventory proving it was unchanged

## Offline proof runner

Use:

```text
benchmark/tools/n04g21r_minicheck_offline_proof.py
```

The runner:

- hardcodes the selected source revision, model revision and threshold 0.50;
- requires local HF `refs/main` to resolve exactly to the pinned model revision;
- requires the exact source checkout to be clean;
- enables `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`;
- requires local NLTK `punkt` and `punkt_tab`;
- blocks Python socket connections in-process;
- runs the immutable G-20 corpus;
- compares verdicts/scores with the tracked G-21V MiniCheck result;
- records runtime/package/GPU identity and network-attempt counters.

Formal command shape from repository root:

```powershell
& .local\n04-v3\runtime\verifier\venv\Scripts\python.exe `
  benchmark\tools\n04g21r_minicheck_offline_proof.py `
  --corpus benchmark\n04g20-source-fact-verifier-v1.json `
  --source-dir .local\n04-v3\runtime\verifier\source\minicheck `
  --cache-dir .local\n04-v3\runtime\verifier\hf-cache `
  --nltk-data .local\n04-v3\runtime\verifier\nltk-data `
  --g21v-result benchmark\results\n04g21v-minicheck-roberta-large-reference-workstation.json `
  --output .local\n04-v3\runtime\verifier\runs\<run_id>\minicheck-offline-proof.json
```

## Mandatory offline Gate

PASS requires all of the following:

```text
source revision exact
model refs/main exact
pinned snapshot locally present
NLTK resources locally present
Python socket network attempts = 0
required negative false-positive = 0
required positive supported = 2 / 2
threshold = 0.50 unchanged
standard SGOKB venv unchanged
```

`comparison_with_g21v.all_verdicts_equal` and score deltas must be recorded. A verdict mismatch is not to be manually overridden; investigate it before Freeze. Do not tune threshold against the corpus.

## Remaining G-21 preflight work after MiniCheck offline proof

If MiniCheck offline Gate passes, continue the existing G-21 preflight without changing profiles:

1. Mistral/Phi-4 output-v2 neutral structured-output smoke.
2. MCP/Harrier/Qdrant runtime identity and integrity preflight.
3. MCP stdio initialization.
4. Focused grounding/replay regression.
5. G-21 candidate tests including new G-21R contract test.
6. Full pytest.
7. Repository-wide Ruff.
8. `git diff --check`.

If a required local model/runtime is missing or differs, stop BLOCKED. Do not download/substitute after the offline boundary.

## Required tracked result on PASS

Create:

```text
benchmark/results/n04g21r-minicheck-offline-reference-workstation.json
docs/evaluation/N04G21R_SELECTED_VERIFIER_RUNTIME_LOCAL_PROOF.md
```

The tracked result should be a copy of the formal runner output or a lossless normalized representation with the raw output retained locally.

Update planning/handoff status:

```text
G-21V = Complete / MiniCheck selected
G-21R = Complete / PASS
```

Then complete the existing G-21 final-freeze update only if **all** G-21 preflight and engineering Gates pass. On full success:

```text
benchmark/n04-v3-source-fact-verifier-profile-v1.json
  reference_workstation_reproduction -> true
  status -> frozen

all G-21 candidate JSON status -> frozen
G-21 unresolved_before_freeze -> empty
G-21 -> Complete / Frozen
G-22 -> NEXT / unblocked
N-04 -> Failed / not Complete
N-05 -> blocked
```

Recompute any file/canonical hashes required by the harness and update hash references consistently. Do not hand-edit a hash to preserve an old value after payload changes.

If MiniCheck proof passes but another G-21 preflight fails, G-21R may be recorded Complete/PASS while G-21 remains BLOCKED with the exact remaining blocker.

## Historical evidence

Do not delete or overwrite:

- G-12 failure evidence
- G-20/G-20R evidence
- G-21V candidate comparison evidence
- the first 2026-10-19 G-21 BLOCKED evidence
- any failed G-21R attempt/log

## Final Codex report

Report:

- run_id
- exact source/model revision
- exact package lock
- offline environment/network-attempt counters
- required negative FP / required positives / recall / specificity
- G-21V verdict/score comparison
- generator/Phi-4 smoke
- MCP/Harrier/Qdrant/integrity result
- focused/full pytest/Ruff/diff result
- tracked files changed
- G-21R/G-21/G-22 status
- commit/PR state
