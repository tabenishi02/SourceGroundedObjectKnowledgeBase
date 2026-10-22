# N05D-02 - Long-input Harrier memory diagnosis

Updated: 2026-10-23

- Status: **Complete**
- Verdict: **VIABLE_FOR_FORMAL_RERUN** (memory viability, not a performance PASS).
- Run: `20261022T230242+0900`; execution HEAD: `5806ebf5baf965051253dff7e20428d9a0b221aa`.
- Initial main was clean and fast-forward synchronized with origin/main before tool implementation.
- N05D-01 remains Complete. N-05 remains BLOCKED / Not Complete; no formal sample was run.

## Authoritative input and isolation

The preserved source DB was opened read-only and backed up into the diagnostic
run root. Repository migrations and the normal
`SearchRepresentationBuilder.build_object_overall()` ran only against that copy.
No new synthetic text was generated; no canonical production DB or Qdrant runtime
was changed by this diagnosis.

- Source: `.local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite`.
- Source DB SHA-256 before/after: `ca321321f57cacc8731c206dea022035a9c3e11c76cf7fa454ef314434d8d5b1` (unchanged).
- Object: `object-n05-large`.
- Current Version: `b9dc52be-32ea-4c31-b05e-d530635f12ed`.
- Logical UTF-8 representation SHA-256: `54db1b0c5c2d966c08e5305e4f7951667f51dafb691b1448042875bc86cfaee6`.
- Characters: **30975**; complete lines: **1206**.
- Exact frozen-tokenizer full length: **18847**, including special tokens;
  below the unchanged 32768-token limit.

Each intermediate input is the largest complete original-line prefix not exceeding
its requested target. Full input is unmodified. All eight workers have distinct
PIDs; no warmup was used for any point. Timing uses monotonic wall-clock with CUDA
synchronization immediately before and after the normal `embed_documents([text])`.

## Exact model/runtime

- Model: `microsoft/harrier-oss-v1-0.6b`.
- Revision/local snapshot: `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`.
- BF16 parameters, CUDA:0, batch size 1, max sequence length 32768,
  overflow reject, normalized 1024-dimensional vectors. No CPU inference,
  truncation, chunking, alternate model or attention-package installation.
- Python 3.10.6; PyTorch **2.6.0+cu124**, CUDA build **12.4**;
  Transformers **5.20.1**, sentence-transformers **6.1.0**, tokenizers **0.23.3**.
- GPU: NVIDIA RTX 4090, 24564 MiB reported VRAM, driver **581.80**.
  Initial GPU usage was 468 MiB; no substantial competing workload was observed.
  A premeasurement baseline above 2 GiB would stop for workload review, without
  terminating another process. This is an isolation guard, not a viability threshold.
- Loaded config `_attn_implementation = sdpa`; model type qwen3, 28 layers,
  hidden size 1024, 16 attention heads, 8 KV heads, head_dim 128,
  max_position_embeddings 32768, use_cache false; attention class Qwen3Attention.
- Flash/memory-efficient/math SDPA availability flags were all true. They do
  **not** prove which CUDA kernel was selected. No kernel profiler was used;
  the memory curve must not be described as proof of eager/math/Flash dispatch.
- Loaded config `_commit_hash` was null. Provider requested revision and the
  resolved local snapshot path were independently checked against the pinned
  revision. No network/download was used.

## Sequence-length curve

All memory units below are **GiB**, seconds are measured embedding wall-clock.
Dedicated/shared columns are sampled Windows GPU Process Memory values for the
worker PID, not PyTorch allocations. Sample interval target was 250 ms; nvidia-smi
observations were retained approximately every 5 seconds. Raw JSONL is preserved.

| Trial | Requested tokens | Actual tokens | Seconds | Torch peak allocated | Torch peak reserved | Windows peak dedicated | Windows peak shared | In-call samples | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2048 | 2048 | 2046 | 0.476 | 1.803 | 1.844 | 1.641 | 0.074 | 1 | PASS |
| 4096 | 4096 | 4094 | 0.802 | 3.644 | 3.732 | 4.186 | 0.074 | 3 | PASS |
| 8192 | 8192 | 8189 | 2.320 | 10.790 | 10.863 | 11.317 | 0.074 | 9 | PASS |
| 12288 | 12288 | 12278 | 4.873 | 22.539 | 22.758 | 23.155 | 0.131 | 19 | PASS |
| 16384 | 16384 | 16383 | 266.413 | 38.966 | 43.268 | 23.199 | 20.637 | 1013 | PASS |
| full-1 | 18847 | 18847 | 642.830 | 51.061 | 56.787 | 23.234 | 34.217 | 2443 | PASS |
| full-2 | 18847 | 18847 | 636.118 | 51.061 | 56.787 | 23.227 | 34.211 | 2418 | PASS |
| full-3 | 18847 | 18847 | 628.092 | 51.061 | 56.787 | 23.290 | 34.154 | 2390 | PASS |

The shortest point has only one in-call PDH observation, so its Windows peak is
sampling-limited and may miss the instantaneous peak. PyTorch peak counters are
independent of PDH sampling. Larger/full points have 19/1013/2390-2443 samples.

