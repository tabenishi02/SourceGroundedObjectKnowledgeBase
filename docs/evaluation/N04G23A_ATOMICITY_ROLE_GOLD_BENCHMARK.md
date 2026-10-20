# N-04G-23A Atomicity / Role Gold Benchmark

実行・評価日: 2026-10-20

- Status: **Complete / valid benchmark; engineering PASS**
- Diagnosis: **Phi-4 insufficient for required Gold under the tested formulations; additional judge candidate evaluation required.**
- G-23B: **blocked pending G-23A-R Judge Candidate Evaluation**.
- G-23 two-stage generation architecture remains adopted.
- N-04: **Failed / not Complete**; N-05: **blocked**.
- Run: `20261020T151126+0900`
- `benchmark_input_head`: `53fbe5a833d8515768cbe2557384d1ecd46cb8de` (committed and pushed before model execution).
- Raw evidence: `.local/n04-v4/g23a/20261020T151126+0900/`; no raw HTTP/logs or model/runtime files committed.

## Frozen inputs and Gold

The execution follows the G-23A protocol and Codex handoff under `docs/planning/phases/N/N04/`. Production code and v3 Frozen artifacts are unchanged. No Gold, required/critical flag, prompt, response schema, scoring rule, model or sampling setting was changed after input freeze.

Final corpus: `benchmark/n04g23a-atomicity-role-gold-v1.json`, status `frozen_for_execution`, source G-22 run `20261020T030904+0900`.

| Corpus | Count |
|---|---:|
| Total | 47 |
| Exact G-22 units | 27 |
| Seed retained unchanged except explicit high-confidence metadata | 20 |
| Required high-confidence | 41 |
| Optional genuinely ambiguous Gold | 6 |

Origin breakdown: g22_exact 27, synthetic 13, g20_reuse 5, synthetic_from_g12_pattern 1, g20_pattern 1. G-22 import covers every material unit from Case 1 Attempts 1/2 (3/3), Case 2 (5/5), Case 3 (5/6). Text/metadata are extracted from saved `parsed-output.json`, not reconstructed from summaries.

Gold was assigned independently using G-14's independent-verdict split test and content-first role definition. Unsupported/false source-world claims remain role-valid when their content type is source_fact. Historical Phi-4 verdicts are separate observations, never Gold authority. Six uncertain items retain INDETERMINATE in Gold and required=false; neither certainty nor safety flags were changed after observing results.

| Gold atomicity / role | Count |
|---|---:|
| NON_ATOMIC / ROLE_VALID | 20 |
| ATOMIC / ROLE_VALID | 8 |
| NON_ATOMIC / ROLE_VIOLATION | 7 |
| ATOMIC / ROLE_VIOLATION | 6 |
| INDETERMINATE / ROLE_VALID | 4 |
| NON_ATOMIC / INDETERMINATE | 2 |

Frozen input SHA-256:

| Input | SHA-256 |
|---|---|
| Final corpus | `347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687` |
| P0/P1/P2 profiles | `a10b9216d6ead15927c23b015ac3d2863c10dfaa6797f3ede72bef51e58ba89e` |
| P1P profile | `326432d09bac22985500820d0b7e67dcede75172e3a0faf8d8aa1b5c45f4e496` |
| Runner | `85b1e4ac7e162eb8841fb557e6611f994ac611c0af23e282d17f2030c7e5df47` |
| Comparator | `db5393a06cff2553d6980d8aee2b048ae61a6f28cc90004826f8bdc85c5ab288` |

All five inputs, execution HEAD and current model digest remained unchanged through completion.

## Exact P0 provenance

All **19** historical Atomicity/Role Phi-4 requests were recovered from G-22 raw evidence. The profile stores exact system prompt, parameterized sorted-JSON user prompt, response schema, request paths/digests and historical helper digest. Runner template re-render reproduces UTF-8 message content and complete request-object settings; **19 verified, 0 mismatch**. The remaining 8 imported units had no historical Phi-4 call because production validation stopped earlier; they still participate in every new profile/repeat.

P1/P1P/P2 prompts were not edited. Preparation repairs were limited to existing E501 formatting, JSON-escaped template substitution needed for exact P0, and contract tests that verify completed provenance/corpus coverage while still executing the unprepared-profile refusal test. Scoring conditions were unchanged.

P0 historical reproduction: 19 historical calls x 3 repeats = **57 comparisons**. Atomicity **57/57**, role **57/57**, joint **57/57 (100%)**. No mismatch unit IDs. This reproduces the historical behavior, not Gold correctness.

## Runtime and execution validity

