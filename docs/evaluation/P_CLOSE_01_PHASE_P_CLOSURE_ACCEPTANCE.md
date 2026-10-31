# P-CLOSE-01 — Phase P Closure Acceptance

Updated: 2026-11-01

- Task: `P-CLOSE-01 [P0] Full regression, documentation integration, release impact`
- Target release: `2.0.0`
- Status: **Complete / Accepted — release tag freeze pending**

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

## P-CLOSE release-contract gates

The closure branch added focused assertions that:

```text
package build without --package-version -> v2
explicit --package-version v1            -> v1
```

These passed together with the full repository regression.

## Regression remediation history

The initial closure candidate exposed two M03 standard-workflow fixture errors after the intended Package default switch.

### Initial run

```text
focused closure regression = 58 passed in 13.86s
full repository regression = 874 passed / 2 errors / 2 known local-Qdrant warnings
```

The errors were both in `tests/test_m03_standard_workflow.py` during Result validation.

### First remediation

Commit:

```text
0177b3cef2db24a6854d37b5ef2dd53039b75cbd
```

The deterministic Result fixture was changed to follow the Package manifest contract:

- Result v2 adds `grounding_contract` and `grounding_set_sha256` binding;
- Result v2 claims ground through audited `raw_artifact_id` members;
- Result v1 still uses Evidence grounding when explicitly exercised.

First remediation re-run:

```text
2 errors in 20.01s
```

### Second remediation

The remaining cause was a v1-only Effective Facet extraction pattern. Package v2 instructions use an em dash separator, so the fixture emitted an empty `knowledge.facets` array.

Commit:

```text
4e520d2db989f7bebb691dd26abdcb3749f8a41d
```

The fixture now extracts Facet IDs from the version-independent bullet prefix:

```text
^- `(facet:[^`]+)`
```

No production validator, Package builder, Result importer, or runtime code was changed by either remediation.

Second remediation re-run:

```text
2 passed in 27.68s
```

## Final executable acceptance

Focused closure regression:

```text
58 passed in 15.78s
```

Latest branch full repository regression at `d5a06bec3e3c0c24837b4411161c25e852ed431e`:

```text
876 passed
2 warnings
257.85s
```

The two warnings are the already-known local-Qdrant test warnings from `tests/test_generation_lifecycle_qdrant_r2.py`:

```text
Payload indexes have no effect in the local Qdrant.
Local mode performs exact (brute-force) search, so search_params has no effect except idf.
```

They are understood test-environment behavior and are not new release blockers.

Ruff:

```text
python -m ruff check src tests
All checks passed!
```

## Merge and main verification

PR #85 was merged using the exact accepted head:

```text
accepted PR head = 41efc5f9661cb2b34eec2cb69b185ff56c8caecc
merge commit     = 1b8c5ddb145367404e31e4b098d3e462afbfee1d
```

GitHub main was then verified to point to that merge commit and the merge commit signature status was `verified=true`.

Release-facing main content was also verified to contain:

```text
pyproject.toml project version = 2.0.0
P-CLOSE accepted code/docs      = merged
```

No product or test code changed between the accepted branch gate and the merge commit.

## Final gate table

| Gate | Status |
|---|---|
| P-GUI accepted workstream | PASS / inherited |
| P-RAW accepted workstream | PASS / inherited |
| P-RUNTIME accepted workstream | PASS / inherited |
| Package v2 default implementation | PASS |
| Package v1 explicit compatibility | PASS |
| Current architecture integration | Complete |
| Requirements integration | Complete |
| Operations integration | Complete |
| README / docs index integration | Complete |
| SemVer determination | PASS / `2.0.0` |
| Third-party dependency/license inventory | PASS for source-release scope |
| M03 remediation re-run | PASS / `2 passed in 27.68s` |
| Final focused closure tests | PASS / `58 passed in 15.78s` |
| Final full regression | PASS / `876 passed, 2 known warnings` |
| Final Ruff | PASS / `All checks passed!` |
| PR #85 merge to main | PASS |
| Merged-main verification | PASS |
| P-CLOSE-01 | **Complete / Accepted** |
| Final `v2.0.0` tag | Pending release-freeze action |

## Closure disposition

P-CLOSE-01 is **Complete / Accepted**. Phase P implementation, documentation integration, regression acceptance, merge, and merged-main verification are complete.

The remaining `v2.0.0` tag creation is the release-freeze action that marks the verified main state as the formal version boundary. No additional Phase P product-code remediation is pending.
