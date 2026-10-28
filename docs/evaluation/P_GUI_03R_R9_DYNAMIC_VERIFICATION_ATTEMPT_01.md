# P-GUI-03R R9 Dynamic Verification — Attempt 01

Updated: 2026-10-28

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-03R [P0] Transport-neutral Application boundary refactor implementation`
- Slice: `R9 Regression / semantic-equivalence acceptance`
- Disposition: **PARTIAL PASS / ENVIRONMENT REMEDIATION + RUFF REMEDIATION REQUIRED**
- Formal task closure: **Pending**

## 1. Operator-provided execution

The operator executed:

```powershell
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

## 2. Result classification

### V1 — Shared boundary + M01 CLI contract

```text
17 collected
17 passed
```

Disposition: **PASS**

This confirms the new P-GUI-03R operator-boundary tests and existing M01 CLI contract suite pass together on Windows/Python 3.10.6.

### V2 — M03 public CLI vertical slice

The tests did not enter the SGOKB workflow. Fixture setup stopped because `WorkflowCLI` could not find an installed `sgokb` console script:

```text
AssertionError: Install the project editable before CLI integration tests
```

Disposition: **NOT RUN / ENVIRONMENT BLOCKED**

This is not evidence of a P-GUI-03R semantic regression. `test_m03_standard_workflow.py` intentionally exercises the installed public CLI and therefore requires an editable/installed project entry point.

### V3 — Full pytest suite

Collection stopped before test execution because `qdrant_client` was not installed for three existing test modules:

```text
tests/test_n05_performance_workflow.py
tests/test_n05_r2_runner_wiring.py
tests/test_n06_retrieval_vector_quality.py
```

Disposition: **NOT RUN / ENVIRONMENT BLOCKED**

The project defines Qdrant support in the `vector-qdrant` optional dependency. These tests use the Qdrant Python client, including in-memory use, so the client package is required for full-suite collection. The current log does not show a failure to connect to a Qdrant server.

### V4 — Ruff

Initial run reported 23 findings.

Classification:

```text
P-GUI-03R-introduced findings = 4
pre-existing fixture-reexport F811 findings = 19
```

P-GUI-03R findings:

- `application_evidence.py` E501
- `application_exchange.py` E501
- `application_exchange.py` F841
- `application_operator.py` I001/E501 presentation findings

The two pre-existing test modules intentionally import/re-export pytest fixtures under their fixture names, which Ruff interprets as F811 when those names are subsequently used as test parameters.

Remediation applied after Attempt 01:

- reformatted `application_evidence.py`
- reformatted `application_exchange.py`
- removed unused Package manifest assignment
- added narrowly scoped Ruff per-file ignores for the explicit operator dispatch table and the two intentional pytest fixture re-export modules

A clean Ruff result is **not yet claimed** until rerun on the operator environment.

## 3. Required environment preflight for Attempt 02

From repository root, after pulling current `main`:

```powershell
git pull --ff-only
python -m pip install -e ".[dev,mcp,vector-qdrant]"
python -m pip check
Get-Command sgokb
python -c "import qdrant_client; print(qdrant_client.__file__)"
```

Expected:

- `Get-Command sgokb` resolves the console script belonging to the same Python environment.
- `qdrant_client` imports successfully.
- `pip check` reports no broken requirements.

`mcp` is included so the M03 MCP-read half executes rather than being skipped.

## 4. Attempt 02 commands

```powershell
python -m pytest tests/test_p_gui_03r_operator_boundary.py tests/test_m01_cli.py
python -m pytest tests/test_m03_standard_workflow.py
python -m pytest
python -m ruff check src tests
```

If the full suite reaches runtime-dependent tests that require an external service, record that separately from Python-package collection failures. Do not reinterpret such an environment failure as a P-GUI-03R semantic failure without evidence.

## 5. Current acceptance state

```text
R1-R8 implementation                     Implemented
R9 targeted operator/M01 regression       PASS (17/17)
R9 M03 public CLI vertical slice          NOT RUN / environment blocked
R9 full pytest                            NOT RUN / collection environment blocked
R9 ruff                                   remediation applied; rerun required
```

Therefore:

```text
P-GUI-03R = Implemented / Dynamic Verification In Progress
P-GUI-04 canonical backend wiring = still gated
```

No `Complete / Accepted` or full-regression PASS is asserted from Attempt 01.
