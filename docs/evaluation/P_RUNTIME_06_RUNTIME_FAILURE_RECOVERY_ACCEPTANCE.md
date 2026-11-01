# P-RUNTIME-06 — Runtime Failure / Recovery Acceptance

Date: 2026-10-31  
Task: `P-RUNTIME-06 [P1] Runtime failure / recovery acceptance`

## Status

**Complete / Accepted**

> **Historical-evidence note — 2026-11-01:** the Qdrant failure/recovery evidence below is preserved as executed. Its recovered `generation_not_active` / Search-generation `DEGRADED` rows reflect the pre-correction runtime-health classifier. Current supported no-pointer routing is `Search generation = HEALTHY / active=none (legacy routing)`; independent rendering-only derived warnings can still keep the historical reference Workspace overall/Semantic readiness degraded. See `POST_RELEASE_GUI_STARTUP_RUNTIME_HEALTH_2026_11_01.md`.

P-RUNTIME-06 is complete. Repository-side fault-contract tests, controlled Windows reference-host failure injection, wrong-service fail-closed behavior, native Qdrant recovery, persistence validation, GUI/CLI baseline recovery, Vector Index rebuild, and final canonical SQLite integrity/count checks all passed.

## Accepted runtime interpretation

The original task checklist contains historical Docker-oriented wording. P-RUNTIME-01 and P-RUNTIME-04 subsequently amended the Windows reference runtime to native `qdrant.exe` + Windows Task Scheduler.

Current interpretation:

```text
Qdrant unavailable            = native Qdrant stopped or not ready
container runtime unavailable = native accepted runtime unavailable/unreachable
port conflict                 = non-Qdrant/not-ready listener occupies HTTP port 6333
volume persistence            = native Qdrant collection persistence across process restart
restart after crash           = P-RUNTIME-04 real-host evidence reused
Vector Index rebuild          = public `system index rebuild`
GUI / CLI degradation         = system.status + System > Overview
canonical SQLite integrity    = public `system integrity`
```

Docker Compose remains optional/historical and is not restored as the Windows acceptance authority.

## Protected boundaries

```text
qdrant_owner        = external
observe             = true
start               = false
stop                = false
restart             = false
readiness authority = GET /readyz -> HTTP 200
```

Runtime failure must never require rewriting accepted canonical Knowledge.

## Repository-side coverage — PASS

Added:

- `docs/design/P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_ACCEPTANCE.md`
- `docs/operations/P_RUNTIME_06_RUNTIME_FAILURE_RECOVERY_OPERATOR_GUIDE.md`
- `tests/test_p_runtime_06_failure_recovery_acceptance.py`

The focused P-RUNTIME-06 tests verify without touching the real Qdrant process:

1. `/readyz` failure is represented as Qdrant unavailable;
2. Semantic Search becomes `BLOCKED` while Qdrant is unavailable;
3. an open port serving the wrong/not-ready service is not accepted as Qdrant-ready;
4. the projection recovers after `/readyz` returns HTTP 200;
5. runtime observation does not write canonical SQLite;
6. external lifecycle ownership remains unchanged during failure.

Reported on the supported Windows workstation:

```text
branch                           = phase-p/runtime-06-failure-recovery-acceptance
focused P-RUNTIME test selection = 22 passed in 6.76s
Ruff                             = All checks passed!
```

Executed focused set:

```text
tests/test_p_runtime_06_failure_recovery_acceptance.py
tests/test_p_runtime_03_runtime_health_boundary.py
tests/test_p_runtime_04_windows_login_autostart.py
tests/test_p_runtime_05_gui_runtime_dashboard.py
```

Result:

```text
G1 focused P-RUNTIME tests + Ruff = PASS
```

## Pre-fault reference-host baseline — PASS

Workspace:

```text
.local/acceptance/sgokb-happy-path.sqlite
```

Observed canonical integrity:

```text
system.integrity.ok       = true
sqlite_integrity          = ["ok"]
foreign_key_violations    = []
Object count              = 5
current-Version count     = 5
```

