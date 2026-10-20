# N-04G-25A — Next Chat Handoff

更新日: 2026-10-21

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Authoritative repository state: GitHub `main`
- G-23F: **Complete / v4 Design Frozen**
- G-24: **Complete / Implementation Ready for G-25A**
- Current task: **N-04G-25A — Residual Classifier Benchmark / Selection**
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Read first

1. `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`
2. `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`
3. `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
4. `docs/planning/phases/N/N04/post-g12/N04G25_V4_DEV_BENCHMARK_TASKS.md`
5. `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
6. `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
7. `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
8. `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
9. v4 production code:
   - `src/sgokb/application_grounding_v4.py`
   - `src/sgokb/grounding/v4_contracts.py`
   - `src/sgokb/grounding/v4_reference.py`
   - `src/sgokb/grounding/v4_validation.py`
   - `src/sgokb/grounding/v4_adapters.py`
   - `src/sgokb/grounding/v4_pipeline.py`
10. G-24 tests:
   - `tests/test_n04g24_v4_implementation.py`
   - `tests/test_n04g24_v4_provider_runtime.py`

GitHub `main` is authoritative. Do not use historical stacked Phase N branches as implementation authority.

---

## 2. Mandatory preflight before G-25A benchmark

G-24 targeted sandbox verification passed, but full Reference Workstation repository verification was not executable during G-24 because the connected remote-command service was unavailable due its execution quota.

Therefore G-25A must start with this hard preflight on the Reference Workstation:

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

Do not waive or xfail a failure to begin G-25A.

---

## 3. G-24 implementation state inherited by G-25A

v4 implementation now provides:

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

Select concrete Residual classifiers for:

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

## 5. Required benchmark procedure

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

## 10. Next state

Current:

```text
G-24  = Complete / Implementation Ready for G-25A
G-25A = NEXT
G-25B = blocked by G-25A PASS
G-26  = blocked by G-25B PASS
N-04  = Failed / not Complete
N-05  = blocked
```

Start G-25A only after Section 2 preflight passes.
