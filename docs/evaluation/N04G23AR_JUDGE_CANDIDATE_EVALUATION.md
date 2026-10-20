# N-04G-23A-R Judge Candidate Evaluation

実行・評価日: 2026-10-20

- Status: **Complete / valid FAIL / no candidate selected**.
- Selector outcome: **VALID_FAIL_NO_SELECTION**; selected_candidate_id: **none**.
- G-23B: **blocked; a new explicit escalation task is required**.
- N-04: **Failed / not Complete**; N-05: **blocked**.
- G-23 two-stage architecture remains adopted. No production or v3 Frozen artifact changes.
- Run: `20261020T180929+0900`
- benchmark_input_head: `8624d9eb689f8093c279af6234dcce3bba40aafe`
- GitHub main authority at preparation: `cfbd7af9663f4cbe5c4acfa9a71d34649b385a48`.
- Branch: `phase-n/n04g23ar-judge-candidate-evaluation`; PR #55; no main merge.
- Raw evidence/models: `.local/n04-v4/g23ar/20261020T180929+0900/` (Git-ignored).

## Authority and execution freeze

The execution follows the G-23A-R protocol, execution handoff, candidate manifest and pre-registered split paraphrase. Gold, labels, required/critical flags, G-23A exact split-v1, sampling, scoring and selection Gates are unchanged.

Before any Gold request, preflight, candidate-evaluation contract tests (8 passed), targeted Ruff and diff check PASS. No tracked engineering repair was necessary, so the remote branch HEAD above is benchmark_input_head.

All four exact candidate files were acquired/confirmed, digested, neutral-smoked one at a time and unloaded before the single `candidate-runtime-lock.json` was saved at **2026-10-20T18:25:36.421749+09:00**. Only ready candidates then received Gold. Primary start epochs are later than this freeze. Candidate availability, smoke failures and model identities were fixed before any Gold output; no accuracy-based early stop or candidate substitution occurred.

Frozen corpus/profile SHA-256:

```text
Gold 347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687
G-23A profiles a10b9216d6ead15927c23b015ac3d2863c10dfaa6797f3ede72bef51e58ba89e
Candidate manifest a19872b50d067751cf10dcbb6111325da16fdcde2aa6294656f5d5e52df54e2e
Secondary profile 4e15ca2afa6fe2605fdbd18fd7826d664b22aa784d7b2a81177c810090bef468
```

Gold remains 47 cases / 41 required / 6 optional. Runtime lock covers exactly the manifest's four candidates. Tracked input hashes, execution HEAD and all candidate model hashes remained unchanged through inference/selection. Current verification recomputed scores from every saved repeat and reran the unmodified selector into a separate review artifact; its output is identical to the original selection.

## Exact runtime and candidate identities

Common runtime: LM Studio ProductVersion **0.4.25.0**, Python **3.10.6**, Windows 11 Reference Workstation, RTX 4090; context **8192**, GPU offload **max**, parallel **1**, temperature **0**, max_tokens **64**, seed **20261018**, stream **false**, strict JSON schema, repeats **3**. Inference used only the local LM Studio endpoint; acquisition network access ended before runtime freeze. No Web/cloud inference, external retrieval, alternate models or task-prompt overrides were used.

| Candidate | Exact GGUF / quantization | Bytes | Model SHA-256 |
|---|---|---:|---|
| qwen35-9b-q6k | Qwen3.5-9B-Q6_K.gguf / Q6_K | 7359259040 | `b2ccc477f0a2449de299bef560b63e498cae94a2f3a3bae13df01168d77773e6` |
| ministral3-8b-q6k | Ministral-3-8B-Instruct-2512-Q6_K.gguf / Q6_K | 6972872672 | `233add1bc275c394e92d451f19296e33e2864236cd42aa47d110b520a8401505` |
| gemma4-12b-q6k | gemma-4-12B-it-Q6_K.gguf / Q6_K | 9786023584 | `383372016e2f801719e4042aecc895c6731f54402f7ec5d88867970856df6161` |
| mistral32-24b-q4km | Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf / Q4_K_M | 14333909728 | `9829cc54f2105c79499b783e81fbb476b610e91ee9373cc68334c267e49f6bbc` |

Acquisition repositories/revisions:

- `lmstudio-community/Qwen3.5-9B-GGUF@1379f25c6b505a3fc737bd7818cb09389cf807c1`
- `lmstudio-community/Ministral-3-8B-Instruct-2512-GGUF@03465d18062ad69116eced14a79a34c7856b6319`
- `lmstudio-community/gemma-4-12B-it-GGUF@40b870babe39398ce917bbf4b4ff9b5a1f12710e`
- Mistral: existing exact G-22 local model; source file size and copied model digest verified. No repository revision is inferred for that historical local artifact.

Aliases are respectively `sgokb-g23ar-qwen35-9b`, `sgokb-g23ar-ministral3-8b`, `sgokb-g23ar-gemma4-12b`, and `sgokb-n04-mistral32`. Per-candidate runtime/load identity and reasoning-mode evidence are retained in runtime lock/smoke files and summarized in the tracked selection result. Model storage is accessible under the ignored run's `models/` junction to dedicated storage on the larger local drive; no model binaries or raw logs are committed.

