# P-GUI-06 — Search / Similarity / Registry / Version GUI Implementation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Smoke Pending**
- Baseline: P-GUI-05 **Complete / Accepted**
- Task authority: `docs/planning/phases/P/PHASE_P_TASKS.md`
- Compatibility authority: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
- Automated verification: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

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
- Primary Class filter;
- Additional Class filter;
- Ancestor Class filter;
- Facet filter;
- Version filter;
- Temporal Scope filter;
- Knowledge-valid-at filter;
- Derivation Kind filter;
- archived Object opt-in;
- ranked result table;
- selected result detail, including match evidence carried by the existing search contract;
- explicit degraded-channel display.

Search does not silently change retrieval semantics. The GUI submits the same `search`
operation arguments as the CLI and keeps the existing runtime/degradation behavior.

If semantic channels are unavailable and the Application returns degradation, the GUI exposes
that state. If strict full-runtime behavior is requested, the existing Application/operator
error remains authoritative.

## 3. Similarity GUI

The `Similarity` tab exposes:

- stable Object selection loaded through `object.list`;
- overall Similarity;
- optional Facet-specific Similarity;
- optional source Version pinning;
- result limit;
- cross-Class opt-in;
- archived Object opt-in;
- ranked result and contribution/evidence detail.

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

No new Version-list storage query was added because the current public operation contract for
P-GUI-06 exposes Version Show and Version Diff, not a separate Version List operation.

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

`MainWindow` now hosts real pages for:

```text
Objects
Sources
Evidence
Associations
Search
Registry
```

The navigation inventory remains the accepted 11 destinations. P-GUI-06 does not add a new
sidebar destination; Version / Diff / Render are grouped under Registry, while Object Search /
Similarity are grouped under Search.

Existing P-GUI-05 shell acceptance was made forward-compatible by checking that its four owned
pages remain present rather than requiring `domain_pages` to contain exactly four entries.

## 9. Automated acceptance coverage

Added:

```text
tests/test_p_gui_06_search_registry_version.py
```

Focused coverage verifies:

1. real Lexical Object Search through the GUI/operator path;
2. Similarity request scope/arguments for Facet, Version, cross-Class, archive and limit;
3. Registry Class and Relation Type browsing;
4. accepted Version Show;
5. accepted Version Diff with structured and Markdown representations;
6. Render / export and generated Markdown preview;
7. separate Registry Proposal accept/reject/apply operation mapping;
8. MainWindow replacement of Search / Registry placeholders.

P-GUI-04 and P-GUI-05 GUI regressions are included because P-GUI-06 extends the shared
MainWindow and `domain_pages` inventory.

## 10. Dynamic verification result

Automated verification was executed by the operator on Windows after updating to the P-GUI-06
implementation baseline.

Measured result:

```text
focused P-GUI-04 / 05 / 06 regression = 16 / 16 PASS
Ruff                                  = All checks passed!
full pytest                            = 811 / 811 PASS
known local-Qdrant warnings            = 2
```

The two warnings are the existing local-Qdrant limitations for payload indexes and brute-force
search parameters. They are not test failures and are not new P-GUI-06 regressions.

Automated authority:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_01.md`

Automated disposition:

```text
P-GUI-06 automated verification = PASS
```

## 11. Interactive smoke acceptance

The remaining acceptance gate is interactive GUI smoke. Run:

```powershell
sgokb-gui
```

Confirm at minimum:

### Search

- Lexical Search returns expected accepted Objects;
- Class / Facet / Version and other hard filters constrain results as expected;
- Semantic / Hybrid requests expose runtime failure or degradation explicitly;
- `Require full runtime` does not silently degrade;
- selected result details render.

### Similarity

- a current accepted Object can be selected;
- overall Similarity executes when semantic runtime is available;
- Facet-specific Similarity preserves the selected Facet scope;
- cross-Class and archived options are explicit;
- runtime-unavailable state remains an explicit failure rather than fallback.

### Registry

- Classes and Relation Types browse/detail work;
- Proposal list/detail works when proposals exist;
- Accept / Reject does not automatically Apply;
- Apply is only offered for accepted, unapplied proposals;
- Apply requires explicit confirmation.

### Version / Diff

- Version Show renders immutable accepted Version content;
- Version Diff renders structured output;
- Markdown Diff renders the same derived comparison in human-readable form.

### Render

- Object or Version render writes to the selected/default derived root;
- generated Markdown preview loads;
- render result path / digest / byte count are visible.

The GUI must remain responsive while backend operations execute.

## 12. Current disposition

```text
implementation       = Complete
desk audit           = Complete
operation wiring     = 14 / 14
automated acceptance = PASS
interactive smoke    = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

P-GUI-06 becomes `Complete / Accepted` only after interactive acceptance evidence is measured
PASS.
