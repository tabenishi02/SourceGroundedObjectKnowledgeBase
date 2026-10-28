# P-GUI-03R R9 — Dynamic Verification Attempt 02

Updated: 2026-10-28

- Task: `P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation`
- Slice: `R9 Regression / semantic-equivalence acceptance`
- Status: **Attempt 02 executed / remediation applied / reverification required**
- Execution environment: Windows / Python 3.10.6 / pytest 9.1.1

## 1. Attempt 02 results

The operator-boundary and M01 contract suite passed again:

```text
tests/test_p_gui_03r_operator_boundary.py + tests/test_m01_cli.py
17 passed
```

The installed public CLI vertical workflow also passed:

```text
tests/test_m03_standard_workflow.py
2 passed
```

Ruff passed:

```text
python -m ruff check src tests
All checks passed!
```

The full pytest suite executed 794 tests and finished:

```text
770 passed
9 failed
15 errors
```

Therefore Attempt 02 is not a closure PASS.

## 2. Failure classification

### A. P-GUI-03R compatibility regressions — 19 non-passing cases

The transport-neutral CLI cutover removed two historical monkeypatch hooks from
`sgokb.cli.main`:

```text
semantic_runtime
build_read_application
```

This caused:

- 15 setup errors in `tests/test_n04p05_derived_cli.py`;
- 1 failure in `tests/test_generation_lifecycle_r2.py`;
- 1 failure in `tests/test_n04p04_vector_index_sync.py`;
- 2 failures in `tests/test_object_similarity_r2.py`.

The product semantics were not shown to be wrong; the regression was the loss of
an established CLI test/downstream patch seam.

### B. Verification environment incomplete — 3 failures

Three tests reached `frozen_harrier_space()` and failed because the Python
environment did not contain installed `sentence-transformers` distribution
metadata.

Affected tests:

- two cases in `tests/test_n05_r2_runner_wiring.py`;
- one case in `tests/test_n07_r01_composite_recovery.py`.

Attempt 02 installed `dev,mcp,vector-qdrant` but omitted the existing
`local-embedding` extra. This is a verification-environment deficiency, not a
P-GUI-03R behavioral regression.

### C. Historical Phase N closure test coupled to current HEAD — 2 failures

`tests/test_phase_n_closure_audit.py` copied current planning authorities and the
audit compared `HEAD:src` against the Phase N accepted baseline. This assumption
was valid while Phase N was current, but is no longer valid after Phase O/Phase P
legitimately changed documentation and production source.

The historical closure contract itself remains preserved. The test fixture is
therefore pinned to the formal Phase N closure candidate:

```text
fb9b0d6a6f670d1b0f053148769ce8cd448ea217
```

The audit implementation remains fail-closed for current formal use; only the
historical unit fixture is made temporally stable.

## 3. Remediation applied

### CLI compatibility adapter

`src/sgokb/cli/runtime.py` now provides a `_CliCompatibilityRuntimeFactory` that:

- retains the transport-neutral shared `RuntimeFactory`/Application architecture;
- honors monkeypatched `sgokb.cli.main.semantic_runtime` when present;
- honors monkeypatched `sgokb.cli.main.build_read_application` when present;
- otherwise uses the shared local runtime composition;
- preserves generation-aware vector routing through inherited
  `RuntimeFactory.routed_semantic_runtime()`.

`src/sgokb/cli/__init__.py` re-exports the historical hooks onto the
`sgokb.cli.main` module so existing tests/downstream code can patch them.

This is a compatibility shim only; business orchestration is not moved back into
the CLI adapter.

### Historical Phase N test fixture

`tests/test_phase_n_closure_audit.py` now loads its authority fixture from the
formal historical closure candidate rather than the current Phase P working
state. The production closure audit itself is unchanged.

## 4. Remaining environment prerequisite

Before the next full-suite run, install the local embedding extra as well:

```powershell
python -m pip install -e ".[dev,mcp,vector-qdrant,local-embedding]"
```

A dedicated virtual environment is preferred because the global Python used in
Attempt 02 already contained an unrelated FastAPI/Starlette dependency conflict.
That conflict did not prevent the SGOKB tests above from executing but should not
be treated as a clean project environment.

## 5. Attempt 03 verification

After pulling the remediation commit and ensuring the local embedding extra is
installed, run:

```powershell
python -m pytest tests/test_n04p05_derived_cli.py \
  tests/test_generation_lifecycle_r2.py \
  tests/test_n04p04_vector_index_sync.py \
  tests/test_object_similarity_r2.py \
  tests/test_phase_n_closure_audit.py \
  tests/test_n05_r2_runner_wiring.py \
  tests/test_n07_r01_composite_recovery.py

python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

P-GUI-03R remains **Implemented / Dynamic Verification In Progress** until these
checks complete without P-GUI-03R regression.
