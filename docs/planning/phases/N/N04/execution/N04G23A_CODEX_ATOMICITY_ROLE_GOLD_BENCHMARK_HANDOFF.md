# N-04G-23A Codex Atomicity / Role Gold Benchmark Handoff

更新日: 2026-10-20

- Branch: `phase-n/n04g23a-atomicity-role-gold-benchmark`
- Base main: `1ff6483c8d9d5760138ecd3dbb45989182d2c986`
- Task: `N-04G-23A Atomicity / Role Gold Benchmark`
- Execution: **Complete / all profiles executed; engineering PASS**
- Run: `20261020T151126+0900`; result: `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`. Original procedure below is retained.
- Reference Workstation: Reference Workstation / Windows 11 / RTX 4090
- Historical G-22 run: `20261020T030904+0900`
- Production code change: **禁止**
- v3 Frozen artifact change: **禁止**

## Read first

1. `docs/planning/phases/N/N04/post-g12/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK_PROTOCOL.md`
2. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
3. `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md`
4. `benchmark/n04g23a-atomicity-role-gold-seed-v1.json`
5. `benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json`
6. `benchmark/n04g23a-atomicity-role-paraphrase-profile-v1.json`
7. `benchmark/tools/n04g23a_atomicity_role_benchmark.py`
8. `benchmark/tools/n04g23a_compare_profiles.py`

---

## 1. Sync and initial engineering check

このbranchをremoteへfast-forward同期し、working treeをcleanにする。

最初に:

```text
python -m pytest -q tests/test_n04g23a_atomicity_role_benchmark_contract.py
python -m ruff check benchmark/tools/n04g23a_atomicity_role_benchmark.py benchmark/tools/n04g23a_compare_profiles.py tests/test_n04g23a_atomicity_role_benchmark_contract.py
git diff --check
```

をPASSさせる。

ここで発見したrunner/testの純粋なengineering defectはformal input freeze前なら修正可能。
Gold policyやGateを緩めてはならない。

---

## 2. Import exact G-22 units

Authority:

```text
.local/n04-v3/runs/20261020T030904+0900/
```

Case 1/2/3、Attempt 1/2の`parsed-output.json`等から**全material unitをexact textで抽出**する。

summary文から再構成しない。

最低metadata:

```text
origin = g22_exact
source_g22_run_id = 20261020T030904+0900
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

seed 20 casesは原則そのまま保持する。

Final corpus:

```text
benchmark/n04g23a-atomicity-role-gold-v1.json
```

へ統合する。

### Gold labeling

Historical Phi-4 verdictをGoldとしてコピーしない。

Gold authorityはG-14のみ。

重要:

```text
support / truth != role validity
```

例:

```text
unsupported source-world fact
  -> Atomicityが1 propositionならATOMICになり得る
  -> source_factとしてcontent typeが正しければROLE_VALIDになり得る
  -> support判定はG-23A対象外
