# N-04G-22 Formal v3 Re-Acceptance

実行・評価日: 2026-10-20

- **G-22: Complete / valid formal FAIL (0 / 3 Case PASS)**
- **N-04: Failed / not Complete; N-05: blocked**
- G-21 remains Complete / Frozen. This run changes no frozen semantics, rubric, model, threshold, material, retry or rendering policy.
- Run: `20261020T030904+0900`
- Evidence: `.local/n04-v3/runs/20261020T030904+0900/` (Git-ignored; retained locally)
- Formal start: `2026-10-20T03:35:04.297853+09:00`, immediately before Case 1 MCP request.
- Start/end HEAD: `dee23db41e03337d61c9613d73f22bf0bb004066` (identical).
- Branch: `phase-n/n04g22-formal-reacceptance`; PR #50. No main merge.

## Frozen runtime and preflight

Authorities: `benchmark/n04-ai-use-cases-v3.json`, `benchmark/n04-v3-formal-harness-v1.json`, `benchmark/n04-v3-material-profiles-v1.json`, `benchmark/n04-v3-source-fact-verifier-profile-v1.json` and the G-22 execution handoff. All identities and file/schema bindings passed preflight.

| Boundary | Observed exact identity / result |
|---|---|
| Workstation | Windows 11 build 26300; Python 3.10.6; NVIDIA RTX 4090 24GB |
| LM Studio | 0.4.25.0; local endpoint `http://127.0.0.1:1234/v1` |
| Generator | `sgokb-n04-mistral32`; Mistral Small 3.2 24B Q4_K_M; context 8192, GPU max, parallel 1, seed 20261018, stream false |
| Case generator settings | Case 1 temperature 0.2 / max_tokens 700; Case 2 0.0 / 900; Case 3 0.2 / 1100 |
| Bounded judge | `sgokb-n04-phi4`; Phi-4 Q4_K_S; context 8192, GPU max, parallel 1, temperature 0, max_tokens 64, seed 20261018 |
| MiniCheck | `Liyan06/MiniCheck@b58b9fa69acbd1015ec970fa65dd752413a053d2`, clean checkout |
| Verifier model | `lytang/MiniCheck-RoBERTa-Large@74c8919647e61ed0f71bc177d94f10930f090068`; refs/main exact local snapshot; threshold >= 0.50 |
| Formal verifier runtime | `.local/n04-v3/runtime/verifier/`; local NLTK punkt/punkt_tab; offline env enabled; socket create_connection/connect counters 0/0 |
| Verifier package lock | MiniCheck 0.1.0; torch 2.6.0+cu124 / CUDA build 12.4; transformers 5.20.1; huggingface_hub 1.33.0; tokenizers 0.23.3; nltk 3.10.3; accelerate 1.4.0 |
| Harrier | `microsoft/harrier-oss-v1-0.6b@f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`; 1024 dimensions, local-only |
| Qdrant / MCP | Qdrant 1.19.2; MCP SDK 2.3.0, protocol 2026-07-28, stdio `python -m sgokb mcp serve --semantic-runtime` |
| Schema SHA-256 | `1fc7674ee9c42ca60feecd1796ec186f970f88e5600f3839d25d851735a1b990` |

Mistral output-v2 smoke, Phi-4 bounded structured-output smoke, MCP initialization/tools, Harrier/Qdrant, six N-03 Object identities, integrity and schema/file identity all PASS. Standard/verifier package inventories match the Frozen runtime lock; no package install/update or alternate model was used. Exact GGUF identity/hash and runtime inventories are retained in `g21-preflight/`, `environment.json` and `reference-runtime-lock.json`.

MiniCheck offline preflight replay: required negative FP **0/11**, required positives **2/2**, positive recall **0.8**, negative specificity **1.0**; all 17 G-21V verdicts match with maximum score delta **0**. This is preflight verifier proof; it does not imply case-level verifier execution.

## Case results and independent claim review

