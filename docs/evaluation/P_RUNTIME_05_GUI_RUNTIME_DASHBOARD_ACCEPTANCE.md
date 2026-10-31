# P-RUNTIME-05 — GUI Runtime Dashboard Acceptance

Date: 2026-10-31  
Task: `P-RUNTIME-05 [P1] GUI Runtime Dashboard integration`  
PR: `#82 P-RUNTIME-05 integrate GUI Runtime Dashboard` — **merged to `main`**

## Status

**Implementation merged / GUI smoke PASS / latest-main focused PASS / Ruff result pending**

GitHub-hosted Actions remain unavailable under the current account billing/spending limit. P-RUNTIME-05 therefore uses the supported Windows workstation for local acceptance, while hosted CI remains separate deferred verification.

## Implemented contract

```text
source operation       = system.status
projection             = data.runtime_health
schema                 = sgokb.runtime-health/1.0
GUI surface            = System > Overview
Qdrant lifecycle owner = external
observe                = true
start/stop/restart     = false / false / false
```

The dashboard adds Semantic Search readiness, component-level status, issue reasons, and troubleshooting entrypoints without changing the accepted P-RUNTIME-03 backend contract.

## Operator procedure

The manual procedure is documented in:

[`P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_OPERATOR_GUIDE.md`](../operations/P_RUNTIME_05_GUI_RUNTIME_DASHBOARD_OPERATOR_GUIDE.md)

The guide now uses `main` as the authoritative branch.

## Local acceptance evidence — 2026-10-31

### Focused P-RUNTIME-05 / System / runtime boundary

Initial result on pre-style-remediation HEAD `3810cab6d228db918f7b30d098037baabecb89e0`:

```text
22 passed in 8.96s
```

After the E501-only style remediation, PR #82 merge, and later documentation-only updates, the operator updated local `main` to commit `b10ddbd2e0bb2e16f319e7d8f942066f8ee6a931` and reran the same focused gate:

```text
22 passed in 7.77s
```

Disposition: **PASS on latest tested main**.

### Ruff

Initial result on the pre-style-remediation HEAD:

```text
9 x E501 line-too-long findings
```

All nine findings were confined to P-RUNTIME-05 additions and were remediated by line wrapping only. No readiness logic or runtime-health contract changed.

The operator invoked the latest-main Ruff command:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
```

but the supplied console transcript ends at the command invocation and does not include the command result or exit status.

Disposition: **REMEDIATED / latest-main result pending evidence**.

### Full regression

Observed on pre-style-remediation HEAD:

```text
869 passed, 2 warnings in 250.83s
```

The two warnings are the previously accepted local-Qdrant warnings. No test failures or new warnings were observed.

Disposition: **PASS**. The subsequent product-code change was formatting-only line wrapping; later commits after PR #82 merge are documentation-only.

### Reference Workspace CLI projection

Reference database:

```text
.local/acceptance/sgokb-happy-path.sqlite
```

Observed authoritative runtime-health snapshot:

```text
schema                  = sgokb.runtime-health/1.0
overall_status           = degraded
sqlite                   = healthy
embedding                = healthy
qdrant                   = healthy
qdrant.ready             = true
qdrant.version           = 1.19.2
generation               = degraded
generation issue         = generation_not_active
derived                  = degraded
derived issue            = derived_state_incomplete
qdrant_owner             = external
observe                  = true
start/stop/restart       = false / false / false
```

Reference details relevant to P-RUNTIME-05:

- SQLite is healthy with WAL active and foreign keys enabled.
- Embedding is healthy and configured; the shallow probe reports `configured_not_loaded`.
- Qdrant `http://localhost:6333` is healthy and ready, version `1.19.2`.
- no active Search generation is selected while five current Objects exist;
- Derived state contains 17 ready states and 3 pending `rendering` states;
- semantic kinds `search_representation`, `embedding`, and `vector_index` are ready for all five current Objects.

Expected dashboard interpretation:

```text
Semantic Search readiness = DEGRADED
hard blocker              = none
Qdrant                     = HEALTHY / ready / v1.19.2
Search generation          = DEGRADED / inactive generation guidance
Derived                    = DEGRADED / rendering-only warning
lifecycle                  = external observer-only
```

Disposition: **PASS**.

## GUI reference-workspace smoke — PASS

The operator executed the Japanese Operator Guide against the reference Workspace and reported every acceptance checklist item as PASS:

```text
GUI starts successfully                                      = PASS
reference Workspace opens                                    = PASS
System > Overview reachable                                  = PASS
Refresh system status completes                              = PASS
Runtime health summary visible                               = PASS
Semantic Search readiness visible                            = PASS
Semantic Search = DEGRADED, not BLOCKED                      = PASS
SQLite = HEALTHY                                             = PASS
Embedding = HEALTHY                                          = PASS
Qdrant = HEALTHY / ready / v1.19.2                           = PASS
Search generation degraded guidance visible                  = PASS
Derived rendering-only degradation warning visible           = PASS
troubleshooting explains degraded reasons                    = PASS
Qdrant lifecycle owner = external                            = PASS
no Qdrant Start / Stop / Restart controls                    = PASS
MCP note points to MCP tab without invented health state      = PASS
raw system.status JSON remains visible after refresh          = PASS
structured dashboard agrees with CLI runtime-health snapshot  = PASS
```

Formal smoke result:

```text
GUI reference-workspace smoke = PASS
```

This confirms the principal P-RUNTIME-05 user-facing requirement: runtime insufficiency and degradation are visible in `System > Overview` before the operator attempts Semantic Search, without transferring Qdrant lifecycle ownership into SGOKB.

### GUI startup font diagnostics

Launching the GUI through `python -m sgokb.gui.main` emitted Qt font-database diagnostics such as:

```text
qt.text.font.db: OpenType support missing for "Yu Gothic UI", script 11
qt.text.font.db: OpenType support missing for "Tahoma", script 11
...
```

The GUI nevertheless started successfully and the full reference-workspace smoke passed. These diagnostics are therefore recorded as **non-blocking startup warnings for this acceptance**, not as a P-RUNTIME-05 functional failure.

## Remaining local gate

Only the latest-main Ruff result remains to be recorded. From current `main`:

```powershell
cd C:\codex\SourceGroundedObjectKnowledgeBase
git switch main
git pull --ff-only
.\.venv\Scripts\python.exe -m ruff check src tests
```

Required: Ruff PASS / exit code 0.

A complete full-regression re-run is not required solely because the post-regression product patch was line wrapping only and later changes are documentation-only.

## Current disposition

```text
implementation                    = Complete / merged to main
focused runtime/dashboard tests   = PASS / 22 passed on latest tested main
Ruff                              = remediated / latest-main result pending evidence
full regression                   = PASS / 869 passed / 2 known warnings
reference CLI projection          = PASS
GUI reference-workspace smoke     = PASS
P-RUNTIME-03 lifecycle boundary   = preserved
new regressions                   = none observed

P-RUNTIME-05 overall              = In Progress / Ruff Verification Pending
```

When the latest-main Ruff command passes, update this document to `Complete / Accepted`, unblock P-RUNTIME-06, and retain hosted CI only as deferred external verification while the GitHub Actions spending limit remains unavailable.
