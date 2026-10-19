# N-04G-21R Selected Verifier Runtime / Reference Workstation Offline Proof

更新日: 2026-10-20

- G-21R: **Complete / PASS**
- G-21: **Complete / Frozen**
- G-22: **NEXT / unblocked; not started**
- N-04: **Failed / not Complete** / N-05: **blocked**
- Branch: `phase-n/n04g21r-offline-proof` / PR #49
- Base main: `92a5d271e030f0da2e912adc460f3b954a803793`
- New formal run_id: `20261019T233552+0900`
- Runtime root: `.local/n04-v3/runtime/verifier/`
- Raw evidence: `.local/n04-v3/runtime/verifier/runs/20261019T233552+0900/`
- Formal runner: `benchmark/tools/n04g21r_minicheck_offline_proof.py` (unchanged)
- Proof: `benchmark/results/n04g21r-minicheck-offline-reference-workstation.json`

## Preparation, authorization and retained history

The selected MiniCheck was not reselected. Exact source, package, HF cache and NLTK assets were already prepared under the formal verifier runtime; no download, install/update, revision/model/runtime substitution or threshold change occurred in this new attempt. Standard SGOKB venv was not modified.

| Prior attempt | Retained outcome |
|---|---|
| `20261019T225703+0900` | Preparation-only helper syntax failure before any offline boundary; logs preserved. |
| `20261019T231409+0900` | MiniCheck proof PASS; G-21 runtime preflight PASS; pytest PASS; repo-wide Ruff F841 blocked final Freeze. All PASS/failure evidence preserved. |

User explicitly authorized deleting only the unused `runner = load_runner()` assignment inside `test_g21r_runner_forces_offline_environment()` before a new boundary. That one line was removed and repo-wide Ruff passed before this attempt. Other contract-test conditions, runner, corpus, labels, required flags, threshold and revisions were unchanged. The earlier state-aware G-21 candidate test guards were already prepared before the previous boundary; they remain unchanged in this attempt and require real PASS proof/lock before allowing Frozen status.

New offline boundary: `2026-10-19T23:35:57.953708+09:00`, recorded in `offline-boundary.json`. It binds every test plus corpus/runner hashes and installed packages. The prior two run directories were hashed before retry and compared afterward: every file and directory file set is unchanged. No failed evidence or historical G-12/G-20/G-20R/G-21V/first G-21 BLOCKED record was deleted or replaced.

## Exact identities and package/runtime lock

- Source: `Liyan06/MiniCheck@b58b9fa69acbd1015ec970fa65dd752413a053d2`, checkout clean.
- Model: `lytang/MiniCheck-RoBERTa-Large@74c8919647e61ed0f71bc177d94f10930f090068`.
- HF `refs/main` equals that exact revision; pinned snapshot and eight config/tokenizer/weight files exist locally. Model cache SHA-256 inventory is unchanged.
- Threshold: `>= 0.50`; max model length 512, chunk size 400, batch size 16, device `cuda:0`.

| Component | Exact identity |
|---|---|
| Python / OS | 3.10.6, MSC v.1932 64-bit / Windows 11 build 26300 |
| MiniCheck | 0.1.0, exact source commit above |
| PyTorch / CUDA build | 2.6.0+cu124 / 12.4 |
| Transformers | 5.20.1 |
| huggingface_hub | 1.33.0 |
| tokenizers | 0.23.3 |
| NLTK / data | 3.10.3 / local `punkt`, `punkt_tab` |
| accelerate | 1.4.0 |
| GPU | NVIDIA GeForce RTX 4090, capability 8.9 |

Full package versions (verifier and standard runtime), CUDA/device and inventory hashes are bound in `benchmark/n04-v3-formal-harness-v1.json` under `reference_workstation.local_runtime_lock`. Full `pip-freeze.txt`, `reference-runtime-lock.json`, snapshot inventory and before/after standard-venv inventory remain in the raw run and `.local/n04-v3/runtime/verifier/lock/`. No credentials, home paths or local install URLs were copied into the tracked lock.

## Formal offline proof

The runner enables `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`, restricts NLTK to local verifier resources and blocks Python socket connections before model load/scoring.

| Gate / measurement | Result |
|---|---|
| Exact source / clean checkout | PASS / PASS |
| Exact refs/main / pinned local snapshot | PASS / PASS |
| Local NLTK punkt / punkt_tab | PASS / PASS |
| socket_connect / create_connection attempts | **0 / 0** |
| Required negative FP | **0/11** |
| Required positive | **2/2** |
| Positive recall | **0.8 (4/5)** |
| Negative specificity | **1.0 (12/12)** |
| G-21V verdict comparison | All 17 equal |
| G-21V max absolute score delta | **0.0** |
| Elapsed model-load/scoring | 1.655695 seconds |
| Peak PyTorch allocated VRAM | 1366.076660 MiB |
| Standard venv / cache / boundary file hashes | unchanged |

