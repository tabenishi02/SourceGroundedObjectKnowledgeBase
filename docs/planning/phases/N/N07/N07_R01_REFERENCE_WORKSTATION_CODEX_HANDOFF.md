# N07-R01 — Reference Workstation Codex handoff

Status: **Formal PASS candidate / result review pending**
Branch: `n07-r01-composite-backup-restore`  
Do not merge to `main` automatically.

## 1. Objective

Complete N07-R01 locally on the Reference Workstation by validating and, where necessary, correcting the GitHub implementation candidate for complete-canonical composite backup/restore.

The original N-07 verdict remains `Complete / FAIL` until this remediation obtains a new formal PASS. Do not rewrite or erase the historical FAIL evidence.

## 2. Start here

Read, in order:

1. `docs/planning/phases/N/N07/N07_R01_COMPOSITE_BACKUP_RESTORE.md`
2. `benchmark/n07-r01-composite-backup-restore-contract-v1.json`
3. `docs/evaluation/N07_FAILURE_RECOVERY.md`
4. `docs/planning/phases/N/N07/N07_FAILURE_RECOVERY_ACCEPTANCE.md`
5. `src/sgokb/composite_recovery.py`
6. `tests/test_n07_r01_composite_recovery.py`
7. existing `tests/test_n07_failure_recovery.py`
8. existing `benchmark/tools/n07_failure_recovery.py`
9. existing `benchmark/tools/n07_evaluate_failure_recovery.py`

The remediation branch currently contains a product implementation candidate and focused tests created through GitHub. They have **not** been executed locally. Treat them as code to review and validate, not as already accepted implementation.

## 3. Branch / safety preflight

1. Fetch the repository and check out `n07-r01-composite-backup-restore`.
2. Confirm the working tree before modification.
3. Record branch HEAD and its `main` merge-base.
4. Preserve the existing N-07/R1 local user-aborted assets byte-for-byte. Record their pre-run SHA-256 values using the same asset set and method as the N-07 formal run.
5. Do not reset, clean, overwrite, delete, or regenerate those R1 assets.
6. Do not use production canonical data as a destructive target. All fault/restore tests must use a unique N07-R01 run root below `.local/n07-r01/<run-id>/` or an equivalent isolated run-owned root.
7. Fail/BLOCK if the branch cannot be cleanly identified or the safety inventory cannot be established.

## 4. Review the implementation candidate before running formal acceptance

Review `src/sgokb/composite_recovery.py` against the machine-readable contract. Correct the branch implementation if necessary.

Mandatory properties:

- SQLite Online Backup is created first.
- Raw/Result inventory is read from the packaged SQLite snapshot, not the live DB.
- every Snapshot with `raw_artifacts` closes to exactly one physical Web Capture bundle;
- original Web Capture basename is preserved because `WebCaptureImporter` validates timestamp/UUID filename identity;
- physical Raw bundle, member SHA/bytes, Snapshot `bundle_sha256`, and capture UUID all agree;
- all accepted `object_result_imports` close to an original immutable `result.json` below the caller-supplied incoming root;
- Result `storage_ref` remains safe incoming-root-relative;
- recovery metadata contains no plaintext secrets and no original absolute Raw/incoming roots;
- manifest is written last and staging directories are not accepted generations;
- verify rejects missing/extra/tampered/unsafe/symlink dependencies;
- restore verifies before target mutation;
- restore changes only `raw_artifacts.storage_ref` for Raw relocation;
- Result import/provenance audit rows remain unchanged;
- staged restored DB passes `PRAGMA integrity_check` and `PRAGMA foreign_key_check`;
- database publication is the final completion marker after external bytes are staged/published;
- failure before database publication does not leave an accepted partial restore;
- legacy SQLite-only backup/restore semantics remain unchanged.

Pay particular attention to publication rollback and pre-existing-target behavior. If the implementation candidate cannot make a safe guarantee for non-empty external roots, retain the documented conservative policy and fail closed. Formal acceptance must use isolated alternate roots rather than weakening this protection.

## 5. CLI integration — local edit required

Safely wire explicit composite commands into `src/sgokb/cli/main.py`. Do not change the meaning of existing commands.

Recommended command surface:

```text
sgokb system backup composite create --incoming-root <path> [--output <dir>] [--root <dir>]
sgokb system backup composite verify <generation>
sgokb system restore composite plan <generation> --db-target <db> --raw-root <dir> --incoming-root <dir>
sgokb system restore composite apply <generation> --db-target <db> --raw-root <dir> --incoming-root <dir> [--acknowledge-overwrite]
```

If the existing parser structure requires a slightly different explicit nesting, keep the semantics unambiguous and document the final commands. The following legacy commands MUST remain SQLite-only and backward-compatible:

```text
sgokb system backup create
sgokb system backup status
sgokb system restore plan
sgokb system restore apply
```

Add focused CLI tests for the final surface.

## 6. Focused tests

Run and repair, as needed:

```text
pytest -q tests/test_n07_r01_composite_recovery.py
pytest -q tests/test_n07_failure_recovery.py
```

Add/adjust focused tests so the contract is directly demonstrated, including at minimum:

