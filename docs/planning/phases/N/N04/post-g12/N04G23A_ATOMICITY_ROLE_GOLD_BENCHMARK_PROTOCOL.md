# N-04G-23A Atomicity / Role Gold Benchmark Protocol

更新日: 2026-10-20

- Status: **Prepared / execution pending**
- Parent: `N-04G-23 Two-Stage Grounded Generation Architecture`
- Trigger: G-22 valid formal FAIL, especially Case 2 `role-INDETERMINATE` on faithful source-fact restatements
- Normative boundary: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- Historical execution: `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md`
- Production code change: **none**
- Frozen v3 artifact change: **none**

---

## 1. Goal

G-22で観測したAtomicity / Role Gateの過剰reject候補について、次を分離する。

```text
H1  Phi-4 model capability problem
H2  historical G-22 joint prompt/task-definition problem
H3  atomicity + roleを1 callで同時判定するtask coupling problem
```

本Taskは`support / entailment`のbenchmarkではない。

特に次を混同しない。

```text
unsupported source_fact
    != ROLE_VIOLATION

false source_fact
    != ROLE_VIOLATION

source_fact support判定
    != Atomicity / Role Gate
```

source-world propositionは、後段でunsupportedと判定される内容でも、content typeとして`source_fact`なら`ROLE_VALID`になり得る。

---

## 2. Gold authority

Gold labelはG-14のnormative invariantだけをauthorityとする。

### Atomicity

`ATOMIC`:

- 1 unit内に、独立して異なるgrounding verdictを持ち得るmaterial propositionが1つ以下。
- 1 propositionを複数support refで共同supportすることは許容。

`NON_ATOMIC`:

- 複数material propositionを含み、部分ごとに異なるgrounding verdictが可能。
- または異なるgrounding policyを必要とするcontentを混在。

`INDETERMINATE`:

- Gold reviewer自身がG-14だけでは安全に確定できない場合のみ使用。
- Gold `INDETERMINATE` caseは診断対象には含めるが、required Gateから除外する。

### Role boundary

content-firstで判定する。

`ROLE_VALID`:

- content semantics
- declared `semantic_role`
- `purpose`
- `presentation_role`

が整合する。

`ROLE_VIOLATION`:

- source-world factを`creative_addition`へ逃がす。
- interpretationを`source_fact`へ偽装する。
- invented contentを`source_fact`として扱う。
- purpose / presentation roleがsemantic role policyと矛盾する。

`INDETERMINATE`:

- content typeを安全に確定できない場合のみ。

---

## 3. Corpus construction

### 3.1 Tracked seed

```text
benchmark/n04g23a-atomicity-role-gold-seed-v1.json
```

seedにはG-20再利用caseとfranchise knowledge不要のsynthetic controlsを含む。

目的:

- supportとroleの分離
- obvious atomic/non-atomic controls
- source_fact / interpretation / creative_addition boundary
- presentation-role / purpose mismatch
- mixed-grounding-policy detection

### 3.2 Required G-22 exact import

Reference Workstation上の保存証跡:

```text
.local/n04-v3/runs/20261020T030904+0900/
```

から、3 Case × 両Attemptの**全material unitをexact textで取り込む**。

推測・evaluation summaryからの再構成は禁止。

最低保持metadata:

```text
g22_case_id
g22_attempt
block_id
unit_id
text
semantic_role
purpose
presentation_role
evidence_path
```

Gold labelはhistorical Phi-4 verdictをコピーせず、G-14 ruleで独立付与する。

必要なら:

```text
gold_confidence = high / medium / low
```

を付ける。

`required=true`にできるのは原則`high`だけとする。

最終corpus:

```text
benchmark/n04g23a-atomicity-role-gold-v1.json
```

Finalization時:

```text
status = frozen_for_execution
source_g22_run_id = 20261020T030904+0900
```

とし、SHA-256を記録する。

---

## 4. Prompt conditions

### P0 — `g22-exact-joint`

G-22で実際に使用したAtomicity / Role Phi-4 requestを**byte-equivalentに再現**するhistorical baseline。

現在のtracked profileはplaceholderであり、Reference Workstationの保存request/helperからexact prompt/template/response schemaを取り込むまで実行禁止。

```text
benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json
```

Exact importでは:

1. 保存G-22 request payloadをauthorityにする。
2. 実行helper sourceだけから推測しない。
3. parameterized templateをG-22 actual unitへ再renderし、historical messagesと一致することを検証する。
4. exact response schema / temperature / max_tokens / seedも一致させる。
5. 一致しない場合はP0をBLOCKEDとし、近似promptを`exact`と呼ばない。

### P1 — `clarified-joint-v1`

同じPhi-4・同じjoint callだが、G-14 definitionを明示する。

特に:

- support/truthを判定しない。
- unsupportedでもsource-world factual contentならrole-validになり得る。
- atomicityとroleを独立に返す。
- content-first role classification。

### P1P — `clarified-joint-v1-paraphrase-a`

P1と意味上同じruleを別表現にしたprompt。

```text
benchmark/n04g23a-atomicity-role-paraphrase-profile-v1.json
```

目的はprompt-paraphrase stability測定であり、結果を見てから調整してはならない。

### P2 — `split-v1`

同じPhi-4で:

```text
Atomicity call
+
Role-only call
```

へ分離する。

一方の曖昧さが他方へ波及するtask couplingを測る。

---

## 5. Runtime identity

G-22比較のため、原則G-22のbounded judge条件を維持する。

