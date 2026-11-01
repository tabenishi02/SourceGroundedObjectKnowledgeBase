# N-04G-24 — v4 Implementation Result

更新日: 2026-10-21

- Status: **Complete / Implementation Ready for G-25A**
- Design authority: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
- Next: `N-04G-25A — Residual Classifier Benchmark / Selection`
- N-04: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Result

G-23Fでfreezeしたv4 grounded-generation contractを、既存v3 production contractを変更せず新しいv4 implementation layerとして実装した。

G-24ではconcrete Residual Atomicity / Content-Type classifierを選定していない。V2-R-A / V2-R-Cはinjectable adapter boundaryとして実装し、adapter未設定・malformed・unavailableはfail-closedとする。

Implementation result:

```text
G-24 = Complete / Implementation Ready for G-25A
G-25A = NEXT
N-04 = Failed / not Complete
N-05 = blocked
```

G-24 Completeはproduction acceptanceを意味しない。G-25A / G-25B / G-26 / G-27は引き続きmandatory Gateである。

---

## 2. Added implementation

### Application facade

`src/sgokb/application_grounding_v4.py`

- Stage 1 request / retry orchestration
- active-attempt enforcement
- pre-V2 Reference Integrity
- V2 / support validation composition
- Certification
- Stage 2 request / retry orchestration
- Stage 2 validation / Validated Presentation Plan
- Material / terminal / render helpers
- evidence / provider-probe access

Historical `src/sgokb/application_grounding.py` remains the v3 facade and was not repurposed to v4 semantics.

### v4 contracts

`src/sgokb/grounding/v4_contracts.py`

Implemented frozen identities:

```text
sgokb.stage1-grounded-content-request.v1
sgokb.stage1-provider-output.v1
sgokb.structured-proposition.v1-candidate
sgokb.v4-validation-record.v1
sgokb.certified-content.v1
sgokb.stage2-presentation-request.v1
sgokb.stage2-provider-output.v1
sgokb.stage-local-retry-feedback.v1
sgokb.validated-presentation-plan.v1
sgokb.system-context-limit.v1
sgokb.grounded-generation-v4-run.v1
```

Implemented:

- Stage 1/2 provider schema instantiation;
- dynamic K / Certified Fact allow-list;
- application schema revalidation;
- duplicate ID / duplicate block checks;
- application-owned request/attempt/proposition identities;
- candidate digests;
- Certified Content digest verification;
- provider COMPLETE / INCOMPLETE / UNAVAILABLE boundary;
- fixed-input Stage 1/2 retry builders;
- retry feedback authority-ID boundary.

Empty Stage 1 K allow-list uses `candidates.maxItems = 0`; implementation does not depend on an empty provider `enum`.

### pre-V2 Reference Integrity

`src/sgokb/grounding/v4_reference.py`

Reference Integrity is implemented as an independent Gate before V2.

Checks include:

```text
context_fingerprint binding
purpose binding
support_refs presence
support ref uniqueness
current Grounded Context membership
```

Reference Integrity FAIL returns an immutable Validation Record with:

```text
reference_integrity_result = FAIL
v2_aggregate_result = NOT_RUN
source_support_aggregate_result = NOT_RUN
```

and does not invoke Residual classifiers or source-support validation.

### V2 / Certification / Stage 2 validation

`src/sgokb/grounding/v4_validation.py`

Implemented authority order:

```text
Reference Integrity
  ↓ PASS only
V2-S
  ↓
V2-P
  ↓
V2-D
  ↓ PASS only
V2-R-A
  ↓ ATOMIC only
V2-R-C
  ↓ compatible only
V3/V4F or V4I
```

Key invariants implemented:

- classifier input is `claim_text` only;
- Content-Type adapter is not passed expected role;
- missing classifier => `UNAVAILABLE` => no PASS;
- earlier FAIL stops downstream semantic evaluation;
- immutable Validation Record + digest;
- certification verifies request/attempt/context/candidate/validation bindings;
- certified text/support are exact candidate copies;
- exact duplicate certification suppression;
- Certified Fact / Certified Content digests;
- Stage 2 verifies Certified Content and Certified Fact bindings;
- main material is exact Certified Fact materialization;
- interpretation uses active Certified Fact premise IDs only;
- creative is creative-purpose only;
- failed Stage 2 model proposition prevents Validated Presentation Plan creation.

### v3 verifier bridge

`src/sgokb/grounding/v4_adapters.py`

Implemented bridges to existing source-support / derivation adapter APIs.

Source support:

```text
deterministic exact support
OR
specialized verifier = SUPPORTED_CANDIDATE
AND independent judge = ENTAILED
```

Specialized negative cannot be rescued. Missing required runtime adapter is fail-closed.

### Material / retry / terminal / evidence / render

`src/sgokb/grounding/v4_pipeline.py`

Implemented:

