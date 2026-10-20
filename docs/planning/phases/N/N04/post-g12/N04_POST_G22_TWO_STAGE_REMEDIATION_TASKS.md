# N-04 Post-G22 Two-Stage Grounded Generation Remediation Tasks

更新日: 2026-10-21

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- v4 Design Freeze: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
- G-24 result: `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`
- G-25 plan: `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
- G-25A handoff: `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`
- G-25A block record: `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**

## 1. Remediation chain

```text
G-22 valid formal FAIL
  ↓
G-23 Two-stage architecture decision                 Complete / Accepted
  ↓
G-23A-E Gate Responsibility Decomposition           Complete / Architecture Accepted
  ├─ E1 47-Gold Responsibility Mapping              Complete
  ├─ E2 v4 V2 Responsibility Boundary               Complete
  ├─ E3 Structured Proposition Contract             Complete
  ├─ E4 Role Provenance / Compatibility Matrix      Complete
  ├─ E5 Residual Classifier Evaluation Design       Complete
  ├─ E6 47-Gold Desk Replay                         Complete
  └─ E7 Integration / Unblock Review                Complete / Accepted
  ↓
G-23B Stage 1 contract                              Complete / Contract Accepted
  ↓
G-23C Certification / Certified Content             Complete / Contract Accepted
  ↓
G-23D Stage 2 contract                              Complete / Contract Accepted
  ↓
G-23E Provider schema + stage-local retry           Complete / Contract Accepted
  ↓
G-23F v4 Design Integration / Freeze                Complete / v4 Design Frozen
  ↓
G-24 v4 implementation                              Complete / Ready for G-25A
  ↓
G-25A mandatory Reference Workstation preflight     BLOCKED / not executed
  ↓ PASS only
G-25A Residual Classifier Benchmark / Selection     not started
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression          blocked
  ↓ PASS only
G-26 Reference Workstation v4 harness freeze        blocked
  ↓
G-27 Formal v4 Re-Acceptance
  ↓ PASS only
N-04 Complete
  ↓
N-05 unblocked
```

Historical G-18/G-21/G-22 artifacts remain immutable evidence.

## 2. Current task table

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-23 | P0 | Complete / Architecture Accepted | two-stage generation architecture |
| N-04G-23A-E | P0 | Complete / Architecture Accepted | decompose V2/Gate responsibilities |
| N-04G-23B | P0 | Complete / Contract Accepted | Stage 1 Content Planner contract |
| N-04G-23C | P0 | Complete / Contract Accepted | Certification / Certified Content contract |
| N-04G-23D | P0 | Complete / Contract Accepted | Stage 2 Presentation Generator contract |
| N-04G-23E | P0 | Complete / Contract Accepted | provider schema + stage-local retry |
| N-04G-23F | P0 | Complete / v4 Design Frozen | end-to-end integration / implementation freeze |
| N-04G-24 | P0 | **Complete / Implementation Ready for G-25A** | v4 production-layer implementation |
| N-04G-25A | P0 | **BLOCKED / mandatory Reference Workstation preflight not executed** | Residual classifier benchmark / selection |
| N-04G-25B | P0 | Blocked by G-25A PASS | integrated adversarial regression |
| N-04G-26 | P0 | Blocked by G-25B PASS | Reference Workstation freeze |
| N-04G-27 | P0 | Blocked by G-26 | Formal v4 Re-Acceptance |

## 3. Frozen v4 architecture

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
Structured Proposition Candidates
  ↓
Reference Integrity
  ↓ PASS only
V2-S / V2-P / V2-D
  ↓
V2-R-A / V2-R-C where required
  ↓
V3/V4F Source Fact Support
  ↓ PASS only
Validation Record
  ↓
Certification
  ↓
Certified Content
  ↓
Stage 2 Presentation Generator
  ↓
application path assignment / exact Certified Fact materialization
  ↓
V2 for Stage 2 model-authored propositions
  ↓
V4I for interpretations
  ↓
Validated Presentation Plan
  ↓
Material Requirement
  ↓
Terminal Decision
  ↓ ACCEPTED only
Deterministic Render
```

Universal invariant:

```text
No downstream positive verdict may rescue an earlier FAIL / INDETERMINATE / UNAVAILABLE.
```

## 4. Frozen path / authority map

```text
stage1_fact_candidate
  -> source_fact
  -> model-authored
  -> Reference Integrity + V2 + V3/V4F

certified_fact_materialization
  -> source_fact
  -> application-owned exact Certified Fact text

stage2_interpretation_candidate
  -> interpretation
  -> model-authored
  -> V2 + V4I

stage2_creative_candidate
  -> creative_addition
  -> model-authored
  -> V2 + creative-purpose/scope policy

