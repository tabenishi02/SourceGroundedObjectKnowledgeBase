# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record: `main`
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed remediation task: **N-04G-16 [P0] Semantic validation architecture redesign**
- Next task: **N-04G-17 [P0] Material sufficiency / terminal / render gate redesign**

---

## 1. Handoff purpose

N-04 post-G12 remediationを別チャットへ引き継ぐための現在状態を固定する。

過去のPhase N stacked branchは正本として使用しない。各Task完了後にmainへ統合し、次Taskはmainから開始する。

---

## 2. Formal v2 baseline

G-12 formal run:

```text
run_id: 20261018T213810+0900
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
Result: 0 / 3 Case PASS
```

| Case | Machine terminal | Formal verdict |
|---|---|---|
| Saber Roleplay | ACCEPTED | FAIL |
| Similar Work Comparison | REJECTED | FAIL |
| Concept Combination Creative | REJECTED | FAIL |

Safety/regressionは正常だった。

```text
canonical SHA-256 before == after
integrity before / after = PASS / PASS
focused grounding = 21 passed
focused read-path = 27 passed
full pytest = 382 passed / 0 skipped / 0 failed
Ruff = PASS
git diff --check = PASS
```

したがって、今回のremediationでは具体的failure evidenceがない限りRetrieval / MCP / Context Builder / canonical schemaを変更しない。

---

## 3. G-12 failure baseline

### Case 1

- supported clause + unsupported Holy Grail War clauseが同一unitに混在。
- Phi-4がunit全体を`entailed`とfalse accept。
- material duty / loyalty claimが`stylistic_expression`として`role_valid`を通過。
- unsupported textがrenderされた。

### Case 2

- Attempt 1 unsupported source fact。
- Attempt 2 support refs欠落。
- unsupported interpretation premiseが存在するのに`derived_supported`相当へ進み得た。

### Case 3

- `creative` blockの`label=null`が2 attempt連続。
- provider schemaでは合法、application parserでは違法というcontract mismatch。

---

## 4. Completed remediation Decisions

### N-04G-14 — Atomic claim / semantic-role boundary

正本:

```text
docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
```

主要Decision:

- `1 validation unit = 1 atomic semantic proposition`。
- Atomicity verdict = `ATOMIC / NON_ATOMIC / INDETERMINATE`。
- `ATOMIC`だけがsupport/derivation validationへ進める。
- content materialityをmodel-declared semantic roleより優先。
- mixed-role unit禁止。
- role mismatchをsilent reclassificationで救済しない。
- v3 baselineではmodel-authored `stylistic_expression`禁止。
- `context_limit` / `creative_addition`境界を狭義化。
- interpretationはconclusion-only。

Case 1 U2/U3はG-14 Gateだけでgrounded PASS不可になる。

### N-04G-15 — Output schema / presentation / renderer

正本:

```text
docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
```

主要Decision:

- model-generated free-form `label`をv3 contractから削除。
- headingはtrusted rendererが`presentation_role`から生成。
- user-visible LLM semantic textはvalidated `unit.text`だけ。
- role-specific block schemaを第一候補。
- provider schema / application parserを同一logical schemaから導出。
- `stylistic_expression`をv3 model output enumから除外。
- schema failure path/detailを保持可能にする。
- `sgokb.grounded-generation-output.v2`へのrevisionを予約。最終shapeはG-18でfreeze。

Case 3 `label=null` failure pathはfield削除により消える。

### N-04G-16 — Semantic validation architecture

正本:

```text
docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md
```

Source fact path:

```text
V3 deterministic support
  ↓ unresolved only
V4F specialized source-fact verifier
  ↓ supported candidate only
independent bounded LLM judge
  ↓
composition / disagreement policy
```

Decision:

- MiniCheck family = primary source-fact verifier benchmark candidate。
- AlignScore = secondary benchmark candidate。
- deterministic-supported source factはmodel verifier不要。
- specialized negativeはgeneral LLM positiveで救済しない。
- specialized positive + independent LLM `ENTAILED` agreementをv3 semantic support条件とする方向。
- disagreement / ambiguity / unavailableはPASS不可。
- raw scoreをtruth probability扱いしない。thresholdはSGOKB replay/adversarial setでfreezeする。

Interpretation path:

```text
validated source_fact units
  ↓
premise_unit_ids integrity gate
  ↓
bounded derivation judge
```

Decision:

- interpretationからdirect K `support_refs`を廃止する方向。
- `premise_unit_ids[]`で既にsupportedのsource_factを参照。
- premiseはv3ではsource_factのみ。interpretation chaining禁止。
- unsupported / contradictory / indeterminate premiseがあればderivation judgeへ進めない。
- derivation judgeはconclusionがpremiseだけからreasonableに導けるかだけを判定。
- hidden external premiseを必要とするconclusionを`derived_supported`にしない。

Empirical verifier Gate:

- G-16では特定MiniCheck/AlignScore checkpointやthresholdをproduction採用していない。
- G-19でcandidate adapterを統合する。
- G-20でG-12 replay/adversarial offline benchmarkを実施する。
- required negative/replay caseをfalse-positiveするprofileはG-21 formal harnessへ採用しない。

G-16でもproduction codeは変更していない。

---

## 5. Current remediation chain

```text
N-04G-13  Root-cause / desk review / research        Complete
N-04G-14  Atomic claim / semantic-role redesign      Complete
N-04G-15  Output / presentation contract hardening   Complete
N-04G-16  Semantic validation architecture           Complete (design)
N-04G-17  Material / terminal / render gate          Pending
N-04G-18  Post-G12 Design Freeze                     Pending
N-04G-19  Implementation + verifier candidate        Pending
N-04G-20  Adversarial / verifier benchmark/regression Pending
N-04G-21  v3 acceptance / harness freeze             Pending
N-04G-22  Formal v3 re-acceptance                    Pending
```

N-04 CompleteはG-22で3/3 Case PASS + safety/regression Gate全PASS後のみ。

---

## 6. Next task — N-04G-17

```text
N-04G-17 [P0]
Material sufficiency / terminal / render gate redesign
```

主な論点:

- `Grounding PASS`と`use-case completion`を分離する。
- `MaterialRequirementGate`または同等componentを設計する。
- comparisonの両Object source coverageをGate化する。
- creativeの両Concept grounding + creative addition存在をGate化する。
- roleplayのformal最低grounded fact数等をcoreにhardcodeせずharness requirementとして注入する。
- `ACCEPTED`をGrounding PASSだけで出さない。
- rendererをterminal decisionへbindする。
- `REJECTED / SYSTEM_FAILURE`はnormal render不可。
- `INSUFFICIENT_CONTEXT`はcontext-limit専用safe render pathだけ許容する。

G-17も設計Taskであり、G-18 Design Freeze前にproduction codeを変更しない。

---

## 7. Read first in next chat

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
4. `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
5. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
6. `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
7. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
8. `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
9. `src/sgokb/grounding/validation.py`
10. `src/sgokb/grounding/failure.py`
11. `src/sgokb/grounding/render.py`

---

## 8. Protected boundaries

具体的failure evidenceがない限り次を変更しない。

```text
Object identity
current accepted Version semantics
Canonical Statement / Attribute / Relation
Evidence / Provenance
Version immutability
Retrieval / Similarity basic contract
MCP read boundary
Context Builder selection / budget
N-03 dataset
G-12 failed evidence
```

rubricを緩和してPASSさせない。