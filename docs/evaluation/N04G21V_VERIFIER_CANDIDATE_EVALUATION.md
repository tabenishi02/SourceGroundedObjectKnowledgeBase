# N-04G-21V Reference Workstation Verifier Candidate Evaluation

更新日: 2026-10-19

- Status: **Complete / MiniCheck selected / all engineering Gates PASS**
- Branch: `phase-n/n04g21v-verifier-benchmark` / PR #48
- Benchmark start HEAD: `754a1d1341524657cf9b86a58482645669b74ae2`
- Decision authority: `docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md`
- Execution handoff: `docs/planning/N04G21V_CODEX_LOCAL_BENCHMARK_HANDOFF.md`
- Immutable corpus: `benchmark/n04g20-source-fact-verifier-v1.json`
- run_id: `20261019T212717+0900`
- Raw evidence: `.local/n04-v3/runtime/g21v/runs/20261019T212717+0900/` (Git-ignored)

## 1. Isolation and exact identities

The three candidates ran sequentially in separate processes on RTX 4090 using the dedicated `.local/n04-v3/runtime/g21v/venv/`, `hf-cache/` and `nltk-data/`. Standard SGOKB venv package inventories were identical before, after and at review. No standard-venv install, corpus label/required-flag edit, decision-surface change, threshold tuning or manual verdict override occurred.

| Candidate | Model repository | Exact resolved revision |
|---|---|---|
| MiniCheck RoBERTa-large | `lytang/MiniCheck-RoBERTa-Large` | `74c8919647e61ed0f71bc177d94f10930f090068` |
| LettuceDetect v2 mmBERT-base | `KRLabsOrg/lettucedect-v2-mmbert-base` | `8831ce063dff760b01efe4519b4188f5ee2456f2` |
| LettuceDetect v2 Qwen-2B | `KRLabsOrg/lettucedect-v2-qwen-2b` | `4511d95c6a5f24df1e810a097685d068208cb149` |

MiniCheck source: `Liyan06/MiniCheck@b58b9fa69acbd1015ec970fa65dd752413a053d2`, verified from the isolated checkout. Model main SHA before/after scoring was identical to the revision above. mmBERT/Qwen resolved SHA at run start and loaded that exact revision. Network-enabled preparation is allowed in G-21V; this is not G-21R offline proof.

| Runtime component | Exact identity |
|---|---|
| OS / Python | Windows 11 build 26300 / Python 3.10.6, MSC v.1932 64-bit |
| GPU | NVIDIA GeForce RTX 4090, CUDA capability 8.9 |
| PyTorch / CUDA build | 2.6.0+cu124 / 12.4 |
| Transformers | 5.20.1 |
| huggingface_hub | 1.33.0 |
| tokenizers | 0.23.3 |
| MiniCheck | 0.1.0, exact source commit above |
| NLTK / data | 3.10.3 / `punkt`, `punkt_tab` |
| accelerate | 1.4.0 |

Full package lock is `pip-freeze.txt`; Python/GPU/git/source/NLTK inventories and setup logs are under the raw run root. Python platform API reports `Windows-10-10.0.26300-SP0`; runner evidence preserves that string verbatim.

## 2. Fixed decision surfaces and measurements

- MiniCheck: support probability `>= 0.50` means SUPPORTED.
- mmBERT: native argmax answer-token labels; any unsupported span means UNSUPPORTED, without added confidence threshold.
- Qwen: fixed runner prompt, greedy decoding, any `hallucinated_spans` means UNSUPPORTED; same input repeated three times with unchanged parser.

Corpus: 17 cases, including 11 required negatives, 2 required positives, 5 positives total and 12 negatives total. Indeterminate count: 0 for every candidate.

| Candidate | Required negative FP | Required positive | Positive recall | Negative specificity | Elapsed seconds | Peak allocated VRAM MiB | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| MiniCheck | 0/11 | 2/2 | 0.8 (4/5) | 1.0 (12/12) | 105.670 | 1366.077 | PASS |
| mmBERT | 0/11 | 2/2 | 0.6 (3/5) | 1.0 (12/12) | 47.896 | 1201.949 | PASS |
| Qwen | 0/11 | 1/2 | 0.6 (3/5) | 1.0 (12/12) | 1048.664 | 3681.563 | FAIL |

Elapsed time includes revision lookup, model download/cache/load and scoring; this is not warmed inference latency. VRAM is PyTorch peak allocated memory, not total device usage. Findings do not establish quality outside this corpus.

