# N-04G-25A — Next Chat Handoff

更新日: 2026-10-22

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Authoritative repository state: GitHub `main`
- G-23F: **Complete / v4 Design Frozen**
- G-24: **Complete / Implementation Ready for G-25A**
- Current task: **N-04G-25A — Residual Classifier Benchmark / Selection**
- Current execution status: **Mandatory preflight PASS / development selection VALID_FAIL_NO_SELECTION / not Complete**
- Preflight result / historical block record: `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Read first

1. `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`
2. `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`
3. `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`
4. `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
5. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
6. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
7. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
8. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
9. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
10. v4 production code:
   - `src/sgokb/application_grounding_v4.py`
   - `src/sgokb/grounding/v4_contracts.py`
   - `src/sgokb/grounding/v4_reference.py`
   - `src/sgokb/grounding/v4_validation.py`
   - `src/sgokb/grounding/v4_adapters.py`
   - `src/sgokb/grounding/v4_pipeline.py`
11. G-24 tests:
   - `tests/test_n04g24_v4_implementation.py`
   - `tests/test_n04g24_v4_provider_runtime.py`

GitHub `main` is authoritative. Do not use historical stacked Phase N branches as implementation authority.

---

## 2. Mandatory preflight before G-25A benchmark

G-24 targeted sandbox verification passed, but full Reference Workstation repository verification was not executable during G-24.

An earlier G-25A attempt tried to start the mandatory preflight on 2026-10-21. The authorized Reference Workstation `FNB1Main` was online and paired, but Desktop Commander reported that its monthly execution quota had been reached and explicitly instructed not to retry or reconnect. No terminal command could therefore be started.

The historical block and subsequent successful local preflight are recorded in:

`docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`

At the 2026-10-21 preflight completion (historical snapshot): Reference Workstation rerun `20261021T123230+0900` passed all four commands: targeted 22, full suite 448 (0 failed), Ruff and diff check PASS, after an import-order-only I001 repair. See `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`. Classifier benchmark is READY / not started; G-25A is not Complete. This preflight task performed no Frozen 47 classifier run or model/threshold tuning.

The hard preflight remains:

```text
python -m pytest -q tests/test_n04g24_v4_implementation.py tests/test_n04g24_v4_provider_runtime.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Required result:

```text
all PASS
```

If any command fails:

```text
STOP
-> do not begin classifier benchmark
-> classify as G-24 implementation verification failure
-> repair implementation/tests without weakening G-23F
-> rerun full preflight
```

If the commands cannot be executed in a future run:

```text
G-25A = BLOCKED
classifier benchmark = not started
classifier selection = not performed
```

Do not waive, skip or xfail a failure to begin G-25A.

---

## 3. G-24 implementation state inherited by G-25A

v4 implementation provides:

```text
Grounded Context
  ↓
Stage 1 request/provider schema
  ↓
application candidate envelope
  ↓
Reference Integrity
  ↓
V2-S / V2-P / V2-D
  ↓
V2-R-A adapter
  ↓
V2-R-C adapter
  ↓
V3/V4F source support
  ↓
Validation Record
  ↓
Certification / Certified Content
  ↓
Stage 2 request/provider schema
  ↓
exact Certified Fact materialization
  + Stage 2 interpretation/creative candidates
  ↓
V2 / V4I
  ↓
Validated Presentation Plan
  ↓
