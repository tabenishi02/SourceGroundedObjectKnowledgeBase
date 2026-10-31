# P-RUNTIME-06 — Runtime Failure / Recovery Acceptance Design

Date: 2026-10-31  
Task: `P-RUNTIME-06 [P1] Runtime failure / recovery acceptance`

## 1. Purpose

P-RUNTIME-06 verifies that failures in the replaceable/local Semantic runtime do not corrupt canonical SGOKB Knowledge and that an operator can observe, diagnose, and recover the runtime through the accepted Windows operating model.

The completion condition remains:

> major runtime failure cases and recovery procedures are verified on the supported workstation.

## 2. Current authority

The task wording predates the P-RUNTIME-01/P-RUNTIME-04 Windows runtime amendment. The accepted Windows reference runtime is now:

```text
Qdrant runtime       = native qdrant.exe
lifecycle owner      = Windows Task Scheduler
startup              = AtLogOn
crash recovery       = repeating TimeTrigger / default 60 seconds
principal            = Interactive / Limited
readiness authority  = GET /readyz -> HTTP 200
SGOKB lifecycle role = observer / client only
```

Docker Compose remains an optional/historical development profile and is not reintroduced as the Windows reference runtime for P-RUNTIME-06.

Therefore the original checklist is interpreted as follows:

| Original task item | P-RUNTIME-06 Windows interpretation |
|---|---|
| Qdrant unavailable | native Qdrant stopped or `/readyz` unavailable |
| container runtime unavailable | accepted native runtime unavailable/unreachable |
| port conflict | TCP endpoint occupied by a non-Qdrant/not-ready listener; `/readyz` must fail closed |
| volume persistence | native Qdrant persistent storage/collection inventory survives process restart |
| restart after crash | reuse P-RUNTIME-04 accepted real-host crash-recovery evidence; optionally reconfirm |
| Vector Index rebuild | public `sgokb system index rebuild` recovery path |
| GUI / CLI degradation / troubleshooting | `system.status.runtime_health` + `System > Overview` |
| canonical SQLite integrity | `sgokb system integrity` remains PASS before/after runtime faults |

## 3. Safety invariants

P-RUNTIME-06 must preserve all of the following:

1. Qdrant remains externally owned.
2. SGOKB does not gain Qdrant Start / Stop / Restart public actions.
3. Runtime health probes are read-only against canonical SQLite.
4. Qdrant/Vector data are replaceable derived state, not canonical Knowledge.
5. No runtime fault may require rewriting accepted Object Knowledge to recover.
6. `system index rebuild` may rebuild derived Vector state but must not mutate accepted canonical Knowledge.
7. A port being open is not sufficient readiness evidence; `/readyz` HTTP 200 remains authoritative.
8. Failure injection must use the accepted maintenance protocol so the 60-second recovery pulse does not fight intentional testing.

## 4. Failure matrix

### F1 — Native Qdrant unavailable

Controlled injection:

```text
Disable scheduled task
-> Stop scheduled task
-> confirm qdrant.exe is stopped
```

Expected observation:

```text
CLI Qdrant status        = unavailable
Qdrant ready             = false
Semantic Search readiness = BLOCKED
canonical integrity      = PASS
```

Expected recovery:

```text
Enable scheduled task
-> Start scheduled task
-> /readyz HTTP 200
-> CLI Qdrant healthy/ready
-> GUI returns to the pre-fault baseline
```

### F2 — Runtime endpoint/port conflict

With genuine Qdrant intentionally stopped, a disposable listener may occupy TCP 6333 but return a non-200 response for `/readyz`.

Expected behavior:

- SGOKB must not treat TCP-open alone as Qdrant-ready;
- `qdrant_readiness_failed` or an equivalent endpoint-unavailable issue must be visible;
- Semantic Search is BLOCKED;
- SGOKB must not terminate the foreign listener or assume process ownership.