system_context_limit
  -> context_limit
  -> application/system-owned only
```

Model-declared role/status is not authority.

## 5. G-24 implementation result

Authority: `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`.

G-24 added a separate v4 implementation layer while retaining the historical v3 facade/contracts.

Production files:

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

Implemented safety properties include:

- Stage 1/2 dynamic provider schemas + application revalidation;
- pre-V2 Reference Integrity;
- application-owned path/attempt/proposition identities;
- V2-S/P/D + separate V2-R-A / V2-R-C adapter interfaces;
- fail-closed missing/unavailable residual components;
- source support and interpretation derivation boundaries;
- immutable Validation Records;
- exact-copy Certification / Certified Content;
- exact Certified Fact Stage 2 materialization;
- Stage 2 whole-plan validation;
- one retry per stage / active-attempt replacement;
- no attempt-1 fallback after attempt 2;
- no Stage 2 -> Stage 1 retry;
- system-owned context-limit;
- terminal/render authorization;
- evidence manifest hashing / lineage;
- provider capability-probe interface/case matrix.

No concrete V2-R-A / V2-R-C classifier was selected in G-24.

## 6. G-24 verification state and G-25A preflight

New v4 implementation was exercised in an isolated local verification environment.

Result:

```text
25 passed
```

The repository contains the automated G-24 test suites listed above.

Reference Workstation full-repository commands could not be executed during G-24 because the connected remote-command service was unavailable due its execution quota. G-25A therefore has a mandatory preflight before any classifier benchmark:

```text
python -m pytest -q tests/test_n04g24_v4_implementation.py tests/test_n04g24_v4_provider_runtime.py
python -m pytest -q
python -m ruff check .
git diff --check
```

On 2026-10-21 G-25A attempted to start this preflight. `FNB1Main` was online and paired, but Desktop Commander reported that its monthly execution quota had been reached and explicitly instructed not to retry or reconnect. No preflight command was executed.

Authority for this block:

`docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`

Therefore:

```text
preflight = NOT EXECUTED
G-25A benchmark = NOT STARTED
G-25A selection = NOT PERFORMED
```

Any future preflight failure blocks benchmark execution and returns to G-24 implementation remediation. The preflight may not be waived.

## 7. Provider / retry invariants retained

Provider schema remains a structural guard only. Application revalidation is mandatory.

Do not depend on provider enforcement of `uniqueItems`, `contains/minContains/maxContains`, conditionals or cross-item uniqueness.

Retry remains:

```text
Stage 1 max attempts = 2 / max retry = 1
Stage 2 max attempts = 2 / max retry = 1
```

Attempt 2 fully replaces attempt 1 as active material. Historical attempts remain evidence only; no cross-attempt merge/fallback is allowed.

## 8. G-25A resume scope

Current task remains **N-04G-25A — Residual Classifier Benchmark / Selection**, but execution is blocked before benchmark start.

Primary handoff:

`docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`

Resume only when Reference Workstation command execution is available and the mandatory preflight can be run.

After preflight PASS, G-25A must select concrete V2-R-A and V2-R-C components under this mandatory Gate:

```text
Atomicity critical NON_ATOMIC false-pass = 0
Content-Type critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
```

All candidates fail:

```text
VALID_FAIL_NO_SELECTION
```

and G-25B/G-26 remain blocked. Gate weakening is prohibited.

## 9. Protected boundaries

Do not change without reopening G-23F or explicit downstream escalation:

- Frozen 47 Gold labels/flags and historical evidence;
- no silent post-hoc atomization;
- two-stage architecture;
- Reference Integrity before V2;
- E2 authority order;
- application-owned provenance;
- Atomicity / Content-Type separation;
- candidate / Validation Record / Certification separation;
- exact Certified Fact materialization;
- Certified Content Stage 2 factual boundary;
- one retry per stage / active-attempt replacement;
- no Stage 2 -> Stage 1 retry;
- system-owned context-limit;
- provider schema as guard only;
- fail-closed ambiguity/unavailability;
- Retrieval / Similarity / Context Builder;
- canonical DB;
- Source / Evidence / Provenance;
- Object / Version identity;
- MCP read-only boundary.

## 10. Current state

```text
G-23F = Complete / v4 Design Frozen
G-24  = Complete / Implementation Ready for G-25A
G-25A = BLOCKED / Reference Workstation preflight not executed
G-25B = blocked by G-25A PASS
G-26  = blocked by G-25B PASS
N-04  = Failed / not Complete
N-05  = blocked
```

## 11. Immediate resume action

Run the four-command Reference Workstation preflight. Only after all PASS may the G-25A Residual Classifier benchmark/selection begin.
