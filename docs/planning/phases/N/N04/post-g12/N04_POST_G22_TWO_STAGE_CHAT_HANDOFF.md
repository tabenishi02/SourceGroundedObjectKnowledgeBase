# N-04 Post-G22 Two-Stage Remediation Handoff

更新日: 2026-10-22

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Primary next-chat entry: `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`
- G-25A block record: `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-22: **Complete / valid formal FAIL (0/3 PASS)**
- G-23F: **Complete / v4 Design Frozen**
- G-24: **Complete / Implementation Ready for G-25A**
- Current task: **N-04G-25A — development VALID_FAIL_NO_SELECTION; explicit escalation required**

## Read first

0. `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`
1. `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`
2. `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`
3. `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
4. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
5. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
6. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
7. v4 production code under `src/sgokb/grounding/v4_*.py`
8. `src/sgokb/application_grounding_v4.py`
9. `tests/test_n04g24_v4_implementation.py`
10. `tests/test_n04g24_v4_provider_runtime.py`

GitHub `main` is authoritative. Do not revive historical stacked Phase N branches as authority.

## Frozen v4 architecture

```text
Grounded Context
  ↓
Stage 1 Planner
  ↓
Structured Proposition Candidates
  ↓
Reference Integrity
  ↓ PASS only
V2-S / V2-P / V2-D
  ↓
V2-R-A / V2-R-C
  ↓
V3/V4F Source Support
  ↓ PASS only
Validation Record
  ↓
Certification
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
exact fact materialization + interpretation/creative candidates
  ↓
V2 / V4I
  ↓
Validated Presentation Plan
  ↓
Material Requirement
  ↓
Terminal Decision
  ↓ ACCEPTED only
Deterministic Render
```

No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE / UNAVAILABLE.

## G-24 result

Normative implementation record:

`docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`

G-24 added a separate v4 implementation layer without assigning v4 semantics to historical v3 code.

Implemented modules:

```text
src/sgokb/application_grounding_v4.py
src/sgokb/grounding/v4_contracts.py
src/sgokb/grounding/v4_reference.py
src/sgokb/grounding/v4_validation.py
src/sgokb/grounding/v4_adapters.py
src/sgokb/grounding/v4_pipeline.py
```

Tests:

```text
tests/test_n04g24_v4_implementation.py
tests/test_n04g24_v4_provider_runtime.py
```

Key implementation properties:

- provider schema is structural guard only;
- application independently parses/revalidates output;
- Reference Integrity is an independent pre-V2 Gate;
- application owns path/role/attempt/proposition identity;
- V2-R-A and V2-R-C are separate injectable interfaces;
- missing/unavailable classifier fails closed;
- Content-Type classifier receives claim text only, not expected role;
- Validation Record is immutable/digest-bound;
- Certification exact-copies candidate text/support;
- Stage 2 source facts are exact Certified Fact materialization only;
- interpretation uses active Certified Fact IDs only;
- creative is creative-purpose only;
- failed Stage 2 plan is not partially rendered;
- one retry per stage / active-attempt replacement;
- no attempt-1 fallback after attempt 2;
- no Stage 2 -> Stage 1 backtracking;
- system context-limit is application-owned;
- only Validated Presentation Plan + ACCEPTED can normal-render;
- evidence manifest binds exact artifact bytes and lineage;
- provider capability-probe API/case matrix exists.

No concrete Residual classifier was selected in G-24.

## G-25A mandatory preflight and current block

New v4 coverage passed in an isolated local verification environment during G-24:

```text
25 passed
```

Full Reference Workstation verification remains a hard Gate:

```text
python -m pytest -q tests/test_n04g24_v4_implementation.py tests/test_n04g24_v4_provider_runtime.py
python -m pytest -q
python -m ruff check .
git diff --check
```

On 2026-10-21 G-25A attempted to start this preflight. The authorized Reference Workstation `FNB1Main` was online and paired, but Desktop Commander reported that the monthly execution quota had been reached and explicitly instructed not to retry or reconnect. No terminal command was executed.

Therefore:

```text
G-25A preflight = NOT EXECUTED
classifier benchmark = NOT STARTED
classifier selection = NOT PERFORMED
```

Do not interpret this as implementation PASS or FAIL on the Reference Workstation. Resume by running the four commands above when command execution is available. Any failure returns to G-24 remediation; no failure may be waived.

## G-25A responsibility after preflight PASS

Select concrete Residual classifiers as two independent components.

### V2-R-A

```text
input: claim_text only
output: ATOMIC / NON_ATOMIC / AMBIGUOUS
```

### V2-R-C

```text
input: claim_text only
output:
  SOURCE_FACT_CONTENT
  INTERPRETATION_CONTENT
  CREATIVE_CONTENT
  CONTEXT_LIMIT_CONTENT
  MIXED_CONTENT
  AMBIGUOUS
```

Do not reveal expected role/purpose/presentation to the Content-Type classifier.

Mandatory selection Gate:

```text
Atomicity critical NON_ATOMIC false-pass = 0
Content-Type critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
```

All candidates may validly fail:

```text
VALID_FAIL_NO_SELECTION
```

In that case G-25B/G-26 remain blocked; do not weaken the Gate.

Frozen 47 is final confirmation only and must not be used for tuning. The blocked preflight attempt produced no classifier output against Frozen 47.

## Protected boundaries

Do not change during G-25A:

- G-23F frozen architecture;
- Reference Integrity before V2;
- V2-S -> V2-P -> V2-D -> V2-R-A -> V2-R-C ordering;
- application-owned role provenance;
- Atomicity / Content-Type separation;
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

## Current state

```text
G-23F = Complete / v4 Design Frozen
G-24  = Complete / Implementation Ready for G-25A
G-25A mandatory preflight = PASS
G-25A development selection = VALID_FAIL_NO_SELECTION
G-25A = VALID_FAIL_NO_SELECTION / not Complete
G-25B = blocked by G-25A PASS
G-26  = blocked by G-25B PASS
N-04  = Failed / not Complete
N-05  = blocked
```

## Immediate resume task

**N-04G-25A — development VALID_FAIL_NO_SELECTION; explicit escalation required.**

At the 2026-10-21 preflight completion (historical snapshot): Reference Workstation rerun `20261021T123230+0900` passed all four commands: targeted 22, full suite 448 (0 failed), Ruff and diff check PASS, after an import-order-only I001 repair. See `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`. Classifier benchmark is READY / not started; G-25A is not Complete. This preflight task performed no Frozen 47 classifier run or model/threshold tuning.

## 2026-10-22 development selection result

Run `20261022T000426+0900` completed all four candidates, both tasks and three repeats. **VALID_FAIL_NO_SELECTION**: no eligible V2-R-A or V2-R-C. Frozen policies/Gates were retained; no selected-checkpoint freeze was created. Frozen 47 final confirmation is **NOT STARTED**.

Engineering: focused 34 passed; full pytest 482 passed / 0 failed / 0 skipped (2 existing local-Qdrant warnings); repository-wide Ruff and diff check PASS. G-25A remains not Complete; G-25B/G-26 remain blocked, N-04 Failed/not Complete and N-05 blocked.

Result and explicit escalation: `docs/evaluation/N04G25A_DEVELOPMENT_CLASSIFIER_SELECTION.md`; `benchmark/results/n04g25a-development-selection-reference-workstation.json`. A separate approved remediation/evaluation protocol with untouched held-out evidence is required. Do not retune from these selection results, weaken Gates, or begin Frozen 47 with failed candidates.
