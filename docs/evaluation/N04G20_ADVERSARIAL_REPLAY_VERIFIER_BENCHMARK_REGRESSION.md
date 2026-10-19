# N-04G-20 Adversarial / Replay / Verifier Benchmark / Regression

更新日: 2026-10-19

- Status: **Complete (verification executed) / Overall Gate FAIL**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Design Freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Implementation: `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
- Branch: `phase-n/n04g20-adversarial-verifier-regression`
- GitHub Actions final run: `39198589270`
- Final tested branch SHA: `13248f1f48b0faa232ebaa7c1a76ef052da97d9b`
- Next state: **G-21 blocked until repository-wide Ruff Gate is restored and G-20 engineering Gate is rerun**

---

## 1. Decision

N-04G-20で要求されたreplay / adversarial / verifier screening / regressionを実行した。

結果は以下の通り。

```text
G-12 replay / adversarial regression       PASS
provider/application schema preflight      PASS after G-20 fix
MiniCheck candidate screening              PASS necessary verifier Gate
focused N-04 tests                          PASS: 37
full pytest                                 PASS: 388 passed / 5 skipped
G-20 changed-scope Ruff                     PASS
git diff --check                            PASS
repository-wide Ruff                        FAIL: 180 existing errors
```

したがって、**G-20 verificationは完了したがOverall GateはFAIL**とする。

G-20 Task masterで`Ruff`をrequired Gateとしているため、repository-wide Ruff failureを「今回の差分ではない」という理由だけでsilentに免除しない。

このため:

```text
N-04G-20 = Complete (verification executed) / Gate FAIL
N-04G-21 = blocked
N-04 = Failed / not Complete
N-05 = blocked
```

とする。

---

## 2. G-12 replay / adversarial coverage

新規:

```text
tests/test_n04g20_adversarial_regression.py
```

G-19 focused testと合わせたfinal CI結果:

```text
37 passed in 0.22s
```

最低限、次をmachine regressionとして確認した。

1. supported clause + unsupported clauseを1 unitへ混在 → `ATOMICITY_VIOLATION` / no PASS。
2. material claimを`stylistic_expression`へ逃がす → output v2 schema reject。
3. creative blockへsource Concept factを混在 → `ROLE_BOUNDARY_VIOLATION` / no PASS。
4. unsupported source_fact premise → interpretation derivation judgeへ進めない。
5. one-side-only comparison → Material PASS不可。
6. arbitrary model `label` → schema reject / render不可。
7. Grounding PASSでもformal roleplay minimumを満たさないoutput → ACCEPTED不可。
8. usable materialがあるのに`context_limit` → INSUFFICIENT_CONTEXT不可。
9. supplied Context自体がrequirementを満たせないexclusive context-limit → trusted safe renderのみ。
10. REJECTED / SYSTEM_FAILURE → renderer拒否。
11. attempt / output digest binding mismatch → renderer拒否。
12. specialized source-fact verifierとindependent judge disagreement → no Grounding PASS。
13. G-12 Case 3旧`label=null` failure path → v2 contractではlabel自体が存在しない。
14. provider/application schema preflight → shared schema surface + explicit V0 identity invariantへ整理。

G-12で観測されたfalse acceptance形状をv3 regressionで再びACCEPTEDへ通す経路は確認されなかった。

---

## 3. Provider / application schema preflight finding and fix

G-19 output parserには、providerへ渡すJSON Schemaでは表現されていないcross-item uniqueness ruleが残っていた。

```text
duplicate block_id
duplicate unit_id
duplicate presentation_role
```

これは:

```text
provider schema accepts
application parser rejects
```

というG-12 Case 3と同型のhidden contract mismatchを再発させ得る。

### G-20 fix

Frozen semantic invariantを削除せず、責務位置を変更した。

旧:

```text
provider JSON Schema
        ↓
application parser
  └─ hidden cross-item uniqueness rules
