# P-GUI-03R R9 — Dynamic Verification Attempt 03

Updated: 2026-10-28

- Task: `P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation`
- Slice: `R9 Regression / semantic-equivalence acceptance`
- Status: **Attempt 03 executed / final compatibility remediation applied / reverification required**
- Execution environment: Windows / Python 3.10.6 / pytest 9.1.1

## 1. Attempt 03 results

The environment was expanded with:

```text
dev,mcp,vector-qdrant,local-embedding
```

The remediation-focused suite collected 146 tests and finished:

```text
144 passed
2 failed
2 warnings
```

Both remaining failures were the same compatibility case in
`tests/test_n04p05_derived_cli.py`:

```text
test_composition_failure_exits_runtime_without_changes[error0-status]
test_composition_failure_exits_runtime_without_changes[error0-sync]
```

The shared operator-boundary + M01 suite passed:

```text
18 passed
```

The installed public CLI vertical workflow passed:

```text
2 passed
```

The full suite collected 795 tests and finished:

```text
793 passed
2 failed
2 warnings
```

Ruff found one import-order issue in the newly stabilized historical Phase N test
fixture.

Therefore Attempt 03 is not yet the formal closure PASS.

## 2. Remaining behavioral regression

The two failures both exercise:

```text
system derived status --semantic-runtime
system derived sync --semantic-runtime
```

with the historical CLI seam monkeypatched so `semantic_runtime()` raises a plain
`RuntimeError("local runtime unavailable")`.

Before P-GUI-03R, the CLI `system derived` path wrapped semantic-composition
exceptions as `DerivedMaintenanceRuntimeUnavailableError`, which maps to runtime
failure / CLI exit code 5. The shared `SystemOperatorApplication._derived()` path
was allowing the plain `RuntimeError` to reach the generic operation error mapper,
which classified it as internal / exit code 1.

This is a P-GUI-03R compatibility regression in failure semantics, not a canonical
state or retrieval result mismatch.

## 3. Final compatibility remediation

`SystemOperatorApplication._derived()` now preserves the historical derived
maintenance contract:

- existing `DerivedMaintenanceRuntimeUnavailableError` passes through unchanged;
- any other exception raised while composing the semantic runtime is wrapped as
  `DerivedMaintenanceRuntimeUnavailableError`;
- the shared operation error contract therefore classifies the failure as runtime;
- the CLI adapter maps that category to exit code 5.

The behavior is scoped to derived status/sync semantic-runtime composition. Search,
similarity and index-rebuild error contracts are not broadened by this change.

## 4. Ruff remediation

The import grouping in `tests/test_phase_n_closure_audit.py` was aligned with Ruff's
classification. The historical Phase N fixture semantics remain unchanged.

## 5. Final reverification gate

After pulling current `main`, run:

```powershell
python -m pytest tests/test_n04p05_derived_cli.py tests/test_phase_n_closure_audit.py
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

If all five commands pass, P-GUI-03R can transition to **Complete / Accepted** and
P-GUI-04 backend wiring can be unblocked.
