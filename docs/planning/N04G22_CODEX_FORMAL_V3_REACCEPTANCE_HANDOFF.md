# N-04G-22 Codex Formal v3 Re-Acceptance Handoff

更新日: 2026-10-20

- Task: `N-04G-22 [P0] Formal v3 Re-Acceptance`
- Status: **Execution completed / valid formal FAIL (2026-10-20; 0/3 Case PASS)**
- Result: `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md`; run `20261020T030904+0900`. N-04 Failed / not Complete; N-05 blocked. The execution procedure below is retained unchanged.
- Branch: `phase-n/n04g22-formal-reacceptance`
- Base main: `1d0fce208b0b38f5483f3e1c658d7445b30759c6`
- Frozen acceptance: `benchmark/n04-ai-use-cases-v3.json`
- Frozen harness: `benchmark/n04-v3-formal-harness-v1.json`
- Frozen material profiles: `benchmark/n04-v3-material-profiles-v1.json`
- Frozen verifier profile: `benchmark/n04-v3-source-fact-verifier-profile-v1.json`
- G-21R proof: `benchmark/results/n04g21r-minicheck-offline-reference-workstation.json`
- Preflight checker: `benchmark/tools/n04g22_freeze_preflight.py`

## 1. Purpose

G-22 is an execution/evaluation task, not a redesign task. Execute the three frozen representative AI use cases on the Reference Workstation with the exact G-21 Frozen harness, retain complete evidence, perform independent claim-level review, and decide PASS/FAIL without relaxing any condition after seeing outputs.

Do not modify G-18 semantics, frozen model identities, threshold, material profiles, retry policy, terminal/render policy, retrieval behavior, corpus, or formal rubric in order to obtain PASS.

## 2. Preparation before formal start

1. Locate the existing local checkout; do not assume a path without confirming it.
2. Fetch and switch to `phase-n/n04g22-formal-reacceptance`.
3. Fast-forward to the remote branch; do not rebase, force-push, or merge unrelated work.
4. Confirm working tree clean except ignored `.local` runtime/evidence.
5. Run:

```text
python benchmark/tools/n04g22_freeze_preflight.py
python -m pytest -q tests/test_n04g21_harness_freeze_candidate.py tests/test_n04g21r_offline_proof_contract.py tests/test_n04g22_execution_contract.py
python -m ruff check .
git diff --check
```

All must PASS before formal start.

A Git-ignored local orchestration helper may be created under `.local/n04-v3/g22/` before formal start. Do not edit Git-managed source/test/benchmark/frozen JSON after formal start. The helper must call existing production code and frozen runtime interfaces; it must not reimplement or weaken validation semantics.

## 3. Frozen runtime identities

Use `benchmark/n04-v3-formal-harness-v1.json` as machine authority. In particular:

Reference Workstation:
- Windows 11 / recorded build
- Python 3.10.6
- RTX 4090 24GB
- evaluation DB `.local/n03/sgokb-n03.sqlite`

