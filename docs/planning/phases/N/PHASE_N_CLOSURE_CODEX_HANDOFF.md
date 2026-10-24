# Phase N Closure Audit — Reference Workstation Codex Handoff

Updated: 2026-10-24

## 1. Mission

Complete the formal Phase N closure audit on the Reference Workstation without weakening any accepted N-01..N-07 gate and without rerunning expensive historical benchmarks unnecessarily.

Repository:

```text
tabenishi02/SourceGroundedObjectKnowledgeBase
```

Target branch:

```text
phase-n-closure-audit
```

Branch ancestry is intentionally:

```text
main fc7609db60a310cd153aa256a5fe183e44ab8fcb
  + accepted N07-R01 feature history
  + N07-R01 result 9cda43e9303488d2b0905f61fa3dbbed4f03a4fb
  + Phase N closure planning/contract
```

Do not switch the audit subject back to stale `main` and do not merge to `main` during this task.

Read first:

1. `docs/planning/phases/N/PHASE_N_CLOSURE_AUDIT.md`
2. `benchmark/phase-n-closure-audit-contract-v1.json`
3. `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`
4. `docs/evaluation/N06_RETRIEVAL_VECTOR_QUALITY.md`
5. `docs/evaluation/N05D04R2_R2_10_CLOSURE_AUDIT.md`
6. `docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`
7. `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
8. `docs/evaluation/N03_REAL_DATA_VERTICAL_SLICE.md`
9. `docs/planning/phases/N/N02_INTEGRATION_TESTS.md`
10. `docs/planning/phases/N/N01_UNIT_TEST_COVERAGE.md`

## 2. Step A — synchronize and preflight

Fetch remote refs and require:

- branch `phase-n-closure-audit` is based on the accepted N07-R01 result history;
- no uncommitted tracked changes before edits;
- local `main` is not modified;
- sufficient disk headroom for full pytest and small audit evidence;
- no need to start/stop normal reference Qdrant or unrelated processes.

Record:

- branch HEAD;
- `origin/main` SHA;
- merge-base with main;
- Python/OS/package versions;
- free disk;
- current process/reference-service inventory through existing safe mechanisms.

Before any audit execution record SHA-256/fingerprints for:

- the three preserved R1 user-aborted files used by N-05/N-06/N-07 safety gates;
- original N-03/reference canonical and Raw assets used by accepted formal evidence, where those local assets are present;
- reference Qdrant inventory/fingerprints through the existing safe read-only/preflight method.

Never alter these assets to make the audit runnable. Missing required preserved evidence is BLOCKED if it prevents a valid safety judgment.

## 3. Step B — state-document reconciliation

Before the formal measurement source is committed, reconcile stale *current-state* documentation. Preserve old failures as historical evidence.

### B1 `docs/planning/phases/N/PHASE_N_PREPARATION.md`

Add a new top authoritative update that supersedes older current-state paragraphs:

```text
N-01 = Complete
N-02 = Complete
N-03 = Complete
N-04 = Complete / PASS
N-05 = Complete / PASS
N-06 = Complete / PASS
N-07 = Complete / PASS
N07-R01 = Complete / PASS
Phase N closure audit = Active / formal execution pending
Phase N = Active / Not Complete
```

Reference N07-R01 run `20261024T222300+0900`, measured source `ffb16e9f7e0e24c8c2648a04430fca57bfb71dfb`, result commit `9cda43e9303488d2b0905f61fa3dbbed4f03a4fb`, and ChatGPT review acceptance.

Do not delete the historical original N-07 47 PASS / 3 FAIL record.

Also correct the current task table/next-work text so it no longer says N-05 Active, N-06 Ready, or N-07 Pending as current truth. Historical sections may retain those old states when labeled historical.

### B2 `docs/planning/phases/N/N07/N07_FAILURE_RECOVERY_ACCEPTANCE.md`

Update the current status to:

```text
N-07 = Complete / PASS — N07-R01 remediation formally PASS and review accepted
```

Keep the original run `20261024T201856+0900` as historical `Complete / FAIL` evidence that opened N07-R01. Add a remediation disposition section pointing to:

- `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`
- `benchmark/results/n07-r01-composite-backup-restore.json`

Record that I08/I11/I12 were the original failed cases and were closed by the supported product Composite recovery path; all other original N-07 gates were already PASS and regression remained PASS.

### B3 `docs/planning/phases/N/N07/N07_R01_COMPOSITE_BACKUP_RESTORE.md`

Change the current status from review-pending candidate to:

```text
Complete / PASS — ChatGPT review accepted 2026-10-24
```

Do not alter measured facts/limits.

### B4 `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`

Append a review disposition section. Do not rewrite the original formal measurement narrative. State that ChatGPT independently compared the GitHub branch/result, reviewed the product Composite implementation and CLI, and accepted the formal PASS as N07-R01 Complete/PASS.

### B5 `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

