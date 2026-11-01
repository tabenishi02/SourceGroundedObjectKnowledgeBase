# P-CLOSE-01 — Release Integration Decision

Updated: 2026-10-31

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-CLOSE-01 [P0] Full regression, documentation integration, release impact`
- Status: **Accepted for release-candidate integration / final regression pending**
- Previous release: `v1.1.0`
- Target release: `v2.0.0`

## Decision

Phase P is integrated as the `2.0.0` release line.

The release-facing changes are:

```text
GUI                = accepted PySide6 desktop client over shared Application/operator boundary
Package default    = v2 Raw-grounded Package/Result contract
Package v1         = explicit legacy compatibility only
Windows Qdrant     = native qdrant.exe + Task Scheduler external lifecycle
Runtime health     = shared system.status.runtime_health observer-only boundary
MCP                = read-only external stdio lifecycle remains unchanged
Canonical SQLite   = authoritative; derived state remains rebuildable
```

## SemVer determination

`2.0.0` is required by `O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md` because the no-option public Package build behavior changes from Package v1 / Result v1 semantics to Package v2 / Result v2 Raw-grounding semantics.

The CLI command remains present, and explicit `--package-version v1` remains available, but default public exchange semantics change. This is therefore a MAJOR release rather than a MINOR release.

## Raw Grounding default

For `2.0.0`:

```text
sgokb package build --object <OBJECT_ID>
```

selects Package v2.

Legacy interoperability remains explicit:

```text
sgokb package build --object <OBJECT_ID> --package-version v1
```

No historical v1 artifact is reinterpreted as v2.

## GUI distribution boundary

At the original P-CLOSE-01 decision on 2026-10-31, P-GUI-02 had accepted PySide6/Qt Widgets and a standalone-directory packaging direction, while the SGOKB application's own public OSS license had not yet been selected. That historical condition was superseded on 2026-11-01: SGOKB source code is now licensed under the MIT License, copyright (c) 2026 tabenishi02, with the authoritative text in the repository root `LICENSE` file.

P-CLOSE-01 still closes the source/repository release integration only. It does **not** publish or certify a standalone GUI binary artifact.

A later packaged-GUI publication must separately satisfy:

- preserve the SGOKB MIT license notice and root `LICENSE`;
- exact bundled/transitive dependency inventory;
- required Qt/PySide6 license texts and notices;
- source-availability/written-offer obligations where applicable;
- replacement/relinking and dynamic-linking constraints from P-GUI-02;
- final packaged-artifact license audit.

The absence of a standalone binary artifact is not a blocker for the `v2.0.0` source/repository release boundary.

## Runtime release boundary

Windows reference runtime remains:

```text
runtime form          = native qdrant.exe
lifecycle owner       = Windows Task Scheduler
SGOKB role            = observer/client only
readiness             = GET /readyz -> HTTP 200
start/stop/restart    = not exposed by SGOKB
crash recovery        = accepted repeating Task Scheduler trigger
```

Docker Compose remains optional/historical and is not restored as Windows authority.

## Release gate

`v2.0.0` may be tagged only after the P-CLOSE-01 latest-branch closure gate passes:

```text
release-contract focused tests = PASS
full repository pytest         = PASS
Ruff src/tests                 = PASS
current docs                   = consistent
P-GUI acceptance               = retained
P-RAW acceptance               = retained
P-RUNTIME acceptance           = retained
critical unexplained failures  = none
```

Until those gates are recorded, `2.0.0` is a release candidate and no `v2.0.0` tag should be created.