- LM Studio **0.4.25.0 ProductVersion**, local endpoint only.
- Alias `sgokb-n04-phi4`, `microsoft/phi-4-gguf/phi-4-Q4_K_S.gguf`, Q4_K_S, 8,440,762,560 bytes.
- Context **8192**, GPU offload **max**, parallel **1**, temperature **0**, max_tokens **64**, seed **20261018**, stream **false**.
- Reference Workstation: Windows / Python **3.10.6**, RTX 4090 24GB, NVIDIA driver **581.80**.
- Model SHA-256 before/after: `8a8189132ef70cd737e136d38b706e8cb832f9cdf3c744547694769e9313550e`.
- Loaded path/size/quantization/context/alias/parallel match G-22 saved load identity. G-22 retained no model-file digest, so historical digest equality is not claimed; current file digest invariance and exact replay are separately demonstrated.

All 47 cases ran 3 times in P0/P1/P1P/P2. P2 made independent atomicity and role calls on every repeat: **705 HTTP calls**, all response finish_reason **stop**, no parser/runtime exception or fallback. Only local LM Studio was contacted; no Web/cloud inference, retrieval, MCP, MiniCheck or Mistral was used. Raw request/response pairs are retained by profile/call index.

The preparation attempt `20261020T151057+0900` stopped before any Phi-4 call because the local orchestration helper compared FileVersion display `0.4.25+1` to ProductVersion authority. That evidence/helper is retained. Only the helper's version field reference was corrected to ProductVersion, then this new run began; frozen tracked inputs and runtime settings were unchanged. No benchmark result existed when that correction was made.

The owned Phi-4 alias was unloaded at completion; `lms ps --json` subsequently returned an empty list.

## Profile metrics and fixed decision

Counts below are **case counts** (any failure among 3 repeats), not summed HTTP predictions. INDETERMINATE rate counts both dimensions across all case/repeat predictions. Full confusion matrices, exact-match failure IDs and per-repeat verdicts are in the tracked result JSONs.

| Profile | Critical atomicity FP | Critical role FP | Required valid atomicity FR | Required valid role FR | Required repeat failures | INDETERMINATE | Elapsed s | Viable |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| P0 exact joint | 18 | 0 | 4 | 28 | 0 | 50.00% | 76.49 | false |
| P1 clarified joint | 26 | 0 | 0 | 28 | 0 | 50.00% | 55.08 | false |
| P1P clarified paraphrase | 26 | 12 | 0 | 5 | 0 | 6.38% | 47.31 | false |
| P2 split | 11 | 8 | 5 | 17 | 0 | 0.00% | 68.98 | false |

All-case repeatability is 47/47 for each profile; required repeatability is 41/41. Repeatability does not imply accuracy. Safety and Required-valid Gates fail for every profile.

P1/P1P required stability: atomicity **123/123**, role **18/123**, joint **18/123 (14.63%)** over 41 required cases x 3 repeats. Only **6/41** required cases have identical joint verdicts across the paraphrase. Required stability Gate **FAIL**. All-case joint agreement is **18/141 (12.77%)**. Lower P1P INDETERMINATE is accompanied by role false-passes; it is not a safety improvement.

Examples: P0 reproduces role-INDETERMINATE even on direct contract facts; P1 still rejects all 28 required role-valid cases. P2 reduces atomicity false-passes but still has 11 critical atomicity false-pass and 8 critical role false-pass cases, including controls for fact/causal additions, disallowed creative purpose and mixed premise/interpretation content. No manual override or output repair was applied.

Applying the frozen decision tree: P1 fails safety/required-valid and paraphrase stability; P2 also fails safety/required-valid. Therefore **Phi-4 is insufficient for required Gold under these tested formulations**. This does not establish that every possible Phi-4 formulation would fail, nor justify post-hoc prompt/Gold tuning within this run.

For v4 V2, neither tested joint nor split Phi-4 profile is recommended for adoption. Add **G-23A-R [P0] Judge Candidate Evaluation** as the next blocker, retaining the frozen Gold and fail-closed semantics as evaluation authority. No alternative model is selected or executed here. G-23B remains blocked pending that evaluation. The adopted two-stage generation architecture remains unchanged.

## Engineering and completion

- Input-freeze G-23A all tests: **10 passed**; targeted Ruff and diff check PASS.
- Final G-23A tests: **10 passed in 0.96s** (`python -m pytest -q tests/test_n04g23a*.py`, filenames explicitly expanded on Windows).
- Final full pytest: **418 passed, 0 skipped, 0 failed, 2 warnings in 144.01s** (`python -m pytest -q`). The warnings are existing local-Qdrant payload-index/exact-search-parameter warnings in `test_hybrid_search`.
- Repository-wide Ruff: **PASS** (`python -m ruff check .`).
- Final git diff --check: **PASS**.

Benchmark results/provenance and decision are valid and fixed; **G-23A is Complete with all final engineering Gates PASS**. N-04 remains Failed / not Complete; N-05 remains blocked. Result JSONs project original verdicts/usage/timing/metrics without raw HTTP bodies. Historical attempts and all raw evidence are preserved; production and v3 Frozen artifacts are unchanged.
