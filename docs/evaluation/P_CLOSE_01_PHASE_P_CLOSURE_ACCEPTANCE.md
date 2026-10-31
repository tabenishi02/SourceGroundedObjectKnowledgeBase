# P-CLOSE-01 — Phase P Closure Acceptance

Updated: 2026-10-31

- Task: `P-CLOSE-01 [P0] Full regression, documentation integration, release impact`
- Branch: `phase-p/close-01-release-integration`
- Target release: `2.0.0`
- Status: **Repository integration in progress / latest-branch regression pending**

## Closure scope

P-CLOSE-01 integrates the three accepted Phase P workstreams into one release-facing contract:

```text
P-GUI-01..10     Complete / Accepted
P-RAW-01..06     Complete / Accepted
P-RUNTIME-01..06 Complete / Accepted
```

The closure gate does not reopen accepted design decisions unless integration reveals an actual inconsistency or regression.

## Release-contract integration

P-CLOSE-01 fixes the following release-facing decisions:

```text
project version                = 2.0.0
Package default                = v2 Raw-grounded contract
explicit Package v1            = retained legacy compatibility
GUI execution boundary         = shared Application/operator layer
Windows Qdrant authority       = native qdrant.exe + Task Scheduler
Qdrant lifecycle inside SGOKB  = observer-only
MCP                            = read-only external stdio lifecycle
standalone GUI binary release  = not certified/published by P-CLOSE
```

The MAJOR version follows O06 because no-option Package build changes public exchange semantics from v1 to v2.

## Inherited acceptance evidence

### GUI

P-GUI-10 final accepted evidence includes:

```text
public capability coverage       = 67 / 67
complete GUI regression          = 50 / 50 PASS
explicit CLI + MCP regression    = 59 / 59 PASS
full repository regression       = 854 / 854 PASS
Ruff                             = PASS
```

Subsequent P-RUNTIME-05 GUI Runtime Dashboard acceptance also passed on the reference Workspace.

### RAW Grounding

P-RAW-06 accepted the Package v2 / Result v2 Raw-grounded path, including deterministic Evidence-to-Raw resolution, exact Raw materialization, v2 validation/import, v1->v2 compatibility, v2->v1 downgrade blocking, and legacy regression.

P-CLOSE-01 changes the release default only; it does not weaken the accepted v2 contract.

### Runtime

P-RUNTIME-06 completed G1-G12 on the supported Windows workstation, including real Qdrant outage/degradation, wrong-service fail-closed behavior, recovery, `80 -> 80` collection persistence, Vector Index rebuild, post-rebuild integrity, and canonical Object/current-Version count stability.

## New P-CLOSE release-contract gates

The branch adds focused assertions that:

```text
package build without --package-version -> v2
explicit --package-version v1            -> v1
```

These must pass together with the full repository regression.

## Required final execution

Before closure:

```text
1. working tree clean
2. P-CLOSE focused release-contract tests PASS
3. full `pytest -q` PASS
4. `ruff check src tests` PASS
5. no new unexplained warnings/failures
6. release-facing docs consistent with 2.0.0
7. main merge completed
8. v2.0.0 tag created only after merged main is verified
```

## Current gate table

| Gate | Status |
|---|---|
| P-GUI accepted workstream | PASS / inherited |
| P-RAW accepted workstream | PASS / inherited |
| P-RUNTIME accepted workstream | PASS / inherited |
| Package v2 default implementation | Implemented / execution pending |
| Package v1 explicit compatibility | Implemented / execution pending |
| Current architecture integration | In progress |
| Requirements integration | In progress |
| Operations integration | In progress |
| README / docs index integration | In progress |
| SemVer determination | PASS / `2.0.0` |
| Third-party dependency/license inventory | PASS for source-release scope |
| Latest-branch focused tests | Pending |
| Latest-branch full regression | Pending |
| Latest-branch Ruff | Pending |
| Final release tag | Pending |

## Closure rule

P-CLOSE-01 becomes `Complete / Accepted` only after all latest-branch executable gates are green and the merged `main` release commit is frozen. Until then, `2.0.0` is a release candidate and no formal `v2.0.0` tag is claimed.
