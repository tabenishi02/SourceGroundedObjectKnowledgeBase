# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Complete / Accepted**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Current amendments:
  - `docs/evaluation/P_GUI_06_FROM_TO_FILTER_REMOVAL.md`
  - `docs/evaluation/P_GUI_06_SEMANTIC_RUNTIME_MODE_COUPLING_REMEDIATION.md`
- Final automated authority: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`
- Final interactive authority: `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`
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

The accepted Search surface exposes:

- Lexical / Semantic / Hybrid modes;
- mode-coupled local Semantic runtime control;
- `require_full_runtime` strict-mode control for Hybrid;
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

### Search mode / Semantic runtime contract

Interactive smoke after Attempt 08 exposed that Search mode and `Semantic runtime` were independently selectable. This admitted contradictory requests such as `mode=semantic` with `semantic_runtime=false`, which necessarily failed because no EmbeddingProvider or VectorIndexAdapter was constructed.

The accepted GUI contract is:

```text
Lexical  -> semantic runtime OFF / disabled
Semantic -> semantic runtime ON / disabled
Hybrid   -> semantic runtime ON by default; explicit operator opt-out remains available
```

`run_search()` also forces the request contract defensively:

```text
mode=semantic -> semantic_runtime=true
mode=lexical  -> semantic_runtime=false
mode=hybrid   -> semantic_runtime=<Hybrid checkbox state>
```

Pure Semantic therefore cannot be submitted without its runtime, while Hybrid can still be deliberately degraded to lexical-only behavior.

### From/To date filter — removed

The experimental P-GUI-06 `Knowledge valid From` / `Knowledge valid To` range filter was removed by operator decision.

```text
From field                    = not exposed
To field                      = not exposed
GUI valid_at="FROM..TO"       = not emitted
range-aware Search adapter    = removed
```

The removal does **not** delete canonical temporal-scope data and does **not** remove the pre-existing non-GUI single-point `knowledge_valid_at` / `valid_at` contract.

Current public retrieval resolves directly to the canonical R2 implementation in `src/sgokb/retrieval/hybrid_search_r2.py`.

## 3. Local semantic runtime and GUI preload

The local embedding profile declares:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

Dependency initialization failures are normalized to `RetrievalRuntimeUnavailableError`. The external Transformers `name 'nn' is not defined` failure is reported as a runtime dependency problem rather than `internal/internal_error`.

Verified operator environment:

```text
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

GUI startup preloads the native ML stack on the Qt main thread before the backend QThread is created. The Harrier model itself remains lazy.

## 4. Similarity GUI

The Similarity tab exposes stable Object selection, overall / Facet-specific Similarity, Object-scoped Facet and source Version selectors, result limit, cross-Class and archived opt-ins, and ranked detail. Similarity requires the configured local Embedding Space and Vector Index; there is no silent lexical or cloud fallback.

## 5. Registry / Version / Render GUI

The Registry page contains Classes, Relation Types, Proposals, Versions / Diff, and Render. Proposal Accept / Reject remains separate from Apply. Version Show/Diff is read-only over immutable accepted Versions. Render creates derived Markdown and is not a canonical write surface.

## 6. Automated coverage

Current P-GUI-06 coverage includes:

```text
tests/test_p_gui_06_search_registry_version.py
tests/test_p_gui_06_search_filter_selectors.py
tests/test_p_gui_06_derivation_kind_selector.py
tests/test_p_gui_06_search_runtime_state.py
tests/test_p_gui_06_runtime_dependency.py
```

`test_p_gui_06_search_runtime_state.py` locks the Search mode / Semantic runtime coupling contract. `tests/test_p_gui_04_shell.py` retains GUI semantic-native preload ordering coverage.

## 7. Verification history

```text
Attempt 01 = 16 / 16 focused PASS, 811 / 811 full PASS
Attempt 02 = 18 / 18 focused PASS, 813 / 813 full PASS
Attempt 03 = fixture/static verification failure
Attempt 04 = 24 / 24 focused PASS, 819 / 819 full PASS
Attempt 05 = 31 / 31 focused PASS, 826 / 826 full PASS
Attempt 06 = 40 / 40 focused PASS, 829 / 829 full PASS
Attempt 07 = 42 / 42 focused PASS, 831 / 831 full PASS — historical pre-removal surface
Attempt 08 = 28 / 28 focused PASS, Ruff PASS, 817 / 817 full PASS — historical post-removal baseline
Attempt 09 = 29 / 29 focused PASS, Ruff PASS, 818 / 818 full PASS — final automated authority
```

Attempt 09 verifies the Search mode / Semantic runtime coupling remediation. The two full-regression warnings are the known local-Qdrant warnings and are not failures.

## 8. Interactive acceptance

Final interactive verification confirmed that the previously reported Semantic / Hybrid Search problems were resolved and that the functions exercised in the acceptance scope showed no remaining problem.

The interactive record intentionally reflects the verified scope rather than claiming exhaustive manual coverage beyond it. Attempt 09 supplies the broader automated regression evidence.

Final interactive authority:

- `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`

## 9. Final disposition

```text
implementation                         = Complete
From/To GUI range filter                = removed
semantic native preload                 = Accepted
Search mode / Semantic runtime coupling = Accepted
operation wiring                        = 14 / 14
automated verification                  = PASS
interactive smoke                       = PASS
```

Therefore:

```text
P-GUI-06 = Complete / Accepted
```

Next:

```text
P-GUI-07 — Progress / error / safety / audit UX
```
