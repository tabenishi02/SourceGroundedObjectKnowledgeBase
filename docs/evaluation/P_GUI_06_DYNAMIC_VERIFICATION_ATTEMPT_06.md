# P-GUI-06 — Dynamic Verification Attempt 06

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Execution source HEAD: `038cfc1115c698db160c2eddb9e80a93ea173da4`
- Verdict: **PASS / CURRENT AUTOMATED AUTHORITY / INTERACTIVE SMOKE PENDING**

## Scope

Attempt 06 verifies the post-Attempt-05 remediation for:

- the frozen R2 From/To Registry-identity boundary;
- local semantic-runtime dependency handling;
- normalization of the Transformers/PyTorch `name 'nn' is not defined` failure;
- all previously accepted P-GUI-04 / P-GUI-05 / P-GUI-06 regression coverage.

The operator environment was first corrected to the SGOKB repository-local virtual environment and verified as:

```text
Python executable = C:\codex\SourceGroundedObjectKnowledgeBase\.venv\Scripts\python.exe
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

## Focused verification

Command set covered:

```text
tests/test_p_gui_03r_operator_boundary.py
tests/test_p_gui_04_optional_boundary.py
tests/test_p_gui_04_shell.py
tests/test_p_gui_05_domain_pages.py
tests/test_p_gui_05_object_class_selector.py
tests/test_p_gui_05_object_class_controls.py
tests/test_p_gui_05_source_recursive_zip_import.py
tests/test_p_gui_06_search_registry_version.py
tests/test_p_gui_06_search_filter_selectors.py
tests/test_p_gui_06_derivation_kind_selector.py
tests/test_p_gui_06_search_runtime_state.py
tests/test_p_gui_06_range_contract_runtime_dependency.py
tests/test_search_validity_range.py
tests/test_search_validity_range_identity.py
tests/test_search_validity_range_qdrant_r2.py
```

Measured result:

```text
platform = win32
Python   = 3.10.6
pytest   = 9.1.1
pluggy   = 1.7.0
collected = 40
result    = 40 passed
warnings  = 2
elapsed   = 6.40 s
```

The two warnings are the known local-Qdrant limitations:

1. payload indexes have no effect in local Qdrant;
2. local mode performs exact brute-force search so `search_params` has no effect except `idf`.

Neither warning is a failure.

The focused gate includes the new three-test remediation module:

```text
tests/test_p_gui_06_range_contract_runtime_dependency.py ... PASS
```

This proves:

- From/To alone does not hide exact Registry identity when Statements do not overlap;
- non-overlapping Statement matches remain excluded;
- semantic-runtime `nn` dependency failure is normalized to the runtime-unavailable boundary through both RuntimeFactory and OperatorSession coverage.

## Static verification

Measured result:

```text
python -m ruff check src tests
All checks passed!
```

## Full regression

Measured result:

```text
collected = 829
result    = 829 passed
warnings  = 2
elapsed   = 220.52 s (0:03:40)
```

No repository regression was observed.

## Disposition

```text
From/To R2 contract correction      = PASS
Registry identity regression        = PASS
Knowledge temporal filtering        = PASS
semantic dependency normalization   = PASS
OperatorSession runtime boundary    = PASS
real Qdrant range-semantic coverage = PASS
Ruff                                = PASS
full regression                     = 829 / 829 PASS
```

Attempt 05 remains historical evidence. Attempt 06 supersedes it as the current automated authority because it verifies the final R2 contract correction and semantic-runtime dependency remediation.

Current task state:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

Interactive acceptance must now re-check the two production symptoms that motivated the remediation:

1. `Mode=lexical` + From/To must retain expected Object-name/alias identity results;
2. `Semantic runtime=ON` must no longer surface `name 'nn' is not defined` in the corrected SGOKB `.venv`.