1. complete generation contains SQLite + Raw + accepted Result + recovery metadata;
2. dependency inventory remains bound to the SQLite snapshot if the live DB changes after snapshot creation;
3. missing Raw fails closed and does not finalize a generation;
4. missing accepted Result fails closed and does not finalize a generation;
5. tampered packaged bytes fail verification;
6. unsafe Result relative paths fail closed;
7. Raw bundle basename identity is preserved;
8. alternate-root restore rewrites only Raw `storage_ref` and existing product reprocessing succeeds;
9. alternate-root restore preserves accepted Result relative ref and `load_immutable_result_artifact` succeeds;
10. restore plan is read-only;
11. overlapping/unsafe targets are rejected;
12. interrupted/incomplete staging generation is rejected;
13. recovery metadata contains no secret/original absolute roots;
14. legacy SQLite-only backup/restore remains unchanged;
15. final CLI composite operations exercise the same product functions.

Do not weaken a product check merely to make the test pass.

## 7. Formal Reference Workstation recovery drill

After focused tests pass, perform a new isolated formal run.

### A. Build a realistic complete-canonical fixture

The fixture must contain, at minimum:

- one imported and processed Web Capture Snapshot with physical Raw bundle;
- canonical Evidence derived from that Raw;
- one Object Evidence Package;
- one received, validated, and accepted Object Result;
- `object_result_imports` and receipt provenance pointing at the immutable original Result;
- enough canonical state to verify post-restore Object/version/provenance reads.

The fixture must be generated under the run-owned root. Do not reconstruct or modify production canonical inputs.

### B. Create and verify composite backup

Use the product CLI/API, not an ad-hoc copy script.

Record:

- measured source commit;
- backup generation ID;
- creation start/end timestamps;
- SQLite SHA/bytes;
- Raw bundle identities/count;
- Result identities/count;
- complete dependency closure result;
- manifest/recovery metadata identity;
- backup age used for RPO evaluation.

Required complete-canonical RPO: `<= 24h`.

### C. Prove source-store independence

After the backup is verified, quarantine or make inaccessible the fixture's original Raw and incoming Result roots inside the isolated run root. Do not touch external user assets.

A successful restore must not depend on the original external locations.

### D. Alternate-root restore

Restore to entirely new isolated targets:

- alternate canonical SQLite path;
- alternate Raw root;
- alternate incoming Result root;
- restored recovery metadata target.

Measure canonical restore start/end and elapsed seconds.

Required canonical RTO: `<= 14,400s`.

### E. Product-level restored proofs

Using the restored database and alternate external roots, prove all of the following:

- `PRAGMA integrity_check` = `ok`;
- `PRAGMA foreign_key_check` = no violations;
- canonical Object/version/evidence/provenance identity equals the backup point;
- restored Raw `storage_ref` resolves only below the alternate Raw root;
- `Application.process_source_snapshot` can reopen/reprocess the restored Raw bundle;
- accepted `result_storage_ref` remains byte-for-byte the same relative reference;
- `load_immutable_result_artifact` can reopen the restored original Result below the alternate incoming root;
- Result SHA/byte count equal the accepted import audit;
- recovery metadata is available and contains no plaintext secret/original absolute root.

### F. Negative drills

Against disposable copies, prove fail-closed behavior for at least:

- missing Raw bundle;
- missing original Result;
- Raw hash corruption;
- Result hash corruption;
- manifest corruption/path traversal;
- incomplete generation without valid `manifest.json`;
- overlapping restore targets;
- non-acknowledged overwrite attempt.

### G. Derived rebuild

Derived Search/Embedding/Vector/Render state remains outside canonical restore RTO. Exercise the existing N-07 derived rebuild path separately and record its elapsed time under the existing N-07 threshold. Do not fold this duration into canonical restore RTO.

## 8. Regression / static verification

After all implementation fixes:

- run the full pytest suite;
- run Ruff using the repository's accepted command/configuration;
- run `git diff --check`;
- run Python compile/import checks used elsewhere in Phase N;
- apply the repository's formatting checks to changed Python files;
- record all warnings rather than hiding them.

No model, retrieval scoring, generation policy, quality gate, or N-07 threshold may be changed as part of this remediation.

## 9. Formal result artifacts

Create committed evidence on this branch, following existing N-06/N-07 conventions. At minimum:

- `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`
- `benchmark/results/n07-r01-composite-backup-restore.json`

The result must include:

- run ID;
- measured commit;
- Reference Workstation identity;
- focused/full regression results;
- complete canonical dependency inventory;
- RPO evidence;
- canonical restore RTO evidence;
- post-restore product proofs;
- negative-drill results;
- derived rebuild timing separately;
- legacy compatibility proof;
- pre/post R1 user-aborted asset hashes;
- final deterministic verdict.

PASS only if every frozen N07-R01 gate is satisfied. Otherwise publish FAIL/BLOCKED with the exact cause.

## 10. Commit / push policy

When local validation is complete:

1. review all diff for scope;
2. commit implementation/test/CLI/formal-harness corrections to `n07-r01-composite-backup-restore`;
3. run formal acceptance on the exact commit intended as measured source;
4. commit the formal result artifacts separately after the measured run;
5. push the branch;
6. report both the measured-source commit and result-publication commit;
7. leave `main` unchanged and do not auto-merge.

If formal acceptance passes, report `N07-R01 = formal PASS candidate` for ChatGPT review. Do not independently rewrite `N-07 = Complete / PASS` or Phase N completion state before review.


## 11. Executed Reference Workstation result

Run `20261024T222300+0900`, measured source
`ffb16e9f7e0e24c8c2648a04430fca57bfb71dfb`, formal evaluator PASS.
All requested product/CLI/negative/recovery/safety proofs and pre/post regression
completed. Review `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`
and `benchmark/results/n07-r01-composite-backup-restore.json`.
Disposition remains **formal PASS candidate for ChatGPT review**; N-07/Phase N
accepted state and main are unchanged. Do not infer an automatic merge/closure.
