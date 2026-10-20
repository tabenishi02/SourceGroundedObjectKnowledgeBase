# N-04G-25 — v4 Development Benchmark / Adversarial Regression Tasks

更新日: 2026-10-21

- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Architecture authority: `docs/decisions/N04G23F_V4_DESIGN_INTEGRATION_AND_FREEZE.md`
- G-24 result: `docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md`
- Residual classifier design: `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
- Status: **G-25A NEXT / G-25B blocked by G-25A PASS**
- N-04: **Failed / not Complete**
- N-05: **blocked**

## 1. Purpose

G-24で実装したv4 pipelineについて、formal Reference Workstation freeze前にResidual classifierの具体componentを選定し、統合adversarial regressionを実施する。

G-23A-E7でResidual Atomicity依存はarchitecture blockerではなくbounded implementation/benchmark riskと判断したが、**classifier未選定のままG-26へ進むことは禁止する。**

G-24はCompleteとなったためG-25AをNEXTとする。ただしG-24中にReference Workstation全repo verificationを実行できなかったため、G-25Aは`N04G25A_NEXT_CHAT_HANDOFF.md`のmandatory preflight PASS後にのみbenchmarkを開始できる。

## 2. Task chain

```text
G-24 v4 implementation                              Complete
  ↓
G-25A Residual Classifier Benchmark / Selection     NEXT
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression          blocked
  ↓ PASS only
G-26 Reference Workstation v4 harness freeze        blocked
```

G-25AまたはG-25Bがvalid FAILの場合、G-26はblockedのままとする。

## 3. G-25A — Residual Classifier Benchmark / Selection

Status: **NEXT**

### 3.0 Mandatory implementation preflight

Before any classifier benchmark:

```text
python -m pytest -q tests/test_n04g24_v4_implementation.py tests/test_n04g24_v4_provider_runtime.py
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS. Any failure returns to G-24 implementation remediation; do not begin classifier selection with a failing implementation baseline.

### 3.1 Inputs

- E5 Residual Classifier Evaluation Plan
- E6 Frozen 47 Gold desk replay
- G-24 classifier adapter/interface implementation
- G-24 implementation result
- Reference Workstation runtime

### 3.2 Dataset preparation

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

```text
PASS / selected V2-R-A and V2-R-C
or
VALID_FAIL_NO_SELECTION
```

`VALID_FAIL_NO_SELECTION`ならG-25B/G-26へ進めずexplicit escalationを作成する。

## 4. G-25B — Integrated v4 Adversarial Regression

Status: **Planned / blocked by G-25A PASS**

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
