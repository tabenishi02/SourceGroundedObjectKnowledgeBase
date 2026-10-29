# P-GUI-06 — Interactive Attempt 07 Failure / R2 Identity + GUI Native Preload Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Interactive FAIL / Remediation Implemented / Automated Re-verification Pending**
- Previous automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md`

## Interactive observations

After Attempt 06 automated PASS, the operator re-ran the production GUI from the SGOKB `.venv` and observed:

```text
Lexical + From/To + Object-name search -> NG
Semantic runtime ON                    -> GUI process crashed / forced termination
```

The environment had already been verified as:

```text
PyTorch          = 2.6.0+cu124
CUDA runtime     = 12.4
CUDA available   = True
GPU              = NVIDIA GeForce RTX 4090
pip check        = No broken requirements found
```

Therefore the Attempt 06 automated PASS is historical evidence only and is not closure authority.

## A. Range identity defect still present

The prior implementation moved the From/To boundary toward the frozen R2 contract, but its range-specific Registry path still represented eligibility as `(object_id, version_id)` pairs and only admitted rows whose `version_id` was a non-empty string.

That means an Object with no current accepted Version could be discovered normally by Registry lexical search but disappear only when From/To was supplied.

This still violates the frozen contract:

```text
Registry name / alias identity discovery
    != Statement temporal eligibility
```

### Remediation

`src/sgokb/retrieval/search_range_identity.py` now bypasses range re-qualification completely when the only temporal narrowing is From/To:

```text
From/To only
    -> call Registry row resolution with knowledge_valid_at removed
    -> return canonical Registry rows unchanged
    -> do not require Version identity
    -> do not require Statement identity

From/To + Facet / Derivation Kind / Temporal Scope
    -> retain Statement-specific canonical range qualification
```

This is stronger and simpler than converting Registry rows into range-eligible Version pairs.

## B. Semantic runtime process crash

The Python-level `nn` dependency failure from the previous attempt was corrected, but the operator then observed a process-level GUI crash when Semantic runtime was enabled.

SGOKB currently constructs the semantic runtime lazily from the backend Qt worker thread. On Windows this means the first import/loading of PyTorch / Transformers / Sentence Transformers native components may happen off the main thread.

Recent external Windows reports show that first loading a local embedding/native ML backend from a worker thread can fail below Python's exception boundary; moving the native import to the main thread before worker startup avoids that loader/thread boundary.

### Remediation

Added `preload_local_semantic_native_dependencies()` in `src/sgokb/runtime.py`.

GUI `create_runtime()` now calls it after `QApplication` construction but before `BackendCoordinator` creates/starts its backend `QThread`.

Preload scope:

```text
PyTorch import
Transformers logging import
Sentence Transformers import
CUDA driver availability probe
Transformers/HF progress bars disabled for GUI runtime
```

The model itself is still constructed lazily in the backend lane; startup does not allocate the Harrier model.

Ordinary optional-dependency errors are cached and later surfaced as `RetrievalRuntimeUnavailableError`, so a missing semantic extra does not prevent lexical-only GUI startup.

CLI composition remains lazy and unchanged.

## Regression additions

Updated:

```text
tests/test_p_gui_06_range_contract_runtime_dependency.py
tests/test_p_gui_04_shell.py
```

New coverage proves:

1. production `KnowledgeReadApplication` + active R2 generation keeps an unversioned Object's exact Registry identity under From/To;
2. GUI semantic native preload is invoked before `BackendCoordinator` starts the backend QThread.

Existing Attempt 06 coverage remains relevant for accepted-Version range identity, runtime error normalization, real Qdrant range semantics, and GUI request state.

## Current disposition

```text
Attempt 06 automated gate           = Historical PASS
Attempt 07 interactive From/To      = FAIL
Attempt 07 interactive semantic GUI = CRASH
R2 unversioned identity defect      = Remediated
GUI native first-load boundary      = Remediated / verification pending
automated re-verification           = Pending
interactive re-smoke                = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
