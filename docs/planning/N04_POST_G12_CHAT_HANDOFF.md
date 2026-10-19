# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Branch of record after integration: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- Current task: **N-04G-21 [P0] v3 Acceptance / Reference Workstation Harness Freeze**
- Current G-21 state: **Prepared / BLOCKED before final Freeze**
- G-22: **blocked by G-21**

---

## 1. Post-G12 chain state

```text
G-12 Formal v2 re-acceptance                   Complete / 0 of 3 PASS
G-13 Root-cause / research                     Complete
G-14 Atomic claim / role boundary              Complete
G-15 Output / presentation hardening           Complete
G-16 Semantic validation architecture          Complete
G-17 Material / terminal / render gate         Complete
G-18 Post-G12 v3 Design Freeze                 Complete / Frozen
G-19 Frozen v3 implementation                  Complete
G-20 Adversarial / verifier regression         Complete / historical Gate FAIL
G-20R Repository-wide Ruff remediation         Complete / PASS
G-21 v3 acceptance / harness freeze            Prepared / BLOCKED before Freeze
G-22 Formal v3 re-acceptance                   BLOCKED
```

N-04はG-22で3/3 formal Case PASSするまでCompleteにしない。

---

## 2. Historical G-12 evidence remains authoritative

```text
run_id: 20261018T213810+0900
Reference Workstation: Windows 11 / Python 3.10.6 / RTX 4090 24GB
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
Overall: 0 / 3 Case PASS
```

G-12 failure evidenceは削除・上書きしない。

G-12でproduction defectが確認されなかったcanonical / MCP / Retrieval / Context Builderは、具体的な新failure evidenceなしに変更しない。

---

## 3. G-18 Frozen architecture

Read first:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Frozen contracts:

```text
sgokb.context-builder.v1
sgokb.grounded-context.v1
sgokb.grounded-generation-output.v2
sgokb.grounding-validation.v2
sgokb.material-requirement.v1
sgokb.grounding-failure-policy.v2
```

Do not reintroduce:

```text
stylistic_expression
model free-form labels
free-form context-limit prose
interpretation direct K support
partial salvage
validation-only renderer authorization
```

---

## 4. G-20 / G-20R evidence

G-20 MiniCheck screening:

```text
MiniCheck source revision:
  b58b9fa69acbd1015ec970fa65dd752413a053d2
model: lytang/MiniCheck-RoBERTa-Large
threshold candidate: 0.50
required negative/replay false-positive: 0
required positive supported: 2/2
negative specificity: 1.0
positive recall: 0.8
```

Persistent evidence:

```text
benchmark/results/n04g20-minicheck-roberta-large-github-actions.json
```

G-20R final engineering Gate:

```text
run_id: 39224975505
focused/replay: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
repository-wide Ruff: PASS
git diff --check: PASS
```

Original G-20 repo-wide Ruff failure remains historical evidence; G-20R separately resolves that blocker。

---

## 5. G-21 freeze candidate artifacts

Authoritative status document:

```text
docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md
```

Candidate artifacts:

```text
benchmark/n04-ai-use-cases-v3.json
benchmark/n04-v3-formal-harness-v1.json
benchmark/n04-v3-material-profiles-v1.json
benchmark/n04-v3-source-fact-verifier-profile-v1.json
tests/test_n04g21_harness_freeze_candidate.py
```

All candidate JSONs intentionally remain:

```text
freeze_candidate_pending_reference_workstation_verification
```

They must not be changed to`frozen`until the local Gate passes。

---

## 6. Candidate runtime/profile

### Generator

```text
LM Studio 0.4.25.0
endpoint: http://127.0.0.1:1234/v1
identifier: sgokb-n04-mistral32
model: Mistral Small 3.2 24B Instruct Q4_K_M
context: 8192
GPU offload: max
parallel: 1
seed: 20261018
```

Case settings:

```text
roleplay:   temperature 0.2 / max_tokens 700
comparison: temperature 0.0 / max_tokens 900
creative:   temperature 0.2 / max_tokens 1100
```

### Bounded semantic model

```text
identifier: sgokb-n04-phi4
model: Phi-4 Q4_K_S
context: 8192
GPU offload: max
parallel: 1
temperature: 0.0
max_tokens: 64
seed: 20261018
```

Stage-specific adapters:

```text
AtomicityRoleValidatorAdapter
SourceFactJudgeAdapter
InterpretationDerivationJudgeAdapter
```

### Specialized source-fact verifier

```text
MiniCheck source revision:
  b58b9fa69acbd1015ec970fa65dd752413a053d2
model repo:
  lytang/MiniCheck-RoBERTa-Large
model revision candidate:
  74c8919647e61ed0f71bc177d94f10930f090068
threshold: >= 0.50
formal network policy: offline / local-files-only
```

