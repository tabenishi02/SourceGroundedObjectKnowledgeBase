# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-20

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
- G-21 freeze candidate: `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`
- G-21V verifier selection plan: `docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md`
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
11. specialized verifierの製品選定とG-18 Frozen semanticsを混同しない。
12. candidate比較結果を見てからthreshold / rubric / required Gateを都合よく変更しない。

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
| N-04G-21 | P0 | **Complete / Frozen (verified 2026-10-20)** | v3 acceptance spec / Reference Workstation harness freeze |
| N-04G-21V | P0 | **Complete / MiniCheck selected (2026-10-19)** | Specialized source-fact verifier candidate evaluation |
| N-04G-21R | P0 | **Complete / PASS (new run 20261019T233552+0900)** | Selected verifier runtime preparation + Reference Workstation offline proof |
| N-04G-22 | P0 | **NEXT / unblocked** | Formal v3 re-acceptance |

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

G-21V/G-21Rはこの意味設計を変更しない。

Frozen requirementは次である。

```text
V3 deterministic support
  ↓ unresolved only
specialized source-fact verifier
  ↓ supported candidate only
independent bounded source-fact judge
  ↓ ENTAILED only
supported
```

特定製品としてMiniCheckを使い続けること自体はFrozen semanticsではない。

---

## 4. G-20 / G-20R evidence entering G-21V

G-20 verifier baseline screening:

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

この結果はMiniCheckを比較baselineに残す十分なevidenceであるが、2026年時点の他candidateを比較せずfinal verifierとして永久固定する根拠にはしない。

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

## 5. N-04G-21 historical freeze candidate preparation

Authoritative freeze-candidate record:

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

All candidate JSON status remains:

```text
freeze_candidate_pending_reference_workstation_verification
```

Generator / bounded semantic model / provider schema / Material profiles / retry / terminal / renderer candidates remain unchanged。

### Specialized source-fact verifier profile

G-21で準備したMiniCheck profileは**provisional baseline candidate**として保持する。

```text
MiniCheck source revision:
  b58b9fa69acbd1015ec970fa65dd752413a053d2
model repo:
  lytang/MiniCheck-RoBERTa-Large
model revision candidate:
  74c8919647e61ed0f71bc177d94f10930f090068
threshold: 0.50 (>=)
```

G-21V完了前にこれをfinal frozen verifierとして扱わない。

---

## 6. Reference Workstation verification result after G-21 preparation

2026-10-19、CodexによるReference Workstation実機確認を実施した。

確認結果:

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
specified model snapshot not present in inspected cache
specified main ref       not present in inspected cache
```

Evidence root:

```text
.local/n04-v3/g21-verification/20261019T184220+0900/
```

Evidence:

```text
reference-runtime-lock.json
minicheck-runtime.json
minicheck-screening.json
overall-evaluation.json
```

Codexは指示どおりdownload / install / alternate runtime substitution / corpus replayを行わず停止した。

この結果から、blockerはReference Workstation故障ではなく、**formal verifier runtimeがまだ準備されていないこと**と確定した。

---

## 7. N-04G-21V — Verifier Candidate Evaluation

**Status: Complete / MiniCheck selected (2026-10-19)**

Reference Workstation run `20261019T212717+0900`: MiniCheck FP 0 / required positive 2/2 / recall 0.8、mmBERT FP 0 / 2/2 / recall 0.6、Qwen FP 0 / 1/2 / recall 0.6。全candidate specificity 1.0、Qwen x3 repeatability PASS / parser errors 0。事前tie-breakのpositive recallによりMiniCheckを選定。G-20 regression 15 passed、G-21 candidate 4 passed、full 402 passed、repo-wide Ruff / diff check PASS。標準venv不変。

成果物: `docs/evaluation/N04G21V_VERIFIER_CANDIDATE_EVALUATION.md` と `benchmark/results/n04g21v-*-reference-workstation.json`。G-21Rのoffline proofは未実行であり、G-21 / G-22はblockedを維持。

Authoritative plan:

```text
docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md
```

Initial candidates:

```text
A. MiniCheck RoBERTa-large
B. LettuceDetect v2 mmBERT-base
C. LettuceDetect v2 Qwen-2B
```

Research finding:

- MiniCheckは2024年系document-grounded fact verifierで、G-20 SGOKB corpusでbaseline GateをPASS済み。
- LettuceDetect v2 mmBERTは2026年の非生成型encoderで、unsupported spanをtoken/span単位で検出する。
- LettuceDetect v2 Qwen 2Bは2026年のgenerative typed-span detectorで、unsupported spanとcategoryをstructured outputできる。
- Granite Guardian 4.1 8Bは有力groundedness judgeだが、first-stage lightweight verifierよりPhi-4側のjudge候補に近いためinitial setから外す。

Selection priority:

```text
critical/G-12 false-positive = 0
  ↓
required positives PASS
  ↓
positive recall / adversarial robustness
  ↓
offline reproducibility
  ↓
dependency/runtime simplicity
  ↓
