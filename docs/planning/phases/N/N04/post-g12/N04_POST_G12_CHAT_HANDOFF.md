# N-04 Post-G12 Chat Handoff

更新日: 2026-10-20

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Branch of record after integration: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-21: **Complete / Frozen (verified 2026-10-20)**
- Current task: **Review G-22 valid formal FAIL; remediation decision pending (N-05 blocked)**
- G-21V: **Complete / MiniCheck selected (2026-10-19)**
- G-21R: **Complete / PASS — new run 20261019T233552+0900**
- G-22: **Complete / valid formal FAIL — run 20261020T030904+0900 (0/3 PASS)**

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
G-21 v3 acceptance / harness freeze            Complete / Frozen
G-21V Verifier candidate evaluation            Complete / MiniCheck selected
G-21R Selected verifier runtime/local proof    Complete / PASS (new run)
G-22 Formal v3 re-acceptance                   Complete / valid formal FAIL (0/3 PASS)
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

Core failure:

```text
unsupported but plausible material claim
  ↓
general semantic judge false-positive
  ↓
unsafe acceptance
```

G-12 failed evidenceは削除・上書きしない。

---

## 3. G-18 Frozen architecture remains unchanged

Read first:

```text
docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md
```

Relevant source-fact path:

```text
V3 deterministic exact/structured support
  ↓ unresolved only
specialized source-fact verifier
  ↓ supported candidate only
independent bounded source-fact judge
  ↓ ENTAILED only
supported
```

Frozenなのはこのcompositionとfail-closed semanticsである。

**MiniCheckという特定製品そのものはFrozen semantic contractではない。**

G-19の`SourceFactVerifierAdapter`を通じてcandidate implementationを交換可能とする。

---

## 4. G-20 / G-20R baseline evidence

MiniCheck baseline:

```text
source revision:
  b58b9fa69acbd1015ec970fa65dd752413a053d2
model:
  lytang/MiniCheck-RoBERTa-Large
threshold:
  >= 0.50
required negative/replay false-positive: 0
required positive supported: 2/2
negative specificity: 1.0
positive recall: 0.8
```

Persistent result:

```text
benchmark/results/n04g20-minicheck-roberta-large-github-actions.json
```

G-20R:

```text
run_id: 39224975505
focused/replay: 37 passed
full pytest: 388 passed / 5 skipped / 0 failed
repository-wide Ruff: PASS
git diff --check: PASS
```

MiniCheckは有効baselineだが、G-21Vで2026年candidateと比較してからfinal verifierを選ぶ。

---

## 5. G-21 freeze candidate

Existing candidate artifacts remain intentionally not frozen:

```text
benchmark/n04-ai-use-cases-v3.json
benchmark/n04-v3-formal-harness-v1.json
benchmark/n04-v3-material-profiles-v1.json
benchmark/n04-v3-source-fact-verifier-profile-v1.json
tests/test_n04g21_harness_freeze_candidate.py
```

Status:

```text
freeze_candidate_pending_reference_workstation_verification
```

Generator, Phi-4 bounded judges, provider schema, Material profiles, retry, terminal and renderer semantics remain unchanged。

MiniCheck-specific profile is now treated as **provisional baseline candidate**, not final frozen verifier identity。

---

## 6. Reference Workstation local verification already performed

Codex performed a real-machine inventory on 2026-10-19.

```text
Python                  3.10.6
PyTorch                 2.6.0+cu124
CUDA build              12.4
Transformers            5.20.1
huggingface_hub         1.33.0
tokenizers              0.23.3
GPU                     RTX 4090 / CUDA available
MiniCheck               not installed in standard venv
NLTK                    not installed in standard venv
specified model snapshot not found in inspected cache
specified main ref       not found in inspected cache
```

Evidence:

```text
.local/n04-v3/g21-verification/20261019T184220+0900/
  reference-runtime-lock.json
  minicheck-runtime.json
  minicheck-screening.json
  overall-evaluation.json
```

No download/install/substitution/corpus replay was performed.

Conclusion:

```text
Reference Workstation is usable.
Formal verifier runtime is not prepared yet.
G-21 remains BLOCKED.
```

---

## 7. G-21V research decision

Read first:

```text
docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md
```

Initial candidates:

```text
A. MiniCheck RoBERTa-large
B. LettuceDetect v2 mmBERT-base
C. LettuceDetect v2 Qwen-2B
```

Summary:

- MiniCheck: 2024系document-grounded fact verifier。SGOKB G-20 baseline PASS済み。
- LettuceDetect v2 mmBERT: 2026、約0.3Bの非生成encoder、unsupported spanをtoken/span単位で検出。
- LettuceDetect v2 Qwen 2B: 2026、generative typed-span detector、structured JSONでunsupported span/categoryを返す。
- Granite Guardian 4.1 8B: groundedness judgeとして有力だが、initial first-stage verifier候補ではなくsecond-line research candidate。