Composition:

```text
deterministic support
  ↓ unresolved only
MiniCheck SUPPORTED_CANDIDATE
  ↓
Phi-4 ENTAILED
  ↓
supported
```

Any negative/disagreement/indeterminate/unavailable is no PASS。

---

## 7. Formal material profiles

### Case 1

```text
Saber: 326a97cf-47aa-4760-a7f1-07bfe639fcf0
minimum supported source facts: 2
```

### Case 2

```text
Fate/stay night: d5824d33-7008-4121-9cfe-1f95a19667fd
expected rank-1 Work in fixed dataset:
BLEACH: 57db855c-574a-4b38-b474-421c165894f1
minimum source fact per Work: 1
minimum interpretation: 1
cross-source interpretation: required
```

Actual Similarity resultを使い、expected IDと違う場合にBLEACHをhardcode/substituteしない。

### Case 3

```text
Tsundere: 8c83f986-f491-41a8-8645-9f71dd5874b9
Hero's Journey: fee32007-0f92-449a-ba21-4ec2f78d1cd4
minimum source fact per Concept: 1
minimum creative addition: 1
```

---

## 8. Provider / retry / terminal candidate

Provider:

```text
LM Studio OpenAI-compatible response_format json_schema
strict=true
schema source:
  src/sgokb/grounding/output.py::GENERATION_OUTPUT_SCHEMA
schema sha256:
  1fc7674ee9c42ca60feecd1796ec186f970f88e5600f3839d25d851735a1b990
```

Retry:

```text
attempt 1 + retry 1 = maximum 2
same Context/fingerprint/purpose/model/settings/schema/material profile
only structured repair feedback may be added
```

Terminal:

```text
ACCEPTED             -> NORMAL
INSUFFICIENT_CONTEXT -> CONTEXT_LIMIT_ONLY
REJECTED             -> NONE
SYSTEM_FAILURE       -> NONE
```

Formal Case PASS requires`ACCEPTED`。

`INSUFFICIENT_CONTEXT`is a safe machine terminal but formal Case FAIL。

---

## 9. Why G-21 remains blocked

2026-10-19にDesktop Commander device listではReference Workstation`FNB1Main`はOnlineだった。

しかしcommand executionを開始するとDesktop Commander monthly usage limitによりtool callが拒否され、tool側からretry/reconnectしないよう指示された。

そのため次のrequired local proofは未取得。

1. MiniCheck exact local source/model revision verification。
2. Reference Workstation上のG-20 verifier corpus offline replay at threshold0.50。
3. MiniCheck/Torch/Transformers/Hugging Face/NLTK exact installed package lock。

GitHub Actions screeningだけでこれらを代用してG-21をCompleteにしてはならない。

---

## 10. Exact next work

Reference Workstation command executionが利用可能になったら、candidate profileを変更せず実施する。

```text
A. exact runtime/package inventory
B. MiniCheck source revision verification
C. local HF cache model revision verification
D. offline G-20 verifier corpus replay
E. threshold0.50 required negative FP=0 / positive=2/2
F. Mistral/Phi-4 output-v2 structured-output neutral smoke
G. MCP/Harrier/Qdrant/system integrity preflight
H. focused/replay tests
I. full pytest
J. repository-wide Ruff
K. git diff --check
```

全PASS時:

```text
candidate JSON status -> frozen
unresolved_before_freeze -> empty
runtime lock -> harnessへ反映
G-21 -> Complete / Frozen
G-22 -> unblocked / NEXT
```

Candidateと異なるruntime/model/revision/thresholdが必要ならG-21をreopenする。

---

## 11. Read first next time

1. `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`
2. `benchmark/n04-v3-formal-harness-v1.json`
3. `benchmark/n04-v3-source-fact-verifier-profile-v1.json`
4. `benchmark/n04-v3-material-profiles-v1.json`
5. `benchmark/n04-ai-use-cases-v3.json`
6. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
7. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
8. `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
9. `docs/evaluation/N04G20R_RUFF_BASELINE_REMEDIATION_AND_GATE_RERUN.md`
10. `tests/test_n04g21_harness_freeze_candidate.py`

---

## 12. Protected boundaries

Do not change without concrete new failure evidence:

```text
Object identity
Version semantics
Canonical Statement / Attribute / Relation
Evidence / Provenance
Version immutability
Retrieval / Similarity contract
MCP read boundary
Context Builder selection / budget
N-03 dataset
G-12 failed evidence
G-18 Frozen grounded-generation semantics
G-20/G-20R historical evidence
```

Do not relax formal rubric, MiniCheck required false-positive Gate, Reference Workstation proof requirement, or engineering Gates merely to advance G-22。
