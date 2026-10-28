# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification Refresh Pending / Interactive Smoke Pending**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Pre-amendment automated verification: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- Current amendment: `docs/evaluation/P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`

## 1. Result summary

P-GUI-06 replaces the accepted shell placeholders for `Search` and `Registry` with real
operator-backed GUI surfaces.

The implementation covers the 14 existing public operations assigned to this task:

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
- result limit and candidate limit;
- left-side hard-filter panel;
- Registry-backed dropdowns for Primary / Additional / Ancestor Class;
- Facet selector with editable historical fallback;
- Version selector with editable historical fallback;
- Temporal Scope selector with editable historical fallback;
- Knowledge validity `From` / `To` range;
- Derivation Kind filter;
- archived Object opt-in;
- ranked result table;
- selected result detail, including match evidence carried by the existing search contract;
- explicit degraded-channel display.

Class choices are loaded through `registry.class.list`. Current accepted Version IDs are loaded
from `object.list`, and `version.show` supplies current accepted Facet and Temporal Scope choices.
The GUI does not query SQLite directly for selector data.

Facet / Version / Temporal Scope selectors are editable because the current public operation
inventory does not expose full historical list operations for these entities. Operators can
therefore type a known historical value that is not present in the automatically loaded current
candidate set.

### Knowledge validity range

The old single-date `valid_at` contract remains backward compatible. GUI `From` / `To` values are
encoded in that slot using `..` and interpreted as temporal overlap. Bounded and one-sided ranges
are supported. Invalid dates and `From > To` are rejected. Timeless Statements remain eligible,
consistent with the previous point-in-time behavior.

Range retrieval is implemented in:

```text
src/sgokb/retrieval/search_range.py
```

The range-aware adapter preserves R2 generation routing and applies consistent overlap intent to
lexical SQL and semantic Vector candidate filtering.

Search does not silently change runtime/degradation semantics. If semantic channels are
unavailable and the Application returns degradation, the GUI exposes it. If strict full-runtime
behavior is requested, the existing Application/operator error remains authoritative.

## 3. Similarity GUI

The `Similarity` tab exposes:

- stable Object selection loaded through `object.list`;
- overall Similarity;
- Object-scoped Facet dropdown with editable historical fallback;
- Object-scoped source Version dropdown with editable historical fallback;
- result limit;
- cross-Class opt-in;
- archived Object opt-in;
- ranked result and contribution/evidence detail.

Similarity itself keeps the existing operation contract: Object / optional Facet / optional source
Version / cross-Class / archived scope. Search-only Class and Temporal-Scope filter semantics were
not added to Similarity.

The GUI states that Similarity requires the configured local Embedding Space and Vector Index.
There is no silent lexical fallback and no cloud fallback.

## 4. Registry browse GUI

Implemented in:

```text
src/sgokb/gui/views/registry_page.py
```

The `Registry` page contains dedicated tabs for:

```text
Classes
Relation Types
Proposals
Versions / Diff
Render
```

### Classes

- `registry.class.list`
- selection-driven `registry.class.show`
- registry IDs / keys / names / policy / status visible

### Relation Types

- `registry.relation-type.list`
- selection-driven `registry.relation-type.show`
- registry IDs / keys / names / descriptions / status visible

Both are read-only browse surfaces in P-GUI-06.

The latest user request contained an unfinished bullet beginning `Registryタブの`. No Registry
change was inferred from that incomplete fragment.

## 5. Registry Proposal review / mutation boundary

Proposal UI supports:

- list with All / Pending / Accepted / Rejected filter;
- selected Proposal detail / rationale / payload / evidence / review state;
- explicit Accept action with optional review note;
- explicit Reject action with optional review note;
- explicit Apply action only after an accepted decision;
- Apply confirmation before canonical mutation;
- applied Proposal buttons disabled from normal GUI flow.

The critical semantic boundary is preserved:

```text
Accept / Reject = review decision
Apply           = separate canonical mutation
```

The GUI never treats Accept as Apply. The storage/Application layer remains responsible for
accepted-before-apply and applied-decision immutability rules.

## 6. Version show / diff

The `Versions / Diff` tab supports:

- `version.show` for an explicitly identified accepted Version;
- `version.diff` between explicit Before / After Version IDs;
- structured JSON-compatible detail;
- Markdown Diff preview using the existing `DiffReviewMarkdownRenderer`.

The Markdown view is a derived read-only comparison and does not mutate immutable accepted
Versions.

## 7. Render preview / export

The `Render` tab supports:

- render current accepted Knowledge by Object ID;
- render an explicit accepted Version ID;
- default managed render root or operator-selected output root;
- result metadata display;
- preview of the generated Markdown artifact.

The canonical render operation remains `render`; GUI preview reads only the generated derived
artifact identified by its returned `output_path`. Editing the generated file is not a canonical
write path.

## 8. Main-window integration

`MainWindow` hosts real pages for:

```text
Objects
Sources
Evidence
Associations
Search
Registry
```

The navigation inventory remains the accepted 11 destinations. Version / Diff / Render are
grouped under Registry, while Object Search / Similarity are grouped under Search.

## 9. Automated acceptance coverage

P-GUI-06 base coverage:

```text
tests/test_p_gui_06_search_registry_version.py
```

Selector / validity-range amendment coverage:

```text
tests/test_p_gui_06_search_filter_selectors.py
tests/test_search_validity_range.py
```

The new coverage verifies selector population, Object-scoped Similarity choices, GUI From/To
request construction, invalid-range rejection, bounded/open temporal overlap, and timeless
Statement eligibility.

## 10. Automated verification history and current gate

The operator measured the following PASS before the selector/range amendment:

```text
focused P-GUI-04 / 05 / 06 regression = 16 / 16 PASS
Ruff                                  = All checks passed!
full pytest                            = 811 / 811 PASS
known local-Qdrant warnings            = 2
```

Authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

Those results remain valid historical evidence for the pre-amendment P-GUI-06 implementation,
but they do not certify the code changed by `P_GUI_06_SEARCH_FILTER_SELECTOR_RANGE_IMPROVEMENT.md`.
A focused / Ruff / full-regression refresh is required.

## 11. Interactive smoke acceptance

Interactive smoke remains pending. After the refreshed automated gates pass, confirm at minimum:

### Search

- Class selectors expose Registry choices;
- Facet / Version / Temporal Scope selectors expose expected current accepted choices;
- known historical values can still be typed in editable selectors;
- `Knowledge valid From` / `To` work for bounded and one-sided ranges;
- Lexical Search returns expected accepted Objects;
- Semantic / Hybrid requests expose runtime failure or degradation explicitly;
- `Require full runtime` does not silently degrade;
- selected result details render.

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

## 12. Current disposition

```text
implementation                 = Complete
desk audit                     = Complete
operation wiring               = 14 / 14
pre-amendment automated gate   = PASS
automated verification refresh = Pending
interactive smoke              = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```

P-GUI-06 becomes `Complete / Accepted` only after the refreshed automated gate and interactive
acceptance are measured PASS.
