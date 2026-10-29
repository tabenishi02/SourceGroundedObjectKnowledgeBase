# P-GUI-06 — Dynamic Verification Attempt 07

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Re-smoke Pending**
- Execution source before documentation-only commits: `89f2e7b879f6a7b6f3fec203f1c8cd2e3c4f516f`
- Interactive remediation authority: `P_GUI_06_INTERACTIVE_ATTEMPT_07_FAILURE_AND_REMEDIATION.md`

## Scope

Attempt 07 verifies the two remediations introduced after the production GUI still failed following Attempt 06:

1. From/To alone must not re-qualify Registry identity through Version/Statement existence;
2. GUI semantic native dependencies must be preloaded on the Qt main thread before the backend QThread starts.

The focused gate also re-runs the accepted P-GUI-03R / 04 / 05 / 06 regression set, the prior From/To range tests, GUI runtime-state tests, and the real local-Qdrant + R2 range-semantic regression.

## Operator environment

```text
platform = win32
Python   = 3.10.6
pytest   = 9.1.1
```

The SGOKB `.venv` had already been verified before this run as:

```text
PyTorch          = 2.6.0+cu124
CUDA runtime     = 12.4
CUDA available   = True
GPU              = NVIDIA GeForce RTX 4090
pip check        = No broken requirements found
```

## Focused verification

Measured result:

```text
collected = 42
passed    = 42
warnings  = 2 known local-Qdrant warnings
elapsed   = 6.17s
```

The focused set includes:

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

New Attempt 07 coverage proves:

- production `KnowledgeReadApplication` + active R2 generation preserves an unversioned Object's exact Registry identity under From/To;
- GUI semantic native preload occurs before `BackendCoordinator` starts its backend QThread.

## Static verification

```text
python -m ruff check src tests
All checks passed!
```

## Full regression

Measured result:

```text
collected = 831
passed    = 831
warnings  = 2 known local-Qdrant warnings
elapsed   = 210.06s (0:03:30)
```

The warnings are the existing local-Qdrant limitations:

1. payload indexes have no effect in local Qdrant mode;
2. local mode performs exact brute-force search, so `search_params` has no effect except `idf`.

They are not product failures.

## Attempt history

```text
Attempt 01 = PASS, pre-amendment
Attempt 02 = PASS, selector/range baseline
Attempt 03 = FAIL, fixture + Ruff defects; product assertion not reached
Attempt 04 = PASS, first validity-range remediation
Attempt 05 = PASS, range identity/runtime-state/Qdrant regression set
interactive after Attempt 05 = FAIL
Attempt 06 = PASS, contract/runtime dependency remediation
interactive after Attempt 06 = FAIL / GUI crash
Attempt 07 = PASS, unversioned identity + GUI native-preload remediation
```

Attempt 06 remains valid historical automated evidence but is superseded because production GUI testing afterward exposed two additional defects.

## Disposition

```text
implementation amendment        = Complete
focused regression              = 42 / 42 PASS
Ruff                            = PASS
full regression                 = 831 / 831 PASS
known local-Qdrant warnings     = 2
From/To production-path coverage= PASS
GUI native-preload ordering     = PASS
interactive re-smoke            = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

P-GUI-06 is not `Complete / Accepted` until the operator re-runs the production GUI and confirms the previously failing From/To and Semantic-runtime cases, followed by the remaining Search / Similarity / Registry / Version / Render smoke.
