# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Smoke Pending**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Current automated verification: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`
- Search selector/range authority: `docs/evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`
- Validity-range remediation: `docs/evaluation/P_GUI_06_VALIDITY_RANGE_FALSE_NEGATIVE_REMEDIATION.md`
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
- explicit degraded-channel display.

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

Range retrieval is implemented in:

```text
src/sgokb/retrieval/search_range.py
```

The range-aware adapter preserves R2 generation routing. A false-negative remediation established the final boundary:

```text
Registry name / alias identity eligibility under From/To
    -> canonical accepted Knowledge

Knowledge lexical / semantic matches
    -> active R2 Search generation only
```

This prevents a current accepted Object from disappearing solely because the active derived Search generation lags its current Version, while preserving generation isolation for Knowledge channels.

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
tests/test_search_validity_range.py
```

Coverage verifies Registry/Version/Render wiring, selector population, fixed Derivation Kind choices, Object-scoped Similarity choices, GUI From/To request construction, invalid-range rejection, lexical/semantic temporal overlap, one-sided ranges, timeless Statements, stale-active-generation range remediation, GUI end-to-end range Search, and preservation of generation isolation.

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

All five pytest failures occurred in stale-generation fixture setup before the product assertion, because a direct-SQL generation setup transaction was not committed before beginning a new Version lifecycle operation. Ruff errors were import-order/static-layout defects. Both were remediated; Attempt 03 remains historical evidence.

### Attempt 04 — current authority

After the Derivation Kind selector, validity-range false-negative remediation, and Attempt 03 cleanup, the operator measured:

```text
focused regression = 24 / 24 PASS
Ruff               = All checks passed!
full pytest         = 819 / 819 PASS
warnings            = 2 known local-Qdrant warnings
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_04.md`

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
- the previously observed From/To false-negative no longer occurs for expected Object-name searches;
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
