# N07-R01 — Composite Recovery Reference Workstation Re-acceptance

Updated: 2026-10-24

**Formal verdict: PASS. N07-R01 = Complete / PASS candidate, pending ChatGPT review.**
N-07 remains **Complete / FAIL** in accepted state; Phase N remains **Active / Not
Complete**. No main merge, N-07 state finalization, remediation beyond this feature,
or Phase N closure audit was performed.

## Run/source identity

- Feature branch: `n07-r01-composite-backup-restore`.
- Initial remote candidate: `a81ef8a5d53eef48d8bb6a0e52d548aef7647336`.
- Measured clean source commit: `ffb16e9f7e0e24c8c2648a04430fca57bfb71dfb`.
- Main/merge-base: `fc7609db60a310cd153aa256a5fe183e44ab8fcb` (unchanged).
- Run ID: `20261024T222300+0900`.
- Raw evidence: `.local/n07-r01/20261024T222300+0900/` (not committed).
- Aggregate: `benchmark/results/n07-r01-composite-backup-restore.json`.

Python 3.10.6, Windows 11, RTX 4090 (24564 MiB), driver 581.80;
PyTorch 2.6.0+cu124, Transformers 5.20.1, sentence-transformers 6.1.0,
qdrant-client 1.19.1, MCP 2.3.0, pytest 9.1.1, Ruff 0.17.0.
No package/model/runtime update was made. GPU process observations remain local.

## Implementation review and corrections

The upstream candidate had not been validated locally. Review/focused tests found:

- SQLite verification could open a writable connection/create sidecars. Verification
  now uses immutable read-only SQLite; packaged snapshots are self-contained DELETE
  journal files. Existing snapshot test was corrected to inspect the immutable backup
  read-only, instead of mutating its header through `Repository`.
- `resolve()` could hide symlinks before inspection. Lexical components now reject
  symlinks/reparse points before resolution. Unsafe POSIX/Windows segments and
  unexpected layout/metadata are rejected.
- Public verification now rejects staging directories even if they contain a manifest;
  internal creation validates staging before atomic finalization.
- Packaged Raw/Result paths and counts are bound to the SQLite snapshot; Result receipt
  and import identities are rechecked against packaged bytes, without original roots.
- Restore now tracks all staging paths before copy, cleans partial staging, restores
  old metadata/empty external roots after pre-DB-publication faults, and preserves the
  old DB. Active SQLite sidecars and non-empty external roots fail closed. All staged
  validation precedes the final atomic DB publication.
- Explicit Composite CLI is wired; existing SQLite-only commands retain their meaning.
- An upstream basename assertion incorrectly removed the original `.zip` suffix when
  comparing a quarantine name; it now checks the original full basename directly.

No N-07 acceptance Gate, frozen contract, retrieval/scoring, Harrier or generation
policy changed. Historical N-07 FAIL tests/evidence remain intact.

## CLI surface and compatibility

```text
sgokb --db <source.sqlite> system backup composite create --incoming-root <incoming> --output <generation>
sgokb system backup composite verify <generation>
sgokb system restore composite plan <generation> --db-target <db> --raw-root <raw> --incoming-root <incoming>
sgokb system restore composite apply <generation> --db-target <db> --raw-root <raw> --incoming-root <incoming> [--acknowledge-overwrite]
```

Verify and restore are handled before opening an unrelated default Repository.
CLI tests exercise the same product functions, verify plan/read-only behavior and
reject unacknowledged overwrite. Existing `system backup create/status` and
`system restore plan/apply` remain SQLite-only and their legacy tests PASS.

## Complete-canonical inventory and consistency point

Run-owned physical Web Capture -> Normalize/Evidence -> confirmed association ->
Package stage/export -> received/validated/accepted Result formed the fixture.
Before the first accepted Version, the supported empty-R2 bootstrap created the
frozen Embedding Space/namespace identity without loading Harrier.

Generation `70317490-3c1f-4c22-98b7-759f00beac0c` contains:

| Dependency | Evidence |
|---|---|
| Canonical SQLite | 1060864 bytes; SHA `37e146babf4df531af010d9ff41931ed681a2c1e493d300ef3ae65706f3ed5dc` |
| Raw store | One physical capture bundle, nine logical Raw rows; original timestamp/UUID basename preserved |
| Original Result | One accepted immutable `result.json`; import/receipt identity and relative ref retained |
| Recovery metadata | 450 bytes; SHA `2bfe4bdb6fedcdacaba18c42ae2eb8cb7b04ace8c23e2bc920119a7f1f8a0b09` |
| Manifest | SHA `7535099cfe4a4ce43cb06ccbb74b765ae774ff9edaa3aa4d5997db461a44f08c` |

SQLite Online Backup is taken first; dependency closure comes from that packaged
snapshot, not a changing live DB. A focused post-snapshot live mutation test proves
the inventory remains bound to the snapshot. Manifest is written last and validated
before final directory publication. Verification does not mutate packaged bytes.
Recovery metadata contains fixed non-secret relocation semantics and no original
absolute roots. Derived artifacts are rebuildable and excluded from canonical RTO.

## Alternate-root restore and product proofs

Original fixture Raw and incoming Result stores were quarantined, retained and made
inaccessible at their former paths. Product restore used wholly new DB/Raw/incoming
roots and a restored metadata target. No original/reference assets were targeted.

PASS evidence:

