# N05D-03 — Evidence-based remediation / closure checkpoint

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Status: **Complete**
- Verdict: **READY_FOR_N05D04**
- Basis HEAD: `c1e334a5fea08eff2aa4fcc61906f0fdf6235dde`
- N05D-01: **Complete**
- N05D-02: **Complete / VIABLE_FOR_FORMAL_RERUN**
- N-05: **BLOCKED / Not Complete** until a new formal run is evaluated

## 1. Purpose

N05D-03 consumes the evidence from the two independent formal-run blockers and decides the minimum remediation required before the frozen N-05 benchmark can be rerun.

It is not a performance optimization task. It must not change workload shape, performance gates, model/revision, semantic representation policy, or the measurement boundary merely to improve the chance of a PASS.

## 2. Evidence reviewed

### N05D-01 — Qdrant environment

N05D-01 classified the Qdrant failure as `QDRANT_ENVIRONMENT_DEFECT` and completed the accepted environment remediation.

Accepted state:

```text
runtime root: C:\Qdrant\SGOKB
config:       C:\Qdrant\SGOKB\qdrant.yaml
Qdrant:       native 1.19.2
HTTP/gRPC:    6333 / 6334
privilege:    non-admin
```

The old workspace-resident storage remains preserved as rollback/evidence and is not the active runtime.

After cutover, approved Vector rebuild, real semantic/filtered query, system integrity, canonical invariance, and regression checks passed. The cleanup `ACCESS DENIED` observations were proven 50/50 to be recovered Rust Windows rename fallback events rather than terminal Qdrant failures.

No additional Qdrant/SGOKB code remediation is required by N05D-03.

### N05D-02 — Harrier long-input memory

The authoritative Large Object Search Representation was reproduced exactly:

```text
tokens: 18,847
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
device: cuda
batch_size: 1
max_sequence_length: 32768
overflow_policy: reject
attention config: sdpa
```

Three independent fresh-process full-input trials all completed with valid normalized 1024-dimensional vectors. No OOM, process kill, detected driver reset, CPU inference fallback, truncation, chunking, or model change occurred.

Therefore the current representation/model contract is operationally memory-viable on the Reference Workstation.

However, the measured full-input Embedding took approximately 628–643 seconds, with a sharp WDDM/shared-memory spill regime between 12,278 and 16,383 tokens and about 34.2 GiB peak shared GPU memory at full length.

This is a significant performance/host-memory risk, but it is not itself a design blocker. Whether the frozen Large workload satisfies the 1,200-second formal total-time gate belongs to N05D-04.

## 3. Remediation decision matrix

| Area | Evidence | N05D-03 action |
|---|---|---|
| Qdrant environment | Environment defect identified and external-storage cutover accepted | **KEEP remediation already applied** |
| Qdrant backend / SGOKB adapter | No remaining accepted blocker after D01 | **No new production change** |
| Benchmark runner | No runner defect established as a current blocker | **No runner behavior change required** |
| Harrier model/revision | Exact frozen input completes 3/3 | **Keep unchanged** |
| Search Representation | Exact 18,847-token representation is within contract and completes | **Keep unchanged** |
| Batch size | Frozen at 1 and used successfully | **Keep unchanged** |
| max sequence length | 32,768; authoritative input 18,847 | **Keep unchanged** |
| CPU fallback / truncation / chunking | Not needed and prohibited as benchmark shortcuts | **Do not introduce** |
| Formal performance gates | Not yet judged | **Keep 600 s / 1,200 s unchanged** |
| Workload profiles | Frozen formal contract | **Keep unchanged** |

## 4. Why no Harrier design remediation is applied

N05D-02 establishes that the frozen full input is operationally executable. Changing the model, truncating the Object representation, reducing the sequence limit, moving to CPU, or arbitrarily chunking the representation at this point would change the system being benchmarked rather than repair a proven runtime blocker.

The observed ~630-second full Object embedding is therefore carried forward as a formal performance risk. N05D-04 must measure the complete eight-segment workflow and let the existing deterministic evaluator decide PASS/FAIL.

A later performance failure may justify a separately reviewed optimization/design task, but N05D-03 must not preempt that formal evidence.

## 5. N05D-04 start conditions

A new formal run is authorized only when all of the following hold at start:

1. `main == origin/main` and the working tree is clean.
2. A new run ID is used; `20261022T130413+0900` and all D01/D02 evidence remain untouched.
3. The active Qdrant endpoint is the remediated native runtime on `localhost:6333/6334`, backed by `C:\Qdrant\SGOKB` rather than the preserved old workspace storage.
4. Qdrant readiness/connectivity is confirmed before the runner starts.
5. Harrier remains the frozen model/revision/profile used by the contract: BF16, CUDA, batch size 1, 32,768 max sequence length, overflow reject, no CPU fallback.
6. No unexpected substantial competing CUDA workload is present. Record the initial GPU/process state; do not terminate unrelated user processes automatically.
7. Record host-memory/commit state because D02 showed large WDDM shared-memory demand. This is environment evidence, not a new numeric performance gate.
8. Mandatory preflight tests, full pytest, Ruff, and `git diff --check` pass.
9. The formal runner starts from Standard cold-01 and executes the frozen sequence from the beginning.
10. Failed/aborted samples are retained and never replaced.

If the remediated Qdrant runtime is not active, the model contract differs, or the workstation is materially confounded by another GPU workload, the new run is `BLOCKED` before formal samples rather than silently changing the environment.

## 6. N05D-04 frozen execution

The following remain unchanged:

```text
Standard: cold 3 + warm 20
Large:    cold 3 + warm 20

Standard warm p95 <= 600 s
Large warm p95    <= 1200 s

nearest-rank p95
terminal failure / abort = 0
automatic retry time included
```

Included segments remain:

```text
package_build
package_stage
package_preflight
result_validation
diff_review
result_import
derived_incremental_sync
render
```

N05D-01 and N05D-02 diagnostic timings are not formal samples and must not be mixed into the new evidence set.

## 7. Risk carried into the formal rerun

The most important remaining risk is performance, not memory completion.

The Large Object-level Harrier embedding alone took approximately 628–643 seconds in N05D-02. This leaves substantially less than the full 1,200-second Large gate for all other local automatic work in a formal sample. In addition, the formal warm policy uses a persistent preloaded provider across the warm profile, whereas D02 full-input viability repetitions were intentionally fresh-process trials.

This difference is not a blocker to N05D-04. It is part of what the formal benchmark must measure. A terminal warm failure is retained as formal evidence under the frozen contract.

## 8. N05D-03 verdict

```text
N05D-01 = Complete
N05D-02 = Complete / VIABLE_FOR_FORMAL_RERUN
N05D-03 = Complete / READY_FOR_N05D04
N05D-04 = Next / Not Started
N-05     = BLOCKED / Not Complete
```

No new production code, embedding behavior, Search Representation policy, benchmark workload, or formal Gate is changed by N05D-03.

Next task: **N05D-04 — Formal benchmark rerun under the frozen contract**.