Semantic runtime:
- Harrier `microsoft/harrier-oss-v1-0.6b`
- revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`
- 1024 dimensions, local-only
- Qdrant frozen profile/collection

MCP:
- SDK 2.3.0
- protocol 2026-07-28
- stdio
- command `python -m sgokb mcp serve --semantic-runtime`
- AI knowledge input must come through public MCP read boundary; consumer direct SQLite Knowledge read is prohibited.

Generator:
- `sgokb-n04-mistral32`
- Mistral Small 3.2 24B Q4_K_M frozen GGUF
- context 8192 / GPU offload max / parallel 1 / seed 20261018 / stream false
- Case 1: temperature 0.2 / max_tokens 700
- Case 2: temperature 0.0 / max_tokens 900
- Case 3: temperature 0.2 / max_tokens 1100

Bounded semantic model:
- `sgokb-n04-phi4`
- Phi-4 Q4_K_S frozen GGUF
- context 8192 / GPU offload max / parallel 1
- temperature 0 / max_tokens 64 / seed 20261018 / stream false

Specialized verifier:
- MiniCheck source `Liyan06/MiniCheck@b58b9fa69acbd1015ec970fa65dd752413a053d2`
- model `lytang/MiniCheck-RoBERTa-Large@74c8919647e61ed0f71bc177d94f10930f090068`
- threshold `>= 0.50`
- formal MiniCheck runtime `.local/n04-v3/runtime/verifier/`
- offline/local-files-only

No alternate model, revision, threshold, package set, cloud inference, Web retrieval, or hidden factual supplementation is allowed.

## 4. Formal preflight

Before formal start, reproduce every frozen G-21 preflight requirement. At minimum:

- Git working tree clean except ignored evidence/runtime.
- Frozen file hashes and schema hash pass `n04g22_freeze_preflight.py`.
- evaluation DB exists; no active WAL at quiescent hash points.
- six N-03 Object identities match.
- Harrier/Qdrant/MCP identities and system integrity PASS.
- LM Studio version/endpoint and Mistral/Phi-4 exact model/load profiles match.
- neutral generator output-v2 structured-output smoke PASS.
- neutral Phi-4 bounded structured-output smoke PASS.
- MiniCheck exact source/model/cache/runtime lock remains valid and offline scoring works.
- MCP stdio initialization/tool discovery PASS.

If any frozen identity cannot be met, stop before formal start. Do not substitute another component.

## 5. Evidence root and formal start boundary

Create:

```text
.local/n04-v3/runs/<run_id>/
```

with `run_id` format `YYYYMMDDTHHMMSS+0900`.

Before Case 1's first MCP request, save the required frozen top-level evidence, including:

- run.json
- git-start.json
- environment.json
- reference-runtime-lock.json
- harness.json
- acceptance-spec.json
- material-profiles.json
- verifier-profile.json
- schema-identity.json
- lm-studio-models.json
- minicheck-runtime.json
- minicheck-screening.json
- mcp-runtime.json
- canonical-before.json
- integrity-before.json
- G-22 freeze-preflight output

Canonical before must be a quiescent SHA-256 of `.local/n03/sgokb-n03.sqlite` with no active WAL.

After these are saved, formal start is immediately before the first Case 1 MCP request. From that point until `git-end.json` is captured, do not edit Git-managed files. Start/end HEAD must be identical.

## 6. v3 production pipeline

Use `sgokb.application_grounding.GroundedGenerationApplication` and existing production contracts.

The local orchestration must provide the four frozen adapter boundaries:

- `AtomicityRoleValidatorAdapter`
- `SourceFactVerifierAdapter`
- `SourceFactJudgeAdapter`
- `InterpretationDerivationJudgeAdapter`

### Atomicity / role adapter

Use frozen Phi-4 bounded runtime. Input only:
- unit text
- semantic role
- purpose
- presentation role
- minimal frozen rule text required to classify atomicity/role

Allowed verdicts are the frozen atomicity and role verdicts. No Web, uncited Knowledge, or generator conversation.

### SourceFactVerifierAdapter

For V3-unresolved source facts, use only exact cited support-unit content plus claim text with the frozen MiniCheck runtime. A score `>= 0.50` yields only `SUPPORTED_CANDIDATE`; below threshold is no PASS. Specialized-negative cannot be overridden.

### SourceFactJudgeAdapter

Only specialized-positive unresolved facts proceed to frozen Phi-4 independent judge. Input only claim text, exact cited support unit content, and minimal identity metadata. Only `ENTAILED` permits support. Negative/disagreement/indeterminate is no PASS.

### InterpretationDerivationJudgeAdapter

Input only validated same-output source_fact premises, premise metadata, atomic conclusion and purpose. Only `REASONABLE_DERIVATION` yields derived support. Any unsupported premise prevents judge rescue.

Generator must use `GroundedGenerationRequestBuilder.to_prompt_text(request)` as the sole user task message and the frozen strict `GENERATION_OUTPUT_SCHEMA` via LM Studio structured output. No case-specific hidden factual prompt is allowed.

## 7. Attempt / retry / terminal / render flow

For each case:

1. Obtain MCP context/retrieval evidence.
2. Project Grounded Context.
3. Build the frozen request.
4. Generate Attempt 1.
5. Parse output.
6. Run V0-V5 validation including all adapters.
7. Evaluate MaterialRequirementGate with the frozen profile.
8. Call failure controller.
9. If and only if retry is authorized, create `build_retry_feedback()` and run exactly one Attempt 2 with unchanged Context/fingerprint/task/model/settings/schema/profile. The only addition is structured repair feedback.
10. Retain Attempt 1 evidence even if Attempt 2 occurs.
11. Render only according to frozen terminal authorization.

Formal Case PASS requires terminal `ACCEPTED`. `INSUFFICIENT_CONTEXT`, `REJECTED`, and `SYSTEM_FAILURE` are formal FAIL even if safely handled.

## 8. Case 1 — Saber Roleplay

Use MCP `build_context` with the exact frozen acceptance settings:

- Saber object `326a97cf-47aa-4760-a7f1-07bfe639fcf0`
- purpose `roleplay`
- max_characters 12000
- include_attributes true
- include_relations true
- include_evidence_refs false
- current accepted version only

Task text must come unchanged from `benchmark/n04-ai-use-cases-v3.json`.

Material profile `n04-v3-case-1-roleplay` requires at least two supported source_fact units covering Saber.

Independent formal review must verify:
- terminal ACCEPTED / NORMAL render;
- first-person roleplay;
- minimum supported facts satisfied;
- no unsupported personality/backstory/event/identity/relationship/world claim;
- no material fact imported from model memory;
- no role escape/non-atomic mixed proposition accepted.

## 9. Case 2 — Similar Work Comparison

First call MCP `find_similar_objects` for Fate/stay night:

- source `d5824d33-7008-4121-9cfe-1f95a19667fd`
- cross_class false
- limit 5
- current scope
- real frozen semantic runtime

Use actual returned current Work rank 1. Do not hardcode BLEACH as the target. Save similarity request/response and candidate-selection evidence.

The frozen expected rank-1 ID is:

```text
57db855c-574a-4b38-b474-421c165894f1
```

If actual rank 1 differs, Case 2 formal verdict is FAIL; do not substitute expected ID.

Build contexts for both Works with:
- purpose `comparison`
- max_characters 24000
- attributes true
- relations false
- evidence refs true
- current accepted versions

Material profile requires:
- at least one supported source_fact from each Work;
- at least one derived_supported interpretation;
- interpretation premise graph covers both Works.

Formal review must also verify no external factual premise and no claim that similarity score is truth/confidence/preference probability.

## 10. Case 3 — Concept Combination Creative

Use MCP `build_context` for:

- Tsundere `8c83f986-f491-41a8-8645-9f71dd5874b9`
- Hero's Journey `fee32007-0f92-449a-ba21-4ec2f78d1cd4`
- purpose `creative`
- max_characters 24000
- attributes true
- relations true
- evidence refs false
- current accepted versions

Material profile requires:
- at least one supported source_fact for each Concept;
- at least one valid creative_addition.

Formal review must verify the new concept meaningfully combines both source Concepts, while creative additions stay role-separated and no unsupported source-Concept claim is presented as grounded SGOKB Knowledge.

## 11. Evidence requirements

Use the exact evidence tree frozen in `benchmark/n04-v3-formal-harness-v1.json`.

For every attempt retain at least:
- request.json
- http-request.json
- http-response.json
- raw-output.txt
- parsed-output.json
- output-binding.json
- validation.json
- atomicity-role.json
- source-fact-verifier.json
- source-fact-judge.json
- interpretation-derivation.json
- material-result.json
- decision.json

For every case retain:
- mcp-request.json
- mcp-response.json
- context-builder.json
- grounded-context.json
- terminal.json
- rubric.json

Case 2 additionally retains similarity request/response/candidate-selection evidence. Retry retains retry-feedback and full attempt-2 evidence. Rendered text exists only when authorized.

## 12. Independent formal rubric review

Machine `ACCEPTED` is not sufficient.

After each terminal result, independently review the saved Context/K mapping, generated units, validation outputs, support references, MiniCheck/Phi-4 results, material result and rendered output against every `formal_acceptance` and `critical_failures` item in `benchmark/n04-ai-use-cases-v3.json`.

For each item record:
- PASS / FAIL / NOT_APPLICABLE
- concise reason
- relevant unit IDs
- support/K refs or premise IDs
- evidence file path

Any unsupported rendered material source-world claim is a critical failure. Do not treat model plausibility or franchise/world truth as Source support.

## 13. Canonical after and engineering Gates

After Case 3, close MCP/read clients and make DB quiescent. Save:
- canonical-after.json
- canonical-compare.json
- integrity-after.json

Before/after DB SHA-256 must be identical and integrity must PASS both times.

Run the Frozen engineering Gates and save logs:

```text
python -m pytest -q tests/test_n04_grounded_generation.py tests/test_n04g20_adversarial_regression.py
python -m pytest -q tests/test_n04g21_harness_freeze_candidate.py tests/test_n04g21r_offline_proof_contract.py tests/test_n04g22_execution_contract.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Save `git-end.json` after all formal/evaluation steps and confirm start/end HEAD identical.

