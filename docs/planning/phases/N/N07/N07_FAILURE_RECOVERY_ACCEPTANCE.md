# N-07 — Failure / Recovery Acceptance

Updated: 2026-10-24

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-07 [P1] — Failure / Recovery`
- Status: **Complete / PASS — N07-R01 remediation formally PASS and review accepted**
- Parent state: N-06 `Complete / PASS`; Phase N `Active / Not Complete`
- Primary requirements: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Previous acceptance: `docs/evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md`

## Current remediation disposition (2026-10-24)

<!-- phase-n-current:start -->
N-07 = Complete / PASS — N07-R01 remediation formally PASS and review accepted
N07-R01 = Complete / PASS — ChatGPT review accepted 2026-10-24
<!-- phase-n-current:end -->

The original run `20261024T201856+0900` remains historical Complete / FAIL:
47 PASS / 3 FAIL, with I08/I11/I12 exposing incomplete SQLite-only recovery.
Accepted product Composite recovery closes these failures without weakening their
Gates. Other N-07 Gates were PASS and regression remained PASS.
Authority: `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md` and
`benchmark/results/n07-r01-composite-backup-restore.json`, run
`20261024T222300+0900`, source `ffb16e9f7e0e24c8c2648a04430fca57bfb71dfb`,
result `9cda43e9303488d2b0905f61fa3dbbed4f03a4fb`, ChatGPT review accepted.
Phase N closure is separate; no Phase O work has started.

## 1. Goal

N-07 determines whether SGOKB fails closed, isolates partial failures, preserves canonical/provenance state, degrades explicitly when derived/runtime dependencies fail, and can restore canonical data within the frozen recovery requirements.

The required priorities remain:

```text
Data integrity / provenance
> recoverability
> correctness of state / explicit boundaries
> availability / graceful degradation
> performance
```

N-07 does not make destructive tests against production/reference artifacts. All fault injection, process termination, corruption, restore and rebuild tests use isolated copies/namespaces under `.local/n07/`.

## 2. Frozen recovery requirements

From the accepted non-functional requirements:

```text
RPO target: <= 24 hours
RTO target: <= 4 hours
```

The RTO covers restoring canonical DB + Raw / Provenance to reusable state. Full Embedding / Vector Index rebuild is not required inside the 4-hour RTO; canonical read and minimum retrieval may recover first and derived semantic state may rebuild afterward.

Canonical backup coverage must include at minimum:

```text
SQLite canonical DB
Raw Artifact store
DB-external canonical/provenance-bearing manifests, if any
recovery-required configuration metadata, excluding plaintext secrets
```

Rebuildable Vector Index / Embedding cache / rendered artifacts / exchange Package payload may be excluded if rebuild from canonical state is demonstrated.

The existing `system backup create` implementation is SQLite-online-backup scoped. N-07 must not silently reinterpret that DB-only operation as satisfying full Raw/Provenance backup coverage. If no existing supported composite recovery path covers the remaining canonical artifacts, record a valid FAIL and open a remediation task rather than adding a benchmark-only bypass.

## 3. Formal stages

### N07-A — Preflight / baseline safety

Require:

```text
clean main == origin/main
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
sufficient disk headroom
reference Qdrant state fingerprint recorded
preserved N-03 DB fingerprint recorded
R1 user-aborted assets hashes recorded if present
```

Record exact runtime/package versions and measured git HEAD.

Create one isolated run root:

```text
.local/n07/<run_id>/
```

No formal fault test may target the original N-03 DB, production/reference canonical DB, reference Qdrant namespaces, or original R1 assets.

### N07-B — Invalid / stale / partial exchange input

Use deterministic valid Package/Result fixtures and isolated canonical DB copies.

Mandatory cases:

```text
B01 invalid Result schema / validation failure
B02 Result package_id mismatch
B03 Result manifest SHA mismatch
B04 stale base Version / stale current state
B05 immutable received Result byte-count mismatch
B06 immutable received Result SHA-256 mismatch
B07 truncated/unparseable Result artifact
B08 Package missing declared file
B09 Package size mismatch
B10 Package SHA-256 mismatch
B11 unsafe/unexpected Package layout
```

Expected for every mandatory case:

- explicit rejection / non-success result;
- accepted current Version unchanged;
- no partial imported Knowledge;
- no invalid receipt/import marked successful;
- no finalized partial Package destination;
- temporary staging cleaned or left clearly non-final/recoverable;
- retrying the original valid input remains possible.

### N07-C — Canonical transaction / crash consistency

Use the existing Result import transaction/failure-hook boundaries and an isolated DB.

Mandatory deterministic injections:

```text
C01 failure after candidate_created
C02 failure after knowledge_written
C03 failure after accepted but before transaction commit
```

For each case require:

```text
current Version unchanged
no accepted partial new Version
no partial statements/attributes/relations/evidence links committed
no successful object_result_import row committed
foreign_key_check clean
integrity_check ok
```

Also perform at least one real disposable child-process termination test at a controlled write boundary if it can be done safely and deterministically. It must use an isolated DB and must never kill the normal SGOKB/Codex/reference Qdrant processes. After termination, reopening SQLite must yield either the old committed state or a complete committed state, never an impossible current pointer / half-version state.

If a deterministic OS-kill checkpoint cannot be made reliable, retain C01-C03 as the formal transaction gate and record the process-kill case as BLOCKED supporting evidence rather than creating an unsafe kill test.

### N07-D — Disk-full / partial file / I/O failure

Never consume the workstation system drive merely to create ENOSPC.

Use one of:

- a safe isolated quota/virtual filesystem; or
- deterministic injected `ENOSPC` / write/copy failure at the actual file boundary.

Mandatory boundaries:

```text
D01 Package staging/copy
D02 restore temporary copy or equivalent canonical file output
D03 one additional repository-supported file artifact write if applicable
```

Require:

- no completed artifact appears from incomplete bytes;
- existing target remains unchanged where replacement is atomic;
- temporary files are cleaned or explicitly identified as non-final;
- canonical SQLite state remains valid;
- a retry after removing the fault succeeds.

The fault must exercise the production code boundary, not a fake benchmark-only copy routine.

### N07-E — Embedding / Vector / derived subsystem failure

Use isolated canonical/derived state.

Mandatory cases:

```text
E01 embedding provider unavailable/fails
E02 Qdrant unavailable during semantic read
E03 Qdrant/vector update failure during derived sync
E04 stale/missing derived state
E05 recovery by normal sync/rebuild after dependency returns
```

Acceptance:

- accepted canonical Version is never rolled back/deleted because derived processing fails;
- Identity/Object read and Lexical Search remain usable where the public contract permits;
- Semantic/Similarity unavailability or degradation is explicit;
- no silent cloud/provider/CPU/backend fallback occurs;
- stale semantic state is not presented as current without an explicit stale/degraded signal;
- active generation pointer is not corrupted;
- after dependency restoration, the normal maintenance/rebuild path converges derived state to canonical state and passes generation/payload/membership audit.

### N07-F — Search generation candidate / backend recovery

Exercise the accepted R2 generation lifecycle with run-owned Qdrant namespaces only.

Mandatory cases:

```text
F01 candidate build failure before ready
F02 invalid/incomplete candidate cannot cut over
F03 failed cutover leaves prior active generation unchanged
F04 interrupted/stale build can be identified and handled by the supported lifecycle
F05 valid isolated rebuild reaches ready and passes membership/vector audit
F06 rollback to a compatible prior generation, if the supported lifecycle exposes rollback
```

Do not introduce another Vector backend in N-07. “Backend exchange” is tested as replacement/rebuild into a new isolated Qdrant namespace/binding through the existing adapter/generation boundary.

If rollback is deliberately unavailable under the final R2 lifecycle, classify F06 against the documented contract rather than inventing a direct pointer write.

### N07-G — Raw / Provenance corruption detection

Use copied real/synthetic assets only.

Mandatory trust-boundary cases:

```text
G01 tampered immutable Result artifact is rejected by byte-count/hash audit
G02 tampered Package artifact is rejected by size/hash/preflight audit
G03 broken canonical provenance/FK relation in a copied DB is detected by integrity/foreign-key audit
G04 missing/corrupt Raw artifact that remains required by canonical provenance is detected by the supported Raw/Provenance verification path
```

For G04 first identify the actual supported verification/restore mechanism in the repository. Do not create a benchmark-only verifier and claim the product already supports it.

If SGOKB has no supported way to verify/restore a required external Raw artifact after canonical backup/restore, G04 is a **valid FAIL / recovery gap**, not BLOCKED. Preserve the evidence and create an explicit remediation task.

Unrelated Objects/Sources should remain readable when one copied Raw/provenance asset is damaged where isolation is technically possible.

### N07-H — Offline / provider / MCP outage

Do not disable the workstation network globally. Use process-local configuration, local-only mode, controlled endpoint denial, or stopped run-owned service instances.

Mandatory cases:

```text
H01 Internet/external service unavailable: local canonical read still works
H02 local cached Harrier path offline: no cloud fallback
H03 embedding provider unavailable: explicit failure/degraded semantic capability
H04 MCP server unavailable/stopped: direct CLI/Application read remains usable
H05 MCP restart/run-owned server recovery: access returns without canonical mutation
```

Where Qdrant outage overlaps E02, evidence may be shared if the case identity and expected behavior are both audited.

### N07-I — Backup / restore / RPO / RTO

First inventory every canonical/provenance-bearing artifact required by NFR-BKP-01. Separate:

```text
SQLite-contained canonical state
Raw Artifact files/store
DB-external canonical/provenance manifests
recovery configuration metadata
rebuildable derived state
```

Then evaluate the supported production recovery path.

Mandatory cases:

```text
I01 SQLite online backup completes and backup integrity_check=ok
I02 backup destination can be outside the active data directory
I03 existing restore target requires explicit overwrite acknowledgement
I04 corrupt/non-integral SQLite backup is refused
I05 restore uses temporary replacement semantics and leaves no valid-looking partial target
I06 restored DB full-table/canonical digest equals the backup-point source digest
I07 restored DB integrity_check=ok and foreign_key_check clean
I08 Raw/Provenance artifacts required at the backup point are present and verified after restore
I09 canonical Object/read/Lexical minimum retrieval works from restored state
I10 rebuildable R2 derived state can be recreated after restore and passes active-generation audit
I11 RPO <=24h capability is demonstrated by a reproducible daily-equivalent backup procedure/operational schedule
I12 RTO <=4h is measured from start of restore procedure through canonical + Raw/Provenance reusable state
```

RTO measurement ends when canonical DB + required Raw/Provenance and minimum local read/retrieval are usable. Full semantic Vector rebuild is measured separately and is not part of the 4-hour hard gate.

Retention requirement:

```text
daily >= 7 generations target
weekly >= 4 generations target
```

Concrete scheduler/rotation implementation is Phase O operational design. N-07 must verify that the backup format/destination scheme does not prevent this retention model and must record whether existing automation already implements it. Absence of a scheduler alone is not an N-07 FAIL if the accepted requirement explicitly defers scheduler implementation; absence of the underlying backup generation/coverage capability is a FAIL.

### N07-J — Deterministic evaluator / post-run regression

Run one deterministic evaluator over all mandatory gates.

Post-run require:

```text
focused N-07 tests PASS
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
original canonical/reference/N-03 state unchanged
reference Qdrant unchanged
R1 preserved assets unchanged if present
```

## 4. Verdict semantics

N-07 returns exactly one of:

```text
PASS
FAIL
BLOCKED
```

PASS requires all mandatory failure-isolation, corruption-detection, backup-coverage and recovery gates to pass.

FAIL means a valid, reproducible test proves a required safety/recovery contract is not satisfied. Missing product capability is FAIL when the requirement clearly requires the capability; do not relabel it BLOCKED.

BLOCKED means the environment or missing prerequisite evidence prevents a valid judgement (for example, a required preserved test asset is unavailable and cannot be replaced without changing the evaluation subject).

A FAIL opens an explicit remediation/design task. Do not silently add a benchmark-only workaround or weaken the requirement.

## 5. Formal hard gates

At minimum:

```text
invalid/stale/partial mandatory inputs rejected = 100%
partial accepted canonical Versions after transaction fault = 0
successful import rows after rolled-back transaction fault = 0
finalized partial Package/file artifacts = 0
silent provider/cloud/CPU/backend fallback = 0
failed generation build/cutover changes active pointer = 0
canonical corruption caused by derived failure = 0
required corruption cases detected = 100%
restored canonical digest == backup-point canonical digest
restored DB integrity_check = ok
restored foreign_key violations = 0
required Raw/Provenance restore verification = PASS
RPO capability <= 24h = PASS
canonical+Raw/Provenance RTO <= 4h = PASS
minimum restored local read/Lexical retrieval = PASS
post-restore R2 rebuild/audit = PASS
original/reference asset mutation = 0
```

## 6. Deliverables

Create/update at minimum:

```text
benchmark/n07-failure-recovery-contract-v1.json
benchmark/tools/n07_failure_recovery.py
benchmark/tools/n07_evaluate_failure_recovery.py
tests/test_n07_failure_recovery.py
docs/evaluation/N07_FAILURE_RECOVERY.md
benchmark/results/n07-failure-recovery.json
docs/planning/phases/N/PHASE_N_PREPARATION.md
```

Additional focused helpers/tests are allowed.

Raw destructive-test artifacts/logs remain under `.local/n07/` and are not committed.

## 7. Final state transition

If PASS:

```text
N-07 = Complete / PASS
Phase N acceptance tasks N-01..N-07 = Complete
Phase N closure audit = Next
```

Do not silently mark Phase N itself Complete until a separate Phase N closure audit reconciles all N-01..N-07 evidence and remaining cross-phase handoff requirements.

If FAIL:

```text
N-07 = Complete / FAIL
Phase N = Active / Not Complete
remediation = required
```

If BLOCKED:

```text
N-07 = BLOCKED / Not Complete
Phase N = Active / Not Complete
```

## 8. Historical original formal result and remediation task (superseded)

Run `20261024T201856+0900`, measured clean HEAD
`e78cf81a1c7d1daddfed729146579b4aacff8434`, completed A-J.
Deterministic result: **FAIL**; cases 47 PASS / 3 FAIL / 0 BLOCKED.
I08/I11/I12 fail because supported SQLite-only recovery omits required external
Raw, accepted original Result and recovery metadata. Complete canonical RPO/RTO
are not established; DB-only restore time is not a substitute. All other cases,
original/reference/R1 safety and pre/post full 727 / focused 38 tests PASS;
Ruff/format/compile/diff PASS. Invalid historical attempt is retained separately.

Result: `docs/evaluation/N07_FAILURE_RECOVERY.md`.
Aggregate: `benchmark/results/n07-failure-recovery.json`.

### N07-R01 — Composite canonical / Raw / Provenance backup and restore

**Required / Not Started**. Provide supported consistent generations containing
SQLite, referenced Raw/capture bundles, original Results/external provenance and
secret-free recovery metadata; checksum/consistency inventory and verified atomic
restore with correct path resolution. Re-accept frozen RPO <=24 h and canonical+
Raw/Provenance RTO <=4 h, with derived rebuild measured separately. Retention stays
daily >=7 / weekly >=4; scheduler stays Phase O. No benchmark-only copier.

```text
N-07 = Complete / FAIL
N07-R01 = Required / Not Started
Phase N closure audit = Not Started / blocked by remediation
Phase N = Active / Not Complete
```

No remediation or Phase N closure audit was started.
