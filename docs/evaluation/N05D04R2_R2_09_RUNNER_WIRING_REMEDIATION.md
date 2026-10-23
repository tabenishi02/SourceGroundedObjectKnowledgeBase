# R2-09 runner wiring remediation — runtime verified

Date: 2026-10-24

- Branch: `r2-09-runner-wiring-remediation`.
- Base main: `a2870d44c0e4f82dcc9bd39e85489856e2d42e4f`.
- Diagnostic run ID: `20261024T040021+0900`.
- Result: wiring remediation verified; eligible for review/integration before a new
  formal R2-09 run. No main merge or formal 46-sample run performed.
- R2-09 and N-05 remain BLOCKED / Not Complete on main until this branch is
  integrated and formal acceptance is executed. R2-10 remains Not Started.

## Root cause and implementation

Fresh isolated sample databases did not inherit the reference database's active
R2 generation. The default maintenance builder materialized the historical v1
family. The prior blocker record is retained as historical evidence.

Normal `DerivedSearchMaintenanceApplication` now defaults to the existing
`GenerationAwareSearchRepresentationBuilder`. No pointer retains historical v1;
active Phase-I v1 builds `object_overall`; active R2 builds `object_overview` and
links Facet/Statement memberships to the same generation. Unknown contract keys
or versions fail closed before materialization. No new representation builder,
scorer, model or benchmark-specific family-selection branch was added.

`KnowledgeSearchGenerationApplication.bootstrap_empty_r2()` explicitly accepts only
an inactive catalog with no accepted Versions, memberships or persisted Embeddings.
It creates a new R2 generation and a zero-point namespace through the Qdrant
adapter's normal schema/filter initialization, verifies identity, persists empty
digests/binding and atomically activates it. A non-empty catalog or competing
active pointer is rejected. No existing collection is dropped or populated with
a dummy point. The lifecycle's normal build/cutover path is retained for non-empty
catalogs. Bootstrap failure is preserved as a failed generation.

`frozen_harrier_space()` constructs only the frozen space declaration plus installed
sentence-transformers package version. It imports/loads no model and performs no
inference. Every sample compares the subsequently loaded provider's full space
identity with this declaration before embedding. Actual local Harrier identity
matched exactly, including provider configuration, revision, preprocessing,
normalization, dimension and overflow policy. Space ID:
`23027d8fcb47c6ffb9e95681742e4c0aa8d14b301b642a974159f05883204bbf`.

Normal single-Object Vector maintenance routes through the active generation and
pins the upsert namespace. It audits/refreshes generation digests and Vector
binding before marking Vector derived state ready. Audit failure remains a failed
sync. The existing operator batch boundary defers this audit until all target
Objects finish, preserving multi-Object consistency and its existing final audit.

## Benchmark boundary preservation

Each sample clones the empty canonical fixture, bootstraps its own empty R2
namespace, and records setup before any timed segment. Then unchanged workload
segments import the first Result, materialize the R2 family, embed, upsert, audit
metadata, and render. No timed `build_r2_candidate()` or full Vector rebuild occurs.

Cold provider/model construction remains inside `derived_incremental_sync`.
Warm workers retain the existing one-preloaded-provider/20-sample policy; no
per-sample provider is constructed during bootstrap. Frozen sample counts/order,
workloads, all eight timing boundaries, targets, model/runtime, Candidate E,
Hybrid fusion and ANN parameters are unchanged. Namespace creation/filter setup
moves to the expressly authorized untimed empty-bootstrap setup.

## Verification coverage

- No pointer / active v1 / active R2 / unsupported key / unsupported version:
  default maintenance contract tests.
- Empty catalog accepted, zero memberships/Embeddings/points, active R2, repeat or
  non-empty bootstrap rejected; no embedding provider is supplied to bootstrap.
- Identity declaration has no torch/model import; mocked encoder-derived provider
  identity equals the declaration. Real local provider equality is checked below.
- First Result through normal Validation/Diff/Import and incremental maintenance:
  full Standard and Large fixture tests; generation payload, all memberships,
  catalog and membership digests, binding counts and public current Semantic
  retrieval verified. Integrity/foreign-key checks PASS.
- Cold factory/embedding calls must occur within timed sync; warm provider reuse;
  no full generation or Vector rebuild; sample namespace uniqueness retained.
