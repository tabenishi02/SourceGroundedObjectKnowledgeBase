# N05D-04 — Resource preflight and Harrier VRAM-reduction research

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Trigger: aborted formal attempt `20261023T025413+0900`
- Attempt execution HEAD: `280a2af9fc9c5338137f46b366bd4e18b0b9416a`
- Status: **Structural Derived Search remediation selected**
- Formal N-05: **BLOCKED / Not Complete**
- Adopted redesign: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- Task breakdown: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

## 1. Why the aborted attempt is not a performance FAIL

The attempt was stopped after disk exhaustion became a confounding Reference Workstation condition. Standard warm samples encountered Qdrant `No space left on device` / `WAL buffer size exceeds available disk space`, and Large had not completed the required formal sample set. The preserved attempt remains historical evidence and must never be resumed or converted into a judgeable PASS/FAIL dataset.

A future formal attempt must use a new run ID and start again from Standard cold-01.

## 2. Disk-headroom research and decision

### Qdrant guidance

Qdrant persists updates through a write-ahead log before applying them to segments. Current Qdrant configuration documentation shows a default single-WAL-segment capacity of 32 MB (`wal_capacity_mb: 32`). Qdrant capacity-planning guidance recommends approximately 20% extra disk headroom for WAL, snapshots, and temporary optimizer segments.

Sources:

- https://qdrant.tech/documentation/manage-data/storage/
- https://qdrant.tech/documentation/operations/configuration/
- https://qdrant.tech/documentation/operations/capacity-planning/

The formal N-05 run plans 46 sample-specific Qdrant namespaces/collections. At the default WAL capacity, 46 × 32 MB = 1472 MB of nominal WAL-segment capacity if one default-capacity segment is present per sample collection. This is not a claim that Qdrant preallocates exactly 1472 MB of physical blocks; it is an engineering floor for understanding why sub-GiB free space is invalid for this run.

### Windows page-file interaction

The more important headroom requirement is the Windows commit/page-file behavior exposed by N05D-02. Microsoft documents that the system commit limit is RAM plus page files and that a system-managed page file may grow once system commit charge exceeds 90% of the current limit, provided sufficient free disk space exists.

Sources:

- https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/introduction-to-the-page-file
- https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/how-to-determine-the-appropriate-page-file-size-for-64-bit-versions-of-windows

N05D-02 observed approximately 136.0 GiB committed against a 148.8 GiB limit during the 18,847-token Harrier call, above the 90% expansion trigger described by Microsoft. Therefore the formal benchmark must reserve disk capacity not only for Qdrant and `.local/n05` evidence, but also for possible page-file growth while WDDM shared-memory spill is active.

### Accepted SGOKB preflight threshold

The Reference Workstation hard start gate remains:

```text
minimum free disk: 32 GiB
scope: every volume hosting the repository/formal evidence or active Qdrant runtime
current topology: both are on C:\
```

`32 GiB` is an SGOKB benchmark safety gate, **not** a general Qdrant product minimum. If practical, 64 GiB free before starting a many-hour formal run is preferred operational margin, but only 32 GiB is the hard benchmark preflight gate.

Implemented guard:

```text
benchmark/tools/n05_resource_preflight.py
tests/test_n05_resource_preflight.py
```

## 3. VRAM root observation

N05D-02 measured the exact 18,847-token Object representation with the frozen Harrier profile:

```text
Torch peak allocated: 51.061 GiB
Torch peak reserved:  56.787 GiB
Windows dedicated:    ~23.2 GiB
Windows shared:       ~34.2 GiB
wall-clock:            ~628-643 s
```

The model itself has only ~1.11 GiB baseline CUDA allocation. Therefore weight quantization alone cannot address the dominant peak. The dominant problem is sequence-dependent attention/intermediate memory.

## 4. N05D-04R1 partial backend diagnosis

Run `20261023T035147+0900` was started as a fresh-process A/B/C backend comparison and then stopped by user instruction during the first full auto-SDPA trial. Raw evidence and local diagnostic work are retained; the run is not a completed acceptance result.

Confirmed before abort:

```text
A. auto SDPA smoke: PASS
   profiler evidence: math backend selected

B. forced FLASH_ATTENTION: FAIL
   current Windows PyTorch build does not provide the required Flash Attention kernel

C. forced EFFICIENT_ATTENTION: FAIL
   current kernel rejected the Q=16 / KV=8 GQA shape

A full-1: ABORTED_by_user
```

After process termination, observed RTX 4090 usage returned near idle. Therefore the partial run does not establish a cross-process persistent VRAM leak.

These observations strengthen the interpretation that native Windows math-SDPA processing of the giant 18,847-token representation is the dominant resource problem. They do not establish a completed alternative-backend acceptance.

## 5. Why runtime-only remediation is no longer the primary path

