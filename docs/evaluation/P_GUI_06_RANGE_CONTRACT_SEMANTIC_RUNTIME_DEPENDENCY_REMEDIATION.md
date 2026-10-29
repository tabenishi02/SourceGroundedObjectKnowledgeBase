# P-GUI-06 — Range Contract / Semantic Runtime Dependency Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Automated Verification PASS / Interactive Smoke Pending**
- Current automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md`
- Previous automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md` — historical

## Interactive evidence

After Attempt 05, operator testing still observed:

```text
lexical without From/To -> expected results
lexical with From/To    -> zero results
semantic runtime ON     -> Search failed: [internal/internal_error] name 'nn' is not defined
```

Attempt 05 therefore remains historical automated evidence but did not certify production Workspace/runtime behavior.

## Range root-cause correction

The frozen R2 Search contract in `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md` states:

- Registry lexical is canonical Object identity discovery;
- identity discovery remains possible even without Knowledge;
- `knowledge_valid_at`, `temporal_scope_id`, and `derivation_kind` are Statement-scoped conditions.

The previous remediation still re-qualified Registry identity using Statement temporal eligibility whenever From/To was present. That was a contract error. Adding Statement-less and stale-generation exceptions could not fully repair the wrong boundary.

The corrected boundary is:

```text
From/To only:
  Registry name/alias identity -> not filtered by Statement valid time
  Knowledge lexical Statement  -> temporal overlap filter
  Semantic Statement           -> temporal overlap filter

From/To + Statement-specific Facet/Derivation/Temporal Scope:
  matching Statement remains required for the narrowed scope
```

Updated:

```text
src/sgokb/retrieval/search_range_identity.py
```

A regression verifies that even when every Statement is outside the requested range, an exact Object-name Registry result remains visible while the non-overlapping Statement match is absent.

## Semantic runtime `nn` failure

SGOKB source does not reference `nn`. The failure occurs while constructing the external local embedding stack.

The current local embedding dependency contract is:

```text
torch >=2.6,<3
sentence-transformers >=6.1,<7
transformers >=5.2,<6
```

The remediation also normalizes dependency initialization failures through `RetrievalRuntimeUnavailableError`. The known `name 'nn' is not defined` failure produces actionable PyTorch-upgrade guidance rather than `internal/internal_error`.

Updated:

```text
pyproject.toml
src/sgokb/runtime.py
```

## Operator environment remediation

The operator moved verification to the repository-local SGOKB virtual environment and verified:

```text
Python executable = C:\codex\SourceGroundedObjectKnowledgeBase\.venv\Scripts\python.exe
PyTorch           = 2.6.0+cu124
CUDA runtime      = 12.4
CUDA available    = True
GPU               = NVIDIA GeForce RTX 4090
pip check         = No broken requirements found
```

This removes the unsupported/stale PyTorch condition that produced the external Transformers `nn` failure.

## Regression coverage

Added and verified:

```text
tests/test_p_gui_06_range_contract_runtime_dependency.py
```

Coverage:

1. From/To does not hide exact Registry identity when all Statements are outside the range;
2. non-overlapping Statement matches remain excluded;
3. dependency `NameError("name 'nn' is not defined")` becomes `RetrievalRuntimeUnavailableError` with PyTorch guidance, including the OperatorSession Search path.

The existing range/Qdrant regressions remain part of the focused gate.

## Automated verification

Current authority:

```text
P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_06.md
```

Measured result:

```text
focused regression = 40 / 40 PASS
Ruff               = All checks passed!
full regression    = 829 / 829 PASS
warnings           = 2 known local-Qdrant warnings
```

The warnings are existing local-Qdrant limitations and are not failures.

## Current disposition

```text
range contract root cause          = Corrected / PASS
semantic dependency root cause     = Identified / environment corrected
range remediation                  = Automated PASS
runtime error normalization        = Automated PASS
local-embedding dependency floor   = torch>=2.6,<3
operator environment               = Verified healthy
full regression                    = 829 / 829 PASS
interactive smoke                  = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```

Interactive smoke must now repeat the two original production symptoms before closure:

1. Lexical + From/To Object identity discovery;
2. Semantic runtime ON in the corrected SGOKB `.venv`.
