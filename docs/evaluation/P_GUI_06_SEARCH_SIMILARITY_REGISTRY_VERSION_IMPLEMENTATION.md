# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Smoke Pending**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Current amendment: `docs/evaluation/P_GUI_06_FROM_TO_FILTER_REMOVAL.md`
- Current automated authority: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_08.md`
- Semantic crash remediation: `docs/evaluation/P_GUI_06_INTERACTIVE_ATTEMPT_07_FAILURE_AND_REMEDIATION.md`

## 1. Result summary

P-GUI-06 replaces the Search and Registry placeholders with operator-backed GUI surfaces.

```text
Search       1 / 1
Similarity   1 / 1
Registry     9 / 9
Version      2 / 2
Render       1 / 1
------------------
Total       14 / 14
```

The accepted transport-neutral boundary remains:

```text
Qt page
  -> GuiOperationRequest
  -> BackendCoordinator / BackendWorker
  -> OperatorSession
  -> Application / Service layer
  -> Repository / Retrieval / Rendering
```

No GUI direct SQL path or CLI-subprocess business path is used.

## 2. Search GUI

Implemented in:

```text
src/sgokb/gui/views/search_page.py
src/sgokb/gui/views/search_page_derivation.py
```

The current Search surface exposes:

- Lexical / Semantic / Hybrid modes;
- local Semantic runtime opt-in;
- `require_full_runtime` strict-mode control;
- result and candidate limits;
- Registry-backed Primary / Additional / Ancestor Class selectors;
- Facet selector with editable historical fallback;
- Version selector with editable historical fallback;
- Temporal Scope selector with editable historical fallback;
- fixed Derivation Kind selector (`Any`, `direct_statement`, `synthesis`, `interpretation`, `reported_view`);
- archived Object opt-in;
- ranked result table and selected-result detail;
- explicit degraded-channel display;
- per-request runtime-state reset.

### From/To date filter — removed

The experimental P-GUI-06 `Knowledge valid From` / `Knowledge valid To` range filter has been removed by operator decision.

Current GUI contract:

```text
From field                    = not exposed
To field                      = not exposed
GUI valid_at="FROM..TO"       = not emitted
range-aware Search adapter    = removed
```

The removal does **not** delete canonical temporal-scope data and does **not** remove the pre-existing non-GUI single-point `knowledge_valid_at` / `valid_at` contract.

Current public retrieval therefore resolves directly to the canonical R2 implementation:

```text
src/sgokb/retrieval/hybrid_search_r2.py
```

Historical range work remains documented for audit only and is not current behavior authority.

## 3. Local semantic runtime and GUI preload

The local embedding profile declares:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

Dependency initialization failures are normalized to `RetrievalRuntimeUnavailableError`. The external Transformers `name 'nn' is not defined` failure is reported as a runtime dependency problem rather than `internal/internal_error`.

Verified operator environment before the latest UI amendment:

```text
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

GUI startup preloads the native ML stack on the Qt main thread before the backend QThread is created:

```text
QApplication
    -> preload PyTorch / Transformers / Sentence Transformers native imports
    -> CUDA availability probe
    -> BackendCoordinator / backend QThread
```

The Harrier model itself remains lazy. This remediation is retained after From/To removal.

## 4. Similarity GUI

The Similarity tab exposes:

- stable Object selection through `object.list`;
- overall Similarity;
- Object-scoped Facet selector;
- Object-scoped source Version selector;
- result limit;
- cross-Class opt-in;
- archived Object opt-in;
- ranked result/evidence detail.

Similarity continues to require the configured local Embedding Space and Vector Index. There is no silent lexical or cloud fallback.

## 5. Registry / Version / Render GUI

The Registry page contains:

```text
Classes
Relation Types
Proposals
Versions / Diff
Render
```

Proposal review preserves the safety boundary:

```text
Accept / Reject = review decision
Apply           = separate canonical mutation
```

Version Show/Diff is read-only over immutable accepted Versions. Render creates derived Markdown and is not a canonical write surface.

## 6. Current automated coverage

Current P-GUI-06 coverage after From/To removal includes:

```text
tests/test_p_gui_06_search_registry_version.py
tests/test_p_gui_06_search_filter_selectors.py
tests/test_p_gui_06_derivation_kind_selector.py
tests/test_p_gui_06_search_runtime_state.py
tests/test_p_gui_06_runtime_dependency.py
```

`tests/test_p_gui_04_shell.py` retains GUI semantic-native preload ordering coverage.

The selector test verifies that the retired From/To compatibility widgets are hidden/disabled and cannot emit a `valid_at` argument even if assigned programmatically.

Removed range-only coverage:

```text
tests/test_search_validity_range.py
tests/test_search_validity_range_identity.py
tests/test_search_validity_range_qdrant_r2.py
tests/test_p_gui_06_range_contract_runtime_dependency.py
```

The last module's semantic dependency checks were preserved in `test_p_gui_06_runtime_dependency.py`.

## 7. Verification history

```text
Attempt 01 = 16 / 16 focused PASS, 811 / 811 full PASS
Attempt 02 = 18 / 18 focused PASS, 813 / 813 full PASS
Attempt 03 = fixture/static verification failure
Attempt 04 = 24 / 24 focused PASS, 819 / 819 full PASS
Attempt 05 = 31 / 31 focused PASS, 826 / 826 full PASS
Attempt 06 = 40 / 40 focused PASS, 829 / 829 full PASS
Attempt 07 = 42 / 42 focused PASS, 831 / 831 full PASS — historical pre-removal surface
Attempt 08 = 28 / 28 focused PASS, Ruff PASS, 817 / 817 full PASS — current post-removal authority
```

Attempt 08 verifies the reduced product surface after the From/To controls, range-aware adapters, and range-specific tests were removed.

The two warnings in the full regression are the known local-Qdrant warnings about payload indexes and brute-force search parameters; they are not failures.

## 8. Interactive smoke acceptance

Automated verification is complete. Confirm at minimum:

### Search

- From/To controls are absent from the operator surface;
- Class / Facet / Version / Temporal Scope / Derivation selectors remain usable;
- Lexical Search returns expected Objects;
- Semantic runtime ON does not crash the GUI process;
- Semantic / Hybrid degradation and runtime failures remain explicit;
- `Require full runtime` does not silently degrade;
- result details render correctly.

### Similarity

- current accepted Object selection works;
- Facet and Version selectors update for that Object;
- overall / Facet-specific Similarity preserves requested scope;
- runtime-unavailable state remains explicit.

### Registry / Version / Render

- Classes and Relation Types browse/detail work;
- Proposal Accept / Reject remains separate from Apply;
- Version Show / Diff render correctly;
- Object/Version Render writes and previews derived Markdown.

## 9. Current disposition

```text
implementation                     = amended
From/To GUI range filter            = removed
canonical R2 Search                 = restored directly
semantic runtime crash remediation  = retained
operation wiring                    = 14 / 14
automated verification              = PASS
interactive smoke                   = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```
