# N-04G-25A — Development Classifier Selection

更新日: 2026-10-22

- Development execution: **Complete / VALID_FAIL_NO_SELECTION**
- V2-R-A / V2-R-C: **none / none**
- G-25A: **not Complete**; G-25B / G-26: **blocked**
- N-04: **Failed / not Complete**; N-05: **blocked**
- Frozen 47 final confirmation: **NOT STARTED**. No confirmation input, similarity comparison, model request, tuning or retry was performed.

## Provenance and frozen order

- Selection run: `20261022T000426+0900`
- Training run: `20261021T230349+0900`
- Corpus/split freeze commit: `ea46ba172fc071f0c4ce160ac4c99b8c831bbfbe` (before any model execution)
- Training input HEAD: `145b00c9b0ca0df403f354f587ae938b99ab0b5d`
- Selection input HEAD / all-policy freeze commit: `9e269e859f65e35511ad0dae5719f6089f242119`
- Pre-selection policy lock SHA-256: `0b5cba8179e2c58fee7a748aba4ce8c4606a18c2257691d0da6f6d378f394881`
- Candidate manifest SHA-256: `c93f70ab3bbfc905609c12c90dbddd628d6e5172f8ed5532a1b05f7b70af18e7`
- Exact source artifact, task checkpoint, class map and validation-only policy identities are in `benchmark/n04g25a-candidate-manifest-v1.json` and `benchmark/n04g25a-development-policy-lock-v1.json`.
- Selection runner and deterministic selector were committed/pushed before selection. Corpus, split, source/model identity, training configuration, class definitions, thresholds and Gates were not changed after selection.
- Aggregate result and raw-evidence SHA-256 index: `benchmark/results/n04g25a-development-selection-reference-workstation.json`.
- Historical G-23A/G-23A-R results were reference only; no historical joint judge or labels were used for training.

## Corpus and leakage validation

| Task | Total | Non-ambiguous | Ambiguous controls | Families | Train / validation / selection |
|---|---:|---:|---:|---:|---|
| Atomicity | 450 | 400 | 50 | 45 | 270 / 90 / 90 |
| Content Type | 550 | 500 | 50 | 55 | 330 / 110 / 110 |

Atomicity: ATOMIC 200 (20 families), NON_ATOMIC 200 (20), AMBIGUOUS 50 (5). Content Type: SOURCE_FACT_CONTENT, INTERPRETATION_CONTENT, CREATIVE_CONTENT, CONTEXT_LIMIT_CONTENT and MIXED_CONTENT each 100 (10 families); AMBIGUOUS 50 (5). Each class has 60/20/20 percent group-level train/validation/selection allocation.

Validator PASS: required fields, IDs, taxonomy, family/class coverage, minimum counts and role metadata. Family/lineage/cross-task lineage leakage = 0; exact/normalized cross-split duplicate text = 0. Lexical variants/minimal-pair lineages stay within a partition. SHA-256 is recorded below.

| Frozen file | SHA-256 |
|---|---|
| `n04g25a-atomicity-development-v1.jsonl` | `b84ec6b110f5b2939dfb75ec34c5aa91ff42d013255ef088da5a47f6fc6fb9bf` |
| `n04g25a-content-type-development-v1.jsonl` | `c039674b35ac5a2ecba74a75c6369b2a80b94bb314545bdeea9f7f8e8d592e2b` |
| `n04g25a-development-manifest-v1.json` | `06fc960c2c763e10160039baa875bc45b1206d54fa1307c7cb2093ba080cf111` |
| `n04g25a-split-manifest-v1.json` | `4e8ed4f1f8c102d894d19d4090687d6da01b531a5f1bc4cc890f41d7475c0fef` |

Labels are design-derived synthetic semantic-family judgments, not independently human-adjudicated Gold. The 100 constructions use ten neutral-domain variants each. Held-out families and neutral lexical banks reduce leakage; corpus size does not establish real-data quality.

## Candidate and runtime identity

| ID | Exact model repository | Exact revision | License | Runtime |
|---|---|---|---|---|
| C1A | `answerdotai/ModernBERT-base` | `8949b909ec900327062f0ebf497f51aef5e6f0c8` | apache-2.0 | Compatible |
| C1B | `microsoft/deberta-v3-base` | `8ccc9b6f36199bec6961081d44eb72fb3f7353f3` | mit | Compatible |
| C2 | `cross-encoder/nli-deberta-v3-base` | `6c749ce3425cd33b46d187e45b92bbf96ee12ec7` | apache-2.0 | Compatible |
| C3 | `sentence-transformers/all-MiniLM-L6-v2` | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | apache-2.0 | Compatible |

