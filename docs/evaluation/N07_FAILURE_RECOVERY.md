# N-07 — Failure / Recovery — Reference Workstation Result

Updated: 2026-10-24

**N-07 = Complete / FAIL. Phase N = Active / Not Complete.**
The deterministic evaluator proves missing required recovery coverage. This is not
an environment blocker or a measured time overrun. Next task is **N07-R01 — Composite
canonical / Raw / Provenance backup and restore** (Required / Not Started).
Neither product remediation nor Phase N closure audit was started.

## Source and execution

- Baseline clean main/origin-main: `19bd646d1d14aff946896e6eefb3eaf155625383`.
- Measured clean branch: `n07-failure-recovery`.
- Measured HEAD: `e78cf81a1c7d1daddfed729146579b4aacff8434`.
- Run: `20261024T201856+0900`; local evidence: `.local/n07/20261024T201856+0900/` (not committed).
- Aggregate: `benchmark/results/n07-failure-recovery.json`.

A preflight/baselines -> B exchange -> C transaction/crash -> D I/O -> E derived
outage -> F generation -> G corruption -> H offline/MCP -> I backup/restore ->
J evaluator/safety/regression all completed. Harness/tests were committed first.
Contract, product behavior and model were unchanged. 50 cases: **47 PASS / 3 FAIL /
0 BLOCKED cases**. Numeric RPO/RTO hard gates remain null; their missing-measurement
diagnostics are retained, while proven coverage failure makes overall verdict FAIL.

## Preflight and runtime

Python 3.10.6; pytest 9.1.1; Ruff 0.17.0; PyTorch 2.6.0+cu124;
Transformers 5.20.1; sentence-transformers 6.1.0; qdrant-client 1.19.1; MCP 2.3.0.
Windows Reference Workstation; free disk 96.667 GiB.
No package/runtime update was made.

Preflight: focused **38 passed**, full **727 passed**; repository-wide Ruff,
changed-file format, compileall and working/staged diff PASS. Tested source-tree
identity was verified before the measurement commit. Post-run focused **38 passed**
(22.45 s), full **727 passed / 0 failed** (180.55 s), two existing Qdrant local-mode
warnings; Ruff and diff PASS.

## B — Invalid/stale/partial exchange

| Case | Fault | Result |
|---|---|---|
| B01 | Invalid Result schema | PASS |
| B02 | package_id mismatch | PASS |
| B03 | manifest SHA mismatch | PASS |
| B04 | Stale base Version | PASS |
| B05 | Immutable Result byte-count mismatch | PASS |
| B06 | Immutable Result SHA mismatch | PASS |
| B07 | Truncated JSON | PASS |
| B08 | Missing declared Package file | PASS |
| B09 | Package size mismatch | PASS |
| B10 | Package SHA mismatch | PASS |
| B11 | Unexpected Package layout/file | PASS |

All faults were explicitly rejected; current Version/import state remained
consistent and no partial finalized Package appeared. Valid artifact retries
succeeded after removing faults. A stale Package remains stale and must be replaced
with a freshly bound Package; it was not silently rebound.

## C — Transaction/crash

All three checkpoints (`candidate_created`, `knowledge_written`, `accepted` before
commit) PASS: digest equals pre-import state, no partial accepted Version or
successful import survives, integrity/FK checks clean, valid retry succeeds.
A supporting disposable child was killed only after its explicit `knowledge_written`
checkpoint. Reopening SQLite yielded the old committed state and clean integrity.
Normal Codex/reference services were not killed.

## D — ENOSPC/I/O

Product copyfile, restore copy2 and export copytree were injected with OS-style
ENOSPC after writing partial bytes. **3/3 PASS**: no completed partial artifact,
previous restore target preserved, temporary state cleaned/non-final, retry succeeds.
No drive-fill, quota mount or security/network configuration change was used.

## E — Derived outage/recovery

Provider failure, Qdrant read outage, Vector update failure, stale/missing state and
normal maintenance recovery **5/5 PASS**. Canonical Version remains accepted;
R2 Hybrid exposes explicit semantic degradation while Semantic-only raises the
runtime error. There is no silent provider/cloud/CPU/backend substitution.
An exclusively reserved non-listening localhost endpoint models Qdrant outage;
reference Qdrant was never stopped. Deterministic fault fixtures exercise normal
production maintenance; live frozen Harrier evidence is separate in H/I.

## F — Generation/backend recovery

Build failure, invalid cutover, failed smoke/pointer recovery, interrupted build,
valid isolated rebuild and compatible rollback **6/6 PASS**. Supported lifecycle
APIs preserve/recover the prior pointer. Real Qdrant in-memory adapter tests cover
namespace separation, cutover/rollback/re-cutover and membership/point identity.
No reference namespace or direct active-pointer table write was used.

## G — Raw/Provenance corruption

Result tamper, Package tamper, copied FK corruption and copied Raw loss detection
**4/4 PASS**. `system integrity` detects FK damage. Product Snapshot reprocessing
rejects missing Raw, although SQLite-only integrity stays clean. Detection does not
imply backup recovery coverage.

The physical fixture follows Capture -> Normalize/Evidence -> confirmed association
-> Package stage/export -> validated Result import. Capture bytes pass the product
importer before loss injection. Only disposable Raw and incoming Result bytes are
quarantined; failed evidence is retained. No benchmark-only recovery copier exists.

## H — Offline/provider/MCP

