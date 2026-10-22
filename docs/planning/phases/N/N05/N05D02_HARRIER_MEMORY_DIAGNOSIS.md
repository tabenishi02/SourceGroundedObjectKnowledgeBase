# N05D-02 — Long-input Harrier memory diagnosis

更新日: 2026-10-22

- Parent: `N-05 [P0] — Performance`
- Status: **Complete - VIABLE_FOR_FORMAL_RERUN**
- N05D-01: **Complete**
- N-05: **BLOCKED / Not Complete**
- Formal source run: `20261022T130413+0900`
- Formal source profile/sample: `large/cold-01`
- Current frozen model: `microsoft/harrier-oss-v1-0.6b`
- Frozen revision: `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`

## 1. Purpose

Formal N-05 Large `cold-01` was interrupted during Embedding after the Object-level Search Representation reached approximately 18,847 tokens. At that time the workstation showed approximately 23.2 GiB dedicated VRAM and 34.2 GiB shared GPU memory usage, but no controlled sequence-length/memory curve was collected.

N05D-02 isolates that question from the formal benchmark and determines whether the frozen Harrier representation/model contract is operationally viable on the Reference Workstation.

This task is diagnostic only. Its measurements are not N-05 p95 samples.

## 2. Frozen runtime conditions

Do not change the production/frozen embedding profile for this diagnosis.

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
device: cuda
batch_size: 1
max_sequence_length: 32768
overflow_policy: reject
normalize_embeddings: true
dimension: 1024
CPU fallback: forbidden
silent truncation: forbidden
```

Use the installed `sentence-transformers` / `transformers` / `torch` environment from the N-05 Reference Workstation and record exact versions.

Record the actual attention implementation/backend exposed by the loaded local model/config. Do not assume Flash Attention, SDPA, or eager attention from model family alone.

## 3. Input authority

The primary diagnostic input is the **actual Large Object Search Representation from the preserved formal run**, not a newly invented synthetic string.

Preferred source:

```text
.local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite
object_id = object-n05-large
```

The source DB is evidence and must remain unchanged.

A safe implementation may copy the DB into the new N05D-02 run root and use the copied DB plus `SearchRepresentationBuilder.build_object_overall()` to reconstruct the deterministic current Object representation.

Record:

```text
source DB path
source DB sha256
object_id
current version_id
representation sha256
character count
line count
actual frozen-tokenizer token count
```

If the full representation cannot be reproduced from the preserved formal run, N05D-02 is BLOCKED rather than silently substituting another input.

## 4. Sequence-length curve

Use the full Object representation as the content source. For intermediate points, use deterministic prefixes composed of complete original representation lines. Select the largest prefix not exceeding each requested token target under the frozen Harrier tokenizer.

Required targets:

```text
~2,048 tokens
~4,096 tokens
~8,192 tokens
~12,288 tokens
~16,384 tokens
actual full representation (~18,847 tokens expected from the historical observation)
```

Record requested and actual token counts. The actual full representation must never be truncated.

Run each curve point in a **fresh Python process** so CUDA allocator/cache growth from a previous longer point cannot contaminate the next point.

A short neutral model initialization/warmup may be performed outside the measured embedding interval for the curve points, but it must be documented and kept identical across curve points.

For final operational-viability evidence, if the full input succeeds once, execute at least **3 independent fresh-process full-input trials total**. These are diagnostic repetitions, not formal N-05 samples.

## 5. Required measurements

For every worker/trial record at minimum:

```text
requested token target
actual token count
input sha256
wall-clock embedding seconds
success / failure / skipped
exception type/message (if any)
output vector dimension
finite vector check
vector norm

torch.cuda.memory_allocated baseline
torch.cuda.max_memory_allocated peak
torch.cuda.memory_reserved baseline
torch.cuda.max_memory_reserved peak
torch.cuda.mem_get_info before/after