Python 3.10.6; PyTorch 2.6.0+cu124 / CUDA build 12.4; RTX 4090 (24 GiB class). Transformers 4.51.3, sentence-transformers 4.1.0, SetFit 1.1.2, scikit-learn 1.6.1, datasets 3.5.0, accelerate 1.6.0, numpy 1.26.4, huggingface_hub 0.30.2, tokenizers 0.21.4, sentencepiece 0.2.0. The full exact package lock is in the tracked result and pre-selection candidate manifest. Runtime/cache/checkpoints are isolated under `.local/n04-v4/g25a/`; standard SGOKB venv and production dependencies are unchanged.

C1A/C1B: separate task checkpoints, 3 epochs, AdamW lr 2e-5, weight decay 0.01, batch 8, max length 128, float32/eager attention, seed 20261021. Checkpoint selection uses lowest validation cross-entropy (earlier epoch on ties). C2: zero-shot only, every frozen class definition including AMBIGUOUS; entailment ID 1 is resolved from exact config (0 contradiction, 2 neutral), then probabilities normalized across definitions. C3: separate SetFit bodies/standard LogisticRegression heads; 16 train-only examples/class, 10 contrastive iterations, body epoch 1/batch 16, head max_iter 1000/random_state 20261021. Ambiguous controls are not hard-supervised targets.

All validation threshold choices use the predeclared confidence/margin grid and critical-error, valid-rejection, macro-F1 ordering. No selection row was used to choose checkpoint/policy. Models receive text only (C2 additionally receives all fixed definitions); compatibility/role/required/critical metadata stays in application-side evaluation.

## Development selection results

Each frozen candidate/task ran its complete held-out set three times: Atomicity 90 rows and Content Type 110 rows, 2,400 predictions total. Counts below are worst per-repeat errors, not sums across repeats. Every required/critical label was identical across all three repeats (0 repeatability failures).

| Candidate | Task | Gate | Critical FP | Required valid FR | Macro F1 | Non-ambiguous abstention | Confidence / margin | Median ms/row | Peak allocated MiB |
|---|---|---|---:|---:|---:|---:|---|---:|---:|
| C1A | atomicity | FAIL | 14 | 0 | 0.519037 | 0.00% | 0.0 / 0.0 | 1.991 | 626.41 |
| C1A | content_type | FAIL | 3 | 10 | 0.718451 | 1.00% | 0.0 / 0.05 | 1.811 | 627.13 |
| C1B | atomicity | FAIL | 8 | 26 | 0.385832 | 28.75% | 0.95 / 0.0 | 1.543 | 771.76 |
| C1B | content_type | FAIL | 0 | 3 | 0.778550 | 1.00% | 0.6 / 0.0 | 1.655 | 774.15 |
| C2 | atomicity | FAIL | 0 | 40 | 0.210114 | 30.00% | 0.5 / 0.0 | 2.423 | 877.99 |
| C2 | content_type | FAIL | 0 | 80 | 0.028986 | 95.00% | 0.0 / 0.05 | 4.081 | 1028.71 |
| C3 | atomicity | FAIL | 1 | 40 | 0.188595 | 75.00% | 0.0 / 0.2 | 0.647 | 121.35 |
| C3 | content_type | FAIL | 0 | 36 | 0.449206 | 55.00% | 0.0 / 0.2 | 0.622 | 122.77 |

Latency is GPU-synchronized batch time divided by row count, median over all repeats, batch 8, excluding model load and one independent neutral warmup. Peak VRAM is torch allocated memory including the resident classifier after warmup, not whole-device utilization. Full elapsed times, artifact sizes, family confusion and per-repeat metrics are in the JSON.

