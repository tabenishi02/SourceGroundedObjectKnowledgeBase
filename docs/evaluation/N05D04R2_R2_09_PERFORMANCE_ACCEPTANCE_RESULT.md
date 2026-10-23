# R2-09 Performance/resource acceptance — Complete / PASS

## Current formal acceptance — Complete / PASS (2026-10-24)

This section supersedes the historical blocked-attempt notes retained below.

- Formal run ID: `20261024T044506+0900`.
- Measured branch/HEAD: clean `main == origin/main`,
  `2711d4c389c4d1c722e864e17a7b6afb05af4c62`.
- Evaluator: **Standard PASS / Large PASS / overall PASS**.
- R2-09 = **Complete / PASS**; R2-10 = **Next / Not Started**.
- N05D-04R2 remains **Active until R2-10 closure**; N05D-04 and N-05 remain
  **Not Complete until R2-10**. No closure or subsequent task was executed.

### Fresh preflight and Accepted diagnostic reuse

All mandatory fresh preflight commands passed: resource preflight, full pytest,
repository-wide Ruff and `git diff --check`. The runner independently repeated
its required evaluator/full/static preflight, also PASS. External full preflight,
runner full preflight and post-run full suites each passed **669 tests**, 0 failed
(2 in-memory Qdrant warnings). Evaluator tests passed **8/8** pre/post run.

Disk free at worker preflight: **124.061 GiB** on the repository/evidence and active
Qdrant volume; minimum unchanged at 32 GiB. Windows physical available:
**76.911 GiB**; virtual total/free: **148.814 / 78.583 GiB**.
Page file allocation/current usage: **21.000 / 2.180 GiB**. These are preflight
observations, not formal peak-memory measurements.

Qdrant 1.19.2 remained healthy on the adopted external storage root and
HTTP/gRPC 6333/6334; process/config/version/health before and after matched.
RTX 4090 / driver 581.80 / PyTorch CUDA 12.4 was available, with about 410 MiB
used and 0% GPU utilization at initial fresh observation; no material competing
CUDA workload was present. No unrelated process or security setting was changed.