SGOKBでは一般benchmarkよりcritical false-positiveを優先する。

```text
critical/G-12 false-positive = 0
  ↓
required positives PASS
  ↓
positive recall / adversarial robustness
  ↓
offline pinning / reproducibility
  ↓
dependency / latency / VRAM
```

---

## 8. Predetermined result handling

Success:

```text
MiniCheck clear winner
  -> MiniCheck select -> G-21R

mmBERT clear winner
  -> adapter candidate switch -> G-20 replay -> G-21R

Qwen 2B only safe winner
  -> additional repeatability/strict-schema Gate -> then select or remain blocked

MiniCheck/mmBERT safety tie
  -> positive recall -> reproducibility -> dependency -> latency
  -> still tied: prefer lower-change MiniCheck
```

Failure:

```text
all candidates critical FP > 0
  -> G-21V BLOCKED; no Gate relaxation; research additional candidates

FP=0 but required positives fail
  -> reject as over-conservative / unusable

exact revision cannot be pinned
  -> no silent latest substitution

GitHub Actions != Reference Workstation
  -> Reference Workstation proof is authority; investigate and block Freeze

G-22 unsupported claim recurrence
  -> preserve FAIL and reopen responsible stage; never relax rubric
```

Atomic unit内にunsupported spanが1つでもあればpartial salvageせずunit全体をno PASSとする。

---

## 9. G-21R after winner selection

G-21V selected MiniCheck; new G-21R offline proof and all engineering Gates PASS. G-21 is Complete / Frozen; G-22 is NEXT / unblocked.

Preferred isolated runtime layout:

```text
.local/n04-v3/runtime/verifier/
  venv/
  source/
  models/
  hf-cache/
  lock/
```

Preparation and proof are separate:

```text
network-enabled exact source/model preparation
  ↓
dependency lock
  ↓
network-independent / local-files-only formal replay
```

Standard SGOKB venvへ無理にverifier dependenciesを混在させない。

---

## 10. Exact next work

**N-04G-22 is Complete / valid formal FAIL (0/3 Case PASS).** Run `20261020T030904+0900` finished with all cases REJECTED after one retry each. No output rendered; unsupported rendered claims/accepted role escapes 0. Canonical/integrity and engineering Gates PASS (focused 37, contracts 10, full 408, Ruff/diff). Read `docs/evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md` and the preserved local `overall-evaluation.json`/case rubrics before deciding remediation. Do not rerun or alter Frozen conditions to improve the result.

G-21R new run `20261019T233552+0900` passed exact offline proof: socket counters 0/0, required negative FP 0/11, required positives 2/2, recall 0.8, specificity 1.0, all 17 G-21V verdicts/scores equal. Runtime preflight and canonical invariance PASS; focused 37 + contract 7 + full 405 tests PASS; repo-wide Ruff/diff PASS; post-Freeze contracts 7 PASS.

Frozen source/model pins remain `b58b9fa69acbd1015ec970fa65dd752413a053d2` / `74c8919647e61ed0f71bc177d94f10930f090068`, threshold >=0.50. All four candidate JSONs are `frozen`; local reproduction true, runtime lock bound, unresolved items empty and hashes recomputed. Standard venv and test/corpus/runner boundary hashes are unchanged.

The previous F841 blocker was repaired only after explicit user authorization and before the new boundary. Runs `20261019T225703+0900` and `20261019T231409+0900`, including original failure/PASS evidence, remain unchanged. G-12/G-20/G-20R/G-21V and prior G-21 BLOCKED evidence are retained.

Read `docs/evaluation/N04G21R_SELECTED_VERIFIER_RUNTIME_LOCAL_PROOF.md`, `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md` and the four Frozen v3 JSONs before G-22.

G-21V Complete; G-21R Complete / PASS; G-21 Complete / Frozen; G-22 Complete / valid formal FAIL. N-04 remains Failed / not Complete; N-05 remains blocked. Next is failure review: unsupported raw premises, generation atomicity/presentation-role errors and bounded role-classifier INDETERMINATE behavior. No automatic G-21 reopen or rubric/threshold/profile change is authorized by this result.

---

## 11. Read first next time

1. `docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`
4. `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
5. `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`
6. `docs/evaluation/N04G20R_RUFF_BASELINE_REMEDIATION_AND_GATE_RERUN.md`
7. `benchmark/n04g20-source-fact-verifier-v1.json`
8. `benchmark/n04-v3-source-fact-verifier-profile-v1.json`
9. `tests/test_n04g21_harness_freeze_candidate.py`

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
Material / retry / terminal / renderer semantics
G-20/G-20R historical evidence
```

Do not relax formal rubric, verifier false-positive Gate, Reference Workstation proof requirement, or engineering Gates merely to advance G-22。