```

各G-22 caseへ:

```text
gold.atomicity
gold.role_boundary
gold_confidence = high / medium / low
rationale
```

を付ける。

Gold reviewer自身が安全に確定できなければ`INDETERMINATE`を許容するが:

```text
required = false
```

とする。

`required=true`はhigh-confidence Goldだけ。

G-22 Case 2の「faithful K restatementなのにrole-INDETERMINATE」だったunit群は特に慎重にreviewする。observed Phi-4 verdictに引っ張られず、content-firstでGold化する。

Final corpusに:

```text
status = frozen_for_execution
source_g22_run_id = 20261020T030904+0900
```

を設定する。

---

## 3. Import exact historical G-22 joint prompt

`g22-exact-joint`を近似で作ってはいけない。

保存された:

- actual Phi-4 request payload
- local G-22 helper source
- request/response evidence

を調査する。

`benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json`の:

```text
g22-exact-joint
```

へexact:

```text
system_prompt
user_prompt_template
response_format
```

を設定し:

```text
status = ready
```

とする。

### Exactness proof

parameterized templateをG-22 historical unitへrenderし、保存されたhistorical requestのmessagesと比較する。

全sampleで一致必須。

少なくとも:

- Case 1 Attempt 1
- Case 2 Attempt 1
- Case 2 Attempt 2
- Case 3 Attempt 1

から複数unitを確認する。

できれば全historical Atomicity/Role callで比較する。

保存するmetadata:

```text
exact_profile_provenance
historical_request_paths
historical_helper_path/hash
verified_render_count
mismatch_count = 0
```

byte-equivalentなparameterizationを証明できない場合はP0を`BLOCKED_exact_profile`とし、推測profileで代替しない。

P1/P1P/P2 promptは結果を見る前に既にtrackedされているため、意味改善目的で追加編集しない。

---

## 4. Freeze benchmark inputs before running Phi-4

ここが重要。

Phi-4実行前に:

- final Gold corpus
- exact P0 profile
- P1/P1P/P2
- runner
- comparator
- contract tests

を確定する。

以下をPASS:

```text
python -m pytest -q tests/test_n04g23a_atomicity_role_benchmark_contract.py
python -m ruff check benchmark/tools/n04g23a_atomicity_role_benchmark.py benchmark/tools/n04g23a_compare_profiles.py tests/test_n04g23a_atomicity_role_benchmark_contract.py
git diff --check
```

その後、**benchmark結果を見る前にcommit + push**する。

このcommit SHAを:

```text
benchmark_input_head
```

として記録する。

Gold corpus / prompt profiles / runner SHA-256も記録する。

以後全profile完了までtracked inputを変更禁止。

---

## 5. Reference Workstation runtime

G-22と同一Phi-4条件を使用する。

```text
LM Studio       0.4.25.0
alias           sgokb-n04-phi4
model           Phi-4 Q4_K_S
context         8192
GPU             max
parallel        1
temperature     0
max_tokens      64
seed            20261018
stream          false
```

モデルidentity/hashがG-22 authorityと一致することを確認する。

Web / cloud inference / external retrievalは禁止。

G-23AではMistral / MiniCheck / MCP / Qdrantは不要。
Atomicity / Roleだけを孤立評価する。

Raw evidence root:

```text
.local/n04-v4/g23a/<run_id>/
```

run_id:

```text
YYYYMMDDTHHMMSS+0900
```

---

## 6. Run four conditions

すべてfinal corpus、repeats=3。

### P0 historical exact joint

```text
python benchmark/tools/n04g23a_atomicity_role_benchmark.py \
  --corpus benchmark/n04g23a-atomicity-role-gold-v1.json \
  --profiles benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json \
  --profile-id g22-exact-joint \
  --repeats 3 \
  --output .local/n04-v4/g23a/<run_id>/exact-joint.json
```

### P1 clarified joint

同様に:

```text
--profile-id clarified-joint-v1
```

output:

```text
clarified-joint.json
```

### P1P clarified paraphrase

profiles:

```text
benchmark/n04g23a-atomicity-role-paraphrase-profile-v1.json
```

profile:

```text
clarified-joint-v1-paraphrase-a
```

output:

```text
clarified-paraphrase.json
```

### P2 split

```text
--profile-id split-v1
```

output:

```text
split.json
```

一つのprofileだけ失敗した場合、他profileへsetting/profileをfallbackしない。
原因を保存する。

---

## 7. Historical G-22 reproduction check

P0について、final corpus中の`origin=g22_exact` caseに対し:

- historical G-22 atomicity verdict
- historical G-22 role verdict
- G-23A exact replay verdict

を比較する。

historical observed verdictはGoldとは別field/evidenceとして扱う。

出力:

```text
.local/n04-v4/g23a/<run_id>/g22-exact-reproduction.json
```

最低報告:

```text
historical call count
exact replay comparison count
atomicity identical count
role identical count
joint identical count
mismatch case/unit IDs
```

P0が再現しない場合、prompt差分かruntime nondeterminismを区別し、`exact baseline reproduction`をPASS扱いしない。

---

## 8. Profile comparison

```text
python benchmark/tools/n04g23a_compare_profiles.py \
  --result exact=.local/n04-v4/g23a/<run_id>/exact-joint.json \
  --result clarified=.local/n04-v4/g23a/<run_id>/clarified-joint.json \
  --result paraphrase=.local/n04-v4/g23a/<run_id>/clarified-paraphrase.json \
  --result split=.local/n04-v4/g23a/<run_id>/split.json \
  --output .local/n04-v4/g23a/<run_id>/profile-comparison.json