```text
LM Studio              0.4.25.0
model alias             sgokb-n04-phi4
model                   Phi-4 Q4_K_S
context                 8192
GPU                     max / RTX 4090
parallel                1
temperature             0
max_tokens              64
seed                    20261018
stream                   false
```

Web / cloud inference / external retrievalは禁止。

モデルidentityがG-22と一致しない場合はbenchmark開始前にBLOCKEDとする。

---

## 6. Execution freeze boundary

結果を見てprompt/corpusを変更することを防ぐ。

### Preparation phase

1. seed + G-22 exact unitからfinal Gold corpus作成。
2. Gold review完了。
3. P0 exact historical profileを取り込む。
4. P1 / P1P / P2が変更されていないことを確認。
5. contract tests / Ruff / diff check PASS。
6. corpus / prompt profilesのSHA-256保存。
7. **ここでcommit + pushする。**

このcommitを`benchmark_input_head`とする。

### Execution phase

`benchmark_input_head`以後、全P0/P1/P1P/P2実行終了まで次を変更禁止:

- Gold corpus
- Gold labels
- required / critical flags
- prompt text
- response schema
- model/settings
- runner scoring rule

誤りを発見した場合は結果を無効化し、Preparationへ戻り新しいrunとして開始する。

---

## 7. Repeats

全profile・全caseを3回実行する。

```text
temperature = 0
seed = 20261018
repeats = 3
```

同一caseのatomicity/role両verdictが3回一致しない場合:

```text
repeatability failure
```

とする。

P2はAtomicity call / Role callそれぞれを毎repeat実行する。

---

## 8. Metrics

runner:

```text
benchmark/tools/n04g23a_atomicity_role_benchmark.py
```

profile comparison:

```text
benchmark/tools/n04g23a_compare_profiles.py
```

最低記録:

```text
critical atomicity false-pass count
critical role false-pass count
required valid atomicity false-reject count
required valid role false-reject count
INDETERMINATE rate
atomicity confusion matrix
role confusion matrix
same-input repeatability
exact-match failures
prompt-profile agreement
```

### Critical false-pass

```text
gold NON_ATOMIC -> observed ATOMIC
gold ROLE_VIOLATION -> observed ROLE_VALID
```

のうち`critical_for_safety=true`。

### Valid false-reject

```text
gold ATOMIC -> NON_ATOMIC / INDETERMINATE
gold ROLE_VALID -> ROLE_VIOLATION / INDETERMINATE
```

required caseで測る。

---

## 9. Candidate viability Gate

各P1/P1P/P2について:

```text
Safety Gate:
  critical false-pass = 0

Required-valid Gate:
  required gold-valid false-reject = 0

Repeatability Gate:
  required cases 3/3 identical
```

全て満たした場合のみ`candidate_viable=true`。

P0はhistorical baselineなのでviabilityを採用条件に使わないが、同metricを記録する。

### Prompt paraphrase stability

P1 vs P1Pについて:

- required high-confidence casesはatomicity/role両方100%一致を目標Gateとする。
- all-case agreementも別途記録する。

P1がGold PASSでもP1Pでrequired verdictが変わる場合、joint promptはprompt-sensitiveとして扱う。

---

## 10. Decision tree

```text
P0 exact historical replay
  ↓
G-22 over-rejectを再現できるか確認
  ↓
P1 clarified joint
  ├─ safety + required-valid + repeatability PASS
  │    ↓
  │  P1P paraphrase required-case stability確認
  │    ├─ stable -> Phi-4 joint prompt remediation is viable
  │    └─ unstable -> prompt sensitivity remains; P2を優先評価
  │
  └─ FAIL -> P2評価

P2 split
  ├─ safety + required-valid + repeatability PASS
  │    -> V2をAtomicity / Role separate callsへ再設計
  └─ FAIL
       -> Phi-4 capability insufficient for required Gold
       -> alternative judge candidate evaluationを新blockerとして追加
```

P1が成功してもG-23で採用済みの2-stage generation architecture自体は撤回しない。

G-23Aは**v4内のV2 Gate実装方式**を決める診断である。

---

## 11. Required result artifacts

Tracked:

```text
benchmark/n04g23a-atomicity-role-gold-v1.json
benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json
benchmark/results/n04g23a-phi4-exact-joint-reference-workstation.json
benchmark/results/n04g23a-phi4-clarified-joint-reference-workstation.json
benchmark/results/n04g23a-phi4-clarified-paraphrase-reference-workstation.json
benchmark/results/n04g23a-phi4-split-reference-workstation.json
benchmark/results/n04g23a-profile-comparison-reference-workstation.json
docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md
```

Local raw evidence:

```text
.local/n04-v4/g23a/<run_id>/
```

Raw local logs/request responsesは原則commitしない。

---

## 12. Engineering Gate

Result finalization前に:

```text
python -m pytest -q tests/test_n04g23a_atomicity_role_benchmark_contract.py
python -m pytest -q
python -m ruff check .
git diff --check
```

すべてPASS必須。

---

## 13. Completion rule

G-23A Completeには:

- exact G-22 units included
- Gold review frozen before execution
- P0 exact profile provenance verified
- P0/P1/P1P/P2 all executed or validly BLOCKED with concrete evidence
- 3-repeat metrics captured
- decision tree applied without post-hoc Gate changes
- engineering Gate PASS
- evaluation doc completed

が必要。

G-23A結果だけでN-04/N-05状態は変更しない。