### F3 — Alive but not ready / bounded health probe

A listener may be alive while `/readyz` returns non-200 or cannot complete normally. Runtime health must degrade/fail closed rather than claim ready. This closes the alive-but-unready boundary explicitly deferred by P-RUNTIME-04.

### F4 — Crash recovery

P-RUNTIME-04 already proved on the supported Windows workstation:

```text
forced qdrant.exe exit
manual Start-ScheduledTask after crash = none
replacement process                    = PASS
/readyz recovery                        = HTTP 200
SGOKB Qdrant health                     = healthy
```

P-RUNTIME-06 accepts this evidence as the crash-restart sub-gate because it exercised the same accepted runtime form and reference host. A new destructive repetition is not required merely to duplicate evidence.

### F5 — Native Qdrant persistence

Record the Qdrant collection inventory before a controlled process restart and after readiness recovers. The relevant collection set must persist. This is the native-Windows equivalent of the original `volume persistence` item.

No canonical Knowledge mutation is required for this gate.

### F6 — Vector Index rebuild

Use the existing public operation:

```text
sgokb system index rebuild
```

The implementation rebuilds the Vector backend from SQLite search memberships and persisted Embeddings. Missing Embeddings are not silently generated by the rebuild path.

Acceptance requires:

- rebuild completes after Qdrant recovery;
- Vector/derived state becomes usable again;
- canonical SQLite integrity remains PASS;
- accepted Object/Version identity is unchanged.

### F7 — GUI / CLI degradation and recovery

During Qdrant failure:

- CLI `system status` exposes Qdrant unavailable/not ready and an issue reason;
- GUI `System > Overview` shows Semantic Search `BLOCKED`;
- troubleshooting points to the externally owned Qdrant process and `/readyz`;
- no lifecycle action appears in the GUI.

After recovery:

- Qdrant is healthy/ready again;
- GUI and CLI agree on the same runtime snapshot;
- for the current reference Workspace, Semantic Search returns to its normal `DEGRADED` baseline because inactive Search generation/rendering-only derived warnings remain independent of Qdrant health.

### F8 — Canonical SQLite integrity

Run before and after the failure sequence:

```text
sgokb system integrity
```

Required:

```text
ok                     = true
sqlite_integrity       = ["ok"]
foreign_key_violations = []
```

Also record stable canonical Object/current-Version counts from `system status`.

## 5. Automated contract coverage

`tests/test_p_runtime_06_failure_recovery_acceptance.py` covers isolated, non-destructive contracts:

- Qdrant `/readyz` failure blocks Semantic Search;
- a wrong service/port occupant returning non-200 is not treated as Qdrant ready;
- runtime projection recovers when `/readyz` returns to HTTP 200;
- health observation does not write canonical SQLite;
- external lifecycle ownership remains unchanged during failure.

These tests deliberately use an `httpx.MockTransport` and never stop the real reference-host Qdrant process.

## 6. Evidence reuse boundary

The following accepted evidence may be reused rather than repeated destructively:

- P-RUNTIME-04 reboot/login startup PASS;
- P-RUNTIME-04 forced-process-exit automatic recovery PASS;
- P-RUNTIME-04 `/readyz` and SGOKB Qdrant-health recovery PASS;
- P-RUNTIME-05 GUI baseline and CLI/GUI projection parity PASS.

P-RUNTIME-06 still requires new real-host evidence for controlled unavailable, port-conflict/not-ready behavior, persistence across restart, post-recovery Vector rebuild, and canonical integrity.

## 7. Completion rule

P-RUNTIME-06 can be marked `Complete / Accepted` only when:

- automated focused tests and Ruff pass;
- the supported Windows host completes the operator guide;
- all required new real-host gates pass;
- inherited P-RUNTIME-04 crash-restart evidence remains applicable;
- canonical SQLite integrity is PASS after recovery;
- no lifecycle ownership regression is introduced.
