# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-19

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Formal run: `20261018T213810+0900`
- Branch of record: `main`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- G-18 freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- G-19 implementation: `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
- G-20 verification: `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
- Current parent state: **N-04 Failed / N-05 blocked**

---

## 1. Remediation principles

1. G-12 failed evidenceを削除・上書きしない。
2. N-04をG-22成功前にCompleteへ変更しない。
3. N-05をblockedのまま維持する。
4. rubric / contract / engineering Gateを実行後に緩めてPASSさせない。
5. generator / verifierをuntrusted or fallible componentとして扱う。
6. deterministicに防げるfailureをLLM judgeへ委ねない。
7. claim / premise / material / terminal / render各境界でfail-closedにする。
8. exact external verifier profileはbenchmark合格前にproduction authority化しない。
9. G-12で正常だったcanonical / MCP / Retrieval / Context Builderを新evidenceなしに変更しない。
10. pre-existing engineering debtがGateを妨げる場合も、Gate条件をsilentに変更せずremediation taskを追加する。

---

## 2. Task status

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-13 | P0 | **Complete (2026-10-18)** | Root-cause / desk review / external research |
| N-04G-14 | P0 | **Complete (2026-10-19)** | Atomic claim / semantic-role boundary redesign |
| N-04G-15 | P0 | **Complete (2026-10-19)** | Output schema / presentation / renderer hardening |
| N-04G-16 | P0 | **Complete (2026-10-19, design)** | Semantic validation architecture redesign |
| N-04G-17 | P0 | **Complete (2026-10-19, design)** | Material sufficiency / terminal / render gate redesign |
| N-04G-18 | P0 | **Complete (2026-10-19, Design Frozen)** | Post-G12 v3 Design Freeze |
| N-04G-19 | P0 | **Complete (2026-10-19, implementation)** | Frozen v3 design implementation + verifier adapter boundary |
| N-04G-20 | P0 | **Complete (verification) / Gate FAIL (2026-10-19)** | Adversarial / replay / verifier benchmark / regression |
| N-04G-20R | P0 | **Pending / NEXT** | Repository-wide Ruff baseline remediation + G-20 engineering Gate rerun |
| N-04G-21 | P0 | **Blocked** | v3 acceptance spec / Reference Workstation harness freeze |
| N-04G-22 | P0 | Pending | Formal v3 re-acceptance |

N-04 CompleteはN-04G-22で全Gate PASS後のみ可能とする。

---

## 3. G-18 Frozen v3 baseline

正本:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Frozen contracts:

```text
sgokb.context-builder.v1              unchanged
sgokb.grounded-context.v1             unchanged
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

Frozen output shape:

```text
main           -> source_fact(text, support_refs[])
interpretation -> interpretation(text, premise_unit_ids[])
creative       -> creative_addition(text)
context_limit  -> context_limit(limit_code)
```

Candidate identity:

```text
context_fingerprint
output_contract_version
attempt
output_digest
```

---

## 4. G-19 implementation

**Status: Complete**

正本:

```text
docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md
```

Implemented:

- output v2 schema/parser + digest/binding。
- Atomicity/Role adapter boundary。
- V4F specialized verifier + independent source-fact judge boundary。
- V4I premise graph / derivation judge boundary。
- `MaterialRequirementGate`。
- failure policy v2。
- terminal-bound deterministic renderer。
- evidence/Application facade wiring。

G-19 focused smoke:

```text
22 passed
```

Exact verifier runtime/profileはG-20/G-21へ残した。

---

## 5. G-20 verification result

**Status: Complete (verification executed) / Overall Gate FAIL**

正本:

```text
docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md
```

Final GitHub Actions run:

```text
run_id: 39198589270
focused/replay: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
G-20 changed-scope Ruff: PASS
git diff --check: PASS
repository-wide Ruff: FAIL — 180 errors
MiniCheck RoBERTa-large screening: PASS necessary candidate Gate
```

### G-12 replay / adversarial

Machine regression化した最低範囲:

1. supported + unsupported clause in one unit -> no PASS。
2. material fact disguised as style -> schema reject。
3. creative block source Concept claim -> no role PASS。
4. unsupported interpretation premise -> no derived_supported。
5. one-side-only comparison -> no Material PASS。
6. arbitrary model label -> contract reject / no render。
7. materially incomplete grounded output -> no ACCEPTED。
8. unjustified context-limit -> no INSUFFICIENT_CONTEXT。
9. justified exclusive context-limit -> safe render only。
10. REJECTED / SYSTEM_FAILURE -> renderer refuses。
11. attempt/output digest mismatch -> renderer refuses。
12. verifier disagreement -> no Grounding PASS。
13. G-12 Case 1/2/3 failure shapes -> no false acceptance path。
14. provider/application contract mismatch preflight。

### G-20 implementation correction

G-19 parserに残っていたprovider JSON Schema外のcross-item uniqueness ruleを発見した。

```text
duplicate_block_id
duplicate_unit_id
duplicate_presentation_role
```

G-20でこれらをparser-local hidden ruleからexplicit Grounding Validation V0へ移動した。

```text
provider JSON Schema == application parse surface
        ↓
