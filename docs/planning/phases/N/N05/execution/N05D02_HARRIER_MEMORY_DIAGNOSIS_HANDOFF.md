# N05D-02 — Reference Workstation execution handoff

更新日: 2026-10-22

## Authoritative inputs

Read first:

1. `docs/planning/phases/N/N05/N05D02_HARRIER_MEMORY_DIAGNOSIS.md`
2. `docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`
3. `docs/evaluation/N05_PERFORMANCE.md`
4. `benchmark/tools/n05_run_performance.py`
5. `benchmark/tools/n05_performance_workflow.py`
6. `src/sgokb/retrieval/embedding.py`
7. `src/sgokb/retrieval/search_representation.py`

N05D-01 is Complete. Do not revisit Qdrant unless an unrelated safety check requires it. N05D-02 is the active task. Formal N-05 rerun remains prohibited until this diagnosis is complete.

## Local execution goal

Build and run a reproducible diagnostic that measures Harrier single-document embedding memory versus token length on the Reference Workstation using the preserved Large formal-run Object representation.

### Source evidence

Prefer:

```text
.local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite
object-n05-large
```

Never mutate this DB. Copy it into the new run root if repository APIs are used to reconstruct the representation.

### Frozen provider

Exactly match the N-05 provider:

```text
microsoft/harrier-oss-v1-0.6b
revision f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
bfloat16
cuda
batch_size=1
max_sequence_length=32768
overflow_policy=reject
local-files-only / offline
```

No CPU fallback, model change, truncation, reduced max length, or chunking.

## Required implementation

Create a diagnostic tool under `benchmark/tools/`, with tests under `tests/`.

Recommended structure:

```text
benchmark/tools/n05d02_harrier_memory_diagnosis.py
benchmark/tools/n05d02_run_harrier_memory_diagnosis.ps1   # optional but recommended on Windows
tests/test_n05d02_harrier_memory_diagnosis.py
```

The implementation should:

1. preserve prior evidence and create a fresh `.local/n05d02/<run_id>`;
2. verify clean `main == origin/main` at execution start;
3. fingerprint the source formal DB before/after;
4. reconstruct the actual Object overall Search Representation from a copy of that DB;
5. use the frozen Harrier tokenizer to record its exact full token count;
6. create deterministic complete-line prefixes for approximately 2048/4096/8192/12288/16384 tokens plus the full input;
7. execute each curve point in a fresh process;
8. use batch size 1 and the exact document embedding path used by SGOKB;
9. record CUDA, WDDM/shared-GPU, host/system-memory and wall-clock evidence;
10. if the full input succeeds once, run 3 independent fresh-process full-input trials total;
11. stop safely and preserve a failure if a shorter point demonstrates a terminal resource failure that makes the longer frozen input non-viable;
12. emit a machine-readable summary and verdict.

## Monitoring details

At minimum use PyTorch CUDA peak counters and system/GPU observations available on Windows.

For shared GPU memory, prefer the Windows `GPU Process Memory` performance counters and sample them during the embedding call. Keep raw samples. Do not infer peak shared usage solely from a before/after value.

Capture competing CUDA processes before measurement. Do not terminate unrelated processes automatically. If another substantial GPU workload materially invalidates the measurement, classify the run BLOCKED and report the process/evidence.

Record local model metadata including `config._attn_implementation` or the closest available actual loaded attention/backend field. The model-family default must not be guessed.

## Required token points

```text
~2048
~4096
~8192
~12288
~16384
full preserved Large Object representation
```

Use complete-line prefixes from the full representation and record actual token counts.

## Required verdict rules

### VIABLE_FOR_FORMAL_RERUN

- authoritative full representation reproduced;
- exact token count <=32768;
- full input succeeds in 3/3 independent fresh processes;
- no OOM/process kill/driver reset/CPU fallback/truncation;
- vector dimension 1024 and finite normalized output;
- memory evidence sufficient to explain the historical pressure.

Shared-memory use by itself is not a memory-viability FAIL; record it as performance risk. Formal timing remains N05D-04's responsibility.

### NOT_VIABLE_REQUIRES_DESIGN_REMEDIATION

Frozen full input cannot reliably complete because of memory/resource failure. Do not patch around it by changing the frozen contract.

### BLOCKED

Authoritative input/model/instrumentation/reference-state evidence is insufficient.

## Expected evaluation document

Create:

```text
docs/evaluation/N05D02_HARRIER_MEMORY_DIAGNOSIS.md
```

Include:

- run_id and execution HEAD;
- exact source DB/object/version/representation fingerprints;
- exact full token count;
- environment/model/backend metadata;
- a table for every curve point and every full-input repeat;
- wall-clock and all memory metrics;
- shared-memory spill/change-point interpretation if observed;
- resource-failure evidence if any;
- verdict and confidence;
- explicit statement that diagnostic measurements are not formal p95 samples;
- exact next task.

Update `N05_BLOCKER_DIAGNOSTIC_PLAN.md` and this planning area with the result.

## Regression

Before commit/push:

```powershell
python -m pytest -q <focused N05D02 tests>
python -m pytest -q
python -m ruff check .
git diff --check
```

Do not modify SGOKB production embedding behavior merely to make the diagnostic pass.

## Commit / push

Commit and push valid diagnostic tooling/evidence documentation whether the verdict is viable, not viable, or blocked, provided tests and static checks pass and the documents state the result accurately.

N05D-02 may be marked Complete only with a supported `VIABLE_FOR_FORMAL_RERUN` or `NOT_VIABLE_REQUIRES_DESIGN_REMEDIATION` verdict. A `BLOCKED` run keeps N05D-02 incomplete.

Do not start N05D-04 formal benchmark automatically.