- Stage 1 readiness separate from final Material Requirement;
- v3 material-profile-compatible requirements;
- one retry per stage / max two attempts;
- active-attempt replacement;
- no attempt-1 fallback after attempt 2;
- no Stage 2 -> Stage 1 backtracking;
- system-owned context-limit artifact;
- terminal outcomes `ACCEPTED / INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`;
- normal render only from Validated Presentation Plan + `ACCEPTED`;
- exact-byte evidence manifest hashing;
- provider capability probe API and required probe-case list.

---

## 3. Added automated tests

Repository tests added:

- `tests/test_n04g24_v4_implementation.py`
- `tests/test_n04g24_v4_provider_runtime.py`

Committed coverage includes:

- schema-valid non-atomic text still reaches V2-R-A;
- forged model role/status rejected;
- invalid/duplicate K refs rejected;
- Certification exact-copy invariant;
- Certification cannot rescue V2 FAIL;
- tampered Validation Record rejected;
- Stage 2 main accepts IDs only;
- factual paraphrase cannot inherit certification;
- interpretation requires active Certified Fact IDs;
- creative denied outside creative purpose;
- duplicate Stage 2 block kinds/IDs rejected by application;
- whole-plan invalidation / no partial render;
- no attempt-1 fallback after attempt 2;
- no Stage 2 -> Stage 1 backtracking;
- retry keeps authoritative inputs/schema fixed;
- tampered Certified Content rejected;
- context-limit is application-owned;
- only Validated Presentation Plan + ACCEPTED can render;
- evidence exact-byte hashing / lineage;
- provider probe matrix identity;
- provider incomplete/unavailable fail closed;
- retry feedback does not contain approved replacement prose.

---

## 4. Verification performed in this task

A local isolated verification environment was assembled for the newly added v4 modules and tests.

Result:

```text
25 passed
```

This consisted of the committed v4 test coverage plus additional targeted checks for:

1. empty Stage 1 allow-list -> `maxItems = 0` without relying on empty enum;
2. attempt 2 request cannot certify attempt 1 candidate material;
3. retry feedback cannot introduce new K / Certified Fact authority IDs.

Static Python parsing of the v4 modules also passed in that verification environment.

### Reference Workstation limitation

Full repository verification on the user's Reference Workstation could not be executed in this session because the connected remote-command service reported its remote command execution unavailable.

GitHub also reports no configured commit status checks / workflow runs for these commits, so no repository CI result exists to substitute for the workstation run.

Therefore this task does **not** claim that the following were executed on the Reference Workstation:

```text
python -m pytest -q
python -m ruff check .
git diff --check
```

G-25A execution must begin with these as preflight, including the committed G-24 tests. Any failure blocks classifier benchmarking until repaired; it must not be waived.

---

## 5. Provider capability probe status

G-24 implements the provider capability probe interface and freezes the required case matrix.

Exact LM Studio / llama.cpp runtime execution is intentionally not treated as a provider semantic authority and must be recorded against the concrete frozen runtime during downstream workstation execution.

Required probe cases are implemented as an explicit set covering:

```text
Stage 1 empty candidates
Stage 1 valid candidate
Stage 1 extra property
Stage 1 invalid support ref
Stage 2 valid main
Stage 2 valid interpretation
Stage 2 creative under creative purpose
Stage 2 invalid Certified Fact ID
application duplicate support/premise rejection
application duplicate block-kind rejection
provider incomplete/interrupted response
```

Safety remains application-owned even when provider probes PASS.

---

## 6. Protected boundaries preserved

G-24 does not alter:

- Frozen 47 Gold labels/flags;
- G-14 no-silent-post-hoc-atomization intent;
- two-stage architecture;
- E2 V2 authority order;
- E3 proposition contract;
- E4 application-owned path provenance;
- E5 classifier selection Gate;
- G-23B/C/D/E contracts;
- Retrieval / Similarity / Context Builder;
- canonical DB;
- Source / Evidence / Provenance;
- Object / Version identity;
- MCP read-only boundary;
- unsupported rendered claim prohibition.

Historical v3 implementation remains available separately and was not assigned v4 semantics.

---

## 7. Residual classifier boundary

No concrete V2-R-A / V2-R-C model, checkpoint or threshold was selected or tuned in G-24.

G-25A remains the sole selection Gate:

```text
Atomicity critical NON_ATOMIC false-pass = 0
Content-Type critical wrong-compatible false-pass = 0
required-valid false reject target = 0
AMBIGUOUS / UNAVAILABLE = fail-closed
```

If all candidates fail:

```text
VALID_FAIL_NO_SELECTION
```

G-26 remains blocked.

---

## 8. Next task

**N-04G-25A — Residual Classifier Benchmark / Selection**

Before benchmark execution, run the Reference Workstation preflight recorded in Section 4 and stop on any failure.
