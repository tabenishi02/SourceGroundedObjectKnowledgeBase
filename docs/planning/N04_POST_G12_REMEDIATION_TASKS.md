# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-19

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Formal v2 run: `20261018T213810+0900`
- Branch of record: `main`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- G-18 freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- G-19 implementation: `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
- G-20 verification: `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
- G-20R remediation: `docs/evaluation/N04G20R_RUFF_BASELINE_REMEDIATION_AND_GATE_RERUN.md`
- G-21 decision: `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`
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
8. Reference Workstation local proof前にexternal verifier profileをfinal freeze扱いしない。
9. G-12で正常だったcanonical / MCP / Retrieval / Context Builderを新evidenceなしに変更しない。
10. pre-existing engineering debtやtooling制約を理由にGate条件をsilentに変更しない。

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
| N-04G-19 | P0 | **Complete (2026-10-19, implementation)** | Frozen v3 implementation + verifier adapter boundary |
| N-04G-20 | P0 | **Complete (verification) / historical Gate FAIL** | Adversarial / replay / verifier benchmark / regression |
| N-04G-20R | P0 | **Complete / PASS (2026-10-19)** | Repository-wide Ruff remediation + engineering Gate rerun |
| N-04G-21 | P0 | **Prepared / BLOCKED before final Freeze (2026-10-19)** | v3 acceptance spec / Reference Workstation harness freeze |
| N-04G-22 | P0 | **Blocked by G-21** | Formal v3 re-acceptance |

N-04 CompleteはN-04G-22で全Gate PASS後のみ可能とする。

---

## 3. Frozen v3 baseline retained from G-18

```text
sgokb.context-builder.v1
sgokb.grounded-context.v1
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

Output roles:

```text
main           -> source_fact(text, support_refs[])
interpretation -> interpretation(text, premise_unit_ids[])
creative       -> creative_addition(text)
context_limit  -> context_limit(limit_code)
```

G-21はこの意味設計を変更しない。

---

## 4. G-20 / G-20R evidence entering G-21

G-20 verifier candidate screening:

```text
MiniCheck source revision:
  b58b9fa69acbd1015ec970fa65dd752413a053d2
model: lytang/MiniCheck-RoBERTa-Large
threshold candidate: 0.50
required negative/replay false-positive: 0
required positive supported: 2 / 2
negative specificity: 1.0
positive recall: 0.8
```

G-20R final engineering Gate:

```text
run_id: 39224975505
focused/replay: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
repository-wide Ruff: PASS
git diff --check: PASS
```

G-20の元のrepo-wide Ruff FAILはhistorical evidenceとして保持し、G-20Rがblocker解消を証明する。

---

## 5. N-04G-21 freeze candidate prepared

Authoritative status record:

```text
docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md
```

Tracked candidate artifacts:

```text
benchmark/n04-ai-use-cases-v3.json
benchmark/n04-v3-formal-harness-v1.json
benchmark/n04-v3-material-profiles-v1.json
benchmark/n04-v3-source-fact-verifier-profile-v1.json
tests/test_n04g21_harness_freeze_candidate.py
```

All candidate JSON status:

```text
freeze_candidate_pending_reference_workstation_verification
```

### Generator candidate

```text
LM Studio 0.4.25.0
sgokb-n04-mistral32
Mistral Small 3.2 24B Instruct Q4_K_M
context 8192 / GPU offload max / parallel 1 / seed 20261018
```

### Bounded semantic model candidate

```text
sgokb-n04-phi4
Phi-4 Q4_K_S
context 8192 / GPU offload max / parallel 1
temperature 0.0 / max_tokens 64 / seed 20261018
```

Used through separate bounded adapters for:

```text
atomicity / role
independent source-fact judge
interpretation derivation judge
```

### Specialized source-fact verifier candidate

```text
MiniCheck source revision:
  b58b9fa69acbd1015ec970fa65dd752413a053d2
model repo:
  lytang/MiniCheck-RoBERTa-Large
