# P-CLOSE-01 — Phase P Closure Acceptance

Updated: 2026-11-01

- Task: `P-CLOSE-01 [P0] Full regression, documentation integration, release impact`
- Branch: `phase-p/close-01-release-integration`
- Target release: `2.0.0`
- Status: **Executable gates PASS / merge and merged-main freeze pending**

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

## Execution evidence — initial closure candidate

Execution HEAD:

```text
fc2a0882368bbcbddc50ee04bfbcdc2f51fc5dcd
```

Repository state:

```text
working tree        = clean
origin branch sync  = up to date
git diff --check    = PASS / no output
```

Focused closure regression:

```text
58 passed in 13.86s
```

Full repository regression:

```text
874 passed
2 errors
2 known local-Qdrant warnings
234.88s
```

The two errors were both in `tests/test_m03_standard_workflow.py`:

```text
test_standard_workflow
test_standard_workflow_mcp_read
```

### Initial root cause

The M03 standard-workflow fixture called:

```text
sgokb package build --object ...
```

without an explicit Package version, so the P-CLOSE release candidate correctly produced Package v2 after the default change. The deterministic external-Result fixture, however, still populated v1 `evidence[]` claim grounding and omitted the Result v2 grounding binding fields. Result validation therefore correctly rejected the fixture.

This is an integration-test fixture incompatibility exposed by the intended release-contract change, not evidence that the accepted Package v2 / Result v2 validator is incorrect.

### First remediation

Remediation commit:

```text
0177b3cef2db24a6854d37b5ef2dd53039b75cbd
```

`tests/test_m03_standard_workflow.py` was changed to construct its deterministic Result from the Package manifest contract:

- Result v2 adds `grounding_contract` and `grounding_set_sha256` binding;
- Result v2 claims ground through audited `raw_artifact_id` members;
- Result v1 still uses Evidence grounding when explicitly exercised;
- the normal M03 no-option workflow therefore exercises the new Raw-grounded v2 release default instead of forcing legacy v1.

## Execution evidence — first remediation re-run

Execution HEAD:

```text
08d889af5830c1c7a87356c96de78bb9b8131e4e
```

Focused M03 re-run:

```text
2 errors in 20.01s
```

Both failures again occurred at `result validate`, so the first remediation was necessary but not sufficient.

### Second root cause

The remaining incompatibility was the Effective Facet extractor inside the M03 deterministic fixture.

The legacy v1 fixture used this separator-specific pattern:

```text
^- `(facet:[^`]+)` /
```

Package v2 instructions render Effective Facets as:

```text
- `facet:...` — Name: description
```

Therefore the v2 Result fixture emitted an empty `knowledge.facets` array. Result v2 validation correctly rejected that Result because every effective Facet must be returned exactly once.

The v2 binding fields and Raw grounding added by the first remediation were not the remaining cause.

### Second remediation

Remediation commit:

```text
4e520d2db989f7bebb691dd26abdcb3749f8a41d
```

The fixture now extracts Facet IDs from the version-independent bullet prefix:

```text
^- `(facet:[^`]+)`
```

This supports both accepted v1 and v2 instruction renderings without coupling the deterministic fixture to either separator glyph. No production validator, Package builder, Result importer, or runtime code was changed by this remediation.

## Execution evidence — second remediation re-run

Execution HEAD:

```text
e786f494fb91a1fd119b8d7e7deafabccf8f55ca
```

Focused M03 re-run:

```text
2 passed in 27.68s
```

This formally closes the M03 remediation gate. The accepted Package-v2 default now passes the installed-public-CLI standard workflow fixture through Result v2 validation/import and the MCP read follow-up path.

## Execution evidence — final closure gates

The final executable gates were run after the second remediation. The only intervening branch commit before the full regression was an acceptance-document update; no product or test code changed.

Focused closure regression:

```text
58 passed in 15.78s
```

Latest branch full repository regression at:

```text
d5a06bec3e3c0c24837b4411161c25e852ed431e
```

Result:

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

They are test-environment behavior already understood by the project and are not new release blockers.

Ruff:

```text
python -m ruff check src tests
All checks passed!
```

Therefore all latest-branch executable P-CLOSE gates are green.

## Current gate table

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
| Initial focused tests | PASS / `58 passed` |
| Initial full regression | FAIL / `874 passed, 2 errors` |
| First M03 v2 fixture remediation | Applied / `0177b3c` |
| First M03 remediation re-run | FAIL / `2 errors` |
| Second M03 Facet extraction remediation | Applied / `4e520d2` |
| Second M03 remediation re-run | PASS / `2 passed in 27.68s` |
| Final focused closure tests | PASS / `58 passed in 15.78s` |
| Final full regression | PASS / `876 passed, 2 known warnings` |
| Final Ruff | PASS / `All checks passed!` |
| PR merge to main | Pending |
| Merged-main release verification | Pending |
| Final `v2.0.0` tag | Pending |

## Closure rule

The executable acceptance portion of P-CLOSE-01 is complete. Formal `Complete / Accepted` closure is reached when this accepted branch is merged to `main`, the merged main release commit is verified, and the `v2.0.0` tag is frozen on that verified commit. No tag is claimed before that point.