## 3. Claim-level audit and repeatability

Every required replay/adversarial negative and optional negative `borderline-overclaim` was UNSUPPORTED for all candidates, including high-overlap additions, wrong predicate, negation, causal/temporal embellishment and extra Concept theory.

- MiniCheck accepted both required positives. Its only false negative was optional `positive-concept-paraphrase`.
- mmBERT accepted both required positives; it rejected optional `positive-journey-paraphrase` and `borderline-contract-rephrasing`.
- Qwen rejected required `positive-direct-contract`, accepted required `positive-faithful-paraphrase`, and rejected optional `borderline-contract-rephrasing`. Required-positive failure disqualifies it despite safety/repeatability PASS.
- Qwen: 17 inputs x3 raw outputs = 51 outputs. Every triplet parsed successfully into structurally identical normalized spans. JSON/schema/verbatim-span parser errors: 0. Repeatability failures: 0. No output repair occurred.

At review, all original corpus fields were compared with result cases, all metrics were recomputed, and all Qwen triplets were parsed and structurally compared. Runner/comparator results matched. Local `manual-audit.json` records the checks.

## 4. Selection and evidence

**Selected for G-21R: MiniCheck RoBERTa-large, threshold 0.50.** Both non-generative candidates pass safety and required positives. The predetermined tie-break first compares positive recall: MiniCheck 0.8 exceeds mmBERT 0.6. Dependency complexity, latency, VRAM and historical preference are later criteria. Qwen is ineligible at required positives 1/2. No decision-matrix conflict or post-result rule change occurred.

Persistent candidate outputs are byte-for-byte copies of runner JSON:

- `benchmark/results/n04g21v-minicheck-roberta-large-reference-workstation.json`
- `benchmark/results/n04g21v-lettucedect-v2-mmbert-base-reference-workstation.json`
- `benchmark/results/n04g21v-lettucedect-v2-qwen-2b-reference-workstation.json`

`benchmark/results/n04g21v-verifier-comparison-reference-workstation.json` was generated by the unchanged comparator using repository-relative result paths, avoiding publication of workstation absolute paths. Selection and metrics/metadata match the original local comparison. Raw setup/cache/failed verdict evidence remains intact under `.local`; only requested result artifacts are tracked.

## 5. Engineering verification

Reference Workstation results after evidence integration:

| Command | Result |
|---|---|
| `python -m pytest tests/test_n04g20_adversarial_regression.py -q` | 15 passed / 0 failed (0.12s) |
| `python -m pytest tests/test_n04g21_harness_freeze_candidate.py -q` | 4 passed / 0 failed (0.12s) |
| `python -m pytest -q` | 402 passed / 0 skipped / 0 failed (138.62s), 2 local-Qdrant warnings |
| `python -m ruff check .` | PASS after equivalent-literal formatting fix |
| `git diff --check` | PASS |

Two engineering issues were fixed without changing decision rules:

1. Windows `core.autocrlf=true` checked out three hash-bound G-21 JSON files as CRLF. Their committed LF blobs exactly matched the existing frozen SHA-256 values. `.gitattributes` now fixes LF checkout for only those three files; the JSON contents, stored hashes and test assertions remain unchanged. Original failed Gate logs remain in `regression/`; the successful full rerun is in `regression-lf-fixed/`.
2. Ruff E501 flagged three long lines in the fixed Qwen prompt. Equivalent adjacent string literals preserve the exact runtime prompt and SHA-256. The entire runner AST is identical to the benchmark-start source after ignoring source locations; the decision surface/parser/parameters are unchanged. The recorded full suite preceded this semantics-identical literal formatting; final repo-wide Ruff and diff checks passed afterward. No inference rerun or result override was needed.

Both original failure logs are retained. No skip/xfail, lint-rule relaxation or assertion weakening was introduced. Full pytest warnings concern local-Qdrant payload indexes and exact-search parameters.

## 6. Disposition

**G-21V Complete / candidate selected; G-21R NEXT / unblocked.** G-21R is not executed here. G-21 remains Prepared / BLOCKED before final Freeze; G-22 remains blocked; N-04 remains Failed / not Complete; N-05 remains blocked. G-18 semantics, Material Gate, terminal/render policy and historical evidence are unchanged.

Candidate processes have exited. RTX 4090 used 479 MiB at review, GPU utilization 0%; no benchmark model remains resident.
