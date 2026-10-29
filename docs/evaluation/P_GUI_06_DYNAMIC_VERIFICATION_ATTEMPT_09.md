# P-GUI-06 — Dynamic Verification Attempt 09

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Scope: post-From/To-removal surface plus Search mode / Semantic runtime coupling remediation
- Disposition: **PASS**
- Current role: **Automated verification authority**

## Trigger

Interactive Search smoke after Attempt 08 exposed a contradictory GUI request contract: `mode=semantic` could be submitted with `semantic_runtime=false`. The GUI was amended so Lexical forces runtime OFF, Semantic forces runtime ON, and Hybrid defaults runtime ON while retaining an explicit opt-out.

A Ruff-only E501 failure was then corrected by wrapping tooltip strings; no functional logic changed in that style-only follow-up.

## Measured verification

```text
focused P-GUI regression = 29 / 29 PASS
Ruff                     = PASS
full regression           = 818 / 818 PASS
warnings                  = 2 known local-Qdrant warnings
```

The focused gate includes the Search mode/runtime coupling regression in `tests/test_p_gui_06_search_runtime_state.py`.

The two warnings are the established local-Qdrant warnings:

- payload indexes have no effect in local Qdrant;
- local mode performs exact brute-force search so `search_params` has no effect except `idf`.

They are not test failures.

## Contract verified

Automated coverage now fixes the following GUI request contract:

```text
Lexical
  semantic runtime = OFF / disabled

Semantic
  semantic runtime = ON / disabled
  request construction forces semantic_runtime=true

Hybrid
  semantic runtime = ON by default
  explicit operator opt-out remains available
  require_full_runtime is available only while semantic runtime is enabled
```

The following previously accepted amendments remain in force:

- From/To range controls and range-aware adapters remain removed;
- canonical R2 `HybridObjectSearch` remains the public Search implementation;
- native PyTorch / Transformers / Sentence Transformers preload remains on the Qt main thread before backend QThread creation;
- local-only / no-cloud-fallback policy remains unchanged.

## Current disposition

```text
implementation                     = Complete for current P-GUI-06 scope
automated focused regression       = PASS
static analysis                    = PASS
full regression                    = PASS
interactive Search re-smoke        = Pending
remaining interactive smoke        = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

Attempt 08 is retained as historical evidence for the post-From/To-removal baseline. Attempt 09 supersedes it as current automated authority because it verifies the later Search mode / Semantic runtime coupling remediation.