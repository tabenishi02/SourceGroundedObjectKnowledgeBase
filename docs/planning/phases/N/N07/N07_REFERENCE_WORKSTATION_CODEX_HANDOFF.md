# N-07 — Failure / Recovery — Codex Handoff

Updated: 2026-10-24

## 1. Task

Execute `N-07 [P1] — Failure / Recovery` on the Reference Workstation.

Canonical inputs:

```text
docs/planning/phases/N/N07/N07_FAILURE_RECOVERY_ACCEPTANCE.md
benchmark/n07-failure-recovery-contract-v1.json
docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md
docs/evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md
src/sgokb/system_ops.py
src/sgokb/exchange/package_transfer.py
src/sgokb/exchange/result_import.py
src/sgokb/storage/result_import_repository.py
src/sgokb/application_derived.py
src/sgokb/application_generation.py
```

Do not start Phase N closure audit inside N-07.

## 2. Local work ownership / safety

All filesystem, command, process-kill, network-outage simulation, SQLite, Qdrant and local-service operations are owned by Codex.

Use a dedicated clean branch/worktree/clone. Preserve all original/reference artifacts byte-for-byte.

Never:

```text
fill C: to trigger ENOSPC
disable the workstation network globally
kill the normal Codex process
kill the accepted reference Qdrant process
modify the original N-03 DB in place
modify production/reference canonical DB
modify/delete original R1 user-aborted assets
perform destructive restore over an original DB
```

All destructive tests belong under `.local/n07/<run_id>/` or run-owned service namespaces.

## 3. Start state

Synchronize latest `origin/main` and require:

```text
main == origin/main
working tree clean
```

Record exact baseline HEAD.

Record before fingerprints/hashes for:

```text
original/reference canonical assets available on workstation
preserved N-03 DB
reference Qdrant collection inventory + point/generation fingerprint
R1 assets 3件 if present
```

## 4. Mandatory implementation review before test code

Inventory existing product behavior. Do not assume a recovery feature exists merely because the requirement requests it.

Specifically confirm:

1. Result import failure hooks / SQLite transaction rollback boundaries.
2. Package staging temporary-directory and final `os.replace` semantics.
3. immutable Result byte-count/SHA checks.
4. Derived Search failure/degradation behavior.
5. R2 generation build/cutover/rollback/recovery APIs.
6. `system integrity` coverage.
7. `system backup create/status` and `restore plan/apply` coverage.
8. Raw Artifact physical storage model and supported verification/recovery path.
9. DB-external provenance-bearing manifests/config required for recovery.
10. MCP run/start/stop boundary that can be safely exercised with a run-owned instance.

Important known fact: current `create_backup()` in `system_ops.py` creates/integrity-checks a SQLite backup. Do not claim this alone satisfies NFR-BKP-01 if required Raw/Provenance artifacts are outside that SQLite file.

## 5. N-07 harness

Implement N-07-specific harness/evaluator/tests. Recommended:

```text
benchmark/tools/n07_failure_recovery.py
benchmark/tools/n07_evaluate_failure_recovery.py
tests/test_n07_failure_recovery.py
```

Helper fixture modules are allowed.

The evaluator must consume `benchmark/n07-failure-recovery-contract-v1.json` and emit PASS/FAIL/BLOCKED deterministically.

Do not modify production recovery semantics merely to make the formal run pass. If product behavior violates a frozen requirement, record FAIL and stop after collecting sufficient evidence. Any remediation requires a separate explicit task.

## 6. Focused test requirements

Before formal execution add deterministic tests for at least:

```text
1. invalid/stale Result cannot alter current Version
2. immutable Result byte-count/hash tamper rejection
3. Package missing/size/hash mismatch rejection
4. Package failure does not finalize staging directory
5. failure_hook candidate_created rolls back
6. failure_hook knowledge_written rolls back
7. failure_hook accepted rolls back
8. rollback leaves receipt/import/current pointer consistent
9. derived provider failure cannot delete/rollback canonical Version
10. Vector/Qdrant failure exposes explicit degraded/unavailable state
11. no silent provider/cloud/CPU fallback
12. failed generation candidate does not move active pointer
13. invalid generation cannot cut over
14. restore existing target requires acknowledgement
15. corrupt SQLite backup is refused
16. restore temporary-file failure preserves previous target
17. restored DB digest/integrity comparison helper is deterministic
18. Raw/Provenance backup coverage inventory is deterministic
19. missing required Raw recovery coverage evaluates FAIL, not BLOCKED
20. RPO/RTO evaluator boundaries use the frozen 24h/4h requirements
21. reference/original paths are rejected as destructive-test targets
22. PASS/FAIL/BLOCKED evaluator semantics are deterministic
```

Add more focused cases as required by actual implementation boundaries.

## 7. Preflight

Before formal fault execution:

```powershell
python -m pytest -q
python -m ruff check .
git diff --check
```

Also run compile/format checks used by recent Phase N tasks.

All must PASS before formal execution.

Commit the harness/tests first so formal measurement has a fixed clean source HEAD.

## 8. Formal run

Create a new Asia/Tokyo run ID and root:

```text
.local/n07/<YYYYMMDDTHHMMSS+0900>/
```

Execute stages in order:

```text
A preflight/before fingerprints
B invalid/stale/partial exchange input
C transaction + controlled crash consistency
D disk-full/I/O/partial-file simulation
E Embedding/Vector/derived failure and recovery
F R2 generation candidate/cutover/backend recovery
G Raw/Provenance corruption detection
H offline/provider/MCP outage
I backup/restore/RPO/RTO
J deterministic evaluator + post-run regression/safety
```

Preserve every failed/BLOCKED attempt under its own run ID; never overwrite it.

## 9. Stage-specific instructions

### B — exchange

Use valid deterministic fixtures then mutate one property at a time. Verify both failure classification and before/after DB/artifact fingerprints.

### C — transaction/crash

Use `ObjectVersionImportService(..., failure_hook=...)` / `ResultImportRepository` checkpoints already exposed by production code.

Expected hook labels include the actual implementation labels such as:

```text
candidate_created
knowledge_written
accepted
```

Verify rollback after each.

For a real process-kill supporting case, create a child worker that only owns a disposable DB. Coordinate a deterministic checkpoint before killing that child. If deterministic coordination cannot be made safe, do not guess; mark only that supporting case BLOCKED and retain the mandatory transaction-hook evidence.

### D — ENOSPC/I/O

Prefer deterministic monkeypatch/fault-injection at production `copyfile`, `copy2`, write, replace or equivalent boundaries if a safe quota filesystem is not already available.

The injected exception must be an OS-style error (`ENOSPC`/`OSError`) at the actual product operation. Do not build a separate fake copy implementation.

### E — derived outage

Use run-owned/copy canonical data. For Qdrant outage, use a run-owned Qdrant instance/endpoint or intentionally unreachable run-owned endpoint; do not stop the reference service.

After recovery, run the normal maintenance/rebuild path and independently verify generation membership/vector identity.

### F — generation

Use only run-owned namespaces. Confirm the prior active generation/pointer before every failed transition and compare after.

Do not manipulate active-generation tables directly to manufacture success.

### G — Raw/Provenance

First document the actual physical Raw Artifact paths and which of them are canonical according to the repository/requirements.

Use copied assets only.

For external Raw artifact loss/corruption, use the product-supported verifier/recovery operation if one exists. If none exists, capture that absence through repository/API/CLI inventory and a reproducible restore test. Per contract, a required capability gap is FAIL, not BLOCKED.

### H — offline/MCP

Do not change Windows/global firewall/network state. Exercise local-only/cached provider behavior and a run-owned MCP process.

Prove direct CLI/Application read independently from MCP process availability.

### I — backup/restore

Inventory canonical recovery set before creating the backup. At minimum classify:

```text
SQLite DB
Raw Artifact store
external canonical/provenance manifests
recovery configuration metadata
rebuildable derived artifacts
```

Run the supported production backup path. Use a backup destination separated from the active data directory.

Test corrupt SQLite backup on a copied backup file.

Restore to a new run-owned path first. Test overwrite acknowledgement on another run-owned target.

Measure:

```text
backup duration
restore duration
integrity/provenance verification duration
time until canonical Object/read + Lexical minimum retrieval usable
optional/full R2 derived rebuild duration separately
```

RTO clock for the hard gate ends when canonical DB + required Raw/Provenance are reusable and minimum local read/Lexical retrieval works. Do not include full Vector rebuild in the 4h gate.

For RPO, demonstrate the available operational procedure can create a completed canonical backup at <=24h cadence. Do not wait 24 hours. Scheduler/rotation code is Phase O; record existing automation if any.

The restored backup-point canonical digest must equal the source digest captured at backup completion. Create a post-backup change in an isolated source if useful to demonstrate the RPO boundary; post-backup data may correctly be absent from the restored generation.

If the existing product backup covers SQLite but not required Raw/Provenance, do not write a benchmark-only copier and call the product PASS. Record formal FAIL and identify the missing recovery surface.

## 10. Formal verdict policy

Use exactly:

```text
PASS
FAIL
BLOCKED
```

Examples:

- backup runs but required Raw store is absent from recovery coverage -> FAIL.
- valid test proves derived outage silently changes canonical data -> FAIL.
- a required preserved source asset cannot be located, making the test unjudgeable -> BLOCKED.
- optional process-kill supporting case cannot be safely coordinated but transaction hooks prove mandatory crash-consistency contract -> supporting case BLOCKED; overall verdict follows mandatory gates.

Never tune or weaken the requirement after seeing the result.

## 11. Post-run

Require:

```text
focused N-07 tests PASS
full pytest PASS
repository-wide Ruff PASS
git diff --check PASS
original/reference canonical fingerprints unchanged
preserved N-03 unchanged
reference Qdrant unchanged
R1 hashes unchanged
```

Also verify no run-owned process/service was left running and no temporary mount/quota resource remains.

## 12. Publication

Create:

```text
docs/evaluation/N07_FAILURE_RECOVERY.md
benchmark/results/n07-failure-recovery.json
```

Update:

```text
docs/planning/phases/N/N07/N07_FAILURE_RECOVERY_ACCEPTANCE.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
```

If PASS:

```text
N-07 = Complete / PASS
N-01..N-07 = Complete
Phase N closure audit = Next
Phase N = Active / Not Complete until closure audit
```

If FAIL, record the failing requirement/case and create a clearly named remediation task; do not start Phase N closure.

If BLOCKED, isolate the blocker and do not start Phase N closure.

## 13. Git policy

Recommended working branch:

`n07-failure-recovery`

Commit harness/tests before formal run to freeze the measured source HEAD. After formal evidence and documentation are complete, commit/push results. Merge to main only according to the final evidence disposition; safe benchmark/test infrastructure and an intentional FAIL/BLOCKED evidence record may be preserved if clearly documented.

## 14. Final report

Return at least:

1. baseline and measured HEAD;
2. run ID;
3. preflight/full regression result;
4. B01-B11 results;
5. C transaction rollback results and optional process-kill result;
6. D ENOSPC/I/O cases;
7. E derived/provider/Qdrant outage and rebuild result;
8. F generation/cutover/rollback/recovery result;
9. G corruption-detection results;
10. H offline/provider/MCP results;
11. canonical recovery inventory;
12. backup coverage and backup duration;
13. restore digest/integrity/Raw/Provenance result;
14. measured RPO capability;
15. measured RTO and boundary definition;
16. post-restore R2 rebuild result/duration;
17. safety/original asset invariance;
18. deterministic verdict and any explicit capability gaps;
19. artifacts/result paths;
20. commit SHA/push state;
21. final N-07 / Phase N state.
