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