- Before reprocessing, all-table canonical identity equals backup point except only
  `raw_artifacts.storage_ref` relocation. Raw immutable fields are unchanged.
- Raw references resolve strictly inside the alternate root, preserving basename;
  `Application.process_source_snapshot` reopens/reprocesses restored bytes.
- Accepted Result audit rows/relative ref are unchanged;
  `load_immutable_result_artifact` reopens the alternate incoming-root bytes and
  matches accepted SHA/byte count.
- SQLite integrity `ok`, FK violations 0; canonical Object/version/provenance read
  and minimum Lexical retrieval succeed.
- Restored metadata verifies; generation remains byte-identical after verify/restore.

Independent review reopened the backup/Raw/Result read-only and replayed the evaluator.
Reprocessing intentionally appends normalization/evidence history on the disposable
restored DB; original rows remain present. Other canonical core identities remain
unchanged. Derived rebuild then preserves that post-reprocessing canonical state.

## RPO/RTO measurements

- Backup procedure start: `2026-10-24T13:26:32.119000+00:00`.
- Generation manifest creation: `2026-10-24T13:26:32.158621+00:00`.
- Restore start: `2026-10-24T13:26:32.365103+00:00`.
- Composite create + verification: **0.107322000 s**.
- Product restore stage/validation/publication: **0.072726100 s**.
- Full canonical RTO through Raw reprocessing, original Result audit, SQLite/FK,
  metadata and Object/Lexical availability: **0.129272400 s <= 14400 s**.
- Conservative complete backup age since procedure start:
  **0.000104199722 h <= 24 h**.
- Two independently completed/verified Composite generations demonstrate repeatable
  daily-equivalent backup capability; no 24-hour wait or scheduler implementation is
  claimed. Daily >=7 / weekly >=4 retention targets and Phase O scheduler boundary
  remain unchanged.

These are measurements of the required small complete fixture, not extrapolations
of production-scale recovery. Full derived recovery is outside this RTO.

## Negative faults

Eight formal drills PASS: missing Raw, missing Result, corrupt Raw hash, corrupt
Result hash, manifest traversal, incomplete generation, overlapping restore targets,
unacknowledged overwrite. Rejections are explicit and copied failures are retained.

Focused tests additionally prove partial-copy/ENOSPC and raw/incoming/metadata/DB
publication failure rollback with existing DB/metadata, absent or empty external
roots; rejection of non-empty/live targets, staging generations, undeclared files,
unsafe paths and unexpected metadata. No system-drive fill, security change,
global network disable or reference-process termination was used.

## Derived rebuild and audit (separate)

The **same restored fixture DB** was rebuilt with normal generation-aware
representation/Embedding/Vector maintenance and Render, then audited. Harrier
`microsoft/harrier-oss-v1-0.6b`, revision
`f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, CUDA/bfloat16/1024 dimensions,
local-files-only; no fallback, truncation or model substitution.

Elapsed **9.155151900 s including provider load**.
Generation `search-generation:r2:f45e9260-6363-4600-aef1-e405763aaacc`: 2 memberships / 2
points, family `object_overview, statement`, active `object_overall` leakage 0.
This fixture has no content Facet representation to rebuild; it does not invent one.
Generation/membership/vector audit, Semantic read, Render and canonical preservation
PASS. Real Qdrant in-memory adapter is run-owned; reference service is untouched.
This is a small recovery proof, not a full reference-scale ANN/performance benchmark.

## Regression, safety and disposition

Formal Composite tests: **45 passed / 0 failed / 0 skipped**.
Pre/post combined focused: **83 passed**; pre/post full: **772 passed / 0 failed**.
Post focused 59.37 s; post full 222.74 s. Two Qdrant local-mode warnings are retained.
Repository-wide Ruff, changed-file format, compileall and diff checks PASS.

Initial implementation-before fingerprints and formal before/after fingerprints
match. R1 three asset SHA-256 values remain byte-identical; original N-03/reference
canonical and Raw assets, reference Qdrant inventory/full point fingerprints,
measurement HEAD/tracked tree and local main are unchanged. No run-owned child
process remains. Before/after R1 hashes are in the sanitized aggregate; full private
inventories/logs remain local.

Deterministic evaluator: **PASS**, failures/blocked lists empty. This is a
**N07-R01 Complete / PASS candidate** for ChatGPT review only. Accepted N-07 remains
Complete / FAIL, Phase N Active / Not Complete. No main merge or closure audit.
Raw evidence is under `.local/n07-r01/20261024T222300+0900/`; control/preflight logs
under `.local/n07-r01-control/20261024T220438+0900/`. No raw DB/store/log/cache is
committed. Source corrections and result publication use separate commits.


## Review disposition accepted (2026-10-24)

<!-- phase-n-current:start -->
N07-R01 = Complete / PASS — ChatGPT review accepted 2026-10-24
N-07 = Complete / PASS after accepted remediation
<!-- phase-n-current:end -->

ChatGPT independently compared the GitHub branch/result, reviewed the supported
product Composite implementation and explicit CLI, and accepted the formal PASS as
N07-R01 Complete/PASS. Accepted result commit:
`9cda43e9303488d2b0905f61fa3dbbed4f03a4fb`.
This disposition supersedes review-pending state in the original measurement narrative
above; its run/source, limits, timings and historical N-07 FAIL are not rewritten.
Phase N closure remains a separate formal audit; no Phase O task is started here.