Accepted Large diagnostic `20261024T040021+0900` at source commit
`30f6bba79d2447d0708fa21f3313239d971bc4d6` was **not rerun**. Only documentation
changed between that source and measured HEAD. The same venv/cache/model/runtime
was used: torch 2.6.0+cu124, transformers 5.20.1, sentence-transformers 6.1.0,
qdrant-client 1.19.1, tokenizers 0.23.3, huggingface-hub 1.33.0, numpy 1.26.4.
Frozen Harrier 0.6B revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`,
CUDA/bfloat16, 1024 dimensions, normalization and reject/no-truncation policy
were unchanged. No attention/package/scoring/ANN/timing tuning was introduced.

The Accepted diagnostic remains the resource comparison evidence: overview 103
exact tokens; Torch allocated/reserved 6.889365/7.072266 GiB, Windows
Dedicated/Shared 7.525581/0.074219 GiB. Historical v1 was 18847 tokens,
approximately 51.061/56.787 GiB Torch and 23.2/34.2 GiB Dedicated/Shared.
These accepted/historical values are **not new formal-run peak measurements**.

### Exact formal sample counts and performance

A completely new run started from Standard cold-01, followed by Standard warm
01..20, Large cold 01..03 and Large warm 01..20. Warm policy remained one
persistent preloaded provider per profile. No prior run was resumed; no sample
was skipped, reordered, replaced or retried.

| Profile | Cold | Warm | PASS / FAIL / ABORTED | Warm min s | Warm p50 s | Warm p95 s | Warm max s | p95 target s | Verdict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| Standard | 3 | 20 | 23 / 0 / 0 | 10.2192924 | 11.3099469 | 12.2832216 | 12.3947986 | 600 | PASS |
| Large | 3 | 20 | 23 / 0 / 0 | 45.6563244 | 49.9412004 | 53.7066947 | 54.1282194 | 1200 | PASS |

p95 is the unchanged nearest-rank statistic (19th sorted sample of 20),
independently recomputed against the evaluator. p50 uses the evaluator's median.
Total retries = 0; warm failure/abort = 0. All 46 actual workloads match the
contract: Standard 10/500/120/300; Large 40/2000/350/1200.

| Cold diagnostic profile | min s | p50 s | p95 s | max s |
|---|---:|---:|---:|---:|
| Standard cold | 16.4993831 | 16.6775226 | 16.9146380 | 16.9146380 |
| Large cold | 54.7359171 | 56.5239185 | 61.8104252 | 61.8104252 |

Cold values are recorded for completeness; formal Gates use warm samples only.

| Included segment | Standard warm p50 / p95 / max s | Large warm p50 / p95 / max s |
|---|---|---|
| `package_build` | 0.9908429 / 1.2188512 / 1.3570348 | 4.6904500 / 6.2110830 / 6.4146303 |
| `package_stage` | 0.3969889 / 0.4785016 / 0.4831506 | 0.8228850 / 0.9574270 / 0.9876556 |
| `package_preflight` | 0.1031948 / 0.1196152 / 0.1357572 | 0.1924645 / 0.2249785 / 0.2630196 |
| `result_validation` | 0.2167127 / 0.2703156 / 0.2972216 | 0.5598831 / 0.6097816 / 0.6683851 |
| `diff_review` | 0.0037168 / 0.0067212 / 0.0122321 | 0.0091889 / 0.0124819 / 0.0155532 |
| `result_import` | 0.0178416 / 0.0332824 / 0.0367199 | 0.1180846 / 0.1454492 / 0.2675899 |
| `derived_incremental_sync` | 9.5000486 / 10.4310613 / 10.5095242 | 43.3101320 / 46.3862137 / 47.0050612 |
| `render` | 0.0125162 / 0.0151591 / 0.0184306 | 0.0431390 / 0.0760917 / 0.0868334 |

Derived incremental sync accounts for **84.163%** of Standard
and **86.487%** of Large aggregate included warm time.
Per-segment percentiles need not sum to total-time percentiles.
The evaluator's profile/overall PASS verdicts were adopted unchanged.

### Every-sample R2 audit and safety

All **46** samples passed SQLite identity/workload/integrity checks and independent
live Qdrant point/payload inspection:

- active contract `n05d04r2-hierarchical-v2`; family overview/Facet/Statement only;
- Standard counts 1/3/300 = 304 points; Large 1/3/1200 = 1204 points;
- active `object_overall` memberships = **0** in every sample;
- **46 unique generation IDs and namespaces**, **34684 audited points**;
- every point had the correct membership identity, `generation_id` and Space ID;
- loaded provider space equaled the frozen bootstrap declaration in every sample;
- bootstrap had zero Versions/memberships/Embeddings and no provider construction;
- cold model construction stayed in timed sync; warm preload policy was unchanged;
- normal incremental upsert/audit was used, with no full generation/Vector rebuild.

Runner safety flags all PASS: canonical unchanged, HEAD unchanged, tracked state
unchanged. The verification clone has no production/reference DB; its canonical
snapshots record those paths as absent. Therefore a separate read-only snapshot
of the **original workspace's real N-03 evaluation DB (68 tables)** was also taken
before and after the run; those full-table fingerprints match exactly. The
production default DB was absent both times. No artificial copies were substituted
for this original-DB check.

Original canonical snapshot normalized JSON SHA-256 (before = after):
`0ee6bdca3a674cabf961804676c90840cfb8684b3949460b4e87e7a5286c3599`.

R1 asset hashes before/after and final review all match:

| Asset in original workspace | SHA-256 | Comparison |
|---|---|---|
| `benchmark/tools/n05_resource_preflight.py` | `996c057354ff032235940775995c46054e0cfd92cb2aa44dd511271acde91cff` | identical |
| `benchmark/tools/n05d04r1_sdpa_vram_diagnosis.py` | `e11efff44264c5a152aaa284e2534c4cb85f058b7b03aab5290eec60eb2bcb40` | identical |
| `tests/test_n05d04r1_sdpa_vram_diagnosis.py` | `9ecfe8e767944c541a1481f0d16454caacfa0d4e576de9afe5e7ccef9cb16ee0` | identical |

Post-run: evaluator **8 passed**, full pytest **669 passed / 0 failed**,
repository-wide Ruff PASS, diff PASS. Worker/evaluator logs contain no hidden
traceback/OOM/access-denied/OS-error failures. Historical formal/diagnostic evidence,
raw artifacts and all benchmark namespaces are retained. Only documentation and
an aggregate result are committed after recording the unchanged measurement HEAD.

### Evidence and published aggregate

All paths below are relative to the isolated verification clone:

- Formal evidence: `.local/n05/20261024T044506+0900/` — status/environment,
  performance-evidence/evaluation, canonical snapshots, safety, preflight/post-run,
  all 46 sample directories and worker/evaluator logs.
- Supplemental control/safety evidence:
  `.local/n05/r2-09-formal-control/20261024T044230+0900/` — fresh preflight,
  package/source identities, Qdrant before/after, original canonical snapshots,
  R1 manifests, sample-R2 audit and independent live Vector audit.
- Published aggregate:
  `benchmark/results/n05d04r2-r2-09-performance-acceptance.json`.
- Accepted diagnostic reference:
  `docs/evaluation/N05D04R2_R2_09_RUNNER_WIRING_REMEDIATION.md`.

Next authorized state is **R2-10 — Closure / Phase N state update (Next / Not
Started)**. It was not started by this task. Formal warm p95 acceptance is PASS;
N-05 completion remains explicitly reserved for that separate closure.


## Historical blocked attempt and remediation notes

# R2-09 Performance/resource acceptance: blocked before timing

Date: 2026-10-24

- Execution branch: `main` (isolated clean clone; original R1 workspace untouched).
- Execution HEAD: `d74b19cf1afc29a794a04cb9b68d6c929e29c0a1` = fetched `origin/main`.
- R2-09 = **BLOCKED / Not Complete**.
- N-05 = **BLOCKED / Not Complete**; N05D-04R2 remains Active.
- R2-10 = Not Started. No closure performed.

## Preflight

Resource preflight PASS: repository/evidence and Qdrant volumes had 124.740 GiB free
(minimum 32 GiB). Windows free physical memory was 77.874 GiB; total virtual
memory 148.814 GiB, free virtual memory 79.286 GiB; allocated page file 21 GiB,
current usage 2.180 GiB. These are preflight observations, not benchmark peaks.
Qdrant 1.19.2 health check passed, with the adopted external storage configuration
and HTTP/gRPC ports 6333/6334. RTX 4090 used 396 MiB of 24564 MiB, GPU utilization
0%; no material competing CUDA workload was observed. No processes were stopped.

Mandatory preflight: full pytest **654 passed, 0 failed**, 2 warnings, 142.18 s;
repository-wide `python -m ruff check .` PASS; `git diff --check` PASS.

## Newly isolated blocker: benchmark workflow still selects v1

Static call-path verification on the execution HEAD found:

1. `benchmark/tools/n05_performance_workflow.py::prepare_fixture` creates a fresh
   canonical database with no accepted Version or active search generation.
2. `run_sample` imports the Result, then constructs the default
   `DerivedSearchMaintenanceApplication` without an R2 builder or generation setup.
3. `src/sgokb/application_maintenance.py::sync_search_representation` calls
   `self._builder.materialize_version(version_id)`.
4. `src/sgokb/retrieval/search_representation.py::materialize_version` explicitly
   builds `object_overall`; `materialize_version_r2` is a separate entrypoint.
5. The frozen performance runner invokes this same workflow for every fresh sample.

The existing reference database's active R2 generation does not carry over into
fresh isolated sample databases. Therefore the prescribed unchanged runner cannot
prove R2 performance or active `object_overall` leakage = 0. Reusing it as-is could
repeat the historical giant-v1 resource regime. This is a benchmark/R2 wiring
blocker established by source inspection, not an observed CUDA OOM or performance
FAIL. No diagnostic timing, model loading, GPU embedding or formal sample started.
No runtime/provider or benchmark source was modified to bypass this blocker.

## v1/R2 comparison availability

| Observation | Historical v1 (N05D-02) | R2 in this attempt |
|---|---:|---|
| Object tokens | 18847 | Not measured |
| Torch peak allocated / reserved, GiB | approximately 51.061 / 56.787 | Not measured |
| Windows dedicated / shared peak, GiB | approximately 23.2 / 34.2 | Not measured |
| Object embedding seconds | approximately 628–643 | Not measured |
| Derived sync / included end-to-end seconds | Not substituted from old data | Not measured |

Historical figures are comparison context only. They are not new R2 measurements.

## Formal and safety outcome

Formal run ID: none. Standard cold/warm = 0/0; Large cold/warm = 0/0.
Formal PASS/FAIL/ABORTED samples = 0/0/0; retries = 0. No samples were skipped,
replaced or resumed: the formal run was never started. Warm p50/p95/max and all
eight segment statistics are unavailable. Targets remain Standard <=600 s and
Large <=1200 s (nearest-rank p95). The deterministic formal evaluator was not run
because no formal evidence exists; no artificial performance verdict was created.

Production/reference canonical databases and Qdrant collections were not mutated.
No canonical before/after snapshots were taken: runtime canonical invariance is
**not measured**, rather than asserted PASS. Tracked source and execution HEAD
remained unchanged through preflight and blocker inspection; only these result
records were edited afterward. Historical evidence was retained.

R1 asset SHA-256 before/after match for all three files:

| Original-workspace asset | SHA-256 (both checks) |
|---|---|
| `benchmark/tools/n05_resource_preflight.py` | `996c057354ff032235940775995c46054e0cfd92cb2aa44dd511271acde91cff` |
| `benchmark/tools/n05d04r1_sdpa_vram_diagnosis.py` | `e11efff44264c5a152aaa284e2534c4cb85f058b7b03aab5290eec60eb2bcb40` |
| `tests/test_n05d04r1_sdpa_vram_diagnosis.py` | `9ecfe8e767944c541a1481f0d16454caacfa0d4e576de9afe5e7ccef9cb16ee0` |

Local-only evidence in the isolated clone:

- `.local/n05/r2-09-resource-preflight.json`
- `.local/n05/r2-09-qdrant-process.json`
- `.local/n05/r2-09-preflight/status.json`, `full-pytest.log`, `ruff.log`, `diff.log`
- `.local/n05/r2-09-preflight/nvidia-smi.txt`
- `.local/n05/r2-09-preflight/r1-before.json`, `r1-after.json`, `r1-final.json`
- `.local/n05/r2-09-preflight/runner-family-blocker.json` (AST call-path evidence)

No post-run regression is claimed because no run occurred. Documentation-only
changes are checked with repository-wide Ruff and `git diff --check` before commit.
Raw environment evidence is not committed.

## Required next action

Review and explicitly authorize a separate benchmark R2-wiring change, preserving
the workload, model, generation isolation, public workflow, timing boundaries and
formal gates. Verify that each fresh sample selects the R2 family and cannot embed
legacy `object_overall`, then commit that implementation before a new R2-09 attempt.
Do not silently inject a replacement builder into the frozen formal run. Do not
start R2-10 or an unrelated optimization task.


## R2-09 wiring remediation verification (2026-10-24)

The v1-fallback blocker is resolved on `r2-09-runner-wiring-remediation`, pending
review/integration into main. Existing generation-aware maintenance, explicit
model-free empty-R2 bootstrap, and incremental namespace audit/metadata refresh
are connected without changing workload, model, scoring or performance gates.
Focused 158 and Windows full 669 tests PASS; compile, repository-wide Ruff,
changed-file format and diff PASS. One fresh Large diagnostic PASS: active R2,
overall leakage 0, overview 103 exact tokens, 1204 audited points, sync 49.1221762 s,
included total 54.8322218 s; canonical snapshots and three R1 asset hashes unchanged.

See `docs/evaluation/N05D04R2_R2_09_RUNNER_WIRING_REMEDIATION.md` for evidence and
resource peaks. No main merge or formal 46-sample benchmark performed. R2-09/N-05
remain Not Complete pending integration and formal acceptance; R2-10 Not Started.
