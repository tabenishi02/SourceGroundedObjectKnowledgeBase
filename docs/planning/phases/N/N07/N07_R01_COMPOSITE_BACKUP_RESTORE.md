# N07-R01 — Composite canonical / Raw / Provenance backup and restore

Status: **Implementation candidate / formal re-acceptance pending**  
Parent: **N-07 — Failure / Recovery**  
Authoritative source: GitHub `main` for accepted project state; this remediation is developed on `n07-r01-composite-backup-restore` until formal re-acceptance.

## 1. Purpose

N-07 formal acceptance established that the existing SQLite-only backup can restore the database but does **not** constitute a complete canonical recovery point. The canonical database contains references to external Raw Web Capture bundles and accepted immutable Object Result inputs. If those bytes are lost, SQLite integrity can still pass while provenance reuse and Raw reprocessing fail.

N07-R01 closes that specific recovery gap without changing canonical knowledge semantics, search ranking, generation behavior, or the legacy SQLite-only backup commands.

Until Reference Workstation re-acceptance passes, the authoritative status remains:

- N-07: `Complete / FAIL`
- N07-R01: `Implementation candidate / formal re-acceptance pending`
- Phase N: `Active / Not Complete`

## 2. Frozen recovery boundary

A complete canonical recovery point consists of all of the following at one frozen consistency point:

1. canonical SQLite database snapshot;
2. every physical Raw Web Capture bundle referenced by the SQLite snapshot;
3. every original accepted immutable Object Result required by `object_result_imports`;
4. provenance identity needed to bind those bytes to canonical records;
5. non-secret recovery metadata sufficient to relocate external stores.

The following are rebuildable derived state and are intentionally outside the canonical restore RTO:

- Search Representation;
- Embedding;
- Vector Index;
- rendered outputs.

Derived rebuild is measured separately by the existing N-07 contract.

## 3. Consistency-point rule

The backup MUST establish the database consistency point first:

1. create `canonical/canonical.sqlite` with SQLite Online Backup;
2. run SQLite integrity checks on that snapshot;
3. inventory Raw and Result dependencies **from the snapshot**, never from the subsequently changing live database;
4. copy and verify exactly those dependencies;
5. write recovery metadata;
6. write `manifest.json` last;
7. verify the staged generation completely;
8. atomically rename the staged generation to its final backup path.

A live-database mutation after step 1 MUST NOT change the dependency closure of that backup generation.

## 4. Composite generation layout

```text
<generation>/
├─ canonical/
│  └─ canonical.sqlite
├─ raw/
│  └─ <snapshot-id>/
│     └─ <original-webcapture-basename>.webcapture.zip
├─ provenance/
│  └─ <original incoming-root-relative result path>
├─ metadata/
│  └─ recovery.json
└─ manifest.json
```

The Raw bundle basename is part of the recoverability contract. `WebCaptureImporter` validates the filename against the capture timestamp and capture UUID, so the backup MUST preserve the original basename rather than normalizing it to a generic filename.

`manifest.json` is the completion marker. A staging directory or a directory without a valid manifest is not a usable backup generation.

## 5. Manifest identity and integrity

The composite manifest uses schema `sgokb.composite-backup.v1` and records:

- generation UUID;
- UTC creation time;
- consistency model;
- canonical SQLite packaged path, SHA-256, and byte count;
- one Raw physical-bundle entry per canonical Snapshot that owns Raw artifacts, preserving the original bundle basename;
- accepted Result entries with import/receipt identity, original safe relative `storage_ref`, SHA-256, and byte count;
- recovery metadata packaged path, SHA-256, and byte count.

Every packaged path MUST be a safe generation-relative POSIX path. Absolute paths, `..`, duplicate packaged paths, symlinks, missing files, hash drift, and byte-count drift fail closed.

## 6. Raw recovery and relocation

Current canonical Raw rows store the physical `.webcapture.zip` path in `raw_artifacts.storage_ref`. Multiple logical Raw rows for the same Snapshot point to the same physical bundle.

For each Snapshot, N07-R01 therefore:

- requires all Raw rows to resolve to one physical bundle;
- validates that physical bundle against the Snapshot's canonical `metadata_json.bundle_sha256`;
- validates the bundle through the existing `WebCaptureImporter`, including member checksums and filename identity;
- copies the physical bundle once to `raw/<snapshot-id>/<original-webcapture-basename>.webcapture.zip`;
- records the Snapshot-to-packaged-bundle mapping in the manifest.

On restore to another Raw root, the restored SQLite database rewrites only `raw_artifacts.storage_ref` for the corresponding Snapshot to the final restored physical file path. The original basename is retained so the existing importer can reopen the restored bundle without a special recovery-only bypass.

This relocation is compatible with the existing schema: `raw_artifacts` content identity fields are immutable, but `storage_ref` is intentionally not part of the immutable content-identity trigger. `snapshot_id`, artifact kind, logical path, media type, SHA-256, and byte count MUST NOT be changed.

## 7. Original Result / provenance recovery

Accepted Result provenance stores a safe incoming-root-relative `result_storage_ref`. N07-R01 takes `incoming_root` explicitly and:

- rejects absolute or parent-traversing Result references;
- resolves the original immutable `result.json` strictly below that root;
- validates its SHA-256 and byte count against `object_result_imports`;
- preserves the same relative path below `provenance/`.

Restore recreates that relative tree below the new `incoming_root`. No accepted import audit field is rewritten.

## 8. Recovery metadata

`metadata/recovery.json` contains only non-secret recovery semantics, including:

- composite schema/version;
- Raw relocation strategy;
- Result relative-root strategy;
- rebuildable-derived classification.

It MUST NOT persist plaintext secrets, credentials, access tokens, or the original absolute Raw/incoming roots.

## 9. Restore safety

Composite restore MUST verify the backup before writing targets. It then restores into staging paths, validates the staged SQLite database and external dependencies, and only then publishes the targets.

Required safety properties:

- backup generation cannot be a restore target;
- database, Raw root, and incoming root cannot overlap one another;
- an existing target requires explicit overwrite acknowledgement;
- unsafe manifest paths fail before any target mutation;
- corrupted or incomplete generations fail closed;
- failure before final publication leaves no accepted partial generation/restore;
- legacy SQLite-only `create_backup` / `restore_apply` behavior remains unchanged.

The initial product contract may conservatively reject non-empty existing Raw/incoming directories even with acknowledgement if safe atomic replacement cannot be guaranteed. Formal re-acceptance uses isolated alternate roots.

## 10. Acceptance thresholds

N07-R01 does not relax the frozen N-07 thresholds:

- complete canonical RPO: `<= 24 hours`;
- canonical restore RTO: `<= 14,400 seconds` (4 hours);
- derived rebuild: measured separately under the existing N-07 limit.

A PASS requires restoration of database + Raw + original Result/provenance + recovery metadata, followed by product-level proof that:

1. restored canonical reads succeed;
2. a restored Raw bundle can be reprocessed through `Application.process_source_snapshot`;
3. an accepted original Result can be reopened through `load_immutable_result_artifact` under the restored incoming root;
4. SQLite integrity and foreign-key checks pass;
5. provenance identity and content hashes remain equal to the backup point.

## 11. Implementation boundary

Product implementation is isolated in `sgokb.composite_recovery` and must not redefine legacy backup semantics. CLI wiring may expose explicit composite commands, but existing `system backup create` and `system restore plan|apply` remain SQLite-only.

Focused tests are added separately from the historical N-07 FAIL test so the previous failure evidence is preserved rather than rewritten.

## 12. Completion rule

N07-R01 is **not Complete** when code merely exists or unit tests pass. It becomes `Complete / PASS` only after the Reference Workstation formal re-acceptance:

- uses the frozen machine-readable N07-R01 contract;
- records the measured source commit;
- records RPO/RTO and dependency-closure evidence;
- passes focused and full regression suites;
- confirms local R1 user-aborted assets remain byte-identical;
- publishes committed result evidence for review.

No automatic merge to `main` is permitted before that review.