- Space mismatch and generation audit failure are explicit failures. Failed audit
  does not publish a new point count or mark Vector state ready.
- R2-05/R2-06/R2-07/R2-08 and CLI maintenance regressions included in focused/full tests.

Focused tests: **158 passed, 0 failed**, 2 warnings, 53.28 s.
Windows full suite: **669 passed, 0 failed**, 2 warnings, 169.07 s.
Warnings concern in-memory Qdrant indexes/exact search; real-Qdrant diagnostic
was run separately. Compileall (`src tests scripts benchmark/tools`) PASS;
repository-wide Ruff PASS; format check of all nine changed Python files PASS;
`git diff --check` PASS. An exploratory repository-wide format check found 22
pre-existing unformatted files outside this task; those files were not changed.

## One fresh Large diagnostic (not formal acceptance)

Public canonical workflow, isolated SQLite and a new diagnostic-only Qdrant
namespace on the adopted external-storage server. Harrier remained
`microsoft/harrier-oss-v1-0.6b` at
`f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, CUDA/bfloat16, batch 1,
1024 dimensions, normalization unchanged, overflow reject, no truncation.
No packages, model, CUDA or attention backend were changed.

| Check | Observed result |
|---|---|
| Workload Sources / candidate Evidence / Package Evidence / Statements | 40 / 2000 / 350 / 1200 |
| Before timed workload | Object 1, accepted Versions 0, memberships 0, Embeddings 0, namespace points 0 |
| Active contract | `n05d04r2-hierarchical-v2` |
| Active representation family | overview 1 / Facet 3 / Statement 1200 |
| Active `object_overall` memberships | 0 |
| Overview exact tokens | **103**, `truncation=False` |
| Derived incremental sync | **49.1221762 s** |
| Included eight-segment total | **54.8322218 s** |
| Torch peak allocated | 7397399040 bytes (6.889365 GiB) |
| Torch peak reserved | 7593787392 bytes (7.072266 GiB) |
| Windows Dedicated GPU peak | 8080531456 bytes (7.525581 GiB) |
| Windows Shared GPU peak | 79691776 bytes (0.074219 GiB) |
| Retry / failed / aborted diagnostic samples | 0 / 0 / 0 |

WDDM Dedicated/Shared usage was sampled during execution at 0.2-second intervals
using English PDH GPU Process Memory counters scoped to the diagnostic PID.
Raw samples were retained; monitoring errors = 0. Torch peaks were reset before
the workflow and collected after CUDA synchronization. Values are sampled
observations, not inferred from pre/post VRAM. The diagnostic process exited and
RTX 4090 returned to 396 MiB usage / 0% utilization afterward.

Active generation:
`search-generation:r2:01401559-e23d-4280-9936-b26a0184142a`.
Diagnostic namespace:
`n05ab972cf2ed46_generation_3d54cdebbd247f40d8311118`.
Membership count = Vector binding point count = **1204**. All point identities and
R2 `generation_id` payloads passed the normal live namespace audit.

- Source catalog digest:
  `6979d7daf5ed0a77d23b243c3eb1c601af93b4f3410c1b9b053f9c6450ec207e`.
- Generation and binding membership digest:
  `851e6ec445e642591fdc3944198b8b5b1f1f234e0ddc54ab1f1d033c2d3d6cb3`.

Production/reference canonical snapshots compare exactly before/after. Only the
new diagnostic namespace and isolated fixture/sample database were written.
Production namespaces and original R1 assets were not changed. Historical evidence
was retained. All three R1 SHA-256 values before/after equal those in the original
blocker result record; raw comparison manifests remain local.

## Evidence and next action

Evidence root, relative to the verification clone:
`.local/n05/r2-09-wiring-remediation/20261024T040021+0900/`.

Retained: status/command return codes, focused/full/static logs, resource and GPU
preflight, fixture/sample artifacts, `empty-r2-bootstrap.json`,
`diagnostic-result.json`, `overview-token-count.json`, `gpu-memory.jsonl`,
monitor errors, canonical snapshots and R1 hash manifests. Local instrumentation
and raw evidence are not committed.

The wiring blocker is resolved on this branch. Review/integrate the code into
main, then resynchronize clean main and recheck current runtime/resource gates
before a new formal R2-09 run. This single diagnostic cannot establish warm p95,
formal 46-sample acceptance or N-05 completion. No R2-10 closure is authorized here.