```

新:

```text
provider JSON Schema
        ↓
application parser using the same JSON Schema surface
        ↓
Grounding Validation V0
  ├─ duplicate_block_id
  ├─ duplicate_unit_id
  └─ duplicate_presentation_role
```

変更対象:

```text
src/sgokb/grounding/output.py
src/sgokb/grounding/validation.py
```

これによりprovider/application parserのstructural accept surfaceを一致させ、SGOKB固有identity invariantはexplicit validation failureとして保持した。

G-18のfail-closed semanticsは緩和していない。

---

## 4. Source-fact verifier benchmark corpus

追加:

```text
benchmark/n04g20-source-fact-verifier-v1.json
benchmark/tools/n04g20_minicheck_benchmark.py
```

Corpusは17 cases。

含むbucket:

- direct supported claim
- faithful paraphrase
- G-12 Case 1 unsupported claims
- G-12 Case 2 unsupported claims
- high lexical overlap + unsupported extra detail
- supported subject + wrong predicate
- negation flip
- temporal / causal embellishment
- concept overclaim
- threshold probes

必要条件:

```text
required negative/replay false-positive = 0
```

---

## 5. MiniCheck RoBERTa-large candidate screening

### Runtime

GitHub Actions diagnostic environment:

```text
workflow run: 39198589270
artifact: 12162723330
artifact digest: sha256:5188a5a40b7c0376e92f7f9c868295f0a84043b19255e3db3a5b34d1d9a705fb
OS: Ubuntu 24.04.5 LTS
Python: 3.10.22
MiniCheck repository revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model alias: roberta-large
model repo: lytang/MiniCheck-RoBERTa-Large
```

Persistent summary:

```text
benchmark/results/n04g20-minicheck-roberta-large-github-actions.json
```

### Result at threshold 0.50

```text
required negative/replay false-positive = 0
required positive supported = 2 / 2
negative specificity = 1.0
positive recall = 0.8
```

17-case scoreの中でG-12 replay / required adversarial negativesは全て0.50未満だった。

代表値:

```text
positive direct contract                 0.985060
positive faithful paraphrase             0.980430
G12 Holy Grail protector                 0.016363
G12 secret identity                      0.066307
G12 magi summon Heroes                   0.026212
G12 Hollows                              0.013668
G12 Soul Reaper balance                  0.014772
G12 extraordinary powers                 0.005672
high-overlap unsupported extra detail    0.068628
negation flip                            0.179140
causal/temporal embellishment            0.020104
```

Threshold sweep `0.50..0.90`はrequired negative false-positive 0 + required positive 2/2を維持した。`0.95`でもrequired Gateは満たすが、全positive recallは0.6へ低下した。

Benchmark runnerのdiagnostic candidateは`0.50`。

### Interpretation

MiniCheck RoBERTa-largeは**G-21へ持ち込むsource-fact verifier candidateとしてscreening PASS**とする。

ただし、これは次を意味しない。

- production verifierとしてfinal adoption済み。
- exact model checkpoint/revisionがfreeze済み。
- threshold `0.50`がformal profileとしてfreeze済み。
- independent source-fact LLM judgeがfreeze済み。
- Reference Workstation local-only runtimeで再現済み。

これらはG-21 freeze前にlocal runtime identity / profileを確定する必要がある。

---

## 6. Engineering regression result

Final GitHub Actions run `39198589270`:

### Focused / replay

```text
37 passed in 0.22s
```

### Full pytest

```text
388 passed, 5 skipped in 103.83s
```

`0 failed`。

### G-20 changed-scope Ruff

対象:

```text
benchmark/tools/n04g20_minicheck_benchmark.py
src/sgokb/grounding/output.py
src/sgokb/grounding/validation.py
tests/test_n04g20_adversarial_regression.py
```

結果:

```text
All checks passed!
```

### git diff --check

```text
PASS
```

---

## 7. Repository-wide Ruff blocker

Task masterはG-20に:

```text
Full pytest / Ruff / diff check required
```

を要求している。

Final runで`python -m ruff check .`も実行した結果:

```text
180 errors
```

を検出した。

代表的な既存対象:

```text
extensions/web-page-capture/native-host/host.py
extensions/web-page-capture/tests/unit/test_host.py
extensions/web-page-capture/tests/unit/test_windows_launcher.py
src/sgokb/exchange/instructions.py
src/sgokb/exchange/package_builder.py
src/sgokb/exchange/package_transfer.py
src/sgokb/exchange/result_receipt.py
src/sgokb/grounding/render.py
tests/test_n04_grounded_generation.py
tests/test_object_analysis_instructions.py
tests/test_result_receipt.py
```

G-20で変更したPython filesについてはchanged-scope Ruff PASSを確認している。

しかし、required Gateを「G-20差分のみRuff」に読み替えてOverall PASSとはしない。

したがってrepository-wide Ruff baselineを復旧し、同じfull Gateを再実行するremediationが必要である。

---

## 8. Reference Workstation boundary

Reference Workstationへ接続するRemote Desktop Commanderは、このG-20実行時点で月次利用上限に達していた。

そのため本チャットから:

- Windows 11 / RTX 4090上でのMiniCheck local screening
- Reference Workstation固有のfull regression

は実行できなかった。

GitHub Actions上のMiniCheck測定はcandidate screening evidenceとして有効だが、**local-only formal runtime proofではない**。

これはG-21でexact runtime/profileをfreezeする前に解消すべき運用上の前提である。

---

## 9. G-20 Gate assessment

| Gate | Result |
|---|---|
| G-12 replay | PASS |
| adversarial false-acceptance regression | PASS |
| provider/application schema preflight | PASS after G-20 fix |
| MiniCheck required negative/replay FP=0 | PASS |
| focused N-04 tests | PASS — 37 |
| full pytest | PASS — 388 passed / 5 skipped |
| G-20 changed-scope Ruff | PASS |
| git diff --check | PASS |
| repository-wide Ruff | **FAIL — 180 errors** |
| Reference Workstation local verifier screening | Not executed — connector quota unavailable |

Overall:

```text
N-04G-20 verification execution = Complete
N-04G-20 required engineering Gate = FAIL
G-21 eligibility = BLOCKED
```

---

## 10. Required remediation before G-21

次のP0 remediationを追加する。

```text
N-04G-20R [P0]
Repository-wide Ruff baseline remediation + G-20 engineering Gate rerun
```

Scope:

1. current mainのrepo-wide Ruff 180 errorsをsemantic changeなしで解消する。
2. `python -m ruff check .`をPASSさせる。
3. G-20 focused/replay suiteを再実行する。
4. full pytestを再実行する。
5. `git diff --check`を再実行する。
6. G-20で修正したprovider/application preflightを維持する。
7. MiniCheck benchmark evidenceは変更がverifier pathへ影響しない限り再利用可能だが、影響がある場合は再runする。

G-20R PASS前にG-21へ進めない。

---

## 11. Completion assessment

- [x] G-12 replay testを実装・実行。
- [x] adversarial false-acceptance testを実装・実行。
- [x] provider/application schema mismatchを発見・修正・regression化。
- [x] verifier benchmark corpusを作成。
- [x] MiniCheck candidate screeningを実行。
- [x] required negative/replay false-positive = 0を確認。
- [x] focused/replay 37 PASS。
- [x] full pytest 388 passed / 5 skipped / 0 failed。
- [x] G-20 changed-scope Ruff PASS。
- [x] git diff --check PASS。
- [ ] repository-wide Ruff PASS — **180 errorsで未達**。
- [ ] Reference Workstation local screening — connector quotaにより未実行。

**N-04G-20のverification作業はCompleteだが、Overall GateはFAIL。G-21へは進まない。**
