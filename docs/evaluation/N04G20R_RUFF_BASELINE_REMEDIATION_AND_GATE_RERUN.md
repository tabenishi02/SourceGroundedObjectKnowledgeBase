# N-04G-20R Repository-wide Ruff Baseline Remediation + G-20 Engineering Gate Rerun

更新日: 2026-10-19

- Status: **Complete / PASS**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-20 repository-wide Ruff `180 errors`
- Branch: `phase-n/n04g20r-ruff-baseline`
- Pull Request: `#45`
- Final engineering Gate run: `39224975505`
- Tested branch SHA: `24b0316aaff2a864c084400f50af920b933c3c24`
- G-20 record: `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`

---

## 1. Decision

N-04G-20で唯一未達だったrepository-wide Ruff baselineを修復し、G-20 engineering Gateを再実行した。

Final result:

```text
G-20 focused / replay tests       PASS — 37 passed
full pytest                       PASS — 388 passed / 5 skipped / 0 failed
repository-wide Ruff              PASS — All checks passed!
git diff --check                  PASS
```

したがって:

```text
N-04G-20R = Complete / PASS
N-04G-20 engineering blocker = resolved
N-04G-21 = unblocked / NEXT
N-04 = Failed / not Complete
N-05 = blocked
```

N-04そのものはG-22 formal v3 re-acceptance PASS前にCompleteへ変更しない。

---

## 2. Initial Ruff debt classification

G-20 final runでrepo-wide:

```text
python -m ruff check .
```

が180 errorsを検出していた。

G-20Rで確認したlint debtは、Ruffの既存`E / F / I` selection内のstyle/static-cleanup classであった。

主なclass:

```text
I001  import block ordering / formatting
F401  unused imports
E501  line length
E702  multiple statements separated by semicolon
```

代表対象:

```text
extensions/web-page-capture/*
src/sgokb/exchange/*
src/sgokb/grounding/*
src/sgokb/retrieval/*
src/sgokb/storage/*
tests/*
```

G-18 Frozen grounded-generation semanticsの変更を必要とするlint classは確認されなかった。

---

## 3. Remediation policy

G-20RではGateを緩める方法を使用しなかった。

使用しなかったもの:

```text
Ruff rule disable
ignore / per-file-ignore追加
noqa追加
line-length緩和
G-20 Gateのchanged-scope-onlyへの読み替え
```

実施したもの:

```text
ruff format
ruff check --fix
import ordering
unused import cleanup
long expression / literal wrapping
semicolon-separated statementsの通常行化
```

長い日本語固定文字列は、文字列値を変更せずPythonの隣接文字列連結へ分割した。

---

## 4. Remediation progression

### Baseline

```text
repository-wide Ruff: 180 errors
```

### Automated cleanup

Repository-wide `ruff format`と`ruff check --fix`を使用して、自動修正可能なimport / unused import / formatting debtを整理した。

その後のengineering Gate:

```text
focused/replay: PASS
full pytest: PASS
Ruff: 23 errors
```

残存はE501のみだった。

### Residual cleanup

`instructions.py`、`package_transfer.py`、grounded-generation testの長い行を値・挙動を変えない形で分割した。

次のrunでは:

```text
Ruff: 17 errors
```

まで減少した。17件はすべて`src/sgokb/exchange/instructions.py`の日本語固定文字列であり、Ruff formatterが隣接文字列を再結合したため残存していた。

### Final targeted cleanup

対象literal keyを明示し、formatterによる再結合を行わず隣接文字列として分割した。

対象例:

```text
series
franchise
event
product
taxon
concept
theme
ideology
continuity
software
service
phenomenon
writing_system
creative_work
capability
temporal_entity
symbolic_system
```

`instructions.py`単体Ruff PASSを確認後、full engineering Gateへ進んだ。

---

## 5. Final engineering Gate

GitHub Actions:

```text
run_id: 39224975505
job: verify
OS: Ubuntu 24.04.5 LTS
Python: 3.10.22
Ruff: 0.17.1
```

### Focused / replay

Command:

```text
python -m pytest tests/test_n04_grounded_generation.py tests/test_n04g20_adversarial_regression.py -q
```

Result:

```text
37 passed in 0.22s
```

### Full pytest

Command:

```text
python -m pytest -q
```

Result:

```text
388 passed, 5 skipped in 105.86s
0 failed
```

### Repository-wide Ruff

Command:

```text
python -m ruff check .
```

Result:

```text
All checks passed!
```

### Diff check

Command:

```text
git diff --check origin/main...HEAD
```

Result:

```text
PASS
```

---

## 6. Semantic / regression assessment

G-20Rの目的はlint baseline restorationであり、G-18 Frozen semanticsの再設計ではない。

確認事項:

- G-20 provider/application V0 identity fixを維持。
- G-20 adversarial/replay suite 37 PASSを維持。
- full pytest 0 failedを維持。
- Grounding validation contractを緩和していない。
- Material / terminal / renderer policyを緩和していない。
- Ruff configurationを緩和していない。

Formatting/import cleanup後のtest結果から、既存machine-observable behavior regressionは検出されなかった。

---

## 7. Verifier benchmark evidence

G-20Rではsource-fact verifier architecture / MiniCheck benchmark corpus / score composition / threshold semanticsを変更していない。

したがってG-20で得たcandidate screening evidence:

```text
MiniCheck RoBERTa-large
required negative/replay false-positive = 0
required positive supported = 2 / 2
threshold diagnostic candidate = 0.50
```

はG-21 candidate selection evidenceとして再利用する。

G-20RではMiniCheck benchmarkを再実行していない。

これはproduction verifier profile freezeを意味しない。exact checkpoint / threshold profile / independent judge / Reference Workstation local runtimeはG-21でfreezeする。

---

## 8. G-21 eligibility

G-20R PASSによりG-20 engineering blockerは解消した。

次Task:

```text
N-04G-21 [P0]
v3 Acceptance / Reference Workstation Harness Freeze
```

G-21では少なくとも次をfreezeする。

- generator model/runtime/settings
- source-fact verifier exact checkpoint/revision
- verifier threshold profile/hash
- independent source-fact judge model/settings
- interpretation derivation judge model/settings
- atomicity/role validator runtime
- formal material requirement profiles
- provider structured-output schema/hash
- retry / terminal policy
- evidence tree
- formal rubric

Reference Workstation local-only runtime evidenceは引き続きG-21の責務である。

---

## 9. Completion checklist

- [x] Ruff 180 errorsを分類した。
- [x] Ruff設定を緩和せず修正した。
- [x] `noqa` / ignoreによる回避を行わなかった。
- [x] style/import/line wrapping中心でbaselineを修復した。
- [x] G-20 provider/application V0 fixを維持した。
- [x] focused/replay 37 PASS。
- [x] full pytest 388 passed / 5 skipped / 0 failed。
- [x] repository-wide Ruff PASS。
- [x] `git diff --check` PASS。
- [x] G-20 verifier screening evidenceの再利用可否を確認した。
- [x] G-21をunblockできる状態になった。

**N-04G-20R = Complete / PASS.**
