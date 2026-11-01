# N-04G-25 — v4 Development Benchmark / Adversarial Regression Tasks

更新日: 2026-10-22

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Architecture authority: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
- G-24 result: `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`
- Residual classifier design: `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
- G-25A block record: `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`
- Status: **G-25A development VALID_FAIL_NO_SELECTION / not Complete; G-25B/G-26 blocked**
- N-04: **Failed / not Complete**
- N-05: **blocked**

## 1. Purpose

G-24で実装したv4 pipelineについて、formal Reference Workstation freeze前にResidual classifierの具体componentを選定し、統合adversarial regressionを実施する。

G-23A-E7でResidual Atomicity依存はarchitecture blockerではなくbounded implementation/benchmark riskと判断したが、**classifier未選定のままG-26へ進むことは禁止する。**

G-24はCompleteだが、G-25AはReference Workstation mandatory preflightをPASSするまでclassifier benchmarkを開始できない。

## 2. Task chain

```text
G-24 v4 implementation                              Complete
  ↓
G-25A Reference Workstation preflight               PASS
  ↓ PASS only
G-25A Residual Classifier Benchmark / Selection     VALID_FAIL_NO_SELECTION
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression          blocked
  ↓ PASS only
G-26 Reference Workstation v4 harness freeze        blocked
```

G-25AまたはG-25Bがvalid FAILの場合、G-26はblockedのままとする。

## 3. G-25A — Residual Classifier Benchmark / Selection

Status: **Mandatory preflight PASS / development selection VALID_FAIL_NO_SELECTION (not Complete)**

### 3.0 Mandatory implementation preflight

Before any classifier benchmark:

```text
python -m pytest -q tests/test_n04g24_v4_implementation.py tests/test_n04g24_v4_provider_runtime.py
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS. Any failure returns to G-24 implementation remediation; do not begin classifier selection with a failing implementation baseline.

In the earlier blocked attempt on 2026-10-21 the authorized Reference Workstation `Reference Workstation` was online and paired, but Desktop Commander reported that its remote command execution was unavailable and explicitly instructed not to retry or reconnect. Therefore none of the four preflight commands was executed.

Preflight result and historical block authority:

`docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`

At the 2026-10-21 preflight completion (historical snapshot): Reference Workstation rerun `20261021T123230+0900` passed all four commands: targeted 22, full suite 448 (0 failed), Ruff and diff check PASS, after an import-order-only I001 repair. See `docs/evaluation/N04G25A_REFERENCE_WORKSTATION_PREFLIGHT_BLOCKED.md`. Classifier benchmark is READY / not started; G-25A is not Complete. This preflight task performed no Frozen 47 classifier run or model/threshold tuning.

The development benchmark is complete: **VALID_FAIL_NO_SELECTION**. No candidate passed either task; final confirmation remains not started.

### 3.1 Inputs

- E5 Residual Classifier Evaluation Plan
- E6 Frozen 47 Gold desk replay
- G-24 classifier adapter/interface implementation
- G-24 implementation result
- Reference Workstation runtime

### 3.2 Dataset preparation after preflight PASS

Atomicity / Content-Typeを別datasetとして構築する。

Required policy:

- pattern-family holdout
- derivation-lineage grouping
- random row splitをselection authorityにしない
- Frozen 47 Goldをtraining/threshold tuningに使い回さない
- ambiguous fixtureを無理にhard targetへ変換しない
- transformation後labelを自動継承しない

### 3.3 Candidate families

最低限:

```text
encoder sequence classifier
cross-encoder / pair classifier
lightweight/few-shot classifier
historical bounded-LLM baseline
```

AtomicityとContent-Typeは別component/別checkpointを許可し、joint classifierへ戻さない。

### 3.4 Selection Gate

Atomicity:

```text
critical NON_ATOMIC false-pass = 0
required ATOMIC false-reject target = 0
repeatability exact/100% as applicable
AMBIGUOUS/UNAVAILABLE = fail-closed
```

Content-Type:

```text
critical wrong-compatible false-pass = 0
required valid compatible false-reject target = 0
repeatability exact/100% as applicable
MIXED/AMBIGUOUS/UNAVAILABLE = fail-closed
```

Selectionはaccuracy最大化ではなくSafety Gate優先。

全候補FAIL:

```text
VALID_FAIL_NO_SELECTION
```

とし、Gateを緩めない。

### 3.5 Frozen 47 confirmation

Model/threshold/abstention policy freeze後にFrozen 47 Goldをfinal confirmationとして実行する。

同じFrozen結果を見てmodel/thresholdを再調整した場合、そのrunはselection evidenceとして無効。

The blocked preflight attempt generated no classifier output against Frozen 47 and did not tune any classifier from it.

### 3.6 Reproducibility

最低限保存する。

```text
base model + revision
artifact/checkpoint SHA-256
training code commit
training dataset manifest/hash
split manifest/hash
seed/hyperparameters
class mapping
threshold/abstention policy
Python/PyTorch/CUDA/library identity
latency/VRAM
```

### 3.7 Outcome

After preflight PASS and benchmark execution:

```text
PASS / selected V2-R-A and V2-R-C
or
VALID_FAIL_NO_SELECTION
```

`VALID_FAIL_NO_SELECTION`ならG-25B/G-26へ進めずexplicit escalationを作成する。

Current development outcome is **VALID_FAIL_NO_SELECTION**. No V2-R-A or V2-R-C is eligible; G-25A is not Complete and Frozen 47 remains NOT STARTED.

## 4. G-25B — Integrated v4 Adversarial Regression

Status: **Blocked by G-25A PASS**

G-25Aで選定したcomponentをv4 pipelineへ接続し、Stage 1 / certification / Stage 2 / final validationを統合評価する。

Minimum hard gates:

```text
critical Atomicity false-pass = 0
critical content-role wrong-compatible false-pass = 0
unsupported rendered material claim = 0
accepted role escape = 0
invalid certified fact binding acceptance = 0
invalid interpretation premise acceptance = 0
creative scope violation acceptance = 0
```

Additional metrics:

```text
required-valid false reject
certified fact yield
required material coverage
INDETERMINATE/abstention rate
Stage 1 retry rate
Stage 2 retry rate
terminal ACCEPTED eligibility
latency / VRAM
```

Material yieldがfail-closed運用で実用上成立しない場合は、Safety Gateを緩めずarchitecture/implementation escalationへ戻す。

## 5. G-26 unblock condition

G-26をunblockできるのは次をすべて満たす場合のみ。

- [ ] G-25A implementation preflight PASS
- [ ] G-25A PASS / concrete V2-R-A selected
- [ ] G-25A PASS / concrete V2-R-C selected
- [ ] Frozen 47 final confirmation valid
- [ ] G-25B hard gates PASS
- [ ] runtime/model/dataset/split identity frozen
- [ ] no Gate weakening after results

それまではG-26をblockedとする。

## 2026-10-22 development selection result

Run `20261022T000426+0900` completed all four candidates, both tasks and three repeats. **VALID_FAIL_NO_SELECTION**: no eligible V2-R-A or V2-R-C. Frozen policies/Gates were retained; no selected-checkpoint freeze was created. Frozen 47 final confirmation is **NOT STARTED**.

Engineering: focused 34 passed; full pytest 482 passed / 0 failed / 0 skipped (2 existing local-Qdrant warnings); repository-wide Ruff and diff check PASS. G-25A remains not Complete; G-25B/G-26 remain blocked, N-04 Failed/not Complete and N-05 blocked.

Result and explicit escalation: `docs/evaluation/N04G25A_DEVELOPMENT_CLASSIFIER_SELECTION.md`; `benchmark/results/n04g25a-development-selection-reference-workstation.json`. A separate approved remediation/evaluation protocol with untouched held-out evidence is required. Do not retune from these selection results, weaken Gates, or begin Frozen 47 with failed candidates.
