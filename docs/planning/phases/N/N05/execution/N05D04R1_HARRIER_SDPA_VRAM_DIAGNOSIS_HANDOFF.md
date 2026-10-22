# N05D-04R1 — Harrier SDPA backend / VRAM A-B diagnosis handoff

Updated: 2026-10-23

- Parent: `N05D-04 — Formal benchmark rerun`
- Status: **Ready / Not Started**
- Formal N-05: **BLOCKED / Not Complete**
- Trigger: formal attempt `20261023T025413+0900` aborted after disk-full and severe Harrier WDDM spill observations
- Research basis: `docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md`

## Goal

Determine whether the current Harrier `_attn_implementation=sdpa` workload is using an avoidable high-memory SDPA path and whether forcing a fused PyTorch SDPA backend can materially reduce the exact 18,847-token input's GPU/shared-memory demand without changing model, tokenizer, representation, pooling, or batch size.

This is a diagnostic. It is not a formal N-05 sample.

## Frozen input/runtime

Reuse the authoritative N05D-02 input and source reconstruction:

```text
source DB: .local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite
object: object-n05-large
version: b9dc52be-32ea-4c31-b05e-d530635f12ed
representation SHA-256: 54db1b0c5c2d966c08e5305e4f7951667f51dafb691b1448042875bc86cfaee6
exact tokens: 18847
```

Keep:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
device: cuda
batch_size: 1
max_sequence_length: 32768
overflow_policy: reject
normalize_embeddings: true
```

No truncation, chunking, CPU fallback, model/revision change, or formal-run execution is allowed.

## Required A/B/C trials

Each trial must be an independent fresh Python process and must retain failures.

```text
A = current SDPA automatic backend selection
B = force torch.nn.attention.SDPBackend.FLASH_ATTENTION
C = force torch.nn.attention.SDPBackend.EFFICIENT_ATTENTION
```

Use `torch.nn.attention.sdpa_kernel(...)` for B/C. A forced backend must not silently fall back to another backend. If unsupported, record the exact warning/error and classify that candidate unsupported.

Run each supported candidate at least twice at full 18,847-token length after a shorter smoke proves it can start. Preserve every trial; do not retry until PASS and discard failures.

## Measurements

For every trial record:

```text
requested backend
accepted/effective backend evidence where obtainable
wall-clock embedding seconds
Torch baseline/peak allocated
Torch baseline/peak reserved
Windows process Dedicated GPU memory peak
Windows process Shared GPU memory peak
process working set/private memory
system committed/available memory
output dimension
finite check
vector norm
input/token-ID identity
exception/warning
```

Compare candidate output to baseline A:

```text
cosine similarity
max absolute component difference
mean absolute component difference
```

Do not set an arbitrary quality PASS threshold only to accept a faster backend. Preserve the measurements for retrieval-level validation.

## Backend-dispatch evidence

Where possible, use PyTorch profiler/logging or backend-forcing failure messages to establish which kernel can actually serve this input. Do not infer the active kernel merely because `_attn_implementation=sdpa` or because Flash/efficient availability flags are true.

If the automatic A path cannot be identified precisely, it remains valid as the measured baseline, but document that the exact A dispatch remains unknown.

## Acceptance for proceeding to runtime adoption review

A candidate B/C is a strong adoption candidate if it:

- completes the exact input reliably;
- materially lowers the 51.061 GiB allocated / ~34.2 GiB shared-memory baseline or materially reduces ~630 s latency;
- uses no CPU fallback/truncation;
- emits valid normalized 1024-dimensional vectors;
- has quantified numerical difference from baseline.

Do not modify production `SentenceTransformerEmbeddingProvider` during the measurement phase.

## If built-in fused SDPA is unavailable

Stop after preserving the evidence and prepare a separate P1 evaluation of Transformers `attn_implementation="flash_attention_2"`. Do not install an unpinned package/kernel or enable network fallback inside this diagnostic without separate documentation and reproducibility review.

## Disk preflight

Before any future formal benchmark—not necessarily before this small diagnostic—run:

```powershell
python benchmark/tools/n05_resource_preflight.py `
  --qdrant-root C:\Qdrant\SGOKB `
  --output .local\n05d04\resource-preflight.json
```

Formal N05D-04 requires at least 32 GiB free on each relevant volume.

## Regression and result recording

Add focused tests for any diagnostic tool. After diagnostic implementation/results:

```powershell
python -m pytest -q <focused tests>
python -m pytest -q
python -m ruff check .
git diff --check
```

Document results in:

```text
docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md
```

Do not restart formal N05D-04 automatically. The result must first decide whether to keep current SDPA, adopt a forced fused backend, or investigate Transformers FlashAttention-2 / design remediation.
