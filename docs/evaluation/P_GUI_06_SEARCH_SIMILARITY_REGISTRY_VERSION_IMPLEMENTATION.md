# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Smoke Pending**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Current automated verification: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_02.md`
- Historical pre-amendment verification: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- Current amendment: `docs/evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`

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
- Derivation Kind filter;
- archived Object opt-in;
- ranked result table and selected-result detail;
- explicit degraded-channel display.

Selector composition remains above Repository storage:

```text
registry.class.list
object.list
    -> current_version_id
    -> version.show(current accepted Version)
    -> Facet / Temporal Scope / Version choices
```

Facet / Version / Temporal Scope selectors remain editable because full historical list operations are not part of the current public operator inventory.

### Knowledge validity range

Existing single-date `valid_at` callers remain backward compatible. GUI `From` / `To` values are encoded in that slot using `..` and interpreted as temporal overlap.

Supported forms:

```text
YYYY-MM-DD..YYYY-MM-DD
YYYY-MM-DD..
..YYYY-MM-DD
```

Invalid dates and `From > To` are rejected. `as_of` is treated as a point interval and timeless Statements remain eligible.

Range retrieval is implemented in:

```text
src/sgokb/retrieval/search_range.py
```

The range-aware adapter preserves R2 generation routing and applies equivalent overlap semantics to lexical SQL and semantic Vector filtering, including the pre-cutover compatibility semantic path.

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

Base P-GUI-06 coverage:

```text
tests/test_p_gui_06_search_registry_version.py
```

Selector / validity-range coverage:

```text
tests/test_p_gui_06_search_filter_selectors.py
tests/test_search_validity_range.py
```

The amendment coverage verifies selector population, Object-scoped Similarity choices, GUI From/To request construction, invalid-range rejection, lexical and semantic temporal-overlap semantics, one-sided ranges, pre-cutover semantic filtering, and timeless Statement eligibility.

## 6. Automated verification history

### Attempt 01 — pre-amendment

```text
focused regression = 16 / 16 PASS
Ruff               = PASS
full pytest         = 811 / 811 PASS
warnings            = 2 known local-Qdrant warnings
```

Attempt 01 remains historical evidence for the pre-amendment implementation.

### Attempt 02 — current implementation

After the selector / validity-range amendment, the operator measured:

```text
focused regression = 18 / 18 PASS
Ruff               = All checks passed!
full pytest         = 813 / 813 PASS
warnings            = 2 known local-Qdrant warnings
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_02.md`

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
- `Knowledge valid From` / `To` work for bounded and one-sided ranges;
- Lexical Search returns expected accepted Objects;
- Semantic / Hybrid runtime failure or degradation is explicit;
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