Observed Qdrant/runtime baseline:

```text
Qdrant status             = healthy
Qdrant ready              = true
Qdrant version            = 1.19.2
qdrant_owner              = external
observe                   = true
start / stop / restart    = false / false / false
```

The pre-fault Qdrant collection inventory contained 80 collections and was retained in the operator shell for persistence comparison.

Result:

```text
G2 pre-fault canonical SQLite integrity = PASS
```

## Controlled runtime failure projection — PASS

With native Qdrant intentionally unavailable under the controlled maintenance protocol, the CLI reported:

```text
Qdrant status       = unavailable
ready               = false
issue.code          = qdrant_endpoint_unavailable
issue.message       = Qdrant endpoint probe failed: ConnectTimeout: timed out
overall_status      = degraded
qdrant_owner        = external
observe             = true
start/stop/restart  = false/false/false
```

The GUI reported every failure-state checklist item PASS:

```text
Qdrant presentation                  = unavailable / not ready
Semantic Search readiness            = BLOCKED
blocker / troubleshooting            = explains Qdrant failure
Qdrant lifecycle owner               = external
Qdrant Start / Stop / Restart        = not exposed
raw system.status JSON               = shows the same Qdrant failure state
```

Results:

```text
G3 controlled native Qdrant unavailable detection in CLI = PASS
G4 GUI Semantic Search = BLOCKED during Qdrant failure   = PASS
G5 external lifecycle boundary preserved during failure  = PASS
```

## Port-conflict / wrong-service fail-closed gate — PASS

With real Qdrant stopped and Task Scheduler disabled, a disposable Python HTTP listener occupied `127.0.0.1:6333` and returned HTTP 503 from `/readyz`.

Observed:

```text
fake listener process    = running
GET /readyz              = HTTP 503 Service Unavailable
Qdrant status            = unavailable
ready                    = false
issue.code               = qdrant_readiness_failed
issue.message            = Qdrant /readyz returned HTTP 503
overall_status           = degraded
qdrant_owner             = external
observe                  = true
start/stop/restart       = false/false/false
```

An open HTTP port alone was therefore not treated as Qdrant readiness, and SGOKB did not take lifecycle ownership of the foreign listener.

Result:

```text
G6 port 6333 wrong-service / non-ready listener fails closed = PASS
```

## Native runtime recovery and persistence — PASS

After the disposable listener was removed, port 6333 was confirmed free. The operator re-enabled and started `\SGOKB\Qdrant` through Windows Task Scheduler.

Observed native recovery:

```text
GET /readyz          = HTTP 200
response             = all shards are ready
Scheduled Task       = Running
qdrant.exe PID       = 41628
```

Recovered CLI runtime:

```text
Qdrant status        = healthy
ready                = true
version              = 1.19.2
overall_status       = degraded
qdrant_owner         = external
observe              = true
start/stop/restart   = false/false/false
```

At the time of the 2026-10-31 acceptance, `overall_status=degraded` was the accepted reference-Workspace baseline because the pre-correction classifier treated inactive Search generation together with rendering-only derived state as degraded; this was not a Qdrant recovery failure. Under the 2026-11-01 correction, the legacy Search route is healthy and only the independent derived warning remains.

Collection persistence comparison:

```text
collection count before = 80
collection count after  = 80
Compare-Object           = no differences
```

Recovered GUI projection returned exactly to the then-accepted P-RUNTIME-05 pre-correction baseline:

```text
Qdrant                 = HEALTHY / ready / v1.19.2
Semantic Search        = DEGRADED, not BLOCKED
Search generation      = DEGRADED / generation_not_active
Derived                = DEGRADED / rendering-only warning
Qdrant lifecycle owner = external
```

Results:

```text
G7 native Qdrant recovery to /readyz HTTP 200                  = PASS
G8 Qdrant collection inventory persists across process restart = PASS
G9 recovered CLI + GUI return to accepted baseline             = PASS
```

## Vector Index recovery rebuild — PASS