Material / terminal / render
```

Concrete V2-R-A / V2-R-C components are deliberately not selected.

Missing classifier adapters fail closed as `UNAVAILABLE`; this is expected until G-25A selects concrete components.

---

## 4. G-25A exact responsibility

Select concrete Residual classifiers for two independent tasks.

### V2-R-A — Atomicity

Input:

```text
claim_text only
```

Taxonomy:

```text
ATOMIC
NON_ATOMIC
AMBIGUOUS
```

### V2-R-C — Content Type

Input:

```text
claim_text only
```

Do **not** provide expected role/purpose/presentation as classifier priming.

Taxonomy:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

Application compares content-only result against application-owned path/role after classification.

Atomicity and Content Type remain separate tasks/components; do not reintroduce the historical joint Atomicity/Role judge.

---

## 5. Required benchmark procedure after preflight PASS

Use the existing G-25 plan and E5 evaluation design.

At minimum:

1. construct/freeze Atomicity development corpus;
2. construct/freeze Content-Type development corpus;
3. use pattern-family / derivation-lineage-aware split;
4. do not use Frozen 47 Gold for training or threshold tuning;
5. benchmark required candidate families;
6. freeze model/checkpoint/threshold/abstention policy using development data only;
7. run Frozen 47 Gold once as final confirmation after freeze;
8. measure repeatability, latency and VRAM on Reference Workstation;
9. write reproducibility manifests/hashes;
10. select concrete V2-R-A and V2-R-C only if all mandatory Gates pass.

Required candidate families remain:

```text
encoder sequence classifier
cross-encoder / pair classifier
lightweight/few-shot classifier
historical bounded-LLM baseline
```

---

## 6. Mandatory selection Gates

Atomicity:

```text
critical NON_ATOMIC false-pass = 0
required ATOMIC false-reject target = 0
repeatability exact / 100% as applicable
AMBIGUOUS / UNAVAILABLE = fail-closed
```

Content Type:

```text
critical wrong-compatible false-pass = 0
required valid-compatible false-reject target = 0
repeatability exact / 100% as applicable
MIXED / AMBIGUOUS / UNAVAILABLE = fail-closed
```

Safety Gate takes priority over aggregate accuracy.

All candidates failing is a valid outcome:

```text
VALID_FAIL_NO_SELECTION
```

If that occurs, do not weaken thresholds or labels. G-25B/G-26 remain blocked and an explicit escalation is required.

---

## 7. Frozen 47 use

Frozen 47 Gold is a final confirmation set, not a tuning set.

Forbidden:

```text
inspect Frozen 47 failure
-> retune model/threshold
-> rerun same set
-> claim final confirmation
```

If adjustment occurs after viewing Frozen 47, that confirmation run is invalid and the evaluation protocol must be re-established without leaking the confirmation set into selection.

The current blocked attempt generated no classifier output against Frozen 47 and performed no G-25A tuning from it.

---

## 8. Provider capability probe

G-24 implemented the provider capability probe API and required case matrix.

The exact selected runtime/provider capability evidence must be recorded before downstream freeze. Provider PASS is never semantic authority; application validation remains mandatory.

---

## 9. Protected boundaries

G-25A must not change:

- G-23F frozen architecture;
- Reference Integrity before V2;
- V2-S -> V2-P -> V2-D -> V2-R-A -> V2-R-C order;
- application-owned role provenance;
- content-only V2-R-C input;
- no silent post-hoc atomization;
- Certification exact-copy semantics;
- Certified Content Stage 2 factual boundary;
- exact Certified Fact materialization;
- one retry per stage / active-attempt replacement;
- no Stage 2 -> Stage 1 retry;
- system-owned context-limit;
- fail-closed ambiguity/unavailability;
- Frozen 47 labels/flags;
- Retrieval / Similarity / Context Builder;
- canonical DB;
- Source / Evidence / Provenance;
- Object / Version identity;
- MCP read-only boundary.

---

## 10. Current state and resume point

```text
G-24  = Complete / Implementation Ready for G-25A
G-25A mandatory preflight = PASS
G-25A development selection = VALID_FAIL_NO_SELECTION
G-25A = VALID_FAIL_NO_SELECTION / not Complete
G-25B = blocked by G-25A PASS
G-26  = blocked by G-25B PASS
N-04  = Failed / not Complete
N-05  = blocked
```

The development-data freeze, training/validation policy freeze and selection have completed with **VALID_FAIL_NO_SELECTION**. No candidate is eligible. This work stops before Frozen 47; explicit escalation is required for further remediation.

## 2026-10-22 development selection result

Run `20261022T000426+0900` completed all four candidates, both tasks and three repeats. **VALID_FAIL_NO_SELECTION**: no eligible V2-R-A or V2-R-C. Frozen policies/Gates were retained; no selected-checkpoint freeze was created. Frozen 47 final confirmation is **NOT STARTED**.

Engineering: focused 34 passed; full pytest 482 passed / 0 failed / 0 skipped (2 existing local-Qdrant warnings); repository-wide Ruff and diff check PASS. G-25A remains not Complete; G-25B/G-26 remain blocked, N-04 Failed/not Complete and N-05 blocked.

Result and explicit escalation: `docs/evaluation/N04G25A_DEVELOPMENT_CLASSIFIER_SELECTION.md`; `benchmark/results/n04g25a-development-selection-reference-workstation.json`. A separate approved remediation/evaluation protocol with untouched held-out evidence is required. Do not retune from these selection results, weaken Gates, or begin Frozen 47 with failed candidates.