| Trial | Peak working set | Peak private memory | Peak system committed | Minimum system available |
|---|---:|---:|---:|---:|
| 2048 | 1.267 | 4.564 | 79.430 | 81.837 |
| 4096 | 1.431 | 7.240 | 81.956 | 81.730 |
| 8192 | 1.432 | 14.424 | 88.884 | 81.962 |
| 12288 | 1.501 | 26.305 | 101.101 | 81.528 |
| 16384 | 22.005 | 46.823 | 122.167 | 60.540 |
| full-1 | 35.630 | 60.420 | 136.010 | 52.353 |
| full-2 | 35.593 | 60.383 | 135.896 | 51.949 |
| full-3 | 35.536 | 60.388 | 135.803 | 52.303 |

System commit limit was **148.814 GiB**.
Model baseline allocated/reserved was **1.110 /
1.133 GiB** in every worker. Raw per-trial results retain
`torch.cuda.mem_get_info` before/after; free bytes reached zero at 12278 tokens
and longer without causing an OOM under Windows WDDM. These values are not a
substitute for separately sampled dedicated/shared residency.

## Interpretation and viability

There is a sharp regime change between **12278 and 16383 actual tokens**:
shared usage rises from 0.131 to 20.637 GiB, while time rises from 4.873 to
266.413 seconds. At full length, sampled shared memory reaches approximately
34.2 GiB; time is 628.092-642.830 seconds. The exact onset within that interval
was not measured and is not interpolated.

The 1.110 GiB model allocation baseline cannot explain the full-input demand.
Sequence-dependent peak allocated memory grows to 51.061 GiB and allocator
reservation to 56.787 GiB, far above physical VRAM. Windows dedicated residency
stays around 23.2 GiB and shared residency/host working set grow substantially.
The empirical allocation curve is strongly superlinear over these sampled
lengths and is consistent with sequence-dependent attention/intermediate-memory
pressure; no unprofiled kernel-specific causal claim is made.

PyTorch allocation, allocator reservation, WDDM dedicated/shared residency,
process private commit, process resident working set and system-wide commit are
different measures and must not be added or equated. System commit includes
unrelated applications; its peak alone is not Harrier's private allocation.

**Full-input trials 1/2/3 all PASS** in independent fresh processes: 642.830 /
636.118 / 628.092 seconds. Each output is 1024-dimensional, finite, normalized
(norm 0.9997392333). No OOM, abnormal worker exit, process kill or detected
Display 4101 / nvlddmkm 153 driver event occurred. Monitor errors were empty.
All full inputs have the authoritative representation hash.

Verdict: **VIABLE_FOR_FORMAL_RERUN**, high confidence for memory completion of
this input under the measured workload/state. This does not establish comfortable
VRAM headroom or general viability on a more heavily committed host. WDDM spill
is a substantial performance and host-memory risk. The original apparent stall
is consistent with the observed spill regime; its complete historical process
state is not recreated, so this is not proof of every original stall mechanism.

These are diagnostic measurements, **not formal N-05 samples or p95 values**.
No claim that Standard/Large performance gates passed follows from these results.

## Diagnostic verification correction and evidence retention

The initial PyTorch AutoModel pre-hook produced no records: installed Sentence
Transformers 6.1.0 calls the bound `model.forward` method directly, bypassing
module pre-hooks. It did not modify inference or the measured model settings.
The diagnostic tool now verifies the installed encoder's actual preprocessing
output token IDs against the untruncated frozen tokenizer before timing.

A supplemental check loaded the identical pinned CUDA/BF16 model and verified
all eight saved inputs through that same preprocessing path: token IDs and
lengths exactly match, default document prompt is null, parameter device is
CUDA:0. It did not repeat/change the measured embedding workload. Original
measurements, original tool hashes and raw logs remain preserved, alongside
`supplemental-input-verification.json`. CPU tokenization is not CPU inference.
No production embedding behavior was changed.

## Regression and reproduction

Commands:

```powershell
python benchmark/tools/n05d02_harrier_memory_diagnosis.py --run-root .local/n05d02/<new_run_id>
python -m pytest -q tests/test_n05d02_harrier_memory_diagnosis.py
python -m pytest -q
python -m ruff check .
git diff --check
```

Initial post-measurement regression: focused **9 passed**, full **550 passed,
0 failed, 2 local-Qdrant warnings**, Ruff/diff PASS. After the preprocessing
verification correction, focused **11 passed** and Ruff PASS.
Final post-review full regression: **552 passed, 0 failed, 2 warnings; focused 11 passed; repository Ruff and git diff --check PASS**.

Evidence root: `.local/n05d02/20261022T230242+0900/`. It contains environment,
source copy, input manifest, all eight requests/results/runtime metadata,
raw PDH/nvidia-smi observations, driver-event review, supplemental input proof
and regression logs. Raw text, DBs, private process paths and monitoring logs
remain Git-ignored; only tooling/tests and this aggregate evaluation are shared.

Next: **N05D-03 - Evidence-based remediation / closure checkpoint**. No automatic
formal N05D-04 rerun, representation/model redesign, Qdrant investigation or
other task was started. N05D-02 = Complete; N-05 = BLOCKED / Not Complete.
