# P-GUI-06 — Range Contract / Semantic Runtime Dependency Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Remediation Implemented / Automated Verification Refresh Pending / Interactive Smoke Pending**
- Previous automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_05.md`

## Interactive evidence

After Attempt 05, operator testing still observed:

```text
lexical without From/To -> expected results
lexical with From/To    -> zero results
semantic runtime ON     -> Search failed: [internal/internal_error] name 'nn' is not defined
```

Therefore Attempt 05 remains valid historical automated evidence but does not certify the interactive behavior under the production Workspace/runtime.

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

A new regression verifies that even when every Statement is outside the requested range, an exact Object-name Registry result remains visible while the non-overlapping Statement match is absent.

## Semantic runtime `nn` failure

SGOKB source does not reference `nn`. The failure occurs while constructing the external local embedding stack.

Current SGOKB dependency contract previously required:

```text
sentence-transformers >=6.1,<7
transformers >=5.2,<6
```

but did not constrain PyTorch.

Current Transformers 5.x requires a supported PyTorch version. A known failure mode when PyTorch is below the supported minimum leaves `torch.nn` unavailable to an evaluated annotation/path and raises:

```text
NameError: name 'nn' is not defined
```

Remediation:

```text
pyproject.toml
  local-embedding += torch>=2.6,<3

src/sgokb/runtime.py
  dependency ImportError / RuntimeError / NameError
    -> RetrievalRuntimeUnavailableError

  nn NameError
    -> actionable message explaining the PyTorch >=2.6 requirement
```

This changes the operator classification from `internal/internal_error` to the local-runtime failure category and prevents future optional-dependency installs from resolving an unsupported PyTorch version.

Existing environments are not mutated by source updates. An already-created venv with PyTorch <2.6 must be upgraded explicitly before Semantic runtime can succeed.

## Regression additions

Added:

```text
tests/test_p_gui_06_range_contract_runtime_dependency.py
```

Coverage:

1. From/To does not hide exact Registry identity when all Statements are outside the range;
2. non-overlapping Statement matches remain excluded;
3. dependency `NameError("name 'nn' is not defined")` becomes `RetrievalRuntimeUnavailableError` with the PyTorch >=2.6 guidance.

## Current disposition

```text
range contract root cause          = Corrected
semantic dependency root cause     = Identified
range remediation                  = Implemented
runtime error normalization        = Implemented
local-embedding dependency floor   = torch>=2.6,<3
existing operator environment      = Requires version check / possible torch upgrade
automated verification refresh     = Pending
interactive smoke                  = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