```

P1 vs P1Pではrequired high-confidence Goldの差分も追加確認する。

Required caseに1件でもverdict差があればprompt-paraphrase stability GateはFAIL。

---

## 9. Decision rule

結果を見てruleを変更しない。

### Phi-4 joint prompt remediation viable

P1:

```text
critical false-pass = 0
required-valid false-reject = 0
required repeatability PASS
```

かつP1/P1P required case verdict 100%一致。

この場合:

```text
G-23A diagnosis:
  model replacement not justified
  clarified joint V2 is viable
```

### Split-call required

P1がGate FAILまたはprompt-paraphrase unstableだがP2が:

```text
critical false-pass = 0
required-valid false-reject = 0
required repeatability PASS
```

なら:

```text
G-23A diagnosis:
  joint task coupling/prompt sensitivity remains
  v4 V2 should split Atomicity and Role calls
```

### Phi-4 inadequate

P2もGate FAILなら:

```text
G-23A diagnosis:
  Phi-4 is not sufficient for required Gold under tested formulation
```

Gateを緩めず、`G-23A-R Judge Candidate Evaluation`等の追加blockerを提案する。
別modelを勝手に投入しない。

---

## 10. After execution

tracked resultを以下へコピーする。Raw HTTP/logはcommit不要。

```text
benchmark/results/n04g23a-phi4-exact-joint-reference-workstation.json
benchmark/results/n04g23a-phi4-clarified-joint-reference-workstation.json
benchmark/results/n04g23a-phi4-clarified-paraphrase-reference-workstation.json
benchmark/results/n04g23a-phi4-split-reference-workstation.json
benchmark/results/n04g23a-profile-comparison-reference-workstation.json
```

必要ならhistorical reproduction summaryもtracked resultとして追加してよい。

作成:

```text
docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md
```

内容:

- run_id
- benchmark_input_head
- exact runtime identity
- final corpus count / origin breakdown
- Gold label distribution
- exact-profile provenance proof
- P0/P1/P1P/P2 metrics
- G-22 exact replay consistency
- P1/P1P stability
- profile comparison
- selected diagnosis
- G-23Bへ渡すV2 policy
- N-04/N-05 unchanged

---

## 11. Final engineering Gate

tracked result/doc更新後:

```text
python -m pytest -q tests/test_n04g23a_atomicity_role_benchmark_contract.py
python -m pytest -q
python -m ruff check .
git diff --check
```

すべてPASS必須。

G-23Aのbenchmark結果を理由に既存テストを弱めない。

---

## 12. Status update

有効な結果が出た場合:

```text
N-04G-23A = Complete
```

P1またはP2がviableなら:

```text
N-04G-23B = NEXT
```

P2まで不十分なら、Judge candidate追加評価をblockerとしてtask文書へ追加し、G-23Bの状態を明確に記録する。

常に:

```text
N-04 = Failed / not Complete
N-05 = blocked
```

を維持。

---

## 13. Git

結果確定後:

- commit
- push
- PRをReady for review

まで実施してよい。

**mainへmergeしない。**

最後に以下を報告する。

```text
run_id
benchmark_input_head
Gold corpus count / G-22 exact count
exact prompt provenance / mismatch count
Phi-4 identity
P0 metrics
G-22 reproduction match rate
P1 metrics
P1P metrics
P1/P1P required stability
P2 metrics
selected diagnosis / V2 recommendation
contract tests
full pytest
Ruff
diff check
commit SHA
PR status
N-04G-23A state
N-04 / N-05 state
```