## Neutral smoke and incompatible candidate

Neutral input was not a Gold case. Each ready candidate completed three neutral split repeats (six strict-JSON calls) before runtime lock. Ministral, Gemma and Mistral satisfied load quantization/context/parallel and parseability, and were marked ready.

**Qwen3.5 is runtime_incompatible**: its first neutral atomicity call returned empty `message.content`, with 34 characters of `reasoning_content` and 13 reported reasoning tokens (14 completion tokens total). finish_reason was stop, but the required structured JSON was absent; parsing failed. A bounded/non-reasoning strict-output path was therefore not established under the prescribed runtime. No Gold was sent to Qwen, no prompt/settings were tuned, and no substitute quantization/model was used.

The incompatible Qwen attempt and raw response remain retained. This is a pre-Gold runtime incompatibility classification, not an accuracy verdict and not an invalidation of the subsequent complete ready-candidate experiment.

## Primary results

Every ready candidate completed **47 x 3 x 2 = 282 calls**, regardless of accuracy. All **846 Primary responses** finished stop and parsed; no Primary early termination, silent repair, retry-to-improve or partial-result selection occurred. Gold input came only from the frozen benchmark corpus. No Knowledge input pipeline or canonical DB was changed.

Counts below are **case counts** (at least one failure among the three repeats). Full per-repeat results, confusion matrices, exact-match failures and usage/timing are retained in tracked projections; raw HTTP bodies remain local.

| Candidate | Atomicity critical FP | Role critical FP | Required atomicity FR | Required role FR | Required repeat failures | All repeat failures | INDETERMINATE | Elapsed s | Primary |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Ministral 3 8B | 10 | 10 | 1 | 13 | 0 | 0 | 0% | 112.25 | FAIL |
| Gemma 4 12B | 0 | 9 | 4 | 3 | 3 | 5 | 0% | 162.64 | FAIL |
| Mistral Small 3.2 24B | 15 | 8 | 0 | 8 | 0 | 0 | 0% | 115.48 | FAIL |

Primary PASS candidates: **none**. Gemma's zero atomicity critical FP does not compensate for role false-passes, false-rejects or required repeatability failures; no manual ranking/override is used. All five zero-tolerance failure lists must be empty.

## Secondary and deterministic selection

Secondary was **not run**, exactly because no Primary candidate passed. Required exact-vs-paraphrase Atomicity / Role / Joint agreement is **NOT_APPLICABLE / not measured**, not 0% or PASS. No synthetic Secondary result file was created.

The sole selection authority, `benchmark/tools/n04g23ar_compare_candidates.py`, consumed all three ready-candidate Primary results and the four-candidate runtime lock. It returned:

```text
outcome = VALID_FAIL_NO_SELECTION
selected_candidate_id = null
```

A separate review rerun produced the identical selector JSON. No model was selected manually. All owned model aliases were unloaded before selection; subsequent `lms ps --json` returned an empty list.

The diagnostic run is valid: fixed complete candidate pool, identity freeze before Gold, incompatible-candidate evidence, complete ready-candidate Primary runs, exact scoring and deterministic selection are present. It demonstrates no viable candidate in this frozen pool/formulation; it does not prove every local judge or every formulation is insufficient. A **new explicit escalation task** must define any further investigation before changing the candidate pool, prompts or benchmark. No such escalation experiment is started in this task.

## Artifacts, engineering and completion

Tracked: three `n04g23ar-<candidate-id>-primary-reference-workstation.json` verdict/metric projections, `n04g23ar-selection-reference-workstation.json`, this evaluation and current planning/handoff statuses. No Qwen Primary or Secondary results are fabricated. Runtime errors/raw HTTP/download metadata/model files remain under the ignored evidence root. Historical G-22/G-23A evidence and all failed acquisition/smoke attempts are preserved.

Final engineering after result/doc updates:

- `python benchmark/tools/n04g23ar_preflight.py`: **PASS**; frozen Gold/profile hashes and candidate pool match.
- G-23A + G-23A-R contract tests (three explicit files): **18 passed in 0.10s**. Candidate-evaluation tests: **8**; G-23A tests: **10**.
- `python -m pytest -q`: **426 passed, 0 skipped, 0 failed, 2 warnings in 150.25s**. Both warnings concern existing local-Qdrant payload-index/exact-search parameter behavior in `test_hybrid_search`.
- `python -m ruff check .`: **PASS**.
- `git diff --check`: **PASS**.
- `git-end.json`: saved after final engineering; start/end HEAD both `8624d9eb689f8093c279af6234dcce3bba40aafe`. Status contains only post-run result/doc changes.

Final completion after engineering PASS: **G-23A-R Complete / valid FAIL / no candidate selected**; **G-23B blocked**; **N-04 Failed / not Complete**; **N-05 blocked**. All required engineering checks were reviewed and PASS. Benchmark FAIL is preserved without weakening any test or Gate. No main merge is authorized.