| Candidate | Task | Per-class recall (frozen output order) |
|---|---|---|
| C1A | atomicity | ATOMIC=1.000, NON_ATOMIC=0.650, AMBIGUOUS=0.000 |
| C1A | content_type | SOURCE_FACT_CONTENT=1.000, INTERPRETATION_CONTENT=0.650, CREATIVE_CONTENT=1.000, CONTEXT_LIMIT_CONTENT=0.850, MIXED_CONTENT=1.000, AMBIGUOUS=0.000 |
| C1B | atomicity | ATOMIC=0.350, NON_ATOMIC=0.750, AMBIGUOUS=0.000 |
| C1B | content_type | SOURCE_FACT_CONTENT=1.000, INTERPRETATION_CONTENT=1.000, CREATIVE_CONTENT=1.000, CONTEXT_LIMIT_CONTENT=0.850, MIXED_CONTENT=1.000, AMBIGUOUS=0.000 |
| C2 | atomicity | ATOMIC=0.000, NON_ATOMIC=0.675, AMBIGUOUS=0.200 |
| C2 | content_type | SOURCE_FACT_CONTENT=0.000, INTERPRETATION_CONTENT=0.000, CREATIVE_CONTENT=0.000, CONTEXT_LIMIT_CONTENT=0.000, MIXED_CONTENT=0.000, AMBIGUOUS=1.000 |
| C3 | atomicity | ATOMIC=0.000, NON_ATOMIC=0.275, AMBIGUOUS=0.800 |
| C3 | content_type | SOURCE_FACT_CONTENT=0.200, INTERPRETATION_CONTENT=1.000, CREATIVE_CONTENT=1.000, CONTEXT_LIMIT_CONTENT=0.000, MIXED_CONTENT=0.050, AMBIGUOUS=1.000 |

Atomicity Gate: critical NON_ATOMIC→ATOMIC = 0; required ATOMIC→NON_ATOMIC/AMBIGUOUS = 0. Content Type Gate: critical incompatible-role false-compatible = 0; required valid-compatible false-reject = 0. MIXED/AMBIGUOUS remain fail-closed. All three repeats must satisfy the Gates. Macro F1/recall include the AMBIGUOUS output class and controls. No candidate passed either task, so ranking tie-breaks cannot select a winner.

## Engineering and evidence review

```text
python -m pytest -q tests/test_n04g25a_development.py tests/test_n04g25a_training_policy.py tests/test_n04g25a_selection.py
  34 passed, 0 failed
python -m pytest -q
  482 passed, 0 failed, 0 skipped, 2 existing local-Qdrant warnings (166.28 s)
python -m ruff check .
  PASS
git diff --check
  PASS
```

Training and selection each recorded exact same-process standard-venv before/after PASS. At completion review (PYTHONNOUSERSITE=1), interpreter and non-editable package versions still match; editable Git provenance differs for the advanced project HEAD and an unrelated inherited editable distribution. This task made no standard-venv install/update or external-repository change.

All checkpoint/policy, corpus/split and training/metric source hashes were reverified after execution. Raw probabilities were independently replayed through the frozen policy and scoring code; all 8 summaries and deterministic selector outcome match. Standard venv before/after identities match. No model inference was rerun during this review.

A preparation attempt (`20261021T230232+0900`) failed before model input because CUDA peak-memory measurement preceded CUDA initialization. Its logs remain intact. The initialization-only repair was committed before the successful training run. The synthetic policy test originally asserted a floating-point threshold boundary; it now asserts the actual required labels. The selection path check was corrected before selection to recognize the already-authorized isolated runtime junction. No Gate or statistical setting changed.

Raw evidence: `.local/n04-v4/g25a/selection/20261022T000426+0900/` and `.local/n04-v4/g25a/completion/20261022T000426+0900/`; training/preparation evidence remains in its original directories. Checkpoints, logs, caches and model files are ignored, never committed.

## Completion decision and escalation

**VALID_FAIL_NO_SELECTION** is a valid semantic benchmark outcome with engineering PASS. V2-R-A = none; V2-R-C = none. No selected-checkpoint/policy freeze (`benchmark/n04g25a-selection-freeze-v1.json`) is created because no candidate is eligible. The pre-selection all-candidate policy lock is preserved as evidence, not deployment approval.

The development execution/reporting task is finished. G-25A is not Complete; G-25B/G-26 remain blocked. N-04 remains Failed/not Complete and N-05 blocked. Frozen 47 final confirmation is NOT STARTED and must not begin with these failed candidates.

Escalation: a separate explicitly approved remediation/evaluation protocol is needed before another selection attempt, with untouched held-out evidence. Do not retune from these selection failures and claim them as independent acceptance. This result does not reopen G-23F, weaken any safety Gate, change Frozen 47, or authorize production adapter integration.
