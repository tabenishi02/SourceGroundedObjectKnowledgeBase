# N05D-04R1 — Harrier SDPA backend / VRAM A-B diagnosis handoff

Updated: 2026-10-23

- Parent: `N05D-04 — Formal benchmark rerun`
- Status: **Historical partial / User-aborted — do not resume**
- Formal N-05: **BLOCKED / Not Complete**
- Run: `20261023T035147+0900`
- Successor: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Research/result record: `docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md`

## 1. Purpose of this document

This document preserves the R1 diagnostic intent and partial result. It is no longer the current execution handoff.

Current work must follow:

```text
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md
```

Current next task is `R2-01 — Impact survey / redesign freeze`.

## 2. Original diagnostic goal

R1 was created to determine whether the current Harrier `_attn_implementation=sdpa` workload used an avoidable high-memory SDPA path and whether a fused PyTorch backend could reduce the exact 18,847-token input without changing model, tokenizer, representation, pooling, or batch size.

Authoritative input:

```text
source DB: .local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite
object: object-n05-large
version: b9dc52be-32ea-4c31-b05e-d530635f12ed
representation SHA-256: 54db1b0c5c2d966c08e5305e4f7951667f51dafb691b1448042875bc86cfaee6
exact tokens: 18847
```

Frozen runtime:

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

## 3. Planned A/B/C comparison

```text
A = current SDPA automatic backend selection
B = forced torch.nn.attention.SDPBackend.FLASH_ATTENTION
C = forced torch.nn.attention.SDPBackend.EFFICIENT_ATTENTION
```

R1 prohibited truncation, chunking, CPU fallback, model/revision changes, and formal N-05 execution.

## 4. Partial result before user abort

Confirmed evidence:

```text
A auto-SDPA smoke: PASS
  profiler: math backend observed

B forced FLASH_ATTENTION: FAIL
  current tested Windows PyTorch build did not provide the required Flash Attention kernel

C forced EFFICIENT_ATTENTION: FAIL
  tested Q=16 / KV=8 GQA shape was rejected

A full-1: ABORTED_by_user
```

The user stopped R1 after observing concerning VRAM behavior. Related processes were terminated and RTX 4090 usage returned near idle. Therefore this run does **not** establish a persistent cross-process VRAM leak.

No alternative backend reached acceptance. R1 is not a completed performance or quality result.

## 5. Why R1 is not resumed

Subsequent design review found a more fundamental Derived Search issue:

```text
object_overall
  = Object context
  + every content-Facet Statement body

facet
  = the same detailed Statements grouped by Facet

statement
  = the same detailed Statements individually
```

The giant `object_overall` duplicates detail already available through Facet/Statement representations and created the 18,847-token full-attention input.

The user selected structural remediation instead:

```text
compact object_overview
+ facet representations
+ statement representations
+ bounded Object aggregation
+ hierarchical Object Similarity
```

Therefore R1 runtime tuning is retained only as historical diagnostic evidence.

## 6. Deferred runtime candidates

The following remain optional later candidates if the structural redesign still leaves unacceptable resource use:

- cuDNN/other supported SDPA backend;
- math SDPA BF16 reduced-precision reduction;
- Transformers FlashAttention-2 / Linux or WSL runtime;
- PyTorch runtime upgrade;
- Harrier 270M.

They are not bundled into the R2 baseline.

## 7. Safety / retention

Do not delete or overwrite raw evidence from run `20261023T035147+0900`.

Do not restart its full-input trial automatically.

Any local uncommitted R1 diagnostic code must be inspected before syncing the local repository with newer `main`; do not discard it with `reset --hard` without an explicit disposition decision.

## 8. Current successor

```text
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Next / Not Started
N-05 = BLOCKED / Not Complete
```