**5/5 PASS**. Process-local network denial preserves canonical/Lexical read.
Live cached Harrier: `microsoft/harrier-oss-v1-0.6b`, revision
`f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, CUDA/bfloat16/1024 dimensions,
local-files-only, finite output, **socket connection attempts 0**, no CPU/cloud
fallback. Missing provider remains explicit.
Run-owned real MCP stdio access works, shuts down, then restarts. Direct Application
and CLI Object reads work while MCP is closed; restart leaves canonical state unchanged.

## I — Recovery inventory and measured coverage

| Inventory | Required fixture contents | Supported backup coverage |
|---|---|---|
| SQLite | Canonical/Identity/history/provenance rows | Yes |
| Raw store | 9 member rows in one physical capture bundle | **No** |
| External provenance | Accepted original Result and capture bundle/manifest | **No** |
| Recovery metadata | Raw resolution and incoming root, no plaintext secrets | **No** |
| Rebuildable derived | Search representations/Embedding/Vector/render | Excludable if rebuilt |

Implementation inventory: `system_ops.create_backup` performs SQLite Online Backup
and SQLite integrity check. `backup_status` lists SQLite; `restore_plan/apply`
validate/copy/replace SQLite only. Source import retains external bundle references;
accepted imports retain external original Result references. No composite recovery
inventory/archive or Raw/Result/config restore surface was found.

Reproducible proof: valid physical Raw and accepted original Result exist at backup
point; destination contains SQLite only (plus SQLite-generated WAL/SHM sidecars
from later access). After disposable originals are quarantined, product restore
reproduces the DB digest but cannot supply Raw for Snapshot reuse or Result bytes
for immutable audit. Inventory still references missing external artifacts.

I01-I07, I09-I10 PASS. **I08 Raw/Provenance recovery, I11 complete-canonical RPO
capability, I12 complete-canonical RTO FAIL**. Underlying tests PASS by asserting the
observed gap; formal case verdicts intentionally stay FAIL.

Representative I08 measurements (small fixture):

- SQLite backup: **0.015168600 s**.
- SQLite restore copy/replace: **0.011564900 s**.
- Restore start through DB digest/integrity + Object/Lexical read:
  **0.029456700 s**.
- Restored digest equals backup point; integrity `ok`, FK violations 0.
- Required Raw/Provenance reusable state: **never reached**.

Those DB-subset times do not establish canonical RTO. Separate isolated verification
time was not captured. Complete-canonical RPO/RTO stay null, not estimated and not
classified as a measured 24 h/4 h exceedance. Daily SQLite backups cannot establish
a complete <=24 h recovery point when required files are absent. Multiple explicit
backup destinations/generation names are possible; daily >=7 / weekly >=4 retention
targets remain. Scheduler/rotation is Phase O and its absence alone is not this FAIL.

Post-restore R2 rebuild/cutover/audit PASS with live frozen Harrier CUDA and isolated
Qdrant memory: 2 memberships/2 points, **0.123849200 s**
for lifecycle work. This excludes provider initialization and fixture/legacy
Embedding preparation; it is not a reference-scale full rebuild estimate and is
separate from the canonical four-hour RTO.

## J — Verdict, safety and historical attempts

Independent evaluator replay exactly matches the original **FAIL**. Decisive gap:
required Raw/Provenance restore coverage (I08/I11/I12). No requirement was relaxed.
Original/reference canonical fingerprints, original N-03, reference Qdrant point
fingerprints/inventory and three R1 asset SHA-256 values are unchanged. Measurement
HEAD/tracked state unchanged; no run-owned process remains. Global network/security
settings and original restore targets were never changed.

Historical `20261024T171708+0900` at source
`d17a48032da3b0b2cb515257110fdecaee5f61c3` is invalid for product acceptance:
missing pytest base-temp parents caused setup errors; launcher ancestry produced a
false residue report. Original FAIL evaluation/logs remain untouched. Corrected
harness creates owned fixture parents, labels setup errors BLOCKED and distinguishes
live launcher ancestors. Safety Gate conditions/product semantics remain unchanged.
Corrected source was fully preflighted and committed before this new run. Preparation
controls that stopped before execution also remain locally; nothing was overwritten.

## Required next task

**N07-R01 — Composite canonical / Raw / Provenance backup and restore**

Required / Not Started. In a separate task, provide supported consistent SQLite +
referenced Raw/capture + retained original Result/provenance + secret-free recovery
metadata generations. Record checksums and DB/file consistency points, corruption
verification, safe atomic output and supported restore/path resolution. Re-accept
under unchanged RPO <=24 h / canonical+Raw/Provenance RTO <=4 h; derived rebuild
timed separately; keep daily/weekly retention targets. No benchmark-only workaround.

```text
N-07 = Complete / FAIL
N-01 ... N-06 = Complete
N07-R01 = Required / Not Started
Phase N closure audit = Not Started / blocked by remediation
Phase N = Active / Not Complete
```

## Local artifacts

`.local/n07/20261024T201856+0900/` retains evidence/evaluation/status JSON, case logs/JUnit reports, copied DBs,
backup/quarantine artifacts and observation JSON; offline provider proof; original
and Qdrant before/after fingerprints; process audit; post-focused/full/Ruff/diff logs.
Preflight logs/tree proof: `.local/n07-control/20261024T201531+0900/`.
Only sanitized aggregates, source/tests and documentation are published.
