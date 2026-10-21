# N-04G-25A — Reference Workstation Preflight Result (Previous Block Resolved)

更新日: 2026-10-21

- Task: `N-04G-25A — Residual Classifier Benchmark / Selection`
- Mandatory Reference Workstation preflight: **PASS**
- Classifier benchmark: **READY / not started**; G-25A itself is **not Complete**.
- Design authority: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
- Handoff authority: `docs/planning/phases/N/N04/post-g12/N04G25A_NEXT_CHAT_HANDOFF.md`
- G-25B remains blocked by G-25A selection PASS; G-26 remains blocked by G-25B PASS.
- N-04: **Failed / not Complete**; N-05: **blocked**.

## 1. Repository and verification identity

Local state before synchronization:

- Branch `phase-n/n04g23ar-judge-candidate-evaluation`, HEAD `e09ea5f8ed1d43d3e5168411cf6e23c8ccdb08e6`.
- Working tree clean; HEAD vs fetched origin/main: 7 local-only / 61 remote-only commits. The historical branch was retained; its commits were not merged into main.
- Local main was safely fast-forwarded to authoritative GitHub main `a41bf018c28782840718043da073c69507ec545e`.
- Work continued on `verification/n04g25a-reference-preflight`, initially clean and 0/0 relative to origin/main.

Successful Reference Workstation run: **`20261021T123230+0900`**.

The four commands ran against GitHub main `a41bf018c28782840718043da073c69507ec545e` plus the sole import-order repair in `tests/test_n04g24_v4_implementation.py`. Test source bytes were unchanged after verification and were committed as **`a92d89886eb8e82be9893a5388ac50e5f8068077`**. No production implementation change was required.

At test execution, `git status --short` contained only:

```text
 M tests/test_n04g24_v4_implementation.py
```

After the repair commit the working tree was clean. Subsequent changes are this preflight result and current task/handoff status documentation only; the final documentation commit is reported in the completion response.

Repaired test SHA-256: `5a96d99dbaa733d7e041e43166bfff5f20cb138f005470f2e44693dfa557e62d`.

## 2. Commands and measured results

Normal project `.venv` was used; no package installation/update or substitute runtime was used.

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_n04g24_v4_implementation.py tests/test_n04g24_v4_provider_runtime.py` | **22 passed, 0 failed**, 0.42s |
| `python -m pytest -q` | **448 passed, 0 skipped, 0 failed**, 2 warnings, 143.03s |
| `python -m ruff check .` | **PASS**, all checks passed |
| `git diff --check` | **PASS**, no output / exit 0 |

All four commands were rerun from the beginning after repair. The full suite includes the 22 targeted tests; these are not 470 distinct tests. The two warnings concern existing local-Qdrant payload-index and exact-search-parameter behavior in `test_hybrid_search`, not test failures.

Runtime versions:

- Python **3.10.6**
- pytest **9.1.1**
- Ruff **0.17.0**

## 3. Historical blocked/failed attempts and repair

The earlier remote-command attempt on 2026-10-21 could not start because Desktop Commander reported a monthly execution quota and instructed not to retry/reconnect. That availability block did not establish a G-24 PASS or FAIL. This later verification used the workstation's local terminal, not a retry of that remote service.

Local run **`20261021T052846+0900`** then produced targeted **22 passed** and full suite **448 passed**, but repository-wide Ruff failed with one **I001** import-order error in `tests/test_n04g24_v4_implementation.py`. It was classified as **G-24 implementation verification failure**; the sequence stopped before diff-check and classifier benchmarking remained prohibited.

The repair moved `ActiveAttemptLedger` after the constants in the same `from sgokb.grounding.v4_pipeline import (...)` statement. It changes no assertion, fixture, test coverage or implementation behavior. No skip/xfail or Gate relaxation was introduced. The original failure logs and helper were retained; successful rerun has a new run ID.

G-23F authority order, Reference Integrity, separate Residual Atomicity/Content-Type boundaries and Frozen 47 bytes remain unchanged.

## 4. Reference Workstation inventory

Read-only inventory was captured for a future benchmark, not as classifier acceptance evidence:

- NVIDIA-SMI / driver: **581.80**.
- NVIDIA-SMI CUDA compatibility display: **13.0**.
- PyTorch: **2.6.0+cu124**; PyTorch CUDA build: **12.4**; CUDA available: true.
- Primary GPU: **NVIDIA GeForce RTX 4090**, **24564 MiB** reported by NVIDIA-SMI (25756696576 bytes reported by PyTorch).
- Secondary GPU: **Quadro P1000**, approximately **4 GiB** (4294836224 bytes reported by PyTorch).

Driver CUDA compatibility and the PyTorch CUDA build are separate identities. No classifier model was loaded, trained, tuned or selected by this preflight.

## 5. Evidence and protected scope

Ignored local evidence:

```text
.local/n04-v4/g25a-preflight/20261021T052846+0900/  # preserved Ruff failure
.local/n04-v4/g25a-preflight/20261021T123230+0900/  # successful rerun
```

Successful evidence includes environment/branch/HEAD/status, repaired-file digest and diff, exact four-command exit codes/stdout/stderr, NVIDIA-SMI/PyTorch inventory and protected-input hash checks. Raw logs/environment paths are not committed.

No Frozen 47 classifier execution, development-corpus construction, model/threshold/abstention tuning, classifier selection, provider capability acceptance or downstream benchmark was performed. G-23F and Frozen 47 hashes are unchanged. Mandatory preflight PASS is implementation-baseline evidence only.

## 6. Current state and next boundary

```text
G-24 = Complete / Implementation Ready for G-25A
G-25A mandatory preflight = PASS
G-25A classifier benchmark = READY / not started
G-25A = not Complete / selection not performed
G-25B = blocked by G-25A selection PASS
G-26 = blocked by G-25B PASS
N-04 = Failed / not Complete
N-05 = blocked
```

The preflight prerequisite is satisfied. A later G-25A benchmark task may proceed under the existing handoff/E5 plan; this task stops at readiness and performs no Frozen 47 run or tuning. G-25A/G-25B selection/safety Gates remain mandatory and unchanged.
