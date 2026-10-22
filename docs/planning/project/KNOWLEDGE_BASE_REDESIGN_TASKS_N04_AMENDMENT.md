# Knowledge Base Redesign Task Master — N-04 Amendment

更新日: 2026-10-22

- Applies to: `docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
- Scope: Phase N / N-04 and downstream dependency state only
- Status: **Accepted amendment — N-04 Complete / N-05 Active BLOCKED**
- Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Asset disposition: `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`

## 1. Authority

この文書は、Task master内のN-04旧記述と、その後のPhase N current stateを2026-10-22以降の状態へ上書きするamendmentである。

N-04の旧generation-quality Gateはsupersede済み。

## 2. Amended Phase N state

```text
N-01 Complete
N-02 Complete
N-03 Complete
N-04P-01..P-06 Complete
N-04R-01..R-05 Complete
N-04 Complete / PASS
N-05 Active / formal BLOCKED
N-06 Ready
N-07 Pending
```

N-05の`BLOCKED`はperformance FAILではない。2026-10-22 formal benchmarkは実行されたが、runtime blockerによりformal performance statisticsを確定できなかった。

## 3. Amended N-04 definition

N-04はAI Knowledge Access Boundaryを受入試験する。

formal evaluation:

- public MCP / Application read boundary
- correct Object / current accepted Version
- purpose-specific Context construction
- Similarity → Context integration
- traceability
- budget / omission / truncation contract
- canonical invariance
- integrity / regression

Consumer LLM output quality / Grounded Generation / Atomicity / Content-Type / Frozen 47はformal Gateではない。

## 4. Dependency

```text
N-03 Complete
  ├─ N-04 Knowledge Access Acceptance  Complete / PASS
  ├─ N-05 Performance                 Active / BLOCKED
  └─ N-06 Retrieval / Vector Quality  Ready
        ↓
      N-07 Failure / Recovery
```

N-04 / N-05 / N-06は兄弟Taskである。

## 5. N-04 reconstruction

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Complete
N-04R-03 Formal Harness Reconstruction           Complete
N-04R-04 Reference Workstation Re-Acceptance     Complete / PASS
N-04R-05 Grounded Generation Asset Disposition   Complete
```

## 6. Grounded Generation disposition

```text
KEEP_CORE
  Grounded Generation chainから0件

MOVE_CONSUMER_SIDE
  implementation / verifier / pipeline / architecture

KEEP_EXPERIMENTAL
  failure analysis / Frozen 47 / G-25A research evidence

RETIRE
  old generation-quality harness / execution tooling
```

## 7. N-05 formal benchmark state

Formal targets:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

Formal run:

```text
run_id: 20261022T130413+0900
HEAD:   a7147f9842f94e96944bc7f67b4c3986970462b0
```

Observed:

```text
Standard:
  23 / 23 sample terminal failure
  Qdrant payload index creationでgridstore path関連error
  Render未到達

Large:
  cold-01 Embedding中断
  Object representation 18,847 tokens
  dedicated VRAM 約23.2 GiB
  shared GPU memory 約34.2 GiB
  required samples未取得
```

Formal evaluator:

```text
BLOCKED
```

Standard/Largeのformal warm p50 / p95 / maxは未判定。

Post-run:

```text
Evaluator tests 8 PASS
Full pytest 517 PASS
Ruff PASS
diff check PASS
canonical/tracked/HEAD safety PASS
```

## 8. N-05 blocker diagnostic chain

```text
N05D-01 Qdrant storage/path blocker diagnosis   Next
N05D-02 Long-input Harrier memory diagnosis     Pending
N05D-03 Evidence-based remediation              Pending
N05D-04 Formal benchmark rerun                  Pending
```

正本:

`docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`

formal Gateはblocker diagnosisを理由に変更しない。

## 9. Current authority

N-04:

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/decisions/N04R05_GROUNDED_GENERATION_ASSET_DISPOSITION.md`
3. `docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`

N-05:

1. `benchmark/n05-performance-contract-v1.json`
2. `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`
3. `docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`
4. `docs/evaluation/N05_PERFORMANCE.md`
5. `docs/planning/phases/N/PHASE_N_PREPARATION.md`

## 10. Current next work

```text
N05D-01 — Qdrant storage/path blocker diagnosis
```

N-06 remains independently Ready.