V0 SGOKB identity invariant
```

意味制約は削除せず、G-12 Case 3型のprovider/parser mismatchを防ぐ責務配置へ修正した。

---

## 6. G-20 verifier candidate screening

Corpus:

```text
benchmark/n04g20-source-fact-verifier-v1.json
```

Runner:

```text
benchmark/tools/n04g20_minicheck_benchmark.py
```

Persistent screening evidence:

```text
benchmark/results/n04g20-minicheck-roberta-large-github-actions.json
```

GitHub Actions diagnostic candidate:

```text
MiniCheck repo revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model: lytang/MiniCheck-RoBERTa-Large
threshold candidate: 0.50
required negative/replay false-positive: 0
required positive supported: 2 / 2
negative specificity: 1.0
positive recall: 0.8
```

必要条件:

```text
required negative/replay false-positive = 0
```

を満たしたため、MiniCheck RoBERTa-largeは**G-21 local-runtime evaluationへ持ち込めるcandidate**とする。

ただしproduction adoption / exact checkpoint / threshold profile / independent judge / local-only runtimeは未freeze。

---

## 7. G-20 Gate failure reason

Task masterはG-20 engineering Gateとして:

```text
full pytest
Ruff
git diff --check
```

を要求している。

Final runではrepo-wide:

```text
python -m ruff check .
```

が`180 errors`を検出した。

G-20 changed Python filesだけのRuffはPASSしたが、この事実を理由にrequired `Ruff`をchanged-scopeへ読み替えない。

代表的なlint debt:

```text
extensions/web-page-capture/*
src/sgokb/exchange/*
src/sgokb/grounding/render.py
tests/test_n04_grounded_generation.py
その他既存test
```

したがってG-20 Overall GateはFAILであり、G-21はblockedとする。

---

## 8. N-04G-20R [P0] — Repository-wide Ruff baseline remediation + Gate rerun

**Status: Pending / NEXT**

Goal:

G-20で発見されたrepository-wide lint baseline failureを、semantic behaviorを変更せず解消し、G-20 engineering Gateを再実行する。

Required work:

1. current mainのRuff 180 errorsを分類する。
2. import order / unused import / line-length / formatting等をstyle-only修正する。
3. 振る舞い変更が必要になるlintはstyle remediationと混在させず個別判断する。
4. `python -m ruff check .` -> PASS。
5. `tests/test_n04_grounded_generation.py + tests/test_n04g20_adversarial_regression.py` -> PASS。
6. full pytest -> 0 failed。
7. `git diff --check` -> PASS。
8. G-20 provider/application V0 fixを維持する。
9. verifier pathに意味変更がなければG-20 MiniCheck screening evidenceは再利用可能。意味変更があればbenchmarkを再runする。

G-20R PASS後にのみG-21をunblockする。

---

## 9. Reference Workstation runtime boundary

G-20実行時、Remote Desktop Commanderは月次利用上限に達していたためReference Workstation上のlocal verifier screeningは実行できなかった。

GitHub Actions verifier resultはcandidate screening evidenceであり、local-only formal runtime proofではない。

G-21 freeze前にexact local runtime/profileを確定する必要がある。

---

## 10. N-04G-21 — v3 Acceptance / Harness Freeze

**Status: Blocked by G-20R**

Unblock後にfreeze:

- generator model/runtime/settings
- source-fact verifier exact checkpoint/revision
- verifier threshold profile/hash
- independent source-fact judge exact model/settings
- interpretation derivation judge exact model/settings
- atomicity/role classifier runtime if model-based
- material requirement profiles + stable Object IDs
- provider structured-output mechanism/schema hash
- retry/terminal policy
- evidence tree
- G-20/G-20R engineering result
- formal rubric

G-20 empirical verifier Gate未達profileはfreezeしない。

---

## 11. N-04G-22 — Formal v3 Re-Acceptance

**Status: Pending**

Same three representative use cases are retained.

N-04 Complete requires:

```text
3 / 3 formal Case PASS
+ no unsupported rendered material claim
+ no role escape
+ material requirement PASS
+ terminal/render authorization PASS
+ canonical invariance
+ integrity PASS
+ focused/adversarial/verifier regression PASS
+ full pytest 0 failed
```

---

## 12. Dependency

```text
G-12 valid formal FAIL
  ↓
G-13..G-18 design/remediation Complete
  ↓
G-19 Implementation Complete
  ↓
G-20 Verification Complete / Gate FAIL (repo-wide Ruff)
  ↓
G-20R Repository-wide Ruff remediation + Gate rerun  ← NEXT
  ↓ PASS only
G-21 v3 Acceptance + Harness Freeze
  ↓
G-22 Formal v3 Re-Acceptance
  ↓
N-04 Complete only if PASS
  ↓
N-05
```

---

## 13. Protected boundaries

Without new failure evidence, do not change:

- canonical 52-table model
- Object ID / Version identity
- Source / Evidence / Provenance
- MCP read-only boundary
- Context Builder budget / purpose selection
- Similarity ranking algorithm
- N-06 retrieval-quality metrics
- G-12 historical failed evidence
- G-18 Frozen grounded-generation semantics

Do not relax G-18 or G-20 engineering Gate merely to obtain PASS.
