# P-RUNTIME-06 — Runtime Failure / Recovery Acceptance

Date: 2026-10-31  
Task: `P-RUNTIME-06 [P1] Runtime failure / recovery acceptance`

## Status

**Repository gate PASS / Failure-recovery PASS through G9 / Final rebuild-integrity acceptance pending**

P-RUNTIME-06 is an acceptance/fault-injection task. The repository-side contract tests, design, and operator procedure are prepared on branch `phase-p/runtime-06-failure-recovery-acceptance`. The supported Windows workstation has completed the focused repository gate, pre-fault canonical/runtime baseline, CLI/GUI failure projection, wrong-service port-conflict fail-closed test, native Qdrant recovery, collection persistence comparison, and recovered CLI/GUI baseline successfully. Only the final Vector Index rebuild and post-rebuild canonical integrity/count gates remain before this task can become `Complete / Accepted`.

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

## Repository-side coverage

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

## Repository gate evidence — PASS

Reported on the supported Windows workstation on 2026-10-31:

```text
branch                           = phase-p/runtime-06-failure-recovery-acceptance
working tree                     = clean
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

Reported on the supported Windows workstation on 2026-10-31 using:

```text
Workspace = .local/acceptance/sgokb-happy-path.sqlite
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
observe                    = true
start / stop / restart    = false / false / false
```

The complete pre-fault Qdrant collection inventory was captured in the operator shell as `$BeforeCollections` for the later persistence comparison. The inventory contained 80 collections, including the reference SGOKB Vector collection together with historical/evaluation collections already present on the workstation.

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

The runtime therefore fails closed: an open HTTP port alone is not treated as Qdrant readiness, and SGOKB does not take lifecycle ownership of the foreign listener.

Result:

```text
G6 port 6333 wrong-service / non-ready listener fails closed = PASS
```

## Native runtime recovery and persistence — PASS

After the disposable wrong-service listener was removed, port 6333 was confirmed free. The operator re-enabled and started `\SGOKB\Qdrant` through Windows Task Scheduler.

Observed native recovery:

```text
GET /readyz          = HTTP 200
response             = all shards are ready
Scheduled Task       = Running
qdrant.exe PID       = 41628
```

Observed recovered CLI runtime:

```text
Qdrant status        = healthy
ready                = true
version              = 1.19.2
overall_status       = degraded
qdrant_owner         = external
observe              = true
start/stop/restart   = false/false/false
```

`overall_status=degraded` is the accepted reference-Workspace baseline because inactive Search generation and rendering-only derived state remain intentionally degraded; this is not a Qdrant recovery failure.

Collection persistence comparison:

```text
collection count before = 80
collection count after  = 80
Compare-Object           = no differences
```

Recovered GUI projection also returned exactly to the accepted P-RUNTIME-05 baseline:

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

## Inherited accepted evidence

### P-RUNTIME-04 crash recovery

Already accepted on the supported Windows workstation:

```text
forced qdrant.exe exit                   = performed
manual Start-ScheduledTask after crash   = none
replacement process                      = PASS
recovered /readyz                        = HTTP 200
SGOKB Qdrant health                      = healthy / ready=true
```

This satisfies the P-RUNTIME-06 `restart after crash` sub-gate without repeating the same destructive experiment.

### P-RUNTIME-05 GUI baseline

Already accepted:

```text
GUI reference-workspace smoke = PASS
CLI / GUI runtime projection  = consistent
normal Semantic Search state  = DEGRADED, not BLOCKED
Qdrant                         = HEALTHY / ready / v1.19.2
```

P-RUNTIME-06 has now proven the transition from this baseline to `BLOCKED` during Qdrant failure and back to the same baseline after recovery.

## Required reference-host gates

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
G10 public system index rebuild succeeds after recovery               Pending
G11 post-rebuild canonical SQLite integrity PASS                      Pending
G12 canonical Object count and current-Version count unchanged         Pending
```

## Expected canonical integrity result

Before and after fault/recovery:

```text
system.integrity.ok       = true
sqlite_integrity          = ["ok"]
foreign_key_violations    = []
```

Object and current-Version counts must also remain unchanged.

Derived-state metadata and Vector backend contents may change during a legitimate Vector Index rebuild. That is not canonical Knowledge mutation.

## Hosted CI status

The account's GitHub-hosted Actions capacity remains unavailable due the previously recorded billing/spending constraint. P-RUNTIME-06 does not claim hosted CI PASS.

The real-host fault/recovery transitions are inherently workstation lifecycle tests and remain the formal acceptance source for this task.

## Current disposition

```text
P-RUNTIME-06 design                  = Complete
repository fault-contract tests      = PASS / 22 passed
Ruff                                 = PASS
operator procedure                   = Complete
G2 pre-fault canonical baseline      = PASS
G3 CLI failure projection            = PASS
G4 GUI failure projection            = PASS
G5 external lifecycle boundary       = PASS
G6 port-conflict fail-closed         = PASS
G7 native runtime recovery           = PASS
G8 collection persistence            = PASS / 80 -> 80 / no diff
G9 CLI + GUI baseline recovery       = PASS
P-RUNTIME-04 crash-restart evidence  = Reusable / Accepted
remaining reference-host gates       = G10-G12
canonical integrity after recovery   = Pending
P-RUNTIME-06 overall                 = In Progress / Final Rebuild-Integrity Acceptance Pending
P-CLOSE-01                           = Blocked by P-RUNTIME-06
```

After the operator reports G10-G12 PASS, record the exact rebuild/integrity/count results here and update P-RUNTIME-06 to `Complete / Accepted`.