Each case used public MCP read inputs and existing `GroundedGenerationApplication` validation/material/failure/render contracts. No consumer SQLite Knowledge input, Web/cloud supplementation, hidden factual prompt, or post-result policy change was used. Each Attempt 1 is retained; each retry used only production repair feedback with unchanged Context/task/model/settings/schema/material. Each case's complete frozen rubric was independently evaluated before proceeding to the next case. Machine verdicts were not overridden.

| Case | Terminal / render | Formal verdict | Retry | Final Grounding / Material |
|---|---|---|---|---|
| 1 Saber roleplay | REJECTED / NONE | FAIL | 1 | INDETERMINATE / INDETERMINATE |
| 2 Work comparison | REJECTED / NONE | FAIL | 1 | INDETERMINATE / INDETERMINATE |
| 3 Concept creative synthesis | REJECTED / NONE | FAIL | 1 | FAIL / INDETERMINATE |

### Case 1: Saber

- Current Version `fb0ab12a-5e11-4df7-983a-925da458a129`; Context 640/12000 characters. K4 identifies Saber/Artoria and K5 describes the sword-wielding Servant/Shirou contract.
- Attempt 1 U1/U2 have role-INDETERMINATE. U2 extends K5 with an unsupported bond/purpose assertion. U3 adds Grail War/Excalibur/contract-power details absent from supplied K1-K5 and violates creative scope for roleplay.
- Attempt 2 U1 combines K4/K5 into NON_ATOMIC output with unresolved role; U2 adds unsupported Grail War purpose; U3 invents respect for Shirou's ideals/war trials and violates creative scope. No two certified supported source facts exist.
- Formal acceptance items 1..6: **FAIL, FAIL, NOT_APPLICABLE, PASS, FAIL, NOT_APPLICABLE**. Critical-failure checks 1..4: **PASS, PASS, FAIL, PASS** (PASS means named failure absent). Raw absent-Context franchise additions fail the unqualified supplementation criterion; no external transport or model-memory provenance is claimed proven.
- Evidence: `case-1-roleplay/grounded-context.json`, both `attempt-*/parsed-output.json`, `validation.json`, `material-result.json`, `terminal.json`, `rubric.json`.

### Case 2: actual Similarity rank 1

- Actual MCP `find_similar_objects` rank 1: **BLEACH**, Object `57db855c-574a-4b38-b474-421c165894f1`, current Version `6e75aa45-9c13-42ef-87b4-923beac43bef`, cosine similarity **0.6469602584838867**. It matches the frozen expected ID; no target substitution occurred.
- Fate/stay night current Version `47f2b146-20a6-4d06-957f-904cc5ef39a9`. Both contexts are current, purpose comparison, 1513/24000 characters.
- Both attempts' U1-U4 faithfully repeat K4/K5/K9/K10 across both Works. Nevertheless, V2 returns role-INDETERMINATE for every unit, and U2 is NON_ATOMIC. No source facts become certified supported.
- Both U5 interpretation candidates cite U1-U4 but infer supernatural abilities for both protagonists; K5 does not establish Shirou's abilities. Cross-Work premise references exist, but no validated premise graph/derived support exists. Similarity is never characterized as truth/confidence/preference probability.
- Formal acceptance items 1..6: **FAIL, PASS, FAIL, FAIL, PASS, PASS**. Critical-failure checks 1..5: **PASS, PASS, FAIL, PASS, PASS**.
- Evidence: `case-2-comparison/similarity-request.json`, `similarity-response.json`, `candidate-selection.json`, Context, both attempts and `rubric.json`.

### Case 3: Tsundere + Hero's Journey

