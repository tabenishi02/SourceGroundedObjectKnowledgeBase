# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Smoke Pending**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Current automated verification: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md`
- Current range/runtime remediation: `docs/evaluation/P_GUI_06_RANGE_CONTRACT_SEMANTIC_RUNTIME_DEPENDENCY_REMEDIATION.md`
- Search selector/range authority: `docs/evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`
- Historical first validity-range remediation: `docs/evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`
- Historical range identity / GUI runtime-state remediation: `docs/evaluation/P_GUI_06_RANGE_IDENTITY_RUNTIME_STATE_REMEDIATION.md`
- Derivation selector amendment: `docs/evaluation/P_GUI_06_DERIVATION_KIND_SELECTOR_IMPROVEMENT.md`

## 1. Result summary

P-GUI-06 replaces the accepted shell placeholders for `Search` and `Registry` with real operator-backed GUI surfaces.

Operation wiring remains:

```text
Search       1 / 1
Similarity   1 / 1
Registry     9 / 9
Version      2 / 2
Render       1 / 1
------------------
Total       14 / 14
```

All operations continue through the accepted transport-neutral boundary:

```text
Qt page
  -> GuiOperationRequest
  -> BackendCoordinator / BackendWorker
  -> OperatorSession
  -> Application / Service layer
  -> Repository / Retrieval / Rendering
```

No GUI direct SQL path or CLI-subprocess business path was introduced.

## 2. Search GUI

Implemented in:

```text
src/sgokb/gui/views/search_page.py
src/sgokb/gui/views/search_page_derivation.py
```

The `Search` tab exposes:

- Lexical / Semantic / Hybrid modes;
- local semantic-runtime opt-in;
- `require_full_runtime` strict-mode control;
- result and candidate limits;
- Registry-backed dropdowns for Primary / Additional / Ancestor Class;
- Facet selector with editable historical fallback;
- Version selector with editable historical fallback;
- Temporal Scope selector with editable historical fallback;
- `Knowledge valid From` / `Knowledge valid To` range fields;
- fixed-value Derivation Kind selector (`Any`, `direct_statement`, `synthesis`, `interpretation`, `reported_view`);
- archived Object opt-in;
- ranked result table and selected-result detail;
- explicit degraded-channel display;
- per-request runtime-state reset so failed semantic/runtime requests cannot leave stale prior results/degradation text visible.

Selector composition remains above Repository storage:

```text
registry.class.list
object.list
    -> current_version_id
    -> version.show(current accepted Version)
    -> Facet / Temporal Scope / Version choices
```

Facet / Version / Temporal Scope selectors remain editable because full historical list operations are not part of the current public operator inventory. Derivation Kind is non-editable because its vocabulary is fixed by the schema.

### Knowledge validity range

Existing single-date `valid_at` callers remain backward compatible. GUI `From` / `To` values are encoded in that slot using `..` and interpreted as temporal overlap.

Supported forms:

```text
YYYY-MM-DD..YYYY-MM-DD
YYYY-MM-DD..
..YYYY-MM-DD
```

Invalid dates and `From > To` are rejected. `as_of` is treated as a point interval and timeless Statements remain eligible.

Range retrieval is implemented through:

```text
src/sgokb/retrieval/search_range.py
src/sgokb/retrieval/search_range_identity.py
```

The frozen R2 contract defines the final boundary:

```text
Registry name / alias identity
    -> canonical identity discovery
    -> From/To alone does not remove the identity result

Knowledge lexical Statement channel
    -> From/To temporal-overlap filter

Semantic Statement channel
    -> From/To temporal-overlap filter
```

`knowledge_valid_at`, `temporal_scope_id`, and `derivation_kind` remain Statement-scoped conditions. Facet / Derivation / Temporal Scope combinations therefore still require a matching Statement where their narrowed semantics apply.

Earlier stale-generation and Statement-less exception-based remediations remain historical evidence. The final implementation corrects the underlying identity-vs-Statement contract boundary directly.

### Local semantic runtime dependency

The local embedding profile declares:

```text
torch>=2.6,<3
sentence-transformers>=6.1,<7
transformers>=5.2,<6
```

Dependency initialization failures are normalized to `RetrievalRuntimeUnavailableError`. The known external Transformers failure `name 'nn' is not defined` is reported as a runtime dependency problem with PyTorch guidance rather than `internal/internal_error`.

The verified operator environment for Attempt 06 is:

```text
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

## 3. Similarity GUI

The `Similarity` tab exposes:

- stable Object selection through `object.list`;
- overall Similarity;
- Object-scoped Facet selector with editable historical fallback;
- Object-scoped source Version selector with editable historical fallback;
- result limit;
- cross-Class opt-in;
- archived Object opt-in;
- ranked result and evidence/contribution detail.

Similarity keeps its existing operation contract: Object / optional Facet / optional source Version / cross-Class / archived scope. Search-only Class and Temporal-Scope filter semantics were not added.

Similarity continues to require the configured local Embedding Space and Vector Index. There is no silent lexical or cloud fallback.

## 4. Registry GUI

The `Registry` page contains:

```text
Classes
Relation Types
Proposals
Versions / Diff
Render
```

### Classes / Relation Types

Both are read-only Registry browse/detail surfaces using existing public operations.

### Proposals

Proposal review preserves the critical boundary:

```text
Accept / Reject = review decision
Apply           = separate canonical mutation
```

Apply is offered only for accepted unapplied proposals and requires explicit confirmation.

### Versions / Diff

The page supports accepted Version Show and Before / After Version Diff, including structured and Markdown representations. Diff is derived/read-only and does not mutate immutable accepted Versions.

### Render

The page renders current Object Knowledge or an explicit Version to derived Markdown, exposes path/digest/byte metadata, and previews the generated artifact. Render output is not a canonical write surface.

The user request that introduced the Search selector amendment contained an unfinished bullet beginning `Registryタブの`; no unspecified Registry change was inferred.

## 5. Automated acceptance coverage

P-GUI-06 coverage now includes:

```text
tests/test_p_gui_06_search_registry_version.py
tests/test_p_gui_06_search_filter_selectors.py
tests/test_p_gui_06_derivation_kind_selector.py
tests/test_p_gui_06_search_runtime_state.py
tests/test_p_gui_06_range_contract_runtime_dependency.py
tests/test_search_validity_range.py
tests/test_search_validity_range_identity.py
tests/test_search_validity_range_qdrant_r2.py
```

Coverage verifies Registry/Version/Render wiring, selector population, fixed Derivation Kind choices, Object-scoped Similarity choices, GUI From/To request construction, invalid-range rejection, lexical/semantic temporal overlap, one-sided ranges, timeless Statements, Registry identity preservation under non-overlapping From/To, GUI runtime-state reset/failure presentation, runtime dependency normalization, OperatorSession error boundary behavior, GUI end-to-end range Search, real Qdrant + R2 range-semantic execution, and preservation of generation isolation.

## 6. Automated verification history

### Attempt 01 — pre-amendment

```text
focused regression = 16 / 16 PASS
Ruff               = PASS
full pytest         = 811 / 811 PASS
warnings            = 2 known local-Qdrant warnings
```

### Attempt 02 — selector/range baseline

```text
focused regression = 18 / 18 PASS
Ruff               = PASS
full pytest         = 813 / 813 PASS
warnings            = 2 known local-Qdrant warnings
```

### Attempt 03 — historical verification-harness failure

```text
focused regression = 19 passed / 5 failed
Ruff               = 7 errors
```

All five pytest failures occurred in stale-generation fixture setup before the product assertion. Ruff errors were import-order/static-layout defects. Both were remediated; Attempt 03 remains historical evidence.

### Attempt 04 — post first-range-remediation PASS

```text
focused regression = 24 / 24 PASS
Ruff               = All checks passed!
full pytest         = 819 / 819 PASS
warnings            = 2 known local-Qdrant warnings
```

Interactive testing after Attempt 04 exposed additional range identity and stale Search runtime presentation defects.

### Attempt 05 — historical PASS before final contract/runtime correction

```text
focused regression = 31 / 31 PASS
Ruff               = All checks passed!
full pytest         = 826 / 826 PASS
warnings            = 2 known local-Qdrant warnings
```

Interactive testing after Attempt 05 proved that From/To still hid Registry identity and that Semantic runtime surfaced `name 'nn' is not defined` in the operator environment. Attempt 05 therefore remains historical automated evidence only.

### Attempt 06 — current authority

After correcting the frozen R2 Registry/Statement temporal boundary, adding the PyTorch dependency floor and runtime normalization, and correcting the operator `.venv`, the operator measured:

```text
focused regression = 40 / 40 PASS
Ruff               = All checks passed!
full pytest         = 829 / 829 PASS
warnings            = 2 known local-Qdrant warnings
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md`
- `docs/evaluation/P_GUI_06_RANGE_CONTRACT_SEMANTIC_RUNTIME_DEPENDENCY_REMEDIATION.md`

Automated disposition:

```text
P-GUI-06 automated verification = PASS
```

## 7. Interactive smoke acceptance

Interactive smoke remains the final gate. Confirm at minimum:

### Search

- Class selectors expose Registry choices;
- Facet / Version / Temporal Scope selectors expose expected current accepted choices;
- historical values can be typed where the selector is editable;
- Derivation Kind exposes only the schema-defined fixed values plus `Any`;
- `Knowledge valid From` / `To` work for bounded and one-sided ranges;
- Object-name/alias Registry identity remains visible when From/To excludes all Statement valid times;
- Lexical Search returns expected accepted Objects;
- Semantic runtime ON does not reproduce the prior `name 'nn' is not defined` failure in the verified `.venv`;
- Semantic / Hybrid runtime failure or degradation is explicit and reflects the current request rather than stale presentation;
- `Require full runtime` does not silently degrade;
- result details render correctly.

### Similarity

- a current accepted Object can be selected;
- Facet and Version selectors update for that Object;
- leaving Version unspecified means current accepted Version;
- overall / Facet-specific Similarity preserves requested scope;
- runtime-unavailable state remains explicit rather than falling back.

### Registry / Version / Render

- Classes and Relation Types browse/detail work;
- Proposal Accept / Reject remains separate from Apply;
- Version Show / Diff render correctly;
- Object/Version Render writes and previews derived Markdown.

The GUI must remain responsive while backend operations execute.

## 8. Current disposition

```text
implementation         = Complete
desk audit             = Complete
operation wiring       = 14 / 14
automated acceptance   = PASS
interactive smoke      = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

P-GUI-06 becomes `Complete / Accepted` only after interactive acceptance is measured PASS.