The optional Concept paraphrase remains unsupported exactly as in G-21V. No manual override or threshold tuning occurred. Raw runner JSON is retained locally; the tracked proof is a lossless representation with only NLTK paths made repository-relative and path separators normalized. All scores/verdicts/counters/identities are unchanged.

## Remaining G-21 preflight

All PASS:

- Mistral neutral generator output-v2 envelope smoke at frozen model/load/settings.
- Phi-4 bounded atomicity/role structured-output smoke on a neutral output-v2 creative unit at frozen temperature 0 / max_tokens 64 / seed. Exact bounded schema/payload is saved; Phi-4 is not asked to generate the generator envelope.
- LM Studio 0.4.25.0 and both exact local GGUF file/load identities.
- MCP SDK 2.3.0 / protocol 2026-07-28 / frozen stdio initialization and tool discovery.
- Harrier pinned revision / 1024 dimensions / local-only, Qdrant 1.19.2 and frozen collection profile / derived readiness.
- System integrity, no foreign-key violations; N-03 six current accepted Object identities.
- Tracked candidate file hashes and output-v2 schema identity.
- Quiescent canonical DB before/after equal:

```text
0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d
```

No G-22 formal case started. Mistral/Phi-4 were unloaded after smoke; worker processes exit after use.

## Engineering and Freeze verification

| Command | Result |
|---|---|
| `python -m pytest tests/test_n04_grounded_generation.py tests/test_n04g20_adversarial_regression.py -q` | 37 passed (0.72s) |
| `python -m pytest tests/test_n04g21_harness_freeze_candidate.py tests/test_n04g21r_offline_proof_contract.py -q` | 7 passed (0.14s) |
| `python -m pytest -q` | **405 passed / 0 skipped / 0 failed** (162.69s), 2 local-Qdrant warnings |
| `python -m ruff check .` | PASS |
| `git diff --check` | PASS |
| Same G-21/G-21R contract tests after Freeze | 7 passed (0.12s) |
| Repo-wide Ruff / diff check after Freeze | PASS / PASS |

Full suite ran before the Freeze transition as required; post-transition contracts rechecked the changed profiles, lock and proof bindings. No assertion weakening, skip/xfail or lint-rule relaxation was introduced. Original prior-attempt F841 log is retained.

After every preflight/engineering Gate passed, all four candidate JSON statuses became `frozen`, local reproduction became true, runtime/package lock was embedded, `unresolved_before_freeze` became empty and file/canonical hashes were recalculated from actual payloads. Material logical payload did not change, so its canonical hash legitimately remains the same; status/file hash changed. Verifier payload changed, so both its canonical and file hashes changed. No payload change is hidden to retain an old hash.

## Final file and canonical identities

| Artifact | SHA-256 |
|---|---|
| `benchmark/n04-v3-formal-harness-v1.json` | `9e290e120b5f638c373d2cb951e220832b23b461a5a7488d071e9f8190a464a0` |
| `benchmark/n04-v3-source-fact-verifier-profile-v1.json` | `bfb8b9ec88e9a1b379dbf795268921255ecb047c921aef6b3029b084dcaf4f37` |
| `benchmark/n04-v3-material-profiles-v1.json` | `f9011fcd7da2a5881486a70a6e799a36793037bb31a1e70c1bafaeba1601a9d6` |
| `benchmark/n04-ai-use-cases-v3.json` | `e49aff7bfb0b33c13745ca0457c860bf27050e7eb779a02550374803b370f126` |
| Proof result | `621da76085e41d2a5b66001c28f1b326785a291db600f0875e2de36e2e081576` |
| Material canonical payload | `44ac430ebf6af60123671fbd29985bd9f036fb11907c937d6c0b4f7523a872b4` |
| Verifier canonical payload | `01eedf64791b71466cee815ad8f44289d2fd4a5859f1bf76041a5ef91847c034` |

All hash-bound artifacts explicitly use LF checkout. Before commit, final JSON byte hashes and dependent proof/file/canonical bindings were recomputed against LF bytes; prior pre-normalization hash evidence remains in the run directory. JSON logical facts and runtime outcomes did not change.

## Completion decision

**G-21R Complete / PASS; G-21 Complete / Frozen; G-22 NEXT / unblocked. N-04 Failed / not Complete; N-05 blocked.** Final proof does not substitute for G-22's three representative AI use-case acceptance. No main merge or G-22 execution is authorized by this completion record.