The original R1 plan prioritized fused attention because it could potentially preserve the exact representation/model contract.

Subsequent design review found a more fundamental issue: current `object_overall` duplicates detailed canonical Knowledge that is already materialized separately as `facet` and `statement` representations.

Current structure:

```text
object_overall = Object-level context + all content-Facet Statement bodies
facet          = the same detailed Statements grouped by Facet
statement      = the same detailed Statements individually
```

For Large N-05 this creates one 18,847-token full-attention input even though the detailed semantic units already exist as child vectors.

The user therefore selected structural remediation as the primary solution:

```text
compact object_overview
+ existing facet vectors
+ existing statement vectors
+ bounded Object aggregation / hierarchical similarity
```

This is not arbitrary token chunking. Boundaries follow canonical SGOKB semantic units.

## 6. Deferred runtime candidates

The following remain valid technical candidates but are no longer blockers to solve before the representation redesign:

### Built-in / fused attention

- PyTorch Flash SDPA: unavailable in the tested native Windows build.
- Efficient Attention: tested GQA shape rejected in R1 smoke.
- cuDNN / other supported SDPA backends may be investigated later if still needed.
- Transformers FlashAttention-2 on Linux/WSL remains a possible runtime optimization.

### Math-SDPA reduced precision

`torch.backends.cuda.allow_fp16_bf16_reduction_math_sdp(True)` may reduce math-SDPA intermediate memory, but it changes numerical behavior and still leaves the architectural long-input scaling problem. It is deferred unless the redesigned representation still requires it.

### Allocator tuning / empty_cache

Allocator tuning can address fragmentation/reservation, but N05D-02 showed live allocated memory far above physical VRAM. It is not a root solution.

### Model change

Harrier 270M remains a later contingency, not part of the first structural redesign baseline. The redesign keeps Harrier 0.6B fixed so representation impact can be measured independently.

## 7. Adopted root remediation

Accepted direction:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`

Core change:

```text
old active path
  giant object_overall
  + facet
  + statement

new active path
  compact object_overview
  + facet
  + statement
  → Object aggregation / hierarchical similarity
```

The compact Object-level representation must not reproduce every Facet Statement body.

The redesign requires Search Requirements, Search Representation, Hybrid Search, Object Similarity, persistence/versioning, Derived Search rebuild/cutover, search-quality acceptance, and N-05 formal remeasurement work.

Task breakdown:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

## 8. Resource acceptance retained for redesigned system

The redesign does not remove general workstation safeguards.

Before any future formal N-05 run:

```text
free disk >= 32 GiB
remediated Qdrant runtime active
clean main == origin/main
no material competing CUDA workload
host memory/commit recorded
full regression / Ruff / diff PASS
```

The redesign itself must additionally prove:

- no mandatory active representation concatenates all 1,200 Large-fixture Statements;
- all Statement and Facet Knowledge remains searchable;
- no truncation/CPU fallback is introduced;
- quality acceptance passes before performance acceptance;
- Harrier 0.6B remains fixed for the first causal comparison.

## 9. Historical runtime-research sources

Retained sources used by the earlier runtime investigation:

- https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention
- https://huggingface.co/docs/transformers/attention_interface
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3/modeling_qwen3.py
- https://docs.pytorch.org/docs/main/notes/cuda.html
- https://docs.pytorch.org/docs/main/generated/torch.cuda.memory.empty_cache.html
- https://huggingface.co/microsoft/harrier-oss-v1-0.6b

These remain useful diagnostics but do not supersede the selected structural remediation.

## 10. Current next action

Do **not** resume the R1 full-input trial and do **not** restart the formal 46-sample N05D-04 run.

Current next task:

```text
N05D-04R2 / R2-01 — Impact survey / redesign freeze
```

After R2-01 through R2-08 complete and quality acceptance authorizes it, R2-09 starts a completely new formal N-05 run from Standard cold-01.


## R2-09 execution update (2026-10-24)

This execution result supersedes earlier R2-09 next-task notes:
**R2-09 = BLOCKED / Not Complete; N-05 = BLOCKED / Not Complete;
N05D-04R2 = Active; R2-10 = Not Started.** R2-08 quality acceptance is unchanged.

Mandatory preflight PASS (654 pytest passed; repository-wide Ruff/diff PASS;
124.740 GiB free; external Qdrant healthy; no material competing CUDA workload).
Before GPU timing, source inspection established that the frozen performance
workflow uses default v1 `materialize_version` for fresh samples, producing
`object_overall` instead of the required R2 family. No Large diagnostic or formal
sample was started. Runner/model/scoring/gates were not changed. R1 assets remain
byte-identical. A separately reviewed R2 benchmark-wiring change is required
before a new acceptance attempt; no closure or optimization is started here.

Execution record: `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`.