latency / VRAM / diagnostic value
```

公開benchmark順位だけでwinnerを決めない。

---

## 8. Predetermined result handling

比較実行前に主要分岐を固定する。

### Success

- MiniCheckが明確に勝つ -> MiniCheckを正式選定しG-21Rへ。
- mmBERTが明確に勝つ -> adapter candidateをmmBERTへ差し替え、G-20 replay後G-21Rへ。
- Qwen 2BだけがPASS -> repeatability / strict schema / temperature 0 / runtime Gateを追加確認してから採否判断。
- MiniCheckとmmBERTが同率 -> positive recall、offline pinning、dependency、latencyの順でtie-breakし、なお同等なら変更量の少ないMiniCheck。

### Failure

- 全candidateにcritical FPあり -> G-21V BLOCKED、Gateを緩めず追加candidate調査。
- FP 0だがrequired positivesをreject -> 実用性不足として不採用。
- exact revision固定不能 -> silent latest substitution禁止、不採用または新candidateとして再評価。
- GitHub ActionsとReference Workstation結果不一致 -> Reference Workstationをformal authorityとして原因調査、Freeze禁止。
- G-22でunsupported claim再発 -> G-22 FAILを保存し、原因stageへ戻す。rubric緩和禁止。

詳細はG-21V planを参照する。

---

## 9. N-04G-21R — Selected Verifier Runtime Preparation / Local Proof

**Status: Complete / PASS; G-21 Complete / Frozen (verified 2026-10-20).**

New Reference Workstation run `20261019T233552+0900` passes all offline and remaining preflight/engineering Gates: exact source/model, network 0/0, required negative FP 0/11, required positives 2/2, recall 0.8, specificity 1.0, all 17 G-21V verdicts/scores equal. Standard venv and boundary hashes unchanged. Mistral/Phi-4 smoke and MCP/Harrier/Qdrant/integrity/schema/Object identity PASS; canonical hash equal; focused 37 / contract 7 / full 405 passed; repo-wide Ruff/diff PASS. Post-Freeze contracts 7 passed again.

Four candidate JSONs are Frozen, reproduction true, exact runtime lock bound, unresolved items empty; file/canonical hashes recomputed. **G-22 is NEXT / unblocked, not executed.** Evidence: `docs/evaluation/N04G21R_SELECTED_VERIFIER_RUNTIME_LOCAL_PROOF.md` and tracked proof JSON.

Historical prior run `20261019T231409+0900` passed MiniCheck proof but was engineering-blocked by F841. The user then authorized removing only the unused assignment before a new boundary. Both old run directories, their original PASS/failure evidence and all earlier historical records are intact. The preparation syntax-failure run `20261019T225703+0900` is also retained.

Winner選定後にのみ実施する。

Standard SGOKB venvへ直接依存を追加せず、formal verifier専用runtimeを隔離することを第一候補とする。

```text
.local/n04-v3/runtime/verifier/
  venv/
  source/
  models/
  hf-cache/
  lock/
```

Procedure:

```text
A. exact source revision取得
B. exact model snapshot取得
C. dedicated venv / dependency lock構築
D. preparation完了後にnetwork-independent modeへ移行
E. G-20 corpus offline replay
F. selected candidateのcritical FP=0 / required positives PASS確認
G. exact package/runtime lock保存
H. generator/Phi-4 smoke
I. MCP/Harrier/Qdrant/integrity preflight
J. focused/replay + full pytest + repo-wide Ruff + diff check
```

全PASS時のみG-21 candidateを最終Freezeする。

---

## 10. N-04G-22 — Formal v3 Re-Acceptance

**Status: NEXT / unblocked; not started**

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

## 11. Dependency

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
G-21 freeze candidate Prepared / not Frozen
  ↓
G-21V verifier candidate evaluation
  ↓ winner selected
G-21R dedicated runtime preparation + Reference Workstation offline proof
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

## 12. Protected boundaries

Without new failure evidence, do not change:

- canonical 52-table model
- Object ID / Version identity
- Source / Evidence / Provenance
- MCP read-only boundary
- Context Builder budget / purpose selection
- Similarity ranking algorithm
- N-03 fixed dataset
- N-06 retrieval-quality metrics
- G-12 historical failed evidence
- G-18 Frozen grounded-generation semantics
- Material / retry / terminal / renderer semantics
- G-20/G-20R historical evidence

Do not relax G-18, verifier false-positive Gate, Reference Workstation proof requirement, or engineering Gates merely to obtain PASS.


## Current dependency after G-21 final Freeze — 2026-10-20

```text
G-21V Complete / MiniCheck selected
  -> G-21R Complete / exact offline proof PASS
  -> G-21 Complete / Frozen
  -> G-22 NEXT / unblocked (not executed)
  -> N-04 Complete only after G-22 3/3 formal PASS
  -> N-05 (currently blocked)
```

Earlier candidate/blocked descriptions and procedures above are retained as historical preparation context. Current machine authority is the Frozen JSON set; current status authority is the table and final G-21R record above.