## 14. Overall decision

Overall PASS requires all of:

- Case 1 formal PASS
- Case 2 formal PASS
- Case 3 formal PASS
- unsupported rendered material claims = 0
- role escape = 0
- material requirements PASS
- terminal/render authorization PASS
- canonical before/after equal
- integrity before/after PASS
- focused/replay regression PASS
- repository-wide Ruff PASS
- full pytest failed = 0
- git start HEAD == git end HEAD

Save `overall-evaluation.json` with explicit reasons.

## 15. Post-run repository update

Only after `git-end.json` has been captured may Git-managed docs/results be changed.

### If Overall PASS

- Add `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md` with full execution summary and claim-level review conclusions.
- Update `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`: G-22 Complete / PASS; N-04 Complete.
- Update the authoritative Phase N task/status documents that currently mark N-04 Failed or N-05 blocked. Unblock N-05 only where the existing dependency says N-04 completion is its prerequisite; do not invent a later task state.
- Preserve all G-12/G-20/G-21 historical evidence.

### If Overall FAIL

- G-22 is Complete / formal FAIL if the formal run itself was valid.
- N-04 remains Failed / not Complete; N-05 remains blocked.
- Record exact failing Case, unit, Gate and evidence. Do not change the rubric to make it pass.
- Classify whether the failure points to generation, atomicity/role, verifier/judge, interpretation, material, retrieval, terminal/render, or runtime.

### If the formal run is INVALID due to harness/system defect

- Preserve evidence.
- Do not mark G-22 Complete as a valid acceptance result.
- Keep N-04 Failed / not Complete.
- Record whether G-21 must be reopened and why.

Raw `.local` evidence and local model/runtime files must not be committed.

## 16. Required final report to ChatGPT

Return:

```text
run_id
formal run valid/invalid
preflight PASS/FAIL
start HEAD
end HEAD
exact generator/verifier/judge identities
Case 1 terminal + formal PASS/FAIL + retry count
Case 2 actual similarity rank-1 + terminal + formal PASS/FAIL + retry count
Case 3 terminal + formal PASS/FAIL + retry count
unsupported rendered material claim count
role escape count
material Gate results
canonical before SHA-256
canonical after SHA-256
canonical equal
integrity before/after
focused regression
contract tests
full pytest
Ruff
git diff --check
overall G-22 verdict
N-04 state
N-05 state
formal evidence root
post-run commit SHA
PR status
```

Do not merge to main. ChatGPT will review the formal evidence summary and PR before merge.