model revision candidate:
  74c8919647e61ed0f71bc177d94f10930f090068
threshold: 0.50 (>=)
formal network policy: offline / local-files-only
```

MiniCheck positive aloneはgrounding authorityではない。Phi-4 independent judge `ENTAILED`とのagreementを必須とする。

### Provider schema candidate

```text
src/sgokb/grounding/output.py::GENERATION_OUTPUT_SCHEMA
sha256:
  1fc7674ee9c42ca60feecd1796ec186f970f88e5600f3839d25d851735a1b990
```

---

## 6. Formal material profiles / stable Objects

### Case 1

```text
Saber
326a97cf-47aa-4760-a7f1-07bfe639fcf0
minimum supported source facts = 2
```

### Case 2

```text
Fate/stay night
d5824d33-7008-4121-9cfe-1f95a19667fd

expected fixed-dataset rank-1 Work: BLEACH
57db855c-574a-4b38-b474-421c165894f1

minimum source fact per Work = 1
minimum interpretation = 1
cross-source interpretation = required
```

Actual Similarity rank-1を使う。expected IDと異なる場合、BLEACHをsubstituteせずCase FAILにする。

### Case 3

```text
Tsundere
8c83f986-f491-41a8-8645-9f71dd5874b9

Hero's Journey
fee32007-0f92-449a-ba21-4ec2f78d1cd4

minimum source fact per Concept = 1
minimum creative addition = 1
```

---

## 7. Why G-21 is not Complete yet

2026-10-19、Reference Workstation `FNB1Main`はDesktop Commander上でOnlineだった。

しかしRemote Desktop Commanderは月次利用上限に達しており、command executionが拒否された。tool側はretry/reconnectしないよう明示したため、本作業では実機commandを継続しない。

その結果、G-21 final freezeに必要な次の3項目が未実測である。

1. Reference Workstation MiniCheck exact local source/model revision。
2. threshold0.50でのG-20 verifier corpus offline replay。
3. MiniCheck/Torch/Transformers/Hugging Face/NLTK等exact installed package version lock。

GitHub Actions screeningはcandidate evidenceでありlocal-only formal proofではないため、これを理由にG-21をCompleteへ変更しない。

---

## 8. Remaining G-21 Gate

Reference Workstation command executionが可能になった時点で、候補を変更せず以下を実行する。

```text
A. exact runtime/package inventory
B. MiniCheck source revision verification
C. local HF cache model revision verification
D. network-disabled/offline G-20 verifier corpus replay
E. threshold 0.50:
     required negative false-positive = 0
     required positive supported = 2/2
F. generator/Phi-4 output-v2 neutral structured-output smoke
G. MCP/Harrier/Qdrant/integrity preflight
H. focused/replay + full pytest + repo-wide Ruff + diff check
```

全PASS時のみcandidate statusを`frozen`へ変更し、G-21をComplete、G-22をunblockする。

Runtime/model/revision/thresholdのsubstitutionが必要ならG-21をreopenして再評価する。

---

## 9. N-04G-22 — Formal v3 Re-Acceptance

**Status: Blocked by G-21**

Same three representative use cases are retained。

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
+ repository-wide Ruff PASS
+ full pytest 0 failed
```

---

## 10. Dependency

```text
G-12 valid formal FAIL
  ↓
G-13..G-18 design/remediation Complete
  ↓
G-19 Implementation Complete
  ↓
G-20 Verification Complete / historical Gate FAIL
  ↓
G-20R Engineering blocker remediation Complete / PASS
  ↓
G-21 freeze candidate Prepared
  ↓
Reference Workstation local verifier/runtime verification
  ↓ PASS only
G-21 Complete / Frozen
  ↓
G-22 Formal v3 Re-Acceptance
  ↓
N-04 Complete only if PASS
  ↓
N-05
```

---

## 11. Protected boundaries

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
- G-20/G-20R historical evidence

Do not relax G-18, verifier false-positive Gate, Reference Workstation proof requirement, or engineering Gates merely to obtain PASS.