After native Qdrant had fully recovered, the public recovery operation was executed:

```text
command = system.index.rebuild
ok      = true
```

Observed result metadata:

```text
backend_key          = qdrant
backend_version      = 1.19.2
space_id             = 832920052e1d1a6d3bbe2a5ef9d3b0d09785b0e0f26bf3081b8728de2897d591
dimension            = 1024
distance             = cosine
points_count          = 126
indexed_points_count  = 0
approximate           = false
status                = green
```

The command emitted an unauthenticated Hugging Face Hub warning while loading the configured Harrier model, but model loading completed and the rebuild returned `ok=true`. Under the P-RUNTIME-06 acceptance contract this warning is non-blocking.

`indexed_points_count=0` is recorded as observed backend metadata; it is not treated as a P-RUNTIME-06 failure because the public recovery operation completed successfully, Qdrant reported `status=green`, and the rebuilt collection contained 126 points.

Result:

```text
G10 public system index rebuild succeeds after recovery = PASS
```

## Post-rebuild canonical integrity — PASS

After Vector Index rebuild:

```text
system.integrity.ok       = true
sqlite_integrity          = ["ok"]
foreign_key_violations    = []
```

Canonical counts remained unchanged:

```text
BeforeObjectCount   = 5
AfterObjectCount    = 5
BeforeCurrentCount  = 5
AfterCurrentCount   = 5
```

Results:

```text
G11 post-rebuild canonical SQLite integrity PASS              = PASS
G12 canonical Object count and current-Version count unchanged = PASS
```

Derived-state metadata and replaceable Vector backend contents may change during a legitimate Vector Index rebuild. No accepted canonical Knowledge identity/count change was observed.

## Inherited accepted crash-recovery evidence

P-RUNTIME-04 had already accepted the supported-workstation crash-recovery sub-gate:

```text
forced qdrant.exe exit                   = performed
manual Start-ScheduledTask after crash   = none
replacement process                      = PASS
recovered /readyz                        = HTTP 200
SGOKB Qdrant health                      = healthy / ready=true
```

This evidence satisfies the P-RUNTIME-06 `restart after crash` requirement without repeating the same destructive experiment.

## Final gate matrix

```text
G1  focused P-RUNTIME tests + Ruff                                  PASS
G2  pre-fault canonical SQLite integrity                            PASS
G3  controlled native Qdrant unavailable detection in CLI           PASS
G4  GUI Semantic Search = BLOCKED during Qdrant failure              PASS
G5  external lifecycle boundary preserved during failure             PASS
G6  port 6333 wrong-service / non-ready listener fails closed         PASS
G7  native Qdrant recovery to /readyz HTTP 200                        PASS
G8  Qdrant collection inventory persists across process restart       PASS
G9  recovered CLI + GUI return to accepted baseline                   PASS
G10 public system index rebuild succeeds after recovery               PASS
G11 post-rebuild canonical SQLite integrity PASS                      PASS
G12 canonical Object count and current-Version count unchanged         PASS
```

## Hosted CI status

The account's GitHub-hosted Actions capacity remains unavailable due the previously recorded billing/spending constraint. P-RUNTIME-06 does not claim hosted CI PASS.

This does not block closure because the task authority requires the real supported Windows host for lifecycle/failure/recovery acceptance, and that acceptance is complete.

## Formal closure

```text
repository fault-contract tests      = PASS / 22 passed
Ruff                                 = PASS
reference-host fault injection       = PASS
wrong-service fail-closed            = PASS
native runtime recovery              = PASS
collection persistence               = PASS / 80 -> 80 / no diff
CLI + GUI baseline recovery          = PASS
Vector Index rebuild                 = PASS / 126 points / Qdrant green
post-rebuild SQLite integrity        = PASS
canonical Object count               = 5 -> 5
canonical current-Version count      = 5 -> 5
P-RUNTIME-04 crash-restart evidence  = Reused / Accepted
P-RUNTIME-06 overall                 = Complete / Accepted
P-CLOSE-01                           = Unblocked / Ready
```