GPU name
total VRAM
driver version
nvidia-smi dedicated-memory observations where available
Windows GPU Process Memory Dedicated Usage observations
Windows GPU Process Memory Shared Usage observations
process working set/private memory
system available/committed memory observations
```

Synchronize CUDA before starting and after completing the timed embedding call.

Peak Windows dedicated/shared GPU process memory should be sampled during the call, not inferred only from pre/post snapshots. Preserve raw monitoring data.

## 6. Model/runtime metadata

Record at least:

```text
Python version
torch version
CUDA build/runtime visible to torch
sentence-transformers version
transformers version
model/revision
resolved model commit hash
dtype
device
batch size
max sequence length
model config model_type
num_hidden_layers
hidden_size
num_attention_heads
num_key_value_heads
head_dim
max_position_embeddings
use_cache
reported attention implementation/backend
```

Desk-review reference for the frozen model indicates a Qwen3-based 0.6B model with max position 32768, BF16, 28 full-attention layers, hidden size 1024, 16 attention heads / 8 KV heads, head dimension 128, and `use_cache=false`; the local loaded config remains authoritative for acceptance.

## 7. Safety and isolation

- Do not run the formal N-05 benchmark.
- Do not modify canonical Knowledge DBs.
- Do not modify Qdrant or rebuild Vector artifacts for this diagnostic.
- Do not disable Defender/EDR.
- Do not change model/revision/dtype/batch size/max sequence length.
- Do not enable CPU fallback.
- Do not install a different attention package merely to make the test pass.
- Do not split/chunk the Object representation in this task.
- Do not silently retry a failed measurement and discard the failure.

If another substantial CUDA workload makes the measurement materially confounded, record it and classify the run BLOCKED instead of killing unrelated user processes automatically.

## 8. Operational viability verdict

### `VIABLE_FOR_FORMAL_RERUN`

Use this verdict when:

- the exact full representation is within the frozen 32768-token limit;
- 3/3 independent fresh-process full-input trials complete;
- no OOM / process kill / driver reset / CPU fallback / truncation occurs;
- output vector checks pass;
- memory observations are complete enough to explain the previous pressure.

High shared-memory use may be recorded as a performance risk without automatically making memory viability FAIL; N05D-04 remains responsible for the frozen formal performance Gate.

### `NOT_VIABLE_REQUIRES_DESIGN_REMEDIATION`

Use this verdict when the frozen full input cannot reliably complete because of GPU/host/shared-memory exhaustion, OOM, process termination, driver failure, or equivalent resource failure under the frozen settings.

Do not repair this by truncation, smaller max length, a different model, CPU fallback, or arbitrary chunking. Such changes require an explicit Derived Search representation/model design remediation in N05D-03.

### `BLOCKED`

Use this when the authoritative input, model, instrumentation, or Reference Workstation state is insufficient to make the above decision.

## 9. Curve interpretation

Do not infer a particular memory complexity only from model architecture. Compare the empirical curve and the actual local attention backend.

At minimum report:

```text
length vs wall-clock
length vs torch peak allocated
length vs torch peak reserved
length vs Windows dedicated usage
length vs Windows shared usage
```

Identify the approximate token range at which WDDM/shared-memory spill or another abrupt resource regime change begins, if observed.

Distinguish:

```text
model weights / baseline residency
sequence-dependent CUDA allocation
allocator reservation
Windows WDDM dedicated/shared residency
host process/system memory
```

## 10. Exit condition

N05D-02 is Complete only when evidence supports one of:

```text
18,847-token-class full input is operationally viable on the Reference Workstation
```

or

```text
current representation/model contract is not operationally viable and requires explicit design remediation
```

The exact measured full-input token count supersedes the historical approximate 18,847 count.

After N05D-02 completion:

- if viable and no remediation is required, proceed to the remaining N05D-03 closure/checkpoint and then N05D-04 formal rerun as defined by the parent plan;
- if not viable, N05D-03 must address the representation/model design explicitly before any formal rerun.

Do not automatically start the formal rerun from the diagnostic worker.

## 11. Evidence and repository updates

Use a new root:

```text
.local/n05d02/<run_id>/
```

Preserve raw worker/monitor logs and prior N-05 evidence.

Expected Git-tracked additions/updates after local execution:

```text
benchmark/tools/n05d02_harrier_memory_diagnosis.py
benchmark/tools/n05d02_run_harrier_memory_diagnosis.ps1   (if useful)
tests/test_n05d02_harrier_memory_diagnosis.py
docs/evaluation/N05D02_HARRIER_MEMORY_DIAGNOSIS.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
this document
```

Run focused tests, full pytest, Ruff, and `git diff --check` before commit/push.


## Reference Workstation result - 2026-10-23

Run `20261022T230242+0900`, execution HEAD `5806ebf5baf965051253dff7e20428d9a0b221aa`.
Authoritative representation reproduced: **18847 tokens**, unchanged source DB.
All six curve points and three independent full-input trials PASS. Full times:
642.830 / 636.118 / 628.092 seconds. Full Torch peak allocated/reserved:
51.061 / 56.787 GiB; Windows dedicated ~23.2 GiB, shared ~34.2 GiB.
Large spill/time regime change is bracketed by 12278-16383 actual tokens.
Loaded attention config is SDPA; selected CUDA kernel is not profiled.
No OOM, abnormal process exit, CPU inference fallback, truncation or detected
driver-reset event. Full vectors pass 1024-dimension/finite/normalization checks.

**N05D-02 = Complete; VIABLE_FOR_FORMAL_RERUN**, with substantial performance and
host-commit risk. Shared-memory usage alone is not a memory-viability failure.
Diagnostic seconds are not formal N-05 p95 evidence. N-05 stays BLOCKED.
Final post-review full regression: **552 passed, 0 failed, 2 warnings; focused 11 passed; repository Ruff and git diff --check PASS**.

Full metrics, preprocessing verification correction, exact runtime and limits:
[local diagnostic evaluation](../../../../evaluation/N05D02_HARRIER_MEMORY_DIAGNOSIS.md).
Next: **N05D-03 remediation/closure checkpoint**, not automatically started;
N05D-04 formal performance rerun remains unstarted.