- Current Versions `98c16da1-a5a6-4d73-b919-bcadcc3df08f` / `31e52190-fdb2-42da-8860-d4e0bbaa4de6`; purpose creative, 1299/24000 characters.
- Attempt 1 U1-U4 repeat K3/K4/K8/K9 but are NON_ATOMIC / role-INDETERMINATE. U5 proposes a fictional cold-to-warm warrior/adventure but is role-INDETERMINATE. No creative unit is validated.
- Attempt 2 U6-U9 repeat source facts; U10/U11 propose fictional Kira. B2 and B3 both declare presentation_role `creative`, causing V0 `duplicate_presentation_role` at `$.blocks[2].presentation_role`. This is generated output contract failure, not an adapter exception. Source coverage and creative synthesis cannot be certified.
- Independent review finds raw invention explicitly role-separated rather than new source-Concept facts represented as Knowledge. The proposed final arc is limited, and no accepted synthesis exists. No Web/cloud factual input occurred.
- Formal acceptance items 1..6: **FAIL, FAIL, FAIL, FAIL, PASS, PASS**. Critical-failure checks 1..4: **FAIL, FAIL, PASS, PASS**.
- Evidence: `case-3-creative/grounded-context.json`, both attempts, `terminal.json`, `rubric.json`.

All 31 acceptance/critical criteria have individual verdicts, reasons, unit/K/premise IDs and evidence paths in the three local `rubric.json` files. Rejected raw claims are distinguished from rendered claims. **Unsupported rendered material claims = 0; accepted role escapes = 0; accepted non-atomic units = 0.** No rendered or context-limit response was authorized or emitted. Material is INDETERMINATE because grounding prerequisites fail, not a certified context-insufficiency finding.

All source facts stop before specialized verifier/judge: Cases 1/2 and Case 3 Attempt 1 stop at V2; Case 3 Attempt 2 stops at V0. Not-invoked adapter traces are retained. No case-level MiniCheck/Phi-4 fact-judge/derivation PASS is claimed. All recorded adapter exception arrays are empty.

## Canonical safety and engineering results

Before/after canonical SHA-256 (identical, quiescent with no active WAL):

```text
0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d
```

Before/after SQLite integrity is `ok`, foreign-key violations 0. Start/end HEAD is identical; tracked-file hashes and pre-start helper hashes are unchanged. `git-end.json` was captured before any tracked documentation changes.

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_n04_grounded_generation.py tests/test_n04g20_adversarial_regression.py` | 37 passed in 0.66s |
| `python -m pytest -q tests/test_n04g21_harness_freeze_candidate.py tests/test_n04g21r_offline_proof_contract.py tests/test_n04g22_execution_contract.py` | 10 passed in 0.20s |
| `python -m pytest -q` | 408 passed, 0 skipped, 0 failed; 2 warnings; 162.83s |
| `python -m ruff check .` | PASS |
| `git diff --check` | PASS |

The two warnings concern local Qdrant payload indexes and exact-search parameters in the existing hybrid-search test. No test was skipped/xfail or weakened. Log stdout/stderr/result originals remain unchanged. After formal end, exact-name `regression/*.log` views were assembled from those original stdout/stderr bytes to satisfy the Frozen evidence paths. Required top-level/per-case/per-attempt evidence audit PASS. Local LM Studio aliases were unloaded after execution (`lms ps --json`: empty).

## Completion and follow-up boundary

The run is **valid**: frozen identities, pipeline execution, evidence, canonical safety and engineering Gates pass; no runtime/adapter exception or tracked/helper drift invalidates it. It is a **formal FAIL**, because all three use cases fail acceptance/material requirements. Safe rejection is not use-case success.

**G-22 Complete / formal FAIL; N-04 Failed / not Complete; N-05 blocked.**

No automatic G-21 reopening or Frozen profile change is performed here. Follow-up review must examine the preserved generator output (unsupported premises, non-atomic units, presentation-role duplication) and Phi-4 atomicity/role calls (including role-INDETERMINATE on verbatim source restatements) before deciding any separately authorized remediation/design/freeze or new formal run. This evidence does not demonstrate a broken MiniCheck runtime or retrieval defect. Do not relax rubric/threshold or override unresolved roles to obtain PASS.

Historical G-12/G-20/G-20R/G-21V/G-21R evidence and all failed formal attempts remain preserved. Raw outputs, DB, local package/runtime/cache and logs are not committed.