Reconcile the Phase N task checklist/current status:

- N-01 Complete
- N-02 Complete
- N-03 Complete
- N-04 Complete / PASS
- N-05 Complete / PASS
- N-06 Complete / PASS
- N-07 Complete / PASS after N07-R01

Preserve detailed historical N-04 failure and N-05 remediation narrative if useful, but it must not remain the file's current next-task claim.

Phase O remains untouched except for any necessary handoff reference. Do not mark O-01..O-06 started or complete.

## 4. Step C — create deterministic closure evaluator

Create if needed:

```text
benchmark/tools/phase_n_closure_audit.py
```

It should inspect the committed closure source and emit machine-readable evidence. It must not modify product data.

At minimum verify:

- every authority path in `benchmark/phase-n-closure-audit-contract-v1.json` exists;
- required aggregate JSONs exist and are parseable;
- N06 aggregate overall PASS;
- N07-R01 aggregate overall PASS, failures=[], blocked=[];
- N07-R01 measured commit/result identity is coherent;
- N07 original FAIL aggregate remains present as historical evidence;
- current-state docs contain the reconciled Complete statuses and do not contain superseded state in their designated current-state section;
- accepted R2 contract/model/revision/family identity is compatible across N-05/N-06/N07-R01 evidence;
- Phase O O-01..O-06 remain downstream/not executed.

Do not create a benchmark-only product bypass or reinterpret historical results.

Focused unit tests for the evaluator may be added if useful.

## 5. Step D — commit the measurement source

Commit all state reconciliation + evaluator/test changes before the formal run.

Record this exact commit as `measured_source_commit`.

The formal run must not measure an uncommitted source tree.

After this commit, the only allowed tracked change before result publication is none. Formal run raw evidence goes under:

```text
.local/phase-n-closure/<run_id>/
```

## 6. Step E — formal closure run

Run the deterministic closure evaluator and the frozen repository checks on the exact measured source:

```text
python -m pytest -q
python -m ruff check .
python -m compileall -q src benchmark/tools tests
python -m ruff format --check .
git diff --check
```

If repository-wide format check discovers a pre-existing accepted formatting baseline incompatible with this command, do not autoformat unrelated files. Record the exact issue and use the narrowest repository-established format check only when justified by existing policy/evidence. A new formatting regression in changed files is FAIL.

Do not rerun N-05 46-sample performance, N-06 100k ANN, N-04 external/consumer experiments, or N07-R01 recovery drill unless the closure evaluator detects a concrete contradiction requiring new evidence.

The purpose of this run is final integration/regression/state audit, not repetition of accepted benchmarks.

## 7. Step F — post-run safety

Repeat the preflight fingerprints and require:

- R1 three SHA-256 values byte-identical;
- original N-03/reference canonical and Raw assets unchanged;
- reference Qdrant inventory/fingerprints unchanged;
- measured HEAD/tracked tree unchanged during the run;
- local main unchanged;
- no run-owned child process remains.

No destructive test is required for Phase N closure. Do not mutate reference assets merely to test safety.

## 8. Step G — evaluate

Verdict exactly one of PASS / FAIL / BLOCKED according to the frozen contract.

PASS requires C01-C07 all PASS.

If PASS, create:

```text
benchmark/results/phase-n-closure-audit.json
docs/evaluation/PHASE_N_CLOSURE_AUDIT.md
```

The result must include:

- run_id;
- measured source commit;
- base accepted N07-R01 result commit;
- origin/main baseline;
- per-gate C01..C07 status;
- authority/evidence inventory;
- cross-task compatibility conclusion;
- documentation reconciliation result;
- full pytest count;
- Ruff/compile/format/diff return codes;
- safety before/after evidence;
- deferred Phase O inventory;
- limitations;
- final `PASS/FAIL/BLOCKED`.

If PASS, update closure-state documents to `Complete / PASS candidate — ChatGPT review pending`, not final accepted Complete/PASS. Do not mark Phase O started.

## 9. Commit/push policy

Use separate commits where practical:

1. state reconciliation + evaluator/tests (measured source);
2. formal result + evaluation/state candidate publication.

Push `phase-n-closure-audit`.

Do NOT merge to `main`.

Do NOT delete N07-R01 or other branches.

Do NOT start Phase O.

## 10. Final report back to ChatGPT

Report:

```text
branch
initial closure HEAD
measured source commit
run_id
result commit / final HEAD
working tree state
C01..C07 results
full pytest passed/failed/skipped/warnings
Ruff / compile / format / diff
state-doc reconciliation files
R1 before/after hashes
N-03/reference before/after status
reference Qdrant before/after status
run-owned process residue
final PASS / FAIL / BLOCKED
main status / merge-base / ahead-behind
```

Only after ChatGPT independently reviews the committed evidence may the state become:

```text
Phase N closure audit = Complete / PASS
Phase N = Complete / PASS
Next = Phase O — Documentation / Release / Git cleanup
```
