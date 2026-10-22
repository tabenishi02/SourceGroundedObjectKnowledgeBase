# N05D-04 — Resource preflight and Harrier VRAM-reduction research

Updated: 2026-10-23

- Parent: `N-05 [P0] — Performance`
- Trigger: aborted formal attempt `20261023T025413+0900`
- Attempt execution HEAD: `280a2af9fc9c5338137f46b366bd4e18b0b9416a`
- Status: **Resource remediation / investigation before a new formal run**
- Formal N-05: **BLOCKED / Not Complete**

## 1. Why the aborted attempt is not a performance FAIL

The attempt was stopped after disk exhaustion became a confounding Reference Workstation condition. Standard warm samples encountered Qdrant `No space left on device` / `WAL buffer size exceeds available disk space`, and Large had not completed the required formal sample set. The preserved attempt must remain historical evidence and must never be resumed or converted into a judgeable PASS/FAIL dataset.

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

The Reference Workstation hard start gate is now:

```text
minimum free disk: 32 GiB
scope: every volume hosting the repository/formal evidence or active Qdrant runtime
current topology: both are on C:
```

`32 GiB` is an SGOKB benchmark safety gate, **not** a general Qdrant product minimum. It is deliberately conservative relative to the ~1.47 GB nominal default WAL-capacity sum, Qdrant's temporary-storage headroom guidance, and the observed Windows page-file/commit pressure. If practical, 64 GiB free before starting a many-hour formal run is preferred operational margin, but only 32 GiB is the hard benchmark preflight gate.

Implemented guard:

```text
benchmark/tools/n05_resource_preflight.py
tests/test_n05_resource_preflight.py
```

The guard runs outside formal timed samples and exits non-zero below 32 GiB.

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

The loaded Transformers setting was `_attn_implementation = sdpa`, but N05D-02 did not profile the CUDA kernel actually selected by PyTorch SDPA.

## 4. Highest-priority VRAM investigation — force fused SDPA kernels

PyTorch SDPA can choose among FlashAttention-2, Memory-Efficient Attention, and the math/C++ implementation. Hugging Face documents that optimized attention avoids materializing the full attention matrix and can substantially reduce memory traffic. Qwen3 advertises support for both SDPA and Flash Attention.

Sources:

- https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention
- https://huggingface.co/docs/transformers/attention_interface
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3/modeling_qwen3.py

The current ~51 GiB allocated peak and sharp 12k→16k regime change are compatible with a non-fused/fallback path, but they do **not** prove that the math backend was selected. The next diagnostic must determine actual dispatch rather than infer it.

### P0 test matrix

Use the identical authoritative 18,847-token input, frozen model/revision/BF16/CUDA/batch-size-1 profile, each in a fresh process:

```text
A. current SDPA auto-selection (baseline)
B. force PyTorch SDPBackend.FLASH_ATTENTION
C. force PyTorch SDPBackend.EFFICIENT_ATTENTION
```

For B/C use `torch.nn.attention.sdpa_kernel(...)` so the model weights, tokenizer, representation, pooling, normalization, and Transformers model identity remain unchanged.

Record:

```text
backend requested
backend accepted/rejected and exact warning/error
wall-clock
Torch peak allocated/reserved
Windows peak dedicated/shared
process working set/private memory
system committed/available
vector dimension/norm
cosine similarity and max absolute difference vs baseline embedding
```

If a forced fused backend is unsupported, retain the failure and reason. Do not silently fall back to math for that comparison.

## 5. P1 option — Transformers FlashAttention-2 backend

If PyTorch built-in forced Flash SDPA cannot execute the Harrier/Qwen3 workload, evaluate Transformers `attn_implementation="flash_attention_2"` as a separate runtime candidate.

Hugging Face documents FlashAttention-2 as a tiled implementation using on-chip memory and shows Qwen3 support for Flash Attention. Current Transformers can also obtain FlashAttention kernels through its kernel interface when configured appropriately.

Sources:

- https://huggingface.co/docs/transformers/attention_interface
- https://huggingface.co/docs/transformers/main/en/kernel_doc/loading_kernels
- https://github.com/huggingface/transformers/blob/main/tests/models/qwen3/test_modeling_qwen3.py

This option is more intrusive because the formal environment is offline and any additional package/kernel must be installed or cached and pinned reproducibly before acceptance. Do not change the formal run automatically merely because this backend is faster.

## 6. Lower-priority VRAM techniques

### Allocator tuning

PyTorch documents `expandable_segments`, `cudaMallocAsync`, and allocator controls for fragmentation. These can reduce allocator reservation/fragmentation but cannot eliminate live tensor allocations.

Source:

- https://docs.pytorch.org/docs/main/notes/cuda.html

N05D-02 allocated 51.061 GiB while reserving 56.787 GiB. Even eliminating the entire ~5.7 GiB reservation gap would still leave active allocation far above 24 GiB VRAM. Allocator tuning is therefore P2, after attention-kernel dispatch.

### `empty_cache()`

PyTorch explicitly states that `empty_cache()` releases unused cached blocks but does not increase the memory available to PyTorch for tensors that are still live. It can help fragmentation, not the 51 GiB active-allocation peak.

Source:

- https://docs.pytorch.org/docs/main/generated/torch.cuda.memory.empty_cache.html

### FP16 instead of BF16

Both are 16-bit formats, so changing BF16→FP16 does not materially halve this memory footprint and would change the frozen runtime without a strong memory rationale. Not prioritized.

### Weight quantization

The model baseline is ~1.11 GiB vs ~51 GiB sequence-dependent peak. 8-bit/4-bit weight quantization would attack the smaller term and would alter the embedding runtime/quality contract. Not prioritized.

### Already-active protections

- batch size is already 1;
- `use_cache=false` in Harrier config;
- Sentence Transformers `encode()` runs under `torch.inference_mode()`;
- CPU fallback is prohibited.

Sources:

- https://huggingface.co/microsoft/harrier-oss-v1-0.6b
- https://github.com/huggingface/sentence-transformers/blob/main/sentence_transformers/sentence_transformer/model.py

## 7. Contract-changing last resorts

The following would likely reduce resource demand but change the system being evaluated and therefore require explicit design review rather than an N05-only shortcut:

```text
Object Search Representation chunking
representation length cap / truncation
smaller Harrier 270m model
alternate embedding model
sliding-window attention
CPU/offload path
```

If fused attention cannot bring the full-input resource profile into a practical range, these become N05 remediation/design candidates and must be evaluated against N-06 retrieval quality and the canonical Derived Search design.

## 8. Adoption gate for an attention-backend change

A candidate backend is not accepted solely for lower VRAM. Before a new formal N05D-04 run it must show:

1. exact same authoritative full input and token IDs;
2. same Harrier model/revision and BF16 weights;
3. 1024-dimensional finite normalized output;
4. materially lower peak dedicated/shared/allocated memory or materially lower wall-clock;
5. no CPU fallback or truncation;
6. numerical-difference evidence vs the current embedding;
7. existing Derived Search smoke/regression PASS;
8. representative retrieval ordering/quality check before treating the new runtime as the accepted embedding implementation.

PyTorch notes that fused and math SDPA implementations can produce small floating-point differences. Exact bit equality is therefore not assumed, but the difference must be measured and retrieval behavior must remain acceptable.

Source:

- https://docs.pytorch.org/docs/main/generated/torch.nn.functional.scaled_dot_product_attention.html

## 9. Next action

Do **not** restart the formal 46-sample N05D-04 yet.

Next local task:

```text
N05D-04R1 — Harrier SDPA backend / VRAM A-B diagnosis
```

Run A/B/C above on the Reference Workstation, retain all results, and decide whether a fused attention backend should be adopted. Only after that decision and the 32 GiB disk preflight PASS should a new formal N05D-04 run be authorized.
