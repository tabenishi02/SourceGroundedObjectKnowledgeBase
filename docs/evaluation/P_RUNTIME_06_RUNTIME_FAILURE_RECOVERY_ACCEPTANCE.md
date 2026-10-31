# P-RUNTIME-06 — Runtime Failure / Recovery Acceptance

Date: 2026-10-31  
Task: `P-RUNTIME-06 [P1] Runtime failure / recovery acceptance`

## Status

**Repository gate PASS / Pre-fault baseline PASS / GUI failure projection PASS / Reference-host fault-recovery acceptance pending**

P-RUNTIME-06 is an acceptance/fault-injection task. The repository-side contract tests, design, and operator procedure are prepared on branch `phase-p/runtime-06-failure-recovery-acceptance`. The supported Windows workstation has completed the focused repository gate, the pre-fault canonical/runtime baseline, and the GUI failure-projection gate successfully. The remaining CLI failure, port-conflict, recovery, persistence, rebuild, and final-integrity gates must still be executed before this task can become `Complete / Accepted`.

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

The complete pre-fault Qdrant collection inventory was captured in the operator shell as `$BeforeCollections` for the later persistence comparison. The inventory is non-empty and includes the reference SGOKB Vector collection together with historical/evaluation collections already present on the workstation.

Result:

```text
G2 pre-fault canonical SQLite integrity = PASS
```

## GUI failure projection — PASS

With the native Qdrant runtime intentionally unavailable under the controlled P-RUNTIME-06 maintenance protocol, the operator reported every GUI failure-state checklist item PASS:

```text
Qdrant presentation                  = unavailable / not ready
Semantic Search readiness            = BLOCKED
blocker / troubleshooting            = explains Qdrant failure
Qdrant lifecycle owner               = external
Qdrant Start / Stop / Restart        = not exposed
raw system.status JSON               = shows the same Qdrant failure state
```

This proves the GUI consumes the shared runtime-health boundary without taking lifecycle ownership during a real runtime outage.

Result:

```text
G4 GUI Semantic Search = BLOCKED during Qdrant failure  = PASS
G5 external lifecycle boundary preserved during failure = PASS
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

P-RUNTIME-06 must prove the transition from this baseline to `BLOCKED` during Qdrant failure and back to the baseline after recovery.

## Required new reference-host gates

The operator guide requires the following evidence:

```text
G1  focused P-RUNTIME tests + Ruff                                  PASS
G2  pre-fault canonical SQLite integrity                            PASS
G3  controlled native Qdrant unavailable detection in CLI           Pending
G4  GUI Semantic Search = BLOCKED during Qdrant failure              PASS
G5  external lifecycle boundary preserved during failure             PASS
G6  port 6333 wrong-service / non-ready listener fails closed         Pending
G7  native Qdrant recovery to /readyz HTTP 200                        Pending
G8  Qdrant collection inventory persists across process restart       Pending
G9  recovered CLI + GUI return to accepted baseline                   Pending
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
G4 GUI failure projection            = PASS
G5 external lifecycle boundary       = PASS
P-RUNTIME-04 crash-restart evidence  = Reusable / Accepted
remaining reference-host gates       = G3, G6-G12
canonical integrity after recovery   = Pending
P-RUNTIME-06 overall                 = In Progress / Reference-host Acceptance Pending
P-CLOSE-01                           = Blocked by P-RUNTIME-06
```

After the operator reports the remaining gates PASS, record the exact CLI failure/recovery/rebuild/integrity results here and update P-RUNTIME-06 to `Complete / Accepted`.
